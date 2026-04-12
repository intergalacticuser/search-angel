"""Base async repository with common CRUD operations."""

from __future__ import annotations

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from search_angel.models.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def get_all(self, *, offset: int = 0, limit: int = 100) -> list[ModelT]:
        stmt = select(self.model).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, **kwargs: Any) -> ModelT:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update_by_id(self, entity_id: uuid.UUID, **kwargs: Any) -> None:
        stmt = update(self.model).where(self.model.id == entity_id).values(**kwargs)  # type: ignore[attr-defined]
        await self.session.execute(stmt)

    async def delete_by_id(self, entity_id: uuid.UUID) -> None:
        stmt = delete(self.model).where(self.model.id == entity_id)  # type: ignore[attr-defined]
        await self.session.execute(stmt)
