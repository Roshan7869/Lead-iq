"""
api/routes/leads.py — Lead CRUD and pipeline trigger endpoints.

GET  /api/leads              → list all leads with filtering
PATCH /api/lead/{id}         → update stage / priority / notes
POST /api/run-miner          → trigger collection Celery task
POST /api/run-ai             → trigger analysis Celery task
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from fastapi.security import HTTPBearer

from backend.api.deps import DbSession, CurrentUser
from backend.api.schemas import (
    LeadListResponse,
    LeadOut,
    LeadUpdateRequest,
    LeadUpdateResponse,
    TriggerResponse,
)
from backend.shared.repository import LeadRepo

bearer = HTTPBearer(auto_error=False)

router = APIRouter(prefix="/api", tags=["leads"])


@router.get("/leads", response_model=LeadListResponse)
async def list_leads(
    session: DbSession,
    stage: str | None = Query(None),
    min_score: float = Query(0.0, ge=0.0, le=100.0),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> LeadListResponse:
    repo = LeadRepo(session)
    leads = await repo.list_all(stage=stage, min_score=min_score, limit=limit, offset=offset)
    return LeadListResponse(
        leads=[LeadOut.model_validate(lead) for lead in leads],
        total=len(leads),
        page=offset // limit + 1,
        page_size=limit,
    )


@router.patch("/lead/{lead_id}", response_model=LeadUpdateResponse)
async def update_lead(
    lead_id: str,
    body: LeadUpdateRequest,
    session: DbSession,
) -> LeadUpdateResponse:
    repo = LeadRepo(session)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=422, detail="No fields to update")
    lead = await repo.update_fields(lead_id, updates)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return LeadUpdateResponse(lead=LeadOut.model_validate(lead))


@router.post("/run-miner", response_model=TriggerResponse)
async def trigger_miner(
    user: CurrentUser,
) -> TriggerResponse:
    """Trigger lead collection pipeline. Requires authentication."""
    try:
        from backend.workers.pipeline import collect_and_publish
        task = collect_and_publish.delay()
        return TriggerResponse(
            status="queued",
            message="Collection pipeline started",
            task_id=task.id,
        )
    except Exception:
        # Celery may not be running in dev — fall back to async execution
        import asyncio
        from backend.collectors.reddit import RedditCollector
        from backend.collectors.hn import HNCollector
        from backend.shared.stream import redis_stream

        async def _quick_collect():
            await redis_stream.connect()
            for Collector in (RedditCollector, HNCollector):
                posts = await Collector().collect()  # type: ignore
                for post in posts:
                    await redis_stream.publish("lead:collected", post.to_stream_payload())

        asyncio.create_task(_quick_collect())
        return TriggerResponse(status="running", message="Background collection started (no Celery)")


@router.post("/run-ai", response_model=TriggerResponse)
async def trigger_ai(
    user: CurrentUser,
) -> TriggerResponse:
    """Trigger AI analysis pipeline. Requires authentication."""
    try:
        from backend.workers.pipeline import run_analysis_consumer
        task = run_analysis_consumer.delay()
        return TriggerResponse(
            status="queued",
            message="AI analysis pipeline started",
            task_id=task.id,
        )
    except Exception:
        import asyncio
        from backend.workers.analyzer import run_analyzer
        asyncio.create_task(run_analyzer())
        return TriggerResponse(status="running", message="AI analysis started in background (no Celery)")
