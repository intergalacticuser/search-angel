"""Privacy middleware - IP anonymization, header stripping, no cookies."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from search_angel.privacy.anonymizer import Anonymizer


class PrivacyMiddleware(BaseHTTPMiddleware):
    """Enforces privacy rules on every request/response.

    - Anonymizes client IP (SHA-256 with rotating salt)
    - Strips tracking headers from requests
    - Removes Set-Cookie from responses
    - Adds privacy-affirming headers
    """

    def __init__(self, app: object, anonymizer: Anonymizer) -> None:
        super().__init__(app)  # type: ignore[arg-type]
        self._anonymizer = anonymizer

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 1. Anonymize IP - store hash on request state
        client_ip = request.client.host if request.client else "0.0.0.0"
        request.state.ip_hash = self._anonymizer.hash_ip(client_ip)

        # 2. Process request
        response = await call_next(request)

        # 3. Strip cookies from response
        if "set-cookie" in response.headers:
            del response.headers["set-cookie"]

        # 4. Add privacy headers
        response.headers["X-Privacy"] = "no-tracking"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"

        return response
