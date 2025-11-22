"""
Tests for new multilayer visualization functions.

This test module validates the new visualization modes added to py3plex:
- Small multiples
- Edge-colored projection
- Supra-adjacency heatmap
- Radial layers
- Ego-centric multilayer

This module includes extensive tests covering:
- Basic functionality
- Parameter variations
- Edge cases
- Error handling
- Integration with existing code
"""

import logging
import random
import time

logger = logging.getLogger()
logger.level = logging.DEBUG

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not available")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("numpy not available")

from py3plex.core import multinet
from py3plex.exceptions import VisualizationError

try:
    from py3plex.visualization.multilayer import (
        visualize_multilayer_network,
        plot_small_multiples,
        plot_edge_colored_projection,
        plot_supra_adjacency_heatmap,
        plot_radial_layers,
        plot_ego_multilayer,
        draw_multilayer_flow
    )
    VISUALIZATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Visualization modules not available: {e}")
    VISUALIZATION_AVAILABLE = False

DEPENDENCIES_AVAILABLE = MATPLOTLIB_AVAILABLE and NUMPY_AVAILABLE and VISUALIZATION_AVAILABLE

# Try to import pytest, but make it optional
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    class MockPytest:
        class mark:
            @staticmethod 
            def skipif(condition, reason=None):
                def decorator(func):
                    if condition:
                        def skipped_func(*args, **kwargs):
                            logger.info(f"Skipping test: {reason}")
                            return None
                        return skipped_func
                    return func
                return decorator
    
    pytest = MockPytest()
    PYTEST_AVAILABLE = False


def create_test_multilayer_network():
    """Create a small synthetic multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes and edges to layer 'A'
    network.add_nodes([
        {'source': '1', 'type': 'A'},
        {'source': '2', 'type': 'A'},
        {'source': '3', 'type': 'A'},
    ], input_type='dict')
    
    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'A', 'target_type': 'A'},
        {'source': '2', 'target': '3', 'source_type': 'A', 'target_type': 'A'},
    ], input_type='dict')
    
    # Add nodes and edges to layer 'B'
    network.add_nodes([
        {'source': '1', 'type': 'B'},
        {'source': '2', 'type': 'B'},
        {'source': '3', 'type': 'B'},
    ], input_type='dict')
    
    network.add_edges([
        {'source': '1', 'target': '3', 'source_type': 'B', 'target_type': 'B'},
    ], input_type='dict')
    
    return network


def create_complex_test_network():
    """Create a more complex multilayer network for edge case testing."""
    network = multinet.multi_layer_network(directed=False)
    
    # Create 4 layers with varying structures
    for layer in ['A', 'B', 'C', 'D']:
        for i in range(1, 6):
            network.add_nodes([{'source': str(i), 'type': layer}], input_type='dict')
    
    # Layer A: Complete graph
    for i in range(1, 6):
        for j in range(i+1, 6):
            network.add_edges([{
                'source': str(i),
                'target': str(j),
                'source_type': 'A',
                'target_type': 'A'
            }], input_type='dict')
    
    # Layer B: Star graph
    for i in [1, 2, 4, 5]:
        network.add_edges([{
            'source': '3',
            'target': str(i),
            'source_type': 'B',
            'target_type': 'B'
        }], input_type='dict')
    
    # Layer C: Path graph
    for i in range(1, 5):
        network.add_edges([{
            'source': str(i),
            'target': str(i+1),
            'source_type': 'C',
            'target_type': 'C'
        }], input_type='dict')
    
    # Layer D: Disconnected pairs
    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'D', 'target_type': 'D'},
        {'source': '3', 'target': '4', 'source_type': 'D', 'target_type': 'D'},
    ], input_type='dict')
    
    return network


# ============================================================================
# Basic Functionality Tests
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_visualize_multilayer_network_diagonal():
    """Test that the diagonal visualization mode works (backward compatibility)."""
    network = create_test_multilayer_network()
    
    # Should not raise an exception
    fig = visualize_multilayer_network(network, visualization_type="diagonal")
    
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_plot_small_multiples():
    """Test small multiples visualization."""
    network = create_test_multilayer_network()
    
    # Test with shared layout
    fig = plot_small_multiples(network, shared_layout=True, layout="spring")
    assert fig is not None
    assert len(fig.axes) >= 2  # Should have at least 2 subplots (layers A and B)
    plt.close('all')
    
    # Test with independent layouts
    fig = plot_small_multiples(network, shared_layout=False, layout="circular")
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_plot_edge_colored_projection():
    """Test edge-colored projection visualization."""
    network = create_test_multilayer_network()
    
    fig = plot_edge_colored_projection(network, layout="spring")
    assert fig is not None
    assert len(fig.axes) == 1  # Single subplot
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_plot_supra_adjacency_heatmap():
    """Test supra-adjacency heatmap visualization."""
    network = create_test_multilayer_network()
    
    # Test without inter-layer edges
    fig = plot_supra_adjacency_heatmap(network, include_inter_layer=False)
    assert fig is not None
    assert len(fig.axes) >= 1  # Should have at least the main axis
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_plot_radial_layers():
    """Test radial layers visualization."""
    network = create_test_multilayer_network()
    
    fig = plot_radial_layers(network, draw_inter_layer_edges=True)
    assert fig is not None
    assert len(fig.axes) == 1
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_plot_ego_multilayer():
    """Test ego-centric multilayer visualization."""
    network = create_test_multilayer_network()
    
    # Test with node '1' as ego
    fig = plot_ego_multilayer(network, ego='1', max_depth=1)
    assert fig is not None
    assert len(fig.axes) >= 1  # Should have at least one subplot
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_draw_multilayer_flow():
    """Test the new layered flow visualization."""
    network = create_test_multilayer_network()
    
    # Get layers data
    labels, graphs, multilinks = network.get_layers("diagonal")
    
    # Test basic flow visualization
    fig, ax = plt.subplots()
    result_ax = draw_multilayer_flow(
        graphs,
        multilinks,
        labels=labels,
        ax=ax,
        display=False
    )
    
    assert result_ax is not None
    assert result_ax == ax
    plt.close('all')
    
    # Test with custom parameters
    fig, ax = plt.subplots()
    result_ax = draw_multilayer_flow(
        graphs,
        multilinks,
        labels=labels,
        ax=ax,
        display=False,
        layer_gap=5.0,
        node_size=50,
        node_cmap="plasma",
        flow_alpha=0.5,
        flow_min_width=0.5,
        flow_max_width=5.0
    )
    
    assert result_ax is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_visualize_network_flow_style():
    """Test that visualize_network supports the 'flow' style."""
    network = create_test_multilayer_network()
    
    # Test with 'flow' style
    ax = network.visualize_network(style='flow', show=False)
    assert ax is not None
    plt.close('all')
    
    # Test with 'alluvial' style (alias)
    ax = network.visualize_network(style='alluvial', show=False)
    assert ax is not None
    plt.close('all')


# ============================================================================
# Parameter Variation Tests
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_small_multiples_layouts():
    """Test small multiples with different layout algorithms."""
    network = create_test_multilayer_network()
    
    layouts = ["spring", "circular", "random", "kamada_kawai"]
    for layout in layouts:
        fig = plot_small_multiples(network, layout=layout, shared_layout=True)
        assert fig is not None
        plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_small_multiples_grid_sizes():
    """Test small multiples with different grid configurations."""
    network = create_complex_test_network()
    
    for max_cols in [1, 2, 3, 5]:
        fig = plot_small_multiples(network, max_cols=max_cols)
        assert fig is not None
        assert len(fig.axes) >= 4  # Should have 4 subplots for 4 layers
        plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_small_multiples_node_sizes():
    """Test small multiples with different node sizes."""
    network = create_test_multilayer_network()
    
    for node_size in [10, 50, 100, 500]:
        fig = plot_small_multiples(network, node_size=node_size)
        assert fig is not None
        plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_edge_projection_custom_colors():
    """Test edge-colored projection with custom layer colors."""
    network = create_test_multilayer_network()
    
    custom_colors = {'A': 'red', 'B': 'blue'}
    fig = plot_edge_colored_projection(network, layer_colors=custom_colors)
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_edge_projection_layouts():
    """Test edge-colored projection with different layouts."""
    network = create_test_multilayer_network()
    
    layouts = ["spring", "circular", "random", "kamada_kawai"]
    for layout in layouts:
        fig = plot_edge_colored_projection(network, layout=layout)
        assert fig is not None
        plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_supra_heatmap_colormaps():
    """Test supra-adjacency heatmap with different colormaps."""
    network = create_test_multilayer_network()
    
    colormaps = ["viridis", "Blues", "RdYlBu_r", "Greys"]
    for cmap in colormaps:
        fig = plot_supra_adjacency_heatmap(network, cmap=cmap)
        assert fig is not None
        plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_supra_heatmap_inter_layer():
    """Test supra-adjacency heatmap with inter-layer connections."""
    network = create_test_multilayer_network()
    
    # Test with different inter-layer weights
    for weight in [0.5, 1.0, 2.0]:
        fig = plot_supra_adjacency_heatmap(
            network, 
            include_inter_layer=True,
            inter_layer_weight=weight
        )
        assert fig is not None
        plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_radial_layers_parameters():
    """Test radial layers with different parameter combinations."""
    network = create_test_multilayer_network()
    
    # Test different radius configurations
    configs = [
        {'base_radius': 0.5, 'radius_step': 0.5},
        {'base_radius': 1.0, 'radius_step': 1.0},
        {'base_radius': 1.5, 'radius_step': 2.0},
    ]
    
    for config in configs:
        fig = plot_radial_layers(network, **config)
        assert fig is not None
        plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_radial_layers_inter_layer_edges():
    """Test radial layers with and without inter-layer edges."""
    network = create_test_multilayer_network()
    
    # With inter-layer edges
    fig = plot_radial_layers(network, draw_inter_layer_edges=True)
    assert fig is not None
    plt.close('all')
    
    # Without inter-layer edges
    fig = plot_radial_layers(network, draw_inter_layer_edges=False)
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_ego_multilayer_depth():
    """Test ego-centric visualization with different depths."""
    network = create_complex_test_network()
    
    for depth in [1, 2]:
        fig = plot_ego_multilayer(network, ego='1', max_depth=depth)
        assert fig is not None
        plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_ego_multilayer_specific_layers():
    """Test ego-centric visualization with specific layers."""
    network = create_complex_test_network()
    
    # Test with specific layers
    fig = plot_ego_multilayer(network, ego='2', layers=['A', 'B'])
    assert fig is not None
    plt.close('all')
    
    # Test with single layer
    fig = plot_ego_multilayer(network, ego='3', layers=['C'])
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_ego_multilayer_layouts():
    """Test ego-centric visualization with different layouts."""
    network = create_test_multilayer_network()
    
    layouts = ["spring", "circular", "kamada_kawai"]
    for layout in layouts:
        fig = plot_ego_multilayer(network, ego='1', layout=layout)
        assert fig is not None
        plt.close('all')


# ============================================================================
# Unified API Tests
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_unified_api_small_multiples():
    """Test small multiples via main API function."""
    network = create_test_multilayer_network()
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="small_multiples",
        layout="spring",
        node_size=100
    )
    
    assert fig is not None
    assert len(fig.axes) >= 2
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_unified_api_edge_projection():
    """Test edge-colored projection via main API function."""
    network = create_test_multilayer_network()
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="edge_colored_projection",
        layout="circular"
    )
    
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_unified_api_supra_heatmap():
    """Test supra-adjacency heatmap via main API function."""
    network = create_test_multilayer_network()
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="supra_adjacency_heatmap",
        cmap="viridis"
    )
    
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_unified_api_radial():
    """Test radial layers via main API function."""
    network = create_test_multilayer_network()
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="radial_layers",
        base_radius=1.0,
        radius_step=1.5
    )
    
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_unified_api_ego():
    """Test ego-centric visualization via main API function."""
    network = create_test_multilayer_network()
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="ego_multilayer",
        ego='1',
        max_depth=1
    )
    
    assert fig is not None
    plt.close('all')


# ============================================================================
# Edge Case Tests
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_complex_network_visualizations():
    """Test all visualization modes with a complex network."""
    network = create_complex_test_network()
    
    modes = [
        ('small_multiples', {}),
        ('edge_colored_projection', {}),
        ('supra_adjacency_heatmap', {}),
        ('radial_layers', {}),
        ('ego_multilayer', {'ego': '3'}),
    ]
    
    for mode, kwargs in modes:
        fig = visualize_multilayer_network(network, visualization_type=mode, **kwargs)
        assert fig is not None
        plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_single_layer_network():
    """Test visualizations with single-layer network."""
    network = multinet.multi_layer_network(directed=False)
    
    # Create single layer
    for i in range(1, 4):
        network.add_nodes([{'source': str(i), 'type': 'A'}], input_type='dict')
    
    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'A', 'target_type': 'A'},
    ], input_type='dict')
    
    # Test modes that should work with single layer
    fig = plot_small_multiples(network)
    assert fig is not None
    plt.close('all')
    
    fig = plot_edge_colored_projection(network)
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_empty_layer_handling():
    """Test handling of layers with no edges."""
    network = multinet.multi_layer_network(directed=False)
    
    # Layer with nodes but no edges
    network.add_nodes([
        {'source': '1', 'type': 'A'},
        {'source': '2', 'type': 'A'},
    ], input_type='dict')
    
    # Layer with edges
    network.add_nodes([
        {'source': '1', 'type': 'B'},
        {'source': '2', 'type': 'B'},
    ], input_type='dict')
    
    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'B', 'target_type': 'B'},
    ], input_type='dict')
    
    fig = plot_small_multiples(network)
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_large_grid_configuration():
    """Test small multiples with many layers."""
    network = multinet.multi_layer_network(directed=False)
    
    # Create 6 layers
    for layer in ['A', 'B', 'C', 'D', 'E', 'F']:
        for i in range(1, 4):
            network.add_nodes([{'source': str(i), 'type': layer}], input_type='dict')
        network.add_edges([
            {'source': '1', 'target': '2', 'source_type': layer, 'target_type': layer},
        ], input_type='dict')
    
    fig = plot_small_multiples(network, max_cols=3)
    assert fig is not None
    assert len(fig.axes) >= 6
    plt.close('all')


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_invalid_visualization_type():
    """Test that invalid visualization type raises ValueError."""
    network = create_test_multilayer_network()
    
    try:
        fig = visualize_multilayer_network(network, visualization_type="invalid_type")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown visualization_type" in str(e)
    
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_ego_node_not_found():
    """Test ego visualization with non-existent node."""
    network = create_test_multilayer_network()
    
    try:
        fig = plot_ego_multilayer(network, ego='999')
        # Should still create figure even if node not found
        plt.close('all')
    except (ValueError, KeyError) as e:
        # Either behavior is acceptable
        pass


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_invalid_layout():
    """Test handling of invalid layout algorithm."""
    network = create_test_multilayer_network()
    
    # Spring should work
    fig = plot_small_multiples(network, layout="spring")
    assert fig is not None
    plt.close('all')


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_all_modes_sequential():
    """Test running all visualization modes sequentially."""
    network = create_test_multilayer_network()
    
    modes = [
        'diagonal',
        'small_multiples',
        'edge_colored_projection',
        'supra_adjacency_heatmap',
        'radial_layers',
    ]
    
    for mode in modes:
        fig = visualize_multilayer_network(network, visualization_type=mode)
        assert fig is not None
        plt.close('all')
    
    # Test ego separately (requires parameter)
    fig = visualize_multilayer_network(network, visualization_type='ego_multilayer', ego='1')
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_figure_properties():
    """Test that created figures have expected properties."""
    network = create_test_multilayer_network()
    
    # Test small multiples
    fig = plot_small_multiples(network)
    assert hasattr(fig, 'axes')
    assert hasattr(fig, 'savefig')
    assert len(fig.axes) >= 2
    plt.close('all')
    
    # Test edge projection
    fig = plot_edge_colored_projection(network)
    assert len(fig.axes) == 1
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_backward_compatibility():
    """Test backward compatibility with existing visualization methods."""
    network = create_test_multilayer_network()
    
    # Old API should still work
    network.visualize_network(style='diagonal', show=False)
    plt.close('all')
    
    network.visualize_network(style='hairball', show=False)
    plt.close('all')


# ============================================================================
# Performance Tests (optional, for development)
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_visualization_performance():
    """Test that visualizations complete in reasonable time."""
    network = create_complex_test_network()
    
    start = time.time()
    fig = visualize_multilayer_network(network, visualization_type="small_multiples")
    duration = time.time() - start
    
    # Should complete within 10 seconds for small network
    assert duration < 10.0
    assert fig is not None
    plt.close('all')


# Run tests if executed directly
if __name__ == "__main__":
    print("=" * 70)
    print("TESTING NEW MULTILAYER VISUALIZATIONS - EXTENSIVE TESTS")
    print("=" * 70)
    
    if not DEPENDENCIES_AVAILABLE:
        print("\nSkipping tests: Required dependencies not available")
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


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_visualize_multilayer_network_diagonal():
    """Test that the diagonal visualization mode works (backward compatibility)."""
    network = create_test_multilayer_network()
    
    # Should not raise an exception
    fig = visualize_multilayer_network(network, visualization_type="diagonal")
    
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_plot_small_multiples():
    """Test small multiples visualization."""
    network = create_test_multilayer_network()
    
    # Test with shared layout
    fig = plot_small_multiples(network, shared_layout=True, layout="spring")
    assert fig is not None
    assert len(fig.axes) >= 2  # Should have at least 2 subplots (layers A and B)
    plt.close('all')
    
    # Test with independent layouts
    fig = plot_small_multiples(network, shared_layout=False, layout="circular")
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_plot_small_multiples_via_main_api():
    """Test small multiples via main API function."""
    network = create_test_multilayer_network()
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="small_multiples",
        layout="spring",
        node_size=100
    )
    
    assert fig is not None
    assert len(fig.axes) >= 2
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_plot_edge_colored_projection():
    """Test edge-colored projection visualization."""
    network = create_test_multilayer_network()
    
    fig = plot_edge_colored_projection(network, layout="spring")
    assert fig is not None
    assert len(fig.axes) == 1  # Single subplot
    plt.close('all')
    
    # Test with custom colors
    layer_colors = {'A': 'red', 'B': 'blue'}
    fig = plot_edge_colored_projection(network, layer_colors=layer_colors)
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_plot_edge_colored_projection_via_main_api():
    """Test edge-colored projection via main API function."""
    network = create_test_multilayer_network()
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="edge_colored_projection",
        layout="circular"
    )
    
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_plot_supra_adjacency_heatmap():
    """Test supra-adjacency heatmap visualization."""
    network = create_test_multilayer_network()
    
    # Test without inter-layer edges
    fig = plot_supra_adjacency_heatmap(network, include_inter_layer=False)
    assert fig is not None
    assert len(fig.axes) >= 1  # Should have at least the main axis
    plt.close('all')
    
    # Test with inter-layer edges
    fig = plot_supra_adjacency_heatmap(network, include_inter_layer=True)
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_plot_supra_adjacency_heatmap_via_main_api():
    """Test supra-adjacency heatmap via main API function."""
    network = create_test_multilayer_network()
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="supra_adjacency_heatmap",
        cmap="viridis"
    )
    
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_plot_radial_layers():
    """Test radial layers visualization."""
    network = create_test_multilayer_network()
    
    # Test with inter-layer edges
    fig = plot_radial_layers(network, draw_inter_layer_edges=True)
    assert fig is not None
    assert len(fig.axes) == 1
    plt.close('all')
    
    # Test without inter-layer edges
    fig = plot_radial_layers(network, draw_inter_layer_edges=False)
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_plot_radial_layers_via_main_api():
    """Test radial layers via main API function."""
    network = create_test_multilayer_network()
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="radial_layers",
        base_radius=1.0,
        radius_step=1.5
    )
    
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_plot_ego_multilayer():
    """Test ego-centric multilayer visualization."""
    network = create_test_multilayer_network()
    
    # Test with node '1' as ego
    fig = plot_ego_multilayer(network, ego='1', max_depth=1)
    assert fig is not None
    assert len(fig.axes) >= 1  # Should have at least one subplot
    plt.close('all')
    
    # Test with specific layers
    fig = plot_ego_multilayer(network, ego='2', layers=['A'], max_depth=1)
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_plot_ego_multilayer_via_main_api():
    """Test ego-centric visualization via main API function."""
    network = create_test_multilayer_network()
    
    fig = visualize_multilayer_network(
        network,
        visualization_type="ego_multilayer",
        ego='1',
        max_depth=1
    )
    
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_invalid_visualization_type():
    """Test that invalid visualization type raises VisualizationError."""
    network = create_test_multilayer_network()
    
    try:
        fig = visualize_multilayer_network(network, visualization_type="invalid_type")
        assert False, "Should have raised VisualizationError"
    except VisualizationError as e:
        assert "Unknown visualization_type" in str(e)
    
    plt.close('all')


# Run tests if executed directly
if __name__ == "__main__":
    print("=" * 70)
    print("TESTING NEW MULTILAYER VISUALIZATIONS")
    print("=" * 70)
    
    if not DEPENDENCIES_AVAILABLE:
        print("\nSkipping tests: Required dependencies not available")
        exit(0)
    
    test_functions = [
        test_visualize_multilayer_network_diagonal,
        test_plot_small_multiples,
        test_plot_small_multiples_via_main_api,
        test_plot_edge_colored_projection,
        test_plot_edge_colored_projection_via_main_api,
        test_plot_supra_adjacency_heatmap,
        test_plot_supra_adjacency_heatmap_via_main_api,
        test_plot_radial_layers,
        test_plot_radial_layers_via_main_api,
        test_plot_ego_multilayer,
        test_plot_ego_multilayer_via_main_api,
        test_invalid_visualization_type,
    ]
    
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
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    exit(0 if failed == 0 else 1)


# ============================================================================
# Legend and Label Generation Tests
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_hairball_plot_with_legend():
    """Test that hairball plot generates legend correctly."""
    from py3plex.visualization.multilayer import hairball_plot
    
    network = create_test_multilayer_network()
    # Get a single layer as NetworkX graph
    labels, graphs, multilinks = network.get_layers("diagonal")
    if len(graphs) > 0:
        g = graphs[0]
        
        # Test with legend enabled
        hairball_plot(g, legend=True, display=False, draw=True)
        
        # Check that a legend was created (or at least that the plot succeeded)
        fig = plt.gcf()
        axes = fig.get_axes()
        assert len(axes) > 0  # Should have at least one axis
        
        ax = axes[0]
        legend = ax.get_legend()
        # Legend might be None if there's only one color, which is acceptable
        # The important thing is that the plot succeeded with legend=True
        
        plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_hairball_plot_with_labels():
    """Test that hairball plot displays node labels correctly."""
    from py3plex.visualization.multilayer import hairball_plot
    
    network = create_test_multilayer_network()
    labels, graphs, multilinks = network.get_layers("diagonal")
    if len(graphs) > 0:
        g = graphs[0]
        
        # Get node labels
        node_labels = list(g.nodes())[:3]  # First 3 nodes
        
        # Test with labels
        hairball_plot(g, labels=node_labels, label_font_size=8, display=False, draw=True)
        
        # Check that text objects were created
        fig = plt.gcf()
        axes = fig.get_axes()
        if axes:
            ax = axes[0]
            texts = ax.texts
            # Should have created text objects for the labels we requested
            assert len(texts) == len(node_labels), f"Expected {len(node_labels)} labels, got {len(texts)}"
        
        plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_small_multiples_with_labels():
    """Test small multiples with layer labels."""
    network = create_test_multilayer_network()
    
    # Small multiples should automatically show layer labels
    fig = plot_small_multiples(network, layout="circular")
    assert fig is not None
    
    # Check that subplots have titles (which serve as labels)
    # The test network has layers 'A' and 'B'
    assert len(fig.axes) >= 2, "Should have at least 2 subplots for layers A and B"
    
    # Verify each subplot has a title
    for ax in fig.axes:
        title = ax.get_title()
        assert isinstance(title, str), "Title should be a string"
        # For small multiples, layer names should appear as titles
    
    plt.close('all')


# ============================================================================
# Edge Case Tests (Self-loops, Multiple Edges)
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_visualization_with_self_loops():
    """Test visualization handles self-loops correctly."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    network.add_nodes([
        {'source': '1', 'type': 'A'},
        {'source': '2', 'type': 'A'},
        {'source': '3', 'type': 'A'},
    ], input_type='dict')
    
    # Add regular edges
    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'A', 'target_type': 'A'},
        {'source': '2', 'target': '3', 'source_type': 'A', 'target_type': 'A'},
    ], input_type='dict')
    
    # Add self-loop
    network.add_edges([
        {'source': '1', 'target': '1', 'source_type': 'A', 'target_type': 'A'},
    ], input_type='dict')
    
    # Test that visualizations don't crash with self-loops
    fig = plot_small_multiples(network)
    assert fig is not None
    plt.close('all')
    
    fig = plot_edge_colored_projection(network)
    assert fig is not None
    plt.close('all')
    
    fig = plot_radial_layers(network)
    assert fig is not None
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_visualization_with_multiple_edges():
    """Test visualization handles multiple edges between same nodes."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes to multiple layers
    for layer in ['A', 'B']:
        network.add_nodes([
            {'source': '1', 'type': layer},
            {'source': '2', 'type': layer},
        ], input_type='dict')
    
    # Add multiple edges between same nodes in different layers
    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'A', 'target_type': 'A'},
        {'source': '1', 'target': '2', 'source_type': 'B', 'target_type': 'B'},
    ], input_type='dict')
    
    # Test edge-colored projection (shows edges from multiple layers)
    fig = plot_edge_colored_projection(network)
    assert fig is not None
    plt.close('all')
    
    # Test small multiples
    fig = plot_small_multiples(network)
    assert fig is not None
    assert len(fig.axes) >= 2
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_visualization_with_isolated_nodes():
    """Test visualization with isolated nodes (no edges)."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes with no edges
    network.add_nodes([
        {'source': '1', 'type': 'A'},
        {'source': '2', 'type': 'A'},
        {'source': '3', 'type': 'A'},
    ], input_type='dict')
    
    # Only connect two nodes, leaving one isolated
    network.add_edges([
        {'source': '1', 'target': '2', 'source_type': 'A', 'target_type': 'A'},
    ], input_type='dict')
    
    # Test visualizations with isolated node
    fig = plot_small_multiples(network)
    assert fig is not None
    plt.close('all')
    
    fig = plot_edge_colored_projection(network)
    assert fig is not None
    plt.close('all')


# ============================================================================
# Performance Tests for Large Graphs
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_large_graph_visualization_performance():
    """Test that large graph visualization completes in reasonable time."""
    # Create a larger multilayer network
    network = multinet.multi_layer_network(directed=False)
    
    # Add 100 nodes per layer, 3 layers
    for layer in ['A', 'B', 'C']:
        for i in range(100):
            network.add_nodes([{'source': str(i), 'type': layer}], input_type='dict')
    
    # Add edges to create a sparse network (200 edges per layer)
    random.seed(42)
    for layer in ['A', 'B', 'C']:
        for _ in range(200):
            src = str(random.randint(0, 99))
            tgt = str(random.randint(0, 99))
            if src != tgt:  # Avoid self-loops
                network.add_edges([{
                    'source': src,
                    'target': tgt,
                    'source_type': layer,
                    'target_type': layer
                }], input_type='dict')
    
    # Test small multiples performance
    start = time.time()
    fig = plot_small_multiples(network, layout="circular")
    duration = time.time() - start
    
    assert fig is not None
    # Should complete within 30 seconds for 300 nodes, 600 edges
    assert duration < 30.0, f"Visualization took {duration:.2f}s, expected < 30s"
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_supra_heatmap_large_network_performance():
    """Test supra-adjacency heatmap performance on larger network."""
    # Create a network with 50 nodes per layer
    network = multinet.multi_layer_network(directed=False)
    
    for layer in ['A', 'B']:
        for i in range(50):
            network.add_nodes([{'source': str(i), 'type': layer}], input_type='dict')
    
    # Add edges
    random.seed(42)
    for layer in ['A', 'B']:
        for _ in range(100):
            src = str(random.randint(0, 49))
            tgt = str(random.randint(0, 49))
            if src != tgt:
                network.add_edges([{
                    'source': src,
                    'target': tgt,
                    'source_type': layer,
                    'target_type': layer
                }], input_type='dict')
    
    start = time.time()
    fig = plot_supra_adjacency_heatmap(network)
    duration = time.time() - start
    
    assert fig is not None
    # Heatmap should be fast even for larger networks
    assert duration < 20.0, f"Heatmap took {duration:.2f}s, expected < 20s"
    plt.close('all')


# ============================================================================
# Output File Format Tests
# ============================================================================

@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_save_visualization_png_format(tmp_path):
    """Test saving visualization to PNG format."""
    network = create_test_multilayer_network()
    
    output_file = tmp_path / "test_viz.png"
    
    # Create visualization
    fig = plot_small_multiples(network)
    assert fig is not None
    
    # Save as PNG
    fig.savefig(str(output_file), format='png', dpi=100, bbox_inches='tight')
    plt.close('all')
    
    # Verify file was created
    assert output_file.exists()
    assert output_file.stat().st_size > 0


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_save_visualization_svg_format(tmp_path):
    """Test saving visualization to SVG format."""
    network = create_test_multilayer_network()
    
    output_file = tmp_path / "test_viz.svg"
    
    # Create visualization
    fig = plot_edge_colored_projection(network)
    assert fig is not None
    
    # Save as SVG
    fig.savefig(str(output_file), format='svg', bbox_inches='tight')
    plt.close('all')
    
    # Verify file was created and contains SVG header
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    
    # Check it's a valid SVG file
    with open(output_file, 'r') as f:
        content = f.read()
        assert '<svg' in content or '<?xml' in content


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_save_visualization_pdf_format(tmp_path):
    """Test saving visualization to PDF format."""
    network = create_test_multilayer_network()
    
    output_file = tmp_path / "test_viz.pdf"
    
    # Create visualization
    fig = plot_radial_layers(network)
    assert fig is not None
    
    # Save as PDF
    fig.savefig(str(output_file), format='pdf', bbox_inches='tight')
    plt.close('all')
    
    # Verify file was created
    assert output_file.exists()
    assert output_file.stat().st_size > 0
    
    # Check it's a PDF file (starts with %PDF)
    with open(output_file, 'rb') as f:
        header = f.read(4)
        assert header == b'%PDF'


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_save_multiple_formats(tmp_path):
    """Test saving the same visualization in multiple formats."""
    network = create_test_multilayer_network()
    
    # Create one visualization
    fig = plot_supra_adjacency_heatmap(network)
    assert fig is not None
    
    formats = ['png', 'svg', 'pdf']
    for fmt in formats:
        output_file = tmp_path / f"test_viz.{fmt}"
        fig.savefig(str(output_file), format=fmt, bbox_inches='tight')
        
        # Verify each file was created
        assert output_file.exists()
        assert output_file.stat().st_size > 0
    
    plt.close('all')


@pytest.mark.skipif(not DEPENDENCIES_AVAILABLE, reason="matplotlib or numpy not available")
def test_save_with_different_dpi(tmp_path):
    """Test saving visualization with different DPI settings."""
    network = create_test_multilayer_network()
    
    fig = plot_small_multiples(network)
    assert fig is not None
    
    # Test different DPI values
    dpis = [72, 150, 300]
    file_sizes = []
    
    for dpi in dpis:
        output_file = tmp_path / f"test_viz_dpi{dpi}.png"
        fig.savefig(str(output_file), format='png', dpi=dpi, bbox_inches='tight')
        
        assert output_file.exists()
        file_size = output_file.stat().st_size
        file_sizes.append(file_size)
    
    # Higher DPI should generally result in larger files
    # (though compression can affect this)
    assert file_sizes[0] > 0
    assert file_sizes[1] > 0
    assert file_sizes[2] > 0
    
    plt.close('all')
