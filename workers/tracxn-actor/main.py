"""
workers/tracxn-actor/main.py — Tracxn Startup Intelligence Collector

Paid enterprise data source for startup profiles, funding, team, tech stack.
Uses Crawl4AI with stealth configuration for web scraping.

Data: Company profiles, funding rounds, founders, tech stack, contact info
Confidence: 0.70 (aggregated data, verify independently)
Rate Limit: 100/day (paid tier)

Note: This requires Crawl4AI library and Tracxn subscription.
"""
from __future__ import annotations

import asyncio
import structlog
from typing import Any

from backend.llm.gemini_service import extract_lead
from backend.llm.cost_guard import check_budget
from backend.services.confidence import compute_confidence

logger = structlog.get_logger()

# Tracxn target URLs
TRACXN_TARGETS = [
    "https://tracxn.com/explore/saas-startups-in-india",
    "https://tracxn.com/explore/fintech-startups-in-india",
    "https://tracxn.com/explore/edtech-startups-in-india",
    "https://tracxn.com/explore/healthtech-startups-in-india",
    "https://tracxn.com/explore/d2c-startups-in-india",
]

# Crawl4AI configuration
CRAWL4AI_CONFIG = {
    "headless": True,
    "user_agent_mode": "random",
    "simulate_user": True,
    "magic": True,  # Anti-bot magic mode
    "word_count_threshold": 30,
    "fit_markdown": True,  # LLM-ready output
    "wait_until": "networkidle",
}


async def scrape_with_crawl4ai(url: str) -> str | None:
    """
    Scrape URL using Crawl4AI with stealth configuration.

    Args:
        url: URL to scrape

    Returns:
        Fit markdown content or None if failed
    """
    try:
        # Crawl4AI import (will fail if not installed)
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

        browser_config = BrowserConfig(
            headless=CRAWL4AI_CONFIG["headless"],
            user_agent_mode=CRAWL4AI_CONFIG["user_agent_mode"],
            extra_args=["--disable-blink-features=AutomationControlled"],
        )

        run_config = CrawlerRunConfig(
            simulate_user=CRAWL4AI_CONFIG["simulate_user"],
            magic=CRAWL4AI_CONFIG["magic"],
            word_count_threshold=CRAWL4AI_CONFIG["word_count_threshold"],
            fit_markdown=CRAWL4AI_CONFIG["fit_markdown"],
            wait_until=CRAWL4AI_CONFIG["wait_until"],
        )

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)

            if result.success:
                return result.fit_markdown
            else:
                logger.error("crawl4ai_error", url=url, error=result.error_message)
                return None

    except ImportError:
        logger.warning("crawl4ai_not_installed_using_fallback")
        return await scrape_with_httpx(url)
    except Exception as exc:
        logger.error("crawl4ai_exception", url=url, error=str(exc))
        return None


async def scrape_with_httpx(url: str) -> str | None:
    """
    Fallback scraper using httpx (no JS rendering).

    Use only when Crawl4AI is not installed.
    Lower quality but no dependencies.
    """
    import httpx

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            return response.text
        except Exception as exc:
            logger.error("httpx_error", url=url, error=str(exc))
            return None


async def scrape_tracxn(url: str) -> dict[str, Any] | None:
    """
    Scrape a Tracxn URL and extract lead data.

    Args:
        url: Tracxn URL to scrape

    Returns:
        Extracted lead dictionary or None
    """
    # Get page content
    markdown_content = await scrape_with_crawl4ai(url)

    if not markdown_content:
        logger.warning("tracxn_no_content", url=url)
        return None

    # Estimate tokens for budget check
    estimated_tokens = len(markdown_content) // 4 + 500

    if not await check_budget(estimated_tokens):
        logger.warning("tracxn_budget_exceeded", url=url)
        return None

    # Extract lead data using Gemini
    lead = await extract_lead(
        markdown_content=markdown_content,
        source="tracxn",
        url=url,
    )

    # Validate extraction
    if not lead.get("company_name"):
        logger.warning("tracxn_no_company_name", url=url)
        return None

    # Compute confidence
    lead["confidence"] = compute_confidence(lead, "tracxn")

    logger.info(
        "tracxn_extraction_complete",
        url=url,
        company=lead.get("company_name"),
        confidence=lead["confidence"],
    )

    return lead


async def run_tracxn_actor(
    targets: list[str] | None = None,
    max_pages: int = 5,
) -> list[dict[str, Any]]:
    """
    Main Tracxn collection entry point.

    Args:
        targets: List of Tracxn URLs to scrape
        max_pages: Maximum pages to scrape per target

    Returns:
        List of extracted leads
    """
    targets = targets or TRACXN_TARGETS
    all_leads = []

    for target_url in targets:
        # Scrape target
        lead = await scrape_tracxn(target_url)

        if lead:
            all_leads.append(lead)

        # Rate limiting
        await asyncio.sleep(2.0)

    logger.info(
        "tracxn_actor_complete",
        leads_collected=len(all_leads),
        targets=len(targets),
    )

    return all_leads


if __name__ == "__main__":
    asyncio.run(run_tracxn_actor())