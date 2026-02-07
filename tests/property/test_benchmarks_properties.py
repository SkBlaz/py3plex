#!/usr/bin/env python3
"""Property-based tests for the benchmarks module.

This module tests properties of the Budget class and metric registry,
ensuring correctness of benchmarking utilities.

Key properties tested:
- Budget tracking is consistent
- Budget exhaustion is correctly detected
- Metric registration is idempotent
- Metric computation is deterministic
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import note
import time

# Import benchmarks module
try:
    from py3plex.benchmarks.budget import Budget, BudgetExhaustedException
    from py3plex.benchmarks.metrics import (
        CommunityMetric,
        register_metric,
        get_metric,
        metric_registry,
    )
    BENCHMARKS_AVAILABLE = True
except ImportError:
    BENCHMARKS_AVAILABLE = False
    pytest.skip("Benchmarks module not available", allow_module_level=True)


# ============================================================================
# Helper Strategies
# ============================================================================

@st.composite
def budget_params(draw):
    """Generate valid budget parameters."""
    # At least one limit must be non-None
    has_time = draw(st.booleans())
    has_evals = draw(st.booleans())
    
    # Ensure at least one is True
    if not has_time and not has_evals:
        has_time = True
    
    limit_ms = draw(st.floats(min_value=100.0, max_value=10000.0)) if has_time else None
    limit_evals = draw(st.integers(min_value=10, max_value=1000)) if has_evals else None
    
    return {"limit_ms": limit_ms, "limit_evals": limit_evals}


@st.composite
def charge_amounts(draw):
    """Generate valid charge amounts."""
    ms = draw(st.floats(min_value=0.0, max_value=1000.0))
    evals = draw(st.integers(min_value=0, max_value=100))
    return {"ms": ms, "evals": evals}


# ============================================================================
# Property Tests: Budget Creation
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(params=budget_params())
def test_budget_creation_valid(params):
    """Property: Budget can be created with valid parameters."""
    budget = Budget(**params)
    
    assert budget.limit_ms == params["limit_ms"]
    assert budget.limit_evals == params["limit_evals"]
    assert budget.used_ms == 0.0
    assert budget.eval_count == 0
    assert isinstance(budget.start_time, float)


@pytest.mark.property
def test_budget_requires_at_least_one_limit():
    """Property: Budget creation fails without any limits."""
    with pytest.raises(ValueError, match="at least one limit"):
        Budget(limit_ms=None, limit_evals=None)


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(limit_ms=st.floats(min_value=100.0, max_value=10000.0))
def test_budget_time_only_valid(limit_ms):
    """Property: Budget can be created with only time limit."""
    budget = Budget(limit_ms=limit_ms)
    
    assert budget.limit_ms == limit_ms
    assert budget.limit_evals is None
    assert not budget.exhausted()


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(limit_evals=st.integers(min_value=10, max_value=1000))
def test_budget_evals_only_valid(limit_evals):
    """Property: Budget can be created with only eval limit."""
    budget = Budget(limit_evals=limit_evals)
    
    assert budget.limit_ms is None
    assert budget.limit_evals == limit_evals
    assert not budget.exhausted()


# ============================================================================
# Property Tests: Budget Charging
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    params=budget_params(),
    charges=st.lists(charge_amounts(), min_size=1, max_size=10)
)
def test_budget_charge_accumulates(params, charges):
    """Property: Charges accumulate correctly."""
    budget = Budget(**params)
    
    total_ms = 0.0
    total_evals = 0
    
    for charge in charges:
        budget.charge(**charge)
        total_ms += charge["ms"]
        total_evals += charge["evals"]
    
    # Allow small floating point errors
    assert abs(budget.used_ms - total_ms) < 1e-6
    assert budget.eval_count == total_evals


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    limit_ms=st.floats(min_value=100.0, max_value=1000.0),
    charge_ms=st.floats(min_value=0.0, max_value=50.0)
)
def test_budget_charge_does_not_exceed_before_exhaustion(limit_ms, charge_ms):
    """Property: Budget not exhausted before limit is reached."""
    budget = Budget(limit_ms=limit_ms)
    
    # Charge less than limit
    if charge_ms < limit_ms:
        budget.charge(ms=charge_ms)
        assert not budget.exhausted()


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    limit_ms=st.floats(min_value=100.0, max_value=1000.0),
    excess=st.floats(min_value=1.0, max_value=100.0)
)
def test_budget_exhausted_when_limit_exceeded(limit_ms, excess):
    """Property: Budget exhausted when limit is exceeded."""
    budget = Budget(limit_ms=limit_ms)
    
    # Charge more than limit
    budget.charge(ms=limit_ms + excess)
    assert budget.exhausted()


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    limit_evals=st.integers(min_value=10, max_value=100),
    evals=st.integers(min_value=1, max_value=5)
)
def test_budget_evals_exhaustion(limit_evals, evals):
    """Property: Budget exhausted when eval count exceeds limit."""
    budget = Budget(limit_evals=limit_evals)
    
    # Charge exactly to or over limit
    charges_needed = (limit_evals // evals) + 1
    
    for _ in range(charges_needed):
        budget.charge(evals=evals)
    
    assert budget.eval_count >= limit_evals
    assert budget.exhausted()


# ============================================================================
# Property Tests: Budget Remaining
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    limit_ms=st.floats(min_value=100.0, max_value=1000.0),
    used_ms=st.floats(min_value=0.0, max_value=50.0)
)
def test_budget_remaining_ms_correct(limit_ms, used_ms):
    """Property: Remaining milliseconds computed correctly."""
    assume(used_ms < limit_ms)
    
    budget = Budget(limit_ms=limit_ms)
    budget.charge(ms=used_ms)
    
    remaining = budget.remaining_ms()
    assert remaining is not None
    assert abs(remaining - (limit_ms - used_ms)) < 1e-6


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    limit_evals=st.integers(min_value=10, max_value=100),
    used_evals=st.integers(min_value=0, max_value=5)
)
def test_budget_remaining_evals_correct(limit_evals, used_evals):
    """Property: Remaining evaluations computed correctly."""
    assume(used_evals < limit_evals)
    
    budget = Budget(limit_evals=limit_evals)
    budget.charge(evals=used_evals)
    
    remaining = budget.remaining_evals()
    assert remaining is not None
    assert remaining == limit_evals - used_evals


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(limit_ms=st.floats(min_value=100.0, max_value=1000.0))
def test_budget_remaining_non_negative(limit_ms):
    """Property: Remaining budget is never negative."""
    budget = Budget(limit_ms=limit_ms)
    
    # Charge way over limit
    budget.charge(ms=limit_ms * 2)
    
    remaining = budget.remaining_ms()
    assert remaining is not None
    assert remaining >= 0.0


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(limit_evals=st.integers(min_value=10, max_value=100))
def test_budget_no_time_limit_returns_none(limit_evals):
    """Property: remaining_ms() returns None when no time limit."""
    budget = Budget(limit_evals=limit_evals)
    assert budget.remaining_ms() is None


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(limit_ms=st.floats(min_value=100.0, max_value=1000.0))
def test_budget_no_eval_limit_returns_none(limit_ms):
    """Property: remaining_evals() returns None when no eval limit."""
    budget = Budget(limit_ms=limit_ms)
    assert budget.remaining_evals() is None


# ============================================================================
# Property Tests: Budget Reset
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    params=budget_params(),
    charges=st.lists(charge_amounts(), min_size=1, max_size=5)
)
def test_budget_reset_clears_usage(params, charges):
    """Property: Reset clears usage but preserves limits."""
    budget = Budget(**params)
    
    # Charge some amount
    for charge in charges:
        budget.charge(**charge)
    
    # Reset
    budget.reset()
    
    # Usage should be zero, limits preserved
    assert budget.used_ms == 0.0
    assert budget.eval_count == 0
    assert budget.limit_ms == params["limit_ms"]
    assert budget.limit_evals == params["limit_evals"]
    assert not budget.exhausted()


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(params=budget_params())
def test_budget_reset_updates_start_time(params):
    """Property: Reset updates start time."""
    budget = Budget(**params)
    
    old_start = budget.start_time
    time.sleep(0.01)  # Small delay
    
    budget.reset()
    new_start = budget.start_time
    
    assert new_start > old_start


# ============================================================================
# Property Tests: Budget Serialization
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    params=budget_params(),
    charge=charge_amounts()
)
def test_budget_to_dict_contains_required_fields(params, charge):
    """Property: to_dict() contains all required fields."""
    budget = Budget(**params)
    budget.charge(**charge)
    
    result = budget.to_dict()
    
    assert "limit_ms" in result
    assert "limit_evals" in result
    assert "used_ms" in result
    assert "eval_count" in result
    assert "exhausted" in result
    
    assert result["limit_ms"] == params["limit_ms"]
    assert result["limit_evals"] == params["limit_evals"]
    assert result["exhausted"] == budget.exhausted()


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(params=budget_params())
def test_budget_to_dict_reflects_state(params):
    """Property: to_dict() reflects current budget state."""
    budget = Budget(**params)
    
    dict1 = budget.to_dict()
    assert dict1["used_ms"] == 0.0
    assert dict1["eval_count"] == 0
    assert not dict1["exhausted"]
    
    # Charge and check again
    budget.charge(ms=50.0, evals=5)
    dict2 = budget.to_dict()
    
    assert dict2["used_ms"] == 50.0
    assert dict2["eval_count"] == 5


# ============================================================================
# Property Tests: Metric Registry
# ============================================================================

def dummy_metric(network, partition, layers, **ctx):
    """Dummy metric for testing."""
    return 0.5


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    name=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")), min_size=3, max_size=20),
    description=st.text(min_size=0, max_size=100)
)
def test_metric_registration_succeeds(name, description):
    """Property: Metrics can be registered with valid names."""
    # Clear registry first
    metric_registry.clear()
    
    register_metric(name, dummy_metric, description)
    
    metric = get_metric(name)
    assert metric is not None
    assert metric.name == name
    assert metric.description == description


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(name=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")), min_size=3, max_size=20))
def test_metric_registration_idempotent(name):
    """Property: Registering same metric twice overwrites."""
    metric_registry.clear()
    
    register_metric(name, dummy_metric, "First")
    register_metric(name, dummy_metric, "Second")
    
    metric = get_metric(name)
    assert metric is not None
    assert metric.description == "Second"


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(name=st.text(min_size=1, max_size=20))
def test_get_nonexistent_metric_returns_none(name):
    """Property: Getting nonexistent metric returns None."""
    metric_registry.clear()
    
    # Don't register anything
    metric = get_metric(name)
    assert metric is None


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(name=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")), min_size=3, max_size=20))
def test_community_metric_dataclass_properties(name):
    """Property: CommunityMetric has correct default values."""
    metric_registry.clear()
    
    register_metric(name, dummy_metric)
    metric = get_metric(name)
    
    assert metric.requires_network is True  # Default
    assert metric.requires_uq is False  # Default
    assert callable(metric.func)


# ============================================================================
# Property Tests: Budget Edge Cases
# ============================================================================

@pytest.mark.property
def test_budget_zero_charges_work():
    """Property: Charging zero amounts is valid."""
    budget = Budget(limit_ms=100.0, limit_evals=10)
    
    budget.charge(ms=0.0, evals=0)
    
    assert budget.used_ms == 0.0
    assert budget.eval_count == 0
    assert not budget.exhausted()


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    limit_ms=st.floats(min_value=10.0, max_value=100.0),
    charge_ms=st.floats(min_value=0.0, max_value=5.0)
)
def test_budget_multiple_charges_before_exhaustion(limit_ms, charge_ms):
    """Property: Multiple small charges accumulate correctly."""
    budget = Budget(limit_ms=limit_ms)
    
    # Make multiple small charges
    n_charges = int(limit_ms / (charge_ms + 1)) if charge_ms > 0 else 0
    
    for _ in range(n_charges):
        if not budget.exhausted():
            budget.charge(ms=charge_ms)
    
    # Should have accumulated
    expected_total = n_charges * charge_ms
    assert abs(budget.used_ms - expected_total) < 1e-6


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(limit_ms=st.floats(min_value=100.0, max_value=1000.0))
def test_budget_exact_limit_is_exhausted(limit_ms):
    """Property: Charging exactly to limit exhausts budget."""
    budget = Budget(limit_ms=limit_ms)
    
    budget.charge(ms=limit_ms)
    
    assert budget.exhausted()
    assert budget.remaining_ms() == 0.0


# ============================================================================
# Property Tests: Budget Monotonicity
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    params=budget_params(),
    charge1=charge_amounts(),
    charge2=charge_amounts()
)
def test_budget_usage_monotonic(params, charge1, charge2):
    """Property: Budget usage is monotonically increasing."""
    budget = Budget(**params)
    
    budget.charge(**charge1)
    used_after_1 = budget.used_ms
    evals_after_1 = budget.eval_count
    
    budget.charge(**charge2)
    used_after_2 = budget.used_ms
    evals_after_2 = budget.eval_count
    
    # Usage should increase (or stay same for zero charges)
    assert used_after_2 >= used_after_1
    assert evals_after_2 >= evals_after_1


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(params=budget_params())
def test_budget_exhaustion_monotonic(params):
    """Property: Once exhausted, budget stays exhausted."""
    budget = Budget(**params)
    
    # Charge enough to exhaust
    if params["limit_ms"] is not None:
        budget.charge(ms=params["limit_ms"] * 2)
    else:
        budget.charge(evals=params["limit_evals"] * 2)
    
    assert budget.exhausted()
    
    # Charge more - should still be exhausted
    budget.charge(ms=10.0, evals=1)
    assert budget.exhausted()
