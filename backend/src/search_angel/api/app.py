"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from search_angel.api.middleware.logging import StructuredLoggingMiddleware
from search_angel.api.middleware.privacy import PrivacyMiddleware
from search_angel.api.middleware.timing import TimingMiddleware
from search_angel.api.routers import documents, evidence, health, ingestion, search
from search_angel.config import get_settings
from search_angel.db.engine import dispose_engine
from search_angel.privacy.anonymizer import Anonymizer

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage startup and shutdown lifecycle."""
    settings = get_settings()
    logger.info(
        "Starting %s v%s [%s]",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )

    # Pre-warm OpenSearch client
    from search_angel.api.dependencies import get_os_client

    os_client = get_os_client(settings)

    # Create index if it doesn't exist
    from search_angel.search.index_manager import IndexManager

    idx_mgr = IndexManager(os_client, settings)
    try:
        created = await idx_mgr.create_index()
        if created:
            logger.info("OpenSearch index created")
    except Exception:
        logger.warning("Could not create OpenSearch index at startup", exc_info=True)

    yield

    # Shutdown
    logger.info("Shutting down %s", settings.app_name)
    await os_client.close()
    await dispose_engine()


def create_app() -> FastAPI:
    settings = get_settings()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Privacy-first deep search engine with hybrid BM25 + vector search",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Middleware (order matters: first added = outermost)
    app.add_middleware(TimingMiddleware)
    app.add_middleware(StructuredLoggingMiddleware)
    app.add_middleware(
        PrivacyMiddleware,
        anonymizer=Anonymizer(rotation_hours=settings.ip_salt_rotation_hours),
    )
    # CORS: allow frontend origin in production, all origins in debug
    cors_origins: list[str] = []
    if settings.debug:
        cors_origins = ["*"]
    elif settings.frontend_url:
        cors_origins = [settings.frontend_url]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["X-API-Key", "X-Session-Token", "Content-Type", "Authorization"],
    )

    # Mount routers
    prefix = "/api/v1"
    app.include_router(health.router, prefix=prefix)
    app.include_router(search.router, prefix=prefix)
    app.include_router(documents.router, prefix=prefix)
    app.include_router(evidence.router, prefix=prefix)
    app.include_router(ingestion.router, prefix=prefix)

    # Auth + Premium routers
    from search_angel.auth.router import router as auth_router
    from search_angel.premium.router import router as premium_router

    app.include_router(auth_router, prefix=prefix)
    app.include_router(premium_router, prefix=prefix)

    # Phantom Mode (ephemeral containers - no auth needed)
    from search_angel.api.routers.phantom import router as phantom_router
    app.include_router(phantom_router, prefix=prefix)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs": "/docs" if settings.debug else "disabled",
        }

    return app
