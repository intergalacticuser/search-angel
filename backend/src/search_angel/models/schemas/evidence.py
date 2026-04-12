"""Evidence schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EvidenceLinkDetail(BaseModel):
    link_id: str
    doc_id: str
    doc_title: str
    doc_url: str
    relationship: str
    confidence: float
    method: str
    evidence_text: str | None = None


class EvidenceChainResponse(BaseModel):
    document_id: str
    supports: list[EvidenceLinkDetail] = Field(default_factory=list)
    contradicts: list[EvidenceLinkDetail] = Field(default_factory=list)
    related: list[EvidenceLinkDetail] = Field(default_factory=list)
    citations: list[EvidenceLinkDetail] = Field(default_factory=list)
    total_links: int = 0
