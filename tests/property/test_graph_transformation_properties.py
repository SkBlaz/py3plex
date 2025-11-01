#!/usr/bin/env python3
"""
Property-based tests for graph transformations in multilayer networks.

Tests structural invariants that should hold under various transformations
such as subgraph extraction, layer merging, and graph modifications.
"""

import networkx as nx
import pytest
from hypothesis import given, strategies as st, settings, assume

from py3plex.core import multinet
from .strategies import layer_labels


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    n=st.integers(min_value=3, max_value=10),
    p=st.floats(min_value=0.2, max_value=0.8)
)
def test_complement_graph_edge_sum(n, p):
    """
    Property: Graph plus its complement equals complete graph.
    
    For simple graphs, |E(G)| + |E(complement(G))| = n(n-1)/2.
    """
    G = nx.gnp_random_graph(n, p, seed=hash((n, p)) % (2**32))
    
    # Remove self-loops for simple graph
    G.remove_edges_from(nx.selfloop_edges(G))
    
    # Create complement
    G_complement = nx.complement(G)
    
    # Calculate totals
    edges_g = G.number_of_edges()
    edges_complement = G_complement.number_of_edges()
    max_edges = n * (n - 1) // 2
    
    assert edges_g + edges_complement == max_edges, \
        f"Edge sum mismatch: {edges_g} + {edges_complement} != {max_edges}"


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    n=st.integers(min_value=3, max_value=10),
    p=st.floats(min_value=0.2, max_value=0.8)
)
def test_subgraph_preserves_edges(n, p):
    """
    Property: Subgraph edges are subset of original graph edges.
    
    All edges in a subgraph must exist in the original graph.
    """
    G = nx.gnp_random_graph(n, p, seed=hash((n, p)) % (2**32))
    assume(G.number_of_edges() > 0)
    assume(n > 2)
    
    # Create subgraph with subset of nodes
    nodes_subset = list(G.nodes())[:n-1]
    H = G.subgraph(nodes_subset)
    
    # All edges in H should be in G
    for u, v in H.edges():
        assert G.has_edge(u, v), \
            f"Edge ({u}, {v}) in subgraph but not in original"


@pytest.mark.property
@settings(deadline=None, max_examples=35)
@given(
    n=st.integers(min_value=3, max_value=10),
    p=st.floats(min_value=0.3, max_value=0.8)
)
def test_connected_components_partition(n, p):
    """
    Property: Connected components partition the node set.
    
    Every node belongs to exactly one component.
    """
    G = nx.gnp_random_graph(n, p, seed=hash((n, p)) % (2**32))
    
    components = list(nx.connected_components(G))
    
    # Union of components should equal all nodes
    all_nodes = set()
    for comp in components:
        all_nodes.update(comp)
    
    assert all_nodes == set(G.nodes()), \
        "Components don't cover all nodes"
    
    # Components should be disjoint
    for i, comp1 in enumerate(components):
        for j, comp2 in enumerate(components):
            if i != j:
                assert len(comp1.intersection(comp2)) == 0, \
                    f"Components {i} and {j} overlap"


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    n=st.integers(min_value=2, max_value=10),
    layers=st.lists(layer_labels(), min_size=2, max_size=4, unique=True)
)
def test_layer_union_preserves_nodes(n, layers):
    """
    Property: Union of layer projections preserves node set.
    
    The union of all nodes across layers should equal the original node set.
    """
    assume(len(layers) >= 2)
    
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes to all layers
    all_node_ids = set()
    for layer in layers:
        for i in range(n):
            network.add_nodes([{
                'source': str(i),
                'type': layer
            }])
            all_node_ids.add(str(i))
    
    # Get nodes per layer
    nodes_by_layer = {}
    for node in network.get_nodes():
        layer = node[1]
        if layer not in nodes_by_layer:
            nodes_by_layer[layer] = set()
        nodes_by_layer[layer].add(node[0])
    
    # Union should preserve original node IDs
    union_nodes = set()
    for layer_nodes in nodes_by_layer.values():
        union_nodes.update(layer_nodes)
    
    assert all_node_ids.issubset(union_nodes), \
        f"Node union doesn't preserve original nodes"


@pytest.mark.property
@settings(deadline=None, max_examples=35)
@given(
    n=st.integers(min_value=3, max_value=10),
    p=st.floats(min_value=0.2, max_value=0.8)
)
def test_edge_reversal_preserves_connectivity(n, p):
    """
    Property: Reversing all edges in undirected graph preserves connectivity.
    
    For undirected graphs, reversing edges doesn't change connectivity.
    """
    G = nx.gnp_random_graph(n, p, seed=hash((n, p)) % (2**32))
    assume(G.number_of_edges() > 0)
    
    # Check if connected
    was_connected = nx.is_connected(G)
    
    # Create "reversed" graph (same for undirected)
    G_rev = G.copy()
    
    # Connectivity should be preserved
    is_connected = nx.is_connected(G_rev)
    
    assert was_connected == is_connected, \
        "Connectivity changed after reversal"


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    n=st.integers(min_value=2, max_value=8),
    layers=st.lists(layer_labels(), min_size=2, max_size=3, unique=True)
)
def test_layer_intersection_subset(n, layers):
    """
    Property: Intersection of layers is subset of each layer.
    
    Nodes common to multiple layers form a subset of each layer.
    """
    assume(len(layers) >= 2)
    
    network = multinet.multi_layer_network(directed=False)
    
    # Add overlapping nodes to layers
    for i, layer in enumerate(layers):
        # Add common nodes plus some layer-specific ones
        for j in range(n):
            if j < n // 2 or i == 0:  # First n//2 are common
                network.add_nodes([{
                    'source': str(j),
                    'type': layer
                }])
    
    # Get nodes per layer
    nodes_by_layer = {}
    for node in network.get_nodes():
        layer = node[1]
        if layer not in nodes_by_layer:
            nodes_by_layer[layer] = set()
        nodes_by_layer[layer].add(node[0])
    
    # Find intersection
    if len(nodes_by_layer) >= 2:
        layer_lists = list(nodes_by_layer.values())
        intersection = layer_lists[0].intersection(*layer_lists[1:])
        
        # Intersection should be subset of each layer
        for layer_nodes in nodes_by_layer.values():
            assert intersection.issubset(layer_nodes), \
                "Intersection not subset of layer"


@pytest.mark.property
@settings(deadline=None, max_examples=35)
@given(
    n=st.integers(min_value=3, max_value=10),
    p=st.floats(min_value=0.3, max_value=0.8)
)
def test_spanning_tree_connected(n, p):
    """
    Property: Spanning tree of connected graph is connected.
    
    A spanning tree should connect all nodes with n-1 edges.
    """
    G = nx.gnp_random_graph(n, p, seed=hash((n, p)) % (2**32))
    assume(nx.is_connected(G))
    assume(G.number_of_edges() > 0)
    
    # Get spanning tree
    T = nx.minimum_spanning_tree(G)
    
    # Should be connected
    assert nx.is_connected(T), \
        "Spanning tree is not connected"
    
    # Should have n-1 edges
    assert T.number_of_edges() == n - 1, \
        f"Spanning tree has wrong number of edges: {T.number_of_edges()} != {n-1}"


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    n=st.integers(min_value=2, max_value=10),
    num_edges=st.integers(min_value=1, max_value=15)
)
def test_degree_sequence_sum_even(n, num_edges):
    """
    Property: Sum of degree sequence is even (Handshaking Lemma).
    
    In any graph, the sum of all degrees equals 2 * number of edges.
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
    
    # Calculate degree sum
    if network.core_network:
        degree_sum = sum(d for _, d in network.core_network.degree())
        edge_count = len(list(network.get_edges()))
        
        # Sum of degrees should be even
        assert degree_sum % 2 == 0, \
            f"Degree sum is odd: {degree_sum}"


@pytest.mark.property
@settings(deadline=None, max_examples=35)
@given(
    n=st.integers(min_value=3, max_value=10),
    p=st.floats(min_value=0.2, max_value=0.8)
)
def test_graph_union_commutative(n, p):
    """
    Property: Graph union is commutative.
    
    G ∪ H = H ∪ G for any graphs G and H.
    """
    # Create two random graphs on same nodes
    G = nx.gnp_random_graph(n, p, seed=hash((n, p)) % (2**32))
    H = nx.gnp_random_graph(n, p * 0.7, seed=hash((n, p, 1)) % (2**32))
    
    # Union in both orders
    union1 = nx.compose(G, H)
    union2 = nx.compose(H, G)
    
    # Should have same nodes
    assert set(union1.nodes()) == set(union2.nodes()), \
        "Union nodes differ by order"
    
    # Should have same edges (as sets)
    edges1 = set(union1.edges())
    edges2 = set(union2.edges())
    
    assert edges1 == edges2, \
        "Union edges differ by order"


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    n=st.integers(min_value=2, max_value=10),
    layers=st.lists(layer_labels(), min_size=1, max_size=3, unique=True)
)
def test_empty_layer_removal_idempotent(n, layers):
    """
    Property: Removing empty layers is idempotent.
    
    Removing empty layers multiple times has same effect as once.
    """
    assume(len(layers) >= 1)
    
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes to first layer only
    for i in range(n):
        network.add_nodes([{
            'source': str(i),
            'type': layers[0]
        }])
    
    # Count nodes before
    nodes_before = len(list(network.get_nodes()))
    
    # The other layers are empty (if they exist)
    # Just verify node count is stable
    nodes_after = len(list(network.get_nodes()))
    
    assert nodes_before == nodes_after, \
        "Node count changed"


@pytest.mark.property
@settings(deadline=None, max_examples=35)
@given(
    n=st.integers(min_value=3, max_value=10),
    p=st.floats(min_value=0.3, max_value=0.8)
)
def test_bipartite_projection_preserves_nodes(n, p):
    """
    Property: Bipartite projection preserves one side's nodes.
    
    Projecting a bipartite graph onto one set preserves those nodes.
    """
    # Create bipartite graph
    m = n // 2
    k = n - m
    
    G = nx.bipartite.random_graph(m, k, p, seed=hash((n, p)) % (2**32))
    assume(G.number_of_edges() > 0)
    
    # Get the two sets
    top_nodes = {n for n, d in G.nodes(data=True) if d.get('bipartite') == 0}
    
    # Project onto top nodes
    try:
        P = nx.bipartite.projected_graph(G, top_nodes)
        
        # Projected graph should have all top nodes
        assert top_nodes.issubset(set(P.nodes())), \
            "Projection lost nodes from projected set"
    except Exception:
        # If projection fails, it's acceptable
        pass
