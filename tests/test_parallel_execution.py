"""Tests for parallel execution in null models and uncertainty quantification.

This module tests that:
1. Parallel execution produces deterministic results
2. Parallel results match serial results
3. Platform safety (works with spawn on Windows)
4. Edge cases are handled correctly
"""

import pytest
import numpy as np
from py3plex.core import multinet
from py3plex._parallel import parallel_map, spawn_seeds
from py3plex.nullmodels import generate_null_model
from py3plex.uncertainty import bootstrap_metric, null_model_metric


# ============================================================================
# Module-level helper functions (for pickling in multiprocessing)
# ============================================================================


def _square(x):
    """Helper function for testing parallel_map."""
    return x * x


def _compute_random(seed):
    """Helper function for testing deterministic parallel execution."""
    if seed is None:
        return 0.0
    rng = np.random.default_rng(seed)
    return rng.random()


def _identity(x):
    """Identity function for testing."""
    return x


def _degree_metric(network):
    """Compute degree centrality for testing."""
    result = {}
    if not hasattr(network, 'core_network') or network.core_network is None:
        return result
    for node in network.get_nodes():
        result[node] = network.core_network.degree(node)
    return result


# ============================================================================
# Test fixtures
# ============================================================================


@pytest.fixture
def simple_network():
    """Create a simple multilayer network for testing."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ["n1", "L1", "n2", "L1", 1.0],
        ["n2", "L1", "n3", "L1", 1.0],
        ["n3", "L1", "n1", "L1", 1.0],
        ["n1", "L2", "n3", "L2", 1.0],
        ["n2", "L2", "n3", "L2", 1.0],
    ]
    net.add_edges(edges, input_type="list")
    return net


@pytest.fixture
def empty_network():
    """Create an empty network for edge case testing."""
    return multinet.multi_layer_network(directed=False, verbose=False)


# ============================================================================
# Core Parallel Infrastructure Tests
# ============================================================================


class TestSeedSpawning:
    """Tests for spawn_seeds function."""
    
    def test_spawn_seeds_deterministic(self):
        """Test that spawn_seeds produces same results with same base seed."""
        seeds1 = spawn_seeds(42, 10)
        seeds2 = spawn_seeds(42, 10)
        assert seeds1 == seeds2
    
    def test_spawn_seeds_different_base(self):
        """Test that different base seeds produce different children."""
        seeds1 = spawn_seeds(42, 10)
        seeds2 = spawn_seeds(123, 10)
        assert seeds1 != seeds2
    
    def test_spawn_seeds_none(self):
        """Test that None base seed produces list of Nones."""
        seeds = spawn_seeds(None, 5)
        assert seeds == [None] * 5
    
    def test_spawn_seeds_unique(self):
        """Test that spawned seeds are unique."""
        seeds = spawn_seeds(42, 10)
        assert len(seeds) == len(set(seeds))


class TestParallelMap:
    """Tests for parallel_map function."""
    
    def test_parallel_map_serial(self):
        """Test parallel_map with n_jobs=1 (serial)."""
        results = parallel_map(_square, [1, 2, 3, 4, 5], n_jobs=1)
        assert results == [1, 4, 9, 16, 25]
    
    def test_parallel_map_parallel(self):
        """Test parallel_map with n_jobs=2 (parallel)."""
        results = parallel_map(_square, [1, 2, 3, 4, 5], n_jobs=2)
        assert results == [1, 4, 9, 16, 25]
    
    def test_parallel_map_deterministic(self):
        """Test that parallel execution is deterministic with seeds."""
        seeds = spawn_seeds(42, 10)
        
        # Serial execution
        results_serial = parallel_map(_compute_random, seeds, n_jobs=1)
        
        # Parallel execution
        results_parallel = parallel_map(_compute_random, seeds, n_jobs=2)
        
        # Results should be identical
        assert len(results_serial) == len(results_parallel)
        for r_s, r_p in zip(results_serial, results_parallel):
            assert abs(r_s - r_p) < 1e-10
    
    def test_parallel_map_empty_list(self):
        """Test parallel_map with empty input."""
        results = parallel_map(_identity, [], n_jobs=2)
        assert results == []


# ============================================================================
# Null Model Parallel Tests
# ============================================================================


class TestNullModelParallel:
    """Tests for parallel execution in null model generation."""
    
    def test_generate_null_model_serial(self, simple_network):
        """Test null model generation with n_jobs=1."""
        result = generate_null_model(
            simple_network,
            model="configuration",
            num_samples=5,
            seed=42,
            n_jobs=1
        )
        
        assert result is not None
        assert len(result.samples) == 5
        assert result.seed == 42
    
    def test_generate_null_model_parallel(self, simple_network):
        """Test null model generation with n_jobs=2."""
        result = generate_null_model(
            simple_network,
            model="configuration",
            num_samples=5,
            seed=42,
            n_jobs=2
        )
        
        assert result is not None
        assert len(result.samples) == 5
        assert result.seed == 42
    
    def test_generate_null_model_deterministic(self, simple_network):
        """Test that null model generation is deterministic."""
        # Serial execution
        result_serial = generate_null_model(
            simple_network,
            model="configuration",
            num_samples=10,
            seed=123,
            n_jobs=1
        )
        
        # Parallel execution
        result_parallel = generate_null_model(
            simple_network,
            model="configuration",
            num_samples=10,
            seed=123,
            n_jobs=2
        )
        
        # Check that both produce same number of samples
        assert len(result_serial.samples) == len(result_parallel.samples)
        
        # Check that networks have same structure (node and edge counts)
        for i, (net_s, net_p) in enumerate(zip(result_serial.samples, result_parallel.samples)):
            nodes_s = list(net_s.get_nodes())
            nodes_p = list(net_p.get_nodes())
            edges_s = list(net_s.get_edges())
            edges_p = list(net_p.get_edges())
            
            assert len(nodes_s) == len(nodes_p), f"Sample {i}: node count mismatch"
            assert len(edges_s) == len(edges_p), f"Sample {i}: edge count mismatch"
    
    def test_generate_null_model_empty_network(self, empty_network):
        """Test null model generation with empty network."""
        result = generate_null_model(
            empty_network,
            model="configuration",
            num_samples=3,
            seed=42,
            n_jobs=2
        )
        
        assert result is not None
        assert len(result.samples) == 3


# ============================================================================
# Bootstrap Parallel Tests
# ============================================================================


class TestBootstrapParallel:
    """Tests for parallel execution in bootstrap."""
    
    def test_bootstrap_metric_serial(self, simple_network):
        """Test bootstrap with n_jobs=1."""
        boot_result = bootstrap_metric(
            simple_network,
            _degree_metric,
            n_boot=10,
            unit="edges",
            random_state=42,
            n_jobs=1
        )
        
        assert boot_result is not None
        assert "mean" in boot_result
        assert "std" in boot_result
        assert boot_result["n_boot"] == 10
    
    def test_bootstrap_metric_parallel(self, simple_network):
        """Test bootstrap with n_jobs=2."""
        boot_result = bootstrap_metric(
            simple_network,
            _degree_metric,
            n_boot=10,
            unit="edges",
            random_state=42,
            n_jobs=2
        )
        
        assert boot_result is not None
        assert "mean" in boot_result
        assert "std" in boot_result
        assert boot_result["n_boot"] == 10
    
    def test_bootstrap_metric_deterministic(self, simple_network):
        """Test that bootstrap is deterministic."""
        # Serial execution
        boot_serial = bootstrap_metric(
            simple_network,
            _degree_metric,
            n_boot=20,
            unit="edges",
            random_state=123,
            n_jobs=1
        )
        
        # Parallel execution
        boot_parallel = bootstrap_metric(
            simple_network,
            _degree_metric,
            n_boot=20,
            unit="edges",
            random_state=123,
            n_jobs=2
        )
        
        # Results should be identical (or very close due to floating point)
        assert len(boot_serial["index"]) == len(boot_parallel["index"])
        assert boot_serial["index"] == boot_parallel["index"]
        
        # Check that mean values are identical
        np.testing.assert_allclose(
            boot_serial["mean"],
            boot_parallel["mean"],
            rtol=1e-10,
            atol=1e-10
        )
    
    def test_bootstrap_metric_empty_network(self, empty_network):
        """Test bootstrap with empty network."""
        boot_result = bootstrap_metric(
            empty_network,
            _degree_metric,
            n_boot=5,
            unit="edges",
            random_state=42,
            n_jobs=2
        )
        
        assert boot_result is not None
        assert len(boot_result["mean"]) == 0


# ============================================================================
# Null Model Metric Parallel Tests
# ============================================================================


class TestNullModelMetricParallel:
    """Tests for parallel execution in null model metric computation."""
    
    def test_null_model_metric_serial(self, simple_network):
        """Test null model metric with n_jobs=1."""
        null_result = null_model_metric(
            simple_network,
            _degree_metric,
            n_null=10,
            model="degree_preserving",
            random_state=42,
            n_jobs=1
        )
        
        assert null_result is not None
        assert "observed" in null_result
        assert "zscore" in null_result
        assert "pvalue" in null_result
        assert null_result["n_null"] == 10
    
    def test_null_model_metric_parallel(self, simple_network):
        """Test null model metric with n_jobs=2."""
        null_result = null_model_metric(
            simple_network,
            _degree_metric,
            n_null=10,
            model="degree_preserving",
            random_state=42,
            n_jobs=2
        )
        
        assert null_result is not None
        assert "observed" in null_result
        assert "zscore" in null_result
        assert "pvalue" in null_result
        assert null_result["n_null"] == 10
    
    def test_null_model_metric_deterministic(self, simple_network):
        """Test that null model metric is deterministic."""
        # Serial execution
        null_serial = null_model_metric(
            simple_network,
            _degree_metric,
            n_null=20,
            model="degree_preserving",
            random_state=123,
            n_jobs=1
        )
        
        # Parallel execution
        null_parallel = null_model_metric(
            simple_network,
            _degree_metric,
            n_null=20,
            model="degree_preserving",
            random_state=123,
            n_jobs=2
        )
        
        # Results should be identical
        assert len(null_serial["index"]) == len(null_parallel["index"])
        assert null_serial["index"] == null_parallel["index"]
        
        # Check that observed values are identical
        np.testing.assert_allclose(
            null_serial["observed"],
            null_parallel["observed"],
            rtol=1e-10,
            atol=1e-10
        )
        
        # Check that null statistics are identical (or very close)
        np.testing.assert_allclose(
            null_serial["mean_null"],
            null_parallel["mean_null"],
            rtol=1e-10,
            atol=1e-10
        )
    
    def test_null_model_metric_empty_network(self, empty_network):
        """Test null model metric with empty network."""
        null_result = null_model_metric(
            empty_network,
            _degree_metric,
            n_null=5,
            model="degree_preserving",
            random_state=42,
            n_jobs=2
        )
        
        assert null_result is not None
        assert len(null_result["observed"]) == 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestParallelIntegration:
    """Integration tests for parallel execution across the library."""
    
    def test_different_null_models_parallel(self, simple_network):
        """Test that different null models work in parallel."""
        models = ["configuration", "erdos_renyi", "edge_swap"]
        
        for model in models:
            result = generate_null_model(
                simple_network,
                model=model,
                num_samples=5,
                seed=42,
                n_jobs=2
            )
            assert result is not None
            assert len(result.samples) == 5
    
    def test_bootstrap_units_parallel(self, simple_network):
        """Test that different bootstrap units work in parallel."""
        units = ["edges", "nodes", "layers"]
        
        for unit in units:
            boot_result = bootstrap_metric(
                simple_network,
                _degree_metric,
                n_boot=5,
                unit=unit,
                random_state=42,
                n_jobs=2
            )
            assert boot_result is not None
    
    def test_large_number_of_jobs(self, simple_network):
        """Test with large number of jobs (should be capped automatically)."""
        result = generate_null_model(
            simple_network,
            model="configuration",
            num_samples=3,
            seed=42,
            n_jobs=100  # Will be capped to reasonable number
        )
        assert result is not None
        assert len(result.samples) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
