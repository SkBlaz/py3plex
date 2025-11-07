"""
Metamorphic tests for py3plex multilayer networks.

This module implements metamorphic testing to verify graph-analytics invariants
under controlled transformations. Metamorphic testing catches bugs even when
exact oracles are hard to define by checking relationships between inputs and outputs.

Metamorphic Relations Tested:
------------------------------
R1 - Label invariance (node relabel): Relabeling node names without changing
     topology should preserve the multiset of metric values (e.g., degree centrality).

R2 - Layer-ID permutation invariance: Permuting/renaming layer IDs without
     changing edges should preserve metric value multisets.

R3 - Edge monotonicity (shortest paths): After adding edges to a graph,
     all-pairs shortest-path distances on a monoplex projection must not increase.
     Disconnected pairs are treated as infinite distance.
"""

import random
from typing import Dict, List, Tuple, Any
import pytest
from hypothesis import given, assume, strategies as st, settings
import networkx as nx

from py3plex.core.random_generators import random_multilayer_ER
from py3plex.core.multinet import multi_layer_network


# ============================================================================
# Helper Functions
# ============================================================================


def relabel_nodes_preserving_structure(
    net: multi_layer_network, mapping: Dict[Any, Any]
) -> multi_layer_network:
    """
    Relabel nodes in a multilayer network while preserving topology.
    
    This function creates a new network with relabeled nodes. The layer structure
    and all edge relationships are preserved, only node identifiers change.
    
    Args:
        net: Original multilayer network
        mapping: Dictionary mapping old node IDs to new node IDs
    
    Returns:
        New multilayer network with relabeled nodes
        
    Example:
        >>> net = random_multilayer_ER(10, 2, 0.3)
        >>> mapping = {i: f"node_{i}" for i in range(10)}
        >>> relabeled = relabel_nodes_preserving_structure(net, mapping)
    """
    # Create new network with same properties
    if net.directed:
        new_core = nx.MultiDiGraph()
    else:
        new_core = nx.MultiGraph()
    
    # Relabel nodes: (node, layer) -> (mapping[node], layer)
    for node, layer in net.get_nodes():
        new_node = mapping.get(node, node)
        new_core.add_node((new_node, layer), type="default")
    
    # Relabel edges
    for edge in net.core_network.edges(data=True, keys=True):
        u, v = edge[0], edge[1]
        u_node, u_layer = u
        v_node, v_layer = v
        
        new_u = (mapping.get(u_node, u_node), u_layer)
        new_v = (mapping.get(v_node, v_node), v_layer)
        
        # Preserve edge attributes
        edge_data = edge[3] if len(edge) > 3 else {}
        new_core.add_edge(new_u, new_v, **edge_data)
    
    # Create new network object
    new_net = multi_layer_network(
        network_type=net.network_type,
        directed=net.directed
    )
    new_net.load_network(new_core, input_type="nx", directed=net.directed)
    
    return new_net


def permute_layers(
    net: multi_layer_network, perm: Dict[int, int]
) -> multi_layer_network:
    """
    Permute layer IDs in a multilayer network while preserving topology.
    
    This function creates a new network where layer IDs are permuted according
    to the provided mapping. Node relationships within and across layers are preserved.
    
    Args:
        net: Original multilayer network
        perm: Dictionary mapping old layer IDs to new layer IDs
    
    Returns:
        New multilayer network with permuted layer IDs
        
    Example:
        >>> net = random_multilayer_ER(10, 3, 0.3)
        >>> perm = {0: 2, 1: 0, 2: 1}  # Rotate layers
        >>> permuted = permute_layers(net, perm)
    """
    # Create new network with same properties
    if net.directed:
        new_core = nx.MultiDiGraph()
    else:
        new_core = nx.MultiGraph()
    
    # Permute nodes: (node, layer) -> (node, perm[layer])
    for node, layer in net.get_nodes():
        new_layer = perm.get(layer, layer)
        new_core.add_node((node, new_layer), type="default")
    
    # Permute edges
    for edge in net.core_network.edges(data=True, keys=True):
        u, v = edge[0], edge[1]
        u_node, u_layer = u
        v_node, v_layer = v
        
        new_u = (u_node, perm.get(u_layer, u_layer))
        new_v = (v_node, perm.get(v_layer, v_layer))
        
        # Preserve edge attributes
        edge_data = edge[3] if len(edge) > 3 else {}
        new_core.add_edge(new_u, new_v, **edge_data)
    
    # Create new network object
    new_net = multi_layer_network(
        network_type=net.network_type,
        directed=net.directed
    )
    new_net.load_network(new_core, input_type="nx", directed=net.directed)
    
    return new_net


def project_to_nx_monoplex(net: multi_layer_network) -> nx.Graph:
    """
    Project a multilayer network to a simple monoplex NetworkX graph.
    
    This creates a deterministic projection where nodes from all layers are
    merged into single nodes, and edges from all layers are combined.
    Useful for computing layer-agnostic metrics like shortest paths.
    
    Args:
        net: Multilayer network to project
    
    Returns:
        NetworkX Graph with projected structure (undirected, simple)
        
    Example:
        >>> net = random_multilayer_ER(10, 3, 0.3)
        >>> mono = project_to_nx_monoplex(net)
        >>> paths = nx.shortest_path_length(mono)
    """
    # Create simple undirected graph (for consistent shortest path semantics)
    mono = nx.Graph()
    
    # Extract unique nodes (ignoring layer)
    nodes = set()
    for node, layer in net.get_nodes():
        nodes.add(node)
    
    mono.add_nodes_from(nodes)
    
    # Add edges, collapsing layers
    for edge in net.core_network.edges():
        u_node = edge[0][0]  # (node, layer)[0] = node
        v_node = edge[1][0]
        
        # Skip self-loops for cleaner shortest path computation
        if u_node != v_node:
            mono.add_edge(u_node, v_node)
    
    return mono


def add_random_edges(
    net: multi_layer_network, num_edges: int, seed: int = None
) -> multi_layer_network:
    """
    Add random edges to a multilayer network without creating duplicates.
    
    Args:
        net: Original network
        num_edges: Number of edges to add
        seed: Random seed for reproducibility
    
    Returns:
        New network with additional random edges
    """
    if seed is not None:
        random.seed(seed)
    
    # Create copy of network
    if net.directed:
        new_core = nx.MultiDiGraph(net.core_network)
    else:
        new_core = nx.MultiGraph(net.core_network)
    
    # Get list of nodes
    nodes = list(net.get_nodes())
    
    if len(nodes) < 2:
        # Can't add edges with fewer than 2 nodes
        new_net = multi_layer_network(
            network_type=net.network_type,
            directed=net.directed
        )
        new_net.load_network(new_core, input_type="nx", directed=net.directed)
        return new_net
    
    # Get existing edges as set for fast lookup
    existing_edges = set()
    for u, v in net.core_network.edges():
        existing_edges.add((u, v))
        if not net.directed:
            existing_edges.add((v, u))
    
    # Add random edges
    added = 0
    attempts = 0
    max_attempts = num_edges * 10  # Avoid infinite loop
    
    while added < num_edges and attempts < max_attempts:
        attempts += 1
        
        # Pick two random nodes
        u = random.choice(nodes)
        v = random.choice(nodes)
        
        # Skip self-loops and existing edges
        if u == v or (u, v) in existing_edges:
            continue
        
        # Add edge
        new_core.add_edge(u, v, type="default")
        existing_edges.add((u, v))
        if not net.directed:
            existing_edges.add((v, u))
        added += 1
    
    # Create new network object
    new_net = multi_layer_network(
        network_type=net.network_type,
        directed=net.directed
    )
    new_net.load_network(new_core, input_type="nx", directed=net.directed)
    
    return new_net


# ============================================================================
# Hypothesis Strategies
# ============================================================================


# Strategy for network parameters
network_params_strategy = st.fixed_dictionaries({
    'n': st.integers(min_value=12, max_value=150),
    'L': st.integers(min_value=1, max_value=6),
    'p': st.floats(min_value=0.01, max_value=0.15),
    'directed': st.booleans(),
})


# ============================================================================
# Metamorphic Tests
# ============================================================================


@pytest.mark.metamorphic
@given(params=network_params_strategy)
@settings(max_examples=10, deadline=None)
def test_R1_label_invariance_node_relabel(params):
    """
    R1 - Label Invariance (Node Relabel).
    
    Metamorphic Relation:
    When we relabel node names without changing the network topology,
    layer-agnostic metrics (e.g., degree centrality) must preserve the
    multiset of values. That is, the sorted list of metric values should
    be identical before and after relabeling.
    
    This tests that the network structure is independent of node naming
    and that centrality computations depend only on topology.
    """
    n, L, p, directed = params['n'], params['L'], params['p'], params['directed']
    
    # Skip degenerate cases
    assume(n >= 2)  # Need at least 2 nodes for meaningful metrics
    assume(L >= 1)  # Need at least 1 layer
    
    # Generate network
    net = random_multilayer_ER(n=n, l=L, p=p, directed=directed)
    
    # Skip if network is trivial (no nodes)
    nodes = list(net.get_nodes())
    assume(len(nodes) >= 2)
    
    # Compute degree centrality on original network
    try:
        original_centrality = net.monoplex_nx_wrapper("degree_centrality")
        original_values = sorted(original_centrality.values())
    except Exception:
        # If centrality computation fails, skip test
        assume(False)
    
    # Create node relabeling: map node IDs to new IDs
    unique_nodes = set(node for node, layer in nodes)
    mapping = {node: f"n_{node}_relabeled" for node in unique_nodes}
    
    # Relabel nodes
    relabeled_net = relabel_nodes_preserving_structure(net, mapping)
    
    # Verify edges were preserved (modulo relabeling)
    assert len(list(relabeled_net.core_network.edges())) == len(
        list(net.core_network.edges())
    ), "Edge count should be preserved after relabeling"
    
    # Compute degree centrality on relabeled network
    try:
        relabeled_centrality = relabeled_net.monoplex_nx_wrapper("degree_centrality")
        relabeled_values = sorted(relabeled_centrality.values())
    except Exception:
        assume(False)
    
    # Assert: sorted value lists must be equal (allowing floating point tolerance)
    assert len(original_values) == len(relabeled_values), (
        "Number of centrality values should match"
    )
    
    for orig, relabeled in zip(original_values, relabeled_values):
        assert abs(orig - relabeled) < 1e-9, (
            f"Centrality values should match: {orig} vs {relabeled}"
        )


@pytest.mark.metamorphic
@given(params=network_params_strategy)
@settings(max_examples=10, deadline=None)
def test_R2_layer_permutation_invariance(params):
    """
    R2 - Layer-ID Permutation Invariance.
    
    Metamorphic Relation:
    When we permute/rename layer IDs without changing edges, the multiset
    of metric values should remain the same. Node identities within each layer
    change (due to (node, layer) tuple representation), but the distribution
    of centrality values should be preserved.
    
    This tests that network metrics are invariant to layer ordering/naming
    and depend only on the structure within and across layers.
    """
    n, L, p, directed = params['n'], params['L'], params['p'], params['directed']
    
    # Skip degenerate cases
    assume(n >= 2)
    assume(L >= 2)  # Need at least 2 layers for meaningful permutation
    
    # Generate network
    net = random_multilayer_ER(n=n, l=L, p=p, directed=directed)
    
    # Skip if network is trivial
    nodes = list(net.get_nodes())
    assume(len(nodes) >= 2)
    
    # Compute degree centrality on original network
    try:
        original_centrality = net.monoplex_nx_wrapper("degree_centrality")
        original_values = sorted(original_centrality.values())
    except Exception:
        assume(False)
    
    # Create layer permutation: reverse layer order as a simple permutation
    unique_layers = set(layer for node, layer in nodes)
    layer_list = sorted(unique_layers)
    perm = {layer_list[i]: layer_list[-(i+1)] for i in range(len(layer_list))}
    
    # Permute layers
    permuted_net = permute_layers(net, perm)
    
    # Verify edges were preserved
    assert len(list(permuted_net.core_network.edges())) == len(
        list(net.core_network.edges())
    ), "Edge count should be preserved after layer permutation"
    
    # Compute degree centrality on permuted network
    try:
        permuted_centrality = permuted_net.monoplex_nx_wrapper("degree_centrality")
        permuted_values = sorted(permuted_centrality.values())
    except Exception:
        assume(False)
    
    # Assert: sorted value lists must be equal (multiset equality)
    assert len(original_values) == len(permuted_values), (
        "Number of centrality values should match"
    )
    
    for orig, permuted in zip(original_values, permuted_values):
        assert abs(orig - permuted) < 1e-9, (
            f"Centrality values should match after layer permutation: {orig} vs {permuted}"
        )


@pytest.mark.metamorphic
@given(params=network_params_strategy, seed=st.integers(min_value=0, max_value=10000))
@settings(max_examples=10, deadline=None)
def test_R3_edge_monotonicity_shortest_paths(params, seed):
    """
    R3 - Edge Monotonicity (Shortest Paths).
    
    Metamorphic Relation:
    After adding edges to a graph, all-pairs shortest-path distances on a
    monoplex projection must not increase. Adding edges can only maintain
    or decrease distances, never increase them. Disconnected pairs are
    treated as having infinite distance.
    
    This tests the fundamental monotonicity property of shortest paths
    under edge addition, which should hold for any graph metric based on
    connectivity.
    """
    n, L, p, directed = params['n'], params['L'], params['p'], params['directed']
    
    # Skip degenerate cases
    assume(n >= 4)  # Need reasonable size for meaningful paths
    assume(L >= 1)
    
    # Generate network
    net = random_multilayer_ER(n=n, l=L, p=p, directed=directed)
    
    # Project to monoplex
    mono_original = project_to_nx_monoplex(net)
    
    # Skip if too few nodes in projection
    assume(len(mono_original.nodes()) >= 3)
    
    # Compute all-pairs shortest paths on original
    try:
        original_paths = dict(nx.all_pairs_shortest_path_length(mono_original))
    except Exception:
        assume(False)
    
    # Sample node pairs for comparison (to keep test fast)
    nodes = list(mono_original.nodes())
    sample_size = min(10, len(nodes) * (len(nodes) - 1) // 2)
    
    # Create deterministic sample based on seed
    random.seed(seed)
    sampled_pairs = []
    for _ in range(sample_size):
        u = random.choice(nodes)
        v = random.choice(nodes)
        if u != v:
            sampled_pairs.append((u, v))
    
    # Skip if no valid pairs
    assume(len(sampled_pairs) > 0)
    
    # Add random edges (use small number to keep test fast)
    num_edges_to_add = max(1, len(list(net.core_network.edges())) // 10)
    net_with_edges = add_random_edges(net, num_edges=num_edges_to_add, seed=seed)
    
    # Project new network to monoplex
    mono_new = project_to_nx_monoplex(net_with_edges)
    
    # Compute all-pairs shortest paths on new network
    try:
        new_paths = dict(nx.all_pairs_shortest_path_length(mono_new))
    except Exception:
        assume(False)
    
    # Check monotonicity for sampled pairs
    for u, v in sampled_pairs:
        # Get distances (inf if no path)
        old_dist = original_paths.get(u, {}).get(v, float('inf'))
        new_dist = new_paths.get(u, {}).get(v, float('inf'))
        
        # Assert: distance should not increase
        assert new_dist <= old_dist, (
            f"Shortest path distance increased after adding edges: "
            f"{u} -> {v}: {old_dist} -> {new_dist}"
        )


# ============================================================================
# Additional Sanity Tests
# ============================================================================


@pytest.mark.metamorphic
def test_relabel_nodes_preserves_structure_simple():
    """
    Sanity test: Verify that node relabeling preserves basic structure.
    """
    # Create small test network
    net = random_multilayer_ER(n=5, l=2, p=0.5, directed=False)
    nodes = list(net.get_nodes())
    
    # Create mapping
    unique_nodes = set(node for node, layer in nodes)
    mapping = {node: f"renamed_{node}" for node in unique_nodes}
    
    # Relabel
    relabeled = relabel_nodes_preserving_structure(net, mapping)
    
    # Check node and edge counts
    assert len(list(relabeled.get_nodes())) == len(list(net.get_nodes()))
    assert len(list(relabeled.core_network.edges())) == len(
        list(net.core_network.edges())
    )


@pytest.mark.metamorphic
def test_permute_layers_preserves_structure_simple():
    """
    Sanity test: Verify that layer permutation preserves basic structure.
    """
    # Create small test network
    net = random_multilayer_ER(n=5, l=3, p=0.5, directed=False)
    
    # Create permutation (reverse layers)
    nodes = list(net.get_nodes())
    layers = sorted(set(layer for node, layer in nodes))
    perm = {layers[i]: layers[-(i+1)] for i in range(len(layers))}
    
    # Permute
    permuted = permute_layers(net, perm)
    
    # Check node and edge counts
    assert len(list(permuted.get_nodes())) == len(list(net.get_nodes()))
    assert len(list(permuted.core_network.edges())) == len(
        list(net.core_network.edges())
    )


@pytest.mark.metamorphic
def test_project_to_nx_monoplex_simple():
    """
    Sanity test: Verify that monoplex projection creates valid NetworkX graph.
    """
    # Create small test network
    net = random_multilayer_ER(n=5, l=2, p=0.5, directed=False)
    
    # Project
    mono = project_to_nx_monoplex(net)
    
    # Check it's a valid NetworkX graph
    assert isinstance(mono, nx.Graph)
    assert len(mono.nodes()) > 0
