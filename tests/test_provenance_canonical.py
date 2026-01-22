"""Tests for provenance integration with canonical AST hashing.

This module verifies that:
- Provenance ast_hash is computed from canonical AST
- Equivalent queries produce identical ast_hash
- Roundtrip-reconstructed queries preserve ast_hash
"""

import pytest
from py3plex.dsl import Q
from py3plex.dsl.provenance import ast_fingerprint
from py3plex.dsl.ast import canonicalize_ast, ast_equals


def test_provenance_uses_canonical_ast_hash():
    """Test that ast_fingerprint uses canonical AST."""
    # Two queries that differ only in compute order (commutative)
    q1 = Q.nodes().compute("degree", "betweenness_centrality")
    q2 = Q.nodes().compute("betweenness_centrality", "degree")
    
    # Get AST fingerprints
    hash1 = ast_fingerprint(q1.to_ast())
    hash2 = ast_fingerprint(q2.to_ast())
    
    # Hashes should be identical because compute order doesn't matter semantically
    assert hash1 == hash2, "Compute order should not affect AST hash"


def test_provenance_roundtrip_preserves_hash():
    """Test that roundtrip reconstruction preserves AST hash."""
    original = Q.nodes().where(degree__gt=5).compute("betweenness_centrality")
    
    # Get original hash
    ast1 = original.to_ast()
    hash1 = ast_fingerprint(ast1)
    
    # Roundtrip
    reconstructed = Q.from_ast(ast1)
    ast2 = reconstructed.to_ast()
    hash2 = ast_fingerprint(ast2)
    
    # Hash should be preserved
    assert hash1 == hash2, "Roundtrip should preserve AST hash"


def test_provenance_equivalent_queries_same_hash():
    """Test that semantically equivalent queries have same hash."""
    # Queries that differ only in filter order (AND is commutative)
    q1 = Q.nodes().where(degree__gt=5, layer="social")
    q2 = Q.nodes().where(layer="social", degree__gt=5)
    
    hash1 = ast_fingerprint(q1.to_ast())
    hash2 = ast_fingerprint(q2.to_ast())
    
    assert hash1 == hash2, "Filter order (AND) should not affect AST hash"


def test_provenance_different_queries_different_hash():
    """Test that different queries have different hashes."""
    q1 = Q.nodes().where(degree__gt=5)
    q2 = Q.nodes().where(degree__gt=10)
    
    hash1 = ast_fingerprint(q1.to_ast())
    hash2 = ast_fingerprint(q2.to_ast())
    
    assert hash1 != hash2, "Different queries should have different hashes"


def test_provenance_hash_stable_across_runs():
    """Test that AST hash is stable across multiple calls."""
    q = Q.nodes().where(degree__gt=5).compute("betweenness_centrality")
    ast = q.to_ast()
    
    # Compute hash multiple times
    hashes = [ast_fingerprint(ast) for _ in range(5)]
    
    # All should be identical
    assert len(set(hashes)) == 1, "AST hash should be stable"


def test_provenance_json_roundtrip_preserves_hash():
    """Test that JSON roundtrip preserves AST hash."""
    from py3plex.dsl.ast import ast_to_json, ast_from_json
    
    original = Q.nodes().where(degree__gt=5).compute("degree")
    ast1 = original.to_ast()
    hash1 = ast_fingerprint(ast1)
    
    # JSON roundtrip
    json_str = ast_to_json(ast1)
    ast2 = ast_from_json(json_str)
    hash2 = ast_fingerprint(ast2)
    
    # Hash should be preserved
    assert hash1 == hash2, "JSON roundtrip should preserve AST hash"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
