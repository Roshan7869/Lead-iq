"""
workers/dpiit-actor/main.py — DPIIT Startup India Government Registry Collector

Free government API for registered startups in India.
NO competitors have this data moat.

API: https://api.startupindia.gov.in/sih/api/startup/search
Data: Company name, sector, state, city, founded_year, website, stage

Confidence: 0.78 (government registry = verified)
Rate Limit: Unlimited (free public API)
"""
from __future__ import annotations

import asyncio
import structlog
from datetime import datetime
from typing import Any

import httpx

from backend.llm.gemini_service import extract_lead, compute_confidence
from backend.llm.cost_guard import check_budget
from backend.services.dedup_service import find_duplicate, merge_leads

logger = structlog.get_logger()

# DPIIT API endpoint
DPIIT_API = "https://api.startupindia.gov.in/sih/api/startup/search"

# Sector mapping
SECTORS = [
    "Technology",
    "Healthcare",
    "Education",
    "Finance",
    "Agriculture",
    "Manufacturing",
    "E-commerce",
    "Fintech",
    "Edtech",
    "Healthtech",
]


async def fetch_dpiit_startups(
    sector: str | None = None,
    state: str | None = None,
    page: int = 0,
    page_size: int = 100,
) -> list[dict[str, Any]]:
    """
    Fetch startups from DPIIT Startup India registry.

    Args:
        sector: Filter by sector (Technology, Healthcare, etc.)
        state: Filter by state (Madhya Pradesh, Karnataka, etc.)
        page: Page number (0-indexed)
        page_size: Results per page (max 100)

    Returns:
        List of startup dictionaries
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            payload = {
                "sector": sector,
                "state": state,
                "stage": ["Ideation", "Validation", "Early Traction", "Scaling"],
                "pageNo": page,
                "pageSize": page_size,
            }

            response = await client.post(
                DPIIT_API,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()

            data = response.json()
            startups = data.get("data", [])

            logger.info(
                "dpiit_fetch_success",
                sector=sector,
                state=state,
                count=len(startups),
            )

            return startups

        except httpx.HTTPStatusError as exc:
            logger.error("dpiit_http_error", status=exc.response.status_code)
            return []
        except Exception as exc:
            logger.error("dpiit_fetch_error", error=str(exc))
            return []


def transform_dpiit_to_lead(startup: dict[str, Any]) -> dict[str, Any]:
    """
    Transform DPIIT startup data to lead format.

    DPIIT provides structured data - no LLM extraction needed.
    """
    return {
        "company_name": startup.get("name"),
        "industry": startup.get("sector"),
        "location": f"{startup.get('city', '')}, {startup.get('state', 'India')}".strip(", "),
        "founded_year": int(startup.get("inceptionDate", "")[:4]) if startup.get("inceptionDate") else None,
        "website": startup.get("website"),
        "source": "dpiit_startup_india",
        "source_url": f"https://startupindia.gov.in/content/sih/en/search.html?q={startup.get('name', '')}",
        "confidence": 0.78,  # Government registry = reliable
        "intent_signals": ["government_registered"],
        "company_size": None,  # Not provided
        "funding_stage": startup.get("stage"),  # Ideation/Validation/Early Traction/Scaling
        "tech_stack": None,  # Not provided
        "email": None,  # Not provided in API
    }


async def scrape_dpiit(
    sectors: list[str] | None = None,
    states: list[str] | None = None,
    max_pages: int = 10,
) -> list[dict[str, Any]]:
    """
    Main DPIIT collection entry point.

    Args:
        sectors: List of sectors to scrape (None = all)
        states: List of states to scrape (None = all)
        max_pages: Maximum pages per sector/state combination

    Returns:
        List of leads extracted from DPIIT
    """
    sectors = sectors or SECTORS
    states = states or ["Madhya Pradesh", "Karnataka", "Maharashtra", "Tamil Nadu", "Delhi"]

    all_leads = []

    for sector in sectors:
        for state in states:
            page = 0
            consecutive_empty = 0

            while page < max_pages and consecutive_empty < 2:
                startups = await fetch_dpiit_startups(
                    sector=sector,
                    state=state,
                    page=page,
                    page_size=100,
                )

                if not startups:
                    consecutive_empty += 1
                    page += 1
                    continue

                consecutive_empty = 0

                for startup in startups:
                    lead = transform_dpiit_to_lead(startup)
                    all_leads.append(lead)

                page += 1

                # Rate limiting
                await asyncio.sleep(0.5)

    logger.info(
        "dpiit_scrape_complete",
        total_leads=len(all_leads),
        sectors=len(sectors),
        states=len(states),
    )

    return all_leads


async def run_dpiit_actor() -> None:
    """
    Celery task entry point for DPIIT actor.
    """
    leads = await scrape_dpiit()

    # TODO: Save leads to database with deduplication
    # for lead in leads:
    #     existing = await find_duplicate(lead, session)
    #     if existing:
    #         await merge_leads(existing, lead, session)
    #     else:
    #         await save_lead(lead, session)

    logger.info("dpiit_actor_complete", leads_collected=len(leads))


if __name__ == "__main__":
    asyncio.run(run_dpiit_actor())