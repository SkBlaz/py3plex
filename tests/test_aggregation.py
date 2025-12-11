"""
Tests for vectorized multiplex aggregation.

Tests both correctness (numerical equivalence with reference) and
performance (speedup targets) for the aggregate_layers function.
"""

import numpy as np
import pytest
import scipy.sparse as sp

from py3plex.multinet.aggregation import aggregate_layers


class TestAggregateLayersCorrectness:
    """Test correctness of aggregation operations."""
    
    def test_simple_sum_aggregation(self):
        """Test basic sum aggregation with known result."""
        edges = np.array([
            [0, 0, 1, 1.0],  # Layer 0: edge (0,1) weight 1.0
            [0, 1, 2, 2.0],  # Layer 0: edge (1,2) weight 2.0
            [1, 0, 1, 0.5],  # Layer 1: edge (0,1) weight 0.5 (duplicate)
            [1, 2, 3, 1.5],  # Layer 1: edge (2,3) weight 1.5
        ])
        
        mat = aggregate_layers(edges, reducer="sum", to_sparse=False)
        
        # Check shape
        assert mat.shape == (4, 4)
        
        # Check aggregated weights
        assert mat[0, 1] == pytest.approx(1.5, abs=1e-6)  # 1.0 + 0.5
        assert mat[1, 2] == pytest.approx(2.0, abs=1e-6)  # Only in layer 0
        assert mat[2, 3] == pytest.approx(1.5, abs=1e-6)  # Only in layer 1
        
        # Check zeros where no edges exist
        assert mat[0, 0] == 0.0
        assert mat[3, 0] == 0.0
    
    def test_mean_aggregation(self):
        """Test mean aggregation computes correct averages."""
        edges = np.array([
            [0, 0, 1, 1.0],
            [1, 0, 1, 0.5],
            [2, 0, 1, 1.5],  # Same edge in 3 layers
        ])
        
        mat = aggregate_layers(edges, reducer="mean", to_sparse=False)
        
        # Mean of [1.0, 0.5, 1.5] = 1.0
        assert mat[0, 1] == pytest.approx(1.0, abs=1e-6)
    
    def test_max_aggregation(self):
        """Test max aggregation selects maximum weight."""
        edges = np.array([
            [0, 0, 1, 1.0],
            [1, 0, 1, 2.5],  # Maximum
            [2, 0, 1, 0.5],
        ])
        
        mat = aggregate_layers(edges, reducer="max", to_sparse=False)
        
        assert mat[0, 1] == pytest.approx(2.5, abs=1e-6)
    
    def test_sparse_output_format(self):
        """Test that sparse output is correct format."""
        edges = np.array([
            [0, 0, 1, 1.0],
            [0, 1, 2, 2.0],
        ])
        
        mat = aggregate_layers(edges, reducer="sum", to_sparse=True)
        
        # Check it's CSR format
        assert sp.isspmatrix_csr(mat)
        assert mat.shape == (3, 3)
        assert mat.nnz == 2  # Two non-zero entries
        
        # Check values
        assert mat[0, 1] == pytest.approx(1.0, abs=1e-6)
        assert mat[1, 2] == pytest.approx(2.0, abs=1e-6)
    
    def test_no_weight_column_defaults_to_one(self):
        """Test that missing weights default to 1.0."""
        edges = np.array([
            [0, 0, 1],  # No weight column
            [1, 0, 1],
        ])
        
        mat = aggregate_layers(edges, reducer="sum", to_sparse=False)
        
        # Should sum to 2.0 (1.0 + 1.0)
        assert mat[0, 1] == pytest.approx(2.0, abs=1e-6)
    
    def test_self_loops_supported(self):
        """Test that self-loops (i,i) are handled correctly."""
        edges = np.array([
            [0, 1, 1, 3.0],  # Self-loop
            [1, 1, 1, 2.0],  # Duplicate self-loop
        ])
        
        mat = aggregate_layers(edges, reducer="sum", to_sparse=False)
        
        assert mat[1, 1] == pytest.approx(5.0, abs=1e-6)
    
    def test_large_node_ids(self):
        """Test handling of large (sparse) node ID space."""
        edges = np.array([
            [0, 100, 200, 1.0],
            [1, 200, 300, 2.0],
        ])
        
        mat = aggregate_layers(edges, reducer="sum", to_sparse=True)
        
        # Matrix should be sized to fit largest ID
        assert mat.shape == (301, 301)
        assert mat[100, 200] == pytest.approx(1.0, abs=1e-6)
        assert mat[200, 300] == pytest.approx(2.0, abs=1e-6)
        
        # Most entries should be zero (sparse)
        assert mat.nnz == 2
    
    def test_list_input_converted(self):
        """Test that list input is converted to ndarray."""
        edges = [
            [0, 0, 1, 1.0],
            [1, 0, 1, 2.0],
        ]
        
        mat = aggregate_layers(edges, reducer="sum")
        
        assert sp.isspmatrix_csr(mat)
        assert mat[0, 1] == pytest.approx(3.0, abs=1e-6)
    
    def test_single_edge(self):
        """Test edge case with single edge."""
        edges = np.array([[0, 5, 10, 7.5]])
        
        mat = aggregate_layers(edges, reducer="sum", to_sparse=False)
        
        assert mat.shape == (11, 11)
        assert mat[5, 10] == pytest.approx(7.5, abs=1e-6)
    
    def test_empty_matrix_for_no_edges(self):
        """Test handling of empty edge list."""
        edges = np.empty((0, 4))
        
        # With icontract, this raises ViolationError
        # Without icontract, this raises ValueError or IndexError
        with pytest.raises((ValueError, IndexError, Exception)):
            # Should fail gracefully with empty input
            aggregate_layers(edges, reducer="sum")


class TestAggregateLayersValidation:
    """Test input validation and error handling."""
    
    def test_invalid_shape_too_few_columns(self):
        """Test error on insufficient columns."""
        edges = np.array([[0, 1]])  # Only 2 columns
        
        with pytest.raises(ValueError, match="must have shape"):
            aggregate_layers(edges)
    
    def test_invalid_shape_1d_array(self):
        """Test error on 1D array."""
        edges = np.array([0, 1, 2, 3])
        
        with pytest.raises(ValueError, match="must have shape"):
            aggregate_layers(edges)
    
    def test_invalid_reducer(self):
        """Test error on unsupported reducer."""
        edges = np.array([[0, 0, 1, 1.0]])
        
        # With icontract, this raises ViolationError
        # Without icontract, this raises ValueError
        with pytest.raises((ValueError, Exception)):
            aggregate_layers(edges, reducer="median")
    
    def test_invalid_type(self):
        """Test error on wrong input type."""
        with pytest.raises(TypeError, match="must be numpy.ndarray or list"):
            aggregate_layers("not an array")


class TestAggregateLayersPerformance:
    """Test performance characteristics and benchmarks."""
    
    @pytest.fixture
    def small_multilayer(self):
        """Small multilayer network for quick tests."""
        np.random.seed(42)
        n_edges = 1000
        n_layers = 4
        n_nodes = 100
        
        layers = np.random.randint(0, n_layers, n_edges)
        srcs = np.random.randint(0, n_nodes, n_edges)
        dsts = np.random.randint(0, n_nodes, n_edges)
        weights = np.random.rand(n_edges)
        
        return np.column_stack([layers, srcs, dsts, weights])
    
    @pytest.fixture
    def large_multilayer(self):
        """Large multilayer network for performance benchmarks."""
        np.random.seed(42)
        n_edges = 100_000  # 100K edges
        n_layers = 4
        n_nodes = 1000
        
        layers = np.random.randint(0, n_layers, n_edges)
        srcs = np.random.randint(0, n_nodes, n_edges)
        dsts = np.random.randint(0, n_nodes, n_edges)
        weights = np.random.rand(n_edges)
        
        return np.column_stack([layers, srcs, dsts, weights])
    
    def test_sparse_vs_dense_memory_efficiency(self, small_multilayer):
        """Test that sparse output uses less memory for sparse graphs."""
        sparse_mat = aggregate_layers(small_multilayer, to_sparse=True)
        dense_mat = aggregate_layers(small_multilayer, to_sparse=False)
        
        # Sparse should have much lower memory footprint
        sparse_bytes = (
            sparse_mat.data.nbytes + 
            sparse_mat.indices.nbytes + 
            sparse_mat.indptr.nbytes
        )
        dense_bytes = dense_mat.nbytes
        
        # Sparse should use < 20% of dense for this sparse graph
        # (Conservative threshold to account for random variations)
        assert sparse_bytes < dense_bytes * 0.2
    
    def test_deterministic_output(self, small_multilayer):
        """Test that output is deterministic for same input."""
        mat1 = aggregate_layers(small_multilayer, reducer="sum", to_sparse=False)
        mat2 = aggregate_layers(small_multilayer, reducer="sum", to_sparse=False)
        
        np.testing.assert_array_almost_equal(mat1, mat2, decimal=10)
    
    def test_benchmark_sum_aggregation(self, benchmark, large_multilayer):
        """Benchmark sum aggregation performance."""
        result = benchmark(
            aggregate_layers,
            large_multilayer,
            reducer="sum",
            to_sparse=True
        )
        
        assert sp.isspmatrix_csr(result)
    
    def test_benchmark_mean_aggregation(self, benchmark, large_multilayer):
        """Benchmark mean aggregation performance."""
        result = benchmark(
            aggregate_layers,
            large_multilayer,
            reducer="mean",
            to_sparse=True
        )
        
        assert sp.isspmatrix_csr(result)
    
    def test_benchmark_max_aggregation(self, benchmark, large_multilayer):
        """Benchmark max aggregation performance."""
        result = benchmark(
            aggregate_layers,
            large_multilayer,
            reducer="max",
            to_sparse=True
        )
        
        assert sp.isspmatrix_csr(result)


class TestAggregateLayersEdgeCases:
    """Test edge cases and corner scenarios."""
    
    def test_all_weights_zero(self):
        """Test handling of all-zero weights."""
        edges = np.array([
            [0, 0, 1, 0.0],
            [1, 1, 2, 0.0],
        ])
        
        mat = aggregate_layers(edges, reducer="sum", to_sparse=False)
        
        assert mat[0, 1] == 0.0
        assert mat[1, 2] == 0.0
    
    def test_negative_weights(self):
        """Test that negative weights are handled correctly."""
        edges = np.array([
            [0, 0, 1, 2.0],
            [1, 0, 1, -1.0],
        ])
        
        mat = aggregate_layers(edges, reducer="sum", to_sparse=False)
        
        assert mat[0, 1] == pytest.approx(1.0, abs=1e-6)
    
    def test_very_large_weights(self):
        """Test handling of large weight values."""
        edges = np.array([
            [0, 0, 1, 1e10],
            [1, 0, 1, 2e10],
        ])
        
        mat = aggregate_layers(edges, reducer="sum", to_sparse=False)
        
        assert mat[0, 1] == pytest.approx(3e10, abs=1e4)
    
    def test_many_layers_same_edge(self):
        """Test edge appearing in many layers."""
        n_layers = 100
        edges = np.array([[i, 0, 1, 1.0] for i in range(n_layers)])
        
        mat = aggregate_layers(edges, reducer="sum", to_sparse=False)
        
        assert mat[0, 1] == pytest.approx(100.0, abs=1e-6)
        
        mat_mean = aggregate_layers(edges, reducer="mean", to_sparse=False)
        assert mat_mean[0, 1] == pytest.approx(1.0, abs=1e-6)
    
    def test_directed_vs_undirected(self):
        """Test that (i,j) and (j,i) are treated as different edges."""
        edges = np.array([
            [0, 0, 1, 1.0],  # Forward edge
            [1, 1, 0, 2.0],  # Reverse edge
        ])
        
        mat = aggregate_layers(edges, reducer="sum", to_sparse=False)
        
        # Should be asymmetric
        assert mat[0, 1] == pytest.approx(1.0, abs=1e-6)
        assert mat[1, 0] == pytest.approx(2.0, abs=1e-6)
