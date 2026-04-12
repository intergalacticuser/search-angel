"""Search request and response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from search_angel.models.schemas.common import SearchMode, SourceInfo


class SearchFilterSchema(BaseModel):
    date_from: str | None = None
    date_to: str | None = None
    source_types: list[str] | None = None
    language: str | None = None
    min_credibility: float | None = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    mode: SearchMode = SearchMode.STANDARD
    filters: SearchFilterSchema | None = None
    include_summary: bool = False
    tor_mode: bool = False
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=10, ge=1, le=100)


class QueryMetadata(BaseModel):
    intent: str
    mode: str
    entity_count: int = 0
    expansion_count: int = 0
    entities: list[dict[str, str]] = Field(default_factory=list)
    expanded_terms: list[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    id: str
    url: str
    title: str
    snippet: str
    score: float
    source: SourceInfo
    evidence_count: int = 0
    published_at: datetime | None = None
    explanation: dict[str, float] | None = None
    # Media fields
    category: str = "general"
    thumbnail: str | None = None
    img_src: str | None = None
    video_url: str | None = None
    iframe_src: str | None = None
    author: str | None = None
    media_metadata: dict[str, object] | None = None


class CategorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    category: str = Field(default="general")
    tor_mode: bool = False
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)


class CategorySearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    category: str
    timing_ms: float = 0.0


class SummarySchema(BaseModel):
    text: str
    citations: list[CitationSchema] = Field(default_factory=list)
    model_used: str = ""
    confidence: str = "medium"


class CitationSchema(BaseModel):
    doc_id: str
    title: str
    url: str
    relevance: str = "high"


class SearchResponse(BaseModel):
    results: list[SearchResult]
    total: int
    summary: SummarySchema | None = None
    query_metadata: QueryMetadata | None = None
    timing_ms: float = 0.0


class EvidenceEdge(BaseModel):
    source_doc_id: str
    target_doc_id: str
    relationship: str
    confidence: float


class DeepSearchResponse(SearchResponse):
    evidence_graph: list[EvidenceEdge] = Field(default_factory=list)
    source_distribution: dict[str, int] = Field(default_factory=dict)
    confidence_assessment: str = ""


class PerspectiveGroup(BaseModel):
    label: str
    source_bias: str
    results: list[SearchResult]
    key_claims: list[str] = Field(default_factory=list)


class CompareRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    perspectives: int = Field(default=3, ge=2, le=5)
    filters: SearchFilterSchema | None = None


class CompareResponse(BaseModel):
    query: str
    perspectives: list[PerspectiveGroup]
    summary: str = ""
    timing_ms: float = 0.0
