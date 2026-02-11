"""Tests for py3plex.benchmarks.budget module.

Tests budget tracking for fair algorithm comparisons.
"""

import time
import pytest
from py3plex.benchmarks.budget import Budget, BudgetExhaustedException


class TestBudgetCreation:
    """Test Budget creation and validation."""

    def test_create_budget_with_time_limit(self):
        """Test creating budget with only time limit."""
        budget = Budget(limit_ms=5000)
        assert budget.limit_ms == 5000
        assert budget.limit_evals is None
        assert budget.used_ms == 0.0
        assert budget.eval_count == 0

    def test_create_budget_with_eval_limit(self):
        """Test creating budget with only eval limit."""
        budget = Budget(limit_evals=100)
        assert budget.limit_ms is None
        assert budget.limit_evals == 100
        assert budget.used_ms == 0.0
        assert budget.eval_count == 0

    def test_create_budget_with_both_limits(self):
        """Test creating budget with both limits."""
        budget = Budget(limit_ms=5000, limit_evals=100)
        assert budget.limit_ms == 5000
        assert budget.limit_evals == 100

    def test_create_budget_without_limits_raises(self):
        """Test that creating budget without limits raises ValueError."""
        with pytest.raises(ValueError, match="must specify at least one limit"):
            Budget()

    def test_start_time_is_set(self):
        """Test that start_time is automatically set."""
        before = time.time()
        budget = Budget(limit_ms=1000)
        after = time.time()
        assert before <= budget.start_time <= after


class TestBudgetCharging:
    """Test budget charging operations."""

    def test_charge_time_only(self):
        """Test charging only time."""
        budget = Budget(limit_ms=5000)
        budget.charge(ms=1500)
        assert budget.used_ms == 1500
        assert budget.eval_count == 0

    def test_charge_evals_only(self):
        """Test charging only evaluations."""
        budget = Budget(limit_evals=100)
        budget.charge(evals=25)
        assert budget.used_ms == 0.0
        assert budget.eval_count == 25

    def test_charge_both(self):
        """Test charging both time and evaluations."""
        budget = Budget(limit_ms=5000, limit_evals=100)
        budget.charge(ms=1500, evals=25)
        assert budget.used_ms == 1500
        assert budget.eval_count == 25

    def test_charge_accumulates(self):
        """Test that charges accumulate."""
        budget = Budget(limit_ms=5000, limit_evals=100)
        budget.charge(ms=1000, evals=10)
        budget.charge(ms=500, evals=5)
        budget.charge(ms=250, evals=2)
        
        assert budget.used_ms == 1750
        assert budget.eval_count == 17

    def test_charge_with_defaults(self):
        """Test charging with default values (no change)."""
        budget = Budget(limit_ms=5000)
        budget.charge()
        assert budget.used_ms == 0.0
        assert budget.eval_count == 0


class TestBudgetExhaustion:
    """Test budget exhaustion detection."""

    def test_not_exhausted_initially(self):
        """Test budget not exhausted when created."""
        budget = Budget(limit_ms=5000, limit_evals=100)
        assert budget.exhausted() is False

    def test_exhausted_when_time_limit_exceeded(self):
        """Test budget exhausted when time limit exceeded."""
        budget = Budget(limit_ms=1000)
        budget.charge(ms=1001)
        assert budget.exhausted() is True

    def test_exhausted_when_time_limit_met(self):
        """Test budget exhausted when time limit exactly met."""
        budget = Budget(limit_ms=1000)
        budget.charge(ms=1000)
        assert budget.exhausted() is True

    def test_exhausted_when_eval_limit_exceeded(self):
        """Test budget exhausted when eval limit exceeded."""
        budget = Budget(limit_evals=50)
        budget.charge(evals=51)
        assert budget.exhausted() is True

    def test_exhausted_when_eval_limit_met(self):
        """Test budget exhausted when eval limit exactly met."""
        budget = Budget(limit_evals=50)
        budget.charge(evals=50)
        assert budget.exhausted() is True

    def test_exhausted_when_either_limit_exceeded(self):
        """Test budget exhausted when either limit exceeded."""
        budget = Budget(limit_ms=1000, limit_evals=50)
        
        # Exceed time but not evals
        budget.charge(ms=1001, evals=10)
        assert budget.exhausted() is True
        
        # Reset and test other way
        budget.reset()
        budget.charge(ms=500, evals=51)
        assert budget.exhausted() is True


class TestBudgetRemaining:
    """Test remaining budget calculations."""

    def test_remaining_ms_with_limit(self):
        """Test remaining milliseconds when limit set."""
        budget = Budget(limit_ms=5000)
        assert budget.remaining_ms() == 5000
        
        budget.charge(ms=1500)
        assert budget.remaining_ms() == 3500
        
        budget.charge(ms=1500)
        assert budget.remaining_ms() == 2000

    def test_remaining_ms_never_negative(self):
        """Test that remaining_ms never goes negative."""
        budget = Budget(limit_ms=1000)
        budget.charge(ms=2000)
        assert budget.remaining_ms() == 0.0

    def test_remaining_ms_when_no_limit(self):
        """Test remaining_ms returns None when no limit."""
        budget = Budget(limit_evals=100)
        assert budget.remaining_ms() is None

    def test_remaining_evals_with_limit(self):
        """Test remaining evaluations when limit set."""
        budget = Budget(limit_evals=100)
        assert budget.remaining_evals() == 100
        
        budget.charge(evals=25)
        assert budget.remaining_evals() == 75
        
        budget.charge(evals=25)
        assert budget.remaining_evals() == 50

    def test_remaining_evals_never_negative(self):
        """Test that remaining_evals never goes negative."""
        budget = Budget(limit_evals=50)
        budget.charge(evals=75)
        assert budget.remaining_evals() == 0

    def test_remaining_evals_when_no_limit(self):
        """Test remaining_evals returns None when no limit."""
        budget = Budget(limit_ms=5000)
        assert budget.remaining_evals() is None


class TestBudgetSerialization:
    """Test budget serialization."""

    def test_to_dict_structure(self):
        """Test that to_dict returns correct structure."""
        budget = Budget(limit_ms=5000, limit_evals=100)
        budget.charge(ms=1500, evals=25)
        
        data = budget.to_dict()
        
        assert isinstance(data, dict)
        assert "limit_ms" in data
        assert "limit_evals" in data
        assert "used_ms" in data
        assert "eval_count" in data
        assert "exhausted" in data

    def test_to_dict_values(self):
        """Test that to_dict returns correct values."""
        budget = Budget(limit_ms=5000, limit_evals=100)
        budget.charge(ms=1500, evals=25)
        
        data = budget.to_dict()
        
        assert data["limit_ms"] == 5000
        assert data["limit_evals"] == 100
        assert data["used_ms"] == 1500
        assert data["eval_count"] == 25
        assert data["exhausted"] is False

    def test_to_dict_exhausted_flag(self):
        """Test that to_dict includes correct exhausted flag."""
        budget = Budget(limit_ms=1000)
        
        # Not exhausted
        data = budget.to_dict()
        assert data["exhausted"] is False
        
        # Exhausted
        budget.charge(ms=1000)
        data = budget.to_dict()
        assert data["exhausted"] is True


class TestBudgetReset:
    """Test budget reset functionality."""

    def test_reset_clears_usage(self):
        """Test that reset clears usage counters."""
        budget = Budget(limit_ms=5000, limit_evals=100)
        budget.charge(ms=1500, evals=25)
        
        budget.reset()
        
        assert budget.used_ms == 0.0
        assert budget.eval_count == 0
        assert budget.exhausted() is False

    def test_reset_preserves_limits(self):
        """Test that reset preserves limits."""
        budget = Budget(limit_ms=5000, limit_evals=100)
        budget.charge(ms=1500, evals=25)
        
        budget.reset()
        
        assert budget.limit_ms == 5000
        assert budget.limit_evals == 100

    def test_reset_updates_start_time(self):
        """Test that reset updates start time."""
        budget = Budget(limit_ms=5000)
        old_start = budget.start_time
        
        time.sleep(0.01)  # Small delay
        budget.reset()
        
        assert budget.start_time > old_start
