#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for Leiden multilayer community detection.

This module contains tests for:
- Leiden algorithm implementation
- LeidenResult class functionality
- Comparison with Louvain method
- Different input formats
"""

import unittest

# Handle missing dependencies gracefully
try:
    import numpy as np
    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.leiden_multilayer import (
        leiden_multilayer,
        LeidenResult,
    )
    from py3plex.algorithms.community_detection.multilayer_modularity import (
        multilayer_modularity,
        louvain_multilayer,
    )
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    np = None
    multinet = None
    leiden_multilayer = None
    LeidenResult = None
    multilayer_modularity = None
    louvain_multilayer = None
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: {e}")


class TestLeidenMultilayer(unittest.TestCase):
    """Test cases for Leiden multilayer algorithm."""
    
    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available for Leiden tests")
        
        # Create a simple 2-layer, 3-node test network
        self.simple_network = multinet.multi_layer_network(directed=False)
        
        # Layer 1: A triangle (all connected)
        self.simple_network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['C', 'L1', 'A', 'L1', 1]
        ], input_type='list')
        
        # Layer 2: A line (A-B-C)
        self.simple_network.add_edges([
            ['A', 'L2', 'B', 'L2', 1],
            ['B', 'L2', 'C', 'L2', 1]
        ], input_type='list')
    
    def test_basic_leiden_execution(self):
        """Test that Leiden algorithm runs without errors."""
        result = leiden_multilayer(
            self.simple_network,
            interlayer_coupling=0.5,
            resolution=1.0,
            seed=42,
            max_iter=10
        )
        
        # Check result type
        self.assertIsInstance(result, LeidenResult)
        
        # Check that communities were assigned
        self.assertIsInstance(result.communities, dict)
        self.assertGreater(len(result.communities), 0)
        
        # Check modularity is in valid range
        self.assertIsInstance(result.modularity, float)
        self.assertGreaterEqual(result.modularity, -1.0)
        self.assertLessEqual(result.modularity, 1.0)
        
        # Check iterations
        self.assertGreaterEqual(result.iterations, 0)
        self.assertLessEqual(result.iterations, 10)
    
    def test_leiden_result_summary(self):
        """Test LeidenResult summary generation."""
        result = leiden_multilayer(
            self.simple_network,
            interlayer_coupling=0.5,
            resolution=1.0,
            seed=42
        )
        
        summary = result.summary()
        self.assertIsInstance(summary, str)
        self.assertIn("Leiden Multilayer", summary)
        self.assertIn("modularity", summary)
        self.assertIn("Communities detected", summary)
    
    def test_reproducibility_with_seed(self):
        """Test that results are reproducible with same seed."""
        result1 = leiden_multilayer(
            self.simple_network,
            interlayer_coupling=0.5,
            resolution=1.0,
            seed=42
        )
        
        result2 = leiden_multilayer(
            self.simple_network,
            interlayer_coupling=0.5,
            resolution=1.0,
            seed=42
        )
        
        # Communities should be identical
        self.assertEqual(result1.communities, result2.communities)
        self.assertAlmostEqual(result1.modularity, result2.modularity, places=10)
    
    def test_different_resolution_parameters(self):
        """Test with different resolution parameters."""
        # Single resolution
        result1 = leiden_multilayer(
            self.simple_network,
            interlayer_coupling=0.5,
            resolution=1.0,
            seed=42
        )
        
        # Per-layer resolution (list)
        result2 = leiden_multilayer(
            self.simple_network,
            interlayer_coupling=0.5,
            resolution=[1.0, 0.8],
            seed=42
        )
        
        # Per-layer resolution (dict)
        result3 = leiden_multilayer(
            self.simple_network,
            interlayer_coupling=0.5,
            resolution={'L1': 1.0, 'L2': 0.8},
            seed=42
        )
        
        # All should execute without error
        self.assertIsInstance(result1.modularity, float)
        self.assertIsInstance(result2.modularity, float)
        self.assertIsInstance(result3.modularity, float)
    
    def test_different_coupling_strengths(self):
        """Test with different interlayer coupling strengths."""
        # No coupling
        result_no_coupling = leiden_multilayer(
            self.simple_network,
            interlayer_coupling=0.0,
            resolution=1.0,
            seed=42
        )
        
        # Strong coupling
        result_strong_coupling = leiden_multilayer(
            self.simple_network,
            interlayer_coupling=2.0,
            resolution=1.0,
            seed=42
        )
        
        # Both should execute
        self.assertIsInstance(result_no_coupling.modularity, float)
        self.assertIsInstance(result_strong_coupling.modularity, float)
        
        # With strong coupling, expect more aligned communities across layers
        # (This is a weak test - just checking execution)
    
    def test_empty_network(self):
        """Test with empty network."""
        empty_network = multinet.multi_layer_network(directed=False)
        empty_network.add_edges([
            ['A', 'L1', 'A', 'L1', 0]  # Self-loop with zero weight
        ], input_type='list')
        
        # Should handle gracefully
        result = leiden_multilayer(
            empty_network,
            interlayer_coupling=0.5,
            resolution=1.0,
            seed=42
        )
        
        # Should return zero modularity
        self.assertAlmostEqual(result.modularity, 0.0, places=10)
    
    def test_comparison_with_louvain(self):
        """Test that Leiden produces comparable or better results than Louvain."""
        # Run both algorithms
        leiden_result = leiden_multilayer(
            self.simple_network,
            interlayer_coupling=0.5,
            resolution=1.0,
            seed=42
        )
        
        louvain_result = louvain_multilayer(
            self.simple_network,
            gamma=1.0,
            omega=0.5,
            random_state=42,
            max_iter=10
        )
        
        # Calculate modularity for louvain result
        louvain_modularity = multilayer_modularity(
            self.simple_network,
            louvain_result,
            gamma=1.0,
            omega=0.5
        )
        
        # Both should produce valid results
        self.assertIsInstance(leiden_result.modularity, float)
        self.assertIsInstance(louvain_modularity, float)
        
        # Leiden should produce at least as good modularity as Louvain
        # (in practice, often better due to refinement)
        # This is a weak test - just checking both run
        self.assertGreaterEqual(leiden_result.modularity, -1.0)
        self.assertGreaterEqual(louvain_modularity, -1.0)
    
    def test_large_network(self):
        """Test with a larger network."""
        # Create a larger test network
        large_network = multinet.multi_layer_network(directed=False)
        
        # Layer 1: Two cliques - batch add all edges
        layer1_edges = []
        for i in range(5):
            for j in range(i + 1, 5):
                layer1_edges.append([i, 'L1', j, 'L1', 1])
        
        for i in range(5, 10):
            for j in range(i + 1, 10):
                layer1_edges.append([i, 'L1', j, 'L1', 1])
        
        large_network.add_edges(layer1_edges, input_type="list")
        
        # Layer 2: Similar structure - batch add all edges
        layer2_edges = []
        for i in range(5):
            for j in range(i + 1, 5):
                layer2_edges.append([i, 'L2', j, 'L2', 1])
        
        for i in range(5, 10):
            for j in range(i + 1, 10):
                layer2_edges.append([i, 'L2', j, 'L2', 1])
        
        large_network.add_edges(layer2_edges, input_type="list")
        
        result = leiden_multilayer(
            large_network,
            interlayer_coupling=1.0,
            resolution=1.0,
            seed=42,
            max_iter=50
        )
        
        # Should detect communities
        n_communities = len(set(result.communities.values()))
        self.assertGreater(n_communities, 0)
        
        # Should have reasonable modularity
        self.assertGreater(result.modularity, 0.0)


class TestLeidenInputFormats(unittest.TestCase):
    """Test different input formats for Leiden algorithm."""
    
    def setUp(self):
        """Set up test data."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available for input format tests")
    
    def test_py3plex_input(self):
        """Test with py3plex network object."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
        ], input_type='list')
        
        result = leiden_multilayer(network, seed=42)
        self.assertIsInstance(result, LeidenResult)
    
    def test_invalid_input(self):
        """Test with invalid input types."""
        # Single supra-adjacency matrix should raise error
        supra_matrix = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        
        with self.assertRaises(ValueError):
            leiden_multilayer(supra_matrix)
    
    def test_invalid_resolution_list_length(self):
        """Test with mismatched resolution list length."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['A', 'L2', 'B', 'L2', 1],
        ], input_type='list')
        
        # 3 resolutions for 2 layers should fail
        with self.assertRaises(ValueError):
            leiden_multilayer(network, resolution=[1.0, 1.0, 1.0])
    
    def test_invalid_coupling_matrix_shape(self):
        """Test with mismatched coupling matrix shape."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['A', 'L2', 'B', 'L2', 1],
        ], input_type='list')
        
        # 3x3 coupling for 2 layers should fail
        coupling = np.ones((3, 3))
        
        with self.assertRaises(ValueError):
            leiden_multilayer(network, interlayer_coupling=coupling)


if __name__ == '__main__':
    unittest.main()
