"""OpenSearch async client wrapper with connection management."""

from __future__ import annotations

import logging
from typing import Any

from opensearchpy import AsyncOpenSearch

from search_angel.config import Settings

logger = logging.getLogger(__name__)


class OpenSearchClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: AsyncOpenSearch | None = None

    @property
    def client(self) -> AsyncOpenSearch:
        if self._client is None:
            self._client = AsyncOpenSearch(
                hosts=[{"host": self._settings.os_host, "port": self._settings.os_port}],
                http_auth=(self._settings.os_user, self._settings.os_password),
                use_ssl=self._settings.os_scheme == "https",
                verify_certs=self._settings.os_verify_certs,
                ssl_show_warn=False,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True,
            )
        return self._client

    async def search(
        self,
        body: dict[str, Any],
        index: str | None = None,
    ) -> dict[str, Any]:
        idx = index or self._settings.os_index_name
        result: dict[str, Any] = await self.client.search(body=body, index=idx)
        return result

    async def index_document(
        self,
        doc_id: str,
        body: dict[str, Any],
        index: str | None = None,
    ) -> dict[str, Any]:
        idx = index or self._settings.os_index_name
        result: dict[str, Any] = await self.client.index(
            index=idx, id=doc_id, body=body, refresh="wait_for"
        )
        return result

    async def bulk_index(
        self,
        actions: list[dict[str, Any]],
        index: str | None = None,
    ) -> dict[str, Any]:
        from opensearchpy.helpers import async_bulk

        idx = index or self._settings.os_index_name
        for action in actions:
            action.setdefault("_index", idx)
        success, errors = await async_bulk(self.client, actions, raise_on_error=False)
        return {"success": success, "errors": errors}

    async def delete_document(
        self, doc_id: str, index: str | None = None
    ) -> dict[str, Any]:
        idx = index or self._settings.os_index_name
        result: dict[str, Any] = await self.client.delete(index=idx, id=doc_id)
        return result

    async def health(self) -> dict[str, Any]:
        result: dict[str, Any] = await self.client.cluster.health()
        return result

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
            self._client = None
