"""Phantom Mode - Ephemeral container API. No auth required."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from search_angel.api.dependencies import get_ip_hash
from search_angel.premium.phantom import PhantomManager

router = APIRouter(prefix="/phantom", tags=["phantom"])

_manager = PhantomManager()


class PhantomStartResponse(BaseModel):
    session_id: str
    status: str
    port: int
    ttl_seconds: int
    message: str


class PhantomSearchRequest(BaseModel):
    session_id: str
    query: str = Field(..., min_length=1, max_length=2000)
    mode: str = "standard"
    limit: int = Field(default=20, ge=1, le=100)


class PhantomStatusResponse(BaseModel):
    session_id: str
    status: str
    active_seconds: int
    search_count: int
    ttl_seconds: int


@router.post("/start", response_model=PhantomStartResponse)
async def start_phantom(
    ip_hash: str = Depends(get_ip_hash),
) -> PhantomStartResponse:
    """Start a Phantom Mode session.

    Creates an ephemeral Docker container for your search session.
    All data exists only inside the container. When you end the session
    or it times out (30min), the container is permanently destroyed.
    Zero trace remains.
    """
    try:
        session = await _manager.create(ip_hash)
        return PhantomStartResponse(
            session_id=session.session_id,
            status=session.status,
            port=session.port,
            ttl_seconds=1800,
            message="Phantom container active. All searches happen inside an isolated container that will be destroyed when you're done.",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start phantom: {e}")


@router.post("/search")
async def phantom_search(
    request: PhantomSearchRequest,
    ip_hash: str = Depends(get_ip_hash),
) -> dict:
    """Search through a Phantom Mode container.

    Routes the search to the ephemeral container, not the main instance.
    """
    session = _manager.get_session(request.session_id)
    if not session or session.status != "running":
        raise HTTPException(status_code=404, detail="Phantom session not found or not running")

    # Verify IP owns this session
    if session.ip_hash != ip_hash:
        raise HTTPException(status_code=403, detail="Not your phantom session")

    # Proxy the search to the ephemeral container
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"http://localhost:{session.port}/api/v1/search",
                json={
                    "query": request.query,
                    "mode": request.mode,
                    "limit": request.limit,
                },
            )
            session.search_count += 1
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Phantom container error: {e}")


@router.get("/status/{session_id}", response_model=PhantomStatusResponse)
async def phantom_status(
    session_id: str,
    ip_hash: str = Depends(get_ip_hash),
) -> PhantomStatusResponse:
    """Check phantom session status."""
    session = _manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    import time
    elapsed = int(time.time() - session.created_at)
    remaining = max(0, 1800 - elapsed)

    return PhantomStatusResponse(
        session_id=session.session_id,
        status=session.status,
        active_seconds=elapsed,
        search_count=session.search_count,
        ttl_seconds=remaining,
    )


@router.delete("/end/{session_id}")
async def end_phantom(
    session_id: str,
    ip_hash: str = Depends(get_ip_hash),
) -> dict:
    """End a Phantom Mode session. Container is permanently destroyed."""
    session = _manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.ip_hash != ip_hash:
        raise HTTPException(status_code=403, detail="Not your session")

    destroyed = await _manager.destroy(session_id)
    return {
        "status": "destroyed" if destroyed else "not_found",
        "message": "Container destroyed. All search data permanently erased. Zero trace.",
    }
