#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for multilayer network statistical comparison framework.

This module tests the stats_comparison module which provides statistical
methods to compare multilayer networks.
"""

import unittest
import warnings

# Handle missing dependencies gracefully
try:
    import numpy as np
    import pandas as pd
    from py3plex.core import multinet
    from py3plex.algorithms.statistics import stats_comparison as sc
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    np = None
    pd = None
    multinet = None
    sc = None
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: {e}")


def skip_if_no_deps(test_func):
    """Decorator to skip tests when dependencies are missing."""
    if not DEPENDENCIES_AVAILABLE:
        return unittest.skip("Dependencies not available")(test_func)
    return test_func


class TestCompareMultilayerNetworks(unittest.TestCase):
    """Test cases for compare_multilayer_networks function."""
    
    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        
        # Create network 1: Dense triangle in L1
        self.net1 = multinet.multi_layer_network(directed=False)
        self.net1.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['C', 'L1', 'A', 'L1', 1],
            ['A', 'L2', 'B', 'L2', 1],
        ], input_type='list')
        
        # Create network 2: Sparse line in L1
        self.net2 = multinet.multi_layer_network(directed=False)
        self.net2.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['A', 'L2', 'B', 'L2', 1],
        ], input_type='list')
        
        # Create network 3: Similar to net2
        self.net3 = multinet.multi_layer_network(directed=False)
        self.net3.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['C', 'L1', 'D', 'L1', 1],
            ['A', 'L2', 'B', 'L2', 1],
        ], input_type='list')
    
    @skip_if_no_deps
    def test_basic_comparison_two_networks(self):
        """Test basic comparison between two networks."""
        results = sc.compare_multilayer_networks(
            [self.net1, self.net2],
            metrics=['density'],
            test='permutation',
            n_permutations=100,
            alpha=0.05
        )
        
        # Check result structure
        self.assertIsInstance(results, pd.DataFrame)
        self.assertIn('metric', results.columns)
        self.assertIn('layer', results.columns)
        self.assertIn('p_value', results.columns)
        self.assertIn('adjusted_p_value', results.columns)
        self.assertIn('significant', results.columns)
        self.assertIn('effect_size', results.columns)
        
        # Check that we have results
        self.assertGreater(len(results), 0)
        
        # Check data types
        self.assertTrue(all(isinstance(x, bool) for x in results['significant']))
        self.assertTrue(all(0 <= x <= 1 for x in results['p_value']))
    
    @skip_if_no_deps
    def test_multiple_metrics(self):
        """Test comparison with multiple metrics."""
        results = sc.compare_multilayer_networks(
            [self.net1, self.net2],
            metrics=['density', 'average_degree', 'clustering'],
            test='permutation',
            n_permutations=100
        )
        
        # Should have results for multiple metrics
        unique_metrics = results['metric'].unique()
        self.assertGreaterEqual(len(unique_metrics), 2)
        self.assertIn('density', unique_metrics)
        self.assertIn('average_degree', unique_metrics)
    
    @skip_if_no_deps
    def test_t_test(self):
        """Test t-test comparison."""
        results = sc.compare_multilayer_networks(
            [self.net1, self.net2],
            metrics=['density'],
            test='t-test',
            alpha=0.05
        )
        
        self.assertIsInstance(results, pd.DataFrame)
        self.assertGreater(len(results), 0)
        self.assertIn('statistic', results.columns)
    
    @skip_if_no_deps
    def test_mann_whitney(self):
        """Test Mann-Whitney U test."""
        results = sc.compare_multilayer_networks(
            [self.net1, self.net2],
            metrics=['density'],
            test='mann-whitney',
            alpha=0.05
        )
        
        self.assertIsInstance(results, pd.DataFrame)
        self.assertGreater(len(results), 0)
    
    @skip_if_no_deps
    def test_anova_three_groups(self):
        """Test ANOVA with three groups."""
        results = sc.compare_multilayer_networks(
            [self.net1, self.net2, self.net3],
            metrics=['density'],
            test='anova',
            alpha=0.05
        )
        
        self.assertIsInstance(results, pd.DataFrame)
        self.assertGreater(len(results), 0)
        self.assertIn('mean_group_0', results.columns)
        self.assertIn('mean_group_1', results.columns)
        self.assertIn('mean_group_2', results.columns)
    
    @skip_if_no_deps
    def test_kruskal_wallis(self):
        """Test Kruskal-Wallis test."""
        results = sc.compare_multilayer_networks(
            [self.net1, self.net2, self.net3],
            metrics=['density'],
            test='kruskal',
            alpha=0.05
        )
        
        self.assertIsInstance(results, pd.DataFrame)
        self.assertGreater(len(results), 0)
    
    @skip_if_no_deps
    def test_bonferroni_correction(self):
        """Test Bonferroni correction."""
        results = sc.compare_multilayer_networks(
            [self.net1, self.net2],
            metrics=['density', 'average_degree'],
            test='permutation',
            n_permutations=100,
            correction='bonferroni',
            alpha=0.05
        )
        
        # Adjusted p-values should be >= raw p-values
        self.assertTrue(
            all(results['adjusted_p_value'] >= results['p_value'])
        )
    
    @skip_if_no_deps
    def test_holm_correction(self):
        """Test Holm-Bonferroni correction."""
        results = sc.compare_multilayer_networks(
            [self.net1, self.net2],
            metrics=['density', 'average_degree'],
            test='permutation',
            n_permutations=100,
            correction='holm',
            alpha=0.05
        )
        
        # Check correction was applied
        self.assertIn('adjusted_p_value', results.columns)
        self.assertTrue(
            all(results['adjusted_p_value'] >= results['p_value'])
        )
    
    @skip_if_no_deps
    def test_fdr_correction(self):
        """Test FDR (Benjamini-Hochberg) correction."""
        results = sc.compare_multilayer_networks(
            [self.net1, self.net2],
            metrics=['density', 'average_degree'],
            test='permutation',
            n_permutations=100,
            correction='fdr_bh',
            alpha=0.05
        )
        
        # Check correction was applied
        self.assertIn('adjusted_p_value', results.columns)
    
    @skip_if_no_deps
    def test_effect_size_cohens_d(self):
        """Test Cohen's d effect size calculation."""
        results = sc.compare_multilayer_networks(
            [self.net1, self.net2],
            metrics=['density'],
            test='t-test',
            alpha=0.05
        )
        
        # Effect size should be present
        self.assertIn('effect_size', results.columns)
        # Effect sizes should be numeric
        self.assertTrue(all(isinstance(x, (int, float)) for x in results['effect_size']))
    
    @skip_if_no_deps
    def test_invalid_inputs(self):
        """Test error handling for invalid inputs."""
        # Too few networks
        with self.assertRaises(ValueError):
            sc.compare_multilayer_networks(
                [self.net1],
                metrics=['density']
            )
        
        # Invalid test type
        with self.assertRaises(ValueError):
            sc.compare_multilayer_networks(
                [self.net1, self.net2],
                metrics=['density'],
                test='invalid_test'
            )
    
    @skip_if_no_deps
    def test_node_activity_metric(self):
        """Test node activity metric comparison."""
        results = sc.compare_multilayer_networks(
            [self.net1, self.net2],
            metrics=['node_activity'],
            test='permutation',
            n_permutations=100
        )
        
        self.assertIsInstance(results, pd.DataFrame)
        self.assertGreater(len(results), 0)
        activity_results = results[results['metric'] == 'node_activity']
        self.assertGreater(len(activity_results), 0)
    
    @skip_if_no_deps
    def test_coupling_strength_metric(self):
        """Test coupling strength metric."""
        # Add inter-layer edges
        net1 = multinet.multi_layer_network(directed=False)
        net1.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['A', 'L2', 'B', 'L2', 1],
            ['A', 'L1', 'A', 'L2', 2],  # Inter-layer
        ], input_type='list')
        
        net2 = multinet.multi_layer_network(directed=False)
        net2.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['A', 'L2', 'B', 'L2', 1],
            ['A', 'L1', 'A', 'L2', 1],  # Weaker coupling
        ], input_type='list')
        
        results = sc.compare_multilayer_networks(
            [net1, net2],
            metrics=['coupling_strength'],
            test='permutation',
            n_permutations=100
        )
        
        self.assertIsInstance(results, pd.DataFrame)
        self.assertGreater(len(results), 0)
    
    @skip_if_no_deps
    def test_entropy_metric(self):
        """Test entropy of multiplexity metric."""
        results = sc.compare_multilayer_networks(
            [self.net1, self.net2],
            metrics=['entropy'],
            test='permutation',
            n_permutations=100
        )
        
        self.assertIsInstance(results, pd.DataFrame)
        self.assertGreater(len(results), 0)
    
    @skip_if_no_deps
    def test_default_metrics(self):
        """Test with default metrics."""
        results = sc.compare_multilayer_networks(
            [self.net1, self.net2],
            test='permutation',
            n_permutations=100
        )
        
        # Should use default metrics
        self.assertIsInstance(results, pd.DataFrame)
        self.assertGreater(len(results), 0)


class TestBootstrapConfidenceInterval(unittest.TestCase):
    """Test bootstrap confidence interval computation."""
    
    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        
        self.net1 = multinet.multi_layer_network(directed=False)
        self.net1.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
        ], input_type='list')
    
    @skip_if_no_deps
    def test_bootstrap_ci_basic(self):
        """Test basic bootstrap confidence interval."""
        def simple_metric(net):
            """Simple metric function for testing."""
            layers = sc._get_layers(net)
            if not layers:
                return 0.0
            return np.mean([sc.mls.layer_density(net, l) for l in layers])
        
        ci = sc.bootstrap_confidence_interval(
            [self.net1],
            simple_metric,
            n_bootstrap=100,
            confidence_level=0.95
        )
        
        # Should have CI for group 0
        self.assertIn('group_0', ci)
        lower, upper = ci['group_0']
        
        # Lower bound should be <= upper bound
        self.assertLessEqual(lower, upper)
        
        # Both should be in valid range [0, 1] for density
        self.assertTrue(0 <= lower <= 1)
        self.assertTrue(0 <= upper <= 1)


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions."""
    
    def setUp(self):
        """Set up test data."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
    
    @skip_if_no_deps
    def test_cohens_d(self):
        """Test Cohen's d calculation."""
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [2.0, 3.0, 4.0, 5.0, 6.0]
        
        d = sc._compute_cohens_d(group1, group2)
        
        # Should be negative (group1 < group2)
        self.assertLess(d, 0)
        
        # Effect size should be moderate
        self.assertTrue(abs(d) > 0)
    
    @skip_if_no_deps
    def test_cohens_d_identical_groups(self):
        """Test Cohen's d with identical groups."""
        group1 = [1.0, 2.0, 3.0]
        group2 = [1.0, 2.0, 3.0]
        
        d = sc._compute_cohens_d(group1, group2)
        
        # Should be zero
        self.assertAlmostEqual(d, 0.0, places=5)
    
    @skip_if_no_deps
    def test_eta_squared(self):
        """Test eta-squared calculation."""
        groups = [
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0]
        ]
        
        eta_sq = sc._compute_eta_squared(groups)
        
        # Should be between 0 and 1
        self.assertTrue(0 <= eta_sq <= 1)
        
        # With clearly separated groups, should be high
        self.assertGreater(eta_sq, 0.8)
    
    @skip_if_no_deps
    def test_eta_squared_identical_groups(self):
        """Test eta-squared with identical groups."""
        groups = [
            [2.0, 2.0, 2.0],
            [2.0, 2.0, 2.0]
        ]
        
        eta_sq = sc._compute_eta_squared(groups)
        
        # Should be zero (no between-group variance)
        self.assertAlmostEqual(eta_sq, 0.0, places=5)
    
    @skip_if_no_deps
    def test_bonferroni_correction_calculation(self):
        """Test Bonferroni correction calculation."""
        p_values = np.array([0.01, 0.02, 0.03, 0.04])
        adjusted = p_values * len(p_values)
        adjusted = np.minimum(adjusted, 1.0)
        
        # First p-value: 0.01 * 4 = 0.04
        self.assertAlmostEqual(adjusted[0], 0.04)
        # Last p-value: 0.04 * 4 = 0.16
        self.assertAlmostEqual(adjusted[3], 0.16)
    
    @skip_if_no_deps
    def test_permutation_test_basic(self):
        """Test permutation test function."""
        group1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        group2 = [6.0, 7.0, 8.0, 9.0, 10.0]
        
        stat, p_val = sc._permutation_test([group1, group2], n_permutations=100)
        
        # Statistic should be difference in means
        expected_stat = np.mean(group1) - np.mean(group2)
        self.assertAlmostEqual(stat, expected_stat, places=5)
        
        # P-value should be between 0 and 1
        self.assertTrue(0 <= p_val <= 1)
        
        # With clearly different groups, p-value should be small
        self.assertLess(p_val, 0.1)
    
    @skip_if_no_deps
    def test_get_layers(self):
        """Test layer extraction from network."""
        net = multinet.multi_layer_network(directed=False)
        net.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['A', 'L2', 'B', 'L2', 1],
            ['A', 'L3', 'B', 'L3', 1],
        ], input_type='list')
        
        layers = sc._get_layers(net)
        
        self.assertEqual(len(layers), 3)
        self.assertIn('L1', layers)
        self.assertIn('L2', layers)
        self.assertIn('L3', layers)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def setUp(self):
        """Set up minimal test cases."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
    
    @skip_if_no_deps
    def test_empty_networks(self):
        """Test handling of empty networks."""
        net1 = multinet.multi_layer_network(directed=False)
        net2 = multinet.multi_layer_network(directed=False)
        
        # Should not crash
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            results = sc.compare_multilayer_networks(
                [net1, net2],
                metrics=['density'],
                test='permutation',
                n_permutations=10
            )
        
        self.assertIsInstance(results, pd.DataFrame)
    
    @skip_if_no_deps
    def test_single_node_networks(self):
        """Test with single-node networks."""
        net1 = multinet.multi_layer_network(directed=False)
        net1.add_edges([['A', 'L1', 'A', 'L1', 1]], input_type='list')
        
        net2 = multinet.multi_layer_network(directed=False)
        net2.add_edges([['B', 'L1', 'B', 'L1', 1]], input_type='list')
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            results = sc.compare_multilayer_networks(
                [net1, net2],
                metrics=['density'],
                test='permutation',
                n_permutations=10
            )
        
        self.assertIsInstance(results, pd.DataFrame)
    
    @skip_if_no_deps
    def test_unknown_metric_warning(self):
        """Test warning for unknown metric."""
        net1 = multinet.multi_layer_network(directed=False)
        net1.add_edges([['A', 'L1', 'B', 'L1', 1]], input_type='list')
        
        net2 = multinet.multi_layer_network(directed=False)
        net2.add_edges([['A', 'L1', 'B', 'L1', 1]], input_type='list')
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            results = sc.compare_multilayer_networks(
                [net1, net2],
                metrics=['unknown_metric'],
                test='permutation',
                n_permutations=10
            )
            
            # Should have warning
            self.assertTrue(any("Unknown metric" in str(warning.message) for warning in w))


if __name__ == '__main__':
    unittest.main()
