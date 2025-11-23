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


class TestNewMultilayerMetrics(unittest.TestCase):
    """Test cases for newly added multilayer metrics (entropy, mutual information, etc.)."""
    
    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available for new metrics tests")
        
        # Create a 3-layer test network with varying structures
        self.test_network = multinet.multi_layer_network(directed=False)
        
        # Layer 1: Dense connectivity (complete triangle)
        self.test_network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['C', 'L1', 'A', 'L1', 1],
            ['A', 'L1', 'D', 'L1', 1],
        ], input_type='list')
        
        # Layer 2: Sparse connectivity (path)
        self.test_network.add_edges([
            ['A', 'L2', 'B', 'L2', 2],
            ['B', 'L2', 'C', 'L2', 2],
        ], input_type='list')
        
        # Layer 3: Mixed connectivity
        self.test_network.add_edges([
            ['A', 'L3', 'C', 'L3', 1],
            ['B', 'L3', 'D', 'L3', 1],
        ], input_type='list')
        
        # Add inter-layer edges
        self.test_network.add_edges([
            ['A', 'L1', 'A', 'L2', 1],
            ['A', 'L2', 'A', 'L3', 1],
            ['B', 'L1', 'B', 'L2', 1],
            ['C', 'L1', 'C', 'L2', 1],
            ['D', 'L1', 'D', 'L3', 1],
        ], input_type='list')
    
    @skip_if_no_deps
    def test_layer_connectivity_entropy(self):
        """Test layer connectivity entropy calculation."""
        # Test for each layer
        entropy_l1 = mls.layer_connectivity_entropy(self.test_network, 'L1')
        entropy_l2 = mls.layer_connectivity_entropy(self.test_network, 'L2')
        entropy_l3 = mls.layer_connectivity_entropy(self.test_network, 'L3')
        
        # All entropies should be non-negative
        self.assertTrue(entropy_l1 >= 0)
        self.assertTrue(entropy_l2 >= 0)
        self.assertTrue(entropy_l3 >= 0)
        
        # L1 has more varied degrees, should have higher entropy than L2
        self.assertGreater(entropy_l1, 0)
        
        # Test empty layer
        entropy_empty = mls.layer_connectivity_entropy(self.test_network, 'L_empty')
        self.assertEqual(entropy_empty, 0.0)
    
    @skip_if_no_deps
    def test_inter_layer_dependence_entropy(self):
        """Test inter-layer dependence entropy."""
        # Test various layer pairs
        entropy_l1_l2 = mls.inter_layer_dependence_entropy(
            self.test_network, 'L1', 'L2'
        )
        entropy_l2_l3 = mls.inter_layer_dependence_entropy(
            self.test_network, 'L2', 'L3'
        )
        
        # Should be non-negative
        self.assertTrue(entropy_l1_l2 >= 0)
        self.assertTrue(entropy_l2_l3 >= 0)
        
        # Test symmetric property
        entropy_l2_l1 = mls.inter_layer_dependence_entropy(
            self.test_network, 'L2', 'L1'
        )
        self.assertAlmostEqual(entropy_l1_l2, entropy_l2_l1, places=6)
        
        # Test with layers that have no inter-layer edges
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['C', 'L2', 'D', 'L2', 1]
        ], input_type='list')
        entropy_no_coupling = mls.inter_layer_dependence_entropy(network, 'L1', 'L2')
        self.assertEqual(entropy_no_coupling, 0.0)
    
    @skip_if_no_deps
    def test_cross_layer_redundancy_entropy(self):
        """Test cross-layer redundancy entropy."""
        entropy = mls.cross_layer_redundancy_entropy(self.test_network)
        
        # Should be non-negative
        self.assertTrue(entropy >= 0)
        
        # Test network with only one layer
        single_layer_network = multinet.multi_layer_network(directed=False)
        single_layer_network.add_edges([
            ['A', 'L1', 'B', 'L1', 1]
        ], input_type='list')
        entropy_single = mls.cross_layer_redundancy_entropy(single_layer_network)
        self.assertEqual(entropy_single, 0.0)
        
        # Test network with complete overlap
        overlap_network = multinet.multi_layer_network(directed=False)
        overlap_network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['A', 'L2', 'B', 'L2', 1],
        ], input_type='list')
        entropy_overlap = mls.cross_layer_redundancy_entropy(overlap_network)
        self.assertTrue(entropy_overlap >= 0)
    
    @skip_if_no_deps
    def test_cross_layer_mutual_information(self):
        """Test cross-layer mutual information."""
        # Test between different layer pairs
        mi_l1_l2 = mls.cross_layer_mutual_information(
            self.test_network, 'L1', 'L2', bins=5
        )
        mi_l1_l3 = mls.cross_layer_mutual_information(
            self.test_network, 'L1', 'L3', bins=5
        )
        
        # MI should be non-negative
        self.assertTrue(mi_l1_l2 >= 0)
        self.assertTrue(mi_l1_l3 >= 0)
        
        # Test symmetric property
        mi_l2_l1 = mls.cross_layer_mutual_information(
            self.test_network, 'L2', 'L1', bins=5
        )
        self.assertAlmostEqual(mi_l1_l2, mi_l2_l1, places=5)
        
        # Test with layers having few common nodes
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['C', 'L2', 'D', 'L2', 1]
        ], input_type='list')
        mi_no_common = mls.cross_layer_mutual_information(network, 'L1', 'L2')
        self.assertEqual(mi_no_common, 0.0)
        
        # Test with uniform degrees (no information)
        uniform_network = multinet.multi_layer_network(directed=False)
        uniform_network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['C', 'L1', 'D', 'L1', 1],
            ['A', 'L2', 'B', 'L2', 1],
            ['C', 'L2', 'D', 'L2', 1],
        ], input_type='list')
        mi_uniform = mls.cross_layer_mutual_information(uniform_network, 'L1', 'L2')
        self.assertEqual(mi_uniform, 0.0)
    
    @skip_if_no_deps
    def test_layer_influence_centrality_coupling(self):
        """Test layer influence centrality with coupling method."""
        # Test coupling-based influence for each layer
        influence_l1 = mls.layer_influence_centrality(
            self.test_network, 'L1', method='coupling'
        )
        influence_l2 = mls.layer_influence_centrality(
            self.test_network, 'L2', method='coupling'
        )
        influence_l3 = mls.layer_influence_centrality(
            self.test_network, 'L3', method='coupling'
        )
        
        # All influences should be non-negative
        self.assertTrue(influence_l1 >= 0)
        self.assertTrue(influence_l2 >= 0)
        self.assertTrue(influence_l3 >= 0)
        
        # L1 and L2 have more inter-layer connections
        self.assertGreater(influence_l1, 0)
        self.assertGreater(influence_l2, 0)
        
        # Test single layer network
        single_layer = multinet.multi_layer_network(directed=False)
        single_layer.add_edges([['A', 'L1', 'B', 'L1', 1]], input_type='list')
        influence_single = mls.layer_influence_centrality(
            single_layer, 'L1', method='coupling'
        )
        self.assertEqual(influence_single, 0.0)
    
    @skip_if_no_deps
    def test_layer_influence_centrality_flow(self):
        """Test layer influence centrality with flow method."""
        influence_flow = mls.layer_influence_centrality(
            self.test_network, 'L1', method='flow', sample_size=50
        )
        
        # Flow influence should be non-negative
        self.assertTrue(influence_flow >= 0)
        
        # Should be a probability (between 0 and 1)
        self.assertTrue(influence_flow <= 1.0)
    
    @skip_if_no_deps
    def test_layer_influence_centrality_invalid_method(self):
        """Test layer influence centrality with invalid method."""
        with self.assertRaises(ValueError):
            mls.layer_influence_centrality(
                self.test_network, 'L1', method='invalid_method'
            )
    
    @skip_if_no_deps
    def test_multilayer_betweenness_surface(self):
        """Test multilayer betweenness surface calculation."""
        surface, (nodes, layers) = mls.multilayer_betweenness_surface(
            self.test_network, normalized=True
        )
        
        # Should return a 2D array
        self.assertIsInstance(surface, np.ndarray)
        self.assertEqual(len(surface.shape), 2)
        
        # Dimensions should match nodes and layers
        self.assertEqual(surface.shape[0], len(nodes))
        self.assertEqual(surface.shape[1], len(layers))
        
        # All values should be non-negative
        self.assertTrue(np.all(surface >= 0))
        
        # Node and layer lists should not be empty
        self.assertGreater(len(nodes), 0)
        self.assertGreater(len(layers), 0)
        
        # Test with empty network
        empty_network = multinet.multi_layer_network(directed=False)
        surface_empty, (nodes_empty, layers_empty) = mls.multilayer_betweenness_surface(
            empty_network
        )
        self.assertEqual(len(nodes_empty), 0)
        self.assertEqual(len(layers_empty), 0)
    
    @skip_if_no_deps
    def test_interlayer_degree_correlation_matrix(self):
        """Test inter-layer degree correlation matrix."""
        corr_matrix, layers = mls.interlayer_degree_correlation_matrix(
            self.test_network
        )
        
        # Should return a square matrix
        self.assertIsInstance(corr_matrix, np.ndarray)
        self.assertEqual(len(corr_matrix.shape), 2)
        self.assertEqual(corr_matrix.shape[0], corr_matrix.shape[1])
        
        # Dimensions should match number of layers
        self.assertEqual(corr_matrix.shape[0], len(layers))
        self.assertEqual(len(layers), 3)
        
        # Diagonal should be all 1.0 (self-correlation)
        for i in range(len(layers)):
            self.assertAlmostEqual(corr_matrix[i, i], 1.0, places=6)
        
        # Matrix should be symmetric
        for i in range(len(layers)):
            for j in range(len(layers)):
                self.assertAlmostEqual(
                    corr_matrix[i, j], corr_matrix[j, i], places=6
                )
        
        # All correlations should be in [-1, 1]
        self.assertTrue(np.all(corr_matrix >= -1.0))
        self.assertTrue(np.all(corr_matrix <= 1.0))
        
        # Test with single layer
        single_layer = multinet.multi_layer_network(directed=False)
        single_layer.add_edges([['A', 'L1', 'B', 'L1', 1]], input_type='list')
        corr_single, layers_single = mls.interlayer_degree_correlation_matrix(
            single_layer
        )
        self.assertEqual(corr_single.shape, (1, 1))
        self.assertEqual(corr_single[0, 0], 1.0)


class TestNewMetricsPropertyBased(unittest.TestCase):
    """Property-based tests for new metrics."""
    
    def setUp(self):
        """Set up for property tests."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
    
    @skip_if_no_deps
    def test_entropy_properties(self):
        """Test mathematical properties of entropy measures."""
        # Create a network with uniform edge distribution
        uniform_network = multinet.multi_layer_network(directed=False)
        for layer in ['L1', 'L2', 'L3']:
            uniform_network.add_edges([
                ['A', layer, 'B', layer, 1],
                ['B', layer, 'C', layer, 1],
            ], input_type='list')
        
        # Entropy of multiplexity should be close to log2(3)
        entropy = mls.entropy_of_multiplexity(uniform_network)
        expected_max = np.log2(3)
        self.assertAlmostEqual(entropy, expected_max, places=1)
    
    @skip_if_no_deps
    def test_mutual_information_symmetry(self):
        """Test that mutual information is symmetric."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['A', 'L2', 'B', 'L2', 1],
            ['B', 'L2', 'C', 'L2', 1],
        ], input_type='list')
        
        mi_12 = mls.cross_layer_mutual_information(network, 'L1', 'L2')
        mi_21 = mls.cross_layer_mutual_information(network, 'L2', 'L1')
        
        self.assertAlmostEqual(mi_12, mi_21, places=6)
    
    @skip_if_no_deps
    def test_correlation_matrix_symmetry(self):
        """Test that correlation matrix is symmetric."""
        network = multinet.multi_layer_network(directed=False)
        for layer in ['L1', 'L2', 'L3']:
            network.add_edges([
                ['A', layer, 'B', layer, 1],
                ['B', layer, 'C', layer, 1],
            ], input_type='list')
        
        corr_matrix, _ = mls.interlayer_degree_correlation_matrix(network)
        
        # Check symmetry
        self.assertTrue(np.allclose(corr_matrix, corr_matrix.T))
    
    @skip_if_no_deps
    def test_betweenness_surface_normalization(self):
        """Test that normalized betweenness surface has values in [0, 1]."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['A', 'L2', 'C', 'L2', 1],
        ], input_type='list')
        
        surface, _ = mls.multilayer_betweenness_surface(network, normalized=True)
        
        # All values should be in [0, 1] for normalized betweenness
        self.assertTrue(np.all(surface >= 0))
        self.assertTrue(np.all(surface <= 1))


if __name__ == '__main__':
    unittest.main()
