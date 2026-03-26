"""
Configuration — Core Infrastructure (Phase 1)
Reads environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Server
    APP_NAME: str = "LeadIQ"
    DEBUG: bool = False

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379"

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://leadiq:leadiq@localhost:5432/leadiq"

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # Redis Stream names
    STREAM_COLLECTED: str = "lead:collected"
    STREAM_ANALYZED: str = "lead:analyzed"
    STREAM_SCORED: str = "lead:scored"
    STREAM_RANKED: str = "lead:ranked"
    STREAM_OUTREACH: str = "lead:outreach"
    STREAM_CRM_UPDATE: str = "lead:crm_update"
    STREAM_LOGS: str = "system:logs"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
