"""Ingestion schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class IndexRequest(BaseModel):
    url: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    source_domain: str | None = None
    published_at: datetime | None = None
    metadata: dict[str, object] | None = None


class IndexResponse(BaseModel):
    document_id: str
    status: str  # created | updated | duplicate
    duplicate_of: str | None = None


class BulkIndexRequest(BaseModel):
    documents: list[IndexRequest] = Field(..., min_length=1, max_length=100)


class BulkIndexResponse(BaseModel):
    total: int
    created: int
    updated: int
    duplicates: int
    errors: int
