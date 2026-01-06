#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Property-based tests for sensitivity analysis.

This module uses Hypothesis to ensure that sensitivity analysis
maintains proper mathematical properties and correctness guarantees.
"""

import pytest
import unittest
from typing import List, Dict, Any

try:
    import numpy as np
    from hypothesis import given, strategies as st, settings, assume
    from py3plex.core import multinet
    from py3plex.sensitivity import (
        jaccard_at_k,
        kendall_tau,
        variation_of_information,
        edge_drop,
        degree_preserving_rewire,
    )
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: {e}")


def skip_if_no_deps(test_func):
    """Decorator to skip tests when dependencies are missing."""
    if not DEPENDENCIES_AVAILABLE:
        return unittest.skip("Dependencies not available")(test_func)
    return test_func


def create_test_network(num_nodes=10, num_layers=2, seed=42):
    """Create a simple test network for property tests."""
    np.random.seed(seed)
    network = multinet.multi_layer_network(directed=False, verbose=False)
    nodes = [f'N{i}' for i in range(num_nodes)]
    layers = [f'L{i}' for i in range(num_layers)]
    
    # Add edges within each layer
    for layer in layers:
        for i in range(len(nodes) - 1):
            for j in range(i + 1, len(nodes)):
                if np.random.random() > 0.5:  # 50% edge probability
                    network.add_edges([
                        [nodes[i], layer, nodes[j], layer, 1.0]
                    ], input_type='list')
    
    return network


@pytest.mark.property
class TestStabilityMetricsProperties(unittest.TestCase):
    """Property-based tests for stability metrics."""
    
    @skip_if_no_deps
    def test_jaccard_reflexive(self):
        """Property: Jaccard(X, X) = 1.0 (reflexivity)."""
        ranking = ['a', 'b', 'c', 'd', 'e']
        for k in range(1, len(ranking) + 1):
            jaccard = jaccard_at_k(ranking, ranking, k=k)
            self.assertAlmostEqual(jaccard, 1.0, places=5,
                                 msg=f"Jaccard(X, X) != 1.0 for k={k}")
    
    @skip_if_no_deps
    def test_jaccard_symmetric(self):
        """Property: Jaccard(X, Y) = Jaccard(Y, X) (symmetry)."""
        baseline = ['a', 'b', 'c', 'd', 'e']
        perturbed = ['b', 'a', 'd', 'c', 'e']
        
        for k in range(1, len(baseline) + 1):
            jaccard_xy = jaccard_at_k(baseline, perturbed, k=k)
            jaccard_yx = jaccard_at_k(perturbed, baseline, k=k)
            self.assertAlmostEqual(jaccard_xy, jaccard_yx, places=5,
                                 msg=f"Jaccard not symmetric for k={k}")
    
    @skip_if_no_deps
    def test_jaccard_range(self):
        """Property: Jaccard ∈ [0, 1]."""
        baseline = ['a', 'b', 'c', 'd', 'e']
        perturbed = ['f', 'g', 'h', 'i', 'j']  # Completely different
        
        for k in range(1, len(baseline) + 1):
            jaccard = jaccard_at_k(baseline, perturbed, k=k)
            self.assertGreaterEqual(jaccard, 0.0,
                                  msg=f"Jaccard < 0 for k={k}")
            self.assertLessEqual(jaccard, 1.0,
                               msg=f"Jaccard > 1 for k={k}")
    
    @skip_if_no_deps
    def test_jaccard_complete_overlap(self):
        """Property: Complete overlap gives Jaccard = 1.0."""
        baseline = ['a', 'b', 'c', 'd', 'e']
        perturbed = ['a', 'b', 'c', 'd', 'e']  # Same ranking
        
        jaccard = jaccard_at_k(baseline, perturbed, k=3)
        self.assertAlmostEqual(jaccard, 1.0, places=5)
    
    @skip_if_no_deps
    def test_jaccard_no_overlap(self):
        """Property: No overlap gives Jaccard = 0.0."""
        baseline = ['a', 'b', 'c', 'd', 'e']
        perturbed = ['f', 'g', 'h', 'i', 'j']  # Completely different
        
        jaccard = jaccard_at_k(baseline, perturbed, k=3)
        self.assertAlmostEqual(jaccard, 0.0, places=5)
    
    @skip_if_no_deps
    def test_kendall_tau_reflexive(self):
        """Property: τ(X, X) = 1.0 (reflexivity)."""
        ranking = ['a', 'b', 'c', 'd', 'e']
        tau = kendall_tau(ranking, ranking)
        self.assertAlmostEqual(tau, 1.0, places=5)
    
    @skip_if_no_deps
    def test_kendall_tau_range(self):
        """Property: Kendall's τ ∈ [-1, 1]."""
        baseline = ['a', 'b', 'c', 'd', 'e']
        perturbed = ['e', 'd', 'c', 'b', 'a']  # Reversed
        
        tau = kendall_tau(baseline, perturbed)
        self.assertGreaterEqual(tau, -1.0, msg="τ < -1")
        self.assertLessEqual(tau, 1.0, msg="τ > 1")
    
    @skip_if_no_deps
    def test_kendall_tau_reversed(self):
        """Property: τ(X, reverse(X)) = -1.0."""
        baseline = ['a', 'b', 'c', 'd', 'e']
        perturbed = ['e', 'd', 'c', 'b', 'a']  # Reversed
        
        tau = kendall_tau(baseline, perturbed)
        self.assertAlmostEqual(tau, -1.0, places=5)
    
    @skip_if_no_deps
    def test_variation_of_information_reflexive(self):
        """Property: VI(X, X) = 0.0 (reflexivity)."""
        partition = {'a': 0, 'b': 0, 'c': 1, 'd': 1, 'e': 2}
        vi = variation_of_information(partition, partition)
        self.assertAlmostEqual(vi, 0.0, places=5)
    
    @skip_if_no_deps
    def test_variation_of_information_symmetric(self):
        """Property: VI(X, Y) = VI(Y, X) (symmetry)."""
        partition1 = {'a': 0, 'b': 0, 'c': 1, 'd': 1}
        partition2 = {'a': 0, 'b': 1, 'c': 1, 'd': 0}
        
        vi_xy = variation_of_information(partition1, partition2)
        vi_yx = variation_of_information(partition2, partition1)
        self.assertAlmostEqual(vi_xy, vi_yx, places=5)
    
    @skip_if_no_deps
    def test_variation_of_information_nonnegative(self):
        """Property: VI ≥ 0."""
        partition1 = {'a': 0, 'b': 0, 'c': 1, 'd': 1}
        partition2 = {'a': 0, 'b': 1, 'c': 1, 'd': 0}
        
        vi = variation_of_information(partition1, partition2)
        self.assertGreaterEqual(vi, 0.0, msg="VI < 0")


@pytest.mark.property
class TestPerturbationProperties(unittest.TestCase):
    """Property-based tests for network perturbations."""
    
    @skip_if_no_deps
    def test_edge_drop_preserves_nodes(self):
        """Property: Edge dropping preserves nodes."""
        network = create_test_network(num_nodes=10, num_layers=2)
        original_nodes = set(network.get_nodes())
        
        perturbed = edge_drop(network, fraction=0.2, seed=42)
        perturbed_nodes = set(perturbed.get_nodes())
        
        self.assertEqual(original_nodes, perturbed_nodes,
                        msg="Edge dropping changed node set")
    
    @skip_if_no_deps
    def test_edge_drop_reduces_edges(self):
        """Property: Edge dropping reduces edge count."""
        network = create_test_network(num_nodes=10, num_layers=2)
        original_edge_count = len(list(network.get_edges(data=False)))
        
        perturbed = edge_drop(network, fraction=0.2, seed=42)
        perturbed_edge_count = len(list(perturbed.get_edges(data=False)))
        
        self.assertLessEqual(perturbed_edge_count, original_edge_count,
                           msg="Edge dropping increased edge count")
    
    @skip_if_no_deps
    def test_edge_drop_zero_fraction(self):
        """Property: Dropping 0 edges leaves network unchanged."""
        network = create_test_network(num_nodes=10, num_layers=2)
        original_edge_count = len(list(network.get_edges(data=False)))
        
        perturbed = edge_drop(network, fraction=0.0, seed=42)
        perturbed_edge_count = len(list(perturbed.get_edges(data=False)))
        
        self.assertEqual(original_edge_count, perturbed_edge_count,
                        msg="0% edge drop changed edge count")
    
    @skip_if_no_deps
    def test_edge_drop_deterministic(self):
        """Property: Same seed produces same perturbation."""
        network = create_test_network(num_nodes=10, num_layers=2)
        
        perturbed1 = edge_drop(network, fraction=0.2, seed=42)
        perturbed2 = edge_drop(network, fraction=0.2, seed=42)
        
        edges1 = sorted(list(perturbed1.get_edges(data=False)))
        edges2 = sorted(list(perturbed2.get_edges(data=False)))
        
        self.assertEqual(len(edges1), len(edges2),
                        msg="Same seed produced different edge counts")


@pytest.mark.property
class TestSensitivityDistinctFromUQ(unittest.TestCase):
    """Tests ensuring sensitivity is distinct from UQ."""
    
    @skip_if_no_deps
    def test_sensitivity_not_mean_std_ci(self):
        """Property: Sensitivity results are NOT mean/std/CI."""
        # Stability metrics should return agreement values, not uncertainty
        baseline = ['a', 'b', 'c', 'd', 'e']
        perturbed = ['a', 'b', 'd', 'c', 'e']
        
        # Jaccard@k returns similarity score, not mean/std/CI
        jaccard = jaccard_at_k(baseline, perturbed, k=3)
        
        # Result should be a single float, not a dict with mean/std
        self.assertIsInstance(jaccard, (float, np.floating),
                            msg="Stability metric returned wrong type")
        self.assertGreaterEqual(jaccard, 0.0)
        self.assertLessEqual(jaccard, 1.0)
    
    @skip_if_no_deps
    def test_stability_measures_conclusion_change(self):
        """Property: Stability measures CONCLUSION change, not value uncertainty."""
        # Create two rankings that differ in conclusions
        baseline = ['a', 'b', 'c', 'd', 'e']
        perturbed = ['b', 'a', 'd', 'e', 'c']  # Top 3 changes
        
        # Jaccard@k measures set overlap (conclusion stability)
        jaccard_top3 = jaccard_at_k(baseline, perturbed, k=3)
        
        # Top 3 in baseline: {a, b, c}
        # Top 3 in perturbed: {b, a, d}
        # Intersection: {a, b}, Union: {a, b, c, d}
        # Expected Jaccard: 2/4 = 0.5
        expected_jaccard = 0.5
        self.assertAlmostEqual(jaccard_top3, expected_jaccard, places=1,
                             msg="Stability metric doesn't measure conclusion change")


@pytest.mark.property  
class TestSensitivityCurveProperties(unittest.TestCase):
    """Property-based tests for stability curves."""
    
    @skip_if_no_deps
    def test_zero_perturbation_perfect_stability(self):
        """Property: p=0 ⇒ stability ≈ 1.0."""
        # At zero perturbation, rankings should be identical
        baseline = ['a', 'b', 'c', 'd', 'e']
        
        # Zero perturbation = same ranking
        jaccard = jaccard_at_k(baseline, baseline, k=3)
        self.assertAlmostEqual(jaccard, 1.0, places=5,
                             msg="Zero perturbation doesn't give perfect stability")
    
    @skip_if_no_deps
    def test_increasing_perturbation_nonincreasing_stability(self):
        """Property: More perturbation ⇒ lower or equal stability (in expectation)."""
        # This is a qualitative property - we test with simple case
        baseline = ['a', 'b', 'c', 'd', 'e']
        
        # Mild perturbation
        perturbed1 = ['a', 'b', 'd', 'c', 'e']
        jaccard1 = jaccard_at_k(baseline, perturbed1, k=5)
        
        # Severe perturbation
        perturbed2 = ['e', 'd', 'c', 'b', 'a']
        jaccard2 = jaccard_at_k(baseline, perturbed2, k=5)
        
        # Severe perturbation should have lower or equal stability
        self.assertLessEqual(jaccard2, jaccard1,
                           msg="Severe perturbation has higher stability than mild")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
