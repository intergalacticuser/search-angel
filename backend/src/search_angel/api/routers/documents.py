"""Document detail endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from search_angel.api.dependencies import get_db, get_ip_hash
from search_angel.db.repositories import DocumentRepository, EvidenceRepository
from search_angel.models.schemas.common import SourceInfo
from search_angel.models.schemas.documents import DocumentDetail, EvidenceLinkSchema
from search_angel.privacy.audit import PrivacyAuditor
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    ip_hash: str = Depends(get_ip_hash),
) -> DocumentDetail:
    """Get full document detail with evidence links."""
    try:
        doc_uuid = uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    doc_repo = DocumentRepository(db)
    doc = await doc_repo.get_by_id(doc_uuid)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    PrivacyAuditor.log_document_access(ip_hash)

    # Build evidence links
    ev_repo = EvidenceRepository(db)
    evidence = await ev_repo.get_chain_for_document(doc_uuid)
    evidence_links = [
        EvidenceLinkSchema(
            linked_doc_id=str(
                ev.target_doc_id if ev.source_doc_id == doc_uuid else ev.source_doc_id
            ),
            linked_doc_title="",  # Would need join to get title
            relationship=ev.relationship_type,
            confidence=ev.confidence,
            method=ev.method,
            evidence_text=ev.evidence_text,
        )
        for ev in evidence
    ]

    # Build source info
    source_info = None
    if doc.source:
        source_info = SourceInfo(
            source_id=str(doc.source.id),
            domain=doc.source.domain,
            name=doc.source.name,
            source_type=doc.source.source_type,
            credibility_score=doc.source.credibility_score,
            bias_label=doc.source.bias_label,
        )

    return DocumentDetail(
        id=str(doc.id),
        url=doc.url,
        title=doc.title,
        content=doc.content,
        summary=doc.summary,
        source=source_info,
        evidence_links=evidence_links,
        language=doc.language,
        word_count=doc.word_count,
        published_at=doc.published_at,
        indexed_at=doc.indexed_at,
        created_at=doc.created_at,
    )
