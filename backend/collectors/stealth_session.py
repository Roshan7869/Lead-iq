"""
stealth_session.py — Playwright-based stealth browser session with anti-detection.
"""

from __future__ import annotations

import asyncio
import random
from typing import Any, Callable, Optional

import structlog
from playwright.async_api import Browser, Page, Playwright, async_playwright
from playwright_stealth import Stealth

logger = structlog.get_logger()


class StealthSession:
    """Stealth browsing session with anti-detection evasions."""

    def __init__(
        self,
        proxy: Optional[dict] = None,
        user_agent: Optional[str] = None,
        headless: bool = True,
    ) -> None:
        self.proxy = proxy
        self.user_agent = user_agent
        self.headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def __aenter__(self) -> StealthSession:
        await self.start()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def start(self) -> None:
        """Launch stealth browser with anti-detection args."""
        self._playwright = await async_playwright().start()

        launch_args = {
            "headless": self.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-site-isolation-trials",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-size=1920,1080",
            ],
        }

        if self.proxy:
            launch_args["proxy"] = {
                "server": self.proxy["url"],
            }

        self._browser = await self._playwright.chromium.launch(**launch_args)

        context = await self._browser.new_context(
            user_agent=self.user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            permissions=["geolocation"],
            geolocation={"latitude": 12.9716, "longitude": 77.5946},  # Bangalore
        )

        self.page = await context.new_page()
        await Stealth().apply_stealth_async(self.page)
        await self._apply_evasions()

        logger.info(
            "stealth_browser_launched",
            ua=(self.user_agent or "")[:50],
            proxy=self.proxy.get("ip") if self.proxy else "none",
        )

    async def _apply_evasions(self) -> None:
        """Apply JS evasions to hide automation."""
        assert self.page is not None
        await self.page.evaluate(
            """() => {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                const origQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (params) => (
                    params.name === 'notifications'
                        ? Promise.resolve({ state: 'denied' })
                        : origQuery(params)
                );
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-IN', 'en-US', 'en'],
                });
            }"""
        )

    async def goto(
        self,
        url: str,
        wait_until: str = "networkidle",
    ) -> None:
        """Navigate with human-like behavior and optional scrolling."""
        assert self.page is not None
        await asyncio.sleep(random.uniform(1.0, 3.0))
        await self.page.goto(url, wait_until=wait_until)
        await self._simulate_scrolling()

    async def _simulate_scrolling(self) -> None:
        """Simulate human-like scrolling behaviour."""
        assert self.page is not None
        scroll_height = await self.page.evaluate(
            "document.body.scrollHeight"
        )
        viewport_height = await self.page.evaluate("window.innerHeight")
        pos = 0
        while pos < scroll_height:
            delta = random.randint(100, 300)
            pos += delta
            await self.page.evaluate(f"window.scrollBy(0, {delta})")
            await asyncio.sleep(random.uniform(0.5, 2.0))
            if random.random() < 0.1:
                back = random.randint(50, 150)
                await self.page.evaluate(f"window.scrollBy(0, -{back})")
                await asyncio.sleep(random.uniform(0.3, 1.0))

    async def intercept_api(
        self,
        pattern: str,
        handler: Callable[[dict], Any],
    ) -> None:
        """Intercept API responses matching a URL pattern."""

        async def route_handler(route: Any) -> None:
            request = route.request
            if pattern in request.url:
                response = await route.fetch()
                try:
                    body = await response.json()
                    await handler(body)
                except Exception:
                    pass
                await route.fulfill(response=response)
            else:
                await route.continue_()

        assert self.page is not None
        await self.page.route(pattern, route_handler)

    async def close(self) -> None:
        """Close browser and playwright resources."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
