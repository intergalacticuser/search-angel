"""Privacy audit logging - tracks what data was accessed, never the data itself."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger("search_angel.privacy.audit")


@dataclass
class AuditEvent:
    timestamp: str
    action: str
    ip_hash: str
    resource_type: str
    resource_count: int
    search_mode: str | None = None


class PrivacyAuditor:
    """Logs privacy-relevant events without exposing user data.

    Every log entry contains ONLY:
    - What action was performed
    - IP hash (not raw IP)
    - What type of resource was accessed
    - How many resources were returned
    - Search mode used

    NEVER logged: query text, document content, user identifiers.
    """

    @staticmethod
    def log_search(
        ip_hash: str,
        mode: str,
        result_count: int,
    ) -> None:
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action="search",
            ip_hash=ip_hash,
            resource_type="search_results",
            resource_count=result_count,
            search_mode=mode,
        )
        logger.info(
            "audit_event",
            extra={"audit": event.__dict__},
        )

    @staticmethod
    def log_document_access(
        ip_hash: str,
        doc_count: int = 1,
    ) -> None:
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action="document_access",
            ip_hash=ip_hash,
            resource_type="document",
            resource_count=doc_count,
        )
        logger.info(
            "audit_event",
            extra={"audit": event.__dict__},
        )

    @staticmethod
    def log_ingestion(
        ip_hash: str,
        doc_count: int = 1,
    ) -> None:
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action="ingestion",
            ip_hash=ip_hash,
            resource_type="document",
            resource_count=doc_count,
        )
        logger.info(
            "audit_event",
            extra={"audit": event.__dict__},
        )
