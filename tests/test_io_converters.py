"""
Tests for py3plex.io.converters module.

This module tests conversion between MultiLayerGraph and external graph libraries.
"""

import pytest
import networkx as nx

from py3plex.exceptions import ConversionError
from py3plex.io.converters import to_networkx, from_networkx
from py3plex.io.schema import MultiLayerGraph, Node, Layer, Edge


class TestToNetworkx:
    """Tests for to_networkx conversion function."""

    @pytest.fixture
    def simple_multilayer_graph(self):
        """Create a simple multilayer graph for testing."""
        graph = MultiLayerGraph(directed=False)
        
        # Add layers
        graph.add_layer(Layer(id="layer1", attributes={"color": "red"}))
        graph.add_layer(Layer(id="layer2", attributes={"color": "blue"}))
        
        # Add nodes
        graph.add_node(Node(id="A", attributes={"type": "hub"}))
        graph.add_node(Node(id="B", attributes={"type": "leaf"}))
        graph.add_node(Node(id="C", attributes={"type": "leaf"}))
        
        # Add intra-layer edges
        graph.add_edge(Edge(src="A", dst="B", src_layer="layer1", dst_layer="layer1", attributes={"weight": 1.0}))
        graph.add_edge(Edge(src="B", dst="C", src_layer="layer1", dst_layer="layer1", attributes={"weight": 0.5}))
        graph.add_edge(Edge(src="A", dst="C", src_layer="layer2", dst_layer="layer2", attributes={"weight": 2.0}))
        
        # Add inter-layer edge
        graph.add_edge(Edge(src="A", dst="A", src_layer="layer1", dst_layer="layer2", attributes={"weight": 0.8}))
        
        return graph

    @pytest.fixture
    def directed_multilayer_graph(self):
        """Create a directed multilayer graph for testing."""
        graph = MultiLayerGraph(directed=True)
        
        graph.add_layer(Layer(id="L1"))
        graph.add_node(Node(id="X"))
        graph.add_node(Node(id="Y"))
        graph.add_edge(Edge(src="X", dst="Y", src_layer="L1", dst_layer="L1"))
        
        return graph

    def test_to_networkx_union_mode(self, simple_multilayer_graph):
        """Test conversion with union mode."""
        G = to_networkx(simple_multilayer_graph, mode="union")
        
        # Check graph type
        assert isinstance(G, nx.MultiGraph)
        assert not G.is_directed()
        
        # Check nodes
        assert G.number_of_nodes() == 3
        assert "A" in G.nodes
        assert "B" in G.nodes
        assert "C" in G.nodes
        
        # Check node attributes preserved
        assert G.nodes["A"]["type"] == "hub"
        
        # Check edges
        assert G.number_of_edges() == 4

    def test_to_networkx_intersection_mode(self, simple_multilayer_graph):
        """Test conversion with intersection mode."""
        G = to_networkx(simple_multilayer_graph, mode="intersection")
        
        # Check graph type
        assert isinstance(G, nx.MultiGraph)
        
        # In intersection mode, only edges present in ALL layers are kept
        # Since no edge is in both layers, we expect few edges
        assert G.number_of_nodes() == 3

    def test_to_networkx_multiplex_mode(self, simple_multilayer_graph):
        """Test conversion with multiplex mode."""
        G = to_networkx(simple_multilayer_graph, mode="multiplex")
        
        # Check graph type
        assert isinstance(G, nx.MultiGraph)
        
        # In multiplex mode, nodes are (node_id, layer_id) tuples
        # 3 nodes * 2 layers = 6 node tuples
        assert G.number_of_nodes() == 6
        
        # Check that nodes are tuples
        for node in G.nodes():
            assert isinstance(node, tuple)
            assert len(node) == 2

    def test_to_networkx_directed(self, directed_multilayer_graph):
        """Test conversion of directed graph."""
        G = to_networkx(directed_multilayer_graph, mode="union")
        
        assert isinstance(G, nx.MultiDiGraph)
        assert G.is_directed()

    def test_to_networkx_preserves_graph_attributes(self, simple_multilayer_graph):
        """Test that graph attributes are preserved."""
        simple_multilayer_graph.attributes["name"] = "test_graph"
        simple_multilayer_graph.attributes["version"] = "1.0"
        
        G = to_networkx(simple_multilayer_graph, mode="union")
        
        assert G.graph["name"] == "test_graph"
        assert G.graph["version"] == "1.0"


class TestFromNetworkx:
    """Tests for from_networkx conversion function."""

    def test_from_networkx_union_mode(self):
        """Test conversion from NetworkX with union mode."""
        G = nx.Graph()
        G.add_node("A", weight=1.0)
        G.add_node("B", weight=2.0)
        G.add_edge("A", "B", strength=0.5)
        
        mlg = from_networkx(G, mode="union", default_layer="default")
        
        # Check structure
        assert len(mlg.nodes) == 2
        assert len(mlg.layers) == 1
        assert "default" in mlg.layers
        
        # Check node attributes
        assert mlg.nodes["A"].attributes["weight"] == 1.0

    def test_from_networkx_union_mode_multigraph(self):
        """Test conversion from MultiGraph with union mode."""
        G = nx.MultiGraph()
        G.add_edge("A", "B", key=0, weight=1.0)
        G.add_edge("A", "B", key=1, weight=2.0)  # Parallel edge
        G.add_edge("B", "C", key=0, weight=0.5)
        
        mlg = from_networkx(G, mode="union", default_layer="L1")
        
        # Check structure
        assert len(mlg.nodes) == 3
        assert len(mlg.edges) == 3  # Including parallel edge

    def test_from_networkx_multiplex_mode(self):
        """Test conversion from NetworkX with multiplex mode."""
        G = nx.Graph()
        # Add nodes as (node_id, layer_id) tuples
        G.add_node(("A", "layer1"), type="hub")
        G.add_node(("A", "layer2"), type="hub")
        G.add_node(("B", "layer1"), type="leaf")
        G.add_edge(("A", "layer1"), ("B", "layer1"), weight=1.0)
        
        mlg = from_networkx(G, mode="multiplex")
        
        # Check structure
        assert len(mlg.layers) == 2
        assert "layer1" in mlg.layers
        assert "layer2" in mlg.layers
        assert len(mlg.nodes) == 2  # A and B

    def test_from_networkx_multiplex_invalid_node_format(self):
        """Test error handling for invalid node format in multiplex mode."""
        G = nx.Graph()
        G.add_node("simple_node")  # Not a tuple
        G.add_edge("simple_node", "another")
        
        with pytest.raises(ConversionError, match="node IDs must be"):
            from_networkx(G, mode="multiplex")

    def test_from_networkx_intersection_mode_error(self):
        """Test that intersection mode raises error."""
        G = nx.Graph()
        G.add_edge("A", "B")
        
        # With icontract, this raises ViolationError
        # Without icontract, this raises ConversionError
        with pytest.raises((ConversionError, Exception)):
            from_networkx(G, mode="intersection")

    def test_from_networkx_preserves_graph_attributes(self):
        """Test that graph attributes are preserved."""
        G = nx.Graph()
        G.graph["name"] = "test_graph"
        G.graph["created"] = "2024-01-01"
        G.add_edge("A", "B")
        
        mlg = from_networkx(G, mode="union")
        
        assert mlg.attributes["name"] == "test_graph"
        assert mlg.attributes["created"] == "2024-01-01"

    def test_from_networkx_directed(self):
        """Test conversion of directed NetworkX graph."""
        G = nx.DiGraph()
        G.add_edge("A", "B")
        G.add_edge("B", "C")
        
        mlg = from_networkx(G, mode="union")
        
        assert mlg.directed is True


class TestRoundTrip:
    """Test roundtrip conversions."""

    def test_union_mode_roundtrip(self):
        """Test that union mode roundtrip preserves structure."""
        # Create original
        original = MultiLayerGraph(directed=False)
        original.add_layer(Layer(id="L1"))
        original.add_node(Node(id="A", attributes={"val": 1}))
        original.add_node(Node(id="B", attributes={"val": 2}))
        original.add_edge(Edge(src="A", dst="B", src_layer="L1", dst_layer="L1", attributes={"w": 0.5}))
        
        # Convert to NetworkX and back
        G = to_networkx(original, mode="union")
        restored = from_networkx(G, mode="union", default_layer="L1")
        
        # Check preserved
        assert len(restored.nodes) == 2
        assert len(restored.edges) == 1

    def test_multiplex_mode_roundtrip(self):
        """Test that multiplex mode roundtrip preserves structure."""
        # Create original
        original = MultiLayerGraph(directed=False)
        original.add_layer(Layer(id="L1"))
        original.add_layer(Layer(id="L2"))
        original.add_node(Node(id="A"))
        original.add_node(Node(id="B"))
        original.add_edge(Edge(src="A", dst="B", src_layer="L1", dst_layer="L1"))
        original.add_edge(Edge(src="A", dst="B", src_layer="L2", dst_layer="L2"))
        
        # Convert to NetworkX and back
        G = to_networkx(original, mode="multiplex")
        restored = from_networkx(G, mode="multiplex")
        
        # Check preserved
        assert len(restored.layers) == 2
        assert len(restored.nodes) == 2
        assert len(restored.edges) == 2


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_graph(self):
        """Test conversion of empty graph."""
        mlg = MultiLayerGraph()
        G = to_networkx(mlg, mode="union")
        
        assert G.number_of_nodes() == 0
        assert G.number_of_edges() == 0

    def test_graph_with_layers_but_no_nodes(self):
        """Test conversion of graph with layers but no nodes."""
        mlg = MultiLayerGraph()
        mlg.add_layer(Layer(id="L1"))
        mlg.add_layer(Layer(id="L2"))
        
        G = to_networkx(mlg, mode="union")
        
        assert G.number_of_nodes() == 0

    def test_parallel_edges(self):
        """Test handling of parallel edges."""
        mlg = MultiLayerGraph()
        mlg.add_layer(Layer(id="L1"))
        mlg.add_node(Node(id="A"))
        mlg.add_node(Node(id="B"))
        
        # Add parallel edges with different keys
        mlg.add_edge(Edge(src="A", dst="B", src_layer="L1", dst_layer="L1", key=0))
        mlg.add_edge(Edge(src="A", dst="B", src_layer="L1", dst_layer="L1", key=1))
        
        G = to_networkx(mlg, mode="union")
        
        # Should have both edges
        assert G.number_of_edges() == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
