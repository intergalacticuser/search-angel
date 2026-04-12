"""Source repository."""

from __future__ import annotations

from sqlalchemy import select

from search_angel.db.repositories.base import BaseRepository
from search_angel.models.db.source import Source


class SourceRepository(BaseRepository[Source]):
    model = Source

    async def get_by_domain(self, domain: str) -> Source | None:
        stmt = select(Source).where(Source.domain == domain)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, domain: str, **defaults: object) -> Source:
        existing = await self.get_by_domain(domain)
        if existing:
            return existing
        return await self.create(domain=domain, **defaults)

    async def get_high_credibility(
        self, min_score: float = 0.7, *, limit: int = 50
    ) -> list[Source]:
        stmt = (
            select(Source)
            .where(Source.credibility_score >= min_score)
            .order_by(Source.credibility_score.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
