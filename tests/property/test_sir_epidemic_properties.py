#!/usr/bin/env python3
"""
Property-based tests for SIR epidemic simulator on multiplex networks.

Tests invariants and properties including:
- Conservation law: S(t) + I(t) + R(t) = N for all t
- Monotonicity: R(t) is non-decreasing, S(t) is non-increasing
- Eventual extinction: I(t) -> 0 as epidemic dies out
- Reproducibility: Same seed produces identical trajectories
- Boundary conditions: beta=0 means no spread, gamma=0 means no recovery
"""

import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import SIR module
try:
    import scipy.sparse as sp
    from py3plex.algorithms.sir_multiplex import (
        simulate_sir_multiplex_discrete,
        simulate_sir_multiplex_gillespie,
        EpidemicResult,
    )
    SIR_AVAILABLE = True
except ImportError:
    SIR_AVAILABLE = False
    pytest.skip("SIR epidemic module not available", allow_module_level=True)


# ============================================================================
# Helper functions
# ============================================================================

def create_random_multiplex_layers(num_nodes, num_layers, density, seed):
    """Create random sparse adjacency matrices for testing."""
    rng = np.random.default_rng(seed)
    layers = []
    for _ in range(num_layers):
        # Create random adjacency matrix
        A = rng.random((num_nodes, num_nodes)) < density
        A = A.astype(float)
        # Make symmetric (undirected)
        A = np.triu(A, 1)
        A = A + A.T
        # No self-loops
        np.fill_diagonal(A, 0)
        layers.append(sp.csr_matrix(A))
    return layers


def create_connected_multiplex_layers(num_nodes, num_layers, seed):
    """Create multiplex layers where at least one layer is connected."""
    rng = np.random.default_rng(seed)
    layers = []

    # First layer: ring graph (always connected)
    A_ring = np.zeros((num_nodes, num_nodes))
    for i in range(num_nodes):
        A_ring[i, (i + 1) % num_nodes] = 1.0
        A_ring[(i + 1) % num_nodes, i] = 1.0
    layers.append(sp.csr_matrix(A_ring))

    # Additional random layers
    for _ in range(num_layers - 1):
        A = rng.random((num_nodes, num_nodes)) < 0.3
        A = A.astype(float)
        A = np.triu(A, 1) + np.triu(A, 1).T
        np.fill_diagonal(A, 0)
        layers.append(sp.csr_matrix(A))

    return layers


# ============================================================================
# Property Tests: Conservation Laws
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=50),
    num_layers=st.integers(min_value=1, max_value=3),
    beta=st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False),
    gamma=st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sir_conservation_law_discrete(num_nodes, num_layers, beta, gamma, seed):
    """Property: S(t) + I(t) + R(t) = N for all time steps (conservation)."""
    layers = create_random_multiplex_layers(num_nodes, num_layers, 0.3, seed)

    result = simulate_sir_multiplex_discrete(
        layers,
        beta=beta,
        gamma=gamma,
        steps=50,
        rng_seed=seed
    )

    # Check conservation at each time step
    N = num_nodes
    for t in range(len(result.times)):
        total = result.S[t] + result.I[t] + result.R[t]
        assert total == N, f"Conservation violated at t={t}: S+I+R={total}, expected {N}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=30),
    num_layers=st.integers(min_value=1, max_value=2),
    beta=st.floats(min_value=0.05, max_value=0.3, allow_nan=False, allow_infinity=False),
    gamma=st.floats(min_value=0.05, max_value=0.3, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sir_conservation_law_gillespie(num_nodes, num_layers, beta, gamma, seed):
    """Property: S(t) + I(t) + R(t) = N for Gillespie simulation."""
    layers = create_connected_multiplex_layers(num_nodes, num_layers, seed)

    result = simulate_sir_multiplex_gillespie(
        layers,
        beta=beta,
        gamma=gamma,
        t_max=10.0,
        rng_seed=seed
    )

    # Check conservation at each event
    N = num_nodes
    for t in range(len(result.times)):
        total = result.S[t] + result.I[t] + result.R[t]
        assert total == N, f"Conservation violated at t={result.times[t]}: S+I+R={total}, expected {N}"


# ============================================================================
# Property Tests: Monotonicity
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=50),
    num_layers=st.integers(min_value=1, max_value=3),
    beta=st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False),
    gamma=st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sir_recovered_monotonic_nondecreasing(num_nodes, num_layers, beta, gamma, seed):
    """Property: R(t) is monotonically non-decreasing (recovered never decrease)."""
    layers = create_random_multiplex_layers(num_nodes, num_layers, 0.3, seed)

    result = simulate_sir_multiplex_discrete(
        layers,
        beta=beta,
        gamma=gamma,
        steps=50,
        rng_seed=seed
    )

    # R(t) should never decrease
    for t in range(1, len(result.times)):
        assert result.R[t] >= result.R[t-1], \
            f"R decreased at t={t}: R[{t-1}]={result.R[t-1]}, R[{t}]={result.R[t]}"


@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=50),
    num_layers=st.integers(min_value=1, max_value=3),
    beta=st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False),
    gamma=st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sir_susceptible_monotonic_nonincreasing(num_nodes, num_layers, beta, gamma, seed):
    """Property: S(t) is monotonically non-increasing (susceptibles never increase)."""
    layers = create_random_multiplex_layers(num_nodes, num_layers, 0.3, seed)

    result = simulate_sir_multiplex_discrete(
        layers,
        beta=beta,
        gamma=gamma,
        steps=50,
        rng_seed=seed
    )

    # S(t) should never increase
    for t in range(1, len(result.times)):
        assert result.S[t] <= result.S[t-1], \
            f"S increased at t={t}: S[{t-1}]={result.S[t-1]}, S[{t}]={result.S[t]}"


# ============================================================================
# Property Tests: Boundary Conditions
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=30),
    num_layers=st.integers(min_value=1, max_value=2),
    gamma=st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sir_zero_beta_no_spread(num_nodes, num_layers, gamma, seed):
    """Property: beta=0 means no new infections (S remains constant after initial)."""
    layers = create_random_multiplex_layers(num_nodes, num_layers, 0.3, seed)

    # Start with one infected
    initial_infected = np.zeros(num_nodes, dtype=bool)
    initial_infected[0] = True

    result = simulate_sir_multiplex_discrete(
        layers,
        beta=0.0,  # No transmission
        gamma=gamma,
        steps=50,
        initial_infected=initial_infected,
        rng_seed=seed
    )

    # S should remain constant (initial infected never spreads)
    initial_S = result.S[0]
    for t in range(1, len(result.times)):
        assert result.S[t] == initial_S, \
            f"S changed with beta=0 at t={t}: S[0]={initial_S}, S[{t}]={result.S[t]}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=30),
    num_layers=st.integers(min_value=1, max_value=2),
    beta=st.floats(min_value=0.1, max_value=0.5, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sir_zero_gamma_no_recovery(num_nodes, num_layers, beta, seed):
    """Property: gamma=0 means no recovery (R remains 0)."""
    layers = create_connected_multiplex_layers(num_nodes, num_layers, seed)

    result = simulate_sir_multiplex_discrete(
        layers,
        beta=beta,
        gamma=0.0,  # No recovery
        steps=50,
        rng_seed=seed
    )

    # R should remain 0 forever
    for t in range(len(result.times)):
        assert result.R[t] == 0, f"R > 0 with gamma=0 at t={t}: R={result.R[t]}"


# ============================================================================
# Property Tests: Reproducibility
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=30),
    num_layers=st.integers(min_value=1, max_value=2),
    beta=st.floats(min_value=0.05, max_value=0.3, allow_nan=False, allow_infinity=False),
    gamma=st.floats(min_value=0.05, max_value=0.3, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sir_discrete_reproducibility(num_nodes, num_layers, beta, gamma, seed):
    """Property: Same seed produces identical trajectories."""
    layers = create_random_multiplex_layers(num_nodes, num_layers, 0.3, seed)

    result1 = simulate_sir_multiplex_discrete(
        layers, beta=beta, gamma=gamma, steps=30, rng_seed=seed
    )
    result2 = simulate_sir_multiplex_discrete(
        layers, beta=beta, gamma=gamma, steps=30, rng_seed=seed
    )

    # Trajectories should be identical
    np.testing.assert_array_equal(result1.S, result2.S, err_msg="S trajectories differ")
    np.testing.assert_array_equal(result1.I, result2.I, err_msg="I trajectories differ")
    np.testing.assert_array_equal(result1.R, result2.R, err_msg="R trajectories differ")


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=25),
    beta=st.floats(min_value=0.1, max_value=0.3, allow_nan=False, allow_infinity=False),
    gamma=st.floats(min_value=0.1, max_value=0.3, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sir_gillespie_reproducibility(num_nodes, beta, gamma, seed):
    """Property: Same seed produces identical Gillespie trajectories."""
    layers = create_connected_multiplex_layers(num_nodes, 1, seed)

    result1 = simulate_sir_multiplex_gillespie(
        layers, beta=beta, gamma=gamma, t_max=5.0, rng_seed=seed
    )
    result2 = simulate_sir_multiplex_gillespie(
        layers, beta=beta, gamma=gamma, t_max=5.0, rng_seed=seed
    )

    # Event times and states should be identical
    np.testing.assert_array_almost_equal(result1.times, result2.times, decimal=10)
    np.testing.assert_array_equal(result1.S, result2.S)
    np.testing.assert_array_equal(result1.I, result2.I)
    np.testing.assert_array_equal(result1.R, result2.R)


# ============================================================================
# Property Tests: Initial Conditions
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=30),
    num_initial_infected=st.integers(min_value=1, max_value=5),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sir_initial_conditions_respected(num_nodes, num_initial_infected, seed):
    """Property: Initial conditions are correctly set."""
    assume(num_initial_infected < num_nodes)

    layers = create_random_multiplex_layers(num_nodes, 1, 0.3, seed)

    # Set specific initial infected
    initial_infected = np.zeros(num_nodes, dtype=bool)
    initial_infected[:num_initial_infected] = True

    result = simulate_sir_multiplex_discrete(
        layers,
        beta=0.1,
        gamma=0.1,
        steps=1,  # Just check initial state
        initial_infected=initial_infected,
        rng_seed=seed
    )

    # Check initial state
    assert result.I[0] == num_initial_infected, \
        f"Initial I mismatch: expected {num_initial_infected}, got {result.I[0]}"
    assert result.S[0] == num_nodes - num_initial_infected, \
        f"Initial S mismatch: expected {num_nodes - num_initial_infected}, got {result.S[0]}"
    assert result.R[0] == 0, f"Initial R should be 0, got {result.R[0]}"


# ============================================================================
# Property Tests: Non-negativity
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=50),
    num_layers=st.integers(min_value=1, max_value=3),
    beta=st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False),
    gamma=st.floats(min_value=0.01, max_value=0.5, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sir_counts_nonnegative(num_nodes, num_layers, beta, gamma, seed):
    """Property: S, I, R are all non-negative at all times."""
    layers = create_random_multiplex_layers(num_nodes, num_layers, 0.3, seed)

    result = simulate_sir_multiplex_discrete(
        layers,
        beta=beta,
        gamma=gamma,
        steps=50,
        rng_seed=seed
    )

    assert np.all(result.S >= 0), f"Negative S values found: min={np.min(result.S)}"
    assert np.all(result.I >= 0), f"Negative I values found: min={np.min(result.I)}"
    assert np.all(result.R >= 0), f"Negative R values found: min={np.min(result.R)}"


# ============================================================================
# Property Tests: Layer Weight Effects
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=15, max_value=30),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sir_layer_weights_affect_spread(num_nodes, seed):
    """Property: Higher layer weights lead to more infections (statistical)."""
    layers = create_connected_multiplex_layers(num_nodes, 2, seed)

    # Run with uniform weights
    result_uniform = simulate_sir_multiplex_discrete(
        layers,
        beta=0.2,
        gamma=0.1,
        layer_weights=np.array([1.0, 1.0]),
        steps=30,
        rng_seed=seed
    )

    # Run with zero weight on second layer (effectively single layer)
    result_single = simulate_sir_multiplex_discrete(
        layers,
        beta=0.2,
        gamma=0.1,
        layer_weights=np.array([1.0, 0.0]),
        steps=30,
        rng_seed=seed
    )

    # With more transmission channels, expect more total infections
    # (Final R is a proxy for total infected)
    final_R_uniform = result_uniform.R[-1]
    final_R_single = result_single.R[-1]

    # This is a soft property - multilayer should spread at least as much
    # Allow for stochastic variation
    assert final_R_uniform >= final_R_single * 0.5, \
        f"Multilayer should not spread significantly less: uniform={final_R_uniform}, single={final_R_single}"


# ============================================================================
# Property Tests: Event Log Consistency
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=25),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sir_event_log_consistency(num_nodes, seed):
    """Property: Event log is consistent with trajectory."""
    layers = create_connected_multiplex_layers(num_nodes, 1, seed)

    result = simulate_sir_multiplex_discrete(
        layers,
        beta=0.2,
        gamma=0.1,
        steps=30,
        rng_seed=seed,
        return_event_log=True
    )

    if result.events is not None and len(result.events) > 0:
        # Count infections and recoveries from event log
        infection_count = sum(1 for e in result.events if e[1] == 'infection')
        recovery_count = sum(1 for e in result.events if e[1] == 'recovery')

        # Final R should equal recovery count
        final_R = result.R[-1]
        assert final_R == recovery_count, \
            f"Event log recovery count ({recovery_count}) != final R ({final_R})"


# ============================================================================
# Property Tests: Epidemic Extinction
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=20),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sir_eventual_extinction(num_nodes, seed):
    """Property: Epidemic eventually dies out (I -> 0) in closed population."""
    layers = create_connected_multiplex_layers(num_nodes, 1, seed)

    # High recovery rate to ensure extinction
    result = simulate_sir_multiplex_discrete(
        layers,
        beta=0.1,
        gamma=0.3,  # High recovery
        steps=200,  # Long simulation
        rng_seed=seed
    )

    # With high gamma and finite network, epidemic should die out
    # Check that I reaches 0 at some point
    reached_zero = any(result.I[t] == 0 for t in range(len(result.times)))

    # Or at least I should be very small at the end
    final_I = result.I[-1]
    assert reached_zero or final_I <= num_nodes * 0.1, \
        f"Epidemic did not die out: final I = {final_I}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
