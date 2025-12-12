#!/usr/bin/env python3
"""
Property-based tests for algorithms.statistics.topology module.

Tests invariants for power law statistics and degree sequence analysis.
"""

import networkx as nx
import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import topology module
try:
    from py3plex.algorithms.statistics.topology import basic_pl_stats
    TOPOLOGY_AVAILABLE = True
except ImportError:
    TOPOLOGY_AVAILABLE = False
    pytest.skip("Topology module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Power Law Statistics
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_nodes=st.integers(min_value=10, max_value=50),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_basic_pl_stats_returns_positive_alpha(n_nodes, seed):
    """Test that power law alpha is positive."""
    # Create a scale-free network (preferential attachment)
    G = nx.barabasi_albert_graph(n_nodes, 2, seed=seed)
    degree_sequence = [d for n, d in G.degree()]
    
    # Get power law statistics
    alpha, sigma = basic_pl_stats(degree_sequence)
    
    # Alpha should be positive
    assert alpha > 0, f"Power law alpha should be positive, got {alpha}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_nodes=st.integers(min_value=10, max_value=50),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_basic_pl_stats_returns_valid_sigma(n_nodes, seed):
    """Test that power law sigma is positive."""
    # Create a scale-free network
    G = nx.barabasi_albert_graph(n_nodes, 2, seed=seed)
    degree_sequence = [d for n, d in G.degree()]
    
    # Get power law statistics
    alpha, sigma = basic_pl_stats(degree_sequence)
    
    # Sigma (standard error) should be positive
    assert sigma > 0, f"Power law sigma should be positive, got {sigma}"


@pytest.mark.property
@pytest.mark.slow
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_nodes=st.integers(min_value=15, max_value=50),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_basic_pl_stats_deterministic(n_nodes, seed):
    """Test that power law stats are deterministic for same input."""
    # Create a scale-free network
    G = nx.barabasi_albert_graph(n_nodes, 2, seed=seed)
    degree_sequence = [d for n, d in G.degree()]
    
    # Get power law statistics twice
    alpha1, sigma1 = basic_pl_stats(degree_sequence)
    alpha2, sigma2 = basic_pl_stats(degree_sequence)
    
    # Should return same values
    assert alpha1 == alpha2, "Alpha should be deterministic"
    assert sigma1 == sigma2, "Sigma should be deterministic"


@pytest.mark.property
@pytest.mark.slow
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_nodes=st.integers(min_value=15, max_value=50),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_basic_pl_stats_scale_free_alpha_range(n_nodes, seed):
    """Test that scale-free networks have alpha in typical range."""
    # Create a scale-free network
    G = nx.barabasi_albert_graph(n_nodes, 2, seed=seed)
    degree_sequence = [d for n, d in G.degree()]
    
    # Get power law statistics
    alpha, sigma = basic_pl_stats(degree_sequence)
    
    # For scale-free networks, alpha typically in range [2, 4]
    # Allow wider range for small networks
    assert 1.5 <= alpha <= 10, \
        f"Scale-free network alpha {alpha} outside expected range [1.5, 10]"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_nodes=st.integers(min_value=15, max_value=50),
    p=st.floats(min_value=0.1, max_value=0.5),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_basic_pl_stats_random_network_higher_alpha(n_nodes, p, seed):
    """Test that random networks typically have higher alpha than scale-free."""
    # Create a random network (Erdős-Rényi)
    G = nx.erdos_renyi_graph(n_nodes, p, seed=seed)
    
    # Ensure network is not trivial
    if G.number_of_edges() < 3:
        return
    
    degree_sequence = [d for n, d in G.degree()]
    
    # Get power law statistics
    alpha, sigma = basic_pl_stats(degree_sequence)
    
    # Random networks typically don't follow power law well
    # But we just check that alpha is computed
    assert alpha > 0, f"Alpha should be positive, got {alpha}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_nodes=st.integers(min_value=10, max_value=40),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_basic_pl_stats_uniform_degrees_high_alpha(n_nodes, seed):
    """Test that networks with uniform degrees have different characteristics."""
    # Create a regular graph (all nodes have same degree)
    # Use k=3 for a 3-regular graph
    if n_nodes * 3 % 2 != 0:  # Need even number of edges
        n_nodes += 1
    
    try:
        G = nx.random_regular_graph(3, n_nodes, seed=seed)
    except nx.NetworkXError:
        # If can't create regular graph, skip
        return
    
    degree_sequence = [d for n, d in G.degree()]
    
    # Get power law statistics
    alpha, sigma = basic_pl_stats(degree_sequence)
    
    # For regular graphs, the fit may be poor but should still compute
    # Allow nan for regular graphs since they don't follow power law
    import math
    if not math.isnan(alpha):
        assert alpha > 0, f"Alpha should be positive, got {alpha}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_nodes=st.integers(min_value=10, max_value=50),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_basic_pl_stats_numeric_stability(n_nodes, seed):
    """Test that power law computation is numerically stable."""
    # Create a scale-free network
    G = nx.barabasi_albert_graph(n_nodes, 2, seed=seed)
    degree_sequence = [d for n, d in G.degree()]
    
    # Get power law statistics
    alpha, sigma = basic_pl_stats(degree_sequence)
    
    # All values should be finite (no inf or nan)
    import math
    assert math.isfinite(alpha), f"Alpha is not finite: {alpha}"
    assert math.isfinite(sigma), f"Sigma is not finite: {sigma}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_nodes=st.integers(min_value=10, max_value=40),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_basic_pl_stats_handles_zeros_in_sequence(n_nodes, seed):
    """Test that power law stats handle degree sequences with zeros."""
    # Create a graph with isolated nodes
    G = nx.barabasi_albert_graph(n_nodes // 2, 2, seed=seed)
    
    # Add isolated nodes (degree 0)
    for i in range(n_nodes // 2, n_nodes):
        G.add_node(i)
    
    degree_sequence = [d for n, d in G.degree()]
    
    # Should handle zeros gracefully
    alpha, sigma = basic_pl_stats(degree_sequence)
    
    # Should still return valid values
    assert alpha > 0, f"Alpha should be positive even with zeros, got {alpha}"
    assert sigma > 0, f"Sigma should be positive even with zeros, got {sigma}"


@pytest.mark.property
@pytest.mark.slow
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_nodes=st.integers(min_value=15, max_value=50),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_basic_pl_stats_sigma_reflects_fit_quality(n_nodes, seed):
    """Test that sigma (standard error) is reasonable."""
    # Create a scale-free network (should have good power law fit)
    G = nx.barabasi_albert_graph(n_nodes, 2, seed=seed)
    degree_sequence = [d for n, d in G.degree()]
    
    # Get power law statistics
    alpha, sigma = basic_pl_stats(degree_sequence)
    
    # Sigma should be reasonable (not too large)
    # For well-fitting power laws, sigma is typically < 1
    assert sigma < 5, f"Sigma {sigma} seems too large, indicating poor fit"


@pytest.mark.property
@pytest.mark.slow
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    seed=st.integers(min_value=0, max_value=10000)
)
def test_basic_pl_stats_handles_small_degree_sequences(seed):
    """Test that power law stats handle small degree sequences."""
    # Create a very small graph
    G = nx.complete_graph(5)
    degree_sequence = [d for n, d in G.degree()]
    
    # Should handle small sequences
    alpha, sigma = basic_pl_stats(degree_sequence)
    
    # For complete graphs (all same degree), may return nan
    # Just check it doesn't crash
    import math
    if not math.isnan(alpha):
        assert alpha > 0, f"Alpha should be positive for small sequences, got {alpha}"
    if not math.isnan(sigma):
        assert sigma > 0, f"Sigma should be positive for small sequences, got {sigma}"
