"""Health check endpoint."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from search_angel.config import Settings, get_settings
from search_angel.models.schemas.common import HealthComponent, HealthResponse
from search_angel.search.client import OpenSearchClient
from search_angel.api.dependencies import get_os_client

router = APIRouter(tags=["health"])

_start_time = time.monotonic()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings: Settings = Depends(get_settings),
    os_client: OpenSearchClient = Depends(get_os_client),
) -> HealthResponse:
    components: dict[str, HealthComponent] = {}

    # Check PostgreSQL
    try:
        from search_angel.db.engine import get_engine

        engine = get_engine()
        start = time.monotonic()
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        pg_latency = (time.monotonic() - start) * 1000
        components["postgres"] = HealthComponent(
            status="healthy", latency_ms=round(pg_latency, 2)
        )
    except Exception as e:
        components["postgres"] = HealthComponent(
            status="unhealthy", detail=str(e)
        )

    # Check OpenSearch
    try:
        start = time.monotonic()
        cluster = await os_client.health()
        os_latency = (time.monotonic() - start) * 1000
        os_status = cluster.get("status", "unknown")
        components["opensearch"] = HealthComponent(
            status="healthy" if os_status in ("green", "yellow") else "degraded",
            latency_ms=round(os_latency, 2),
            detail=f"cluster_status={os_status}",
        )
    except Exception as e:
        components["opensearch"] = HealthComponent(
            status="unhealthy", detail=str(e)
        )

    # Check embedding model
    try:
        from search_angel.embeddings.encoder import EmbeddingEncoder

        enc = EmbeddingEncoder(settings.embedding_model, settings.embedding_dimension)
        start = time.monotonic()
        test_emb = enc.encode("health check")
        emb_latency = (time.monotonic() - start) * 1000
        components["embedding_model"] = HealthComponent(
            status="healthy" if len(test_emb) == settings.embedding_dimension else "degraded",
            latency_ms=round(emb_latency, 2),
            detail=f"dimension={len(test_emb)}",
        )
    except Exception as e:
        components["embedding_model"] = HealthComponent(
            status="unhealthy", detail=str(e)
        )

    # Overall status
    statuses = [c.status for c in components.values()]
    if all(s == "healthy" for s in statuses):
        overall = "healthy"
    elif any(s == "unhealthy" for s in statuses):
        overall = "unhealthy"
    else:
        overall = "degraded"

    uptime = time.monotonic() - _start_time

    return HealthResponse(
        status=overall,
        version=settings.app_version,
        components=components,
        uptime_seconds=round(uptime, 2),
    )
