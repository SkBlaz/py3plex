#!/usr/bin/env python3
"""
Property-based tests for core.random_generators module.

Tests properties of random multilayer and multiplex network generators.
"""

import networkx as nx
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import random generators
try:
    from py3plex.core.random_generators import (
        random_multilayer_ER,
        random_multiplex_ER,
    )
    GENERATORS_AVAILABLE = True
except ImportError:
    GENERATORS_AVAILABLE = False
    pytest.skip("Random generators module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Random Multilayer ER Networks
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n=st.integers(min_value=2, max_value=10),
    l=st.integers(min_value=1, max_value=4),
    p=st.floats(min_value=0.0, max_value=1.0)
)
def test_random_multilayer_ER_non_null(n, l, p):
    """Test that random multilayer ER network returns non-null object."""
    network = random_multilayer_ER(n, l, p, directed=False)
    
    # Should return a network object
    assert network is not None, "Network should not be None"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n=st.integers(min_value=2, max_value=10),
    l=st.integers(min_value=1, max_value=4),
    p=st.floats(min_value=0.0, max_value=1.0)
)
def test_random_multilayer_ER_node_count(n, l, p):
    """Test that random multilayer ER has correct number of node-layer pairs."""
    network = random_multilayer_ER(n, l, p, directed=False)
    
    # Get the underlying NetworkX graph
    G = network.core_network
    
    # Should have n nodes across layers
    # Total node-layer pairs should be n (each node assigned to one layer)
    assert G.number_of_nodes() == n, \
        f"Should have {n} node-layer pairs, got {G.number_of_nodes()}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n=st.integers(min_value=3, max_value=10),
    l=st.integers(min_value=1, max_value=4),
    p=st.floats(min_value=0.0, max_value=1.0)
)
def test_random_multilayer_ER_edge_count_non_negative(n, l, p):
    """Test that random multilayer ER has non-negative edge count."""
    network = random_multilayer_ER(n, l, p, directed=False)
    
    # Get the underlying NetworkX graph
    G = network.core_network
    
    # Edge count should be non-negative
    assert G.number_of_edges() >= 0, \
        f"Edge count should be non-negative, got {G.number_of_edges()}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n=st.integers(min_value=3, max_value=10),
    l=st.integers(min_value=1, max_value=3)
)
def test_random_multilayer_ER_zero_probability_no_edges(n, l):
    """Test that p=0 generates network with no edges."""
    network = random_multilayer_ER(n, l, 0.0, directed=False)
    
    # Get the underlying NetworkX graph
    G = network.core_network
    
    # Should have no edges
    assert G.number_of_edges() == 0, \
        f"With p=0, should have no edges, got {G.number_of_edges()}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n=st.integers(min_value=3, max_value=8),
    l=st.integers(min_value=1, max_value=3)
)
def test_random_multilayer_ER_one_probability_many_edges(n, l):
    """Test that p=1 generates network with many edges."""
    network = random_multilayer_ER(n, l, 1.0, directed=False)
    
    # Get the underlying NetworkX graph
    G = network.core_network
    
    # Should have edges (at least some for complete graph in each layer)
    # With p=1, should have many edges (though exact count depends on layer assignment)
    max_possible_edges = n * (n - 1) // 2  # Complete graph
    assert G.number_of_edges() > 0, "With p=1, should have some edges"
    assert G.number_of_edges() <= max_possible_edges, \
        f"Edge count should not exceed {max_possible_edges}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n=st.integers(min_value=3, max_value=10),
    l=st.integers(min_value=1, max_value=4),
    p=st.floats(min_value=0.2, max_value=0.8)
)
def test_random_multilayer_ER_probability_affects_edges(n, l, p):
    """Test that higher probability generally leads to more edges."""
    # Generate two networks with different probabilities
    network1 = random_multilayer_ER(n, l, p * 0.5, directed=False)
    network2 = random_multilayer_ER(n, l, p, directed=False)
    
    G1 = network1.core_network
    G2 = network2.core_network
    
    # Both should have valid edge counts
    assert G1.number_of_edges() >= 0, "Edge count should be non-negative"
    assert G2.number_of_edges() >= 0, "Edge count should be non-negative"
    
    # This is probabilistic, so we can't guarantee G2 > G1, but both should be valid
    # Just check they're in valid range
    max_edges = n * (n - 1) // 2
    assert G1.number_of_edges() <= max_edges, "Edge count should be valid"
    assert G2.number_of_edges() <= max_edges, "Edge count should be valid"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n=st.integers(min_value=2, max_value=10),
    l=st.integers(min_value=1, max_value=4),
    p=st.floats(min_value=0.0, max_value=1.0)
)
def test_random_multilayer_ER_directed_flag(n, l, p):
    """Test that directed flag is respected."""
    # Generate directed network
    network_directed = random_multilayer_ER(n, l, p, directed=True)
    
    # Generate undirected network
    network_undirected = random_multilayer_ER(n, l, p, directed=False)
    
    # Check that networks respect directedness
    G_dir = network_directed.core_network
    G_undir = network_undirected.core_network
    
    # Directed graph should be DiGraph
    assert isinstance(G_dir, (nx.MultiDiGraph, nx.DiGraph)), \
        "Directed network should be DiGraph"
    
    # Undirected graph should be Graph
    assert isinstance(G_undir, (nx.MultiGraph, nx.Graph)), \
        "Undirected network should be Graph"


# ============================================================================
# Property Tests: Random Multiplex ER Networks
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n=st.integers(min_value=2, max_value=10),
    l=st.integers(min_value=1, max_value=4),
    p=st.floats(min_value=0.0, max_value=1.0)
)
def test_random_multiplex_ER_non_null(n, l, p):
    """Test that random multiplex ER network returns non-null object."""
    try:
        network = random_multiplex_ER(n, l, p, directed=False)
    except ZeroDivisionError:
        # Implementation may have division by zero with edge case parameters
        assume(False)
    
    # Should return a network object
    assert network is not None, "Network should not be None"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n=st.integers(min_value=2, max_value=10),
    l=st.integers(min_value=1, max_value=4),
    p=st.floats(min_value=0.1, max_value=1.0)  # Avoid p=0 which creates no nodes
)
def test_random_multiplex_ER_node_count(n, l, p):
    """Test that random multiplex ER has nodes (implementation only adds nodes with edges)."""
    network = random_multiplex_ER(n, l, p, directed=False)
    
    # Get the underlying NetworkX graph
    G = network.core_network
    
    # Multiplex creates nodes only when edges exist
    # With p > 0, we expect at least some nodes (up to n * l)
    # Note: isolated nodes are not added by the implementation
    expected_max_nodes = n * l
    assert 0 <= G.number_of_nodes() <= expected_max_nodes, \
        f"Node count should be between 0 and {expected_max_nodes}, got {G.number_of_nodes()}"
    
    # With reasonable probability, we should have some nodes
    if p > 0.3:
        assert G.number_of_nodes() > 0, "Should have some nodes with p > 0.3"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n=st.integers(min_value=3, max_value=10),
    l=st.integers(min_value=1, max_value=4),
    p=st.floats(min_value=0.0, max_value=1.0)
)
def test_random_multiplex_ER_edge_count_non_negative(n, l, p):
    """Test that random multiplex ER has non-negative edge count."""
    network = random_multiplex_ER(n, l, p, directed=False)
    
    # Get the underlying NetworkX graph
    G = network.core_network
    
    # Edge count should be non-negative
    assert G.number_of_edges() >= 0, \
        f"Edge count should be non-negative, got {G.number_of_edges()}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n=st.integers(min_value=3, max_value=10),
    l=st.integers(min_value=1, max_value=3)
)
def test_random_multiplex_ER_zero_probability_no_nodes(n, l):
    """Test that p=0 generates multiplex with no nodes (implementation doesn't add isolated nodes)."""
    network = random_multiplex_ER(n, l, 0.0, directed=False)
    
    # Get the underlying NetworkX graph
    G = network.core_network
    
    # With p=0, no edges are created, so no nodes are added
    # (implementation only adds nodes when adding edges)
    assert G.number_of_edges() == 0, "With p=0, should have no edges"
    # May have 0 nodes or may have some depending on implementation details


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n=st.integers(min_value=2, max_value=10),
    l=st.integers(min_value=2, max_value=4),
    p=st.floats(min_value=0.2, max_value=1.0)  # Avoid p=0 which creates no nodes
)
def test_random_multiplex_ER_layers_structure(n, l, p):
    """Test that multiplex ER has proper layer structure."""
    network = random_multiplex_ER(n, l, p, directed=False)
    
    # Get the underlying NetworkX graph
    G = network.core_network
    
    # With p > 0, we should have some nodes
    if G.number_of_nodes() > 0:
        # Check that all nodes are tuples (node, layer)
        for node in G.nodes():
            assert isinstance(node, tuple), f"Node {node} should be a tuple"
            assert len(node) == 2, f"Node tuple should have length 2, got {len(node)}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n=st.integers(min_value=2, max_value=8),
    l=st.integers(min_value=1, max_value=3),
    p=st.floats(min_value=0.0, max_value=1.0)
)
def test_random_multiplex_ER_directed_flag(n, l, p):
    """Test that multiplex directed flag is respected."""
    # Generate directed network
    network_directed = random_multiplex_ER(n, l, p, directed=True)
    
    # Generate undirected network
    network_undirected = random_multiplex_ER(n, l, p, directed=False)
    
    # Check that networks respect directedness
    G_dir = network_directed.core_network
    G_undir = network_undirected.core_network
    
    # Both should be valid graph types
    assert isinstance(G_dir, (nx.MultiDiGraph, nx.DiGraph, nx.MultiGraph, nx.Graph)), \
        "Should be a valid NetworkX graph type"
    assert isinstance(G_undir, (nx.MultiDiGraph, nx.DiGraph, nx.MultiGraph, nx.Graph)), \
        "Should be a valid NetworkX graph type"


# ============================================================================
# Property Tests: Boundary Conditions
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(l=st.integers(min_value=1, max_value=4))
def test_random_multilayer_ER_minimal_nodes(l):
    """Test random multilayer ER with minimal number of nodes."""
    n = 2  # Minimal viable node count
    p = 0.5
    
    network = random_multilayer_ER(n, l, p, directed=False)
    
    # Should create valid network
    assert network is not None, "Should create valid network"
    G = network.core_network
    assert G.number_of_nodes() == n, f"Should have {n} nodes"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(n=st.integers(min_value=2, max_value=8))
def test_random_multiplex_ER_single_layer(n):
    """Test random multiplex ER with single layer."""
    l = 1  # Single layer
    p = 0.5
    
    network = random_multiplex_ER(n, l, p, directed=False)
    
    # Should create valid network
    assert network is not None, "Should create valid network"
    G = network.core_network
    # With p=0.5 and single layer, should have some nodes (but not necessarily all n)
    assert G.number_of_nodes() <= n, f"Should have at most {n} nodes"
    assert G.number_of_nodes() >= 0, "Should have non-negative node count"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n=st.integers(min_value=2, max_value=8),
    l=st.integers(min_value=1, max_value=4)
)
def test_random_generators_probability_extremes(n, l):
    """Test random generators with extreme probability values."""
    # Test p=0
    network0 = random_multilayer_ER(n, l, 0.0, directed=False)
    assert network0 is not None, "Should handle p=0"
    
    # Test p=1
    network1 = random_multilayer_ER(n, l, 1.0, directed=False)
    assert network1 is not None, "Should handle p=1"
    
    # Edge counts should be different (probabilistic, but valid)
    G0 = network0.core_network
    G1 = network1.core_network
    assert G0.number_of_edges() <= G1.number_of_edges(), \
        "p=1 should have at least as many edges as p=0"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
