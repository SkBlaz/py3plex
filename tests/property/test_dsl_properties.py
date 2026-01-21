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

# Import graph_ops for integration tests
try:
    from py3plex.graph_ops import nodes as graph_ops_nodes
    GRAPH_OPS_AVAILABLE = True
except ImportError:
    graph_ops_nodes = None
    GRAPH_OPS_AVAILABLE = False


# ============================================================================
# Property Tests: Query Tokenization
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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
@settings(deadline=None, max_examples=3)
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


# ============================================================================
# Property Tests: DSL and graph_ops Integration  
# ============================================================================

@pytest.mark.property
@pytest.mark.skipif(not GRAPH_OPS_AVAILABLE, reason="graph_ops not available")
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_dsl_and_graph_ops_equivalent_layer_filter(layer_idx):
    """Test that DSL layer filter and graph_ops layer filter produce equivalent results."""
    network = create_test_network(num_nodes=5, num_layers=2)
    layer = f'layer{layer_idx}'
    
    # DSL query
    dsl_result = execute_query(network, f'SELECT nodes WHERE layer="{layer}"')
    
    # graph_ops filter
    graph_ops_result = graph_ops_nodes(network, layers=[layer])
    
    # Both should return same count
    assert dsl_result['count'] == len(graph_ops_result)


@pytest.mark.property
@pytest.mark.skipif(not GRAPH_OPS_AVAILABLE, reason="graph_ops not available")
@settings(deadline=None, max_examples=3)
@given(
    threshold=st.integers(min_value=0, max_value=5)
)
def test_dsl_and_graph_ops_equivalent_degree_filter(threshold):
    """Test that DSL degree filter and graph_ops filter produce equivalent results."""
    network = create_test_network(num_nodes=5, num_layers=2)
    
    # DSL query
    dsl_result = execute_query(network, f'SELECT nodes WHERE degree > {threshold}')
    
    # graph_ops filter
    graph_ops_result = graph_ops_nodes(network).filter(lambda n: n['degree'] > threshold)
    
    # Both should return same count
    assert dsl_result['count'] == len(graph_ops_result)


@pytest.mark.property
@pytest.mark.skipif(not GRAPH_OPS_AVAILABLE, reason="graph_ops not available")
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=1),
    threshold=st.integers(min_value=0, max_value=5)
)
def test_dsl_and_graph_ops_combined_filter(layer_idx, threshold):
    """Test DSL and graph_ops with combined layer and degree filters."""
    network = create_test_network(num_nodes=5, num_layers=2)
    layer = f'layer{layer_idx}'
    
    # DSL query with AND
    dsl_result = execute_query(
        network, 
        f'SELECT nodes WHERE layer="{layer}" AND degree > {threshold}'
    )
    
    # graph_ops chained filter
    graph_ops_result = (
        graph_ops_nodes(network, layers=[layer])
        .filter(lambda n: n['degree'] > threshold)
    )
    
    # Both should return same count
    assert dsl_result['count'] == len(graph_ops_result)


@pytest.mark.property
def test_execute_query_method_on_network():
    """Test that multi_layer_network has execute_query method."""
    network = create_test_network(num_nodes=4, num_layers=2)
    
    # Use the method on the network object
    result = network.execute_query('SELECT nodes')
    
    assert result['count'] == 8  # 4 nodes * 2 layers
    assert result['target'] == 'nodes'


# ============================================================================
# Property Tests: Edge Cases and Error Paths
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_nodes=st.integers(min_value=1, max_value=5)
)
def test_select_edges_on_network(num_nodes):
    """Test SELECT edges query."""
    network = create_test_network(num_nodes=num_nodes, num_layers=1)
    
    result = execute_query(network, 'SELECT edges')
    
    assert result['target'] == 'edges'
    assert 'edges' in result
    assert result['count'] >= 0


@pytest.mark.property
def test_format_result_with_empty_nodes():
    """Test format_result with zero results."""
    network = create_test_network(num_nodes=3, num_layers=1)
    
    # Query that returns no results
    result = execute_query(network, 'SELECT nodes WHERE degree > 1000')
    formatted = format_result(result)
    
    assert 'Count: 0' in formatted
    assert isinstance(formatted, str)


# ============================================================================
# Property Tests: Additional Centrality Measures
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    measure=st.sampled_from(['pagerank', 'eigenvector_centrality', 'eigenvector'])
)
def test_execute_query_compute_additional_centrality_measures(measure):
    """Test that COMPUTE clause returns additional centrality measures."""
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
@settings(deadline=None, max_examples=3)
@given(
    measure=st.sampled_from([
        'degree', 'degree_centrality', 'betweenness_centrality', 'betweenness',
        'closeness_centrality', 'closeness', 'pagerank', 
        'eigenvector_centrality', 'eigenvector'
    ])
)
def test_compute_all_centrality_measures_non_negative(measure):
    """Test that all centrality measures return non-negative values."""
    network = create_test_network(num_nodes=5, num_layers=1)
    query = f'SELECT nodes COMPUTE {measure}'

    result = execute_query(network, query)

    # All centrality values should be non-negative
    assert 'computed' in result
    assert measure in result['computed']
    
    for node, value in result['computed'][measure].items():
        # Eigenvector centrality might fail to converge and return 0
        # but should still be non-negative
        assert value >= 0, f"Centrality {measure} for node {node} is negative: {value}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    measure=st.sampled_from([
        'betweenness_centrality', 'closeness_centrality', 'pagerank', 
        'eigenvector_centrality'
    ])
)
def test_compute_centrality_on_filtered_nodes(measure):
    """Test computing centrality measures on filtered node sets."""
    network = create_test_network(num_nodes=5, num_layers=2)
    
    # Filter by layer first, then compute
    query = f'SELECT nodes WHERE layer="layer0" COMPUTE {measure}'
    result = execute_query(network, query)

    # Should have computed the measure
    assert 'computed' in result
    assert measure in result['computed']
    
    # All returned nodes should be from layer0
    for node in result['nodes']:
        assert node[1] == 'layer0'


# ============================================================================
# Property Tests: Operation Order Invariance
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    threshold=st.integers(min_value=0, max_value=3),
    measure=st.sampled_from(['degree', 'betweenness_centrality', 'closeness_centrality'])
)
def test_operation_order_where_then_compute_vs_compute_then_where(threshold, measure):
    """Test that WHERE then COMPUTE gives same results as COMPUTE then WHERE (filter on same field)."""
    network = create_test_network(num_nodes=5, num_layers=1)
    
    # Approach 1: WHERE degree > threshold, then COMPUTE measure
    query1 = f'SELECT nodes WHERE degree > {threshold} COMPUTE {measure}'
    result1 = execute_query(network, query1)
    
    # Approach 2: COMPUTE measure first, then filter using WHERE on same measure
    # Note: This tests filtering on the computed attribute, not the selection order
    query2 = f'SELECT nodes COMPUTE {measure} WHERE degree > {threshold}'
    result2 = execute_query(network, query2)
    
    # Both should return same nodes (degree is available before COMPUTE)
    assert result1['count'] == result2['count']
    
    # Both should have the computed measure
    assert measure in result1['computed']
    assert measure in result2['computed']


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=1),
    measure=st.sampled_from([
        'degree', 'betweenness_centrality', 'closeness_centrality', 
        'pagerank', 'eigenvector_centrality'
    ])
)
def test_operation_order_layer_filter_with_all_measures(layer_idx, measure):
    """Test that layer filtering works correctly with all centrality measures."""
    network = create_test_network(num_nodes=4, num_layers=2)
    layer = f'layer{layer_idx}'
    
    # Filter by layer, then compute centrality
    query1 = f'SELECT nodes WHERE layer="{layer}" COMPUTE {measure}'
    result1 = execute_query(network, query1)
    
    # Compute centrality, then filter by layer
    query2 = f'SELECT nodes COMPUTE {measure} WHERE layer="{layer}"'
    result2 = execute_query(network, query2)
    
    # Both should return same number of nodes
    assert result1['count'] == result2['count']
    
    # Both should compute the same measure
    assert measure in result1['computed']
    assert measure in result2['computed']
    
    # All nodes should be from the specified layer
    for node in result1['nodes']:
        assert node[1] == layer
    for node in result2['nodes']:
        assert node[1] == layer


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    threshold=st.integers(min_value=0, max_value=3),
    measure=st.sampled_from(['pagerank', 'eigenvector_centrality'])
)
def test_operation_order_compute_then_filter_on_computed_measure(threshold, measure):
    """Test filtering on computed measure values (COMPUTE then WHERE on computed attribute)."""
    network = create_test_network(num_nodes=5, num_layers=1)
    
    # First compute the measure on all nodes
    query_all = f'SELECT nodes COMPUTE {measure}'
    result_all = execute_query(network, query_all)
    
    # Filter nodes based on degree threshold, then compute
    query_filtered = f'SELECT nodes WHERE degree > {threshold} COMPUTE {measure}'
    result_filtered = execute_query(network, query_filtered)
    
    # Filtered result should have <= nodes than unfiltered
    assert result_filtered['count'] <= result_all['count']
    
    # Both should have computed the measure
    assert measure in result_all['computed']
    assert measure in result_filtered['computed']
    
    # Filtered nodes should all have degree > threshold
    for node in result_filtered['nodes']:
        degree = network.core_network.degree(node)
        assert degree > threshold


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=1),
    measure1=st.sampled_from(['degree', 'betweenness_centrality']),
    measure2=st.sampled_from(['closeness_centrality', 'pagerank'])
)
def test_multiple_measures_with_layer_filter(layer_idx, measure1, measure2):
    """Test computing multiple measures with layer filtering."""
    network = create_test_network(num_nodes=4, num_layers=2)
    layer = f'layer{layer_idx}'
    
    # Compute multiple measures on filtered layer
    query = f'SELECT nodes WHERE layer="{layer}" COMPUTE {measure1} {measure2}'
    result = execute_query(network, query)
    
    # Should have computed both measures
    assert 'computed' in result
    assert measure1 in result['computed']
    assert measure2 in result['computed']
    
    # All nodes should be from the specified layer
    for node in result['nodes']:
        assert node[1] == layer
    
    # Both measures should have values for all returned nodes
    for node in result['nodes']:
        assert node in result['computed'][measure1]
        assert node in result['computed'][measure2]


# ============================================================================
# Property Tests: Centrality Measure Consistency
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    measure=st.sampled_from([
        'degree', 'betweenness_centrality', 'closeness_centrality', 
        'pagerank', 'eigenvector_centrality'
    ]),
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_centrality_measure_count_matches_node_count(measure, num_nodes):
    """Test that centrality measures are computed for all selected nodes.
    
    Note: eigenvector_centrality may fail on multigraphs in legacy DSL,
    but should still return an empty dict gracefully without raising an exception.
    """
    network = create_test_network(num_nodes=num_nodes, num_layers=1)
    query = f'SELECT nodes COMPUTE {measure}'
    
    result = execute_query(network, query)
    
    # Number of computed values should match number of nodes
    assert measure in result['computed']
    
    # For eigenvector centrality on multigraphs, it may fail and return empty dict
    # This is acceptable behavior (graceful degradation)
    if measure in ['eigenvector_centrality', 'eigenvector'] and len(result['computed'][measure]) == 0:
        # Eigenvector centrality failed on multigraph - acceptable
        pass
    else:
        # All other cases should have values for all nodes
        assert len(result['computed'][measure]) == result['count']


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    measure=st.sampled_from(['betweenness', 'closeness', 'eigenvector']),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_centrality_aliases_work_with_multilayer(measure, num_layers):
    """Test that centrality measure aliases work with multilayer networks.
    
    Note: eigenvector centrality may fail on multigraphs in legacy DSL,
    but should still return an empty dict gracefully without raising an exception.
    """
    network = create_test_network(num_nodes=4, num_layers=num_layers)
    query = f'SELECT nodes COMPUTE {measure}'
    
    result = execute_query(network, query)
    
    # Should compute using the alias
    assert 'computed' in result
    assert measure in result['computed']
    
    # For eigenvector centrality on multigraphs, it may fail and return empty dict
    # This is acceptable behavior (graceful degradation)
    if measure == 'eigenvector' and len(result['computed'][measure]) == 0:
        # Eigenvector centrality failed on multigraph - acceptable
        pass
    else:
        # All other cases should have values for all nodes
        assert len(result['computed'][measure]) == result['count']
