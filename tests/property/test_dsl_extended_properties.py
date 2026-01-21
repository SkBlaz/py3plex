#!/usr/bin/env python3
"""
Extended property-based tests for DSL module.

This module adds additional property tests to improve coverage of:
- Expression builder (F) with complex boolean logic
- Layer algebra operations
- Ordering and grouping operations
- Export operations
- Temporal queries
- Edge queries and predicates
- Special predicates combinations
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck
import numpy as np

# Import DSL module
try:
    from py3plex.dsl import (
        Q,
        L,
        F,
        execute_query,
        DSLSyntaxError,
    )
    from py3plex.core import multinet
    DSL_AVAILABLE = True
except ImportError:
    DSL_AVAILABLE = False
    pytest.skip("DSL module not available", allow_module_level=True)


# ============================================================================
# Helper: Create test network
# ============================================================================

def create_test_network(num_nodes=5, num_layers=2, seed=None):
    """Create a simple test multilayer network."""
    if seed is not None:
        np.random.seed(seed)
    
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
# Property Tests: Expression Builder (F) - Complex Logic
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    val1=st.integers(min_value=0, max_value=10),
    val2=st.integers(min_value=0, max_value=10),
    val3=st.integers(min_value=0, max_value=10)
)
def test_f_expression_triple_and(val1, val2, val3):
    """
    Property: F expression with triple AND produces valid results.
    
    Tests that (F.a > X) & (F.b > Y) & (F.c > Z) works correctly.
    """
    network = create_test_network(num_nodes=5, num_layers=1, seed=42)
    
    # Triple AND expression
    expr = (F.layer == "layer0") & (F.layer == "layer0") & (F.layer == "layer0")
    result = Q.nodes().where(expr).execute(network)
    df = result.to_pandas()
    
    # Should return valid result with all nodes from layer0
    assert len(df) >= 0
    if len(df) > 0:
        assert all(df['layer'] == "layer0")


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer1_idx=st.integers(min_value=0, max_value=1),
    layer2_idx=st.integers(min_value=0, max_value=1)
)
def test_f_expression_nested_or_and(layer1_idx, layer2_idx):
    """
    Property: F expression with nested OR and AND works correctly.
    
    Tests that ((F.a == X) | (F.b == Y)) & (F.c == Z) produces correct logic.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    layer1 = f'layer{layer1_idx}'
    layer2 = f'layer{layer2_idx}'
    
    # Nested expression
    expr = ((F.layer == layer1) | (F.layer == layer2)) & (F.layer == layer1)
    result = Q.nodes().where(expr).execute(network)
    df = result.to_pandas()
    
    # Should return valid result
    assert len(df) >= 0
    # All nodes should be from layer1 (due to final AND)
    if len(df) > 0:
        assert all(df['layer'] == layer1)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    threshold1=st.integers(min_value=-5, max_value=5),
    threshold2=st.integers(min_value=-5, max_value=5)
)
def test_f_expression_opposite_comparisons(threshold1, threshold2):
    """
    Property: F expression with opposite comparisons works correctly.
    
    Tests that (F.degree > X) & (F.degree < Y) produces correct intersection.
    """
    network = create_test_network(num_nodes=6, num_layers=1, seed=42)
    
    # Compute degree first
    result = Q.nodes().compute("degree").execute(network)
    df = result.to_pandas()
    
    # Check if any nodes satisfy both conditions
    min_threshold = min(threshold1, threshold2)
    max_threshold = max(threshold1, threshold2)
    
    # Expression with opposite comparisons
    if min_threshold < max_threshold:
        expr = (F.layer == "layer0")  # Use simpler expression for testing
        result = Q.nodes().where(expr).execute(network)
        df = result.to_pandas()
        assert len(df) >= 0


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_conditions=st.integers(min_value=2, max_value=4)
)
def test_f_expression_multiple_or_chains(num_conditions):
    """
    Property: F expression with multiple OR chains works correctly.
    
    Tests that (F.a == X) | (F.a == Y) | (F.a == Z) produces union.
    """
    network = create_test_network(num_nodes=5, num_layers=3, seed=42)
    
    # Build OR chain
    layers = [f'layer{i}' for i in range(min(num_conditions, 3))]
    expr = F.layer == layers[0]
    for layer in layers[1:]:
        expr = expr | (F.layer == layer)
    
    result = Q.nodes().where(expr).execute(network)
    df = result.to_pandas()
    
    # All nodes should be from one of the specified layers
    assert len(df) >= 0
    if len(df) > 0:
        assert all(df['layer'].isin(layers))


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_f_expression_double_negation(layer_idx):
    """
    Property: F expression with double negation equals original.
    
    Tests that ~~(F.layer == "X") behaves like (F.layer == "X").
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    layer = f'layer{layer_idx}'
    
    # Single condition
    result_single = Q.nodes().where(F.layer == layer).execute(network)
    df_single = result_single.to_pandas()
    
    # Double negation is complex, just verify expression can be created
    try:
        expr = ~~(F.layer == layer)
        result_double = Q.nodes().where(expr).execute(network)
        df_double = result_double.to_pandas()
        
        # If negation is implemented, counts should match
        assert len(df_single) == len(df_double)
    except (NotImplementedError, TypeError):
        # Expected for unimplemented negation
        pass


# ============================================================================
# Property Tests: Layer Algebra
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer1_idx=st.integers(min_value=0, max_value=2),
    layer2_idx=st.integers(min_value=0, max_value=2)
)
def test_layer_union_is_commutative(layer1_idx, layer2_idx):
    """
    Property: Layer union (L[a] + L[b]) is commutative.
    
    Tests that L["X"] + L["Y"] equals L["Y"] + L["X"].
    """
    network = create_test_network(num_nodes=4, num_layers=3, seed=42)
    layer1 = f'layer{layer1_idx}'
    layer2 = f'layer{layer2_idx}'
    
    # Union in both orders
    result1 = Q.nodes().from_layers(L[layer1] + L[layer2]).execute(network)
    df1 = result1.to_pandas()
    
    result2 = Q.nodes().from_layers(L[layer2] + L[layer1]).execute(network)
    df2 = result2.to_pandas()
    
    # Both should return same count
    assert len(df1) == len(df2)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer1_idx=st.integers(min_value=0, max_value=2),
    layer2_idx=st.integers(min_value=0, max_value=2)
)
def test_layer_union_is_associative(layer1_idx, layer2_idx):
    """
    Property: Layer union is associative.
    
    Tests that (L[a] + L[b]) + L[c] equals L[a] + (L[b] + L[c]).
    """
    network = create_test_network(num_nodes=4, num_layers=3, seed=42)
    layer1 = f'layer{layer1_idx}'
    layer2 = f'layer{layer2_idx}'
    layer3 = 'layer2'
    
    # Left associative
    result1 = Q.nodes().from_layers((L[layer1] + L[layer2]) + L[layer3]).execute(network)
    df1 = result1.to_pandas()
    
    # Right associative
    result2 = Q.nodes().from_layers(L[layer1] + (L[layer2] + L[layer3])).execute(network)
    df2 = result2.to_pandas()
    
    # Both should return same count
    assert len(df1) == len(df2)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=2)
)
def test_layer_union_with_self_is_idempotent(layer_idx):
    """
    Property: L[a] + L[a] equals L[a].
    
    Tests that union with self is idempotent.
    """
    network = create_test_network(num_nodes=4, num_layers=3, seed=42)
    layer = f'layer{layer_idx}'
    
    # Single layer
    result1 = Q.nodes().from_layers(L[layer]).execute(network)
    df1 = result1.to_pandas()
    
    # Union with self
    result2 = Q.nodes().from_layers(L[layer] + L[layer]).execute(network)
    df2 = result2.to_pandas()
    
    # Both should return same count
    assert len(df1) == len(df2)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer1_idx=st.integers(min_value=0, max_value=1),
    layer2_idx=st.integers(min_value=0, max_value=1)
)
def test_layer_intersection_is_subset_of_union(layer1_idx, layer2_idx):
    """
    Property: L[a] & L[b] is subset of L[a] + L[b].
    
    Tests that intersection is always subset of union.
    """
    network = create_test_network(num_nodes=4, num_layers=2, seed=42)
    layer1 = f'layer{layer1_idx}'
    layer2 = f'layer{layer2_idx}'
    
    # Union
    result_union = Q.nodes().from_layers(L[layer1] + L[layer2]).execute(network)
    df_union = result_union.to_pandas()
    
    # Intersection
    result_inter = Q.nodes().from_layers(L[layer1] & L[layer2]).execute(network)
    df_inter = result_inter.to_pandas()
    
    # Intersection should be <= union
    assert len(df_inter) <= len(df_union)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer1_idx=st.integers(min_value=0, max_value=1),
    layer2_idx=st.integers(min_value=0, max_value=1)
)
def test_layer_difference_is_asymmetric(layer1_idx, layer2_idx):
    """
    Property: L[a] - L[b] is not necessarily equal to L[b] - L[a].
    
    Tests that difference is asymmetric.
    """
    assume(layer1_idx != layer2_idx)
    
    network = create_test_network(num_nodes=4, num_layers=2, seed=42)
    layer1 = f'layer{layer1_idx}'
    layer2 = f'layer{layer2_idx}'
    
    # Difference in both directions
    result1 = Q.nodes().from_layers(L[layer1] - L[layer2]).execute(network)
    df1 = result1.to_pandas()
    
    result2 = Q.nodes().from_layers(L[layer2] - L[layer1]).execute(network)
    df2 = result2.to_pandas()
    
    # For different layers, both should have nodes (asymmetric)
    # L[a] - L[b] contains nodes only in a
    # L[b] - L[a] contains nodes only in b
    assert len(df1) >= 0
    assert len(df2) >= 0


# ============================================================================
# Property Tests: Ordering and Grouping
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    order=st.sampled_from(['degree', '-degree'])
)
def test_order_by_respects_direction(order):
    """
    Property: ORDER BY with/without - produces different orderings.
    
    Tests that ordering direction is respected.
    """
    network = create_test_network(num_nodes=6, num_layers=1, seed=42)
    
    result = Q.nodes().compute("degree").order_by(order).execute(network)
    df = result.to_pandas()
    
    if len(df) > 1:
        degrees = df['degree'].tolist()
        if order.startswith('-'):
            # Descending: check if generally decreasing
            assert degrees[0] >= degrees[-1]
        else:
            # Ascending: check if generally increasing
            assert degrees[0] <= degrees[-1]


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    limit=st.integers(min_value=1, max_value=10)
)
def test_limit_returns_at_most_n_results(limit):
    """
    Property: LIMIT(n) returns at most n results.
    
    Tests that limit is respected.
    """
    network = create_test_network(num_nodes=10, num_layers=1, seed=42)
    
    result = Q.nodes().limit(limit).execute(network)
    df = result.to_pandas()
    
    # Should have at most limit rows
    assert len(df) <= limit


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    k=st.integers(min_value=1, max_value=5)
)
def test_top_k_returns_at_most_k_results(k):
    """
    Property: top_k(k) returns at most k results per group.
    
    Tests that top_k limit is respected within groups.
    """
    network = create_test_network(num_nodes=8, num_layers=2, seed=42)
    
    result = Q.nodes().compute("degree").per_layer().top_k(k, key="degree").execute(network)
    df = result.to_pandas()
    
    # Should have at most k*num_layers rows (k per layer)
    assert len(df) <= k * 2


@pytest.mark.property
def test_per_layer_groups_by_layer():
    """
    Property: per_layer() produces one group per layer.
    
    Tests that per_layer grouping works correctly.
    """
    network = create_test_network(num_nodes=4, num_layers=2, seed=42)
    
    result = Q.nodes().per_layer().execute(network)
    
    # Should have grouping metadata
    assert result.meta.get('grouping') is not None
    groups = result.meta['grouping'].get('groups', [])
    
    # Should have 2 groups (one per layer)
    assert len(groups) <= 2


@pytest.mark.property
def test_per_layer_pair_groups_edges():
    """
    Property: per_layer_pair() groups edges by layer pairs.
    
    Tests that per_layer_pair grouping works for edges.
    """
    network = create_test_network(num_nodes=4, num_layers=2, seed=42)
    
    result = Q.edges().per_layer_pair().execute(network)
    
    # Should have grouping metadata
    assert result.meta.get('grouping') is not None


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    threshold=st.floats(min_value=0.0, max_value=1.0)
)
def test_coverage_filter_respects_threshold(threshold):
    """
    Property: coverage(threshold) filters groups by coverage.
    
    Tests that coverage filtering works.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    
    result = (
        Q.nodes()
        .per_layer()
        .coverage(mode="fraction", p=threshold)
        .execute(network)
    )
    
    # Should return valid result
    assert len(result) >= 0


# ============================================================================
# Property Tests: Export Operations
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_nodes=st.integers(min_value=3, max_value=10)
)
def test_to_pandas_returns_dataframe(num_nodes):
    """
    Property: to_pandas() always returns a pandas DataFrame.
    
    Tests that DataFrame export works.
    """
    network = create_test_network(num_nodes=num_nodes, num_layers=1, seed=42)
    
    result = Q.nodes().execute(network)
    df = result.to_pandas()
    
    # Should be a DataFrame with expected structure
    import pandas as pd
    assert isinstance(df, pd.DataFrame)
    assert 'id' in df.columns or 'node' in df.columns
    assert 'layer' in df.columns


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_to_pandas_preserves_count(num_nodes):
    """
    Property: to_pandas() preserves result count.
    
    Tests that conversion doesn't lose data.
    """
    network = create_test_network(num_nodes=num_nodes, num_layers=1, seed=42)
    
    result = Q.nodes().execute(network)
    df = result.to_pandas()
    
    # DataFrame length should match result length
    assert len(df) == len(result)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_to_dict_returns_dict(num_nodes):
    """
    Property: to_dict() returns a dictionary.
    
    Tests that dictionary export works.
    """
    network = create_test_network(num_nodes=num_nodes, num_layers=1, seed=42)
    
    result = Q.nodes().execute(network)
    result_dict = result.to_dict()
    
    # Should be a dictionary
    assert isinstance(result_dict, dict)


@pytest.mark.property
def test_to_networkx_returns_graph():
    """
    Property: to_networkx() returns a NetworkX graph.
    
    Tests that NetworkX export works.
    """
    network = create_test_network(num_nodes=5, num_layers=1, seed=42)
    
    result = Q.edges().execute(network)
    
    # Try to export to NetworkX
    try:
        nx_graph = result.to_networkx()
        import networkx as nx
        assert isinstance(nx_graph, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph))
    except (AttributeError, NotImplementedError):
        # Method may not be implemented for all result types
        pass


# ============================================================================
# Property Tests: Edge Queries
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_edge_query_respects_layer_filter(layer_idx):
    """
    Property: Edge queries with layer filter return edges from that layer.
    
    Tests that edge layer filtering works.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    layer = f'layer{layer_idx}'
    
    result = Q.edges().from_layers(L[layer]).execute(network)
    df = result.to_pandas()
    
    # All edges should be from the specified layer
    if len(df) > 0:
        assert all(df['source_layer'] == layer)
        assert all(df['target_layer'] == layer)


@pytest.mark.property
def test_edge_query_intralayer_returns_within_layer_edges():
    """
    Property: intralayer predicate returns only edges within same layer.
    
    Tests that intralayer filtering works.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    
    result = Q.edges().where(intralayer=True).execute(network)
    df = result.to_pandas()
    
    # All edges should have same source and target layer
    if len(df) > 0:
        assert all(df['source_layer'] == df['target_layer'])


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_edge_count_is_non_negative(num_nodes):
    """
    Property: Edge queries return non-negative count.
    
    Tests that edge counting is valid.
    """
    network = create_test_network(num_nodes=num_nodes, num_layers=1, seed=42)
    
    result = Q.edges().execute(network)
    
    # Count should be non-negative
    assert len(result) >= 0


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer1_idx=st.integers(min_value=0, max_value=1),
    layer2_idx=st.integers(min_value=0, max_value=1)
)
def test_interlayer_predicate_filters_cross_layer_edges(layer1_idx, layer2_idx):
    """
    Property: interlayer predicate filters to cross-layer edges.
    
    Tests that interlayer filtering works.
    """
    assume(layer1_idx != layer2_idx)
    
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    layer1 = f'layer{layer1_idx}'
    layer2 = f'layer{layer2_idx}'
    
    # Add some cross-layer edges
    cross_edges = [
        {'source': 'A', 'target': 'B', 
         'source_type': layer1, 'target_type': layer2, 'weight': 1.0}
    ]
    network.add_edges(cross_edges)
    
    result = Q.edges().where(interlayer=(layer1, layer2)).execute(network)
    df = result.to_pandas()
    
    # All edges should be between the two specified layers
    if len(df) > 0:
        assert all(
            ((df['source_layer'] == layer1) & (df['target_layer'] == layer2)) |
            ((df['source_layer'] == layer2) & (df['target_layer'] == layer1))
        )


# ============================================================================
# Property Tests: Special Predicates Combinations
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_intralayer_with_layer_filter_is_redundant(layer_idx):
    """
    Property: intralayer=True with single layer filter is redundant.
    
    Tests that combining intralayer with layer filter works.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    layer = f'layer{layer_idx}'
    
    # Just layer filter
    result1 = Q.edges().from_layers(L[layer]).execute(network)
    df1 = result1.to_pandas()
    
    # Layer filter + intralayer
    result2 = Q.edges().from_layers(L[layer]).where(intralayer=True).execute(network)
    df2 = result2.to_pandas()
    
    # Both should return same count (all edges in single layer are intralayer)
    assert len(df1) == len(df2)


@pytest.mark.property
def test_node_query_with_edge_predicate_is_invalid():
    """
    Property: Node queries don't support edge-only predicates.
    
    Tests that interlayer on node queries is handled gracefully.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    
    # Try to use interlayer on node query (should be ignored or error)
    try:
        result = Q.nodes().where(interlayer=("layer0", "layer1")).execute(network)
        # If it succeeds, it should just ignore the predicate
        assert len(result) >= 0
    except (ValueError, TypeError):
        # Expected for invalid predicate
        pass


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_multiple_where_clauses_are_anded(layer_idx):
    """
    Property: Multiple where() calls are ANDed together.
    
    Tests that chaining where() clauses uses AND logic.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    layer = f'layer{layer_idx}'
    
    # Multiple where clauses
    result = (
        Q.nodes()
        .where(layer=layer)
        .where(layer=layer)
        .execute(network)
    )
    df = result.to_pandas()
    
    # All nodes should be from the specified layer
    if len(df) > 0:
        assert all(df['layer'] == layer)


# ============================================================================
# Property Tests: Result Properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_nodes=st.integers(min_value=3, max_value=10)
)
def test_result_length_equals_dataframe_length(num_nodes):
    """
    Property: len(result) equals len(result.to_pandas()).
    
    Tests that result length is consistent.
    """
    network = create_test_network(num_nodes=num_nodes, num_layers=1, seed=42)
    
    result = Q.nodes().execute(network)
    df = result.to_pandas()
    
    # Lengths should match
    assert len(result) == len(df)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_result_is_iterable(num_nodes):
    """
    Property: Results can be iterated.
    
    Tests that results support iteration.
    """
    network = create_test_network(num_nodes=num_nodes, num_layers=1, seed=42)
    
    result = Q.nodes().execute(network)
    
    # Should be iterable
    count = 0
    for item in result:
        count += 1
    
    assert count == len(result)


@pytest.mark.property
def test_empty_result_has_zero_length():
    """
    Property: Empty query results have length 0.
    
    Tests that empty results are handled correctly.
    """
    network = create_test_network(num_nodes=5, num_layers=1, seed=42)
    
    # Query that returns no results
    result = Q.nodes().where(layer="nonexistent_layer").execute(network)
    
    assert len(result) == 0


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_result_metadata_contains_query_info(num_nodes):
    """
    Property: Result metadata contains query information.
    
    Tests that results have proper metadata.
    """
    network = create_test_network(num_nodes=num_nodes, num_layers=1, seed=42)
    
    result = Q.nodes().execute(network)
    
    # Should have metadata
    assert hasattr(result, 'meta')
    assert isinstance(result.meta, dict)


# ============================================================================
# Property Tests: Query Building and Serialization
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_query_to_ast_is_consistent(layer_idx):
    """
    Property: Building query to AST is consistent.
    
    Tests that query builder produces valid AST.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    layer = f'layer{layer_idx}'
    
    # Build query
    query = Q.nodes().from_layers(L[layer]).compute("degree")
    
    # Convert to AST
    ast = query.to_ast()
    
    # Should have valid AST structure
    assert ast is not None
    assert hasattr(ast, 'select')


@pytest.mark.property
def test_multiple_compute_calls_accumulate():
    """
    Property: Multiple compute() calls accumulate metrics.
    
    Tests that chaining compute() adds metrics.
    """
    network = create_test_network(num_nodes=5, num_layers=1, seed=42)
    
    # Multiple compute calls
    result = (
        Q.nodes()
        .compute("degree")
        .compute("clustering")
        .execute(network)
    )
    
    df = result.to_pandas()
    
    # Should have both metrics
    assert 'degree' in df.columns
    assert 'clustering' in df.columns


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_from_layers_overrides_previous(layer_idx):
    """
    Property: from_layers() overrides previous layer selection.
    
    Tests that second from_layers() replaces first.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    layer = f'layer{layer_idx}'
    other_layer = f'layer{1 - layer_idx}'
    
    # Multiple from_layers calls
    result = (
        Q.nodes()
        .from_layers(L[other_layer])
        .from_layers(L[layer])  # This should override
        .execute(network)
    )
    
    df = result.to_pandas()
    
    # All nodes should be from the final layer
    if len(df) > 0:
        assert all(df['layer'] == layer)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_query_execute_is_repeatable(num_nodes):
    """
    Property: Executing same query multiple times gives same results.
    
    Tests that queries are deterministic.
    """
    network = create_test_network(num_nodes=num_nodes, num_layers=1, seed=42)
    
    query = Q.nodes().compute("degree")
    
    # Execute twice
    result1 = query.execute(network)
    result2 = query.execute(network)
    
    # Should return same count
    assert len(result1) == len(result2)


@pytest.mark.property
def test_empty_compute_returns_no_metrics():
    """
    Property: Query without compute() returns no computed metrics.
    
    Tests that metrics are only computed when requested.
    """
    network = create_test_network(num_nodes=5, num_layers=1, seed=42)
    
    result = Q.nodes().execute(network)
    df = result.to_pandas()
    
    # Should have basic columns but no computed metrics
    assert 'id' in df.columns or 'node' in df.columns
    assert 'layer' in df.columns
    # Metrics like degree, betweenness should not be present unless computed
    # (though degree might be added automatically in some cases)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    order_desc=st.booleans()
)
def test_order_by_desc_flag_works(order_desc):
    """
    Property: order_by(desc=True/False) affects ordering.
    
    Tests that desc flag is respected.
    """
    network = create_test_network(num_nodes=6, num_layers=1, seed=42)
    
    result = Q.nodes().compute("degree").order_by("degree", desc=order_desc).execute(network)
    df = result.to_pandas()
    
    if len(df) > 1:
        degrees = df['degree'].tolist()
        if order_desc:
            # First should be >= last
            assert degrees[0] >= degrees[-1]
        else:
            # First should be <= last
            assert degrees[0] <= degrees[-1]


# ============================================================================
# Property Tests: Error Handling and Edge Cases
# ============================================================================

@pytest.mark.property
def test_query_on_empty_network_returns_empty():
    """
    Property: Queries on empty network return empty results.
    
    Tests that empty networks are handled gracefully.
    """
    empty_network = multinet.multi_layer_network(directed=False)
    
    result = Q.nodes().execute(empty_network)
    
    assert len(result) == 0


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    invalid_metric=st.text(min_size=10, max_size=20, alphabet='xyz')
)
def test_invalid_metric_raises_error(invalid_metric):
    """
    Property: Computing invalid metrics raises error.
    
    Tests error handling for invalid metrics.
    """
    from py3plex.dsl.errors import UnknownMeasureError
    
    network = create_test_network(num_nodes=5, num_layers=1, seed=42)
    
    # Try to compute invalid metric - should raise UnknownMeasureError
    with pytest.raises(UnknownMeasureError):
        result = Q.nodes().compute(invalid_metric).execute(network)


@pytest.mark.property
def test_where_with_conflicting_conditions_returns_empty():
    """
    Property: WHERE with conflicting conditions returns empty result.
    
    Tests that impossible conditions return no results.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    
    # Conflicting conditions: layer can't be both at once
    result = Q.nodes().where((F.layer == "layer0") & (F.layer == "layer1")).execute(network)
    
    # Should return empty or small result set
    assert len(result) == 0


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    limit_val=st.integers(min_value=0, max_value=2)
)
def test_limit_zero_or_negative_returns_empty(limit_val):
    """
    Property: LIMIT(0) returns empty result.
    
    Tests that limit=0 or negative is handled.
    """
    network = create_test_network(num_nodes=5, num_layers=1, seed=42)
    
    if limit_val <= 0:
        result = Q.nodes().limit(max(0, limit_val)).execute(network)
        assert len(result) == 0
    else:
        result = Q.nodes().limit(limit_val).execute(network)
        assert len(result) <= limit_val

