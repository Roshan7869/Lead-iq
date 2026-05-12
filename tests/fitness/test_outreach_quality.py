"""Outreach quality gate fitness tests - refuse specificity < 7.0"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "backend"))

try:
    from backend.workers.outreach_scorer import gate_outreach, score_outreach_draft
    HAS_SCORER = True
except ImportError:
    HAS_SCORER = False


@pytest.mark.skipif(not HAS_SCORER, reason="outreach_scorer module not yet created")
class TestOutreachQualityGate:
    """All tests requiring the outreach_scorer module."""

    def test_spam_draft_is_refused(self):
        spam_drafts = [
            "Hi, I hope this finds you well. Would love to connect!",
            "I noticed your post and wanted to reach out and touch base.",
            "Checking in to see if you'd like to explore synergies!",
        ]
        for draft in spam_drafts:
            result, score = gate_outreach(draft, "CRM pain", "pain")
            assert result is None, f"Spam draft should be refused, got score={score}"
            assert score < 7.0, f"Spam score {score} should be < 7.0"

    def test_specific_draft_passes(self):
        good_cases = [
            ("Your post about SDR manual research hit home — we cut research time by 60% for 12-rep teams. 15 mins this week?",
             "SDR team drowning in manual research", "pain"),
        ]
        for draft, source, intent in good_cases:
            result, score = gate_outreach(draft, source, intent)
            assert result is not None, f"Specific draft should pass, got score={score}"
            assert score >= 7.0

    def test_none_draft_returns_zero(self):
        result, score = gate_outreach(None, "any source", "buy")
        assert result is None
        assert score == 0.0

    def test_short_draft_refused(self):
        result, score = gate_outreach("Hi there!", "any source", "buy")
        assert result is None
        assert score < 7.0
