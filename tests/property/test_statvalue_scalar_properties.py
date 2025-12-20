"""Property-based tests for scalar scaling behavior in StatValue."""

import pytest
from hypothesis import given, settings, strategies as st, assume
from hypothesis import HealthCheck

from py3plex.stats import Delta, Gaussian, Provenance, StatValue


@given(
    st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=80, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_scalar_multiplication_scales_gaussian_std(value, std, scalar):
    """Multiplying by k scales Gaussian std by |k|."""
    assume(abs(scalar) > 1e-6)
    sv = StatValue(value, Gaussian(0.0, std), Provenance("test", "gaussian", {}))
    out = sv * scalar
    assert out.std() == pytest.approx(abs(scalar) * std, rel=1e-6, abs=1e-9)


@given(
    st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=80, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_scalar_division_scales_delta_sigma(value, sigma, scalar):
    """Dividing by k scales Delta sigma by 1/|k|."""
    assume(abs(scalar) > 1e-6)
    sv = StatValue(value, Delta(sigma), Provenance("test", "delta", {}))
    out = sv / scalar
    assert out.std() == pytest.approx(sigma / abs(scalar), rel=1e-6, abs=1e-9)

