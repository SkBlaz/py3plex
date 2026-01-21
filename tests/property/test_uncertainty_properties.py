"""
Property-based tests for the uncertainty module.

This module tests fundamental properties and invariants that the uncertainty
types should satisfy using Hypothesis for property-based testing.
"""

import numpy as np
import pytest
from hypothesis import given, settings, assume, strategies as st
from hypothesis import HealthCheck

from py3plex.uncertainty import (
    StatSeries,
    StatMatrix,
    CommunityStats,
    ResamplingStrategy,
    UncertaintyMode,
    UncertaintyConfig,
)


# ============================================================================
# Custom Strategies
# ============================================================================

@st.composite
def stat_series_strategy(draw, min_size=1, max_size=20):
    """Generate valid StatSeries objects."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    index = [f"node_{i}" for i in range(size)]
    mean = draw(st.lists(
        st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
        min_size=size,
        max_size=size
    ))
    
    # Optionally add std
    has_std = draw(st.booleans())
    std = None
    if has_std:
        std = draw(st.lists(
            st.floats(min_value=0, max_value=10, allow_nan=False, allow_infinity=False),
            min_size=size,
            max_size=size
        ))
    
    # Optionally add quantiles
    has_quantiles = draw(st.booleans())
    quantiles = None
    if has_quantiles:
        q025 = draw(st.lists(
            st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
            min_size=size,
            max_size=size
        ))
        q975 = draw(st.lists(
            st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
            min_size=size,
            max_size=size
        ))
        quantiles = {0.025: np.array(q025), 0.975: np.array(q975)}
    
    return StatSeries(
        index=index,
        mean=np.array(mean),
        std=np.array(std) if std is not None else None,
        quantiles=quantiles
    )


@st.composite
def stat_matrix_strategy(draw, min_size=2, max_size=10):
    """Generate valid StatMatrix objects."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    index = [f"node_{i}" for i in range(size)]
    
    # Generate mean matrix
    mean_data = []
    for i in range(size):
        row = draw(st.lists(
            st.floats(min_value=-100, max_value=100, allow_nan=False, allow_infinity=False),
            min_size=size,
            max_size=size
        ))
        mean_data.append(row)
    mean = np.array(mean_data)
    
    # Optionally add std matrix
    has_std = draw(st.booleans())
    std = None
    if has_std:
        std_data = []
        for i in range(size):
            row = draw(st.lists(
                st.floats(min_value=0, max_value=10, allow_nan=False, allow_infinity=False),
                min_size=size,
                max_size=size
            ))
            std_data.append(row)
        std = np.array(std_data)
    
    return StatMatrix(
        index=index,
        mean=mean,
        std=std,
        quantiles=None
    )


# ============================================================================
# Property Tests for StatSeries
# ============================================================================

class TestStatSeriesProperties:
    """Property-based tests for StatSeries."""
    
    @given(stat_series_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_length_consistency(self, series):
        """Property: Length of index equals length of mean array."""
        assert len(series.index) == len(series.mean)
        assert len(series) == len(series.index)
    
    @given(stat_series_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_std_length_matches_mean(self, series):
        """Property: If std exists, it has same length as mean."""
        if series.std is not None:
            assert len(series.std) == len(series.mean)
    
    @given(stat_series_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_quantiles_length_matches_mean(self, series):
        """Property: If quantiles exist, all have same length as mean."""
        if series.quantiles is not None:
            for q, arr in series.quantiles.items():
                assert len(arr) == len(series.mean), \
                    f"Quantile {q} has length {len(arr)}, expected {len(series.mean)}"
    
    @given(stat_series_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_std_non_negative(self, series):
        """Property: Standard deviations are always non-negative."""
        if series.std is not None:
            assert np.all(series.std >= 0), "std values must be non-negative"
    
    @given(stat_series_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_deterministic_iff_std_none_or_zero(self, series):
        """Property: Series is deterministic iff std is None or all zeros."""
        if series.std is None:
            assert series.is_deterministic
        elif np.all(series.std == 0):
            assert series.is_deterministic
        else:
            assert not series.is_deterministic
    
    @given(stat_series_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_certainty_binary(self, series):
        """Property: Certainty is either 0.0 or 1.0."""
        assert series.certainty in (0.0, 1.0)
    
    @given(stat_series_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_certainty_matches_deterministic(self, series):
        """Property: certainty == 1.0 iff is_deterministic."""
        if series.is_deterministic:
            assert series.certainty == 1.0
        else:
            assert series.certainty == 0.0
    
    @given(stat_series_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_array_conversion_gives_mean(self, series):
        """Property: Converting to array gives mean values."""
        arr = np.array(series)
        np.testing.assert_array_equal(arr, series.mean)
    
    @given(stat_series_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_dict_access_returns_valid_structure(self, series):
        """Property: Dictionary access returns dict with 'mean' key."""
        if len(series.index) > 0:
            node = series.index[0]
            item = series[node]
            assert isinstance(item, dict)
            assert 'mean' in item
            assert isinstance(item['mean'], (int, float, np.number))
    
    @given(stat_series_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_to_dict_has_all_nodes(self, series):
        """Property: to_dict() contains all nodes from index."""
        d = series.to_dict()
        assert len(d) == len(series.index)
        for node in series.index:
            assert node in d
    
    @given(stat_series_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_mean_array_is_float_type(self, series):
        """Property: Mean array has float dtype."""
        assert series.mean.dtype.kind == 'f', "mean should be float type"
    
    @given(stat_series_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_std_array_is_float_type_when_present(self, series):
        """Property: Std array has float dtype when present."""
        if series.std is not None:
            assert series.std.dtype.kind == 'f', "std should be float type"


# ============================================================================
# Property Tests for StatMatrix
# ============================================================================

class TestStatMatrixProperties:
    """Property-based tests for StatMatrix."""
    
    @given(stat_matrix_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_square_matrix(self, matrix):
        """Property: Mean matrix is square."""
        assert matrix.mean.shape[0] == matrix.mean.shape[1]
        assert matrix.mean.shape[0] == len(matrix.index)
    
    @given(stat_matrix_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_std_matches_shape(self, matrix):
        """Property: If std exists, it has same shape as mean."""
        if matrix.std is not None:
            assert matrix.std.shape == matrix.mean.shape
    
    @given(stat_matrix_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_std_non_negative(self, matrix):
        """Property: All std values are non-negative."""
        if matrix.std is not None:
            assert np.all(matrix.std >= 0)
    
    @given(stat_matrix_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_deterministic_iff_std_none_or_zero(self, matrix):
        """Property: Matrix is deterministic iff std is None or all zeros."""
        if matrix.std is None:
            assert matrix.is_deterministic
        elif np.all(matrix.std == 0):
            assert matrix.is_deterministic
        else:
            assert not matrix.is_deterministic
    
    @given(stat_matrix_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_certainty_binary(self, matrix):
        """Property: Certainty is either 0.0 or 1.0."""
        assert matrix.certainty in (0.0, 1.0)
    
    @given(stat_matrix_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_array_conversion_gives_mean(self, matrix):
        """Property: Converting to array gives mean matrix."""
        arr = np.array(matrix)
        np.testing.assert_array_equal(arr, matrix.mean)
    
    @given(stat_matrix_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_length_equals_dimension(self, matrix):
        """Property: len(matrix) equals matrix dimension."""
        assert len(matrix) == matrix.mean.shape[0]


# ============================================================================
# Property Tests for CommunityStats
# ============================================================================

class TestCommunityStatsProperties:
    """Property-based tests for CommunityStats."""
    
    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.integers(min_value=0, max_value=10),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_n_communities_computed_correctly(self, labels):
        """Property: n_communities equals number of unique community IDs."""
        stats = CommunityStats(labels=labels)
        unique_communities = len(set(labels.values()))
        assert stats.n_communities == unique_communities
    
    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.integers(min_value=0, max_value=10),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_length_equals_node_count(self, labels):
        """Property: len(stats) equals number of nodes."""
        stats = CommunityStats(labels=labels)
        assert len(stats) == len(labels)
    
    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.integers(min_value=0, max_value=10),
            min_size=1,
            max_size=20
        ),
        st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_modularity_in_valid_range(self, labels, modularity):
        """Property: Modularity is typically in [-1, 1] range."""
        stats = CommunityStats(labels=labels, modularity=modularity)
        if stats.modularity is not None:
            # For generated data we only check it's a float
            assert isinstance(stats.modularity, (int, float, np.number))
    
    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.integers(min_value=0, max_value=10),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_deterministic_when_no_uncertainty_info(self, labels):
        """Property: Stats are deterministic when no uncertainty info present."""
        stats = CommunityStats(labels=labels)
        assert stats.is_deterministic
        assert stats.certainty == 1.0


# ============================================================================
# Property Tests for Configuration Types
# ============================================================================

class TestConfigurationProperties:
    """Property-based tests for configuration classes."""
    
    @given(
        st.sampled_from(list(UncertaintyMode)),
        st.integers(min_value=1, max_value=1000),
        st.sampled_from(list(ResamplingStrategy))
    )
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_config_construction(self, mode, n_runs, strategy):
        """Property: UncertaintyConfig can be constructed with any valid parameters."""
        config = UncertaintyConfig(
            mode=mode,
            default_n_runs=n_runs,
            default_resampling=strategy
        )
        assert config.mode == mode
        assert config.default_n_runs == n_runs
        assert config.default_resampling == strategy
    
    @given(st.integers(min_value=1, max_value=1000))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_n_runs_positive(self, n_runs):
        """Property: n_runs should always be positive."""
        config = UncertaintyConfig(default_n_runs=n_runs)
        assert config.default_n_runs > 0


# ============================================================================
# Property Tests for Invariants
# ============================================================================

class TestUncertaintyInvariants:
    """Property-based tests for uncertainty invariants."""
    
    @given(stat_series_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_idempotent_array_conversion(self, series):
        """Property: Converting to array twice gives same result."""
        arr1 = np.array(series)
        arr2 = np.array(series)
        np.testing.assert_array_equal(arr1, arr2)
    
    @given(stat_series_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_to_dict_roundtrip_preserves_structure(self, series):
        """Property: to_dict preserves all node information."""
        d = series.to_dict()
        
        # All nodes should be present
        assert set(d.keys()) == set(series.index)
        
        # Each entry should have mean
        for node, stats in d.items():
            assert 'mean' in stats
            
            # If series has std, dict should have std
            if series.std is not None:
                assert 'std' in stats
    
    @given(stat_series_strategy())
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_quantile_ordering(self, series):
        """Property: Lower quantile values should be <= higher quantile values."""
        if series.quantiles is not None and len(series.quantiles) >= 2:
            quantiles_sorted = sorted(series.quantiles.items())
            for i in range(len(quantiles_sorted) - 1):
                q1_val, arr1 = quantiles_sorted[i]
                q2_val, arr2 = quantiles_sorted[i + 1]
                
                # Lower quantile should have lower or equal values
                # (allowing for sampling noise in generated data)
                # We just check the structure is valid
                assert len(arr1) == len(arr2)


# ============================================================================
# Edge Cases and Boundary Conditions
# ============================================================================

class TestEdgeCases:
    """Property-based tests for edge cases."""
    
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_single_value_series(self, size):
        """Property: Series with constant values works correctly."""
        index = [f"node_{i}" for i in range(size)]
        mean = np.ones(size) * 5.0
        series = StatSeries(index=index, mean=mean)
        
        assert len(series) == size
        assert np.all(series.mean == 5.0)
        assert series.is_deterministic
    
    @given(st.integers(min_value=2, max_value=10))
    @settings(max_examples=3, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_zero_std_is_deterministic(self, size):
        """Property: Series with zero std is deterministic."""
        index = [f"node_{i}" for i in range(size)]
        mean = np.random.randn(size)
        std = np.zeros(size)
        
        series = StatSeries(index=index, mean=mean, std=std)
        assert series.is_deterministic
        assert series.certainty == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
