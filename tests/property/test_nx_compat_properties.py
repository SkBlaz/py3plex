#!/usr/bin/env python3
"""
Property-based tests for nx_compat module.

Tests compatibility functions for NetworkX operations across versions.
"""

import tempfile
import os
import pytest
import numpy as np
import networkx as nx
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import nx_compat module
try:
    from py3plex.core.nx_compat import (
        nx_info,
        is_string_like,
        nx_read_gpickle,
        nx_write_gpickle
    )
    NX_COMPAT_AVAILABLE = True
except ImportError:
    NX_COMPAT_AVAILABLE = False
    pytest.skip("nx_compat module not available", allow_module_level=True)


# ============================================================================
# Property Tests: nx_info
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(num_nodes=st.integers(min_value=0, max_value=20))
def test_nx_info_returns_string(num_nodes):
    """Test that nx_info returns a string for any valid graph."""
    G = nx.Graph()
    G.add_nodes_from(range(num_nodes))
    
    result = nx_info(G)
    
    assert isinstance(result, str), "nx_info should return a string"
    assert len(result) > 0, "nx_info should return non-empty string"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_nodes=st.integers(min_value=1, max_value=15),
    num_edges=st.integers(min_value=0, max_value=20)
)
def test_nx_info_contains_node_count(num_nodes, num_edges):
    """Test that nx_info output contains node count."""
    G = nx.Graph()
    G.add_nodes_from(range(num_nodes))
    
    # Add random edges (some may be duplicates)
    for _ in range(min(num_edges, num_nodes * (num_nodes - 1) // 2)):
        try:
            import random
            u, v = random.sample(range(num_nodes), 2)
            G.add_edge(u, v)
        except (ValueError, IndexError):
            pass
    
    result = nx_info(G)
    
    # Should mention number of nodes
    assert str(num_nodes) in result or "nodes" in result.lower(), \
        "nx_info should contain node count information"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(num_nodes=st.integers(min_value=0, max_value=20))
def test_nx_info_handles_directed_graphs(num_nodes):
    """Test that nx_info works with directed graphs."""
    G = nx.DiGraph()
    G.add_nodes_from(range(num_nodes))
    
    result = nx_info(G)
    
    assert isinstance(result, str), "nx_info should work with directed graphs"
    assert len(result) > 0, "nx_info should return non-empty string for DiGraph"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(num_nodes=st.integers(min_value=0, max_value=20))
def test_nx_info_handles_multigraphs(num_nodes):
    """Test that nx_info works with multigraphs."""
    G = nx.MultiGraph()
    G.add_nodes_from(range(num_nodes))
    
    result = nx_info(G)
    
    assert isinstance(result, str), "nx_info should work with multigraphs"
    assert len(result) > 0, "nx_info should return non-empty string for MultiGraph"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(graph_name=st.text(min_size=0, max_size=50))
def test_nx_info_with_graph_name(graph_name):
    """Test that nx_info handles graph names."""
    G = nx.Graph(name=graph_name)
    G.add_node(0)
    
    result = nx_info(G)
    
    assert isinstance(result, str), "nx_info should handle named graphs"


# ============================================================================
# Property Tests: is_string_like
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(text=st.text(min_size=0, max_size=100))
def test_is_string_like_accepts_strings(text):
    """Test that is_string_like accepts strings."""
    result = is_string_like(text)
    
    assert result is True, "is_string_like should return True for strings"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(num=st.integers())
def test_is_string_like_rejects_integers(num):
    """Test that is_string_like rejects integers."""
    result = is_string_like(num)
    
    assert result is False, "is_string_like should return False for integers"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(num=st.floats(allow_nan=False, allow_infinity=False))
def test_is_string_like_rejects_floats(num):
    """Test that is_string_like rejects floats."""
    result = is_string_like(num)
    
    assert result is False, "is_string_like should return False for floats"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(lst=st.lists(st.integers(), min_size=0, max_size=10))
def test_is_string_like_rejects_lists(lst):
    """Test that is_string_like rejects lists."""
    result = is_string_like(lst)
    
    assert result is False, "is_string_like should return False for lists"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(dct=st.dictionaries(st.text(min_size=1), st.integers(), min_size=0, max_size=5))
def test_is_string_like_rejects_dicts(dct):
    """Test that is_string_like rejects dictionaries."""
    result = is_string_like(dct)
    
    assert result is False, "is_string_like should return False for dictionaries"


@pytest.mark.property
def test_is_string_like_rejects_none():
    """Test that is_string_like rejects None."""
    result = is_string_like(None)
    
    assert result is False, "is_string_like should return False for None"


# ============================================================================
# Property Tests: gpickle read/write
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=0, max_value=15))
def test_gpickle_roundtrip_preserves_node_count(num_nodes):
    """Test that gpickle write/read preserves node count."""
    G = nx.Graph()
    G.add_nodes_from(range(num_nodes))
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.gpickle') as f:
        temp_path = f.name
    
    try:
        # Write graph
        nx_write_gpickle(G, temp_path)
        
        # Read graph back
        G_read = nx_read_gpickle(temp_path)
        
        # Should have same number of nodes
        assert G_read.number_of_nodes() == num_nodes, \
            "gpickle roundtrip should preserve node count"
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=10),
    num_edges=st.integers(min_value=1, max_value=15),
    seed=st.integers(min_value=0, max_value=2**31-1)
)
def test_gpickle_roundtrip_preserves_edges(num_nodes, num_edges, seed):
    """Test that gpickle write/read preserves edges."""
    G = nx.Graph()
    G.add_nodes_from(range(num_nodes))
    
    # Use numpy random generator with seed from Hypothesis
    import numpy as np
    rng = np.random.default_rng(seed)
    edges_added = 0
    max_edges = num_nodes * (num_nodes - 1) // 2
    
    for _ in range(min(num_edges, max_edges)):
        if edges_added >= max_edges:
            break
        # Generate random edge using numpy
        nodes = rng.choice(num_nodes, size=2, replace=False)
        u, v = int(nodes[0]), int(nodes[1])
        if not G.has_edge(u, v):
            G.add_edge(u, v)
            edges_added += 1
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.gpickle') as f:
        temp_path = f.name
    
    try:
        # Write graph
        nx_write_gpickle(G, temp_path)
        
        # Read graph back
        G_read = nx_read_gpickle(temp_path)
        
        # Should have same number of edges
        assert G_read.number_of_edges() == G.number_of_edges(), \
            "gpickle roundtrip should preserve edge count"
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=0, max_value=10))
def test_gpickle_roundtrip_preserves_graph_type(num_nodes):
    """Test that gpickle write/read preserves graph type."""
    G = nx.DiGraph()  # Use directed graph
    G.add_nodes_from(range(num_nodes))
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.gpickle') as f:
        temp_path = f.name
    
    try:
        # Write graph
        nx_write_gpickle(G, temp_path)
        
        # Read graph back
        G_read = nx_read_gpickle(temp_path)
        
        # Should be directed
        assert G_read.is_directed(), \
            "gpickle roundtrip should preserve graph type (directed)"
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=1, max_value=10),
    node_attr_val=st.integers()
)
def test_gpickle_roundtrip_preserves_node_attributes(num_nodes, node_attr_val):
    """Test that gpickle write/read preserves node attributes."""
    G = nx.Graph()
    for i in range(num_nodes):
        G.add_node(i, value=node_attr_val)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.gpickle') as f:
        temp_path = f.name
    
    try:
        # Write graph
        nx_write_gpickle(G, temp_path)
        
        # Read graph back
        G_read = nx_read_gpickle(temp_path)
        
        # Check node attributes preserved
        for node in G_read.nodes():
            assert 'value' in G_read.nodes[node], \
                "Node attributes should be preserved"
            assert G_read.nodes[node]['value'] == node_attr_val, \
                "Node attribute values should be preserved"
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
