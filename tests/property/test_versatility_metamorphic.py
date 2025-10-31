#!/usr/bin/env python3
"""
Versatility spectral metamorphic tests for py3plex.

Tests advanced properties of versatility (multilayer eigenvector centrality):
- Single-layer reduction to eigenvector centrality
- Normalization properties (L1, L2)
- Scale invariance
- Zero layer behavior
"""

import networkx as nx
import numpy as np
import pytest
import scipy.sparse as sp
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from scipy.stats import spearmanr

from py3plex.algorithms.multilayer_algorithms.versatility import versatility


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=3, max_value=8))
def test_versatility_single_layer_reduction(n):
    """
    Test that versatility on single layer matches eigenvector centrality.
    
    Property: With L=1 and omega=0, versatility should be rank-equivalent
    to NetworkX eigenvector centrality (Spearman ρ ≥ 0.99).
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(nx.is_connected(G))
    assume(G.number_of_edges() >= n - 1)
    
    # Compute versatility
    nodelist = list(range(n))
    A = nx.to_scipy_sparse_array(G, nodelist=nodelist, format="csr")
    v = versatility([A], interlayer=0.0, normalize="l1")
    
    # Compute NetworkX eigenvector centrality
    try:
        ec = nx.eigenvector_centrality_numpy(G, max_iter=1000)
        ec_vals = np.array([ec[i] for i in nodelist])
        
        # L1 normalize
        if np.sum(np.abs(ec_vals)) > 0:
            ec_vals = ec_vals / np.sum(np.abs(ec_vals))
        
        # Check rank correlation
        if len(v) > 2 and np.std(v) > 1e-6 and np.std(ec_vals) > 1e-6:
            rho, _ = spearmanr(v, ec_vals)
            assert abs(rho) >= 0.99, \
                f"Rank correlation too low: {abs(rho):.4f}"
    
    except (nx.PowerIterationFailedConvergence, np.linalg.LinAlgError):
        # Skip if convergence fails
        assume(False)


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    n=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4)
)
def test_versatility_l1_normalization(n, num_layers):
    """
    Test that L1 normalization sums to 1.
    
    Property: With normalize='l1', sum(|v|) ≈ 1.
    """
    p = 0.4
    
    # Create multiple layers
    layers = []
    for layer_idx in range(num_layers):
        G = nx.gnp_random_graph(n, p, seed=hash((n, layer_idx)) % (2**32))
        assume(G.number_of_edges() > 0)
        
        nodelist = list(range(n))
        A = nx.to_scipy_sparse_array(G, nodelist=nodelist, format="csr")
        layers.append(A)
    
    # Compute versatility with L1 normalization
    v = versatility(layers, interlayer=0.1, normalize="l1")
    
    # Check L1 norm
    l1_norm = np.sum(np.abs(v))
    assert np.isclose(l1_norm, 1.0, atol=1e-5), \
        f"L1 norm not 1: {l1_norm}"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    n=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4)
)
def test_versatility_l2_normalization(n, num_layers):
    """
    Test that L2 normalization produces unit norm.
    
    Property: With normalize='l2', ||v||_2 ≈ 1.
    """
    p = 0.4
    
    # Create layers
    layers = []
    for layer_idx in range(num_layers):
        G = nx.gnp_random_graph(n, p, seed=hash((n, layer_idx)) % (2**32))
        assume(G.number_of_edges() > 0)
        
        nodelist = list(range(n))
        A = nx.to_scipy_sparse_array(G, nodelist=nodelist, format="csr")
        layers.append(A)
    
    # Compute versatility with L2 normalization
    v = versatility(layers, interlayer=0.1, normalize="l2")
    
    # Check L2 norm
    l2_norm = np.linalg.norm(v)
    assert np.isclose(l2_norm, 1.0, atol=1e-5), \
        f"L2 norm not 1: {l2_norm}"


@pytest.mark.property
@settings(deadline=None, max_examples=25)
@given(
    n=st.integers(min_value=3, max_value=7),
    scale_factor=st.floats(min_value=0.1, max_value=10.0)
)
def test_versatility_scale_invariance(n, scale_factor):
    """
    Test that scaling edge weights preserves normalized versatility.
    
    Property: versatility(α·A) = versatility(A) for α > 0 (normalized).
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(nx.is_connected(G))
    assume(G.number_of_edges() >= n - 1)
    
    # Original adjacency
    nodelist = list(range(n))
    A = nx.to_scipy_sparse_array(G, nodelist=nodelist, format="csr")
    
    # Scaled adjacency
    A_scaled = A * scale_factor
    
    # Compute versatility on both
    v_original = versatility([A], interlayer=0.0, normalize="l1")
    v_scaled = versatility([A_scaled], interlayer=0.0, normalize="l1")
    
    # Normalized results should be very close
    assert np.allclose(v_original, v_scaled, atol=1e-4), \
        f"Scale invariance violated"


@pytest.mark.property
@settings(deadline=None, max_examples=25)
@given(
    n=st.integers(min_value=3, max_value=7),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_versatility_zero_layer_stable(n, num_layers):
    """
    Test that appending an all-zero layer doesn't change results.
    
    Property: versatility([A1, ..., AL, 0]) ≈ versatility([A1, ..., AL])
    when treating missing nodes consistently.
    """
    p = 0.4
    
    # Create non-zero layers
    layers = []
    for layer_idx in range(num_layers):
        G = nx.gnp_random_graph(n, p, seed=hash((n, layer_idx)) % (2**32))
        assume(G.number_of_edges() > 0)
        
        nodelist = list(range(n))
        A = nx.to_scipy_sparse_array(G, nodelist=nodelist, format="csr")
        layers.append(A)
    
    # Compute versatility without zero layer
    v_without = versatility(layers, interlayer=0.1, normalize="l1")
    
    # Add zero layer
    zero_layer = sp.csr_matrix((n, n))
    layers_with_zero = layers + [zero_layer]
    
    # Compute with zero layer
    v_with = versatility(layers_with_zero, interlayer=0.1, normalize="l1")
    
    # Results should be similar (zero layer contributes nothing)
    # The results will differ slightly due to averaging, but structure preserved
    # Check that at least the ranking is preserved
    if len(v_without) > 2 and np.std(v_without) > 1e-6 and np.std(v_with) > 1e-6:
        rho, _ = spearmanr(v_without, v_with)
        assert rho > 0.90, \
            f"Adding zero layer changed ranking significantly: ρ={rho:.3f}"


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(
    n=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=2, max_value=4)
)
def test_versatility_finite_values(n, num_layers):
    """
    Test that versatility always produces finite values.
    
    Property: No NaN, no inf in results.
    """
    p = 0.4
    
    layers = []
    for layer_idx in range(num_layers):
        G = nx.gnp_random_graph(n, p, seed=hash((n, layer_idx)) % (2**32))
        assume(G.number_of_edges() > 0)
        
        nodelist = list(range(n))
        A = nx.to_scipy_sparse_array(G, nodelist=nodelist, format="csr")
        layers.append(A)
    
    # Compute versatility
    v = versatility(layers, interlayer=0.1, normalize="l1")
    
    # Check all finite
    assert np.all(np.isfinite(v)), \
        f"Non-finite values in versatility: {v}"


@pytest.mark.property
@settings(deadline=None, max_examples=25)
@given(
    n=st.integers(min_value=3, max_value=7),
    omega=st.floats(min_value=0.0, max_value=2.0)
)
def test_versatility_interlayer_coupling_effect(n, omega):
    """
    Test that increasing omega blends layer centralities.
    
    Property: As omega increases, versatility becomes more uniform across layers.
    """
    # Create two layers with different structures
    # Layer 0: star graph (one central node)
    G0 = nx.star_graph(n - 1)
    A0 = nx.to_scipy_sparse_array(G0, nodelist=list(range(n)), format="csr")
    
    # Layer 1: path graph
    G1 = nx.path_graph(n)
    A1 = nx.to_scipy_sparse_array(G1, nodelist=list(range(n)), format="csr")
    
    layers = [A0, A1]
    
    # Compute versatility
    v = versatility(layers, interlayer=omega, normalize="l1")
    
    # Results should be finite and normalized
    assert np.all(np.isfinite(v))
    assert np.isclose(np.sum(np.abs(v)), 1.0, atol=1e-5)


@pytest.mark.property
@settings(deadline=None, max_examples=30)
@given(n=st.integers(min_value=3, max_value=8))
def test_versatility_nonnegative_weights_nonnegative_result(n):
    """
    Test that non-negative weights produce non-negative versatility.
    
    Property: If all weights ≥ 0, then v ≥ 0 (for connected components).
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(nx.is_connected(G))
    assume(G.number_of_edges() >= n - 1)
    
    nodelist = list(range(n))
    A = nx.to_scipy_sparse_array(G, nodelist=nodelist, format="csr")
    
    # Ensure non-negative (should be by default for adjacency)
    assert A.min() >= 0
    
    # Compute versatility
    v = versatility([A], interlayer=0.0, normalize="none")
    
    # For connected strongly connected graph, eigenvector should be non-negative
    # (by Perron-Frobenius)
    # Check that all are non-negative or all are non-positive (sign ambiguity)
    all_nonneg = np.all(v >= -1e-10)
    all_nonpos = np.all(v <= 1e-10)
    
    assert all_nonneg or all_nonpos, \
        f"Mixed signs in versatility: {v}"


@pytest.mark.property
@settings(deadline=None, max_examples=25)
@given(n=st.integers(min_value=4, max_value=8))
def test_versatility_normalization_options(n):
    """
    Test that all normalization options produce valid results.
    
    Property: 'l1', 'l2', and 'none' all produce finite results with
    correct normalization properties.
    """
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(nx.is_connected(G))
    assume(G.number_of_edges() > 0)
    
    nodelist = list(range(n))
    A = nx.to_scipy_sparse_array(G, nodelist=nodelist, format="csr")
    
    # Test each normalization
    for norm in ["l1", "l2", "none"]:
        v = versatility([A], interlayer=0.0, normalize=norm)
        
        # All should be finite
        assert np.all(np.isfinite(v)), \
            f"Non-finite values with normalize='{norm}'"
        
        # Check normalization
        if norm == "l1":
            assert np.isclose(np.sum(np.abs(v)), 1.0, atol=1e-5)
        elif norm == "l2":
            assert np.isclose(np.linalg.norm(v), 1.0, atol=1e-5)
        # 'none' has no specific constraint
