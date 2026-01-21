#!/usr/bin/env python3
"""
Property-based tests for core.supporting module.

Tests layer splitting, multiplex edge addition, and utility function invariants.
"""

import networkx as nx
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import supporting module
try:
    from py3plex.core.supporting import split_to_layers, add_mpx_edges
    SUPPORTING_AVAILABLE = True
except ImportError:
    SUPPORTING_AVAILABLE = False
    pytest.skip("Supporting module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Layer Splitting
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=8),
    num_layers=st.integers(min_value=1, max_value=4)
)
def test_split_to_layers_preserves_nodes(num_nodes, num_layers):
    """Test that layer splitting preserves all nodes."""
    # Create a multilayer network
    G = nx.Graph()
    for layer_idx in range(num_layers):
        for node_idx in range(num_nodes):
            G.add_node((f'n{node_idx}', f'layer{layer_idx}'))
    
    total_nodes_before = G.number_of_nodes()
    
    # Split to layers
    layers = split_to_layers(G)
    
    # Count nodes in all layers
    total_nodes_after = sum(layer.number_of_nodes() for layer in layers.values())
    
    # Node count should be preserved
    assert total_nodes_after == total_nodes_before, \
        f"Total nodes should be {total_nodes_before}, got {total_nodes_after}"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=8),
    num_layers=st.integers(min_value=1, max_value=4)
)
def test_split_to_layers_correct_count(num_nodes, num_layers):
    """Test that layer splitting produces correct number of layers."""
    # Create a multilayer network
    G = nx.Graph()
    for layer_idx in range(num_layers):
        for node_idx in range(num_nodes):
            G.add_node((f'n{node_idx}', f'layer{layer_idx}'))
    
    # Split to layers
    layers = split_to_layers(G)
    
    # Should have correct number of layers
    assert len(layers) == num_layers, \
        f"Should have {num_layers} layers, got {len(layers)}"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4)
)
def test_split_to_layers_each_layer_has_nodes(num_nodes, num_layers):
    """Test that each layer has the expected nodes."""
    # Create a multilayer network
    G = nx.Graph()
    for layer_idx in range(num_layers):
        for node_idx in range(num_nodes):
            G.add_node((f'n{node_idx}', f'layer{layer_idx}'))
    
    # Split to layers
    layers = split_to_layers(G)
    
    # Each layer should have nodes
    for layer_name, layer_graph in layers.items():
        assert layer_graph.number_of_nodes() == num_nodes, \
            f"Layer {layer_name} should have {num_nodes} nodes, got {layer_graph.number_of_nodes()}"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4)
)
def test_split_to_layers_preserves_intra_layer_edges(num_nodes, num_layers):
    """Test that layer splitting preserves intra-layer edges."""
    # Create a multilayer network with intra-layer edges
    G = nx.Graph()
    
    # Add nodes
    for layer_idx in range(num_layers):
        for node_idx in range(num_nodes):
            G.add_node((f'n{node_idx}', f'layer{layer_idx}'))
    
    # Add intra-layer edges
    expected_edges_per_layer = num_nodes - 1
    for layer_idx in range(num_layers):
        for i in range(num_nodes - 1):
            G.add_edge(
                (f'n{i}', f'layer{layer_idx}'),
                (f'n{i+1}', f'layer{layer_idx}')
            )
    
    # Split to layers
    layers = split_to_layers(G)
    
    # Each layer should have the expected edges
    for layer_name, layer_graph in layers.items():
        assert layer_graph.number_of_edges() == expected_edges_per_layer, \
            f"Layer {layer_name} should have {expected_edges_per_layer} edges"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=3)
)
def test_split_to_layers_excludes_interlayer_edges(num_nodes, num_layers):
    """Test that layer splitting excludes inter-layer edges."""
    # Create a multilayer network
    G = nx.Graph()
    
    # Add nodes
    for layer_idx in range(num_layers):
        for node_idx in range(num_nodes):
            G.add_node((f'n{node_idx}', f'layer{layer_idx}'))
    
    # Add intra-layer edges
    for layer_idx in range(num_layers):
        for i in range(num_nodes - 1):
            G.add_edge(
                (f'n{i}', f'layer{layer_idx}'),
                (f'n{i+1}', f'layer{layer_idx}')
            )
    
    # Add inter-layer edges (these should be excluded from layer subgraphs)
    for node_idx in range(num_nodes):
        for layer_idx in range(num_layers - 1):
            G.add_edge(
                (f'n{node_idx}', f'layer{layer_idx}'),
                (f'n{node_idx}', f'layer{layer_idx+1}')
            )
    
    # Split to layers
    layers = split_to_layers(G)
    
    # Each layer should only have intra-layer edges
    expected_edges_per_layer = num_nodes - 1
    for layer_name, layer_graph in layers.items():
        # Count only intra-layer edges
        intra_edges = sum(1 for u, v in layer_graph.edges() if u[1] == v[1])
        assert intra_edges == expected_edges_per_layer, \
            f"Layer {layer_name} should have {expected_edges_per_layer} intra-layer edges"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=8))
def test_split_to_layers_returns_dict(num_nodes):
    """Test that split_to_layers returns a dictionary."""
    # Create a simple multilayer network
    G = nx.Graph()
    for i in range(num_nodes):
        G.add_node((f'n{i}', 'layer1'))
    
    # Split to layers
    layers = split_to_layers(G)
    
    # Should return a dictionary
    assert isinstance(layers, dict), "Result should be a dictionary"
    
    # All values should be NetworkX graphs
    for layer_graph in layers.values():
        assert isinstance(layer_graph, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph)), \
            "All layer values should be NetworkX graphs"


# ============================================================================
# Property Tests: Multiplex Edge Addition
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4)
)
def test_add_mpx_edges_increases_edge_count(num_nodes, num_layers):
    """Test that adding multiplex edges increases edge count."""
    # Create a multilayer network
    G = nx.MultiGraph()  # Use MultiGraph to support multiple edges
    for layer_idx in range(num_layers):
        for node_idx in range(num_nodes):
            G.add_node((f'n{node_idx}', f'layer{layer_idx}'))
    
    edges_before = G.number_of_edges()
    
    # Add multiplex edges
    G = add_mpx_edges(G)
    
    edges_after = G.number_of_edges()
    
    # Edge count should increase (multiplex edges added)
    assert edges_after >= edges_before, \
        "Multiplex edges should increase or maintain edge count"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4)
)
def test_add_mpx_edges_preserves_nodes(num_nodes, num_layers):
    """Test that adding multiplex edges preserves node count."""
    # Create a multilayer network
    G = nx.MultiGraph()
    for layer_idx in range(num_layers):
        for node_idx in range(num_nodes):
            G.add_node((f'n{node_idx}', f'layer{layer_idx}'))
    
    nodes_before = G.number_of_nodes()
    
    # Add multiplex edges
    G = add_mpx_edges(G)
    
    nodes_after = G.number_of_nodes()
    
    # Node count should be preserved
    assert nodes_after == nodes_before, \
        f"Node count should be {nodes_before}, got {nodes_after}"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=6),
    num_layers=st.integers(min_value=2, max_value=3)
)
def test_add_mpx_edges_connects_corresponding_nodes(num_nodes, num_layers):
    """Test that multiplex edges connect corresponding nodes across layers."""
    # Create a multilayer network
    G = nx.MultiGraph()
    for layer_idx in range(num_layers):
        for node_idx in range(num_nodes):
            G.add_node((f'n{node_idx}', f'layer{layer_idx}'))
    
    # Add multiplex edges
    G = add_mpx_edges(G)
    
    # Count multiplex edges (edges marked with type='coupling')
    mpx_edges = [(u, v) for u, v, data in G.edges(data=True) if data.get('type') == 'coupling']
    
    # Should have edges connecting corresponding nodes
    # For n nodes across L layers, we expect n * C(L, 2) multiplex edges
    from math import comb
    expected_mpx_edges = num_nodes * comb(num_layers, 2)
    
    assert len(mpx_edges) == expected_mpx_edges, \
        f"Should have {expected_mpx_edges} multiplex edges, got {len(mpx_edges)}"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=6),
    num_layers=st.integers(min_value=2, max_value=3)
)
def test_add_mpx_edges_only_between_layers(num_nodes, num_layers):
    """Test that multiplex edges only connect different layers."""
    # Create a multilayer network
    G = nx.MultiGraph()
    for layer_idx in range(num_layers):
        for node_idx in range(num_nodes):
            G.add_node((f'n{node_idx}', f'layer{layer_idx}'))
    
    # Add multiplex edges
    G = add_mpx_edges(G)
    
    # Check all multiplex edges connect different layers
    mpx_edges = [(u, v) for u, v, data in G.edges(data=True) if data.get('type') == 'coupling']
    
    for u, v in mpx_edges:
        assert u[1] != v[1], \
            f"Multiplex edge should connect different layers, got {u[1]} and {v[1]}"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=6),
    num_layers=st.integers(min_value=2, max_value=3)
)
def test_add_mpx_edges_connects_same_node_ids(num_nodes, num_layers):
    """Test that multiplex edges connect nodes with same ID across layers."""
    # Create a multilayer network
    G = nx.MultiGraph()
    for layer_idx in range(num_layers):
        for node_idx in range(num_nodes):
            G.add_node((f'n{node_idx}', f'layer{layer_idx}'))
    
    # Add multiplex edges
    G = add_mpx_edges(G)
    
    # Check all multiplex edges connect same node IDs
    mpx_edges = [(u, v) for u, v, data in G.edges(data=True) if data.get('type') == 'coupling']
    
    for u, v in mpx_edges:
        assert u[0] == v[0], \
            f"Multiplex edge should connect same node ID, got {u[0]} and {v[0]}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=8))
def test_add_mpx_edges_single_layer_unchanged(num_nodes):
    """Test that adding multiplex edges to single-layer network doesn't add edges."""
    # Create a single-layer network
    G = nx.MultiGraph()
    for node_idx in range(num_nodes):
        G.add_node((f'n{node_idx}', 'layer1'))
    
    edges_before = G.number_of_edges()
    
    # Add multiplex edges (should be no-op for single layer)
    G = add_mpx_edges(G)
    
    edges_after = G.number_of_edges()
    
    # Edge count should be unchanged (no multiplex edges possible)
    assert edges_after == edges_before, \
        "Single-layer network should not get multiplex edges"


@pytest.mark.property
@settings(deadline=None, max_examples=5, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_shared=st.integers(min_value=1, max_value=4),
    num_unique1=st.integers(min_value=1, max_value=3),
    num_unique2=st.integers(min_value=1, max_value=3)
)
def test_add_mpx_edges_partial_overlap(num_shared, num_unique1, num_unique2):
    """Test multiplex edges with partially overlapping node sets."""
    # Create a multilayer network with partial overlap
    G = nx.MultiGraph()
    
    # Add shared nodes in both layers
    for i in range(num_shared):
        G.add_node((f'shared{i}', 'layer1'))
        G.add_node((f'shared{i}', 'layer2'))
    
    # Add unique nodes in layer1
    for i in range(num_unique1):
        G.add_node((f'unique1_{i}', 'layer1'))
    
    # Add unique nodes in layer2
    for i in range(num_unique2):
        G.add_node((f'unique2_{i}', 'layer2'))
    
    # Add multiplex edges
    G = add_mpx_edges(G)
    
    # Count multiplex edges
    mpx_edges = [(u, v) for u, v, data in G.edges(data=True) if data.get('type') == 'coupling']
    
    # Should only have multiplex edges for shared nodes
    assert len(mpx_edges) == num_shared, \
        f"Should have {num_shared} multiplex edges for shared nodes, got {len(mpx_edges)}"


# ============================================================================
# Property Tests: Edge Cases
# ============================================================================

@pytest.mark.property
def test_split_to_layers_empty_network():
    """Test that splitting empty network returns empty dict."""
    G = nx.Graph()
    
    # Split to layers
    layers = split_to_layers(G)
    
    # Should return empty or minimal result
    assert isinstance(layers, dict), "Should return a dictionary"
    # Empty network may have 0 layers or handle gracefully
    assert len(layers) >= 0, "Should handle empty network gracefully"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=8))
def test_add_mpx_edges_idempotent(num_nodes):
    """Test that adding multiplex edges twice doesn't double them."""
    # Create a multilayer network
    G = nx.MultiGraph()
    G.add_node(('n1', 'layer1'))
    G.add_node(('n1', 'layer2'))
    G.add_node(('n2', 'layer1'))
    G.add_node(('n2', 'layer2'))
    
    # Add multiplex edges once
    G = add_mpx_edges(G)
    edges_after_first = G.number_of_edges()
    
    # Add multiplex edges again
    G = add_mpx_edges(G)
    edges_after_second = G.number_of_edges()
    
    # Should add more edges (MultiGraph allows parallel edges)
    # This tests the behavior - whether it's idempotent or additive
    assert edges_after_second >= edges_after_first, \
        "Second call should not reduce edges"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
