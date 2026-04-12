"""Evidence chain endpoint."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from search_angel.api.dependencies import get_db, get_ip_hash
from search_angel.db.repositories import DocumentRepository, EvidenceRepository
from search_angel.models.schemas.evidence import EvidenceChainResponse, EvidenceLinkDetail
from search_angel.privacy.audit import PrivacyAuditor

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("/{doc_id}", response_model=EvidenceChainResponse)
async def get_evidence_chain(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    ip_hash: str = Depends(get_ip_hash),
) -> EvidenceChainResponse:
    """Get the full evidence chain for a document."""
    try:
        doc_uuid = uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID format")

    doc_repo = DocumentRepository(db)
    doc = await doc_repo.get_by_id(doc_uuid)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    PrivacyAuditor.log_document_access(ip_hash)

    ev_repo = EvidenceRepository(db)
    links = await ev_repo.get_chain_for_document(doc_uuid)

    # Collect all linked doc IDs for title lookup
    linked_ids = set()
    for link in links:
        linked_ids.add(
            link.target_doc_id if link.source_doc_id == doc_uuid else link.source_doc_id
        )
    linked_docs = await doc_repo.get_by_ids(list(linked_ids))
    doc_map = {d.id: d for d in linked_docs}

    # Categorize links
    supports: list[EvidenceLinkDetail] = []
    contradicts: list[EvidenceLinkDetail] = []
    related: list[EvidenceLinkDetail] = []
    citations: list[EvidenceLinkDetail] = []

    for link in links:
        linked_id = (
            link.target_doc_id
            if link.source_doc_id == doc_uuid
            else link.source_doc_id
        )
        linked_doc = doc_map.get(linked_id)

        detail = EvidenceLinkDetail(
            link_id=str(link.id),
            doc_id=str(linked_id),
            doc_title=linked_doc.title if linked_doc else "Unknown",
            doc_url=linked_doc.url if linked_doc else "",
            relationship=link.relationship_type,
            confidence=link.confidence,
            method=link.method,
            evidence_text=link.evidence_text,
        )

        if link.relationship_type == "supports":
            supports.append(detail)
        elif link.relationship_type == "contradicts":
            contradicts.append(detail)
        elif link.relationship_type in ("cites", "cited_by"):
            citations.append(detail)
        else:
            related.append(detail)

    return EvidenceChainResponse(
        document_id=doc_id,
        supports=supports,
        contradicts=contradicts,
        related=related,
        citations=citations,
        total_links=len(links),
    )
