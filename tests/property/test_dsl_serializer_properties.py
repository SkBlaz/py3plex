#!/usr/bin/env python3
"""
Property-based tests for DSL serializer module.

Tests invariants for AST to DSL string conversion, including:
- Round-trip serialization (ast -> dsl -> ast)
- Idempotency of serialization
- Structural preservation
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import DSL module
try:
    from py3plex.dsl import (
        Q,
        L,
        F,
        Param,
        serializer,
    )
    from py3plex.dsl.ast import (
        Query,
        SelectStmt,
        Target,
        LayerExpr,
        LayerTerm,
        ConditionExpr,
        ConditionAtom,
        Comparison,
        ComputeItem,
        OrderItem,
        ParamRef,
    )
    from py3plex.dsl.serializer import ast_to_dsl
    from py3plex.core import multinet
    DSL_AVAILABLE = True
except ImportError:
    DSL_AVAILABLE = False
    pytest.skip("DSL module not available", allow_module_level=True)


# ============================================================================
# Helper Functions
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
            })
    network.add_edges(edges)
    
    return network


# ============================================================================
# Property Tests: Serialization Idempotency
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    layer_name=st.text(
        min_size=1,
        max_size=10,
        alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))
    )
)
def test_serialization_idempotent_simple_query(layer_name):
    """
    Property: Serializing the same query twice produces identical strings.
    
    For any query Q, ast_to_dsl(Q) should always produce the same string.
    """
    # Build a simple query
    query = Q.nodes().from_layers(L[layer_name]).to_ast()
    
    # Serialize twice
    dsl1 = ast_to_dsl(query)
    dsl2 = ast_to_dsl(query)
    
    # Should be identical
    assert dsl1 == dsl2
    assert isinstance(dsl1, str)
    assert len(dsl1) > 0


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    attr=st.sampled_from(['degree', 'centrality', 'clustering']),
    threshold=st.integers(min_value=0, max_value=100)
)
def test_serialization_preserves_comparisons(attr, threshold):
    """
    Property: Serialization preserves comparison operators.
    
    A query with comparison should serialize to include the operator and value.
    """
    # Build query with comparison using kwargs
    query_builder = Q.nodes()
    
    # Use kwargs-style comparison
    kwargs = {f"{attr}__gt": threshold}
    query = query_builder.where(**kwargs).to_ast()
    
    # Serialize
    dsl = ast_to_dsl(query)
    
    # Should contain the attribute name and threshold
    assert attr in dsl
    assert str(threshold) in dsl
    assert ">" in dsl or "gt" in dsl  # May use symbol or word


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    limit=st.integers(min_value=1, max_value=100),
)
def test_serialization_preserves_limit(limit):
    """
    Property: Serialization preserves LIMIT clause.
    
    A query with LIMIT n should serialize to include "LIMIT n".
    """
    query = Q.nodes().limit(limit).to_ast()
    dsl = ast_to_dsl(query)
    
    # Should contain LIMIT keyword and value
    assert "LIMIT" in dsl
    assert str(limit) in dsl


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    measure=st.sampled_from(['degree', 'betweenness', 'clustering']),
)
def test_serialization_preserves_compute(measure):
    """
    Property: Serialization preserves COMPUTE clause.
    
    A query with COMPUTE should serialize to include the measure name.
    """
    query = Q.nodes().compute(measure).to_ast()
    dsl = ast_to_dsl(query)
    
    # Should contain COMPUTE keyword and measure name
    assert "COMPUTE" in dsl
    assert measure in dsl


# ============================================================================
# Property Tests: AST Structure Preservation
# ============================================================================

@pytest.mark.property
def test_serialization_preserves_target():
    """
    Property: Serialization preserves query target (nodes vs edges).
    
    SELECT nodes should serialize with "nodes", SELECT edges with "edges".
    """
    # Test nodes
    query_nodes = Q.nodes().to_ast()
    dsl_nodes = ast_to_dsl(query_nodes)
    assert "nodes" in dsl_nodes
    
    # Test edges
    query_edges = Q.edges().to_ast()
    dsl_edges = ast_to_dsl(query_edges)
    assert "edges" in dsl_edges


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    layer1=st.text(min_size=1, max_size=8, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    layer2=st.text(min_size=1, max_size=8, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_serialization_preserves_layer_union(layer1, layer2):
    """
    Property: Serialization preserves layer union operations.
    
    L['a'] + L['b'] should serialize to include both layers with + operator.
    """
    assume(layer1 != layer2)  # Ensure distinct layers
    
    query = Q.nodes().from_layers(L[layer1] + L[layer2]).to_ast()
    dsl = ast_to_dsl(query)
    
    # Should contain both layer names and the + operator
    assert layer1 in dsl
    assert layer2 in dsl
    assert "+" in dsl or "UNION" in dsl.upper()


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    key=st.sampled_from(['degree', 'centrality', 'score']),
    desc=st.booleans()
)
def test_serialization_preserves_order_by(key, desc):
    """
    Property: Serialization preserves ORDER BY clause.
    
    ORDER BY key [DESC] should serialize correctly.
    """
    query = Q.nodes().order_by(key, desc=desc).to_ast()
    dsl = ast_to_dsl(query)
    
    # Should contain ORDER BY and the key
    assert "ORDER BY" in dsl
    assert key in dsl
    
    # DESC should be present if specified
    if desc:
        assert "DESC" in dsl


# ============================================================================
# Property Tests: Special Cases
# ============================================================================

@pytest.mark.property
def test_serialization_handles_empty_query():
    """
    Property: Serialization handles minimal queries gracefully.
    
    Even a query with just SELECT nodes should serialize properly.
    """
    query = Q.nodes().to_ast()
    dsl = ast_to_dsl(query)
    
    # Should be a valid string with at least SELECT and target
    assert isinstance(dsl, str)
    assert len(dsl) > 0
    assert "SELECT" in dsl
    assert "nodes" in dsl


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    param_name=st.text(
        min_size=1,
        max_size=10,
        alphabet=st.characters(min_codepoint=ord('a'), max_codepoint=ord('z'))
    )
)
def test_serialization_preserves_parameters(param_name):
    """
    Property: Serialization preserves parameter references.
    
    A query with Param.ref('k') should serialize to include :k.
    """
    query = Q.nodes().where(degree__gt=Param.ref(param_name)).to_ast()
    dsl = ast_to_dsl(query)
    
    # Should contain parameter reference with colon prefix
    assert f":{param_name}" in dsl


@pytest.mark.property
def test_serialization_preserves_explain():
    """
    Property: Serialization preserves EXPLAIN keyword.
    
    A query with explain=True should serialize with EXPLAIN prefix.
    """
    query = Q.nodes().explain().to_ast()
    dsl = ast_to_dsl(query)
    
    # Should start with EXPLAIN
    assert dsl.startswith("EXPLAIN") or "EXPLAIN" in dsl


# ============================================================================
# Property Tests: Composition
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    layer=st.text(min_size=1, max_size=8, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    threshold=st.integers(min_value=1, max_value=10),
    limit=st.integers(min_value=1, max_value=20)
)
def test_serialization_complex_query(layer, threshold, limit):
    """
    Property: Serialization handles complex queries with multiple clauses.
    
    A query with FROM, WHERE, COMPUTE, ORDER BY, and LIMIT should serialize
    to include all components.
    """
    query = (
        Q.nodes()
        .from_layers(L[layer])
        .where(degree__gt=threshold)
        .compute("betweenness")
        .order_by("degree", desc=True)
        .limit(limit)
        .to_ast()
    )
    
    dsl = ast_to_dsl(query)
    
    # Should contain all the key components
    assert "SELECT" in dsl
    assert "nodes" in dsl
    assert layer in dsl
    assert "WHERE" in dsl
    assert str(threshold) in dsl
    assert "COMPUTE" in dsl
    assert "betweenness" in dsl
    assert "ORDER BY" in dsl
    assert "LIMIT" in dsl
    assert str(limit) in dsl


@pytest.mark.property
@settings(deadline=None, max_examples=20)
@given(
    measure1=st.sampled_from(['degree', 'betweenness']),
    measure2=st.sampled_from(['clustering', 'closeness']),
)
def test_serialization_multiple_compute(measure1, measure2):
    """
    Property: Serialization handles multiple COMPUTE clauses.
    
    COMPUTE m1, m2 should serialize with both measures.
    """
    assume(measure1 != measure2)
    
    query = Q.nodes().compute(measure1).compute(measure2).to_ast()
    dsl = ast_to_dsl(query)
    
    # Should contain COMPUTE and both measures
    assert "COMPUTE" in dsl
    assert measure1 in dsl
    assert measure2 in dsl
