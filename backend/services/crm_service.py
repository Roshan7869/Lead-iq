"""CRM Service — Phase 8: DB persistence for leads, scores, and outreach"""

from typing import Any


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
