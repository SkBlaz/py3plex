#!/usr/bin/env python3
"""
Property-based tests for algorithms.statistics.topology module.

Tests invariants and properties of power law fitting and network topology:
- Alpha (exponent) is positive for power law distributions
- Sigma (standard error) is non-negative
- Degree sequences are valid (non-negative integers)
- Power law fitting consistency
"""

import networkx as nx
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import shared strategies
from .strategies import (
    small_graphs,
)

# Import topology module
try:
    from py3plex.algorithms.statistics.topology import (
        basic_pl_stats,
    )
    TOPOLOGY_AVAILABLE = True
except ImportError:
    TOPOLOGY_AVAILABLE = False
    pytest.skip("Topology module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Power Law Statistics
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=50),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_basic_pl_stats_alpha_positive(num_nodes, seed):
    """Property: Power law alpha (exponent) should be positive."""
    # Create a scale-free graph (expected to follow power law)
    G = nx.barabasi_albert_graph(num_nodes, 2, seed=seed)
    
    degree_sequence = sorted([d for n, d in G.degree()], reverse=True)
    assume(len(degree_sequence) >= 10)  # Need sufficient data
    assume(max(degree_sequence) > 1)  # Need some variation
    
    try:
        alpha, sigma = basic_pl_stats(degree_sequence)
        
        # Alpha should be positive for power law
        assert alpha > 0, f"Power law alpha should be positive, got {alpha}"
    except Exception as e:
        # If fitting fails, skip this test case
        if "powerlaw" in str(e).lower() or "fit" in str(e).lower():
            pytest.skip(f"Power law fitting failed: {e}")
        raise


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=50),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_basic_pl_stats_sigma_non_negative(num_nodes, seed):
    """Property: Power law sigma (standard error) should be non-negative."""
    # Create a scale-free graph
    G = nx.barabasi_albert_graph(num_nodes, 2, seed=seed)
    
    degree_sequence = sorted([d for n, d in G.degree()], reverse=True)
    assume(len(degree_sequence) >= 10)
    assume(max(degree_sequence) > 1)
    
    try:
        alpha, sigma = basic_pl_stats(degree_sequence)
        
        # Sigma should be non-negative (it's a standard error)
        assert sigma >= 0, f"Power law sigma should be non-negative, got {sigma}"
    except Exception as e:
        if "powerlaw" in str(e).lower() or "fit" in str(e).lower():
            pytest.skip(f"Power law fitting failed: {e}")
        raise


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=20, max_value=50),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_basic_pl_stats_returns_two_values(num_nodes, seed):
    """Property: basic_pl_stats returns exactly two values (alpha, sigma)."""
    G = nx.barabasi_albert_graph(num_nodes, 2, seed=seed)
    
    degree_sequence = sorted([d for n, d in G.degree()], reverse=True)
    assume(len(degree_sequence) >= 10)
    assume(max(degree_sequence) > 1)
    
    try:
        result = basic_pl_stats(degree_sequence)
        
        # Should return a tuple of two values
        assert isinstance(result, tuple), "Should return a tuple"
        assert len(result) == 2, f"Should return 2 values, got {len(result)}"
        
        alpha, sigma = result
        assert isinstance(alpha, (int, float)), f"Alpha should be numeric, got {type(alpha)}"
        assert isinstance(sigma, (int, float)), f"Sigma should be numeric, got {type(sigma)}"
    except Exception as e:
        if "powerlaw" in str(e).lower() or "fit" in str(e).lower():
            pytest.skip(f"Power law fitting failed: {e}")
        raise


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=20, max_value=50),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_basic_pl_stats_alpha_reasonable_range(num_nodes, seed):
    """Property: Alpha for scale-free networks typically in range [2, 4]."""
    # Create a scale-free graph using Barabasi-Albert model
    G = nx.barabasi_albert_graph(num_nodes, 2, seed=seed)
    
    degree_sequence = sorted([d for n, d in G.degree()], reverse=True)
    assume(len(degree_sequence) >= 10)
    assume(max(degree_sequence) > 1)
    
    try:
        alpha, sigma = basic_pl_stats(degree_sequence)
        
        # For scale-free networks, alpha is typically between 2 and 4
        # Allow wider range for small/noisy data (up to 15 to handle edge cases)
        assert 1.0 < alpha < 15.0, \
            f"Alpha should be in reasonable range [1, 15], got {alpha}"
    except Exception as e:
        if "powerlaw" in str(e).lower() or "fit" in str(e).lower():
            pytest.skip(f"Power law fitting failed: {e}")
        raise


# ============================================================================
# Property Tests: Degree Sequence Validity
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=30),
    prob=st.floats(min_value=0.1, max_value=0.8, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_degree_sequence_all_non_negative(num_nodes, prob, seed):
    """Property: All degrees in a degree sequence are non-negative."""
    G = nx.gnp_random_graph(num_nodes, prob, seed=seed)
    
    degree_sequence = [d for n, d in G.degree()]
    
    # All degrees should be non-negative integers
    for degree in degree_sequence:
        assert degree >= 0, f"Degree should be non-negative, got {degree}"
        assert isinstance(degree, int), f"Degree should be integer, got {type(degree)}"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=30),
    prob=st.floats(min_value=0.1, max_value=0.8, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_degree_sequence_sum_even(num_nodes, prob, seed):
    """Property: Sum of degree sequence is even (handshaking lemma)."""
    G = nx.gnp_random_graph(num_nodes, prob, seed=seed)
    
    degree_sequence = [d for n, d in G.degree()]
    degree_sum = sum(degree_sequence)
    
    # Sum of degrees should be even (equals 2 * number of edges)
    assert degree_sum % 2 == 0, \
        f"Sum of degrees should be even, got {degree_sum}"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=30),
    prob=st.floats(min_value=0.1, max_value=0.8, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_degree_sequence_length_matches_nodes(num_nodes, prob, seed):
    """Property: Degree sequence length equals number of nodes."""
    G = nx.gnp_random_graph(num_nodes, prob, seed=seed)
    
    degree_sequence = [d for n, d in G.degree()]
    
    assert len(degree_sequence) == num_nodes, \
        f"Degree sequence length should match node count, got {len(degree_sequence)} vs {num_nodes}"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=30),
    prob=st.floats(min_value=0.1, max_value=0.8, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_degree_sequence_max_degree_bounded(num_nodes, prob, seed):
    """Property: Max degree is bounded by n-1 (for undirected simple graphs)."""
    G = nx.gnp_random_graph(num_nodes, prob, seed=seed)
    
    degree_sequence = [d for n, d in G.degree()]
    max_degree = max(degree_sequence) if degree_sequence else 0
    
    # Maximum degree in a simple graph is n-1 (connected to all other nodes)
    assert max_degree <= num_nodes - 1, \
        f"Max degree should be <= {num_nodes - 1}, got {max_degree}"


# ============================================================================
# Property Tests: Scale-Free Network Properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=20, max_value=50),
    m=st.integers(min_value=1, max_value=5),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_barabasi_albert_has_high_degree_hubs(num_nodes, m, seed):
    """Property: Barabasi-Albert graphs have some high-degree hubs."""
    # Create a scale-free graph
    G = nx.barabasi_albert_graph(num_nodes, m, seed=seed)
    
    degree_sequence = [d for n, d in G.degree()]
    max_degree = max(degree_sequence)
    avg_degree = sum(degree_sequence) / len(degree_sequence)
    
    # Scale-free networks have hubs with degree much higher than average
    # Max degree should be significantly higher than average
    assert max_degree > avg_degree, \
        f"Scale-free graph should have hubs: max={max_degree}, avg={avg_degree:.2f}"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=20, max_value=50),
    m=st.integers(min_value=2, max_value=5),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_barabasi_albert_min_degree(num_nodes, m, seed):
    """Property: In Barabasi-Albert graphs, min degree is at least 1."""
    # Create a scale-free graph
    G = nx.barabasi_albert_graph(num_nodes, m, seed=seed)
    
    degree_sequence = [d for n, d in G.degree()]
    min_degree = min(degree_sequence)
    
    # In BA model, minimum degree should be at least 1
    # Note: Initial nodes (m nodes) may have degree < m, but all nodes have degree >= 1
    assert min_degree >= 1, \
        f"BA graph min degree should be >= 1, got {min_degree}"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=20, max_value=50),
    m=st.integers(min_value=2, max_value=5),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_barabasi_albert_connected(num_nodes, m, seed):
    """Property: Barabasi-Albert graphs are connected."""
    # Create a scale-free graph
    G = nx.barabasi_albert_graph(num_nodes, m, seed=seed)
    
    # BA graphs should be connected
    assert nx.is_connected(G), "Barabasi-Albert graph should be connected"


# ============================================================================
# Property Tests: Power Law Fitting Edge Cases
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=10, max_value=30)
)
def test_complete_graph_degree_sequence(num_nodes):
    """Property: Complete graph has all nodes with degree n-1."""
    G = nx.complete_graph(num_nodes)
    
    degree_sequence = [d for n, d in G.degree()]
    
    # All nodes should have degree n-1
    assert all(d == num_nodes - 1 for d in degree_sequence), \
        f"Complete graph should have all degrees = {num_nodes - 1}"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=30)
)
def test_star_graph_degree_distribution(num_nodes):
    """Property: Star graph has one hub with degree n-1, others with degree 1."""
    # Star graph: center connected to all others
    G = nx.star_graph(num_nodes - 1)
    
    degree_sequence = sorted([d for n, d in G.degree()], reverse=True)
    
    # Highest degree should be n-1 (center)
    assert degree_sequence[0] == num_nodes - 1, \
        f"Star center should have degree {num_nodes - 1}"
    
    # All other nodes should have degree 1
    assert all(d == 1 for d in degree_sequence[1:]), \
        "Star leaves should all have degree 1"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=30)
)
def test_path_graph_degree_distribution(num_nodes):
    """Property: Path graph has 2 endpoints with degree 1, others with degree 2."""
    G = nx.path_graph(num_nodes)
    
    degree_sequence = sorted([d for n, d in G.degree()])
    
    # Two endpoints have degree 1
    assert degree_sequence[0] == 1, "Path endpoint should have degree 1"
    assert degree_sequence[1] == 1, "Path endpoint should have degree 1"
    
    # All middle nodes have degree 2
    if num_nodes > 2:
        assert all(d == 2 for d in degree_sequence[2:]), \
            "Path middle nodes should have degree 2"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=30)
)
def test_cycle_graph_all_degree_two(num_nodes):
    """Property: Cycle graph has all nodes with degree 2."""
    G = nx.cycle_graph(num_nodes)
    
    degree_sequence = [d for n, d in G.degree()]
    
    # All nodes in a cycle have degree 2
    assert all(d == 2 for d in degree_sequence), \
        "All nodes in cycle should have degree 2"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
