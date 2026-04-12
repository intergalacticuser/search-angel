"""Evidence repository with chain and contradiction queries."""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select

from search_angel.db.repositories.base import BaseRepository
from search_angel.models.db.evidence import EvidenceLink


class EvidenceRepository(BaseRepository[EvidenceLink]):
    model = EvidenceLink

    async def get_chain_for_document(self, doc_id: uuid.UUID) -> list[EvidenceLink]:
        stmt = select(EvidenceLink).where(
            or_(
                EvidenceLink.source_doc_id == doc_id,
                EvidenceLink.target_doc_id == doc_id,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_relationship(
        self, doc_id: uuid.UUID, relationship: str
    ) -> list[EvidenceLink]:
        stmt = select(EvidenceLink).where(
            EvidenceLink.source_doc_id == doc_id,
            EvidenceLink.relationship_type == relationship,
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_contradictions(self, doc_id: uuid.UUID) -> list[EvidenceLink]:
        return await self.get_by_relationship(doc_id, "contradicts")

    async def get_supporting(self, doc_id: uuid.UUID) -> list[EvidenceLink]:
        return await self.get_by_relationship(doc_id, "supports")

    async def get_links_for_documents(
        self, doc_ids: list[uuid.UUID]
    ) -> list[EvidenceLink]:
        if not doc_ids:
            return []
        stmt = select(EvidenceLink).where(
            or_(
                EvidenceLink.source_doc_id.in_(doc_ids),
                EvidenceLink.target_doc_id.in_(doc_ids),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
