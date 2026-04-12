"""Document ingestion endpoint - protected by API key."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from search_angel.api.dependencies import (
    get_db,
    get_encoder,
    get_evidence_analyzer,
    get_ip_hash,
    get_os_client,
    verify_api_key,
)
from search_angel.config import Settings, get_settings
from search_angel.core.deduplication import compute_simhash
from search_angel.core.evidence import EvidenceAnalyzer
from search_angel.db.repositories import DocumentRepository, SourceRepository
from search_angel.embeddings.encoder import EmbeddingEncoder
from search_angel.models.schemas.ingestion import IndexRequest, IndexResponse
from search_angel.privacy.audit import PrivacyAuditor
from search_angel.search.client import OpenSearchClient

router = APIRouter(prefix="/index", tags=["ingestion"])


@router.post("", response_model=IndexResponse, dependencies=[Depends(verify_api_key)])
async def index_document(
    request: IndexRequest,
    db: AsyncSession = Depends(get_db),
    os_client: OpenSearchClient = Depends(get_os_client),
    encoder: EmbeddingEncoder = Depends(get_encoder),
    evidence_analyzer: EvidenceAnalyzer = Depends(get_evidence_analyzer),
    settings: Settings = Depends(get_settings),
    ip_hash: str = Depends(get_ip_hash),
) -> IndexResponse:
    """Ingest a single document into the search engine."""
    # 1. Compute hashes for dedup
    normalized_url = request.url.strip().rstrip("/").lower()
    url_hash = hashlib.sha256(normalized_url.encode()).hexdigest()
    content_hash = hashlib.sha256(request.content.encode()).hexdigest()

    # 2. Check for URL duplicate
    doc_repo = DocumentRepository(db)
    existing = await doc_repo.get_by_url_hash(url_hash)
    if existing:
        # Check if content changed
        if existing.content_hash == content_hash:
            return IndexResponse(
                document_id=str(existing.id),
                status="duplicate",
                duplicate_of=str(existing.id),
            )
        # Content changed - update
        await doc_repo.update_by_id(
            existing.id,
            content=request.content,
            content_hash=content_hash,
            title=request.title,
            updated_at=datetime.now(timezone.utc),
        )
        doc_id = existing.id
        status = "updated"
    else:
        # 3. Classify and ensure source exists
        domain = request.source_domain or _extract_domain(request.url)
        source_repo = SourceRepository(db)
        classification = evidence_analyzer.classify_source(request.url)
        source = await source_repo.get_or_create(
            domain=domain,
            source_type=classification.source_type,
            credibility_score=classification.credibility_score,
            bias_label=classification.bias_label,
        )

        # 4. Compute embedding
        embedding = await encoder.async_encode(
            f"{request.title} {request.content[:1000]}"
        )

        # 5. Compute SimHash
        simhash = compute_simhash(request.content)

        # 6. Create document
        word_count = len(request.content.split())
        doc = await doc_repo.create(
            source_id=source.id,
            url=request.url,
            url_hash=url_hash,
            title=request.title,
            content=request.content,
            content_hash=content_hash,
            language="en",
            word_count=word_count,
            embedding=embedding,
            published_at=request.published_at,
            indexed_at=datetime.now(timezone.utc),
        )
        doc_id = doc.id
        status = "created"

    # 7. Index in OpenSearch
    try:
        source_data = {}
        if not existing:
            source_data = {
                "source_id": str(source.id),
                "domain": domain,
                "name": source.name,
                "source_type": classification.source_type,
                "credibility_score": classification.credibility_score,
                "bias_label": classification.bias_label,
            }

        os_doc = {
            "doc_id": str(doc_id),
            "url": request.url,
            "title": request.title,
            "content": request.content,
            "word_count": len(request.content.split()),
            "embedding": embedding if not existing else None,
            "source": source_data,
            "published_at": (
                request.published_at.isoformat() if request.published_at else None
            ),
            "indexed_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": content_hash,
        }
        # Remove None embedding for updates
        os_doc = {k: v for k, v in os_doc.items() if v is not None}

        await os_client.index_document(str(doc_id), os_doc)
    except Exception:
        # Log but don't fail - document is in PostgreSQL, can be re-indexed
        import logging
        logging.getLogger(__name__).exception("Failed to index document in OpenSearch")

    PrivacyAuditor.log_ingestion(ip_hash)

    return IndexResponse(
        document_id=str(doc_id),
        status=status,
    )


def _extract_domain(url: str) -> str:
    try:
        parsed = urlparse(url)
        domain = parsed.hostname or ""
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.lower()
    except Exception:
        return "unknown"
