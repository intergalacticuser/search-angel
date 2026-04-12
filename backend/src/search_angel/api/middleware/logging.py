"""Structured logging middleware - NEVER logs query content."""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("search_angel.access")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Logs request metadata in structured format.

    PRIVACY RULES:
    - NEVER log query text, request body, or response body
    - NEVER log raw IP addresses
    - ONLY log: method, path, status, duration, ip_hash, request_id
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        start = time.monotonic()

        response = await call_next(request)

        duration_ms = round((time.monotonic() - start) * 1000, 2)
        ip_hash = getattr(request.state, "ip_hash", "unknown")

        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "ip_hash": ip_hash,
            },
        )

        response.headers["X-Request-ID"] = request_id
        return response
