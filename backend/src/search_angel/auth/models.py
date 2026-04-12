"""User and API key models - privacy-preserving authentication."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from search_angel.models.db.base import Base


class User(Base):
    """User account. Email stored as hash - we never see the actual email."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    account_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="free"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_users_email_hash", "email_hash"),
    )


class UserAPIKey(Base):
    """API keys for programmatic access."""

    __tablename__ = "user_api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    tier: Mapped[str] = mapped_column(String(20), default="free")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_api_keys_hash", "key_hash"),
    )
