"""Search session model - privacy-respecting, anonymous, TTL-based."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from search_angel.models.db.base import Base


class SearchSession(Base):
    __tablename__ = "search_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_token: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )
    ip_hash: Mapped[str | None] = mapped_column(String(64))
    query_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_sessions_expires", "expires_at"),
        Index("idx_sessions_token", "session_token"),
    )
