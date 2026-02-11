"""
Tests for py3plex.algorithms.statistics.correlation_networks module.

This module tests correlation network construction methods.
"""

import pytest
import numpy as np
from unittest.mock import patch
from py3plex.algorithms.statistics.correlation_networks import (
    pick_threshold,
    default_correlation_to_network,
)


class TestPickThreshold:
    """Test pick_threshold function."""

    def test_returns_float(self):
        """Test that pick_threshold returns a float value."""
        matrix = np.random.rand(10, 5)
        result = pick_threshold(matrix)
        assert isinstance(result, float)

    def test_result_in_valid_range(self):
        """Test that threshold is in range [0, 1]."""
        matrix = np.random.rand(10, 5)
        result = pick_threshold(matrix)
        assert 0 <= result <= 1

    def test_with_small_matrix(self):
        """Test with small matrix."""
        matrix = np.random.rand(5, 3)
        result = pick_threshold(matrix)
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_with_larger_matrix(self):
        """Test with larger matrix."""
        matrix = np.random.rand(20, 10)
        result = pick_threshold(matrix)
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_deterministic_with_seed(self):
        """Test that results are deterministic with fixed random seed."""
        np.random.seed(42)
        matrix1 = np.random.rand(10, 5)
        result1 = pick_threshold(matrix1)
        
        np.random.seed(42)
        matrix2 = np.random.rand(10, 5)
        result2 = pick_threshold(matrix2)
        
        assert result1 == result2

    def test_with_identity_matrix(self):
        """Test with identity matrix (perfect correlation on diagonal)."""
        matrix = np.eye(5)
        result = pick_threshold(matrix)
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_with_constant_matrix(self):
        """Test with constant matrix (all same values)."""
        matrix = np.ones((10, 5))
        result = pick_threshold(matrix)
        assert isinstance(result, float)
        assert 0 <= result <= 1


class TestDefaultCorrelationToNetwork:
    """Test default_correlation_to_network function."""

    def test_returns_numpy_array(self):
        """Test that function returns a numpy array."""
        matrix = np.random.rand(10, 5)
        result = default_correlation_to_network(matrix)
        assert isinstance(result, np.ndarray)

    def test_result_is_binary(self):
        """Test that result is binary (0s and 1s only)."""
        matrix = np.random.rand(10, 5)
        result = default_correlation_to_network(matrix)
        unique_values = np.unique(result)
        # Result should contain only 0s and 1s (and possibly NaNs if input had them)
        assert all(val in [0.0, 1.0] or np.isnan(val) for val in unique_values)

    def test_preserves_shape(self):
        """Test that output preserves input shape."""
        matrix = np.random.rand(10, 5)
        result = default_correlation_to_network(matrix)
        assert result.shape == matrix.shape

    def test_standard_preprocessing(self):
        """Test with standard preprocessing (default)."""
        matrix = np.random.rand(10, 5)
        result = default_correlation_to_network(matrix, preprocess="standard")
        assert isinstance(result, np.ndarray)
        assert result.shape == matrix.shape

    def test_no_preprocessing(self):
        """Test with no preprocessing."""
        matrix = np.random.rand(10, 5)
        result = default_correlation_to_network(matrix, preprocess="none")
        assert isinstance(result, np.ndarray)
        assert result.shape == matrix.shape

    def test_with_constant_column(self):
        """Test that constant columns (std=0) are handled without error."""
        matrix = np.random.rand(10, 5)
        matrix[:, 2] = 1.0  # Make one column constant
        
        # Should not raise ZeroDivisionError
        result = default_correlation_to_network(matrix, preprocess="standard")
        assert isinstance(result, np.ndarray)
        assert result.shape == matrix.shape

    def test_input_type_parameter(self):
        """Test that input_type parameter is accepted."""
        matrix = np.random.rand(10, 5)
        result = default_correlation_to_network(matrix, input_type="matrix")
        assert isinstance(result, np.ndarray)

    def test_deterministic_with_seed(self):
        """Test that results are deterministic with fixed random seed."""
        np.random.seed(42)
        matrix1 = np.random.rand(10, 5)
        result1 = default_correlation_to_network(matrix1)
        
        np.random.seed(42)
        matrix2 = np.random.rand(10, 5)
        result2 = default_correlation_to_network(matrix2)
        
        assert np.array_equal(result1, result2)

    @patch('py3plex.algorithms.statistics.correlation_networks.pick_threshold')
    def test_uses_pick_threshold(self, mock_pick_threshold):
        """Test that pick_threshold is called internally."""
        mock_pick_threshold.return_value = 0.5
        
        matrix = np.random.rand(10, 5)
        result = default_correlation_to_network(matrix)
        
        # Verify pick_threshold was called
        assert mock_pick_threshold.called

    def test_with_all_zeros(self):
        """Test with matrix of all zeros."""
        matrix = np.zeros((10, 5))
        # Should handle gracefully
        result = default_correlation_to_network(matrix)
        assert isinstance(result, np.ndarray)
        assert result.shape == matrix.shape

    def test_with_small_values(self):
        """Test with very small values."""
        matrix = np.random.rand(10, 5) * 0.001
        result = default_correlation_to_network(matrix)
        assert isinstance(result, np.ndarray)
        assert result.shape == matrix.shape
