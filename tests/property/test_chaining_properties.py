#!/usr/bin/env python3
"""
Property-based tests for graph_ops (dplyr-style chainable operations) module.

Tests invariants for:
- NodeFrame and EdgeFrame operations
- Method chaining consistency
- Filter, select, mutate, arrange, head, group_by operations
- Data integrity through chained operations
"""

import math
import pytest
from hypothesis import given, settings, assume, strategies as st

# Import pandas for to_pandas tests
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

# Import graph_ops module
try:
    from py3plex.graph_ops import (
        nodes,
        edges,
        NodeFrame,
        EdgeFrame,
        GroupedNodeFrame,
        GroupedEdgeFrame,
    )
    from py3plex.core import multinet
    GRAPH_OPS_AVAILABLE = True
except ImportError:
    GRAPH_OPS_AVAILABLE = False
    pytest.skip("graph_ops module not available", allow_module_level=True)


# ============================================================================
# Helper: Create test networks
# ============================================================================

def create_test_network(num_nodes=5, num_layers=2, num_edges_per_layer=3):
    """Create a simple test multilayer network."""
    network = multinet.multi_layer_network(directed=False)
    
    layers = [f'layer{i}' for i in range(num_layers)]
    node_names = [chr(ord('A') + i) for i in range(num_nodes)]
    
    # Add nodes to each layer
    node_dicts = []
    for name in node_names:
        for layer in layers:
            node_dicts.append({'source': name, 'type': layer})
    network.add_nodes(node_dicts)
    
    # Add edges within layers
    edge_dicts = []
    for layer in layers:
        for i in range(min(num_edges_per_layer, len(node_names) - 1)):
            edge_dicts.append({
                'source': node_names[i],
                'target': node_names[i + 1],
                'source_type': layer,
                'target_type': layer,
                'weight': float(i + 1)
            })
    network.add_edges(edge_dicts)
    
    return network


# ============================================================================
# Property Tests: NodeFrame Creation
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_nodes=st.integers(min_value=2, max_value=10),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_nodes_count_equals_nodes_times_layers(num_nodes, num_layers):
    """Test that nodes() returns num_nodes * num_layers nodes."""
    network = create_test_network(num_nodes=num_nodes, num_layers=num_layers)
    
    result = nodes(network)
    
    # Should have exactly num_nodes * num_layers nodes
    assert len(result) == num_nodes * num_layers


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=2)
)
def test_nodes_layer_filter_contains_only_target_layer(layer_idx):
    """Test that layer filter returns only nodes from that layer."""
    network = create_test_network(num_nodes=5, num_layers=3)
    layer = f'layer{layer_idx}'
    
    result = nodes(network, layers=[layer])
    
    # All nodes should be from the specified layer
    for item in result:
        assert item['layer'] == layer


# ============================================================================
# Property Tests: NodeFrame.filter()
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    threshold=st.integers(min_value=0, max_value=10)
)
def test_filter_degree_threshold_invariant(threshold):
    """Test that filter by degree respects threshold."""
    network = create_test_network(num_nodes=6, num_layers=2)
    
    result = nodes(network).filter(lambda n: n['degree'] > threshold)
    
    # All returned nodes should have degree > threshold
    for item in result:
        assert item['degree'] > threshold


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_filter_by_layer_matches_layer_param(layer_idx):
    """Test that filter by layer equals layer parameter result."""
    network = create_test_network(num_nodes=4, num_layers=2)
    layer = f'layer{layer_idx}'
    
    # Filter with lambda
    result_filter = nodes(network).filter(lambda n: n['layer'] == layer)
    
    # Filter with layers parameter
    result_param = nodes(network, layers=[layer])
    
    # Both should return same number of nodes
    assert len(result_filter) == len(result_param)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    threshold1=st.integers(min_value=0, max_value=5),
    threshold2=st.integers(min_value=0, max_value=5)
)
def test_filter_chaining_is_associative(threshold1, threshold2):
    """Test that chaining filters is equivalent to a single combined filter."""
    network = create_test_network(num_nodes=5, num_layers=2)
    
    # Chained filters
    result_chained = (
        nodes(network)
        .filter(lambda n: n['degree'] >= threshold1)
        .filter(lambda n: n['degree'] <= threshold2)
    )
    
    # Single combined filter
    result_single = nodes(network).filter(
        lambda n: n['degree'] >= threshold1 and n['degree'] <= threshold2
    )
    
    # Both should return same count
    assert len(result_chained) == len(result_single)


@pytest.mark.property
def test_filter_preserves_nodeframe_type():
    """Test that filter returns a NodeFrame."""
    network = create_test_network()
    
    result = nodes(network).filter(lambda n: n['degree'] >= 0)
    
    assert isinstance(result, NodeFrame)


# ============================================================================
# Property Tests: NodeFrame.filter_expr()
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    threshold=st.integers(min_value=0, max_value=10)
)
def test_filter_expr_degree_equivalent_to_filter(threshold):
    """Test that filter_expr produces same results as filter for simple conditions."""
    network = create_test_network(num_nodes=5, num_layers=2)
    
    result_expr = nodes(network).filter_expr(f"degree > {threshold}")
    result_lambda = nodes(network).filter(lambda n: n['degree'] > threshold)
    
    # Should produce same count
    assert len(result_expr) == len(result_lambda)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_filter_expr_layer_equality(layer_idx):
    """Test filter_expr with layer equality."""
    network = create_test_network(num_nodes=4, num_layers=2)
    layer = f'layer{layer_idx}'
    
    result = nodes(network).filter_expr(f"layer == '{layer}'")
    
    for item in result:
        assert item['layer'] == layer


# ============================================================================
# Property Tests: NodeFrame.select()
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    fields=st.lists(
        st.sampled_from(['id', 'layer', 'degree']),
        min_size=1,
        max_size=3,
        unique=True
    )
)
def test_select_returns_only_specified_fields(fields):
    """Test that select returns only the specified fields."""
    network = create_test_network()
    
    result = nodes(network).select(*fields)
    
    for item in result:
        # All requested fields that exist should be present
        for field in fields:
            if field in ['id', 'layer', 'degree']:  # These always exist
                assert field in item
        
        # No extra fields (except possibly internal _ fields if not filtered)
        for key in item.keys():
            if not key.startswith('_'):
                assert key in fields


@pytest.mark.property
def test_select_preserves_count():
    """Test that select preserves node count."""
    network = create_test_network()
    
    original = nodes(network)
    selected = original.select('id', 'layer')
    
    assert len(selected) == len(original)


@pytest.mark.property
def test_select_no_fields_is_noop():
    """Test that select with no fields is a no-op."""
    network = create_test_network()
    
    original = nodes(network)
    selected = original.select()
    
    assert len(selected) == len(original)


# ============================================================================
# Property Tests: NodeFrame.mutate()
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    multiplier=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
)
def test_mutate_computes_correctly(multiplier):
    """Test that mutate computes new fields correctly."""
    network = create_test_network()
    
    result = nodes(network).mutate(
        scaled_degree=lambda n: n['degree'] * multiplier
    )
    
    for item in result:
        expected = item['degree'] * multiplier
        assert abs(item['scaled_degree'] - expected) < 1e-9


@pytest.mark.property
def test_mutate_preserves_count():
    """Test that mutate preserves node count."""
    network = create_test_network()
    
    original = nodes(network)
    mutated = original.mutate(new_field=lambda n: 1)
    
    assert len(mutated) == len(original)


@pytest.mark.property
def test_mutate_preserves_existing_fields():
    """Test that mutate preserves existing fields."""
    network = create_test_network()
    
    result = nodes(network).mutate(new_field=lambda n: n['degree'] + 1)
    
    for item in result:
        assert 'id' in item
        assert 'layer' in item
        assert 'degree' in item
        assert 'new_field' in item


@pytest.mark.property
def test_mutate_handles_errors_gracefully():
    """Test that mutate handles computation errors gracefully."""
    network = create_test_network()
    
    # Division by zero should result in None, not crash
    result = nodes(network).mutate(
        error_field=lambda n: 1 / (n['degree'] - n['degree'])  # Always 0
    )
    
    for item in result:
        assert 'error_field' in item
        assert item['error_field'] is None


# ============================================================================
# Property Tests: NodeFrame.arrange()
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    reverse=st.booleans()
)
def test_arrange_sorts_correctly(reverse):
    """Test that arrange sorts by the specified field."""
    network = create_test_network(num_nodes=5, num_layers=1)
    
    result = nodes(network).arrange('degree', reverse=reverse)
    degrees = [item['degree'] for item in result]
    
    expected = sorted(degrees, reverse=reverse)
    assert degrees == expected


@pytest.mark.property
def test_arrange_preserves_count():
    """Test that arrange preserves node count."""
    network = create_test_network()
    
    original = nodes(network)
    arranged = original.arrange('degree')
    
    assert len(arranged) == len(original)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    reverse=st.booleans()
)
def test_arrange_by_callable_equivalent_to_string(reverse):
    """Test that arrange by callable is equivalent to string for simple cases."""
    network = create_test_network()
    
    result_str = nodes(network).arrange('degree', reverse=reverse)
    result_fn = nodes(network).arrange(lambda n: n['degree'], reverse=reverse)
    
    degrees_str = [item['degree'] for item in result_str]
    degrees_fn = [item['degree'] for item in result_fn]
    
    assert degrees_str == degrees_fn


# ============================================================================
# Property Tests: NodeFrame.head()
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=1, max_value=20)
)
def test_head_returns_at_most_n_items(n):
    """Test that head returns at most n items."""
    network = create_test_network(num_nodes=10, num_layers=2)
    
    result = nodes(network).head(n)
    
    assert len(result) <= n


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=1, max_value=5)
)
def test_head_returns_first_n_items(n):
    """Test that head returns the first n items in order."""
    network = create_test_network()
    
    original = nodes(network)
    result = original.head(n)
    
    # Get first n items from original
    original_items = list(original)[:n]
    result_items = list(result)
    
    # IDs should match
    original_ids = [item['id'] for item in original_items]
    result_ids = [item['id'] for item in result_items]
    
    assert original_ids == result_ids


# ============================================================================
# Property Tests: NodeFrame.group_by() and summarise()
# ============================================================================

@pytest.mark.property
def test_group_by_returns_grouped_frame():
    """Test that group_by returns a GroupedNodeFrame."""
    network = create_test_network()
    
    result = nodes(network).group_by('layer')
    
    assert isinstance(result, GroupedNodeFrame)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_layers=st.integers(min_value=1, max_value=4)
)
def test_group_by_summarise_produces_one_row_per_group(num_layers):
    """Test that summarise produces one row per group."""
    network = create_test_network(num_nodes=4, num_layers=num_layers)
    
    result = nodes(network).group_by('layer').summarise(n=('id', len))
    
    # Should have one row per layer
    assert len(result) == num_layers


@pytest.mark.property
def test_group_by_summarise_count_sums_to_total():
    """Test that sum of group counts equals total count."""
    network = create_test_network(num_nodes=5, num_layers=2)
    
    total = len(nodes(network))
    
    result = nodes(network).group_by('layer').summarise(n=('id', len))
    
    # Sum of counts should equal total
    count_sum = sum(item['n'] for item in result)
    assert count_sum == total


@pytest.mark.property
def test_group_by_summarise_preserves_group_key():
    """Test that summarise preserves group key fields."""
    network = create_test_network(num_nodes=4, num_layers=2)
    
    result = nodes(network).group_by('layer').summarise(n=('id', len))
    
    for item in result:
        assert 'layer' in item


# ============================================================================
# Property Tests: Chaining Operations
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    threshold=st.integers(min_value=0, max_value=5),
    head_n=st.integers(min_value=1, max_value=10)
)
def test_filter_arrange_head_chain(threshold, head_n):
    """Test filter -> arrange -> head chain maintains invariants."""
    network = create_test_network(num_nodes=6, num_layers=2)
    
    result = (
        nodes(network)
        .filter(lambda n: n['degree'] >= threshold)
        .arrange('degree', reverse=True)
        .head(head_n)
    )
    
    # All returned items should have degree >= threshold
    degrees = [item['degree'] for item in result]
    for d in degrees:
        assert d >= threshold
    
    # Should be sorted in descending order
    assert degrees == sorted(degrees, reverse=True)
    
    # Should have at most head_n items
    assert len(result) <= head_n


@pytest.mark.property
def test_mutate_select_chain():
    """Test mutate -> select chain."""
    network = create_test_network()
    
    result = (
        nodes(network)
        .mutate(doubled=lambda n: n['degree'] * 2)
        .select('id', 'doubled')
    )
    
    for item in result:
        assert 'id' in item
        assert 'doubled' in item
        assert 'degree' not in item  # Should be filtered out by select


@pytest.mark.property
def test_filter_mutate_select_chain():
    """Test filter -> mutate -> select chain."""
    network = create_test_network()
    
    result = (
        nodes(network)
        .filter(lambda n: n['degree'] >= 1)
        .mutate(log_degree=lambda n: math.log1p(n['degree']))
        .select('id', 'layer', 'log_degree')
    )
    
    for item in result:
        assert 'id' in item
        assert 'layer' in item
        assert 'log_degree' in item
        assert 'degree' not in item


# ============================================================================
# Property Tests: EdgeFrame Operations
# ============================================================================

@pytest.mark.property
def test_edges_returns_edgeframe():
    """Test that edges() returns an EdgeFrame."""
    network = create_test_network()
    
    result = edges(network)
    
    assert isinstance(result, EdgeFrame)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    weight_threshold=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False)
)
def test_edge_filter_weight_threshold(weight_threshold):
    """Test that edge filter by weight respects threshold."""
    network = create_test_network(num_nodes=5, num_layers=2, num_edges_per_layer=4)
    
    result = edges(network).filter(lambda e: e.get('weight', 0) >= weight_threshold)
    
    for item in result:
        assert item.get('weight', 0) >= weight_threshold


@pytest.mark.property
def test_edge_mutate_preserves_count():
    """Test that edge mutate preserves count."""
    network = create_test_network()
    
    original = edges(network)
    mutated = original.mutate(new_field=lambda e: 1)
    
    assert len(mutated) == len(original)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    reverse=st.booleans()
)
def test_edge_arrange_sorts_correctly(reverse):
    """Test that edge arrange sorts by weight."""
    network = create_test_network(num_nodes=5, num_layers=1, num_edges_per_layer=4)
    
    result = edges(network).arrange('weight', reverse=reverse)
    weights = [item.get('weight', 0) for item in result]
    
    expected = sorted(weights, reverse=reverse)
    assert weights == expected


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=1, max_value=10)
)
def test_edge_head_returns_at_most_n(n):
    """Test that edge head returns at most n items."""
    network = create_test_network()
    
    result = edges(network).head(n)
    
    assert len(result) <= n


@pytest.mark.property
def test_edge_group_by_returns_grouped():
    """Test that edge group_by returns GroupedEdgeFrame."""
    network = create_test_network(num_nodes=4, num_layers=2)
    
    result = edges(network).group_by('source_layer')
    
    assert isinstance(result, GroupedEdgeFrame)


# ============================================================================
# Property Tests: to_pandas() export
# ============================================================================

@pytest.mark.property
@pytest.mark.skipif(not PANDAS_AVAILABLE, reason="pandas not available")
def test_to_pandas_row_count_matches():
    """Test that to_pandas row count matches frame length."""
    network = create_test_network()
    
    frame = nodes(network)
    df = frame.to_pandas()
    
    assert len(df) == len(frame)


@pytest.mark.property
@pytest.mark.skipif(not PANDAS_AVAILABLE, reason="pandas not available")
def test_to_pandas_excludes_internal_fields():
    """Test that to_pandas excludes fields starting with _."""
    network = create_test_network()
    
    df = nodes(network).to_pandas()
    
    for col in df.columns:
        assert not col.startswith('_')


# ============================================================================
# Property Tests: Iterable Protocol
# ============================================================================

@pytest.mark.property
def test_nodeframe_len_matches_iter():
    """Test that len(frame) matches number of items from iter."""
    network = create_test_network()
    
    frame = nodes(network)
    
    assert len(frame) == len(list(frame))


@pytest.mark.property
def test_edgeframe_len_matches_iter():
    """Test that len(frame) matches number of items from iter."""
    network = create_test_network()
    
    frame = edges(network)
    
    assert len(frame) == len(list(frame))


# ============================================================================
# Property Tests: Idempotence
# ============================================================================

@pytest.mark.property
def test_filter_true_is_identity():
    """Test that filter(lambda: True) returns all items."""
    network = create_test_network()
    
    original = nodes(network)
    filtered = original.filter(lambda n: True)
    
    assert len(filtered) == len(original)


@pytest.mark.property
def test_arrange_is_stable():
    """Test that arranging twice by same key gives same result."""
    network = create_test_network()
    
    first = nodes(network).arrange('degree')
    second = first.arrange('degree')
    
    # Results should be same
    first_ids = [item['id'] for item in first]
    second_ids = [item['id'] for item in second]
    
    assert first_ids == second_ids


@pytest.mark.property
def test_select_same_fields_is_idempotent():
    """Test that selecting same fields twice is idempotent."""
    network = create_test_network()
    
    first = nodes(network).select('id', 'layer')
    second = first.select('id', 'layer')
    
    # Both should have same structure
    assert len(first) == len(second)
    for item1, item2 in zip(first, second):
        assert set(item1.keys()) == set(item2.keys())


# ============================================================================
# Property Tests: to_subgraph and EdgeFrame Integration
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    layer_idx=st.integers(min_value=0, max_value=1)
)
def test_to_subgraph_preserves_layer(layer_idx):
    """Test that to_subgraph preserves layer information."""
    network = create_test_network(num_nodes=5, num_layers=2)
    layer = f'layer{layer_idx}'
    
    subgraph = nodes(network, layers=[layer]).to_subgraph()
    
    # All nodes in subgraph should be from the specified layer
    for node in subgraph.get_nodes():
        if isinstance(node, tuple):
            assert node[1] == layer


@pytest.mark.property
def test_to_subgraph_on_filtered_nodes():
    """Test to_subgraph on filtered nodes."""
    network = create_test_network(num_nodes=5, num_layers=1)
    
    subgraph = (
        nodes(network)
        .filter(lambda n: n['degree'] >= 1)
        .to_subgraph()
    )
    
    # Subgraph should have nodes
    assert hasattr(subgraph, 'core_network')


@pytest.mark.property
def test_edge_filter_expr():
    """Test EdgeFrame filter_expr method."""
    network = create_test_network(num_nodes=4, num_layers=2, num_edges_per_layer=3)
    
    result = edges(network).filter_expr("weight >= 1")
    
    for item in result:
        assert item.get('weight', 0) >= 1


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=1, max_value=5)
)
def test_edge_select_fields(n):
    """Test EdgeFrame select with various fields."""
    network = create_test_network(num_nodes=5, num_layers=1, num_edges_per_layer=4)
    
    result = edges(network).select('source', 'target').head(n)
    
    for item in result:
        assert 'source' in item
        assert 'target' in item


@pytest.mark.property
def test_edge_summarise_count():
    """Test EdgeFrame group_by and summarise."""
    network = create_test_network(num_nodes=4, num_layers=2, num_edges_per_layer=3)
    
    result = (
        edges(network)
        .group_by('source_layer')
        .summarise(n=('source', len))
    )
    
    # Each group should have the count
    for item in result:
        assert 'source_layer' in item
        assert 'n' in item


@pytest.mark.property
def test_repr_formats():
    """Test __repr__ methods return strings."""
    network = create_test_network()
    
    node_frame = nodes(network)
    edge_frame = edges(network)
    
    assert isinstance(repr(node_frame), str)
    assert isinstance(repr(edge_frame), str)
    assert 'NodeFrame' in repr(node_frame)
    assert 'EdgeFrame' in repr(edge_frame)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_group_by_multiple_fields(num_layers):
    """Test group_by with multiple fields."""
    network = create_test_network(num_nodes=4, num_layers=num_layers)
    
    # Group by layer only
    result = nodes(network).group_by('layer').summarise(n=('id', len))
    
    # Should have one row per layer
    assert len(result) == num_layers


# ============================================================================
# Property Tests: NodeFrame.tail()
# ============================================================================


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=1, max_value=20)
)
def test_tail_returns_at_most_n_items(n):
    """Test that tail returns at most n items."""
    network = create_test_network(num_nodes=10, num_layers=2)
    
    result = nodes(network).tail(n)
    
    assert len(result) <= n


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=1, max_value=5)
)
def test_tail_returns_last_n_items(n):
    """Test that tail returns the last n items in order."""
    network = create_test_network()
    
    original = nodes(network)
    result = original.tail(n)
    
    # Get last n items from original
    original_items = list(original)[-n:]
    result_items = list(result)
    
    # IDs should match
    original_ids = [item['id'] for item in original_items]
    result_ids = [item['id'] for item in result_items]
    
    assert original_ids == result_ids


@pytest.mark.property
def test_tail_zero_returns_empty():
    """Test that tail(0) returns empty result."""
    network = create_test_network()
    
    result = nodes(network).tail(0)
    
    assert len(result) == 0


@pytest.mark.property
def test_tail_preserves_nodeframe_type():
    """Test that tail returns a NodeFrame."""
    network = create_test_network()
    
    result = nodes(network).tail(3)
    
    assert isinstance(result, NodeFrame)


# ============================================================================
# Property Tests: NodeFrame.sample()
# ============================================================================


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=1, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sample_returns_at_most_n_items(n, seed):
    """Test that sample returns at most n items."""
    network = create_test_network(num_nodes=10, num_layers=2)
    
    result = nodes(network).sample(n, seed=seed)
    
    assert len(result) <= n


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sample_is_reproducible(seed):
    """Test that sample with same seed returns same result."""
    network = create_test_network(num_nodes=6, num_layers=2)
    
    result1 = nodes(network).sample(4, seed=seed)
    result2 = nodes(network).sample(4, seed=seed)
    
    ids1 = [item['id'] for item in result1]
    ids2 = [item['id'] for item in result2]
    
    assert ids1 == ids2


@pytest.mark.property
def test_sample_preserves_nodeframe_type():
    """Test that sample returns a NodeFrame."""
    network = create_test_network()
    
    result = nodes(network).sample(3, seed=42)
    
    assert isinstance(result, NodeFrame)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=1, max_value=5)
)
def test_sample_items_are_from_original(n):
    """Test that sampled items are from the original data."""
    network = create_test_network(num_nodes=6, num_layers=2)
    
    original = nodes(network)
    result = original.sample(n, seed=42)
    
    original_ids = set(item['id'] for item in original)
    result_ids = set(item['id'] for item in result)
    
    # All result ids should be in original
    assert result_ids.issubset(original_ids)


# ============================================================================
# Property Tests: NodeFrame.distinct()
# ============================================================================


@pytest.mark.property
def test_distinct_reduces_or_keeps_count():
    """Test that distinct does not increase the count."""
    network = create_test_network(num_nodes=5, num_layers=2)
    
    original = nodes(network)
    result = original.distinct('id')
    
    assert len(result) <= len(original)


@pytest.mark.property
def test_distinct_on_id_returns_unique_ids():
    """Test that distinct on id field returns unique ids."""
    network = create_test_network(num_nodes=5, num_layers=2)
    
    result = nodes(network).distinct('id')
    
    ids = [item['id'] for item in result]
    assert len(ids) == len(set(ids))


@pytest.mark.property
def test_distinct_on_all_fields_is_idempotent():
    """Test that distinct on all fields twice returns same result."""
    network = create_test_network()
    
    first = nodes(network).distinct('id', 'layer')
    second = first.distinct('id', 'layer')
    
    assert len(first) == len(second)


@pytest.mark.property
def test_distinct_preserves_nodeframe_type():
    """Test that distinct returns a NodeFrame."""
    network = create_test_network()
    
    result = nodes(network).distinct('id')
    
    assert isinstance(result, NodeFrame)


# ============================================================================
# Property Tests: NodeFrame.count()
# ============================================================================


@pytest.mark.property
def test_count_equals_len():
    """Test that count() equals len() of frame."""
    network = create_test_network()
    
    frame = nodes(network)
    
    assert frame.count() == len(frame)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    threshold=st.integers(min_value=0, max_value=10)
)
def test_count_after_filter(threshold):
    """Test that count after filter is consistent."""
    network = create_test_network(num_nodes=6, num_layers=2)
    
    result = nodes(network).filter(lambda n: n['degree'] >= threshold)
    
    assert result.count() == len(list(result))


@pytest.mark.property
def test_count_returns_integer():
    """Test that count returns an integer."""
    network = create_test_network()
    
    count = nodes(network).count()
    
    assert isinstance(count, int)


# ============================================================================
# Property Tests: NodeFrame.rename()
# ============================================================================


@pytest.mark.property
def test_rename_preserves_count():
    """Test that rename preserves node count."""
    network = create_test_network()
    
    original = nodes(network)
    result = original.rename(id='node_id')
    
    assert len(result) == len(original)


@pytest.mark.property
def test_rename_replaces_old_with_new():
    """Test that rename replaces old field with new."""
    network = create_test_network()
    
    result = nodes(network).rename(id='node_id')
    
    for item in result:
        assert 'node_id' in item
        assert 'id' not in item


@pytest.mark.property
def test_rename_preserves_values():
    """Test that rename preserves field values."""
    network = create_test_network()
    
    original = list(nodes(network))
    result = list(nodes(network).rename(id='node_id'))
    
    # Check that values are preserved
    orig_ids = [item['id'] for item in original]
    new_ids = [item['node_id'] for item in result]
    
    assert orig_ids == new_ids


@pytest.mark.property
def test_rename_preserves_nodeframe_type():
    """Test that rename returns a NodeFrame."""
    network = create_test_network()
    
    result = nodes(network).rename(id='node_id')
    
    assert isinstance(result, NodeFrame)


# ============================================================================
# Property Tests: NodeFrame.drop()
# ============================================================================


@pytest.mark.property
def test_drop_preserves_count():
    """Test that drop preserves node count."""
    network = create_test_network()
    
    original = nodes(network)
    result = original.drop('degree')
    
    assert len(result) == len(original)


@pytest.mark.property
def test_drop_removes_specified_field():
    """Test that drop removes the specified field."""
    network = create_test_network()
    
    result = nodes(network).drop('degree')
    
    for item in result:
        assert 'degree' not in item
        assert 'id' in item  # Other fields remain


@pytest.mark.property
def test_drop_preserves_nodeframe_type():
    """Test that drop returns a NodeFrame."""
    network = create_test_network()
    
    result = nodes(network).drop('degree')
    
    assert isinstance(result, NodeFrame)


# ============================================================================
# Property Tests: NodeFrame.where() (alias for filter)
# ============================================================================


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    threshold=st.integers(min_value=0, max_value=10)
)
def test_where_equivalent_to_filter(threshold):
    """Test that where() is equivalent to filter()."""
    network = create_test_network(num_nodes=6, num_layers=2)
    
    result_where = nodes(network).where(lambda n: n['degree'] >= threshold)
    result_filter = nodes(network).filter(lambda n: n['degree'] >= threshold)
    
    assert len(result_where) == len(result_filter)


@pytest.mark.property
def test_where_preserves_nodeframe_type():
    """Test that where returns a NodeFrame."""
    network = create_test_network()
    
    result = nodes(network).where(lambda n: n['degree'] >= 0)
    
    assert isinstance(result, NodeFrame)


# ============================================================================
# Property Tests: NodeFrame.order_by() (alias for arrange)
# ============================================================================


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    descending=st.booleans()
)
def test_order_by_equivalent_to_arrange(descending):
    """Test that order_by() is equivalent to arrange()."""
    network = create_test_network(num_nodes=5, num_layers=1)
    
    result_order_by = nodes(network).order_by('degree', descending=descending)
    result_arrange = nodes(network).arrange('degree', reverse=descending)
    
    ids_order_by = [item['id'] for item in result_order_by]
    ids_arrange = [item['id'] for item in result_arrange]
    
    assert ids_order_by == ids_arrange


@pytest.mark.property
def test_order_by_preserves_nodeframe_type():
    """Test that order_by returns a NodeFrame."""
    network = create_test_network()
    
    result = nodes(network).order_by('degree')
    
    assert isinstance(result, NodeFrame)


# ============================================================================
# Property Tests: NodeFrame.take() (alias for head)
# ============================================================================


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=1, max_value=20)
)
def test_take_equivalent_to_head(n):
    """Test that take() is equivalent to head()."""
    network = create_test_network(num_nodes=10, num_layers=2)
    
    result_take = nodes(network).take(n)
    result_head = nodes(network).head(n)
    
    ids_take = [item['id'] for item in result_take]
    ids_head = [item['id'] for item in result_head]
    
    assert ids_take == ids_head


@pytest.mark.property
def test_take_preserves_nodeframe_type():
    """Test that take returns a NodeFrame."""
    network = create_test_network()
    
    result = nodes(network).take(3)
    
    assert isinstance(result, NodeFrame)


# ============================================================================
# Property Tests: NodeFrame.slice()
# ============================================================================


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    start=st.integers(min_value=0, max_value=5),
    length=st.integers(min_value=1, max_value=5)
)
def test_slice_returns_correct_range(start, length):
    """Test that slice returns the correct range."""
    network = create_test_network(num_nodes=10, num_layers=2)
    
    original = list(nodes(network))
    end = start + length
    result = list(nodes(network).slice(start, end))
    
    expected = original[start:end]
    
    assert len(result) == len(expected)
    for r, e in zip(result, expected):
        assert r['id'] == e['id']


@pytest.mark.property
def test_slice_preserves_nodeframe_type():
    """Test that slice returns a NodeFrame."""
    network = create_test_network()
    
    result = nodes(network).slice(0, 3)
    
    assert isinstance(result, NodeFrame)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    start=st.integers(min_value=0, max_value=10)
)
def test_slice_without_end_goes_to_end(start):
    """Test that slice without end goes to end of data."""
    network = create_test_network(num_nodes=6, num_layers=2)
    
    original = list(nodes(network))
    result = list(nodes(network).slice(start))
    
    expected = original[start:]
    
    assert len(result) == len(expected)


# ============================================================================
# Property Tests: NodeFrame.first()
# ============================================================================


@pytest.mark.property
def test_first_returns_first_item():
    """Test that first returns the first item."""
    network = create_test_network()
    
    original = list(nodes(network))
    result = nodes(network).first()
    
    assert result is not None
    assert result['id'] == original[0]['id']


@pytest.mark.property
def test_first_on_empty_returns_none():
    """Test that first on empty frame returns None."""
    network = create_test_network()
    
    result = nodes(network).filter(lambda n: False).first()
    
    assert result is None


@pytest.mark.property
def test_first_returns_dict():
    """Test that first returns a dict."""
    network = create_test_network()
    
    result = nodes(network).first()
    
    assert isinstance(result, dict)


# ============================================================================
# Property Tests: NodeFrame.last()
# ============================================================================


@pytest.mark.property
def test_last_returns_last_item():
    """Test that last returns the last item."""
    network = create_test_network()
    
    original = list(nodes(network))
    result = nodes(network).last()
    
    assert result is not None
    assert result['id'] == original[-1]['id']


@pytest.mark.property
def test_last_on_empty_returns_none():
    """Test that last on empty frame returns None."""
    network = create_test_network()
    
    result = nodes(network).filter(lambda n: False).last()
    
    assert result is None


@pytest.mark.property
def test_last_returns_dict():
    """Test that last returns a dict."""
    network = create_test_network()
    
    result = nodes(network).last()
    
    assert isinstance(result, dict)


# ============================================================================
# Property Tests: NodeFrame.collect()
# ============================================================================


@pytest.mark.property
def test_collect_returns_list():
    """Test that collect returns a list."""
    network = create_test_network()
    
    result = nodes(network).collect()
    
    assert isinstance(result, list)


@pytest.mark.property
def test_collect_length_equals_frame_length():
    """Test that collect returns list of same length as frame."""
    network = create_test_network()
    
    frame = nodes(network)
    result = frame.collect()
    
    assert len(result) == len(frame)


@pytest.mark.property
def test_collect_preserves_items():
    """Test that collect preserves all items."""
    network = create_test_network()
    
    frame = nodes(network)
    collected = frame.collect()
    iterated = list(frame)
    
    assert len(collected) == len(iterated)
    for c, i in zip(collected, iterated):
        assert c['id'] == i['id']


# ============================================================================
# Property Tests: NodeFrame.pluck()
# ============================================================================


@pytest.mark.property
def test_pluck_returns_list():
    """Test that pluck returns a list."""
    network = create_test_network()
    
    result = nodes(network).pluck('id')
    
    assert isinstance(result, list)


@pytest.mark.property
def test_pluck_length_equals_frame_length():
    """Test that pluck returns list of same length as frame."""
    network = create_test_network()
    
    frame = nodes(network)
    result = frame.pluck('id')
    
    assert len(result) == len(frame)


@pytest.mark.property
def test_pluck_extracts_correct_values():
    """Test that pluck extracts the correct field values."""
    network = create_test_network()
    
    frame = nodes(network)
    plucked = frame.pluck('degree')
    
    # Verify against manually extracted values
    expected = [item['degree'] for item in frame]
    
    assert plucked == expected


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    field=st.sampled_from(['id', 'layer', 'degree'])
)
def test_pluck_field_consistency(field):
    """Test that pluck extracts values for any valid field."""
    network = create_test_network()
    
    frame = nodes(network)
    plucked = frame.pluck(field)
    
    # All plucked values should match the field values
    for i, item in enumerate(frame):
        assert plucked[i] == item[field]


# ============================================================================
# Property Tests: EdgeFrame.tail()
# ============================================================================


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=1, max_value=10)
)
def test_edge_tail_returns_at_most_n(n):
    """Test that edge tail returns at most n items."""
    network = create_test_network(num_nodes=5, num_layers=2, num_edges_per_layer=4)
    
    result = edges(network).tail(n)
    
    assert len(result) <= n


@pytest.mark.property
def test_edge_tail_preserves_edgeframe_type():
    """Test that edge tail returns an EdgeFrame."""
    network = create_test_network()
    
    result = edges(network).tail(3)
    
    assert isinstance(result, EdgeFrame)


# ============================================================================
# Property Tests: EdgeFrame.sample()
# ============================================================================


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=1, max_value=10),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_edge_sample_returns_at_most_n(n, seed):
    """Test that edge sample returns at most n items."""
    network = create_test_network(num_nodes=5, num_layers=2, num_edges_per_layer=4)
    
    result = edges(network).sample(n, seed=seed)
    
    assert len(result) <= n


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    seed=st.integers(min_value=0, max_value=10000)
)
def test_edge_sample_is_reproducible(seed):
    """Test that edge sample with same seed is reproducible."""
    network = create_test_network(num_nodes=5, num_layers=2, num_edges_per_layer=4)
    
    result1 = edges(network).sample(3, seed=seed)
    result2 = edges(network).sample(3, seed=seed)
    
    sources1 = [item['source'] for item in result1]
    sources2 = [item['source'] for item in result2]
    
    assert sources1 == sources2


# ============================================================================
# Property Tests: EdgeFrame.distinct()
# ============================================================================


@pytest.mark.property
def test_edge_distinct_reduces_or_keeps_count():
    """Test that edge distinct does not increase count."""
    network = create_test_network()
    
    original = edges(network)
    result = original.distinct('source', 'target')
    
    assert len(result) <= len(original)


@pytest.mark.property
def test_edge_distinct_returns_unique():
    """Test that edge distinct returns unique combinations."""
    network = create_test_network(num_nodes=5, num_layers=2, num_edges_per_layer=3)
    
    result = edges(network).distinct('source', 'target')
    
    pairs = [(item['source'], item['target']) for item in result]
    assert len(pairs) == len(set(pairs))


# ============================================================================
# Property Tests: EdgeFrame.count()
# ============================================================================


@pytest.mark.property
def test_edge_count_equals_len():
    """Test that edge count equals len."""
    network = create_test_network()
    
    frame = edges(network)
    
    assert frame.count() == len(frame)


# ============================================================================
# Property Tests: EdgeFrame.rename()
# ============================================================================


@pytest.mark.property
def test_edge_rename_preserves_count():
    """Test that edge rename preserves count."""
    network = create_test_network()
    
    original = edges(network)
    result = original.rename(source='from_node')
    
    assert len(result) == len(original)


@pytest.mark.property
def test_edge_rename_replaces_old_with_new():
    """Test that edge rename replaces old field with new."""
    network = create_test_network()
    
    result = edges(network).rename(source='from_node')
    
    for item in result:
        assert 'from_node' in item
        assert 'source' not in item


# ============================================================================
# Property Tests: EdgeFrame.drop()
# ============================================================================


@pytest.mark.property
def test_edge_drop_preserves_count():
    """Test that edge drop preserves count."""
    network = create_test_network()
    
    original = edges(network)
    result = original.drop('weight')
    
    assert len(result) == len(original)


@pytest.mark.property
def test_edge_drop_removes_specified_field():
    """Test that edge drop removes the specified field."""
    network = create_test_network()
    
    result = edges(network).drop('weight')
    
    for item in result:
        assert 'weight' not in item


# ============================================================================
# Property Tests: EdgeFrame.where() (alias for filter)
# ============================================================================


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    threshold=st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False)
)
def test_edge_where_equivalent_to_filter(threshold):
    """Test that edge where is equivalent to filter."""
    network = create_test_network(num_nodes=5, num_layers=2, num_edges_per_layer=4)
    
    result_where = edges(network).where(lambda e: e.get('weight', 0) >= threshold)
    result_filter = edges(network).filter(lambda e: e.get('weight', 0) >= threshold)
    
    assert len(result_where) == len(result_filter)


# ============================================================================
# Property Tests: EdgeFrame.order_by() (alias for arrange)
# ============================================================================


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    descending=st.booleans()
)
def test_edge_order_by_equivalent_to_arrange(descending):
    """Test that edge order_by is equivalent to arrange."""
    network = create_test_network(num_nodes=5, num_layers=1, num_edges_per_layer=4)
    
    result_order_by = edges(network).order_by('weight', descending=descending)
    result_arrange = edges(network).arrange('weight', reverse=descending)
    
    weights_order_by = [item.get('weight', 0) for item in result_order_by]
    weights_arrange = [item.get('weight', 0) for item in result_arrange]
    
    assert weights_order_by == weights_arrange


# ============================================================================
# Property Tests: EdgeFrame.take() (alias for head)
# ============================================================================


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=1, max_value=10)
)
def test_edge_take_equivalent_to_head(n):
    """Test that edge take is equivalent to head."""
    network = create_test_network()
    
    result_take = edges(network).take(n)
    result_head = edges(network).head(n)
    
    assert len(result_take) == len(result_head)


# ============================================================================
# Property Tests: EdgeFrame.slice()
# ============================================================================


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    start=st.integers(min_value=0, max_value=3),
    length=st.integers(min_value=1, max_value=3)
)
def test_edge_slice_returns_correct_range(start, length):
    """Test that edge slice returns correct range."""
    network = create_test_network(num_nodes=5, num_layers=2, num_edges_per_layer=4)
    
    original = list(edges(network))
    end = start + length
    result = list(edges(network).slice(start, end))
    
    expected = original[start:end]
    
    assert len(result) == len(expected)


# ============================================================================
# Property Tests: EdgeFrame.first() and EdgeFrame.last()
# ============================================================================


@pytest.mark.property
def test_edge_first_returns_first_item():
    """Test that edge first returns the first item."""
    network = create_test_network()
    
    original = list(edges(network))
    result = edges(network).first()
    
    assert result is not None
    assert result['source'] == original[0]['source']


@pytest.mark.property
def test_edge_last_returns_last_item():
    """Test that edge last returns the last item."""
    network = create_test_network()
    
    original = list(edges(network))
    result = edges(network).last()
    
    assert result is not None
    assert result['source'] == original[-1]['source']


@pytest.mark.property
def test_edge_first_on_empty_returns_none():
    """Test that edge first on empty returns None."""
    network = create_test_network()
    
    result = edges(network).filter(lambda e: False).first()
    
    assert result is None


@pytest.mark.property
def test_edge_last_on_empty_returns_none():
    """Test that edge last on empty returns None."""
    network = create_test_network()
    
    result = edges(network).filter(lambda e: False).last()
    
    assert result is None


# ============================================================================
# Property Tests: EdgeFrame.collect()
# ============================================================================


@pytest.mark.property
def test_edge_collect_returns_list():
    """Test that edge collect returns a list."""
    network = create_test_network()
    
    result = edges(network).collect()
    
    assert isinstance(result, list)


@pytest.mark.property
def test_edge_collect_length_equals_frame_length():
    """Test that edge collect length equals frame length."""
    network = create_test_network()
    
    frame = edges(network)
    result = frame.collect()
    
    assert len(result) == len(frame)


# ============================================================================
# Property Tests: EdgeFrame.pluck()
# ============================================================================


@pytest.mark.property
def test_edge_pluck_returns_list():
    """Test that edge pluck returns a list."""
    network = create_test_network()
    
    result = edges(network).pluck('source')
    
    assert isinstance(result, list)


@pytest.mark.property
def test_edge_pluck_length_equals_frame_length():
    """Test that edge pluck length equals frame length."""
    network = create_test_network()
    
    frame = edges(network)
    result = frame.pluck('source')
    
    assert len(result) == len(frame)


@pytest.mark.property
def test_edge_pluck_extracts_correct_values():
    """Test that edge pluck extracts correct values."""
    network = create_test_network()
    
    frame = edges(network)
    plucked = frame.pluck('source')
    
    expected = [item['source'] for item in frame]
    
    assert plucked == expected


# ============================================================================
# Property Tests: Chaining Invariants for New Methods
# ============================================================================


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=1, max_value=5)
)
def test_filter_tail_chain(n):
    """Test filter -> tail chain maintains invariants."""
    network = create_test_network(num_nodes=6, num_layers=2)
    
    result = (
        nodes(network)
        .filter(lambda node: node['degree'] >= 0)
        .tail(n)
    )
    
    assert len(result) <= n


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=1, max_value=5),
    seed=st.integers(min_value=0, max_value=1000)
)
def test_filter_sample_chain(n, seed):
    """Test filter -> sample chain maintains invariants."""
    network = create_test_network(num_nodes=6, num_layers=2)
    
    result = (
        nodes(network)
        .filter(lambda node: node['degree'] >= 0)
        .sample(n, seed=seed)
    )
    
    assert len(result) <= n


@pytest.mark.property
def test_mutate_rename_chain():
    """Test mutate -> rename chain maintains invariants."""
    network = create_test_network()
    
    result = (
        nodes(network)
        .mutate(doubled=lambda n: n['degree'] * 2)
        .rename(doubled='double_degree')
    )
    
    for item in result:
        assert 'double_degree' in item
        assert 'doubled' not in item


@pytest.mark.property
def test_mutate_drop_chain():
    """Test mutate -> drop chain maintains invariants."""
    network = create_test_network()
    
    result = (
        nodes(network)
        .mutate(doubled=lambda n: n['degree'] * 2)
        .drop('degree')
    )
    
    for item in result:
        assert 'doubled' in item
        assert 'degree' not in item


@pytest.mark.property
def test_distinct_count_consistency():
    """Test that distinct then count is consistent."""
    network = create_test_network(num_nodes=5, num_layers=2)
    
    result = nodes(network).distinct('id')
    
    assert result.count() == len(result)


@pytest.mark.property
def test_collect_first_consistency():
    """Test that collect()[0] equals first()."""
    network = create_test_network()
    
    frame = nodes(network)
    collected = frame.collect()
    first = frame.first()
    
    if collected:
        assert collected[0]['id'] == first['id']


@pytest.mark.property
def test_collect_last_consistency():
    """Test that collect()[-1] equals last()."""
    network = create_test_network()
    
    frame = nodes(network)
    collected = frame.collect()
    last = frame.last()
    
    if collected:
        assert collected[-1]['id'] == last['id']


@pytest.mark.property
def test_pluck_matches_select_collect():
    """Test that pluck equals select then collect then extract."""
    network = create_test_network()
    
    frame = nodes(network)
    plucked = frame.pluck('layer')
    
    # Manual extraction
    collected = [item['layer'] for item in frame.collect()]
    
    assert plucked == collected


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    start=st.integers(min_value=0, max_value=3),
    length=st.integers(min_value=1, max_value=3)
)
def test_slice_head_tail_consistency(start, length):
    """Test slice behavior relative to head and tail."""
    network = create_test_network(num_nodes=8, num_layers=2)
    
    frame = nodes(network)
    total = len(frame)
    
    # slice(0, n) should equal head(n)
    slice_from_start = list(frame.slice(0, length))
    head_result = list(frame.head(length))
    
    assert [item['id'] for item in slice_from_start] == [item['id'] for item in head_result]


@pytest.mark.property
def test_where_order_by_take_chain():
    """Test where -> order_by -> take chain (SQL style)."""
    network = create_test_network(num_nodes=6, num_layers=2)
    
    result = (
        nodes(network)
        .where(lambda n: n['layer'] == 'layer0')
        .order_by('degree', descending=True)
        .take(3)
    )
    
    # All items should be from layer0
    for item in result:
        assert item['layer'] == 'layer0'
    
    # Should be sorted descending
    degrees = [item['degree'] for item in result]
    assert degrees == sorted(degrees, reverse=True)
    
    # Should have at most 3 items
    assert len(result) <= 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
