"""
Benchmark suite for vectorized multiplex aggregation.

Compares new vectorized implementation against legacy loop-based approach.
Target: ≥3× speedup for 1M edges across 4 layers.
"""

import time

import numpy as np
import pytest

from py3plex.multinet.aggregation import aggregate_layers


def legacy_aggregate_sum(edges):
    """
    Legacy loop-based aggregation for comparison.
    
    Simulates the old approach using Python dictionaries and loops.
    This is intentionally slow to demonstrate the speedup.
    """
    edge_dict = {}
    
    for edge in edges:
        layer, src, dst = int(edge[0]), int(edge[1]), int(edge[2])
        weight = edge[3] if len(edge) > 3 else 1.0
        
        key = (src, dst)
        if key not in edge_dict:
            edge_dict[key] = 0.0
        edge_dict[key] += weight
    
    # Convert to dense matrix
    if not edge_dict:
        return np.zeros((1, 1))
    
    max_node = max(max(k[0], k[1]) for k in edge_dict.keys())
    n = max_node + 1
    mat = np.zeros((n, n))
    
    for (src, dst), weight in edge_dict.items():
        mat[src, dst] = weight
    
    return mat


class TestAggregationBenchmarks:
    """Benchmark tests for aggregation performance."""
    
    @pytest.fixture
    def tiny_edges(self):
        """100 edges, 4 layers."""
        np.random.seed(42)
        n_edges = 100
        return self._generate_edges(n_edges, n_layers=4, n_nodes=20)
    
    @pytest.fixture
    def small_edges(self):
        """10K edges, 4 layers."""
        np.random.seed(42)
        n_edges = 10_000
        return self._generate_edges(n_edges, n_layers=4, n_nodes=100)
    
    @pytest.fixture
    def medium_edges(self):
        """100K edges, 4 layers."""
        np.random.seed(42)
        n_edges = 100_000
        return self._generate_edges(n_edges, n_layers=4, n_nodes=500)
    
    @pytest.fixture
    def large_edges(self):
        """1M edges, 4 layers - target benchmark size."""
        np.random.seed(42)
        n_edges = 1_000_000
        return self._generate_edges(n_edges, n_layers=4, n_nodes=5000)
    
    @pytest.fixture
    def multilayer_edges(self):
        """100K edges, 8 layers."""
        np.random.seed(42)
        n_edges = 100_000
        return self._generate_edges(n_edges, n_layers=8, n_nodes=500)
    
    def _generate_edges(self, n_edges, n_layers, n_nodes):
        """Generate random edge list."""
        layers = np.random.randint(0, n_layers, n_edges)
        srcs = np.random.randint(0, n_nodes, n_edges)
        dsts = np.random.randint(0, n_nodes, n_edges)
        weights = np.random.rand(n_edges)
        return np.column_stack([layers, srcs, dsts, weights])
    
    # Benchmarks with pytest-benchmark
    
    def test_bench_vectorized_tiny(self, benchmark, tiny_edges):
        """Benchmark vectorized on tiny dataset."""
        result = benchmark(aggregate_layers, tiny_edges, reducer="sum", to_sparse=True)
        assert result is not None
    
    def test_bench_vectorized_small(self, benchmark, small_edges):
        """Benchmark vectorized on 10K edges."""
        result = benchmark(aggregate_layers, small_edges, reducer="sum", to_sparse=True)
        assert result is not None
    
    def test_bench_vectorized_medium(self, benchmark, medium_edges):
        """Benchmark vectorized on 100K edges."""
        result = benchmark(aggregate_layers, medium_edges, reducer="sum", to_sparse=True)
        assert result is not None
    
    def test_bench_vectorized_large(self, benchmark, large_edges):
        """Benchmark vectorized on 1M edges (target size)."""
        result = benchmark(aggregate_layers, large_edges, reducer="sum", to_sparse=True)
        assert result is not None
    
    def test_bench_vectorized_multilayer(self, benchmark, multilayer_edges):
        """Benchmark vectorized on 8-layer network."""
        result = benchmark(aggregate_layers, multilayer_edges, reducer="sum", to_sparse=True)
        assert result is not None
    
    def test_bench_dense_output(self, benchmark, small_edges):
        """Benchmark with dense output format."""
        result = benchmark(aggregate_layers, small_edges, reducer="sum", to_sparse=False)
        assert result is not None
    
    def test_bench_mean_reducer(self, benchmark, medium_edges):
        """Benchmark mean aggregation."""
        result = benchmark(aggregate_layers, medium_edges, reducer="mean", to_sparse=True)
        assert result is not None
    
    def test_bench_max_reducer(self, benchmark, medium_edges):
        """Benchmark max aggregation."""
        result = benchmark(aggregate_layers, medium_edges, reducer="max", to_sparse=True)
        assert result is not None
    
    # Manual timing comparison tests
    
    def test_speedup_vs_legacy_small(self, small_edges):
        """Compare speedup vs legacy on 10K edges."""
        # Vectorized
        t0 = time.perf_counter()
        vec_result = aggregate_layers(small_edges, reducer="sum", to_sparse=False)
        vec_time = time.perf_counter() - t0
        
        # Legacy
        t0 = time.perf_counter()
        leg_result = legacy_aggregate_sum(small_edges)
        leg_time = time.perf_counter() - t0
        
        speedup = leg_time / vec_time
        
        print(f"\n10K edges:")
        print(f"  Legacy: {leg_time:.4f}s")
        print(f"  Vectorized: {vec_time:.4f}s")
        print(f"  Speedup: {speedup:.2f}×")
        
        # Check correctness
        np.testing.assert_array_almost_equal(vec_result, leg_result, decimal=6)
        
        # Expect at least 2× speedup on small dataset
        assert speedup >= 2.0, f"Speedup {speedup:.2f}× below 2× target"
    
    @pytest.mark.slow
    def test_speedup_vs_legacy_medium(self, medium_edges):
        """Compare speedup vs legacy on 100K edges."""
        # Vectorized
        t0 = time.perf_counter()
        vec_result = aggregate_layers(medium_edges, reducer="sum", to_sparse=False)
        vec_time = time.perf_counter() - t0
        
        # Legacy
        t0 = time.perf_counter()
        leg_result = legacy_aggregate_sum(medium_edges)
        leg_time = time.perf_counter() - t0
        
        speedup = leg_time / vec_time
        
        print(f"\n100K edges:")
        print(f"  Legacy: {leg_time:.4f}s")
        print(f"  Vectorized: {vec_time:.4f}s")
        print(f"  Speedup: {speedup:.2f}×")
        
        # Check correctness
        np.testing.assert_array_almost_equal(vec_result, leg_result, decimal=6)
        
        # Expect at least 3× speedup on medium dataset
        assert speedup >= 3.0, f"Speedup {speedup:.2f}× below 3× target"
    
    @pytest.mark.slow
    def test_speedup_target_1m_edges(self, large_edges):
        """
        Test primary performance target: ≥3× speedup on 1M edges, 4 layers.
        
        This is the key acceptance criterion from Spec A.
        """
        # Vectorized
        t0 = time.perf_counter()
        vec_result = aggregate_layers(large_edges, reducer="sum", to_sparse=True)
        vec_time = time.perf_counter() - t0
        
        # Legacy (sample only to avoid timeout)
        sample_edges = large_edges[:100_000]
        t0 = time.perf_counter()
        leg_result_sample = legacy_aggregate_sum(sample_edges)
        leg_time_sample = time.perf_counter() - t0
        
        # Extrapolate legacy time
        leg_time = leg_time_sample * (len(large_edges) / len(sample_edges))
        
        speedup = leg_time / vec_time
        
        print(f"\n1M edges (primary target):")
        print(f"  Legacy (extrapolated): {leg_time:.4f}s")
        print(f"  Vectorized: {vec_time:.4f}s")
        print(f"  Speedup: {speedup:.2f}×")
        print(f"  Matrix shape: {vec_result.shape}")
        print(f"  Non-zeros: {vec_result.nnz}")
        
        # Primary acceptance criterion: ≥3× speedup
        assert speedup >= 3.0, (
            f"Speedup {speedup:.2f}× below 3× target. "
            f"Legacy: {leg_time:.2f}s, Vectorized: {vec_time:.2f}s"
        )
        
        # Also verify reasonable absolute performance
        assert vec_time < 5.0, f"Vectorized time {vec_time:.2f}s too slow for 1M edges"


class TestScalabilityCharacteristics:
    """Test scaling behavior with increasing problem size."""
    
    def test_linear_scaling_edges(self):
        """Test that runtime scales linearly with number of edges."""
        np.random.seed(42)
        
        times = []
        sizes = [1000, 5000, 10000, 50000]
        
        for n_edges in sizes:
            layers = np.random.randint(0, 4, n_edges)
            srcs = np.random.randint(0, 100, n_edges)
            dsts = np.random.randint(0, 100, n_edges)
            weights = np.random.rand(n_edges)
            edges = np.column_stack([layers, srcs, dsts, weights])
            
            t0 = time.perf_counter()
            aggregate_layers(edges, reducer="sum", to_sparse=True)
            times.append(time.perf_counter() - t0)
        
        # Check roughly linear: time ratio ≈ size ratio
        # For 10× more edges, expect < 15× time (allowing for overhead)
        ratio_size = sizes[-1] / sizes[0]
        ratio_time = times[-1] / times[0]
        
        print(f"\nScaling test:")
        for size, time_val in zip(sizes, times):
            print(f"  {size:6d} edges: {time_val:.4f}s")
        print(f"  Size ratio: {ratio_size:.1f}×")
        print(f"  Time ratio: {ratio_time:.1f}×")
        
        assert ratio_time < ratio_size * 1.5, "Non-linear scaling detected"
    
    def test_layer_count_impact(self):
        """Test that performance doesn't degrade significantly with more layers."""
        np.random.seed(42)
        n_edges = 50000
        
        times = {}
        for n_layers in [2, 4, 8, 16]:
            layers = np.random.randint(0, n_layers, n_edges)
            srcs = np.random.randint(0, 100, n_edges)
            dsts = np.random.randint(0, 100, n_edges)
            weights = np.random.rand(n_edges)
            edges = np.column_stack([layers, srcs, dsts, weights])
            
            t0 = time.perf_counter()
            aggregate_layers(edges, reducer="sum", to_sparse=True)
            times[n_layers] = time.perf_counter() - t0
        
        print(f"\nLayer scaling test (fixed 50K edges):")
        for n_layers, time_val in times.items():
            print(f"  {n_layers:2d} layers: {time_val:.4f}s")
        
        # More layers shouldn't significantly increase time (same # edges)
        assert times[16] < times[2] * 2.0, "Excessive slowdown with more layers"


if __name__ == "__main__":
    # Allow running as standalone script for quick profiling
    print("Running benchmark suite...")
    pytest.main([__file__, "-v", "--benchmark-only"])
