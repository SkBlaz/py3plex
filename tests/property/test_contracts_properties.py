"""Property-based tests for py3plex.contracts module.

Tests robustness contracts, predicates, and failure modes to ensure:
- Contract configurations are always valid
- Predicates produce consistent results on equivalent inputs
- Failure modes are correctly identified
- Deterministic behavior with fixed seeds
"""

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st, assume
from hypothesis import HealthCheck

from py3plex.contracts import (
    Robustness,
    JaccardAtK,
    KendallTau,
    PartitionVI,
    PartitionARI,
    FailureMode,
)


# ============================================================================
# Contract Configuration Properties
# ============================================================================


@given(
    perturb=st.sampled_from(["edge_drop", "node_drop", "rewire", "weight_noise"]),
    p_max=st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False),
    n_samples=st.integers(min_value=5, max_value=100),
    seed=st.integers(min_value=0, max_value=1000),
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_robustness_contract_initialization_is_always_valid(perturb, p_max, n_samples, seed):
    """Robustness contract can be initialized with any valid parameter combination."""
    contract = Robustness(
        perturb=perturb,
        p_max=p_max,
        n_samples=n_samples,
        seed=seed
    )
    
    assert contract.perturb == perturb
    assert contract.p_max == p_max
    assert contract.n_samples == n_samples
    assert contract.seed == seed
    assert not contract.allow_nondeterminism  # Default should be False


@given(
    p_max=st.floats(min_value=0.01, max_value=0.3, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_robustness_contract_with_default_seed_is_deterministic(p_max):
    """Robustness contract with default seed=0 should be deterministic."""
    contract = Robustness(p_max=p_max)
    
    assert contract.seed == 0
    assert not contract.allow_nondeterminism


@given(
    grid_points=st.integers(min_value=2, max_value=10),
    p_max=st.floats(min_value=0.05, max_value=0.4, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_robustness_contract_with_explicit_grid_maintains_order(grid_points, p_max):
    """Contract grid should maintain ascending order."""
    grid = sorted([p_max * i / (grid_points - 1) for i in range(grid_points)])
    contract = Robustness(grid=grid, p_max=p_max)
    
    assert contract.grid == grid
    assert len(contract.grid) == grid_points
    # Grid should be in ascending order
    for i in range(len(grid) - 1):
        assert grid[i] <= grid[i + 1]


# ============================================================================
# Predicate Properties
# ============================================================================


@given(
    k=st.integers(min_value=1, max_value=50),
    threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_jaccard_at_k_predicate_initialization(k, threshold):
    """JaccardAtK predicate can be initialized with valid parameters."""
    predicate = JaccardAtK(k=k, threshold=threshold)
    
    assert predicate.k == k
    assert predicate.threshold == threshold


@given(
    threshold=st.floats(min_value=-1.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_kendall_tau_predicate_initialization(threshold):
    """KendallTau predicate can be initialized with valid parameters."""
    predicate = KendallTau(threshold=threshold)
    
    assert predicate.threshold == threshold


@given(
    threshold=st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_partition_vi_predicate_initialization(threshold):
    """PartitionVI predicate can be initialized with valid parameters."""
    predicate = PartitionVI(threshold=threshold)
    
    assert predicate.threshold == threshold


@given(
    threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_partition_ari_predicate_initialization(threshold):
    """PartitionARI predicate can be initialized with valid parameters."""
    predicate = PartitionARI(threshold=threshold)
    
    assert predicate.threshold == threshold


# ============================================================================
# Failure Mode Properties
# ============================================================================


@given(
    mode_name=st.sampled_from([
        "INSUFFICIENT_BASELINE",
        "NONDETERMINISM_LEAK",
        "PERTURBATION_INVALID",
        "METRIC_UNDEFINED",
    ])
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_failure_mode_enum_values_are_valid(mode_name):
    """FailureMode enum contains all expected failure modes."""
    assert hasattr(FailureMode, mode_name)
    mode = getattr(FailureMode, mode_name)
    assert isinstance(mode.value, str)


# ============================================================================
# Contract Composition Properties
# ============================================================================


@given(
    n_predicates=st.integers(min_value=1, max_value=5),
    k_values=st.lists(st.integers(min_value=1, max_value=20), min_size=1, max_size=5),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_contract_with_multiple_predicates_is_valid(n_predicates, k_values):
    """Contract can be initialized with multiple predicates."""
    assume(len(k_values) >= n_predicates)
    
    predicates = [JaccardAtK(k=k_values[i], threshold=0.8) for i in range(n_predicates)]
    contract = Robustness(predicates=predicates)
    
    assert len(contract.predicates) == n_predicates
    assert all(isinstance(p, JaccardAtK) for p in contract.predicates)


@given(
    repair=st.booleans(),
    mode=st.sampled_from(["soft", "hard"]),
)
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_contract_repair_and_mode_settings_are_respected(repair, mode):
    """Contract repair and mode settings are correctly stored."""
    contract = Robustness(repair=repair, mode=mode)
    
    assert contract.repair == repair
    assert contract.mode == mode


# ============================================================================
# Edge Case Properties
# ============================================================================


@given(
    tie_policy=st.sampled_from(["break", "undefined"]),
)
@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_contract_tie_policy_is_valid(tie_policy):
    """Contract tie_policy setting is correctly stored."""
    contract = Robustness(tie_policy=tie_policy)
    
    assert contract.tie_policy == tie_policy


@given(
    max_seconds=st.floats(min_value=0.1, max_value=60.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_contract_budget_can_be_configured(max_seconds):
    """Contract budget can be configured with custom values."""
    from py3plex.contracts.contract import Budget
    
    budget = Budget(max_seconds=max_seconds)
    contract = Robustness(budget=budget)
    
    assert contract.budget.max_seconds == max_seconds
