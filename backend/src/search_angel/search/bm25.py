"""BM25 text retrieval via OpenSearch."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from search_angel.config import Settings
from search_angel.search.client import OpenSearchClient

logger = logging.getLogger(__name__)


@dataclass
class SearchFilters:
    date_from: str | None = None
    date_to: str | None = None
    source_types: list[str] = field(default_factory=list)
    language: str | None = None
    min_credibility: float | None = None


@dataclass
class ScoredDocument:
    doc_id: str
    score: float
    title: str
    content: str
    url: str
    source: dict[str, Any] = field(default_factory=dict)
    highlight: dict[str, list[str]] = field(default_factory=dict)
    published_at: str | None = None
    # Media fields
    category: str = "general"
    thumbnail: str | None = None
    img_src: str | None = None
    video_url: str | None = None
    iframe_src: str | None = None
    author: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BM25Retriever:
    def __init__(self, os_client: OpenSearchClient, settings: Settings) -> None:
        self._os = os_client
        self._settings = settings

    async def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
        filters: SearchFilters | None = None,
        expanded_terms: list[str] | None = None,
    ) -> list[ScoredDocument]:
        k = top_k or self._settings.search_bm25_top_k

        # Build the main query
        search_query = query
        if expanded_terms:
            search_query = f"{query} {' '.join(expanded_terms)}"

        must_clauses: list[dict[str, Any]] = [
            {
                "multi_match": {
                    "query": search_query,
                    "fields": ["title^3", "content", "summary^1.5"],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            }
        ]

        filter_clauses: list[dict[str, Any]] = []
        should_clauses: list[dict[str, Any]] = [
            # Boost high-credibility sources
            {"range": {"source.credibility_score": {"gte": 0.7, "boost": 1.5}}}
        ]

        if filters:
            if filters.date_from or filters.date_to:
                date_range: dict[str, str] = {}
                if filters.date_from:
                    date_range["gte"] = filters.date_from
                if filters.date_to:
                    date_range["lte"] = filters.date_to
                filter_clauses.append({"range": {"published_at": date_range}})

            if filters.source_types:
                filter_clauses.append(
                    {"terms": {"source.source_type": filters.source_types}}
                )

            if filters.language:
                filter_clauses.append({"term": {"language": filters.language}})

            if filters.min_credibility is not None:
                filter_clauses.append(
                    {"range": {"source.credibility_score": {"gte": filters.min_credibility}}}
                )

        body: dict[str, Any] = {
            "query": {
                "bool": {
                    "must": must_clauses,
                    "filter": filter_clauses,
                    "should": should_clauses,
                }
            },
            "highlight": {
                "fields": {
                    "title": {"number_of_fragments": 1},
                    "content": {"number_of_fragments": 3, "fragment_size": 200},
                }
            },
            "size": k,
        }

        result = await self._os.search(body=body)
        return self._parse_hits(result)

    def _parse_hits(self, result: dict[str, Any]) -> list[ScoredDocument]:
        hits = result.get("hits", {}).get("hits", [])
        documents: list[ScoredDocument] = []
        for hit in hits:
            src = hit["_source"]
            documents.append(
                ScoredDocument(
                    doc_id=src.get("doc_id", hit["_id"]),
                    score=float(hit["_score"]),
                    title=src.get("title", ""),
                    content=src.get("content", ""),
                    url=src.get("url", ""),
                    source=src.get("source", {}),
                    highlight=hit.get("highlight", {}),
                    published_at=src.get("published_at"),
                )
            )
        return documents
