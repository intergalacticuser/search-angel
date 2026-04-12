"""Duplicate cluster models - near-duplicate document grouping."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from search_angel.models.db.base import Base


class DuplicateCluster(Base):
    __tablename__ = "duplicate_clusters"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    canonical_doc_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL")
    )
    simhash: Mapped[int] = mapped_column(BigInteger, nullable=False)
    cluster_size: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    canonical_doc: Mapped["Document | None"] = relationship(  # noqa: F821
        foreign_keys=[canonical_doc_id]
    )
    members: Mapped[list["DuplicateClusterMember"]] = relationship(
        back_populates="cluster", lazy="selectin"
    )

    __table_args__ = (
        Index("idx_dup_clusters_simhash", "simhash"),
    )


class DuplicateClusterMember(Base):
    __tablename__ = "duplicate_cluster_members"

    cluster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("duplicate_clusters.id", ondelete="CASCADE"),
        primary_key=True,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    cluster: Mapped["DuplicateCluster"] = relationship(back_populates="members")
    document: Mapped["Document"] = relationship()  # noqa: F821
