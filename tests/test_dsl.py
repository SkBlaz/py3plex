"""Tests for the DSL (Domain-Specific Language) module.

Tests cover:
- Query parsing and tokenization
- Condition evaluation
- Node filtering
- Centrality computation
- Error handling
- Convenience functions
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import (
    execute_query,
    format_result,
    select_nodes_by_layer,
    select_high_degree_nodes,
    compute_centrality_for_layer,
    DSLSyntaxError,
    DSLExecutionError,
    _tokenize_query,
)


@pytest.fixture
def sample_network():
    """Create a sample multilayer network for testing."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'D', 'type': 'layer1'},
        {'source': 'A', 'type': 'layer2'},
        {'source': 'B', 'type': 'layer2'},
        {'source': 'C', 'type': 'layer2'},
    ]
    network.add_nodes(nodes)
    
    # Add edges
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 1.0},
        {'source': 'C', 'target': 'D', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 1.0},
        {'source': 'A', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 1.0},
        {'source': 'A', 'target': 'B', 'source_type': 'layer2', 'target_type': 'layer2', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'layer2', 'target_type': 'layer2', 'weight': 1.0},
    ]
    network.add_edges(edges)
    
    return network


class TestTokenization:
    """Test query tokenization."""
    
    def test_basic_tokenization(self):
        """Test basic query tokenization."""
        tokens = _tokenize_query('SELECT nodes WHERE layer="social"')
        assert 'SELECT' in tokens
        assert 'nodes' in tokens
        assert 'WHERE' in tokens
        assert 'layer' in tokens
        assert 'social' in tokens
    
    def test_tokenization_with_operators(self):
        """Test tokenization with comparison operators."""
        tokens = _tokenize_query('SELECT nodes WHERE degree > 5')
        assert '>' in tokens
        assert '5' in tokens
    
    def test_tokenization_with_logical_operators(self):
        """Test tokenization with AND/OR."""
        tokens = _tokenize_query('SELECT nodes WHERE layer="social" AND degree > 3')
        assert 'AND' in tokens or 'and' in [t.upper() for t in tokens]


class TestBasicQueries:
    """Test basic query execution."""
    
    def test_select_all_nodes(self, sample_network):
        """Test selecting all nodes without filter."""
        result = execute_query(sample_network, 'SELECT nodes')
        
        assert result['target'] == 'nodes'
        assert result['count'] > 0
        assert 'nodes' in result
        assert len(result['nodes']) == result['count']
    
    def test_select_by_layer(self, sample_network):
        """Test selecting nodes by layer."""
        result = execute_query(sample_network, 'SELECT nodes WHERE layer="layer1"')
        
        assert result['count'] > 0
        # All returned nodes should be from layer1
        for node in result['nodes']:
            assert node[1] == 'layer1'
    
    def test_select_by_degree(self, sample_network):
        """Test selecting nodes by degree."""
        result = execute_query(sample_network, 'SELECT nodes WHERE degree > 1')
        
        assert result['count'] >= 0
        # Verify all returned nodes have degree > 1
        for node in result['nodes']:
            degree = sample_network.core_network.degree(node)
            assert degree > 1


class TestComplexQueries:
    """Test complex queries with multiple conditions."""
    
    def test_and_operator(self, sample_network):
        """Test AND operator in queries."""
        result = execute_query(sample_network, 
                              'SELECT nodes WHERE layer="layer1" AND degree >= 2')
        
        # All nodes should be from layer1 and have degree >= 2
        for node in result['nodes']:
            assert node[1] == 'layer1'
            degree = sample_network.core_network.degree(node)
            assert degree >= 2
    
    def test_or_operator(self, sample_network):
        """Test OR operator in queries."""
        result = execute_query(sample_network,
                              'SELECT nodes WHERE layer="layer1" OR layer="layer2"')
        
        # All nodes should be from either layer1 or layer2
        for node in result['nodes']:
            assert node[1] in ['layer1', 'layer2']
    
    def test_comparison_operators(self, sample_network):
        """Test various comparison operators."""
        # Greater than
        result = execute_query(sample_network, 'SELECT nodes WHERE degree > 1')
        assert result['count'] >= 0
        
        # Less than or equal
        result = execute_query(sample_network, 'SELECT nodes WHERE degree <= 2')
        assert result['count'] >= 0
        
        # Not equal
        result = execute_query(sample_network, 'SELECT nodes WHERE layer!="layer1"')
        for node in result['nodes']:
            assert node[1] != 'layer1'


class TestComputeClause:
    """Test COMPUTE clause for computing measures."""
    
    def test_compute_degree(self, sample_network):
        """Test computing degree for nodes."""
        result = execute_query(sample_network, 
                              'SELECT nodes WHERE layer="layer1" COMPUTE degree')
        
        assert 'computed' in result
        assert 'degree' in result['computed']
        assert len(result['computed']['degree']) > 0
    
    def test_compute_centrality(self, sample_network):
        """Test computing centrality measures."""
        result = execute_query(sample_network,
                              'SELECT nodes WHERE layer="layer1" COMPUTE betweenness_centrality')
        
        assert 'computed' in result
        assert 'betweenness_centrality' in result['computed']
        
        # Centrality values should be between 0 and 1
        for value in result['computed']['betweenness_centrality'].values():
            assert 0 <= value <= 1
    
    def test_compute_multiple_measures(self, sample_network):
        """Test computing multiple measures."""
        result = execute_query(sample_network,
                              'SELECT nodes WHERE layer="layer1" COMPUTE degree degree_centrality')
        
        assert 'computed' in result
        assert 'degree' in result['computed']
        assert 'degree_centrality' in result['computed']


class TestErrorHandling:
    """Test error handling in DSL."""
    
    def test_empty_query(self, sample_network):
        """Test error on empty query."""
        with pytest.raises(DSLSyntaxError):
            execute_query(sample_network, '')
    
    def test_missing_select(self, sample_network):
        """Test error when SELECT is missing."""
        with pytest.raises(DSLSyntaxError):
            execute_query(sample_network, 'nodes WHERE layer="layer1"')
    
    def test_invalid_target(self, sample_network):
        """Test error on invalid SELECT target."""
        with pytest.raises(DSLSyntaxError):
            execute_query(sample_network, 'SELECT invalid_target')
    
    def test_unknown_measure(self, sample_network):
        """Test error on unknown measure."""
        # Unknown measure returns empty computed dict but doesn't raise
        result = execute_query(sample_network, 'SELECT nodes COMPUTE unknown_measure')
        # The error is logged but execution continues
        assert 'computed' in result
        # Unknown measure should have empty or error result
        assert result['computed'].get('unknown_measure', {}) == {}


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_select_nodes_by_layer(self, sample_network):
        """Test select_nodes_by_layer function."""
        nodes = select_nodes_by_layer(sample_network, 'layer1')
        
        assert len(nodes) > 0
        for node in nodes:
            assert node[1] == 'layer1'
    
    def test_select_high_degree_nodes(self, sample_network):
        """Test select_high_degree_nodes function."""
        min_deg = 1
        nodes = select_high_degree_nodes(sample_network, min_degree=min_deg)
        
        assert len(nodes) >= 0
        for node in nodes:
            degree = sample_network.core_network.degree(node)
            assert degree > min_deg  # Function uses > (exclusive)
    
    def test_select_high_degree_nodes_with_layer(self, sample_network):
        """Test select_high_degree_nodes with layer filter."""
        min_deg = 1
        nodes = select_high_degree_nodes(sample_network, min_degree=min_deg, layer='layer1')
        
        for node in nodes:
            assert node[1] == 'layer1'
            degree = sample_network.core_network.degree(node)
            assert degree > min_deg  # Function uses > (exclusive)
    
    def test_compute_centrality_for_layer(self, sample_network):
        """Test compute_centrality_for_layer function."""
        centrality = compute_centrality_for_layer(sample_network, 'layer1', 
                                                  'degree_centrality')
        
        assert len(centrality) > 0
        for value in centrality.values():
            assert 0 <= value <= 1


class TestResultFormatting:
    """Test result formatting."""
    
    def test_format_basic_result(self, sample_network):
        """Test formatting a basic result."""
        result = execute_query(sample_network, 'SELECT nodes WHERE layer="layer1"')
        formatted = format_result(result, limit=5)
        
        assert isinstance(formatted, str)
        assert 'Query:' in formatted
        assert 'Count:' in formatted
    
    def test_format_result_with_computed(self, sample_network):
        """Test formatting a result with computed measures."""
        result = execute_query(sample_network,
                              'SELECT nodes WHERE layer="layer1" COMPUTE degree')
        formatted = format_result(result, limit=5)
        
        assert 'Computed measures:' in formatted
        assert 'degree' in formatted


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_query_with_no_results(self, sample_network):
        """Test query that returns no results."""
        result = execute_query(sample_network, 'SELECT nodes WHERE degree > 100')
        
        assert result['count'] == 0
        assert len(result['nodes']) == 0
    
    def test_query_on_empty_network(self):
        """Test query on empty network."""
        empty_network = multinet.multi_layer_network(directed=False)
        result = execute_query(empty_network, 'SELECT nodes')
        
        assert result['count'] == 0
    
    def test_case_insensitive_keywords(self, sample_network):
        """Test that keywords are case-insensitive."""
        result1 = execute_query(sample_network, 'SELECT nodes WHERE layer="layer1"')
        result2 = execute_query(sample_network, 'select nodes where layer="layer1"')
        
        # Both should return same results
        assert result1['count'] == result2['count']


class TestQueryValidation:
    """Test query validation and syntax checking."""
    
    def test_validate_layer_string(self, sample_network):
        """Test that layer values are treated as strings."""
        result = execute_query(sample_network, 'SELECT nodes WHERE layer="layer1"')
        assert result['count'] > 0
    
    def test_validate_numeric_comparison(self, sample_network):
        """Test numeric comparisons work correctly."""
        result = execute_query(sample_network, 'SELECT nodes WHERE degree > 0')
        assert result['count'] > 0


class TestIntegration:
    """Integration tests with realistic scenarios."""
    
    def test_hub_identification_workflow(self, sample_network):
        """Test a complete hub identification workflow."""
        # Find high-degree nodes in layer1
        result = execute_query(sample_network,
                              'SELECT nodes WHERE layer="layer1" AND degree >= 2')
        hubs = result['nodes']
        
        # Compute centrality for hubs
        result = execute_query(sample_network,
                              'SELECT nodes WHERE layer="layer1" AND degree >= 2 COMPUTE betweenness_centrality')
        
        assert 'computed' in result
        assert len(result['computed']['betweenness_centrality']) <= len(hubs)
    
    def test_layer_comparison_workflow(self, sample_network):
        """Test layer comparison workflow."""
        # Get nodes from each layer
        layer1_result = execute_query(sample_network, 'SELECT nodes WHERE layer="layer1"')
        layer2_result = execute_query(sample_network, 'SELECT nodes WHERE layer="layer2"')
        
        # Both layers should have nodes
        assert layer1_result['count'] > 0
        assert layer2_result['count'] > 0
        
        # Layers should be different
        assert layer1_result['count'] != layer2_result['count'] or \
               set(layer1_result['nodes']) != set(layer2_result['nodes'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
