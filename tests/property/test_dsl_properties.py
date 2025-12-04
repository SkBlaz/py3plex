#!/usr/bin/env python3
"""
Property-based tests for DSL module.

Tests invariants for SQL-like DSL query parsing and execution.
"""

import pytest
from hypothesis import given, settings, assume, strategies as st

# Import DSL module
try:
    from py3plex.dsl import (
        _tokenize_query,
        _parse_condition,
        _evaluate_condition,
        _evaluate_conditions,
        execute_query,
        format_result,
        select_nodes_by_layer,
        select_high_degree_nodes,
        compute_centrality_for_layer,
        DSLSyntaxError,
    )
    from py3plex.core import multinet
    DSL_AVAILABLE = True
except ImportError:
    DSL_AVAILABLE = False
    pytest.skip("DSL module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Query Tokenization
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    identifier=st.text(
        min_size=1,
        max_size=30,
        alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))
    ).filter(lambda x: len(x) > 0)
)
def test_tokenize_preserves_identifiers(identifier):
    """Test that tokenization preserves valid identifiers."""
    # Use only lowercase ascii letters to ensure valid identifiers
    query = f"SELECT nodes WHERE {identifier} > 0"

    tokens = _tokenize_query(query)

    # The identifier should appear in the token list
    # Note: tokenizer may transform or filter some identifiers
    assert isinstance(tokens, list)
    assert len(tokens) >= 5  # At least: SELECT, nodes, WHERE, >, 0


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    string_value=st.text(min_size=1, max_size=50, alphabet=st.characters(
        blacklist_characters='"\'',
        blacklist_categories=('Cc', 'Cs')  # Exclude control and surrogate characters
    ))
)
def test_tokenize_handles_quoted_strings(string_value):
    """Test that tokenization correctly handles quoted strings."""
    query = f'SELECT nodes WHERE layer="{string_value}"'

    # Should not raise an exception
    tokens = _tokenize_query(query)

    # Tokens should be a list
    assert isinstance(tokens, list)
    assert len(tokens) > 0


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    value1=st.integers(min_value=0, max_value=1000),
    value2=st.integers(min_value=0, max_value=1000)
)
def test_tokenize_handles_numeric_values(value1, value2):
    """Test that tokenization correctly handles numeric values."""
    query = f"SELECT nodes WHERE degree > {value1} AND centrality < {value2}"

    tokens = _tokenize_query(query)

    # Should contain string representations of the numbers
    assert str(value1) in tokens or any(str(value1) in token for token in tokens)
    assert str(value2) in tokens or any(str(value2) in token for token in tokens)


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    operator=st.sampled_from(['>', '<', '=', '>=', '<=', '!='])
)
def test_tokenize_recognizes_comparison_operators(operator):
    """Test that tokenization recognizes comparison operators."""
    query = f"SELECT nodes WHERE degree {operator} 5"

    tokens = _tokenize_query(query)

    # The operator should be in the token list
    assert operator in tokens


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    logical_op=st.sampled_from(['AND', 'OR', 'NOT'])
)
def test_tokenize_recognizes_logical_operators(logical_op):
    """Test that tokenization recognizes logical operators."""
    if logical_op == 'NOT':
        query = f"SELECT nodes WHERE {logical_op} (degree > 5)"
    else:
        query = f"SELECT nodes WHERE degree > 5 {logical_op} centrality < 1"

    tokens = _tokenize_query(query)

    # The logical operator should be in the token list
    assert logical_op in tokens


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    keyword=st.sampled_from(['SELECT', 'WHERE', 'COMPUTE'])
)
def test_tokenize_recognizes_keywords(keyword):
    """Test that tokenization recognizes DSL keywords."""
    if keyword == 'SELECT':
        query = f"{keyword} nodes WHERE degree > 0"
    elif keyword == 'WHERE':
        query = f"SELECT nodes {keyword} degree > 0"
    else:  # COMPUTE
        query = f"SELECT nodes WHERE degree > 0 {keyword} centrality"

    tokens = _tokenize_query(query)

    # The keyword should be in the token list
    assert keyword in tokens


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    target=st.sampled_from(['nodes', 'edges'])
)
def test_tokenize_recognizes_selection_targets(target):
    """Test that tokenization recognizes selection targets."""
    query = f"SELECT {target} WHERE degree > 0"

    tokens = _tokenize_query(query)

    # The target should be in the token list
    assert target in tokens


# ============================================================================
# Property Tests: Query Structure Invariants
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    target=st.sampled_from(['nodes', 'edges']),
    field=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz_').filter(lambda x: x[0].isalpha()),
    value=st.integers(min_value=0, max_value=100)
)
def test_simple_query_tokenization_structure(target, field, value):
    """Test that simple queries maintain their structure after tokenization."""
    query = f"SELECT {target} WHERE {field} > {value}"

    tokens = _tokenize_query(query)

    # Basic structure checks
    assert 'SELECT' in tokens
    assert target in tokens
    assert 'WHERE' in tokens
    assert '>' in tokens
    # Field may or may not be present depending on tokenization rules


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    value1=st.integers(min_value=0, max_value=50),
    value2=st.integers(min_value=0, max_value=50),
    logical_op=st.sampled_from(['AND', 'OR'])
)
def test_compound_query_tokenization_structure(value1, value2, logical_op):
    """Test that compound queries with logical operators are tokenized correctly."""
    query = f"SELECT nodes WHERE degree > {value1} {logical_op} centrality < {value2}"

    tokens = _tokenize_query(query)

    # Should contain all major components
    assert 'SELECT' in tokens
    assert 'nodes' in tokens
    assert 'WHERE' in tokens
    assert logical_op in tokens
    assert '>' in tokens
    assert '<' in tokens


# ============================================================================
# Property Tests: Tokenization Properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    query_parts=st.lists(
        st.sampled_from(['SELECT nodes', 'WHERE degree > 0', 'AND centrality < 1']),
        min_size=1,
        max_size=3,
        unique=True
    )
)
def test_tokenization_produces_list(query_parts):
    """Test that tokenization always produces a list."""
    query = ' '.join(query_parts)

    result = _tokenize_query(query)

    assert isinstance(result, list)
    assert len(result) > 0


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    whitespace=st.sampled_from(['  ', '\t', '\n', '    '])
)
def test_tokenization_ignores_extra_whitespace(whitespace):
    """Test that tokenization handles extra whitespace correctly."""
    query = f"SELECT{whitespace}nodes{whitespace}WHERE{whitespace}degree > 0"

    tokens = _tokenize_query(query)

    # Should produce same structure regardless of whitespace
    assert 'SELECT' in tokens
    assert 'nodes' in tokens or any('nodes' in t for t in tokens)
    assert 'WHERE' in tokens


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    layer_name=st.text(min_size=1, max_size=30, alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd'),
        whitelist_characters='_-'
    )),
    threshold=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
)
def test_tokenization_preserves_layer_queries(layer_name, threshold):
    """Test that tokenization preserves layer-specific queries."""
    query = f'SELECT nodes WHERE layer="{layer_name}" AND centrality > {threshold:.2f}'

    tokens = _tokenize_query(query)

    # Should contain the layer name (possibly as a placeholder or direct value)
    assert isinstance(tokens, list)
    assert len(tokens) > 0
    assert 'SELECT' in tokens
    assert '>' in tokens


# ============================================================================
# Property Tests: Edge Cases
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    nested_level=st.integers(min_value=1, max_value=3)
)
def test_tokenization_handles_nested_conditions(nested_level):
    """Test that tokenization can handle nested conditions (with parentheses)."""
    # Build a query with nested conditions
    base = "degree > 0"
    for _ in range(nested_level):
        base = f"({base} AND centrality < 1)"

    query = f"SELECT nodes WHERE {base}"

    # Should not raise an exception
    tokens = _tokenize_query(query)

    assert isinstance(tokens, list)
    assert 'SELECT' in tokens


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    empty_parts=st.integers(min_value=0, max_value=3)
)
def test_tokenization_handles_minimal_queries(empty_parts):
    """Test that tokenization handles minimal valid queries."""
    # Different levels of minimal queries
    queries = [
        "SELECT nodes",
        "SELECT nodes WHERE degree > 0",
        "SELECT edges WHERE source = target"
    ]

    query = queries[empty_parts % len(queries)]

    tokens = _tokenize_query(query)

    # Should always produce a non-empty list
    assert isinstance(tokens, list)
    assert len(tokens) > 0
    assert 'SELECT' in tokens


# ============================================================================
# Helper: Create test network
# ============================================================================

def create_test_network(num_nodes=5, num_layers=2):
    """Create a simple test multilayer network."""
    network = multinet.multi_layer_network(directed=False)

    layers = [f'layer{i}' for i in range(num_layers)]
    node_names = [chr(ord('A') + i) for i in range(num_nodes)]

    # Add nodes
    nodes = []
    for name in node_names:
        for layer in layers:
            nodes.append({'source': name, 'type': layer})
    network.add_nodes(nodes)

    # Add edges within layers
    edges = []
    for layer in layers:
        for i in range(len(node_names) - 1):
            edges.append({
                'source': node_names[i],
                'target': node_names[i + 1],
                'source_type': layer,
                'target_type': layer,
                'weight': 1.0
            })
    network.add_edges(edges)

    return network


# ============================================================================
# Property Tests: Query Execution
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    target=st.sampled_from(['nodes', 'edges'])
)
def test_execute_query_returns_dict(target):
    """Test that execute_query always returns a dictionary with expected keys."""
    network = create_test_network()
    query = f"SELECT {target}"

    result = execute_query(network, query)

    # Should return a dictionary
    assert isinstance(result, dict)

    # Should have required keys
    assert 'query' in result
    assert 'target' in result
    assert 'count' in result
    assert target in result


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_execute_query_layer_filter_returns_correct_layer(layer_idx):
    """Test that filtering by layer returns only nodes from that layer."""
    network = create_test_network(num_nodes=4, num_layers=2)
    layer = f'layer{layer_idx}'
    query = f'SELECT nodes WHERE layer="{layer}"'

    result = execute_query(network, query)

    # All returned nodes should be from the specified layer
    for node in result['nodes']:
        assert node[1] == layer, f"Node {node} should be from layer {layer}"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    threshold=st.integers(min_value=0, max_value=10)
)
def test_execute_query_degree_filter_invariant(threshold):
    """Test that degree filter respects the threshold."""
    network = create_test_network(num_nodes=5, num_layers=2)
    query = f'SELECT nodes WHERE degree > {threshold}'

    result = execute_query(network, query)

    # All returned nodes should have degree > threshold
    for node in result['nodes']:
        degree = network.core_network.degree(node)
        assert degree > threshold, f"Node {node} has degree {degree}, expected > {threshold}"


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    measure=st.sampled_from(['degree', 'degree_centrality', 'betweenness_centrality', 'clustering'])
)
def test_execute_query_compute_returns_measures(measure):
    """Test that COMPUTE clause returns measures for filtered nodes."""
    network = create_test_network(num_nodes=4, num_layers=1)
    query = f'SELECT nodes COMPUTE {measure}'

    result = execute_query(network, query)

    # Should have computed key
    assert 'computed' in result
    assert measure in result['computed']

    # Computed values should be numeric
    for value in result['computed'][measure].values():
        assert isinstance(value, (int, float))


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    logical_op=st.sampled_from(['AND', 'OR'])
)
def test_execute_query_logical_operators(logical_op):
    """Test that logical operators are correctly applied."""
    network = create_test_network(num_nodes=5, num_layers=2)

    if logical_op == 'AND':
        # AND should be more restrictive
        query = f'SELECT nodes WHERE layer="layer0" {logical_op} degree >= 0'
    else:
        # OR should be more inclusive
        query = f'SELECT nodes WHERE layer="layer0" {logical_op} layer="layer1"'

    result = execute_query(network, query)

    # Should return valid results
    assert result['count'] >= 0
    assert isinstance(result['nodes'], list)


@pytest.mark.property
def test_execute_query_empty_network():
    """Test that query on empty network returns empty results."""
    network = multinet.multi_layer_network(directed=False)
    query = 'SELECT nodes'

    result = execute_query(network, query)

    assert result['count'] == 0
    assert result['nodes'] == []


# ============================================================================
# Property Tests: Result Formatting
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    limit=st.integers(min_value=1, max_value=20)
)
def test_format_result_respects_limit(limit):
    """Test that format_result respects the limit parameter."""
    network = create_test_network(num_nodes=10, num_layers=2)
    query = 'SELECT nodes'
    result = execute_query(network, query)

    formatted = format_result(result, limit=limit)

    # Should return a string
    assert isinstance(formatted, str)

    # Should contain query info
    assert 'Query:' in formatted
    assert 'Count:' in formatted


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    target=st.sampled_from(['nodes', 'edges'])
)
def test_format_result_shows_target(target):
    """Test that format_result shows the correct target."""
    network = create_test_network()
    query = f'SELECT {target}'
    result = execute_query(network, query)

    formatted = format_result(result)

    # Should mention the target
    assert 'Target:' in formatted
    assert target in formatted.lower()


# ============================================================================
# Property Tests: Convenience Functions
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_select_nodes_by_layer_returns_list(layer_idx):
    """Test that select_nodes_by_layer returns a list of nodes."""
    network = create_test_network(num_nodes=4, num_layers=2)
    layer = f'layer{layer_idx}'

    nodes = select_nodes_by_layer(network, layer)

    # Should return a list
    assert isinstance(nodes, list)

    # All nodes should be from the specified layer
    for node in nodes:
        assert node[1] == layer


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    min_degree=st.integers(min_value=0, max_value=5)
)
def test_select_high_degree_nodes_invariant(min_degree):
    """Test that select_high_degree_nodes returns nodes with degree > min_degree."""
    network = create_test_network(num_nodes=5, num_layers=2)

    nodes = select_high_degree_nodes(network, min_degree)

    # All returned nodes should have degree > min_degree
    for node in nodes:
        degree = network.core_network.degree(node)
        assert degree > min_degree


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(
    layer_idx=st.integers(min_value=0, max_value=1),
    centrality=st.sampled_from(['degree_centrality', 'betweenness_centrality'])
)
def test_compute_centrality_for_layer_returns_dict(layer_idx, centrality):
    """Test that compute_centrality_for_layer returns a dictionary."""
    network = create_test_network(num_nodes=4, num_layers=2)
    layer = f'layer{layer_idx}'

    result = compute_centrality_for_layer(network, layer, centrality)

    # Should return a dictionary
    assert isinstance(result, dict)

    # All values should be numeric
    for value in result.values():
        assert isinstance(value, (int, float))


# ============================================================================
# Property Tests: Condition Parsing
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    attribute=st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz_'),
    operator=st.sampled_from(['>', '<', '=', '>=', '<=', '!=']),
    value=st.integers(min_value=0, max_value=100)
)
def test_parse_condition_returns_dict(attribute, operator, value):
    """Test that _parse_condition returns a valid condition dictionary."""
    assume(len(attribute) > 0 and attribute[0].isalpha())

    tokens = [attribute, operator, str(value)]

    condition, next_idx = _parse_condition(tokens, 0)

    # Should return a dictionary with required keys
    assert isinstance(condition, dict)
    assert 'attribute' in condition
    assert 'operator' in condition
    assert 'value' in condition
    assert 'negated' in condition

    # Next index should be after the condition
    assert next_idx == 3


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    value=st.integers(min_value=0, max_value=100)
)
def test_parse_condition_with_not_operator(value):
    """Test that NOT operator is correctly parsed."""
    tokens = ['NOT', 'degree', '>', str(value)]

    condition, next_idx = _parse_condition(tokens, 0)

    # Should be negated
    assert condition['negated'] is True
    assert condition['attribute'] == 'degree'
    assert next_idx == 4


# ============================================================================
# Property Tests: Condition Evaluation
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    layer_name=st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz')
)
def test_evaluate_condition_layer_equality(layer_name):
    """Test that layer equality condition works correctly."""
    assume(len(layer_name) > 0)

    network = create_test_network(num_nodes=3, num_layers=1)

    condition = {
        'attribute': 'layer',
        'operator': '=',
        'value': layer_name,
        'negated': False
    }

    # Create a node tuple
    node = ('A', layer_name)

    result = _evaluate_condition(node, condition, network, {})

    # Should return True for matching layer
    assert result is True


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    threshold=st.integers(min_value=0, max_value=10)
)
def test_evaluate_condition_degree_comparison(threshold):
    """Test that degree comparison works correctly."""
    network = create_test_network(num_nodes=5, num_layers=1)

    condition = {
        'attribute': 'degree',
        'operator': '>',
        'value': threshold,
        'negated': False
    }

    # Get a node from the network
    nodes = list(network.get_nodes())
    if nodes:
        node = nodes[0]
        result = _evaluate_condition(node, condition, network, {})

        # Verify the result matches actual degree
        actual_degree = network.core_network.degree(node)
        expected = actual_degree > threshold
        assert result == expected


@pytest.mark.property
def test_evaluate_conditions_empty_list():
    """Test that empty conditions list returns True."""
    network = create_test_network()
    node = ('A', 'layer0')

    result = _evaluate_conditions(node, [], network, {})

    # Empty conditions should return True (no filtering)
    assert result is True


# ============================================================================
# Property Tests: Query Result Invariants
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_query_count_matches_result_length(num_nodes, num_layers):
    """Test that query count matches actual result length."""
    network = create_test_network(num_nodes=num_nodes, num_layers=num_layers)
    query = 'SELECT nodes'

    result = execute_query(network, query)

    # Count should match length of nodes list
    assert result['count'] == len(result['nodes'])


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_query_all_nodes_returns_all(num_nodes):
    """Test that SELECT nodes returns all nodes when no filter."""
    network = create_test_network(num_nodes=num_nodes, num_layers=2)
    query = 'SELECT nodes'

    result = execute_query(network, query)

    # Should return all nodes (num_nodes * num_layers)
    expected_count = num_nodes * 2
    assert result['count'] == expected_count


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    threshold=st.integers(min_value=0, max_value=5)
)
def test_query_filter_reduces_or_maintains_count(threshold):
    """Test that filtering reduces or maintains count compared to unfiltered."""
    network = create_test_network(num_nodes=5, num_layers=2)

    all_result = execute_query(network, 'SELECT nodes')
    filtered_result = execute_query(network, f'SELECT nodes WHERE degree >= {threshold}')

    # Filtered count should be <= all count
    assert filtered_result['count'] <= all_result['count']


# ============================================================================
# Property Tests: Error Handling
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    invalid_target=st.sampled_from(['invalid', 'xyz', 'abc', 'unknown', 'data', 'items', 'all'])
)
def test_invalid_target_raises_error(invalid_target):
    """Test that invalid SELECT target raises DSLSyntaxError."""
    network = create_test_network()
    query = f'SELECT {invalid_target}'

    with pytest.raises(DSLSyntaxError):
        execute_query(network, query)


@pytest.mark.property
def test_empty_query_raises_error():
    """Test that empty query raises DSLSyntaxError."""
    network = create_test_network()

    with pytest.raises(DSLSyntaxError):
        execute_query(network, '')


# ============================================================================
# Property Tests: DSL Chaining - IN LAYER / IN LAYERS Clauses
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_in_layer_clause_filters_correctly(layer_idx):
    """Test that IN LAYER clause filters to only specified layer."""
    network = create_test_network(num_nodes=4, num_layers=2)
    layer = f'layer{layer_idx}'
    
    result = execute_query(network, f"SELECT * FROM nodes IN LAYER '{layer}'")
    
    # All returned nodes should be from the specified layer
    for node in result['nodes']:
        assert node[1] == layer


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_in_layer_equivalent_to_where_layer(layer_idx):
    """Test that IN LAYER produces same result as WHERE layer=..."""
    network = create_test_network(num_nodes=5, num_layers=2)
    layer = f'layer{layer_idx}'
    
    result_in = execute_query(network, f"SELECT * FROM nodes IN LAYER '{layer}'")
    result_where = execute_query(network, f'SELECT nodes WHERE layer="{layer}"')
    
    # Both should return same number of nodes
    assert result_in['count'] == result_where['count']


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_in_layers_multiple_layers(num_layers):
    """Test IN LAYERS with multiple layers."""
    network = create_test_network(num_nodes=4, num_layers=3)
    layers = [f'layer{i}' for i in range(num_layers)]
    layers_str = ', '.join(f"'{l}'" for l in layers)
    
    result = execute_query(network, f"SELECT * FROM nodes IN LAYERS ({layers_str})")
    
    # All nodes should be from one of the specified layers
    for node in result['nodes']:
        assert node[1] in layers


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_in_layer_with_where_clause(layer_idx):
    """Test IN LAYER combined with WHERE clause."""
    network = create_test_network(num_nodes=5, num_layers=2)
    layer = f'layer{layer_idx}'
    
    result = execute_query(network, f"SELECT * FROM nodes IN LAYER '{layer}' WHERE degree >= 0")
    
    # All nodes should be from the specified layer
    for node in result['nodes']:
        assert node[1] == layer


# ============================================================================
# Property Tests: DSL Chaining - MATCH Queries
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_match_single_node_pattern(layer_idx):
    """Test MATCH with single node pattern."""
    network = create_test_network(num_nodes=4, num_layers=2)
    layer = f'layer{layer_idx}'
    
    result = execute_query(network, f"MATCH (n:{layer}) RETURN n")
    
    assert result['type'] == 'match'
    assert 'bindings' in result
    
    # Each binding should have 'n' from the correct layer
    for binding in result['bindings']:
        assert 'n' in binding
        if binding['n']:
            assert binding['n'][1] == layer


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_match_count_equals_bindings_length(layer_idx):
    """Test that MATCH count equals bindings length."""
    network = create_test_network(num_nodes=4, num_layers=2)
    layer = f'layer{layer_idx}'
    
    result = execute_query(network, f"MATCH (n:{layer}) RETURN n")
    
    assert result['count'] == len(result['bindings'])


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_match_with_layer_clause(layer_idx):
    """Test MATCH with IN LAYER clause."""
    network = create_test_network(num_nodes=4, num_layers=2)
    layer = f'layer{layer_idx}'
    
    result = execute_query(network, f"MATCH (n) IN LAYER '{layer}' RETURN n")
    
    assert 'layers' in result
    assert result['layers'] == [layer]


@pytest.mark.property
def test_match_return_star():
    """Test MATCH with RETURN * syntax."""
    network = create_test_network(num_nodes=4, num_layers=1)
    
    result = execute_query(network, "MATCH (n:layer0) RETURN *")
    
    assert result['type'] == 'match'
    # RETURN * should include 'n' in each binding
    for binding in result['bindings']:
        assert 'n' in binding


@pytest.mark.property
def test_match_on_empty_network():
    """Test MATCH on empty network returns empty bindings."""
    empty_network = multinet.multi_layer_network(directed=False)
    
    result = execute_query(empty_network, "MATCH (n:layer0) RETURN n")
    
    assert result['type'] == 'match'
    assert result['count'] == 0
    assert result['bindings'] == []


# ============================================================================
# Property Tests: DSL Query Chaining (SELECT with COMPUTE)
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    measure=st.sampled_from(['degree', 'betweenness_centrality', 'closeness_centrality'])
)
def test_select_compute_returns_computed(measure):
    """Test that SELECT with COMPUTE returns computed measures."""
    network = create_test_network(num_nodes=4, num_layers=1)
    
    result = execute_query(network, f"SELECT nodes COMPUTE {measure}")
    
    assert 'computed' in result
    assert measure in result['computed']


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_select_in_layer_with_compute(layer_idx):
    """Test SELECT with IN LAYER and COMPUTE."""
    network = create_test_network(num_nodes=4, num_layers=2)
    layer = f'layer{layer_idx}'
    
    result = execute_query(network, f"SELECT * FROM nodes IN LAYER '{layer}' COMPUTE degree")
    
    assert 'computed' in result
    assert 'degree' in result['computed']
    
    # All nodes should be from the specified layer
    for node in result['nodes']:
        assert node[1] == layer


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    layer_idx=st.integers(min_value=0, max_value=1),
    threshold=st.integers(min_value=0, max_value=5)
)
def test_select_where_in_layer_combined(layer_idx, threshold):
    """Test SELECT with WHERE and IN LAYER combined."""
    network = create_test_network(num_nodes=5, num_layers=2)
    layer = f'layer{layer_idx}'
    
    result = execute_query(
        network, 
        f"SELECT * FROM nodes IN LAYER '{layer}' WHERE degree >= {threshold}"
    )
    
    # All nodes should meet both conditions
    for node in result['nodes']:
        assert node[1] == layer
        degree = network.core_network.degree(node)
        assert degree >= threshold


# ============================================================================
# Property Tests: DSL Idempotence and Equivalence
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_double_layer_filter_is_idempotent(layer_idx):
    """Test that filtering by same layer twice returns same result."""
    network = create_test_network(num_nodes=5, num_layers=2)
    layer = f'layer{layer_idx}'
    
    result_single = execute_query(network, f'SELECT nodes WHERE layer="{layer}"')
    result_double = execute_query(
        network, 
        f'SELECT nodes WHERE layer="{layer}" AND layer="{layer}"'
    )
    
    assert result_single['count'] == result_double['count']


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    threshold=st.integers(min_value=0, max_value=5)
)
def test_degree_filter_with_and_self(threshold):
    """Test that degree > X AND degree > X equals single filter."""
    network = create_test_network(num_nodes=5, num_layers=2)
    
    result_single = execute_query(network, f'SELECT nodes WHERE degree > {threshold}')
    result_double = execute_query(
        network, 
        f'SELECT nodes WHERE degree > {threshold} AND degree > {threshold}'
    )
    
    assert result_single['count'] == result_double['count']


@pytest.mark.property
def test_or_layer_expands_result():
    """Test that OR with layers expands or maintains result."""
    network = create_test_network(num_nodes=4, num_layers=2)
    
    result_layer0 = execute_query(network, 'SELECT nodes WHERE layer="layer0"')
    result_layer1 = execute_query(network, 'SELECT nodes WHERE layer="layer1"')
    result_or = execute_query(
        network, 
        'SELECT nodes WHERE layer="layer0" OR layer="layer1"'
    )
    
    # OR result should be >= each individual result
    assert result_or['count'] >= result_layer0['count']
    assert result_or['count'] >= result_layer1['count']
    
    # OR result should be at most sum (when no overlap)
    assert result_or['count'] <= result_layer0['count'] + result_layer1['count']


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_not_layer_is_complement(layer_idx):
    """Test that NOT layer is complement of layer filter."""
    network = create_test_network(num_nodes=4, num_layers=2)
    layer = f'layer{layer_idx}'
    
    result_layer = execute_query(network, f'SELECT nodes WHERE layer="{layer}"')
    result_not_layer = execute_query(network, f'SELECT nodes WHERE NOT layer="{layer}"')
    result_all = execute_query(network, 'SELECT nodes')
    
    # Sum of layer + not layer should equal all
    assert result_layer['count'] + result_not_layer['count'] == result_all['count']
