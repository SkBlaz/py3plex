"""
Tests for pymnet style multilayer visualization.

This test module validates the pymnet style visualization implementation:
- MultilayerGraph conversion from various formats
- Deterministic layout with fixed seed
- Headless rendering (Matplotlib Agg backend)
- API return values (fig, ax, handles, positions)
- Styling options

The tests ensure that the pymnet style visualization works correctly
and produces deterministic, reproducible output.
"""

import logging
import pytest

logger = logging.getLogger()
logger.level = logging.DEBUG

# Set up Matplotlib for headless testing
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available")

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("networkx not available")

try:
    from py3plex.core import multinet
    PY3PLEX_AVAILABLE = True
except ImportError:
    PY3PLEX_AVAILABLE = False
    logger.warning("py3plex core not available")

try:
    from py3plex.visualization.pymnet_style import (
        MultilayerGraph,
        to_multilayer_graph,
        draw_multilayer_pymnet,
        _from_dict_of_graphs,
        _from_nx_graph_with_layers,
        _from_edge_list,
        _compute_layout,
    )
    PYMNET_STYLE_AVAILABLE = True
except ImportError as e:
    PYMNET_STYLE_AVAILABLE = False
    logger.warning(f"pymnet_style not available: {e}")

DEPENDENCIES_AVAILABLE = (
    MATPLOTLIB_AVAILABLE and 
    NETWORKX_AVAILABLE and 
    PY3PLEX_AVAILABLE and 
    PYMNET_STYLE_AVAILABLE
)


# ============================================================================
# Test Fixtures and Helpers
# ============================================================================

def create_simple_multilayer_dict():
    """Create a simple multilayer network as dict of NetworkX graphs."""
    layer_a = nx.Graph()
    layer_a.add_edges_from([('A', 'B'), ('B', 'C')])
    
    layer_b = nx.Graph()
    layer_b.add_edges_from([('A', 'C'), ('C', 'D')])
    
    return {'layer_A': layer_a, 'layer_B': layer_b}


def create_py3plex_network():
    """Create a simple multilayer network using py3plex."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes to layer A
    network.add_nodes([
        {'source': 'node1', 'type': 'A'},
        {'source': 'node2', 'type': 'A'},
        {'source': 'node3', 'type': 'A'},
    ], input_type='dict')
    
    # Add edges to layer A
    network.add_edges([
        {'source': 'node1', 'target': 'node2', 'source_type': 'A', 'target_type': 'A'},
        {'source': 'node2', 'target': 'node3', 'source_type': 'A', 'target_type': 'A'},
    ], input_type='dict')
    
    # Add nodes to layer B
    network.add_nodes([
        {'source': 'node1', 'type': 'B'},
        {'source': 'node2', 'type': 'B'},
        {'source': 'node3', 'type': 'B'},
    ], input_type='dict')
    
    # Add edges to layer B
    network.add_edges([
        {'source': 'node1', 'target': 'node3', 'source_type': 'B', 'target_type': 'B'},
    ], input_type='dict')
    
    return network


def create_edge_list():
    """Create a simple edge list for multilayer network."""
    return [
        ('X', 'layer1', 'Y', 'layer1'),
        ('Y', 'layer1', 'Z', 'layer1'),
        ('X', 'layer2', 'Z', 'layer2'),
        ('X', 'layer1', 'X', 'layer2'),  # Inter-layer edge
    ]


# ============================================================================
# MultilayerGraph Conversion Tests
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_to_multilayer_graph_from_dict():
    """Test conversion from dict of NetworkX graphs."""
    layer_dict = create_simple_multilayer_dict()
    mlg = to_multilayer_graph(layer_dict)
    
    assert isinstance(mlg, MultilayerGraph)
    assert set(mlg.layers) == {'layer_A', 'layer_B'}
    assert 'A' in mlg.nodes['layer_A']
    assert 'B' in mlg.nodes['layer_A']
    assert ('A', 'B') in mlg.intra_edges['layer_A'] or ('B', 'A') in mlg.intra_edges['layer_A']


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_to_multilayer_graph_from_edge_list():
    """Test conversion from edge list."""
    edges = create_edge_list()
    mlg = to_multilayer_graph(edges)
    
    assert isinstance(mlg, MultilayerGraph)
    assert set(mlg.layers) == {'layer1', 'layer2'}
    assert 'X' in mlg.nodes['layer1']
    assert len(mlg.inter_edges) == 1  # One inter-layer edge


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_to_multilayer_graph_from_nx_with_layer_attribute():
    """Test conversion from NetworkX graph with layer attributes."""
    G = nx.Graph()
    G.add_node('n1', layer='L1')
    G.add_node('n2', layer='L1')
    G.add_node('n3', layer='L2')
    G.add_edge('n1', 'n2')  # Intra-layer
    G.add_edge('n1', 'n3')  # Inter-layer
    
    mlg = to_multilayer_graph(G)
    
    assert isinstance(mlg, MultilayerGraph)
    assert set(mlg.layers) == {'L1', 'L2'}
    assert 'n1' in mlg.nodes['L1']
    assert 'n3' in mlg.nodes['L2']
    assert len(mlg.inter_edges) >= 1


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_to_multilayer_graph_from_py3plex():
    """Test conversion from py3plex multi_layer_network."""
    network = create_py3plex_network()
    mlg = to_multilayer_graph(network)
    
    assert isinstance(mlg, MultilayerGraph)
    assert set(mlg.layers) == {'A', 'B'}
    assert 'node1' in mlg.nodes['A']
    assert 'node1' in mlg.nodes['B']


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_multilayer_graph_passthrough():
    """Test that MultilayerGraph is passed through unchanged."""
    mlg_original = MultilayerGraph(
        layers=['A', 'B'],
        nodes={'A': {'n1', 'n2'}, 'B': {'n1', 'n2'}},
        intra_edges={'A': [('n1', 'n2')], 'B': []},
        inter_edges=[('n1', 'A', 'n1', 'B')]
    )
    
    mlg_result = to_multilayer_graph(mlg_original)
    
    assert mlg_result is mlg_original


# ============================================================================
# Layout Computation Tests
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_compute_layout_spring():
    """Test spring layout computation."""
    mlg = MultilayerGraph(
        layers=['A'],
        nodes={'A': {'n1', 'n2', 'n3'}},
        intra_edges={'A': [('n1', 'n2'), ('n2', 'n3')]},
        inter_edges=[]
    )
    
    positions = _compute_layout(mlg, "spring", seed=42)
    
    assert len(positions) == 3
    assert 'n1' in positions
    assert isinstance(positions['n1'], tuple)
    assert len(positions['n1']) == 2


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_compute_layout_deterministic():
    """Test that layout is deterministic with fixed seed."""
    mlg = MultilayerGraph(
        layers=['A'],
        nodes={'A': {'n1', 'n2', 'n3'}},
        intra_edges={'A': [('n1', 'n2'), ('n2', 'n3')]},
        inter_edges=[]
    )
    
    pos1 = _compute_layout(mlg, "spring", seed=42)
    pos2 = _compute_layout(mlg, "spring", seed=42)
    
    # Should be identical with same seed
    for node in pos1:
        assert abs(pos1[node][0] - pos2[node][0]) < 1e-10
        assert abs(pos1[node][1] - pos2[node][1]) < 1e-10


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_compute_layout_all_algorithms():
    """Test all supported layout algorithms."""
    mlg = MultilayerGraph(
        layers=['A'],
        nodes={'A': {'n1', 'n2', 'n3'}},
        intra_edges={'A': [('n1', 'n2'), ('n2', 'n3')]},
        inter_edges=[]
    )
    
    layouts = ["spring", "kamada_kawai", "circular", "spectral"]
    
    for layout in layouts:
        positions = _compute_layout(mlg, layout, seed=42)
        assert len(positions) == 3
        assert all(isinstance(pos, tuple) and len(pos) == 2 for pos in positions.values())


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_compute_layout_custom_callable():
    """Test custom layout function."""
    mlg = MultilayerGraph(
        layers=['A'],
        nodes={'A': {'n1', 'n2', 'n3'}},
        intra_edges={'A': [('n1', 'n2'), ('n2', 'n3')]},
        inter_edges=[]
    )
    
    def custom_layout(G):
        # Simple circular layout
        return nx.circular_layout(G)
    
    positions = _compute_layout(mlg, custom_layout, seed=42)
    
    assert len(positions) == 3


# ============================================================================
# Visualization Rendering Tests
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_basic():
    """Test basic pymnet style visualization."""
    layer_dict = create_simple_multilayer_dict()
    
    fig, ax, handles, positions = draw_multilayer_pymnet(
        layer_dict,
        layout="spring",
        seed=42
    )
    
    assert fig is not None
    assert ax is not None
    assert isinstance(handles, dict)
    assert isinstance(positions, dict)
    
    plt.close(fig)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_return_types():
    """Test that draw_multilayer_pymnet returns correct types."""
    edges = create_edge_list()
    
    fig, ax, handles, positions = draw_multilayer_pymnet(
        edges,
        layout="circular",
        seed=42
    )
    
    # Check return types
    assert isinstance(fig, plt.Figure)
    assert isinstance(ax, plt.Axes)
    assert isinstance(handles, dict)
    assert 'nodes' in handles
    assert 'intra_edges' in handles
    assert 'inter_edges' in handles
    assert isinstance(positions, dict)
    
    plt.close(fig)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_with_py3plex():
    """Test pymnet style visualization with py3plex network."""
    network = create_py3plex_network()
    
    fig, ax, handles, positions = draw_multilayer_pymnet(
        network,
        layout="spring",
        seed=42,
        show_layer_labels=True,
        show_node_labels=False
    )
    
    assert fig is not None
    assert len(positions) > 0
    
    plt.close(fig)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_headless():
    """Test that visualization works in headless mode (Agg backend)."""
    # Backend should already be set to 'Agg' at module level
    current_backend = matplotlib.get_backend()
    assert current_backend == 'Agg'
    
    layer_dict = create_simple_multilayer_dict()
    
    fig, ax, handles, positions = draw_multilayer_pymnet(
        layer_dict,
        layout="spring",
        seed=42
    )
    
    # Should not raise any display-related errors
    assert fig is not None
    
    plt.close(fig)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_deterministic():
    """Test that visualization is deterministic with fixed seed."""
    layer_dict = create_simple_multilayer_dict()
    
    fig1, ax1, handles1, pos1 = draw_multilayer_pymnet(
        layer_dict,
        layout="spring",
        seed=123
    )
    
    fig2, ax2, handles2, pos2 = draw_multilayer_pymnet(
        layer_dict,
        layout="spring",
        seed=123
    )
    
    # Positions should be identical with same seed
    assert set(pos1.keys()) == set(pos2.keys())
    for key in pos1:
        assert abs(pos1[key][0] - pos2[key][0]) < 1e-10
        assert abs(pos1[key][1] - pos2[key][1]) < 1e-10
    
    plt.close(fig1)
    plt.close(fig2)


# ============================================================================
# Styling Options Tests
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_node_coloring():
    """Test different node coloring options."""
    layer_dict = create_simple_multilayer_dict()
    
    # Test "layer" coloring (default)
    fig, ax, handles, pos = draw_multilayer_pymnet(
        layer_dict,
        node_color_by="layer",
        seed=42
    )
    assert fig is not None
    plt.close(fig)
    
    # Test "degree" coloring
    fig, ax, handles, pos = draw_multilayer_pymnet(
        layer_dict,
        node_color_by="degree",
        seed=42
    )
    assert fig is not None
    plt.close(fig)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_custom_node_coloring():
    """Test custom node coloring function."""
    layer_dict = create_simple_multilayer_dict()
    
    def custom_color(node, layer):
        if layer == 'layer_A':
            return 'red'
        else:
            return 'blue'
    
    fig, ax, handles, pos = draw_multilayer_pymnet(
        layer_dict,
        node_color_by=custom_color,
        seed=42
    )
    
    assert fig is not None
    plt.close(fig)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_edge_styling():
    """Test edge styling parameters."""
    edges = create_edge_list()
    
    fig, ax, handles, pos = draw_multilayer_pymnet(
        edges,
        intra_edge_alpha=0.5,
        inter_edge_alpha=0.3,
        intra_edge_width=1.5,
        inter_edge_width=1.0,
        seed=42
    )
    
    assert fig is not None
    assert len(handles['inter_edges']) > 0  # Should have inter-layer edges
    plt.close(fig)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_labels():
    """Test label display options."""
    layer_dict = create_simple_multilayer_dict()
    
    # With both labels
    fig, ax, handles, pos = draw_multilayer_pymnet(
        layer_dict,
        show_node_labels=True,
        show_layer_labels=True,
        seed=42
    )
    assert 'labels' in handles
    assert 'layer_labels' in handles
    plt.close(fig)
    
    # Without labels
    fig, ax, handles, pos = draw_multilayer_pymnet(
        layer_dict,
        show_node_labels=False,
        show_layer_labels=False,
        seed=42
    )
    plt.close(fig)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_layer_gap():
    """Test layer gap parameter."""
    layer_dict = create_simple_multilayer_dict()
    
    # Small gap
    fig1, ax1, h1, pos1 = draw_multilayer_pymnet(
        layer_dict,
        layer_gap=1.0,
        seed=42
    )
    
    # Large gap
    fig2, ax2, h2, pos2 = draw_multilayer_pymnet(
        layer_dict,
        layer_gap=5.0,
        seed=42
    )
    
    # Y positions should differ based on gap
    # (nodes in second layer should be further apart with larger gap)
    assert fig1 is not None
    assert fig2 is not None
    
    plt.close(fig1)
    plt.close(fig2)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_layer_order():
    """Test explicit layer ordering."""
    layer_dict = create_simple_multilayer_dict()
    
    # Default order (alphabetical)
    fig1, ax1, h1, pos1 = draw_multilayer_pymnet(
        layer_dict,
        seed=42
    )
    
    # Reverse order
    fig2, ax2, h2, pos2 = draw_multilayer_pymnet(
        layer_dict,
        layer_order=['layer_B', 'layer_A'],
        seed=42
    )
    
    assert fig1 is not None
    assert fig2 is not None
    
    plt.close(fig1)
    plt.close(fig2)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_figsize():
    """Test figure size parameter."""
    layer_dict = create_simple_multilayer_dict()
    
    fig, ax, handles, pos = draw_multilayer_pymnet(
        layer_dict,
        figsize=(12, 8),
        seed=42
    )
    
    # Check figure size
    width, height = fig.get_size_inches()
    assert abs(width - 12) < 0.1
    assert abs(height - 8) < 0.1
    
    plt.close(fig)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_custom_ax():
    """Test providing custom axes."""
    layer_dict = create_simple_multilayer_dict()
    
    # Create custom figure and axes
    custom_fig, custom_ax = plt.subplots(figsize=(8, 6))
    
    fig, ax, handles, pos = draw_multilayer_pymnet(
        layer_dict,
        ax=custom_ax,
        seed=42
    )
    
    # Should use the provided axes
    assert ax is custom_ax
    assert fig is custom_fig
    
    plt.close(fig)


# ============================================================================
# Edge Case Tests
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_single_layer():
    """Test visualization with single layer."""
    single_layer = {'layer1': nx.karate_club_graph()}
    
    fig, ax, handles, pos = draw_multilayer_pymnet(
        single_layer,
        seed=42
    )
    
    assert fig is not None
    assert len(pos) > 0
    
    plt.close(fig)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_empty_layer():
    """Test visualization with empty layer."""
    layer_dict = {
        'layer_A': nx.Graph(),
        'layer_B': nx.path_graph(3)
    }
    layer_dict['layer_A'].add_node('isolated')
    
    fig, ax, handles, pos = draw_multilayer_pymnet(
        layer_dict,
        seed=42
    )
    
    assert fig is not None
    plt.close(fig)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_disconnected_graph():
    """Test visualization with disconnected graph."""
    G = nx.Graph()
    G.add_edge('A', 'B')
    G.add_edge('C', 'D')  # Disconnected component
    
    layer_dict = {'layer1': G}
    
    fig, ax, handles, pos = draw_multilayer_pymnet(
        layer_dict,
        layout="spring",
        seed=42
    )
    
    assert fig is not None
    plt.close(fig)


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_to_multilayer_graph_invalid_format():
    """Test that invalid format raises appropriate error."""
    from py3plex.exceptions import Py3plexFormatError
    
    invalid_input = "not a valid format"
    
    with pytest.raises(Py3plexFormatError):
        to_multilayer_graph(invalid_input)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_invalid_layout():
    """Test that invalid layout raises error."""
    from py3plex.exceptions import VisualizationError
    
    layer_dict = create_simple_multilayer_dict()
    
    with pytest.raises(VisualizationError):
        draw_multilayer_pymnet(
            layer_dict,
            layout="invalid_layout",
            seed=42
        )


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_draw_multilayer_pymnet_invalid_layer_order():
    """Test that invalid layer_order raises error."""
    from py3plex.exceptions import VisualizationError
    
    layer_dict = create_simple_multilayer_dict()
    
    with pytest.raises(VisualizationError):
        draw_multilayer_pymnet(
            layer_dict,
            layer_order=['nonexistent_layer'],
            seed=42
        )


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_complete_workflow_dict():
    """Test complete workflow from dict to visualization."""
    # Create multilayer network
    layers = {
        'social': nx.karate_club_graph(),
        'work': nx.erdos_renyi_graph(10, 0.3, seed=42)
    }
    
    # Draw with various options
    fig, ax, handles, pos = draw_multilayer_pymnet(
        layers,
        layout="spring",
        seed=42,
        layer_gap=3.0,
        node_size=100,
        show_layer_labels=True,
        node_color_by="layer"
    )
    
    assert fig is not None
    assert len(handles['nodes']) == 2  # Two layers
    
    plt.close(fig)


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="Dependencies not available")
def test_complete_workflow_py3plex():
    """Test complete workflow from py3plex to visualization."""
    network = create_py3plex_network()
    
    fig, ax, handles, pos = draw_multilayer_pymnet(
        network,
        layout="circular",
        seed=42,
        show_node_labels=True,
        show_layer_labels=True
    )
    
    assert fig is not None
    plt.close(fig)


# ============================================================================
# Run tests standalone
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("TESTING PYMNET STYLE VISUALIZATION")
    print("=" * 70)
    
    if not DEPENDENCIES_AVAILABLE:
        print("\nSkipping tests: Required dependencies not available")
        print(f"  Matplotlib: {MATPLOTLIB_AVAILABLE}")
        print(f"  NetworkX: {NETWORKX_AVAILABLE}")
        print(f"  Py3plex: {PY3PLEX_AVAILABLE}")
        print(f"  Pymnet Style: {PYMNET_STYLE_AVAILABLE}")
        exit(0)
    
    # Get all test functions
    test_functions = [obj for name, obj in globals().items() 
                     if name.startswith('test_') and callable(obj)]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        test_name = test_func.__name__
        try:
            print(f"\nRunning {test_name}...", end=" ")
            test_func()
            print("✓ PASSED")
            passed += 1
        except Exception as e:
            print(f"✗ FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_functions)} total")
    print("=" * 70)
    
    exit(0 if failed == 0 else 1)
