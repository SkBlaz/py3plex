#!/usr/bin/env python3
"""
Test suite for MultiXRank algorithm implementation.

This module tests the MultiXRank random walk with restart implementation
for universal multilayer networks, with emphasis on supra-heterogeneous
adjacency construction and bipartite inter-multiplex connections.
"""

import unittest

import numpy as np
import scipy.sparse as sp

# Handle missing dependencies gracefully
try:
    from py3plex.algorithms.multilayer_algorithms.multixrank import (
        MultiXRank, multixrank_from_py3plex_networks)
    from py3plex.core import multinet

    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    MultiXRank = None
    multixrank_from_py3plex_networks = None
    multinet = None
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: {e}")


class TestMultiXRank(unittest.TestCase):
    """Test cases for MultiXRank algorithm."""

    def setUp(self):
        """Set up test fixtures."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available for MultiXRank tests")

    def test_initialization(self):
        """Test MultiXRank initialization with various parameters."""
        # Default initialization
        mxr = MultiXRank()
        self.assertEqual(mxr.restart_prob, 0.4)
        self.assertEqual(mxr.epsilon, 1e-6)
        self.assertEqual(mxr.max_iter, 100000)

        # Custom parameters
        mxr2 = MultiXRank(restart_prob=0.3, epsilon=1e-8, max_iter=50000)
        self.assertEqual(mxr2.restart_prob, 0.3)
        self.assertEqual(mxr2.epsilon, 1e-8)
        self.assertEqual(mxr2.max_iter, 50000)

    def test_add_single_multiplex(self):
        """Test adding a single multiplex."""
        mxr = MultiXRank(verbose=False)

        # Create a simple 4x4 adjacency matrix (2 nodes, 2 layers)
        adj = sp.csr_matrix([[0, 1, 1, 0], [1, 0, 0, 1], [1, 0, 0, 1], [0, 1, 1, 0]])

        mxr.add_multiplex("test_net", adj)

        self.assertIn("test_net", mxr.multiplexes)
        self.assertEqual(mxr._multiplex_dims["test_net"], 4)
        self.assertEqual(len(mxr.node_order["test_net"]), 4)

    def test_add_multiple_multiplexes(self):
        """Test adding multiple multiplexes of different sizes."""
        mxr = MultiXRank(verbose=False)

        # Multiplex 1: 3x3
        adj1 = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]])

        # Multiplex 2: 2x2
        adj2 = sp.csr_matrix([[0, 1], [1, 0]])

        mxr.add_multiplex("net1", adj1)
        mxr.add_multiplex("net2", adj2)

        self.assertEqual(len(mxr.multiplexes), 2)
        self.assertEqual(mxr._multiplex_dims["net1"], 3)
        self.assertEqual(mxr._multiplex_dims["net2"], 2)

    def test_add_bipartite_block(self):
        """Test adding bipartite inter-multiplex connections."""
        mxr = MultiXRank(verbose=False)

        # Two 3x3 multiplexes
        adj1 = sp.eye(3, format="csr")
        adj2 = sp.eye(3, format="csr")

        mxr.add_multiplex("net1", adj1)
        mxr.add_multiplex("net2", adj2)

        # Bipartite block connecting them (3x3)
        bipartite = sp.csr_matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

        mxr.add_bipartite_block("net1", "net2", bipartite)

        self.assertIn(("net1", "net2"), mxr.bipartite_blocks)
        self.assertEqual(mxr.bipartite_blocks[("net1", "net2")].shape, (3, 3))

    def test_bipartite_block_dimension_validation(self):
        """Test that bipartite block dimensions are validated."""
        mxr = MultiXRank(verbose=False)

        adj1 = sp.eye(3, format="csr")
        adj2 = sp.eye(2, format="csr")

        mxr.add_multiplex("net1", adj1)
        mxr.add_multiplex("net2", adj2)

        # Wrong dimensions (should be 3x2)
        wrong_bipartite = sp.csr_matrix([[1, 1], [1, 1]])

        with self.assertRaises(ValueError):
            mxr.add_bipartite_block("net1", "net2", wrong_bipartite)

    def test_build_supra_heterogeneous_single_multiplex(self):
        """Test building supra-heterogeneous matrix with single multiplex."""
        mxr = MultiXRank(verbose=False)

        # Simple 3x3 matrix
        adj = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]])

        mxr.add_multiplex("net1", adj)
        supra = mxr.build_supra_heterogeneous_matrix()

        self.assertEqual(supra.shape, (3, 3))
        self.assertEqual(supra.nnz, adj.nnz)

        # Check that matrix content is preserved
        np.testing.assert_array_almost_equal(supra.toarray(), adj.toarray())

    def test_build_supra_heterogeneous_multiple_multiplexes(self):
        """Test building supra-heterogeneous matrix with multiple multiplexes."""
        mxr = MultiXRank(verbose=False)

        # Multiplex 1: 2x2
        adj1 = sp.csr_matrix([[0, 1], [1, 0]])

        # Multiplex 2: 3x3
        adj2 = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]])

        mxr.add_multiplex("net1", adj1)
        mxr.add_multiplex("net2", adj2)

        supra = mxr.build_supra_heterogeneous_matrix()

        # Should be 5x5 (2+3)
        self.assertEqual(supra.shape, (5, 5))

        # Check block structure
        supra_array = supra.toarray()

        # Top-left block should match adj1
        np.testing.assert_array_almost_equal(supra_array[0:2, 0:2], adj1.toarray())

        # Bottom-right block should match adj2
        np.testing.assert_array_almost_equal(supra_array[2:5, 2:5], adj2.toarray())

        # Off-diagonal blocks should be zero (no bipartite connections)
        self.assertEqual(np.sum(supra_array[0:2, 2:5]), 0)
        self.assertEqual(np.sum(supra_array[2:5, 0:2]), 0)

    def test_build_supra_heterogeneous_with_bipartite(self):
        """Test supra-heterogeneous matrix construction with bipartite blocks."""
        mxr = MultiXRank(verbose=False)

        # Two 2x2 multiplexes
        adj1 = sp.csr_matrix([[0, 1], [1, 0]])
        adj2 = sp.csr_matrix([[0, 1], [1, 0]])

        mxr.add_multiplex("net1", adj1)
        mxr.add_multiplex("net2", adj2)

        # Bipartite connections
        bipartite = sp.csr_matrix([[1, 0], [0, 1]])
        mxr.add_bipartite_block("net1", "net2", bipartite)

        supra = mxr.build_supra_heterogeneous_matrix()

        # Should be 4x4 (2+2)
        self.assertEqual(supra.shape, (4, 4))

        supra_array = supra.toarray()

        # Check bipartite block is present
        np.testing.assert_array_almost_equal(supra_array[0:2, 2:4], bipartite.toarray())

    def test_column_normalization(self):
        """Test column-stochastic normalization."""
        mxr = MultiXRank(verbose=False)

        # Create a simple matrix
        adj = sp.csr_matrix([[0, 2, 0], [1, 0, 3], [0, 1, 0]], dtype=float)

        mxr.add_multiplex("net1", adj)
        mxr.build_supra_heterogeneous_matrix()
        transition = mxr.column_normalize()

        # Check column sums are 1
        col_sums = np.array(transition.sum(axis=0)).flatten()
        np.testing.assert_array_almost_equal(col_sums, np.ones(3))

    def test_column_normalization_with_dangling_nodes(self):
        """Test column normalization handles dangling nodes."""
        mxr = MultiXRank(verbose=False)

        # Matrix with a dangling node (column 2 has zero sum)
        adj = sp.csr_matrix([[0, 1, 0], [1, 0, 0], [0, 1, 0]], dtype=float)

        mxr.add_multiplex("net1", adj)
        mxr.build_supra_heterogeneous_matrix()
        transition = mxr.column_normalize(handle_dangling="uniform")

        # Check all column sums are 1
        col_sums = np.array(transition.sum(axis=0)).flatten()
        np.testing.assert_array_almost_equal(col_sums, np.ones(3))

    def test_rwr_convergence_single_seed(self):
        """Test RWR converges with a single seed node."""
        mxr = MultiXRank(restart_prob=0.5, epsilon=1e-6, verbose=False)

        # Simple chain: 0 -> 1 -> 2
        adj = sp.csr_matrix([[0, 1, 0], [0, 0, 1], [0, 0, 0]], dtype=float)

        mxr.add_multiplex("net1", adj)
        mxr.build_supra_heterogeneous_matrix()
        mxr.column_normalize()

        # Seed at node 0
        scores = mxr.random_walk_with_restart([0])

        # Check scores are valid probabilities
        self.assertAlmostEqual(np.sum(scores), 1.0, places=6)
        self.assertTrue(np.all(scores >= 0))
        self.assertTrue(np.all(scores <= 1))

        # Seed node should have highest score
        self.assertEqual(np.argmax(scores), 0)

    def test_rwr_multiple_seeds(self):
        """Test RWR with multiple seed nodes."""
        mxr = MultiXRank(restart_prob=0.3, verbose=False)

        # Fully connected 3-node network
        adj = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)

        mxr.add_multiplex("net1", adj)
        mxr.build_supra_heterogeneous_matrix()
        mxr.column_normalize()

        # Multiple seeds
        scores = mxr.random_walk_with_restart([0, 2])

        # Check valid probability distribution
        self.assertAlmostEqual(np.sum(scores), 1.0, places=6)
        self.assertTrue(np.all(scores >= 0))

    def test_rwr_with_seed_weights(self):
        """Test RWR with weighted seed nodes."""
        mxr = MultiXRank(restart_prob=0.5, verbose=False)

        adj = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)

        mxr.add_multiplex("net1", adj)
        mxr.build_supra_heterogeneous_matrix()
        mxr.column_normalize()

        # Seed with weights
        scores = mxr.random_walk_with_restart([0, 2], seed_weights=np.array([0.8, 0.2]))

        # Node 0 should have higher influence than node 2
        self.assertGreater(scores[0], scores[2])

    def test_rwr_across_multiplexes(self):
        """Test RWR propagates across multiplexes via bipartite connections."""
        mxr = MultiXRank(restart_prob=0.3, verbose=False)

        # Two isolated 2-node networks
        adj1 = sp.csr_matrix([[0, 1], [1, 0]], dtype=float)
        adj2 = sp.csr_matrix([[0, 1], [1, 0]], dtype=float)

        mxr.add_multiplex("net1", adj1)
        mxr.add_multiplex("net2", adj2)

        # Connect them bidirectionally
        bipartite = sp.csr_matrix([[1, 0], [0, 1]], dtype=float)
        mxr.add_bipartite_block("net1", "net2", bipartite)
        mxr.add_bipartite_block("net2", "net1", bipartite)

        mxr.build_supra_heterogeneous_matrix()
        mxr.column_normalize()

        # Seed in net1
        scores = mxr.random_walk_with_restart({"net1": [0]})

        # Check that net2 also receives some probability mass
        # Indices 2-3 correspond to net2
        net2_mass = np.sum(scores[2:4])
        self.assertGreater(net2_mass, 0)

    def test_aggregate_scores_single_multiplex(self):
        """Test score aggregation for single multiplex."""
        mxr = MultiXRank(verbose=False)

        adj = sp.csr_matrix([[0, 1], [1, 0]], dtype=float)
        mxr.add_multiplex("net1", adj, node_order=["A", "B"])
        mxr.build_supra_heterogeneous_matrix()
        mxr.column_normalize()

        scores = mxr.random_walk_with_restart([0])
        aggregated = mxr.aggregate_scores(scores)

        self.assertIn("net1", aggregated)
        self.assertIn("A", aggregated["net1"])
        self.assertIn("B", aggregated["net1"])

    def test_aggregate_scores_multiple_multiplexes(self):
        """Test score aggregation across multiple multiplexes."""
        mxr = MultiXRank(verbose=False)

        adj1 = sp.csr_matrix([[0, 1], [1, 0]], dtype=float)
        adj2 = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)

        mxr.add_multiplex("net1", adj1, node_order=["A", "B"])
        mxr.add_multiplex("net2", adj2, node_order=["X", "Y", "Z"])

        mxr.build_supra_heterogeneous_matrix()
        mxr.column_normalize()

        scores = mxr.random_walk_with_restart([0])
        aggregated = mxr.aggregate_scores(scores)

        self.assertEqual(len(aggregated), 2)
        self.assertIn("net1", aggregated)
        self.assertIn("net2", aggregated)
        self.assertEqual(len(aggregated["net1"]), 2)
        self.assertEqual(len(aggregated["net2"]), 3)

    def test_get_top_ranked(self):
        """Test getting top-k ranked nodes."""
        mxr = MultiXRank(verbose=False)

        adj = sp.csr_matrix(
            [[0, 1, 0, 0], [1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0]], dtype=float
        )

        mxr.add_multiplex("net1", adj)
        mxr.build_supra_heterogeneous_matrix()
        mxr.column_normalize()

        scores = mxr.random_walk_with_restart([1])
        top_k = mxr.get_top_ranked(scores, k=2, exclude_seeds=False)

        # Should return 2 nodes
        self.assertEqual(len(top_k), 2)

        # Check format: (index, score)
        self.assertEqual(len(top_k[0]), 2)

        # Scores should be descending
        self.assertGreaterEqual(top_k[0][1], top_k[1][1])

    def test_get_top_ranked_exclude_seeds(self):
        """Test top-k with seed exclusion."""
        mxr = MultiXRank(verbose=False)

        adj = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)
        mxr.add_multiplex("net1", adj)
        mxr.build_supra_heterogeneous_matrix()
        mxr.column_normalize()

        seed_nodes = [0]
        scores = mxr.random_walk_with_restart(seed_nodes)
        top_k = mxr.get_top_ranked(
            scores, k=3, exclude_seeds=True, seed_nodes=seed_nodes
        )

        # Seed node 0 should not be in results
        indices = [idx for idx, score in top_k]
        self.assertNotIn(0, indices)

    def test_seed_nodes_dict_format(self):
        """Test seed nodes specified as dict mapping multiplex to nodes."""
        mxr = MultiXRank(verbose=False)

        adj1 = sp.csr_matrix([[0, 1], [1, 0]], dtype=float)
        adj2 = sp.csr_matrix([[0, 1], [1, 0]], dtype=float)

        mxr.add_multiplex("net1", adj1)
        mxr.add_multiplex("net2", adj2)

        bipartite = sp.csr_matrix([[1, 0], [0, 1]], dtype=float)
        mxr.add_bipartite_block("net1", "net2", bipartite)

        mxr.build_supra_heterogeneous_matrix()
        mxr.column_normalize()

        # Seed using dict format
        scores = mxr.random_walk_with_restart({"net1": [0], "net2": [1]})

        self.assertAlmostEqual(np.sum(scores), 1.0, places=6)

    def test_integration_with_py3plex_networks(self):
        """Test integration with py3plex multi_layer_network objects."""
        # Create two simple multilayer networks
        net1 = multinet.multi_layer_network(directed=False)
        net1.add_edges(
            [["A", "L1", "B", "L1", 1], ["B", "L1", "C", "L1", 1]], input_type="list"
        )

        net2 = multinet.multi_layer_network(directed=False)
        net2.add_edges([["X", "L1", "Y", "L1", 1]], input_type="list")

        networks = {"net1": net1, "net2": net2}

        # Create bipartite connection (assuming matching dimensions)
        # Get dimensions
        dim1 = net1.get_supra_adjacency_matrix().shape[0]
        dim2 = net2.get_supra_adjacency_matrix().shape[0]
        bipartite = sp.csr_matrix((dim1, dim2), dtype=float)

        mxr, scores = multixrank_from_py3plex_networks(
            networks,
            bipartite_connections={("net1", "net2"): bipartite},
            seed_nodes={"net1": [0]},
            verbose=False,
        )

        self.assertIsNotNone(mxr)
        self.assertIsNotNone(scores)
        self.assertAlmostEqual(np.sum(scores), 1.0, places=6)

    def test_block_weights(self):
        """Test optional block weighting."""
        mxr = MultiXRank(verbose=False)

        adj1 = sp.csr_matrix([[0, 1], [1, 0]], dtype=float)
        adj2 = sp.csr_matrix([[0, 1], [1, 0]], dtype=float)

        mxr.add_multiplex("net1", adj1)
        mxr.add_multiplex("net2", adj2)

        bipartite = sp.csr_matrix([[1, 0], [0, 1]], dtype=float)
        mxr.add_bipartite_block("net1", "net2", bipartite)

        # Build with weights
        block_weights = {"net1": 2.0, ("net1", "net2"): 0.5}
        supra = mxr.build_supra_heterogeneous_matrix(block_weights=block_weights)

        # Check that net1 block is weighted
        supra_array = supra.toarray()
        self.assertEqual(supra_array[0, 1], 2.0)  # Was 1.0, now weighted by 2.0

        # Check bipartite block is weighted
        self.assertEqual(supra_array[0, 2], 0.5)  # Was 1.0, now weighted by 0.5

    def test_empty_multiplex_error(self):
        """Test that building without multiplexes raises error."""
        mxr = MultiXRank(verbose=False)

        with self.assertRaises(ValueError):
            mxr.build_supra_heterogeneous_matrix()

    def test_normalize_before_build_error(self):
        """Test that normalizing before building raises error."""
        mxr = MultiXRank(verbose=False)

        with self.assertRaises(ValueError):
            mxr.column_normalize()

    def test_rwr_before_normalize_error(self):
        """Test that RWR before normalization raises error."""
        mxr = MultiXRank(verbose=False)

        adj = sp.csr_matrix([[0, 1], [1, 0]], dtype=float)
        mxr.add_multiplex("net1", adj)
        mxr.build_supra_heterogeneous_matrix()

        with self.assertRaises(ValueError):
            mxr.random_walk_with_restart([0])

    def test_non_square_matrix_error(self):
        """Test that non-square matrices are rejected."""
        mxr = MultiXRank(verbose=False)

        # Non-square matrix
        adj = sp.csr_matrix([[0, 1, 0], [1, 0, 1]])

        with self.assertRaises(ValueError):
            mxr.add_multiplex("net1", adj)


if __name__ == "__main__":
    unittest.main()
