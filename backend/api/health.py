"""Health check API.
GET /api/health
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "service": "LeadIQ API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0.0",
    }
