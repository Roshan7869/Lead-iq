"""
source_pattern_learner.py — Per-domain success rate tracking and fetch mode selection.

Merged from scrapecraft (pattern_learner.py) algorithmic core:
- _extract_domain, _classify_data_type
- suggest_optimizations (concurrency, retry, JS, rate limiting)
- _get_domain_knowledge, get_field_suggestions, get_extraction_tips
"""
from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from urllib.parse import urlparse

import structlog

from backend.collectors.scrapling_adapter import FetchMode

logger = structlog.get_logger(__name__)


class DomainProfile:
    def __init__(self, domain: str):
        self.domain = domain
        self.total_requests = 0
        self.successful = 0
        self.blocked = 0
        self.timeout_count = 0
        self.parser_errors = 0
        self.avg_response_time_ms = 0.0
        self.last_fetch_mode: str | None = None
        self.js_required: bool = False
        self.anti_bot_likely: bool = False
        self.common_selectors: dict[str, list[str]] = {}
        self.last_seen: float = time.time()

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful / self.total_requests

    @property
    def blocked_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.blocked / self.total_requests

    def record(self, success: bool, blocked: bool = False, timeout: bool = False,
               parser_error: bool = False, response_time_ms: float = 0.0):
        self.total_requests += 1
        if success:
            self.successful += 1
        if blocked:
            self.blocked += 1
        if timeout:
            self.timeout_count += 1
        if parser_error:
            self.parser_errors += 1
        self.avg_response_time_ms = (
            (self.avg_response_time_ms * (self.total_requests - 1) + response_time_ms)
            / self.total_requests
        )
        self.last_seen = time.time()

    def suggested_fetch_mode(self) -> str:
        if self.success_rate < 0.2 and self.blocked_rate > 0.3:
            self.anti_bot_likely = True
            return FetchMode.STEALTH
        if self.success_rate < 0.5 and self.blocked > 2:
            return FetchMode.STEALTH
        if self.js_required:
            return FetchMode.DYNAMIC
        if self.success_rate > 0.8:
            return FetchMode.STATIC
        return FetchMode.DYNAMIC

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "total_requests": self.total_requests,
            "success_rate": round(self.success_rate, 3),
            "blocked_rate": round(self.blocked_rate, 3),
            "timeout_count": self.timeout_count,
            "parser_errors": self.parser_errors,
            "avg_response_time_ms": round(self.avg_response_time_ms, 1),
            "suggested_fetch_mode": self.suggested_fetch_mode(),
            "js_required": self.js_required,
            "anti_bot_likely": self.anti_bot_likely,
        }


class SourcePatternLearner:
    def __init__(self):
        self._profiles: dict[str, DomainProfile] = {}
        self._pattern_cache: dict[str, dict] = {}
        self._domain_cache: dict[str, dict] = {}
        self._load_default_patterns()

    def _load_default_patterns(self):
        self._pattern_cache = {
            "jobs": {
                "common_fields": [
                    "title", "company", "location", "salary", "description",
                    "experience", "skills", "job_type", "posted_date",
                ],
                "selectors": {
                    "title": ["h1", ".job-title", "[data-testid='job-title']"],
                    "company": [".company-name", "[data-testid='company']", ".employer"],
                    "location": [".location", "[data-testid='location']"],
                    "salary": [".salary", "[data-testid='salary']"],
                },
            },
            "general": {
                "common_fields": ["title", "content", "url"],
                "selectors": {
                    "title": ["h1", "title"],
                    "content": ["article", "main", ".content"],
                },
            },
        }

    def _extract_domain(self, url: str) -> str:
        parsed = urlparse(url)
        return parsed.netloc or "unknown"

    def _classify_data_type(self, fields: set[str]) -> str:
        job_fields = {"salary", "experience", "company", "job", "hiring", "skills", "resume"}
        if any(f in fields for f in job_fields):
            return "jobs"
        return "general"

    def get_profile(self, url: str) -> DomainProfile:
        domain = self._extract_domain(url)
        if domain not in self._profiles:
            self._profiles[domain] = DomainProfile(domain)
        return self._profiles[domain]

    def record_result(self, url: str, result_status: str, response_time_ms: float = 0.0):
        profile = self.get_profile(url)
        profile.record(
            success=result_status == "success",
            blocked=result_status == "blocked",
            timeout=result_status == "timeout",
            parser_error=result_status == "parser_error",
            response_time_ms=response_time_ms,
        )

    def suggest_fetch_mode(self, url: str) -> str:
        return self.get_profile(url).suggested_fetch_mode()

    def get_field_suggestions(self, url: str, schema_fields: set[str] | None = None) -> list[dict]:
        fields = schema_fields or set()
        data_type = self._classify_data_type(fields)
        pattern = self._pattern_cache.get(data_type, self._pattern_cache["general"])
        suggestions = []
        if pattern.get("common_fields"):
            for field in pattern["common_fields"]:
                suggestions.append({
                    "field": field,
                    "required": field in {"title", "company"},
                    "description": f"Extract {field}",
                })
        domain = self._extract_domain(url)
        domain_knowledge = self._domain_cache.get(domain, {})
        if domain_knowledge.get("common_fields"):
            for field in domain_knowledge["common_fields"]:
                if not any(s["field"] == field for s in suggestions):
                    suggestions.append({
                        "field": field,
                        "required": False,
                        "description": f"Domain-specific {field}",
                    })
        return suggestions

    def get_extraction_tips(self, url: str) -> list[str]:
        profile = self.get_profile(url)
        tips = []
        if profile.js_required:
            tips.append("Site requires JS rendering — use stealth/dynamic mode")
        if profile.anti_bot_likely:
            tips.append("Anti-bot detected — increase delays, rotate user-agents")
        if profile.blocked > 2:
            tips.append(f"Blocked {profile.blocked}x — consider proxy rotation")
        if profile.success_rate < 0.5 and profile.total_requests > 3:
            tips.append("Low success rate — try different fetch strategy")
        if profile.avg_response_time_ms > 5000:
            tips.append("Slow responses — consider increasing timeout")
        return tips

    def suggest_optimizations(self, url: str) -> list[dict]:
        profile = self.get_profile(url)
        opts = []

        if profile.total_requests > 5 and profile.success_rate > 0.8:
            opts.append({
                "type": "fetch_mode",
                "suggestion": f"Try static mode for {profile.domain} (current: {profile.last_fetch_mode})",
                "confidence": 0.7,
            })

        if profile.blocked_rate > 0.3:
            opts.append({
                "type": "stealth_upgrade",
                "suggestion": f"Upgrade to stealth mode for {profile.domain} — {profile.blocked_rate:.0%} blocked",
                "confidence": 0.9,
            })

        if profile.avg_response_time_ms > 3000:
            opts.append({
                "type": "timeout_increase",
                "suggestion": f"Increase timeout — avg response is {profile.avg_response_time_ms:.0f}ms",
                "confidence": 0.8,
            })

        if profile.total_requests > 10 and profile.success_rate < 0.4:
            opts.append({
                "type": "disable_source",
                "suggestion": f"Consider disabling {profile.domain} — {profile.success_rate:.0%} success rate",
                "confidence": 0.95,
            })

        return opts

    def summary(self) -> dict[str, dict]:
        return {d: p.to_dict() for d, p in self._profiles.items()}
