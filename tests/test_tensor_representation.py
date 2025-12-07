#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for tensor representation functionality.

Tests the get_tensor() method which provides sparse tensor representations
of multilayer networks in various sparse matrix formats.
"""

import unittest
import numpy as np

try:
    import scipy.sparse as sp
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

from py3plex.core import random_generators


class TestTensorRepresentation(unittest.TestCase):
    """Test cases for get_tensor() method."""

    def setUp(self):
        """Create sample networks for testing."""
        # Small network for quick tests
        self.small_net = random_generators.random_multilayer_ER(
            10, 2, 0.3, directed=False
        )
        
        # Slightly larger network for format conversion tests
        self.medium_net = random_generators.random_multilayer_ER(
            20, 3, 0.2, directed=False
        )

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy not available")
    def test_get_tensor_default_format(self):
        """Test get_tensor() with default BSR format."""
        tensor = self.small_net.get_tensor()
        
        self.assertIsNotNone(tensor)
        # Should return a sparse matrix
        self.assertTrue(sp.issparse(tensor))
        # Should be square matrix
        self.assertEqual(tensor.shape[0], tensor.shape[1])

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy not available")
    def test_get_tensor_bsr_format(self):
        """Test get_tensor() explicitly requesting BSR format."""
        tensor = self.small_net.get_tensor(sparsity_type='bsr')
        
        self.assertIsNotNone(tensor)
        self.assertTrue(sp.issparse(tensor))

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy not available")
    def test_get_tensor_csr_format(self):
        """Test get_tensor() with CSR (Compressed Sparse Row) format."""
        tensor = self.small_net.get_tensor(sparsity_type='csr')
        
        self.assertIsNotNone(tensor)
        self.assertTrue(sp.issparse(tensor))
        self.assertTrue(sp.isspmatrix_csr(tensor))

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy not available")
    def test_get_tensor_csc_format(self):
        """Test get_tensor() with CSC (Compressed Sparse Column) format."""
        tensor = self.small_net.get_tensor(sparsity_type='csc')
        
        self.assertIsNotNone(tensor)
        self.assertTrue(sp.issparse(tensor))
        self.assertTrue(sp.isspmatrix_csc(tensor))

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy not available")
    def test_get_tensor_coo_format(self):
        """Test get_tensor() with COO (Coordinate) format."""
        tensor = self.small_net.get_tensor(sparsity_type='coo')
        
        self.assertIsNotNone(tensor)
        self.assertTrue(sp.issparse(tensor))
        self.assertTrue(sp.isspmatrix_coo(tensor))

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy not available")
    def test_get_tensor_lil_format(self):
        """Test get_tensor() with LIL (List of Lists) format."""
        tensor = self.small_net.get_tensor(sparsity_type='lil')
        
        self.assertIsNotNone(tensor)
        self.assertTrue(sp.issparse(tensor))
        self.assertTrue(sp.isspmatrix_lil(tensor))

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy not available")
    def test_get_tensor_dok_format(self):
        """Test get_tensor() with DOK (Dictionary of Keys) format."""
        tensor = self.small_net.get_tensor(sparsity_type='dok')
        
        self.assertIsNotNone(tensor)
        self.assertTrue(sp.issparse(tensor))
        self.assertTrue(sp.isspmatrix_dok(tensor))

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy not available")
    def test_get_tensor_consistency(self):
        """Test that different formats represent the same data."""
        tensor_bsr = self.small_net.get_tensor(sparsity_type='bsr')
        tensor_csr = self.small_net.get_tensor(sparsity_type='csr')
        
        # Convert both to dense for comparison
        dense_bsr = tensor_bsr.todense()
        dense_csr = tensor_csr.todense()
        
        # Should be identical
        np.testing.assert_array_equal(dense_bsr, dense_csr)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy not available")
    def test_get_tensor_shape(self):
        """Test that tensor shape matches expected dimensions."""
        tensor = self.small_net.get_tensor()
        
        # Get number of node-layer pairs
        nodes_list = list(self.small_net.get_nodes())
        expected_size = len(nodes_list)
        
        self.assertEqual(tensor.shape[0], expected_size)
        self.assertEqual(tensor.shape[1], expected_size)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy not available")
    def test_get_tensor_multiple_calls(self):
        """Test that multiple calls to get_tensor() work correctly."""
        tensor1 = self.small_net.get_tensor(sparsity_type='csr')
        tensor2 = self.small_net.get_tensor(sparsity_type='csc')
        tensor3 = self.small_net.get_tensor(sparsity_type='bsr')
        
        # All should be non-None and sparse
        self.assertIsNotNone(tensor1)
        self.assertIsNotNone(tensor2)
        self.assertIsNotNone(tensor3)
        
        # All should represent the same data
        dense1 = tensor1.todense()
        dense2 = tensor2.todense()
        dense3 = tensor3.todense()
        
        np.testing.assert_array_equal(dense1, dense2)
        np.testing.assert_array_equal(dense2, dense3)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy not available")
    def test_get_tensor_equivalent_to_supra_adjacency(self):
        """Test that get_tensor() produces same result as get_supra_adjacency_matrix()."""
        tensor = self.small_net.get_tensor(sparsity_type='bsr')
        supra = self.small_net.get_supra_adjacency_matrix(mtype='sparse')
        
        # Convert both to CSR for comparison (standard format)
        tensor_csr = tensor.tocsr()
        supra_csr = supra.tocsr() if hasattr(supra, 'tocsr') else supra
        
        # Should be equivalent
        dense_tensor = tensor_csr.todense()
        dense_supra = supra_csr.todense()
        
        np.testing.assert_array_equal(dense_tensor, dense_supra)

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy not available")
    def test_get_tensor_invalid_format_warning(self):
        """Test that invalid sparse format produces warning and returns matrix anyway."""
        # This should produce a warning but still return a matrix
        with self.assertWarns(UserWarning):
            tensor = self.small_net.get_tensor(sparsity_type='invalid_format')
        
        # Should still get a valid sparse matrix (in whatever format it was stored)
        self.assertIsNotNone(tensor)
        self.assertTrue(sp.issparse(tensor))

    @unittest.skipIf(not SCIPY_AVAILABLE, "scipy not available")
    def test_get_tensor_larger_network(self):
        """Test get_tensor() works correctly on larger network."""
        tensor = self.medium_net.get_tensor(sparsity_type='csr')
        
        self.assertIsNotNone(tensor)
        self.assertTrue(sp.issparse(tensor))
        self.assertTrue(sp.isspmatrix_csr(tensor))
        
        # Verify it's square
        self.assertEqual(tensor.shape[0], tensor.shape[1])
        
        # Verify it has some non-zero entries (network has edges)
        self.assertGreater(tensor.nnz, 0)


if __name__ == "__main__":
    unittest.main()
