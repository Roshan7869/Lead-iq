"""
collectors/stackoverflow.py — Stack Overflow Jobs & Questions collector.

Surfaces two types of signals:
  1. Questions tagged with tools/technologies (buying intent: "how do I integrate X?")
  2. Job listings from Stack Overflow Jobs API (hiring signals)

Uses the public Stack Exchange API v2.3 (no auth needed for read-only).
Rate limit: 300 requests/day unauthenticated, 10,000 with key.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from backend.collectors.base import BaseCollector, RawPost

logger = logging.getLogger(__name__)

_SO_API_BASE = "https://api.stackexchange.com/2.3"

# Tags that signal B2B tech buying intent
_B2B_SIGNAL_TAGS = [
    "saas", "crm", "erp", "api-integration", "webhook",
    "enterprise", "oauth", "stripe", "twilio", "sendgrid",
    "aws", "gcp", "azure", "kubernetes", "docker",
    "postgresql", "redis", "elasticsearch", "kafka",
]

# Question title patterns indicating buying/evaluation intent
_BUYING_PATTERNS = [
    "best way to", "how to choose", "which tool", "recommend",
    "alternative to", "instead of", "compare", "migrate from",
    "integrate with", "looking for", "what is the best",
]

_HIRING_TAGS = [
    "python", "javascript", "typescript", "react", "fastapi",
    "rust", "golang", "java", "kubernetes", "machine-learning",
]


class StackOverflowCollector(BaseCollector):
    """
    Collects Stack Overflow questions and job signals.
    Focuses on:
      - Questions with buying/tool-evaluation intent
      - Hiring signals (for hiring/job_search modes)
    """

    source = "stackoverflow"

    def __init__(
        self,
        mode: str = "b2b_sales",
        max_items: int = 40,
        days_back: int = 2,
        api_key: str = "",
    ) -> None:
        self._mode      = mode
        self._max_items = max_items
        self._days_back = days_back
        self._api_key   = api_key

    async def collect(self) -> list[RawPost]:
        posts: list[RawPost] = []
        async with httpx.AsyncClient(timeout=20.0) as client:
            if self._mode in ("hiring", "job_search"):
                posts.extend(await self._collect_hiring_questions(client))
            else:
                posts.extend(await self._collect_b2b_questions(client))
        return posts[: self._max_items]

    async def _collect_b2b_questions(self, client: httpx.AsyncClient) -> list[RawPost]:
        """Fetch recent questions with B2B-signal tags."""
        posts: list[RawPost] = []
        cutoff_ts = int((datetime.now(UTC) - timedelta(days=self._days_back)).timestamp())

        tags_subset = _B2B_SIGNAL_TAGS[:5]  # limit to keep under rate limit

        for tag in tags_subset:
            try:
                params: dict[str, Any] = {
                    "site":     "stackoverflow",
                    "tagged":   tag,
                    "sort":     "creation",
                    "order":    "desc",
                    "fromdate": cutoff_ts,
                    "filter":   "withbody",
                    "pagesize": 10,
                }
                if self._api_key:
                    params["key"] = self._api_key

                resp = await client.get(
                    f"{_SO_API_BASE}/questions",
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()

                for item in data.get("items", []):
                    title = item.get("title", "")
                    body  = item.get("body", "") or ""

                    # Filter to buying-signal questions
                    combined = f"{title} {body}".lower()
                    is_signal = any(p in combined for p in _BUYING_PATTERNS)
                    if not is_signal:
                        continue

                    created_at = datetime.fromtimestamp(
                        item.get("creation_date", datetime.now(UTC).timestamp()),
                        tz=UTC,
                    )
                    posts.append(RawPost(
                        source=self.source,
                        external_id=str(item["question_id"]),
                        url=item.get("link", ""),
                        title=title,
                        body=body[:2000],  # cap body length
                        author=item.get("owner", {}).get("display_name", ""),
                        score=item.get("score", 0),
                        raw_meta={
                            "tags":           item.get("tags", []),
                            "answer_count":   item.get("answer_count", 0),
                            "view_count":     item.get("view_count", 0),
                            "is_answered":    item.get("is_answered", False),
                        },
                        collected_at=created_at,
                    ))

            except Exception as exc:
                logger.warning("StackOverflow B2B query tag=%s failed: %s", tag, exc)

        return posts

    async def _collect_hiring_questions(self, client: httpx.AsyncClient) -> list[RawPost]:
        """Fetch hiring-related questions (for hiring/job_search modes)."""
        posts: list[RawPost] = []
        cutoff_ts = int((datetime.now(UTC) - timedelta(days=self._days_back)).timestamp())

        try:
            params: dict[str, Any] = {
                "site":     "softwareengineering.stackexchange.com",
                "tagged":   "career",
                "sort":     "creation",
                "order":    "desc",
                "fromdate": cutoff_ts,
                "filter":   "withbody",
                "pagesize": 20,
            }
            if self._api_key:
                params["key"] = self._api_key

            resp = await client.get(f"{_SO_API_BASE}/questions", params=params)
            # Non-critical: don't raise on error
            if resp.is_success:
                data = resp.json()
                for item in data.get("items", []):
                    created_at = datetime.fromtimestamp(
                        item.get("creation_date", datetime.now(UTC).timestamp()),
                        tz=UTC,
                    )
                    posts.append(RawPost(
                        source=self.source,
                        external_id=f"se_{item['question_id']}",
                        url=item.get("link", ""),
                        title=item.get("title", ""),
                        body=(item.get("body", "") or "")[:2000],
                        author=item.get("owner", {}).get("display_name", ""),
                        score=item.get("score", 0),
                        raw_meta={"tags": item.get("tags", [])},
                        collected_at=created_at,
                    ))
        except Exception as exc:
            logger.warning("StackOverflow hiring query failed: %s", exc)

        return posts
