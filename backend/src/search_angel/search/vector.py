"""kNN vector search via OpenSearch."""

from __future__ import annotations

import logging
from typing import Any

from search_angel.config import Settings
from search_angel.search.bm25 import ScoredDocument
from search_angel.search.client import OpenSearchClient

logger = logging.getLogger(__name__)


class VectorRetriever:
    def __init__(self, os_client: OpenSearchClient, settings: Settings) -> None:
        self._os = os_client
        self._settings = settings

    async def search(
        self,
        query_embedding: list[float],
        *,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[ScoredDocument]:
        k = top_k or self._settings.search_vector_top_k

        knn_clause: dict[str, Any] = {
            "embedding": {
                "vector": query_embedding,
                "k": k,
            }
        }

        # If filters are present, wrap kNN with a bool filter
        if filters:
            body: dict[str, Any] = {
                "size": k,
                "query": {
                    "bool": {
                        "must": [{"knn": knn_clause}],
                        "filter": [filters],
                    }
                },
            }
        else:
            body = {
                "size": k,
                "query": {"knn": knn_clause},
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
                    published_at=src.get("published_at"),
                )
            )
        return documents
