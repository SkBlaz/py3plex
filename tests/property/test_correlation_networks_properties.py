#!/usr/bin/env python3
"""
Property-based tests for algorithms.statistics.correlation_networks module.

Tests invariants for correlation network construction and threshold selection.
"""

import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

# Import correlation_networks module
try:
    from py3plex.algorithms.statistics.correlation_networks import (
        pick_threshold,
        default_correlation_to_network,
    )
    CORRELATION_AVAILABLE = True
except ImportError:
    CORRELATION_AVAILABLE = False
    pytest.skip("Correlation networks module not available", allow_module_level=True)


# ============================================================================
# Property Tests: Threshold Selection
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_samples=st.integers(min_value=10, max_value=30),
    n_features=st.integers(min_value=5, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_pick_threshold_returns_valid_range(n_samples, n_features, seed):
    """Test that pick_threshold returns a value in [0, 1]."""
    np.random.seed(seed)
    matrix = np.random.randn(n_samples, n_features)
    
    threshold = pick_threshold(matrix)
    
    # Threshold should be in valid range
    assert 0 <= threshold <= 1, f"Threshold {threshold} not in [0, 1]"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_samples=st.integers(min_value=10, max_value=25),
    n_features=st.integers(min_value=5, max_value=12),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_pick_threshold_deterministic(n_samples, n_features, seed):
    """Test that pick_threshold is deterministic for the same input."""
    np.random.seed(seed)
    matrix = np.random.randn(n_samples, n_features)
    
    threshold1 = pick_threshold(matrix)
    threshold2 = pick_threshold(matrix)
    
    # Should return same threshold for same input
    assert threshold1 == threshold2, "Threshold selection should be deterministic"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_samples=st.integers(min_value=10, max_value=25),
    n_features=st.integers(min_value=5, max_value=12),
    scale=st.floats(min_value=0.1, max_value=10.0),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_pick_threshold_scale_invariant(n_samples, n_features, scale, seed):
    """Test that pick_threshold is invariant to scaling (due to correlation)."""
    np.random.seed(seed)
    matrix = np.random.randn(n_samples, n_features)
    
    threshold1 = pick_threshold(matrix)
    threshold2 = pick_threshold(matrix * scale)
    
    # Correlation is scale-invariant, so threshold should be similar
    # Allow some numerical tolerance
    assert abs(threshold1 - threshold2) < 0.2, \
        f"Threshold should be roughly scale-invariant: {threshold1} vs {threshold2}"


# ============================================================================
# Property Tests: Correlation to Network Conversion
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_samples=st.integers(min_value=10, max_value=30),
    n_features=st.integers(min_value=5, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_correlation_to_network_binary(n_samples, n_features, seed):
    """Test that default_correlation_to_network returns binary matrix."""
    np.random.seed(seed)
    matrix = np.random.randn(n_samples, n_features)
    
    result = default_correlation_to_network(matrix)
    
    # Result should be binary (only 0s and 1s)
    unique_values = np.unique(result)
    assert all(val in [0, 1] for val in unique_values), \
        f"Result should be binary, got values: {unique_values}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_samples=st.integers(min_value=10, max_value=30),
    n_features=st.integers(min_value=5, max_value=15),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_correlation_to_network_shape_preserved(n_samples, n_features, seed):
    """Test that output shape matches input matrix shape."""
    np.random.seed(seed)
    matrix = np.random.randn(n_samples, n_features)
    
    result = default_correlation_to_network(matrix)
    
    # The function operates on the matrix in place and returns it
    # Shape should match input
    assert result.shape == matrix.shape, \
        f"Result shape {result.shape} should match input shape {matrix.shape}"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_samples=st.integers(min_value=10, max_value=25),
    n_features=st.integers(min_value=5, max_value=12),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_correlation_to_network_result_matrix(n_samples, n_features, seed):
    """Test that result is a valid matrix."""
    np.random.seed(seed)
    matrix = np.random.randn(n_samples, n_features)
    
    result = default_correlation_to_network(matrix)
    
    # Result should be an ndarray
    assert isinstance(result, np.ndarray), \
        "Result should be an ndarray"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_samples=st.integers(min_value=10, max_value=25),
    n_features=st.integers(min_value=5, max_value=12),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_correlation_standard_preprocessing_handles_varied_data(n_samples, n_features, seed):
    """Test that standard preprocessing handles normal varied data gracefully."""
    np.random.seed(seed)
    matrix = np.random.randn(n_samples, n_features)
    
    # Standard preprocessing should work
    result = default_correlation_to_network(matrix, preprocess="standard")
    
    # Result should still be valid
    assert result.shape == matrix.shape, "Shape should be preserved"
    assert np.isfinite(result).all(), "Result should not contain inf or nan"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_samples=st.integers(min_value=10, max_value=25),
    n_features=st.integers(min_value=5, max_value=12),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_correlation_to_network_no_preprocessing_option(n_samples, n_features, seed):
    """Test that non-standard preprocessing option is handled."""
    np.random.seed(seed)
    matrix = np.random.randn(n_samples, n_features)
    
    # Use non-standard preprocessing (should skip normalization)
    result = default_correlation_to_network(matrix, preprocess="none")
    
    # Should still return a valid binary matrix
    assert result.shape == matrix.shape, "Shape should match input"
    unique_values = np.unique(result)
    assert all(val in [0, 1] for val in unique_values), \
        "Result should be binary even without standard preprocessing"


# ============================================================================
# Property Tests: Edge Cases
# ============================================================================

@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_samples=st.integers(min_value=10, max_value=20),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_correlation_identical_features(n_samples, seed):
    """Test behavior when all features are identical."""
    np.random.seed(seed)
    # Create matrix where all features are the same
    base_feature = np.random.randn(n_samples)
    matrix = np.tile(base_feature.reshape(-1, 1), (1, 5))
    
    # Should handle perfect correlation gracefully
    result = default_correlation_to_network(matrix, preprocess="standard")
    
    # Should be all ones (perfect correlation) or all zeros depending on threshold
    assert result.shape == matrix.shape, "Shape should match input"
    assert np.isfinite(result).all(), "Result should not contain inf or nan"


@pytest.mark.property
@settings(deadline=None, max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    n_samples=st.integers(min_value=10, max_value=20),
    n_features=st.integers(min_value=5, max_value=10),
    seed=st.integers(min_value=0, max_value=10000)
)
def test_correlation_network_finite_values(n_samples, n_features, seed):
    """Test that all output values are finite."""
    np.random.seed(seed)
    matrix = np.random.randn(n_samples, n_features)
    
    result = default_correlation_to_network(matrix)
    
    # All values should be finite (no inf or nan)
    assert np.isfinite(result).all(), \
        "All values in correlation network should be finite"
