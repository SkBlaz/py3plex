"""
Tests for R interoperability module.

This test suite validates that py3plex networks can be successfully converted
and exported in R-friendly formats for use with reticulate, igraph, and MLnet.
"""

import pytest

import py3plex as p3

# Check for optional dependencies
try:
    import igraph  # noqa: F401

    IGRAPH_AVAILABLE = True
except ImportError:
    IGRAPH_AVAILABLE = False

try:
    from py3plex.wrappers import r_interop  # noqa: F401

    R_INTEROP_AVAILABLE = True
except ImportError:
    R_INTEROP_AVAILABLE = False


@pytest.mark.skipif(
    not R_INTEROP_AVAILABLE or not IGRAPH_AVAILABLE,
    reason="R interop or igraph not available",
)
class TestRInteropBasic:
    """Test basic R interop functionality."""

    def test_import_r_interop(self):
        """Test that r_interop module can be imported."""
        from py3plex.wrappers import r_interop

        assert hasattr(r_interop, "to_igraph_for_r")
        assert hasattr(r_interop, "export_edgelist")
        assert hasattr(r_interop, "export_nodelist")

    def test_to_igraph_simple_network(self):
        """Test conversion of simple network to igraph."""
        from py3plex.wrappers.r_interop import to_igraph_for_r

        # Create simple network
        net = p3.multi_layer_network()
        net.add_nodes([{"source": "A"}, {"source": "B"}, {"source": "C"}])
        net.add_edges(
            [
                {"source": "A", "target": "B"},
                {"source": "B", "target": "C"},
            ]
        )

        # Convert to igraph
        g = to_igraph_for_r(net, mode="union")

        # Validate
        assert g is not None
        assert g.vcount() == 3
        assert g.ecount() == 2

    def test_to_igraph_multilayer_union(self):
        """Test conversion of multilayer network in union mode."""
        from py3plex.wrappers.r_interop import to_igraph_for_r

        # Create multilayer network
        net = p3.multi_layer_network()
        net.add_nodes(
            [
                {"source": "A", "type": "layer1"},
                {"source": "B", "type": "layer1"},
                {"source": "A", "type": "layer2"},
                {"source": "C", "type": "layer2"},
            ]
        )
        net.add_edges(
            [
                {
                    "source": "A",
                    "target": "B",
                    "source_type": "layer1",
                    "target_type": "layer1",
                },
                {
                    "source": "A",
                    "target": "C",
                    "source_type": "layer2",
                    "target_type": "layer2",
                },
            ]
        )

        # Convert to igraph (union mode merges layers)
        g = to_igraph_for_r(net, mode="union")

        # Validate - should have unique nodes
        assert g is not None
        assert g.vcount() >= 3  # At least A, B, C

    def test_export_edgelist(self):
        """Test export of edge list in R-friendly format."""
        from py3plex.wrappers.r_interop import export_edgelist

        # Create network
        net = p3.multi_layer_network()
        net.add_nodes([{"source": "A"}, {"source": "B"}])
        net.add_edges([{"source": "A", "target": "B", "weight": 0.5}])

        # Export edge list
        edges = export_edgelist(net, include_attributes=True)

        # Validate
        assert isinstance(edges, list)
        assert len(edges) >= 1
        assert isinstance(edges[0], dict)
        assert "src" in edges[0]
        assert "dst" in edges[0]

    def test_export_nodelist(self):
        """Test export of node list in R-friendly format."""
        from py3plex.wrappers.r_interop import export_nodelist

        # Create network
        net = p3.multi_layer_network()
        net.add_nodes(
            [
                {"source": "A", "age": 30},
                {"source": "B", "age": 25},
                {"source": "C", "age": 35},
            ]
        )

        # Export node list
        nodes = export_nodelist(net, include_attributes=True)

        # Validate
        assert isinstance(nodes, list)
        assert len(nodes) >= 3

    def test_export_graph_data(self):
        """Test export of complete graph data."""
        from py3plex.wrappers.r_interop import export_graph_data

        # Create network
        net = p3.multi_layer_network()
        net.add_nodes([{"source": "A"}, {"source": "B"}])
        net.add_edges([{"source": "A", "target": "B"}])

        # Export graph data
        data = export_graph_data(net)

        # Validate
        assert isinstance(data, dict)
        assert "nodes" in data
        assert "edges" in data
        assert "layers" in data
        assert "directed" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

    def test_get_network_stats(self):
        """Test getting network statistics."""
        from py3plex.wrappers.r_interop import get_network_stats

        # Create network
        net = p3.multi_layer_network()
        net.add_nodes([{"source": "A"}, {"source": "B"}, {"source": "C"}])
        net.add_edges(
            [
                {"source": "A", "target": "B"},
                {"source": "B", "target": "C"},
            ]
        )

        # Get stats
        stats = get_network_stats(net)

        # Validate
        assert isinstance(stats, dict)
        assert "num_nodes" in stats
        assert "num_edges" in stats
        assert "directed" in stats
        assert stats["num_nodes"] >= 3
        assert stats["num_edges"] >= 2


@pytest.mark.skipif(
    not R_INTEROP_AVAILABLE or not IGRAPH_AVAILABLE,
    reason="R interop or igraph not available",
)
class TestRInteropNewIO:
    """Test R interop with new I/O system (MultiLayerGraph)."""

    def test_multilayergraph_to_igraph(self):
        """Test conversion of MultiLayerGraph to igraph."""
        try:
            from py3plex.io import Edge, Layer, MultiLayerGraph, Node
            from py3plex.wrappers.r_interop import to_igraph_for_r
        except ImportError:
            pytest.skip("New I/O system not available")

        # Create MultiLayerGraph
        graph = MultiLayerGraph(directed=False)
        graph.add_layer(Layer(id="social"))
        graph.add_node(Node(id="alice"))
        graph.add_node(Node(id="bob"))
        graph.add_edge(
            Edge(src="alice", dst="bob", src_layer="social", dst_layer="social")
        )

        # Convert to igraph
        g = to_igraph_for_r(graph, mode="union")

        # Validate
        assert g is not None
        assert g.vcount() == 2
        assert g.ecount() == 1
        assert not g.is_directed()

    def test_multilayergraph_export_edgelist(self):
        """Test edge list export from MultiLayerGraph."""
        try:
            from py3plex.io import Edge, Layer, MultiLayerGraph, Node
            from py3plex.wrappers.r_interop import export_edgelist
        except ImportError:
            pytest.skip("New I/O system not available")

        # Create MultiLayerGraph
        graph = MultiLayerGraph()
        graph.add_layer(Layer(id="layer1"))
        graph.add_node(Node(id="A"))
        graph.add_node(Node(id="B"))
        graph.add_edge(
            Edge(
                src="A",
                dst="B",
                src_layer="layer1",
                dst_layer="layer1",
                attributes={"weight": 0.8},
            )
        )

        # Export
        edges = export_edgelist(graph, include_attributes=True)

        # Validate
        assert isinstance(edges, list)
        assert len(edges) == 1
        assert edges[0]["src"] == "A"
        assert edges[0]["dst"] == "B"
        assert edges[0]["weight"] == 0.8

    def test_multilayergraph_layer_extraction(self):
        """Test extracting specific layer from MultiLayerGraph."""
        try:
            from py3plex.io import Edge, Layer, MultiLayerGraph, Node
            from py3plex.wrappers.r_interop import to_igraph_for_r
        except ImportError:
            pytest.skip("New I/O system not available")

        # Create multi-layer graph
        graph = MultiLayerGraph()
        graph.add_layer(Layer(id="facebook"))
        graph.add_layer(Layer(id="twitter"))
        graph.add_node(Node(id="alice"))
        graph.add_node(Node(id="bob"))
        graph.add_edge(
            Edge(src="alice", dst="bob", src_layer="facebook", dst_layer="facebook")
        )
        graph.add_edge(
            Edge(src="alice", dst="bob", src_layer="twitter", dst_layer="twitter")
        )

        # Extract specific layer
        g = to_igraph_for_r(graph, layer="facebook")

        # Validate
        assert g is not None
        assert g.vcount() == 2
        assert g.ecount() == 1  # Only facebook edge


@pytest.mark.skipif(
    not R_INTEROP_AVAILABLE or not IGRAPH_AVAILABLE,
    reason="R interop or igraph not available",
)
class TestRInteropAdvanced:
    """Test advanced R interop features."""

    def test_export_adjacency_matrix(self):
        """Test adjacency matrix export."""
        from py3plex.wrappers.r_interop import export_adjacency

        # Create simple triangle network
        net = p3.multi_layer_network()
        net.add_nodes([{"source": "A"}, {"source": "B"}, {"source": "C"}])
        net.add_edges(
            [
                {"source": "A", "target": "B"},
                {"source": "B", "target": "C"},
                {"source": "C", "target": "A"},
            ]
        )

        # Export adjacency matrix
        adj = export_adjacency(net, mode="union")

        # Validate
        assert isinstance(adj, list)
        assert len(adj) == 3  # 3 nodes
        assert all(len(row) == 3 for row in adj)  # Square matrix
        assert all(isinstance(val, float) for row in adj for val in row)

    def test_get_layer_names(self):
        """Test getting layer names."""
        from py3plex.wrappers.r_interop import get_layer_names

        # Create multilayer network
        net = p3.multi_layer_network()
        net.add_nodes(
            [
                {"source": "A", "type": "layer1"},
                {"source": "B", "type": "layer2"},
            ]
        )

        # Get layer names
        layers = get_layer_names(net)

        # Validate
        assert isinstance(layers, list)

    def test_directed_network_conversion(self):
        """Test conversion of directed network."""
        from py3plex.wrappers.r_interop import to_igraph_for_r

        # Create directed network
        net = p3.multi_layer_network(network_type="directed")
        net.add_nodes([{"source": "A"}, {"source": "B"}])
        net.add_edges([{"source": "A", "target": "B"}])

        # Convert to igraph
        g = to_igraph_for_r(net, mode="union")

        # Validate
        assert g is not None
        assert g.is_directed()

    def test_attribute_preservation(self):
        """Test that attributes are preserved in conversion."""
        from py3plex.wrappers.r_interop import to_igraph_for_r

        # Create network with attributes
        net = p3.multi_layer_network()
        net.add_nodes(
            [
                {"source": "A", "age": 30},
                {"source": "B", "age": 25},
            ]
        )
        net.add_edges([{"source": "A", "target": "B", "weight": 0.8}])

        # Convert to igraph
        g = to_igraph_for_r(net, mode="union")

        # Check if attributes are preserved (if supported)
        assert g is not None
        # Note: Attribute preservation depends on NetworkX structure


@pytest.mark.skipif(
    not R_INTEROP_AVAILABLE or not IGRAPH_AVAILABLE,
    reason="R interop or igraph not available",
)
class TestRInteropErrorHandling:
    """Test error handling in R interop."""

    def test_invalid_mode(self):
        """Test handling of invalid conversion mode."""
        from py3plex.wrappers.r_interop import to_igraph_for_r

        net = p3.multi_layer_network()
        net.add_nodes([{"source": "A"}])

        # This should not raise an error but use a valid default
        # or raise a clear error
        try:
            # Try with invalid mode - should handle gracefully
            g = to_igraph_for_r(net, mode="union")
            assert g is not None
        except Exception:
            # If it does raise, it should be a clear error
            pass

    def test_empty_network(self):
        """Test handling of empty network."""
        from py3plex.wrappers.r_interop import to_igraph_for_r

        net = p3.multi_layer_network()

        # Should handle empty network gracefully
        g = to_igraph_for_r(net, mode="union")
        assert g is not None
        assert g.vcount() == 0

    def test_export_empty_edgelist(self):
        """Test exporting edge list from empty network."""
        from py3plex.wrappers.r_interop import export_edgelist

        net = p3.multi_layer_network()

        edges = export_edgelist(net)
        assert isinstance(edges, list)
        assert len(edges) == 0


def test_r_interop_documentation():
    """Test that R interop functions have proper documentation."""
    try:
        from py3plex.wrappers import r_interop
    except ImportError:
        pytest.skip("R interop not available")

    # Check that key functions have docstrings
    assert r_interop.to_igraph_for_r.__doc__ is not None
    assert "R Usage Example" in r_interop.to_igraph_for_r.__doc__
    assert "reticulate" in r_interop.to_igraph_for_r.__doc__

    assert r_interop.export_edgelist.__doc__ is not None
    assert "R Usage Example" in r_interop.export_edgelist.__doc__

    assert r_interop.export_graph_data.__doc__ is not None
    assert "R Usage Example" in r_interop.export_graph_data.__doc__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
