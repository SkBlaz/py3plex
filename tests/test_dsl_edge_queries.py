"""Tests for DSL v2 edge query support.

This module tests comprehensive edge query functionality including:
- Basic edge selection
- Edge filters (intralayer, interlayer, weight)
- Edge measures (edge betweenness)
- Edge ordering and limiting
- Edge result exports (to_pandas, to_networkx)
- Error handling for incompatible measures
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import (
    Q,
    L,
    QueryResult,
    execute_ast,
    Query,
    SelectStmt,
    Target,
    DslExecutionError,
)


@pytest.fixture
def edge_test_network():
    """Create a multilayer network for edge query testing.
    
    Network structure:
    - Layer 'social': A-B, B-C, A-C (triangle)
    - Layer 'work': D-E
    - Interlayer: A-D (social to work)
    """
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'work'},
        {'source': 'E', 'type': 'work'},
    ]
    network.add_nodes(nodes)
    
    edges = [
        # Social layer edges (intralayer)
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 2.0},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 3.0},
        # Work layer edges (intralayer)
        {'source': 'D', 'target': 'E', 'source_type': 'work', 'target_type': 'work', 'weight': 1.5},
        # Interlayer edge
        {'source': 'A', 'target': 'D', 'source_type': 'social', 'target_type': 'work', 'weight': 0.5},
    ]
    network.add_edges(edges)
    
    return network


class TestBasicEdgeSelection:
    """Test basic edge selection without filters."""
    
    def test_select_all_edges(self, edge_test_network):
        """Test selecting all edges."""
        result = Q.edges().execute(edge_test_network)
        
        assert isinstance(result, QueryResult)
        assert result.target == "edges"
        assert result.count == 5  # Total edges in network
        assert len(result.edges) == 5
    
    def test_edge_result_properties(self, edge_test_network):
        """Test that edge result has correct properties."""
        result = Q.edges().execute(edge_test_network)
        
        # Check that edges property works
        edges = result.edges
        assert len(edges) == 5
        
        # Check that count matches
        assert result.count == len(edges)
        
        # Verify edges have correct structure
        for edge in edges:
            assert isinstance(edge, tuple)
            assert len(edge) >= 2
            # Each endpoint should be a (node, layer) tuple
            assert isinstance(edge[0], tuple) and len(edge[0]) >= 2
            assert isinstance(edge[1], tuple) and len(edge[1]) >= 2
    
    def test_select_edges_from_layer(self, edge_test_network):
        """Test selecting edges from specific layer."""
        result = Q.edges().from_layers(L["social"]).execute(edge_test_network)
        
        assert result.count >= 3  # At least 3 social layer edges
        
        # Verify all edges involve the social layer
        for edge in result.edges:
            source_layer = edge[0][1]
            target_layer = edge[1][1]
            assert source_layer == "social" or target_layer == "social"


class TestEdgePredicates:
    """Test edge-specific predicates (intralayer, interlayer)."""
    
    def test_intralayer_edges(self, edge_test_network):
        """Test filtering for intralayer edges only."""
        result = Q.edges().where(intralayer=True).execute(edge_test_network)
        
        # Should have 4 intralayer edges (3 in social, 1 in work)
        assert result.count == 4
        
        # Verify all edges are intralayer
        for edge in result.edges:
            source_layer = edge[0][1]
            target_layer = edge[1][1]
            assert source_layer == target_layer
    
    def test_interlayer_edges(self, edge_test_network):
        """Test filtering for interlayer edges."""
        result = Q.edges().where(interlayer=("social", "work")).execute(edge_test_network)
        
        # Should have 1 interlayer edge
        assert result.count == 1
        
        # Verify it's the A-D edge
        edge = result.edges[0]
        source_layer = edge[0][1]
        target_layer = edge[1][1]
        assert (source_layer == "social" and target_layer == "work") or \
               (source_layer == "work" and target_layer == "social")
    
    def test_intralayer_with_layer_filter(self, edge_test_network):
        """Test combining intralayer predicate with layer filter."""
        result = (
            Q.edges()
            .from_layers(L["social"])
            .where(intralayer=True)
            .execute(edge_test_network)
        )
        
        # Should have 3 social intralayer edges
        assert result.count == 3
        
        for edge in result.edges:
            assert edge[0][1] == "social"
            assert edge[1][1] == "social"


class TestEdgeAttributeFilters:
    """Test filtering edges by attributes."""
    
    def test_filter_by_weight(self, edge_test_network):
        """Test filtering edges by weight."""
        result = Q.edges().where(weight__gt=1.0).execute(edge_test_network)
        
        # Should have 3 edges with weight > 1.0 (2.0, 3.0, 1.5)
        assert result.count == 3
    
    def test_filter_by_weight_range(self, edge_test_network):
        """Test filtering edges by weight range."""
        result = (
            Q.edges()
            .where(weight__ge=1.0, weight__le=2.0)
            .execute(edge_test_network)
        )
        
        # Should have edges with weight in [1.0, 2.0]
        assert result.count >= 2
    
    def test_filter_by_source_layer(self, edge_test_network):
        """Test filtering by source_layer attribute."""
        result = Q.edges().where(source_layer="social").execute(edge_test_network)
        
        # Should have edges originating from social layer
        assert result.count >= 3
        
        for edge in result.edges:
            assert edge[0][1] == "social"


class TestEdgeMeasures:
    """Test computing measures on edges."""
    
    def test_edge_betweenness(self, edge_test_network):
        """Test computing edge betweenness centrality."""
        result = Q.edges().compute("edge_betweenness").execute(edge_test_network)
        
        assert "edge_betweenness" in result.attributes
        betweenness = result.attributes["edge_betweenness"]
        
        # Should have betweenness value for each edge
        assert len(betweenness) > 0
        
        # All values should be floats
        for value in betweenness.values():
            assert isinstance(value, (int, float))
    
    def test_edge_betweenness_with_alias(self, edge_test_network):
        """Test computing edge betweenness with alias."""
        result = (
            Q.edges()
            .compute("edge_betweenness", alias="eb")
            .execute(edge_test_network)
        )
        
        assert "eb" in result.attributes
        assert "edge_betweenness" not in result.attributes
    
    def test_node_measure_on_edges_fails(self, edge_test_network):
        """Test that node-only measures fail on edge queries."""
        with pytest.raises(DslExecutionError) as exc_info:
            Q.edges().compute("degree").execute(edge_test_network)
        
        # Check error message mentions incompatibility
        error_msg = str(exc_info.value).lower()
        assert "node" in error_msg or "edge" in error_msg


class TestEdgeOrdering:
    """Test ordering and limiting edge results."""
    
    def test_order_by_weight(self, edge_test_network):
        """Test ordering edges by weight attribute."""
        result = Q.edges().order_by("weight").execute(edge_test_network)
        
        # Verify edges are ordered by weight
        weights = []
        for edge in result.edges:
            if len(edge) >= 3 and isinstance(edge[2], dict):
                weights.append(edge[2].get('weight', 1.0))
        
        # Check ordering (should be ascending by default)
        if len(weights) > 1:
            for i in range(len(weights) - 1):
                assert weights[i] <= weights[i + 1]
    
    def test_order_by_weight_desc(self, edge_test_network):
        """Test ordering edges by weight descending."""
        result = Q.edges().order_by("-weight").execute(edge_test_network)
        
        # Get weights from edges
        weights = []
        for edge in result.edges:
            if len(edge) >= 3 and isinstance(edge[2], dict):
                weights.append(edge[2].get('weight', 1.0))
        
        # Check descending order
        if len(weights) > 1:
            for i in range(len(weights) - 1):
                assert weights[i] >= weights[i + 1]
    
    def test_limit_edges(self, edge_test_network):
        """Test limiting number of edge results."""
        result = Q.edges().limit(2).execute(edge_test_network)
        
        assert result.count == 2
        assert len(result.edges) == 2
    
    def test_order_and_limit(self, edge_test_network):
        """Test combining ordering and limiting."""
        result = (
            Q.edges()
            .where(intralayer=True)
            .order_by("-weight")
            .limit(2)
            .execute(edge_test_network)
        )
        
        # Should get top 2 intralayer edges by weight
        assert result.count == 2
        
        # Get weights
        weights = []
        for edge in result.edges:
            if len(edge) >= 3 and isinstance(edge[2], dict):
                weights.append(edge[2].get('weight', 1.0))
        
        # Should be descending
        if len(weights) == 2:
            assert weights[0] >= weights[1]


class TestEdgeResultExports:
    """Test exporting edge results to different formats."""
    
    def test_edge_to_pandas(self, edge_test_network):
        """Test exporting edge results to pandas DataFrame."""
        result = Q.edges().execute(edge_test_network)
        df = result.to_pandas()
        
        # Check DataFrame has expected columns
        assert 'source' in df.columns
        assert 'target' in df.columns
        assert 'source_layer' in df.columns
        assert 'target_layer' in df.columns
        assert 'weight' in df.columns
        
        # Check row count matches edge count
        assert len(df) == result.count
    
    def test_edge_to_pandas_with_measures(self, edge_test_network):
        """Test exporting edges with computed measures to pandas."""
        result = (
            Q.edges()
            .compute("edge_betweenness", alias="eb")
            .execute(edge_test_network)
        )
        df = result.to_pandas()
        
        # Check that computed measure is in DataFrame
        assert 'eb' in df.columns
        
        # Check no null values in betweenness
        assert df['eb'].notna().all()
    
    def test_edge_to_networkx(self, edge_test_network):
        """Test exporting edge results to NetworkX graph."""
        result = (
            Q.edges()
            .where(intralayer=True)
            .execute(edge_test_network)
        )
        
        subgraph = result.to_networkx(edge_test_network)
        
        # Check that subgraph has the correct number of edges
        assert subgraph.number_of_edges() == result.count
        
        # Verify all edges are in the subgraph
        for edge in result.edges:
            u, v = edge[0], edge[1]
            assert subgraph.has_edge(u, v) or subgraph.has_edge(v, u)
    
    def test_edge_to_networkx_preserves_attributes(self, edge_test_network):
        """Test that to_networkx preserves edge attributes."""
        result = Q.edges().limit(3).execute(edge_test_network)
        subgraph = result.to_networkx(edge_test_network)
        
        # Check that edges have weight attribute
        for u, v, data in subgraph.edges(data=True):
            assert 'weight' in data


class TestComplexEdgeQueries:
    """Test complex edge queries combining multiple features."""
    
    def test_filtered_edges_with_measures(self, edge_test_network):
        """Test filtering edges and computing measures."""
        result = (
            Q.edges()
            .where(intralayer=True, weight__gt=1.0)
            .compute("edge_betweenness")
            .order_by("-edge_betweenness")
            .limit(2)
            .execute(edge_test_network)
        )
        
        # Should have at most 2 edges
        assert result.count <= 2
        
        # Should have betweenness values
        assert "edge_betweenness" in result.attributes
    
    def test_layer_specific_edge_query(self, edge_test_network):
        """Test querying edges from specific layer."""
        result = (
            Q.edges()
            .from_layers(L["social"])
            .where(intralayer=True)
            .compute("edge_betweenness")
            .execute(edge_test_network)
        )
        
        # Should have 3 social intralayer edges
        assert result.count == 3
        
        # All should be in social layer
        for edge in result.edges:
            assert edge[0][1] == "social"
            assert edge[1][1] == "social"
    
    def test_multiple_layer_edge_query(self, edge_test_network):
        """Test querying edges from multiple layers."""
        result = (
            Q.edges()
            .from_layers(L["social"] + L["work"])
            .where(intralayer=True)
            .execute(edge_test_network)
        )
        
        # Should have all intralayer edges (4 total)
        assert result.count == 4


class TestEdgeQueryBackwardCompatibility:
    """Test that edge queries don't break existing node queries."""
    
    def test_node_query_still_works(self, edge_test_network):
        """Test that node queries work as before."""
        result = Q.nodes().execute(edge_test_network)
        
        assert result.target == "nodes"
        assert result.count == 5  # 5 nodes in network
    
    def test_node_measures_still_work(self, edge_test_network):
        """Test that node measures still work correctly."""
        result = Q.nodes().compute("degree").execute(edge_test_network)
        
        assert "degree" in result.attributes
        assert result.count == 5
