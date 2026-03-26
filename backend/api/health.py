"""
Health check API — Phase 1
GET /api/health
"""

from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "LeadIQ Backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
