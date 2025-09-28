#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for multilayer centrality measures.

This module contains comprehensive tests for all centrality measures
implemented in py3plex.algorithms.multilayer_algorithms.centrality.
"""

import unittest
import numpy as np
from py3plex.core import multinet
from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality, compute_all_centralities


class TestMultilayerCentrality(unittest.TestCase):
    """Test cases for multilayer centrality measures."""
    
    def setUp(self):
        """Set up test networks."""
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


if __name__ == '__main__':
    unittest.main()