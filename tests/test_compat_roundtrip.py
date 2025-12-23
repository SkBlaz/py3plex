"""
Tests for compat layer roundtrip conversions.

These tests verify that conversion to external formats and back preserves
graph structure, semantics, and attributes.
"""

import pytest
import numpy as np
import pandas as pd
import networkx as nx
import scipy.sparse as sp

from py3plex.compat import convert, GraphIR, to_ir, from_ir
from py3plex.compat.exceptions import CompatibilityError, ConversionNotSupportedError
from py3plex.io.schema import MultiLayerGraph, Node, Layer, Edge


@pytest.fixture
def simple_graph():
    """Create a simple graph for testing."""
    graph = MultiLayerGraph(directed=False)
    graph.add_layer(Layer(id="layer1"))
    
    graph.add_node(Node(id="A", attributes={"type": "hub", "value": 1.0}))
    graph.add_node(Node(id="B", attributes={"type": "leaf", "value": 2.0}))
    graph.add_node(Node(id="C", attributes={"type": "leaf", "value": 3.0}))
    
    graph.add_edge(Edge(src="A", dst="B", src_layer="layer1", dst_layer="layer1",
                       attributes={"weight": 1.0}))
    graph.add_edge(Edge(src="B", dst="C", src_layer="layer1", dst_layer="layer1",
                       attributes={"weight": 0.5}))
    
    return graph


@pytest.fixture
def directed_multigraph():
    """Create a directed multigraph for testing."""
    graph = MultiLayerGraph(directed=True)
    graph.add_layer(Layer(id="L1"))
    
    graph.add_node(Node(id=0, attributes={"name": "zero"}))
    graph.add_node(Node(id=1, attributes={"name": "one"}))
    graph.add_node(Node(id=2, attributes={"name": "two"}))
    
    # Add multiple edges between same nodes
    graph.add_edge(Edge(src=0, dst=1, src_layer="L1", dst_layer="L1",
                       attributes={"weight": 1.0, "type": "A"}))
    graph.add_edge(Edge(src=0, dst=1, src_layer="L1", dst_layer="L1",
                       attributes={"weight": 2.0, "type": "B"}))
    graph.add_edge(Edge(src=1, dst=2, src_layer="L1", dst_layer="L1",
                       attributes={"weight": 0.5, "type": "C"}))
    
    return graph


class TestNetworkXRoundtrip:
    """Test NetworkX conversion roundtrip."""
    
    def test_simple_graph_roundtrip(self, simple_graph):
        """Test simple graph roundtrip through NetworkX."""
        # Convert to NetworkX
        nx_graph = convert(simple_graph, "networkx")
        
        assert isinstance(nx_graph, nx.Graph)
        assert nx_graph.number_of_nodes() == 3
        assert nx_graph.number_of_edges() == 2
        
        # Convert back to py3plex
        result_graph = convert(nx_graph, "multilayer_graph")
        
        assert isinstance(result_graph, MultiLayerGraph)
        assert len(result_graph.nodes) == 3
        assert len(result_graph.edges) == 2
    
    def test_directed_multigraph_roundtrip(self, directed_multigraph):
        """Test directed multigraph roundtrip through NetworkX."""
        # Convert to NetworkX
        nx_graph = convert(directed_multigraph, "networkx")
        
        assert isinstance(nx_graph, nx.MultiDiGraph)
        assert nx_graph.is_directed()
        assert nx_graph.number_of_nodes() == 3
        assert nx_graph.number_of_edges() == 3
        
        # Convert back
        result_graph = convert(nx_graph, "multilayer_graph")
        
        assert result_graph.directed
        assert len(result_graph.nodes) == 3
        assert len(result_graph.edges) == 3
    
    def test_attributes_preserved(self, simple_graph):
        """Test that node and edge attributes are preserved."""
        nx_graph = convert(simple_graph, "networkx")
        result_graph = convert(nx_graph, "multilayer_graph")
        
        # Check node attributes
        node_a = next(n for n in result_graph.nodes if n.id == "A")
        assert node_a.attributes.get("type") == "hub"
        assert node_a.attributes.get("value") == 1.0
        
        # Check edge attributes
        edge_ab = next(e for e in result_graph.edges if e.src == "A" and e.dst == "B")
        assert edge_ab.attributes.get("weight") == 1.0


class TestScipySparseConversion:
    """Test SciPy sparse matrix conversion."""
    
    def test_simple_graph_to_sparse(self, simple_graph):
        """Test conversion to sparse matrix."""
        matrix = convert(simple_graph, "scipy_sparse", strict=False, sidecar="/tmp/test_sidecar")
        
        assert sp.issparse(matrix)
        assert matrix.shape == (3, 3)
        
        # Check symmetry for undirected graph
        assert np.allclose(matrix.toarray(), matrix.toarray().T)
    
    def test_strict_mode_rejects_attributes(self, simple_graph):
        """Test that strict mode rejects graphs with attributes."""
        with pytest.raises(CompatibilityError) as exc_info:
            convert(simple_graph, "scipy_sparse", strict=True)
        
        assert "attributes" in str(exc_info.value).lower()
    
    def test_multigraph_rejected_in_strict(self, directed_multigraph):
        """Test that multigraphs are rejected in strict mode."""
        with pytest.raises(CompatibilityError) as exc_info:
            convert(directed_multigraph, "scipy_sparse", strict=True)
        
        assert "multigraph" in str(exc_info.value).lower()
    
    def test_weight_extraction(self):
        """Test that edge weights are correctly extracted."""
        graph = MultiLayerGraph(directed=False)
        graph.add_layer(Layer(id="L"))
        graph.add_node(Node(id=0))
        graph.add_node(Node(id=1))
        graph.add_edge(Edge(src=0, dst=1, src_layer="L", dst_layer="L",
                           attributes={"weight": 5.0}))
        
        matrix = convert(graph, "scipy_sparse", strict=False)
        
        # Check weight value
        assert matrix[0, 1] == 5.0
        assert matrix[1, 0] == 5.0  # Symmetric


class TestIR:
    """Test Intermediate Representation."""
    
    def test_to_ir_from_multilayer_graph(self, simple_graph):
        """Test conversion to IR from MultiLayerGraph."""
        ir = to_ir(simple_graph)
        
        assert isinstance(ir, GraphIR)
        assert len(ir.nodes.node_id) == 3
        assert len(ir.edges.edge_id) == 2
        assert not ir.meta.directed
    
    def test_from_ir_to_multilayer_graph(self, simple_graph):
        """Test conversion from IR to MultiLayerGraph."""
        ir = to_ir(simple_graph)
        result = from_ir(ir, target_type="multilayer_graph")
        
        assert isinstance(result, MultiLayerGraph)
        assert len(result.nodes) == 3
        assert len(result.edges) == 2
    
    def test_ir_preserves_node_order(self, simple_graph):
        """Test that IR preserves node ordering."""
        ir = to_ir(simple_graph)
        
        assert ir.nodes.node_order == [0, 1, 2]
        assert len(set(ir.nodes.node_order)) == len(ir.nodes.node_order)
    
    def test_ir_preserves_edge_order(self, simple_graph):
        """Test that IR preserves edge ordering."""
        ir = to_ir(simple_graph)
        
        assert ir.edges.edge_order == [0, 1]
        assert len(set(ir.edges.edge_order)) == len(ir.edges.edge_order)


class TestConvertEntryPoint:
    """Test the main convert() entry point."""
    
    def test_invalid_target_raises(self, simple_graph):
        """Test that invalid target raises exception."""
        with pytest.raises(ConversionNotSupportedError):
            convert(simple_graph, "invalid_format")
    
    def test_networkx_target(self, simple_graph):
        """Test conversion to NetworkX via convert()."""
        result = convert(simple_graph, "networkx")
        assert isinstance(result, nx.Graph)
    
    def test_scipy_target(self, simple_graph):
        """Test conversion to scipy sparse via convert()."""
        result = convert(simple_graph, "scipy_sparse", strict=False)
        assert sp.issparse(result)
    
    def test_py3plex_target_from_networkx(self):
        """Test conversion from NetworkX to py3plex via convert()."""
        G = nx.Graph()
        G.add_edge("A", "B", weight=1.0)
        G.add_edge("B", "C", weight=0.5)
        
        result = convert(G, "py3plex")
        assert isinstance(result, MultiLayerGraph)
        assert len(result.nodes) == 3
        assert len(result.edges) == 2


@pytest.mark.skipif(
    True,  # Always skip unless igraph is available
    reason="igraph is an optional dependency"
)
class TestIgraphConversion:
    """Test igraph conversion (requires python-igraph)."""
    
    def test_igraph_conversion_unavailable(self, simple_graph):
        """Test that igraph conversion gives clear error when unavailable."""
        try:
            import igraph
            pytest.skip("igraph is available, test not applicable")
        except ImportError:
            pass
        
        with pytest.raises(ConversionNotSupportedError) as exc_info:
            convert(simple_graph, "igraph")
        
        assert "igraph" in str(exc_info.value).lower()


class TestErrorHandling:
    """Test error handling and validation."""
    
    def test_empty_graph(self):
        """Test handling of empty graph."""
        graph = MultiLayerGraph(directed=False)
        
        ir = to_ir(graph)
        assert len(ir.nodes.node_id) == 0
        assert len(ir.edges.edge_id) == 0
    
    def test_self_loops(self):
        """Test handling of self-loops."""
        graph = MultiLayerGraph(directed=True)
        graph.add_layer(Layer(id="L"))
        graph.add_node(Node(id="A"))
        graph.add_edge(Edge(src="A", dst="A", src_layer="L", dst_layer="L",
                           attributes={"weight": 1.0}))
        
        nx_graph = convert(graph, "networkx")
        assert nx_graph.has_edge("A", "A")
        
        result = convert(nx_graph, "multilayer_graph")
        assert len(result.edges) == 1
        assert result.edges[0].src == result.edges[0].dst


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
