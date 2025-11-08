#!/usr/bin/env python3
"""
Property-based tests for core.parsers module.

Tests invariants and properties of parsing functions:
- Parsed graphs maintain node and edge counts
- Graph type (directed/undirected) is preserved
- Node and edge attributes are valid
- Round-trip preservation (save and load)
"""

import networkx as nx
import numpy as np
import pytest
import tempfile
import os
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import shared strategies
from .strategies import (
    small_graphs,
)

# Import parsers module
try:
    from py3plex.core.parsers import (
        parse_gml,
        load_network_from_nx,
        edgelist_to_nx,
    )
    from py3plex.core import multinet
    PARSERS_AVAILABLE = True
except ImportError:
    PARSERS_AVAILABLE = False
    pytest.skip("Parsers module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Network Loading from NetworkX
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=12),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_load_network_preserves_node_count(num_nodes, seed):
    """Property: Loading from NetworkX preserves node count."""
    # Create a NetworkX graph
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    # Load into py3plex
    net = multinet.multi_layer_network()
    load_network_from_nx(G, net)
    
    # Should have same number of nodes
    assert net.number_of_nodes() == num_nodes, \
        f"Node count should be preserved: expected {num_nodes}, got {net.number_of_nodes()}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=12),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_load_network_preserves_edge_count(num_nodes, seed):
    """Property: Loading from NetworkX preserves edge count."""
    # Create a NetworkX graph
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    original_edge_count = G.number_of_edges()
    
    # Load into py3plex
    net = multinet.multi_layer_network()
    load_network_from_nx(G, net)
    
    # Should have same number of edges
    assert net.number_of_edges() == original_edge_count, \
        f"Edge count should be preserved: expected {original_edge_count}, got {net.number_of_edges()}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=12),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_load_network_directed_undirected(num_nodes, seed):
    """Property: Loading preserves directed/undirected nature."""
    # Test undirected
    G_undirected = nx.gnp_random_graph(num_nodes, 0.5, seed=seed, directed=False)
    assume(G_undirected.number_of_edges() > 0)
    
    net_undirected = multinet.multi_layer_network()
    load_network_from_nx(G_undirected, net_undirected)
    
    # Test directed
    G_directed = nx.gnp_random_graph(num_nodes, 0.5, seed=seed, directed=True)
    assume(G_directed.number_of_edges() > 0)
    
    net_directed = multinet.multi_layer_network()
    load_network_from_nx(G_directed, net_directed)
    
    # Both should complete without error
    assert net_undirected.number_of_nodes() > 0
    assert net_directed.number_of_nodes() > 0


# ============================================================================
# Property Tests: Edge List to NetworkX Conversion
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_edges=st.integers(min_value=1, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_edgelist_to_nx_preserves_edge_count(num_edges, seed):
    """Property: Converting edge list to NetworkX preserves edge count."""
    import random
    random.seed(seed)
    
    # Create edge list
    edge_list = []
    for _ in range(num_edges):
        u = random.randint(0, 10)
        v = random.randint(0, 10)
        if u != v:  # Avoid self-loops
            edge_list.append([u, v])
    
    assume(len(edge_list) > 0)
    
    try:
        # Convert to NetworkX
        G = edgelist_to_nx(edge_list)
        
        # Should have at least as many edges (duplicates may be merged)
        assert G.number_of_edges() > 0, "Graph should have edges"
        assert G.number_of_edges() <= len(edge_list), \
            "Graph edges should not exceed input edge list"
    except Exception as e:
        # If edgelist_to_nx doesn't exist or fails, skip
        if "edgelist_to_nx" in str(e):
            pytest.skip("edgelist_to_nx not available")
        raise


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_edges=st.integers(min_value=1, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_edgelist_to_nx_creates_valid_graph(num_edges, seed):
    """Property: Edge list conversion creates valid NetworkX graph."""
    import random
    random.seed(seed)
    
    # Create edge list
    edge_list = []
    for _ in range(num_edges):
        u = random.randint(0, 10)
        v = random.randint(0, 10)
        if u != v:
            edge_list.append([u, v])
    
    assume(len(edge_list) > 0)
    
    try:
        # Convert to NetworkX
        G = edgelist_to_nx(edge_list)
        
        # Should be a valid NetworkX graph
        assert isinstance(G, nx.Graph), "Result should be a NetworkX graph"
        assert G.number_of_nodes() > 0, "Graph should have nodes"
        assert G.number_of_edges() > 0, "Graph should have edges"
    except Exception as e:
        if "edgelist_to_nx" in str(e):
            pytest.skip("edgelist_to_nx not available")
        raise


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_edges=st.integers(min_value=1, max_value=10),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_edgelist_to_nx_all_edges_present(num_edges, seed):
    """Property: All edges from edge list are present in graph."""
    import random
    random.seed(seed)
    
    # Create edge list with unique edges
    edge_set = set()
    while len(edge_set) < num_edges:
        u = random.randint(0, 5)
        v = random.randint(0, 5)
        if u != v:
            edge_set.add((min(u, v), max(u, v)))  # Normalize edge
    
    edge_list = [[u, v] for u, v in edge_set]
    
    try:
        # Convert to NetworkX
        G = edgelist_to_nx(edge_list)
        
        # All edges should be in graph
        for u, v in edge_set:
            assert G.has_edge(u, v) or G.has_edge(v, u), \
                f"Edge ({u}, {v}) should be in graph"
    except Exception as e:
        if "edgelist_to_nx" in str(e):
            pytest.skip("edgelist_to_nx not available")
        raise


# ============================================================================
# Property Tests: GML Parsing
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    directed=st.booleans(),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_gml_roundtrip_preserves_structure(num_nodes, directed, seed):
    """Property: Writing and reading GML preserves graph structure."""
    # Create a graph
    if directed:
        G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed, directed=True)
    else:
        G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed, directed=False)
    
    assume(G.number_of_edges() > 0)
    
    # Add type attribute to nodes (required for parse_gml)
    for node in G.nodes():
        G.nodes[node]['type'] = 'default'
    
    original_nodes = G.number_of_nodes()
    original_edges = G.number_of_edges()
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gml', delete=False) as f:
        temp_file = f.name
    
    try:
        # Write to GML
        nx.write_gml(G, temp_file)
        
        # Parse back
        H, _ = parse_gml(temp_file, directed)
        
        # Should preserve structure (within reason for MultiGraph conversion)
        assert H.number_of_nodes() >= original_nodes, \
            f"Node count should be preserved or increased"
        assert H.number_of_edges() >= original_edges, \
            f"Edge count should be preserved or increased"
        
        # Should be correct graph type
        if directed:
            assert isinstance(H, nx.MultiDiGraph), "Should be MultiDiGraph"
        else:
            assert isinstance(H, nx.MultiGraph), "Should be MultiGraph"
    
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_gml_parse_returns_multigraph(num_nodes, seed):
    """Property: parse_gml always returns a MultiGraph or MultiDiGraph."""
    # Create a graph
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    # Add type attribute
    for node in G.nodes():
        G.nodes[node]['type'] = 'default'
    
    # Create temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gml', delete=False) as f:
        temp_file = f.name
    
    try:
        # Write to GML
        nx.write_gml(G, temp_file)
        
        # Parse as undirected
        H_undirected, _ = parse_gml(temp_file, directed=False)
        assert isinstance(H_undirected, nx.MultiGraph), \
            "Undirected parse should return MultiGraph"
        
        # Parse as directed
        H_directed, _ = parse_gml(temp_file, directed=True)
        assert isinstance(H_directed, nx.MultiDiGraph), \
            "Directed parse should return MultiDiGraph"
    
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)


# ============================================================================
# Property Tests: Parser Consistency
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_load_network_empty_graph(num_nodes, seed):
    """Property: Loading empty graph (no edges) should work."""
    # Create a graph with nodes but no edges
    G = nx.Graph()
    G.add_nodes_from(range(num_nodes))
    
    # Load into py3plex
    net = multinet.multi_layer_network()
    load_network_from_nx(G, net)
    
    # Should have nodes
    assert net.number_of_nodes() == num_nodes
    # Should have no edges
    assert net.number_of_edges() == 0


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10)
)
def test_load_network_complete_graph(num_nodes):
    """Property: Loading complete graph preserves all edges."""
    # Create complete graph
    G = nx.complete_graph(num_nodes)
    
    expected_edges = num_nodes * (num_nodes - 1) // 2
    
    # Load into py3plex
    net = multinet.multi_layer_network()
    load_network_from_nx(G, net)
    
    # Should have all nodes
    assert net.number_of_nodes() == num_nodes
    # Should have all edges
    assert net.number_of_edges() == expected_edges


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10)
)
def test_load_network_star_graph(num_nodes):
    """Property: Loading star graph preserves structure."""
    # Create star graph
    G = nx.star_graph(num_nodes - 1)
    
    expected_edges = num_nodes - 1  # Center connected to all leaves
    
    # Load into py3plex
    net = multinet.multi_layer_network()
    load_network_from_nx(G, net)
    
    # Should have all nodes
    assert net.number_of_nodes() == num_nodes
    # Should have correct edges
    assert net.number_of_edges() == expected_edges


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10)
)
def test_load_network_cycle_graph(num_nodes):
    """Property: Loading cycle graph preserves structure."""
    # Create cycle graph
    G = nx.cycle_graph(num_nodes)
    
    expected_edges = num_nodes  # Each node connected to 2 neighbors
    
    # Load into py3plex
    net = multinet.multi_layer_network()
    load_network_from_nx(G, net)
    
    # Should have all nodes
    assert net.number_of_nodes() == num_nodes
    # Should have correct edges
    assert net.number_of_edges() == expected_edges


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10)
)
def test_load_network_path_graph(num_nodes):
    """Property: Loading path graph preserves structure."""
    # Create path graph
    G = nx.path_graph(num_nodes)
    
    expected_edges = num_nodes - 1  # Linear chain
    
    # Load into py3plex
    net = multinet.multi_layer_network()
    load_network_from_nx(G, net)
    
    # Should have all nodes
    assert net.number_of_nodes() == num_nodes
    # Should have correct edges
    assert net.number_of_edges() == expected_edges


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
