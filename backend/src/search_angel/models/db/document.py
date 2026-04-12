"""Document model - core content storage with embeddings."""

from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from search_angel.models.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="SET NULL")
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10), default="en")
    word_count: Mapped[int | None] = mapped_column(Integer)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    source: Mapped["Source | None"] = relationship(back_populates="documents")  # noqa: F821
    evidence_as_source: Mapped[list["EvidenceLink"]] = relationship(  # noqa: F821
        foreign_keys="EvidenceLink.source_doc_id", back_populates="source_doc", lazy="selectin"
    )
    evidence_as_target: Mapped[list["EvidenceLink"]] = relationship(  # noqa: F821
        foreign_keys="EvidenceLink.target_doc_id", back_populates="target_doc", lazy="selectin"
    )

    __table_args__ = (
        Index("idx_documents_source", "source_id"),
        Index("idx_documents_url_hash", "url_hash"),
        Index("idx_documents_published", "published_at"),
    )
