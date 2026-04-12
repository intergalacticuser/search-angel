"""Hybrid search engine with Reciprocal Rank Fusion (3-way: BM25 + vector + web)."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from search_angel.config import Settings
from search_angel.embeddings.encoder import EmbeddingEncoder
from search_angel.search.bm25 import BM25Retriever, ScoredDocument, SearchFilters
from search_angel.search.vector import VectorRetriever

logger = logging.getLogger(__name__)


@dataclass
class RankedDocument:
    doc_id: str
    rrf_score: float
    bm25_score: float
    vector_score: float
    web_score: float
    bm25_rank: int | None
    vector_rank: int | None
    web_rank: int | None
    title: str
    content: str
    url: str
    source: dict[str, Any] = field(default_factory=dict)
    highlight: dict[str, list[str]] = field(default_factory=dict)
    published_at: str | None = None


class HybridSearchEngine:
    """Orchestrates BM25 + vector + live web search with RRF fusion."""

    MODE_TOP_K = {
        "standard": 30,
        "deep": 100,
        "evidence": 50,
        "open_web": 50,
        "compare_narratives": 60,
        "private": 30,
    }

    def __init__(
        self,
        bm25: BM25Retriever,
        vector: VectorRetriever,
        encoder: EmbeddingEncoder,
        settings: Settings,
        web_retriever: Any | None = None,
    ) -> None:
        self._bm25 = bm25
        self._vector = vector
        self._encoder = encoder
        self._settings = settings
        self._web = web_retriever

    async def search(
        self,
        query: str,
        *,
        mode: str = "standard",
        filters: SearchFilters | None = None,
        expanded_terms: list[str] | None = None,
    ) -> list[RankedDocument]:
        top_k = self.MODE_TOP_K.get(mode, 30)

        # Encode query for vector search
        query_embedding = await self._encoder.async_encode(query)

        # Build OpenSearch filter dict for vector search
        os_filters = self._build_os_filters(filters) if filters else None

        # Build parallel tasks: BM25 + vector + optional web
        tasks: list[Any] = [
            self._bm25.search(
                query, top_k=top_k, filters=filters, expanded_terms=expanded_terms
            ),
            self._vector.search(
                query_embedding, top_k=top_k, filters=os_filters
            ),
        ]

        # Add web search if available
        use_web = self._web is not None and mode != "private"
        if use_web:
            # Pick categories based on mode
            categories = ["general"]
            if mode == "deep":
                categories = ["general", "news", "science"]
            elif mode == "compare_narratives":
                categories = ["general", "news"]
            elif mode == "open_web":
                categories = ["general", "news", "science", "it"]

            tasks.append(
                self._web.search(
                    query,
                    top_k=self._settings.web_search_top_k,
                    categories=categories,
                )
            )

        # Run all retrievers in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        bm25_results: list[ScoredDocument] = results[0] if not isinstance(results[0], Exception) else []
        vector_results: list[ScoredDocument] = results[1] if not isinstance(results[1], Exception) else []
        web_results: list[ScoredDocument] = []

        if use_web and len(results) > 2:
            web_results = results[2] if not isinstance(results[2], Exception) else []

        if isinstance(results[0], Exception):
            logger.warning("BM25 search failed: %s", results[0])
        if isinstance(results[1], Exception):
            logger.warning("Vector search failed: %s", results[1])
        if use_web and len(results) > 2 and isinstance(results[2], Exception):
            logger.warning("Web search failed: %s", results[2])

        logger.info(
            "Hybrid search: BM25=%d, vector=%d, web=%d",
            len(bm25_results),
            len(vector_results),
            len(web_results),
        )

        # 3-way RRF fusion
        return self._reciprocal_rank_fusion(
            bm25_results, vector_results, web_results, k=self._settings.rrf_k
        )

    def _reciprocal_rank_fusion(
        self,
        bm25_results: list[ScoredDocument],
        vector_results: list[ScoredDocument],
        web_results: list[ScoredDocument],
        k: int = 60,
    ) -> list[RankedDocument]:
        """Combine three ranked lists using Reciprocal Rank Fusion.

        RRF_score(d) = sum over systems S of: 1 / (k + rank_S(d))
        """
        # Build doc_id -> rank maps (1-indexed)
        bm25_ranks: dict[str, int] = {
            doc.doc_id: rank + 1 for rank, doc in enumerate(bm25_results)
        }
        vector_ranks: dict[str, int] = {
            doc.doc_id: rank + 1 for rank, doc in enumerate(vector_results)
        }

        # For web results, use URL as dedup key since doc_ids are synthetic
        web_ranks: dict[str, int] = {}
        web_by_url: dict[str, ScoredDocument] = {}
        for rank, doc in enumerate(web_results):
            web_ranks[doc.url] = rank + 1
            web_by_url[doc.url] = doc

        # Collect all unique documents (by doc_id for local, by URL for web)
        all_docs: dict[str, ScoredDocument] = {}
        for doc in bm25_results:
            all_docs[doc.doc_id] = doc
        for doc in vector_results:
            if doc.doc_id not in all_docs:
                all_docs[doc.doc_id] = doc
        for doc in web_results:
            # Use URL-based key for web results to avoid collisions
            key = f"web:{doc.url}"
            if key not in all_docs and doc.url not in {d.url for d in all_docs.values()}:
                all_docs[key] = doc

        # Compute RRF scores
        fused: list[RankedDocument] = []
        for doc_key, doc in all_docs.items():
            bm25_rank = bm25_ranks.get(doc.doc_id)
            vector_rank = vector_ranks.get(doc.doc_id)
            web_rank = web_ranks.get(doc.url)

            rrf_score = 0.0
            if bm25_rank is not None:
                rrf_score += 1.0 / (k + bm25_rank)
            if vector_rank is not None:
                rrf_score += 1.0 / (k + vector_rank)
            if web_rank is not None:
                rrf_score += 1.0 / (k + web_rank)

            fused.append(
                RankedDocument(
                    doc_id=doc.doc_id,
                    rrf_score=rrf_score,
                    bm25_score=doc.score if bm25_rank is not None else 0.0,
                    vector_score=doc.score if vector_rank is not None else 0.0,
                    web_score=doc.score if web_rank is not None else 0.0,
                    bm25_rank=bm25_rank,
                    vector_rank=vector_rank,
                    web_rank=web_rank,
                    title=doc.title,
                    content=doc.content,
                    url=doc.url,
                    source=doc.source,
                    highlight=doc.highlight,
                    published_at=doc.published_at,
                )
            )

        fused.sort(key=lambda d: d.rrf_score, reverse=True)
        return fused

    @staticmethod
    def _build_os_filters(filters: SearchFilters) -> dict[str, Any] | None:
        clauses: list[dict[str, Any]] = []

        if filters.date_from or filters.date_to:
            date_range: dict[str, str] = {}
            if filters.date_from:
                date_range["gte"] = filters.date_from
            if filters.date_to:
                date_range["lte"] = filters.date_to
            clauses.append({"range": {"published_at": date_range}})

        if filters.source_types:
            clauses.append({"terms": {"source.source_type": filters.source_types}})

        if filters.language:
            clauses.append({"term": {"language": filters.language}})

        if not clauses:
            return None
        if len(clauses) == 1:
            return clauses[0]
        return {"bool": {"must": clauses}}
