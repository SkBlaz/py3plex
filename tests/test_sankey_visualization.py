"""
Tests for the sankey visualization module.

This module tests the inter-layer flow visualization functionality.
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for testing

import matplotlib.pyplot as plt
import networkx as nx
import pytest

from py3plex.visualization.sankey import (
    draw_multilayer_sankey,
    _draw_simple_flow_diagram,
    _draw_aggregated_flow_diagram,
)


class TestDrawMultilayerSankey:
    """Test the main draw_multilayer_sankey function."""

    def test_empty_graphs_list(self):
        """Test handling of empty graphs list."""
        fig, ax = plt.subplots()
        result = draw_multilayer_sankey([], {}, ax=ax, display=False)
        assert result is ax
        plt.close(fig)

    def test_single_layer_no_multilinks(self):
        """Test with single layer and no inter-layer links."""
        g = nx.Graph()
        g.add_edge("A", "B")
        g.add_edge("B", "C")
        
        fig, ax = plt.subplots()
        result = draw_multilayer_sankey(
            [g], {}, labels=["Layer1"], ax=ax, display=False
        )
        assert result is ax
        plt.close(fig)

    def test_two_layers_with_multilinks(self):
        """Test with two layers and inter-layer connections."""
        g1 = nx.Graph()
        g1.add_edge("A", "B")
        g1.add_edge("B", "C")
        
        g2 = nx.Graph()
        g2.add_edge("A", "D")
        g2.add_edge("D", "E")
        
        multilinks = {"cross": [("A", "A"), ("B", "D")]}
        
        fig, ax = plt.subplots()
        result = draw_multilayer_sankey(
            [g1, g2], multilinks, labels=["L1", "L2"], ax=ax, display=False
        )
        assert result is ax
        plt.close(fig)

    def test_three_layers_with_multilinks(self):
        """Test with three layers (simple flow diagram)."""
        graphs = []
        for i in range(3):
            g = nx.Graph()
            g.add_edge(f"A{i}", f"B{i}")
            graphs.append(g)
        
        # Add shared nodes across layers
        graphs[0].add_node("shared")
        graphs[1].add_node("shared")
        graphs[2].add_node("shared")
        
        multilinks = {"cross": [("shared", "shared")]}
        
        fig, ax = plt.subplots()
        result = draw_multilayer_sankey(
            graphs, multilinks, ax=ax, display=False
        )
        assert result is ax
        plt.close(fig)

    def test_many_layers_aggregated_diagram(self):
        """Test with many layers triggers aggregated diagram."""
        # Create 5 layers with shared nodes
        graphs = []
        for i in range(5):
            g = nx.Graph()
            g.add_edge(f"N{i}", "shared")
            g.add_edge("shared", f"M{i}")
            graphs.append(g)
        
        multilinks = {"cross": [("shared", "shared")]}
        
        fig, ax = plt.subplots()
        result = draw_multilayer_sankey(
            graphs, multilinks, ax=ax, display=False
        )
        assert result is ax
        plt.close(fig)

    def test_no_labels_uses_defaults(self):
        """Test that default labels are used when none provided."""
        g1 = nx.Graph()
        g1.add_edge("A", "B")
        
        g2 = nx.Graph()
        g2.add_edge("A", "C")
        
        multilinks = {"link": [("A", "A")]}
        
        fig, ax = plt.subplots()
        result = draw_multilayer_sankey(
            [g1, g2], multilinks, labels=None, ax=ax, display=False
        )
        assert result is ax
        plt.close(fig)

    def test_creates_figure_when_no_ax_provided(self):
        """Test that function creates a figure when no ax is provided."""
        g1 = nx.Graph()
        g1.add_edge("A", "B")
        
        result = draw_multilayer_sankey([g1], {}, display=False)
        assert result is not None
        plt.close('all')

    def test_multilinks_with_insufficient_edge_length(self):
        """Test handling of multilinks with edge tuples < 2 elements."""
        g = nx.Graph()
        g.add_edge("A", "B")
        
        # Edge tuple with only 1 element
        multilinks = {"weird": [("A",)]}
        
        fig, ax = plt.subplots()
        result = draw_multilayer_sankey(
            [g], multilinks, ax=ax, display=False
        )
        assert result is ax
        plt.close(fig)


class TestDrawSimpleFlowDiagram:
    """Test the simple flow diagram helper function."""

    def test_basic_flow_diagram(self):
        """Test drawing a basic simple flow diagram."""
        labels = ["Layer A", "Layer B"]
        layer_connections = [(0, 1, 5)]  # 5 connections from layer 0 to 1
        
        fig, ax = plt.subplots()
        _draw_simple_flow_diagram(labels, layer_connections, ax)
        plt.close(fig)

    def test_multiple_connections(self):
        """Test with multiple layer connections."""
        labels = ["L1", "L2", "L3"]
        layer_connections = [
            (0, 1, 10),
            (0, 2, 5),
            (1, 2, 15),
        ]
        
        fig, ax = plt.subplots()
        _draw_simple_flow_diagram(labels, layer_connections, ax)
        plt.close(fig)


class TestDrawAggregatedFlowDiagram:
    """Test the aggregated flow diagram helper function."""

    def test_basic_aggregated_diagram(self):
        """Test drawing a basic aggregated flow diagram."""
        import numpy as np
        
        labels = ["L1", "L2", "L3", "L4", "L5"]
        n_layers = 5
        flow_matrix = np.zeros((n_layers, n_layers), dtype=int)
        flow_matrix[0, 1] = 10
        flow_matrix[0, 2] = 5
        flow_matrix[1, 3] = 8
        flow_matrix[2, 4] = 3
        
        fig, ax = plt.subplots()
        _draw_aggregated_flow_diagram(labels, flow_matrix, n_layers, ax)
        plt.close(fig)

    def test_aggregated_with_many_connections(self):
        """Test aggregated diagram with many connections."""
        import numpy as np
        
        labels = [f"Layer{i}" for i in range(10)]
        n_layers = 10
        flow_matrix = np.zeros((n_layers, n_layers), dtype=int)
        
        # Create a dense connection pattern
        for i in range(n_layers):
            for j in range(i + 1, n_layers):
                flow_matrix[i, j] = (i + 1) * (j + 1)
        
        fig, ax = plt.subplots()
        _draw_aggregated_flow_diagram(labels, flow_matrix, n_layers, ax)
        plt.close(fig)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_multilinks_dict(self):
        """Test with empty multilinks dictionary."""
        g = nx.Graph()
        g.add_edge("A", "B")
        
        fig, ax = plt.subplots()
        result = draw_multilayer_sankey([g], {}, ax=ax, display=False)
        assert result is ax
        plt.close(fig)

    def test_multilinks_with_nonexistent_nodes(self):
        """Test multilinks referencing nodes that don't exist in any layer."""
        g = nx.Graph()
        g.add_edge("A", "B")
        
        # Multilinks with nodes not in any graph
        multilinks = {"cross": [("X", "Y")]}
        
        fig, ax = plt.subplots()
        result = draw_multilayer_sankey([g], multilinks, ax=ax, display=False)
        assert result is ax
        plt.close(fig)

    def test_large_flow_values(self):
        """Test handling of large flow values."""
        g1 = nx.Graph()
        g2 = nx.Graph()
        
        # Add many shared nodes to generate large flow values
        for i in range(100):
            g1.add_node(f"node{i}")
            g2.add_node(f"node{i}")
        
        multilinks = {"cross": [(f"node{i}", f"node{i}") for i in range(100)]}
        
        fig, ax = plt.subplots()
        result = draw_multilayer_sankey(
            [g1, g2], multilinks, ax=ax, display=False
        )
        assert result is ax
        plt.close(fig)

    def test_single_edge_multilink(self):
        """Test with multilink containing single edge."""
        g1 = nx.Graph()
        g1.add_edge("A", "B")
        
        g2 = nx.Graph()
        g2.add_edge("A", "C")
        
        multilinks = {"single": [("A", "A")]}
        
        fig, ax = plt.subplots()
        result = draw_multilayer_sankey(
            [g1, g2], multilinks, labels=["L1", "L2"], ax=ax, display=False
        )
        assert result is ax
        plt.close(fig)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
