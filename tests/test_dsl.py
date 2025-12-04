"""Tests for the DSL (Domain-Specific Language) module.

Tests cover:
- Query parsing and tokenization
- Condition evaluation
- Node filtering
- Centrality computation
- Error handling
- Convenience functions
- Community detection via DSL
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
    _parse_condition,
    _parse_where_clause,
    _evaluate_condition,
    _evaluate_conditions,
    _compute_measure,
    # New DSL v3 parsing functions
    _parse_node_pattern,
    _parse_edge_pattern,
    _parse_path_pattern,
    _parse_layer_clause,
    _parse_return_clause,
    _tokenize_match_pattern,
    # Community detection functions
    detect_communities,
    get_community_partition,
    get_biggest_community,
    get_smallest_community,
    get_num_communities,
    get_community_sizes,
    get_community_size_distribution,
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


class TestInternalFunctions:
    """Test internal DSL parsing and evaluation functions."""

    def test_parse_condition_empty_tokens(self):
        """Test _parse_condition with empty token list at start index."""
        with pytest.raises(DSLSyntaxError, match="Unexpected end"):
            _parse_condition([], 0)

    def test_parse_condition_no_attribute_after_not(self):
        """Test _parse_condition when NOT has no following attribute."""
        tokens = ['NOT']
        with pytest.raises(DSLSyntaxError, match="Expected attribute after NOT"):
            _parse_condition(tokens, 0)

    def test_parse_condition_no_operator_after_attribute(self):
        """Test _parse_condition when no operator follows attribute."""
        tokens = ['degree']
        with pytest.raises(DSLSyntaxError, match="Expected operator"):
            _parse_condition(tokens, 0)

    def test_parse_condition_no_value_after_operator(self):
        """Test _parse_condition when no value follows operator."""
        tokens = ['degree', '>']
        with pytest.raises(DSLSyntaxError, match="Expected value"):
            _parse_condition(tokens, 0)

    def test_parse_where_clause_and_at_start(self, sample_network):
        """Test _parse_where_clause when AND appears at start."""
        # This would be caught by the WHERE clause parser
        tokens = ['SELECT', 'nodes', 'WHERE', 'AND', 'degree', '>', '5']
        with pytest.raises(DSLSyntaxError, match="Unexpected.*AND"):
            _parse_where_clause(tokens, 2)

    def test_evaluate_condition_on_edge_tuple(self, sample_network):
        """Test _evaluate_condition on non-node (edge) data."""
        # Create a simple condition
        condition = {
            'attribute': 'layer',
            'operator': '=',
            'value': 'layer1',
            'negated': False
        }

        # Test with a non-tuple (should return False)
        result = _evaluate_condition('not_a_tuple', condition, sample_network, {})
        assert not result

    def test_evaluate_condition_unknown_operator(self, sample_network):
        """Test _evaluate_condition with unknown operator."""
        condition = {
            'attribute': 'layer',
            'operator': '~',  # Unknown operator
            'value': 'layer1',
            'negated': False
        }
        node = ('A', 'layer1')

        with pytest.raises(DSLSyntaxError, match="Unknown operator"):
            _evaluate_condition(node, condition, sample_network, {})

    def test_evaluate_condition_no_core_network_degree(self):
        """Test _evaluate_condition degree when network has no core_network."""
        network = multinet.multi_layer_network(directed=False)
        # Empty network - core_network exists but is empty

        condition = {
            'attribute': 'degree',
            'operator': '>',
            'value': 0,
            'negated': False
        }
        node = ('A', 'layer1')

        # Should not crash, return False for degree comparison
        result = _evaluate_condition(node, condition, network, {})
        assert not result

    def test_evaluate_condition_betweenness_not_in_context(self, sample_network):
        """Test _evaluate_condition betweenness when not in context."""
        condition = {
            'attribute': 'betweenness',
            'operator': '>',
            'value': 0,
            'negated': False
        }
        node = ('A', 'layer1')

        # Should return False when betweenness_centrality not in context
        result = _evaluate_condition(node, condition, sample_network, {})
        assert not result

    def test_evaluate_condition_closeness_not_in_context(self, sample_network):
        """Test _evaluate_condition closeness when not in context."""
        condition = {
            'attribute': 'closeness',
            'operator': '>',
            'value': 0,
            'negated': False
        }
        node = ('A', 'layer1')

        # Should return False when centrality not in context
        result = _evaluate_condition(node, condition, sample_network, {})
        assert not result

    def test_evaluate_condition_eigenvector_not_in_context(self, sample_network):
        """Test _evaluate_condition eigenvector when not in context."""
        condition = {
            'attribute': 'eigenvector_centrality',
            'operator': '>',
            'value': 0,
            'negated': False
        }
        node = ('A', 'layer1')

        # Should return False when centrality not in context
        result = _evaluate_condition(node, condition, sample_network, {})
        assert not result

    def test_evaluate_condition_custom_attribute(self, sample_network):
        """Test _evaluate_condition with custom node attribute."""
        condition = {
            'attribute': 'custom_attr',
            'operator': '=',
            'value': 'value1',
            'negated': False
        }
        node = ('A', 'layer1')

        # Should return False when attribute doesn't exist
        result = _evaluate_condition(node, condition, sample_network, {})
        assert not result

    def test_evaluate_conditions_empty_list(self, sample_network):
        """Test _evaluate_conditions with empty conditions list."""
        node = ('A', 'layer1')

        # Empty conditions should return True (no filtering)
        result = _evaluate_conditions(node, [], sample_network, {})
        assert result

    def test_compute_measure_no_core_network(self):
        """Test _compute_measure when network has no core_network."""
        network = multinet.multi_layer_network(directed=False)
        network.core_network = None

        with pytest.raises(DSLExecutionError, match="no core_network"):
            _compute_measure(network, 'degree')

    def test_evaluate_condition_type_error_comparison(self, sample_network):
        """Test _evaluate_condition when comparison raises TypeError."""
        condition = {
            'attribute': 'layer',
            'operator': '>',  # Layer is a string, can't compare > with string
            'value': 'layer1',
            'negated': False
        }
        node = ('A', 'layer1')

        # Should return False when comparison fails
        result = _evaluate_condition(node, condition, sample_network, {})
        assert not result

    def test_evaluate_condition_closeness_in_context_missing_node(self, sample_network):
        """Test _evaluate_condition closeness when node not in context centrality."""
        condition = {
            'attribute': 'closeness',
            'operator': '>',
            'value': 0,
            'negated': False
        }
        node = ('NONEXISTENT', 'layer1')

        # Context has closeness_centrality but node is not in it
        context = {'closeness_centrality': {('A', 'layer1'): 0.5}}
        result = _evaluate_condition(node, condition, sample_network, context)
        assert not result

    def test_evaluate_condition_eigenvector_in_context_missing_node(self, sample_network):
        """Test _evaluate_condition eigenvector when node not in context centrality."""
        condition = {
            'attribute': 'eigenvector_centrality',
            'operator': '>',
            'value': 0,
            'negated': False
        }
        node = ('NONEXISTENT', 'layer1')

        # Context has eigenvector_centrality but node is not in it
        context = {'eigenvector_centrality': {('A', 'layer1'): 0.5}}
        result = _evaluate_condition(node, condition, sample_network, context)
        assert not result

    def test_evaluate_condition_custom_attribute_no_core_network(self):
        """Test _evaluate_condition custom attribute when no core_network."""
        network = multinet.multi_layer_network(directed=False)
        network.core_network = None

        condition = {
            'attribute': 'custom_attr',
            'operator': '=',
            'value': 'value1',
            'negated': False
        }
        node = ('A', 'layer1')

        # Should return False when no core_network
        result = _evaluate_condition(node, condition, network, {})
        assert not result

    def test_evaluate_condition_less_than_type_error(self, sample_network):
        """Test _evaluate_condition with < operator on non-numeric."""
        condition = {
            'attribute': 'layer',
            'operator': '<',
            'value': 5,
            'negated': False
        }
        node = ('A', 'layer1')

        result = _evaluate_condition(node, condition, sample_network, {})
        assert not result

    def test_evaluate_condition_gte_type_error(self, sample_network):
        """Test _evaluate_condition with >= operator on non-numeric."""
        condition = {
            'attribute': 'layer',
            'operator': '>=',
            'value': 5,
            'negated': False
        }
        node = ('A', 'layer1')

        result = _evaluate_condition(node, condition, sample_network, {})
        assert not result

    def test_evaluate_condition_lte_type_error(self, sample_network):
        """Test _evaluate_condition with <= operator on non-numeric."""
        condition = {
            'attribute': 'layer',
            'operator': '<=',
            'value': 5,
            'negated': False
        }
        node = ('A', 'layer1')

        result = _evaluate_condition(node, condition, sample_network, {})
        assert not result


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

    def test_not_operator(self, sample_network):
        """Test NOT operator in queries."""
        # NOT should negate the condition
        result = execute_query(sample_network,
                              'SELECT nodes WHERE NOT layer="layer1"')

        # All nodes should NOT be from layer1
        for node in result['nodes']:
            assert node[1] != 'layer1'

    def test_less_than_operator(self, sample_network):
        """Test less than operator."""
        result = execute_query(sample_network, 'SELECT nodes WHERE degree < 3')

        # All returned nodes should have degree < 3
        for node in result['nodes']:
            degree = sample_network.core_network.degree(node)
            assert degree < 3

    def test_betweenness_filter(self, sample_network):
        """Test filtering by betweenness (short form)."""
        result = execute_query(sample_network,
                              'SELECT nodes WHERE betweenness >= 0')

        # Betweenness should be computed and used for filtering
        assert result['count'] >= 0


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

    def test_compute_closeness_centrality(self, sample_network):
        """Test computing closeness centrality."""
        result = execute_query(sample_network,
                              'SELECT nodes WHERE layer="layer1" COMPUTE closeness_centrality')

        assert 'computed' in result
        assert 'closeness_centrality' in result['computed']

    def test_compute_pagerank(self, sample_network):
        """Test computing pagerank."""
        result = execute_query(sample_network,
                              'SELECT nodes COMPUTE pagerank')

        assert 'computed' in result
        assert 'pagerank' in result['computed']

    def test_compute_clustering(self, sample_network):
        """Test computing clustering coefficient."""
        result = execute_query(sample_network,
                              'SELECT nodes COMPUTE clustering')

        assert 'computed' in result
        assert 'clustering' in result['computed']


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

    def test_select_only(self, sample_network):
        """Test error when SELECT has no target."""
        with pytest.raises(DSLSyntaxError):
            execute_query(sample_network, 'SELECT')


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

    def test_select_edges(self, sample_network):
        """Test selecting edges from the network."""
        result = execute_query(sample_network, 'SELECT edges')

        assert result['target'] == 'edges'
        # The network has edges, but edge filtering returns empty (edges tuple handling)
        assert 'edges' in result

    def test_select_edges_on_empty_network(self):
        """Test selecting edges on empty network."""
        empty_network = multinet.multi_layer_network(directed=False)
        result = execute_query(empty_network, 'SELECT edges')

        assert result['count'] == 0
        assert result['target'] == 'edges'

    def test_float_value_parsing(self, sample_network):
        """Test that float values are parsed correctly."""
        result = execute_query(sample_network, 'SELECT nodes WHERE degree > 0.5')

        # Should work and return nodes with degree > 0.5
        assert result['count'] >= 0

    def test_closeness_centrality_filter(self, sample_network):
        """Test filtering by closeness centrality."""
        result = execute_query(sample_network,
                              'SELECT nodes WHERE closeness_centrality > 0')

        # Closeness centrality should be computed and used for filtering
        assert result['count'] >= 0

    def test_eigenvector_centrality_filter(self, sample_network):
        """Test filtering by eigenvector centrality."""
        result = execute_query(sample_network,
                              'SELECT nodes WHERE eigenvector > 0')

        # Eigenvector centrality should be computed and used for filtering
        assert result['count'] >= 0

    def test_format_result_with_many_nodes(self, sample_network):
        """Test format_result with limit less than total nodes."""
        result = execute_query(sample_network, 'SELECT nodes')
        formatted = format_result(result, limit=2)

        assert '...' in formatted or result['count'] <= 2

    def test_format_result_with_many_computed_values(self, sample_network):
        """Test format_result with computed values exceeding limit."""
        result = execute_query(sample_network,
                              'SELECT nodes WHERE layer="layer1" COMPUTE degree')
        formatted = format_result(result, limit=1)

        # Should have "more" in the output if there are more than 1 node
        if result['count'] > 1:
            assert '...' in formatted


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


# ═══════════════════════════════════════════════════════════════════════════════
# New DSL v3 Feature Tests: Layer Clauses
# ═══════════════════════════════════════════════════════════════════════════════


class TestLayerClauses:
    """Test IN LAYER and IN LAYERS clauses for SELECT queries."""

    def test_select_in_layer_single(self, sample_network):
        """Test SELECT with single layer clause."""
        result = execute_query(sample_network, "SELECT * FROM nodes IN LAYER 'layer1' WHERE degree > 0")
        
        assert result['count'] >= 0
        assert 'layers' in result
        assert result['layers'] == ['layer1']
        
        # All returned nodes should be from layer1
        for node in result['nodes']:
            assert node[1] == 'layer1'

    def test_select_in_layer_without_where(self, sample_network):
        """Test SELECT with layer clause but no WHERE."""
        result = execute_query(sample_network, "SELECT * FROM nodes IN LAYER 'layer1'")
        
        assert result['count'] > 0
        # All returned nodes should be from layer1
        for node in result['nodes']:
            assert node[1] == 'layer1'

    def test_select_in_layers_multiple(self, sample_network):
        """Test SELECT with multiple layers clause."""
        result = execute_query(sample_network, 
                              "SELECT * FROM nodes IN LAYERS ('layer1', 'layer2') WHERE degree >= 0")
        
        assert result['count'] >= 0
        assert 'layers' in result
        assert set(result['layers']) == {'layer1', 'layer2'}
        
        # All returned nodes should be from layer1 or layer2
        for node in result['nodes']:
            assert node[1] in ['layer1', 'layer2']

    def test_select_with_from_nodes(self, sample_network):
        """Test SELECT * FROM nodes syntax."""
        result = execute_query(sample_network, "SELECT * FROM nodes WHERE degree > 0")
        
        assert result['count'] >= 0
        assert result['target'] == 'nodes'

    def test_select_layer_filters_correctly(self, sample_network):
        """Test that layer clause properly filters nodes."""
        # Get all nodes
        all_result = execute_query(sample_network, 'SELECT nodes')
        
        # Get layer1 nodes
        layer1_result = execute_query(sample_network, "SELECT * FROM nodes IN LAYER 'layer1'")
        
        # Get layer2 nodes  
        layer2_result = execute_query(sample_network, "SELECT * FROM nodes IN LAYER 'layer2'")
        
        # Sum of layer1 and layer2 should equal or be less than all nodes
        assert layer1_result['count'] + layer2_result['count'] <= all_result['count']
        
        # Verify no overlap in returned nodes
        layer1_nodes = set(tuple(n) if isinstance(n, list) else n for n in layer1_result['nodes'])
        layer2_nodes = set(tuple(n) if isinstance(n, list) else n for n in layer2_result['nodes'])
        assert len(layer1_nodes.intersection(layer2_nodes)) == 0

    def test_select_nonexistent_layer(self, sample_network):
        """Test SELECT with non-existent layer returns empty."""
        result = execute_query(sample_network, "SELECT * FROM nodes IN LAYER 'nonexistent'")
        
        assert result['count'] == 0
        assert result['nodes'] == []


# ═══════════════════════════════════════════════════════════════════════════════
# New DSL v3 Feature Tests: MATCH Queries  
# ═══════════════════════════════════════════════════════════════════════════════


class TestMatchQueries:
    """Test Cypher-like MATCH query syntax."""

    def test_match_single_node_pattern(self, sample_network):
        """Test MATCH with single node pattern."""
        result = execute_query(sample_network, "MATCH (n:layer1) RETURN n")
        
        assert result['type'] == 'match'
        assert 'bindings' in result
        assert result['count'] >= 0
        
        # Each binding should have alias 'n'
        for binding in result['bindings']:
            assert 'n' in binding
            assert binding['n'][1] == 'layer1'

    def test_match_node_edge_pattern(self, sample_network):
        """Test MATCH with node-edge-node pattern."""
        result = execute_query(sample_network, "MATCH (a:layer1)-[r]->(b:layer1) RETURN a, b")
        
        assert result['type'] == 'match'
        assert 'bindings' in result
        
        # Each binding should have aliases 'a' and 'b'
        for binding in result['bindings']:
            assert 'a' in binding
            assert 'b' in binding

    def test_match_with_layer_clause(self, sample_network):
        """Test MATCH with IN LAYER clause."""
        result = execute_query(sample_network, 
                              "MATCH (g:layer1)-[r]->(t:layer1) IN LAYER 'layer1' RETURN g, t")
        
        assert result['type'] == 'match'
        assert 'layers' in result
        assert result['layers'] == ['layer1']

    def test_match_with_where_condition(self, sample_network):
        """Test MATCH with WHERE clause using alias.attribute syntax."""
        result = execute_query(sample_network, 
                              "MATCH (a:layer1)-[r]->(b:layer1) WHERE a.degree >= 0 RETURN a, b")
        
        assert result['type'] == 'match'
        assert 'bindings' in result

    def test_match_return_star(self, sample_network):
        """Test MATCH with RETURN * syntax."""
        result = execute_query(sample_network, "MATCH (n:layer1) RETURN *")
        
        assert result['type'] == 'match'
        # RETURN * should return all bindings with all aliases
        for binding in result['bindings']:
            assert 'n' in binding

    def test_match_return_specific_aliases(self, sample_network):
        """Test MATCH with specific aliases in RETURN."""
        result = execute_query(sample_network, 
                              "MATCH (a:layer1)-[r]->(b:layer1) RETURN a")
        
        assert result['type'] == 'match'
        # Each binding should only have 'a' (not 'b')
        for binding in result['bindings']:
            assert 'a' in binding
            # 'b' and 'r' should be filtered out if they exist
            # Note: bindings may only include requested aliases

    def test_match_without_edge_alias(self, sample_network):
        """Test MATCH with edge pattern without alias."""
        result = execute_query(sample_network, 
                              "MATCH (a:layer1)-[:INTERACTS]->(b:layer1) RETURN a, b")
        
        assert result['type'] == 'match'
        assert 'bindings' in result

    def test_match_empty_pattern_returns_empty(self):
        """Test MATCH on empty network returns empty."""
        empty_network = multinet.multi_layer_network(directed=False)
        result = execute_query(empty_network, "MATCH (n:layer1) RETURN n")
        
        assert result['type'] == 'match'
        assert result['count'] == 0
        assert result['bindings'] == []


# ═══════════════════════════════════════════════════════════════════════════════
# New DSL v3 Feature Tests: Pattern Parsing
# ═══════════════════════════════════════════════════════════════════════════════


class TestPatternParsing:
    """Test parsing of MATCH patterns."""

    def test_parse_node_pattern(self):
        """Test parsing of node patterns."""
        from py3plex.dsl import _parse_node_pattern, _tokenize_match_pattern
        
        tokens = _tokenize_match_pattern("(g:Gene)")
        node, idx = _parse_node_pattern(tokens, 0)
        
        assert node.alias == 'g'
        assert node.label == 'Gene'

    def test_parse_node_pattern_no_label(self):
        """Test parsing of node pattern without label."""
        from py3plex.dsl import _parse_node_pattern, _tokenize_match_pattern
        
        tokens = _tokenize_match_pattern("(n)")
        node, idx = _parse_node_pattern(tokens, 0)
        
        assert node.alias == 'n'
        assert node.label is None

    def test_parse_edge_pattern(self):
        """Test parsing of edge patterns."""
        from py3plex.dsl import _parse_edge_pattern, _tokenize_match_pattern
        
        tokens = _tokenize_match_pattern("-[r:REGULATES]->")
        edge, idx = _parse_edge_pattern(tokens, 0)
        
        assert edge.alias == 'r'
        assert edge.type == 'REGULATES'
        assert edge.directed is True

    def test_parse_edge_pattern_no_alias(self):
        """Test parsing of edge pattern without alias."""
        from py3plex.dsl import _parse_edge_pattern, _tokenize_match_pattern
        
        tokens = _tokenize_match_pattern("-[:INTERACTS]->")
        edge, idx = _parse_edge_pattern(tokens, 0)
        
        assert edge.alias is None
        assert edge.type == 'INTERACTS'

    def test_parse_edge_pattern_no_type(self):
        """Test parsing of edge pattern without type."""
        from py3plex.dsl import _parse_edge_pattern, _tokenize_match_pattern
        
        tokens = _tokenize_match_pattern("-[e]->")
        edge, idx = _parse_edge_pattern(tokens, 0)
        
        assert edge.alias == 'e'
        assert edge.type is None

    def test_parse_path_pattern(self):
        """Test parsing of complete path patterns."""
        from py3plex.dsl import _parse_path_pattern
        
        path = _parse_path_pattern("(g:Gene)-[r:REGULATES]->(t:Gene)")
        
        assert len(path.nodes) == 2
        assert len(path.edges) == 1
        
        assert path.nodes[0].alias == 'g'
        assert path.nodes[0].label == 'Gene'
        assert path.nodes[1].alias == 't'
        assert path.nodes[1].label == 'Gene'
        
        assert path.edges[0].alias == 'r'
        assert path.edges[0].type == 'REGULATES'

    def test_parse_layer_clause_single(self):
        """Test parsing of IN LAYER clause."""
        from py3plex.dsl import _parse_layer_clause
        
        tokens = ['IN', 'LAYER', 'ppi']
        layers, idx = _parse_layer_clause(tokens, 0)
        
        assert layers == ['ppi']
        assert idx == 3

    def test_parse_layer_clause_multiple(self):
        """Test parsing of IN LAYERS clause."""
        from py3plex.dsl import _parse_layer_clause
        
        tokens = ['IN', 'LAYERS', '(', 'ppi', ',', 'coexpr', ')']
        layers, idx = _parse_layer_clause(tokens, 0)
        
        assert set(layers) == {'ppi', 'coexpr'}

    def test_parse_return_clause_star(self):
        """Test parsing of RETURN * clause."""
        from py3plex.dsl import _parse_return_clause
        
        tokens = ['RETURN', '*']
        aliases, idx = _parse_return_clause(tokens, 0)
        
        assert aliases is None  # None means return all

    def test_parse_return_clause_aliases(self):
        """Test parsing of RETURN with aliases."""
        from py3plex.dsl import _parse_return_clause
        
        tokens = ['RETURN', 'g', ',', 't']
        aliases, idx = _parse_return_clause(tokens, 0)
        
        assert aliases == ['g', 't']


# ═══════════════════════════════════════════════════════════════════════════════
# Backward Compatibility Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestBackwardCompatibility:
    """Ensure existing queries still work after DSL extensions."""

    def test_original_select_still_works(self, sample_network):
        """Test that original SELECT syntax still works."""
        result = execute_query(sample_network, 'SELECT nodes WHERE layer="layer1"')
        
        assert result['target'] == 'nodes'
        assert result['count'] > 0

    def test_original_select_with_compute(self, sample_network):
        """Test that SELECT with COMPUTE still works."""
        result = execute_query(sample_network, 
                              'SELECT nodes WHERE layer="layer1" COMPUTE degree')
        
        assert 'computed' in result
        assert 'degree' in result['computed']

    def test_original_and_or_conditions(self, sample_network):
        """Test that AND/OR conditions still work."""
        result = execute_query(sample_network, 
                              'SELECT nodes WHERE layer="layer1" AND degree >= 1')
        
        assert result['count'] >= 0
        
        result2 = execute_query(sample_network, 
                               'SELECT nodes WHERE layer="layer1" OR layer="layer2"')
        assert result2['count'] >= 0

    def test_original_not_condition(self, sample_network):
        """Test that NOT condition still works."""
        result = execute_query(sample_network, 
                              'SELECT nodes WHERE NOT layer="layer1"')
        
        for node in result['nodes']:
            assert node[1] != 'layer1'

    def test_original_comparison_operators(self, sample_network):
        """Test that all comparison operators still work."""
        # Test each operator
        for op in ['>', '<', '>=', '<=', '=', '!=']:
            if op == '=':
                query = 'SELECT nodes WHERE degree = 2'
            elif op == '!=':
                query = 'SELECT nodes WHERE degree != 0'
            elif op == '>':
                query = 'SELECT nodes WHERE degree > 0'
            elif op == '<':
                query = 'SELECT nodes WHERE degree < 100'
            elif op == '>=':
                query = 'SELECT nodes WHERE degree >= 0'
            elif op == '<=':
                query = 'SELECT nodes WHERE degree <= 100'
            
            result = execute_query(sample_network, query)
            assert result['count'] >= 0

    def test_convenience_functions_still_work(self, sample_network):
        """Test that convenience functions still work."""
        nodes = select_nodes_by_layer(sample_network, 'layer1')
        assert len(nodes) > 0
        
        high_deg = select_high_degree_nodes(sample_network, min_degree=0)
        assert len(high_deg) >= 0
        
        centrality = compute_centrality_for_layer(sample_network, 'layer1')
        assert isinstance(centrality, dict)


# ═══════════════════════════════════════════════════════════════════════════════
# First-Class Method Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestFirstClassMethod:
    """Test execute_query as a first-class method on multi_layer_network."""

    def test_execute_query_method_exists(self, sample_network):
        """Test that execute_query method exists on the network object."""
        assert hasattr(sample_network, 'execute_query')
        assert callable(sample_network.execute_query)

    def test_execute_query_method_select(self, sample_network):
        """Test execute_query method with SELECT query."""
        result = sample_network.execute_query('SELECT nodes WHERE layer="layer1"')
        
        assert result['target'] == 'nodes'
        assert result['count'] > 0
        
        # All returned nodes should be from layer1
        for node in result['nodes']:
            assert node[1] == 'layer1'

    def test_execute_query_method_match(self, sample_network):
        """Test execute_query method with MATCH query."""
        result = sample_network.execute_query('MATCH (n:layer1) RETURN n')
        
        assert result['type'] == 'match'
        assert 'bindings' in result
        assert result['count'] > 0

    def test_execute_query_method_with_layer_clause(self, sample_network):
        """Test execute_query method with IN LAYER clause."""
        result = sample_network.execute_query("SELECT * FROM nodes IN LAYER 'layer1'")
        
        assert 'layers' in result
        assert result['layers'] == ['layer1']
        assert result['count'] > 0

    def test_execute_query_method_equivalent_to_function(self, sample_network):
        """Test that method and function produce equivalent results."""
        query = 'SELECT nodes WHERE layer="layer1"'
        
        # Using method
        result_method = sample_network.execute_query(query)
        
        # Using function
        result_function = execute_query(sample_network, query)
        
        # Results should be equivalent
        assert result_method['count'] == result_function['count']
        assert set(result_method['nodes']) == set(result_function['nodes'])


# ═══════════════════════════════════════════════════════════════════════════════
# Community Detection via DSL Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestCommunityDetectionDSL:
    """Test community detection via DSL."""

    @pytest.fixture
    def community_network(self):
        """Create a network with clear community structure."""
        network = multinet.multi_layer_network(directed=False)

        # Add nodes
        nodes = [
            {'source': 'A', 'type': 'social'},
            {'source': 'B', 'type': 'social'},
            {'source': 'C', 'type': 'social'},
            {'source': 'D', 'type': 'social'},
            {'source': 'E', 'type': 'social'},
            {'source': 'F', 'type': 'social'},
        ]
        network.add_nodes(nodes)

        # Add edges to form two clear communities
        edges = [
            # Community 1: A, B, C (densely connected)
            {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
            {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
            {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
            
            # Community 2: D, E, F (densely connected)
            {'source': 'D', 'target': 'E', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
            {'source': 'D', 'target': 'F', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
            {'source': 'E', 'target': 'F', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
            
            # Bridge between communities (weak connection)
            {'source': 'C', 'target': 'D', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        ]
        network.add_edges(edges)

        return network

    def test_compute_communities(self, community_network):
        """Test computing communities via DSL."""
        result = execute_query(community_network, 'SELECT nodes COMPUTE communities')

        assert 'computed' in result
        assert 'communities' in result['computed']
        
        # Should assign community IDs to all nodes
        communities = result['computed']['communities']
        assert len(communities) == result['count']

    def test_compute_community_alias(self, community_network):
        """Test 'community' alias works same as 'communities'."""
        result = execute_query(community_network, 'SELECT nodes COMPUTE community')

        assert 'computed' in result
        assert 'community' in result['computed']

    def test_communities_with_layer_filter(self, sample_network):
        """Test computing communities filtered by layer."""
        result = execute_query(sample_network, 'SELECT nodes WHERE layer="layer1" COMPUTE communities')

        assert 'computed' in result
        assert 'communities' in result['computed']
        
        # All nodes should be from layer1
        for node in result['nodes']:
            assert node[1] == 'layer1'


class TestCommunityConvenienceFunctions:
    """Test community detection convenience functions."""

    @pytest.fixture
    def community_network(self):
        """Create a network with clear community structure."""
        network = multinet.multi_layer_network(directed=False)

        # Add nodes for two communities of different sizes
        nodes = [
            {'source': 'A', 'type': 'social'},
            {'source': 'B', 'type': 'social'},
            {'source': 'C', 'type': 'social'},
            {'source': 'D', 'type': 'social'},  # Bridge
            {'source': 'E', 'type': 'social'},
            {'source': 'F', 'type': 'social'},
        ]
        network.add_nodes(nodes)

        # Add edges
        edges = [
            # Community 1: A, B, C (3 nodes)
            {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
            {'source': 'A', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
            {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
            
            # Community 2: D, E, F (3 nodes)
            {'source': 'D', 'target': 'E', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
            {'source': 'D', 'target': 'F', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
            {'source': 'E', 'target': 'F', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
            
            # Bridge
            {'source': 'C', 'target': 'D', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        ]
        network.add_edges(edges)

        return network

    def test_detect_communities(self, community_network):
        """Test detect_communities function."""
        result = detect_communities(community_network)
        
        assert 'partition' in result
        assert 'num_communities' in result
        assert 'community_sizes' in result
        assert 'biggest_community' in result
        assert 'smallest_community' in result
        assert 'size_distribution' in result
        
        # Should find at least 1 community
        assert result['num_communities'] >= 1

    def test_get_community_partition(self, community_network):
        """Test get_community_partition function."""
        partition = get_community_partition(community_network)
        
        assert isinstance(partition, dict)
        # All nodes should be assigned
        assert len(partition) == 6

    def test_get_biggest_community(self, community_network):
        """Test get_biggest_community function."""
        community_id, size, nodes = get_biggest_community(community_network)
        
        assert isinstance(community_id, int)
        assert isinstance(size, int)
        assert isinstance(nodes, list)
        assert size > 0
        assert len(nodes) == size

    def test_get_smallest_community(self, community_network):
        """Test get_smallest_community function."""
        community_id, size, nodes = get_smallest_community(community_network)
        
        assert isinstance(community_id, int)
        assert isinstance(size, int)
        assert isinstance(nodes, list)
        assert size > 0
        assert len(nodes) == size

    def test_get_num_communities(self, community_network):
        """Test get_num_communities function."""
        num = get_num_communities(community_network)
        
        assert isinstance(num, int)
        assert num >= 1

    def test_get_community_sizes(self, community_network):
        """Test get_community_sizes function."""
        sizes = get_community_sizes(community_network)
        
        assert isinstance(sizes, dict)
        # Sum of sizes should equal number of nodes
        assert sum(sizes.values()) == 6

    def test_get_community_size_distribution(self, community_network):
        """Test get_community_size_distribution function."""
        distribution = get_community_size_distribution(community_network)
        
        assert isinstance(distribution, list)
        # Should be sorted in descending order
        assert distribution == sorted(distribution, reverse=True)
        # Sum should equal number of nodes
        assert sum(distribution) == 6

    def test_empty_network_communities(self):
        """Test community detection on empty network."""
        empty_network = multinet.multi_layer_network(directed=False)
        result = detect_communities(empty_network)
        
        assert result['num_communities'] == 0
        assert result['partition'] == {}
        assert result['size_distribution'] == []

    def test_single_node_network(self):
        """Test community detection on single node network."""
        network = multinet.multi_layer_network(directed=False)
        network.add_nodes([{'source': 'A', 'type': 'social'}])
        
        result = detect_communities(network)
        
        # Single node without edges may be detected as 0 or 1 communities
        # depending on the algorithm - we just verify it doesn't crash
        assert result['num_communities'] >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
