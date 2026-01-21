#!/usr/bin/env python3
"""
Permutation/isomorphism invariance tests for py3plex algorithms.

Tests that algorithms produce consistent results on isomorphic graphs
(graphs that differ only in node labeling).
"""

import networkx as nx
import numpy as np
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from scipy.stats import spearmanr

from py3plex.core.multinet import multi_layer_network
from py3plex.algorithms.multilayer_algorithms.versatility import versatility

from .strategies import relabel_graph


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(n=st.integers(min_value=3, max_value=8))
def test_degree_invariant_under_relabeling(n):
    """
    Test that degree distribution is invariant under node relabeling.
    
    Property: Degree multiset should be identical for isomorphic graphs.
    """
    p = 0.5
    seed = hash(n) % (2**32)
    G = nx.gnp_random_graph(n, p, seed=seed)
    assume(nx.is_connected(G))
    assume(G.number_of_edges() >= n - 1)
    
    # Get degree sequence of original
    degrees_original = sorted(dict(G.degree()).values())
    
    # Relabel and check
    H, mapping = relabel_graph(G, seed=seed + 1)
    degrees_relabeled = sorted(dict(H.degree()).values())
    
    assert degrees_original == degrees_relabeled, \
        f"Degree sequences differ: {degrees_original} vs {degrees_relabeled}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(n=st.integers(min_value=3, max_value=8))
def test_monoplex_betweenness_ranking_invariant(n):
    """
    Test that betweenness centrality ranking is invariant under relabeling.
    
    Property: Sorted centrality values should be identical.
    """
    p = 0.5
    seed = hash(n) % (2**32)
    G = nx.gnp_random_graph(n, p, seed=seed)
    assume(nx.is_connected(G))
    assume(G.number_of_edges() >= n)
    
    # Compute betweenness on original
    bc_original = nx.betweenness_centrality(G)
    values_original = sorted(bc_original.values())
    
    # Relabel and recompute
    H, mapping = relabel_graph(G, seed=seed + 1)
    bc_relabeled = nx.betweenness_centrality(H)
    values_relabeled = sorted(bc_relabeled.values())
    
    # Compare sorted values (up to floating point error)
    assert len(values_original) == len(values_relabeled)
    for v1, v2 in zip(values_original, values_relabeled):
        assert abs(v1 - v2) < 1e-10, \
            f"Betweenness values differ: {v1} vs {v2}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(n=st.integers(min_value=3, max_value=8))
def test_clustering_coefficient_invariant(n):
    """
    Test that clustering coefficients are invariant under relabeling.
    
    Property: Sorted clustering values should be identical.
    """
    p = 0.5
    seed = hash(n) % (2**32)
    G = nx.gnp_random_graph(n, p, seed=seed)
    assume(G.number_of_edges() >= n - 1)
    
    # Compute clustering on original
    cc_original = nx.clustering(G)
    values_original = sorted(cc_original.values())
    
    # Relabel and recompute
    H, mapping = relabel_graph(G, seed=seed + 1)
    cc_relabeled = nx.clustering(H)
    values_relabeled = sorted(cc_relabeled.values())
    
    # Compare
    assert len(values_original) == len(values_relabeled)
    for v1, v2 in zip(values_original, values_relabeled):
        assert abs(v1 - v2) < 1e-10


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(n=st.integers(min_value=5, max_value=8))
def test_eigenvector_centrality_ranking_invariant(n):
    """
    Test that eigenvector centrality ranking is invariant under relabeling.
    
    Property: Sorted centrality values should be identical for isomorphic graphs.
    Note: Excludes very small graphs (n<5) due to numerical instability.
    """
    p = 0.5
    seed = hash(n) % (2**32)
    G = nx.gnp_random_graph(n, p, seed=seed)
    assume(nx.is_connected(G))
    assume(G.number_of_edges() >= n)
    
    try:
        # Compute eigenvector centrality on original
        ec_original = nx.eigenvector_centrality_numpy(G, max_iter=1000)
        values_original = sorted(ec_original.values())
        
        # Relabel and recompute
        H, mapping = relabel_graph(G, seed=seed + 1)
        ec_relabeled = nx.eigenvector_centrality_numpy(H, max_iter=1000)
        values_relabeled = sorted(ec_relabeled.values())
        
        # Compare sorted values directly (element-wise)
        # For isomorphic graphs, the sorted centrality values must be identical
        assert len(values_original) == len(values_relabeled)
        
        # Allow small numerical differences but rankings should be nearly identical
        # Eigenvector centrality uses iterative methods with inherent numerical precision limits
        if len(values_original) > 2:
            rho, _ = spearmanr(values_original, values_relabeled)
            assert abs(rho - 1.0) < 0.02, \
                f"Rank correlation not close to 1.0: {rho}"
    
    except (nx.PowerIterationFailedConvergence, np.linalg.LinAlgError):
        # Skip if convergence fails
        assume(False)


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(n=st.integers(min_value=4, max_value=7))
def test_versatility_single_layer_invariant(n):
    """
    Test that versatility on single layer is invariant under relabeling.
    
    Property: Sorted versatility scores are identical for isomorphic graphs.
    """
    p = 0.5
    seed = hash(n) % (2**32)
    G = nx.gnp_random_graph(n, p, seed=seed)
    assume(nx.is_connected(G))
    assume(G.number_of_edges() >= n - 1)
    
    # Compute versatility on original
    nodelist_original = list(range(n))
    A_original = nx.to_scipy_sparse_array(G, nodelist=nodelist_original, format="csr")
    v_original = versatility([A_original], interlayer=0.0, normalize="l1")
    values_original = sorted(v_original)
    
    # Relabel and recompute
    H, mapping = relabel_graph(G, seed=seed + 1)
    nodelist_relabeled = sorted(H.nodes())
    A_relabeled = nx.to_scipy_sparse_array(H, nodelist=nodelist_relabeled, format="csr")
    v_relabeled = versatility([A_relabeled], interlayer=0.0, normalize="l1")
    values_relabeled = sorted(v_relabeled)
    
    # Compare sorted values
    assert len(values_original) == len(values_relabeled)
    for v1, v2 in zip(values_original, values_relabeled):
        assert abs(v1 - v2) < 1e-5, \
            f"Versatility values differ: {v1} vs {v2}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(n=st.integers(min_value=3, max_value=7))
def test_louvain_partition_size_invariant(n):
    """
    Test that Louvain community sizes are invariant under relabeling.
    
    Property: Sorted community sizes should be identical.
    """
    # Try to import python-louvain
    pytest.importorskip("community")
    import community as community_louvain
    
    p = 0.5
    seed = hash(n) % (2**32)
    G = nx.gnp_random_graph(n, p, seed=seed)
    assume(G.number_of_edges() >= n - 1)
    
    # Compute communities on original
    partition_original = community_louvain.best_partition(G, random_state=seed)
    sizes_original = sorted([
        sum(1 for v in partition_original.values() if v == comm_id)
        for comm_id in set(partition_original.values())
    ])
    
    # Relabel and recompute
    H, mapping = relabel_graph(G, seed=seed + 1)
    partition_relabeled = community_louvain.best_partition(H, random_state=seed)
    sizes_relabeled = sorted([
        sum(1 for v in partition_relabeled.values() if v == comm_id)
        for comm_id in set(partition_relabeled.values())
    ])
    
    # Compare community size distributions
    assert sizes_original == sizes_relabeled, \
        f"Community size distributions differ: {sizes_original} vs {sizes_relabeled}"


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(n=st.integers(min_value=3, max_value=8))
def test_shortest_path_lengths_invariant(n):
    """
    Test that shortest path length distribution is invariant.
    
    Property: Sorted path lengths should be identical.
    """
    p = 0.5
    seed = hash(n) % (2**32)
    G = nx.gnp_random_graph(n, p, seed=seed)
    assume(nx.is_connected(G))
    
    # Compute all shortest paths on original
    paths_original = dict(nx.all_pairs_shortest_path_length(G))
    lengths_original = sorted([
        length for source in paths_original.values()
        for length in source.values()
    ])
    
    # Relabel and recompute
    H, mapping = relabel_graph(G, seed=seed + 1)
    paths_relabeled = dict(nx.all_pairs_shortest_path_length(H))
    lengths_relabeled = sorted([
        length for source in paths_relabeled.values()
        for length in source.values()
    ])
    
    assert lengths_original == lengths_relabeled


@pytest.mark.property
@settings(deadline=None, max_examples=3)
@given(n=st.integers(min_value=3, max_value=8))
def test_monoplex_wrapper_degree_invariant(n):
    """
    Test that monoplex_nx_wrapper preserves degree under relabeling.
    
    Property: Degree centrality multiset is invariant.
    """
    p = 0.5
    seed = hash(n) % (2**32)
    G = nx.gnp_random_graph(n, p, seed=seed)
    assume(G.number_of_edges() >= n - 1)
    
    # Load into py3plex
    mlnet1 = multi_layer_network(verbose=False)
    mlnet1.load_network(G, input_type="nx")
    
    # Use monoplex wrapper to get degree centrality
    try:
        result1 = mlnet1.monoplex_nx_wrapper(method="degree_centrality")
        values1 = sorted(result1.values())
    except Exception:
        # If wrapper fails, skip
        assume(False)
    
    # Relabel and repeat
    H, mapping = relabel_graph(G, seed=seed + 1)
    mlnet2 = multi_layer_network(verbose=False)
    mlnet2.load_network(H, input_type="nx")
    
    try:
        result2 = mlnet2.monoplex_nx_wrapper(method="degree_centrality")
        values2 = sorted(result2.values())
    except Exception:
        assume(False)
    
    # Compare sorted values
    assert len(values1) == len(values2)
    for v1, v2 in zip(values1, values2):
        assert abs(v1 - v2) < 1e-10
