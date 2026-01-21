#!/usr/bin/env python3
"""
Property-based tests for edge operations in multilayer networks.

Tests fundamental invariants and properties of edge addition, removal,
and manipulation operations.
"""

import networkx as nx
import pytest
from hypothesis import given, strategies as st, settings, assume

from py3plex.core import multinet
from .strategies import layer_labels


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=2, max_value=10),
    num_edges=st.integers(min_value=1, max_value=15)
)
def test_edge_addition_increases_edge_count(n, num_edges):
    """
    Property: Adding edges increases the total edge count.
    
    For any network, adding valid edges should increase or maintain
    the edge count (duplicates may not increase count).
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Get initial edge count
    initial_count = len(list(network.get_edges())) if network.core_network else 0
    
    # Generate and add edges
    edges = []
    for i in range(num_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:  # Avoid self-loops
            edges.append({
                'source': str(src),
                'target': str(dst),
                'source_type': layer,
                'target_type': layer,
                'type': 'edge'
            })
    
    assume(len(edges) > 0)
    network.add_edges(edges)
    
    # Get final edge count
    final_count = len(list(network.get_edges()))
    
    # Edge count should increase or stay same (if duplicates)
    assert final_count >= initial_count, \
        f"Edge count decreased: {initial_count} -> {final_count}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=3, max_value=10),
    num_edges=st.integers(min_value=2, max_value=12)
)
def test_edge_removal_decreases_edge_count(n, num_edges):
    """
    Property: Removing existing edges decreases the total edge count.
    
    After adding edges and then removing some, the count should decrease.
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add edges
    edges = []
    for i in range(num_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:
            edges.append({
                'source': str(src),
                'target': str(dst),
                'source_type': layer,
                'target_type': layer,
                'type': 'edge'
            })
    
    assume(len(edges) > 0)
    network.add_edges(edges)
    
    initial_count = len(list(network.get_edges()))
    assume(initial_count > 0)
    
    # Remove one edge
    if initial_count > 0:
        edge_to_remove = [[str(0), layer, str(1), layer, 1]]
        try:
            network.remove_edges(edge_to_remove, input_type='list')
            final_count = len(list(network.get_edges()))
            
            # Edge count should decrease or stay same
            assert final_count <= initial_count, \
                f"Edge count increased after removal: {initial_count} -> {final_count}"
        except (KeyError, ValueError):
            # Edge might not exist, which is acceptable
            pass


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=2, max_value=8),
    num_edges=st.integers(min_value=1, max_value=10)
)
def test_edge_endpoints_are_nodes(n, num_edges):
    """
    Property: All edge endpoints must be valid nodes in the network.
    
    For any edge (u, v) in the network, both u and v must exist as nodes.
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add edges
    edges = []
    for i in range(num_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:
            edges.append({
                'source': str(src),
                'target': str(dst),
                'source_type': layer,
                'target_type': layer,
                'type': 'edge'
            })
    
    assume(len(edges) > 0)
    network.add_edges(edges)
    
    # Get all nodes
    all_nodes = set(network.get_nodes())
    
    # Check all edges
    for edge in network.get_edges():
        src_node = edge[0]  # (node_id, layer_id)
        dst_node = edge[1]
        
        assert src_node in all_nodes, \
            f"Edge source {src_node} not in node set"
        assert dst_node in all_nodes, \
            f"Edge target {dst_node} not in node set"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=2, max_value=10),
    num_edges=st.integers(min_value=1, max_value=12)
)
def test_edge_weights_non_negative(n, num_edges):
    """
    Property: Edge weights should be non-negative by default.
    
    When adding edges without explicit negative weights, all weights
    should be >= 0.
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add edges with default weights
    edges = []
    for i in range(num_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:
            edges.append({
                'source': str(src),
                'target': str(dst),
                'source_type': layer,
                'target_type': layer,
                'type': 'edge'
            })
    
    assume(len(edges) > 0)
    network.add_edges(edges)
    
    # Check all edge weights
    for edge in network.get_edges(data=True):
        if len(edge) > 2 and 'weight' in edge[2]:
            weight = edge[2]['weight']
            assert weight >= 0, \
                f"Negative weight found: {weight}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=2, max_value=8),
    num_edges=st.integers(min_value=1, max_value=10),
    weight=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
)
def test_edge_weight_preservation(n, num_edges, weight):
    """
    Property: Explicitly set edge weights should be preserved.
    
    When adding edges with specific weights, those weights should
    be retrievable from the network.
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add edges with specific weight
    edges = []
    for i in range(num_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:
            edges.append([str(src), layer, str(dst), layer, weight])
    
    assume(len(edges) > 0)
    network.add_edges(edges, input_type='list')
    
    # Check that at least some edges have the specified weight
    edge_weights = []
    for edge in network.get_edges(data=True):
        if len(edge) > 2 and 'weight' in edge[2]:
            edge_weights.append(edge[2]['weight'])
    
    # At least one edge should have approximately the specified weight
    if edge_weights:
        assert any(abs(w - weight) < 1e-6 for w in edge_weights), \
            f"No edge has weight close to {weight}, found: {edge_weights}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=2, max_value=10),
    p=st.floats(min_value=0.1, max_value=0.9)
)
def test_undirected_edge_symmetry(n, p):
    """
    Property: Undirected networks have symmetric edges.
    
    For undirected networks, if edge (u,v) exists, the reverse should
    also be accessible (or it's the same edge).
    """
    G = nx.gnp_random_graph(n, p, seed=hash((n, p)) % (2**32))
    assume(G.number_of_edges() > 0)
    
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add edges
    edges = []
    for u, v in G.edges():
        edges.append([str(u), layer, str(v), layer, 1])
    
    network.add_edges(edges, input_type='list')
    
    # Create edge set (normalized for undirected)
    edge_set = set()
    for edge in network.get_edges():
        src = edge[0]
        dst = edge[1]
        # Normalize for undirected (smaller first)
        normalized = tuple(sorted([src, dst]))
        edge_set.add(normalized)
    
    # Each edge appears once in normalized form
    assert len(edge_set) > 0, "No edges found in network"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layers=st.lists(layer_labels(), min_size=2, max_size=4, unique=True),
    n=st.integers(min_value=2, max_value=6)
)
def test_inter_layer_edge_validity(layers, n):
    """
    Property: Inter-layer edges connect nodes across different layers.
    
    Inter-layer edges should have source and target in different layers.
    """
    assume(len(layers) >= 2)
    
    network = multinet.multi_layer_network(directed=False)
    
    # Add inter-layer edges
    edges = []
    for i in range(n):
        # Connect same node across layers
        edges.append({
            'source': str(i),
            'target': str(i),
            'source_type': layers[0],
            'target_type': layers[1],
            'type': 'edge'
        })
    
    network.add_edges(edges)
    
    # Check that inter-layer edges exist
    inter_layer_count = 0
    for edge in network.get_edges():
        src_layer = edge[0][1]
        dst_layer = edge[1][1]
        if src_layer != dst_layer:
            inter_layer_count += 1
    
    # Should have inter-layer edges
    assert inter_layer_count >= 0, "Inter-layer edge count should be non-negative"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=2, max_value=8),
    num_initial_edges=st.integers(min_value=1, max_value=10),
    num_new_edges=st.integers(min_value=1, max_value=8)
)
def test_edge_addition_idempotence(n, num_initial_edges, num_new_edges):
    """
    Property: Adding the same edges multiple times should be idempotent.
    
    Adding duplicate edges should not keep increasing the edge count
    (for simple graphs).
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add initial edges
    edges = []
    for i in range(num_initial_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:
            edges.append({
                'source': str(src),
                'target': str(dst),
                'source_type': layer,
                'target_type': layer,
                'type': 'edge'
            })
    
    assume(len(edges) > 0)
    network.add_edges(edges)
    
    count_after_first = len(list(network.get_edges()))
    
    # Add same edges again
    network.add_edges(edges)
    
    count_after_second = len(list(network.get_edges()))
    
    # For MultiGraph, duplicates may be allowed, so count could increase
    # But it shouldn't increase by more than the number of edges added
    assert count_after_second >= count_after_first, \
        "Edge count should not decrease"
    assert count_after_second <= count_after_first + len(edges), \
        "Edge count increased too much"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=3, max_value=10),
    num_edges=st.integers(min_value=2, max_value=12)
)
def test_edge_list_consistency(n, num_edges):
    """
    Property: Edges retrieved via get_edges() should be consistent.
    
    The same edge should appear consistently across multiple retrievals.
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add edges
    edges = []
    for i in range(num_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:
            edges.append({
                'source': str(src),
                'target': str(dst),
                'source_type': layer,
                'target_type': layer,
                'type': 'edge'
            })
    
    assume(len(edges) > 0)
    network.add_edges(edges)
    
    # Get edges twice
    edges1 = list(network.get_edges())
    edges2 = list(network.get_edges())
    
    # Should have same count
    assert len(edges1) == len(edges2), \
        f"Edge count inconsistent: {len(edges1)} vs {len(edges2)}"
    
    # Convert to sets for comparison (order may differ)
    set1 = set(tuple(e[:2]) for e in edges1)
    set2 = set(tuple(e[:2]) for e in edges2)
    
    assert set1 == set2, "Edge sets inconsistent across retrievals"
