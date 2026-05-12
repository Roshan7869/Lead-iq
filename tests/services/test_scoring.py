"""tests/services/test_scoring.py — Day 15-17 tests."""
import pytest
from datetime import datetime, timedelta, timezone


class TestTemporalDecay:
    def test_hiring_half_life_72_hours(self):
        from backend.services.temporal_decay import get_half_life
        assert get_half_life("hiring") == 72.0

    def test_b2b_sales_half_life_336_hours(self):
        from backend.services.temporal_decay import get_half_life
        assert get_half_life("b2b_sales") == 336.0

    def test_decay_at_half_life_is_0_5(self):
        from backend.services.temporal_decay import compute_decay_factor
        old = datetime.now(timezone.utc) - timedelta(hours=72)
        factor = compute_decay_factor(old, "hiring")
        assert 0.49 <= factor <= 0.51

    def test_decay_never_below_min(self):
        from backend.services.temporal_decay import compute_decay_factor
        old = datetime.now(timezone.utc) - timedelta(hours=720)  # 30 days
        factor = compute_decay_factor(old, "hiring")
        assert factor >= 0.05

    def test_fresh_post_is_1_0(self):
        from backend.services.temporal_decay import compute_decay_factor
        now = datetime.now(timezone.utc)
        assert compute_decay_factor(now, "hiring") == pytest.approx(1.0)

    def test_missing_timestamp_is_0_5(self):
        from backend.services.temporal_decay import compute_decay_factor
        assert compute_decay_factor(None) == 0.5

    def test_apply_decay_reduces_score(self):
        from backend.services.temporal_decay import apply_decay
        old = datetime.now(timezone.utc) - timedelta(hours=72)
        decayed = apply_decay(10.0, old, "hiring")
        assert 4.5 < decayed < 5.5  # ~5.0 (50% of 10)

    def test_b2b_decays_slower_than_hiring(self):
        from backend.services.temporal_decay import compute_decay_factor
        old = datetime.now(timezone.utc) - timedelta(hours=72)
        hiring_factor = compute_decay_factor(old, "hiring")
        b2b_factor = compute_decay_factor(old, "b2b_sales")
        assert b2b_factor > hiring_factor


class TestIcpScorer:
    def test_sigmoid_center_is_0_5(self):
        from backend.services.icp_scorer import sigmoid
        assert sigmoid(0) == 0.5

    def test_exact_match_scores_high(self):
        from backend.services.icp_scorer import compute_icp_score
        lead = {"industry": "SaaS", "company_size": "11-50", "intent": "hiring",
                "source": "github", "source_text": "hiring backend Python engineers for B2B"}
        icp = {"target_industries": ["SaaS"], "company_size": "11-50",
               "keywords": ["hiring", "Python", "backend"]}
        result = compute_icp_score(lead, icp)
        assert result["icp_probability"] > 0.9

    def test_no_match_scores_lower_than_match(self):
        from backend.services.icp_scorer import compute_icp_score
        lead_no_match = {"industry": "Unknown", "company_size": "10000+", "intent": "",
                         "source": "unknown", "source_text": ""}
        lead_match = {"industry": "SaaS", "company_size": "11-50", "intent": "hiring",
                      "source": "github", "source_text": "hiring engineers"}
        icp = {"target_industries": ["SaaS"], "company_size": "11-50", "keywords": ["hiring"]}
        score_no = compute_icp_score(lead_no_match, icp)["icp_probability"]
        score_yes = compute_icp_score(lead_match, icp)["icp_probability"]
        assert score_yes > score_no  # matching lead always outscores non-matching

    def test_all_features_present(self):
        from backend.services.icp_scorer import compute_icp_score
        lead = {"industry": "SaaS", "company_size": "11-50", "intent": "hiring",
                "source": "github", "source_text": "hiring engineers"}
        icp = {"target_industries": ["SaaS"], "company_size": "11-50", "keywords": ["hiring"]}
        result = compute_icp_score(lead, icp)
        features = result["feature_scores"]
        assert "industry_match" in features
        assert "company_size_match" in features
        assert "source_trust" in features
        assert "keyword_density" in features
        assert "intent_signal_strength" in features


class TestFeedbackLoop:
    def test_event_weights_known_types(self):
        from backend.services.feedback_loop import EVENT_WEIGHTS
        assert "approved" in EVENT_WEIGHTS
        assert "rejected" in EVENT_WEIGHTS
        assert "converted" in EVENT_WEIGHTS

    def test_aggregate_empty_events(self):
        from backend.services.feedback_loop import aggregate_event_impact
        result = aggregate_event_impact([])
        assert result["total_adjustment"] == 0.0
        assert result["net_direction"] == "neutral"

    def test_aggregate_positive(self):
        from backend.services.feedback_loop import aggregate_event_impact
        events = [{"event_type": "approved"}, {"event_type": "converted"}]
        result = aggregate_event_impact(events)
        assert result["total_adjustment"] > 0.3
        assert result["net_direction"] == "positive"

    def test_aggregate_negative(self):
        from backend.services.feedback_loop import aggregate_event_impact
        events = [{"event_type": "rejected"}, {"event_type": "email_bounced"}]
        result = aggregate_event_impact(events)
        assert result["total_adjustment"] < -0.3
        assert result["net_direction"] == "negative"

    def test_update_weights_positive_feedback(self):
        from backend.services.feedback_loop import update_icp_weights_from_feedback
        w = {"industry_match": 2.5, "intent_signal_strength": 3.0, "intercept": -2.0}
        impact = {"total_adjustment": 0.3}
        updated = update_icp_weights_from_feedback(w, impact)
        assert updated["industry_match"] > 2.5  # increased

    def test_update_weights_negative_feedback(self):
        from backend.services.feedback_loop import update_icp_weights_from_feedback
        w = {"industry_match": 2.5, "intent_signal_strength": 3.0, "intercept": -2.0}
        impact = {"total_adjustment": -0.3}
        updated = update_icp_weights_from_feedback(w, impact)
        assert updated["industry_match"] < 2.5  # decreased

    def test_quality_freeze_at_50_pct(self):
        from backend.services.feedback_loop import should_trigger_quality_freeze
        assert should_trigger_quality_freeze(0.50) is True

    def test_no_freeze_at_80_pct(self):
        from backend.services.feedback_loop import should_trigger_quality_freeze
        assert should_trigger_quality_freeze(0.80) is False
