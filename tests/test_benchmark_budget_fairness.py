"""Tests for budget fairness and enforcement.

Tests that budgets are enforced fairly across algorithms and configs.
"""

import pytest
from py3plex.benchmarks.budget import Budget, BudgetExhaustedException


class TestBudgetClass:
    """Tests for Budget class."""

    def test_budget_creation_time_only(self):
        """Test creating budget with time limit only."""
        budget = Budget(limit_ms=5000)
        assert budget.limit_ms == 5000
        assert budget.limit_evals is None
        assert budget.used_ms == 0.0
        assert budget.eval_count == 0

    def test_budget_creation_evals_only(self):
        """Test creating budget with eval limit only."""
        budget = Budget(limit_evals=100)
        assert budget.limit_ms is None
        assert budget.limit_evals == 100

    def test_budget_creation_both(self):
        """Test creating budget with both limits."""
        budget = Budget(limit_ms=5000, limit_evals=100)
        assert budget.limit_ms == 5000
        assert budget.limit_evals == 100

    def test_budget_creation_invalid(self):
        """Test that budget requires at least one limit."""
        with pytest.raises(ValueError, match="at least one limit"):
            Budget()

    def test_budget_charge(self):
        """Test charging the budget."""
        budget = Budget(limit_ms=5000, limit_evals=100)

        budget.charge(ms=250, evals=1)
        assert budget.used_ms == 250
        assert budget.eval_count == 1

        budget.charge(ms=500, evals=2)
        assert budget.used_ms == 750
        assert budget.eval_count == 3

    def test_budget_exhausted_time(self):
        """Test time-based exhaustion."""
        budget = Budget(limit_ms=1000)

        assert not budget.exhausted()

        budget.charge(ms=500)
        assert not budget.exhausted()

        budget.charge(ms=500)
        assert budget.exhausted()

        budget.charge(ms=100)
        assert budget.exhausted()

    def test_budget_exhausted_evals(self):
        """Test eval-based exhaustion."""
        budget = Budget(limit_evals=10)

        for i in range(9):
            budget.charge(evals=1)
            assert not budget.exhausted()

        budget.charge(evals=1)
        assert budget.exhausted()

    def test_budget_exhausted_either(self):
        """Test exhaustion when either limit is reached."""
        budget = Budget(limit_ms=1000, limit_evals=10)

        # Exhaust time first
        budget.charge(ms=1000, evals=5)
        assert budget.exhausted()

        # Reset
        budget.reset()

        # Exhaust evals first
        budget.charge(ms=500, evals=10)
        assert budget.exhausted()

    def test_budget_remaining(self):
        """Test remaining budget calculations."""
        budget = Budget(limit_ms=1000, limit_evals=10)

        assert budget.remaining_ms() == 1000
        assert budget.remaining_evals() == 10

        budget.charge(ms=300, evals=3)

        assert budget.remaining_ms() == 700
        assert budget.remaining_evals() == 7

        # Exhaust time
        budget.charge(ms=700)
        assert budget.remaining_ms() == 0
        assert budget.remaining_evals() == 7

    def test_budget_reset(self):
        """Test budget reset."""
        budget = Budget(limit_ms=1000, limit_evals=10)

        budget.charge(ms=500, evals=5)
        assert budget.used_ms == 500
        assert budget.eval_count == 5

        budget.reset()
        assert budget.used_ms == 0
        assert budget.eval_count == 0
        assert budget.limit_ms == 1000
        assert budget.limit_evals == 10

    def test_budget_to_dict(self):
        """Test budget serialization."""
        budget = Budget(limit_ms=1000, limit_evals=10)
        budget.charge(ms=300, evals=3)

        d = budget.to_dict()

        assert d["limit_ms"] == 1000
        assert d["limit_evals"] == 10
        assert d["used_ms"] == 300
        assert d["eval_count"] == 3
        assert d["exhausted"] is False


class TestBudgetFairness:
    """Tests for budget fairness in benchmarks."""

    def test_grid_expansion_deterministic(self):
        """Test that grid expansion is deterministic."""
        from py3plex.dsl.executors.benchmark_executor import _expand_grid

        # Test with a grid spec
        params = {
            "gamma": [0.8, 1.0, 1.2],
            "n_iter": [2, 5],
        }

        # Expand multiple times
        configs1 = _expand_grid(params)
        configs2 = _expand_grid(params)

        assert len(configs1) == 6  # 3 * 2
        assert configs1 == configs2  # Same order

        # Check ordering is stable
        for i, config in enumerate(configs1):
            assert "gamma" in config
            assert "n_iter" in config

    def test_config_id_stable(self):
        """Test that config IDs are stable."""
        from py3plex.benchmarks.runners import compute_config_id

        params1 = {"gamma": 1.0, "n_iter": 2}
        params2 = {"n_iter": 2, "gamma": 1.0}  # Different order

        id1 = compute_config_id(params1)
        id2 = compute_config_id(params2)

        assert id1 == id2  # Same hash despite order

        # Different params = different ID
        params3 = {"gamma": 1.2, "n_iter": 2}
        id3 = compute_config_id(params3)

        assert id1 != id3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
