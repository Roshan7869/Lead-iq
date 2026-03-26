"""
Scoring Engine Worker — Phase 5
Consumes lead:analyzed, computes deterministic score, publishes to lead:scored.

Score formula:
  score = 0.25*intent + 0.20*authority + 0.15*urgency + 0.15*budget
        + 0.10*engagement + 0.10*network + 0.05*history
  (all inputs are 0–1; output is 0–100)
"""

import json
from datetime import datetime, timezone

from backend.core.config import settings
from backend.core.redis_client import redis_client


def compute_score(
    intent: float,
    authority: float = 0.5,
    urgency: float = 0.5,
    budget: float = 0.5,
    engagement: float = 0.5,
    network: float = 0.5,
    history: float = 0.5,
) -> tuple[int, str]:
    """
    Deterministic scoring model.
    Returns (score 0-100, priority: hot|warm|cold).
    """
    raw = (
        0.25 * intent
        + 0.20 * authority
        + 0.15 * urgency
        + 0.15 * budget
        + 0.10 * engagement
        + 0.10 * network
        + 0.05 * history
    )
    score = round(raw * 100)

    if score > 80:
        priority = "hot"
    elif score >= 60:
        priority = "warm"
    else:
        priority = "cold"

    return score, priority


async def run_scoring(last_id: str = "0") -> list[str]:
    """
    Consume events from lead:analyzed, score each, publish to lead:scored.
    Returns list of published event IDs.
    """
    events = await redis_client.consume(settings.STREAM_ANALYZED, last_id=last_id)
    published: list[str] = []

    for event_id, data in events:
        analysis = data.get("analysis", {})
        if isinstance(analysis, str):
            analysis = json.loads(analysis)

        score, priority = compute_score(
            intent=analysis.get("intent", 0.5),
            urgency=analysis.get("urgency", 0.5),
            budget=analysis.get("budget", 0.5),
        )

        enriched = {
            **data,
            "score": score,
            "priority": priority,
            "scored_at": datetime.now(timezone.utc).isoformat(),
            "source_event_id": event_id,
        }
        new_id = await redis_client.publish(settings.STREAM_SCORED, enriched)
        published.append(new_id)

    return published
