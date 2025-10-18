#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for supra matrix function centrality measures.

This module tests the communicability and Katz centrality implementations
for multilayer networks using the supra-adjacency matrix.
"""

import unittest

import numpy as np
import scipy.sparse as sp

from py3plex.algorithms.multilayer_algorithms.supra_matrix_function_centrality import (
    communicability_centrality,
    katz_centrality,
)
from py3plex.core import random_generators
from py3plex.exceptions import Py3plexMatrixError


class TestCommunicabilityCentrality(unittest.TestCase):
    """Test cases for communicability centrality."""

    def test_communicability_centrality_sparse_small(self):
        """Test communicability centrality on small sparse network."""
        # Create a simple 3-node, 2-layer network
        net = random_generators.random_multiplex_ER(3, 2, 0.5, directed=False)
        A = net.get_supra_adjacency_matrix()

        comm = communicability_centrality(A, normalize=True)

        # Check shape and type
        self.assertIsInstance(comm, np.ndarray)
        self.assertEqual(len(comm), A.shape[0])

        # Check normalization
        self.assertAlmostEqual(np.sum(comm), 1.0, places=5)

        # Check all values are non-negative
        self.assertTrue(np.all(comm >= 0))

    def test_communicability_centrality_sparse_medium(self):
        """Test communicability centrality on medium sparse network."""
        net = random_generators.random_multiplex_ER(50, 3, 0.1, directed=False)
        A = net.get_supra_adjacency_matrix()

        comm = communicability_centrality(A, normalize=True, use_sparse=True)

        # Check shape
        self.assertEqual(len(comm), A.shape[0])

        # Check normalization
        self.assertAlmostEqual(np.sum(comm), 1.0, places=5)

        # Check all values are positive (should be > 0 for connected network)
        self.assertTrue(np.all(comm > 0))

    def test_communicability_centrality_dense_fallback(self):
        """Test communicability centrality with dense fallback."""
        net = random_generators.random_multiplex_ER(10, 2, 0.3, directed=False)
        A = net.get_supra_adjacency_matrix()

        # Force dense computation
        comm = communicability_centrality(A, normalize=True, use_sparse=False)

        # Check shape
        self.assertEqual(len(comm), A.shape[0])

        # Check normalization
        self.assertAlmostEqual(np.sum(comm), 1.0, places=5)

        # Check all values are non-negative
        self.assertTrue(np.all(comm >= 0))

    def test_communicability_centrality_unnormalized(self):
        """Test communicability centrality without normalization."""
        net = random_generators.random_multiplex_ER(10, 2, 0.3, directed=False)
        A = net.get_supra_adjacency_matrix()

        comm = communicability_centrality(A, normalize=False)

        # Check shape
        self.assertEqual(len(comm), A.shape[0])

        # Check all values are non-negative
        self.assertTrue(np.all(comm >= 0))

        # Sum should not be exactly 1 (since not normalized)
        # but should be positive
        self.assertGreater(np.sum(comm), 0)

    def test_communicability_centrality_empty_matrix(self):
        """Test communicability centrality with empty matrix."""
        empty_matrix = sp.csr_matrix((0, 0))

        with self.assertRaises(Py3plexMatrixError):
            communicability_centrality(empty_matrix)

    def test_communicability_centrality_non_square_matrix(self):
        """Test communicability centrality with non-square matrix."""
        non_square = sp.csr_matrix(np.random.rand(5, 3))

        with self.assertRaises(Py3plexMatrixError):
            communicability_centrality(non_square)

    def test_communicability_centrality_none_matrix(self):
        """Test communicability centrality with None matrix."""
        with self.assertRaises(Py3plexMatrixError):
            communicability_centrality(None)

    def test_communicability_centrality_consistency(self):
        """Test that sparse and dense computations give similar results."""
        net = random_generators.random_multiplex_ER(8, 2, 0.4, directed=False)
        A = net.get_supra_adjacency_matrix()

        # Compute with both methods
        comm_sparse = communicability_centrality(A, normalize=True, use_sparse=True)
        comm_dense = communicability_centrality(A, normalize=True, use_sparse=False)

        # They should be very close
        np.testing.assert_allclose(comm_sparse, comm_dense, rtol=1e-4, atol=1e-6)


class TestKatzCentrality(unittest.TestCase):
    """Test cases for Katz centrality."""

    def test_katz_centrality_auto_alpha(self):
        """Test Katz centrality with automatic alpha calculation."""
        net = random_generators.random_multiplex_ER(50, 3, 0.1, directed=False)
        A = net.get_supra_adjacency_matrix()

        katz = katz_centrality(A, alpha=None)

        # Check shape
        self.assertEqual(len(katz), A.shape[0])

        # Check normalization (should sum to 1)
        self.assertAlmostEqual(np.sum(katz), 1.0, places=5)

        # Check all values are positive
        self.assertTrue(np.all(katz > 0))

    def test_katz_centrality_manual_alpha(self):
        """Test Katz centrality with manually specified alpha."""
        net = random_generators.random_multiplex_ER(20, 2, 0.2, directed=False)
        A = net.get_supra_adjacency_matrix()

        # Use a small alpha value to ensure convergence
        katz = katz_centrality(A, alpha=0.05, beta=1.0)

        # Check shape
        self.assertEqual(len(katz), A.shape[0])

        # Check normalization
        self.assertAlmostEqual(np.sum(katz), 1.0, places=5)

        # Check all values are positive
        self.assertTrue(np.all(katz > 0))

    def test_katz_centrality_different_beta(self):
        """Test Katz centrality with different beta values."""
        net = random_generators.random_multiplex_ER(15, 2, 0.3, directed=False)
        A = net.get_supra_adjacency_matrix()

        katz_beta1 = katz_centrality(A, alpha=0.05, beta=1.0)
        katz_beta2 = katz_centrality(A, alpha=0.05, beta=2.0)

        # Check that both are normalized to sum to 1
        self.assertAlmostEqual(np.sum(katz_beta1), 1.0, places=5)
        self.assertAlmostEqual(np.sum(katz_beta2), 1.0, places=5)

        # The relative ordering should be the same
        order1 = np.argsort(katz_beta1)
        order2 = np.argsort(katz_beta2)
        np.testing.assert_array_equal(order1, order2)

    def test_katz_centrality_small_network(self):
        """Test Katz centrality on small network."""
        net = random_generators.random_multiplex_ER(5, 2, 0.4, directed=False)
        A = net.get_supra_adjacency_matrix()

        katz = katz_centrality(A)

        # Check shape
        self.assertEqual(len(katz), A.shape[0])

        # Check normalization
        self.assertAlmostEqual(np.sum(katz), 1.0, places=5)

        # Check all values are non-negative
        self.assertTrue(np.all(katz >= 0))

    def test_katz_centrality_empty_matrix(self):
        """Test Katz centrality with empty matrix."""
        empty_matrix = sp.csr_matrix((0, 0))

        with self.assertRaises(Py3plexMatrixError):
            katz_centrality(empty_matrix)

    def test_katz_centrality_non_square_matrix(self):
        """Test Katz centrality with non-square matrix."""
        non_square = sp.csr_matrix(np.random.rand(5, 3))

        with self.assertRaises(Py3plexMatrixError):
            katz_centrality(non_square)

    def test_katz_centrality_none_matrix(self):
        """Test Katz centrality with None matrix."""
        with self.assertRaises(Py3plexMatrixError):
            katz_centrality(None)


class TestCombinedCentralities(unittest.TestCase):
    """Test cases comparing both centrality measures."""

    def test_communicability_and_katz_shapes(self):
        """Test that both centralities return same shape."""
        net = random_generators.random_multiplex_ER(30, 3, 0.15, directed=False)
        A = net.get_supra_adjacency_matrix()

        comm = communicability_centrality(A)
        katz = katz_centrality(A)

        self.assertEqual(comm.shape, katz.shape)
        self.assertEqual(len(comm), A.shape[0])

    def test_communicability_and_katz_positive(self):
        """Test that both centralities produce positive values."""
        net = random_generators.random_multiplex_ER(25, 2, 0.2, directed=False)
        A = net.get_supra_adjacency_matrix()

        comm = communicability_centrality(A)
        katz = katz_centrality(A)

        self.assertTrue(np.all(comm > 0))
        self.assertTrue(np.all(katz > 0))

    def test_communicability_and_katz_normalized(self):
        """Test that both centralities are properly normalized."""
        net = random_generators.random_multiplex_ER(20, 2, 0.25, directed=False)
        A = net.get_supra_adjacency_matrix()

        comm = communicability_centrality(A, normalize=True)
        katz = katz_centrality(A)

        self.assertAlmostEqual(np.sum(comm), 1.0, places=5)
        self.assertAlmostEqual(np.sum(katz), 1.0, places=5)

    def test_centralities_reproducible(self):
        """Test that centralities are reproducible with same input."""
        net = random_generators.random_multiplex_ER(15, 2, 0.3, directed=False)
        A = net.get_supra_adjacency_matrix()

        # Compute twice
        comm1 = communicability_centrality(A, normalize=True)
        comm2 = communicability_centrality(A, normalize=True)

        katz1 = katz_centrality(A, alpha=0.05)
        katz2 = katz_centrality(A, alpha=0.05)

        # Should be identical
        np.testing.assert_array_equal(comm1, comm2)
        np.testing.assert_array_equal(katz1, katz2)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def test_single_node_network(self):
        """Test centralities on single node network."""
        # Create a 1x1 matrix
        single_node = sp.csr_matrix([[0]])

        comm = communicability_centrality(single_node, normalize=True)
        katz = katz_centrality(single_node, alpha=0.1)

        # Should have length 1
        self.assertEqual(len(comm), 1)
        self.assertEqual(len(katz), 1)

        # Should be normalized to 1
        self.assertAlmostEqual(comm[0], 1.0, places=5)
        self.assertAlmostEqual(katz[0], 1.0, places=5)

    def test_disconnected_network(self):
        """Test centralities on disconnected network."""
        # Create a block diagonal matrix (2 disconnected components)
        block1 = np.array([[0, 1], [1, 0]])
        block2 = np.array([[0, 1], [1, 0]])
        disconnected = sp.block_diag([block1, block2], format="csr")

        comm = communicability_centrality(disconnected, normalize=True)
        katz = katz_centrality(disconnected)

        # Should have correct length
        self.assertEqual(len(comm), 4)
        self.assertEqual(len(katz), 4)

        # All values should be positive
        self.assertTrue(np.all(comm > 0))
        self.assertTrue(np.all(katz > 0))

        # Should be normalized
        self.assertAlmostEqual(np.sum(comm), 1.0, places=5)
        self.assertAlmostEqual(np.sum(katz), 1.0, places=5)

    def test_directed_network(self):
        """Test centralities on directed network."""
        net = random_generators.random_multiplex_ER(20, 2, 0.2, directed=True)
        A = net.get_supra_adjacency_matrix()

        comm = communicability_centrality(A, normalize=True)
        katz = katz_centrality(A)

        # Should work fine with directed networks
        self.assertEqual(len(comm), A.shape[0])
        self.assertEqual(len(katz), A.shape[0])

        # Should be normalized
        self.assertAlmostEqual(np.sum(comm), 1.0, places=5)
        self.assertAlmostEqual(np.sum(katz), 1.0, places=5)


class TestPerformance(unittest.TestCase):
    """Performance and stress tests."""

    @unittest.skip("Slow test - run manually for benchmarking")
    def test_large_network_communicability(self):
        """Benchmark communicability centrality on large network."""
        net = random_generators.random_multiplex_ER(200, 3, 0.05, directed=False)
        A = net.get_supra_adjacency_matrix()

        import time

        start = time.time()
        comm = communicability_centrality(A, normalize=True, use_sparse=True)
        elapsed = time.time() - start

        print(f"Communicability computation took {elapsed:.2f} seconds")

        # Should complete and return valid results
        self.assertEqual(len(comm), A.shape[0])
        self.assertAlmostEqual(np.sum(comm), 1.0, places=5)

    @unittest.skip("Slow test - run manually for benchmarking")
    def test_large_network_katz(self):
        """Benchmark Katz centrality on large network."""
        net = random_generators.random_multiplex_ER(200, 3, 0.05, directed=False)
        A = net.get_supra_adjacency_matrix()

        import time

        start = time.time()
        katz = katz_centrality(A, alpha=None)
        elapsed = time.time() - start

        print(f"Katz computation took {elapsed:.2f} seconds")

        # Should complete and return valid results
        self.assertEqual(len(katz), A.shape[0])
        self.assertAlmostEqual(np.sum(katz), 1.0, places=5)


if __name__ == "__main__":
    unittest.main()
