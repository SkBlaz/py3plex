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
        parse_nx,
    )
    from py3plex.core import multinet
    PARSERS_AVAILABLE = True
except ImportError:
    PARSERS_AVAILABLE = False
    pytest.skip("Parsers module not available", allow_module_level=True)


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
    # Create a graph - use higher probability to ensure all nodes have edges
    if directed:
        G = nx.gnp_random_graph(num_nodes, 0.7, seed=seed, directed=True)
    else:
        G = nx.gnp_random_graph(num_nodes, 0.7, seed=seed, directed=False)
    
    assume(G.number_of_edges() > 0)
    
    # Remove isolated nodes (parse_gml only preserves nodes with edges)
    isolated = list(nx.isolates(G))
    G.remove_nodes_from(isolated)
    
    assume(G.number_of_nodes() > 0)
    
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
        
        # Should preserve structure (all nodes should be preserved since no isolated nodes)
        assert H.number_of_nodes() == original_nodes, \
            f"Node count should be preserved, expected {original_nodes}, got {H.number_of_nodes()}"
        assert H.number_of_edges() == original_edges, \
            f"Edge count should be preserved, expected {original_edges}, got {H.number_of_edges()}"
        
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

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
