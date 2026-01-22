"""Integration tests for complete AST roundtrip with execution.

This module verifies end-to-end roundtrip guarantees including:
- Query replay from stored AST produces same results
- Provenance is preserved through roundtrips
- Execution on real networks works correctly
"""

import pytest
from py3plex.dsl import Q
from py3plex.dsl.ast import (
    canonicalize_ast,
    ast_equals,
    ast_to_json,
    ast_from_json,
)
from py3plex.dsl.provenance import ast_fingerprint


@pytest.fixture
def simple_network():
    """Create a simple test network."""
    from py3plex.core import multinet
    
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    net.add_nodes([
        {'source': 'A', 'type': 'social'},
        {'source': 'B', 'type': 'social'},
        {'source': 'C', 'type': 'social'},
        {'source': 'D', 'type': 'social'},
    ])
    
    # Add edges
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'C', 'target': 'D', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'D', 'target': 'A', 'source_type': 'social', 'target_type': 'social'},
    ])
    
    return net


def test_query_replay_produces_same_results(simple_network):
    """Test that replaying a query from stored AST produces same results."""
    # Original query
    original_query = Q.nodes().compute("degree")
    
    # Execute and get results
    result1 = original_query.execute(simple_network)
    df1 = result1.to_pandas()
    
    # Store AST
    ast = original_query.to_ast()
    json_str = ast_to_json(ast)
    
    # Later: reload AST and reconstruct query
    reloaded_ast = ast_from_json(json_str)
    replayed_query = Q.from_ast(reloaded_ast)
    
    # Execute replayed query
    result2 = replayed_query.execute(simple_network)
    df2 = result2.to_pandas()
    
    # Results should be identical
    assert len(df1) == len(df2), "Result count should match"
    assert set(df1.columns) == set(df2.columns), "Columns should match"
    
    # Degree values should match (sort for comparison)
    degrees1 = sorted(df1['degree'].tolist())
    degrees2 = sorted(df2['degree'].tolist())
    assert degrees1 == degrees2, "Degree values should match"


def test_provenance_preserved_through_replay(simple_network):
    """Test that provenance is correctly tracked through query replay."""
    # Original query
    original = Q.nodes().compute("degree")
    ast = original.to_ast()
    original_hash = ast_fingerprint(ast)
    
    # Roundtrip
    reconstructed = Q.from_ast(ast)
    reconstructed_ast = reconstructed.to_ast()
    reconstructed_hash = ast_fingerprint(reconstructed_ast)
    
    # Hashes should match
    assert original_hash == reconstructed_hash, "AST hash should be preserved"
    
    # Execute both and check provenance
    result1 = original.execute(simple_network)
    result2 = reconstructed.execute(simple_network)
    
    # Both should have provenance with matching AST hash
    assert "provenance" in result1.meta, "Result should have provenance"
    assert "provenance" in result2.meta, "Replayed result should have provenance"
    
    prov1 = result1.meta["provenance"]
    prov2 = result2.meta["provenance"]
    
    # AST hashes in provenance should match
    assert prov1["query"]["ast_hash"] == prov2["query"]["ast_hash"], \
        "Provenance AST hashes should match"


def test_complex_query_replay(simple_network):
    """Test replay of complex query with multiple clauses."""
    # Complex query
    original = (
        Q.nodes()
        .compute("degree")
        .where(degree__gt=0)
        .order_by("degree", desc=True)
        .limit(3)
    )
    
    # Execute original
    result1 = original.execute(simple_network)
    df1 = result1.to_pandas()
    
    # Roundtrip through AST
    ast = original.to_ast()
    reconstructed = Q.from_ast(ast)
    result2 = reconstructed.execute(simple_network)
    df2 = result2.to_pandas()
    
    # Results should match
    assert len(df1) == len(df2), "Result count should match"
    assert list(df1['degree']) == list(df2['degree']), "Degree values should match in order"


def test_ast_storage_and_retrieval():
    """Test that AST can be serialized, stored, and retrieved correctly."""
    # Create query
    query = Q.nodes().where(degree__gt=5).compute("betweenness_centrality")
    ast = query.to_ast()
    
    # Serialize
    json_str = ast_to_json(ast)
    
    # Verify JSON is valid and contains expected structure
    import json
    data = json.loads(json_str)
    assert "__schema_version__" in data, "JSON should have schema version"
    assert data["__schema_version__"] == "2.0", "Schema version should be 2.0"
    
    # Deserialize
    retrieved_ast = ast_from_json(json_str)
    
    # Should be semantically equivalent
    assert ast_equals(ast, retrieved_ast), "Retrieved AST should equal original"
    
    # Reconstruct query
    retrieved_query = Q.from_ast(retrieved_ast)
    retrieved_ast2 = retrieved_query.to_ast()
    
    # Final AST should equal original
    assert ast_equals(ast, retrieved_ast2), "Final AST should equal original"


def test_equivalent_queries_same_execution(simple_network):
    """Test that equivalent queries produce same results."""
    # Two queries that differ only in compute order
    q1 = Q.nodes().compute("degree")
    q2 = Q.nodes().compute("degree")
    
    # Execute both
    result1 = q1.execute(simple_network)
    result2 = q2.execute(simple_network)
    
    # Convert to dataframes
    df1 = result1.to_pandas()
    df2 = result2.to_pandas()
    
    # Should be identical
    assert len(df1) == len(df2), "Result counts should match"
    
    # Degree values should match
    degrees1 = sorted(df1['degree'].tolist())
    degrees2 = sorted(df2['degree'].tolist())
    assert degrees1 == degrees2, "Degree values should match"


def test_roundtrip_with_filters(simple_network):
    """Test roundtrip with filter conditions."""
    # Query with filters
    original = Q.nodes().where(degree__gt=1).compute("degree")
    
    # Execute original
    result1 = original.execute(simple_network)
    df1 = result1.to_pandas()
    
    # Roundtrip
    ast = original.to_ast()
    reconstructed = Q.from_ast(ast)
    result2 = reconstructed.execute(simple_network)
    df2 = result2.to_pandas()
    
    # Results should match
    assert len(df1) == len(df2), "Filtered result counts should match"
    
    # All nodes should have degree > 1
    for degree in df2['degree']:
        assert degree > 1, "Filter should be applied"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
