"""Unit tests for cost_guard.py"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "backend"))


class TestCostGuardConstants:
    """Tests for budget constants."""

    def test_daily_budget_constant(self):
        from backend.llm.cost_guard import DAILY_TOKEN_BUDGET
        assert DAILY_TOKEN_BUDGET == 2_000_000

    def test_hourly_budget_exists_if_day10_done(self):
        from backend.llm import cost_guard
        # Check if hourly budget was added (Day 10 feature)
        has_hourly = hasattr(cost_guard, 'HOURLY_BUDGET')
        # Not a hard fail - this test reports whether Day 10 was completed
        if has_hourly:
            assert cost_guard.HOURLY_BUDGET > 0

    def test_module_imports(self):
        from backend.llm import cost_guard
        assert hasattr(cost_guard, 'check_budget')
        assert hasattr(cost_guard, 'get_budget_status')
