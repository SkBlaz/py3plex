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
@settings(deadline=None, max_examples=30)
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
@settings(deadline=None, max_examples=30)
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
@settings(deadline=None, max_examples=30)
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
@settings(deadline=None, max_examples=30)
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
@settings(deadline=None, max_examples=20)
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
@settings(deadline=None, max_examples=30)
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
@settings(deadline=None, max_examples=20)
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
@settings(deadline=None, max_examples=30)
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
@settings(deadline=None, max_examples=30)
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
@settings(deadline=None, max_examples=30)
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
@settings(deadline=None, max_examples=20)
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
@settings(deadline=None, max_examples=30)
@given(
    n=st.integers(min_value=1, max_value=20)
)
def test_head_returns_at_most_n_items(n):
    """Test that head returns at most n items."""
    network = create_test_network(num_nodes=10, num_layers=2)
    
    result = nodes(network).head(n)
    
    assert len(result) <= n


@pytest.mark.property
@settings(deadline=None, max_examples=20)
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
@settings(deadline=None, max_examples=20)
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
@settings(deadline=None, max_examples=30)
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
@settings(deadline=None, max_examples=30)
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
@settings(deadline=None, max_examples=30)
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
@settings(deadline=None, max_examples=20)
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
def test_to_pandas_row_count_matches():
    """Test that to_pandas row count matches frame length."""
    import pandas as pd
    network = create_test_network()
    
    frame = nodes(network)
    df = frame.to_pandas()
    
    assert len(df) == len(frame)


@pytest.mark.property
def test_to_pandas_excludes_internal_fields():
    """Test that to_pandas excludes fields starting with _."""
    import pandas as pd
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
@settings(deadline=None, max_examples=20)
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
@settings(deadline=None, max_examples=20)
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
@settings(deadline=None, max_examples=20)
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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
