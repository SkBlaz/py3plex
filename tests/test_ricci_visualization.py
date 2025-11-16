"""
Tests for Ricci-flow-based visualization functions.

This module tests the Ricci-flow visualization capabilities for multilayer networks,
including core, per-layer, and supra-graph visualizations.
"""

import pytest
import networkx as nx
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend for testing
import matplotlib.pyplot as plt

from py3plex.core import multinet
from py3plex.algorithms.curvature.ollivier_ricci_multilayer import (
    RicciBackendNotAvailable,
    GRAPHRICCICURVATURE_AVAILABLE,
)

# Skip all tests if GraphRicciCurvature is not available
pytestmark = pytest.mark.skipif(
    not GRAPHRICCICURVATURE_AVAILABLE, reason="GraphRicciCurvature not installed"
)


@pytest.fixture
def simple_multilayer_network():
    """Create a simple multilayer network for testing."""
    net = multinet.multi_layer_network(directed=False)

    # Add edges in two layers
    net.add_edges(
        [
            ["A", "layer1", "B", "layer1", 1],
            ["B", "layer1", "C", "layer1", 1],
            ["C", "layer1", "D", "layer1", 1],
            ["A", "layer2", "B", "layer2", 1],
            ["B", "layer2", "D", "layer2", 1],
            ["C", "layer2", "D", "layer2", 1],
        ],
        input_type="list",
    )

    return net


@pytest.fixture
def triangle_multilayer():
    """Create a multilayer network with triangular structures."""
    net = multinet.multi_layer_network(directed=False)

    # Layer 1: Triangle ABC
    net.add_edges(
        [
            ["A", "layer1", "B", "layer1", 1],
            ["B", "layer1", "C", "layer1", 1],
            ["C", "layer1", "A", "layer1", 1],
        ],
        input_type="list",
    )

    # Layer 2: Triangle DEF
    net.add_edges(
        [
            ["D", "layer2", "E", "layer2", 1],
            ["E", "layer2", "F", "layer2", 1],
            ["F", "layer2", "D", "layer2", 1],
        ],
        input_type="list",
    )

    return net


class TestRicciFlowLayoutSingle:
    """Test the core ricci_flow_layout_single function."""

    def test_layout_simple_graph(self):
        """Test layout computation on a simple graph."""
        from py3plex.visualization.ricci_layout import ricci_flow_layout_single
        from py3plex.algorithms.curvature.ollivier_ricci_multilayer import (
            compute_ollivier_ricci_flow_single_graph,
        )

        # Create a small graph
        G = nx.karate_club_graph()

        # Apply Ricci flow
        G_flow = compute_ollivier_ricci_flow_single_graph(G, alpha=0.5, iterations=5)

        # Compute layout
        positions = ricci_flow_layout_single(G_flow, dim=2, layout_type="mds")

        # Verify positions
        assert isinstance(positions, dict)
        assert len(positions) == G_flow.number_of_nodes()

        # Check that each position is a 2D array
        for node, pos in positions.items():
            assert len(pos) == 2
            assert isinstance(pos[0], (int, float))
            assert isinstance(pos[1], (int, float))

    def test_layout_types(self):
        """Test different layout types."""
        from py3plex.visualization.ricci_layout import ricci_flow_layout_single
        from py3plex.algorithms.curvature.ollivier_ricci_multilayer import (
            compute_ollivier_ricci_flow_single_graph,
        )

        G = nx.karate_club_graph()
        G_flow = compute_ollivier_ricci_flow_single_graph(G, alpha=0.5, iterations=3)

        for layout_type in ["mds", "spring", "spectral"]:
            positions = ricci_flow_layout_single(G_flow, dim=2, layout_type=layout_type)
            assert len(positions) == G_flow.number_of_nodes()

    def test_layout_3d(self):
        """Test 3D layout computation."""
        from py3plex.visualization.ricci_layout import ricci_flow_layout_single
        from py3plex.algorithms.curvature.ollivier_ricci_multilayer import (
            compute_ollivier_ricci_flow_single_graph,
        )

        G = nx.karate_club_graph()
        G_flow = compute_ollivier_ricci_flow_single_graph(G, alpha=0.5, iterations=3)

        positions = ricci_flow_layout_single(G_flow, dim=3, layout_type="spring")

        # Verify 3D positions
        for node, pos in positions.items():
            assert len(pos) == 3


class TestVisualizeCoreRicci:
    """Test core (aggregated) Ricci visualization."""

    def test_core_visualization_basic(self, simple_multilayer_network):
        """Test basic core visualization."""
        net = simple_multilayer_network

        # Visualize core network
        fig, ax, positions = net.visualize_ricci_core(
            alpha=0.5, iterations=5, layout_type="mds", dim=2, compute_if_missing=True
        )

        # Verify outputs
        assert fig is not None
        assert ax is not None
        assert isinstance(positions, dict)
        assert len(positions) > 0

        # Clean up
        plt.close(fig)

    def test_core_visualization_with_precomputed_flow(self, simple_multilayer_network):
        """Test visualization with pre-computed Ricci flow."""
        net = simple_multilayer_network

        # Pre-compute Ricci flow
        net.compute_ollivier_ricci_flow(
            mode="core", alpha=0.5, iterations=5, inplace=True
        )

        # Visualize
        fig, ax, positions = net.visualize_ricci_core(
            alpha=0.5, iterations=5, compute_if_missing=False
        )

        assert len(positions) == net.core_network.number_of_nodes()
        plt.close(fig)

    def test_core_visualization_node_coloring(self, simple_multilayer_network):
        """Test different node coloring schemes."""
        net = simple_multilayer_network

        for color_by in ["layer_overlap", "degree", "curvature"]:
            fig, ax, positions = net.visualize_ricci_core(
                node_color_by=color_by, iterations=3
            )
            assert fig is not None
            plt.close(fig)

    def test_core_visualization_3d(self, simple_multilayer_network):
        """Test 3D core visualization."""
        net = simple_multilayer_network

        fig, ax, positions = net.visualize_ricci_core(
            dim=3, layout_type="spring", iterations=3
        )

        # Verify 3D positions
        for node, pos in positions.items():
            assert len(pos) == 3

        plt.close(fig)


class TestVisualizeLayersRicci:
    """Test per-layer Ricci visualization."""

    def test_layers_visualization_basic(self, simple_multilayer_network):
        """Test basic per-layer visualization."""
        net = simple_multilayer_network

        fig, layer_positions = net.visualize_ricci_layers(
            alpha=0.5,
            iterations=5,
            layout_type="mds",
            share_layout=True,
            compute_if_missing=True,
        )

        assert fig is not None
        assert isinstance(layer_positions, dict)
        assert len(layer_positions) > 0

        # Verify each layer has positions
        for layer_id, positions in layer_positions.items():
            assert isinstance(positions, dict)
            assert len(positions) > 0

        plt.close(fig)

    def test_layers_shared_vs_independent_layout(self, simple_multilayer_network):
        """Test shared vs independent layouts."""
        net = simple_multilayer_network

        # Shared layout
        fig_shared, pos_shared = net.visualize_ricci_layers(
            share_layout=True, iterations=3
        )

        # Independent layout
        fig_indep, pos_indep = net.visualize_ricci_layers(
            share_layout=False, iterations=3
        )

        assert len(pos_shared) > 0
        assert len(pos_indep) > 0

        plt.close(fig_shared)
        plt.close(fig_indep)

    def test_layers_specific_layers(self, simple_multilayer_network):
        """Test visualization of specific layers."""
        net = simple_multilayer_network

        # Visualize only layer1
        fig, layer_positions = net.visualize_ricci_layers(
            layers=["layer1"], iterations=3
        )

        assert "layer1" in layer_positions
        assert len(layer_positions) == 1

        plt.close(fig)

    def test_layers_grid_arrangement(self, triangle_multilayer):
        """Test grid arrangement of layers."""
        net = triangle_multilayer

        fig, layer_positions = net.visualize_ricci_layers(
            arrangement="grid", iterations=3
        )

        # Should have positions for both layers
        assert len(layer_positions) == 2

        plt.close(fig)


class TestVisualizeSupraRicci:
    """Test supra-graph Ricci visualization."""

    def test_supra_visualization_basic(self, simple_multilayer_network):
        """Test basic supra-graph visualization."""
        net = simple_multilayer_network

        fig, ax, positions = net.visualize_ricci_supra(
            alpha=0.5, iterations=5, layout_type="mds", dim=2, compute_if_missing=True
        )

        assert fig is not None
        assert ax is not None
        assert isinstance(positions, dict)
        assert len(positions) > 0

        # Verify supra-graph nodes (should be tuples)
        for node in positions.keys():
            if isinstance(node, tuple):
                assert len(node) == 2  # (node_id, layer_id)

        plt.close(fig)

    def test_supra_visualization_3d(self, simple_multilayer_network):
        """Test 3D supra-graph visualization."""
        net = simple_multilayer_network

        fig, ax, positions = net.visualize_ricci_supra(
            dim=3, layout_type="spring", iterations=3
        )

        # Verify 3D positions
        for node, pos in positions.items():
            assert len(pos) == 3

        plt.close(fig)

    def test_supra_layer_separation(self, simple_multilayer_network):
        """Test layer separation in 3D supra visualization."""
        net = simple_multilayer_network

        fig, ax, positions = net.visualize_ricci_supra(
            dim=3, layer_separation=1.0, iterations=3
        )

        # Verify that layers are separated along z-axis
        z_coords = [pos[2] for pos in positions.values()]
        assert len(set(z_coords)) > 1  # Should have different z values

        plt.close(fig)

    def test_supra_node_coloring(self, simple_multilayer_network):
        """Test different node coloring schemes for supra-graph."""
        net = simple_multilayer_network

        for color_by in ["layer", "curvature"]:
            fig, ax, positions = net.visualize_ricci_supra(
                node_color_by=color_by, iterations=3
            )
            assert fig is not None
            plt.close(fig)


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_network(self):
        """Test visualization with empty network."""
        net = multinet.multi_layer_network(directed=False)

        with pytest.raises(ValueError):
            net.visualize_ricci_core()

    def test_missing_flow_with_compute_false(self, simple_multilayer_network):
        """Test error when Ricci flow not computed and compute_if_missing=False."""
        net = simple_multilayer_network

        with pytest.raises(ValueError):
            net.visualize_ricci_core(compute_if_missing=False)

    def test_invalid_layout_type(self, simple_multilayer_network):
        """Test invalid layout type."""
        from py3plex.visualization.ricci_layout import ricci_flow_layout_single

        G = nx.karate_club_graph()

        with pytest.raises(ValueError):
            ricci_flow_layout_single(G, layout_type="invalid")

    def test_invalid_dim(self, simple_multilayer_network):
        """Test invalid dimension."""
        from py3plex.visualization.ricci_layout import ricci_flow_layout_single

        G = nx.karate_club_graph()

        with pytest.raises(ValueError):
            ricci_flow_layout_single(G, dim=4)


class TestBackendAvailability:
    """Test backend availability checking."""

    @pytest.mark.skipif(
        GRAPHRICCICURVATURE_AVAILABLE,
        reason="Only test when GraphRicciCurvature is NOT available",
    )
    def test_missing_backend_error(self, simple_multilayer_network):
        """Test that appropriate error is raised when backend is missing."""
        net = simple_multilayer_network

        with pytest.raises(RicciBackendNotAvailable) as exc_info:
            net.visualize_ricci_core()

        # Check error message
        assert "GraphRicciCurvature" in str(exc_info.value)
        assert "pip install" in str(exc_info.value)


class TestLayoutConsistency:
    """Test consistency of layouts across different calls."""

    def test_shared_layout_consistency(self, simple_multilayer_network):
        """Test that shared layout produces consistent positions across layers."""
        net = simple_multilayer_network

        fig, layer_positions = net.visualize_ricci_layers(
            share_layout=True, random_state=42, iterations=3
        )

        # Check if common nodes have same positions across layers
        common_nodes = set.intersection(
            *[set(positions.keys()) for positions in layer_positions.values()]
        )

        if len(common_nodes) > 0:
            # Pick a common node and check positions are similar
            test_node = list(common_nodes)[0]
            positions_for_node = [
                layer_positions[layer][test_node]
                for layer in layer_positions.keys()
                if test_node in layer_positions[layer]
            ]

            # All positions for this node should be identical or very close
            if len(positions_for_node) > 1:
                import numpy as np

                for i in range(1, len(positions_for_node)):
                    assert np.allclose(
                        positions_for_node[0], positions_for_node[i], rtol=1e-5
                    )

        plt.close(fig)


class TestVisualizationOutputs:
    """Test that visualizations produce valid outputs."""

    def test_positions_are_numeric(self, simple_multilayer_network):
        """Test that all position values are numeric."""
        import numpy as np

        net = simple_multilayer_network
        fig, ax, positions = net.visualize_ricci_core(iterations=3)

        for node, pos in positions.items():
            assert isinstance(pos, np.ndarray)
            assert not np.any(np.isnan(pos))
            assert not np.any(np.isinf(pos))

        plt.close(fig)

    def test_figure_exists(self, simple_multilayer_network):
        """Test that figures are properly created."""
        net = simple_multilayer_network

        fig, ax, positions = net.visualize_ricci_core(iterations=3)

        # Check figure exists and has correct type
        assert isinstance(fig, plt.Figure)
        assert isinstance(ax, plt.Axes)

        plt.close(fig)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
