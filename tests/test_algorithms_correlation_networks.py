"""Tests for py3plex.algorithms.statistics.correlation_networks module.

Tests the correlation network construction functions.
"""

import numpy as np
import pytest
from py3plex.algorithms.statistics.correlation_networks import (
    pick_threshold,
    default_correlation_to_network,
)


class TestPickThreshold:
    """Test pick_threshold function."""
    
    def test_pick_threshold_basic(self):
        """Test pick_threshold on simple matrix."""
        # Create a simple 5x10 matrix with some correlation structure
        np.random.seed(42)
        matrix = np.random.randn(10, 5)
        
        threshold = pick_threshold(matrix)
        
        # Threshold should be between 0 and 1
        assert 0 <= threshold <= 1
        assert isinstance(threshold, float)
    
    def test_pick_threshold_high_correlation(self):
        """Test pick_threshold with highly correlated data."""
        # Create data with strong correlation
        np.random.seed(123)
        base = np.random.randn(20, 1)
        matrix = np.hstack([base, base + np.random.randn(20, 1) * 0.1])
        matrix = np.hstack([matrix] * 3)  # Replicate to get more columns
        
        threshold = pick_threshold(matrix)
        
        assert 0 <= threshold <= 1
        assert isinstance(threshold, float)
    
    def test_pick_threshold_uncorrelated(self):
        """Test pick_threshold with uncorrelated data."""
        np.random.seed(456)
        matrix = np.random.randn(15, 6)
        
        threshold = pick_threshold(matrix)
        
        assert 0 <= threshold <= 1
        assert isinstance(threshold, float)
    
    def test_pick_threshold_deterministic(self):
        """Test that pick_threshold is deterministic."""
        np.random.seed(789)
        matrix = np.random.randn(10, 5)
        
        threshold1 = pick_threshold(matrix)
        threshold2 = pick_threshold(matrix.copy())
        
        # Should return the same threshold for the same input
        assert threshold1 == threshold2
    
    def test_pick_threshold_small_matrix(self):
        """Test pick_threshold with minimum sized matrix."""
        np.random.seed(111)
        matrix = np.random.randn(5, 3)
        
        threshold = pick_threshold(matrix)
        
        assert 0 <= threshold <= 1
        assert isinstance(threshold, float)
    
    def test_pick_threshold_single_column(self):
        """Test pick_threshold with single column (edge case)."""
        np.random.seed(222)
        matrix = np.random.randn(10, 1)
        
        # Should handle gracefully or return reasonable value
        threshold = pick_threshold(matrix)
        
        assert 0 <= threshold <= 1
        assert isinstance(threshold, float)


class TestDefaultCorrelationToNetwork:
    """Test default_correlation_to_network function."""
    
    def test_default_correlation_basic(self):
        """Test basic correlation to network conversion."""
        np.random.seed(42)
        matrix = np.random.randn(10, 5)
        
        result = default_correlation_to_network(matrix)
        
        # Result should be binary matrix
        assert result.shape == matrix.shape
        assert np.all((result == 0) | (result == 1))
    
    def test_default_correlation_standard_preprocess(self):
        """Test with standard preprocessing."""
        np.random.seed(123)
        matrix = np.random.randn(15, 6)
        
        result = default_correlation_to_network(
            matrix, preprocess="standard"
        )
        
        assert result.shape == matrix.shape
        assert np.all((result == 0) | (result == 1))
    
    def test_default_correlation_no_preprocess(self):
        """Test without preprocessing."""
        np.random.seed(456)
        matrix = np.random.randn(12, 4)
        
        # Use a different preprocess value
        result = default_correlation_to_network(
            matrix, preprocess="none"
        )
        
        # Should still work but skip standardization
        assert result.shape == matrix.shape
    
    def test_default_correlation_constant_column(self):
        """Test with constant column (std=0 case)."""
        np.random.seed(789)
        matrix = np.random.randn(10, 5)
        matrix[:, 2] = 5.0  # Constant column
        
        # Should handle without division by zero
        result = default_correlation_to_network(matrix)
        
        assert result.shape == matrix.shape
        assert np.all((result == 0) | (result == 1))
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))
    
    def test_default_correlation_all_constant(self):
        """Test with all columns constant."""
        matrix = np.ones((10, 5)) * 3.14
        
        # Should handle all constant columns
        result = default_correlation_to_network(matrix)
        
        assert result.shape == matrix.shape
        assert not np.any(np.isnan(result))
        assert not np.any(np.isinf(result))
    
    def test_default_correlation_deterministic(self):
        """Test that conversion is deterministic."""
        np.random.seed(111)
        matrix = np.random.randn(10, 5)
        
        result1 = default_correlation_to_network(matrix.copy())
        result2 = default_correlation_to_network(matrix.copy())
        
        np.testing.assert_array_equal(result1, result2)
    
    def test_default_correlation_preserves_shape(self):
        """Test that output shape matches input shape."""
        np.random.seed(222)
        shapes = [(5, 3), (10, 5), (15, 8), (20, 10)]
        
        for shape in shapes:
            matrix = np.random.randn(*shape)
            result = default_correlation_to_network(matrix)
            assert result.shape == shape
    
    def test_default_correlation_binary_output(self):
        """Test that output is strictly binary (0 or 1)."""
        np.random.seed(333)
        matrix = np.random.randn(10, 5)
        
        result = default_correlation_to_network(matrix)
        
        unique_values = np.unique(result)
        # Should only contain 0 and/or 1
        assert all(v in [0, 1, 0.0, 1.0] for v in unique_values)


class TestCorrelationNetworksIntegration:
    """Integration tests for correlation network workflow."""
    
    def test_full_workflow_small_data(self):
        """Test complete workflow on small dataset."""
        np.random.seed(42)
        # Create small dataset with some structure
        n_samples = 20
        n_features = 6
        
        # Create data with some correlation structure
        base = np.random.randn(n_samples, 1)
        matrix = np.hstack([
            base,
            base + np.random.randn(n_samples, 1) * 0.5,
            np.random.randn(n_samples, 4)
        ])
        
        # Step 1: Pick threshold
        threshold = pick_threshold(matrix)
        assert 0 <= threshold <= 1
        
        # Step 2: Convert to network
        network = default_correlation_to_network(matrix)
        
        assert network.shape == matrix.shape
        assert np.all((network == 0) | (network == 1))
    
    def test_workflow_with_different_sizes(self):
        """Test workflow with various data sizes."""
        np.random.seed(123)
        
        sizes = [(10, 5), (20, 8), (15, 6)]
        
        for n_samples, n_features in sizes:
            matrix = np.random.randn(n_samples, n_features)
            
            threshold = pick_threshold(matrix)
            network = default_correlation_to_network(matrix)
            
            assert 0 <= threshold <= 1
            assert network.shape == (n_samples, n_features)
            assert np.all((network == 0) | (network == 1))
    
    def test_network_sparsity_range(self):
        """Test that resulting networks have reasonable sparsity."""
        np.random.seed(456)
        matrix = np.random.randn(30, 10)
        
        network = default_correlation_to_network(matrix)
        
        # Calculate sparsity (proportion of zeros)
        sparsity = np.mean(network == 0)
        
        # Should have some zeros and some ones (not all 0 or all 1)
        assert 0 < sparsity < 1


class TestCorrelationNetworksEdgeCases:
    """Test edge cases and error handling."""
    
    def test_very_small_matrix(self):
        """Test with very small matrix."""
        np.random.seed(42)
        matrix = np.random.randn(3, 2)
        
        threshold = pick_threshold(matrix)
        network = default_correlation_to_network(matrix)
        
        assert 0 <= threshold <= 1
        assert network.shape == matrix.shape
    
    def test_negative_values(self):
        """Test with matrix containing negative values."""
        np.random.seed(123)
        matrix = np.random.randn(10, 5) - 5  # All negative
        
        network = default_correlation_to_network(matrix)
        
        assert network.shape == matrix.shape
        assert np.all((network == 0) | (network == 1))
    
    def test_large_values(self):
        """Test with matrix containing large values."""
        np.random.seed(456)
        matrix = np.random.randn(10, 5) * 1000
        
        network = default_correlation_to_network(matrix)
        
        assert network.shape == matrix.shape
        assert np.all((network == 0) | (network == 1))
    
    def test_zero_matrix(self):
        """Test with all-zero matrix."""
        matrix = np.zeros((10, 5))
        
        # Should handle without errors
        network = default_correlation_to_network(matrix)
        
        assert network.shape == matrix.shape
        assert not np.any(np.isnan(network))
    
    def test_sparse_correlation(self):
        """Test with data that has very sparse correlations."""
        np.random.seed(789)
        # Independent random variables
        matrix = np.random.randn(50, 10)
        
        network = default_correlation_to_network(matrix)
        
        assert network.shape == matrix.shape
        assert np.all((network == 0) | (network == 1))
    
    def test_perfect_correlation(self):
        """Test with perfectly correlated columns."""
        np.random.seed(111)
        base = np.random.randn(20, 1)
        matrix = np.hstack([base] * 5)  # All columns identical
        
        network = default_correlation_to_network(matrix)
        
        assert network.shape == matrix.shape
        assert np.all((network == 0) | (network == 1))


class TestCorrelationNetworksNumericalStability:
    """Test numerical stability of correlation network functions."""
    
    def test_no_nan_in_output(self):
        """Test that output never contains NaN values."""
        np.random.seed(42)
        test_matrices = [
            np.random.randn(10, 5),
            np.ones((10, 5)) * 3.14,  # Constant
            np.random.randn(10, 5) * 1000,  # Large values
        ]
        
        for matrix in test_matrices:
            network = default_correlation_to_network(matrix)
            assert not np.any(np.isnan(network)), "Output contains NaN"
    
    def test_no_inf_in_output(self):
        """Test that output never contains infinity."""
        np.random.seed(123)
        test_matrices = [
            np.random.randn(10, 5),
            np.ones((10, 5)) * 0.0001,  # Small values
        ]
        
        for matrix in test_matrices:
            network = default_correlation_to_network(matrix)
            assert not np.any(np.isinf(network)), "Output contains Inf"
    
    def test_consistent_dtype(self):
        """Test that output has consistent dtype."""
        np.random.seed(456)
        matrix = np.random.randn(10, 5)
        
        network = default_correlation_to_network(matrix)
        
        # Should be numeric type
        assert np.issubdtype(network.dtype, np.number)
