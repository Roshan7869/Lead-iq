"""
scrapling_adapter.py — Anti-detection web scraping adapter.

Refactors the existing scrapling_wrapper.py into a proper adapter that
integrates Scheduler, CheckpointManager, ProxyRotator, and the crawler
reliability service. Provides StealthyFetcher and FetcherSession adapters
with uniform error handling and retry.
"""
from __future__ import annotations

import os
import time
from typing import Any

import structlog

from backend.collectors.base import BaseCollector, RawPost
from backend.collectors.checkpoint_manager import CheckpointManager, CheckpointData
from backend.collectors.proxy_rotation import ProxyRotator
from backend.collectors.url_scheduler import CrawlRequest, Scheduler
from backend.services.crawler_reliability import (
    ScrapeResult,
    RetryReason,
    classify_error,
    run_with_timeout,
)

logger = structlog.get_logger(__name__)

SCRAPLING_HEADLESS = os.getenv("SCRAPLING_HEADLESS", "true").lower() == "true"
SCRAPLING_NETWORK_IDLE = os.getenv("SCRAPLING_NETWORK_IDLE", "true").lower() == "true"
SCRAPLING_TIMEOUT = int(os.getenv("SCRAPLING_TIMEOUT", "30"))


class FetchMode:
    STATIC = "static"
    STEALTH = "stealth"
    DYNAMIC = "dynamic"


def get_fetch_mode(source: str) -> str:
    overrides = {
        "linkedin": FetchMode.STEALTH,
        "indeed": FetchMode.STEALTH,
        "naukri": FetchMode.STEALTH,
        "internshala": FetchMode.DYNAMIC,
        "shine": FetchMode.DYNAMIC,
        "cutshort": FetchMode.STATIC,
        "hirect": FetchMode.STATIC,
        "instahyre": FetchMode.STATIC,
        "timesjobs": FetchMode.DYNAMIC,
        "weekday": FetchMode.STATIC,
        "employment_news": FetchMode.STATIC,
    }
    return overrides.get(source, FetchMode.DYNAMIC)


class ScraplingAdapter:
    def __init__(
        self,
        source: str,
        proxy_rotator: ProxyRotator | None = None,
        scheduler: Scheduler | None = None,
        checkpoint_manager: CheckpointManager | None = None,
    ):
        self.source = source
        self.proxy_rotator = proxy_rotator
        self.scheduler = scheduler or Scheduler()
        self.checkpoint_manager = checkpoint_manager

    async def fetch_static(self, url: str, **kwargs) -> ScrapeResult:
        try:
            from scrapling.fetchers import AsyncFetcher
        except ImportError:
            return ScrapeResult.unknown_error("Scrapling not installed", source=self.source)

        start = time.monotonic()
        try:
            proxy = self.proxy_rotator.get_proxy() if self.proxy_rotator else None
            response = await run_with_timeout(
                AsyncFetcher.get(url, impersonate="chrome", proxy=proxy, **kwargs),
                timeout=SCRAPLING_TIMEOUT,
                label=f"static_fetch:{url}",
            )
            elapsed = (time.monotonic() - start) * 1000
            html = response.body if hasattr(response, 'body') and response.body else str(response)
            return ScrapeResult.success(
                data={"text": html, "status": response.status, "url": url},
                source=self.source,
                response_time_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            reason = classify_error(str(e))
            return ScrapeResult(
                status="error",
                error=str(e),
                reason=reason,
                response_time_ms=elapsed,
                source=self.source,
            )

    async def fetch_stealth(self, url: str, **kwargs) -> ScrapeResult:
        try:
            from scrapling.fetchers.stealth_chrome import StealthyFetcher
        except ImportError:
            return ScrapeResult.unknown_error("Scrapling not installed (stealth)", source=self.source)

        start = time.monotonic()
        try:
            proxy = self.proxy_rotator.get_proxy() if self.proxy_rotator else None
            response = await run_with_timeout(
                StealthyFetcher.async_fetch(
                    url,
                    headless=SCRAPLING_HEADLESS,
                    network_idle=SCRAPLING_NETWORK_IDLE,
                    disable_resources=True,
                    solve_cloudflare=True,
                    proxy=proxy,
                    **kwargs,
                ),
                timeout=SCRAPLING_TIMEOUT * 2,
                label=f"stealth_fetch:{url}",
            )
            elapsed = (time.monotonic() - start) * 1000
            html = response.body if hasattr(response, 'body') and response.body else str(response)
            return ScrapeResult.success(
                data={"text": html, "status": response.status, "url": url},
                source=self.source,
                response_time_ms=elapsed,
            )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            reason = classify_error(str(e))
            return ScrapeResult(
                status="error",
                error=str(e),
                reason=reason,
                response_time_ms=elapsed,
                source=self.source,
            )

    async def fetch(self, url: str, mode: str | None = None) -> ScrapeResult:
        mode = mode or get_fetch_mode(self.source)
        if mode == FetchMode.STATIC:
            return await self.fetch_static(url)
        result = await self.fetch_static(url)
        if result.is_success():
            return result
        if mode == FetchMode.STEALTH:
            return await self.fetch_stealth(url)
        return result

    async def crawl(self, urls: list[str], callback=None) -> list[ScrapeResult]:
        for url in urls:
            await self.scheduler.enqueue(CrawlRequest(url=url, priority=0))

        results = []
        while not self.scheduler.is_empty:
            request = await self.scheduler.dequeue()
            result = await self.fetch(request.url)
            results.append(result)
            if callback:
                await callback(result)

        if self.checkpoint_manager:
            reqs, seen = self.scheduler.snapshot()
            self.checkpoint_manager.save(CheckpointData(requests=reqs, seen=seen))

        return results


class ScraplingCollectorAdapter(BaseCollector):
    """Base class for collectors using the ScraplingAdapter."""

    source: str = "scrapling"

    def __init__(self, adapter: ScraplingAdapter | None = None):
        self.adapter = adapter or ScraplingAdapter(source=self.source)

    async def collect(self) -> list[RawPost]:
        raise NotImplementedError

    async def fetch_and_parse(self, url: str) -> ScrapeResult:
        return await self.adapter.fetch(url)
