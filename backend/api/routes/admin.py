"""
api/routes/admin.py — Admin endpoints: feedback, lead deletion, quota stats.

POST  /api/admin/feedback        → submit lead quality feedback  [auth required]
GET   /api/admin/feedback/{id}   → list feedback for a lead      [auth required]
DELETE /api/admin/lead/{id}      → soft-delete a lead            [auth required]
GET   /api/admin/quota           → Gemini API quota usage today  [auth required]
GET   /api/admin/deploy-check    → verify deployment readiness   [auth required]
"""
from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.api.deps import DbSession, CurrentUser
from backend.api.schemas import FeedbackRequest, FeedbackResponse
from backend.shared.repository import FeedbackRepo, LeadRepo, QuotaRepo, ProfileRepo
from backend.shared.config import settings
from backend.shared.stream import redis_stream

from backend.llm.circuit_breaker import get_state

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    body: FeedbackRequest,
    session: DbSession,
    _user: CurrentUser,                          # ← requires valid JWT
) -> FeedbackResponse:
    lead_repo = LeadRepo(session)
    lead = await lead_repo.get(body.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    fb_repo = FeedbackRepo(session)
    fb = await fb_repo.create(
        lead_id=body.lead_id,
        rating=body.rating,
        label=body.label,
        reviewer=body.reviewer,
    )

    # ── Feedback learning: update profile scoring weights ────────────────────
    try:
        from backend.services.personalization import record_feedback
        profile_repo = ProfileRepo(session)
        profile = await profile_repo.get_active()
        if profile:
            new_adj = record_feedback(
                dict(profile.feedback_adjustments or {}),
                industry=lead.industry,
                intent=lead.intent or "other",
                rating=body.rating,
            )
            await profile_repo.update_feedback_adjustments(new_adj)
    except Exception:
        pass  # learning is best-effort; never fail the feedback write

    return FeedbackResponse.model_validate(fb)


@router.get("/feedback/{lead_id}", response_model=list[FeedbackResponse])
async def list_feedback(
    lead_id: str,
    session: DbSession,
    _user: CurrentUser,
) -> list[FeedbackResponse]:
    fb_repo = FeedbackRepo(session)
    feedbacks = await fb_repo.list_by_lead(lead_id)
    return [FeedbackResponse.model_validate(fb) for fb in feedbacks]


@router.delete("/lead/{lead_id}", status_code=204, response_class=Response)
async def delete_lead(
    lead_id: str,
    session: DbSession,
    _user: CurrentUser,
) -> Response:
    repo = LeadRepo(session)
    lead = await repo.update_fields(lead_id, {"stage": "closed"})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return Response(status_code=204)


@router.get("/quota")
async def get_quota(
    session: DbSession,
    _user: CurrentUser,
) -> dict:
    repo = QuotaRepo(session)
    today = date.today().isoformat()
    usage = await repo.get_daily_total(model=settings.GEMINI_MODEL, day=today)
    return {
        "date": today,
        "model": settings.GEMINI_MODEL,
        "tokens_used": usage.tokens_used if usage else 0,
        "requests_count": usage.requests_count if usage else 0,
    }


@router.get("/deploy-check")
async def deploy_check(
    session: DbSession,
    _user: CurrentUser,
) -> dict[str, Any]:
    """
    Deployment readiness check.

    Verifies:
        - Database connection
        - Redis connectivity
        - Gemini API key configured
        - Required models exist
    """
    result: dict[str, Any] = {
        "status": "healthy",
        "checks": {},
        "errors": [],
    }

    # Check database
    try:
        from sqlalchemy import text
        await session.execute(text("SELECT 1"))
        result["checks"]["database"] = "ok"
    except Exception as e:
        result["checks"]["database"] = "error"
        result["errors"].append(f"Database: {str(e)}")
        result["status"] = "unhealthy"

    # Check Redis
    try:
        r = redis_stream._r if redis_stream._r else None
        if r:
            await r.ping()
            result["checks"]["redis"] = "ok"
        else:
            result["checks"]["redis"] = "not_connected"
    except Exception as e:
        result["checks"]["redis"] = "error"
        result["errors"].append(f"Redis: {str(e)}")
        result["status"] = "unhealthy"

    # Check Gemini API key
    if settings.GEMINI_API_KEY:
        result["checks"]["gemini_api"] = "configured"
    else:
        result["checks"]["gemini_api"] = "missing"
        result["errors"].append("GEMINI_API_KEY not set")
        result["status"] = "unhealthy"

    # Check database tables exist
    try:
        from sqlalchemy import text
        tables = ["leads", "icps", "lead_events", "profiles"]
        for table in tables:
            result = await session.execute(text(
                f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}')"
            ))
            exists = result.scalar()
            result["checks"][f"table_{table}"] = "ok" if exists else "missing"
    except Exception as e:
        result["checks"]["table_check"] = "error"
        result["errors"].append(f"Table check: {str(e)}")

    # Check migration status
    try:
        from sqlalchemy import text
        result = await session.execute(text(
            "SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1"
        ))
        row = result.fetchone()
        if row:
            result["checks"]["migration"] = row[0]
        else:
            result["checks"]["migration"] = "no_migrations"
    except Exception as e:
        result["checks"]["migration"] = "error"
        result["errors"].append(f"Migration check: {str(e)}")

    return result


@router.get("/dlq")
async def get_dlq_dashboard():
    """DLQ inspection endpoint"""
    from redis import Redis
    r = Redis.from_url("redis://localhost:6379", decode_responses=True)

    dlq_stats = {
        "pending": r.xlen("lead:dlq") if r else 0,
        "permanent_failed": r.xlen("lead:dlq:perm") if r else 0,
    }

    circuit_status = {
        "gemini": get_state("gemini").value,
    }

    return {"dlq_stats": dlq_stats, "circuit_breakers": circuit_status}

