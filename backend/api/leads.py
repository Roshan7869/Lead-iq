"""
Leads API — Phase 9
GET  /api/leads
POST /api/run-miner
POST /api/run-ai
PATCH /api/lead/{id}
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.workers.collector.worker import run_collector
from backend.workers.analyzer.worker import run_analyzer
from backend.services.crm_service import get_leads, update_lead

router = APIRouter()


class LeadUpdate(BaseModel):
    stage: str | None = None
    priority: str | None = None
    notes: str | None = None


@router.get("/leads")
async def list_leads():
    leads = await get_leads()
    return {"leads": leads}


@router.post("/run-miner")
async def trigger_miner(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_collector)
    return {"status": "running", "message": "Collector worker triggered"}


@router.post("/run-ai")
async def trigger_ai(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_analyzer)
    return {"status": "running", "message": "AI analyzer worker triggered"}


@router.patch("/lead/{lead_id}")
async def patch_lead(lead_id: str, update: LeadUpdate):
    lead = await update_lead(lead_id, update.model_dump(exclude_none=True))
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"lead": lead}
