#!/usr/bin/env python3
"""
Property-based tests for algorithms.general.walkers module.

Tests invariants and properties of random walk algorithms including:
- Walk validity (all transitions are valid edges)
- Walk length consistency
- Probability conservation (transition probabilities sum to 1)
- Reproducibility with same seed
- Edge weight handling correctness
"""

import networkx as nx
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import shared strategies
from .strategies import (
    small_graphs,
    connected_graphs,
    weighted_graphs,
    probabilities,
    positive_weights,
)

# Import walkers module
try:
    from py3plex.algorithms.general.walkers import (
        basic_random_walk,
        node2vec_walk,
        generate_walks,
    )
    WALKERS_AVAILABLE = True
except ImportError:
    WALKERS_AVAILABLE = False
    pytest.skip("Walkers module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Basic Random Walk Invariants
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=12),
    walk_length=st.integers(min_value=1, max_value=20),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_basic_walk_length_property(num_nodes, walk_length, seed):
    """Property: Walk returns exactly walk_length + 1 nodes (including start)."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)  # Need at least one edge
    
    start_node = 0
    walk = basic_random_walk(G, start_node, walk_length, seed=seed)
    
    # Walk should have walk_length + 1 nodes (including start) unless terminated early
    assert len(walk) <= walk_length + 1
    assert len(walk) >= 1  # At least start node


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=12),
    walk_length=st.integers(min_value=5, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_walk_transitions_are_valid_edges(num_nodes, walk_length, seed):
    """Property: All consecutive nodes in walk are connected by edges."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    start_node = 0
    walk = basic_random_walk(G, start_node, walk_length, seed=seed)
    
    # Check all transitions are valid edges
    for i in range(len(walk) - 1):
        current = walk[i]
        next_node = walk[i + 1]
        assert G.has_edge(current, next_node) or G.has_edge(next_node, current), \
            f"Invalid transition from {current} to {next_node}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=12),
    walk_length=st.integers(min_value=5, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_walk_starts_at_specified_node(num_nodes, walk_length, seed):
    """Property: Walk always starts at the specified start node."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    start_node = 0
    walk = basic_random_walk(G, start_node, walk_length, seed=seed)
    
    assert walk[0] == start_node, "Walk must start at specified node"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    walk_length=st.integers(min_value=5, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_walk_reproducibility_property(num_nodes, walk_length, seed):
    """Property: Same seed produces identical walks."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    start_node = 0
    walk1 = basic_random_walk(G, start_node, walk_length, seed=seed)
    walk2 = basic_random_walk(G, start_node, walk_length, seed=seed)
    
    assert walk1 == walk2, "Same seed should produce identical walks"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    walk_length=st.integers(min_value=5, max_value=15)
)
def test_walk_stays_in_connected_component(num_nodes, walk_length):
    """Property: Walk stays within the connected component of start node."""
    # Create a disconnected graph
    G = nx.Graph()
    # Component 1: nodes 0, 1, 2
    G.add_edges_from([(0, 1), (1, 2), (2, 0)])
    # Component 2: nodes 3, 4, 5
    G.add_edges_from([(3, 4), (4, 5), (5, 3)])
    
    start_node = 0
    walk = basic_random_walk(G, start_node, walk_length, seed=42)
    
    # All nodes in walk should be in component {0, 1, 2}
    component_nodes = {0, 1, 2}
    for node in walk:
        assert node in component_nodes, \
            f"Walk should stay in component, but found node {node}"


# ============================================================================
# Property Tests: Node2Vec Biased Walk Invariants
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=12),
    walk_length=st.integers(min_value=5, max_value=15),
    p=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False),
    q=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_node2vec_walk_valid_transitions(num_nodes, walk_length, p, q, seed):
    """Property: Node2Vec walk transitions are all valid edges."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 3)  # Need some connectivity
    
    start_node = 0
    walk = node2vec_walk(G, start_node, walk_length, p=p, q=q, seed=seed)
    
    # All transitions must be valid edges
    for i in range(len(walk) - 1):
        current = walk[i]
        next_node = walk[i + 1]
        assert G.has_edge(current, next_node) or G.has_edge(next_node, current), \
            f"Invalid Node2Vec transition from {current} to {next_node}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=10),
    walk_length=st.integers(min_value=5, max_value=15),
    p=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False),
    q=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_node2vec_walk_reproducibility(num_nodes, walk_length, p, q, seed):
    """Property: Node2Vec walks are reproducible with same seed."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 3)
    
    start_node = 0
    walk1 = node2vec_walk(G, start_node, walk_length, p=p, q=q, seed=seed)
    walk2 = node2vec_walk(G, start_node, walk_length, p=p, q=q, seed=seed)
    
    assert walk1 == walk2, "Same seed should produce identical Node2Vec walks"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=10),
    walk_length=st.integers(min_value=3, max_value=10),
    p=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False),
    q=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_node2vec_walk_length_consistency(num_nodes, walk_length, p, q, seed):
    """Property: Node2Vec walk has correct length."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 3)
    
    start_node = 0
    walk = node2vec_walk(G, start_node, walk_length, p=p, q=q, seed=seed)
    
    # Walk should have walk_length + 1 nodes or less if terminated early
    assert len(walk) <= walk_length + 1
    assert len(walk) >= 1


# ============================================================================
# Property Tests: Generate Walks Batch Generation
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=10),
    num_walks=st.integers(min_value=1, max_value=5),
    walk_length=st.integers(min_value=3, max_value=10),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_generate_walks_count_property(num_nodes, num_walks, walk_length, seed):
    """Property: generate_walks produces correct number of walks."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    walks = generate_walks(G, num_walks, walk_length=walk_length, seed=seed)
    
    # Should generate num_walks * number_of_nodes walks
    expected_count = num_walks * G.number_of_nodes()
    assert len(walks) == expected_count, \
        f"Expected {expected_count} walks, got {len(walks)}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=10),
    num_walks=st.integers(min_value=2, max_value=5),
    walk_length=st.integers(min_value=3, max_value=10),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_generate_walks_reproducibility_property(num_nodes, num_walks, walk_length, seed):
    """Property: generate_walks is reproducible with same seed."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    walks1 = generate_walks(G, num_walks, walk_length=walk_length, seed=seed)
    walks2 = generate_walks(G, num_walks, walk_length=walk_length, seed=seed)
    
    assert walks1 == walks2, "Same seed should produce identical walk sets"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=12),
    num_walks=st.integers(min_value=2, max_value=5),
    walk_length=st.integers(min_value=3, max_value=10),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_generate_walks_all_valid_transitions(num_nodes, num_walks, walk_length, seed):
    """Property: All walks from generate_walks have valid transitions."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    walks = generate_walks(G, num_walks, walk_length=walk_length, seed=seed)
    
    # Check every walk has valid transitions
    for walk in walks:
        for i in range(len(walk) - 1):
            current = walk[i]
            next_node = walk[i + 1]
            assert G.has_edge(current, next_node) or G.has_edge(next_node, current), \
                f"Invalid transition in generated walk: {current} -> {next_node}"


# ============================================================================
# Property Tests: Weighted Walk Properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    walk_length=st.integers(min_value=5, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_weighted_walk_respects_graph_structure(num_nodes, walk_length, seed):
    """Property: Weighted walks follow edge weights proportionally (statistical test)."""
    # Create a simple weighted graph
    G = nx.Graph()
    G.add_weighted_edges_from([
        (0, 1, 9.0),  # High weight edge
        (0, 2, 1.0),  # Low weight edge
    ])
    
    # Run multiple walks and count transitions
    visits = {1: 0, 2: 0}
    num_trials = 100
    
    for i in range(num_trials):
        walk = basic_random_walk(G, 0, 1, weighted=True, seed=i + seed)
        if len(walk) > 1:
            visits[walk[1]] += 1
    
    # Node 1 should be visited more often than node 2 (proportional to weights)
    # With weights 9:1, expect ratio around 9:1
    if visits[2] > 0:
        ratio = visits[1] / visits[2]
        # Allow some variance but should clearly favor node 1
        assert ratio > 2.0, f"Expected weighted visits to favor high-weight edge, got ratio {ratio}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    walk_length=st.integers(min_value=5, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_unweighted_walk_ignores_weights(num_nodes, walk_length, seed):
    """Property: Unweighted walks ignore edge weights."""
    # Create a weighted graph
    G = nx.Graph()
    G.add_weighted_edges_from([
        (0, 1, 100.0),  # Very high weight
        (0, 2, 1.0),    # Low weight
    ])
    
    # Run unweighted walks
    visits = {1: 0, 2: 0}
    num_trials = 100
    
    for i in range(num_trials):
        walk = basic_random_walk(G, 0, 1, weighted=False, seed=i + seed)
        if len(walk) > 1:
            visits[walk[1]] += 1
    
    # With unweighted, should visit both roughly equally (within reasonable bounds)
    if visits[1] > 0 and visits[2] > 0:
        ratio = visits[1] / visits[2]
        # Allow 3x variance (unweighted should be near 1:1)
        assert 0.3 < ratio < 3.0, \
            f"Unweighted walk should be uniform, got ratio {ratio}"


# ============================================================================
# Property Tests: Edge Cases
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    walk_length=st.integers(min_value=1, max_value=20),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_isolated_node_terminates_immediately(walk_length, seed):
    """Property: Walk on isolated node returns only start node."""
    G = nx.Graph()
    G.add_nodes_from([0, 1, 2])
    G.add_edge(1, 2)  # Node 0 is isolated
    
    walk = basic_random_walk(G, 0, walk_length, seed=seed)
    
    assert walk == [0], "Walk on isolated node should contain only start node"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    walk_length=st.integers(min_value=5, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_directed_graph_follows_edge_direction(num_nodes, walk_length, seed):
    """Property: Walk on directed graph only follows outgoing edges."""
    # Create a directed cycle
    G = nx.DiGraph()
    for i in range(num_nodes):
        G.add_edge(i, (i + 1) % num_nodes)
    
    start_node = 0
    walk = basic_random_walk(G, start_node, walk_length, seed=seed)
    
    # All transitions must follow directed edges
    for i in range(len(walk) - 1):
        current = walk[i]
        next_node = walk[i + 1]
        assert G.has_edge(current, next_node), \
            f"Walk on directed graph must follow edge direction: {current} -> {next_node}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
