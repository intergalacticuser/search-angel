"""Common schemas shared across endpoints."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class SearchMode(str, Enum):
    STANDARD = "standard"
    DEEP = "deep"
    EVIDENCE = "evidence"
    OPEN_WEB = "open_web"
    COMPARE_NARRATIVES = "compare_narratives"
    PRIVATE = "private"


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    request_id: str | None = None


class HealthComponent(BaseModel):
    status: str  # healthy | degraded | unhealthy
    latency_ms: float | None = None
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str  # healthy | degraded | unhealthy
    version: str
    components: dict[str, HealthComponent]
    uptime_seconds: float


class SourceInfo(BaseModel):
    source_id: str | None = None
    domain: str
    name: str | None = None
    source_type: str = "unknown"
    credibility_score: float = 0.5
    bias_label: str = "unknown"
