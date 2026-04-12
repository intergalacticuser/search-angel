"""Premium ephemeral session API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from search_angel.auth.tokens import TokenManager
from search_angel.config import get_settings
from search_angel.premium.ephemeral import EphemeralSessionManager

router = APIRouter(prefix="/premium", tags=["premium"])

_session_manager = EphemeralSessionManager()
_token_manager: TokenManager | None = None


def _get_token_mgr() -> TokenManager:
    global _token_manager
    if _token_manager is None:
        settings = get_settings()
        _token_manager = TokenManager(settings.pg_password)
    return _token_manager


async def require_premium(
    authorization: str = Header(..., alias="Authorization"),
) -> dict:
    """Verify user is premium."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    token = authorization[7:]
    tm = _get_token_mgr()
    payload = tm.verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    if payload.get("typ") != "premium":
        raise HTTPException(
            status_code=403,
            detail="Premium account required for ephemeral sessions",
        )

    return payload


class SessionResponse(BaseModel):
    session_id: str
    status: str
    port: int
    message: str


class SessionStatusResponse(BaseModel):
    session_id: str
    status: str
    active_seconds: int
    max_ttl_seconds: int


@router.post("/session/start", response_model=SessionResponse)
async def start_session(
    user: dict = Depends(require_premium),
) -> SessionResponse:
    """Spin up an ephemeral Docker container for a premium user."""
    user_id = user["sub"]

    # Limit: 1 active session per user
    existing = _session_manager.get_user_sessions(user_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail="You already have an active session. End it first.",
        )

    try:
        session = await _session_manager.create_session(user_id)
        return SessionResponse(
            session_id=session.session_id,
            status=session.status,
            port=session.port,
            message="Ephemeral container running. All data will be destroyed when session ends.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create ephemeral session: {e}",
        )


@router.delete("/session/{session_id}")
async def end_session(
    session_id: str,
    user: dict = Depends(require_premium),
) -> dict[str, str]:
    """Destroy an ephemeral container. All data is permanently erased."""
    session = _session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != user["sub"]:
        raise HTTPException(status_code=403, detail="Not your session")

    destroyed = await _session_manager.destroy_session(session_id)
    if destroyed:
        return {
            "status": "destroyed",
            "message": "Container destroyed. All search data has been permanently erased.",
        }
    return {"status": "already_destroyed"}


@router.get("/session/{session_id}/status", response_model=SessionStatusResponse)
async def session_status(
    session_id: str,
    user: dict = Depends(require_premium),
) -> SessionStatusResponse:
    """Check the status of an ephemeral session."""
    session = _session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.user_id != user["sub"]:
        raise HTTPException(status_code=403, detail="Not your session")

    from datetime import datetime, timezone

    elapsed = int((datetime.now(timezone.utc) - session.created_at).total_seconds())

    return SessionStatusResponse(
        session_id=session.session_id,
        status=session.status,
        active_seconds=elapsed,
        max_ttl_seconds=session.max_ttl_seconds,
    )
