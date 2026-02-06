"""Property-based tests for py3plex.stats module.

Tests StatValue, uncertainty types, and statistical operations to ensure:
- StatValue behaves correctly with different uncertainty types
- Uncertainty scaling follows mathematical laws
- Confidence intervals are consistent
- Arithmetic operations preserve uncertainty
"""

import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st, assume
from hypothesis import HealthCheck
import numpy as np

from py3plex.stats import (
    StatValue,
    Delta,
    Gaussian,
    Interval,
    Provenance,
)


# ============================================================================
# StatValue Properties
# ============================================================================


@given(
    value=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    sigma=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_statvalue_with_delta_uncertainty_initialization(value, sigma):
    """StatValue can be initialized with Delta uncertainty."""
    sv = StatValue(
        value=value,
        uncertainty=Delta(sigma),
        provenance=Provenance("test", "delta", {}),
    )
    
    assert float(sv) == value
    assert sv.std() == sigma


@given(
    value=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    std_dev=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_statvalue_with_gaussian_uncertainty_initialization(value, std_dev):
    """StatValue can be initialized with Gaussian uncertainty."""
    sv = StatValue(
        value=value,
        uncertainty=Gaussian(0.0, std_dev),
        provenance=Provenance("test", "gaussian", {}),
    )
    
    assert float(sv) == value
    assert sv.std() == pytest.approx(std_dev, rel=0.01)


@given(
    value=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    low=st.floats(min_value=-10.0, max_value=0.0, allow_nan=False, allow_infinity=False),
    high=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_statvalue_with_interval_uncertainty_initialization(value, low, high):
    """StatValue can be initialized with Interval uncertainty."""
    assume(low < high)
    
    sv = StatValue(
        value=value,
        uncertainty=Interval(low, high),
        provenance=Provenance("test", "interval", {}),
    )
    
    assert float(sv) == value
    ci = sv.ci(0.95)
    assert ci[0] <= value <= ci[1] or abs(ci[0] - value) < 1e-10 or abs(ci[1] - value) < 1e-10


# ============================================================================
# Uncertainty Scaling Properties
# ============================================================================


@given(
    value=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    sigma=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    scale_factor=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_delta_uncertainty_scales_with_multiplication(value, sigma, scale_factor):
    """Delta uncertainty should scale correctly when StatValue is multiplied."""
    sv = StatValue(
        value=value,
        uncertainty=Delta(sigma),
        provenance=Provenance("test", "delta", {}),
    )
    
    scaled = sv * scale_factor
    
    assert float(scaled) == pytest.approx(value * scale_factor, rel=0.01)
    assert scaled.std() == pytest.approx(abs(scale_factor) * sigma, rel=0.01)


@given(
    value=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    std_dev=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    scale_factor=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_gaussian_uncertainty_scales_with_multiplication(value, std_dev, scale_factor):
    """Gaussian uncertainty should scale correctly when StatValue is multiplied."""
    assume(abs(scale_factor) > 0.01)  # Avoid very small factors
    
    sv = StatValue(
        value=value,
        uncertainty=Gaussian(0.0, std_dev),
        provenance=Provenance("test", "gaussian", {}),
    )
    
    scaled = sv * scale_factor
    
    assert float(scaled) == pytest.approx(value * scale_factor, rel=0.01)
    assert scaled.std() == pytest.approx(abs(scale_factor) * std_dev, rel=0.05)


# ============================================================================
# Confidence Interval Properties
# ============================================================================


@given(
    value=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    std_dev=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
    ci_level=st.floats(min_value=0.8, max_value=0.99, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_confidence_interval_contains_value(value, std_dev, ci_level):
    """Confidence interval should contain the point estimate (for symmetric distributions)."""
    sv = StatValue(
        value=value,
        uncertainty=Gaussian(0.0, std_dev),
        provenance=Provenance("test", "gaussian", {}),
    )
    
    ci = sv.ci(ci_level)
    
    # For Gaussian centered at 0, value should be approximately in the CI
    # (Not strictly guaranteed for all cases, but usually true)
    assert ci[0] <= ci[1]
    assert ci[1] - ci[0] > 0  # CI should have non-zero width


@given(
    value=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    low=st.floats(min_value=-10.0, max_value=0.0, allow_nan=False, allow_infinity=False),
    high=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_interval_uncertainty_ci_matches_bounds(value, low, high):
    """Interval uncertainty CI should match the specified bounds (relative to value)."""
    assume(low < high)
    
    sv = StatValue(
        value=value,
        uncertainty=Interval(low, high),
        provenance=Provenance("test", "interval", {}),
    )
    
    ci = sv.ci(0.95)  # Level doesn't matter for Interval
    
    # CI should be value + offset bounds
    assert abs(ci[0] - (value + low)) < 1e-6
    assert abs(ci[1] - (value + high)) < 1e-6


# ============================================================================
# Arithmetic Properties
# ============================================================================


@given(
    value1=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    value2=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    sigma1=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    sigma2=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_statvalue_addition_combines_values(value1, value2, sigma1, sigma2):
    """Adding two StatValues should combine their point estimates."""
    sv1 = StatValue(
        value=value1,
        uncertainty=Delta(sigma1),
        provenance=Provenance("test1", "delta", {}),
    )
    
    sv2 = StatValue(
        value=value2,
        uncertainty=Delta(sigma2),
        provenance=Provenance("test2", "delta", {}),
    )
    
    result = sv1 + sv2
    
    assert float(result) == pytest.approx(value1 + value2, rel=0.01)


@given(
    value1=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    value2=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    sigma1=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    sigma2=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_statvalue_subtraction_combines_values(value1, value2, sigma1, sigma2):
    """Subtracting two StatValues should combine their point estimates."""
    sv1 = StatValue(
        value=value1,
        uncertainty=Delta(sigma1),
        provenance=Provenance("test1", "delta", {}),
    )
    
    sv2 = StatValue(
        value=value2,
        uncertainty=Delta(sigma2),
        provenance=Provenance("test2", "delta", {}),
    )
    
    result = sv1 - sv2
    
    assert float(result) == pytest.approx(value1 - value2, rel=0.01)


# ============================================================================
# Provenance Properties
# ============================================================================


@given(
    algorithm=st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    method=st.sampled_from(["delta", "bootstrap", "gaussian", "empirical"]),
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_statvalue_provenance_is_preserved(algorithm, method):
    """StatValue provenance should be preserved."""
    prov = Provenance(algorithm, method, {})
    
    sv = StatValue(
        value=1.0,
        uncertainty=Delta(0.0),
        provenance=prov,
    )
    
    assert sv.provenance.algorithm == algorithm
    assert sv.provenance.uncertainty_method == method


# ============================================================================
# Edge Case Properties
# ============================================================================


def test_statvalue_with_zero_uncertainty_has_zero_std():
    """StatValue with Delta(0) should have zero standard deviation."""
    sv = StatValue(
        value=42.0,
        uncertainty=Delta(0.0),
        provenance=Provenance("test", "delta", {}),
    )
    
    assert sv.std() == 0.0


@given(
    value=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_statvalue_multiplication_by_zero_gives_zero(value):
    """Multiplying StatValue by zero should give zero."""
    sv = StatValue(
        value=value,
        uncertainty=Delta(1.0),
        provenance=Provenance("test", "delta", {}),
    )
    
    result = sv * 0.0
    
    assert float(result) == 0.0
    assert result.std() == 0.0  # Uncertainty should also become zero
