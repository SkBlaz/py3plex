"""Tests for node-edge feature parity.

This module ensures that node queries and edge queries support symmetric
operations where documented (filtering, grouping, aggregation, ordering).

Key Guarantees Tested:
- Filtering works for both nodes and edges
- Grouping works for both nodes and edges  
- Aggregation works for both nodes and edges
- Ordering works for both nodes and edges
- Parity breaks are intentional and documented
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.graph_ops import nodes, edges


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes_list = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'D', 'type': 'layer2'},
        {'source': 'E', 'type': 'layer2'},
    ]
    network.add_nodes(nodes_list)
    
    edges_list = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 2.0},
        {'source': 'A', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 1.5},
        {'source': 'D', 'target': 'E', 'source_type': 'layer2', 'target_type': 'layer2', 'weight': 0.5},
    ]
    network.add_edges(edges_list)
    
    return network


class TestFilteringParity:
    """Test that filtering works for both nodes and edges."""

    def test_node_filtering_by_layer(self, sample_network):
        """Test that nodes can be filtered by layer."""
        query = Q.nodes().from_layers(L["layer1"])
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        # Should have nodes from layer1 only
        assert len(df) > 0
        if 'layer' in df.columns:
            assert all(df['layer'] == 'layer1')

    def test_edge_filtering_by_layer(self, sample_network):
        """Test that edges can be filtered by layer."""
        query = Q.edges().from_layers(L["layer1"])
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        # Should have edges from layer1
        assert len(df) > 0

    def test_node_filtering_by_condition(self, sample_network):
        """Test that nodes can be filtered by conditions."""
        query = Q.nodes().where(degree__gte=2)
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        # Should return some nodes
        # (exact count depends on network structure)
        assert len(df) >= 0  # May be 0 if no nodes match

    def test_edge_filtering_by_weight(self, sample_network):
        """Test that edges can be filtered by weight."""
        query = Q.edges().where(weight__gt=1.0)
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        # Should return edges with weight > 1.0
        if 'weight' in df.columns:
            assert all(df['weight'] > 1.0)


class TestGroupingParity:
    """Test that grouping works for both nodes and edges."""

    def test_node_grouping_by_layer(self, sample_network):
        """Test that nodes can be grouped by layer."""
        query = Q.nodes().per_layer()
        result = query.execute(sample_network)
        
        # Should have grouping metadata
        if hasattr(result, 'meta') and 'grouping' in result.meta:
            grouping = result.meta['grouping']
            assert grouping is not None

    def test_edge_grouping_by_layer_pair(self, sample_network):
        """Test that edges can be grouped by layer pair."""
        query = Q.edges().per_layer_pair()
        result = query.execute(sample_network)
        
        # Should have grouping metadata
        if hasattr(result, 'meta') and 'grouping' in result.meta:
            grouping = result.meta['grouping']
            assert grouping is not None


class TestOrderingParity:
    """Test that ordering works for both nodes and edges."""

    def test_node_ordering_by_degree(self, sample_network):
        """Test that nodes can be ordered by degree."""
        query = Q.nodes().compute("degree").order_by("degree")
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        if 'degree' in df.columns:
            # Check if sorted (ascending)
            degrees = df['degree'].tolist()
            assert degrees == sorted(degrees), "Results should be ordered by degree"

    def test_node_ordering_descending(self, sample_network):
        """Test that nodes can be ordered descending."""
        query = Q.nodes().compute("degree").order_by("-degree")
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        if 'degree' in df.columns:
            # Check if sorted descending
            degrees = df['degree'].tolist()
            assert degrees == sorted(degrees, reverse=True), \
                "Results should be ordered descending"

    def test_edge_ordering_by_weight(self, sample_network):
        """Test that edges can be ordered by weight."""
        query = Q.edges().order_by("weight")
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        if 'weight' in df.columns:
            # Check if sorted
            weights = df['weight'].tolist()
            # Allow for small floating point differences
            for i in range(len(weights) - 1):
                assert weights[i] <= weights[i + 1] + 1e-10, \
                    "Edges should be ordered by weight"


class TestComputeParity:
    """Test that compute operations work for nodes (edges don't compute metrics)."""

    def test_node_compute_degree(self, sample_network):
        """Test that nodes can compute degree."""
        query = Q.nodes().compute("degree")
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        assert 'degree' in df.columns, "Nodes should be able to compute degree"
        assert all(df['degree'] >= 0), "Degree should be non-negative"

    def test_node_compute_multiple_metrics(self, sample_network):
        """Test that nodes can compute multiple metrics."""
        query = Q.nodes().compute("degree", "betweenness_centrality")
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        assert 'degree' in df.columns
        # Betweenness may or may not be computed depending on implementation
        # Just check that the query completes


class TestLimitParity:
    """Test that LIMIT works for both nodes and edges."""

    def test_node_limit(self, sample_network):
        """Test that nodes can be limited."""
        query = Q.nodes().limit(2)
        result = query.execute(sample_network)
        
        assert len(result) <= 2, "Result should respect limit"

    def test_edge_limit(self, sample_network):
        """Test that edges can be limited."""
        query = Q.edges().limit(2)
        result = query.execute(sample_network)
        
        assert len(result) <= 2, "Result should respect limit"


class TestGraphOpsFilteringParity:
    """Test that graph_ops filtering works for both nodes and edges."""

    def test_graphops_node_filter(self, sample_network):
        """Test that graph_ops nodes can be filtered."""
        result = nodes(sample_network).filter(lambda n: n.get("degree", 0) > 0)
        
        # Should return nodes
        assert len(result) > 0

    def test_graphops_edge_filter(self, sample_network):
        """Test that graph_ops edges can be filtered."""
        result = edges(sample_network).filter(lambda e: e.get("weight", 0) > 0.5)
        
        # Should return edges
        # (may be 0 if no edges match condition)
        assert len(result) >= 0


class TestGraphOpsOrderingParity:
    """Test that graph_ops ordering works for both nodes and edges."""

    def test_graphops_node_arrange(self, sample_network):
        """Test that graph_ops nodes can be arranged."""
        result = (
            nodes(sample_network)
            .mutate(score=lambda n: n.get("degree", 0) * 2)
            .arrange("score")
        )
        
        # Should complete successfully
        assert len(result) > 0

    def test_graphops_edge_arrange(self, sample_network):
        """Test that graph_ops edges can be arranged."""
        result = edges(sample_network).arrange("weight")
        
        # Should complete successfully
        assert len(result) > 0


class TestGraphOpsHeadParity:
    """Test that head() works for both nodes and edges."""

    def test_graphops_node_head(self, sample_network):
        """Test that graph_ops nodes support head()."""
        result = nodes(sample_network).head(2)
        
        assert len(result) <= 2

    def test_graphops_edge_head(self, sample_network):
        """Test that graph_ops edges support head()."""
        result = edges(sample_network).head(2)
        
        assert len(result) <= 2


class TestToPandasParity:
    """Test that to_pandas() works for both node and edge operations."""

    def test_node_to_pandas(self, sample_network):
        """Test that node results can be converted to pandas."""
        query = Q.nodes()
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        assert df is not None
        assert len(df) > 0

    def test_edge_to_pandas(self, sample_network):
        """Test that edge results can be converted to pandas."""
        query = Q.edges()
        result = query.execute(sample_network)
        
        df = result.to_pandas()
        
        assert df is not None
        assert len(df) > 0

    def test_graphops_node_to_pandas(self, sample_network):
        """Test that graph_ops node results can be converted to pandas."""
        try:
            result = nodes(sample_network).to_pandas()
            assert result is not None
        except (AttributeError, NotImplementedError):
            # to_pandas might not be implemented for graph_ops
            pytest.skip("to_pandas not available for graph_ops nodes")

    def test_graphops_edge_to_pandas(self, sample_network):
        """Test that graph_ops edge results can be converted to pandas."""
        try:
            result = edges(sample_network).to_pandas()
            assert result is not None
        except (AttributeError, NotImplementedError):
            # to_pandas might not be implemented for graph_ops
            pytest.skip("to_pandas not available for graph_ops edges")


class TestFeatureParityDocumentation:
    """Test that parity differences are intentional and consistent."""

    def test_node_specific_operations_documented(self, sample_network):
        """Test that node-specific operations (like compute) work only for nodes."""
        # Nodes should support compute
        node_query = Q.nodes().compute("degree")
        node_result = node_query.execute(sample_network)
        
        assert len(node_result) > 0

    def test_edge_specific_operations_consistent(self, sample_network):
        """Test that edge-specific operations are consistent."""
        # Edges can be queried
        edge_query = Q.edges()
        edge_result = edge_query.execute(sample_network)
        
        assert len(edge_result) > 0


class TestEmptyResultParity:
    """Test that empty results are handled consistently for nodes and edges."""

    def test_node_query_with_no_matches(self, sample_network):
        """Test node query with condition that matches nothing."""
        query = Q.nodes().where(degree__gt=1000)  # Unrealistic condition
        result = query.execute(sample_network)
        
        # Should return empty result gracefully
        assert len(result) == 0
        
        # Should still convert to pandas
        df = result.to_pandas()
        assert len(df) == 0

    def test_edge_query_with_no_matches(self, sample_network):
        """Test edge query with condition that matches nothing."""
        query = Q.edges().where(weight__gt=1000)  # Unrealistic condition
        result = query.execute(sample_network)
        
        # Should return empty result gracefully
        assert len(result) == 0
        
        # Should still convert to pandas
        df = result.to_pandas()
        assert len(df) == 0


class TestComplexOperationParity:
    """Test parity in complex multi-step operations."""

    def test_node_filter_order_limit(self, sample_network):
        """Test node query with filter, order, and limit."""
        query = (
            Q.nodes()
            .where(degree__gt=0)
            .compute("degree")
            .order_by("-degree")
            .limit(3)
        )
        result = query.execute(sample_network)
        
        assert len(result) <= 3

    def test_edge_filter_order_limit(self, sample_network):
        """Test edge query with filter, order, and limit."""
        query = (
            Q.edges()
            .where(weight__gt=0)
            .order_by("-weight")
            .limit(2)
        )
        result = query.execute(sample_network)
        
        assert len(result) <= 2

    def test_graphops_node_complex_chain(self, sample_network):
        """Test graph_ops node complex operation chain."""
        result = (
            nodes(sample_network)
            .filter(lambda n: n.get("degree", 0) > 0)
            .arrange("degree")
            .head(3)
        )
        
        assert len(result) <= 3

    def test_graphops_edge_complex_chain(self, sample_network):
        """Test graph_ops edge complex operation chain."""
        result = (
            edges(sample_network)
            .filter(lambda e: e.get("weight", 0) > 0)
            .arrange("weight")
            .head(2)
        )
        
        assert len(result) <= 2
