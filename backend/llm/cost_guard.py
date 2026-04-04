"""
backend/llm/cost_guard.py — Gemini Token Budget Enforcement

Prevents runaway API costs by tracking daily token usage in Redis.
Runs before EVERY Gemini call. Returns False → use fallback HTML parser.

DAILY BUDGET: 2,000,000 tokens (~$0.15/day on Flash-Lite)
REDIS KEY: gemini:tokens:{YYYY-MM-DD}
TTL: 86400 seconds (24 hours)

Usage:
    from backend.llm.cost_guard import check_budget

    if not await check_budget(tokens_requested):
        # Fallback to regex parser (zero LLM cost)
        return await regex_fallback_extract(content)
"""
from __future__ import annotations

import structlog
from datetime import date

import redis.asyncio as aioredis

from backend.shared.config import settings

logger = structlog.get_logger()

# Daily token budget (2M tokens ≈ $0.15/day on Flash-Lite)
DAILY_TOKEN_BUDGET = 2_000_000

# Redis client (singleton)
_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def check_budget(tokens_requested: int) -> bool:
    """
    Check if request fits within daily budget.

    Args:
        tokens_requested: Estimated tokens for this API call

    Returns:
        True if within budget (proceed with call)
        False if budget exceeded (use fallback)

    Side effects:
        - Increments Redis counter if within budget
        - Sets 24-hour TTL on first write of day
    """
    r = await get_redis()
    today = date.today().isoformat()
    key = f"gemini:tokens:{today}"

    try:
        used = int(await r.get(key) or 0)

        if used + tokens_requested > DAILY_TOKEN_BUDGET:
            logger.warning(
                "gemini_budget_exceeded",
                used=used,
                requested=tokens_requested,
                budget=DAILY_TOKEN_BUDGET,
                remaining=max(0, DAILY_TOKEN_BUDGET - used),
            )
            return False

        # Increment and set TTL on first write
        new_value = await r.incrby(key, tokens_requested)
        if new_value == tokens_requested:
            # First write of the day - set 24-hour TTL
            await r.expire(key, 86400)

        logger.debug(
            "gemini_budget_used",
            previous=used,
            added=tokens_requested,
            total=new_value,
            remaining=DAILY_TOKEN_BUDGET - new_value,
        )
        return True

    except Exception as exc:
        logger.error("gemini_budget_check_failed", error=str(exc))
        # On error, allow the call (fail-open for availability)
        return True


async def get_budget_status() -> dict:
    """
    Get current budget status for monitoring.

    Returns:
        dict with used, remaining, budget, percent_used
    """
    r = await get_redis()
    today = date.today().isoformat()
    key = f"gemini:tokens:{today}"

    try:
        used = int(await r.get(key) or 0)
        return {
            "date": today,
            "used": used,
            "remaining": max(0, DAILY_TOKEN_BUDGET - used),
            "budget": DAILY_TOKEN_BUDGET,
            "percent_used": round(used / DAILY_TOKEN_BUDGET * 100, 2),
        }
    except Exception as exc:
        logger.error("gemini_budget_status_failed", error=str(exc))
        return {
            "date": today,
            "used": 0,
            "remaining": DAILY_TOKEN_BUDGET,
            "budget": DAILY_TOKEN_BUDGET,
            "percent_used": 0.0,
            "error": str(exc),
        }


async def reset_budget() -> None:
    """
    Reset today's budget counter (admin only).

    Use with caution - typically only for testing.
    """
    r = await get_redis()
    today = date.today().isoformat()
    key = f"gemini:tokens:{today}"
    await r.delete(key)
    logger.info("gemini_budget_reset", date=today)