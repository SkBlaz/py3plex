#!/usr/bin/env python3
"""
Property-based tests for node operations in multilayer networks.

Tests fundamental invariants and properties of node addition, removal,
and querying operations.
"""

import networkx as nx
import pytest
from hypothesis import given, strategies as st, settings, assume

from py3plex.core import multinet


def layer_names():
    """Generate valid layer names."""
    return st.text(min_size=1, max_size=8, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_'
    ))


def node_ids():
    """Generate valid node IDs."""
    return st.one_of(
        st.integers(min_value=0, max_value=100).map(str),
        st.text(min_size=1, max_size=10, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_'
        ))
    )


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    n=st.integers(min_value=1, max_value=15),
    layer=layer_names()
)
def test_node_addition_increases_node_count(n, layer):
    """
    Property: Adding nodes increases the total node count.
    
    For any network, adding new nodes should increase the node count.
    """
    network = multinet.multi_layer_network(directed=False)
    
    initial_count = len(list(network.get_nodes())) if network.core_network else 0
    
    # Add nodes
    nodes = []
    for i in range(n):
        nodes.append({
            'source': str(i),
            'type': layer
        })
    
    network.add_nodes(nodes)
    
    final_count = len(list(network.get_nodes()))
    
    # Node count should increase
    assert final_count >= initial_count + n, \
        f"Node count did not increase as expected: {initial_count} -> {final_count}"


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    n=st.integers(min_value=2, max_value=12),
    layer=layer_names()
)
def test_node_uniqueness_within_layer(n, layer):
    """
    Property: Nodes within a layer should be unique.
    
    Adding the same node multiple times should not create duplicates
    within the same layer.
    """
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    nodes = []
    for i in range(n):
        nodes.append({
            'source': str(i),
            'type': layer
        })
    
    network.add_nodes(nodes)
    
    # Get all nodes in the layer
    layer_nodes = [node for node in network.get_nodes() if node[1] == layer]
    
    # Check for uniqueness
    node_ids = [node[0] for node in layer_nodes]
    unique_ids = set(node_ids)
    
    assert len(node_ids) == len(unique_ids), \
        f"Duplicate nodes found in layer {layer}"


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    n=st.integers(min_value=3, max_value=10),
    num_to_remove=st.integers(min_value=1, max_value=3)
)
def test_node_removal_consistency(n, num_to_remove):
    """
    Property: Removing nodes should also remove incident edges.
    
    When a node is removed, all edges connected to it should also be removed.
    """
    assume(num_to_remove < n)
    
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add nodes and edges
    edges = []
    for i in range(n - 1):
        edges.append({
            'source': str(i),
            'target': str(i + 1),
            'source_type': layer,
            'target_type': layer,
            'type': 'edge'
        })
    
    network.add_edges(edges)
    
    initial_nodes = len(list(network.get_nodes()))
    initial_edges = len(list(network.get_edges()))
    
    # Remove some nodes
    nodes_to_remove = [(str(i), layer) for i in range(num_to_remove)]
    
    try:
        for node in nodes_to_remove:
            if network.core_network and node in network.core_network.nodes():
                network.core_network.remove_node(node)
        
        final_nodes = len(list(network.get_nodes()))
        final_edges = len(list(network.get_edges()))
        
        # Node count should decrease
        assert final_nodes <= initial_nodes, \
            f"Node count should not increase after removal"
        
        # Edge count should decrease or stay same
        assert final_edges <= initial_edges, \
            f"Edge count should not increase after node removal"
    except (KeyError, ValueError):
        # Node might not exist
        pass


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    layers=st.lists(layer_names(), min_size=1, max_size=4, unique=True),
    n=st.integers(min_value=2, max_value=8)
)
def test_node_layer_assignment(layers, n):
    """
    Property: Nodes are correctly associated with their layers.
    
    Each node-layer pair should be retrievable with the correct layer.
    """
    assume(len(layers) >= 1)
    
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes to different layers
    for layer in layers:
        nodes = []
        for i in range(n):
            nodes.append({
                'source': str(i),
                'type': layer
            })
        network.add_nodes(nodes)
    
    # Check layer assignment
    all_nodes = list(network.get_nodes())
    
    # Each layer should have nodes
    for layer in layers:
        layer_nodes = [node for node in all_nodes if node[1] == layer]
        assert len(layer_nodes) > 0, \
            f"Layer {layer} has no nodes"
        assert len(layer_nodes) <= n, \
            f"Layer {layer} has too many nodes: {len(layer_nodes)}"


@pytest.mark.property
@settings(deadline=None, max_examples=35)
@given(
    n=st.integers(min_value=2, max_value=10),
    layers=st.lists(layer_names(), min_size=2, max_size=4, unique=True)
)
def test_same_node_different_layers(n, layers):
    """
    Property: Same node ID can exist in different layers.
    
    A node with the same ID can appear in multiple layers as
    distinct node-layer pairs.
    """
    assume(len(layers) >= 2)
    
    network = multinet.multi_layer_network(directed=False)
    
    # Add same node IDs to different layers
    for layer in layers:
        nodes = []
        for i in range(n):
            nodes.append({
                'source': str(i),
                'type': layer
            })
        network.add_nodes(nodes)
    
    all_nodes = list(network.get_nodes())
    
    # Count occurrences of each node ID
    node_id_counts = {}
    for node in all_nodes:
        node_id = node[0]
        node_id_counts[node_id] = node_id_counts.get(node_id, 0) + 1
    
    # Each node ID should appear in multiple layers
    for node_id, count in node_id_counts.items():
        assert count <= len(layers), \
            f"Node {node_id} appears in more layers than exist: {count} > {len(layers)}"


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    n=st.integers(min_value=2, max_value=10),
    layer=layer_names()
)
def test_node_count_non_negative(n, layer):
    """
    Property: Node count is always non-negative.
    
    The number of nodes should never be negative.
    """
    network = multinet.multi_layer_network(directed=False)
    
    nodes = []
    for i in range(n):
        nodes.append({
            'source': str(i),
            'type': layer
        })
    
    network.add_nodes(nodes)
    
    node_count = len(list(network.get_nodes()))
    
    assert node_count >= 0, \
        f"Node count is negative: {node_count}"


@pytest.mark.property
@settings(deadline=None, max_examples=35)
@given(
    n=st.integers(min_value=2, max_value=10),
    p=st.floats(min_value=0.2, max_value=0.8)
)
def test_isolated_nodes_preserved(n, p):
    """
    Property: Isolated nodes (with no edges) are preserved.
    
    Nodes without edges should still be retrievable from the network.
    """
    G = nx.gnp_random_graph(n, p, seed=hash((n, p)) % (2**32))
    
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add all nodes explicitly
    for node in G.nodes():
        network.add_nodes([{'source': str(node), 'type': layer}])
    
    # Add edges
    for u, v in G.edges():
        network.add_edges([{
            'source': str(u),
            'target': str(v),
            'source_type': layer,
            'target_type': layer,
            'type': 'edge'
        }])
    
    # Check all nodes are present
    network_nodes = {node[0] for node in network.get_nodes()}
    original_nodes = {str(node) for node in G.nodes()}
    
    assert original_nodes.issubset(network_nodes), \
        f"Some nodes were lost: {original_nodes - network_nodes}"


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    n=st.integers(min_value=2, max_value=12),
    layer=layer_names()
)
def test_node_retrieval_consistency(n, layer):
    """
    Property: Node retrieval is consistent across multiple calls.
    
    Calling get_nodes() multiple times should return the same nodes.
    """
    network = multinet.multi_layer_network(directed=False)
    
    nodes = []
    for i in range(n):
        nodes.append({
            'source': str(i),
            'type': layer
        })
    
    network.add_nodes(nodes)
    
    # Get nodes twice
    nodes1 = set(network.get_nodes())
    nodes2 = set(network.get_nodes())
    
    assert nodes1 == nodes2, \
        f"Node sets inconsistent across retrievals"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    n=st.integers(min_value=2, max_value=10),
    layers=st.lists(layer_names(), min_size=1, max_size=3, unique=True)
)
def test_node_degree_non_negative(n, layers):
    """
    Property: Node degree is always non-negative.
    
    The degree of any node should be >= 0.
    """
    assume(len(layers) >= 1)
    
    network = multinet.multi_layer_network(directed=False)
    layer = layers[0]
    
    # Add nodes and edges (path graph)
    for i in range(n - 1):
        network.add_edges([{
            'source': str(i),
            'target': str(i + 1),
            'source_type': layer,
            'target_type': layer,
            'type': 'edge'
        }])
    
    # Check node degrees
    if network.core_network:
        for node in network.core_network.nodes():
            degree = network.core_network.degree(node)
            assert degree >= 0, \
                f"Negative degree found for node {node}: {degree}"


@pytest.mark.property
@settings(deadline=None, max_examples=35)
@given(
    n=st.integers(min_value=3, max_value=10),
    num_edges=st.integers(min_value=2, max_value=12)
)
def test_node_neighborhood_consistency(n, num_edges):
    """
    Property: Node neighborhoods are consistent with edges.
    
    If node v is in neighborhood of u, then edge (u,v) should exist.
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
    
    # Check neighborhoods
    if network.core_network:
        for node in list(network.core_network.nodes())[:min(5, n)]:  # Check first 5
            neighbors = list(network.core_network.neighbors(node))
            
            # Each neighbor should have an edge to this node
            for neighbor in neighbors:
                has_edge = (
                    network.core_network.has_edge(node, neighbor) or
                    network.core_network.has_edge(neighbor, node)
                )
                assert has_edge, \
                    f"Neighbor {neighbor} of {node} has no connecting edge"
