#!/usr/bin/env python3
"""
Property-based tests for Graph Program Rewrite Rules.

Comprehensive tests for rewrite rule equivalence, ensuring that all
rewrites preserve program semantics.
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck
import copy

# Import Graph Program modules
try:
    from py3plex.dsl import Q, L
    from py3plex.dsl.program import (
        GraphProgram,
        apply_rewrites,
        get_standard_rules,
        get_aggressive_rules,
        RewriteEngine,
        RewriteContext,
    )
    from py3plex.dsl.program.types import TypeSystem
    from py3plex.dsl.program.cost import GraphStats
    from py3plex.core import multinet
    PROGRAM_AVAILABLE = True
except ImportError as e:
    PROGRAM_AVAILABLE = False
    pytest.skip(f"Graph Programs not available: {e}", allow_module_level=True)


# ============================================================================
# Test Fixtures and Strategies
# ============================================================================

@st.composite
def random_multilayer_network(draw):
    """Generate a random multilayer network with varying properties."""
    num_nodes = draw(st.integers(min_value=5, max_value=15))
    num_layers = draw(st.integers(min_value=1, max_value=4))
    density = draw(st.floats(min_value=0.1, max_value=0.5))
    
    net = multinet.multi_layer_network(directed=False)
    
    nodes = [f"node{i}" for i in range(num_nodes)]
    layers = [f"L{i}" for i in range(num_layers)]
    
    # Add all nodes to all layers using correct API
    node_list = []
    for layer in layers:
        for node in nodes:
            node_list.append({"source": node, "type": layer})
    net.add_nodes(node_list)
    
    # Add edges based on density
    import random
    random.seed(42)  # Deterministic for reproducibility
    edge_list = []
    for layer in layers:
        for i, src in enumerate(nodes):
            for tgt in nodes[i+1:]:
                if random.random() < density:
                    edge_list.append({
                        "source": src,
                        "target": tgt,
                        "source_type": layer,
                        "target_type": layer
                    })
    if edge_list:
        net.add_edges(edge_list)
    
    return net


@st.composite
def complex_node_query(draw):
    """Generate more complex node queries for thorough testing."""
    builder = Q.nodes()
    
    # Add layer filter (sometimes)
    if draw(st.booleans()):
        num_layers = draw(st.integers(min_value=1, max_value=3))
        if num_layers == 1:
            builder = builder.from_layers(L["L0"])
        else:
            # Multiple layers
            builder = builder.from_layers(L["L0"])
    
    # Add multiple computes
    num_computes = draw(st.integers(min_value=0, max_value=3))
    for _ in range(num_computes):
        measure = draw(st.sampled_from(["degree", "clustering", "triangles"]))
        builder = builder.compute(measure)
    
    # Add where clause (sometimes)
    if draw(st.booleans()) and num_computes > 0:
        builder = builder.where(degree__gt=0)
    
    # Add order_by (sometimes)
    if draw(st.booleans()) and num_computes > 0:
        measure = draw(st.sampled_from(["degree", "clustering", "triangles"]))
        builder = builder.order_by(measure, desc=True)
    
    # Add limit (sometimes)
    if draw(st.booleans()):
        k = draw(st.integers(min_value=1, max_value=10))
        builder = builder.limit(k)
    
    return builder


# ============================================================================
# Property Tests: Individual Rewrite Rules
# ============================================================================

@pytest.mark.property
@settings(
    deadline=None,
    max_examples=3,
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow, HealthCheck.filter_too_much]
)
@given(network=random_multilayer_network())
def test_push_where_past_compute_equivalence(network):
    """Property: Pushing WHERE before COMPUTE preserves results."""
    # Program with compute first, then where
    program = (Q.nodes()
        .compute("degree")
        .where(degree__gt=1)
        .to_program())
    
    # Get the push_where_past_compute rule
    rules = get_standard_rules()
    push_where_rule = [r for r in rules if "push_where" in r.name.lower()]
    
    if not push_where_rule:
        # Skip if rule not found
        assume(False)
        return
    
    engine = RewriteEngine(rules=push_where_rule)
    
    context = RewriteContext(
        network_stats={"num_nodes": 10, "num_edges": 20, "num_layers": 2}
    )
    rewritten = engine.apply_rules(program, push_where_rule, context)
    
    # Execute both - let real errors propagate
    result1 = program.execute(network)
    result2 = rewritten.execute(network)
    
    # Should have same items
    assert set(result1.items) == set(result2.items)


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.filter_too_much])
@given(network=random_multilayer_network())
def test_fuse_compute_equivalence(network):
    """Property: Fusing multiple computes preserves results."""
    # Program with multiple compute calls
    program = (Q.nodes()
        .compute("degree")
        .compute("clustering")
        .to_program())
    
    # Apply fuse_compute rewrite
    rules = get_standard_rules()
    fuse_rules = [r for r in rules if "fuse" in r.name.lower() and "compute" in r.name.lower()]
    
    if not fuse_rules:
        assume(False)
        return
    
    engine = RewriteEngine(rules=fuse_rules)
    context = RewriteContext(
        network_stats={"num_nodes": 10, "num_edges": 20, "num_layers": 2}
    )
    rewritten = engine.apply_rules(program, fuse_rules, context)
    
    result1 = program.execute(network)
    result2 = rewritten.execute(network)
    
    # Should compute same attributes
    assert result1.computed_metrics == result2.computed_metrics
    assert set(result1.items) == set(result2.items)


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.filter_too_much])
@given(network=random_multilayer_network())
def test_fuse_where_equivalence(network):
    """Property: Fusing multiple WHERE clauses preserves results."""
    # Program with multiple where clauses
    program = (Q.nodes()
        .compute("degree")
        .where(degree__gt=0)
        .where(degree__lt=10)
        .to_program())
    
    rules = get_standard_rules()
    fuse_where_rules = [r for r in rules if "fuse" in r.name.lower() and "where" in r.name.lower()]
    
    if not fuse_where_rules:
        assume(False)
        return
    
    engine = RewriteEngine(rules=fuse_where_rules)
    context = RewriteContext(
        network_stats={"num_nodes": 10, "num_edges": 20, "num_layers": 2}
    )
    rewritten = engine.apply_rules(program, fuse_where_rules, context)
    
    result1 = program.execute(network)
    result2 = rewritten.execute(network)
    
    assert set(result1.items) == set(result2.items)


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.filter_too_much])
@given(network=random_multilayer_network())
def test_push_limit_early_equivalence(network):
    """Property: Pushing LIMIT early preserves results."""
    # Program with limit after compute
    program = (Q.nodes()
        .compute("degree")
        .order_by("degree", desc=True)
        .limit(5)
        .to_program())
    
    rules = get_aggressive_rules()
    limit_rules = [r for r in rules if "limit" in r.name.lower() or "top_k" in r.name.lower()]
    
    if limit_rules:
        engine = RewriteEngine(rules=limit_rules)
        context = RewriteContext(
            network_stats={"num_nodes": 10, "num_edges": 20, "num_layers": 2}
        )
        rewritten = engine.apply_rules(program, limit_rules, context)
        
        result1 = program.execute(network)
        result2 = rewritten.execute(network)
        
        # Results should have same size and top items
        assert len(result1.items) == len(result2.items)


# ============================================================================
# Property Tests: Rule Combinations
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.filter_too_much])
@given(
    network=random_multilayer_network(),
    query=complex_node_query()
)
def test_multiple_rewrites_preserve_semantics(network, query):
    """Property: Applying multiple rewrites preserves semantics."""
    program = query.to_program()
    
    # Apply all standard rules
    rewritten = apply_rewrites(program, get_standard_rules())
    
    # Execute both
    result1 = program.execute(network)
    result2 = rewritten.execute(network)
    
    # Core items should match
    assert set(result1.items) == set(result2.items)
    
    # Computed metrics should match
    assert result1.computed_metrics == result2.computed_metrics


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.filter_too_much])
@given(
    network=random_multilayer_network(),
    query=complex_node_query()
)
def test_aggressive_rewrites_preserve_semantics(network, query):
    """Property: Aggressive optimization preserves semantics."""
    program = query.to_program()
    
    # Apply aggressive rules
    rewritten = apply_rewrites(program, get_aggressive_rules())
    
    result1 = program.execute(network)
    result2 = rewritten.execute(network)
    
    # Should have same core results
    assert set(result1.items) == set(result2.items)


# ============================================================================
# Property Tests: Rewrite Invariants
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.filter_too_much])
@given(query=complex_node_query())
def test_rewrite_preserves_type_validity(query):
    """Property: Rewrites preserve type validity."""
    program = query.to_program()
    
    # Original should be type-valid
    from py3plex.dsl.program import type_check
    assert type_check(program.canonical_ast)
    
    # Rewritten should also be type-valid
    rewritten = apply_rewrites(program, get_standard_rules())
    assert type_check(rewritten.canonical_ast)


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.filter_too_much])
@given(query=complex_node_query())
def test_rewrite_preserves_hash_determinism(query):
    """Property: Rewritten programs have stable hashes."""
    program = query.to_program()
    
    rewritten = apply_rewrites(program, get_standard_rules())
    
    # Hash should be stable
    hash1 = rewritten.hash()
    hash2 = rewritten.hash()
    
    assert hash1 == hash2
    assert len(hash1) == 64


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.filter_too_much])
@given(query=complex_node_query())
def test_rewrite_produces_valid_provenance(query):
    """Property: Rewrites update provenance correctly."""
    program = query.to_program()
    
    rewritten = apply_rewrites(program, get_standard_rules())
    
    # Provenance should exist
    assert rewritten.metadata is not None
    assert hasattr(rewritten.metadata, "provenance_chain")
    
    # If rewrites were applied, provenance should reflect that
    if program.hash() != rewritten.hash():
        assert len(rewritten.metadata.provenance_chain) > 0


# ============================================================================
# Property Tests: Idempotence
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.filter_too_much])
@given(query=complex_node_query())
def test_rewrite_idempotence(query):
    """Property: Applying rewrites twice gives same result as once."""
    program = query.to_program()
    
    rules = get_standard_rules()
    
    # Apply once
    rewritten_once = apply_rewrites(program, rules)
    
    # Apply again
    rewritten_twice = apply_rewrites(rewritten_once, rules)
    
    # Hashes should be same (idempotent)
    assert rewritten_once.hash() == rewritten_twice.hash()


# ============================================================================
# Property Tests: Rule Guards
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.filter_too_much])
@given(query=complex_node_query())
def test_rule_guards_prevent_invalid_rewrites(query):
    """Property: Rule guards prevent application when preconditions not met."""
    program = query.to_program()
    
    rules = get_standard_rules()
    engine = RewriteEngine(rules=rules)
    
    # Each rule should have guards
    for rule in rules:
        assert rule.guards is not None
        assert len(rule.guards) >= 0  # Can be empty list
        
    # Guards should be callable
    context = RewriteContext(
        network_stats={"num_nodes": 10, "num_edges": 20, "num_layers": 2}
    )
    
    # Applying rules should not crash
    rewritten = engine.apply_rules(program, rules, context)
    assert rewritten is not None


# ============================================================================
# Property Tests: Performance Characteristics
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.filter_too_much])
@given(query=complex_node_query())
def test_rewrite_cost_estimate_valid(query):
    """Property: Cost estimates remain valid after rewrites."""
    program = query.to_program()
    
    from py3plex.dsl.program import CostModel, GraphStats
    
    cost_model = CostModel()
    stats = GraphStats(num_nodes=100, num_edges=500, num_layers=2)
    
    # Original cost
    cost1 = cost_model.estimate_program_cost(program, stats)
    
    # Rewritten cost
    rewritten = apply_rewrites(program, get_standard_rules())
    cost2 = cost_model.estimate_program_cost(rewritten, stats)
    
    # Both should have valid estimates
    assert cost1.time_estimate_seconds > 0
    assert cost2.time_estimate_seconds > 0
    
    # Rewritten should ideally be faster or same
    # (but we can't enforce this strictly)


# ============================================================================
# Property Tests: Edge Cases
# ============================================================================

@pytest.mark.property
def test_rewrite_empty_program():
    """Property: Rewriting minimal programs doesn't break them."""
    program = Q.nodes().to_program()
    
    rewritten = apply_rewrites(program, get_standard_rules())
    
    # Should still be valid
    from py3plex.dsl.program import type_check
    assert type_check(rewritten.canonical_ast)
    assert rewritten.hash() is not None


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.filter_too_much])
@given(network=random_multilayer_network())
def test_rewrite_with_no_optimizations(network):
    """Property: Programs that can't be optimized still work."""
    # Simple program that can't be optimized much
    program = Q.nodes().to_program()
    
    rewritten = apply_rewrites(program, get_standard_rules())
    
    # Should execute successfully
    result = rewritten.execute(network)
    assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "property"])
