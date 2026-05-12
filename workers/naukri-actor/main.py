"""
workers/naukri-actor/main.py — Naukri Job Listings Collector Actor.

Uses Crawlee PlaywrightCrawler to scrape Naukri.com job listings by keyword
and location. Extracts job details from rendered DOM, transforms into pipeline
stream payloads, and enqueues to Redis stream lead:collected.

QUOTA: 2000 requests/day
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

from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext
from backend.shared.config import settings  # noqa: E402

logger = structlog.get_logger(__name__)

NAUKRI_BASE_URL = "https://www.naukri.com"
QUOTA_KEY = "quota:naukri:{date}"
QUOTA_DAILY_MAX = 2000

# Default search keywords and locations (mirrors backend/collectors/naukri.py)
DEFAULT_KEYWORDS = [
    "software-engineer",
    "data-scientist",
    "product-manager",
    "devops-engineer",
    "frontend-developer",
    "backend-developer",
    "full-stack-developer",
    "machine-learning-engineer",
    "cloud-architect",
    "cybersecurity-analyst",
]
DEFAULT_LOCATIONS = [
    "bangalore",
    "hyderabad",
    "pune",
    "chennai",
    "mumbai",
    "delhi",
    "gurgaon",
    "noida",
]

MAX_RESULTS_PER_SEARCH = 50


class NaukriActor:
    """Crawlee PlaywrightCrawler that scrapes Naukri.com and enqueues to Redis."""

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self.redis = redis_client
        self._intercepted_payloads: list[dict[str, Any]] = []
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
                    "naukri_quota_exhausted", used=current, max=QUOTA_DAILY_MAX
                )
                return False
            await self.redis.incr(key)
            await self.redis.expire(key, 86400)
            return True
        except Exception as e:
            self.logger.warning("naukri_quota_check_failed", error=str(e))
            return True  # Fail open

    # ── API Interception ────────────────────────────────────────────────────

    def _setup_response_interception(self, context: PlaywrightCrawlingContext) -> None:
        """Hook into Playwright responses to capture Naukri's internal job API."""
        async def on_response(response) -> None:
            if "jobapi/v3/search" in response.url:
                try:
                    body = await response.json()
                    self._intercepted_payloads.append(body)
                except Exception:
                    pass  # Non-JSON response, skip

        context.page.on("response", on_response)

    # ── DOM Extraction (fallback when API interception yields nothing) ──────

    async def _extract_from_dom(self, context: PlaywrightCrawlingContext) -> list[dict[str, Any]]:
        """Extract job cards from rendered DOM using Playwright selectors."""
        jobs: list[dict[str, Any]] = []
        cards = await context.page.query_selector_all(
            "article.jobTuple, div.jobTuple, div[class*=job]"
        )
        for card in cards:
            job = {
                "jobId": await self._get_attribute(card, "[data-job-id]") or "",
                "title": await self._get_text(card, "a.title, .title, [class*=title]") or "",
                "companyName": await self._get_text(
                    card, "a.company-name, .company-name, [class*=company]"
                ) or "",
                "location": await self._get_text(card, ".location, [class*=loc]") or "",
                "experience": await self._get_text(card, ".experience, [class*=exp]") or "",
                "salary": await self._get_text(card, ".salary, [class*=salary], [class*=sal]") or "",
                "description": await self._get_text(card, ".job-description, [class*=desc]") or "",
                "skills": [],
                "workMode": "",
                "jobType": "",
                "postedDate": "",
                "applyCount": 0,
                "ambitionBoxRating": None,
            }
            jobs.append(job)
        return jobs

    @staticmethod
    async def _get_text(element, selector: str) -> str:
        el = await element.query_selector(selector)
        if el:
            return (await el.inner_text()).strip()
        return ""

    @staticmethod
    async def _get_attribute(element, selector: str) -> str:
        el = await element.query_selector(selector)
        if el:
            return await el.get_attribute("data-job-id") or ""
        return ""

    # ── API Response Parsing ────────────────────────────────────────────────

    def _parse_api_jobs(self) -> list[dict[str, Any]]:
        """Parse intercepted API payloads into structured job dicts."""
        jobs: list[dict[str, Any]] = []
        for payload in self._intercepted_payloads:
            raw_ads = payload.get("jobAds", []) or payload.get("data", {}).get("jobAds", [])
            for ad in raw_ads:
                placeholders = ad.get("placeholders") or {}
                tags = ad.get("tagsAndSkills") or []
                ambition_box = ad.get("ambitionBoxData") or {}
                jobs.append({
                    "jobId": str(ad.get("jobId", "")),
                    "title": ad.get("title", ""),
                    "companyName": ad.get("companyName", ""),
                    "description": ad.get("jobDescription", ""),
                    "location": placeholders.get("location", ""),
                    "experience": placeholders.get("experience", ""),
                    "salary": placeholders.get("salary", ""),
                    "skills": (
                        [t["label"] for t in tags if isinstance(t, dict) and "label" in t]
                        if isinstance(tags, list) else []
                    ),
                    "workMode": ad.get("workFromHomeType", ""),
                    "jobType": ad.get("jobType", ""),
                    "postedDate": ad.get("footerPlaceholderLabel", ""),
                    "applyCount": ad.get("applyCount", 0),
                    "ambitionBoxRating": ambition_box.get("rating"),
                })
        return jobs

    # ── Transform → Redis ─────────────────────────────────────────────────

    def _to_pipeline_payload(self, job: dict[str, Any], search_keyword: str, search_location: str) -> dict[str, Any]:
        """Convert a job dict to a flat dict suitable for Redis XADD."""
        job_id = str(job.get("jobId", ""))
        company = str(job.get("companyName", ""))
        title = str(job.get("title", ""))
        salary_min, salary_max = self._parse_salary(job.get("salary") or "")
        exp_min, exp_max = self._parse_experience(job.get("experience") or "")
        content_hash = hashlib.sha256(
            f"naukri:{job_id}:{title}:{company}".encode()
        ).hexdigest()

        return {
            "source": "naukri",
            "external_id": job_id,
            "url": f"{NAUKRI_BASE_URL}/job-listings-{job_id}" if job_id else "",
            "title": title,
            "body": str(job.get("description", "")),
            "author": company,
            "score": str(int(job.get("ambitionBoxRating") or 0)),
            "content_hash": content_hash,
            "collected_at": datetime.utcnow().isoformat(),
            "raw_meta": {
                "company_name": company,
                "salary_min": salary_min,
                "salary_max": salary_max,
                "experience_min": exp_min,
                "experience_max": exp_max,
                "location": str(job.get("location", "")),
                "skills": job.get("skills", []),
                "work_mode": str(job.get("workMode", "")),
                "job_type": str(job.get("jobType", "")),
                "posted_date": str(job.get("postedDate", "")),
                "apply_count": job.get("applyCount", 0),
                "ambition_box_rating": job.get("ambitionBoxRating"),
                "search_keyword": search_keyword,
                "search_location": search_location,
            },
        }

    @staticmethod
    def _parse_salary(salary_str: str) -> tuple[int | None, int | None]:
        if not salary_str or salary_str.strip().lower() in ("not disclosed", "", "na"):
            return None, None
        cleaned = salary_str.replace("₹", "").replace(",", "").strip()
        is_monthly = "month" in cleaned.lower() or "/m" in cleaned.lower()
        has_k = bool(re.search(r"\d+\s*K", cleaned, re.IGNORECASE))
        numbers = [int(x) for x in re.findall(r"\d+", cleaned)]
        if len(numbers) >= 2:
            lo, hi = numbers[0], numbers[1]
        elif len(numbers) == 1:
            lo = hi = numbers[0]
        else:
            return None, None
        if has_k:
            lo, hi = lo * 1_000, hi * 1_000
        if is_monthly:
            lo, hi = lo * 12, hi * 12
        else:
            if not has_k and hi < 1000:
                lo, hi = lo * 100_000, hi * 100_000
        return lo, hi

    @staticmethod
    def _parse_experience(exp_str: str) -> tuple[int | None, int | None]:
        if not exp_str or not exp_str.strip():
            return None, None
        numbers = [int(x) for x in re.findall(r"\d+", exp_str)]
        if len(numbers) >= 2:
            return numbers[0], numbers[1]
        if len(numbers) == 1:
            return numbers[0], numbers[0]
        return None, None

    # ── Run ────────────────────────────────────────────────────────────────

    async def run(
        self,
        keywords: list[str] | None = None,
        locations: list[str] | None = None,
        pipeline_stream: str | None = None,
    ) -> dict[str, Any]:
        """
        Build a PlaywrightCrawler and crawl Naukri.com for each keyword+location.

        Args:
            keywords: Job search keywords (default: DEFAULT_KEYWORDS)
            locations: Location filters (default: DEFAULT_LOCATIONS)
            pipeline_stream: Redis stream name (default: settings.STREAM_COLLECTED)

        Returns:
            Summary dict with status and counts.
        """
        if not await self._check_quota():
            return {"status": "quota_exhausted", "jobs_collected": 0}

        stream = pipeline_stream or settings.STREAM_COLLECTED
        keywords = keywords or DEFAULT_KEYWORDS
        locations = locations or DEFAULT_LOCATIONS
        total_queued = 0

        for keyword in keywords:
            for location in locations:
                search_url = f"{NAUKRI_BASE_URL}/{keyword.replace(' ', '-')}-jobs-in-{location}"
                self._intercepted_payloads.clear()

                crawler = PlaywrightCrawler(
                    headless=True,
                    max_requests_per_crawl=1,
                    browser_type="chromium",
                )

                @crawler.router.default_handler
                async def handler(context: PlaywrightCrawlingContext) -> None:
                    # Set up API response interception
                    self._setup_response_interception(context)

                    context.log.info(
                        "naukri_searching",
                        keyword=keyword,
                        location=location,
                        url=context.request.url,
                    )

                    # Wait for job cards or the API response to arrive
                    await asyncio.sleep(5)

                    # Try API payloads first, fall back to DOM extraction
                    api_jobs = self._parse_api_jobs()
                    jobs = api_jobs if api_jobs else await self._extract_from_dom(context)

                    # Limit results
                    jobs = jobs[:MAX_RESULTS_PER_SEARCH]

                    # Enqueue each job to Redis
                    for job in jobs:
                        payload = self._to_pipeline_payload(
                            job, keyword, location
                        )
                        try:
                            entry_id = await self.redis.xadd(stream, payload)
                            nonlocal total_queued
                            total_queued += 1
                            context.log.info(
                                "naukri_job_queued",
                                job_id=job.get("jobId"),
                                title=job.get("title"),
                                company=job.get("companyName"),
                                entry_id=entry_id,
                            )
                        except Exception as e:
                            context.log.error(
                                "naukri_queue_failed",
                                job_id=job.get("jobId"),
                                error=str(e),
                            )

                await crawler.run([search_url])

        logger.info(
            "naukri_actor_complete",
            keywords=len(keywords),
            locations=len(locations),
            jobs_queued=total_queued,
        )

        return {
            "status": "completed",
            "keywords_searched": len(keywords),
            "locations_searched": len(locations),
            "jobs_queued": total_queued,
        }


async def main() -> None:
    """Entry point: connect to Redis, run the actor, then disconnect."""
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    actor = NaukriActor(redis_client)
    try:
        result = await actor.run()
        logger.info("naukri_actor_finished", result=result)
    finally:
        await redis_client.close()


if __name__ == "__main__":
    asyncio.run(main())
