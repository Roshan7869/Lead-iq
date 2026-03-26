"""
Collector Worker — Phase 3
Generates demand signals and publishes them to lead:collected stream.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from random import choice, uniform

from backend.core.config import settings
from backend.core.redis_client import redis_client

DEMO_SIGNALS = [
    "Looking for SaaS developer for MVP — budget allocated, 6 weeks timeline",
    "Need React agency for dashboard redesign — urgent, pre-seed funded",
    "Building fintech app — hiring dev team, Series A",
    "Healthcare platform rebuild — modern stack, good budget",
    "EdTech startup needs full-stack team — LMS, payments, live classes",
    "Logistics dashboard ASAP — internal team overloaded",
]

SOURCES = ["reddit", "linkedin", "x", "yc", "indie_hackers"]


async def run_collector(count: int = 5, delay_seconds: float = 0.5) -> list[str]:
    """
    Simulate demand signal collection.
    Publishes `count` events to the `lead:collected` stream.
    Returns list of published event IDs.
    """
    event_ids: list[str] = []
    for _ in range(count):
        event = {
            "id": str(uuid.uuid4()),
            "text": choice(DEMO_SIGNALS),
            "source": choice(SOURCES),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "intent_score": round(uniform(4.0, 10.0), 1),
        }
        event_id = await redis_client.publish(settings.STREAM_COLLECTED, event)
        event_ids.append(event_id)
        await asyncio.sleep(delay_seconds)
    return event_ids
