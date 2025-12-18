"""Correctness tests for scalar operations and mixed-model propagation in py3plex.stats."""

import numpy as np
import pytest

from py3plex.stats import Bootstrap, Delta, Gaussian, Interval, Provenance, StatValue


def test_delta_sampling_respects_sigma():
    """Delta.sample should reflect non-zero sigma for MC propagation."""
    d = Delta(0.5)
    samples = d.sample(5000, seed=123)
    assert np.isfinite(samples).all()
    assert abs(float(np.mean(samples))) < 0.05
    assert np.std(samples) == pytest.approx(0.5, rel=0.1)


def test_statvalue_mul_scalar_scales_delta_uncertainty():
    """Multiplying by a scalar scales Delta sigma by |k|."""
    sv = StatValue(10.0, Delta(0.5), Provenance("algo", "delta", {}))
    out = sv * -3.0
    assert float(out) == pytest.approx(-30.0)
    assert out.std() == pytest.approx(1.5)


def test_statvalue_div_scalar_scales_gaussian_uncertainty():
    """Dividing by a scalar scales Gaussian std by 1/|k| and mean by 1/k."""
    sv = StatValue(8.0, Gaussian(0.0, 2.0), Provenance("algo", "gaussian", {}))
    out = sv / 4.0
    assert float(out) == pytest.approx(2.0)
    assert out.std() == pytest.approx(0.5)


def test_statvalue_mul_scalar_scales_interval_uncertainty_and_orders_bounds():
    """Scaling an Interval uncertainty by a negative scalar should swap bounds."""
    sv = StatValue(1.0, Interval(-1.0, 2.0), Provenance("algo", "interval", {}))
    out = sv * -2.0
    assert float(out) == pytest.approx(-2.0)
    assert out.uncertainty.low == pytest.approx(-4.0)
    assert out.uncertainty.high == pytest.approx(2.0)


def test_mc_propagate_delta_sigma_affects_mixed_type_propagation():
    """Delta(sigma) should contribute variance when combined with non-Delta models."""
    delta = Delta(0.5)
    boot_samples = np.array([-1.0, 0.0, 1.0])
    boot = Bootstrap(boot_samples)

    combined = delta.propagate("+", boot, seed=42)

    # Under MC propagation, Bootstrap is treated as an empirical distribution over samples.
    expected_std = float(np.sqrt(np.var(boot_samples, ddof=0) + delta.sigma**2))
    assert combined.std() == pytest.approx(expected_std, rel=0.08)


def test_statvalue_div_by_zero_raises():
    """Division by scalar 0 must raise ZeroDivisionError."""
    sv = StatValue(1.0, Delta(0.1), Provenance("algo", "delta", {}))
    with pytest.raises(ZeroDivisionError):
        _ = sv / 0

