#!/usr/bin/env python3
"""
Property-based tests for versatility (multilayer eigenvector centrality).

Tests reduction to eigenvector centrality, normalization properties,
and scale invariance.
"""

import numpy as np
import networkx as nx
import scipy.sparse as sp
import pytest
from hypothesis import given, strategies as st, settings, assume
from scipy.stats import spearmanr

from py3plex.algorithms.multilayer_algorithms.versatility import versatility


def _nx_evc_order(G):
    """
    Compute normalized NetworkX eigenvector centrality.
    
    Returns node list and L1-normalized centrality values.
    """
    try:
        ev = nx.eigenvector_centrality_numpy(G, max_iter=1000)
        nodes = list(G.nodes())
        vals = np.array([ev[n] for n in nodes])
        # L1 normalize
        if np.sum(np.abs(vals)) > 0:
            vals = vals / np.sum(np.abs(vals))
        return nodes, vals
    except (nx.PowerIterationFailedConvergence, np.linalg.LinAlgError):
        # Fallback for difficult cases
        return None, None


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(n=st.integers(min_value=3, max_value=8))
def test_versatility_single_layer_matches_evc(n):
    """
    Test that versatility on a single layer matches eigenvector centrality.
    
    Property: With one layer and interlayer=0, versatility should reduce
    to standard eigenvector centrality (up to normalization and sign).
    """
    # Build a connected graph with reasonable probability
    p = 0.5
    G = nx.gnp_random_graph(n, p, seed=hash(n) % (2**32))
    assume(nx.is_connected(G))
    assume(G.number_of_edges() >= n - 1)
    
    # Convert to scipy sparse matrix
    nodelist = list(range(n))
    A = nx.to_scipy_sparse_array(G, nodelist=nodelist, format="csr")
    
    # Compute versatility with single layer
    v = versatility([A], interlayer=0.0, normalize="l1")
    
    # Compute NetworkX eigenvector centrality
    nodes, ev = _nx_evc_order(G)
    
    if ev is None:
        # Skip if NetworkX fails to converge
        assume(False)
    
    # Check L1 normalization
    assert np.isclose(np.sum(np.abs(v)), 1.0, atol=1e-5), \
        f"L1 norm not close to 1: {np.sum(np.abs(v))}"
    
    # Check that rankings are highly correlated
    # Use Spearman rank correlation for robustness
    # Take absolute value to handle sign ambiguity
    if len(v) > 2 and np.std(v) > 1e-6 and np.std(ev) > 1e-6:
        rho, _ = spearmanr(v, ev)
        # Expect high correlation (allowing for sign flip)
        # Use more lenient threshold for small graphs where numerical precision varies
        assert abs(rho) > 0.85, \
            f"Rank correlation magnitude too low: {abs(rho):.3f}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_versatility_l1_normalization(n, num_layers):
    """
    Test that L1 normalization produces unit sum.
    
    Property: When normalize="l1", sum of absolute values equals 1.
    """
    # Create random layers with enough connectivity
    layers = []
    for i in range(num_layers):
        p = 0.6  # Higher probability for better connectivity
        G = nx.gnp_random_graph(n, p, seed=hash((n, i)) % (2**32))
        # Ensure connected by using cycle as base
        if not nx.is_connected(G):
            G = nx.cycle_graph(n)
        A = nx.to_scipy_sparse_array(G, nodelist=list(range(n)), format="csr")
        layers.append(A)
    
    # Skip if graph is empty
    total_edges = sum(layer.nnz for layer in layers)
    assume(total_edges > 0)
    
    # Compute versatility
    v = versatility(layers, interlayer=0.1, normalize="l1")
    
    # Check L1 normalization
    l1_sum = np.sum(np.abs(v))
    assert np.isclose(l1_sum, 1.0, atol=1e-5), \
        f"L1 norm not 1: {l1_sum}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=3, max_value=6),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_versatility_l2_normalization(n, num_layers):
    """
    Test that L2 normalization produces unit norm.
    
    Property: When normalize="l2", L2 norm equals 1.
    """
    # Create random layers with enough connectivity
    layers = []
    for i in range(num_layers):
        p = 0.6  # Higher probability for better connectivity
        G = nx.gnp_random_graph(n, p, seed=hash((n, i + 100)) % (2**32))
        # Ensure connected by using cycle as base
        if not nx.is_connected(G):
            G = nx.cycle_graph(n)
        A = nx.to_scipy_sparse_array(G, nodelist=list(range(n)), format="csr")
        layers.append(A)
    
    # Skip if graph is empty
    total_edges = sum(layer.nnz for layer in layers)
    assume(total_edges > 0)
    
    # Compute versatility
    v = versatility(layers, interlayer=0.1, normalize="l2")
    
    # Check L2 normalization
    l2_norm = np.linalg.norm(v)
    assert np.isclose(l2_norm, 1.0, atol=1e-5), \
        f"L2 norm not 1: {l2_norm}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=3, max_value=6),
    scale=st.floats(min_value=0.1, max_value=10.0)
)
def test_versatility_scale_invariance(n, scale):
    """
    Test scale invariance of normalized versatility.
    
    Property: Scaling all edge weights by a positive constant
    leaves the normalized versatility vector unchanged.
    """
    # Create a simple connected graph
    G = nx.cycle_graph(n)
    A = nx.to_scipy_sparse_array(G, nodelist=list(range(n)), format="csr")
    
    # Compute versatility on original
    v1 = versatility([A], interlayer=0.0, normalize="l1")
    
    # Scale adjacency matrix
    A_scaled = A * scale
    v2 = versatility([A_scaled], interlayer=0.0, normalize="l1")
    
    # Normalized results should be very close
    assert np.allclose(v1, v2, atol=1e-4), \
        f"Scale invariance violated: max diff {np.max(np.abs(v1 - v2))}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(
    n=st.integers(min_value=3, max_value=8),
    num_layers=st.integers(min_value=1, max_value=3)
)
def test_versatility_finite_values(n, num_layers):
    """
    Test that versatility always returns finite values.
    
    Property: Result vector contains only finite values (no NaN, no inf).
    """
    # Create random layers with sufficient connectivity
    layers = []
    for i in range(num_layers):
        p = 0.5
        G = nx.gnp_random_graph(n, p, seed=hash((n, i, num_layers)) % (2**32))
        # Ensure connected
        if not nx.is_connected(G):
            G = nx.cycle_graph(n)
        A = nx.to_scipy_sparse_array(G, nodelist=list(range(n)), format="csr")
        layers.append(A)
    
    # Skip if graph is empty
    total_edges = sum(layer.nnz for layer in layers)
    assume(total_edges > 0)
    
    # Compute versatility
    v = versatility(layers, interlayer=0.15, normalize="l1")
    
    # Check all values are finite
    assert np.all(np.isfinite(v)), \
        f"Non-finite values in result: {v}"
    assert len(v) == n, \
        f"Result length {len(v)} != expected {n}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(n=st.integers(min_value=2, max_value=8))
def test_versatility_nonnegative_for_nonnegative_weights(n):
    """
    Test that non-negative weights produce non-negative versatility.
    
    Property: For adjacency matrices with non-negative weights,
    versatility values should be non-negative (for connected graphs).
    """
    # Create a connected graph (cycle)
    G = nx.cycle_graph(n)
    A = nx.to_scipy_sparse_array(G, nodelist=list(range(n)), format="csr")
    
    # Ensure non-negative weights
    A = sp.csr_matrix(np.abs(A.toarray()))
    
    # Compute versatility
    v = versatility([A], interlayer=0.0, normalize="l1")
    
    # Check non-negativity (allowing small numerical errors)
    assert np.all(v >= -1e-10), \
        f"Negative values found: {v[v < 0]}"
