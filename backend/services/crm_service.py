"""CRM Service — DB persistence for leads, scores, and outreach"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from backend.core.config import settings
from backend.core.redis_client import redis_client


# In-memory store (replace with SQLAlchemy + PostgreSQL for production)
_leads_store: dict[str, dict] = {}


async def get_leads() -> list[dict]:
    return list(_leads_store.values())


async def upsert_lead(lead_data: dict) -> dict:
    lead_id = lead_data["id"]
    _leads_store[lead_id] = lead_data
    return lead_data


async def update_lead(lead_id: str, updates: dict[str, Any]) -> dict | None:
    if lead_id not in _leads_store:
        return None
    _leads_store[lead_id].update(updates)
    return _leads_store[lead_id]


async def delete_lead(lead_id: str) -> bool:
    if lead_id in _leads_store:
        del _leads_store[lead_id]
        return True
    return False


# ── Pipeline → CRM writer ─────────────────────────────────────────────────────

def _get_analysis_float(analysis: dict, key: str, default: float = 0.5) -> float:
    """Safely extract a float from the analysis dict with a fallback default."""
    try:
        return float(analysis.get(key, default))
    except (TypeError, ValueError):
        return default


def _event_to_lead(data: dict) -> dict:
    """Convert a fully-enriched outreach pipeline event into a CRM lead record."""
    lead_id = data.get("id", "unknown")

    analysis: dict = data.get("analysis", {})
    if isinstance(analysis, str):
        analysis = json.loads(analysis)

    outreach: dict = data.get("outreach", {})
    if isinstance(outreach, str):
        outreach = json.loads(outreach)

    intent_raw = _get_analysis_float(analysis, "intent")
    budget_raw = _get_analysis_float(analysis, "budget")
    urgency_raw = _get_analysis_float(analysis, "urgency")
    category: str = analysis.get("category", "general")
    project_size: str = analysis.get("estimated_project_size", "medium")

    intent_score = round(intent_raw * 10, 1)
    founder_score = round((budget_raw + urgency_raw) * 5, 1)
    network_score = round(5 + intent_raw * 3, 1)

    _size_value = {"small": 25000, "medium": 75000, "large": 150000}
    estimated_value = _size_value.get(project_size, 75000)

    _category_company = {
        "saas": "SaaS Startup",
        "fintech": "FinTech Startup",
        "healthtech": "HealthTech Startup",
        "edtech": "EdTech Startup",
        "logistics": "Logistics Company",
        "general": "Tech Startup",
    }

    score = int(data.get("score", 50))
    priority = data.get("priority", "cold")
    strategy = outreach.get("strategy", "direct_pitch")
    source = data.get("source", "reddit")

    return {
        "id": lead_id,
        "name": f"Signal {lead_id[:8]}",
        "company": _category_company.get(category, "Tech Startup"),
        "title": "Founder",
        "stage": "detected",
        "source": source,
        "priority": priority,
        "intentScore": intent_score,
        "founderScore": founder_score,
        "fundingStage": "Pre-Seed",
        "networkScore": network_score,
        "detectedAt": data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "lastActivity": data.get(
            "outreach_generated_at", datetime.now(timezone.utc).isoformat()
        ),
        "signal": data.get("text", ""),
        "estimatedValue": estimated_value,
        "outreachStrategy": strategy,
        "avatar": "🚀",
        "email": "",
        "linkedinUrl": "",
        "score": score,
        "outreachMessages": outreach,
        "aiProvider": data.get("ai_provider", "heuristic"),
        "outreachAngle": analysis.get("outreach_angle", ""),
    }


async def write_pipeline_results(last_id: str = "0") -> int:
    """
    Read enriched leads from the outreach stream (events after *last_id*),
    convert them to CRM lead records, and upsert into the in-memory store.

    Returns the number of leads written.
    """
    events = await redis_client.consume(settings.STREAM_OUTREACH, last_id=last_id)
    for _event_id, data in events:
        lead = _event_to_lead(data)
        await upsert_lead(lead)
    return len(events)
