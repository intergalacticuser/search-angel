"""Alembic environment configuration."""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add src to path so models can be imported
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from search_angel.models.db import Base  # noqa: E402

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Override URL from environment (for Docker/production)
    import os

    configuration = config.get_section(config.config_ini_section, {})
    pg_host = os.environ.get("SEARCH_ANGEL_PG_HOST", "localhost")
    pg_port = os.environ.get("SEARCH_ANGEL_PG_PORT", "5432")
    pg_user = os.environ.get("SEARCH_ANGEL_PG_USER", "search_angel")
    pg_pass = os.environ.get("SEARCH_ANGEL_PG_PASSWORD", "changeme_pg_password")
    pg_db = os.environ.get("SEARCH_ANGEL_PG_DATABASE", "search_angel")
    configuration["sqlalchemy.url"] = (
        f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
    )

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
