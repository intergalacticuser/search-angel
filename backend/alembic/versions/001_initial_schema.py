"""Initial schema - all core tables.

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Sources table
    op.create_table(
        "sources",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("domain", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text()),
        sa.Column("source_type", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("credibility_score", sa.Float(), server_default="0.5"),
        sa.Column("bias_label", sa.String(20), server_default="'unknown'"),
        sa.Column("fact_check_count", sa.Integer(), server_default="0"),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "source_type IN ('news','academic','government','blog',"
            "'social_media','wiki','corporate','unknown')",
            name="ck_source_type",
        ),
        sa.CheckConstraint(
            "credibility_score BETWEEN 0.0 AND 1.0",
            name="ck_credibility_range",
        ),
        sa.CheckConstraint(
            "bias_label IN ('left','center_left','center','center_right','right','unknown')",
            name="ck_bias_label",
        ),
    )
    op.create_index("idx_sources_domain", "sources", ["domain"])
    op.create_index("idx_sources_credibility", "sources", ["credibility_score"])

    # Documents table
    op.create_table(
        "documents",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_id", sa.dialects.postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("sources.id", ondelete="SET NULL")),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("url_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("language", sa.String(10), server_default="'en'"),
        sa.Column("word_count", sa.Integer()),
        sa.Column("embedding", Vector(384)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("crawled_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("indexed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_documents_source", "documents", ["source_id"])
    op.create_index("idx_documents_url_hash", "documents", ["url_hash"])
    op.create_index("idx_documents_published", "documents", ["published_at"])

    # Evidence links table
    op.create_table(
        "evidence_links",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_doc_id", sa.dialects.postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_doc_id", sa.dialects.postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship", sa.String(20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_text", sa.Text()),
        sa.Column("method", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "relationship IN ('supports','contradicts','related','cites','cited_by','updates')",
            name="ck_relationship_type",
        ),
        sa.CheckConstraint("confidence BETWEEN 0.0 AND 1.0", name="ck_confidence_range"),
        sa.CheckConstraint(
            "method IN ('nlp_entailment','citation_extraction','manual',"
            "'url_reference','cosine_similarity')",
            name="ck_method_type",
        ),
        sa.CheckConstraint("source_doc_id != target_doc_id", name="ck_no_self_link"),
        sa.UniqueConstraint("source_doc_id", "target_doc_id", "relationship",
                            name="uq_evidence_pair"),
    )
    op.create_index("idx_evidence_source", "evidence_links", ["source_doc_id"])
    op.create_index("idx_evidence_target", "evidence_links", ["target_doc_id"])
    op.create_index("idx_evidence_relationship", "evidence_links", ["relationship"])

    # Duplicate clusters
    op.create_table(
        "duplicate_clusters",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("canonical_doc_id", sa.dialects.postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("documents.id", ondelete="SET NULL")),
        sa.Column("simhash", sa.BigInteger(), nullable=False),
        sa.Column("cluster_size", sa.Integer(), server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_dup_clusters_simhash", "duplicate_clusters", ["simhash"])

    # Duplicate cluster members
    op.create_table(
        "duplicate_cluster_members",
        sa.Column("cluster_id", sa.dialects.postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("duplicate_clusters.id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("document_id", sa.dialects.postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("documents.id", ondelete="CASCADE"),
                  primary_key=True),
        sa.Column("similarity_score", sa.Float(), nullable=False),
    )

    # Search sessions
    op.create_table(
        "search_sessions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_token", sa.String(64), nullable=False, unique=True),
        sa.Column("ip_hash", sa.String(64)),
        sa.Column("query_count", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_active_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_sessions_expires", "search_sessions", ["expires_at"])
    op.create_index("idx_sessions_token", "search_sessions", ["session_token"])

    # Cleanup function
    op.execute("""
        CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
        RETURNS void AS $$
        BEGIN
            DELETE FROM search_sessions WHERE expires_at < NOW();
        END;
        $$ LANGUAGE plpgsql;
    """)


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS cleanup_expired_sessions()")
    op.drop_table("duplicate_cluster_members")
    op.drop_table("duplicate_clusters")
    op.drop_table("search_sessions")
    op.drop_table("evidence_links")
    op.drop_table("documents")
    op.drop_table("sources")
