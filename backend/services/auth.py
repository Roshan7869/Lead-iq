"""
services/auth.py — JWT token lifecycle management.

Provides:
  - create_access_token / create_refresh_token
  - verify_token       — decode and return the subject claim
  - verify_credentials — constant-time credential comparison (no timing attacks)

Credentials are configured via env vars ADMIN_USERNAME / ADMIN_PASSWORD.
For multi-user setups, extend verify_credentials to query a users table.
"""
from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from backend.shared.config import settings

# ── Token Blocklist (in-memory; use Redis for multi-instance) ─────────────────
# Tokens added here are revoked immediately. In production, back this with Redis
# or a shared store so all instances respect revocations.
_token_blocklist: set[str] = set()
_BLOCKLIST_MAX_SIZE = 10_000  # safety cap to prevent unbounded growth


def revoke_token(token: str) -> None:
    """Add a token to the revocation list. Call on logout."""
    if not token:
        return
    _token_blocklist.add(token)
    # crude TTL: if list grows too large, drop oldest half (by arbitrary order)
    if len(_token_blocklist) > _BLOCKLIST_MAX_SIZE:
        half = sorted(_token_blocklist)[:_BLOCKLIST_MAX_SIZE // 2]
        _token_blocklist.difference_update(half)


def is_token_revoked(token: str) -> bool:
    return token in _token_blocklist


# ── Token creation ────────────────────────────────────────────────────────────

def create_access_token(username: str) -> str:
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": username, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(username: str) -> str:
    expire = datetime.now(UTC) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {"sub": username, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# ── Token verification ────────────────────────────────────────────────────────

def verify_token(token: str, expected_type: str = "access") -> str:
    """Decode JWT and return the username (sub). Raises ValueError on failure."""
    if expected_type == "refresh" and is_token_revoked(token):
        raise ValueError("Refresh token has been revoked")

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

    sub = payload.get("sub")
    if not sub:
        raise ValueError("Token missing subject claim")

    tok_type = payload.get("type", "access")
    if tok_type != expected_type:
        raise ValueError(f"Expected {expected_type} token, got {tok_type}")

    return str(sub)


# ── Credential verification ───────────────────────────────────────────────────

def verify_credentials(username: str, password: str) -> bool:
    """Constant-time credential check — safe against timing attacks."""
    valid_user = secrets.compare_digest(
        username.encode(), settings.ADMIN_USERNAME.encode()
    )
    valid_pass = secrets.compare_digest(
        password.encode(), settings.ADMIN_PASSWORD.encode()
    )
    return valid_user and valid_pass
