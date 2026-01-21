#!/usr/bin/env python3
"""
Property-based tests for compositional uncertainty quantification.

Tests invariants for:
- Aggregate operations with UQ
- Ranking stability with UQ
- Coverage operations with UQ
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

def create_test_network(num_nodes=10, num_layers=2, seed=42):
    """Create a simple test multilayer network."""
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
# Property Tests: Aggregate with UQ
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n_samples=st.integers(min_value=3, max_value=10),
    seed=st.integers(min_value=1, max_value=1000)
)
def test_aggregate_uq_produces_dict_with_stats(n_samples, seed):
    """
    Property: Aggregate with UQ produces dict with mean, std, quantiles.
    
    All aggregate results should have uncertainty structure.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=seed)
    
    result = (
        Q.nodes()
         .compute("degree")
         .summarize(mean_degree="mean(degree)")
         .uq(method="bootstrap", n_samples=n_samples, seed=seed)
         .execute(network)
    )
    
    # Check structure
    assert len(result.items) == 1
    assert "mean_degree" in result.attributes
    
    # Check uncertainty structure
    val = result.attributes["mean_degree"][result.items[0]]
    assert isinstance(val, dict)
    assert "mean" in val
    assert "std" in val
    assert "quantiles" in val
    assert "n_samples" in val
    assert val["n_samples"] == n_samples


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    seed=st.integers(min_value=1, max_value=1000)
)
def test_aggregate_uq_std_non_negative(seed):
    """
    Property: Standard deviation in aggregate UQ is non-negative.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=seed)
    
    result = (
        Q.nodes()
         .compute("degree")
         .summarize(mean_degree="mean(degree)")
         .uq(method="bootstrap", n_samples=5, seed=seed)
         .execute(network)
    )
    
    val = result.attributes["mean_degree"][result.items[0]]
    assert val["std"] >= 0


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    seed=st.integers(min_value=1, max_value=1000)
)
def test_aggregate_uq_ci_ordered(seed):
    """
    Property: Confidence interval bounds are properly ordered.
    
    Lower quantile should be <= mean <= upper quantile.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=seed)
    
    result = (
        Q.nodes()
         .compute("degree")
         .summarize(mean_degree="mean(degree)")
         .uq(method="bootstrap", n_samples=5, ci=0.95, seed=seed)
         .execute(network)
    )
    
    val = result.attributes["mean_degree"][result.items[0]]
    quantiles = val["quantiles"]
    
    # Check that quantiles exist and are ordered
    if len(quantiles) >= 2:
        q_vals = sorted(quantiles.values())
        # Lower quantile <= mean <= upper quantile (with some tolerance)
        assert q_vals[0] <= val["mean"] + 1e-6
        assert val["mean"] <= q_vals[-1] + 1e-6


# ============================================================================
# Property Tests: Per-layer aggregate with UQ
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    num_layers=st.integers(min_value=2, max_value=3),
    seed=st.integers(min_value=1, max_value=1000)
)
def test_per_layer_aggregate_uq_group_count(num_layers, seed):
    """
    Property: Per-layer aggregate produces one result per layer.
    """
    network = create_test_network(num_nodes=5, num_layers=num_layers, seed=seed)
    
    result = (
        Q.nodes()
         .compute("degree")
         .per_layer()
         .aggregate(mean_degree="mean(degree)")
         .uq(method="bootstrap", n_samples=5, seed=seed)
         .execute(network)
    )
    
    # Should have one item per layer
    assert len(result.items) == num_layers


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    seed=st.integers(min_value=1, max_value=1000)
)
def test_per_layer_aggregate_uq_all_groups_have_uncertainty(seed):
    """
    Property: All groups in per-layer aggregate have uncertainty.
    """
    network = create_test_network(num_nodes=5, num_layers=3, seed=seed)
    
    result = (
        Q.nodes()
         .compute("degree")
         .per_layer()
         .aggregate(mean_degree="mean(degree)")
         .uq(method="bootstrap", n_samples=5, seed=seed)
         .execute(network)
    )
    
    # Check all groups have uncertainty structure
    for item in result.items:
        val = result.attributes["mean_degree"][item]
        assert isinstance(val, dict)
        assert "mean" in val
        assert "std" in val


# ============================================================================
# Property Tests: Ranking stability with UQ
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    top_k=st.integers(min_value=3, max_value=7),
    seed=st.integers(min_value=1, max_value=1000)
)
def test_ranking_uq_respects_limit(top_k, seed):
    """
    Property: Ranking with UQ respects the limit parameter.
    
    Result should contain at most top_k items.
    """
    network = create_test_network(num_nodes=10, num_layers=1, seed=seed)
    
    result = (
        Q.nodes()
         .compute("degree")
         .order_by("-degree")
         .limit(top_k)
         .uq(method="perturbation", n_samples=5, seed=seed)  # Use perturbation, not bootstrap
         .execute(network)
    )
    
    # Result should have at most top_k items
    assert len(result.items) <= top_k


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    seed=st.integers(min_value=1, max_value=1000)
)
def test_ranking_uq_has_stability_metadata(seed):
    """
    Property: Ranking with UQ includes stability metadata or attributes.
    """
    network = create_test_network(num_nodes=10, num_layers=1, seed=seed)
    
    result = (
        Q.nodes()
         .compute("degree")
         .order_by("-degree")
         .limit(5)
         .uq(method="perturbation", n_samples=5, seed=seed)  # Use perturbation
         .execute(network)
    )
    
    # Check for UQ metadata or ranking attributes
    has_uq = "uq" in result.meta
    has_rank_attrs = "rank_mean" in result.attributes or "present_prob" in result.attributes
    assert has_uq or has_rank_attrs


# ============================================================================
# Property Tests: Determinism
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    seed=st.integers(min_value=1, max_value=1000)
)
def test_same_seed_same_uq_results(seed):
    """
    Property: Same seed produces identical UQ results.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=seed)
    
    result1 = (
        Q.nodes()
         .compute("degree")
         .summarize(mean_degree="mean(degree)")
         .uq(method="bootstrap", n_samples=5, seed=seed)
         .execute(network)
    )
    
    result2 = (
        Q.nodes()
         .compute("degree")
         .summarize(mean_degree="mean(degree)")
         .uq(method="bootstrap", n_samples=5, seed=seed)
         .execute(network)
    )
    
    val1 = result1.attributes["mean_degree"][result1.items[0]]
    val2 = result2.attributes["mean_degree"][result2.items[0]]
    
    # Should be identical
    assert abs(val1["mean"] - val2["mean"]) < 1e-10
    assert abs(val1["std"] - val2["std"]) < 1e-10


# ============================================================================
# Property Tests: Backward compatibility
# ============================================================================

@pytest.mark.property
def test_non_uq_query_returns_scalar():
    """
    Property: Queries without UQ return scalar values, not dicts.
    
    Ensures backward compatibility.
    """
    network = create_test_network(num_nodes=5, num_layers=2, seed=42)
    
    result = (
        Q.nodes()
         .compute("degree")
         .summarize(mean_degree="mean(degree)")
         .execute(network)
    )
    
    val = result.attributes["mean_degree"][result.items[0]]
    # Should be scalar or dict without UQ structure
    if isinstance(val, dict):
        assert "mean" not in val or "std" not in val
    else:
        assert isinstance(val, (int, float))
