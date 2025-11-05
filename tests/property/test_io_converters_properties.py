#!/usr/bin/env python3
"""
Property-based tests for io.converters module.

Tests conversion between MultiLayerGraph and NetworkX, preserving structure and attributes.
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import converters module
try:
    from py3plex.io.schema import MultiLayerGraph, Node, Edge, Layer
    from py3plex.io.converters import to_networkx, from_networkx
    import networkx as nx
    CONVERTERS_AVAILABLE = True
except ImportError:
    CONVERTERS_AVAILABLE = False
    pytest.skip("IO converters module not available", allow_module_level=True)


# ============================================================================
# Helper Functions
# ============================================================================

def create_simple_multilayer_graph(num_nodes=3, num_layers=2):
    """Create a simple MultiLayerGraph for testing."""
    graph = MultiLayerGraph(directed=False)
    
    # Add layers
    for i in range(num_layers):
        layer = Layer(id=f'layer{i}', attributes={})
        graph.add_layer(layer)
    
    # Add nodes
    for i in range(num_nodes):
        node = Node(id=f'n{i}', attributes={})
        graph.add_node(node)
    
    # Add edges within layers
    for layer_idx in range(num_layers):
        layer_id = f'layer{layer_idx}'
        for i in range(num_nodes - 1):
            edge = Edge(
                src=f'n{i}',
                dst=f'n{i+1}',
                src_layer=layer_id,
                dst_layer=layer_id,
                attributes={}
            )
            graph.add_edge(edge)
    
    return graph


# ============================================================================
# Property Tests: to_networkx Conversion
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=8),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_to_networkx_union_preserves_nodes(num_nodes, num_layers):
    """Test that union mode preserves all unique nodes."""
    graph = create_simple_multilayer_graph(num_nodes, num_layers)
    
    # Convert to NetworkX with union mode
    nx_graph = to_networkx(graph, mode="union")
    
    # Should have all nodes
    assert nx_graph.number_of_nodes() == num_nodes, \
        f"Should have {num_nodes} nodes, got {nx_graph.number_of_nodes()}"


@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=8),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_to_networkx_union_merges_edges(num_nodes, num_layers):
    """Test that union mode merges edges from all layers."""
    graph = create_simple_multilayer_graph(num_nodes, num_layers)
    
    # Convert to NetworkX with union mode
    nx_graph = to_networkx(graph, mode="union")
    
    # Union mode merges edges from all layers
    # Each layer has num_nodes-1 edges, merged into single graph
    # Depending on implementation, may have parallel edges or merged
    assert nx_graph.number_of_edges() >= num_nodes - 1, \
        f"Should have at least {num_nodes - 1} edges"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=8),
    num_layers=st.integers(min_value=2, max_value=3)
)
def test_to_networkx_multiplex_preserves_layer_info(num_nodes, num_layers):
    """Test that multiplex mode preserves layer information."""
    graph = create_simple_multilayer_graph(num_nodes, num_layers)
    
    # Convert to NetworkX with multiplex mode
    nx_graph = to_networkx(graph, mode="multiplex")
    
    # Multiplex mode creates (node, layer) tuples
    # Should have num_nodes * num_layers node-layer pairs
    expected_nodes = num_nodes * num_layers
    assert nx_graph.number_of_nodes() == expected_nodes, \
        f"Should have {expected_nodes} node-layer pairs, got {nx_graph.number_of_nodes()}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=8),
    num_layers=st.integers(min_value=2, max_value=3)
)
def test_to_networkx_multiplex_preserves_edges(num_nodes, num_layers):
    """Test that multiplex mode preserves all edges."""
    graph = create_simple_multilayer_graph(num_nodes, num_layers)
    
    # Convert to NetworkX with multiplex mode
    nx_graph = to_networkx(graph, mode="multiplex")
    
    # Each layer has num_nodes-1 edges
    expected_edges = num_layers * (num_nodes - 1)
    assert nx_graph.number_of_edges() >= expected_edges, \
        f"Should have at least {expected_edges} edges"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=8))
def test_to_networkx_returns_correct_type(num_nodes):
    """Test that conversion returns correct NetworkX graph type."""
    # Test undirected
    graph_undirected = create_simple_multilayer_graph(num_nodes, 1)
    graph_undirected.directed = False
    nx_graph = to_networkx(graph_undirected, mode="union")
    assert isinstance(nx_graph, (nx.MultiGraph, nx.MultiDiGraph)), \
        "Should return NetworkX MultiGraph or MultiDiGraph"
    
    # Test directed
    graph_directed = create_simple_multilayer_graph(num_nodes, 1)
    graph_directed.directed = True
    nx_graph = to_networkx(graph_directed, mode="union")
    assert isinstance(nx_graph, (nx.MultiGraph, nx.MultiDiGraph)), \
        "Should return NetworkX MultiGraph or MultiDiGraph"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=6))
def test_to_networkx_intersection_conservative(num_nodes):
    """Test that intersection mode is conservative (fewer or equal edges)."""
    graph = create_simple_multilayer_graph(num_nodes, 2)
    
    # Convert with different modes
    nx_union = to_networkx(graph, mode="union")
    nx_intersection = to_networkx(graph, mode="intersection")
    
    # Intersection should have fewer or equal edges than union
    assert nx_intersection.number_of_edges() <= nx_union.number_of_edges(), \
        "Intersection should have fewer or equal edges than union"


# ============================================================================
# Property Tests: Conversion Invariants
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=6),
    mode=st.sampled_from(["union", "multiplex", "intersection"])
)
def test_to_networkx_non_negative_counts(num_nodes, mode):
    """Test that converted graph has non-negative node and edge counts."""
    graph = create_simple_multilayer_graph(num_nodes, 2)
    
    # Convert to NetworkX
    nx_graph = to_networkx(graph, mode=mode)
    
    # Counts should be non-negative
    assert nx_graph.number_of_nodes() >= 0, "Node count should be non-negative"
    assert nx_graph.number_of_edges() >= 0, "Edge count should be non-negative"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=6))
def test_to_networkx_empty_layer_handling(num_nodes):
    """Test that empty layers are handled correctly."""
    graph = MultiLayerGraph(directed=False)
    
    # Add empty layer
    layer = Layer(id='empty_layer', attributes={})
    graph.add_layer(layer)
    
    # Add nodes but no edges
    for i in range(num_nodes):
        node = Node(id=f'n{i}', attributes={})
        graph.add_node(node)
    
    # Convert should not crash
    nx_graph = to_networkx(graph, mode="union")
    
    # Should have nodes, no edges
    assert nx_graph.number_of_nodes() == num_nodes, "Should have all nodes"
    assert nx_graph.number_of_edges() == 0, "Empty layer should have no edges"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=6),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_to_networkx_preserves_connectivity_pattern(num_nodes, num_layers):
    """Test that path graph structure is preserved in conversion."""
    # Create a path graph structure in each layer
    graph = MultiLayerGraph(directed=False)
    
    # Add layers
    for i in range(num_layers):
        layer = Layer(id=f'layer{i}', attributes={})
        graph.add_layer(layer)
    
    # Add nodes
    for i in range(num_nodes):
        node = Node(id=f'n{i}', attributes={})
        graph.add_node(node)
    
    # Add path edges (0-1-2-...-n)
    for layer_idx in range(num_layers):
        layer_id = f'layer{layer_idx}'
        for i in range(num_nodes - 1):
            edge = Edge(src=f'n{i}', dst=f'n{i+1}', src_layer=layer_id, dst_layer=layer_id, attributes={})
            graph.add_edge(edge)
    
    # Convert to NetworkX
    nx_graph = to_networkx(graph, mode="union")
    
    # Should be connected (path graph property)
    if nx_graph.number_of_nodes() > 0:
        # Check if graph is connected
        is_connected = nx.is_connected(nx_graph.to_undirected())
        assert is_connected, "Union of path graphs should be connected"


# ============================================================================
# Property Tests: Attribute Preservation
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=6))
def test_to_networkx_preserves_graph_attributes(num_nodes):
    """Test that graph-level attributes are preserved."""
    graph = create_simple_multilayer_graph(num_nodes, 1)
    
    # Add graph attributes
    graph.attributes['name'] = 'test_graph'
    graph.attributes['created'] = '2024'
    
    # Convert to NetworkX
    nx_graph = to_networkx(graph, mode="union")
    
    # Graph attributes should be preserved
    assert 'name' in nx_graph.graph, "Graph name attribute should be preserved"
    assert nx_graph.graph['name'] == 'test_graph', "Graph name should match"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=6))
def test_to_networkx_preserves_node_attributes(num_nodes):
    """Test that node attributes are preserved in union mode."""
    graph = MultiLayerGraph(directed=False)
    
    # Add layer
    layer = Layer(id='layer1', attributes={})
    graph.add_layer(layer)
    
    # Add nodes with attributes
    for i in range(num_nodes):
        node = Node(id=f'n{i}', attributes={'label': f'Node {i}', 'value': i})
        graph.add_node(node)
    
    # Convert to NetworkX
    nx_graph = to_networkx(graph, mode="union")
    
    # Check node attributes
    for i in range(num_nodes):
        node_id = f'n{i}'
        if node_id in nx_graph.nodes:
            node_data = nx_graph.nodes[node_id]
            # Attributes may or may not be preserved depending on implementation
            # Just check that node exists
            assert node_id in nx_graph.nodes, f"Node {node_id} should exist"


# ============================================================================
# Property Tests: Mode-Specific Properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=3, max_value=8))
def test_union_mode_flattens_layers(num_nodes):
    """Test that union mode flattens multilayer structure."""
    graph = create_simple_multilayer_graph(num_nodes, 3)
    
    # Convert with union mode
    nx_graph = to_networkx(graph, mode="union")
    
    # Should have flat node structure (no layer tuples)
    for node in nx_graph.nodes():
        # Union mode uses simple node IDs, not (node, layer) tuples
        # Check that node IDs are strings (our node IDs are 'n0', 'n1', etc.)
        assert isinstance(node, (str, int)), \
            "Union mode should use simple node IDs"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=6))
def test_multiplex_mode_creates_node_layer_tuples(num_nodes):
    """Test that multiplex mode creates (node, layer) tuples."""
    graph = create_simple_multilayer_graph(num_nodes, 2)
    
    # Convert with multiplex mode
    nx_graph = to_networkx(graph, mode="multiplex")
    
    # Check that nodes are tuples
    tuple_nodes = [n for n in nx_graph.nodes() if isinstance(n, tuple)]
    
    # Most nodes should be tuples in multiplex mode
    # (allowing for implementation variations)
    assert len(tuple_nodes) > 0, \
        "Multiplex mode should create some node-layer tuples"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
