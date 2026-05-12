"""
proxy_manager.py — Intelligent proxy rotation and management.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

import structlog

logger = structlog.get_logger()


@dataclass
class Proxy:
    """Represents a single proxy endpoint."""

    ip: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    country: str = "IN"
    city: Optional[str] = None
    proxy_type: str = "residential"
    last_used: Optional[float] = None
    use_count: int = 0
    success_rate: float = 1.0

    @property
    def url(self) -> str:
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"http://{auth}{self.ip}:{self.port}"


class ProxyManager:
    """Manage proxy pool with intelligent weighted rotation."""

    def __init__(self, config: Optional[dict] = None) -> None:
        self.config = config or {}
        self.proxy_pool: list[Proxy] = []
        self.failed_proxies: set[str] = set()

    async def initialize_pool(self) -> None:
        """Load initial proxy pool from provider or file."""
        provider = self.config.get("provider", "brightdata")
        if provider == "brightdata":
            self.proxy_pool = await self._load_brightdata()
        elif provider == "scrapingbee":
            self.proxy_pool = await self._load_scrapingbee()
        else:
            self.proxy_pool = await self._load_from_file()
        logger.info("proxy_pool_initialized", count=len(self.proxy_pool))

    async def get_proxy(self) -> Optional[dict]:
        """Get next proxy with weighted random selection."""
        available = [
            p for p in self.proxy_pool
            if p.ip not in self.failed_proxies
        ]
        if not available:
            logger.warning("no_proxies_available")
            return None
        weights = [max(p.success_rate, 0.01) for p in available]
        proxy = random.choices(available, weights=weights, k=1)[0]
        proxy.use_count += 1
        return {
            "ip": proxy.ip,
            "port": proxy.port,
            "username": proxy.username,
            "password": proxy.password,
            "url": proxy.url,
        }

    async def report_success(self, proxy_ip: str) -> None:
        """Mark proxy use as successful."""
        for p in self.proxy_pool:
            if p.ip == proxy_ip:
                p.success_rate = min(1.0, p.success_rate + 0.05)
                break

    async def report_failure(self, proxy_ip: str, error_type: str = "") -> None:
        """Mark proxy use as failed; remove if too unreliable."""
        for p in self.proxy_pool:
            if p.ip == proxy_ip:
                p.success_rate = max(0.1, p.success_rate - 0.2)
                if p.success_rate < 0.3:
                    self.failed_proxies.add(proxy_ip)
                    logger.warning(
                        "proxy_marked_failed",
                        ip=proxy_ip,
                        error=error_type,
                    )
                break

    async def _load_brightdata(self) -> list[Proxy]:
        """Generate BrightData residential proxy entries."""
        username = self.config.get("username", "")
        password = self.config.get("password", "")
        count = self.config.get("pool_size", 100)
        return [
            Proxy(
                ip="brd.superproxy.io",
                port=22225,
                username=f"brd-customer-{username}-country-in",
                password=password,
                country="IN",
            )
            for _ in range(count)
        ]

    async def _load_scrapingbee(self) -> list[Proxy]:
        """ScrapingBee API-key based proxy stub."""
        api_key = self.config.get("api_key", "")
        if not api_key:
            logger.warning("scrapingbee_no_api_key")
        return [
            Proxy(
                ip="proxy.scrapingbee.com",
                port=8886,
                username="bearer",
                password=api_key,
                country="IN",
            )
        ]

    async def _load_from_file(self, path: str = "proxies.txt") -> list[Proxy]:
        """Load proxies from a text file (ip:port per line)."""
        proxies: list[Proxy] = []
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split(":")
                    if len(parts) >= 2:
                        proxies.append(Proxy(ip=parts[0], port=int(parts[1])))
        except FileNotFoundError:
            logger.warning("proxy_file_not_found", path=path)
        return proxies
