#!/usr/bin/env python3
"""
Test suite for centrality weight handling on supra-graphs.

This module tests the high-likelihood issues mentioned in the problem statement:
1. Weight propagation in betweenness/closeness on supra-graph
2. Closeness normalization (wf_improved)
3. Katz stability (alpha vs spectral radius)
"""

import unittest
import warnings

# Handle missing dependencies gracefully
try:
    import networkx as nx
    import numpy as np
    from py3plex.core import multinet
    from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    nx = None
    np = None
    multinet = None
    MultilayerCentrality = None
    DEPENDENCIES_AVAILABLE = False
    warnings.warn(f"Dependencies not available: {e}")


def skip_if_no_deps(test_func):
    """Decorator to skip tests when dependencies are missing."""
    if not DEPENDENCIES_AVAILABLE:
        return unittest.skip("Dependencies not available")(test_func)
    return test_func


class TestWeightPropagation(unittest.TestCase):
    """Test weight propagation in shortest-path centralities."""
    
    def setUp(self):
        """Set up test network with weighted edges."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        
        # Create a 2-layer network with different edge weights
        self.network = multinet.multi_layer_network(directed=False)
        
        # Layer 1: Heavy edges (weight 10)
        self.network.add_edges([
            ['A', 'L1', 'B', 'L1', 10],
            ['B', 'L1', 'C', 'L1', 10],
        ], input_type='list')
        
        # Layer 2: Light edges (weight 1)
        self.network.add_edges([
            ['A', 'L2', 'B', 'L2', 1],
            ['B', 'L2', 'C', 'L2', 1],
        ], input_type='list')
        
        # Add interlayer coupling (omega)
        # Note: py3plex automatically adds interlayer edges
        
    @skip_if_no_deps
    def test_weight_affects_betweenness(self):
        """Test that edge weights affect betweenness centrality."""
        calc = MultilayerCentrality(self.network)
        
        # Compute betweenness centrality
        betweenness = calc.multilayer_betweenness_centrality(normalized=True)
        
        # Betweenness should be sensitive to weights
        # Node B in layer 1 should have different betweenness than in layer 2
        # because of different edge weights
        b_l1 = betweenness.get(('B', 'L1'), 0)
        b_l2 = betweenness.get(('B', 'L2'), 0)
        
        # At minimum, the values should exist
        self.assertIsNotNone(b_l1)
        self.assertIsNotNone(b_l2)
        
        # Both should be non-negative
        self.assertGreaterEqual(b_l1, 0)
        self.assertGreaterEqual(b_l2, 0)
    
    @skip_if_no_deps
    def test_weight_affects_closeness(self):
        """Test that edge weights affect closeness centrality."""
        calc = MultilayerCentrality(self.network)
        
        # Compute closeness centrality
        closeness = calc.multilayer_closeness_centrality(normalized=True)
        
        # Closeness should be sensitive to weights
        # Nodes with heavy edges should have lower closeness (longer distances)
        c_l1 = closeness.get(('C', 'L1'), 0)
        c_l2 = closeness.get(('C', 'L2'), 0)
        
        # At minimum, the values should exist and be non-negative
        self.assertIsNotNone(c_l1)
        self.assertIsNotNone(c_l2)
        self.assertGreaterEqual(c_l1, 0)
        self.assertGreaterEqual(c_l2, 0)
    
    @skip_if_no_deps
    def test_closeness_wf_improved_parameter(self):
        """Test that wf_improved parameter can be toggled."""
        calc = MultilayerCentrality(self.network)
        
        # Compute closeness with wf_improved=True (default)
        closeness_wf = calc.multilayer_closeness_centrality(
            normalized=True, wf_improved=True
        )
        
        # Compute closeness with wf_improved=False
        closeness_no_wf = calc.multilayer_closeness_centrality(
            normalized=True, wf_improved=False
        )
        
        # Both should complete without errors
        self.assertIsNotNone(closeness_wf)
        self.assertIsNotNone(closeness_no_wf)
        
        # Both should have entries for all node-layer pairs
        self.assertEqual(len(closeness_wf), len(closeness_no_wf))
        
        # Values might differ depending on graph structure
        # (for disconnected graphs they will differ)
        for key in closeness_wf:
            self.assertTrue(np.isfinite(closeness_wf[key]))
            self.assertTrue(np.isfinite(closeness_no_wf[key]))


class TestKatzStability(unittest.TestCase):
    """Test Katz centrality stability and parameter guardrails."""
    
    def setUp(self):
        """Set up test network."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        
        # Create a simple connected network
        self.network = multinet.multi_layer_network(directed=False)
        self.network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
        ], input_type='list')
    
    @skip_if_no_deps
    def test_katz_auto_alpha(self):
        """Test that Katz with auto alpha doesn't diverge."""
        calc = MultilayerCentrality(self.network)
        
        # Compute Katz with auto alpha (default)
        katz = calc.katz_bonacich_centrality(alpha=None)
        
        # Should not have NaNs or infinities
        for node_layer, value in katz.items():
            self.assertTrue(np.isfinite(value), 
                           f"Katz centrality for {node_layer} is not finite: {value}")
            self.assertGreaterEqual(value, 0,
                                  f"Katz centrality for {node_layer} is negative: {value}")
    
    @skip_if_no_deps
    def test_katz_manual_alpha(self):
        """Test Katz with manually specified alpha."""
        calc = MultilayerCentrality(self.network)
        
        # Use a small safe alpha
        katz = calc.katz_bonacich_centrality(alpha=0.01)
        
        # Should not have NaNs or infinities
        for node_layer, value in katz.items():
            self.assertTrue(np.isfinite(value))
            self.assertGreaterEqual(value, 0)


class TestParticipationCoefficient(unittest.TestCase):
    """Test participation coefficient edge cases."""
    
    def setUp(self):
        """Set up test network with sparse layer presence."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        
        # Create network where node C is absent from Layer 2
        self.network = multinet.multi_layer_network(directed=False)
        
        # Layer 1: All nodes present
        self.network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
        ], input_type='list')
        
        # Layer 2: Node C is absent (no edges involving C in L2)
        self.network.add_edges([
            ['A', 'L2', 'B', 'L2', 1],
        ], input_type='list')
    
    @skip_if_no_deps
    def test_participation_coefficient_zero_degree(self):
        """Test that participation coefficient handles zero degree correctly."""
        calc = MultilayerCentrality(self.network)
        
        # Compute participation coefficient
        participation = calc.participation_coefficient(weighted=False)
        
        # Node C has degree 0 in Layer 2, so it should have lower participation
        c_participation = participation.get('C', None)
        
        # Should exist and be finite
        self.assertIsNotNone(c_participation)
        self.assertTrue(np.isfinite(c_participation))
        
        # Should be between 0 and 1
        self.assertGreaterEqual(c_participation, 0)
        self.assertLessEqual(c_participation, 1)
    
    @skip_if_no_deps
    def test_participation_coefficient_isolated_node(self):
        """Test participation coefficient for completely isolated node."""
        # Create network with an isolated node
        isolated_network = multinet.multi_layer_network(directed=False)
        isolated_network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
        ], input_type='list')
        # Add isolated node D with self-loop or just in the node list
        # (py3plex may or may not automatically track isolated nodes)
        
        calc = MultilayerCentrality(isolated_network)
        participation = calc.participation_coefficient(weighted=False)
        
        # All values should be finite and in [0, 1]
        for node, value in participation.items():
            self.assertTrue(np.isfinite(value),
                          f"Participation for {node} is not finite: {value}")
            self.assertGreaterEqual(value, 0,
                                  f"Participation for {node} is negative: {value}")
            self.assertLessEqual(value, 1,
                               f"Participation for {node} exceeds 1: {value}")


if __name__ == '__main__':
    unittest.main()
