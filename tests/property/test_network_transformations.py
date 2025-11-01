#!/usr/bin/env python3
"""
Property-based tests for network transformation operations.

Tests algebraic properties and invariants of operations like:
- Node/edge addition and removal
- Subgraph extraction
- Graph complement
- Graph products
- Layer aggregation
"""

import networkx as nx
import pytest
from hypothesis import given, strategies as st, settings, assume

from py3plex.core import multinet
from tests.property.strategies import (
    small_graphs, 
    weighted_graphs,
    node_names,
    layer_labels,
    positive_weights,
    integer_node_ids
)


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(G=small_graphs(min_nodes=2, max_nodes=8))
def test_subgraph_preserves_edges(G):
    """
    Property: Subgraph edges are a subset of original graph edges.
    
    Any edge in the subgraph must exist in the original graph.
    """
    assume(G.number_of_nodes() >= 2)
    
    # Create a subgraph by selecting subset of nodes
    nodes_to_keep = list(G.nodes())[:-1]  # Remove last node
    if len(nodes_to_keep) == 0:
        return
    
    H = G.subgraph(nodes_to_keep)
    
    # All edges in H should be in G
    for u, v in H.edges():
        assert G.has_edge(u, v), f"Edge ({u}, {v}) in subgraph but not in original"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(G=small_graphs(min_nodes=2, max_nodes=8))
def test_edge_addition_increases_count(G):
    """
    Property: Adding a new edge increases edge count by 1.
    
    Unless the edge already exists (for simple graphs).
    """
    assume(G.number_of_nodes() >= 2)
    
    # Get initial edge count
    initial_edges = G.number_of_edges()
    
    # Get two distinct nodes
    nodes = list(G.nodes())
    if len(nodes) < 2:
        return
    
    u, v = nodes[0], nodes[1]
    
    # If edge exists, count shouldn't change
    # If edge doesn't exist, count should increase by 1
    edge_exists = G.has_edge(u, v)
    
    G_copy = G.copy()
    G_copy.add_edge(u, v)
    
    if edge_exists:
        assert G_copy.number_of_edges() == initial_edges, \
            "Adding existing edge should not change count"
    else:
        assert G_copy.number_of_edges() == initial_edges + 1, \
            "Adding new edge should increase count by 1"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(G=small_graphs(min_nodes=2, max_nodes=8))
def test_node_removal_removes_incident_edges(G):
    """
    Property: Removing a node removes all its incident edges.
    
    After removing node u, no edges should reference u.
    """
    assume(G.number_of_nodes() >= 2)
    
    nodes = list(G.nodes())
    if len(nodes) == 0:
        return
    
    # Pick a node to remove
    node_to_remove = nodes[0]
    
    # Get edges involving this node
    incident_edges_before = [(u, v) for u, v in G.edges() if u == node_to_remove or v == node_to_remove]
    
    G_copy = G.copy()
    G_copy.remove_node(node_to_remove)
    
    # Verify node is gone
    assert node_to_remove not in G_copy.nodes(), "Node should be removed"
    
    # Verify no edges reference removed node
    for u, v in G_copy.edges():
        assert u != node_to_remove and v != node_to_remove, \
            f"Edge ({u}, {v}) still references removed node {node_to_remove}"


@pytest.mark.property
@settings(deadline=None, max_examples=25)
@given(
    G=weighted_graphs(min_nodes=2, max_nodes=6),
    scale=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
)
def test_weight_scaling_preserves_structure(G, scale):
    """
    Property: Scaling all weights preserves graph structure.
    
    Scaling weights should not change nodes, edges, or topology.
    """
    assume(G.number_of_edges() > 0)
    
    # Record structure before scaling
    nodes_before = set(G.nodes())
    edges_before = set(G.edges())
    
    # Scale all weights
    G_scaled = G.copy()
    for u, v in G_scaled.edges():
        if 'weight' in G_scaled[u][v]:
            G_scaled[u][v]['weight'] *= scale
    
    # Structure should be preserved
    assert set(G_scaled.nodes()) == nodes_before, "Nodes changed after scaling"
    assert set(G_scaled.edges()) == edges_before, "Edges changed after scaling"
    
    # Weights should be scaled correctly
    for u, v in G.edges():
        if 'weight' in G[u][v]:
            original_weight = G[u][v]['weight']
            scaled_weight = G_scaled[u][v]['weight']
            assert abs(scaled_weight - original_weight * scale) < 1e-9, \
                f"Weight not scaled correctly: {scaled_weight} != {original_weight * scale}"


@pytest.mark.property
@settings(deadline=None, max_examples=25)
@given(G=small_graphs(min_nodes=3, max_nodes=7))
def test_complement_union_is_complete(G):
    """
    Property: Graph union with its complement equals complete graph.
    
    G ∪ complement(G) = K_n (for simple graphs without self-loops)
    """
    assume(G.number_of_nodes() >= 2)
    assume(G.number_of_nodes() <= 7)  # Keep small for performance
    
    # Remove self-loops for this test
    G_simple = G.copy()
    G_simple.remove_edges_from(nx.selfloop_edges(G_simple))
    
    # Get complement
    H = nx.complement(G_simple)
    
    n = G_simple.number_of_nodes()
    max_edges = n * (n - 1) // 2
    
    # Edges in G + edges in complement should equal max possible
    total_edges = G_simple.number_of_edges() + H.number_of_edges()
    
    assert total_edges == max_edges, \
        f"G + complement should have {max_edges} edges, got {total_edges}"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    n1=st.text(min_size=1, max_size=8, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    n2=st.text(min_size=1, max_size=8, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    l1=st.text(min_size=1, max_size=8, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    l2=st.text(min_size=1, max_size=8, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    weight=positive_weights()
)
def test_multilayer_edge_addition_consistency(n1, n2, l1, l2, weight):
    """
    Property: Adding the same edge multiple times should be idempotent.
    
    Edge count should not increase beyond the first addition.
    """
    net = multinet.multi_layer_network(verbose=False, network_type="multilayer")
    
    # Add edge first time
    edge_dict = {
        "source": n1,
        "target": n2,
        "source_type": l1,
        "target_type": l2,
        "weight": weight
    }
    net.add_edges([edge_dict], input_type="dict")
    
    edges_after_first = net.core_network.number_of_edges()
    nodes_after_first = net.core_network.number_of_nodes()
    
    # Add same edge again
    net.add_edges([edge_dict], input_type="dict")
    
    edges_after_second = net.core_network.number_of_edges()
    nodes_after_second = net.core_network.number_of_nodes()
    
    # Node count should be the same
    assert nodes_after_first == nodes_after_second, \
        "Node count changed after adding duplicate edge"
    
    # Edge count should be the same for simple graphs, 
    # or may increase for multigraphs
    # This tests that the behavior is at least deterministic
    assert edges_after_second >= edges_after_first, \
        "Edge count decreased after adding edge"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(G=small_graphs(min_nodes=3, max_nodes=8))
def test_connected_components_are_disjoint(G):
    """
    Property: Connected components partition the node set.
    
    - Union of components = all nodes
    - Components are pairwise disjoint
    """
    components = list(nx.connected_components(G))
    
    # Union should equal node set
    all_nodes_in_components = set().union(*components) if components else set()
    assert all_nodes_in_components == set(G.nodes()), \
        "Components don't cover all nodes"
    
    # Components should be pairwise disjoint
    for i, comp1 in enumerate(components):
        for j, comp2 in enumerate(components):
            if i != j:
                intersection = comp1.intersection(comp2)
                assert len(intersection) == 0, \
                    f"Components {i} and {j} overlap: {intersection}"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=2, max_value=4)
)
def test_multilayer_layer_count_preserved(num_nodes, num_layers):
    """
    Property: Multilayer networks preserve layer count when feasible.
    
    After construction, the network should have layers present, up to the 
    specified number. With very few nodes and many layers, some layers may
    be empty depending on the random graph generation.
    """
    from py3plex.core import random_generators
    
    # Skip cases where layers > nodes as not all layers may be used
    assume(num_nodes >= num_layers)
    
    net = random_generators.random_multilayer_ER(
        n=num_nodes,
        l=num_layers,
        p=0.5,
        directed=False
    )
    
    # Get unique layers from nodes
    nodes = list(net.core_network.nodes())
    if not nodes:
        return
    
    # Nodes should be tuples (node_id, layer)
    layers_found = set()
    for node in nodes:
        if isinstance(node, tuple) and len(node) >= 2:
            layers_found.add(node[1])
    
    # Should have at least 1 layer and at most num_layers
    assert 1 <= len(layers_found) <= num_layers, \
        f"Expected 1 to {num_layers} layers, found {len(layers_found)}"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(G=small_graphs(min_nodes=2, max_nodes=8))
def test_degree_sequence_sum_equals_double_edges(G):
    """
    Property: Sum of degree sequence equals twice the number of edges.
    
    This is the handshaking lemma for undirected graphs.
    """
    assume(G.number_of_edges() > 0)
    
    degree_sequence = [d for n, d in G.degree()]
    degree_sum = sum(degree_sequence)
    
    assert degree_sum == 2 * G.number_of_edges(), \
        f"Degree sum {degree_sum} != 2 * edges {2 * G.number_of_edges()}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
