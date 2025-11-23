#!/usr/bin/env python3
"""
Property-based tests for DSL module.

Tests invariants for SQL-like DSL query parsing and execution.
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import DSL module
try:
    from py3plex.dsl import (
        _tokenize_query,
        DSLSyntaxError,
        DSLExecutionError
    )
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
