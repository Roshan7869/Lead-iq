"""Tests for scraping_utils — StealthConfig, UserAgentRotator, TLSFingerprintManager."""
from __future__ import annotations

import re

import pytest

from backend.collectors.scraping_utils import (
    StealthConfig,
    TLSFingerprintManager,
    UserAgentRotator,
)


class TestStealthConfig:
    """Verify StealthConfig default values match expected anti-detection profile."""

    def test_defaults(self) -> None:
        config = StealthConfig()
        assert config.browser == "playwright"
        assert config.headless is True
        assert config.user_agent_rotation is True
        assert config.proxy_type == "residential"
        assert config.proxy_rotation_interval == 20
        assert config.delay_min == 2.0
        assert config.delay_max == 5.0
        assert config.tls_bypass == "curl_cffi"
        assert config.fingerprint_spoofing is True
        assert config.mouse_movement is True
        assert config.scroll_simulation is True

    def test_custom_values(self) -> None:
        config = StealthConfig(
            browser="playwright",
            headless=False,
            delay_min=1.0,
            delay_max=3.0,
        )
        assert config.headless is False
        assert config.delay_min == 1.0
        assert config.delay_max == 3.0


class TestUserAgentRotator:
    """Verify UA strings are valid and browser-filtering works."""

    UA_PATTERN = re.compile(
        r"Mozilla/5\.0\s*\(.+\) AppleWebKit/\d+\.\d+"
    )

    def test_get_random_returns_valid_ua(self) -> None:
        rotator = UserAgentRotator()
        ua = rotator.get_random()
        assert isinstance(ua, str)
        assert len(ua) > 50
        assert ua.startswith("Mozilla/5.0")
        assert "AppleWebKit" in ua or "Gecko" in ua

    def test_get_random_returns_different_values(self) -> None:
        rotator = UserAgentRotator()
        results = {rotator.get_random() for _ in range(20)}
        assert len(results) > 1, "Should return more than one unique UA across 20 calls"

    def test_get_for_browser_chrome_returns_chrome_ua(self) -> None:
        rotator = UserAgentRotator()
        ua = rotator.get_for_browser("chrome")
        assert isinstance(ua, str)
        assert "Chrome" in ua
        assert "Edg" not in ua, "Chrome filter should exclude Edge UAs"

    def test_get_for_browser_edge_returns_edge_ua(self) -> None:
        rotator = UserAgentRotator()
        ua = rotator.get_for_browser("edge")
        assert "Edg" in ua

    def test_get_for_browser_firefox_returns_firefox_ua(self) -> None:
        rotator = UserAgentRotator()
        ua = rotator.get_for_browser("firefox")
        assert "Firefox" in ua
        assert "Chrome" not in ua

    def test_get_for_browser_safari(self) -> None:
        rotator = UserAgentRotator()
        ua = rotator.get_for_browser("safari")
        assert "Safari" in ua
        assert "Chrome" not in ua, "Safari filter should exclude Chrome UAs"

    def test_get_for_browser_unknown_falls_back(self) -> None:
        rotator = UserAgentRotator()
        ua = rotator.get_for_browser("unknown_browser")
        assert isinstance(ua, str)
        assert ua.startswith("Mozilla/5.0")


class TestTLSFingerprintManager:
    """Verify TLS session creation behaves as expected."""

    def test_create_session_default_is_curl_cffi(self) -> None:
        manager = TLSFingerprintManager()
        assert manager.method == "curl_cffi"

    def test_create_session_with_curl_cffi_returns_session(self) -> None:
        """When curl_cffi is installed the manager should return a Session-like object."""
        manager = TLSFingerprintManager(method="curl_cffi")
        try:
            session = manager.create_session()
            assert session is not None
        except ImportError:
            pytest.skip("curl_cffi not installed in test environment")

    def test_create_session_with_tls_client_fallback(self) -> None:
        manager = TLSFingerprintManager(method="tls_client")
        try:
            session = manager.create_session()
            assert session is not None
        except ImportError:
            pytest.skip("tls_client not installed in test environment")

    def test_create_session_fallback_httpx(self) -> None:
        manager = TLSFingerprintManager(method="unknown")
        import httpx

        session = manager.create_session()
        assert isinstance(session, httpx.AsyncClient)

    def test_create_context_alias(self) -> None:
        """create_context should be an alias for create_session."""
        manager = TLSFingerprintManager(method="unknown")
        session = manager.create_session()
        context = manager.create_context()
        assert type(session) is type(context)
