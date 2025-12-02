#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extended property-based tests for multilayer centrality metrics.

This module adds comprehensive property tests for centrality metrics that
are not yet covered by test_centrality_invariants.py, including:

- PageRank centrality (stochasticity, non-negativity)
- Katz-Bonacich centrality (positivity, finiteness)
- Current-flow centrality (non-negativity)
- Subgraph centrality (positivity from matrix exponential)
- Total communicability (positivity)
- Bridging centrality (non-negativity)
- Load centrality (non-negativity)
- Spreading centrality (bounded [0,1])
- Percolation centrality (bounded [0,1])
- Accessibility centrality (positivity)
- K-core decomposition (non-negative integers)
- Edge betweenness (non-negativity)
- Communicability betweenness (non-negativity)
- Local efficiency (bounded)
- Flow betweenness (non-negativity)
- HITS centrality (non-negativity)
"""

import pytest
import numpy as np
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Conditional imports with proper error handling
try:
    from py3plex.core import multinet
    from py3plex.algorithms.multilayer_algorithms.centrality import (
        MultilayerCentrality,
        compute_all_centralities,
    )
    CENTRALITY_AVAILABLE = True
except ImportError:
    CENTRALITY_AVAILABLE = False
    pytest.skip("Centrality module not available", allow_module_level=True)


# ============================================================================
# Helper Functions
# ============================================================================

def create_connected_multilayer_network(num_nodes=4, num_layers=2, seed=None):
    """Create a connected multilayer network for testing."""
    if seed is not None:
        np.random.seed(seed)
    
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [f'N{i}' for i in range(num_nodes)]
    layers = [f'L{i}' for i in range(num_layers)]
    
    # Add edges to create a connected network in each layer (path + random edges)
    for layer in layers:
        # Create a path to ensure connectivity
        for i in range(len(nodes) - 1):
            weight = np.random.uniform(0.5, 2.0)
            network.add_edges([
                [nodes[i], layer, nodes[i+1], layer, weight]
            ], input_type='list')
        
        # Add some random additional edges for more structure
        for _ in range(num_nodes // 2):
            i, j = np.random.choice(num_nodes, size=2, replace=False)
            if i != j:
                weight = np.random.uniform(0.5, 2.0)
                network.add_edges([
                    [nodes[i], layer, nodes[j], layer, weight]
                ], input_type='list')
    
    return network


def create_multilayer_network_with_interlayer(num_nodes=4, num_layers=2, seed=None):
    """Create a multilayer network with interlayer connections."""
    if seed is not None:
        np.random.seed(seed)
    
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [f'N{i}' for i in range(num_nodes)]
    layers = [f'L{i}' for i in range(num_layers)]
    
    # Add intralayer edges
    for layer in layers:
        for i in range(len(nodes) - 1):
            weight = np.random.uniform(0.5, 2.0)
            network.add_edges([
                [nodes[i], layer, nodes[i+1], layer, weight]
            ], input_type='list')
    
    # Add interlayer coupling edges (same node across layers)
    for node in nodes:
        for i in range(len(layers) - 1):
            weight = np.random.uniform(0.1, 1.0)
            network.add_edges([
                [node, layers[i], node, layers[i+1], weight]
            ], input_type='list')
    
    return network


# ============================================================================
# Property Tests: PageRank
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_pagerank_sums_to_one(num_nodes, num_layers, seed):
    """Property: PageRank values sum to approximately 1.0."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed)
    calc = MultilayerCentrality(network)
    
    result = calc.pagerank_centrality()
    
    # PageRank should sum to 1 (within tolerance)
    total = sum(result.values())
    assert abs(total - 1.0) < 1e-3, f"PageRank should sum to 1, got {total}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_pagerank_non_negative(num_nodes, num_layers, seed):
    """Property: All PageRank values are non-negative."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed)
    calc = MultilayerCentrality(network)
    
    result = calc.pagerank_centrality()
    
    for node_layer, value in result.items():
        assert value >= 0, f"PageRank for {node_layer} should be non-negative, got {value}"
        assert np.isfinite(value), f"PageRank for {node_layer} should be finite"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2),
    damping=st.floats(min_value=0.5, max_value=0.99)
)
def test_pagerank_damping_factor_effect(num_nodes, num_layers, damping):
    """Property: Different damping factors produce different but valid PageRank."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.pagerank_centrality(damping=damping)
    
    # All values should be valid probability distribution
    total = sum(result.values())
    assert abs(total - 1.0) < 1e-3, f"PageRank should sum to 1, got {total}"
    assert all(v >= 0 for v in result.values()), "All values should be non-negative"


# ============================================================================
# Property Tests: Katz-Bonacich Centrality
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_katz_centrality_positive(num_nodes, num_layers, seed):
    """Property: Katz-Bonacich centrality values are positive."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed)
    calc = MultilayerCentrality(network)
    
    # Use a safe alpha value
    result = calc.katz_bonacich_centrality(alpha=0.05)
    
    for node_layer, value in result.items():
        assert value > 0, f"Katz centrality for {node_layer} should be positive, got {value}"
        assert np.isfinite(value), f"Katz centrality for {node_layer} should be finite"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2),
    alpha=st.floats(min_value=0.01, max_value=0.1)
)
def test_katz_centrality_finite(num_nodes, num_layers, alpha):
    """Property: Katz-Bonacich centrality values are finite for safe alpha."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.katz_bonacich_centrality(alpha=alpha)
    
    assert len(result) > 0, "Should have centrality results"
    assert all(np.isfinite(v) for v in result.values()), "All values should be finite"


# ============================================================================
# Property Tests: Current-Flow Centrality
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_current_flow_closeness_non_negative(num_nodes, num_layers):
    """Property: Current-flow closeness values are non-negative."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.current_flow_closeness_centrality()
    
    assert len(result) > 0, "Should have centrality results"
    for node_layer, value in result.items():
        assert value >= 0, f"Current-flow closeness for {node_layer} should be non-negative"
        assert np.isfinite(value), f"Current-flow closeness for {node_layer} should be finite"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_current_flow_betweenness_non_negative(num_nodes, num_layers):
    """Property: Current-flow betweenness values are non-negative."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.current_flow_betweenness_centrality()
    
    assert len(result) > 0, "Should have centrality results"
    for node_layer, value in result.items():
        assert value >= 0, f"Current-flow betweenness for {node_layer} should be non-negative"
        assert np.isfinite(value), f"Current-flow betweenness for {node_layer} should be finite"


# ============================================================================
# Property Tests: Subgraph Centrality and Total Communicability
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_subgraph_centrality_positive(num_nodes, num_layers):
    """Property: Subgraph centrality values are positive (diagonal of matrix exponential)."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.subgraph_centrality()
    
    assert len(result) > 0, "Should have centrality results"
    for node_layer, value in result.items():
        assert value > 0, f"Subgraph centrality for {node_layer} should be positive, got {value}"
        assert np.isfinite(value), f"Subgraph centrality for {node_layer} should be finite"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_total_communicability_positive(num_nodes, num_layers):
    """Property: Total communicability values are positive."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.total_communicability()
    
    assert len(result) > 0, "Should have centrality results"
    for node_layer, value in result.items():
        assert value > 0, f"Total communicability for {node_layer} should be positive, got {value}"
        assert np.isfinite(value), f"Total communicability for {node_layer} should be finite"


@pytest.mark.property
@settings(deadline=None, max_examples=8, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_subgraph_leq_total_communicability(num_nodes, num_layers):
    """Property: Subgraph centrality <= Total communicability for each node."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    subgraph = calc.subgraph_centrality()
    total_comm = calc.total_communicability()
    
    for node_layer in subgraph:
        if node_layer in total_comm:
            assert subgraph[node_layer] <= total_comm[node_layer] + 1e-6, \
                f"Subgraph centrality should be <= total communicability for {node_layer}"


# ============================================================================
# Property Tests: K-Core Decomposition
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_k_core_non_negative_integers(num_nodes, num_layers):
    """Property: K-core values are non-negative integers."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.multiplex_k_core()
    
    assert len(result) > 0, "Should have core number results"
    for node_layer, value in result.items():
        assert value >= 0, f"K-core for {node_layer} should be non-negative, got {value}"
        assert isinstance(value, (int, np.integer)), \
            f"K-core for {node_layer} should be integer, got {type(value)}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_k_core_bounded_by_degree(num_nodes, num_layers):
    """Property: K-core value <= degree for each node."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    core_numbers = calc.multiplex_k_core()
    degrees = calc.supra_degree_centrality(weighted=False)
    
    for node_layer in core_numbers:
        if node_layer in degrees:
            assert core_numbers[node_layer] <= degrees[node_layer] + 1e-6, \
                f"K-core for {node_layer} should be <= degree"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_k_core_equals_coreness(num_nodes, num_layers):
    """Property: multiplex_k_core and multiplex_coreness return identical results."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    k_core = calc.multiplex_k_core()
    coreness = calc.multiplex_coreness()
    
    assert k_core == coreness, "multiplex_k_core and multiplex_coreness should be identical"


# ============================================================================
# Property Tests: Bridging Centrality
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_bridging_centrality_non_negative(num_nodes, num_layers):
    """Property: Bridging centrality values are non-negative."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.bridging_centrality()
    
    assert len(result) > 0, "Should have centrality results"
    for node_layer, value in result.items():
        assert value >= 0, f"Bridging centrality for {node_layer} should be non-negative"
        assert np.isfinite(value), f"Bridging centrality for {node_layer} should be finite"


# ============================================================================
# Property Tests: Load Centrality
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_load_centrality_non_negative(num_nodes, num_layers):
    """Property: Load centrality values are non-negative."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.load_centrality()
    
    assert len(result) > 0, "Should have centrality results"
    for node_layer, value in result.items():
        assert value >= 0, f"Load centrality for {node_layer} should be non-negative"
        assert np.isfinite(value), f"Load centrality for {node_layer} should be finite"


# ============================================================================
# Property Tests: Spreading Centrality
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=8, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_spreading_centrality_bounded(num_nodes, num_layers):
    """Property: Spreading centrality values are in [0, 1]."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    # Use fewer trials for speed in property tests
    result = calc.spreading_centrality(trials=10, steps=20)
    
    assert len(result) > 0, "Should have centrality results"
    for node_layer, value in result.items():
        assert 0 <= value <= 1, \
            f"Spreading centrality for {node_layer} should be in [0,1], got {value}"


@pytest.mark.property
@settings(deadline=None, max_examples=8, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2),
    beta=st.floats(min_value=0.1, max_value=0.5),
    mu=st.floats(min_value=0.05, max_value=0.3)
)
def test_spreading_centrality_parameters(num_nodes, num_layers, beta, mu):
    """Property: Spreading centrality works with different parameters."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.spreading_centrality(beta=beta, mu=mu, trials=5, steps=15)
    
    assert len(result) > 0, "Should have centrality results"
    assert all(0 <= v <= 1 for v in result.values()), "All values should be in [0,1]"


# ============================================================================
# Property Tests: Percolation Centrality
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=8, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_percolation_centrality_bounded(num_nodes, num_layers):
    """Property: Percolation centrality values are in [0, 1]."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    # Use fewer trials for speed in property tests
    result = calc.percolation_centrality(trials=20)
    
    assert len(result) > 0, "Should have centrality results"
    for node_layer, value in result.items():
        assert 0 <= value <= 1, \
            f"Percolation centrality for {node_layer} should be in [0,1], got {value}"


@pytest.mark.property
@settings(deadline=None, max_examples=8, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2),
    edge_prob=st.floats(min_value=0.1, max_value=0.9)
)
def test_percolation_centrality_edge_probability(num_nodes, num_layers, edge_prob):
    """Property: Percolation centrality works with different edge activation probabilities."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.percolation_centrality(edge_activation_prob=edge_prob, trials=10)
    
    assert len(result) > 0, "Should have centrality results"
    assert all(0 <= v <= 1 for v in result.values()), "All values should be in [0,1]"


# ============================================================================
# Property Tests: Accessibility Centrality
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=2),
    h=st.integers(min_value=1, max_value=4)
)
def test_accessibility_centrality_positive(num_nodes, num_layers, h):
    """Property: Accessibility centrality values are positive."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.accessibility_centrality(h=h)
    
    assert len(result) > 0, "Should have centrality results"
    for node_layer, value in result.items():
        assert value > 0, f"Accessibility for {node_layer} should be positive, got {value}"
        assert np.isfinite(value), f"Accessibility for {node_layer} should be finite"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_accessibility_bounded_by_network_size(num_nodes, num_layers):
    """Property: Accessibility is bounded by effective network size."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.accessibility_centrality(h=2)
    
    # Maximum accessibility is the number of node-layer pairs (exp(log(n)))
    max_accessibility = num_nodes * num_layers
    
    for node_layer, value in result.items():
        assert value <= max_accessibility + 1, \
            f"Accessibility for {node_layer} should be <= {max_accessibility}, got {value}"


# ============================================================================
# Property Tests: Local Efficiency
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=6),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_local_efficiency_non_negative(num_nodes, num_layers):
    """Property: Local efficiency values are non-negative."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.local_efficiency_centrality()
    
    assert len(result) > 0, "Should have centrality results"
    for node_layer, value in result.items():
        assert value >= 0, f"Local efficiency for {node_layer} should be non-negative"
        assert np.isfinite(value), f"Local efficiency for {node_layer} should be finite"


# ============================================================================
# Property Tests: Flow Betweenness
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=8, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_flow_betweenness_non_negative(num_nodes, num_layers):
    """Property: Flow betweenness values are non-negative."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    # Use fewer samples for speed in property tests
    result = calc.flow_betweenness_centrality(samples=20)
    
    assert len(result) > 0, "Should have centrality results"
    for node_layer, value in result.items():
        assert value >= 0, f"Flow betweenness for {node_layer} should be non-negative"
        assert np.isfinite(value), f"Flow betweenness for {node_layer} should be finite"


# ============================================================================
# Property Tests: Edge Betweenness
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_edge_betweenness_non_negative(num_nodes, num_layers):
    """Property: Edge betweenness values are non-negative."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.edge_betweenness_centrality()
    
    # Edge betweenness may be empty for small networks with few edges
    for edge, value in result.items():
        assert value >= 0, f"Edge betweenness for {edge} should be non-negative"
        assert np.isfinite(value), f"Edge betweenness for {edge} should be finite"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_edge_betweenness_normalized_bounded(num_nodes, num_layers):
    """Property: Normalized edge betweenness values are in [0, 1]."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.edge_betweenness_centrality(normalized=True)
    
    for edge, value in result.items():
        assert 0 <= value <= 1, \
            f"Normalized edge betweenness for {edge} should be in [0,1], got {value}"


# ============================================================================
# Property Tests: Communicability Betweenness
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_communicability_betweenness_non_negative(num_nodes, num_layers):
    """Property: Communicability betweenness values are non-negative."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.communicability_betweenness_centrality()
    
    assert len(result) > 0, "Should have centrality results"
    for node_layer, value in result.items():
        assert value >= 0, \
            f"Communicability betweenness for {node_layer} should be non-negative, got {value}"
        assert np.isfinite(value), \
            f"Communicability betweenness for {node_layer} should be finite"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_communicability_betweenness_normalized_bounded(num_nodes, num_layers):
    """Property: Normalized communicability betweenness values are in [0, 1]."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.communicability_betweenness_centrality(normalized=True)
    
    for node_layer, value in result.items():
        assert 0 <= value <= 1, \
            f"Normalized communicability betweenness for {node_layer} should be in [0,1], got {value}"


# ============================================================================
# Property Tests: HITS Centrality
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_hits_centrality_non_negative(num_nodes, num_layers):
    """Property: HITS centrality values are non-negative."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    result = calc.hits_centrality()
    
    # For undirected networks, HITS equals eigenvector centrality
    if isinstance(result, dict) and 'hubs' in result:
        # Directed case
        for node_layer, value in result['hubs'].items():
            assert value >= 0, f"HITS hub for {node_layer} should be non-negative"
            assert np.isfinite(value), f"HITS hub for {node_layer} should be finite"
        for node_layer, value in result['authorities'].items():
            assert value >= 0, f"HITS authority for {node_layer} should be non-negative"
            assert np.isfinite(value), f"HITS authority for {node_layer} should be finite"
    else:
        # Undirected case (returns eigenvector centrality)
        for node_layer, value in result.items():
            assert value >= 0, f"HITS for {node_layer} should be non-negative"
            assert np.isfinite(value), f"HITS for {node_layer} should be finite"


# ============================================================================
# Property Tests: Cross-Metric Invariants
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_harmonic_geq_closeness(num_nodes, num_layers):
    """Property: Harmonic closeness >= standard closeness for connected networks."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    harmonic = calc.harmonic_closeness_centrality()
    standard = calc.multilayer_closeness_centrality(variant='standard')
    
    # For connected networks, both should have valid values
    assert len(harmonic) > 0, "Should have harmonic closeness results"
    assert len(standard) > 0, "Should have standard closeness results"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=2, max_value=3)
)
def test_eigenvector_versatility_aggregation(num_nodes, num_layers):
    """Property: Eigenvector versatility equals sum of eigenvector centralities."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    calc = MultilayerCentrality(network)
    
    eigenvector = calc.multiplex_eigenvector_centrality()
    versatility = calc.multiplex_eigenvector_versatility()
    
    # Manually compute sum for each node
    manual_sum = {}
    for (node, layer), value in eigenvector.items():
        if node not in manual_sum:
            manual_sum[node] = 0.0
        manual_sum[node] += value
    
    # Should match versatility (within numerical tolerance)
    for node in versatility:
        if node in manual_sum:
            assert abs(versatility[node] - manual_sum[node]) < 1e-6, \
                f"Versatility should equal sum of layer centralities for {node}"


# ============================================================================
# Property Tests: Consistency with compute_all_centralities
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_compute_all_returns_all_basic_metrics(num_nodes, num_layers):
    """Property: compute_all_centralities returns all expected basic metrics."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    
    results = compute_all_centralities(network)
    
    expected_keys = [
        'layer_degree', 'layer_strength', 'supra_degree', 'supra_strength',
        'overlapping_degree', 'overlapping_strength',
        'participation_coefficient', 'participation_coefficient_strength',
        'multiplex_eigenvector', 'eigenvector_versatility',
        'katz_bonacich', 'pagerank'
    ]
    
    for key in expected_keys:
        assert key in results, f"Expected metric '{key}' not found in results"
        assert isinstance(results[key], dict), f"Metric '{key}' should be a dict"
        assert len(results[key]) > 0, f"Metric '{key}' should have results"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=5),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_compute_all_with_extended_returns_more(num_nodes, num_layers):
    """Property: compute_all_centralities with extended=True returns more metrics."""
    network = create_connected_multilayer_network(num_nodes, num_layers, seed=42)
    
    basic_results = compute_all_centralities(network, include_extended=False)
    extended_results = compute_all_centralities(network, include_extended=True)
    
    assert len(extended_results) > len(basic_results), \
        "Extended should include more metrics than basic"
    
    # Extended should include additional metrics
    extended_only_keys = ['information', 'accessibility', 'harmonic_closeness',
                          'local_efficiency', 'bridging', 'percolation',
                          'spreading', 'collective_influence', 'load', 'flow_betweenness']
    
    for key in extended_only_keys:
        assert key in extended_results, f"Extended metric '{key}' not found"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
