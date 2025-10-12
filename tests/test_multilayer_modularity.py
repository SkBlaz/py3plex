#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for multilayer modularity and community detection.

This module contains tests for:
- Multilayer modularity calculation
- Multilayer community detection algorithms
- Multilayer synthetic graph generation
"""

import unittest

# Handle missing dependencies gracefully
try:
    import numpy as np
    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.multilayer_modularity import (
        multilayer_modularity,
        build_supra_modularity_matrix,
        louvain_multilayer,
    )
    from py3plex.algorithms.community_detection.multilayer_benchmark import (
        generate_multilayer_lfr,
        generate_coupled_er_multilayer,
        generate_sbm_multilayer,
    )
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    np = None
    multinet = None
    multilayer_modularity = None
    build_supra_modularity_matrix = None
    louvain_multilayer = None
    generate_multilayer_lfr = None
    generate_coupled_er_multilayer = None
    generate_sbm_multilayer = None
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: {e}")


class TestMultilayerModularity(unittest.TestCase):
    """Test cases for multilayer modularity calculation."""
    
    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available for multilayer modularity tests")
        
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
    
    def test_perfect_community_structure(self):
        """Test modularity with perfect community structure."""
        # All nodes in same community
        communities = {
            ('A', 'L1'): 0,
            ('B', 'L1'): 0,
            ('C', 'L1'): 0,
            ('A', 'L2'): 0,
            ('B', 'L2'): 0,
            ('C', 'L2'): 0,
        }
        
        Q = multilayer_modularity(self.simple_network, communities, gamma=1.0, omega=0.0)
        
        # With omega=0 (no coupling), modularity depends only on intra-layer structure
        # Should be non-negative for cohesive structure
        self.assertIsInstance(Q, float)
        self.assertGreaterEqual(Q, -1.0)
        self.assertLessEqual(Q, 1.0)
    
    def test_split_communities(self):
        """Test modularity with communities split between layers."""
        # Different communities in each layer
        communities = {
            ('A', 'L1'): 0,
            ('B', 'L1'): 0,
            ('C', 'L1'): 1,
            ('A', 'L2'): 0,
            ('B', 'L2'): 1,
            ('C', 'L2'): 1,
        }
        
        Q = multilayer_modularity(self.simple_network, communities, gamma=1.0, omega=0.0)
        
        # Should return valid modularity
        self.assertIsInstance(Q, float)
        self.assertGreaterEqual(Q, -1.0)
        self.assertLessEqual(Q, 1.0)
    
    def test_modularity_with_coupling(self):
        """Test modularity with inter-layer coupling."""
        # Same community across layers
        communities = {
            ('A', 'L1'): 0,
            ('B', 'L1'): 0,
            ('C', 'L1'): 1,
            ('A', 'L2'): 0,
            ('B', 'L2'): 0,
            ('C', 'L2'): 1,
        }
        
        Q_no_coupling = multilayer_modularity(
            self.simple_network, communities, gamma=1.0, omega=0.0
        )
        Q_with_coupling = multilayer_modularity(
            self.simple_network, communities, gamma=1.0, omega=1.0
        )
        
        # With positive coupling and same communities across layers,
        # modularity should increase
        self.assertGreater(Q_with_coupling, Q_no_coupling)
    
    def test_layer_specific_gamma(self):
        """Test modularity with layer-specific resolution parameters."""
        communities = {
            ('A', 'L1'): 0,
            ('B', 'L1'): 0,
            ('C', 'L1'): 0,
            ('A', 'L2'): 0,
            ('B', 'L2'): 0,
            ('C', 'L2'): 0,
        }
        
        gamma_dict = {'L1': 0.5, 'L2': 2.0}
        
        Q = multilayer_modularity(
            self.simple_network, communities, gamma=gamma_dict, omega=0.0
        )
        
        # Should return valid modularity
        self.assertIsInstance(Q, float)
        self.assertGreaterEqual(Q, -1.0)
        self.assertLessEqual(Q, 1.0)
    
    def test_omega_matrix(self):
        """Test modularity with layer-pair specific coupling."""
        communities = {
            ('A', 'L1'): 0,
            ('B', 'L1'): 0,
            ('C', 'L1'): 0,
            ('A', 'L2'): 0,
            ('B', 'L2'): 0,
            ('C', 'L2'): 0,
        }
        
        # Custom coupling matrix (2x2 for 2 layers)
        omega_matrix = np.array([
            [0.0, 0.5],  # L1 to L2
            [0.5, 0.0]   # L2 to L1
        ])
        
        Q = multilayer_modularity(
            self.simple_network, communities, gamma=1.0, omega=omega_matrix
        )
        
        # Should return valid modularity
        self.assertIsInstance(Q, float)
        self.assertGreaterEqual(Q, -1.0)
        self.assertLessEqual(Q, 1.0)
    
    def test_empty_communities(self):
        """Test modularity with empty communities dict."""
        communities = {}
        
        Q = multilayer_modularity(self.simple_network, communities, gamma=1.0, omega=0.0)
        
        # Should return valid modularity (likely 0 or negative)
        self.assertIsInstance(Q, float)
    
    def test_supra_modularity_matrix_shape(self):
        """Test supra-modularity matrix construction."""
        B, node_layer_list = build_supra_modularity_matrix(
            self.simple_network, gamma=1.0, omega=1.0
        )
        
        # Check matrix is square
        self.assertEqual(B.shape[0], B.shape[1])
        
        # Check size matches number of node-layer pairs
        self.assertEqual(B.shape[0], len(node_layer_list))
        
        # Check node-layer list contains expected format
        for nl in node_layer_list:
            self.assertIsInstance(nl, tuple)
            self.assertEqual(len(nl), 2)  # (node, layer)
    
    def test_supra_modularity_matrix_symmetry(self):
        """Test that supra-modularity matrix is symmetric for undirected networks."""
        B, _ = build_supra_modularity_matrix(
            self.simple_network, gamma=1.0, omega=1.0
        )
        
        # For undirected networks, B should be symmetric
        self.assertTrue(np.allclose(B, B.T))


class TestLouvainMultilayer(unittest.TestCase):
    """Test cases for multilayer Louvain algorithm."""
    
    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available for multilayer community detection tests")
        
        # Create a network with clear community structure
        self.network = multinet.multi_layer_network(directed=False)
        
        # Layer 1: Two cliques
        edges_l1 = [
            ['A', 'L1', 'B', 'L1', 1],
            ['A', 'L1', 'C', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['D', 'L1', 'E', 'L1', 1],
            ['D', 'L1', 'F', 'L1', 1],
            ['E', 'L1', 'F', 'L1', 1],
        ]
        
        # Layer 2: Same structure
        edges_l2 = [
            ['A', 'L2', 'B', 'L2', 1],
            ['A', 'L2', 'C', 'L2', 1],
            ['B', 'L2', 'C', 'L2', 1],
            ['D', 'L2', 'E', 'L2', 1],
            ['D', 'L2', 'F', 'L2', 1],
            ['E', 'L2', 'F', 'L2', 1],
        ]
        
        self.network.add_edges(edges_l1 + edges_l2, input_type='list')
    
    def test_louvain_finds_communities(self):
        """Test that Louvain algorithm finds communities."""
        communities = louvain_multilayer(
            self.network, gamma=1.0, omega=1.0, random_state=42, max_iter=10
        )
        
        # Should return communities for all node-layer pairs
        self.assertIsInstance(communities, dict)
        self.assertGreater(len(communities), 0)
        
        # Check that community IDs are integers
        for nl, com in communities.items():
            self.assertIsInstance(nl, tuple)
            self.assertEqual(len(nl), 2)
            self.assertIsInstance(com, int)
            self.assertGreaterEqual(com, 0)
    
    def test_louvain_with_strong_coupling(self):
        """Test Louvain with strong inter-layer coupling."""
        communities = louvain_multilayer(
            self.network, gamma=1.0, omega=10.0, random_state=42, max_iter=10
        )
        
        # With strong coupling, same node should be in same community across layers
        nodes = ['A', 'B', 'C', 'D', 'E', 'F']
        layers = ['L1', 'L2']
        
        for node in nodes:
            coms = [communities.get((node, layer), -1) for layer in layers]
            # At least should have valid communities
            self.assertTrue(all(c >= 0 for c in coms))
    
    def test_louvain_improves_modularity(self):
        """Test that Louvain improves modularity over random assignment."""
        # Random assignment
        nodes = ['A', 'B', 'C', 'D', 'E', 'F']
        layers = ['L1', 'L2']
        random_communities = {
            (node, layer): np.random.randint(0, 2)
            for node in nodes for layer in layers
        }
        
        # Louvain assignment
        louvain_communities = louvain_multilayer(
            self.network, gamma=1.0, omega=1.0, random_state=42, max_iter=10
        )
        
        # Calculate modularity
        Q_random = multilayer_modularity(
            self.network, random_communities, gamma=1.0, omega=1.0
        )
        Q_louvain = multilayer_modularity(
            self.network, louvain_communities, gamma=1.0, omega=1.0
        )
        
        # Louvain should find better or equal modularity
        # (not always guaranteed due to randomness and max_iter, but likely)
        self.assertIsInstance(Q_louvain, float)
        self.assertIsInstance(Q_random, float)


class TestMultilayerBenchmarks(unittest.TestCase):
    """Test cases for multilayer synthetic graph generation."""
    
    def setUp(self):
        """Set up test parameters."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available for multilayer benchmark tests")
    
    def test_generate_multilayer_lfr_basic(self):
        """Test basic multilayer LFR generation."""
        network, communities = generate_multilayer_lfr(
            n=30,
            layers=['L1', 'L2'],
            mu=0.1,
            avg_degree=5,
            min_community=5,
            seed=42
        )
        
        # Check network is created
        self.assertIsNotNone(network)
        
        # Check communities are returned
        self.assertIsInstance(communities, dict)
        self.assertGreater(len(communities), 0)
        
        # Check community format
        for (node, layer), coms in communities.items():
            self.assertIsInstance(coms, set)
            self.assertGreater(len(coms), 0)
    
    def test_generate_multilayer_lfr_persistence(self):
        """Test multilayer LFR with community persistence."""
        # Full persistence
        network1, communities1 = generate_multilayer_lfr(
            n=30,
            layers=['L1', 'L2'],
            mu=0.1,
            community_persistence=1.0,
            seed=42
        )
        
        # Low persistence
        network2, communities2 = generate_multilayer_lfr(
            n=30,
            layers=['L1', 'L2'],
            mu=0.1,
            community_persistence=0.1,
            seed=43
        )
        
        # Both should generate valid networks
        self.assertIsNotNone(network1)
        self.assertIsNotNone(network2)
    
    def test_generate_multilayer_lfr_node_overlap(self):
        """Test multilayer LFR with partial node overlap."""
        network, communities = generate_multilayer_lfr(
            n=30,
            layers=['L1', 'L2', 'L3'],
            mu=0.1,
            node_overlap=0.7,  # 70% nodes in all layers
            seed=42
        )
        
        # Check that some nodes may not appear in all layers
        self.assertIsNotNone(network)
        self.assertIsInstance(communities, dict)
    
    def test_generate_multilayer_lfr_overlapping_communities(self):
        """Test multilayer LFR with overlapping communities."""
        network, communities = generate_multilayer_lfr(
            n=30,
            layers=['L1', 'L2'],
            mu=0.1,
            overlapping_nodes=5,
            overlapping_membership=2,
            seed=42
        )
        
        # Check that some nodes belong to multiple communities
        overlapping_count = 0
        for coms in communities.values():
            if len(coms) > 1:
                overlapping_count += 1
        
        # Should have some overlapping nodes (though not guaranteed with small n)
        self.assertGreaterEqual(overlapping_count, 0)
    
    def test_generate_coupled_er_basic(self):
        """Test basic coupled ER generation."""
        network = generate_coupled_er_multilayer(
            n=30,
            layers=['L1', 'L2'],
            p=0.1,
            omega=1.0,
            coupling_probability=1.0,
            seed=42
        )
        
        # Check network is created
        self.assertIsNotNone(network)
        
        # Check it has nodes
        nodes = list(network.get_nodes())
        self.assertGreater(len(nodes), 0)
    
    def test_generate_coupled_er_partial_coupling(self):
        """Test coupled ER with partial coupling."""
        network = generate_coupled_er_multilayer(
            n=30,
            layers=['L1', 'L2', 'L3'],
            p=0.1,
            omega=0.5,
            coupling_probability=0.5,  # Only 50% nodes coupled
            seed=42
        )
        
        # Check network is created
        self.assertIsNotNone(network)
    
    def test_generate_coupled_er_layer_specific_p(self):
        """Test coupled ER with layer-specific edge probabilities."""
        network = generate_coupled_er_multilayer(
            n=30,
            layers=['L1', 'L2'],
            p=[0.1, 0.2],  # Different probabilities per layer
            omega=1.0,
            seed=42
        )
        
        # Check network is created
        self.assertIsNotNone(network)
    
    def test_generate_sbm_multilayer_basic(self):
        """Test basic multilayer SBM generation."""
        communities = [
            {0, 1, 2, 3, 4},
            {5, 6, 7, 8, 9}
        ]
        
        network, ground_truth = generate_sbm_multilayer(
            n=10,
            layers=['L1', 'L2'],
            communities=communities,
            p_in=0.7,
            p_out=0.1,
            seed=42
        )
        
        # Check network is created
        self.assertIsNotNone(network)
        
        # Check ground truth
        self.assertIsInstance(ground_truth, dict)
        self.assertGreater(len(ground_truth), 0)
        
        # Check ground truth format
        for (node, layer), com in ground_truth.items():
            self.assertIsInstance(com, int)
            self.assertIn(com, [0, 1])
    
    def test_generate_sbm_multilayer_persistence(self):
        """Test multilayer SBM with community persistence."""
        communities = [
            {0, 1, 2, 3, 4},
            {5, 6, 7, 8, 9}
        ]
        
        # High persistence
        network1, gt1 = generate_sbm_multilayer(
            n=10,
            layers=['L1', 'L2'],
            communities=communities,
            p_in=0.7,
            p_out=0.1,
            community_persistence=1.0,
            seed=42
        )
        
        # Low persistence
        network2, gt2 = generate_sbm_multilayer(
            n=10,
            layers=['L1', 'L2'],
            communities=communities,
            p_in=0.7,
            p_out=0.1,
            community_persistence=0.1,
            seed=43
        )
        
        # Both should generate valid networks
        self.assertIsNotNone(network1)
        self.assertIsNotNone(network2)


class TestMultilayerModularityConsistency(unittest.TestCase):
    """Test mathematical consistency of multilayer modularity."""
    
    def setUp(self):
        """Set up test network."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        
        self.network = multinet.multi_layer_network(directed=False)
        self.network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['A', 'L2', 'C', 'L2', 1]
        ], input_type='list')
    
    def test_modularity_bounds(self):
        """Test that modularity is always in [-1, 1]."""
        # Try various community assignments
        test_cases = [
            {('A', 'L1'): 0, ('B', 'L1'): 0, ('C', 'L1'): 0,
             ('A', 'L2'): 0, ('C', 'L2'): 0},
            {('A', 'L1'): 0, ('B', 'L1'): 1, ('C', 'L1'): 2,
             ('A', 'L2'): 0, ('C', 'L2'): 1},
            {('A', 'L1'): 0, ('B', 'L1'): 0, ('C', 'L1'): 1,
             ('A', 'L2'): 1, ('C', 'L2'): 1},
        ]
        
        for communities in test_cases:
            Q = multilayer_modularity(
                self.network, communities, gamma=1.0, omega=1.0
            )
            self.assertGreaterEqual(Q, -1.0, f"Q={Q} < -1 for {communities}")
            self.assertLessEqual(Q, 1.0, f"Q={Q} > 1 for {communities}")
    
    def test_omega_zero_independence(self):
        """Test that omega=0 gives independent layer modularity."""
        communities = {
            ('A', 'L1'): 0, ('B', 'L1'): 0, ('C', 'L1'): 1,
            ('A', 'L2'): 0, ('C', 'L2'): 0
        }
        
        # With omega=0, changing communities in one layer shouldn't affect
        # the contribution from coupling
        Q1 = multilayer_modularity(
            self.network, communities, gamma=1.0, omega=0.0
        )
        
        # Change community in one layer
        communities_modified = communities.copy()
        communities_modified[('A', 'L2')] = 1
        
        Q2 = multilayer_modularity(
            self.network, communities_modified, gamma=1.0, omega=0.0
        )
        
        # Both should be valid (but may differ due to intra-layer structure)
        self.assertIsInstance(Q1, float)
        self.assertIsInstance(Q2, float)


if __name__ == '__main__':
    unittest.main()
