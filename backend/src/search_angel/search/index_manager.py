"""OpenSearch index creation and mapping management."""

from __future__ import annotations

import logging
from typing import Any

from search_angel.config import Settings
from search_angel.search.client import OpenSearchClient

logger = logging.getLogger(__name__)

DOCUMENT_INDEX_SETTINGS: dict[str, Any] = {
    "settings": {
        "index": {
            "number_of_shards": 2,
            "number_of_replicas": 1,
            "knn": True,
            "knn.algo_param.ef_search": 100,
        },
        "analysis": {
            "analyzer": {
                "content_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop", "snowball", "trim"],
                },
                "title_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding"],
                },
            }
        },
    },
    "mappings": {
        "properties": {
            "doc_id": {"type": "keyword"},
            "url": {"type": "keyword"},
            "title": {
                "type": "text",
                "analyzer": "title_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "suggest": {"type": "search_as_you_type"},
                },
            },
            "content": {
                "type": "text",
                "analyzer": "content_analyzer",
                "fields": {
                    "exact": {"type": "text", "analyzer": "standard"},
                },
            },
            "summary": {"type": "text", "analyzer": "content_analyzer"},
            "language": {"type": "keyword"},
            "word_count": {"type": "integer"},
            "embedding": {
                "type": "knn_vector",
                "dimension": 384,
                "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "lucene",
                    "parameters": {
                        "ef_construction": 256,
                        "m": 16,
                    },
                },
            },
            "source": {
                "type": "object",
                "properties": {
                    "source_id": {"type": "keyword"},
                    "domain": {"type": "keyword"},
                    "name": {"type": "text"},
                    "source_type": {"type": "keyword"},
                    "credibility_score": {"type": "float"},
                    "bias_label": {"type": "keyword"},
                },
            },
            "evidence": {
                "type": "nested",
                "properties": {
                    "linked_doc_id": {"type": "keyword"},
                    "relationship": {"type": "keyword"},
                    "confidence": {"type": "float"},
                },
            },
            "published_at": {"type": "date"},
            "indexed_at": {"type": "date"},
            "content_hash": {"type": "keyword"},
        }
    },
}


class IndexManager:
    def __init__(self, os_client: OpenSearchClient, settings: Settings) -> None:
        self._os = os_client
        self._settings = settings

    async def create_index(self, index_name: str | None = None) -> bool:
        name = index_name or self._settings.os_index_name
        exists: bool = await self._os.client.indices.exists(index=name)
        if exists:
            logger.info("Index '%s' already exists, skipping creation", name)
            return False

        await self._os.client.indices.create(
            index=name, body=DOCUMENT_INDEX_SETTINGS
        )
        logger.info("Created index '%s'", name)
        return True

    async def delete_index(self, index_name: str | None = None) -> bool:
        name = index_name or self._settings.os_index_name
        exists: bool = await self._os.client.indices.exists(index=name)
        if not exists:
            return False

        await self._os.client.indices.delete(index=name)
        logger.info("Deleted index '%s'", name)
        return True

    async def get_mapping(self, index_name: str | None = None) -> dict:
        name = index_name or self._settings.os_index_name
        result: dict = await self._os.client.indices.get_mapping(index=name)
        return result

    async def get_doc_count(self, index_name: str | None = None) -> int:
        name = index_name or self._settings.os_index_name
        result: dict = await self._os.client.count(index=name)
        return int(result["count"])
