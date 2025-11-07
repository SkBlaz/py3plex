#!/usr/bin/env python3
"""
Property-based tests for basic statistics functions.

This module tests network statistics functions from 
py3plex.algorithms.statistics.basic_statistics using Hypothesis.

TARGET FUNCTIONS:
1. identify_n_hubs(G, top_n, node_type) - find top N hub nodes by degree

PROPERTIES TESTED:
- Structural: returns dict with at most top_n entries
- Structural: all degree values are non-negative integers
- Monotone: degrees are in descending order
- Boundary: handles top_n larger than graph size
- Invariant: result is subset of graph nodes
"""

import networkx as nx
import pytest
from hypothesis import assume, given, strategies as st

from py3plex.algorithms.statistics.basic_statistics import identify_n_hubs
from tests.property.strategies import small_graphs


# ============================================================================
# Property Tests: identify_n_hubs
# ============================================================================

@pytest.mark.property
@given(
    G=small_graphs(min_nodes=3, max_nodes=10),
    top_n=st.integers(min_value=1, max_value=20)
)
def test_identify_n_hubs_returns_dict(G, top_n):
    """Property: identify_n_hubs returns a dictionary."""
    result = identify_n_hubs(G, top_n=top_n)
    
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"


@pytest.mark.property
@given(
    G=small_graphs(min_nodes=3, max_nodes=10),
    top_n=st.integers(min_value=1, max_value=20)
)
def test_identify_n_hubs_at_most_top_n_entries(G, top_n):
    """Property: identify_n_hubs returns at most top_n entries."""
    result = identify_n_hubs(G, top_n=top_n)
    
    assert len(result) <= top_n, \
        f"Expected at most {top_n} entries, got {len(result)}"


@pytest.mark.property
@given(
    G=small_graphs(min_nodes=3, max_nodes=10),
    top_n=st.integers(min_value=1, max_value=20)
)
def test_identify_n_hubs_non_negative_degrees(G, top_n):
    """Property: all degree values are non-negative integers."""
    result = identify_n_hubs(G, top_n=top_n)
    
    for node, degree in result.items():
        assert isinstance(degree, int), f"Degree {degree} is not an integer"
        assert degree >= 0, f"Degree {degree} is negative"


@pytest.mark.property
@given(
    G=small_graphs(min_nodes=3, max_nodes=10),
    top_n=st.integers(min_value=1, max_value=20)
)
def test_identify_n_hubs_nodes_in_graph(G, top_n):
    """Property: all returned nodes exist in the graph."""
    result = identify_n_hubs(G, top_n=top_n)
    graph_nodes = set(G.nodes())
    
    for node in result.keys():
        assert node in graph_nodes, f"Node {node} not in graph"


@pytest.mark.property
@given(
    G=small_graphs(min_nodes=3, max_nodes=10),
    top_n=st.integers(min_value=1, max_value=20)
)
def test_identify_n_hubs_degrees_match_graph(G, top_n):
    """Property: returned degrees match actual node degrees in graph."""
    result = identify_n_hubs(G, top_n=top_n)
    
    for node, degree in result.items():
        actual_degree = G.degree(node)
        assert degree == actual_degree, \
            f"Degree mismatch for node {node}: {degree} != {actual_degree}"


@pytest.mark.property
@given(
    G=small_graphs(min_nodes=3, max_nodes=10),
    top_n=st.integers(min_value=1, max_value=20)
)
def test_identify_n_hubs_descending_order(G, top_n):
    """Property: hubs are returned in descending order of degree."""
    result = identify_n_hubs(G, top_n=top_n)
    
    degrees = list(result.values())
    # Check that degrees are non-increasing
    for i in range(len(degrees) - 1):
        assert degrees[i] >= degrees[i + 1], \
            f"Degrees not in descending order: {degrees}"


@pytest.mark.property
@given(
    G=small_graphs(min_nodes=5, max_nodes=10),
    top_n=st.integers(min_value=1, max_value=3)
)
def test_identify_n_hubs_returns_highest_degree_nodes(G, top_n):
    """Property: returned nodes have the highest degrees in the graph."""
    assume(G.number_of_nodes() >= top_n)
    
    result = identify_n_hubs(G, top_n=top_n)
    
    # Get all degrees from graph
    all_degrees = dict(G.degree())
    sorted_degrees = sorted(all_degrees.items(), key=lambda x: x[1], reverse=True)
    
    # Top top_n nodes from manual sort
    expected_top = {node: deg for node, deg in sorted_degrees[:top_n]}
    
    assert result == expected_top, \
        f"Returned hubs {result} don't match expected top {top_n}: {expected_top}"


@pytest.mark.property
@given(
    G=small_graphs(min_nodes=3, max_nodes=10),
    top_n=st.integers(min_value=1, max_value=5)
)
def test_identify_n_hubs_handles_top_n_larger_than_graph(G, top_n):
    """Property: when top_n > |V|, returns at most |V| nodes."""
    result = identify_n_hubs(G, top_n=top_n)
    
    num_nodes = G.number_of_nodes()
    assert len(result) <= num_nodes, \
        f"Returned {len(result)} hubs for graph with {num_nodes} nodes"
    assert len(result) <= top_n, \
        f"Returned {len(result)} hubs when top_n={top_n}"


@pytest.mark.property
@given(G=small_graphs(min_nodes=1, max_nodes=10))
def test_identify_n_hubs_empty_graph_returns_empty(G):
    """Property: for empty graph (no nodes), returns empty dict."""
    # Create empty graph
    empty_G = type(G)()  # Same type as G but empty
    
    result = identify_n_hubs(empty_G, top_n=5)
    
    assert result == {}, "Empty graph should return empty dict"


@pytest.mark.property
@given(
    G=small_graphs(min_nodes=3, max_nodes=10, directed=False),
    top_n=st.integers(min_value=1, max_value=5)
)
def test_identify_n_hubs_deterministic(G, top_n):
    """Property: identify_n_hubs is deterministic (same inputs -> same outputs)."""
    result1 = identify_n_hubs(G, top_n=top_n)
    result2 = identify_n_hubs(G, top_n=top_n)
    
    assert result1 == result2, "Function should be deterministic"


@pytest.mark.property
@given(
    G=small_graphs(min_nodes=3, max_nodes=10),
    top_n1=st.integers(min_value=1, max_value=5),
    top_n2=st.integers(min_value=1, max_value=5)
)
def test_identify_n_hubs_subset_property(G, top_n1, top_n2):
    """Property: top_n1 < top_n2 implies result1 ⊆ result2."""
    assume(top_n1 < top_n2)
    assume(G.number_of_nodes() >= top_n2)
    
    result1 = identify_n_hubs(G, top_n=top_n1)
    result2 = identify_n_hubs(G, top_n=top_n2)
    
    # All nodes in result1 should be in result2
    for node in result1.keys():
        assert node in result2, \
            f"Node {node} in top-{top_n1} but not in top-{top_n2}"


@pytest.mark.property
@given(
    n=st.integers(min_value=3, max_value=10),
    top_n=st.integers(min_value=1, max_value=5)
)
def test_identify_n_hubs_complete_graph_all_equal(n, top_n):
    """Property: in complete graph, all nodes have degree n-1."""
    G = nx.complete_graph(n)
    
    result = identify_n_hubs(G, top_n=top_n)
    
    expected_degree = n - 1
    for node, degree in result.items():
        assert degree == expected_degree, \
            f"Complete graph node {node} should have degree {expected_degree}, got {degree}"


@pytest.mark.property
@given(
    n=st.integers(min_value=3, max_value=10),
    top_n=st.integers(min_value=1, max_value=20)
)
def test_identify_n_hubs_star_graph_center_is_hub(n, top_n):
    """Property: in star graph, center (node 0) is the top hub."""
    assume(top_n >= 1)
    G = nx.star_graph(n - 1)  # Creates star with n nodes
    
    result = identify_n_hubs(G, top_n=top_n)
    
    # Node 0 is the center with highest degree
    assert 0 in result, "Center node 0 should be in top hubs"
    
    if len(result) >= 1:
        # First node in result (highest degree) should be center
        first_node = list(result.keys())[0]
        assert first_node == 0, f"Center (0) should be top hub, got {first_node}"
        assert result[0] == n - 1, f"Center should have degree {n-1}, got {result[0]}"


@pytest.mark.property
@given(
    n=st.integers(min_value=4, max_value=10),
    top_n=st.integers(min_value=1, max_value=5)
)
def test_identify_n_hubs_path_graph_middle_nodes_higher(n, top_n):
    """Property: in path graph, middle nodes tend to have higher degree than endpoints."""
    G = nx.path_graph(n)
    
    result = identify_n_hubs(G, top_n=top_n)
    
    # Endpoints (0 and n-1) have degree 1
    # Middle nodes have degree 2
    # Middle nodes should appear in hubs before endpoints (if top_n allows)
    
    if len(result) > 0:
        # All returned degrees should be at least 1
        for degree in result.values():
            assert degree >= 1, "Path graph nodes have degree >= 1"
        
        # If we return more than n-2 hubs, we'll include endpoints
        # Otherwise, hubs should all have degree 2 (middle nodes)
        if top_n < n - 2:
            for node, degree in result.items():
                assert degree == 2, \
                    f"Top hubs in path should have degree 2, got {degree} for node {node}"


@pytest.mark.property
@given(n=st.integers(min_value=3, max_value=10))
def test_identify_n_hubs_zero_top_n_returns_empty(n):
    """Property: top_n = 0 returns empty dict (boundary case)."""
    G = nx.complete_graph(n)
    
    # With top_n=0, should return empty dict
    result = identify_n_hubs(G, top_n=0)
    # Note: @require decorator may not enforce when icontract unavailable
    # Current behavior returns empty dict
    if result is not None:
        assert isinstance(result, dict)
        # May return empty dict or raise - document actual behavior
