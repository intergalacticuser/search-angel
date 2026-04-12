"""Document repository with search-specific queries."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from search_angel.db.repositories.base import BaseRepository
from search_angel.models.db.document import Document


class DocumentRepository(BaseRepository[Document]):
    model = Document

    async def get_by_url_hash(self, url_hash: str) -> Document | None:
        stmt = select(Document).where(Document.url_hash == url_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_content_hash(self, content_hash: str) -> list[Document]:
        stmt = select(Document).where(Document.content_hash == content_hash)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_source(
        self, source_id: uuid.UUID, *, offset: int = 0, limit: int = 100
    ) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.source_id == source_id)
            .offset(offset)
            .limit(limit)
            .order_by(Document.published_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_unindexed(self, *, limit: int = 100) -> list[Document]:
        stmt = (
            select(Document)
            .where(Document.indexed_at.is_(None))
            .limit(limit)
            .order_by(Document.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_ids(self, doc_ids: list[uuid.UUID]) -> list[Document]:
        if not doc_ids:
            return []
        stmt = select(Document).where(Document.id.in_(doc_ids))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
