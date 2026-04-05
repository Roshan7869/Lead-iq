"""
shared/config.py — Pydantic BaseSettings for all environment variables.
Single source of truth — import `settings` everywhere, never os.getenv directly.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Server ────────────────────────────────────────────────────────────────
    APP_NAME: str = "LeadIQ"
    DEBUG: bool = False
    SECRET_KEY: str  # Must be set via environment variable in production

    # ── PostgreSQL ────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://leadiq:leadiq@localhost:5432/leadiq"

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # ── Gemini / GCP ─────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GCP_PROJECT_ID: str = ""
    GCP_LOCATION: str = "us-central1"

    # ── Redis Stream names ────────────────────────────────────────────────────
    STREAM_COLLECTED: str = "lead:collected"
    STREAM_ANALYZED: str = "lead:analyzed"
    STREAM_SCORED: str = "lead:scored"
    STREAM_RANKED: str = "lead:ranked"
    STREAM_OUTREACH: str = "lead:outreach"
    STREAM_CRM_UPDATE: str = "lead:crm_update"
    STREAM_LOGS: str = "system:logs"

    # ── Celery ────────────────────────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── External API Keys ─────────────────────────────────────────────────────
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "LeadIQ/1.0"
    TWITTER_BEARER_TOKEN: str = ""
    GITHUB_TOKEN: str = ""

    # ── Enrichment API Keys ───────────────────────────────────────────────────
    HUNTER_API_KEY: str = ""       # Hunter.io email finder
    CLEARBIT_API_KEY: str = ""     # Clearbit company enrichment

    # ── Telegram ──────────────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str = ""       # For outbound notifications (bot API)
    TELEGRAM_CHAT_ID: str = ""         # For outbound notifications
    TELEGRAM_API_ID: str = ""          # For inbound scraping (my.telegram.org)
    TELEGRAM_API_HASH: str = ""        # For inbound scraping (my.telegram.org)

    # ── Auth (JWT) ────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str  # Must be set via environment variable in production
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480       # 8 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str  # Must be set via environment variable in production

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_DEFAULT: str = "120/minute"
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_EXPENSIVE: str = "5/minute"

    # ── MCP ─────────────────────────────────────────────────────────────────
    MCP_API_KEY: str = ""  # Optional: protect /mcp endpoint; empty = dev mode (no auth)

    # ── Observability ─────────────────────────────────────────────────────────
    SENTRY_DSN: str = ""
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True

    # ── Helper Methods ─────────────────────────────────────────────────────────
    def get_timezone(self) -> timezone:
        """Get the configured timezone (default UTC)."""
        return timezone.utc

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Compatibility shim for Pydantic v1/v2 dump."""
        return dict(self)


settings = Settings()
