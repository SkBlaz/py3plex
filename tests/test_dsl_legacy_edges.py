"""Tests for legacy DSL edge query support via execute_query().

This module tests that the string-based legacy DSL supports edge queries.
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import execute_query


@pytest.fixture
def edge_test_network():
    """Create a multilayer network for edge query testing."""
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
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 2.0},
        {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 3.0},
        {'source': 'D', 'target': 'E', 'source_type': 'work', 'target_type': 'work', 'weight': 1.5},
        {'source': 'A', 'target': 'D', 'source_type': 'social', 'target_type': 'work', 'weight': 0.5},
    ]
    network.add_edges(edges)
    
    return network


class TestLegacyDSLEdgeQueries:
    """Test edge queries using the string-based legacy DSL."""
    
    def test_select_all_edges(self, edge_test_network):
        """Test selecting all edges."""
        result = execute_query(edge_test_network, 'SELECT edges')
        
        assert result['target'] == 'edges'
        assert 'edges' in result
        assert result['count'] == 5
        assert len(result['edges']) == 5
    
    def test_select_edges_with_weight_filter(self, edge_test_network):
        """Test filtering edges by weight."""
        result = execute_query(edge_test_network, 'SELECT edges WHERE weight > 1.0')
        
        assert result['target'] == 'edges'
        assert result['count'] == 3  # Edges with weight > 1.0
    
    def test_select_edges_compute_betweenness(self, edge_test_network):
        """Test computing edge betweenness."""
        result = execute_query(edge_test_network, 'SELECT edges COMPUTE edge_betweenness')
        
        assert result['target'] == 'edges'
        assert 'computed' in result
        assert 'edge_betweenness' in result['computed']
        assert len(result['computed']['edge_betweenness']) > 0
    
    def test_select_edges_from_layer(self, edge_test_network):
        """Test selecting edges from specific layer."""
        result = execute_query(edge_test_network, "SELECT edges IN LAYER 'social'")
        
        assert result['target'] == 'edges'
        # Should have edges involving the social layer
        assert result['count'] >= 3
    
    def test_backward_compatibility_nodes(self, edge_test_network):
        """Test that node queries still work."""
        result = execute_query(edge_test_network, 'SELECT nodes')
        
        assert result['target'] == 'nodes'
        assert result['count'] == 5
    
    def test_backward_compatibility_node_measures(self, edge_test_network):
        """Test that node measures still work."""
        result = execute_query(edge_test_network, 'SELECT nodes COMPUTE degree')
        
        assert result['target'] == 'nodes'
        assert 'computed' in result
        assert 'degree' in result['computed']
