#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for multilayer network statistics.

This module contains comprehensive tests for all statistics implemented
in py3plex.algorithms.statistics.multilayer_statistics.
"""

import unittest

# Handle missing dependencies gracefully
try:
    import numpy as np
    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    np = None
    multinet = None
    mls = None
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: {e}")


def skip_if_no_deps(test_func):
    """Decorator to skip tests when dependencies are missing."""
    if not DEPENDENCIES_AVAILABLE:
        return unittest.skip("Dependencies not available")(test_func)
    return test_func


class TestMultilayerStatistics(unittest.TestCase):
    """Test cases for multilayer network statistics."""
    
    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available for multilayer statistics tests")
        
        # Create a simple 2-layer, 3-node test network
        self.simple_network = multinet.multi_layer_network(directed=False)
        
        # Layer 1: Triangle (A-B-C-A)
        self.simple_network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['C', 'L1', 'A', 'L1', 1]
        ], input_type='list')
        
        # Layer 2: Line (A-B-C)
        self.simple_network.add_edges([
            ['A', 'L2', 'B', 'L2', 2],
            ['B', 'L2', 'C', 'L2', 2]
        ], input_type='list')
        
        # Add inter-layer edges
        self.simple_network.add_edges([
            ['A', 'L1', 'A', 'L2', 1],
            ['B', 'L1', 'B', 'L2', 1],
            ['C', 'L1', 'C', 'L2', 1]
        ], input_type='list')
        
        # Create a directed test network
        self.directed_network = multinet.multi_layer_network(directed=True)
        self.directed_network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['C', 'L1', 'A', 'L1', 1]
        ], input_type='list')
    
    @skip_if_no_deps
    def test_layer_density(self):
        """Test layer density calculation."""
        # Layer 1 is a triangle (3 nodes, 3 edges)
        # Density = 3 / (3*2/2) = 3/3 = 1.0
        density_l1 = mls.layer_density(self.simple_network, 'L1')
        self.assertAlmostEqual(density_l1, 1.0, places=2)
        
        # Layer 2 is a line (3 nodes, 2 edges)
        # Density = 2 / (3*2/2) = 2/3 ≈ 0.67
        density_l2 = mls.layer_density(self.simple_network, 'L2')
        self.assertAlmostEqual(density_l2, 2/3, places=2)
    
    @skip_if_no_deps
    def test_inter_layer_coupling_strength(self):
        """Test inter-layer coupling strength."""
        # We have 3 inter-layer edges with weight 1.0 each
        coupling = mls.inter_layer_coupling_strength(self.simple_network, 'L1', 'L2')
        self.assertAlmostEqual(coupling, 1.0, places=2)
    
    @skip_if_no_deps
    def test_node_activity(self):
        """Test node activity calculation."""
        # All nodes are active in both layers (2/2 = 1.0)
        activity_a = mls.node_activity(self.simple_network, 'A')
        self.assertAlmostEqual(activity_a, 1.0, places=2)
        
        activity_b = mls.node_activity(self.simple_network, 'B')
        self.assertAlmostEqual(activity_b, 1.0, places=2)
    
    @skip_if_no_deps
    def test_degree_vector(self):
        """Test degree vector calculation."""
        # Node A in L1: connects to B and C = degree 2
        # Node A in L2: connects to B = degree 1
        degrees_a = mls.degree_vector(self.simple_network, 'A')
        self.assertEqual(degrees_a['L1'], 2)
        self.assertEqual(degrees_a['L2'], 1)
        
        # Node B has higher degree
        degrees_b = mls.degree_vector(self.simple_network, 'B')
        self.assertEqual(degrees_b['L1'], 2)
        self.assertEqual(degrees_b['L2'], 2)
    
    @skip_if_no_deps
    def test_inter_layer_degree_correlation(self):
        """Test inter-layer degree correlation."""
        # Degrees in L1: A=2, B=2, C=2
        # Degrees in L2: A=1, B=2, C=1
        # Should have some correlation
        corr = mls.inter_layer_degree_correlation(self.simple_network, 'L1', 'L2')
        # Exact value depends on the calculation, but should be between -1 and 1
        self.assertTrue(-1.0 <= corr <= 1.0)
    
    @skip_if_no_deps
    def test_edge_overlap(self):
        """Test edge overlap calculation."""
        # L1 has edges: A-B, B-C, C-A
        # L2 has edges: A-B, B-C
        # Intersection: {A-B, B-C}
        # Union: {A-B, B-C, C-A}
        # Overlap = 2/3
        overlap = mls.edge_overlap(self.simple_network, 'L1', 'L2')
        self.assertAlmostEqual(overlap, 2/3, places=2)
    
    @skip_if_no_deps
    def test_layer_similarity_cosine(self):
        """Test layer similarity with cosine method."""
        similarity = mls.layer_similarity(self.simple_network, 'L1', 'L2', method='cosine')
        # Should be positive since layers share some structure
        self.assertTrue(0 <= similarity <= 1)
    
    @skip_if_no_deps
    def test_layer_similarity_jaccard(self):
        """Test layer similarity with Jaccard method."""
        similarity = mls.layer_similarity(self.simple_network, 'L1', 'L2', method='jaccard')
        # Should match edge overlap
        overlap = mls.edge_overlap(self.simple_network, 'L1', 'L2')
        self.assertAlmostEqual(similarity, overlap, places=2)
    
    @skip_if_no_deps
    def test_multilayer_clustering_coefficient_node(self):
        """Test multilayer clustering coefficient for a single node."""
        # Node A is in triangles in L1
        clustering_a = mls.multilayer_clustering_coefficient(self.simple_network, node='A')
        # Should be high since A is in a triangle in L1
        self.assertTrue(0 <= clustering_a <= 1)
    
    @skip_if_no_deps
    def test_multilayer_clustering_coefficient_all(self):
        """Test multilayer clustering coefficient for all nodes."""
        clustering = mls.multilayer_clustering_coefficient(self.simple_network)
        self.assertIsInstance(clustering, dict)
        # Should have all three nodes
        self.assertEqual(len(clustering), 3)
        # All values should be between 0 and 1
        for node, coeff in clustering.items():
            self.assertTrue(0 <= coeff <= 1)
    
    @skip_if_no_deps
    def test_versatility_centrality_degree(self):
        """Test versatility centrality with degree."""
        versatility = mls.versatility_centrality(self.simple_network, centrality_type='degree')
        self.assertIsInstance(versatility, dict)
        # Should have all three nodes
        self.assertEqual(len(versatility), 3)
        # Node B has highest total degree, should have highest versatility
        self.assertTrue(versatility['B'] >= versatility['A'])
        self.assertTrue(versatility['B'] >= versatility['C'])
    
    @skip_if_no_deps
    def test_versatility_centrality_weighted(self):
        """Test versatility centrality with custom layer weights."""
        alpha = {'L1': 0.7, 'L2': 0.3}
        versatility = mls.versatility_centrality(
            self.simple_network, 
            centrality_type='degree',
            alpha=alpha
        )
        self.assertIsInstance(versatility, dict)
        self.assertEqual(len(versatility), 3)
    
    @skip_if_no_deps
    def test_interdependence(self):
        """Test interdependence calculation."""
        # Use small sample size for speed
        interdep = mls.interdependence(self.simple_network, sample_size=10)
        # Should be a positive number
        self.assertTrue(interdep > 0)
    
    @skip_if_no_deps
    def test_supra_laplacian_spectrum(self):
        """Test supra-Laplacian spectrum calculation."""
        spectrum = mls.supra_laplacian_spectrum(self.simple_network, k=3)
        # Should return array of eigenvalues
        self.assertIsInstance(spectrum, np.ndarray)
        # First eigenvalue should be close to 0 (connected graph)
        if len(spectrum) > 0:
            self.assertAlmostEqual(spectrum[0], 0, places=1)
    
    @skip_if_no_deps
    def test_algebraic_connectivity(self):
        """Test algebraic connectivity (Fiedler value)."""
        alg_conn = mls.algebraic_connectivity(self.simple_network)
        # Should be non-negative for connected graphs
        self.assertTrue(alg_conn >= 0)
    
    @skip_if_no_deps
    def test_inter_layer_assortativity(self):
        """Test inter-layer assortativity."""
        assort = mls.inter_layer_assortativity(self.simple_network, 'L1', 'L2')
        # Should be between -1 and 1
        self.assertTrue(-1.0 <= assort <= 1.0)
    
    @skip_if_no_deps
    def test_entropy_of_multiplexity(self):
        """Test entropy of multiplexity."""
        entropy = mls.entropy_of_multiplexity(self.simple_network)
        # Should be non-negative
        self.assertTrue(entropy >= 0)
        # For 2 layers, max entropy is log2(2) = 1
        self.assertTrue(entropy <= 1.0)
    
    @skip_if_no_deps
    def test_multilayer_motif_frequency(self):
        """Test multilayer motif frequency."""
        motifs = mls.multilayer_motif_frequency(self.simple_network, motif_size=3)
        self.assertIsInstance(motifs, dict)
        # Should have intra-layer and inter-layer triangles
        self.assertIn('intra_layer_triangles', motifs)
    
    @skip_if_no_deps
    def test_resilience_layer_removal(self):
        """Test resilience with layer removal."""
        # Remove layer L2
        r = mls.resilience(self.simple_network, 'layer_removal', perturbation_param='L2')
        # Should be between 0 and 1
        self.assertTrue(0 <= r <= 1)
        # Removing one layer should reduce the size
        self.assertTrue(r < 1.0)
    
    @skip_if_no_deps
    def test_resilience_coupling_removal(self):
        """Test resilience with coupling removal."""
        # Remove 50% of inter-layer edges
        r = mls.resilience(self.simple_network, 'coupling_removal', perturbation_param=0.5)
        # Should be between 0 and 1
        self.assertTrue(0 <= r <= 1)
    
    @skip_if_no_deps
    def test_multilayer_modularity_wrapper(self):
        """Test multilayer modularity wrapper."""
        # Create simple community structure
        communities = {
            ('A', 'L1'): 0,
            ('B', 'L1'): 0,
            ('C', 'L1'): 1,
            ('A', 'L2'): 0,
            ('B', 'L2'): 0,
            ('C', 'L2'): 1
        }
        
        Q = mls.multilayer_modularity(self.simple_network, communities)
        # Modularity should be between -1 and 1
        self.assertTrue(-1.0 <= Q <= 1.0)
    
    @skip_if_no_deps
    def test_directed_network(self):
        """Test statistics on directed networks."""
        # Test a few functions on directed network
        density = mls.layer_density(self.directed_network, 'L1')
        self.assertTrue(0 <= density <= 1)
        
        degrees = mls.degree_vector(self.directed_network, 'A')
        self.assertIsInstance(degrees, dict)
    
    @skip_if_no_deps
    def test_empty_layer(self):
        """Test handling of empty layers."""
        # Create network with an empty layer reference
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1]
        ], input_type='list')
        
        # Test density on non-existent layer
        density = mls.layer_density(network, 'L_empty')
        self.assertEqual(density, 0.0)
    
    @skip_if_no_deps
    def test_single_node_network(self):
        """Test handling of single-node networks."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'A', 'L1', 1]
        ], input_type='list')
        
        # Test various statistics
        density = mls.layer_density(network, 'L1')
        self.assertEqual(density, 0.0)  # No edges between distinct nodes
        
        activity = mls.node_activity(network, 'A')
        self.assertEqual(activity, 1.0)  # Active in 1/1 layers


class TestMultilayerStatisticsEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up minimal test cases."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        
        # Create minimal network
        self.minimal_network = multinet.multi_layer_network(directed=False)
        self.minimal_network.add_edges([
            ['A', 'L1', 'B', 'L1', 1]
        ], input_type='list')
    
    @skip_if_no_deps
    def test_weighted_degree_vector(self):
        """Test weighted degree vector."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 5],
            ['A', 'L1', 'C', 'L1', 3]
        ], input_type='list')
        
        degrees_weighted = mls.degree_vector(network, 'A', weighted=True)
        degrees_unweighted = mls.degree_vector(network, 'A', weighted=False)
        
        # Weighted should sum weights
        self.assertEqual(degrees_weighted['L1'], 8)
        # Unweighted should count edges
        self.assertEqual(degrees_unweighted['L1'], 2)
    
    @skip_if_no_deps
    def test_correlation_with_constant_degrees(self):
        """Test correlation when all degrees are the same."""
        network = multinet.multi_layer_network(directed=False)
        # All nodes have degree 1 in both layers
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['A', 'L2', 'B', 'L2', 1]
        ], input_type='list')
        
        corr = mls.inter_layer_degree_correlation(network, 'L1', 'L2')
        # Should be 0 when there's no variance
        self.assertEqual(corr, 0.0)
    
    @skip_if_no_deps
    def test_entropy_single_layer(self):
        """Test entropy with only one layer."""
        # Single layer means no diversity, entropy should be 0
        entropy = mls.entropy_of_multiplexity(self.minimal_network)
        self.assertAlmostEqual(entropy, 0.0, places=5)
    
    @skip_if_no_deps
    def test_versatility_betweenness(self):
        """Test versatility with betweenness centrality."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['C', 'L1', 'D', 'L1', 1]
        ], input_type='list')
        
        versatility = mls.versatility_centrality(network, centrality_type='betweenness')
        self.assertIsInstance(versatility, dict)
        # B and C should have higher betweenness
        self.assertTrue(versatility['B'] > versatility['A'])


class TestStatisticsIntegration(unittest.TestCase):
    """Integration tests with realistic networks."""
    
    def setUp(self):
        """Set up a more realistic test network."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        
        # Create a 3-layer social network
        self.social_network = multinet.multi_layer_network(directed=False)
        
        # Facebook layer (dense)
        facebook_edges = [
            ['Alice', 'facebook', 'Bob', 'facebook', 1],
            ['Alice', 'facebook', 'Carol', 'facebook', 1],
            ['Bob', 'facebook', 'Carol', 'facebook', 1],
            ['Bob', 'facebook', 'David', 'facebook', 1]
        ]
        
        # Twitter layer (sparse)
        twitter_edges = [
            ['Alice', 'twitter', 'Carol', 'twitter', 1],
            ['Bob', 'twitter', 'David', 'twitter', 1]
        ]
        
        # LinkedIn layer (moderate)
        linkedin_edges = [
            ['Alice', 'linkedin', 'Bob', 'linkedin', 1],
            ['Carol', 'linkedin', 'David', 'linkedin', 1]
        ]
        
        # Add all edges
        self.social_network.add_edges(
            facebook_edges + twitter_edges + linkedin_edges,
            input_type='list'
        )
        
        # Add inter-layer connections
        inter_edges = [
            ['Alice', 'facebook', 'Alice', 'twitter', 1],
            ['Alice', 'twitter', 'Alice', 'linkedin', 1],
            ['Bob', 'facebook', 'Bob', 'twitter', 1],
            ['Bob', 'twitter', 'Bob', 'linkedin', 1]
        ]
        self.social_network.add_edges(inter_edges, input_type='list')
    
    @skip_if_no_deps
    def test_comprehensive_analysis(self):
        """Test multiple statistics on realistic network."""
        # Layer densities
        fb_density = mls.layer_density(self.social_network, 'facebook')
        tw_density = mls.layer_density(self.social_network, 'twitter')
        
        # Facebook should be denser
        self.assertTrue(fb_density > tw_density)
        
        # Node activity (Alice is in all layers)
        alice_activity = mls.node_activity(self.social_network, 'Alice')
        self.assertAlmostEqual(alice_activity, 1.0, places=1)
        
        # Versatility
        versatility = mls.versatility_centrality(self.social_network)
        # Alice and Bob should have high versatility (active in multiple layers)
        self.assertTrue(versatility['Alice'] > 0)
        self.assertTrue(versatility['Bob'] > 0)
        
        # Entropy should indicate diversity
        entropy = mls.entropy_of_multiplexity(self.social_network)
        self.assertTrue(entropy > 0)
    
    @skip_if_no_deps
    def test_layer_comparisons(self):
        """Test layer comparison statistics."""
        # Edge overlap between layers
        overlap_fb_tw = mls.edge_overlap(self.social_network, 'facebook', 'twitter')
        overlap_fb_li = mls.edge_overlap(self.social_network, 'facebook', 'linkedin')
        
        # All should be valid overlaps
        self.assertTrue(0 <= overlap_fb_tw <= 1)
        self.assertTrue(0 <= overlap_fb_li <= 1)
        
        # Degree correlation
        corr = mls.inter_layer_degree_correlation(
            self.social_network, 'facebook', 'linkedin'
        )
        self.assertTrue(-1 <= corr <= 1)


if __name__ == '__main__':
    unittest.main()
