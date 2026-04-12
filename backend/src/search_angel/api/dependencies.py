"""FastAPI dependency injection."""

from __future__ import annotations

import hashlib
from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from search_angel.config import Settings, get_settings
from search_angel.core.deduplication import Deduplicator
from search_angel.core.evidence import EvidenceAnalyzer
from search_angel.core.pipeline import SearchPipeline
from search_angel.core.query_processor import QueryProcessor
from search_angel.core.ranking import EvidenceRanker
from search_angel.core.summarizer import Summarizer
from search_angel.db.engine import get_async_session
from search_angel.embeddings.encoder import EmbeddingEncoder
from search_angel.search.bm25 import BM25Retriever
from search_angel.search.client import OpenSearchClient
from search_angel.search.hybrid import HybridSearchEngine
from search_angel.search.vector import VectorRetriever

# Singletons (initialized once)
_os_client: OpenSearchClient | None = None
_encoder: EmbeddingEncoder | None = None
_web_retriever: object | None = None
_web_retriever_tor: object | None = None


def get_os_client(settings: Settings = Depends(get_settings)) -> OpenSearchClient:
    global _os_client
    if _os_client is None:
        _os_client = OpenSearchClient(settings)
    return _os_client


def get_encoder(settings: Settings = Depends(get_settings)) -> EmbeddingEncoder:
    global _encoder
    if _encoder is None:
        _encoder = EmbeddingEncoder(
            model_name=settings.embedding_model,
            dimension=settings.embedding_dimension,
        )
    return _encoder


async def get_db(
) -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_session():
        yield session


def get_web_retriever(settings: Settings = Depends(get_settings)) -> object | None:
    global _web_retriever
    if not settings.web_search_enabled:
        return None
    if _web_retriever is None:
        from search_angel.search.web import WebRetriever

        _web_retriever = WebRetriever(
            searxng_url=settings.searxng_url,
            timeout=settings.web_search_timeout,
        )
    return _web_retriever


def get_web_retriever_tor(settings: Settings = Depends(get_settings)) -> object | None:
    global _web_retriever_tor
    if not settings.web_search_enabled:
        return None
    if _web_retriever_tor is None:
        from search_angel.search.web import WebRetriever

        _web_retriever_tor = WebRetriever(
            searxng_url=settings.searxng_tor_url,
            timeout=15.0,  # Tor is slower
        )
    return _web_retriever_tor


def get_search_pipeline(
    settings: Settings = Depends(get_settings),
    os_client: OpenSearchClient = Depends(get_os_client),
    encoder: EmbeddingEncoder = Depends(get_encoder),
    web_retriever: object | None = Depends(get_web_retriever),
) -> SearchPipeline:
    bm25 = BM25Retriever(os_client, settings)
    vector = VectorRetriever(os_client, settings)
    hybrid = HybridSearchEngine(bm25, vector, encoder, settings, web_retriever)

    return SearchPipeline(
        query_processor=QueryProcessor(),
        hybrid_engine=hybrid,
        ranker=EvidenceRanker(),
        deduplicator=Deduplicator(),
        summarizer=Summarizer(settings),
    )


def get_evidence_analyzer() -> EvidenceAnalyzer:
    return EvidenceAnalyzer()


def get_ip_hash(request: Request) -> str:
    return getattr(request.state, "ip_hash", "unknown")


async def verify_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> str:
    """Verify API key for ingestion endpoints."""
    if not settings.ingestion_api_key_hash:
        raise HTTPException(
            status_code=503,
            detail="Ingestion API key not configured",
        )

    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    if key_hash != settings.ingestion_api_key_hash:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return x_api_key
