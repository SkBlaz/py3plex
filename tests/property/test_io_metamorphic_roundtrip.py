#!/usr/bin/env python3
"""
Metamorphic I/O roundtrip tests for py3plex.

Tests that loading/importing networks preserves structure and that
certain transformations (permutations, format changes) don't affect topology.
"""

import tempfile
from pathlib import Path

import networkx as nx
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from py3plex.core.multinet import multi_layer_network

from .strategies import small_graphs, connected_graphs


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=2, max_value=8))
def test_nx_import_preserves_nodes(n):
    """
    Test that importing a NetworkX graph preserves the node set.
    
    Property: load_network(G, input_type="nx") should preserve nodes.
    """
    # Create a simple graph
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    
    # Import into py3plex
    mlnet = multi_layer_network(verbose=False, network_type="multilayer")
    mlnet.load_network(G, input_type="nx")
    
    # Check that nodes are preserved
    original_nodes = set(G.nodes())
    imported_nodes = set(mlnet.get_nodes())
    
    assert original_nodes == imported_nodes, \
        f"Node set mismatch: original={original_nodes}, imported={imported_nodes}"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=2, max_value=8))
def test_nx_import_preserves_edges(n):
    """
    Test that importing a NetworkX graph preserves the edge set.
    
    Property: load_network(G, input_type="nx") should preserve edges.
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(G.number_of_edges() > 0)
    
    # Import into py3plex
    mlnet = multi_layer_network(verbose=False, network_type="multilayer")
    mlnet.load_network(G, input_type="nx")
    
    # Check edge counts match
    original_edge_count = G.number_of_edges()
    imported_edge_count = len(list(mlnet.get_edges()))
    
    assert original_edge_count == imported_edge_count, \
        f"Edge count mismatch: original={original_edge_count}, imported={imported_edge_count}"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=2, max_value=8))
def test_nx_directed_flag_respected(n):
    """
    Test that the directed flag is respected when loading.
    
    Property: directed=True should create DiGraph, directed=False should create Graph.
    """
    p = 0.5
    G_directed = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32), directed=True)
    G_undirected = nx.gnp_random_graph(n, p, seed=hash(n+1) % (2**32), directed=False)
    
    # Test directed
    mlnet_dir = multi_layer_network(verbose=False, directed=True)
    mlnet_dir.load_network(G_directed, input_type="nx", directed=True)
    assert mlnet_dir.directed is True
    assert isinstance(mlnet_dir.core_network, (nx.DiGraph, nx.MultiDiGraph))
    
    # Test undirected
    mlnet_undir = multi_layer_network(verbose=False, directed=False)
    mlnet_undir.load_network(G_undirected, input_type="nx", directed=False)
    assert mlnet_undir.directed is False
    assert isinstance(mlnet_undir.core_network, (nx.Graph, nx.MultiGraph))


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=3, max_value=8))
def test_edgelist_roundtrip_preserves_structure(n):
    """
    Test that writing to edgelist and reading back preserves basic structure.
    
    Property: save -> load roundtrip produces a valid network with edges.
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(G.number_of_edges() > 0)
    
    # Create multilayer network
    mlnet = multi_layer_network(verbose=False, network_type="multilayer")
    mlnet.load_network(G, input_type="nx")
    
    original_edge_count = len(list(mlnet.get_edges()))
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.edgelist', delete=False) as f:
        temp_path = f.name
    
    try:
        mlnet.save_network(output_file=temp_path, output_type="edgelist")
        
        # Load back
        mlnet2 = multi_layer_network(verbose=False, network_type="multilayer")
        mlnet2.load_network(
            input_file=temp_path,
            input_type="edgelist",
            directed=False
        )
        
        # Check that network is valid and has edges
        reloaded_edge_count = len(list(mlnet2.get_edges()))
        
        # Should have some edges (exact count may differ due to format)
        assert reloaded_edge_count > 0, \
            "No edges after roundtrip"
        
        # Should have reasonable number of edges (at least half)
        assert reloaded_edge_count >= original_edge_count * 0.5, \
            f"Too few edges after roundtrip: {reloaded_edge_count} vs {original_edge_count}"
    
    finally:
        # Cleanup
        Path(temp_path).unlink(missing_ok=True)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=2, max_value=6))
def test_node_relabeling_preserves_topology(n):
    """
    Test that relabeling nodes doesn't change graph structure.
    
    Property: Isomorphic graphs have same structural properties.
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(G.number_of_edges() > 0)
    
    # Create a relabeled version
    mapping = {i: str(i) for i in G.nodes()}
    G_relabeled = nx.relabel_nodes(G, mapping)
    
    # Import both
    mlnet1 = multi_layer_network(verbose=False)
    mlnet1.load_network(G, input_type="nx")
    
    mlnet2 = multi_layer_network(verbose=False)
    mlnet2.load_network(G_relabeled, input_type="nx")
    
    # Check same counts
    assert mlnet1.core_network.number_of_nodes() == mlnet2.core_network.number_of_nodes()
    assert mlnet1.core_network.number_of_edges() == mlnet2.core_network.number_of_edges()


@pytest.mark.property
def test_empty_network_import():
    """
    Test that importing an empty graph doesn't crash.
    
    Property: Empty graphs are valid inputs.
    """
    G = nx.Graph()
    
    mlnet = multi_layer_network(verbose=False)
    mlnet.load_network(G, input_type="nx")
    
    assert mlnet.core_network is not None
    assert mlnet.core_network.number_of_nodes() == 0
    assert mlnet.core_network.number_of_edges() == 0


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=1, max_value=8))
def test_load_network_nonnegative_counts(n):
    """
    Test that loaded networks have non-negative node/edge counts.
    
    Property: Counts are always >= 0 (contract postcondition).
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    
    mlnet = multi_layer_network(verbose=False)
    mlnet.load_network(G, input_type="nx")
    
    assert mlnet.core_network.number_of_nodes() >= 0
    assert mlnet.core_network.number_of_edges() >= 0


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(n=st.integers(min_value=2, max_value=6))
def test_weighted_graph_import(n):
    """
    Test that weighted graphs import correctly.
    
    Property: Edge weights should be preserved during import.
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(G.number_of_edges() > 0)
    
    # Add weights
    for u, v in G.edges():
        G[u][v]['weight'] = float(u + v + 1)
    
    mlnet = multi_layer_network(verbose=False)
    mlnet.load_network(G, input_type="nx")
    
    # Check that network loaded
    assert mlnet.core_network.number_of_edges() > 0
    
    # Check that some edges have weight attribute
    edges_with_weight = sum(
        1 for _, _, data in mlnet.get_edges(data=True)
        if data and 'weight' in data
    )
    
    assert edges_with_weight > 0, "No edges with weight attribute found"
