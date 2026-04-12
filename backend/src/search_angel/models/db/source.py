"""Source model - publisher/origin metadata with credibility scoring."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from search_angel.models.db.base import Base


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    domain: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="unknown",
    )
    credibility_score: Mapped[float] = mapped_column(Float, default=0.5)
    bias_label: Mapped[str] = mapped_column(String(20), default="unknown")
    fact_check_count: Mapped[int] = mapped_column(Integer, default=0)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    documents: Mapped[list["Document"]] = relationship(  # noqa: F821
        back_populates="source", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('news','academic','government','blog',"
            "'social_media','wiki','corporate','unknown')",
            name="ck_source_type",
        ),
        CheckConstraint(
            "credibility_score BETWEEN 0.0 AND 1.0",
            name="ck_credibility_range",
        ),
        CheckConstraint(
            "bias_label IN ('left','center_left','center','center_right','right','unknown')",
            name="ck_bias_label",
        ),
        Index("idx_sources_domain", "domain"),
        Index("idx_sources_credibility", "credibility_score"),
    )
