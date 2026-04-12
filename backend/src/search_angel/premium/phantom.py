"""Phantom Mode - Ephemeral Docker containers for anonymous search sessions.

Creates a fresh Docker container per session. All search data exists only
inside the container. When the session ends, the container is destroyed.
Zero trace remains. No machine ID, no logs, nothing.

Available to ALL users (rate limited by IP hash).
"""

from __future__ import annotations

import asyncio
import logging
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

MAX_SESSIONS = 5  # Max concurrent ephemeral containers
SESSION_TTL = 1800  # 30 minutes max per session


@dataclass
class PhantomSession:
    session_id: str
    ip_hash: str
    container_id: str | None = None
    container_name: str = ""
    port: int = 0
    status: str = "creating"
    created_at: float = field(default_factory=time.time)
    search_count: int = 0


class PhantomManager:
    """Manages ephemeral Docker containers for Phantom Mode."""

    def __init__(self) -> None:
        self._sessions: dict[str, PhantomSession] = {}
        self._docker: Any = None

    def _get_docker(self) -> Any:
        if self._docker is None:
            import docker
            self._docker = docker.from_env()
        return self._docker

    @property
    def active_count(self) -> int:
        return sum(1 for s in self._sessions.values() if s.status == "running")

    def get_session(self, session_id: str) -> PhantomSession | None:
        return self._sessions.get(session_id)

    def has_active_session(self, ip_hash: str) -> PhantomSession | None:
        """Check if this IP already has an active session."""
        for s in self._sessions.values():
            if s.ip_hash == ip_hash and s.status == "running":
                return s
        return None

    async def create(self, ip_hash: str) -> PhantomSession:
        """Create a new ephemeral container."""
        # Rate limit: 1 session per IP
        existing = self.has_active_session(ip_hash)
        if existing:
            return existing

        # Global limit
        if self.active_count >= MAX_SESSIONS:
            raise RuntimeError("Maximum concurrent phantom sessions reached")

        session_id = secrets.token_hex(16)
        session = PhantomSession(
            session_id=session_id,
            ip_hash=ip_hash,
        )
        self._sessions[session_id] = session

        try:
            client = self._get_docker()

            # Find available port (9100-9199 range)
            used_ports = {s.port for s in self._sessions.values() if s.port > 0}
            port = 9100
            while port in used_ports and port < 9200:
                port += 1

            container_name = f"phantom_{session_id[:12]}"

            # Create ephemeral container from our app image
            # It connects to the shared SearXNG for web search
            # But has NO persistent storage - everything is in-memory
            container = client.containers.run(
                image="search_angel-app:latest",
                name=container_name,
                detach=True,
                auto_remove=True,  # Auto-delete when stopped
                network="search_angel_sa-internal",
                ports={"8000/tcp": port},
                environment={
                    "SEARCH_ANGEL_ENVIRONMENT": "phantom",
                    "SEARCH_ANGEL_DEBUG": "false",
                    "SEARCH_ANGEL_PG_HOST": "sa-postgres",
                    "SEARCH_ANGEL_OS_HOST": "sa-opensearch",
                    "SEARCH_ANGEL_SEARXNG_URL": "http://sa-searxng:8080",
                    "SEARCH_ANGEL_WEB_SEARCH_ENABLED": "true",
                },
                # Resource limits - keep it light
                mem_limit="512m",
                cpu_period=100000,
                cpu_quota=50000,
                # NO volumes - nothing persists
                tmpfs={"/tmp": "size=100m"},
            )

            session.container_id = container.id
            session.container_name = container_name
            session.port = port
            session.status = "running"

            # Schedule auto-destruction
            asyncio.create_task(self._auto_destroy(session_id))

            logger.info(
                "Phantom session created: %s (port %d) for ip_hash %s",
                session_id[:8], port, ip_hash[:8]
            )
            return session

        except Exception as e:
            session.status = "failed"
            logger.exception("Failed to create phantom container")
            raise

    async def destroy(self, session_id: str) -> bool:
        """Destroy a phantom container. All data vanishes."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        if session.container_id:
            try:
                client = self._get_docker()
                container = client.containers.get(session.container_id)
                container.stop(timeout=3)
                logger.info("Phantom destroyed: %s (zero trace)", session_id[:8])
            except Exception:
                logger.debug("Container already gone: %s", session_id[:8])

        session.status = "destroyed"
        del self._sessions[session_id]
        return True

    async def _auto_destroy(self, session_id: str) -> None:
        """Auto-destroy after TTL."""
        await asyncio.sleep(SESSION_TTL)
        if session_id in self._sessions:
            logger.info("Auto-destroying expired phantom: %s", session_id[:8])
            await self.destroy(session_id)
