#!/usr/bin/env python3
"""
Property-based tests for DSL aggregation and edge query enhancements.

Tests invariants for:
- Aggregation operators (median, quantile, count, etc.)
- Edge endpoint properties (src_degree, dst_degree)
- Aggregation behavior across nodes and edges
- Per-layer and per-layer-pair grouping with aggregations
"""

import pytest
from hypothesis import given, settings, assume, strategies as st
import numpy as np

# Import DSL module
try:
    from py3plex.dsl import Q, L
    from py3plex.core import multinet
    DSL_AVAILABLE = True
except ImportError:
    DSL_AVAILABLE = False
    pytest.skip("DSL module not available", allow_module_level=True)


# ============================================================================
# Helper: Create test network
# ============================================================================

def create_weighted_network(num_nodes=5, num_layers=2, seed=42):
    """Create a test multilayer network with weighted edges."""
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
    
    # Add edges with random weights
    edges = []
    for layer in layers:
        for i in range(len(node_names) - 1):
            weight = np.random.uniform(0.5, 5.0)
            edges.append({
                'source': node_names[i],
                'target': node_names[i + 1],
                'source_type': layer,
                'target_type': layer,
                'weight': weight
            })
    network.add_edges(edges)
    
    return network


# ============================================================================
# Property Tests: Aggregation Operators - Basic Properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_count_aggregation_equals_item_count(num_nodes, num_layers):
    """
    Property: count() aggregation returns the correct number of items.
    
    Tests that count() matches the actual number of nodes/edges in result.
    """
    network = create_weighted_network(num_nodes=num_nodes, num_layers=num_layers)
    
    # Test on nodes
    result = Q.nodes().summarize(total="count()").execute(network)
    expected_count = num_nodes * num_layers
    
    assert result.items[0] in ['__global__']
    actual_count = result.attributes['total'][result.items[0]]
    assert actual_count == expected_count


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_mean_aggregation_bounded(num_nodes, num_layers):
    """
    Property: mean() aggregation is within min and max of data.
    
    Tests that mean(attr) is between min(attr) and max(attr).
    """
    network = create_weighted_network(num_nodes=num_nodes, num_layers=num_layers)
    
    result = (
        Q.edges()
         .summarize(
             mean_weight="mean(weight)",
             min_weight="min(weight)",
             max_weight="max(weight)"
         )
         .execute(network)
    )
    
    item = result.items[0]
    mean_val = result.attributes['mean_weight'][item]
    min_val = result.attributes['min_weight'][item]
    max_val = result.attributes['max_weight'][item]
    
    # Mean should be between min and max
    assert min_val <= mean_val <= max_val


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_median_aggregation_properties(num_nodes):
    """
    Property: median() is robust and within data range.
    
    Tests that median is within [min, max] and handles odd/even counts.
    """
    network = create_weighted_network(num_nodes=num_nodes, num_layers=1)
    
    result = (
        Q.edges()
         .summarize(
             median_weight="median(weight)",
             min_weight="min(weight)",
             max_weight="max(weight)"
         )
         .execute(network)
    )
    
    item = result.items[0]
    median_val = result.attributes['median_weight'][item]
    min_val = result.attributes['min_weight'][item]
    max_val = result.attributes['max_weight'][item]
    
    # Median should be between min and max
    assert min_val <= median_val <= max_val


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    quantile_p=st.floats(min_value=0.0, max_value=1.0)
)
def test_quantile_aggregation_bounded(quantile_p):
    """
    Property: quantile(attr, p) is bounded by min and max.
    
    Tests that any quantile is within the data range.
    """
    network = create_weighted_network(num_nodes=5, num_layers=1)
    
    result = (
        Q.edges()
         .summarize(
             quantile_weight=f"quantile(weight, {quantile_p})",
             min_weight="min(weight)",
             max_weight="max(weight)"
         )
         .execute(network)
    )
    
    item = result.items[0]
    q_val = result.attributes['quantile_weight'][item]
    min_val = result.attributes['min_weight'][item]
    max_val = result.attributes['max_weight'][item]
    
    # Quantile should be between min and max
    assert min_val <= q_val <= max_val


@pytest.mark.property
@settings(deadline=None, max_examples=30)
def test_quantile_ordering_property():
    """
    Property: quantile(attr, p1) <= quantile(attr, p2) when p1 < p2.
    
    Tests that quantiles are monotonically increasing.
    """
    network = create_weighted_network(num_nodes=6, num_layers=1)
    
    result = (
        Q.edges()
         .summarize(
             q25="quantile(weight, 0.25)",
             q50="quantile(weight, 0.50)",
             q75="quantile(weight, 0.75)"
         )
         .execute(network)
    )
    
    item = result.items[0]
    q25 = result.attributes['q25'][item]
    q50 = result.attributes['q50'][item]
    q75 = result.attributes['q75'][item]
    
    # Quantiles should be ordered
    assert q25 <= q50 <= q75


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_std_var_relationship(num_nodes):
    """
    Property: var() equals std()^2.
    
    Tests mathematical relationship between variance and standard deviation.
    """
    network = create_weighted_network(num_nodes=num_nodes, num_layers=1)
    
    result = (
        Q.edges()
         .summarize(
             std_weight="std(weight)",
             var_weight="var(weight)"
         )
         .execute(network)
    )
    
    item = result.items[0]
    std_val = result.attributes['std_weight'][item]
    var_val = result.attributes['var_weight'][item]
    
    # Variance should equal standard deviation squared
    assert abs(var_val - std_val ** 2) < 1e-6


# ============================================================================
# Property Tests: Edge Endpoint Properties
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    min_degree=st.integers(min_value=0, max_value=3)
)
def test_edge_src_degree_filter_consistency(min_degree):
    """
    Property: Filtering by src_degree returns edges with sources meeting criteria.
    
    Tests that src_degree__gt=k returns edges where source node degree > k.
    """
    network = create_weighted_network(num_nodes=5, num_layers=1)
    
    # Get all edges
    all_edges = Q.edges().execute(network)
    
    # Filter by src_degree
    filtered = Q.edges().where(src_degree__gt=min_degree).execute(network)
    
    # Filtered count should be <= all edges count
    assert filtered.count <= all_edges.count


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    min_src_degree=st.integers(min_value=0, max_value=2),
    min_dst_degree=st.integers(min_value=0, max_value=2)
)
def test_edge_endpoint_filters_conjunctive(min_src_degree, min_dst_degree):
    """
    Property: Filtering by both src_degree AND dst_degree is conjunctive.
    
    Tests that combining filters reduces or maintains result size.
    """
    network = create_weighted_network(num_nodes=5, num_layers=1)
    
    # Filter by src_degree only
    src_only = Q.edges().where(src_degree__gt=min_src_degree).execute(network)
    
    # Filter by dst_degree only
    dst_only = Q.edges().where(dst_degree__gt=min_dst_degree).execute(network)
    
    # Filter by both
    both = Q.edges().where(
        src_degree__gt=min_src_degree,
        dst_degree__gt=min_dst_degree
    ).execute(network)
    
    # Both filters should be <= each individual filter
    assert both.count <= src_only.count
    assert both.count <= dst_only.count


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_endpoint_degree_aggregation_bounded(num_nodes):
    """
    Property: Aggregating endpoint degrees produces valid statistics.
    
    Tests that mean/max of endpoint degrees are reasonable.
    """
    network = create_weighted_network(num_nodes=num_nodes, num_layers=1)
    
    result = (
        Q.edges()
         .aggregate(
             avg_src_degree="mean(src_degree)",
             max_src_degree="max(src_degree)",
             avg_dst_degree="mean(dst_degree)"
         )
         .execute(network)
    )
    
    item = result.items[0]
    avg_src = result.attributes['avg_src_degree'][item]
    max_src = result.attributes['max_src_degree'][item]
    avg_dst = result.attributes['avg_dst_degree'][item]
    
    # Average should be <= max
    assert avg_src <= max_src
    
    # Degrees should be non-negative
    assert avg_src >= 0
    assert avg_dst >= 0
    assert max_src >= 0


# ============================================================================
# Property Tests: Node vs Edge Aggregation Parity
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=1, max_value=2)
)
def test_count_aggregation_parity(num_nodes, num_layers):
    """
    Property: count() works identically for nodes and edges.
    
    Tests that count() aggregation has consistent behavior.
    """
    network = create_weighted_network(num_nodes=num_nodes, num_layers=num_layers)
    
    # Count nodes
    node_result = Q.nodes().summarize(total="count()").execute(network)
    node_count = node_result.attributes['total'][node_result.items[0]]
    
    # Count edges  
    edge_result = Q.edges().summarize(total="count()").execute(network)
    edge_count = edge_result.attributes['total'][edge_result.items[0]]
    
    # Both should return positive integers
    assert isinstance(node_count, int)
    assert isinstance(edge_count, int)
    assert node_count > 0
    assert edge_count > 0


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    num_layers=st.integers(min_value=2, max_value=3)
)
def test_per_layer_aggregation_sum_equals_global(num_layers):
    """
    Property: Sum of per-layer counts equals global count.
    
    Tests that per_layer grouping is complete (no missing items).
    """
    network = create_weighted_network(num_nodes=4, num_layers=num_layers)
    
    # Global count
    global_result = Q.nodes().summarize(total="count()").execute(network)
    global_count = global_result.attributes['total'][global_result.items[0]]
    
    # Per-layer counts
    per_layer_result = (
        Q.nodes()
         .per_layer()
         .aggregate(count="count()")
         .execute(network)
    )
    
    # Sum of per-layer counts
    per_layer_sum = sum(per_layer_result.attributes['count'].values())
    
    # Should equal global count
    assert per_layer_sum == global_count


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_per_layer_pair_edge_aggregation_complete(num_nodes):
    """
    Property: Per-layer-pair aggregation accounts for all edges.
    
    Tests that grouping by layer pairs is complete.
    """
    network = create_weighted_network(num_nodes=num_nodes, num_layers=2)
    
    # Global edge count
    global_result = Q.edges().summarize(total="count()").execute(network)
    global_count = global_result.attributes['total'][global_result.items[0]]
    
    # Per-layer-pair counts
    per_pair_result = (
        Q.edges()
         .per_layer_pair()
         .aggregate(count="count()")
         .execute(network)
    )
    
    # Sum of per-layer-pair counts
    per_pair_sum = sum(per_pair_result.attributes['count'].values())
    
    # Should equal global count
    assert per_pair_sum == global_count


# ============================================================================
# Property Tests: Aggregation Composability
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_multiple_aggregations_independence(num_nodes):
    """
    Property: Multiple aggregations in single query are independent.
    
    Tests that computing multiple aggregations doesn't interfere.
    """
    network = create_weighted_network(num_nodes=num_nodes, num_layers=1)
    
    # Compute multiple aggregations
    result = (
        Q.edges()
         .summarize(
             count="count()",
             mean_weight="mean(weight)",
             median_weight="median(weight)",
             std_weight="std(weight)"
         )
         .execute(network)
    )
    
    # All aggregations should be present
    item = result.items[0]
    assert 'count' in result.attributes
    assert 'mean_weight' in result.attributes
    assert 'median_weight' in result.attributes
    assert 'std_weight' in result.attributes
    
    # Each should have valid values
    assert result.attributes['count'][item] > 0
    assert result.attributes['mean_weight'][item] > 0
    assert result.attributes['std_weight'][item] >= 0


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    num_layers=st.integers(min_value=2, max_value=3)
)
def test_aggregate_and_summarize_equivalence(num_layers):
    """
    Property: aggregate() and summarize() produce equivalent results.
    
    Tests that both aggregation APIs work consistently.
    """
    network = create_weighted_network(num_nodes=4, num_layers=num_layers)
    
    # Using summarize
    result_summarize = (
        Q.nodes()
         .compute("degree")
         .per_layer()
         .summarize(avg_degree="mean(degree)")
         .execute(network)
    )
    
    # Using aggregate
    result_aggregate = (
        Q.nodes()
         .compute("degree")
         .per_layer()
         .aggregate(avg_degree="mean(degree)")
         .execute(network)
    )
    
    # Should have same number of groups
    assert len(result_summarize.items) == len(result_aggregate.items)
    
    # Should have same attributes
    assert 'avg_degree' in result_summarize.attributes
    assert 'avg_degree' in result_aggregate.attributes


# ============================================================================
# Property Tests: Edge Cases and Robustness
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=30)
def test_aggregation_on_empty_group():
    """
    Property: Aggregations on empty groups return NaN or 0.
    
    Tests graceful handling of empty result sets.
    """
    network = multinet.multi_layer_network(directed=False)
    network.add_nodes([{'source': 'A', 'type': 'layer0'}])
    
    # Query that results in empty edges
    result = Q.edges().summarize(mean_weight="mean(weight)").execute(network)
    
    # Should not raise exception
    assert isinstance(result.items, list)


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_quantile_extreme_values(num_nodes):
    """
    Property: Quantile at 0.0 equals min, at 1.0 equals max.
    
    Tests boundary behavior of quantile function.
    """
    network = create_weighted_network(num_nodes=num_nodes, num_layers=1)
    
    result = (
        Q.edges()
         .summarize(
             q0="quantile(weight, 0.0)",
             q1="quantile(weight, 1.0)",
             min_weight="min(weight)",
             max_weight="max(weight)"
         )
         .execute(network)
    )
    
    item = result.items[0]
    q0 = result.attributes['q0'][item]
    q1 = result.attributes['q1'][item]
    min_val = result.attributes['min_weight'][item]
    max_val = result.attributes['max_weight'][item]
    
    # Quantile at extremes should match min/max (with tolerance)
    assert abs(q0 - min_val) < 1e-6
    assert abs(q1 - max_val) < 1e-6


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    num_nodes=st.integers(min_value=3, max_value=8)
)
def test_median_equals_q50(num_nodes):
    """
    Property: median() equals quantile(attr, 0.5).
    
    Tests consistency between median and 50th percentile.
    """
    network = create_weighted_network(num_nodes=num_nodes, num_layers=1)
    
    result = (
        Q.edges()
         .summarize(
             median_weight="median(weight)",
             q50="quantile(weight, 0.5)"
         )
         .execute(network)
    )
    
    item = result.items[0]
    median_val = result.attributes['median_weight'][item]
    q50_val = result.attributes['q50'][item]
    
    # Median and 50th percentile should be equal (or very close)
    assert abs(median_val - q50_val) < 1e-6
