#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for versatility (multilayer eigenvector centrality).

This module contains comprehensive tests for the versatility implementation,
validating correctness, edge cases, and robustness as specified in the
multilayer eigenvector centrality formulation.
"""

import unittest

# Handle missing dependencies gracefully
try:
    import numpy as np
    import scipy.sparse as sp
    from py3plex.algorithms.multilayer_algorithms.versatility import (
        build_supra_adjacency,
        versatility,
        versatility_katz,
        _power_iteration,
    )
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    np = None
    sp = None
    build_supra_adjacency = None
    versatility = None
    versatility_katz = None
    _power_iteration = None
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: {e}")


def skip_if_no_deps(test_func):
    """Decorator to skip tests when dependencies are missing."""
    if not DEPENDENCIES_AVAILABLE:
        return unittest.skip("Dependencies not available")(test_func)
    return test_func


class TestSupraAdjacency(unittest.TestCase):
    """Test cases for supra-adjacency matrix construction."""
    
    def setUp(self):
        """Set up test matrices."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        
        # Simple 3-node networks
        self.L1 = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        self.L2 = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
    
    @skip_if_no_deps
    def test_scalar_interlayer(self):
        """Test supra-adjacency construction with scalar interlayer coupling."""
        S = build_supra_adjacency([self.L1, self.L2], interlayer=0.1)
        
        # Check shape
        self.assertEqual(S.shape, (6, 6))
        
        # Check diagonal blocks contain layer adjacencies
        np.testing.assert_array_equal(S[:3, :3].toarray(), self.L1.toarray())
        np.testing.assert_array_equal(S[3:, 3:].toarray(), self.L2.toarray())
        
        # Check off-diagonal blocks are identity * 0.1
        expected_coupling = np.eye(3) * 0.1
        np.testing.assert_array_almost_equal(S[:3, 3:].toarray(), expected_coupling)
        np.testing.assert_array_almost_equal(S[3:, :3].toarray(), expected_coupling)
    
    @skip_if_no_deps
    def test_dict_interlayer(self):
        """Test supra-adjacency with dictionary interlayer specification."""
        # Custom coupling between layers
        coupling_01 = sp.csr_matrix([[0.5, 0, 0], [0, 0.5, 0], [0, 0, 0.5]])
        coupling_10 = sp.csr_matrix([[0.2, 0, 0], [0, 0.2, 0], [0, 0, 0.2]])
        
        S = build_supra_adjacency(
            [self.L1, self.L2],
            interlayer={(0, 1): coupling_01, (1, 0): coupling_10}
        )
        
        # Check off-diagonal blocks
        np.testing.assert_array_almost_equal(S[:3, 3:].toarray(), coupling_01.toarray())
        np.testing.assert_array_almost_equal(S[3:, :3].toarray(), coupling_10.toarray())
    
    @skip_if_no_deps
    def test_single_layer(self):
        """Test that single layer works correctly."""
        S = build_supra_adjacency([self.L1], interlayer=0.0)
        
        # Should just be the layer itself
        np.testing.assert_array_equal(S.toarray(), self.L1.toarray())
    
    @skip_if_no_deps
    def test_invalid_dimensions(self):
        """Test error handling for mismatched layer dimensions."""
        L_wrong = sp.csr_matrix([[0, 1], [1, 0]])  # 2x2 instead of 3x3
        
        with self.assertRaises(ValueError):
            build_supra_adjacency([self.L1, L_wrong], interlayer=0.1)
    
    @skip_if_no_deps
    def test_non_square_layer(self):
        """Test error handling for non-square matrices."""
        L_nonsquare = sp.csr_matrix([[0, 1, 0]])  # 1x3
        
        with self.assertRaises(ValueError):
            build_supra_adjacency([L_nonsquare], interlayer=0.1)


class TestVersatility(unittest.TestCase):
    """Test cases for versatility computation."""
    
    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
    
    @skip_if_no_deps
    def test_single_layer_equals_eigenvector_centrality(self):
        """T1: Single layer should equal standard eigenvector centrality."""
        # Triangle graph - all nodes equally central
        L = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        
        v = versatility([L], interlayer=0.0, normalize="l1", seed=42)
        
        # For a symmetric triangle, all nodes should have equal centrality
        np.testing.assert_array_almost_equal(v, np.ones(3) / 3, decimal=5)
    
    @skip_if_no_deps
    def test_single_layer_star_graph(self):
        """Test single layer star graph (one hub, multiple spokes)."""
        # Star graph: node 0 is the hub
        L = sp.csr_matrix([
            [0, 1, 1, 1],
            [1, 0, 0, 0],
            [1, 0, 0, 0],
            [1, 0, 0, 0]
        ])
        
        v = versatility([L], interlayer=0.0, normalize="l1", seed=42)
        
        # Hub should have highest centrality
        self.assertGreater(v[0], v[1])
        self.assertGreater(v[0], v[2])
        self.assertGreater(v[0], v[3])
        
        # Spokes should have equal centrality
        np.testing.assert_almost_equal(v[1], v[2])
        np.testing.assert_almost_equal(v[2], v[3])
    
    @skip_if_no_deps
    def test_layer_permutation_invariance(self):
        """T2: Layer permutation should not change node rankings."""
        L1 = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        L2 = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        
        v1 = versatility([L1, L2], interlayer=0.1, normalize="l1", seed=42)
        v2 = versatility([L2, L1], interlayer=0.1, normalize="l1", seed=42)
        
        # Versatility should be the same regardless of layer order
        np.testing.assert_array_almost_equal(v1, v2, decimal=5)
    
    @skip_if_no_deps
    def test_omega_sweep(self):
        """T3: Omega sweep - increasing omega should blend layer rankings."""
        # Layer 1: node 0 is strongly central (star with degree 3)
        L1 = sp.csr_matrix([
            [0, 2, 2, 2],
            [2, 0, 0, 0],
            [2, 0, 0, 0],
            [2, 0, 0, 0]
        ])
        
        # Layer 2: node 1 is weakly central (star with degree 3, but lower weights)
        L2 = sp.csr_matrix([
            [0, 1, 0, 0],
            [1, 0, 1, 1],
            [0, 1, 0, 0],
            [0, 1, 0, 0]
        ])
        
        # Small omega: should be dominated by stronger layer (L1)
        v_small = versatility([L1, L2], interlayer=0.01, normalize="l1", seed=42, max_iter=2000)
        
        # Large omega: should blend the two layers
        v_large = versatility([L1, L2], interlayer=1.0, normalize="l1", seed=42, max_iter=2000)
        
        # At small omega, node 0 should dominate (central in the stronger layer)
        self.assertGreater(v_small[0], v_small[1])
        
        # At large omega, centrality should be more balanced
        # (the exact behavior depends on the coupling strength)
        # Here we just check that omega affects the results significantly
        self.assertFalse(np.allclose(v_small, v_large, atol=0.01))
    
    @skip_if_no_deps
    def test_missing_nodes(self):
        """T4: Nodes absent from some layers (zero rows/cols) should not cause NaNs."""
        # Layer 1: all 4 nodes present
        L1 = sp.csr_matrix([
            [0, 1, 1, 0],
            [1, 0, 0, 1],
            [1, 0, 0, 1],
            [0, 1, 1, 0]
        ])
        
        # Layer 2: node 3 is isolated (zero row/column)
        L2 = sp.csr_matrix([
            [0, 1, 0, 0],
            [1, 0, 1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 0]
        ])
        
        v = versatility([L1, L2], interlayer=0.1, normalize="l1", seed=42)
        
        # Should not have NaNs
        self.assertFalse(np.any(np.isnan(v)))
        self.assertFalse(np.any(np.isinf(v)))
        
        # Node 3 should have some centrality from layer 1
        self.assertGreater(v[3], 0)
    
    @skip_if_no_deps
    def test_directed_weighted(self):
        """T5: Directed weighted networks should converge without errors."""
        # Directed weighted layer 1
        L1 = sp.csr_matrix([
            [0, 2, 0],
            [0, 0, 3],
            [1, 0, 0]
        ])
        
        # Directed weighted layer 2
        L2 = sp.csr_matrix([
            [0, 1, 2],
            [0, 0, 1],
            [0, 0, 0]
        ])
        
        v = versatility([L1, L2], interlayer=0.5, normalize="l1", seed=42)
        
        # Should be non-negative
        self.assertTrue(np.all(v >= 0))
        
        # Should sum to 1 (l1 normalization)
        np.testing.assert_almost_equal(v.sum(), 1.0)
    
    @skip_if_no_deps
    def test_return_layer_scores(self):
        """Test that return_layer_scores returns correct shapes."""
        L1 = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        L2 = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        
        v, X = versatility([L1, L2], interlayer=0.1, return_layer_scores=True, seed=42)
        
        # Check shapes
        self.assertEqual(v.shape, (3,))
        self.assertEqual(X.shape, (3, 2))
        
        # Verify that v is the sum of X over layers (both normalized)
        # Since versatility normalizes v, we need to compare normalized versions
        v_unnorm = X.sum(axis=1)
        np.testing.assert_array_almost_equal(v, v_unnorm / v_unnorm.sum())
    
    @skip_if_no_deps
    def test_normalization_options(self):
        """Test different normalization options."""
        L1 = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        L2 = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        
        # L1 normalization
        v_l1 = versatility([L1, L2], interlayer=0.1, normalize="l1", seed=42)
        np.testing.assert_almost_equal(v_l1.sum(), 1.0)
        
        # L2 normalization
        v_l2 = versatility([L1, L2], interlayer=0.1, normalize="l2", seed=42)
        np.testing.assert_almost_equal(np.linalg.norm(v_l2), 1.0)
        
        # No normalization
        v_none = versatility([L1, L2], interlayer=0.1, normalize=None, seed=42)
        # Should still be proportional
        np.testing.assert_array_almost_equal(v_l1 / v_l1.sum(), v_none / v_none.sum())
    
    @skip_if_no_deps
    def test_scipy_eigs_fallback(self):
        """Test that scipy.sparse.linalg.eigs fallback works."""
        L1 = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        L2 = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        
        v1 = versatility([L1, L2], interlayer=0.1, use_scipy_eigs=False, seed=42)
        v2 = versatility([L1, L2], interlayer=0.1, use_scipy_eigs=True, seed=42)
        
        # Results should be similar (may differ slightly due to different algorithms)
        np.testing.assert_array_almost_equal(v1, v2, decimal=3)


class TestVersatilityKatz(unittest.TestCase):
    """Test cases for Katz-based versatility."""
    
    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
    
    @skip_if_no_deps
    def test_basic_katz(self):
        """Test basic Katz versatility computation."""
        L1 = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        L2 = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        
        v = versatility_katz([L1, L2], interlayer=0.1, alpha=0.1, normalize="l1")
        
        # Should be non-negative
        self.assertTrue(np.all(v >= 0))
        
        # Should sum to 1
        np.testing.assert_almost_equal(v.sum(), 1.0)
    
    @skip_if_no_deps
    def test_katz_auto_alpha(self):
        """Test Katz with automatic alpha selection."""
        L1 = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
        L2 = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        
        v = versatility_katz([L1, L2], interlayer=0.1, alpha=None, normalize="l1")
        
        # Should converge without errors
        self.assertTrue(np.all(v >= 0))
        np.testing.assert_almost_equal(v.sum(), 1.0)
    
    @skip_if_no_deps
    def test_katz_disconnected_graph(self):
        """Test Katz on a graph with disconnected component."""
        # Layer 1: nodes 0,1 connected; node 2 isolated
        L1 = sp.csr_matrix([
            [0, 1, 0],
            [1, 0, 0],
            [0, 0, 0]
        ])
        
        # Layer 2: nodes 1,2 connected; node 0 isolated
        L2 = sp.csr_matrix([
            [0, 0, 0],
            [0, 0, 1],
            [0, 1, 0]
        ])
        
        # Katz should handle this better than standard eigenvector
        v = versatility_katz([L1, L2], interlayer=0.1, alpha=0.1, normalize="l1")
        
        # Should not have NaNs
        self.assertFalse(np.any(np.isnan(v)))
        
        # All nodes should have some centrality due to interlayer coupling
        self.assertTrue(np.all(v > 0))


class TestPowerIteration(unittest.TestCase):
    """Test cases for power iteration helper."""
    
    def setUp(self):
        """Set up test matrices."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
    
    @skip_if_no_deps
    def test_simple_convergence(self):
        """Test that power iteration converges on a simple matrix."""
        # Simple symmetric matrix with clear dominant eigenvector
        A = sp.csr_matrix([
            [0, 1, 1],
            [1, 0, 1],
            [1, 1, 0]
        ])
        
        x = _power_iteration(A, tol=1e-9, max_iter=1000, seed=42)
        
        # Should be non-negative
        self.assertTrue(np.all(x >= 0))
        
        # Should be normalized
        np.testing.assert_almost_equal(x.sum(), 1.0)
    
    @skip_if_no_deps
    def test_zero_matrix_error(self):
        """Test that zero matrix raises error."""
        A = sp.csr_matrix((3, 3))
        
        with self.assertRaises(ValueError):
            _power_iteration(A, tol=1e-9, max_iter=1000, seed=42)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up test data."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
    
    @skip_if_no_deps
    def test_empty_layer_list(self):
        """Test that empty layer list raises error."""
        with self.assertRaises(ValueError):
            versatility([], interlayer=0.1)
    
    @skip_if_no_deps
    def test_invalid_normalization(self):
        """Test that invalid normalization option raises error."""
        L = sp.csr_matrix([[0, 1], [1, 0]])
        
        with self.assertRaises(ValueError):
            versatility([L], interlayer=0.0, normalize="invalid")
    
    @skip_if_no_deps
    def test_single_node(self):
        """Test single-node network."""
        L1 = sp.csr_matrix([[0]])
        L2 = sp.csr_matrix([[0]])
        
        # With interlayer coupling, should still work
        v = versatility([L1, L2], interlayer=0.1, seed=42)
        
        # Single node should have all centrality
        self.assertEqual(len(v), 1)
        np.testing.assert_almost_equal(v[0], 1.0)
    
    @skip_if_no_deps
    def test_two_nodes(self):
        """Test two-node network."""
        L1 = sp.csr_matrix([[0, 1], [1, 0]])
        L2 = sp.csr_matrix([[0, 1], [1, 0]])
        
        v = versatility([L1, L2], interlayer=0.1, seed=42)
        
        # Both nodes should have equal centrality
        np.testing.assert_almost_equal(v[0], v[1])


if __name__ == '__main__':
    unittest.main()
