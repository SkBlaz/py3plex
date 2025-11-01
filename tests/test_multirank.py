#!/usr/bin/env python3
"""
Tests for MultiRank and Multiplex PageRank Variants

These tests validate the implementations of:
1. MultiRank co-ranking algorithm
2. Multiplex PageRank variants (neutral, additive, multiplicative, combined)

Test coverage follows py3plex testing conventions.
"""

import unittest

import numpy as np

from py3plex.algorithms.multilayer_algorithms.multirank import (
    multirank,
    multiplex_pagerank,
)


class TestMultiRank(unittest.TestCase):
    """Tests for MultiRank co-ranking algorithm."""

    def setUp(self):
        """Set up test fixtures."""
        # Simple 3-node, 2-layer network
        self.L1 = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)
        self.L2 = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)

    def test_basic_multirank(self):
        """Test basic MultiRank computation."""
        node_scores, layer_scores = multirank([self.L1, self.L2])

        # Check output shapes
        self.assertEqual(node_scores.shape, (3,))
        self.assertEqual(layer_scores.shape, (2,))

        # Check normalization
        self.assertAlmostEqual(np.sum(node_scores), 1.0, places=6)
        self.assertAlmostEqual(np.sum(layer_scores), 1.0, places=6)

        # Check all scores are non-negative
        self.assertTrue(np.all(node_scores >= 0))
        self.assertTrue(np.all(layer_scores >= 0))

    def test_single_layer_multirank(self):
        """Test MultiRank with single layer."""
        node_scores, layer_scores = multirank([self.L1])

        self.assertEqual(node_scores.shape, (3,))
        self.assertEqual(layer_scores.shape, (1,))

        # Single layer should have score 1.0
        self.assertAlmostEqual(layer_scores[0], 1.0, places=6)

    def test_symmetric_layers(self):
        """Test MultiRank with identical layers."""
        # Two identical layers should have equal layer scores
        node_scores, layer_scores = multirank([self.L1, self.L1.copy()])

        self.assertAlmostEqual(layer_scores[0], layer_scores[1], places=6)

    def test_convergence(self):
        """Test that MultiRank converges."""
        # With strict tolerance, should converge in reasonable iterations
        node_scores, layer_scores = multirank(
            [self.L1, self.L2], tol=1e-8, max_iter=1000
        )

        # If converged properly, scores should be stable
        self.assertAlmostEqual(np.sum(node_scores), 1.0, places=6)

    def test_damping_parameter(self):
        """Test MultiRank with different damping parameters."""
        node_scores_low, _ = multirank([self.L1, self.L2], alpha=0.5)
        node_scores_high, _ = multirank([self.L1, self.L2], alpha=0.95)

        # Different damping should produce different results
        self.assertFalse(np.allclose(node_scores_low, node_scores_high))

    def test_interlayer_coupling(self):
        """Test MultiRank with custom interlayer coupling."""
        # Strong coupling between layers
        coupling = np.array([[1.0, 0.5], [0.5, 1.0]])

        node_scores, layer_scores = multirank(
            [self.L1, self.L2], interlayer_coupling=coupling
        )

        self.assertEqual(node_scores.shape, (3,))
        self.assertEqual(layer_scores.shape, (2,))

    def test_empty_layers_raises_error(self):
        """Test that empty layer list raises ValueError."""
        with self.assertRaises(ValueError):
            multirank([])

    def test_inconsistent_layer_sizes_raises_error(self):
        """Test that inconsistent layer sizes raise ValueError."""
        L3 = np.array([[0, 1], [1, 0]], dtype=float)  # 2x2 instead of 3x3
        with self.assertRaises(ValueError):
            multirank([self.L1, L3])

    def test_non_square_layer_raises_error(self):
        """Test that non-square layer raises ValueError."""
        L3 = np.array([[0, 1, 1], [1, 0, 1]], dtype=float)  # 2x3
        with self.assertRaises(ValueError):
            multirank([L3])


class TestMultiplexPageRank(unittest.TestCase):
    """Tests for Multiplex PageRank variants."""

    def setUp(self):
        """Set up test fixtures."""
        # Simple 3-node, 2-layer network
        self.L1 = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)
        self.L2 = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)

    def test_neutral_variant(self):
        """Test neutral variant (baseline, no cross-layer influence)."""
        result = multiplex_pagerank([self.L1, self.L2], variant="neutral")

        self.assertIn("node_scores", result)
        self.assertIn("replica_scores", result)

        node_scores = result["node_scores"]
        replica_scores = result["replica_scores"]

        # Check shapes
        self.assertEqual(node_scores.shape, (3,))
        self.assertEqual(replica_scores.shape, (3, 2))

        # Check all scores are non-negative
        self.assertTrue(np.all(node_scores >= 0))
        self.assertTrue(np.all(replica_scores >= 0))

        # Check each layer is normalized
        for ell in range(2):
            layer_sum = np.sum(replica_scores[:, ell])
            self.assertAlmostEqual(layer_sum, 1.0, places=6)

    def test_additive_variant(self):
        """Test additive variant with cross-layer sum."""
        result = multiplex_pagerank(
            [self.L1, self.L2], variant="additive", c=0.5
        )

        node_scores = result["node_scores"]
        replica_scores = result["replica_scores"]

        # Check shapes
        self.assertEqual(node_scores.shape, (3,))
        self.assertEqual(replica_scores.shape, (3, 2))

        # Check all scores are non-negative
        self.assertTrue(np.all(node_scores >= 0))

    def test_multiplicative_variant(self):
        """Test multiplicative variant with cross-layer product."""
        result = multiplex_pagerank(
            [self.L1, self.L2], variant="multiplicative", c=0.5
        )

        node_scores = result["node_scores"]
        replica_scores = result["replica_scores"]

        # Check shapes
        self.assertEqual(node_scores.shape, (3,))
        self.assertEqual(replica_scores.shape, (3, 2))

        # Check all scores are non-negative
        self.assertTrue(np.all(node_scores >= 0))

    def test_combined_variant(self):
        """Test combined variant with both additive and multiplicative."""
        result = multiplex_pagerank(
            [self.L1, self.L2], variant="combined", c1=0.5, c2=0.3
        )

        node_scores = result["node_scores"]
        replica_scores = result["replica_scores"]

        # Check shapes
        self.assertEqual(node_scores.shape, (3,))
        self.assertEqual(replica_scores.shape, (3, 2))

        # Check all scores are non-negative
        self.assertTrue(np.all(node_scores >= 0))

    def test_variants_produce_different_results(self):
        """Test that different variants produce different results."""
        result_neutral = multiplex_pagerank([self.L1, self.L2], variant="neutral")
        result_additive = multiplex_pagerank(
            [self.L1, self.L2], variant="additive", c=0.5
        )
        result_multiplicative = multiplex_pagerank(
            [self.L1, self.L2], variant="multiplicative", c=0.5
        )

        # Different variants should produce different scores
        self.assertFalse(
            np.allclose(
                result_neutral["node_scores"], result_additive["node_scores"]
            )
        )
        self.assertFalse(
            np.allclose(
                result_neutral["node_scores"], result_multiplicative["node_scores"]
            )
        )

    def test_single_layer_multiplex_pagerank(self):
        """Test Multiplex PageRank with single layer."""
        result = multiplex_pagerank([self.L1], variant="neutral")

        node_scores = result["node_scores"]
        replica_scores = result["replica_scores"]

        self.assertEqual(node_scores.shape, (3,))
        self.assertEqual(replica_scores.shape, (3, 1))

    def test_convergence(self):
        """Test that Multiplex PageRank converges."""
        result = multiplex_pagerank(
            [self.L1, self.L2], variant="additive", tol=1e-8, max_iter=1000
        )

        node_scores = result["node_scores"]

        # Check that scores are stable (normalized per layer, sum can be > 1)
        self.assertTrue(np.all(node_scores >= 0))

    def test_coupling_strength_effect(self):
        """Test that coupling strength affects results."""
        result_weak = multiplex_pagerank(
            [self.L1, self.L2], variant="additive", c=0.1
        )
        result_strong = multiplex_pagerank(
            [self.L1, self.L2], variant="additive", c=2.0
        )

        # Different coupling strengths should produce different results
        self.assertFalse(
            np.allclose(
                result_weak["node_scores"], result_strong["node_scores"]
            )
        )

    def test_epsilon_prevents_zero_division(self):
        """Test that epsilon prevents numerical issues."""
        # This should not raise any numerical errors
        result = multiplex_pagerank(
            [self.L1, self.L2],
            variant="multiplicative",
            c=1.0,
            epsilon=1e-12,
        )

        self.assertEqual(result["node_scores"].shape, (3,))

    def test_invalid_variant_raises_error(self):
        """Test that invalid variant raises ValueError."""
        with self.assertRaises(ValueError):
            multiplex_pagerank([self.L1, self.L2], variant="invalid")

    def test_empty_layers_raises_error(self):
        """Test that empty layer list raises ValueError."""
        with self.assertRaises(ValueError):
            multiplex_pagerank([])

    def test_inconsistent_layer_sizes_raises_error(self):
        """Test that inconsistent layer sizes raise ValueError."""
        L3 = np.array([[0, 1], [1, 0]], dtype=float)  # 2x2 instead of 3x3
        with self.assertRaises(ValueError):
            multiplex_pagerank([self.L1, L3])

    def test_non_square_layer_raises_error(self):
        """Test that non-square layer raises ValueError."""
        L3 = np.array([[0, 1, 1], [1, 0, 1]], dtype=float)  # 2x3
        with self.assertRaises(ValueError):
            multiplex_pagerank([L3])


class TestMultiplexPageRankProperties(unittest.TestCase):
    """Property-based tests for Multiplex PageRank."""

    def test_node_scores_aggregation(self):
        """Test that node scores are correctly aggregated from replica scores."""
        L1 = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)
        L2 = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)

        result = multiplex_pagerank([L1, L2], variant="neutral")

        # Node scores should equal sum of replica scores
        computed_node_scores = np.sum(result["replica_scores"], axis=1)
        np.testing.assert_allclose(
            result["node_scores"], computed_node_scores, rtol=1e-5
        )

    def test_layer_normalization(self):
        """Test that replica scores are normalized per layer."""
        L1 = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)
        L2 = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)

        result = multiplex_pagerank([L1, L2], variant="additive", c=0.5)

        # Each layer should be normalized
        for ell in range(2):
            layer_sum = np.sum(result["replica_scores"][:, ell])
            self.assertAlmostEqual(layer_sum, 1.0, places=5)

    def test_neutral_is_independent_pagerank(self):
        """Test that neutral variant behaves like independent PageRank per layer."""
        L1 = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)

        result = multiplex_pagerank([L1, L1.copy()], variant="neutral")

        # With identical layers and no coupling, layer scores should be similar
        layer0_scores = result["replica_scores"][:, 0]
        layer1_scores = result["replica_scores"][:, 1]

        np.testing.assert_allclose(layer0_scores, layer1_scores, rtol=1e-4)


class TestIntegration(unittest.TestCase):
    """Integration tests with larger networks."""

    def test_larger_network(self):
        """Test with a larger network (10 nodes, 3 layers)."""
        N = 10
        L = 3

        np.random.seed(42)
        layers = []
        for _ in range(L):
            # Generate random adjacency matrix
            layer = np.random.rand(N, N)
            layer = (layer + layer.T) / 2  # Make symmetric
            np.fill_diagonal(layer, 0)  # Remove self-loops
            layers.append(layer)

        # Test MultiRank
        node_scores, layer_scores = multirank(layers, max_iter=500)

        self.assertEqual(node_scores.shape, (N,))
        self.assertEqual(layer_scores.shape, (L,))
        self.assertAlmostEqual(np.sum(node_scores), 1.0, places=5)

        # Test Multiplex PageRank
        result = multiplex_pagerank(layers, variant="combined", max_iter=500)

        self.assertEqual(result["node_scores"].shape, (N,))
        self.assertEqual(result["replica_scores"].shape, (N, L))

    def test_sparse_network(self):
        """Test with sparse network (few edges)."""
        # Create sparse 5-node network
        L1 = np.zeros((5, 5))
        L1[0, 1] = 1
        L1[1, 0] = 1
        L1[2, 3] = 1
        L1[3, 2] = 1

        L2 = np.zeros((5, 5))
        L2[1, 2] = 1
        L2[2, 1] = 1
        L2[3, 4] = 1
        L2[4, 3] = 1

        # Should not crash
        node_scores, layer_scores = multirank([L1, L2])
        result = multiplex_pagerank([L1, L2], variant="additive")

        self.assertEqual(node_scores.shape, (5,))
        self.assertEqual(result["node_scores"].shape, (5,))


if __name__ == "__main__":
    unittest.main()
