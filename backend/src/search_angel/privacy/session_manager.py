"""TTL-based anonymous session management."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from search_angel.models.db.session import SearchSession
from search_angel.privacy.anonymizer import Anonymizer


class SessionManager:
    """Manages opt-in anonymous sessions with TTL expiry.

    Sessions store NO query content - only token, ip_hash, count, and timestamps.
    """

    def __init__(self, anonymizer: Anonymizer, ttl_minutes: int = 30) -> None:
        self._anonymizer = anonymizer
        self._ttl = timedelta(minutes=ttl_minutes)

    async def get_or_create(
        self, session_token: str | None, ip: str, db: AsyncSession
    ) -> SearchSession | None:
        """Look up an existing session or return None if no token provided.

        Sessions are opt-in: only created when a client explicitly sends a token.
        """
        if not session_token:
            return None

        # Look up existing session
        stmt = select(SearchSession).where(
            SearchSession.session_token == session_token,
            SearchSession.expires_at > datetime.now(timezone.utc),
        )
        result = await db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            # Update activity
            session.query_count += 1
            session.last_active_at = datetime.now(timezone.utc)
            # Extend TTL on activity
            session.expires_at = datetime.now(timezone.utc) + self._ttl
            await db.flush()
            return session

        return None

    async def create_session(self, ip: str, db: AsyncSession) -> SearchSession:
        """Explicitly create a new anonymous session."""
        now = datetime.now(timezone.utc)
        session = SearchSession(
            session_token=secrets.token_hex(32),
            ip_hash=self._anonymizer.hash_ip(ip),
            query_count=0,
            expires_at=now + self._ttl,
            last_active_at=now,
        )
        db.add(session)
        await db.flush()
        return session

    async def cleanup_expired(self, db: AsyncSession) -> int:
        """Delete expired sessions. Returns count deleted."""
        stmt = delete(SearchSession).where(
            SearchSession.expires_at < datetime.now(timezone.utc)
        )
        result = await db.execute(stmt)
        return result.rowcount  # type: ignore[return-value]
