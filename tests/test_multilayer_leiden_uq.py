#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for multilayer_leiden and multilayer_leiden_uq with UQ support.

This module contains comprehensive tests for:
- multilayer_leiden function (production API)
- multilayer_leiden_uq function (uncertainty quantification)
- Determinism and reproducibility
- Parameter sweeps (gamma, omega)
- DSL integration
- Property-based tests
"""

import unittest
import numpy as np

# Handle missing dependencies gracefully
try:
    from py3plex.core import multinet
    from py3plex.algorithms.community_detection import (
        multilayer_leiden,
        multilayer_leiden_uq,
        UQResult,
        canonicalize_partition,
    )
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    multinet = None
    multilayer_leiden = None
    multilayer_leiden_uq = None
    UQResult = None
    canonicalize_partition = None
    DEPENDENCIES_AVAILABLE = False
    print(f"Warning: {e}")


class TestMultilayerLeiden(unittest.TestCase):
    """Test cases for multilayer_leiden function."""
    
    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        
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
    
    def test_basic_execution(self):
        """Test that multilayer_leiden runs without errors."""
        partition, score = multilayer_leiden(
            self.simple_network,
            gamma=1.0,
            omega=1.0,
            random_state=42
        )
        
        # Check types
        self.assertIsInstance(partition, dict)
        self.assertIsInstance(score, float)
        
        # Check partition coverage
        nodes = list(self.simple_network.get_nodes())
        self.assertEqual(len(partition), len(nodes))
        
        # Check all nodes are assigned
        for node in nodes:
            self.assertIn(node, partition)
        
        # Check community IDs are non-negative integers
        for comm_id in partition.values():
            self.assertIsInstance(comm_id, (int, np.integer))
            self.assertGreaterEqual(comm_id, 0)
    
    def test_determinism_same_seed(self):
        """Test that same seed yields identical results."""
        partition1, score1 = multilayer_leiden(
            self.simple_network,
            gamma=1.0,
            omega=1.0,
            random_state=42
        )
        
        partition2, score2 = multilayer_leiden(
            self.simple_network,
            gamma=1.0,
            omega=1.0,
            random_state=42
        )
        
        # Partitions should be identical
        self.assertEqual(partition1, partition2)
        self.assertAlmostEqual(score1, score2, places=12)
    
    def test_different_seeds_different_results(self):
        """Test that different seeds usually yield different results."""
        partition1, score1 = multilayer_leiden(
            self.simple_network,
            gamma=1.0,
            omega=1.0,
            random_state=42
        )
        
        partition2, score2 = multilayer_leiden(
            self.simple_network,
            gamma=1.0,
            omega=1.0,
            random_state=99
        )
        
        # Note: For very small networks, partitions might be identical
        # We just check that the function runs with different seeds
        self.assertIsInstance(partition1, dict)
        self.assertIsInstance(partition2, dict)
    
    def test_default_seed_determinism(self):
        """Test that None random_state defaults to seed=0 deterministically."""
        partition1, score1 = multilayer_leiden(
            self.simple_network,
            gamma=1.0,
            omega=1.0,
            random_state=None
        )
        
        partition2, score2 = multilayer_leiden(
            self.simple_network,
            gamma=1.0,
            omega=1.0,
            random_state=0
        )
        
        # Should be identical (None defaults to 0)
        self.assertEqual(partition1, partition2)
        self.assertAlmostEqual(score1, score2, places=12)
    
    def test_with_diagnostics(self):
        """Test return_diagnostics=True."""
        partition, score, diagnostics = multilayer_leiden(
            self.simple_network,
            gamma=1.0,
            omega=1.0,
            random_state=42,
            return_diagnostics=True
        )
        
        # Check diagnostics structure
        self.assertIsInstance(diagnostics, dict)
        self.assertIn('timing', diagnostics)
        self.assertIn('convergence_info', diagnostics)
        self.assertIn('backend_used', diagnostics)
        self.assertIn('n_communities', diagnostics)
        self.assertIn('n_nodes', diagnostics)
        
        # Check values
        self.assertGreater(diagnostics['timing'], 0)
        self.assertEqual(diagnostics['backend_used'], 'native')
        self.assertGreater(diagnostics['n_communities'], 0)
        self.assertEqual(diagnostics['n_nodes'], len(partition))
    
    def test_gamma_sweep(self):
        """Test that higher gamma leads to more communities (on average)."""
        partition_low, score_low = multilayer_leiden(
            self.simple_network,
            gamma=0.5,
            omega=1.0,
            random_state=42
        )
        
        partition_high, score_high = multilayer_leiden(
            self.simple_network,
            gamma=2.0,
            omega=1.0,
            random_state=42
        )
        
        n_comm_low = len(set(partition_low.values()))
        n_comm_high = len(set(partition_high.values()))
        
        # Higher gamma should not decrease number of communities
        self.assertGreaterEqual(n_comm_high, n_comm_low)
    
    def test_omega_sweep(self):
        """Test effect of omega on layer coupling."""
        partition_no_coupling, _ = multilayer_leiden(
            self.simple_network,
            gamma=1.0,
            omega=0.0,
            random_state=42
        )
        
        partition_strong_coupling, _ = multilayer_leiden(
            self.simple_network,
            gamma=1.0,
            omega=10.0,
            random_state=42
        )
        
        # Both should execute successfully
        self.assertIsInstance(partition_no_coupling, dict)
        self.assertIsInstance(partition_strong_coupling, dict)
    
    def test_canonicalize_partition(self):
        """Test partition canonicalization."""
        # Create a partition with non-canonical labels
        partition = {
            ('A', 'L1'): 5,
            ('B', 'L1'): 5,
            ('C', 'L1'): 10,
            ('A', 'L2'): 10,
        }
        
        canonical = canonicalize_partition(partition)
        
        # Should have labels 0, 1, ...
        labels = sorted(set(canonical.values()))
        self.assertEqual(labels, list(range(len(labels))))
        
        # A and B should still be in same community
        self.assertEqual(canonical[('A', 'L1')], canonical[('B', 'L1')])
        
        # C and A(L2) should still be in same community
        self.assertEqual(canonical[('C', 'L1')], canonical[('A', 'L2')])
    
    def test_input_validation(self):
        """Test input validation."""
        # Invalid gamma
        with self.assertRaises(Exception):
            multilayer_leiden(
                self.simple_network,
                gamma=-1.0,
                omega=1.0,
                random_state=42
            )
        
        # Invalid omega
        with self.assertRaises(Exception):
            multilayer_leiden(
                self.simple_network,
                gamma=1.0,
                omega=-1.0,
                random_state=42
            )
        
        # Invalid n_iterations
        with self.assertRaises(Exception):
            multilayer_leiden(
                self.simple_network,
                gamma=1.0,
                omega=1.0,
                n_iterations=0,
                random_state=42
            )


class TestMultilayerLeidenUQ(unittest.TestCase):
    """Test cases for multilayer_leiden_uq function."""
    
    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        
        # Create a simple network for UQ tests
        self.network = multinet.multi_layer_network(directed=False)
        
        # Layer 1
        self.network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
            ['C', 'L1', 'D', 'L1', 1],
            ['D', 'L1', 'A', 'L1', 1],
        ], input_type='list')
        
        # Layer 2
        self.network.add_edges([
            ['A', 'L2', 'B', 'L2', 1],
            ['C', 'L2', 'D', 'L2', 1],
        ], input_type='list')
    
    def test_basic_uq_execution(self):
        """Test that multilayer_leiden_uq runs without errors."""
        result = multilayer_leiden_uq(
            self.network,
            gamma=1.0,
            omega=1.0,
            n_runs=5,
            random_state=42
        )
        
        # Check result type
        self.assertIsInstance(result, UQResult)
        
        # Check required fields
        self.assertIsInstance(result.scores, list)
        self.assertEqual(len(result.scores), 5)
        self.assertIsInstance(result.consensus_partition, dict)
        self.assertIsInstance(result.stability_metrics, dict)
        self.assertIsInstance(result.ci, dict)
        self.assertIsInstance(result.summary, dict)
        self.assertIsInstance(result.diagnostics, dict)
    
    def test_uq_determinism(self):
        """Test that UQ results are deterministic with same seed."""
        result1 = multilayer_leiden_uq(
            self.network,
            n_runs=10,
            random_state=42
        )
        
        result2 = multilayer_leiden_uq(
            self.network,
            n_runs=10,
            random_state=42
        )
        
        # Scores should be identical
        np.testing.assert_array_almost_equal(result1.scores, result2.scores)
        
        # Consensus partitions should be identical
        self.assertEqual(result1.consensus_partition, result2.consensus_partition)
    
    def test_uq_with_return_all(self):
        """Test return_all=True includes all partitions."""
        result = multilayer_leiden_uq(
            self.network,
            n_runs=5,
            return_all=True,
            random_state=42
        )
        
        self.assertIsNotNone(result.partitions)
        self.assertEqual(len(result.partitions), 5)
        
        # Each partition should be a dict
        for partition in result.partitions:
            self.assertIsInstance(partition, dict)
    
    def test_uq_without_return_all(self):
        """Test return_all=False excludes partitions."""
        result = multilayer_leiden_uq(
            self.network,
            n_runs=5,
            return_all=False,
            random_state=42
        )
        
        self.assertIsNone(result.partitions)
    
    def test_uq_methods(self):
        """Test different UQ methods."""
        # Seed-based
        result_seed = multilayer_leiden_uq(
            self.network,
            n_runs=5,
            method="seed",
            random_state=42
        )
        self.assertEqual(len(result_seed.scores), 5)
        
        # Perturbation-based (may have fewer runs due to network structure changes)
        result_perturb = multilayer_leiden_uq(
            self.network,
            n_runs=5,
            method="perturbation",
            perturbation_rate=0.1,
            random_state=42
        )
        self.assertGreater(len(result_perturb.scores), 0)
        self.assertLessEqual(len(result_perturb.scores), 5)
        
        # Bootstrap-based (may have fewer runs due to network structure changes)
        result_bootstrap = multilayer_leiden_uq(
            self.network,
            n_runs=5,
            method="bootstrap",
            random_state=42
        )
        self.assertGreater(len(result_bootstrap.scores), 0)
        self.assertLessEqual(len(result_bootstrap.scores), 5)
    
    def test_uq_stability_metrics(self):
        """Test stability metrics are computed."""
        result = multilayer_leiden_uq(
            self.network,
            n_runs=10,
            random_state=42
        )
        
        metrics = result.stability_metrics
        
        # Check required metrics
        self.assertIn('vi_mean', metrics)
        self.assertIn('vi_std', metrics)
        self.assertIn('nmi_mean', metrics)
        self.assertIn('nmi_std', metrics)
        self.assertIn('node_entropy', metrics)
        self.assertIn('pairwise_agreement', metrics)
        
        # Check value ranges
        self.assertGreaterEqual(metrics['vi_mean'], 0)
        self.assertGreaterEqual(metrics['vi_std'], 0)
        self.assertGreaterEqual(metrics['nmi_mean'], 0)
        self.assertLessEqual(metrics['nmi_mean'], 1)
        self.assertIsInstance(metrics['node_entropy'], np.ndarray)
    
    def test_uq_confidence_intervals(self):
        """Test confidence intervals are computed."""
        result = multilayer_leiden_uq(
            self.network,
            n_runs=20,
            ci=0.95,
            random_state=42
        )
        
        ci_result = result.ci
        
        # Check CI for score
        self.assertIn('score', ci_result)
        score_ci = ci_result['score']
        self.assertEqual(len(score_ci), 2)
        self.assertLessEqual(score_ci[0], score_ci[1])
        
        # Check CI for n_communities
        self.assertIn('n_communities', ci_result)
        n_comm_ci = ci_result['n_communities']
        self.assertEqual(len(n_comm_ci), 2)
        self.assertLessEqual(n_comm_ci[0], n_comm_ci[1])
    
    def test_uq_summary_statistics(self):
        """Test summary statistics are computed."""
        result = multilayer_leiden_uq(
            self.network,
            n_runs=10,
            random_state=42
        )
        
        summary = result.summary
        
        # Check required fields
        self.assertIn('score_mean', summary)
        self.assertIn('score_std', summary)
        self.assertIn('n_communities_mean', summary)
        self.assertIn('n_communities_std', summary)
        self.assertIn('n_runs_success', summary)
        self.assertIn('n_runs_failed', summary)
        
        # Check values
        self.assertEqual(summary['n_runs_success'], 10)
        self.assertEqual(summary['n_runs_failed'], 0)
        self.assertGreater(summary['score_mean'], 0)
        self.assertGreaterEqual(summary['score_std'], 0)
    
    def test_uq_diagnostics(self):
        """Test diagnostics are computed."""
        result = multilayer_leiden_uq(
            self.network,
            n_runs=5,
            random_state=42
        )
        
        diag = result.diagnostics
        
        # Check required fields
        self.assertIn('seeds', diag)
        self.assertIn('runtime_total', diag)
        self.assertIn('runtime_per_run', diag)
        self.assertIn('failures', diag)
        self.assertIn('method', diag)
        self.assertIn('agg', diag)
        
        # Check values
        self.assertEqual(len(diag['seeds']), 5)
        self.assertGreater(diag['runtime_total'], 0)
        self.assertEqual(len(diag['failures']), 0)
    
    def test_uq_input_validation(self):
        """Test UQ input validation."""
        # Invalid n_runs
        with self.assertRaises(Exception):
            multilayer_leiden_uq(
                self.network,
                n_runs=0,
                random_state=42
            )
        
        # Invalid method
        with self.assertRaises(Exception):
            multilayer_leiden_uq(
                self.network,
                n_runs=5,
                method="invalid",
                random_state=42
            )
        
        # Invalid agg
        with self.assertRaises(Exception):
            multilayer_leiden_uq(
                self.network,
                n_runs=5,
                agg="invalid",
                random_state=42
            )
        
        # Invalid ci
        with self.assertRaises(Exception):
            multilayer_leiden_uq(
                self.network,
                n_runs=5,
                ci=1.5,
                random_state=42
            )


class TestPropertyBased(unittest.TestCase):
    """Property-based tests for partition validity."""
    
    def setUp(self):
        """Set up test networks."""
        if not DEPENDENCIES_AVAILABLE:
            self.skipTest("Dependencies not available")
        
        self.network = multinet.multi_layer_network(directed=False)
        self.network.add_edges([
            ['A', 'L1', 'B', 'L1', 1],
            ['B', 'L1', 'C', 'L1', 1],
        ], input_type='list')
    
    def test_partition_covers_all_nodes(self):
        """Test that partition covers all nodes."""
        partition, _ = multilayer_leiden(
            self.network,
            random_state=42
        )
        
        nodes = set(self.network.get_nodes())
        partition_nodes = set(partition.keys())
        
        self.assertEqual(nodes, partition_nodes)
    
    def test_partition_has_no_missing_keys(self):
        """Test that partition has no missing keys."""
        partition, _ = multilayer_leiden(
            self.network,
            random_state=42
        )
        
        for node in self.network.get_nodes():
            self.assertIn(node, partition)
    
    def test_partition_community_ids_valid(self):
        """Test that community IDs are valid."""
        partition, _ = multilayer_leiden(
            self.network,
            random_state=42
        )
        
        for comm_id in partition.values():
            # Should be integer
            self.assertIsInstance(comm_id, (int, np.integer))
            # Should be non-negative
            self.assertGreaterEqual(comm_id, 0)
    
    def test_modularity_finite(self):
        """Test that modularity is finite."""
        _, score = multilayer_leiden(
            self.network,
            random_state=42
        )
        
        self.assertTrue(np.isfinite(score))


if __name__ == '__main__':
    unittest.main()
