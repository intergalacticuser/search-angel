"""Add users and API keys tables.

Revision ID: 002
Revises: 001
Create Date: 2025-01-02 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("email_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(128), nullable=False),
        sa.Column("account_type", sa.String(20), nullable=False, server_default="'free'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_users_email_hash", "users", ["email_hash"])

    op.create_table(
        "user_api_keys",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("tier", sa.String(20), server_default="'free'"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_api_keys_hash", "user_api_keys", ["key_hash"])


def downgrade() -> None:
    op.drop_table("user_api_keys")
    op.drop_table("users")
