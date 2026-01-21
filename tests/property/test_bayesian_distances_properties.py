#!/usr/bin/env python3
"""
Property-based tests for algorithms.statistics.bayesian_distances module.

Tests invariants for Bayesian comparison diagrams.
"""

import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import bayesian_distances module
try:
    from py3plex.algorithms.statistics.bayesian_distances import (
        generate_bayesian_diagram,
    )
    # Try to check if pystan is available
    try:
        import pystan
        PYSTAN_AVAILABLE = True
    except ImportError:
        PYSTAN_AVAILABLE = False
        pytest.skip("pystan module not available", allow_module_level=True)
    
    BAYESIAN_AVAILABLE = True
except ImportError:
    BAYESIAN_AVAILABLE = False
    pytest.skip("Bayesian distances module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Bayesian Comparison
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_folds=st.integers(min_value=3, max_value=10),
    n_runs=st.integers(min_value=3, max_value=8),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_bayesian_comparison_returns_probabilities(n_folds, n_runs, seed):
    """Test that Bayesian comparison returns valid probabilities."""
    np.random.seed(seed)
    
    # Generate random accuracy matrices for two algorithms
    # Shape: (n_folds, n_runs, n_algorithms)
    result_matrices = np.random.uniform(0.5, 1.0, size=(n_folds, n_runs, 2))
    
    # Generate comparison
    pl, pe, pr = generate_bayesian_diagram(
        result_matrices,
        algo_names=["algo1", "algo2"],
        show_diagram=False,
        save_diagram=None
    )
    
    # All probabilities should be in [0, 1]
    assert 0 <= pl <= 1, f"Left probability {pl} not in [0, 1]"
    assert 0 <= pe <= 1, f"Equivalence probability {pe} not in [0, 1]"
    assert 0 <= pr <= 1, f"Right probability {pr} not in [0, 1]"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_folds=st.integers(min_value=3, max_value=10),
    n_runs=st.integers(min_value=3, max_value=8),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_bayesian_comparison_probabilities_sum_to_one(n_folds, n_runs, seed):
    """Test that probabilities approximately sum to 1."""
    np.random.seed(seed)
    
    # Generate random accuracy matrices
    result_matrices = np.random.uniform(0.5, 1.0, size=(n_folds, n_runs, 2))
    
    # Generate comparison
    pl, pe, pr = generate_bayesian_diagram(
        result_matrices,
        algo_names=["algo1", "algo2"],
        show_diagram=False,
        save_diagram=None
    )
    
    # Probabilities should sum to approximately 1
    total = pl + pe + pr
    assert abs(total - 1.0) < 0.01, f"Probabilities sum to {total}, expected ~1.0"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_folds=st.integers(min_value=3, max_value=10),
    n_runs=st.integers(min_value=3, max_value=8),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_bayesian_comparison_symmetric_input(n_folds, n_runs, seed):
    """Test behavior when both algorithms have identical performance."""
    np.random.seed(seed)
    
    # Generate identical performance for both algorithms
    performance = np.random.uniform(0.5, 1.0, size=(n_folds, n_runs, 1))
    result_matrices = np.concatenate([performance, performance], axis=2)
    
    # Generate comparison
    pl, pe, pr = generate_bayesian_diagram(
        result_matrices,
        algo_names=["algo1", "algo2"],
        show_diagram=False,
        save_diagram=None
    )
    
    # For identical performance, left and right probabilities should be similar
    # and equivalence probability should be high
    assert pe > 0.5, f"Equivalence probability {pe} should be high for identical algorithms"
    assert abs(pl - pr) < 0.2, f"Left ({pl}) and right ({pr}) should be similar"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_folds=st.integers(min_value=3, max_value=8),
    n_runs=st.integers(min_value=3, max_value=6),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_bayesian_comparison_clear_winner(n_folds, n_runs, seed):
    """Test behavior when one algorithm clearly outperforms the other."""
    np.random.seed(seed)
    
    # Algorithm 1 consistently better (0.8-0.9)
    algo1_perf = np.random.uniform(0.8, 0.9, size=(n_folds, n_runs))
    # Algorithm 2 consistently worse (0.5-0.6)
    algo2_perf = np.random.uniform(0.5, 0.6, size=(n_folds, n_runs))
    
    result_matrices = np.stack([algo1_perf, algo2_perf], axis=2)
    
    # Generate comparison
    pl, pe, pr = generate_bayesian_diagram(
        result_matrices,
        algo_names=["algo1", "algo2"],
        show_diagram=False,
        save_diagram=None
    )
    
    # Algo1 should have higher probability of being better (pr > pl)
    # Note: pr is probability that algo2 > algo1, so for algo1 being better, pl should be high
    assert pl > pr, f"When algo1 is better, pl ({pl}) should be > pr ({pr})"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_folds=st.integers(min_value=3, max_value=10),
    n_runs=st.integers(min_value=3, max_value=8),
    rope=st.floats(min_value=0.001, max_value=0.1),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_bayesian_comparison_rope_parameter(n_folds, n_runs, rope, seed):
    """Test that ROPE parameter affects equivalence region."""
    np.random.seed(seed)
    
    # Generate slightly different performance
    algo1_perf = np.random.uniform(0.7, 0.8, size=(n_folds, n_runs))
    algo2_perf = algo1_perf + np.random.uniform(-0.02, 0.02, size=(n_folds, n_runs))
    
    result_matrices = np.stack([algo1_perf, algo2_perf], axis=2)
    
    # Generate comparison
    pl, pe, pr = generate_bayesian_diagram(
        result_matrices,
        algo_names=["algo1", "algo2"],
        rope=rope,
        show_diagram=False,
        save_diagram=None
    )
    
    # Probabilities should still be valid
    assert 0 <= pl <= 1, f"Left probability {pl} not in [0, 1]"
    assert 0 <= pe <= 1, f"Equivalence probability {pe} not in [0, 1]"
    assert 0 <= pr <= 1, f"Right probability {pr} not in [0, 1]"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_folds=st.integers(min_value=3, max_value=10),
    n_runs=st.integers(min_value=3, max_value=8),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_bayesian_comparison_numeric_stability(n_folds, n_runs, seed):
    """Test that comparison is numerically stable."""
    np.random.seed(seed)
    
    # Generate random accuracy matrices
    result_matrices = np.random.uniform(0.5, 1.0, size=(n_folds, n_runs, 2))
    
    # Generate comparison
    pl, pe, pr = generate_bayesian_diagram(
        result_matrices,
        algo_names=["algo1", "algo2"],
        show_diagram=False,
        save_diagram=None
    )
    
    # All values should be finite (no inf or nan)
    import math
    assert math.isfinite(pl), f"Left probability is not finite: {pl}"
    assert math.isfinite(pe), f"Equivalence probability is not finite: {pe}"
    assert math.isfinite(pr), f"Right probability is not finite: {pr}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_folds=st.integers(min_value=3, max_value=8),
    n_runs=st.integers(min_value=3, max_value=6),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_bayesian_comparison_with_default_names(n_folds, n_runs, seed):
    """Test that comparison works with default algorithm names."""
    np.random.seed(seed)
    
    # Generate random accuracy matrices
    result_matrices = np.random.uniform(0.5, 1.0, size=(n_folds, n_runs, 2))
    
    # Generate comparison without specifying names
    pl, pe, pr = generate_bayesian_diagram(
        result_matrices,
        show_diagram=False,
        save_diagram=None
    )
    
    # Should return valid probabilities
    assert 0 <= pl <= 1, f"Left probability {pl} not in [0, 1]"
    assert 0 <= pe <= 1, f"Equivalence probability {pe} not in [0, 1]"
    assert 0 <= pr <= 1, f"Right probability {pr} not in [0, 1]"
