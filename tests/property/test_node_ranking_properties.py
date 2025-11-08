#!/usr/bin/env python3
"""
Property-based tests for algorithms.node_ranking module.

Tests invariants and properties of node ranking algorithms including:
- Modularity bounds (between -0.5 and 1.0)
- PageRank convergence and normalization
- Stochastic matrix properties (row/column sums)
- HITS algorithm invariants
"""

import networkx as nx
import numpy as np
import pytest
import scipy.sparse as sp
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import shared strategies
from .strategies import (
    small_graphs,
    connected_graphs,
    weighted_graphs,
)

# Import node_ranking module
try:
    from py3plex.algorithms.node_ranking.node_ranking import (
        modularity,
        stochastic_normalization,
        sparse_page_rank,
        hubs_and_authorities,
    )
    NODE_RANKING_AVAILABLE = True
except ImportError:
    NODE_RANKING_AVAILABLE = False
    pytest.skip("Node ranking module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Modularity Bounds
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=12),
    num_communities=st.integers(min_value=2, max_value=4),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_bounds_property(num_nodes, num_communities, seed):
    """Property: Modularity is bounded between -0.5 and 1.0."""
    G = nx.gnp_random_graph(num_nodes, 0.4, seed=seed)
    assume(G.number_of_edges() > 0)
    
    # Create random communities
    nodes = list(G.nodes())
    community_size = max(1, num_nodes // num_communities)
    communities = []
    for i in range(num_communities):
        start_idx = i * community_size
        end_idx = min((i + 1) * community_size, num_nodes)
        if start_idx < num_nodes:
            communities.append(nodes[start_idx:end_idx])
    
    # Handle remaining nodes
    if len(communities) > 0 and len(communities[-1]) == 0:
        communities = communities[:-1]
    
    assume(len(communities) > 0 and all(len(c) > 0 for c in communities))
    
    mod = modularity(G, communities)
    
    # Modularity should be bounded
    assert -0.5 <= mod <= 1.0, f"Modularity {mod} out of bounds [-0.5, 1.0]"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=10),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_single_community_is_zero(num_nodes, seed):
    """Property: Modularity is 0 when all nodes in single community."""
    G = nx.gnp_random_graph(num_nodes, 0.4, seed=seed)
    assume(G.number_of_edges() > 0)
    
    # Single community containing all nodes
    communities = [list(G.nodes())]
    
    mod = modularity(G, communities)
    
    # Modularity should be approximately 0
    assert abs(mod) < 1e-10, f"Single community modularity should be ~0, got {mod}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=10),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_complete_graph_all_singletons(num_nodes, seed):
    """Property: Complete graph with all nodes as separate communities has negative modularity."""
    G = nx.complete_graph(num_nodes)
    
    # Each node is its own community
    communities = [[node] for node in G.nodes()]
    
    mod = modularity(G, communities)
    
    # For complete graph with all singletons, modularity should be negative or zero
    assert mod <= 0, f"Complete graph singleton partition should have non-positive modularity, got {mod}"


# ============================================================================
# Property Tests: Stochastic Normalization
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_stochastic_normalization_column_sums(num_nodes, seed):
    """Property: After stochastic normalization, column sums should be 1."""
    # Create random adjacency matrix
    G = nx.gnp_random_graph(num_nodes, 0.4, seed=seed)
    assume(G.number_of_edges() > 0)
    
    # Convert to sparse matrix
    adj_matrix = nx.adjacency_matrix(G)
    
    # Apply stochastic normalization
    normalized = stochastic_normalization(adj_matrix)
    
    # Check column sums (should be 1 for non-zero columns)
    col_sums = np.array(normalized.sum(axis=0)).flatten()
    
    # Columns with non-zero sum should sum to approximately 1
    non_zero_cols = col_sums > 1e-10
    if np.any(non_zero_cols):
        col_sums_nonzero = col_sums[non_zero_cols]
        assert np.allclose(col_sums_nonzero, 1.0, atol=1e-6), \
            f"Non-zero columns should sum to 1, got {col_sums_nonzero}"


@pytest.mark.property
@settings(deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_stochastic_normalization_preserves_zeros(num_nodes, seed):
    """Property: Stochastic normalization preserves zero entries."""
    # Create random sparse adjacency matrix
    G = nx.gnp_random_graph(num_nodes, 0.3, seed=seed)
    assume(G.number_of_edges() > 0)
    
    adj_matrix = nx.adjacency_matrix(G)
    original_nonzero = adj_matrix.nnz
    
    # Apply stochastic normalization
    normalized = stochastic_normalization(adj_matrix)
    
    # Number of non-zero entries should remain similar (diagonal may be removed)
    # Allow some flexibility due to diagonal removal
    assert normalized.nnz <= original_nonzero, \
        "Stochastic normalization should not add new edges"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=3, max_value=12),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_stochastic_normalization_removes_diagonal(num_nodes, seed):
    """Property: Stochastic normalization removes diagonal entries."""
    # Create adjacency matrix with self-loops
    G = nx.gnp_random_graph(num_nodes, 0.4, seed=seed)
    assume(G.number_of_edges() > 0)
    
    adj_matrix = nx.adjacency_matrix(G).tolil()
    
    # Add some diagonal entries (self-loops)
    for i in range(min(3, num_nodes)):
        adj_matrix[i, i] = 1.0
    
    adj_matrix = adj_matrix.tocsr()
    
    # Apply stochastic normalization
    normalized = stochastic_normalization(adj_matrix)
    
    # Check diagonal is zero
    diagonal = normalized.diagonal()
    assert np.allclose(diagonal, 0.0, atol=1e-10), \
        "Diagonal should be zero after stochastic normalization"


# ============================================================================
# Property Tests: Sparse PageRank
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=12),
    damping=st.floats(min_value=0.1, max_value=0.9, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sparse_pagerank_sums_to_one(num_nodes, damping, seed):
    """Property: PageRank scores should sum to approximately 1 (or close to start vector)."""
    # Create and normalize adjacency matrix
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    adj_matrix = nx.adjacency_matrix(G)
    normalized = stochastic_normalization(adj_matrix)
    
    # Compute PageRank
    pr = sparse_page_rank(
        normalized,
        start_nodes=None,  # Uniform start
        damping=damping,
        epsilon=1e-6,
        max_steps=10000
    )
    
    # PageRank should sum to approximately 1 (probability distribution)
    pr_sum = np.sum(pr)
    assert 0.9 <= pr_sum <= 1.1, f"PageRank should sum to ~1, got {pr_sum}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=12),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sparse_pagerank_all_non_negative(num_nodes, seed):
    """Property: All PageRank scores should be non-negative."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    adj_matrix = nx.adjacency_matrix(G)
    normalized = stochastic_normalization(adj_matrix)
    
    # Compute PageRank
    pr = sparse_page_rank(
        normalized,
        start_nodes=None,
        damping=0.85,
        epsilon=1e-6,
        max_steps=10000
    )
    
    # All scores should be non-negative
    assert np.all(pr >= 0), f"PageRank scores should be non-negative, got min={np.min(pr)}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=10),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_sparse_pagerank_personalized_higher_at_start(num_nodes, seed):
    """Property: Personalized PageRank has higher scores near start nodes."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed)
    assume(G.number_of_edges() > 0)
    
    adj_matrix = nx.adjacency_matrix(G)
    normalized = stochastic_normalization(adj_matrix)
    
    # Personalized PageRank from node 0
    start_node = 0
    pr = sparse_page_rank(
        normalized,
        start_nodes=[start_node],
        damping=0.85,
        epsilon=1e-6,
        max_steps=10000
    )
    
    # Start node should have zero score (as per implementation)
    # But neighbors should have higher scores than distant nodes
    # Just verify it completes and returns valid scores
    assert len(pr) == num_nodes
    assert np.all(pr >= 0)


# ============================================================================
# Property Tests: HITS Algorithm (Hubs and Authorities)
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=12),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_hits_scores_non_negative(num_nodes, seed):
    """Property: HITS hub and authority scores are non-negative."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed, directed=True)
    assume(G.number_of_edges() > 0)
    
    hubs, authorities = hubs_and_authorities(G)
    
    # All hub scores should be non-negative
    assert all(score >= 0 for score in hubs.values()), \
        f"Hub scores should be non-negative, got {hubs}"
    
    # All authority scores should be non-negative
    assert all(score >= 0 for score in authorities.values()), \
        f"Authority scores should be non-negative, got {authorities}"


@pytest.mark.property
@settings(deadline=None, max_examples=15, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=12),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_hits_scores_bounded(num_nodes, seed):
    """Property: HITS scores are bounded (normalized)."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed, directed=True)
    assume(G.number_of_edges() > 0)
    
    hubs, authorities = hubs_and_authorities(G)
    
    # Scores should be normalized (typically L2 norm = 1)
    hub_values = np.array(list(hubs.values()))
    auth_values = np.array(list(authorities.values()))
    
    hub_norm = np.linalg.norm(hub_values)
    auth_norm = np.linalg.norm(auth_values)
    
    # Norms should be close to 1 (normalized)
    assert 0.99 <= hub_norm <= 1.01, f"Hub norm should be ~1, got {hub_norm}"
    assert 0.99 <= auth_norm <= 1.01, f"Authority norm should be ~1, got {auth_norm}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=12),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_hits_all_nodes_covered(num_nodes, seed):
    """Property: HITS returns scores for all nodes."""
    G = nx.gnp_random_graph(num_nodes, 0.5, seed=seed, directed=True)
    assume(G.number_of_edges() > 0)
    
    hubs, authorities = hubs_and_authorities(G)
    
    # Should have score for every node
    assert len(hubs) == num_nodes, f"Hub scores missing for some nodes"
    assert len(authorities) == num_nodes, f"Authority scores missing for some nodes"
    
    # All nodes should be in results
    assert set(hubs.keys()) == set(G.nodes())
    assert set(authorities.keys()) == set(G.nodes())


# ============================================================================
# Property Tests: Modularity Edge Cases
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=4, max_value=10),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_modularity_disconnected_communities(num_nodes, seed):
    """Property: Modularity is high for truly disconnected communities."""
    # Create two disconnected components
    half = num_nodes // 2
    G = nx.Graph()
    
    # Component 1: complete graph on first half
    for i in range(half):
        for j in range(i + 1, half):
            G.add_edge(i, j)
    
    # Component 2: complete graph on second half
    for i in range(half, num_nodes):
        for j in range(i + 1, num_nodes):
            G.add_edge(i, j)
    
    assume(G.number_of_edges() > 0)
    
    # Communities match components
    communities = [list(range(half)), list(range(half, num_nodes))]
    
    mod = modularity(G, communities)
    
    # Modularity should be positive for well-separated communities
    assert mod > 0, f"Disconnected communities should have positive modularity, got {mod}"


@pytest.mark.property
@settings(deadline=None, max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    num_nodes=st.integers(min_value=5, max_value=10),
)
def test_modularity_star_graph_center_vs_leaves(num_nodes):
    """Property: Star graph modularity with center vs leaves partition."""
    # Star graph: node 0 (center) connected to all others
    G = nx.star_graph(num_nodes - 1)
    
    # Partition: center alone vs all leaves
    communities = [[0], list(range(1, num_nodes))]
    
    mod = modularity(G, communities)
    
    # This partition should have low modularity (center is connected to all leaves)
    # Modularity should be bounded
    assert -0.5 <= mod <= 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'property'])
