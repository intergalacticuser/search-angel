"""Authentication API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from search_angel.api.dependencies import get_db
from search_angel.auth.models import User
from search_angel.auth.tokens import TokenManager
from search_angel.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

_token_manager: TokenManager | None = None


def _get_token_manager() -> TokenManager:
    global _token_manager
    if _token_manager is None:
        settings = get_settings()
        secret = settings.pg_password  # Use a config-derived secret
        _token_manager = TokenManager(secret)
    return _token_manager


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    account_type: str
    message: str


@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    tm = _get_token_manager()

    email_hash = tm.hash_email(request.email)
    password_hash = tm.hash_password(request.password)

    # Check if user already exists
    stmt = select(User).where(User.email_hash == email_hash)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Account already exists")

    # Create user - we store email HASH, never the actual email
    user = User(
        email_hash=email_hash,
        password_hash=password_hash,
        account_type="free",
    )
    db.add(user)
    await db.flush()

    token = tm.create_token(str(user.id), user.account_type)

    return AuthResponse(
        token=token,
        account_type=user.account_type,
        message="Account created. Your email is stored as a hash - we never see it.",
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    tm = _get_token_manager()

    email_hash = tm.hash_email(request.email)
    password_hash = tm.hash_password(request.password)

    stmt = select(User).where(
        User.email_hash == email_hash,
        User.password_hash == password_hash,
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = tm.create_token(str(user.id), user.account_type)

    return AuthResponse(
        token=token,
        account_type=user.account_type,
        message="Logged in. No session data is stored server-side.",
    )
