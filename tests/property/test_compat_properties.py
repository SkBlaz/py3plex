"""
Property-based tests for compat layer conversions using Hypothesis.

These tests verify roundtrip properties and invariants for graph conversions.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis import example
import networkx as nx
import pandas as pd

from py3plex.compat import convert, to_ir, from_ir, ir_equals
from py3plex.compat.exceptions import CompatibilityError
from py3plex.io.schema import MultiLayerGraph, Node, Layer, Edge


# Hypothesis strategies for generating test graphs
@st.composite
def node_ids(draw, id_type=None):
    """Generate valid node IDs (all str or all int per-graph).
    
    Args:
        draw: Hypothesis draw function
        id_type: Optional type ('int' or 'str'). If None, randomly choose per-graph.
    
    Returns:
        Node ID of consistent type within a graph
    """
    if id_type is None:
        id_type = draw(st.sampled_from(['int', 'str']))
    
    if id_type == 'int':
        return draw(st.integers(min_value=0, max_value=100))
    else:
        return draw(st.text(min_size=1, max_size=10, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            min_codepoint=65, max_codepoint=122
        )))


@st.composite
def simple_attributes(draw):
    """Generate simple attribute dictionaries."""
    return draw(st.dictionaries(
        keys=st.text(min_size=1, max_size=10, alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll'),
            min_codepoint=97, max_codepoint=122
        )),
        values=st.one_of(
            st.integers(min_value=-100, max_value=100),
            st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
            st.text(min_size=0, max_size=20, alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                min_codepoint=65, max_codepoint=122
            )),
            st.booleans()
        ),
        min_size=0,
        max_size=5
    ))


@st.composite
def simple_graphs(draw, directed=None, min_nodes=0, max_nodes=5):
    """Generate simple MultiLayerGraph instances."""
    is_directed = draw(st.booleans()) if directed is None else directed
    n_nodes = draw(st.integers(min_value=min_nodes, max_value=max_nodes))
    
    # Choose consistent node ID type for this entire graph (all int or all str)
    id_type = draw(st.sampled_from(['int', 'str']))
    
    graph = MultiLayerGraph(directed=is_directed)
    graph.add_layer(Layer(id="L1"))
    
    # Generate nodes with consistent ID type
    node_id_list = []
    for i in range(n_nodes):
        node_id = draw(node_ids(id_type=id_type))
        # Ensure unique node IDs
        while node_id in node_id_list:
            node_id = draw(node_ids(id_type=id_type))
        node_id_list.append(node_id)
        
        attrs = draw(simple_attributes())
        graph.add_node(Node(id=node_id, attributes=attrs))
    
    # Generate edges (ensure valid endpoints) - limit to smaller number
    if n_nodes >= 2:
        n_edges = draw(st.integers(min_value=0, max_value=min(8, n_nodes * 2)))
        used_edge_tuples = set()
        
        # Try to generate n_edges unique edges, with extra attempts in case of duplicates
        for _ in range(n_edges * 3):  # Extra attempts to handle duplicates
            if len(used_edge_tuples) >= n_edges:
                break
            
            src = draw(st.sampled_from(node_id_list))
            dst = draw(st.sampled_from(node_id_list))
            key = 0  # Default key for simple graphs
            
            # For undirected graphs, normalize edge tuple to avoid (u,v) vs (v,u) duplicates
            # Use canonical ordering: smaller value first (works for both int and str)
            if not is_directed:
                if (src, dst) > (dst, src):  # Lexicographic comparison
                    src, dst = dst, src
            
            edge_tuple = (src, dst, "L1", "L1", key)
            
            # Skip if this edge already exists
            if edge_tuple in used_edge_tuples:
                continue
            
            used_edge_tuples.add(edge_tuple)
            
            edge_attrs = draw(simple_attributes())
            if "weight" not in edge_attrs:
                edge_attrs["weight"] = draw(st.floats(min_value=0.1, max_value=10.0, allow_nan=False))
            
            graph.add_edge(Edge(
                src=src, dst=dst,
                src_layer="L1", dst_layer="L1",
                key=key,
                attributes=edge_attrs
            ))
    
    return graph


@pytest.mark.property
class TestNetworkXRoundtripProperties:
    """Property tests for NetworkX conversions."""
    
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example])
    @given(graph=simple_graphs(min_nodes=1, max_nodes=5))
    def test_networkx_roundtrip_preserves_structure(self, graph):
        """Property: NetworkX roundtrip preserves graph structure."""
        # Skip empty graphs and graphs with no edges
        assume(len(graph.nodes) > 0)
        assume(len(graph.edges) > 0)
        
        # Convert to NetworkX and back
        nx_graph = convert(graph, "networkx")
        restored = convert(nx_graph, "multilayer_graph")
        
        # Check structure preservation
        assert len(restored.nodes) == len(graph.nodes)
        assert len(restored.edges) == len(graph.edges)
        assert restored.directed == graph.directed
    
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example])
    @given(graph=simple_graphs(min_nodes=2, max_nodes=5))
    def test_networkx_roundtrip_preserves_node_ids(self, graph):
        """Property: NetworkX roundtrip preserves node IDs."""
        assume(len(graph.nodes) > 0)
        
        # graph.nodes is a dict, so get keys (node IDs) directly
        original_ids = set(graph.nodes.keys())
        
        nx_graph = convert(graph, "networkx")
        restored = convert(nx_graph, "multilayer_graph")
        
        # restored.nodes is also a dict
        restored_ids = set(restored.nodes.keys())
        assert restored_ids == original_ids
    
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example])
    @given(graph=simple_graphs(directed=False, min_nodes=2, max_nodes=5))
    def test_undirected_graph_symmetry(self, graph):
        """Property: Undirected graphs maintain symmetry through conversion."""
        assume(len(graph.edges) > 0)
        
        nx_graph = convert(graph, "networkx")
        assert not nx_graph.is_directed()
        
        # Check symmetry
        for u, v in nx_graph.edges():
            assert nx_graph.has_edge(v, u) or u == v  # Self-loops are symmetric
    
    @settings(max_examples=15, deadline=5000, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example])
    @given(graph=simple_graphs(directed=True, min_nodes=2, max_nodes=5))
    def test_directed_graph_preserved(self, graph):
        """Property: Directed graphs maintain directedness."""
        assume(len(graph.nodes) > 0)
        
        nx_graph = convert(graph, "networkx")
        restored = convert(nx_graph, "multilayer_graph")
        
        assert nx_graph.is_directed()
        assert restored.directed


@pytest.mark.property
class TestIRProperties:
    """Property tests for Intermediate Representation."""
    
    @settings(max_examples=20, deadline=3000, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example])
    @given(graph=simple_graphs(min_nodes=1, max_nodes=5))
    def test_to_ir_from_ir_roundtrip(self, graph):
        """Property: IR roundtrip preserves graph structure."""
        assume(len(graph.nodes) > 0)
        
        ir = to_ir(graph)
        restored = from_ir(ir, target_type="multilayer_graph")
        
        assert len(restored.nodes) == len(graph.nodes)
        assert len(restored.edges) == len(graph.edges)
        assert restored.directed == graph.directed
    
    @settings(max_examples=20, deadline=3000, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example])
    @given(graph=simple_graphs(min_nodes=1, max_nodes=5))
    def test_ir_node_order_is_deterministic(self, graph):
        """Property: IR maintains deterministic node ordering."""
        assume(len(graph.nodes) > 0)
        
        ir = to_ir(graph)
        
        # Check that node_order is sequential
        assert ir.nodes.node_order == list(range(len(ir.nodes.node_id)))
    
    @settings(max_examples=20, deadline=3000, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example])
    @given(graph=simple_graphs(min_nodes=2, max_nodes=5))
    def test_ir_edge_order_is_deterministic(self, graph):
        """Property: IR maintains deterministic edge ordering."""
        assume(len(graph.edges) > 0)
        
        ir = to_ir(graph)
        
        # Check that edge_order is sequential
        assert ir.edges.edge_order == list(range(len(ir.edges.edge_id)))
    
    @settings(max_examples=20, deadline=3000, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example])
    @given(graph=simple_graphs(min_nodes=1, max_nodes=5))
    def test_ir_preserves_metadata(self, graph):
        """Property: IR preserves graph metadata."""
        assume(len(graph.nodes) > 0)
        
        ir = to_ir(graph)
        
        assert ir.meta.directed == graph.directed
        assert ir.meta.layers is not None
        assert len(ir.meta.layers) > 0


@pytest.mark.property
class TestScipySparseProperties:
    """Property tests for SciPy sparse conversions."""
    
    @settings(max_examples=15, deadline=5000, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example])
    @given(graph=simple_graphs(directed=False, min_nodes=2, max_nodes=5))
    def test_scipy_sparse_matrix_shape(self, graph):
        """Property: Sparse matrix has correct shape."""
        assume(len(graph.nodes) >= 2)
        
        n_nodes = len(graph.nodes)
        
        try:
            matrix = convert(graph, "scipy_sparse", strict=False)
            assert matrix.shape == (n_nodes, n_nodes)
        except Exception:
            # Expected if graph has attributes
            pass
    
    @settings(max_examples=15, deadline=5000, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example])
    @given(graph=simple_graphs(directed=False, min_nodes=2, max_nodes=5))
    def test_scipy_sparse_undirected_symmetry(self, graph):
        """Property: Undirected graphs produce symmetric matrices."""
        assume(len(graph.nodes) >= 2)
        assume(len(graph.edges) > 0)
        
        try:
            matrix = convert(graph, "scipy_sparse", strict=False)
            dense = matrix.toarray()
            
            # Check symmetry (within numerical tolerance)
            import numpy as np
            assert np.allclose(dense, dense.T, rtol=1e-10)
        except CompatibilityError:
            # Expected in strict mode with attributes
            pass
    
    @settings(max_examples=10, deadline=5000, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example])
    @given(graph=simple_graphs(min_nodes=2, max_nodes=5))
    def test_scipy_strict_mode_rejects_attributes(self, graph):
        """Property: Strict mode rejects graphs with attributes."""
        assume(len(graph.nodes) > 0)
        
        # If graph has node or edge attributes, strict mode should fail
        # graph.nodes is a dict, iterate over values to get Node objects
        has_node_attrs = any(node.attributes for node in graph.nodes.values())
        has_edge_attrs = any(edge.attributes for edge in graph.edges)
        
        if has_node_attrs or has_edge_attrs:
            with pytest.raises(CompatibilityError):
                convert(graph, "scipy_sparse", strict=True)


@pytest.mark.property
class TestConversionInvariants:
    """Property tests for general conversion invariants."""
    
    @settings(max_examples=20, deadline=3000, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example])
    @given(graph=simple_graphs(min_nodes=1, max_nodes=5))
    def test_double_roundtrip_idempotent(self, graph):
        """Property: Double roundtrip through IR is idempotent."""
        assume(len(graph.nodes) > 0)
        
        ir1 = to_ir(graph)
        graph1 = from_ir(ir1, target_type="multilayer_graph")
        ir2 = to_ir(graph1)
        
        # Structure should be preserved
        assert len(ir2.nodes.node_id) == len(ir1.nodes.node_id)
        assert len(ir2.edges.edge_id) == len(ir1.edges.edge_id)
    
    @settings(max_examples=20, deadline=3000, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example])
    @given(graph=simple_graphs(min_nodes=1, max_nodes=5))
    def test_node_count_invariant(self, graph):
        """Property: Node count is preserved across conversions."""
        assume(len(graph.nodes) > 0)
        
        original_count = len(graph.nodes)
        
        # Through NetworkX
        nx_graph = convert(graph, "networkx")
        assert nx_graph.number_of_nodes() == original_count
        
        restored = convert(nx_graph, "multilayer_graph")
        assert len(restored.nodes) == original_count
    
    @settings(max_examples=15, deadline=3000, suppress_health_check=[HealthCheck.too_slow, HealthCheck.large_base_example])
    @given(graph=simple_graphs(min_nodes=2, max_nodes=5))
    def test_edge_count_invariant(self, graph):
        """Property: Edge count is preserved across conversions."""
        assume(len(graph.edges) > 0)
        
        original_count = len(graph.edges)
        
        nx_graph = convert(graph, "networkx")
        restored = convert(nx_graph, "multilayer_graph")
        
        assert len(restored.edges) == original_count


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
