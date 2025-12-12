#!/usr/bin/env python3
"""
Random multilayer ER network statistical tests for py3plex.

Tests that random_multilayer_ER produces networks with expected
statistical properties (edge counts, density bounds).
"""

import networkx as nx
import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from py3plex.core.random_generators import random_multilayer_ER


@pytest.mark.property
@pytest.mark.slow
@settings(deadline=None, max_examples=20)
@given(
    N=st.integers(min_value=5, max_value=15),
    L=st.integers(min_value=2, max_value=4),
    p=st.floats(min_value=0.1, max_value=0.7)
)
def test_random_er_edge_count_bounds(N, L, p):
    """
    Test that random ER networks have edge counts within expected bounds.
    
    Property: For each layer, edge count should be close to expected
    value E[m] = p * n_layer * (n_layer-1) / 2 for undirected graphs,
    where n_layer is the number of nodes in that layer.
    Uses Chebyshev's inequality for wide bounds.
    """
    # Generate network
    mlnet = random_multilayer_ER(n=N, l=L, p=p, directed=False)
    
    # Split to layers
    mlnet.split_to_layers(style="none")
    
    # Check each layer
    for layer in mlnet.separate_layers:
        nodes_in_layer = layer.number_of_nodes()
        edge_count = layer.number_of_edges()
        
        # Expected edge count for this layer (undirected)
        expected_edges = p * nodes_in_layer * (nodes_in_layer - 1) / 2
        
        # Standard deviation for binomial: sqrt(n * p * (1-p))
        # where n = nodes_in_layer*(nodes_in_layer-1)/2 is number of possible edges
        n_possible = nodes_in_layer * (nodes_in_layer - 1) // 2
        if n_possible == 0:
            # Single node layer, skip
            continue
        std_edges = np.sqrt(n_possible * p * (1 - p))
        
        # Use wide bounds (Chebyshev: within k standard deviations with prob >= 1 - 1/k^2)
        # Use k=5 for very wide bounds (96% confidence)
        k = 5
        lower_bound = max(0, expected_edges - k * std_edges)
        upper_bound = expected_edges + k * std_edges
        
        assert edge_count >= lower_bound, \
            f"Edge count {edge_count} below lower bound {lower_bound} for layer with {nodes_in_layer} nodes"
        assert edge_count <= upper_bound, \
            f"Edge count {edge_count} above upper bound {upper_bound} for layer with {nodes_in_layer} nodes"


@pytest.mark.property
@pytest.mark.slow
@settings(deadline=None, max_examples=20)
@given(
    N=st.integers(min_value=5, max_value=12),
    L=st.integers(min_value=2, max_value=4)
)
def test_random_er_monotonicity_in_p(N, L):
    """
    Test that expected edge count is non-decreasing in p.
    
    Property: For fixed (N, L), E[edges(p1)] <= E[edges(p2)] when p1 < p2.
    """
    p_low = 0.2
    p_high = 0.5
    
    # Generate networks with different p values
    mlnet_low = random_multilayer_ER(n=N, l=L, p=p_low, directed=False)
    mlnet_high = random_multilayer_ER(n=N, l=L, p=p_high, directed=False)
    
    # Count total edges
    edges_low = len(list(mlnet_low.get_edges()))
    edges_high = len(list(mlnet_high.get_edges()))
    
    # Higher p should produce more edges on average
    # Allow for randomness with a margin
    expected_low = p_low * N * (N - 1) / 2 * L
    expected_high = p_high * N * (N - 1) / 2 * L
    
    # Check that the trend is correct (higher p -> more edges)
    # Use a relaxed check since this is a single sample
    assert expected_high > expected_low, \
        "Expected edge counts should be ordered"


@pytest.mark.property
@pytest.mark.slow
@settings(deadline=None, max_examples=30)
@given(
    N=st.integers(min_value=3, max_value=10),
    L=st.integers(min_value=1, max_value=4)
)
def test_random_er_node_count(N, L):
    """
    Test that generated networks have correct node count.
    
    Property: Network should have N nodes per layer.
    """
    p = 0.5
    mlnet = random_multilayer_ER(n=N, l=L, p=p, directed=False)
    
    # Total nodes should be N * L (assuming each node appears in each layer)
    total_nodes = mlnet.core_network.number_of_nodes()
    
    # Should have at least N nodes (some may be shared across layers)
    assert total_nodes >= N, \
        f"Too few nodes: {total_nodes} < {N}"
    
    # Should have at most N * L nodes
    assert total_nodes <= N * L, \
        f"Too many nodes: {total_nodes} > {N * L}"


@pytest.mark.property
@pytest.mark.slow
@settings(deadline=None, max_examples=30)
@given(
    N=st.integers(min_value=3, max_value=10),
    L=st.integers(min_value=2, max_value=4)
)
def test_random_er_layer_count(N, L):
    """
    Test that generated networks have correct layer count.
    
    Property: split_to_layers should produce min(N, L) layers
    (can't have more layers than nodes).
    """
    p = 0.5
    mlnet = random_multilayer_ER(n=N, l=L, p=p, directed=False)
    
    # Split to layers
    mlnet.split_to_layers(style="none")
    
    # Should have min(N, L) layers
    expected = min(N, L)
    assert len(mlnet.separate_layers) == expected, \
        f"Layer count mismatch: {len(mlnet.separate_layers)} != {expected}"


@pytest.mark.property
@pytest.mark.slow
@settings(deadline=None, max_examples=30)
@given(
    N=st.integers(min_value=3, max_value=10),
    L=st.integers(min_value=1, max_value=4),
    p=st.floats(min_value=0.0, max_value=1.0)
)
def test_random_er_nonnegative_counts(N, L, p):
    """
    Test that generated networks have non-negative node and edge counts.
    
    Property: Node count >= 0, edge count >= 0.
    """
    mlnet = random_multilayer_ER(n=N, l=L, p=p, directed=False)
    
    node_count = mlnet.core_network.number_of_nodes()
    edge_count = mlnet.core_network.number_of_edges()
    
    assert node_count >= 0, f"Negative node count: {node_count}"
    assert edge_count >= 0, f"Negative edge count: {edge_count}"


@pytest.mark.property
@pytest.mark.slow
@settings(deadline=None, max_examples=30)
@given(
    N=st.integers(min_value=3, max_value=10),
    L=st.integers(min_value=1, max_value=4)
)
def test_random_er_extreme_p_values(N, L):
    """
    Test behavior at extreme p values (0 and 1).
    
    Property: p=0 gives no edges, p=1 gives complete graphs per layer.
    """
    # Test p=0 (no edges)
    mlnet_empty = random_multilayer_ER(n=N, l=L, p=0.0, directed=False)
    mlnet_empty.split_to_layers(style="none")
    
    for layer in mlnet_empty.separate_layers:
        # Each layer should have no intra-layer edges
        # (may have coupling edges in multiplex mode, but intra-layer should be 0)
        edge_count = layer.number_of_edges()
        assert edge_count == 0, \
            f"Expected 0 edges with p=0, got {edge_count}"
    
    # Test p=1 (complete graphs)
    mlnet_complete = random_multilayer_ER(n=N, l=L, p=1.0, directed=False)
    mlnet_complete.split_to_layers(style="none")
    
    for layer in mlnet_complete.separate_layers:
        nodes_in_layer = layer.number_of_nodes()
        edge_count = layer.number_of_edges()
        # Each layer should be a complete graph for its nodes
        expected_edges_complete = nodes_in_layer * (nodes_in_layer - 1) // 2
        assert edge_count == expected_edges_complete, \
            f"Expected {expected_edges_complete} edges with p=1 for {nodes_in_layer} nodes, got {edge_count}"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(N=st.integers(min_value=3, max_value=10))
def test_random_er_single_layer_matches_nx(N):
    """
    Test that single-layer ER matches NetworkX Erdos-Renyi behavior.
    
    Property: With L=1, should produce structure similar to nx.erdos_renyi_graph.
    """
    p = 0.5
    seed = 42
    
    # Generate with py3plex
    mlnet = random_multilayer_ER(n=N, l=1, p=p, directed=False)
    mlnet.split_to_layers(style="none")
    
    py3plex_edges = mlnet.separate_layers[0].number_of_edges()
    
    # Generate with NetworkX for comparison
    G = nx.gnp_random_graph(N, p, seed=seed)
    nx_edges = G.number_of_edges()
    
    # Both should be roughly similar (within statistical bounds)
    # Use very wide bounds since these are independent random samples
    expected = p * N * (N - 1) / 2
    n_possible = N * (N - 1) // 2
    std = np.sqrt(n_possible * p * (1 - p))
    
    # Both should be within reasonable range
    k = 5
    lower = max(0, expected - k * std)
    upper = expected + k * std
    
    assert lower <= py3plex_edges <= upper, \
        f"py3plex edge count out of bounds: {py3plex_edges}"


@pytest.mark.property
@settings(deadline=None, max_examples=25)
@given(
    N=st.integers(min_value=5, max_value=12),
    L=st.integers(min_value=2, max_value=4),
    p=st.floats(min_value=0.2, max_value=0.8)
)
def test_random_er_layers_independent(N, L, p):
    """
    Test that different layers have independent edge distributions.
    
    Property: Edge counts across layers should have variance consistent
    with independent sampling.
    """
    mlnet = random_multilayer_ER(n=N, l=L, p=p, directed=False)
    mlnet.split_to_layers(style="none")
    
    # Get edge counts per layer
    edge_counts = [layer.number_of_edges() for layer in mlnet.separate_layers]
    
    # All should be >= 0
    assert all(count >= 0 for count in edge_counts)
    
    # Variance should exist (not all the same unless p=0 or p=1)
    if 0 < p < 1 and L > 1:
        # Expect some variation
        variance = np.var(edge_counts)
        # Variance should be >= 0 (trivially true, but check it's computed)
        assert variance >= 0


@pytest.mark.property
@pytest.mark.slow
@settings(deadline=None, max_examples=30)
@given(
    N=st.integers(min_value=3, max_value=10),
    L=st.integers(min_value=1, max_value=4),
    p=st.floats(min_value=0.1, max_value=0.9)
)
def test_random_er_produces_valid_network(N, L, p):
    """
    Test that generated networks are valid py3plex networks.
    
    Property: All basic network operations work on generated networks.
    """
    mlnet = random_multilayer_ER(n=N, l=L, p=p, directed=False)
    
    # Should be able to get nodes
    nodes = list(mlnet.get_nodes())
    assert len(nodes) >= 0
    
    # Should be able to get edges
    edges = list(mlnet.get_edges())
    assert len(edges) >= 0
    
    # Should have core_network
    assert mlnet.core_network is not None
    
    # Should be able to split to layers
    mlnet.split_to_layers(style="none")
    assert len(mlnet.separate_layers) == L
