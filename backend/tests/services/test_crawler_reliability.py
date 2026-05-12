"""
Tests for crawler reliability service — ScrapeResult, error classification, retry.
"""
from __future__ import annotations

import pytest

from backend.services.crawler_reliability import (
    ScrapeResult,
    RetryReason,
    classify_error,
    validate_urls,
)


class TestScrapeResult:
    def test_success(self):
        r = ScrapeResult.success({"key": "val"}, source="indeed")
        assert r.is_success()
        assert r.status == "success"
        assert r.data == {"key": "val"}

    def test_blocked(self):
        r = ScrapeResult.blocked(reason="Cloudflare", source="indeed")
        assert not r.is_success()
        assert r.status == "blocked"
        assert r.reason == RetryReason.BLOCKED

    def test_timeout(self):
        r = ScrapeResult.timeout(reason="timed out", source="indeed")
        assert r.status == "timeout"
        assert r.reason == RetryReason.TIMEOUT

    def test_empty(self):
        r = ScrapeResult.empty(reason="no content", source="indeed")
        assert r.status == "empty"
        assert r.reason == RetryReason.PARSER_ERROR

    def test_to_dict(self):
        r = ScrapeResult.success({"a": 1}, source="test", response_time_ms=150.0)
        d = r.to_dict()
        assert d["status"] == "success"
        assert d["source"] == "test"
        assert d["response_time_ms"] == 150.0


class TestClassifyError:
    def test_timeout(self):
        assert classify_error("timed out after 30s") == RetryReason.TIMEOUT
        assert classify_error("TimeoutError") == RetryReason.TIMEOUT

    def test_rate_limit(self):
        assert classify_error("429 Too Many Requests") == RetryReason.RATE_LIMIT
        assert classify_error("rate limit exceeded") == RetryReason.RATE_LIMIT

    def test_server_error(self):
        assert classify_error("500 Internal Server Error") == RetryReason.SERVER_ERROR
        assert classify_error("503 Service Unavailable") == RetryReason.SERVER_ERROR

    def test_blocked(self):
        assert classify_error("Cloudflare challenge") == RetryReason.BLOCKED
        assert classify_error("captcha required") == RetryReason.BLOCKED
        assert classify_error("WAF blocked") == RetryReason.BLOCKED

    def test_proxy_error(self):
        assert classify_error("proxy connection refused") == RetryReason.PROXY_ERROR

    def test_connection_error(self):
        assert classify_error("connection refused") == RetryReason.CONNECTION_ERROR
        assert classify_error("connection reset") == RetryReason.CONNECTION_ERROR

    def test_parser_error(self):
        assert classify_error("parse error at line 42") == RetryReason.PARSER_ERROR
        assert classify_error("Selector not found") == RetryReason.PARSER_ERROR

    def test_unknown(self):
        assert classify_error("some random error") == RetryReason.UNKNOWN
