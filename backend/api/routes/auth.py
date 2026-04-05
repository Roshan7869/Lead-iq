"""
api/routes/auth.py — Authentication endpoints.

POST /api/auth/login    → exchange credentials for JWT pair
POST /api/auth/refresh  → exchange refresh token for new access token
GET  /api/auth/me       → verify token + return current username
POST /api/auth/logout   → client-side logout hint (no server state)
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.services.auth import (
    create_access_token,
    create_refresh_token,
    verify_credentials,
    verify_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ── Request / Response schemas ────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 60 * 8   # seconds — informational


class RefreshRequest(BaseModel):
    refresh_token: str


class MeResponse(BaseModel):
    username: str
    authenticated: bool


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """
    Exchange username + password for a JWT access + refresh token pair.
    Rate-limited by slowapi at the app level (10/minute).
    """
    if not verify_credentials(body.username, body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(
        access_token  = create_access_token(body.username),
        refresh_token = create_refresh_token(body.username),
        expires_in    = 60 * 8,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest) -> TokenResponse:
    """Exchange a valid refresh token for a new access + refresh token pair."""
    try:
        username = verify_token(body.refresh_token, expected_type="refresh")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return TokenResponse(
        access_token  = create_access_token(username),
        refresh_token = create_refresh_token(username),
        expires_in    = 60 * 8,
    )


@router.get("/me", response_model=MeResponse)
async def me(token: str = "") -> MeResponse:
    """
    Verify an access token and return the username.
    Token is passed as query param ?token=<jwt> (browser-friendly) or
    read from the Authorization header by the dependency in protected routes.
    """
    if not token:
        return MeResponse(username="", authenticated=False)
    try:
        username = verify_token(token, expected_type="access")
        return MeResponse(username=username, authenticated=True)
    except ValueError:
        return MeResponse(username="", authenticated=False)


@router.post("/logout")
async def logout() -> dict:
    """
    Stateless JWT — real logout happens client-side by deleting stored tokens.
    This endpoint exists for audit logging purposes.
    """
    return {"detail": "Logged out. Delete stored tokens client-side."}
