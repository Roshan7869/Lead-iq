"""
crawler_reliability.py — Structured retry taxonomy, exponential backoff,
timeout handling, and scrape result types for the crawl layer.

Merged from scrapecraft (scraping_service_enhanced.py) retry/backoff patterns
and sherlock (sherlock.py) error classification taxonomy.
"""
from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Any, TypeVar

import structlog
from tenacity import (
    after_log,
    before_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger(__name__)
_plain_log = logging.getLogger(__name__)

T = TypeVar("T")


class RetryReason(Enum):
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    BLOCKED = "blocked"
    PARSER_ERROR = "parser_error"
    PROXY_ERROR = "proxy_error"
    CONNECTION_ERROR = "connection_error"
    UNKNOWN = "unknown"


class ScrapeResult:

    def __init__(
        self,
        status: str,
        data: dict[str, Any] | None = None,
        error: str | None = None,
        reason: RetryReason | None = None,
        response_time_ms: float = 0.0,
        source: str = "",
    ):
        self.status = status
        self.data = data or {}
        self.error = error
        self.reason = reason
        self.response_time_ms = response_time_ms
        self.source = source

    @classmethod
    def success(cls, data: dict[str, Any], source: str = "", response_time_ms: float = 0.0):
        return cls("success", data=data, source=source, response_time_ms=response_time_ms)

    @classmethod
    def blocked(cls, reason: str = "", source: str = ""):
        return cls("blocked", error=reason, reason=RetryReason.BLOCKED, source=source)

    @classmethod
    def timeout(cls, reason: str = "", source: str = ""):
        return cls("timeout", error=reason, reason=RetryReason.TIMEOUT, source=source)

    @classmethod
    def empty(cls, reason: str = "", source: str = ""):
        return cls("empty", error=reason, reason=RetryReason.PARSER_ERROR, source=source)

    @classmethod
    def parser_error(cls, reason: str = "", source: str = ""):
        return cls("parser_error", error=reason, reason=RetryReason.PARSER_ERROR, source=source)

    @classmethod
    def unknown_error(cls, reason: str = "", source: str = ""):
        return cls("error", error=reason, reason=RetryReason.UNKNOWN, source=source)

    def is_success(self) -> bool:
        return self.status == "success"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "data": self.data,
            "error": self.error,
            "reason": self.reason.value if self.reason else None,
            "response_time_ms": self.response_time_ms,
            "source": self.source,
        }


class ScrapingError(Exception):
    pass


class APIError(ScrapingError):
    pass


class RateLimitError(ScrapingError):
    pass


class BlockedError(ScrapingError):
    pass


class TimeoutError_(ScrapingError):
    pass


def classify_error(error_msg: str) -> RetryReason:
    msg = error_msg.lower()
    if "timeout" in msg or "timed out" in msg:
        return RetryReason.TIMEOUT
    if "429" in msg or "rate limit" in msg:
        return RetryReason.RATE_LIMIT
    if "500" in msg or "502" in msg or "503" in msg:
        return RetryReason.SERVER_ERROR
    if "blocked" in msg or "captcha" in msg or "cloudflare" in msg or "waf" in msg:
        return RetryReason.BLOCKED
    if "proxy" in msg:
        return RetryReason.PROXY_ERROR
    if "connection" in msg or "refused" in msg or "reset" in msg:
        return RetryReason.CONNECTION_ERROR
    if "parse" in msg or "selector" in msg:
        return RetryReason.PARSER_ERROR
    return RetryReason.UNKNOWN


def error_to_exception(reason: RetryReason, msg: str) -> ScrapingError:
    mapping = {
        RetryReason.TIMEOUT: TimeoutError_,
        RetryReason.RATE_LIMIT: RateLimitError,
        RetryReason.SERVER_ERROR: APIError,
        RetryReason.BLOCKED: BlockedError,
    }
    exc_cls = mapping.get(reason, ScrapingError)
    return exc_cls(msg)


def retry_decorator(
    max_attempts: int = 3,
    min_wait: float = 2.0,
    max_wait: float = 30.0,
    retryable_exceptions: tuple | None = None,
):
    if retryable_exceptions is None:
        retryable_exceptions = (ScrapingError, APIError, RateLimitError, TimeoutError_, BlockedError)
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(retryable_exceptions),
        before=before_log(_plain_log, logging.WARNING),
        after=after_log(_plain_log, logging.WARNING),
        reraise=True,
    )


async def run_with_timeout(coro, timeout: float = 30.0, label: str = "") -> Any:
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError_(f"{label} timed out after {timeout}s")


async def scrape_multiple(
    scrape_fn,
    urls: list[str],
    max_concurrent: int = 5,
    **kwargs,
) -> list[dict[str, Any]]:
    semaphore = asyncio.Semaphore(max_concurrent)

    async def with_limit(url: str) -> dict[str, Any]:
        async with semaphore:
            try:
                result = await scrape_fn(url, **kwargs)
                return {"success": True, "url": url, "data": result}
            except Exception as e:
                logger.warning("scrape_failed", url=url, error=str(e))
                return {"success": False, "url": url, "error": str(e)}

    tasks = [with_limit(url) for url in urls]
    results = await asyncio.gather(*tasks)
    ok = sum(1 for r in results if r.get("success"))
    logger.info("scrape_multiple_complete", successful=ok, total=len(urls))
    return results


async def validate_urls(urls: list[str], timeout: float = 5.0) -> dict[str, bool]:
    import httpx

    async def check(url: str) -> tuple[str, bool]:
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                r = await client.head(url)
                return url, r.is_success
        except Exception:
            return url, False

    tasks = [check(url) for url in urls]
    results = await asyncio.gather(*tasks)
    return dict(results)
