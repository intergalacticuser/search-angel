"""Document schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from search_angel.models.schemas.common import SourceInfo


class EvidenceLinkSchema(BaseModel):
    linked_doc_id: str
    linked_doc_title: str
    relationship: str
    confidence: float
    method: str
    evidence_text: str | None = None


class DuplicateClusterInfo(BaseModel):
    cluster_id: str
    cluster_size: int
    is_canonical: bool


class DocumentDetail(BaseModel):
    id: str
    url: str
    title: str
    content: str
    summary: str | None = None
    source: SourceInfo | None = None
    evidence_links: list[EvidenceLinkSchema] = Field(default_factory=list)
    duplicate_cluster: DuplicateClusterInfo | None = None
    language: str = "en"
    word_count: int | None = None
    published_at: datetime | None = None
    indexed_at: datetime | None = None
    created_at: datetime | None = None
