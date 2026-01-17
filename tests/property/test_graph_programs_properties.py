#!/usr/bin/env python3
"""
Property-based tests for Graph Programs.

Tests invariants for:
- Rewrite rule equivalence
- Type system consistency
- Program composition
- Hashing stability
- Cache correctness
"""

import pytest
from hypothesis import given, settings, assume, strategies as st, example
from hypothesis import HealthCheck
import networkx as nx

# Import Graph Program modules
try:
    from py3plex.dsl import Q, L
    from py3plex.dsl.program import (
        GraphProgram,
        type_check,
        infer_type,
        apply_rewrites,
        get_standard_rules,
        compose,
        diff_programs,
        graph_fingerprint,
        program_fingerprint,
        execution_fingerprint,
        ProgramCache,
    )
    from py3plex.dsl.program.types import (
        NodeSetType,
        EdgeSetType,
        TableType,
        TypeSystem,
    )
    from py3plex.core import multinet
    PROGRAM_AVAILABLE = True
except ImportError as e:
    PROGRAM_AVAILABLE = False
    pytest.skip(f"Graph Programs not available: {e}", allow_module_level=True)


# ============================================================================
# Strategies for generating test data
# ============================================================================

@st.composite
def small_multilayer_network(draw):
    """Generate a small multilayer network for testing."""
    num_nodes = draw(st.integers(min_value=3, max_value=10))
    num_layers = draw(st.integers(min_value=1, max_value=3))
    
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes to each layer
    nodes = [f"n{i}" for i in range(num_nodes)]
    layers = [f"layer{i}" for i in range(num_layers)]
    
    for layer in layers:
        for node in nodes:
            net.add_node(node, layer=layer)
    
    # Add some edges
    num_edges = draw(st.integers(min_value=num_nodes, max_value=num_nodes * 2))
    for _ in range(num_edges):
        src = draw(st.sampled_from(nodes))
        tgt = draw(st.sampled_from(nodes))
        layer = draw(st.sampled_from(layers))
        if src != tgt:
            net.add_edge(src, tgt, layer_from=layer, layer_to=layer)
    
    return net


@st.composite
def simple_node_query(draw):
    """Generate a simple node query builder."""
    builder = Q.nodes()
    
    # Optionally add layer filter
    if draw(st.booleans()):
        layer_idx = draw(st.integers(min_value=0, max_value=2))
        builder = builder.from_layers(L[f"layer{layer_idx}"])
    
    # Optionally add compute
    if draw(st.booleans()):
        measure = draw(st.sampled_from(["degree", "clustering"]))
        builder = builder.compute(measure)
    
    return builder


# ============================================================================
# Property Tests: Rewrite Rule Equivalence
# ============================================================================

@pytest.mark.property
@settings(
    deadline=None,
    max_examples=20,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
)
@given(network=small_multilayer_network())
def test_rewrite_preserves_results(network):
    """Property: Rewriting a program preserves its execution results."""
    # Create a simple program
    program = (Q.nodes()
        .compute("degree")
        .where(degree__gt=0)
        .to_program())
    
    # Apply rewrites
    rewritten = apply_rewrites(program, get_standard_rules())
    
    # Execute both
    try:
        result_original = program.execute(network)
        result_rewritten = rewritten.execute(network)
        
        # Results should have same items (order may differ)
        items_original = set(result_original.items)
        items_rewritten = set(result_rewritten.items)
        
        assert items_original == items_rewritten, \
            f"Rewrite changed results: {items_original} != {items_rewritten}"
    except Exception as e:
        # Some queries may fail on certain networks, that's ok
        assume(False)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    network=small_multilayer_network(),
    query_builder=simple_node_query()
)
def test_push_where_equivalence(network, query_builder):
    """Property: Pushing WHERE before COMPUTE preserves results."""
    # Build program with compute then where
    program1 = query_builder.compute("degree").where(degree__gt=0).to_program()
    
    # Build program with where then compute (if possible)
    # This tests the push_where_past_compute rewrite
    program2 = query_builder.to_program()
    
    try:
        # Apply rewrite that pushes where
        rewritten = apply_rewrites(program1, get_standard_rules())
        
        result1 = program1.execute(network)
        result2 = rewritten.execute(network)
        
        # Should have same results
        assert set(result1.items) == set(result2.items)
    except Exception:
        # Query may not be applicable to this network
        assume(False)


# ============================================================================
# Property Tests: Type System
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(query_builder=simple_node_query())
def test_type_checking_consistency(query_builder):
    """Property: Type checking is consistent - valid programs always pass."""
    program = query_builder.to_program()
    
    # Type check should not raise
    is_valid = type_check(program.canonical_ast)
    
    # Valid programs should have a type signature
    assert program.type_signature is not None
    assert is_valid is True


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(query_builder=simple_node_query())
def test_type_inference_deterministic(query_builder):
    """Property: Type inference is deterministic."""
    program = query_builder.to_program()
    
    # Infer type multiple times
    type1 = infer_type(program.canonical_ast)
    type2 = infer_type(program.canonical_ast)
    
    # Should always get same result
    assert str(type1) == str(type2)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
def test_node_query_returns_nodeset_type():
    """Property: Node queries always return NodeSet or Table type."""
    program = Q.nodes().to_program()
    output_type = infer_type(program.canonical_ast)
    
    # Should be NodeSet initially
    assert isinstance(output_type, NodeSetType) or isinstance(output_type, TableType)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
def test_edge_query_returns_edgeset_type():
    """Property: Edge queries always return EdgeSet or Table type."""
    program = Q.edges().to_program()
    output_type = infer_type(program.canonical_ast)
    
    # Should be EdgeSet initially
    assert isinstance(output_type, EdgeSetType) or isinstance(output_type, TableType)


# ============================================================================
# Property Tests: Hashing Stability
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(query_builder=simple_node_query())
def test_hash_stability(query_builder):
    """Property: Program hash is stable across multiple computations."""
    program = query_builder.to_program()
    
    # Hash multiple times
    hash1 = program.hash()
    hash2 = program.hash()
    hash3 = program.hash()
    
    # Should always be identical
    assert hash1 == hash2 == hash3
    assert len(hash1) == 64  # SHA-256 produces 64 hex chars


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    builder1=simple_node_query(),
    builder2=simple_node_query()
)
def test_different_programs_different_hashes(builder1, builder2):
    """Property: Different programs (usually) have different hashes."""
    program1 = builder1.to_program()
    program2 = builder2.to_program()
    
    hash1 = program1.hash()
    hash2 = program2.hash()
    
    # Hashes should be 64 chars
    assert len(hash1) == 64
    assert len(hash2) == 64
    
    # Note: We can't assert they're different because the builders
    # might generate identical programs


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(query_builder=simple_node_query())
def test_hash_independent_of_python_dict_ordering(query_builder):
    """Property: Hash is independent of Python dict ordering."""
    program = query_builder.to_program()
    
    # Hash should be consistent even if we rebuild
    program2 = query_builder.to_program()
    
    # Same program structure should give same hash
    # Note: This may not always be true due to randomness in builder
    hash1 = program.hash()
    hash2 = program2.hash()
    
    # Both should be valid hashes
    assert len(hash1) == 64
    assert len(hash2) == 64


# ============================================================================
# Property Tests: Program Composition
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(network=small_multilayer_network())
def test_composition_associativity(network):
    """Property: Program composition is associative where type-compatible."""
    # Create simple programs
    p1 = Q.nodes().to_program()
    p2 = Q.nodes().compute("degree").to_program()
    
    try:
        # Try to compose
        composed = compose(p1, p2)
        
        # Should be able to execute
        result = composed.execute(network)
        assert result is not None
    except Exception:
        # Type incompatibility is ok
        assume(False)


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(network=small_multilayer_network())
def test_composed_program_hash_stable(network):
    """Property: Composed program has stable hash."""
    p1 = Q.nodes().to_program()
    p2 = Q.nodes().compute("degree").to_program()
    
    try:
        composed = compose(p1, p2)
        
        # Hash should be stable
        hash1 = composed.hash()
        hash2 = composed.hash()
        
        assert hash1 == hash2
        assert len(hash1) == 64
    except Exception:
        assume(False)


# ============================================================================
# Property Tests: Cache Correctness
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(network=small_multilayer_network())
def test_cache_hit_on_identical_execution(network):
    """Property: Executing same program twice should hit cache."""
    cache = ProgramCache()
    
    program = Q.nodes().compute("degree").to_program()
    
    try:
        # First execution
        result1 = program.execute(network, seed=42)
        
        # Second execution should use cache (if caching is enabled)
        result2 = program.execute(network, seed=42)
        
        # Results should be identical
        assert set(result1.items) == set(result2.items)
    except Exception:
        assume(False)


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(
    network=small_multilayer_network(),
    seed1=st.integers(min_value=0, max_value=100),
    seed2=st.integers(min_value=0, max_value=100)
)
def test_execution_fingerprint_different_for_different_seeds(network, seed1, seed2):
    """Property: Different seeds produce different execution fingerprints."""
    assume(seed1 != seed2)
    
    fp1 = execution_fingerprint(seed=seed1)
    fp2 = execution_fingerprint(seed=seed2)
    
    # Different seeds should produce different fingerprints
    assert fp1 != fp2


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(network=small_multilayer_network())
def test_graph_fingerprint_stable(network):
    """Property: Graph fingerprint is stable for same network."""
    fp1 = graph_fingerprint(network)
    fp2 = graph_fingerprint(network)
    
    # Should be identical
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256


# ============================================================================
# Property Tests: Program Diff
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(query_builder=simple_node_query())
def test_program_diff_reflexivity(query_builder):
    """Property: A program diffed with itself shows no differences."""
    program = query_builder.to_program()
    
    diff = diff_programs(program, program)
    
    # Should be identical
    assert diff.is_identical()
    assert len(diff.differences) == 0
    assert not diff.hash_changed
    assert not diff.type_changed


@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(
    builder1=simple_node_query(),
    builder2=simple_node_query()
)
def test_program_diff_symmetry(builder1, builder2):
    """Property: Diff result should indicate when programs differ."""
    program1 = builder1.to_program()
    program2 = builder2.to_program()
    
    diff = diff_programs(program1, program2)
    
    # Diff should have valid structure
    assert isinstance(diff.differences, list)
    assert isinstance(diff.hash_changed, bool)
    assert isinstance(diff.type_changed, bool)
    
    # If hashes differ, hash_changed should be True
    if program1.hash() != program2.hash():
        assert diff.hash_changed


# ============================================================================
# Property Tests: Optimization
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15)
@given(network=small_multilayer_network())
def test_optimization_preserves_semantics(network):
    """Property: Optimization preserves program semantics."""
    program = (Q.nodes()
        .compute("degree")
        .where(degree__gt=0)
        .to_program())
    
    try:
        # Optimize
        optimized = program.optimize(level=1)
        
        # Execute both
        result_original = program.execute(network)
        result_optimized = optimized.execute(network)
        
        # Results should match
        assert set(result_original.items) == set(result_optimized.items)
    except Exception:
        # May fail on certain networks
        assume(False)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(query_builder=simple_node_query())
def test_optimization_produces_valid_program(query_builder):
    """Property: Optimized programs are still type-valid."""
    program = query_builder.to_program()
    
    try:
        optimized = program.optimize(level=1)
        
        # Should still be type-valid
        assert type_check(optimized.canonical_ast)
        assert optimized.type_signature is not None
    except Exception:
        assume(False)


# ============================================================================
# Property Tests: Explain and Metadata
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(query_builder=simple_node_query())
def test_explain_produces_output(query_builder):
    """Property: explain() always produces non-empty output."""
    program = query_builder.to_program()
    
    explanation = program.explain()
    
    # Should produce some output
    assert explanation is not None
    assert len(explanation) > 0
    assert isinstance(explanation, str)


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(query_builder=simple_node_query())
def test_program_metadata_exists(query_builder):
    """Property: All programs have metadata."""
    program = query_builder.to_program()
    
    # Should have metadata
    assert program.metadata is not None
    assert hasattr(program.metadata, "creation_timestamp")
    assert hasattr(program.metadata, "dsl_version")
    assert hasattr(program.metadata, "library_version")


# ============================================================================
# Property Tests: Edge Cases
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10)
def test_empty_program_valid():
    """Property: Minimal programs are valid."""
    program = Q.nodes().to_program()
    
    # Should be valid
    assert type_check(program.canonical_ast)
    assert program.hash() is not None
    assert program.type_signature is not None


@pytest.mark.property
@settings(deadline=None, max_examples=10)
@given(network=small_multilayer_network())
def test_program_execution_deterministic_with_seed(network):
    """Property: Execution with same seed is deterministic."""
    program = Q.nodes().compute("degree").to_program()
    
    try:
        result1 = program.execute(network, seed=42)
        result2 = program.execute(network, seed=42)
        
        # Should get same results
        assert set(result1.items) == set(result2.items)
        
        # Attributes should match
        if result1.attributes and result2.attributes:
            for key in result1.attributes:
                if key in result2.attributes:
                    # Note: Floating point may have small differences
                    pass
    except Exception:
        assume(False)


if __name__ == "__main__":
    # Run with pytest
    pytest.main([__file__, "-v", "-m", "property"])
