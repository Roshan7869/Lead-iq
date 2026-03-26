"""
AI Analyzer Worker — Phase 4
Consumes lead:collected, extracts structured intelligence, publishes to lead:analyzed.
"""

import json
from datetime import datetime, timezone
from random import uniform

from backend.core.config import settings
from backend.core.redis_client import redis_client


async def analyze_signal(text: str) -> dict:
    """
    Convert raw signal text into structured intelligence.
    Uses deterministic heuristics (LLM integration to be added).
    Output schema: { intent, urgency, budget, category }
    """
    lower = text.lower()
    intent = round(uniform(0.6, 1.0) if any(w in lower for w in ["need", "looking", "hire", "build"]) else uniform(0.3, 0.6), 2)
    urgency = round(uniform(0.5, 1.0) if any(w in lower for w in ["asap", "urgent", "6 weeks", "immediately"]) else uniform(0.2, 0.5), 2)
    budget = round(uniform(0.5, 0.9) if any(w in lower for w in ["budget", "funded", "series", "million", "$"]) else uniform(0.2, 0.5), 2)
    category = "saas" if "saas" in lower else "fintech" if "fintech" in lower else "healthtech" if "health" in lower else "general"

    return {
        "intent": intent,
        "urgency": urgency,
        "budget": budget,
        "category": category,
    }


async def run_analyzer(last_id: str = "0") -> list[str]:
    """
    Consume events from lead:collected, analyze each, publish to lead:analyzed.
    Returns list of published event IDs.
    """
    events = await redis_client.consume(settings.STREAM_COLLECTED, last_id=last_id)
    published: list[str] = []

    for event_id, data in events:
        text = data.get("text", "")
        analysis = await analyze_signal(text)

        enriched = {
            **data,
            "analysis": json.dumps(analysis),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "source_event_id": event_id,
        }
        new_id = await redis_client.publish(settings.STREAM_ANALYZED, enriched)
        published.append(new_id)

    return published
