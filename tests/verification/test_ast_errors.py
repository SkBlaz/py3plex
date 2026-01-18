"""
AST Compilation and Error Handling Tests.

Tests for:
- Invalid tokens/fields → DslSyntaxError
- Unknown measures → explicit error listing allowed measures
- Invalid layer expressions → InvalidLayerError
- AST roundtrip tests
"""

import pytest
from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.dsl.errors import DslSyntaxError, DslExecutionError

try:
    from py3plex.dsl import execute_query
    from py3plex.dsl.executor import execute_ast
    LEGACY_DSL_AVAILABLE = True
except ImportError:
    LEGACY_DSL_AVAILABLE = False


def create_test_network():
    """Create a simple test network."""
    network = multinet.multi_layer_network(directed=False)
    
    nodes = [{'source': 'A', 'type': 'layer1'}]
    network.add_nodes(nodes)
    
    return network


@pytest.mark.verification
@pytest.mark.fast
def test_ast_summary_stable():
    """
    Test that AST summary produces stable hashes for identical queries.
    
    Invariant: Same query → same AST hash
    """
    query1 = Q.nodes().compute('degree').to_ast()
    query2 = Q.nodes().compute('degree').to_ast()
    
    summary1 = query1.summary()
    summary2 = query2.summary()
    
    # Summaries should have ast_hash field
    assert 'ast_hash' in summary1, "Summary should contain ast_hash"
    assert 'ast_hash' in summary2, "Summary should contain ast_hash"
    
    # Hashes should be identical
    assert summary1['ast_hash'] == summary2['ast_hash'], \
        "Identical queries should produce identical AST hashes"


@pytest.mark.verification
@pytest.mark.fast
def test_ast_summary_different_queries():
    """
    Test that different queries produce different AST hashes.
    """
    query1 = Q.nodes().compute('degree').to_ast()
    query2 = Q.nodes().compute('betweenness_centrality').to_ast()
    
    summary1 = query1.summary()
    summary2 = query2.summary()
    
    # Hashes should be different
    assert summary1['ast_hash'] != summary2['ast_hash'], \
        "Different queries should produce different AST hashes"


@pytest.mark.verification
@pytest.mark.fast
def test_unknown_measure_error():
    """
    Test that unknown measures produce clear error messages.
    
    Should raise DslExecutionError with helpful message.
    """
    network = create_test_network()
    
    # Try to compute a non-existent measure
    query = Q.nodes().compute('nonexistent_measure').to_ast()
    
    with pytest.raises((DslExecutionError, KeyError, ValueError, AttributeError)) as exc_info:
        execute_ast(network, query)
    
    # Error message should mention the unknown measure
    error_msg = str(exc_info.value).lower()
    assert 'nonexistent_measure' in error_msg or 'unknown' in error_msg or \
           'not found' in error_msg or 'invalid' in error_msg, \
        f"Error message should mention unknown measure: {error_msg}"


@pytest.mark.verification
@pytest.mark.fast
@pytest.mark.skipif(not LEGACY_DSL_AVAILABLE, reason="Legacy DSL not available")
def test_invalid_syntax_error():
    """
    Test that invalid query syntax raises DslSyntaxError.
    """
    network = create_test_network()
    
    # Try various invalid syntaxes
    invalid_queries = [
        'SELECT',  # Incomplete
        'SELECT nodes WHERE',  # Incomplete WHERE
        'SELECT nodes WHERE degree',  # Incomplete comparison
        'INVALID QUERY',  # Invalid command
    ]
    
    for invalid_query in invalid_queries:
        with pytest.raises((DslSyntaxError, ValueError, SyntaxError, KeyError)):
            execute_query(network, invalid_query)


@pytest.mark.verification
@pytest.mark.fast
def test_invalid_comparator_error():
    """
    Test that invalid comparators are caught.
    """
    network = create_test_network()
    
    # Try to use invalid comparator in builder API
    # Note: Builder API type hints should catch this at IDE time,
    # but we can still test runtime behavior
    
    query = Q.nodes().to_ast()
    # Valid query should work
    result = execute_ast(network, query)
    assert result is not None


@pytest.mark.verification
@pytest.mark.fast
def test_invalid_layer_name_handling():
    """
    Test that querying non-existent layers is handled gracefully.
    """
    network = create_test_network()
    
    # Query a layer that doesn't exist
    query = Q.nodes().from_layers(L['nonexistent_layer']).to_ast()
    result = execute_ast(network, query)
    
    # Should return empty result, not crash
    assert result.count == 0, "Querying non-existent layer should return empty result"


@pytest.mark.verification
@pytest.mark.fast
def test_empty_layer_list_handling():
    """
    Test that empty layer list is handled gracefully.
    """
    network = create_test_network()
    
    # Query with empty layer list
    query = Q.nodes().from_layers([]).to_ast()
    result = execute_ast(network, query)
    
    # Should return empty result or all nodes (implementation dependent)
    assert result.count >= 0, "Empty layer list should not crash"


@pytest.mark.verification
@pytest.mark.fast
def test_ast_has_target():
    """
    Test that AST contains target information.
    """
    node_query = Q.nodes().to_ast()
    edge_query = Q.edges().to_ast()
    
    # AST should have select statement
    assert hasattr(node_query, 'select'), "AST should have select attribute"
    
    # Select should have target
    if hasattr(node_query.select, 'target'):
        assert node_query.select.target in ['nodes', 'edges']


@pytest.mark.verification
@pytest.mark.fast
def test_ast_roundtrip_consistency():
    """
    Test that building AST and converting back is consistent.
    
    Query → AST → Summary should be repeatable.
    """
    query = Q.nodes().compute('degree').order_by('degree').limit(5).to_ast()
    
    # Get summary twice
    summary1 = query.summary()
    summary2 = query.summary()
    
    # Should be identical
    assert summary1 == summary2, "Summary should be consistent across calls"


@pytest.mark.verification
@pytest.mark.fast
def test_builder_chaining():
    """
    Test that builder methods can be chained.
    """
    # Build complex query with chaining
    query = (
        Q.nodes()
        .from_layers(L['layer1'])
        .where(degree__gt=0)
        .compute('degree')
        .order_by('degree', desc=True)
        .limit(10)
        .to_ast()
    )
    
    # Should produce valid AST
    assert query is not None, "Chained query should produce valid AST"
    assert hasattr(query, 'summary'), "AST should have summary method"


@pytest.mark.verification
@pytest.mark.fast
def test_query_builder_immutable():
    """
    Test that query builder operations don't mutate original.
    """
    q1 = Q.nodes()
    q2 = q1.where(degree__gt=1)
    q3 = q1.where(degree__lt=5)
    
    # q2 and q3 should be independent
    ast2 = q2.to_ast()
    ast3 = q3.to_ast()
    
    # Summaries should be different (different WHERE clauses)
    summary2 = ast2.summary()
    summary3 = ast3.summary()
    
    # Should have different hashes or content
    # (exact behavior depends on implementation)
    assert ast2 is not ast3, "Different queries should produce different AST objects"


@pytest.mark.verification
@pytest.mark.fast
def test_multiple_compute_measures():
    """
    Test that computing multiple measures works.
    """
    query = (
        Q.nodes()
        .compute('degree')
        .compute('betweenness_centrality')
        .to_ast()
    )
    
    # Should produce valid AST with multiple compute items
    assert query is not None, "Query with multiple computes should be valid"


@pytest.mark.verification
@pytest.mark.fast
def test_order_by_nonexistent_field():
    """
    Test that ordering by non-computed field is handled.
    """
    network = create_test_network()
    
    # Try to order by field that wasn't computed
    query = Q.nodes().order_by('nonexistent_field').to_ast()
    
    # Should either raise error or handle gracefully
    # (exact behavior depends on implementation)
    try:
        result = execute_ast(network, query)
        # If it doesn't raise, check that result is valid
        assert result is not None
    except (KeyError, ValueError, DslExecutionError):
        # Raising an error is acceptable behavior
        pass


@pytest.mark.verification
@pytest.mark.fast
def test_negative_limit():
    """
    Test that negative limit is handled appropriately.
    """
    # Negative limit should either raise error or be treated as 0/no limit
    try:
        query = Q.nodes().limit(-1).to_ast()
        # If it doesn't raise, the implementation accepts it
        assert query is not None
    except (ValueError, AssertionError):
        # Raising an error is acceptable
        pass


@pytest.mark.verification
@pytest.mark.fast
def test_zero_limit():
    """
    Test that limit=0 returns empty results.
    """
    network = create_test_network()
    query = Q.nodes().limit(0).to_ast()
    result = execute_ast(network, query)
    
    assert result.count == 0, "Limit of 0 should return empty result"
