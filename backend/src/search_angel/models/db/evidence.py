"""Evidence link model - directional relationships between documents."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from search_angel.models.db.base import Base


class EvidenceLink(Base):
    __tablename__ = "evidence_links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_doc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_doc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    relationship_type: Mapped[str] = mapped_column(
        "relationship", String(20), nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_text: Mapped[str | None] = mapped_column(Text)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    source_doc: Mapped["Document"] = relationship(  # noqa: F821
        foreign_keys=[source_doc_id], back_populates="evidence_as_source"
    )
    target_doc: Mapped["Document"] = relationship(  # noqa: F821
        foreign_keys=[target_doc_id], back_populates="evidence_as_target"
    )

    __table_args__ = (
        CheckConstraint(
            "relationship IN ('supports','contradicts','related','cites','cited_by','updates')",
            name="ck_relationship_type",
        ),
        CheckConstraint(
            "confidence BETWEEN 0.0 AND 1.0",
            name="ck_confidence_range",
        ),
        CheckConstraint(
            "method IN ('nlp_entailment','citation_extraction','manual',"
            "'url_reference','cosine_similarity')",
            name="ck_method_type",
        ),
        CheckConstraint(
            "source_doc_id != target_doc_id",
            name="ck_no_self_link",
        ),
        UniqueConstraint(
            "source_doc_id", "target_doc_id", "relationship",
            name="uq_evidence_pair",
        ),
        Index("idx_evidence_source", "source_doc_id"),
        Index("idx_evidence_target", "target_doc_id"),
        Index("idx_evidence_relationship", "relationship"),
    )
