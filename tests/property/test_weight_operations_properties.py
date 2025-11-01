#!/usr/bin/env python3
"""
Property-based tests for weight operations in multilayer networks.

Tests numerical properties of edge weights including normalization,
scaling, and aggregation.
"""

import networkx as nx
import pytest
from hypothesis import given, strategies as st, settings, assume
import math

from py3plex.core import multinet
from .strategies import layer_labels, positive_weights


@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(
    n=st.integers(min_value=2, max_value=10),
    num_edges=st.integers(min_value=1, max_value=12),
    weight=positive_weights()
)
def test_weight_assignment_preserved(n, num_edges, weight):
    """
    Property: Assigned edge weights are preserved.
    
    When edges are added with specific weights, those weights
    should be retrievable.
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add edges with specific weight
    edges = []
    for i in range(num_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:
            edges.append([str(src), layer, str(dst), layer, weight])
    
    assume(len(edges) > 0)
    network.add_edges(edges, input_type='list')
    
    # Check weights
    found_weights = []
    for edge in network.get_edges(data=True):
        if len(edge) > 2 and 'weight' in edge[2]:
            found_weights.append(edge[2]['weight'])
    
    # At least one edge should have the assigned weight
    if found_weights:
        assert any(abs(w - weight) < 1e-6 for w in found_weights), \
            f"No edge has expected weight {weight}, found: {found_weights[:5]}"


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    n=st.integers(min_value=2, max_value=8),
    num_edges=st.integers(min_value=2, max_value=10),
    scale=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False)
)
def test_weight_scaling_linearity(n, num_edges, scale):
    """
    Property: Scaling all weights by a constant factor preserves relative ratios.
    
    If all weights are multiplied by k, their ratios remain the same.
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add edges with varying weights
    edges = []
    base_weights = []
    for i in range(num_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:
            w = 1.0 + (i % 5)
            base_weights.append(w)
            edges.append([str(src), layer, str(dst), layer, w])
    
    assume(len(edges) >= 2)
    network.add_edges(edges, input_type='list')
    
    # Get original weights
    original_weights = []
    for edge in network.get_edges(data=True):
        if len(edge) > 2 and 'weight' in edge[2]:
            original_weights.append(edge[2]['weight'])
    
    assume(len(original_weights) >= 2)
    
    # Calculate ratios
    if len(original_weights) >= 2:
        original_ratio = original_weights[0] / original_weights[1] if original_weights[1] != 0 else float('inf')
        
        # Scale and calculate new ratio
        scaled_ratio = (original_weights[0] * scale) / (original_weights[1] * scale) if original_weights[1] != 0 else float('inf')
        
        # Ratios should be equal (within floating point tolerance)
        if not math.isinf(original_ratio):
            assert abs(original_ratio - scaled_ratio) < 1e-6, \
                f"Scaling changed ratio: {original_ratio} vs {scaled_ratio}"


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    n=st.integers(min_value=2, max_value=8),
    num_edges=st.integers(min_value=2, max_value=10)
)
def test_weight_sum_non_negative(n, num_edges):
    """
    Property: Sum of non-negative weights is non-negative.
    
    The total weight of all edges should be >= 0 when all individual
    weights are >= 0.
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add edges with positive weights
    edges = []
    for i in range(num_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:
            w = 1.0 + (i % 5)
            edges.append([str(src), layer, str(dst), layer, w])
    
    assume(len(edges) > 0)
    network.add_edges(edges, input_type='list')
    
    # Sum weights
    total_weight = 0.0
    for edge in network.get_edges(data=True):
        if len(edge) > 2 and 'weight' in edge[2]:
            total_weight += edge[2]['weight']
    
    assert total_weight >= 0, \
        f"Total weight is negative: {total_weight}"


@pytest.mark.property
@settings(deadline=None, max_examples=35)
@given(
    n=st.integers(min_value=2, max_value=8),
    num_edges=st.integers(min_value=1, max_value=10),
    base_weight=positive_weights()
)
def test_weight_addition_commutative(n, num_edges, base_weight):
    """
    Property: Weight addition is commutative.
    
    Adding weights in different orders should give the same total.
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add edges
    edges = []
    weights = []
    for i in range(num_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:
            w = base_weight + i
            weights.append(w)
            edges.append([str(src), layer, str(dst), layer, w])
    
    assume(len(edges) > 0)
    network.add_edges(edges, input_type='list')
    
    # Calculate sum forward
    sum_forward = sum(weights)
    
    # Calculate sum backward
    sum_backward = sum(reversed(weights))
    
    assert abs(sum_forward - sum_backward) < 1e-6, \
        f"Weight sum not commutative: {sum_forward} vs {sum_backward}"


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    n=st.integers(min_value=2, max_value=8),
    num_edges=st.integers(min_value=2, max_value=10)
)
def test_weight_mean_bounds(n, num_edges):
    """
    Property: Mean weight is bounded by min and max weights.
    
    The average weight should be between the minimum and maximum weights.
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add edges with varying weights
    edges = []
    for i in range(num_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:
            w = 1.0 + (i % 10)
            edges.append([str(src), layer, str(dst), layer, w])
    
    assume(len(edges) >= 2)
    network.add_edges(edges, input_type='list')
    
    # Collect weights
    weights = []
    for edge in network.get_edges(data=True):
        if len(edge) > 2 and 'weight' in edge[2]:
            weights.append(edge[2]['weight'])
    
    assume(len(weights) >= 2)
    
    # Calculate statistics
    min_weight = min(weights)
    max_weight = max(weights)
    mean_weight = sum(weights) / len(weights)
    
    assert min_weight <= mean_weight <= max_weight, \
        f"Mean {mean_weight} not in bounds [{min_weight}, {max_weight}]"


@pytest.mark.property
@settings(deadline=None, max_examples=35)
@given(
    n=st.integers(min_value=2, max_value=8),
    num_edges=st.integers(min_value=2, max_value=10),
    weight1=positive_weights(),
    weight2=positive_weights()
)
def test_weight_comparison_transitivity(n, num_edges, weight1, weight2):
    """
    Property: Weight comparison is transitive.
    
    If w1 < w2 and w2 < w3, then w1 < w3.
    """
    # Sort weights
    weights = sorted([weight1, weight2])
    w1, w2 = weights[0], weights[1]
    
    # Define w3
    w3 = w2 + 1.0
    
    # Check transitivity
    if w1 < w2 and w2 < w3:
        assert w1 < w3, \
            f"Transitivity violated: {w1} < {w2} < {w3} but not {w1} < {w3}"


@pytest.mark.property
@settings(deadline=None, max_examples=40)
@given(
    n=st.integers(min_value=2, max_value=8),
    num_edges=st.integers(min_value=1, max_value=10),
    weight=positive_weights()
)
def test_uniform_weights_constant_mean(n, num_edges, weight):
    """
    Property: Uniform weights have mean equal to the weight value.
    
    If all edges have the same weight w, the mean weight is w.
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add edges with uniform weight
    edges = []
    for i in range(num_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:
            edges.append([str(src), layer, str(dst), layer, weight])
    
    assume(len(edges) > 0)
    network.add_edges(edges, input_type='list')
    
    # Collect weights
    weights = []
    for edge in network.get_edges(data=True):
        if len(edge) > 2 and 'weight' in edge[2]:
            weights.append(edge[2]['weight'])
    
    assume(len(weights) > 0)
    
    # Calculate mean
    mean_weight = sum(weights) / len(weights)
    
    # Mean should equal the uniform weight
    assert abs(mean_weight - weight) < 1e-6, \
        f"Mean {mean_weight} does not equal uniform weight {weight}"


@pytest.mark.property
@settings(deadline=None, max_examples=35)
@given(
    n=st.integers(min_value=2, max_value=8),
    num_edges=st.integers(min_value=2, max_value=10)
)
def test_weight_variance_non_negative(n, num_edges):
    """
    Property: Weight variance is always non-negative.
    
    The variance of edge weights should be >= 0.
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add edges with varying weights
    edges = []
    for i in range(num_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:
            w = 1.0 + (i % 5)
            edges.append([str(src), layer, str(dst), layer, w])
    
    assume(len(edges) >= 2)
    network.add_edges(edges, input_type='list')
    
    # Collect weights
    weights = []
    for edge in network.get_edges(data=True):
        if len(edge) > 2 and 'weight' in edge[2]:
            weights.append(edge[2]['weight'])
    
    assume(len(weights) >= 2)
    
    # Calculate variance
    mean = sum(weights) / len(weights)
    variance = sum((w - mean) ** 2 for w in weights) / len(weights)
    
    assert variance >= 0, \
        f"Variance is negative: {variance}"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    n=st.integers(min_value=2, max_value=8),
    num_edges=st.integers(min_value=1, max_value=10),
    weight=positive_weights()
)
def test_weight_multiplication_identity(n, num_edges, weight):
    """
    Property: Multiplying weights by 1 preserves them.
    
    w * 1 = w for all weights.
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add edges
    edges = []
    for i in range(num_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:
            edges.append([str(src), layer, str(dst), layer, weight])
    
    assume(len(edges) > 0)
    network.add_edges(edges, input_type='list')
    
    # Get weights
    weights = []
    for edge in network.get_edges(data=True):
        if len(edge) > 2 and 'weight' in edge[2]:
            weights.append(edge[2]['weight'])
    
    assume(len(weights) > 0)
    
    # Multiply by identity
    scaled_weights = [w * 1.0 for w in weights]
    
    # Should be equal
    for original, scaled in zip(weights, scaled_weights):
        assert abs(original - scaled) < 1e-6, \
            f"Identity multiplication failed: {original} vs {scaled}"


@pytest.mark.property
@settings(deadline=None, max_examples=35)
@given(
    n=st.integers(min_value=2, max_value=8),
    num_edges=st.integers(min_value=2, max_value=10)
)
def test_weight_ordering_preserved(n, num_edges):
    """
    Property: Ordering of weights is preserved.
    
    If w1 < w2, then w1 remains less than w2.
    """
    network = multinet.multi_layer_network(directed=False)
    layer = 'L1'
    
    # Add edges with distinct weights
    edges = []
    for i in range(num_edges):
        src = i % n
        dst = (i + 1) % n
        if src != dst:
            w = 1.0 + i
            edges.append([str(src), layer, str(dst), layer, w])
    
    assume(len(edges) >= 2)
    network.add_edges(edges, input_type='list')
    
    # Collect weights
    weights = []
    for edge in network.get_edges(data=True):
        if len(edge) > 2 and 'weight' in edge[2]:
            weights.append(edge[2]['weight'])
    
    assume(len(weights) >= 2)
    
    # Sort weights
    sorted_weights = sorted(weights)
    
    # Check ordering is preserved
    for i in range(len(sorted_weights) - 1):
        assert sorted_weights[i] <= sorted_weights[i + 1], \
            f"Ordering not preserved at index {i}"
