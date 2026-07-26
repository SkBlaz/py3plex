"""
Comprehensive tests for node ranking algorithms.
"""

import numpy as np
import scipy.sparse as sp
import networkx as nx

from py3plex.algorithms.node_ranking import (
    stochastic_normalization,
    sparse_page_rank,
    run_PPR,
    hubs_and_authorities,
    hub_matrix,
    authority_matrix,
)


class TestStochasticNormalization:
    """Tests for stochastic_normalization function."""

    def test_simple_matrix(self):
        """Test normalization of a simple matrix."""
        # Create a simple adjacency matrix
        adj = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)

        result = stochastic_normalization(adj)

        assert isinstance(result, sp.spmatrix)
        # Check column sums are approximately 1
        col_sums = result.sum(axis=0).A1
        assert np.allclose(col_sums, 1.0)

    def test_removes_self_loops(self):
        """Test that self-loops are removed."""
        adj = sp.csr_matrix([[1, 1, 0], [1, 1, 0], [0, 0, 1]], dtype=float)

        result = stochastic_normalization(adj)

        # Diagonal should be all zeros
        assert np.allclose(result.diagonal(), 0)

    def test_handles_zero_degree_nodes(self):
        """Test handling of nodes with zero degree."""
        adj = sp.csr_matrix([[0, 1, 0], [1, 0, 0], [0, 0, 0]], dtype=float)

        result = stochastic_normalization(adj)

        assert isinstance(result, sp.spmatrix)
        # Third column should be all zeros (isolated node)
        assert np.allclose(result[:, 2].toarray(), 0)

    def test_preserves_sparsity(self):
        """Test that sparsity structure is preserved."""
        adj = sp.random(100, 100, density=0.1, format='csr')

        result = stochastic_normalization(adj)

        # Should still be sparse
        assert sp.issparse(result)
        # Density should be similar (self-loops removed)
        assert result.nnz <= adj.nnz

    def test_directed_graph(self):
        """Test with directed graph (non-symmetric matrix)."""
        adj = sp.csr_matrix([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=float)

        result = stochastic_normalization(adj)

        assert isinstance(result, sp.spmatrix)
        # Non-zero columns should sum to 1
        for i in range(result.shape[1]):
            col_sum = result[:, i].sum()
            if col_sum > 0:
                assert np.isclose(col_sum, 1.0)

    def test_weighted_graph(self):
        """Test with weighted edges."""
        adj = sp.csr_matrix([[0, 2.0, 1.0],
                             [3.0, 0, 1.0],
                             [1.0, 2.0, 0]], dtype=float)

        result = stochastic_normalization(adj)

        # Column sums should be 1
        col_sums = result.sum(axis=0).A1
        assert np.allclose(col_sums, 1.0)

    def test_large_matrix(self):
        """Test with larger matrix."""
        size = 500
        adj = sp.random(size, size, density=0.05, format='csr')

        result = stochastic_normalization(adj)

        assert result.shape == (size, size)
        # Non-zero columns should sum to approximately 1
        col_sums = result.sum(axis=0).A1
        non_zero_cols = col_sums > 1e-10
        assert np.allclose(col_sums[non_zero_cols], 1.0)


class TestSparsePageRank:
    """Tests for sparse_page_rank function."""

    def test_simple_graph(self):
        """Test PageRank on a simple graph."""
        # Create a simple path graph: 0->1->2
        adj = sp.csr_matrix([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=float)
        adj = stochastic_normalization(adj)

        # Compute PageRank from node 0
        pr = sparse_page_rank(adj, [0], epsilon=1e-6, max_steps=1000,
                             damping=0.85)

        assert isinstance(pr, np.ndarray)
        assert len(pr) == 3
        assert np.all(pr >= 0)
        # Nodes that can be reached should have positive scores
        assert pr[1] > 0 or pr[2] > 0

    def test_multiple_start_nodes(self):
        """Test with multiple starting nodes."""
        adj = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)
        adj = stochastic_normalization(adj)

        pr = sparse_page_rank(adj, [0, 1], epsilon=1e-6, max_steps=1000)

        assert isinstance(pr, np.ndarray)
        assert len(pr) == 3
        # At least one non-starting node should have positive score
        assert pr[2] > 0

    def test_damping_factor(self):
        """Test different damping factors."""
        adj = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)
        adj = stochastic_normalization(adj)

        pr_low = sparse_page_rank(adj, [0], damping=0.5)
        pr_high = sparse_page_rank(adj, [0], damping=0.95)

        # Results should be different
        assert not np.allclose(pr_low, pr_high)

    def test_convergence(self):
        """Test that algorithm converges."""
        adj = sp.csr_matrix([[0, 1, 0, 0],
                            [1, 0, 1, 0],
                            [0, 1, 0, 1],
                            [0, 0, 1, 0]], dtype=float)
        adj = stochastic_normalization(adj)

        pr = sparse_page_rank(adj, [0], epsilon=1e-8, max_steps=10000)

        assert isinstance(pr, np.ndarray)
        assert np.all(np.isfinite(pr))

    def test_strongly_connected_graph(self):
        """Test on a strongly connected graph."""
        # Create a cycle
        adj = sp.csr_matrix([[0, 1, 0, 0],
                            [0, 0, 1, 0],
                            [0, 0, 0, 1],
                            [1, 0, 0, 0]], dtype=float)
        adj = stochastic_normalization(adj)

        pr = sparse_page_rank(adj, [0], epsilon=1e-6)

        assert len(pr) == 4
        # Non-starting nodes should have positive scores
        assert pr[1] > 0
        assert pr[2] > 0
        assert pr[3] > 0

    def test_spread_parameters(self):
        """Test with different spread parameters."""
        adj = sp.random(50, 50, density=0.1, format='csr')
        adj = stochastic_normalization(adj)

        pr1 = sparse_page_rank(adj, [0], spread_step=5, spread_percent=0.1)
        pr2 = sparse_page_rank(adj, [0], spread_step=20, spread_percent=0.5)

        assert isinstance(pr1, np.ndarray)
        assert isinstance(pr2, np.ndarray)
        assert len(pr1) == len(pr2)


class TestRunPPR:
    """Tests for run_PPR function."""

    def test_targets_compute_only_requested_nodes(self):
        """Target batching should not expand each target into a range slice."""
        adj = sp.csr_matrix(
            [
                [0, 1, 0, 0],
                [1, 0, 1, 0],
                [0, 1, 0, 1],
                [0, 0, 1, 0],
            ],
            dtype=float,
        )

        results = list(run_PPR(adj, cores=2, targets=[2], parallel=False))

        assert [node_idx for node_idx, _ in results] == [2]

    def test_parallel_targets_compute_only_requested_nodes(self):
        """Parallel target batches should contain only explicitly requested targets."""
        adj = sp.csr_matrix(
            [
                [0, 1, 0, 0],
                [1, 0, 1, 0],
                [0, 1, 0, 1],
                [0, 0, 1, 0],
            ],
            dtype=float,
        )

        batches = list(run_PPR(adj, cores=2, targets=[1, 3], parallel=True))
        node_ids = [node_idx for batch in batches for node_idx, _ in batch]

        assert node_ids == [1, 3]


class TestNodeRankingSubmodule:
    """Tests for direct node_ranking submodule imports."""

    def test_submodule_uses_package_sparse_page_rank(self):
        """Direct submodule imports should use the maintained package implementation."""
        from py3plex.algorithms import node_ranking as package_module
        from py3plex.algorithms.node_ranking import node_ranking as submodule

        assert submodule.sparse_page_rank is package_module.sparse_page_rank
        assert submodule.hubs_and_authorities is package_module.hubs_and_authorities


class TestHubsAndAuthorities:
    """Tests for hubs_and_authorities function."""

    def test_simple_graph(self):
        """Test HITS on a simple graph."""
        # Create a simple directed graph
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (0, 2), (1, 3), (2, 3)])

        hubs, authorities = hubs_and_authorities(G)

        assert isinstance(hubs, dict)
        assert isinstance(authorities, dict)
        assert len(hubs) == 4
        assert len(authorities) == 4
        assert all(v >= 0 for v in hubs.values())
        assert all(v >= 0 for v in authorities.values())

    def test_hub_authority_relationship(self):
        """Test that hubs point to authorities."""
        # Hub (0) points to authorities (1, 2)
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (0, 2), (3, 1), (3, 2)])

        hubs, authorities = hubs_and_authorities(G)

        # Node 0 and 3 should have high hub scores
        assert hubs[0] > 0
        assert hubs[3] > 0
        # Nodes 1 and 2 should have high authority scores
        assert authorities[1] > 0
        assert authorities[2] > 0

    def test_normalization(self):
        """Test that scores are normalized."""
        G = nx.Graph()
        G.add_edges_from([(0, 1), (0, 2), (1, 2)])

        hubs, authorities = hubs_and_authorities(G)

        # Check values are normalized (sum of squares = 1)
        hub_values = np.array(list(hubs.values()))
        auth_values = np.array(list(authorities.values()))
        assert np.isclose(np.sum(hub_values**2), 1.0, atol=1e-5)
        assert np.isclose(np.sum(auth_values**2), 1.0, atol=1e-5)

    def test_matrix_helpers_work_without_networkx_removed_apis(self):
        """Matrix helpers should not depend on removed NetworkX 3.x APIs."""
        G = nx.DiGraph()
        G.add_edges_from([(0, 1), (0, 2), (1, 2)])

        hubs = hub_matrix(G)
        authorities = authority_matrix(G)

        assert hubs.shape == (3, 3)
        assert authorities.shape == (3, 3)
        assert np.allclose(hubs, np.array([[2, 1, 0], [1, 1, 0], [0, 0, 0]]))
        assert np.allclose(
            authorities, np.array([[0, 0, 0], [0, 1, 1], [0, 1, 2]])
        )



