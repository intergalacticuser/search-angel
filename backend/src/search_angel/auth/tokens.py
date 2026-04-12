"""Stateless JWT token management - privacy-preserving."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode


class TokenManager:
    """Simple HMAC-based tokens. No external JWT library needed.

    Tokens contain: user_id, account_type, expiry. Nothing else.
    No email, no name, no PII.
    """

    def __init__(self, secret: str, ttl_hours: int = 24) -> None:
        self._secret = secret.encode()
        self._ttl = ttl_hours * 3600

    def create_token(self, user_id: str, account_type: str) -> str:
        payload = {
            "sub": user_id,
            "typ": account_type,
            "exp": int(time.time()) + self._ttl,
        }
        data = urlsafe_b64encode(json.dumps(payload).encode()).decode()
        sig = hmac.new(self._secret, data.encode(), hashlib.sha256).hexdigest()
        return f"{data}.{sig}"

    def verify_token(self, token: str) -> dict | None:
        try:
            data, sig = token.rsplit(".", 1)
            expected_sig = hmac.new(
                self._secret, data.encode(), hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(sig, expected_sig):
                return None
            payload = json.loads(urlsafe_b64decode(data))
            if payload.get("exp", 0) < time.time():
                return None
            return payload
        except Exception:
            return None

    @staticmethod
    def hash_email(email: str) -> str:
        return hashlib.sha256(email.lower().strip().encode()).hexdigest()

    @staticmethod
    def hash_password(password: str) -> str:
        # In production, use bcrypt. This is a simple hash for the initial implementation.
        salt = "search_angel_pw_salt"
        return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
