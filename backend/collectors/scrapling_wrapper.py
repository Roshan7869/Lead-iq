"""
backend/collectors/scrapling_wrapper.py — Anti-detection web scraping collectors.
Uses Scrapling for Cloudflare bypass, dynamic loading, and adaptive scraping.
Targets: LinkedIn public posts, AngelList startups, Crunchbase funding, company pages.
Supports session cookies for authenticated scraping where available.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, UTC

from backend.collectors.base import BaseCollector, RawPost

logger = logging.getLogger(__name__)

# Support for anti-detection with session cookies
SCRAPLING_HEADLESS = os.getenv("SCRAPLING_HEADLESS", "true").lower() == "true"
SCRAPLING_NETWORK_IDLE = os.getenv("SCRAPLING_NETWORK_IDLE", "true").lower() == "true"
SCRAPLING_TIMEOUT = int(os.getenv("SCRAPLING_TIMEOUT", "30"))


class ScraplingLinkedInCollector(BaseCollector):
    """LinkedIn public post collector using Scrapling's anti-detection."""
    source = "linkedin"

    async def collect(self) -> list[RawPost]:
        try:
            from scrapling.fetchers import StealthyFetcher
        except ImportError:
            logger.warning("Scrapling not installed. Skipping LinkedIn collection.")
            return []

        posts = []
        keywords = ["hiring", "looking for", "open role", "growing team", "join our", "we are hiring"]

        # Try StealthyFetcher with configurable headless/network_idle
        for attempt in range(2):
            try:
                headless = SCRAPLING_HEADLESS if attempt == 0 else False  # second attempt: visible browser
                page = StealthyFetcher.fetch(
                    "https://www.linkedin.com/feed/hashtag/?keywords=hiring",
                    headless=headless,
                    network_idle=SCRAPLING_NETWORK_IDLE,
                )
                if page and page.text:
                    items = page.css('.feed-shared-update-v2__description, .update-components-text')[:10]
                    if not items:
                        items = page.css('article')[:10]
                    for item in items:
                        text = " ".join(item.text.split())[:500]
                        if text and any(kw.lower() in text.lower() for kw in keywords):
                            posts.append(RawPost(
                                source=self.source,
                                external_id=f"linkedin_{hash(text)}",
                                url="https://linkedin.com",
                                title=text[:150],
                                body=text,
                                author="linkedin_user",
                                score=1,
                                raw_meta={"platform": "linkedin", "headless": headless},
                                collected_at=datetime.now(UTC),
                            ))
                    if posts:
                        break
            except Exception as e:
                logger.debug("LinkedIn attempt %d failed: %s", attempt + 1, e)

        if not posts:
            logger.debug("LinkedIn collector: no results (anti-scraping protection)")

        return posts


class ScraplingAngelListCollector(BaseCollector):
    """AngelList startup signal collector."""
    source = "angellist"

    async def collect(self) -> list[RawPost]:
        try:
            from scrapling.fetchers import Fetcher
        except ImportError:
            logger.warning("Scrapling not installed. Skipping AngelList collection.")
            return []

        posts = []
        try:
            page = Fetcher.get("https://wellfound.com/job-seeker-guide", stealthy_headers=True)
            items = page.css('a[href*="/company/"]')[:15]
            for item in items:
                posts.append(RawPost(
                    source=self.source,
                    external_id=f"angel_{hash(item.text)}",
                    url=item.attrib.get("href", ""),
                    title=item.text.strip(),
                    body=item.text.strip(),
                    author="startup_founder",
                    score=1,
                    raw_meta={"platform": "angellist"},
                    collected_at=datetime.now(UTC),
                ))
        except Exception as e:
            logger.warning("AngelList scraper failed: %s", e)

        logger.info("AngelListCollector fetched %d posts", len(posts))
        return posts


class ScraplingCrunchbaseCollector(BaseCollector):
    """Crunchbase funding signal collector."""
    source = "crunchbase"

    async def collect(self) -> list[RawPost]:
        try:
            from scrapling.fetchers import Fetcher
        except ImportError:
            logger.warning("Scrapling not installed. Skipping Crunchbase collection.")
            return []

        posts = []
        try:
            page = Fetcher.get("https://www.crunchbase.com/discover/funding_rounds", stealthy_headers=True)
            items = page.css('.component--grid-card')[:10]
            for item in items:
                text = item.text.strip()
                posts.append(RawPost(
                    source=self.source,
                    external_id=f"crunch_{hash(text)}",
                    url=item.attrib.get("href", ""),
                    title=text[:150],
                    body=text,
                    author="funding_source",
                    score=1,
                    raw_meta={"platform": "crunchbase", "signal_type": "funding"},
                    collected_at=datetime.now(UTC),
                ))
        except Exception as e:
            logger.warning("Crunchbase scraper failed: %s", e)

        logger.info("CrunchbaseCollector fetched %d posts", len(posts))
        return posts