"""Edge-case tests for py3plex.stats."""

import numpy as np
import pytest

from py3plex.stats import (
    Delta,
    Interval,
    Provenance,
    StatValue,
    StatisticSpec,
    compute_statistic,
    register_statistic,
)


def test_statvalue_rejects_non_numeric_value():
    """StatValue should enforce numeric values."""
    with pytest.raises(TypeError):
        StatValue("not-a-number", Delta(0.0), Provenance("algo", "delta", {}))


def test_statvalue_array_to_float_requires_scalar():
    """Conversion to float should fail for multi-element arrays."""
    sv = StatValue(np.array([1.0, 2.0]), Delta(0.0), Provenance("algo", "delta", {}))
    with pytest.raises(ValueError):
        float(sv)


def test_mc_propagate_unknown_operation_raises():
    """Unknown operations should bubble up as ValueError."""
    with pytest.raises(ValueError):
        Delta(0.0).propagate("xor", Delta(0.0))


def test_mc_propagate_division_by_zero_returns_delta():
    """MC propagation should return deterministic zero when samples are invalid."""
    result = Interval(0.0, 0.0).propagate("/", Interval(0.0, 0.0), seed=123)
    assert isinstance(result, Delta)
    assert result.std() == 0.0


def test_compute_statistic_propagates_kwargs_into_provenance():
    """compute_statistic should forward kwargs to estimator, uncertainty, and provenance."""
    spec = StatisticSpec(
        name="edge_case_compute",
        estimator=lambda x, factor=1, **_: x * factor,
        uncertainty_model=lambda x, factor=1, **_: Delta(0.1 * factor),
    )

    register_statistic(spec, force=True)
    stat = compute_statistic("edge_case_compute", 2, factor=4, seed=7)

    assert isinstance(stat, StatValue)
    assert float(stat) == 8.0
    assert stat.std() == pytest.approx(0.4)
    assert stat.provenance.parameters["factor"] == 4
    assert stat.provenance.seed == 7
