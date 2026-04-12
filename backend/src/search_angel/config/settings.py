"""Application configuration via environment variables."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SEARCH_ANGEL_",
        case_sensitive=False,
    )

    # ── Application ──────────────────────────────────────────────────────
    app_name: str = "Search Angel"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"

    # ── PostgreSQL ───────────────────────────────────────────────────────
    pg_host: str = "localhost"
    pg_port: int = 5432
    pg_user: str = "search_angel"
    pg_password: str = "changeme_pg_password"
    pg_database: str = "search_angel"
    pg_pool_size: int = 20
    pg_max_overflow: int = 10

    # ── OpenSearch ───────────────────────────────────────────────────────
    os_host: str = "localhost"
    os_port: int = 9200
    os_scheme: str = "https"
    os_user: str = "admin"
    os_password: str = "YOUR_OS_PASSWORD"
    os_index_name: str = "search_angel_documents"
    os_verify_certs: bool = False

    # ── Embeddings ───────────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    embedding_batch_size: int = 32

    # ── Search ───────────────────────────────────────────────────────────
    search_default_limit: int = 10
    search_max_limit: int = 100
    search_bm25_top_k: int = 50
    search_vector_top_k: int = 50
    rrf_k: int = 60

    # ── Privacy ──────────────────────────────────────────────────────────
    session_ttl_minutes: int = 30
    ip_salt_rotation_hours: int = 24

    # ── AI Summary ───────────────────────────────────────────────────────
    llm_provider: str = "openai"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_max_tokens: int = 500

    # ── Live Web Search (SearXNG) ────────────────────────────────────────
    web_search_enabled: bool = True
    searxng_url: str = "http://sa-searxng:8080"
    searxng_tor_url: str = "http://sa-searxng-tor:8080"
    web_search_top_k: int = 20
    web_search_timeout: float = 10.0

    # ── Frontend ─────────────────────────────────────────────────────────
    frontend_url: str = ""  # e.g. "https://search.example.com"

    # ── Ingestion Auth ───────────────────────────────────────────────────
    ingestion_api_key_hash: str = ""

    # ── Database URL (alternative to individual PG_ vars) ────────────────
    database_url: str = ""  # Full DSN, overrides PG_* vars if set

    # ── Derived properties ───────────────────────────────────────────────
    @property
    def pg_dsn(self) -> str:
        if self.database_url:
            # Convert postgres:// to postgresql+asyncpg://
            url = self.database_url
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )

    @property
    def pg_dsn_sync(self) -> str:
        return (
            f"postgresql://{self.pg_user}:{self.pg_password}"
            f"@{self.pg_host}:{self.pg_port}/{self.pg_database}"
        )

    @property
    def os_url(self) -> str:
        return f"{self.os_scheme}://{self.os_host}:{self.os_port}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
