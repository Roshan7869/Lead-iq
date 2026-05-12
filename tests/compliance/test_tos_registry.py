"""tests/compliance/test_tos_registry.py — Day 12 compliance tests."""
import pytest
from backend.compliance.tos_registry import (
    RiskLevel,
    SourceCompliance,
    check_source_compliance,
    get_blocked_sources,
    get_allowed_sources,
    get_compliance_summary,
    COMPLIANCE_REGISTRY,
)


class TestSourceCompliance:
    def test_all_sources_have_entries(self):
        expected = ["github", "hn", "reddit", "telegram", "twitter", "rss", "producthunt", "stackoverflow"]
        for s in expected:
            assert s in COMPLIANCE_REGISTRY, f"{s} missing from registry"

    def test_no_critical_sources_blocked(self):
        blocked = get_blocked_sources()
        assert isinstance(blocked, list)

    def test_allowed_sources_excludes_high(self):
        allowed = get_allowed_sources()
        assert "twitter" not in allowed  # high risk

    def test_check_known_source(self):
        result = check_source_compliance("github")
        assert result["status"] == "allowed"
        assert result["risk_level"] == "low"

    def test_check_unknown_source_blocks(self):
        result = check_source_compliance("darkweb_forum")
        assert result["status"] == "blocked"
        assert "unknown" in result.get("reason", "").lower()

    def test_check_twitter_restricted(self):
        result = check_source_compliance("twitter")
        assert result["status"] == "restricted"
        assert result["risk_level"] == "high"

    def test_summary_has_all_keys(self):
        s = get_compliance_summary()
        assert "total_sources" in s
        assert "blocked_sources" in s
        assert "allowed_sources" in s
        assert s["total_sources"] == 8

    def test_source_compliance_frozen(self):
        """SourceCompliance is frozen — cannot be mutated post creation."""
        from dataclasses import FrozenInstanceError
        entry = COMPLIANCE_REGISTRY["github"]
        with pytest.raises(FrozenInstanceError):
            entry.risk_level = RiskLevel.critical  # type: ignore[misc]
