"""
workers/internshala-actor/main.py — Internshala Internship Listings Collector Actor.

Uses Crawlee BeautifulSoupCrawler to scrape Internshala.com internship
listings by category. Extracts internship details from server-rendered HTML,
transforms into pipeline stream payloads, and enqueues to Redis stream
lead:collected.

QUOTA: 1000 requests/day
"""
from __future__ import annotations

import asyncio
import os
import re
import sys
import hashlib
import structlog
from datetime import date, datetime
from typing import Any

import redis.asyncio as aioredis

# Ensure project root is on sys.path so backend imports resolve
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext
from backend.shared.config import settings  # noqa: E402

logger = structlog.get_logger(__name__)

INTERNSHALA_BASE_URL = "https://internshala.com"
QUOTA_KEY = "quota:internshala:{date}"
QUOTA_DAILY_MAX = 1000

# Default categories (mirrors backend/collectors/internshala.py)
DEFAULT_CATEGORIES = [
    "software-development",
    "data-science",
    "web-development",
    "android-app-development",
    "ios-development",
    "machine-learning",
    "cloud-computing",
    "cyber-security",
]

MAX_PAGES_PER_CATEGORY = 10


class InternshalaActor:
    """Crawlee BeautifulSoupCrawler that scrapes Internshala and enqueues to Redis."""

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self.redis = redis_client
        self.logger = logger

    # ── Quota ────────────────────────────────────────────────────────────────

    async def _check_quota(self) -> bool:
        """Check + increment Redis quota counter. Auto-expires at midnight UTC."""
        key = QUOTA_KEY.format(date=date.today().isoformat())
        try:
            current = await self.redis.get(key)
            current = int(current) if current else 0
            if current >= QUOTA_DAILY_MAX:
                self.logger.warning(
                    "internshala_quota_exhausted", used=current, max=QUOTA_DAILY_MAX
                )
                return False
            await self.redis.incr(key)
            await self.redis.expire(key, 86400)
            return True
        except Exception as e:
            self.logger.warning("internshala_quota_check_failed", error=str(e))
            return True  # Fail open

    # ── Card Parsing ────────────────────────────────────────────────────────

    def _parse_card(self, soup: Any) -> dict[str, Any] | None:
        """Parse a single internship card element into a structured dict."""
        try:
            title_el = soup.select_one(
                "h3.job-internship-name, h3.internship-title, .heading_4_5"
            )
            company_el = soup.select_one(
                "h4.company-name, .company-name, .link_display_like_button"
            )
            location_el = soup.select_one(
                "a#location_names, [id*=location], .location"
            )

            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else ""

            stipend_el = soup.select_one(
                "span.stipend, .stipend, .salary, [class*=stipend]"
            )
            stipend_text = stipend_el.get_text(strip=True) if stipend_el else ""
            stipend_min, stipend_max = self._parse_stipend(stipend_text)

            duration_el = soup.select_one(
                "div#duration, [id*=duration], .duration"
            )
            duration = duration_el.get_text(strip=True) if duration_el else ""

            posted_el = soup.select_one(
                "div.status-success, .status-success, .posted-date, [class*=posted]"
            )
            posted = posted_el.get_text(strip=True) if posted_el else ""

            link_el = soup.select_one(
                "a.view_detail_button, a[href*='/internship/detail/'], a[class*=apply]"
            )
            href = link_el.get("href") if link_el and hasattr(link_el, "get") else ""
            link = f"{INTERNSHALA_BASE_URL}{href}" if href else ""

            location = location_el.get_text(strip=True) if location_el else ""
            card_text = soup.get_text(separator=" ", strip=True).lower()

            external_id = self._extract_id(link or href)

            return {
                "external_id": external_id,
                "url": link,
                "title": title,
                "body": (
                    f"Internship at {company}. Duration: {duration}. "
                    f"Stipend: {stipend_text}. Location: {location}."
                ) if title else "",
                "author": company,
                "score": 0,
                "company_name": company,
                "location": location,
                "stipend_min": stipend_min,
                "stipend_max": stipend_max,
                "stipend_text": stipend_text,
                "duration": duration,
                "posted_date": posted,
                "is_work_from_home": "work from home" in card_text,
                "is_part_time": "part time" in card_text,
                "is_in_office": "in office" in card_text,
            }
        except Exception as exc:
            self.logger.warning("internshala_card_parse_failed", error=str(exc))
            return None

    @staticmethod
    def _parse_stipend(stipend_str: str) -> tuple[int | None, int | None]:
        if not stipend_str or stipend_str.strip().lower() in ("unpaid", "", "na"):
            return None, None
        cleaned = (
            stipend_str.replace("₹", "")
            .replace(",", "")
            .replace("k", "000")
            .replace("K", "000")
            .strip()
        )
        numbers = [int(x) for x in re.findall(r"\d+", cleaned)]
        if len(numbers) >= 2:
            return numbers[0], numbers[1]
        if len(numbers) == 1:
            return numbers[0], numbers[0]
        return None, None

    @staticmethod
    def _extract_id(url_or_path: str) -> str:
        match = re.search(r"/internship/detail/([^/?]+)", url_or_path)
        if match:
            return match.group(1)
        match = re.search(r"internship_(\d+)", url_or_path)
        if match:
            return match.group(1)
        return hashlib.md5(url_or_path.encode()).hexdigest()[:12]

    # ── Transform → Redis ─────────────────────────────────────────────────

    def _to_pipeline_payload(self, parsed: dict[str, Any], category: str) -> dict[str, Any]:
        """Convert parsed internship dict to a flat dict for Redis XADD."""
        content_hash = hashlib.sha256(
            f"internshala:{parsed['external_id']}:{parsed['title']}:{parsed['author']}".encode()
        ).hexdigest()

        return {
            "source": "internshala",
            "external_id": parsed["external_id"],
            "url": parsed["url"],
            "title": parsed["title"],
            "body": parsed["body"],
            "author": parsed["author"],
            "score": str(parsed["score"]),
            "content_hash": content_hash,
            "collected_at": datetime.utcnow().isoformat(),
            "raw_meta": {
                "company_name": parsed["company_name"],
                "location": parsed["location"],
                "stipend_min": parsed["stipend_min"],
                "stipend_max": parsed["stipend_max"],
                "stipend_text": parsed["stipend_text"],
                "duration": parsed["duration"],
                "posted_date": parsed["posted_date"],
                "category": category,
                "is_work_from_home": parsed["is_work_from_home"],
                "is_part_time": parsed["is_part_time"],
                "is_in_office": parsed["is_in_office"],
            },
        }

    # ── Run ────────────────────────────────────────────────────────────────

    async def run(
        self,
        categories: list[str] | None = None,
        pipeline_stream: str | None = None,
    ) -> dict[str, Any]:
        """
        Build a BeautifulSoupCrawler and crawl Internshala categories.

        Args:
            categories: Internship categories to scrape (default: DEFAULT_CATEGORIES)
            pipeline_stream: Redis stream name (default: settings.STREAM_COLLECTED)

        Returns:
            Summary dict with status and counts.
        """
        if not await self._check_quota():
            return {"status": "quota_exhausted", "internships_collected": 0}

        stream = pipeline_stream or settings.STREAM_COLLECTED
        categories = categories or DEFAULT_CATEGORIES
        total_queued = 0

        urls: list[str] = []
        for cat in categories:
            for page in range(1, MAX_PAGES_PER_CATEGORY + 1):
                urls.append(f"{INTERNSHALA_BASE_URL}/internships/{cat}/page-{page}/")

        crawler = BeautifulSoupCrawler(
            max_requests_per_crawl=len(urls),
        )

        @crawler.router.default_handler
        async def handler(context: BeautifulSoupCrawlingContext) -> None:
            nonlocal total_queued

            # Determine category from URL path
            path = context.request.url.path
            match = re.search(r"/internships/([^/]+)/", path)
            category = match.group(1) if match else "unknown"

            # Find internship cards
            cards = context.soup.select(
                "div.individual_internship, div.internship"
            )

            if not cards:
                context.log.info(
                    "internshala_no_cards",
                    url=str(context.request.url),
                    category=category,
                )
                return

            context.log.info(
                "internshala_page_processed",
                url=str(context.request.url),
                category=category,
                card_count=len(cards),
            )

            for card in cards:
                parsed = self._parse_card(card)
                if parsed is None:
                    continue

                payload = self._to_pipeline_payload(parsed, category)
                try:
                    entry_id = await self.redis.xadd(stream, payload)
                    total_queued += 1
                    context.log.info(
                        "internshala_internship_queued",
                        internship_id=parsed["external_id"],
                        title=parsed["title"],
                        company=parsed["author"],
                        entry_id=entry_id,
                    )
                except Exception as e:
                    context.log.error(
                        "internshala_queue_failed",
                        internship_id=parsed["external_id"],
                        error=str(e),
                    )

        await crawler.run(urls)

        logger.info(
            "internshala_actor_complete",
            categories=len(categories),
            urls=len(urls),
            internships_queued=total_queued,
        )

        return {
            "status": "completed",
            "categories_scraped": len(categories),
            "pages_crawled": len(urls),
            "internships_queued": total_queued,
        }


async def main() -> None:
    """Entry point: connect to Redis, run the actor, then disconnect."""
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    actor = InternshalaActor(redis_client)
    try:
        result = await actor.run()
        logger.info("internshala_actor_finished", result=result)
    finally:
        await redis_client.close()


if __name__ == "__main__":
    asyncio.run(main())
