"""
Outreach Generator Worker — Phase 7
Consumes lead:ranked, generates personalised outreach messages, publishes to lead:outreach.

Logic:
  networkScore > 6 → warm_intro
  else             → direct_pitch
"""

import json
from datetime import datetime, timezone

from backend.core.config import settings
from backend.core.redis_client import redis_client


def generate_outreach(data: dict) -> dict:
    """
    Generate personalised outreach for a ranked lead.
    Returns { linkedin, email, whatsapp }.
    """
    name = data.get("id", "Founder")
    score = data.get("score", 50)
    network_score = float(data.get("network_score", 5))
    strategy = "warm_intro" if network_score > 6 else "direct_pitch"
    signal = data.get("text", "your project")

    if strategy == "warm_intro":
        linkedin = (
            f"Hi! I noticed you're looking for development help ({signal[:60]}…). "
            f"A mutual connection suggested I reach out — happy to help!"
        )
        email = (
            f"Subject: Intro via mutual connection — LeadIQ\n\n"
            f"Hi,\n\nA mutual contact thought we should connect regarding your development needs. "
            f"We specialise in exactly what you're building. Worth a quick call?\n\nBest,\nLeadIQ Team"
        )
        whatsapp = f"Hi! Saw you're looking for dev help. Mutual connection suggested I reach out. Open for a quick chat? 🚀"
    else:
        linkedin = (
            f"Hi! I came across your post about needing a dev team ({signal[:60]}…). "
            f"We've helped 20+ founders in similar situations. Can I share some examples?"
        )
        email = (
            f"Subject: Dev help for your project — LeadIQ\n\n"
            f"Hi,\n\nI saw you're looking for development expertise. We specialise in rapid MVP delivery for founders. "
            f"Would love to show you what we've built. Free 15-min call?\n\nBest,\nLeadIQ Team"
        )
        whatsapp = f"Hi! Noticed you need dev help. We build MVPs fast for founders — can I share a quick case study? 👋"

    return {"linkedin": linkedin, "email": email, "whatsapp": whatsapp, "strategy": strategy}


async def run_outreach(last_id: str = "0") -> list[str]:
    """
    Consume events from lead:ranked, generate outreach, publish to lead:outreach.
    Returns list of published event IDs.
    """
    events = await redis_client.consume(settings.STREAM_RANKED, last_id=last_id)
    published: list[str] = []

    for event_id, data in events:
        outreach = generate_outreach(data)

        enriched = {
            **data,
            "outreach": json.dumps(outreach),
            "outreach_generated_at": datetime.now(timezone.utc).isoformat(),
            "source_event_id": event_id,
        }
        new_id = await redis_client.publish(settings.STREAM_OUTREACH, enriched)
        published.append(new_id)

    return published
