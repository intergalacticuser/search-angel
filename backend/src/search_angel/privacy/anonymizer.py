"""IP anonymization and PII stripping."""

from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone


class Anonymizer:
    """Handles IP hashing with rotating salt and PII detection."""

    def __init__(self, rotation_hours: int = 24) -> None:
        self._rotation_hours = rotation_hours
        self._salt: str = ""
        self._salt_timestamp: float = 0.0
        self._rotate_salt()

    def hash_ip(self, ip: str) -> str:
        """One-way hash of IP address with rotating daily salt.

        Returns a 16-char hex string. The raw IP is never stored.
        """
        self._maybe_rotate_salt()
        raw = f"{ip}:{self._salt}".encode()
        return hashlib.sha256(raw).hexdigest()[:16]

    def _maybe_rotate_salt(self) -> None:
        elapsed = time.monotonic() - self._salt_timestamp
        if elapsed > self._rotation_hours * 3600:
            self._rotate_salt()

    def _rotate_salt(self) -> None:
        now = datetime.now(timezone.utc)
        # Deterministic salt based on date (same salt across restarts within the day)
        day_key = now.strftime("%Y-%m-%d")
        self._salt = hashlib.sha256(
            f"search_angel_salt:{day_key}".encode()
        ).hexdigest()[:32]
        self._salt_timestamp = time.monotonic()

    @staticmethod
    def strip_headers(headers: dict[str, str]) -> dict[str, str]:
        """Remove privacy-sensitive headers."""
        sensitive = {
            "user-agent",
            "referer",
            "cookie",
            "x-forwarded-for",
            "x-real-ip",
            "authorization",
            "x-request-id",
        }
        return {
            k: v for k, v in headers.items()
            if k.lower() not in sensitive
        }
