#!/usr/bin/env python3
"""
Property-based tests for supra-adjacency matrix function centralities.

Tests invariants and properties for:
- Communicability centrality
- Katz centrality

Properties tested:
- Non-negativity: all centrality values >= 0
- Finiteness: no NaN or Inf values
- Normalization: normalized values sum to 1
- Alpha bounds for Katz: alpha must be < 1/lambda_max
- Scale invariance: normalized rankings preserved under scaling
- Output shape: correct dimensions
"""

import numpy as np
import pytest
import scipy.sparse as sp
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck
from scipy.stats import spearmanr

# Import supra matrix centrality module
try:
    from py3plex.algorithms.multilayer_algorithms.supra_matrix_function_centrality import (
        communicability_centrality,
        katz_centrality,
    )
    SUPRA_CENTRALITY_AVAILABLE = True
except ImportError:
    SUPRA_CENTRALITY_AVAILABLE = False
    pytest.skip("Supra matrix centrality module not available", allow_module_level=True)


# ============================================================================
# Helper functions
# ============================================================================

def create_random_supra_adjacency(num_nodes, num_layers, density, seed):
    """Create a random supra-adjacency matrix."""
    total_size = num_nodes * num_layers
    rng = np.random.default_rng(seed)

    # Create block diagonal for intra-layer connections
    blocks = []
    for _ in range(num_layers):
        A = rng.random((num_nodes, num_nodes)) < density
        A = A.astype(float)
        A = np.triu(A, 1) + np.triu(A, 1).T  # Symmetric
        np.fill_diagonal(A, 0)
        blocks.append(A)

    # Build supra matrix
    supra = np.zeros((total_size, total_size))
    for layer_idx, block in enumerate(blocks):
        start = layer_idx * num_nodes
        end = start + num_nodes
        supra[start:end, start:end] = block

    # Add inter-layer couplings (identity blocks for replica nodes)
    coupling_strength = 0.5
    for i in range(num_layers - 1):
        for j in range(i + 1, num_layers):
            start_i = i * num_nodes
            start_j = j * num_nodes
            # Couple replica nodes
            for n in range(num_nodes):
                supra[start_i + n, start_j + n] = coupling_strength
                supra[start_j + n, start_i + n] = coupling_strength

    return sp.csr_matrix(supra)


def create_connected_supra_adjacency(num_nodes, num_layers, seed):
    """Create a connected supra-adjacency matrix (ring structure)."""
    total_size = num_nodes * num_layers
    rng = np.random.default_rng(seed)

    supra = np.zeros((total_size, total_size))

    # Ring connectivity within each layer
    for layer_idx in range(num_layers):
        start = layer_idx * num_nodes
        for i in range(num_nodes):
            j = (i + 1) % num_nodes
            supra[start + i, start + j] = 1.0
            supra[start + j, start + i] = 1.0

    # Inter-layer couplings
    for i in range(num_layers - 1):
        start_i = i * num_nodes
        start_j = (i + 1) * num_nodes
        for n in range(num_nodes):
            supra[start_i + n, start_j + n] = 0.5
            supra[start_j + n, start_i + n] = 0.5

    # Add some random edges
    random_edges = rng.random((total_size, total_size)) < 0.1
    random_edges = np.triu(random_edges, 1).astype(float)
    supra = np.maximum(supra, random_edges + random_edges.T)

    return sp.csr_matrix(supra)


# ============================================================================
# Property Tests: Communicability Centrality - Non-negativity
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=1, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_communicability_nonnegative(num_nodes, num_layers, seed):
    """Property: Communicability centrality is non-negative."""
    A = create_connected_supra_adjacency(num_nodes, num_layers, seed)

    scores = communicability_centrality(A, normalize=False)

    assert np.all(scores >= 0), f"Negative communicability scores: min={np.min(scores)}"


@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=1, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_communicability_finite(num_nodes, num_layers, seed):
    """Property: All communicability values are finite (no NaN or Inf)."""
    A = create_connected_supra_adjacency(num_nodes, num_layers, seed)

    scores = communicability_centrality(A, normalize=True)

    assert np.all(np.isfinite(scores)), "Non-finite communicability values found"


# ============================================================================
# Property Tests: Communicability Centrality - Normalization
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=1, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_communicability_normalized_sums_to_one(num_nodes, num_layers, seed):
    """Property: Normalized communicability scores sum to 1."""
    A = create_connected_supra_adjacency(num_nodes, num_layers, seed)

    scores = communicability_centrality(A, normalize=True)

    score_sum = np.sum(scores)
    assert np.isclose(score_sum, 1.0, atol=1e-4), \
        f"Normalized scores sum to {score_sum}, expected 1.0"


# ============================================================================
# Property Tests: Communicability Centrality - Output Shape
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=15),
    num_layers=st.integers(min_value=1, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_communicability_output_shape(num_nodes, num_layers, seed):
    """Property: Output has correct shape (total node-layer pairs)."""
    A = create_random_supra_adjacency(num_nodes, num_layers, 0.3, seed)
    total_size = num_nodes * num_layers

    scores = communicability_centrality(A, normalize=True)

    assert scores.shape == (total_size,), \
        f"Output shape {scores.shape} != expected ({total_size},)"


# ============================================================================
# Property Tests: Communicability Centrality - Scale Invariance
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=8),
    num_layers=st.integers(min_value=1, max_value=2),
    scale=st.floats(min_value=0.5, max_value=2.0, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_communicability_scale_invariance_rankings(num_nodes, num_layers, scale, seed):
    """Property: Scaling preserves normalized rankings (high correlation)."""
    A = create_connected_supra_adjacency(num_nodes, num_layers, seed)

    scores1 = communicability_centrality(A, normalize=True)
    scores2 = communicability_centrality(A * scale, normalize=True)

    total_size = num_nodes * num_layers
    if total_size > 2:
        corr, _ = spearmanr(scores1, scores2)
        # Note: communicability may not be perfectly scale-invariant
        # but rankings should be reasonably preserved
        assert corr > 0.7 or np.allclose(scores1, scores2, atol=0.1), \
            f"Scale changed rankings significantly: correlation = {corr}"


# ============================================================================
# Property Tests: Communicability Centrality - Reproducibility
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=1, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_communicability_deterministic(num_nodes, num_layers, seed):
    """Property: Same input produces identical output (deterministic)."""
    A = create_connected_supra_adjacency(num_nodes, num_layers, seed)

    scores1 = communicability_centrality(A, normalize=True)
    scores2 = communicability_centrality(A, normalize=True)

    np.testing.assert_array_almost_equal(scores1, scores2, decimal=10)


# ============================================================================
# Property Tests: Katz Centrality - Non-negativity
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=1, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_katz_nonnegative(num_nodes, num_layers, seed):
    """Property: Katz centrality is non-negative."""
    A = create_connected_supra_adjacency(num_nodes, num_layers, seed)

    scores = katz_centrality(A, alpha=None)  # Auto-compute safe alpha

    assert np.all(scores >= 0), f"Negative Katz scores: min={np.min(scores)}"


@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=1, max_value=3),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_katz_finite(num_nodes, num_layers, seed):
    """Property: All Katz centrality values are finite."""
    A = create_connected_supra_adjacency(num_nodes, num_layers, seed)

    scores = katz_centrality(A, alpha=None)

    assert np.all(np.isfinite(scores)), "Non-finite Katz values found"


# ============================================================================
# Property Tests: Katz Centrality - Alpha Bounds
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=1, max_value=2),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_katz_auto_alpha_valid(num_nodes, num_layers, seed):
    """Property: Auto-computed alpha produces valid results."""
    A = create_connected_supra_adjacency(num_nodes, num_layers, seed)

    # alpha=None should auto-compute a safe value
    scores = katz_centrality(A, alpha=None)

    # Should produce valid normalized scores
    assert np.all(scores >= 0)
    assert np.all(np.isfinite(scores))
    assert np.isclose(np.sum(scores), 1.0, atol=1e-4)


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=6),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_katz_small_alpha_valid(num_nodes, seed):
    """Property: Small alpha values always work."""
    A = create_connected_supra_adjacency(num_nodes, 1, seed)

    # Very small alpha should always be safe
    scores = katz_centrality(A, alpha=0.01)

    assert np.all(scores >= 0)
    assert np.all(np.isfinite(scores))


# ============================================================================
# Property Tests: Katz Centrality - Output Shape
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=15),
    num_layers=st.integers(min_value=1, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_katz_output_shape(num_nodes, num_layers, seed):
    """Property: Katz output has correct shape."""
    A = create_random_supra_adjacency(num_nodes, num_layers, 0.3, seed)
    total_size = num_nodes * num_layers

    scores = katz_centrality(A, alpha=None)

    assert scores.shape == (total_size,), \
        f"Output shape {scores.shape} != expected ({total_size},)"


# ============================================================================
# Property Tests: Katz Centrality - Reproducibility
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=10),
    num_layers=st.integers(min_value=1, max_value=3),
    alpha=st.floats(min_value=0.01, max_value=0.1, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_katz_deterministic(num_nodes, num_layers, alpha, seed):
    """Property: Same input produces identical Katz output."""
    A = create_connected_supra_adjacency(num_nodes, num_layers, seed)

    scores1 = katz_centrality(A, alpha=alpha)
    scores2 = katz_centrality(A, alpha=alpha)

    np.testing.assert_array_almost_equal(scores1, scores2, decimal=10)


# ============================================================================
# Property Tests: Katz Centrality - Beta Parameter
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=1, max_value=2),
    beta=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_katz_beta_parameter(num_nodes, num_layers, beta, seed):
    """Property: Different beta values produce valid results."""
    A = create_connected_supra_adjacency(num_nodes, num_layers, seed)

    scores = katz_centrality(A, alpha=0.05, beta=beta)

    assert np.all(scores >= 0)
    assert np.all(np.isfinite(scores))


# ============================================================================
# Property Tests: Comparison Between Methods
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=10),
    num_layers=st.integers(min_value=1, max_value=2),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_communicability_katz_correlation(num_nodes, num_layers, seed):
    """Property: Communicability and Katz have positive correlation."""
    A = create_connected_supra_adjacency(num_nodes, num_layers, seed)

    comm_scores = communicability_centrality(A, normalize=True)
    katz_scores = katz_centrality(A, alpha=None)

    total_size = num_nodes * num_layers
    if total_size > 2:
        # Check for constant arrays (would cause NaN correlation)
        if np.std(comm_scores) < 1e-10 or np.std(katz_scores) < 1e-10:
            # Constant scores are expected for highly regular graphs
            # (e.g., complete graph), which is still valid behavior
            return

        corr, _ = spearmanr(comm_scores, katz_scores)
        # Both measure node importance, should have positive correlation
        assert corr > 0, f"Expected positive correlation, got {corr}"


# ============================================================================
# Property Tests: Edge Cases
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=10000))
def test_communicability_sparse_matrix(seed):
    """Property: Works with very sparse matrices."""
    # Create sparse ring graph
    n = 10
    A = np.zeros((n, n))
    for i in range(n):
        A[i, (i + 1) % n] = 1.0
        A[(i + 1) % n, i] = 1.0
    A = sp.csr_matrix(A)

    scores = communicability_centrality(A, normalize=True)

    assert np.all(np.isfinite(scores))
    assert np.isclose(np.sum(scores), 1.0, atol=1e-4)


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(seed=st.integers(min_value=0, max_value=10000))
def test_katz_sparse_matrix(seed):
    """Property: Katz works with very sparse matrices."""
    # Create sparse ring graph
    n = 10
    A = np.zeros((n, n))
    for i in range(n):
        A[i, (i + 1) % n] = 1.0
        A[(i + 1) % n, i] = 1.0
    A = sp.csr_matrix(A)

    scores = katz_centrality(A, alpha=0.05)

    assert np.all(np.isfinite(scores))
    assert np.all(scores >= 0)


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_communicability_complete_graph_uniform(num_nodes, seed):
    """Property: Complete graph has approximately uniform communicability."""
    # Complete graph
    A = np.ones((num_nodes, num_nodes))
    np.fill_diagonal(A, 0)
    A = sp.csr_matrix(A)

    scores = communicability_centrality(A, normalize=True)

    # Should be approximately uniform
    expected_score = 1.0 / num_nodes
    assert np.allclose(scores, expected_score, atol=0.05), \
        f"Complete graph should have uniform scores: {scores}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_katz_complete_graph_uniform(num_nodes, seed):
    """Property: Complete graph has approximately uniform Katz centrality."""
    # Complete graph
    A = np.ones((num_nodes, num_nodes))
    np.fill_diagonal(A, 0)
    A = sp.csr_matrix(A)

    scores = katz_centrality(A, alpha=None)

    # Should be approximately uniform
    expected_score = 1.0 / num_nodes
    assert np.allclose(scores, expected_score, atol=0.05), \
        f"Complete graph should have uniform Katz scores: {scores}"


# ============================================================================
# Property Tests: Use Sparse Flag
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=1, max_value=2),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_communicability_sparse_dense_equivalent(num_nodes, num_layers, seed):
    """Property: Sparse and dense computation produce similar results."""
    A = create_connected_supra_adjacency(num_nodes, num_layers, seed)

    scores_sparse = communicability_centrality(A, normalize=True, use_sparse=True)
    scores_dense = communicability_centrality(A, normalize=True, use_sparse=False)

    # Should be approximately equal (within numerical tolerance)
    np.testing.assert_array_almost_equal(scores_sparse, scores_dense, decimal=4)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
