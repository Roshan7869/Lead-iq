"""
Ranking Engine Worker — Phase 6
Consumes lead:scored, categorises leads, publishes to lead:ranked.

Rules:
  > 80  → hot
  60–80 → warm
  < 60  → cold
"""

from datetime import datetime, timezone

from backend.core.config import settings
from backend.core.redis_client import redis_client


def classify_priority(score: int) -> str:
    if score > 80:
        return "hot"
    elif score >= 60:
        return "warm"
    return "cold"


async def run_ranking(last_id: str = "0") -> list[str]:
    """
    Consume events from lead:scored, classify priority, publish to lead:ranked.
    Returns list of published event IDs.
    """
    events = await redis_client.consume(settings.STREAM_SCORED, last_id=last_id)
    published: list[str] = []

    for event_id, data in events:
        score = int(data.get("score", 0))
        priority = classify_priority(score)

        enriched = {
            **data,
            "priority": priority,
            "rank_label": f"{priority.upper()} — score {score}",
            "ranked_at": datetime.now(timezone.utc).isoformat(),
            "source_event_id": event_id,
        }
        new_id = await redis_client.publish(settings.STREAM_RANKED, enriched)
        published.append(new_id)

    return published
