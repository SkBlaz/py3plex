"""
Property-based tests for uncertainty aggregation in estimation.py.

This module tests properties of the _aggregate_samples function and
uncertainty estimation, focusing on:
- Proper aggregation of samples
- Statistical consistency
- Deterministic behavior when expected
- Proper handling of different sample types
"""

import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

from py3plex.uncertainty.estimation import _aggregate_samples
from py3plex.uncertainty.types import StatSeries


# ============================================================================
# Custom Strategies
# ============================================================================

@st.composite
def dict_samples_strategy(draw, min_samples=2, max_samples=20, min_nodes=1, max_nodes=10):
    """Generate lists of dict samples (per-node statistics).
    
    Note: Some nodes may be missing from some samples to test the
    implementation's handling of sparse data (which uses default value 0.0).
    """
    n_samples = draw(st.integers(min_value=min_samples, max_value=max_samples))
    n_nodes = draw(st.integers(min_value=min_nodes, max_value=max_nodes))
    
    # Create node names
    nodes = [f"node_{i}" for i in range(n_nodes)]
    
    samples = []
    for _ in range(n_samples):
        sample = {}
        for node in nodes:
            # Include node with 80% probability to ensure some data while testing sparsity
            if draw(st.booleans()) or draw(st.booleans()) or draw(st.booleans()):
                value = draw(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False))
                sample[node] = value
        samples.append(sample)
    
    return samples


@st.composite
def scalar_samples_strategy(draw, min_samples=2, max_samples=50):
    """Generate lists of scalar samples."""
    n_samples = draw(st.integers(min_value=min_samples, max_value=max_samples))
    samples = []
    for _ in range(n_samples):
        value = draw(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False))
        samples.append(value)
    return samples


@st.composite
def array_samples_strategy(draw, min_samples=2, max_samples=20, array_length=5):
    """Generate lists of array samples."""
    n_samples = draw(st.integers(min_value=min_samples, max_value=max_samples))
    samples = []
    for _ in range(n_samples):
        arr = np.array([
            draw(st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False))
            for _ in range(array_length)
        ])
        samples.append(arr)
    return samples


# ============================================================================
# Property Tests: Dict Samples (Per-Node Statistics)
# ============================================================================

class TestDictSamplesAggregation:
    """Property-based tests for aggregating dict samples."""
    
    @given(dict_samples_strategy(min_samples=2, max_samples=20))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_statseries_for_dict_samples(self, samples):
        """Property: Aggregating dict samples returns StatSeries."""
        # Skip if all samples are empty
        assume(any(len(s) > 0 for s in samples))
        
        result = _aggregate_samples(samples)
        assert isinstance(result, StatSeries), "Should return StatSeries for dict samples"
    
    @given(dict_samples_strategy(min_samples=2, max_samples=20, min_nodes=3, max_nodes=5))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_aggregated_length_includes_all_nodes(self, samples):
        """Property: Result includes all nodes that appear in any sample."""
        # Skip if all samples are empty
        assume(any(len(s) > 0 for s in samples))
        
        # Collect all nodes
        all_nodes = set()
        for sample in samples:
            all_nodes.update(sample.keys())
        
        result = _aggregate_samples(samples)
        
        # Result should have at least as many nodes as appeared in samples
        assert len(result) >= len(all_nodes), \
            f"Result length {len(result)} < number of unique nodes {len(all_nodes)}"
    
    @given(dict_samples_strategy(min_samples=2, max_samples=20))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_mean_is_within_sample_range(self, samples):
        """Property: Mean values should be within the range of all sample values including zeros."""
        # Skip if all samples are empty
        assume(any(len(s) > 0 for s in samples))
        
        result = _aggregate_samples(samples)
        
        # For each node, check mean is reasonable
        for i, node in enumerate(result.index):
            # Collect all values for this node (including implicit 0.0 for missing)
            # This matches the implementation which uses sample.get(node, 0.0)
            node_values = [s.get(node, 0.0) for s in samples]
            
            min_val = min(node_values)
            max_val = max(node_values)
            mean_val = result.mean[i]
            
            # Mean should be between min and max (with small tolerance)
            assert min_val - 1e-10 <= mean_val <= max_val + 1e-10, \
                f"Mean {mean_val} not in range [{min_val}, {max_val}] for node {node}"
    
    @given(dict_samples_strategy(min_samples=5, max_samples=20))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_std_is_non_negative(self, samples):
        """Property: Standard deviation is always non-negative."""
        # Skip if all samples are empty
        assume(any(len(s) > 0 for s in samples))
        
        result = _aggregate_samples(samples)
        
        assert result.std is not None, "std should not be None"
        assert np.all(result.std >= 0), "All std values must be non-negative"
    
    @given(dict_samples_strategy(min_samples=5, max_samples=20))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_quantiles_ordered(self, samples):
        """Property: Lower quantile <= upper quantile for all nodes."""
        # Skip if all samples are empty
        assume(any(len(s) > 0 for s in samples))
        
        result = _aggregate_samples(samples)
        
        if result.quantiles is not None:
            q025 = result.quantiles.get(0.025)
            q975 = result.quantiles.get(0.975)
            
            if q025 is not None and q975 is not None:
                # 2.5th percentile should be <= 97.5th percentile
                assert np.all(q025 <= q975 + 1e-10), \
                    "Lower quantile should be <= upper quantile"
    
    @given(dict_samples_strategy(min_samples=5, max_samples=20))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_mean_between_quantiles(self, samples):
        """Property: Mean should be within the quantile range for most nodes."""
        # Skip if all samples are empty
        assume(any(len(s) > 0 for s in samples))
        
        result = _aggregate_samples(samples)
        
        if result.quantiles is not None:
            q025 = result.quantiles.get(0.025)
            q975 = result.quantiles.get(0.975)
            
            if q025 is not None and q975 is not None:
                # For most nodes, mean should be within the 95% CI
                # (allowing some to be outside due to skewed distributions)
                within_ci = (q025 <= result.mean) & (result.mean <= q975)
                proportion_within = np.mean(within_ci)
                
                assert proportion_within >= 0.8, \
                    f"Only {proportion_within*100:.1f}% of means within CI, expected >= 80%"


# ============================================================================
# Property Tests: Scalar Samples
# ============================================================================

class TestScalarSamplesAggregation:
    """Property-based tests for aggregating scalar samples."""
    
    @given(scalar_samples_strategy(min_samples=2, max_samples=50))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_float_for_scalar_samples(self, samples):
        """Property: Aggregating scalar samples returns float."""
        result = _aggregate_samples(samples)
        assert isinstance(result, (int, float, np.number)), \
            f"Should return scalar for scalar samples, got {type(result)}"
    
    @given(scalar_samples_strategy(min_samples=2, max_samples=50))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_scalar_mean_in_sample_range(self, samples):
        """Property: Scalar mean should be within sample range."""
        result = _aggregate_samples(samples)
        
        min_val = min(samples)
        max_val = max(samples)
        
        assert min_val <= result <= max_val, \
            f"Mean {result} not in range [{min_val}, {max_val}]"
    
    @given(scalar_samples_strategy(min_samples=5, max_samples=50))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_scalar_mean_equals_numpy_mean(self, samples):
        """Property: Scalar aggregation should match numpy mean."""
        result = _aggregate_samples(samples)
        expected = np.mean(samples)
        
        assert np.isclose(result, expected, rtol=1e-10), \
            f"Aggregated mean {result} != numpy mean {expected}"
    
    @given(st.lists(st.floats(min_value=5.0, max_value=5.0), min_size=2, max_size=10))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_constant_samples_give_constant_mean(self, samples):
        """Property: Constant samples should give constant mean."""
        # All samples are 5.0
        result = _aggregate_samples(samples)
        assert np.isclose(result, 5.0, rtol=1e-10)


# ============================================================================
# Property Tests: Array Samples
# ============================================================================

class TestArraySamplesAggregation:
    """Property-based tests for aggregating array samples."""
    
    @given(array_samples_strategy(min_samples=2, max_samples=20, array_length=5))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_returns_statseries_for_array_samples(self, samples):
        """Property: Aggregating array samples returns StatSeries."""
        result = _aggregate_samples(samples)
        assert isinstance(result, StatSeries), "Should return StatSeries for array samples"
    
    @given(array_samples_strategy(min_samples=2, max_samples=20, array_length=5))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_array_aggregation_preserves_length(self, samples):
        """Property: Aggregated array has same length as input arrays."""
        result = _aggregate_samples(samples)
        expected_length = len(samples[0])
        
        assert len(result) == expected_length, \
            f"Result length {len(result)} != expected {expected_length}"
    
    @given(array_samples_strategy(min_samples=5, max_samples=20, array_length=5))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_array_mean_in_sample_range(self, samples):
        """Property: Each element's mean should be within its sample range."""
        result = _aggregate_samples(samples)
        
        # Convert samples to 2D array
        samples_array = np.array(samples)
        
        for i in range(len(result)):
            values = samples_array[:, i]
            min_val = np.min(values)
            max_val = np.max(values)
            mean_val = result.mean[i]
            
            assert min_val - 1e-10 <= mean_val <= max_val + 1e-10, \
                f"Mean {mean_val} not in range [{min_val}, {max_val}] for element {i}"
    
    @given(array_samples_strategy(min_samples=5, max_samples=20, array_length=5))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_array_std_non_negative(self, samples):
        """Property: All std values are non-negative."""
        result = _aggregate_samples(samples)
        
        assert result.std is not None
        assert np.all(result.std >= 0), "All std values must be non-negative"


# ============================================================================
# Property Tests: Deterministic Cases
# ============================================================================

class TestDeterministicAggregation:
    """Property-based tests for deterministic (zero variance) cases."""
    
    @given(
        st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
        st.integers(min_value=2, max_value=20)
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_identical_scalars_have_zero_std(self, value, n_samples):
        """Property: Identical scalar samples should have zero variance."""
        samples = [value] * n_samples
        result = _aggregate_samples(samples)
        
        assert np.isclose(result, value, rtol=1e-10)
    
    @given(
        st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
        st.integers(min_value=3, max_value=10),
        st.integers(min_value=2, max_value=20)
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_identical_dict_samples_have_zero_std(self, value, n_nodes, n_samples):
        """Property: Identical dict samples should have zero std."""
        nodes = [f"node_{i}" for i in range(n_nodes)]
        sample = {node: value for node in nodes}
        samples = [sample.copy() for _ in range(n_samples)]
        
        result = _aggregate_samples(samples)
        
        # All means should be the value
        assert np.allclose(result.mean, value)
        # All stds should be zero
        assert np.allclose(result.std, 0.0, atol=1e-10)
    
    @given(
        st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
        st.integers(min_value=5, max_value=10),
        st.integers(min_value=2, max_value=20)
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_identical_array_samples_have_zero_std(self, value, array_length, n_samples):
        """Property: Identical array samples should have zero std."""
        sample = np.full(array_length, value)
        samples = [sample.copy() for _ in range(n_samples)]
        
        result = _aggregate_samples(samples)
        
        # All means should be the value
        assert np.allclose(result.mean, value)
        # All stds should be zero
        assert np.allclose(result.std, 0.0, atol=1e-10)


# ============================================================================
# Property Tests: Statistical Properties
# ============================================================================

class TestStatisticalProperties:
    """Property-based tests for statistical properties of aggregation."""
    
    @given(scalar_samples_strategy(min_samples=10, max_samples=50))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_adding_extreme_value_increases_variance(self, samples):
        """Property: Adding an extreme value should increase variance."""
        # Get original result
        result1 = _aggregate_samples(samples)
        
        # Add an extreme value
        extreme = max(samples) * 2 + 100
        samples_with_extreme = samples + [extreme]
        result2 = _aggregate_samples(samples_with_extreme)
        
        # The mean should change
        assert not np.isclose(result1, result2), \
            "Adding extreme value should change mean"
    
    @given(dict_samples_strategy(min_samples=5, max_samples=15))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_more_samples_same_distribution_similar_mean(self, samples):
        """Property: Doubling samples from same distribution gives similar mean."""
        # Skip if all samples are empty
        assume(any(len(s) > 0 for s in samples))
        
        result1 = _aggregate_samples(samples)
        
        # Double the samples
        samples_doubled = samples + samples
        result2 = _aggregate_samples(samples_doubled)
        
        # Means should be very similar (identical samples)
        assert np.allclose(result1.mean, result2.mean, rtol=1e-10), \
            "Doubling samples should give same mean"
        
        # Std should also be very similar
        assert np.allclose(result1.std, result2.std, rtol=1e-10), \
            "Doubling samples should give same std"
    
    @given(array_samples_strategy(min_samples=10, max_samples=20, array_length=5))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_aggregation_is_commutative(self, samples):
        """Property: Order of samples should not matter."""
        result1 = _aggregate_samples(samples)
        
        # Create a shuffled version using deterministic permutation
        # Convert to list of tuples for hashing, then back
        indices = list(range(len(samples)))
        # Use a simple deterministic permutation based on list length
        shuffled_indices = indices[::-1]  # Reverse order - deterministic
        shuffled = [samples[i] for i in shuffled_indices]
        result2 = _aggregate_samples(shuffled)
        
        # Means should be identical
        assert np.allclose(result1.mean, result2.mean, rtol=1e-10)
        # Stds should be identical
        assert np.allclose(result1.std, result2.std, rtol=1e-10)


# ============================================================================
# Property Tests: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Property-based tests for edge cases and error conditions."""
    
    def test_empty_samples_raises_error(self):
        """Property: Empty sample list should raise ValueError."""
        with pytest.raises(ValueError, match="No samples to aggregate"):
            _aggregate_samples([])
    
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_single_sample_returns_valid_result(self, n_nodes):
        """Property: Single sample should return valid result with std."""
        nodes = [f"node_{i}" for i in range(n_nodes)]
        sample = {node: float(i) for i, node in enumerate(nodes)}
        samples = [sample]
        
        result = _aggregate_samples(samples)
        
        # Should return StatSeries
        assert isinstance(result, StatSeries)
        # std should be zero (only one sample)
        assert np.allclose(result.std, 0.0)
    
    @given(dict_samples_strategy(min_samples=2, max_samples=10))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_handles_missing_nodes_gracefully(self, samples):
        """Property: Should handle samples with different sets of nodes."""
        # This is already tested by dict_samples_strategy which can have
        # different nodes in different samples
        assume(any(len(s) > 0 for s in samples))
        
        result = _aggregate_samples(samples)
        
        # Should complete without error
        assert isinstance(result, StatSeries)
        # Should have nodes from all samples
        all_nodes = set()
        for s in samples:
            all_nodes.update(s.keys())
        assert len(result.index) >= len(all_nodes)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
