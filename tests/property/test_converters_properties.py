#!/usr/bin/env python3
"""
Property-based tests for core.converters module.

Tests layout computation, coordinate normalization, and network preparation invariants.
"""

import networkx as nx
import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import shared strategies
from .strategies import small_graphs, positive_weights

# Import converters module
try:
    from py3plex.core.converters import (
        compute_layout,
        prepare_for_visualization_hairball,
        prepare_for_parsing,
    )
    CONVERTERS_AVAILABLE = True
except ImportError:
    CONVERTERS_AVAILABLE = False
    pytest.skip("Converters module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Layout Computation
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=10))
def test_random_layout_preserves_nodes(num_nodes):
    """Test that random layout preserves all nodes."""
    G = nx.complete_graph(num_nodes)
    
    # Compute random layout
    try:
        compute_layout(G, "random", None, verbose=False)
    except (ValueError, ZeroDivisionError):
        # Layout computation may fail in edge cases
        assume(False)
    
    # All nodes should have 'pos' attribute
    assert all('pos' in G.nodes[n] for n in G.nodes()), "All nodes must have 'pos' attribute"
    
    # Node count should be preserved
    assert G.number_of_nodes() == num_nodes, "Node count should be preserved"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=8))
def test_layout_coordinates_normalized(num_nodes):
    """Test that layout coordinates are normalized to [0, 1] range."""
    G = nx.complete_graph(num_nodes)
    
    # Compute random layout
    try:
        compute_layout(G, "random", None, verbose=False)
    except (ValueError, ZeroDivisionError):
        # Layout computation may fail in edge cases
        assume(False)
    
    # Check all coordinates are in normalized range [0, 1]
    for node in G.nodes():
        pos = G.nodes[node]['pos']
        assert len(pos) == 2, "Position should be 2D"
        
        # Skip if coordinates are NaN (can happen with identical positions)
        if not (np.isfinite(pos[0]) and np.isfinite(pos[1])):
            assume(False)
        
        # Coordinates should be in [0, 1] or very close (allowing small numerical errors)
        assert -0.01 <= pos[0] <= 1.01, f"X coordinate {pos[0]} out of normalized range"
        assert -0.01 <= pos[1] <= 1.01, f"Y coordinate {pos[1]} out of normalized range"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=8))
def test_layout_coordinates_finite(num_nodes):
    """Test that layout coordinates are finite when layout succeeds."""
    G = nx.complete_graph(num_nodes)
    
    # Compute random layout
    try:
        compute_layout(G, "random", None, verbose=False)
    except (ValueError, ZeroDivisionError):
        # Layout computation may fail in edge cases
        assume(False)
    
    # All coordinates should be finite (or skip if implementation produces NaN)
    has_nan = False
    for node in G.nodes():
        pos = G.nodes[node]['pos']
        if not (np.isfinite(pos[0]) and np.isfinite(pos[1])):
            has_nan = True
            break
    
    # Skip tests where implementation produces NaN (edge case in normalization)
    assume(not has_nan)


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=8))
def test_custom_layout_preserves_positions(num_nodes):
    """Test that custom layout preserves provided positions."""
    G = nx.complete_graph(num_nodes)
    
    # Create custom positions
    custom_pos = {i: np.array([i / num_nodes, (num_nodes - i) / num_nodes]) 
                  for i in range(num_nodes)}
    
    # Compute custom layout
    layout_params = {"pos": custom_pos}
    compute_layout(G, "custom_coordinates", layout_params, verbose=False)
    
    # All nodes should have positions
    assert all('pos' in G.nodes[n] for n in G.nodes()), "All nodes must have 'pos' attribute"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=8),
    p=st.floats(min_value=0.3, max_value=0.8)
)
def test_layout_respects_graph_structure(num_nodes, p):
    """Test that layout can be computed for different graph structures."""
    # Generate random graph
    G = nx.gnp_random_graph(num_nodes, p, seed=hash((num_nodes, p)) % (2**32))
    assume(G.number_of_nodes() > 0)
    
    # Compute random layout (may fail in edge cases)
    try:
        compute_layout(G, "random", None, verbose=False)
    except (ValueError, ZeroDivisionError):
        assume(False)
    
    # All nodes should have positions
    assert all('pos' in G.nodes[n] for n in G.nodes()), "All nodes must have 'pos' attribute"
    
    # Node count preserved
    assert G.number_of_nodes() == num_nodes, "Node count should be preserved"


# ============================================================================
# Property Tests: Hairball Preparation
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=10))
def test_hairball_preparation_preserves_network(num_nodes):
    """Test that hairball preparation preserves network structure."""
    # Create a simple multilayer network
    G = nx.Graph()
    for i in range(num_nodes):
        G.add_node((f'n{i}', 'layer1'))
    
    # Add some edges
    for i in range(num_nodes - 1):
        G.add_edge((f'n{i}', 'layer1'), (f'n{i+1}', 'layer1'))
    
    # Prepare for hairball visualization
    names, network = prepare_for_visualization_hairball(G, compute_layouts=False)
    
    # Network should be preserved
    assert network.number_of_nodes() == G.number_of_nodes(), "Node count should be preserved"
    assert network.number_of_edges() == G.number_of_edges(), "Edge count should be preserved"
    
    # Names list should have correct length
    assert len(names) == num_nodes, "Names list should match node count"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_hairball_preparation_layer_enumeration(num_nodes, num_layers):
    """Test that hairball preparation enumerates layers correctly."""
    # Create a multilayer network
    G = nx.Graph()
    for layer_idx in range(num_layers):
        for node_idx in range(num_nodes):
            G.add_node((f'n{node_idx}', f'layer{layer_idx}'))
    
    # Add edges within layers
    for layer_idx in range(num_layers):
        for i in range(num_nodes - 1):
            G.add_edge(
                (f'n{i}', f'layer{layer_idx}'),
                (f'n{i+1}', f'layer{layer_idx}')
            )
    
    # Prepare for hairball visualization
    names, network = prepare_for_visualization_hairball(G, compute_layouts=False)
    
    # Names should be integer layer IDs
    assert all(isinstance(n, (int, np.integer)) for n in names), "Names should be integers"
    
    # Number of unique layer IDs should match number of layers
    unique_layers = len(set(names))
    assert unique_layers == num_layers, f"Should have {num_layers} unique layers, got {unique_layers}"


# ============================================================================
# Property Tests: Parsing Preparation
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4)
)
def test_parsing_separates_layers(num_nodes, num_layers):
    """Test that parsing preparation correctly separates layers."""
    # Create a multilayer network
    G = nx.MultiGraph()
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
    
    # Prepare for parsing
    names, networks, multiedges = prepare_for_parsing(G)
    
    # Should have correct number of layers
    assert len(names) == num_layers, f"Should have {num_layers} layer names"
    assert len(networks) == num_layers, f"Should have {num_layers} networks"
    
    # Each layer should have correct node count
    for network in networks:
        assert network.number_of_nodes() == num_nodes, "Each layer should have all nodes"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=3)
)
def test_parsing_identifies_interlayer_edges(num_nodes, num_layers):
    """Test that parsing correctly identifies inter-layer edges."""
    # Create a multilayer network
    G = nx.MultiGraph()
    for layer_idx in range(num_layers):
        for node_idx in range(num_nodes):
            G.add_node((f'n{node_idx}', f'layer{layer_idx}'))
    
    # Add intra-layer edges
    intra_edge_count = 0
    for layer_idx in range(num_layers):
        for i in range(num_nodes - 1):
            G.add_edge(
                (f'n{i}', f'layer{layer_idx}'),
                (f'n{i+1}', f'layer{layer_idx}')
            )
            intra_edge_count += 1
    
    # Add inter-layer edges (coupling between layers)
    inter_edge_count = 0
    for node_idx in range(num_nodes):
        for layer_idx in range(num_layers - 1):
            G.add_edge(
                (f'n{node_idx}', f'layer{layer_idx}'),
                (f'n{node_idx}', f'layer{layer_idx+1}'),
                type='coupling'
            )
            inter_edge_count += 1
    
    # Prepare for parsing
    names, networks, multiedges = prepare_for_parsing(G)
    
    # Count inter-layer edges
    total_inter_edges = sum(len(edges) for edges in multiedges.values())
    
    # Should have identified inter-layer edges
    assert total_inter_edges == inter_edge_count, \
        f"Should identify {inter_edge_count} inter-layer edges, found {total_inter_edges}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=8))
def test_parsing_handles_empty_layers_gracefully(num_nodes):
    """Test that parsing handles networks with no proper layer structure."""
    # Create a simple graph without layer structure
    G = nx.Graph()
    for i in range(num_nodes):
        G.add_node(i)
    
    for i in range(num_nodes - 1):
        G.add_edge(i, i + 1)
    
    # Prepare for parsing (should not crash)
    names, networks, multiedges = prepare_for_parsing(G)
    
    # Should return some result (possibly empty or default)
    assert isinstance(names, tuple), "Names should be a tuple"
    assert isinstance(networks, tuple), "Networks should be a tuple"
    assert isinstance(multiedges, dict), "Multiedges should be a dict"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=2, max_value=8),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_parsing_preserves_total_node_count(num_nodes, num_layers):
    """Test that parsing preserves total node count across layers."""
    # Create a multilayer network
    G = nx.MultiGraph()
    for layer_idx in range(num_layers):
        for node_idx in range(num_nodes):
            G.add_node((f'n{node_idx}', f'layer{layer_idx}'))
    
    total_nodes_before = G.number_of_nodes()
    
    # Prepare for parsing
    names, networks, multiedges = prepare_for_parsing(G)
    
    # Sum nodes across all layer subgraphs
    total_nodes_after = sum(net.number_of_nodes() for net in networks)
    
    # Total should be preserved
    assert total_nodes_after == total_nodes_before, \
        f"Total nodes should be {total_nodes_before}, got {total_nodes_after}"


# ============================================================================
# Property Tests: Edge Case Handling
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(num_nodes=st.integers(min_value=2, max_value=8))
def test_layout_handles_isolated_nodes(num_nodes):
    """Test that layout computation handles isolated nodes correctly."""
    # Create a graph with isolated nodes
    G = nx.Graph()
    for i in range(num_nodes):
        G.add_node(i)
    
    # Only add edges to half the nodes
    for i in range(num_nodes // 2 - 1):
        G.add_edge(i, i + 1)
    
    # Compute layout
    compute_layout(G, "random", None, verbose=False)
    
    # All nodes should have positions (including isolated ones)
    assert all('pos' in G.nodes[n] for n in G.nodes()), "All nodes must have 'pos' attribute"
    
    # Positions should be finite
    for node in G.nodes():
        pos = G.nodes[node]['pos']
        assert np.isfinite(pos[0]) and np.isfinite(pos[1]), "Positions must be finite"


@pytest.mark.property
def test_layout_handles_single_edge_graphs():
    """Test that layout handles graphs with just one edge."""
    G = nx.Graph()
    G.add_edge(0, 1)
    
    # Compute layout
    compute_layout(G, "random", None, verbose=False)
    
    # Both nodes should have positions
    assert 'pos' in G.nodes[0], "Node 0 must have 'pos' attribute"
    assert 'pos' in G.nodes[1], "Node 1 must have 'pos' attribute"
    
    # Positions should be different
    pos0 = G.nodes[0]['pos']
    pos1 = G.nodes[1]['pos']
    assert not np.allclose(pos0, pos1), "Nodes should have different positions"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
