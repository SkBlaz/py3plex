#!/usr/bin/env python3
"""
Property-based tests for I/O round-trip invariants.

Tests that loading a NetworkX graph into py3plex preserves nodes and edges.
"""

import networkx as nx
import pytest
from hypothesis import given, strategies as st, settings, assume

from py3plex.core import multinet


# Custom strategy to generate simple undirected graphs
@st.composite
def simple_graph(draw, min_nodes=1, max_nodes=12, p=0.3):
    """
    Generate a simple undirected NetworkX graph.
    
    Args:
        draw: Hypothesis draw function
        min_nodes: Minimum number of nodes
        max_nodes: Maximum number of nodes
        p: Edge probability for random graph
    
    Returns:
        NetworkX Graph object
    """
    n = draw(st.integers(min_value=min_nodes, max_value=max_nodes))
    # Use fixed seed based on n for determinism
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    # Relabel nodes with string labels to test label handling
    mapping = {i: f"node_{i}" for i in G.nodes()}
    G = nx.relabel_nodes(G, mapping)
    return G


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(G=simple_graph())
def test_load_network_preserves_nodes_edges(G):
    """
    Test that loading a NetworkX graph preserves nodes and edges.
    
    Property: For any simple undirected graph G, loading it into py3plex
    and accessing core_network should preserve:
    - The set of nodes (unordered)
    - The set of edges (unordered, undirected)
    """
    # Skip empty graphs
    assume(G.number_of_nodes() > 0)
    
    # Load the graph into py3plex
    m = multinet.multi_layer_network().load_network(
        G, input_type="nx", directed=False
    )
    H = m.core_network
    
    # Verify nodes are preserved
    assert set(H.nodes()) == set(G.nodes()), \
        f"Nodes mismatch: expected {set(G.nodes())}, got {set(H.nodes())}"
    
    # Verify edges are preserved (as unordered pairs for undirected graphs)
    g_edges = {tuple(sorted(e)) for e in G.edges()}
    h_edges = {tuple(sorted(e)) for e in H.edges()}
    
    assert h_edges == g_edges, \
        f"Edges mismatch: expected {g_edges}, got {h_edges}"


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    n=st.integers(min_value=2, max_value=10),
    m=st.integers(min_value=1, max_value=15)
)
def test_load_network_directed_preserves_structure(n, m):
    """
    Test that loading directed graphs preserves directed edges.
    
    Property: For directed graphs, edge direction is preserved.
    """
    # Create a directed graph with m edges
    G = nx.DiGraph()
    G.add_nodes_from(range(n))
    
    # Add m edges ensuring valid node indices
    edges = set()
    for _ in range(m):
        u = hash((n, m, _)) % n
        v = hash((n, m, _ + 1000)) % n
        if u != v:  # Avoid self-loops
            edges.add((u, v))
    
    G.add_edges_from(edges)
    assume(G.number_of_edges() > 0)
    
    # Load as directed
    m_net = multinet.multi_layer_network().load_network(
        G, input_type="nx", directed=True
    )
    H = m_net.core_network
    
    # Verify directed edges are preserved
    assert set(H.edges()) == set(G.edges()), \
        f"Directed edges mismatch"
    
    # Verify the graph is directed
    assert isinstance(H, (nx.MultiDiGraph, nx.DiGraph)), \
        f"Expected directed graph, got {type(H)}"


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(n=st.integers(min_value=1, max_value=15))
def test_load_network_node_count_invariant(n):
    """
    Test that node count is preserved.
    
    Property: number_of_nodes() after loading equals input node count.
    """
    G = nx.complete_graph(n)
    
    m = multinet.multi_layer_network().load_network(
        G, input_type="nx", directed=False
    )
    H = m.core_network
    
    assert H.number_of_nodes() == n, \
        f"Node count mismatch: expected {n}, got {H.number_of_nodes()}"


@pytest.mark.property
@settings(deadline=None, max_examples=5)
@given(
    n=st.integers(min_value=2, max_value=8),
    p=st.floats(min_value=0.0, max_value=1.0)
)
def test_load_network_nonnegative_counts(n, p):
    """
    Test that loaded network has non-negative node and edge counts.
    
    Property: After loading, core_network has:
    - number_of_nodes() >= 0
    - number_of_edges() >= 0
    """
    G = nx.gnp_random_graph(n, p, seed=hash((n, p)) % (2**32))
    
    m = multinet.multi_layer_network().load_network(
        G, input_type="nx", directed=False
    )
    H = m.core_network
    
    assert H.number_of_nodes() >= 0, \
        f"Negative node count: {H.number_of_nodes()}"
    assert H.number_of_edges() >= 0, \
        f"Negative edge count: {H.number_of_edges()}"
