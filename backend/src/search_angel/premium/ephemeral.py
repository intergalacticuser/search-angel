"""Ephemeral Docker session manager for premium users.

Spins up isolated containers per search session.
When the session ends, the container is destroyed - zero trace remains.
"""

from __future__ import annotations

import asyncio
import logging
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class EphemeralSession:
    session_id: str
    user_id: str
    container_id: str | None = None
    port: int = 0
    status: str = "creating"  # creating, running, destroyed
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    max_ttl_seconds: int = 3600  # 1 hour max


class EphemeralSessionManager:
    """Manages isolated Docker containers for premium search sessions.

    Each premium user gets their own container with:
    - Isolated search state (in-memory only)
    - Connection to shared SearXNG (for web search)
    - No persistent storage
    - Auto-destruction on session end or TTL expiry
    """

    def __init__(self, network_name: str = "search_angel_sa-internal") -> None:
        self._network = network_name
        self._sessions: dict[str, EphemeralSession] = {}
        self._docker_client = None

    def _get_docker(self):  # type: ignore[no-untyped-def]
        if self._docker_client is None:
            try:
                import docker
                self._docker_client = docker.from_env()
            except Exception:
                logger.error("Docker SDK not available. Install: pip install docker")
                raise
        return self._docker_client

    async def create_session(self, user_id: str) -> EphemeralSession:
        """Spin up an ephemeral container for a premium user."""
        session_id = secrets.token_hex(16)

        session = EphemeralSession(
            session_id=session_id,
            user_id=user_id,
        )
        self._sessions[session_id] = session

        try:
            client = self._get_docker()

            # Find an available port
            port = 9000 + len(self._sessions)

            container = client.containers.run(
                image="search_angel-app:latest",
                name=f"sa_ephemeral_{session_id[:12]}",
                detach=True,
                auto_remove=True,
                network=self._network,
                ports={"8000/tcp": port},
                environment={
                    "SEARCH_ANGEL_ENVIRONMENT": "ephemeral",
                    "SEARCH_ANGEL_DEBUG": "false",
                    "SEARCH_ANGEL_SESSION_TTL_MINUTES": "60",
                    # Use shared infrastructure
                    "SEARCH_ANGEL_PG_HOST": "sa-postgres",
                    "SEARCH_ANGEL_OS_HOST": "sa-opensearch",
                    "SEARCH_ANGEL_SEARXNG_URL": "http://sa-searxng:8888",
                },
                mem_limit="512m",
                cpu_period=100000,
                cpu_quota=50000,  # 50% of one CPU
            )

            session.container_id = container.id
            session.port = port
            session.status = "running"

            # Schedule auto-destruction
            asyncio.create_task(
                self._auto_destroy(session_id, session.max_ttl_seconds)
            )

            logger.info(
                "Ephemeral session created: %s (container: %s, port: %d)",
                session_id[:8],
                container.short_id,
                port,
            )

            return session

        except Exception:
            session.status = "failed"
            logger.exception("Failed to create ephemeral session")
            raise

    async def destroy_session(self, session_id: str) -> bool:
        """Destroy an ephemeral container. All data is lost."""
        session = self._sessions.get(session_id)
        if not session or not session.container_id:
            return False

        try:
            client = self._get_docker()
            container = client.containers.get(session.container_id)
            container.stop(timeout=5)
            logger.info(
                "Ephemeral session destroyed: %s (zero trace)",
                session_id[:8],
            )
        except Exception:
            logger.warning("Container already stopped: %s", session_id[:8])

        session.status = "destroyed"
        del self._sessions[session_id]
        return True

    async def _auto_destroy(self, session_id: str, ttl: int) -> None:
        """Auto-destroy container after TTL expires."""
        await asyncio.sleep(ttl)
        if session_id in self._sessions:
            logger.info("Auto-destroying expired session: %s", session_id[:8])
            await self.destroy_session(session_id)

    def get_session(self, session_id: str) -> EphemeralSession | None:
        return self._sessions.get(session_id)

    def get_user_sessions(self, user_id: str) -> list[EphemeralSession]:
        return [s for s in self._sessions.values() if s.user_id == user_id]

    @property
    def active_count(self) -> int:
        return len(self._sessions)
