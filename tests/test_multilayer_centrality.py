#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for multilayer centrality measures.

This module contains comprehensive tests for all centrality measures
implemented in py3plex.algorithms.multilayer_algorithms.centrality.
"""

import unittest

# Handle missing dependencies gracefully
try:
    import numpy as np
    from py3plex.core import multinet
    from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality, compute_all_centralities
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    # Mock the missing dependencies
    np = None
    multinet = None
    MultilayerCentrality = None
    compute_all_centralities = None
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: {e}")

# Decorator to skip tests when dependencies are missing
def skip_if_no_deps(test_func):
    if not DEPENDENCIES_AVAILABLE:
        return unittest.skip("Dependencies not available")(test_func)
    return test_func


class TestMultilayerCentrality(unittest.TestCase):
    """Test cases for multilayer centrality measures."""
    
    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available for multilayer centrality tests")
            
        # Create a simple 2-layer, 3-node test network
        self.simple_network = multinet.multi_layer_network(directed=False)
        
        # Layer 1: A triangle
        self.simple_network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1], 
            ['C', 'L1', 'A', 'L1', 1]
        ], input_type='list')
        
        # Layer 2: A line
        self.simple_network.add_edges([
            ['A', 'L2', 'B', 'L2', 2],
            ['B', 'L2', 'C', 'L2', 2]
        ], input_type='list')
        
        # Create a directed test network
        self.directed_network = multinet.multi_layer_network(directed=True)
        self.directed_network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1]
        ], input_type='list')
        
        # Single node network for edge cases
        self.single_node_network = multinet.multi_layer_network(directed=False)
        self.single_node_network.add_edges([
            ['A', 'L1', 'A', 'L1', 1]  # Self-loop
        ], input_type='list')
        
    def test_layer_degree_centrality_unweighted(self):
        """Test layer-specific degree centrality (unweighted)."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.layer_degree_centrality(layer='L1', weighted=False)
        
        # In layer L1 (triangle), all nodes should have degree 2
        self.assertEqual(centralities['A'], 2)
        self.assertEqual(centralities['B'], 2)
        self.assertEqual(centralities['C'], 2)
        
        # Test layer L2 (line)
        centralities_l2 = calc.layer_degree_centrality(layer='L2', weighted=False)
        self.assertEqual(centralities_l2['A'], 1)
        self.assertEqual(centralities_l2['B'], 2)
        self.assertEqual(centralities_l2['C'], 1)
        
    def test_layer_degree_centrality_weighted(self):
        """Test layer-specific strength centrality (weighted)."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.layer_degree_centrality(layer='L1', weighted=True)
        
        # In layer L1, all edges have weight 1, so strength = degree
        self.assertEqual(centralities['A'], 2)
        self.assertEqual(centralities['B'], 2)
        self.assertEqual(centralities['C'], 2)
        
        # In layer L2, edges have weight 2
        centralities_l2 = calc.layer_degree_centrality(layer='L2', weighted=True)
        self.assertEqual(centralities_l2['A'], 2)
        self.assertEqual(centralities_l2['B'], 4)
        self.assertEqual(centralities_l2['C'], 2)
        
    def test_layer_degree_centrality_directed(self):
        """Test layer-specific degree centrality for directed networks."""
        calc = MultilayerCentrality(self.directed_network)
        
        # Out-degree
        out_centralities = calc.layer_degree_centrality(layer='L1', weighted=False, direction='out')
        self.assertEqual(out_centralities['A'], 1)
        self.assertEqual(out_centralities['B'], 1)
        self.assertEqual(out_centralities['C'], 0)
        
        # In-degree
        in_centralities = calc.layer_degree_centrality(layer='L1', weighted=False, direction='in')
        self.assertEqual(in_centralities['A'], 0)
        self.assertEqual(in_centralities['B'], 1)
        self.assertEqual(in_centralities['C'], 1)
        
    def test_all_layers_degree_centrality(self):
        """Test degree centrality computation for all layers."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.layer_degree_centrality(weighted=False)
        
        # Check that we get results for both layers
        self.assertIn(('A', 'L1'), centralities)
        self.assertIn(('A', 'L2'), centralities)
        self.assertIn(('B', 'L1'), centralities)
        self.assertIn(('B', 'L2'), centralities)
        
        # Verify values
        self.assertEqual(centralities[('A', 'L1')], 2)
        self.assertEqual(centralities[('A', 'L2')], 1)
        self.assertEqual(centralities[('B', 'L1')], 2)
        self.assertEqual(centralities[('B', 'L2')], 2)
        
    def test_supra_degree_centrality(self):
        """Test supra degree centrality."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.supra_degree_centrality(weighted=False)
        
        # Each node should have entries for both layers
        self.assertIn(('A', 'L1'), centralities)
        self.assertIn(('A', 'L2'), centralities)
        
        # Values should be >= layer-specific values due to interlayer connections
        self.assertGreaterEqual(centralities[('A', 'L1')], 2)
        self.assertGreaterEqual(centralities[('A', 'L2')], 1)
        
    def test_overlapping_degree_centrality(self):
        """Test overlapping degree centrality."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.overlapping_degree_centrality(weighted=False)
        
        # Should return node-level centralities
        self.assertIn('A', centralities)
        self.assertIn('B', centralities)
        self.assertIn('C', centralities)
        
        # A has degree 2 in L1 and 1 in L2, so overlapping degree = 3
        self.assertEqual(centralities['A'], 3)
        # B has degree 2 in L1 and 2 in L2, so overlapping degree = 4
        self.assertEqual(centralities['B'], 4)
        # C has degree 2 in L1 and 1 in L2, so overlapping degree = 3
        self.assertEqual(centralities['C'], 3)
        
    def test_overlapping_strength_centrality(self):
        """Test overlapping strength centrality."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.overlapping_degree_centrality(weighted=True)
        
        # A has strength 2 in L1 and 2 in L2, so overlapping strength = 4
        self.assertEqual(centralities['A'], 4)
        # B has strength 2 in L1 and 4 in L2, so overlapping strength = 6
        self.assertEqual(centralities['B'], 6)
        # C has strength 2 in L1 and 2 in L2, so overlapping strength = 4
        self.assertEqual(centralities['C'], 4)
        
    def test_participation_coefficient(self):
        """Test participation coefficient."""
        calc = MultilayerCentrality(self.simple_network)
        coefficients = calc.participation_coefficient(weighted=False)
        
        # Should return values between 0 and 1
        for node, coeff in coefficients.items():
            self.assertGreaterEqual(coeff, 0)
            self.assertLessEqual(coeff, 1)
        
        # Node B has more balanced degree distribution (2,2) vs A and C (2,1)
        # so B should have higher participation coefficient
        self.assertGreater(coefficients['B'], coefficients['A'])
        self.assertGreater(coefficients['B'], coefficients['C'])
        
    def test_participation_coefficient_edge_case(self):
        """Test participation coefficient edge case (zero degree)."""
        # Create network with isolated node
        isolated_network = multinet.multi_layer_network(directed=False)
        isolated_network.add_edges([
            ['A', 'L1', 'B', 'L1', 1]
        ], input_type='list')
        
        calc = MultilayerCentrality(isolated_network)
        coefficients = calc.participation_coefficient(weighted=False)
        
        # All nodes should have valid coefficients (0 for isolated nodes)
        for node, coeff in coefficients.items():
            self.assertGreaterEqual(coeff, 0)
            self.assertLessEqual(coeff, 1)
            self.assertFalse(np.isnan(coeff))
        
    def test_multiplex_eigenvector_centrality(self):
        """Test multiplex eigenvector centrality."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.multiplex_eigenvector_centrality()
        
        # Should return node-layer centralities
        self.assertIn(('A', 'L1'), centralities)
        self.assertIn(('A', 'L2'), centralities)
        
        # All values should be non-negative
        for centrality in centralities.values():
            self.assertGreaterEqual(centrality, 0)
        
        # Sum of squares should be approximately 1 (normalized eigenvector)
        sum_squares = sum(c**2 for c in centralities.values())
        self.assertAlmostEqual(sum_squares, 1.0, places=3)
        
    def test_eigenvector_versatility(self):
        """Test eigenvector versatility (node-level aggregation)."""
        calc = MultilayerCentrality(self.simple_network)
        versatility = calc.multiplex_eigenvector_versatility()
        
        # Should return node-level centralities
        self.assertIn('A', versatility)
        self.assertIn('B', versatility)
        self.assertIn('C', versatility)
        
        # All values should be non-negative
        for value in versatility.values():
            self.assertGreaterEqual(value, 0)
        
    def test_katz_bonacich_centrality(self):
        """Test Katz-Bonacich centrality."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.katz_bonacich_centrality(alpha=0.1)
        
        # Should return node-layer centralities
        self.assertIn(('A', 'L1'), centralities)
        self.assertIn(('A', 'L2'), centralities)
        
        # All values should be positive (due to exogenous term)
        for centrality in centralities.values():
            self.assertGreater(centrality, 0)
        
    def test_pagerank_centrality(self):
        """Test PageRank centrality."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.pagerank_centrality()
        
        # Should return node-layer centralities
        self.assertIn(('A', 'L1'), centralities)
        self.assertIn(('A', 'L2'), centralities)
        
        # All values should be positive
        for centrality in centralities.values():
            self.assertGreater(centrality, 0)
        
        # Sum should be approximately 1
        total = sum(centralities.values())
        self.assertAlmostEqual(total, 1.0, places=3)
        
    def test_aggregation_methods(self):
        """Test different aggregation methods."""
        calc = MultilayerCentrality(self.simple_network)
        layer_centralities = calc.layer_degree_centrality(weighted=False)
        
        # Test sum aggregation
        sum_agg = calc.aggregate_to_node_level(layer_centralities, method='sum')
        self.assertEqual(sum_agg['A'], 3)  # 2 + 1
        self.assertEqual(sum_agg['B'], 4)  # 2 + 2
        
        # Test mean aggregation
        mean_agg = calc.aggregate_to_node_level(layer_centralities, method='mean')
        self.assertEqual(mean_agg['A'], 1.5)  # (2 + 1) / 2
        self.assertEqual(mean_agg['B'], 2.0)  # (2 + 2) / 2
        
        # Test max aggregation
        max_agg = calc.aggregate_to_node_level(layer_centralities, method='max')
        self.assertEqual(max_agg['A'], 2)  # max(2, 1)
        self.assertEqual(max_agg['B'], 2)  # max(2, 2)
        
        # Test weighted sum
        weights = {'L1': 2, 'L2': 1}
        weighted_agg = calc.aggregate_to_node_level(layer_centralities, 
                                                   method='weighted_sum', 
                                                   weights=weights)
        self.assertEqual(weighted_agg['A'], 5)  # 2*2 + 1*1
        self.assertEqual(weighted_agg['B'], 6)  # 2*2 + 1*2
        
    def test_single_node_network(self):
        """Test centrality measures on single node network."""
        calc = MultilayerCentrality(self.single_node_network)
        
        # Should not raise errors
        degree_centralities = calc.layer_degree_centrality(weighted=False)
        supra_centralities = calc.supra_degree_centrality(weighted=False)
        participation = calc.participation_coefficient(weighted=False)
        
        # Single node should have some valid centrality values
        self.assertIsInstance(degree_centralities, dict)
        self.assertIsInstance(supra_centralities, dict)
        self.assertIsInstance(participation, dict)
        
    def test_multilayer_closeness_centrality(self):
        """Test multilayer closeness centrality."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.multilayer_closeness_centrality()
        
        # Should return node-layer centralities
        self.assertIn(('A', 'L1'), centralities)
        self.assertIn(('A', 'L2'), centralities)
        
        # All values should be non-negative
        for centrality in centralities.values():
            self.assertGreaterEqual(centrality, 0)

    def test_multilayer_closeness_harmonic_variant(self):
        """Test multilayer closeness centrality with harmonic variant."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.multilayer_closeness_centrality(variant='harmonic')
        
        # Should return node-layer centralities
        self.assertIn(('A', 'L1'), centralities)
        self.assertIn(('A', 'L2'), centralities)
        
        # All values should be non-negative
        for centrality in centralities.values():
            self.assertGreaterEqual(centrality, 0)

    def test_multilayer_closeness_auto_variant(self):
        """Test multilayer closeness centrality with auto variant."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.multilayer_closeness_centrality(variant='auto')
        
        # Should return node-layer centralities
        self.assertIn(('A', 'L1'), centralities)
        self.assertIn(('A', 'L2'), centralities)
        
        # All values should be non-negative
        for centrality in centralities.values():
            self.assertGreaterEqual(centrality, 0)
        
    def test_multilayer_betweenness_centrality(self):
        """Test multilayer betweenness centrality."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.multilayer_betweenness_centrality()
        
        # Should return node-layer centralities
        self.assertIn(('A', 'L1'), centralities)
        self.assertIn(('A', 'L2'), centralities)
        
        # All values should be non-negative
        for centrality in centralities.values():
            self.assertGreaterEqual(centrality, 0)
            
    def test_hits_centrality(self):
        """Test HITS centrality."""
        calc = MultilayerCentrality(self.simple_network)
        hits_results = calc.hits_centrality()
        
        # For undirected networks, should be equivalent to eigenvector centrality
        self.assertIsInstance(hits_results, dict)
        # Should return node-layer centralities
        self.assertIn(('A', 'L1'), hits_results)
        
        # All values should be non-negative
        for centrality in hits_results.values():
            self.assertGreaterEqual(centrality, 0)
    
    def test_hits_centrality_directed(self):
        """Test HITS centrality on directed network."""
        calc = MultilayerCentrality(self.directed_network)
        hits_results = calc.hits_centrality()
        
        # For directed networks, should return hubs and authorities
        if isinstance(hits_results, dict) and 'hubs' in hits_results:
            self.assertIn('hubs', hits_results)
            self.assertIn('authorities', hits_results)
            
            # Check that we have results for node-layer pairs
            self.assertIn(('A', 'L1'), hits_results['hubs'])
            self.assertIn(('A', 'L1'), hits_results['authorities'])
    
    def test_current_flow_closeness_centrality(self):
        """Test current-flow closeness centrality."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.current_flow_closeness_centrality()
        
        # Should return node-layer centralities
        self.assertIn(('A', 'L1'), centralities)
        self.assertIn(('A', 'L2'), centralities)
        
        # All values should be non-negative
        for centrality in centralities.values():
            self.assertGreaterEqual(centrality, 0)
    
    def test_current_flow_betweenness_centrality(self):
        """Test current-flow betweenness centrality."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.current_flow_betweenness_centrality()
        
        # Should return node-layer centralities
        self.assertIn(('A', 'L1'), centralities)
        self.assertIn(('A', 'L2'), centralities)
        
        # All values should be non-negative
        for centrality in centralities.values():
            self.assertGreaterEqual(centrality, 0)
    
    def test_subgraph_centrality(self):
        """Test subgraph centrality."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.subgraph_centrality()
        
        # Should return node-layer centralities
        self.assertIn(('A', 'L1'), centralities)
        self.assertIn(('A', 'L2'), centralities)
        
        # All values should be positive (matrix exponential diagonal elements)
        for centrality in centralities.values():
            self.assertGreater(centrality, 0)
    
    def test_total_communicability(self):
        """Test total communicability."""
        calc = MultilayerCentrality(self.simple_network)
        centralities = calc.total_communicability()
        
        # Should return node-layer centralities
        self.assertIn(('A', 'L1'), centralities)
        self.assertIn(('A', 'L2'), centralities)
        
        # All values should be positive
        for centrality in centralities.values():
            self.assertGreater(centrality, 0)
    
    def test_multiplex_k_core(self):
        """Test multiplex k-core decomposition."""
        calc = MultilayerCentrality(self.simple_network)
        core_numbers = calc.multiplex_k_core()
        
        # Should return node-layer centralities
        self.assertIn(('A', 'L1'), core_numbers)
        self.assertIn(('A', 'L2'), core_numbers)
        
        # All values should be non-negative integers
        for core_num in core_numbers.values():
            self.assertGreaterEqual(core_num, 0)
            self.assertIsInstance(core_num, (int, np.integer))
    
    def test_multiplex_coreness(self):
        """Test multiplex coreness (alias for k-core)."""
        calc = MultilayerCentrality(self.simple_network)
        core_numbers = calc.multiplex_coreness()
        k_core_numbers = calc.multiplex_k_core()
        
        # Should be identical to k-core
        self.assertEqual(core_numbers, k_core_numbers)
    
    def test_compute_all_centralities_with_advanced(self):
        """Test the convenience function with advanced measures included."""
        results = compute_all_centralities(self.simple_network, 
                                          include_path_based=True, 
                                          include_advanced=True)
        
        # Should contain all expected centrality measures including advanced ones
        expected_measures = [
            'layer_degree', 'layer_strength', 'supra_degree', 'supra_strength',
            'overlapping_degree', 'overlapping_strength', 'participation_coefficient',
            'participation_coefficient_strength', 'multiplex_eigenvector',
            'eigenvector_versatility', 'katz_bonacich', 'pagerank',
            'closeness', 'betweenness', 'hits', 'current_flow_closeness',
            'current_flow_betweenness', 'subgraph_centrality', 'total_communicability',
            'multiplex_k_core'
        ]
        
        for measure in expected_measures:
            self.assertIn(measure, results)
            self.assertIsInstance(results[measure], dict)
            self.assertGreater(len(results[measure]), 0)
    
    def test_compute_all_centralities_with_path_based(self):
        """Test the convenience function with path-based measures included."""
        results = compute_all_centralities(self.simple_network, include_path_based=True)
        
        # Should contain all expected centrality measures including path-based
        expected_measures = [
            'layer_degree', 'layer_strength', 'supra_degree', 'supra_strength',
            'overlapping_degree', 'overlapping_strength', 'participation_coefficient',
            'participation_coefficient_strength', 'multiplex_eigenvector',
            'eigenvector_versatility', 'katz_bonacich', 'pagerank',
            'closeness', 'betweenness'
        ]
        
        for measure in expected_measures:
            self.assertIn(measure, results)
            self.assertIsInstance(results[measure], dict)
            self.assertGreater(len(results[measure]), 0)
    
    def test_compute_all_centralities(self):
        """Test the convenience function to compute all centralities."""
        results = compute_all_centralities(self.simple_network)
        
        # Should contain all expected centrality measures
        expected_measures = [
            'layer_degree', 'layer_strength', 'supra_degree', 'supra_strength',
            'overlapping_degree', 'overlapping_strength', 'participation_coefficient',
            'participation_coefficient_strength', 'multiplex_eigenvector',
            'eigenvector_versatility', 'katz_bonacich', 'pagerank'
        ]
        
        for measure in expected_measures:
            self.assertIn(measure, results)
            self.assertIsInstance(results[measure], dict)
            self.assertGreater(len(results[measure]), 0)
        
    def test_invalid_aggregation_method(self):
        """Test error handling for invalid aggregation method."""
        calc = MultilayerCentrality(self.simple_network)
        layer_centralities = calc.layer_degree_centrality(weighted=False)
        
        with self.assertRaises(ValueError):
            calc.aggregate_to_node_level(layer_centralities, method='invalid')
        
    def test_weighted_sum_without_weights(self):
        """Test error handling for weighted sum without weights."""
        calc = MultilayerCentrality(self.simple_network)
        layer_centralities = calc.layer_degree_centrality(weighted=False)
        
        with self.assertRaises(ValueError):
            calc.aggregate_to_node_level(layer_centralities, method='weighted_sum')


class TestCentralityConsistency(unittest.TestCase):
    """Test consistency and mathematical properties of centrality measures."""
    
    def setUp(self):
        """Set up test network."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available for multilayer centrality tests")
            
        self.network = multinet.multi_layer_network(directed=False)
        self.network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['A', 'L2', 'C', 'L2', 1]
        ], input_type='list')
        
    def test_overlapping_equals_sum_of_layers(self):
        """Test that overlapping degree equals sum of layer-specific degrees."""
        calc = MultilayerCentrality(self.network)
        
        layer_centralities = calc.layer_degree_centrality(weighted=False)
        overlapping_centralities = calc.overlapping_degree_centrality(weighted=False)
        
        # Manually compute sum for each node
        manual_sum = {}
        for (node, layer), centrality in layer_centralities.items():
            if node not in manual_sum:
                manual_sum[node] = 0
            manual_sum[node] += centrality
        
        # Should match overlapping centralities
        for node in manual_sum:
            self.assertEqual(manual_sum[node], overlapping_centralities[node])
            
    def test_participation_coefficient_bounds(self):
        """Test that participation coefficient is always between 0 and 1."""
        calc = MultilayerCentrality(self.network)
        coefficients = calc.participation_coefficient(weighted=False)
        
        for node, coeff in coefficients.items():
            self.assertGreaterEqual(coeff, 0, f"Node {node} has negative participation coefficient")
            self.assertLessEqual(coeff, 1, f"Node {node} has participation coefficient > 1")
            
    def test_pagerank_sums_to_one(self):
        """Test that PageRank centralities sum to 1."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.pagerank_centrality()
        
        total = sum(centralities.values())
        self.assertAlmostEqual(total, 1.0, places=3)


class TestDisconnectedNetworkCloseness(unittest.TestCase):
    """Test cases for closeness centrality on disconnected multilayer networks."""
    
    def setUp(self):
        """Set up disconnected test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available for disconnected network tests")
            
        # Create a disconnected multilayer network (two components in different layers)
        self.disconnected_network = multinet.multi_layer_network(directed=False)
        
        # Component 1 in L1: A-B-C triangle
        self.disconnected_network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['C', 'L1', 'A', 'L1', 1]
        ], input_type='list')
        
        # Component 2 in L2: D-E edge (no connection to L1)
        self.disconnected_network.add_edges([
            ['D', 'L2', 'E', 'L2', 1]
        ], input_type='list')
        
    def test_standard_closeness_on_disconnected(self):
        """Test standard closeness centrality on disconnected network."""
        calc = MultilayerCentrality(self.disconnected_network)
        centralities = calc.multilayer_closeness_centrality(variant='standard')
        
        # Should return node-layer centralities
        self.assertIn(('A', 'L1'), centralities)
        self.assertIn(('D', 'L2'), centralities)
        
        # All values should be non-negative
        for centrality in centralities.values():
            self.assertGreaterEqual(centrality, 0)
        
    def test_harmonic_closeness_on_disconnected(self):
        """Test harmonic closeness centrality on disconnected network."""
        calc = MultilayerCentrality(self.disconnected_network)
        centralities = calc.multilayer_closeness_centrality(variant='harmonic')
        
        # Should return node-layer centralities
        self.assertIn(('A', 'L1'), centralities)
        self.assertIn(('D', 'L2'), centralities)
        
        # All values should be non-negative
        for centrality in centralities.values():
            self.assertGreaterEqual(centrality, 0)
        
        # Nodes in L1 triangle should have higher harmonic closeness than L2 edge
        # (more reachable nodes at shorter distances)
        l1_avg = np.mean([centralities[('A', 'L1')], 
                         centralities[('B', 'L1')], 
                         centralities[('C', 'L1')]])
        l2_avg = np.mean([centralities[('D', 'L2')], 
                         centralities[('E', 'L2')]])
        self.assertGreater(l1_avg, l2_avg)
        
    def test_auto_closeness_selects_harmonic_for_disconnected(self):
        """Test that auto variant selects harmonic for disconnected network."""
        calc = MultilayerCentrality(self.disconnected_network)
        
        # Get closeness with auto variant
        auto_centralities = calc.multilayer_closeness_centrality(variant='auto')
        
        # Get closeness with explicit harmonic variant
        harmonic_centralities = calc.multilayer_closeness_centrality(variant='harmonic')
        
        # For a disconnected network, auto should choose harmonic
        for node_layer in auto_centralities:
            self.assertAlmostEqual(
                auto_centralities[node_layer], 
                harmonic_centralities[node_layer],
                places=6,
                msg=f"Auto and harmonic should match for {node_layer}"
            )
    
    def test_harmonic_closeness_handles_unreachable_nodes(self):
        """Test that harmonic closeness properly handles unreachable nodes."""
        calc = MultilayerCentrality(self.disconnected_network)
        centralities = calc.multilayer_closeness_centrality(variant='harmonic')
        
        # No node should have infinite or NaN closeness
        for node_layer, value in centralities.items():
            self.assertFalse(np.isnan(value), f"NaN closeness for {node_layer}")
            self.assertFalse(np.isinf(value), f"Infinite closeness for {node_layer}")
        
        # All nodes should have positive closeness (at least 1 reachable neighbor)
        for node_layer, value in centralities.items():
            self.assertGreater(value, 0, f"Zero closeness for {node_layer}")
    
    def test_compute_all_centralities_with_harmonic_variant(self):
        """Test compute_all_centralities with harmonic closeness variant."""
        results = compute_all_centralities(
            self.disconnected_network,
            include_path_based=True,
            closeness_variant='harmonic'
        )
        
        # Should contain closeness
        self.assertIn('closeness', results)
        
        # Closeness values should be non-negative
        for value in results['closeness'].values():
            self.assertGreaterEqual(value, 0)
    
    def test_compute_all_centralities_with_auto_variant(self):
        """Test compute_all_centralities with auto closeness variant."""
        results = compute_all_centralities(
            self.disconnected_network,
            include_path_based=True,
            closeness_variant='auto'
        )
        
        # Should contain closeness
        self.assertIn('closeness', results)
        
        # Closeness values should be non-negative
        for value in results['closeness'].values():
            self.assertGreaterEqual(value, 0)


class TestExtendedCentralityMetrics(unittest.TestCase):
    """Test cases for extended centrality measures (metrics 18-30)."""
    
    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available for extended centrality tests")
            
        # Create a simple 2-layer, 4-node test network
        self.network = multinet.multi_layer_network(directed=False)
        
        # Layer 1: A square
        self.network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1], 
            ['C', 'L1', 'D', 'L1', 1],
            ['D', 'L1', 'A', 'L1', 1]
        ], input_type='list')
        
        # Layer 2: A line
        self.network.add_edges([
            ['A', 'L2', 'B', 'L2', 1],
            ['B', 'L2', 'C', 'L2', 1],
            ['C', 'L2', 'D', 'L2', 1]
        ], input_type='list')
        
    def test_information_centrality_returns_dict(self):
        """Test that information centrality returns a dictionary."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.information_centrality()
        
        self.assertIsInstance(centralities, dict)
        self.assertGreater(len(centralities), 0)
        
    def test_information_centrality_values_non_negative(self):
        """Test that information centrality values are non-negative."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.information_centrality()
        
        for node_layer, value in centralities.items():
            self.assertGreaterEqual(value, 0, 
                f"Information centrality for {node_layer} is negative: {value}")
    
    def test_communicability_betweenness_returns_dict(self):
        """Test that communicability betweenness returns a dictionary."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.communicability_betweenness_centrality()
        
        self.assertIsInstance(centralities, dict)
        self.assertGreater(len(centralities), 0)
        
    def test_communicability_betweenness_values_non_negative(self):
        """Test that communicability betweenness values are non-negative."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.communicability_betweenness_centrality(normalized=True)
        
        for node_layer, value in centralities.items():
            self.assertGreaterEqual(value, 0,
                f"Communicability betweenness for {node_layer} is negative: {value}")
    
    def test_accessibility_centrality_returns_dict(self):
        """Test that accessibility centrality returns a dictionary."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.accessibility_centrality(h=2)
        
        self.assertIsInstance(centralities, dict)
        self.assertGreater(len(centralities), 0)
        
    def test_accessibility_centrality_values_positive(self):
        """Test that accessibility centrality values are positive."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.accessibility_centrality(h=2)
        
        for node_layer, value in centralities.items():
            self.assertGreater(value, 0,
                f"Accessibility for {node_layer} is not positive: {value}")
    
    def test_harmonic_closeness_returns_dict(self):
        """Test that harmonic closeness returns a dictionary."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.harmonic_closeness_centrality()
        
        self.assertIsInstance(centralities, dict)
        self.assertGreater(len(centralities), 0)
        
    def test_harmonic_closeness_values_non_negative(self):
        """Test that harmonic closeness values are non-negative."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.harmonic_closeness_centrality()
        
        for node_layer, value in centralities.items():
            self.assertGreaterEqual(value, 0,
                f"Harmonic closeness for {node_layer} is negative: {value}")
    
    def test_local_efficiency_returns_dict(self):
        """Test that local efficiency returns a dictionary."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.local_efficiency_centrality()
        
        self.assertIsInstance(centralities, dict)
        self.assertGreater(len(centralities), 0)
        
    def test_local_efficiency_values_in_range(self):
        """Test that local efficiency values are between 0 and reasonable upper bound."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.local_efficiency_centrality()
        
        for node_layer, value in centralities.items():
            self.assertGreaterEqual(value, 0,
                f"Local efficiency for {node_layer} is negative: {value}")
    
    def test_edge_betweenness_returns_dict(self):
        """Test that edge betweenness returns a dictionary."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.edge_betweenness_centrality()
        
        self.assertIsInstance(centralities, dict)
        # Edge betweenness may be empty if no edges exist
        
    def test_bridging_centrality_returns_dict(self):
        """Test that bridging centrality returns a dictionary."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.bridging_centrality()
        
        self.assertIsInstance(centralities, dict)
        self.assertGreater(len(centralities), 0)
        
    def test_bridging_centrality_values_non_negative(self):
        """Test that bridging centrality values are non-negative."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.bridging_centrality()
        
        for node_layer, value in centralities.items():
            self.assertGreaterEqual(value, 0,
                f"Bridging centrality for {node_layer} is negative: {value}")
    
    def test_percolation_centrality_returns_dict(self):
        """Test that percolation centrality returns a dictionary."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.percolation_centrality(trials=10)
        
        self.assertIsInstance(centralities, dict)
        self.assertGreater(len(centralities), 0)
        
    def test_percolation_centrality_values_in_range(self):
        """Test that percolation centrality values are in valid range."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.percolation_centrality(trials=10)
        
        for node_layer, value in centralities.items():
            self.assertGreaterEqual(value, 0,
                f"Percolation centrality for {node_layer} is negative: {value}")
            self.assertLessEqual(value, 1,
                f"Percolation centrality for {node_layer} exceeds 1: {value}")
    
    def test_spreading_centrality_returns_dict(self):
        """Test that spreading centrality returns a dictionary."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.spreading_centrality(trials=5, steps=10)
        
        self.assertIsInstance(centralities, dict)
        self.assertGreater(len(centralities), 0)
        
    def test_spreading_centrality_values_in_range(self):
        """Test that spreading centrality values are in valid range."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.spreading_centrality(trials=5, steps=10)
        
        for node_layer, value in centralities.items():
            self.assertGreaterEqual(value, 0,
                f"Spreading centrality for {node_layer} is negative: {value}")
            self.assertLessEqual(value, 1,
                f"Spreading centrality for {node_layer} exceeds 1: {value}")
    
    def test_collective_influence_returns_dict(self):
        """Test that collective influence returns a dictionary."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.collective_influence(radius=2)
        
        self.assertIsInstance(centralities, dict)
        self.assertGreater(len(centralities), 0)
        
    def test_collective_influence_values_non_negative(self):
        """Test that collective influence values are non-negative."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.collective_influence(radius=2)
        
        for node_layer, value in centralities.items():
            self.assertGreaterEqual(value, 0,
                f"Collective influence for {node_layer} is negative: {value}")
    
    def test_load_centrality_returns_dict(self):
        """Test that load centrality returns a dictionary."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.load_centrality()
        
        self.assertIsInstance(centralities, dict)
        self.assertGreater(len(centralities), 0)
        
    def test_load_centrality_values_non_negative(self):
        """Test that load centrality values are non-negative."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.load_centrality()
        
        for node_layer, value in centralities.items():
            self.assertGreaterEqual(value, 0,
                f"Load centrality for {node_layer} is negative: {value}")
    
    def test_flow_betweenness_returns_dict(self):
        """Test that flow betweenness returns a dictionary."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.flow_betweenness_centrality(samples=10)
        
        self.assertIsInstance(centralities, dict)
        self.assertGreater(len(centralities), 0)
        
    def test_flow_betweenness_values_non_negative(self):
        """Test that flow betweenness values are non-negative."""
        calc = MultilayerCentrality(self.network)
        centralities = calc.flow_betweenness_centrality(samples=10)
        
        for node_layer, value in centralities.items():
            self.assertGreaterEqual(value, 0,
                f"Flow betweenness for {node_layer} is negative: {value}")
    
    def test_lp_aggregated_centrality_l2_norm(self):
        """Test Lp-aggregated centrality with L2 norm."""
        calc = MultilayerCentrality(self.network)
        
        # Get layer degrees as input
        layer_degrees = calc.layer_degree_centrality(weighted=False)
        
        # Aggregate with L2 norm
        aggregated = calc.lp_aggregated_centrality(layer_degrees, p=2)
        
        self.assertIsInstance(aggregated, dict)
        self.assertGreater(len(aggregated), 0)
        
        for node, value in aggregated.items():
            self.assertGreaterEqual(value, 0,
                f"Lp-aggregated centrality for {node} is negative: {value}")
    
    def test_lp_aggregated_centrality_linf_norm(self):
        """Test Lp-aggregated centrality with L-infinity norm."""
        calc = MultilayerCentrality(self.network)
        
        # Get layer degrees as input
        layer_degrees = calc.layer_degree_centrality(weighted=False)
        
        # Aggregate with L-infinity norm
        aggregated = calc.lp_aggregated_centrality(layer_degrees, p=float('inf'))
        
        self.assertIsInstance(aggregated, dict)
        self.assertGreater(len(aggregated), 0)
        
        for node, value in aggregated.items():
            self.assertGreaterEqual(value, 0,
                f"Lp-aggregated centrality (L-inf) for {node} is negative: {value}")
    
    def test_compute_all_centralities_extended(self):
        """Test that compute_all_centralities with extended flag works."""
        results = compute_all_centralities(self.network, include_extended=True)
        
        self.assertIsInstance(results, dict)
        
        # Check that extended measures are included
        extended_keys = [
            'information', 'communicability_betweenness', 'accessibility',
            'harmonic_closeness', 'local_efficiency', 'edge_betweenness',
            'bridging', 'percolation', 'spreading', 'collective_influence',
            'load', 'flow_betweenness'
        ]
        
        for key in extended_keys:
            self.assertIn(key, results, f"Extended metric '{key}' not found in results")


if __name__ == '__main__':
    unittest.main()