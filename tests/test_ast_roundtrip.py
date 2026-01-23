"""Tests for AST roundtrip guarantees in DSL v2.

This module enforces the fundamental invariant:
    canonical_ast(q.to_ast()) == canonical_ast(Q.from_ast(q.to_ast()).to_ast())

Tests cover:
- Builder → AST → Builder → AST roundtrip
- JSON serialization roundtrip
- Canonicalization stability
- AST equality and diff operations
- Error handling for invalid ASTs
"""

import pytest
from py3plex.dsl import Q, L
from py3plex.dsl.ast import (
    canonicalize_ast,
    ast_equals,
    ast_diff,
    ast_to_json,
    ast_from_json,
    Query,
    Target,
)
from py3plex.dsl.errors import (
    ASTValidationError,
    ASTSchemaVersionError,
    ASTInvalidStructureError,
    ASTMissingFieldError,
)


# ==============================================================================
# Basic Roundtrip Tests
# ==============================================================================


def test_simple_nodes_query_roundtrip():
    """Test roundtrip of simple nodes query."""
    # Build query
    original = Q.nodes()
    
    # Convert to AST
    ast1 = original.to_ast()
    
    # Reconstruct from AST
    reconstructed = Q.from_ast(ast1)
    
    # Convert back to AST
    ast2 = reconstructed.to_ast()
    
    # Canonical ASTs should be equal
    assert ast_equals(ast1, ast2), "Roundtrip failed for simple nodes query"


def test_nodes_with_where_roundtrip():
    """Test roundtrip of nodes query with WHERE filter."""
    original = Q.nodes().where(degree__gt=5)
    ast1 = original.to_ast()
    reconstructed = Q.from_ast(ast1)
    ast2 = reconstructed.to_ast()
    assert ast_equals(ast1, ast2), "Roundtrip failed for WHERE filter"


def test_nodes_with_compute_roundtrip():
    """Test roundtrip of nodes query with COMPUTE."""
    original = Q.nodes().compute("degree", "betweenness_centrality")
    ast1 = original.to_ast()
    reconstructed = Q.from_ast(ast1)
    ast2 = reconstructed.to_ast()
    assert ast_equals(ast1, ast2), "Roundtrip failed for COMPUTE"


def test_nodes_with_order_roundtrip():
    """Test roundtrip of nodes query with ORDER BY."""
    original = Q.nodes().compute("degree").order_by("degree", desc=True)
    ast1 = original.to_ast()
    reconstructed = Q.from_ast(ast1)
    ast2 = reconstructed.to_ast()
    assert ast_equals(ast1, ast2), "Roundtrip failed for ORDER BY"


def test_nodes_with_limit_roundtrip():
    """Test roundtrip of nodes query with LIMIT."""
    original = Q.nodes().compute("degree").limit(20)
    ast1 = original.to_ast()
    reconstructed = Q.from_ast(ast1)
    ast2 = reconstructed.to_ast()
    assert ast_equals(ast1, ast2), "Roundtrip failed for LIMIT"


def test_complex_query_roundtrip():
    """Test roundtrip of complex query with multiple clauses."""
    original = (
        Q.nodes()
        .where(degree__gt=5, layer="social")
        .compute("degree", "betweenness_centrality")
        .order_by("betweenness_centrality", desc=True)
        .limit(10)
    )
    ast1 = original.to_ast()
    reconstructed = Q.from_ast(ast1)
    ast2 = reconstructed.to_ast()
    assert ast_equals(ast1, ast2), "Roundtrip failed for complex query"


def test_edges_query_roundtrip():
    """Test roundtrip of edges query."""
    original = Q.edges().where(intralayer=True)
    ast1 = original.to_ast()
    reconstructed = Q.from_ast(ast1)
    ast2 = reconstructed.to_ast()
    assert ast_equals(ast1, ast2), "Roundtrip failed for edges query"


# ==============================================================================
# Canonicalization Tests
# ==============================================================================


def test_canonicalization_sorts_compute():
    """Test that canonicalization sorts compute items."""
    q1 = Q.nodes().compute("degree", "betweenness_centrality")
    q2 = Q.nodes().compute("betweenness_centrality", "degree")
    
    ast1 = canonicalize_ast(q1.to_ast())
    ast2 = canonicalize_ast(q2.to_ast())
    
    # After canonicalization, compute order shouldn't matter
    assert ast1 == ast2, "Canonicalization should sort compute items"


def test_canonicalization_sorts_and_filters():
    """Test that canonicalization sorts AND filters."""
    q1 = Q.nodes().where(degree__gt=5, layer="social")
    q2 = Q.nodes().where(layer="social", degree__gt=5)
    
    ast1 = canonicalize_ast(q1.to_ast())
    ast2 = canonicalize_ast(q2.to_ast())
    
    # After canonicalization, AND filter order shouldn't matter
    assert ast1 == ast2, "Canonicalization should sort AND filters"


def test_canonicalization_normalizes_floats():
    """Test that canonicalization normalizes float precision.
    
    Note: Canonicalization normalizes to 10 decimal places.
    Values that differ beyond this precision remain distinct.
    """
    # These differ at the 11th decimal place - should be normalized
    q1 = Q.nodes().where(weight__gt=0.12345678901)
    q2 = Q.nodes().where(weight__gt=0.12345678902)
    
    ast1 = canonicalize_ast(q1.to_ast())
    ast2 = canonicalize_ast(q2.to_ast())
    
    # After canonicalization to 10 decimals, these should be equal
    assert ast1 == ast2, "Canonicalization should normalize float precision to 10 decimals"


def test_canonicalization_stability():
    """Test that canonicalization is stable (idempotent)."""
    original = (
        Q.nodes()
        .compute("betweenness_centrality", "degree")
        .where(layer="social", degree__gt=5)
    )
    
    ast = original.to_ast()
    canonical1 = canonicalize_ast(ast)
    canonical2 = canonicalize_ast(canonical1)
    
    # Canonicalizing a canonical AST should produce the same result
    assert canonical1 == canonical2, "Canonicalization should be idempotent"


# ==============================================================================
# JSON Serialization Tests
# ==============================================================================


def test_json_roundtrip_simple():
    """Test JSON serialization roundtrip for simple query."""
    original = Q.nodes().where(degree__gt=5)
    ast = original.to_ast()
    
    # Serialize to JSON
    json_str = ast_to_json(ast)
    
    # Deserialize from JSON
    reconstructed_ast = ast_from_json(json_str)
    
    # Should be equivalent
    assert ast_equals(ast, reconstructed_ast), "JSON roundtrip failed"


def test_json_roundtrip_complex():
    """Test JSON serialization roundtrip for complex query."""
    original = (
        Q.nodes()
        .where(degree__gt=5, layer="social")
        .compute("degree", "betweenness_centrality")
        .order_by("betweenness_centrality", desc=True)
        .limit(10)
    )
    ast = original.to_ast()
    
    json_str = ast_to_json(ast)
    reconstructed_ast = ast_from_json(json_str)
    
    assert ast_equals(ast, reconstructed_ast), "JSON roundtrip failed for complex query"


def test_json_contains_schema_version():
    """Test that JSON includes schema version."""
    import json
    
    original = Q.nodes()
    ast = original.to_ast()
    json_str = ast_to_json(ast)
    data = json.loads(json_str)
    
    assert "__schema_version__" in data, "JSON should include schema version"
    assert data["__schema_version__"] == "2.0", "Schema version should be 2.0"


def test_json_incompatible_schema_version():
    """Test that incompatible schema version raises error."""
    import json
    
    # Create JSON with incompatible version
    data = {
        "__schema_version__": "3.0",
        "__type__": "Query",
        "explain": False,
        "select": {},
    }
    json_str = json.dumps(data)
    
    with pytest.raises(ValueError, match="Incompatible schema version"):
        ast_from_json(json_str)


# ==============================================================================
# AST Equality and Diff Tests
# ==============================================================================


def test_ast_equals_identical():
    """Test ast_equals returns True for identical ASTs."""
    q = Q.nodes().where(degree__gt=5)
    ast1 = q.to_ast()
    ast2 = q.to_ast()
    assert ast_equals(ast1, ast2), "Identical ASTs should be equal"


def test_ast_equals_different_target():
    """Test ast_equals returns False for different targets."""
    ast1 = Q.nodes().to_ast()
    ast2 = Q.edges().to_ast()
    assert not ast_equals(ast1, ast2), "Different targets should not be equal"


def test_ast_diff_shows_differences():
    """Test ast_diff identifies differences."""
    ast1 = Q.nodes().where(degree__gt=5).to_ast()
    ast2 = Q.nodes().where(degree__gt=10).to_ast()
    
    diff = ast_diff(ast1, ast2)
    assert not diff["equal"], "Different ASTs should not be equal"
    assert "where_diff" in diff, "Diff should identify WHERE difference"


def test_ast_diff_identical():
    """Test ast_diff returns equal=True for identical ASTs."""
    q = Q.nodes().where(degree__gt=5)
    ast1 = q.to_ast()
    ast2 = q.to_ast()
    
    diff = ast_diff(ast1, ast2)
    assert diff["equal"], "Identical ASTs should have equal=True in diff"


# ==============================================================================
# Negative Tests (Error Handling)
# ==============================================================================


def test_from_ast_invalid_type():
    """Test from_ast raises error for non-Query input."""
    with pytest.raises(TypeError, match="Expected Query AST"):
        Q.from_ast("not an AST")


def test_from_ast_incompatible_version():
    """Test from_ast raises error for incompatible version."""
    from py3plex.dsl.ast import Query, SelectStmt
    
    # Create AST with incompatible version
    ast = Query(
        explain=False,
        select=SelectStmt(target=Target.NODES),
        dsl_version="3.0"
    )
    
    with pytest.raises(ValueError, match="Incompatible DSL version"):
        Q.from_ast(ast)


def test_from_ast_invalid_select():
    """Test from_ast raises error for invalid select statement."""
    ast = Query(
        explain=False,
        select="not a SelectStmt",
        dsl_version="2.0"
    )
    
    with pytest.raises(TypeError, match="Expected SelectStmt"):
        Q.from_ast(ast)


# ==============================================================================
# Integration Tests
# ==============================================================================


def test_multiple_roundtrips():
    """Test that multiple roundtrips maintain equivalence."""
    original = Q.nodes().where(degree__gt=5).compute("betweenness_centrality")
    
    # First roundtrip
    ast1 = original.to_ast()
    recon1 = Q.from_ast(ast1)
    ast2 = recon1.to_ast()
    
    # Second roundtrip
    recon2 = Q.from_ast(ast2)
    ast3 = recon2.to_ast()
    
    # Third roundtrip
    recon3 = Q.from_ast(ast3)
    ast4 = recon3.to_ast()
    
    # All should be equivalent
    assert ast_equals(ast1, ast2), "First roundtrip failed"
    assert ast_equals(ast2, ast3), "Second roundtrip failed"
    assert ast_equals(ast3, ast4), "Third roundtrip failed"
    assert ast_equals(ast1, ast4), "Transitive equality failed"


def test_json_then_builder_roundtrip():
    """Test AST → JSON → AST → Builder → AST roundtrip."""
    original = Q.nodes().where(degree__gt=5).compute("degree")
    
    # AST → JSON → AST
    ast1 = original.to_ast()
    json_str = ast_to_json(ast1)
    ast2 = ast_from_json(json_str)
    
    # AST → Builder → AST
    rebuilt = Q.from_ast(ast2)
    ast3 = rebuilt.to_ast()
    
    # All should be equivalent
    assert ast_equals(ast1, ast2), "JSON roundtrip failed"
    assert ast_equals(ast2, ast3), "Builder reconstruction failed"
    assert ast_equals(ast1, ast3), "Full roundtrip failed"


# ==============================================================================
# Property-Based Tests (Hypothesis)
# ==============================================================================


try:
    from hypothesis import given, strategies as st
    
    # Strategy for generating simple queries
    @st.composite
    def simple_query_strategy(draw):
        """Generate a simple but valid DSL query."""
        target = draw(st.sampled_from(["nodes", "edges"]))
        
        if target == "nodes":
            builder = Q.nodes()
        else:
            builder = Q.edges()
        
        # Optionally add WHERE
        if draw(st.booleans()):
            threshold = draw(st.integers(min_value=1, max_value=10))
            builder = builder.where(degree__gt=threshold)
        
        # Optionally add COMPUTE
        if draw(st.booleans()):
            measures = draw(
                st.lists(
                    st.sampled_from(["degree", "betweenness_centrality"]),
                    min_size=1,
                    max_size=2,
                    unique=True
                )
            )
            builder = builder.compute(*measures)
        
        # Optionally add LIMIT
        if draw(st.booleans()):
            limit = draw(st.integers(min_value=1, max_value=100))
            builder = builder.limit(limit)
        
        return builder
    
    @given(simple_query_strategy())
    def test_property_any_query_roundtrips(query):
        """Property: Any valid query should roundtrip successfully."""
        ast1 = query.to_ast()
        reconstructed = Q.from_ast(ast1)
        ast2 = reconstructed.to_ast()
        assert ast_equals(ast1, ast2), "Property violated: query failed to roundtrip"
    
except ImportError:
    # Hypothesis not available, skip property-based tests
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
