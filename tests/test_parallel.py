"""
Tests for py3plex._parallel module.

This module tests internal parallel execution utilities including:
- Deterministic seed spawning
- Parallel map execution
- Serial/parallel execution equivalence
"""

import pytest
import numpy as np
from py3plex._parallel import spawn_seeds, parallel_map, _compute_random_value


class TestSpawnSeeds:
    """Test deterministic seed spawning."""
    
    def test_spawn_seeds_basic(self):
        """Test basic seed spawning functionality."""
        seeds = spawn_seeds(42, 5)
        assert len(seeds) == 5
        assert all(isinstance(s, (int, np.integer)) for s in seeds)
    
    def test_spawn_seeds_deterministic(self):
        """Test that same base seed produces same children."""
        seeds1 = spawn_seeds(42, 10)
        seeds2 = spawn_seeds(42, 10)
        assert seeds1 == seeds2
    
    def test_spawn_seeds_unique(self):
        """Test that spawned seeds are unique."""
        seeds = spawn_seeds(42, 10)
        assert len(set(seeds)) == len(seeds)
    
    def test_spawn_seeds_different_base(self):
        """Test that different base seeds produce different children."""
        seeds1 = spawn_seeds(42, 5)
        seeds2 = spawn_seeds(123, 5)
        assert seeds1 != seeds2
    
    def test_spawn_seeds_none(self):
        """Test spawning with None base seed."""
        seeds = spawn_seeds(None, 5)
        assert len(seeds) == 5
        assert all(s is None for s in seeds)
    
    def test_spawn_seeds_single(self):
        """Test spawning single seed."""
        seeds = spawn_seeds(42, 1)
        assert len(seeds) == 1
        assert isinstance(seeds[0], (int, np.integer))
    
    def test_spawn_seeds_large_count(self):
        """Test spawning many seeds."""
        seeds = spawn_seeds(42, 1000)
        assert len(seeds) == 1000
        assert len(set(seeds)) == 1000  # All unique


class TestParallelMap:
    """Test parallel map functionality."""
    
    def test_parallel_map_serial(self):
        """Test serial execution (n_jobs=1)."""
        def square(x):
            return x * x
        
        results = parallel_map(square, [1, 2, 3, 4], n_jobs=1)
        assert results == [1, 4, 9, 16]
    
    def test_parallel_map_parallel(self):
        """Test parallel execution (n_jobs=2)."""
        def square(x):
            return x * x
        
        results = parallel_map(square, [1, 2, 3, 4], n_jobs=2)
        assert results == [1, 4, 9, 16]
    
    def test_parallel_map_empty(self):
        """Test with empty input."""
        def identity(x):
            return x
        
        results = parallel_map(identity, [], n_jobs=1)
        assert results == []
    
    def test_parallel_map_single_item(self):
        """Test with single item."""
        def double(x):
            return x * 2
        
        results = parallel_map(double, [5], n_jobs=1)
        assert results == [10]
    
    def test_parallel_map_determinism_with_seeds(self):
        """Test that parallel execution is deterministic with seeds."""
        base_seed = 42
        n_tasks = 10
        
        # Run twice with same seeds
        seeds = spawn_seeds(base_seed, n_tasks)
        results1 = parallel_map(_compute_random_value, seeds, n_jobs=1)
        
        seeds = spawn_seeds(base_seed, n_tasks)
        results2 = parallel_map(_compute_random_value, seeds, n_jobs=1)
        
        # Should be identical
        assert len(results1) == len(results2)
        for r1, r2 in zip(results1, results2):
            assert abs(r1 - r2) < 1e-10
    
    def test_parallel_map_serial_vs_parallel(self):
        """Test that serial and parallel give same results with seeds."""
        base_seed = 42
        n_tasks = 10
        
        # Serial
        seeds = spawn_seeds(base_seed, n_tasks)
        results_serial = parallel_map(_compute_random_value, seeds, n_jobs=1)
        
        # Parallel
        seeds = spawn_seeds(base_seed, n_tasks)
        results_parallel = parallel_map(_compute_random_value, seeds, n_jobs=2)
        
        # Should be identical
        assert len(results_serial) == len(results_parallel)
        for r_s, r_p in zip(results_serial, results_parallel):
            assert abs(r_s - r_p) < 1e-10
    
    def test_parallel_map_chunksize(self):
        """Test with explicit chunksize."""
        def identity(x):
            return x
        
        results = parallel_map(identity, range(20), n_jobs=2, chunksize=5)
        assert results == list(range(20))
    
    def test_parallel_map_n_jobs_negative_one(self):
        """Test n_jobs=-1 (use all cores)."""
        def identity(x):
            return x
        
        results = parallel_map(identity, [1, 2, 3], n_jobs=-1)
        assert results == [1, 2, 3]
    
    def test_parallel_map_invalid_backend(self):
        """Test invalid backend raises error."""
        def identity(x):
            return x
        
        with pytest.raises(ValueError, match="Unknown backend"):
            parallel_map(identity, [1, 2], n_jobs=1, backend="invalid")


class TestComputeRandomValue:
    """Test helper function for random value computation."""
    
    def test_compute_random_value_with_seed(self):
        """Test deterministic random value generation."""
        value1 = _compute_random_value(42)
        value2 = _compute_random_value(42)
        assert abs(value1 - value2) < 1e-10
    
    def test_compute_random_value_none_seed(self):
        """Test random value with None seed (non-deterministic)."""
        value = _compute_random_value(None)
        assert 0.0 <= value <= 1.0
    
    def test_compute_random_value_different_seeds(self):
        """Test different seeds produce different values."""
        value1 = _compute_random_value(42)
        value2 = _compute_random_value(123)
        assert abs(value1 - value2) > 1e-6
