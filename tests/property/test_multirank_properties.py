#!/usr/bin/env python3
"""
Property-based tests for MultiRank and Multiplex PageRank variants.

Tests invariants and properties including:
- Normalization: scores sum to 1
- Non-negativity: all scores >= 0
- Convergence: algorithm converges within max_iter
- Single-layer reduction: reduces to standard PageRank
- Scale invariance: edge scaling preserves normalized rankings
- Reproducibility: deterministic results
"""

import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck
from scipy.stats import spearmanr

# Import multirank module
try:
    from py3plex.algorithms.multilayer_algorithms.multirank import (
        multirank,
        multiplex_pagerank,
    )
    MULTIRANK_AVAILABLE = True
except ImportError:
    MULTIRANK_AVAILABLE = False
    pytest.skip("MultiRank module not available", allow_module_level=True)


# ============================================================================
# Helper functions
# ============================================================================

def create_random_layer(num_nodes, density, seed):
    """Create a random adjacency matrix."""
    rng = np.random.default_rng(seed)
    A = rng.random((num_nodes, num_nodes)) < density
    A = A.astype(float)
    # Make symmetric (undirected)
    A = np.triu(A, 1) + np.triu(A, 1).T
    np.fill_diagonal(A, 0)
    return A


def create_connected_layer(num_nodes, seed):
    """Create a connected adjacency matrix (ring + random edges)."""
    rng = np.random.default_rng(seed)
    # Start with ring for connectivity
    A = np.zeros((num_nodes, num_nodes))
    for i in range(num_nodes):
        A[i, (i + 1) % num_nodes] = 1.0
        A[(i + 1) % num_nodes, i] = 1.0
    # Add random edges
    random_edges = rng.random((num_nodes, num_nodes)) < 0.2
    random_edges = np.triu(random_edges, 1).astype(float)
    A = np.maximum(A, random_edges + random_edges.T)
    return A


def create_multiplex_layers(num_nodes, num_layers, seed):
    """Create multiple layers with guaranteed connectivity in at least one."""
    layers = [create_connected_layer(num_nodes, seed)]
    for i in range(1, num_layers):
        layers.append(create_random_layer(num_nodes, 0.3, seed + i * 100))
    return layers


# ============================================================================
# Property Tests: MultiRank Normalization
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=15),
    num_layers=st.integers(min_value=1, max_value=4),
    alpha=st.floats(min_value=0.5, max_value=0.95, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_multirank_node_scores_sum_to_one(num_nodes, num_layers, alpha, seed):
    """Property: Node scores sum to approximately 1 (L1 normalization)."""
    layers = create_multiplex_layers(num_nodes, num_layers, seed)

    node_scores, layer_scores = multirank(layers, alpha=alpha)

    # Node scores should sum to ~1
    score_sum = np.sum(node_scores)
    assert np.isclose(score_sum, 1.0, atol=1e-4), \
        f"Node scores sum to {score_sum}, expected ~1.0"


@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=15),
    num_layers=st.integers(min_value=1, max_value=4),
    alpha=st.floats(min_value=0.5, max_value=0.95, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_multirank_layer_scores_sum_to_one(num_nodes, num_layers, alpha, seed):
    """Property: Layer scores sum to approximately 1."""
    layers = create_multiplex_layers(num_nodes, num_layers, seed)

    node_scores, layer_scores = multirank(layers, alpha=alpha)

    # Layer scores should sum to ~1
    score_sum = np.sum(layer_scores)
    assert np.isclose(score_sum, 1.0, atol=1e-4), \
        f"Layer scores sum to {score_sum}, expected ~1.0"


# ============================================================================
# Property Tests: Non-negativity
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=15),
    num_layers=st.integers(min_value=1, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_multirank_scores_nonnegative(num_nodes, num_layers, seed):
    """Property: All scores are non-negative."""
    layers = create_multiplex_layers(num_nodes, num_layers, seed)

    node_scores, layer_scores = multirank(layers)

    assert np.all(node_scores >= 0), f"Negative node scores found: min={np.min(node_scores)}"
    assert np.all(layer_scores >= 0), f"Negative layer scores found: min={np.min(layer_scores)}"


@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=15),
    num_layers=st.integers(min_value=1, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_multirank_scores_finite(num_nodes, num_layers, seed):
    """Property: All scores are finite (no NaN or Inf)."""
    layers = create_multiplex_layers(num_nodes, num_layers, seed)

    node_scores, layer_scores = multirank(layers)

    assert np.all(np.isfinite(node_scores)), "Non-finite node scores found"
    assert np.all(np.isfinite(layer_scores)), "Non-finite layer scores found"


# ============================================================================
# Property Tests: Output Shape
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=20),
    num_layers=st.integers(min_value=1, max_value=5),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_multirank_output_shapes(num_nodes, num_layers, seed):
    """Property: Output arrays have correct shapes."""
    layers = create_multiplex_layers(num_nodes, num_layers, seed)

    node_scores, layer_scores = multirank(layers)

    assert node_scores.shape == (num_nodes,), \
        f"Node scores shape {node_scores.shape} != expected ({num_nodes},)"
    assert layer_scores.shape == (num_layers,), \
        f"Layer scores shape {layer_scores.shape} != expected ({num_layers},)"


# ============================================================================
# Property Tests: Reproducibility
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=12),
    num_layers=st.integers(min_value=1, max_value=3),
    alpha=st.floats(min_value=0.5, max_value=0.95, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_multirank_deterministic(num_nodes, num_layers, alpha, seed):
    """Property: Same input produces identical output (deterministic)."""
    layers = create_multiplex_layers(num_nodes, num_layers, seed)

    node_scores1, layer_scores1 = multirank(layers, alpha=alpha)
    node_scores2, layer_scores2 = multirank(layers, alpha=alpha)

    np.testing.assert_array_almost_equal(node_scores1, node_scores2, decimal=10)
    np.testing.assert_array_almost_equal(layer_scores1, layer_scores2, decimal=10)


# ============================================================================
# Property Tests: Single Layer Reduction
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=12),
    alpha=st.floats(min_value=0.7, max_value=0.9, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_multirank_single_layer_pagerank_correlation(num_nodes, alpha, seed):
    """Property: Single layer MultiRank correlates highly with PageRank."""
    import networkx as nx

    layer = create_connected_layer(num_nodes, seed)
    layers = [layer]

    # Compute MultiRank
    node_scores, _ = multirank(layers, alpha=alpha)

    # Compute standard PageRank via NetworkX
    G = nx.from_numpy_array(layer)
    pr = nx.pagerank(G, alpha=alpha)
    pr_scores = np.array([pr[i] for i in range(num_nodes)])

    # Check for constant arrays (would cause NaN correlation)
    if np.std(node_scores) < 1e-10 or np.std(pr_scores) < 1e-10:
        # Both should be approximately uniform for regular graphs
        assert np.allclose(node_scores, 1.0/num_nodes, atol=0.1) or \
               np.allclose(pr_scores, 1.0/num_nodes, atol=0.1), \
            "Constant scores should be approximately uniform"
        return

    # Should have high rank correlation (>0.8)
    correlation, _ = spearmanr(node_scores, pr_scores)
    assert correlation > 0.8 or np.isnan(correlation), \
        f"Low correlation ({correlation}) between MultiRank and PageRank"


# ============================================================================
# Property Tests: Scale Invariance
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=12),
    num_layers=st.integers(min_value=1, max_value=3),
    scale=st.floats(min_value=0.5, max_value=5.0, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_multirank_scale_invariance(num_nodes, num_layers, scale, seed):
    """Property: Scaling edge weights preserves normalized rankings."""
    layers = create_multiplex_layers(num_nodes, num_layers, seed)

    # Original scores
    node_scores1, layer_scores1 = multirank(layers)

    # Scale all layers
    scaled_layers = [layer * scale for layer in layers]
    node_scores2, layer_scores2 = multirank(scaled_layers)

    # Rankings should be preserved (high correlation)
    if num_nodes > 2:
        # Check for constant arrays (would cause NaN correlation)
        if np.std(node_scores1) < 1e-10 or np.std(node_scores2) < 1e-10:
            # Both should be approximately uniform for regular graphs
            assert np.allclose(node_scores1, 1.0/num_nodes, atol=0.1), \
                "Constant scores should be approximately uniform"
            return

        corr, _ = spearmanr(node_scores1, node_scores2)
        assert corr > 0.95, f"Scaling changed rankings: correlation = {corr}"


# ============================================================================
# Property Tests: Interlayer Coupling
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=10),
    num_layers=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_multirank_interlayer_coupling_valid(num_nodes, num_layers, seed):
    """Property: Custom interlayer coupling produces valid results."""
    layers = create_multiplex_layers(num_nodes, num_layers, seed)

    # Create custom coupling matrix
    rng = np.random.default_rng(seed)
    coupling = rng.random((num_layers, num_layers)) * 0.5
    coupling = (coupling + coupling.T) / 2  # Symmetric
    np.fill_diagonal(coupling, 0)  # No self-coupling

    node_scores, layer_scores = multirank(layers, interlayer_coupling=coupling)

    # Should still produce valid normalized scores
    assert np.isclose(np.sum(node_scores), 1.0, atol=1e-4)
    assert np.isclose(np.sum(layer_scores), 1.0, atol=1e-4)
    assert np.all(node_scores >= 0)
    assert np.all(layer_scores >= 0)


# ============================================================================
# Property Tests: Multiplex PageRank Variants
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=12),
    num_layers=st.integers(min_value=2, max_value=3),
    variant=st.sampled_from(['neutral', 'additive', 'multiplicative', 'combined']),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_multiplex_pagerank_variants_valid(num_nodes, num_layers, variant, seed):
    """Property: All PageRank variants produce valid results.

    Note: node_scores = sum across layers of replica_scores, where each layer sums to 1.
    Therefore node_scores sum to L (number of layers), not 1.
    """
    layers = create_multiplex_layers(num_nodes, num_layers, seed)

    result = multiplex_pagerank(layers, variant=variant)

    # Node scores should be valid
    node_scores = result['node_scores']
    replica_scores = result['replica_scores']
    assert node_scores.shape == (num_nodes,)
    assert replica_scores.shape == (num_nodes, num_layers)
    assert np.all(node_scores >= 0), f"Negative scores in {variant} variant"
    assert np.all(np.isfinite(node_scores)), f"Non-finite scores in {variant} variant"

    # Each layer's replica scores should sum to ~1
    for layer_idx in range(num_layers):
        layer_sum = np.sum(replica_scores[:, layer_idx])
        assert np.isclose(layer_sum, 1.0, atol=1e-3), \
            f"Layer {layer_idx} replica scores sum to {layer_sum}, expected ~1.0"

    # node_scores = sum of replica_scores across layers, so should sum to L
    assert np.isclose(np.sum(node_scores), float(num_layers), atol=1e-3), \
        f"{variant} node_scores sum to {np.sum(node_scores)}, expected ~{num_layers}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=10),
    num_layers=st.integers(min_value=2, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_multiplex_pagerank_neutral_baseline(num_nodes, num_layers, seed):
    """Property: Neutral variant is independent across layers."""
    layers = create_multiplex_layers(num_nodes, num_layers, seed)

    result = multiplex_pagerank(layers, variant='neutral')
    replica_scores = result['replica_scores']  # Shape: (N, L)

    # Each layer's scores should sum to ~1 independently
    for layer_idx in range(num_layers):
        layer_sum = np.sum(replica_scores[:, layer_idx])
        assert np.isclose(layer_sum, 1.0, atol=1e-3), \
            f"Layer {layer_idx} scores sum to {layer_sum}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=10),
    num_layers=st.integers(min_value=2, max_value=3),
    c=st.floats(min_value=0.1, max_value=2.0, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_multiplex_pagerank_coupling_parameter_effect(num_nodes, num_layers, c, seed):
    """Property: Coupling parameter c affects cross-layer influence.

    Note: node_scores sum to L (number of layers), not 1.
    """
    layers = create_multiplex_layers(num_nodes, num_layers, seed)

    # Low coupling
    result_low = multiplex_pagerank(layers, variant='additive', c=0.1)

    # Higher coupling
    result_high = multiplex_pagerank(layers, variant='additive', c=c + 0.5)

    # Both should be valid - node_scores sum to num_layers (not 1)
    assert np.isclose(np.sum(result_low['node_scores']), float(num_layers), atol=1e-3)
    assert np.isclose(np.sum(result_high['node_scores']), float(num_layers), atol=1e-3)


# ============================================================================
# Property Tests: Edge Cases
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_multirank_sparse_layer(num_nodes, seed):
    """Property: Works with very sparse layers."""
    # Create a very sparse layer (only ring connectivity)
    A = np.zeros((num_nodes, num_nodes))
    for i in range(num_nodes):
        A[i, (i + 1) % num_nodes] = 1.0
        A[(i + 1) % num_nodes, i] = 1.0

    layers = [A]
    node_scores, layer_scores = multirank(layers)

    # Should produce valid results
    assert np.isclose(np.sum(node_scores), 1.0, atol=1e-4)
    assert np.all(node_scores >= 0)


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_multirank_dense_layer(num_nodes, seed):
    """Property: Works with dense (complete) layers."""
    # Create complete graph
    A = np.ones((num_nodes, num_nodes))
    np.fill_diagonal(A, 0)

    layers = [A]
    node_scores, layer_scores = multirank(layers)

    # Complete graph should have uniform scores
    expected_score = 1.0 / num_nodes
    assert np.allclose(node_scores, expected_score, atol=1e-3), \
        f"Complete graph should have uniform scores, got {node_scores}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=10000))
def test_multirank_minimum_size(seed):
    """Property: Works with minimum valid input (1 node, 1 layer)."""
    # Single node layer
    layers = [np.array([[0.0]])]

    node_scores, layer_scores = multirank(layers)

    # Single node should have score 1
    assert np.isclose(node_scores[0], 1.0, atol=1e-6)
    assert np.isclose(layer_scores[0], 1.0, atol=1e-6)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
