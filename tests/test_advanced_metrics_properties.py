#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for advanced multilayer metrics.

This module uses Hypothesis for property-based testing to ensure
mathematical properties of entropy, mutual information, and correlation metrics.
"""

import unittest

try:
    import numpy as np
    from hypothesis import given, strategies as st, settings, assume
    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: {e}")


def skip_if_no_deps(test_func):
    """Decorator to skip tests when dependencies are missing."""
    if not DEPENDENCIES_AVAILABLE:
        return unittest.skip("Dependencies not available")(test_func)
    return test_func


def create_simple_network(num_nodes=3, num_layers=2):
    """Create a simple test network."""
    network = multinet.multi_layer_network(directed=False)
    nodes = [f'N{i}' for i in range(num_nodes)]
    layers = [f'L{i}' for i in range(num_layers)]
    
    # Add edges within each layer
    for layer in layers:
        for i in range(len(nodes) - 1):
            network.add_edges([
                [nodes[i], layer, nodes[i+1], layer, 1]
            ], input_type='list')
    
    # Add some inter-layer edges
    for node in nodes[:2]:
        for i in range(len(layers) - 1):
            network.add_edges([
                [node, layers[i], node, layers[i+1], 1]
            ], input_type='list')
    
    return network


class TestEntropyProperties(unittest.TestCase):
    """Property-based tests for entropy metrics."""
    
    @skip_if_no_deps
    def test_entropy_non_negative(self):
        """Property: All entropy values must be non-negative."""
        network = create_simple_network(num_nodes=4, num_layers=3)
        
        # Layer connectivity entropy
        for layer in ['L0', 'L1', 'L2']:
            entropy = mls.layer_connectivity_entropy(network, layer)
            self.assertGreaterEqual(entropy, 0.0, 
                f"Layer connectivity entropy for {layer} is negative: {entropy}")
        
        # Inter-layer dependence entropy
        entropy = mls.inter_layer_dependence_entropy(network, 'L0', 'L1')
        self.assertGreaterEqual(entropy, 0.0,
            f"Inter-layer dependence entropy is negative: {entropy}")
        
        # Cross-layer redundancy entropy
        entropy = mls.cross_layer_redundancy_entropy(network)
        self.assertGreaterEqual(entropy, 0.0,
            f"Cross-layer redundancy entropy is negative: {entropy}")
    
    @skip_if_no_deps
    def test_entropy_empty_network(self):
        """Property: Entropy of empty network should be zero."""
        network = multinet.multi_layer_network(directed=False)
        
        entropy = mls.layer_connectivity_entropy(network, 'L1')
        self.assertEqual(entropy, 0.0)
        
        entropy = mls.cross_layer_redundancy_entropy(network)
        self.assertEqual(entropy, 0.0)
    
    @skip_if_no_deps
    def test_entropy_single_layer(self):
        """Property: Cross-layer entropy is zero for single-layer network."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1]
        ], input_type='list')
        
        entropy = mls.cross_layer_redundancy_entropy(network)
        self.assertEqual(entropy, 0.0,
            "Single-layer network should have zero cross-layer redundancy entropy")
    
    @skip_if_no_deps
    def test_entropy_uniform_distribution(self):
        """Property: Uniform edge distribution yields maximum entropy."""
        network = multinet.multi_layer_network(directed=False)
        
        # Create network with uniform edge distribution across layers
        for layer in ['L1', 'L2', 'L3']:
            network.add_edges([
                ['A', layer, 'B', layer, 1],
                ['B', layer, 'C', layer, 1]
            ], input_type='list')
        
        entropy = mls.entropy_of_multiplexity(network)
        expected_max = np.log2(3)  # log2(num_layers)
        
        # Should be close to maximum (allowing for small numerical differences)
        self.assertAlmostEqual(entropy, expected_max, places=1,
            msg=f"Uniform distribution should yield max entropy ~{expected_max}, got {entropy}")


class TestMutualInformationProperties(unittest.TestCase):
    """Property-based tests for mutual information."""
    
    @skip_if_no_deps
    def test_mutual_information_non_negative(self):
        """Property: Mutual information is always non-negative."""
        network = create_simple_network(num_nodes=5, num_layers=3)
        
        mi = mls.cross_layer_mutual_information(network, 'L0', 'L1', bins=5)
        self.assertGreaterEqual(mi, 0.0,
            f"Mutual information is negative: {mi}")
    
    @skip_if_no_deps
    def test_mutual_information_symmetry(self):
        """Property: MI(X;Y) = MI(Y;X) (symmetric)."""
        network = create_simple_network(num_nodes=4, num_layers=2)
        
        mi_01 = mls.cross_layer_mutual_information(network, 'L0', 'L1', bins=5)
        mi_10 = mls.cross_layer_mutual_information(network, 'L1', 'L0', bins=5)
        
        self.assertAlmostEqual(mi_01, mi_10, places=6,
            msg=f"Mutual information not symmetric: MI(L0;L1)={mi_01}, MI(L1;L0)={mi_10}")
    
    @skip_if_no_deps
    def test_mutual_information_independence(self):
        """Property: MI = 0 for independent layers."""
        network = multinet.multi_layer_network(directed=False)
        
        # Layer 1: only nodes A, B
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['A', 'L1', 'B', 'L1', 1]  # Higher degree for A
        ], input_type='list')
        
        # Layer 2: only nodes C, D (no overlap)
        network.add_edges([
            ['C', 'L2', 'D', 'L2', 1]
        ], input_type='list')
        
        mi = mls.cross_layer_mutual_information(network, 'L1', 'L2', bins=5)
        self.assertEqual(mi, 0.0,
            "Layers with no common nodes should have MI = 0")
    
    @skip_if_no_deps
    def test_mutual_information_uniform_degrees(self):
        """Property: MI = 0 when all nodes have same degree in both layers."""
        network = multinet.multi_layer_network(directed=False)
        
        # Both layers: all nodes have degree 1
        for layer in ['L1', 'L2']:
            network.add_edges([
                ['A', layer, 'B', layer, 1],
                ['C', layer, 'D', layer, 1]
            ], input_type='list')
        
        mi = mls.cross_layer_mutual_information(network, 'L1', 'L2', bins=5)
        self.assertEqual(mi, 0.0,
            "Uniform degree distribution in both layers should yield MI = 0")


class TestCorrelationProperties(unittest.TestCase):
    """Property-based tests for degree correlation metrics."""
    
    @skip_if_no_deps
    def test_correlation_matrix_symmetric(self):
        """Property: Correlation matrix is symmetric."""
        network = create_simple_network(num_nodes=4, num_layers=3)
        
        corr_matrix, layers = mls.interlayer_degree_correlation_matrix(network)
        
        # Check symmetry
        for i in range(len(layers)):
            for j in range(len(layers)):
                self.assertAlmostEqual(corr_matrix[i, j], corr_matrix[j, i], places=6,
                    msg=f"Correlation matrix not symmetric at ({i},{j})")
    
    @skip_if_no_deps
    def test_correlation_matrix_diagonal_ones(self):
        """Property: Diagonal elements are 1.0 (self-correlation)."""
        network = create_simple_network(num_nodes=4, num_layers=3)
        
        corr_matrix, layers = mls.interlayer_degree_correlation_matrix(network)
        
        # Check diagonal
        for i in range(len(layers)):
            self.assertAlmostEqual(corr_matrix[i, i], 1.0, places=6,
                msg=f"Diagonal element [{i},{i}] is not 1.0: {corr_matrix[i, i]}")
    
    @skip_if_no_deps
    def test_correlation_matrix_bounds(self):
        """Property: All correlations in [-1, 1]."""
        network = create_simple_network(num_nodes=5, num_layers=3)
        
        corr_matrix, layers = mls.interlayer_degree_correlation_matrix(network)
        
        # Check bounds
        self.assertTrue(np.all(corr_matrix >= -1.0),
            f"Correlation values below -1: {np.min(corr_matrix)}")
        self.assertTrue(np.all(corr_matrix <= 1.0),
            f"Correlation values above 1: {np.max(corr_matrix)}")
    
    @skip_if_no_deps
    def test_correlation_single_layer(self):
        """Property: Single-layer network has 1×1 identity matrix."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1]
        ], input_type='list')
        
        corr_matrix, layers = mls.interlayer_degree_correlation_matrix(network)
        
        self.assertEqual(corr_matrix.shape, (1, 1))
        self.assertEqual(corr_matrix[0, 0], 1.0)


class TestInfluenceProperties(unittest.TestCase):
    """Property-based tests for layer influence centrality."""
    
    @skip_if_no_deps
    def test_influence_non_negative(self):
        """Property: Influence centrality is non-negative."""
        network = create_simple_network(num_nodes=4, num_layers=3)
        
        # Coupling-based
        influence_coupling = mls.layer_influence_centrality(
            network, 'L0', method='coupling'
        )
        self.assertGreaterEqual(influence_coupling, 0.0,
            f"Coupling influence is negative: {influence_coupling}")
        
        # Flow-based
        influence_flow = mls.layer_influence_centrality(
            network, 'L0', method='flow', sample_size=50
        )
        self.assertGreaterEqual(influence_flow, 0.0,
            f"Flow influence is negative: {influence_flow}")
    
    @skip_if_no_deps
    def test_influence_single_layer(self):
        """Property: Single-layer network has zero influence."""
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'L1', 'B', 'L1', 1]
        ], input_type='list')
        
        influence = mls.layer_influence_centrality(network, 'L1', method='coupling')
        self.assertEqual(influence, 0.0,
            "Single-layer network should have zero influence")
    
    @skip_if_no_deps
    def test_influence_flow_bounded(self):
        """Property: Flow-based influence is a probability in [0, 1]."""
        network = create_simple_network(num_nodes=4, num_layers=3)
        
        influence = mls.layer_influence_centrality(
            network, 'L0', method='flow', sample_size=100
        )
        
        self.assertGreaterEqual(influence, 0.0)
        self.assertLessEqual(influence, 1.0,
            f"Flow influence exceeds 1.0: {influence}")


class TestBetweennessSurfaceProperties(unittest.TestCase):
    """Property-based tests for betweenness surface."""
    
    @skip_if_no_deps
    def test_surface_shape(self):
        """Property: Surface has correct shape (nodes × layers)."""
        network = create_simple_network(num_nodes=4, num_layers=3)
        
        surface, (nodes, layers) = mls.multilayer_betweenness_surface(network)
        
        self.assertEqual(surface.shape[0], len(nodes),
            f"Surface rows {surface.shape[0]} != number of nodes {len(nodes)}")
        self.assertEqual(surface.shape[1], len(layers),
            f"Surface cols {surface.shape[1]} != number of layers {len(layers)}")
    
    @skip_if_no_deps
    def test_surface_non_negative(self):
        """Property: All betweenness values are non-negative."""
        network = create_simple_network(num_nodes=4, num_layers=2)
        
        surface, _ = mls.multilayer_betweenness_surface(network)
        
        self.assertTrue(np.all(surface >= 0),
            f"Negative betweenness values found: {np.min(surface)}")
    
    @skip_if_no_deps
    def test_surface_normalized_bounds(self):
        """Property: Normalized betweenness in [0, 1]."""
        network = create_simple_network(num_nodes=5, num_layers=2)
        
        surface, _ = mls.multilayer_betweenness_surface(network, normalized=True)
        
        self.assertTrue(np.all(surface <= 1.0),
            f"Normalized betweenness exceeds 1.0: {np.max(surface)}")
    
    @skip_if_no_deps
    def test_surface_empty_network(self):
        """Property: Empty network returns empty surface."""
        network = multinet.multi_layer_network(directed=False)
        
        surface, (nodes, layers) = mls.multilayer_betweenness_surface(network)
        
        self.assertEqual(len(nodes), 0)
        self.assertEqual(len(layers), 0)


if __name__ == '__main__':
    unittest.main()
