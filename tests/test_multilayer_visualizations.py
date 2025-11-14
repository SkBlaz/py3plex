"""
Tests for new multilayer visualization functions.

This test module validates the new visualization modes added to py3plex:
- Small multiples
- Edge-colored projection
- Supra-adjacency heatmap
- Radial layers
- Ego-centric multilayer
"""

import logging
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

try:
    from py3plex.visualization.multilayer import (
        visualize_multilayer_network,
        plot_small_multiples,
        plot_edge_colored_projection,
        plot_supra_adjacency_heatmap,
        plot_radial_layers,
        plot_ego_multilayer
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
    """Test that invalid visualization type raises ValueError."""
    network = create_test_multilayer_network()
    
    try:
        fig = visualize_multilayer_network(network, visualization_type="invalid_type")
        assert False, "Should have raised ValueError"
    except ValueError as e:
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
