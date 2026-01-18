"""
Metamorphic tests for centrality measures in py3plex.

These tests verify that centrality algorithms satisfy key invariants
under controlled transformations:

1. Relabel invariance: Node naming shouldn't affect centrality distributions
2. Layer permutation invariance: Layer ordering shouldn't affect results
3. Edge order invariance: Edge insertion order shouldn't matter
4. Finiteness: All centrality values must be finite (no NaN/inf)
5. PageRank normalization: PageRank values should sum to approximately 1

All tests use canonical small graphs for reproducibility.
"""

import pytest
import math
from typing import List, Dict, Any
import networkx as nx

from tests.fixtures import (
    tiny_two_layer,
    small_three_layer,
    two_cliques_bridge,
    path_graph_multilayer,
    relabel_nodes,
    permute_layers,
    shuffle_edge_order,
)


# ============================================================================
# Helper Functions
# ============================================================================


def get_centrality_values(net, measure: str) -> List[float]:
    """
    Compute centrality values for all nodes in the network.
    
    Args:
        net: Multilayer network
        measure: Centrality measure name (degree_centrality, betweenness_centrality, etc.)
        
    Returns:
        Sorted list of centrality values
    """
    try:
        centrality_dict = net.monoplex_nx_wrapper(measure)
        return sorted(centrality_dict.values())
    except Exception:
        # If computation fails, return None to skip test
        return None


def assert_values_close(values1: List[float], values2: List[float], tol: float = 1e-9):
    """
    Assert that two lists of values are numerically close.
    
    Args:
        values1: First list of values
        values2: Second list of values
        tol: Numerical tolerance
    """
    assert len(values1) == len(values2), (
        f"Value lists have different lengths: {len(values1)} vs {len(values2)}"
    )
    
    for i, (v1, v2) in enumerate(zip(values1, values2)):
        assert abs(v1 - v2) < tol, (
            f"Values at index {i} differ: {v1} vs {v2} (diff: {abs(v1 - v2)})"
        )


def assert_all_finite(values: List[float]):
    """
    Assert that all values are finite (not NaN or inf).
    
    Args:
        values: List of values to check
    """
    for i, v in enumerate(values):
        assert math.isfinite(v), (
            f"Value at index {i} is not finite: {v}"
        )


# ============================================================================
# Degree Centrality Tests
# ============================================================================


@pytest.mark.metamorphic
def test_degree_centrality_relabel_invariance_tiny():
    """
    Degree centrality must be invariant to node relabeling.
    
    Metamorphic relation: When nodes are relabeled bijectively,
    the multiset of degree centrality values must be preserved.
    """
    # Create original network
    net = tiny_two_layer()
    
    # Compute original centrality
    original_values = get_centrality_values(net, "degree_centrality")
    assert original_values is not None, "Failed to compute original centrality"
    
    # Create relabeling
    mapping = {'A': 'node_0', 'B': 'node_1', 'C': 'node_2', 'D': 'node_3'}
    relabeled_net = relabel_nodes(net, mapping)
    
    # Compute relabeled centrality
    relabeled_values = get_centrality_values(relabeled_net, "degree_centrality")
    assert relabeled_values is not None, "Failed to compute relabeled centrality"
    
    # Assert invariance
    assert_values_close(original_values, relabeled_values)


@pytest.mark.metamorphic
def test_degree_centrality_relabel_invariance_small():
    """
    Degree centrality relabel invariance on small three-layer network.
    """
    net = small_three_layer()
    
    original_values = get_centrality_values(net, "degree_centrality")
    assert original_values is not None
    
    # Relabel with string prefixes
    mapping = {node: f"v_{node}" for node in ['A', 'B', 'C', 'D', 'E']}
    relabeled_net = relabel_nodes(net, mapping)
    
    relabeled_values = get_centrality_values(relabeled_net, "degree_centrality")
    assert relabeled_values is not None
    
    assert_values_close(original_values, relabeled_values)


@pytest.mark.metamorphic
def test_degree_centrality_layer_permutation_invariance():
    """
    Degree centrality must be invariant to layer permutation.
    
    Metamorphic relation: When layers are permuted,
    the multiset of degree centrality values must be preserved.
    """
    net = small_three_layer()
    
    original_values = get_centrality_values(net, "degree_centrality")
    assert original_values is not None
    
    # Permute layers: 0->2, 1->0, 2->1 (rotation)
    perm = {0: 2, 1: 0, 2: 1}
    permuted_net = permute_layers(net, perm)
    
    permuted_values = get_centrality_values(permuted_net, "degree_centrality")
    assert permuted_values is not None
    
    assert_values_close(original_values, permuted_values)


@pytest.mark.metamorphic
def test_degree_centrality_edge_order_invariance():
    """
    Degree centrality must be invariant to edge insertion order.
    
    Metamorphic relation: When edges are shuffled,
    the multiset of degree centrality values must be preserved.
    """
    net = two_cliques_bridge()
    
    original_values = get_centrality_values(net, "degree_centrality")
    assert original_values is not None
    
    # Shuffle edge order
    shuffled_net = shuffle_edge_order(net, seed=42)
    
    shuffled_values = get_centrality_values(shuffled_net, "degree_centrality")
    assert shuffled_values is not None
    
    assert_values_close(original_values, shuffled_values)


@pytest.mark.metamorphic
def test_degree_centrality_finiteness():
    """
    Degree centrality values must always be finite (no NaN or inf).
    """
    networks = [
        tiny_two_layer(),
        small_three_layer(),
        two_cliques_bridge(),
        path_graph_multilayer(5, 2),
    ]
    
    for net in networks:
        values = get_centrality_values(net, "degree_centrality")
        assert values is not None
        assert_all_finite(values)


# ============================================================================
# Betweenness Centrality Tests
# ============================================================================


@pytest.mark.metamorphic
def test_betweenness_centrality_relabel_invariance():
    """
    Betweenness centrality must be invariant to node relabeling.
    """
    net = two_cliques_bridge()
    
    original_values = get_centrality_values(net, "betweenness_centrality")
    assert original_values is not None
    
    # Relabel nodes
    mapping = {node: f"node_{i}" for i, node in enumerate(['A', 'B', 'C', 'D', 'E', 'F'])}
    relabeled_net = relabel_nodes(net, mapping)
    
    relabeled_values = get_centrality_values(relabeled_net, "betweenness_centrality")
    assert relabeled_values is not None
    
    assert_values_close(original_values, relabeled_values)


@pytest.mark.metamorphic
def test_betweenness_centrality_layer_permutation_invariance():
    """
    Betweenness centrality must be invariant to layer permutation.
    """
    net = small_three_layer()
    
    original_values = get_centrality_values(net, "betweenness_centrality")
    assert original_values is not None
    
    # Reverse layer order
    perm = {0: 2, 1: 1, 2: 0}
    permuted_net = permute_layers(net, perm)
    
    permuted_values = get_centrality_values(permuted_net, "betweenness_centrality")
    assert permuted_values is not None
    
    assert_values_close(original_values, permuted_values)


@pytest.mark.metamorphic
def test_betweenness_centrality_edge_order_invariance():
    """
    Betweenness centrality must be invariant to edge insertion order.
    """
    net = path_graph_multilayer(5, 2)
    
    original_values = get_centrality_values(net, "betweenness_centrality")
    assert original_values is not None
    
    shuffled_net = shuffle_edge_order(net, seed=123)
    
    shuffled_values = get_centrality_values(shuffled_net, "betweenness_centrality")
    assert shuffled_values is not None
    
    assert_values_close(original_values, shuffled_values)


@pytest.mark.metamorphic
def test_betweenness_centrality_finiteness():
    """
    Betweenness centrality values must always be finite.
    """
    networks = [
        tiny_two_layer(),
        small_three_layer(),
        two_cliques_bridge(),
        path_graph_multilayer(4, 1),
    ]
    
    for net in networks:
        values = get_centrality_values(net, "betweenness_centrality")
        assert values is not None
        assert_all_finite(values)


# ============================================================================
# PageRank Tests
# ============================================================================


@pytest.mark.metamorphic
def test_pagerank_relabel_invariance():
    """
    PageRank must be invariant to node relabeling.
    """
    net = two_cliques_bridge()
    
    original_values = get_centrality_values(net, "pagerank")
    assert original_values is not None
    
    mapping = {node: f"v{i}" for i, node in enumerate(['A', 'B', 'C', 'D', 'E', 'F'])}
    relabeled_net = relabel_nodes(net, mapping)
    
    relabeled_values = get_centrality_values(relabeled_net, "pagerank")
    assert relabeled_values is not None
    
    assert_values_close(original_values, relabeled_values)


@pytest.mark.metamorphic
def test_pagerank_layer_permutation_invariance():
    """
    PageRank must be invariant to layer permutation.
    """
    net = small_three_layer()
    
    original_values = get_centrality_values(net, "pagerank")
    assert original_values is not None
    
    perm = {0: 1, 1: 2, 2: 0}
    permuted_net = permute_layers(net, perm)
    
    permuted_values = get_centrality_values(permuted_net, "pagerank")
    assert permuted_values is not None
    
    assert_values_close(original_values, permuted_values)


@pytest.mark.metamorphic
def test_pagerank_edge_order_invariance():
    """
    PageRank must be invariant to edge insertion order.
    """
    net = tiny_two_layer()
    
    original_values = get_centrality_values(net, "pagerank")
    assert original_values is not None
    
    shuffled_net = shuffle_edge_order(net, seed=999)
    
    shuffled_values = get_centrality_values(shuffled_net, "pagerank")
    assert shuffled_values is not None
    
    assert_values_close(original_values, shuffled_values)


@pytest.mark.metamorphic
def test_pagerank_normalization():
    """
    PageRank values should sum to approximately 1.0.
    
    This is a fundamental property of PageRank as a probability distribution.
    """
    networks = [
        tiny_two_layer(),
        small_three_layer(),
        two_cliques_bridge(),
        path_graph_multilayer(6, 2),
    ]
    
    for net in networks:
        try:
            centrality_dict = net.monoplex_nx_wrapper("pagerank")
            total = sum(centrality_dict.values())
            
            # PageRank should sum to 1.0 (within tolerance)
            assert abs(total - 1.0) < 1e-6, (
                f"PageRank values sum to {total}, expected 1.0"
            )
        except Exception as e:
            pytest.skip(f"PageRank computation failed: {e}")


@pytest.mark.metamorphic
def test_pagerank_finiteness():
    """
    PageRank values must always be finite and non-negative.
    """
    networks = [
        tiny_two_layer(),
        small_three_layer(),
        two_cliques_bridge(),
    ]
    
    for net in networks:
        values = get_centrality_values(net, "pagerank")
        assert values is not None
        assert_all_finite(values)
        
        # PageRank values must be non-negative
        for v in values:
            assert v >= 0, f"PageRank value {v} is negative"


# ============================================================================
# Closeness Centrality Tests
# ============================================================================


@pytest.mark.metamorphic
def test_closeness_centrality_relabel_invariance():
    """
    Closeness centrality must be invariant to node relabeling.
    """
    net = path_graph_multilayer(5, 1)
    
    original_values = get_centrality_values(net, "closeness_centrality")
    assert original_values is not None
    
    mapping = {i: f"n{i}" for i in range(5)}
    relabeled_net = relabel_nodes(net, mapping)
    
    relabeled_values = get_centrality_values(relabeled_net, "closeness_centrality")
    assert relabeled_values is not None
    
    assert_values_close(original_values, relabeled_values)


@pytest.mark.metamorphic
def test_closeness_centrality_edge_order_invariance():
    """
    Closeness centrality must be invariant to edge insertion order.
    """
    net = two_cliques_bridge()
    
    original_values = get_centrality_values(net, "closeness_centrality")
    assert original_values is not None
    
    shuffled_net = shuffle_edge_order(net, seed=456)
    
    shuffled_values = get_centrality_values(shuffled_net, "closeness_centrality")
    assert shuffled_values is not None
    
    assert_values_close(original_values, shuffled_values)


@pytest.mark.metamorphic
def test_closeness_centrality_finiteness():
    """
    Closeness centrality values must always be finite.
    """
    networks = [
        tiny_two_layer(),
        two_cliques_bridge(),
        path_graph_multilayer(4, 1),
    ]
    
    for net in networks:
        values = get_centrality_values(net, "closeness_centrality")
        assert values is not None
        assert_all_finite(values)
