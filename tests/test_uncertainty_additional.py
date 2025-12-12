"""Additional tests for py3plex.uncertainty core types and helpers."""

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.uncertainty import (
    ResamplingStrategy,
    get_uncertainty_config,
    uncertainty_enabled,
)
from py3plex.uncertainty.estimation import estimate_uncertainty, _aggregate_samples
from py3plex.uncertainty.types import StatMatrix, StatSeries


def test_statseries_quantile_length_validation():
    """Quantile arrays must match index length."""
    with pytest.raises(ValueError, match="quantile .*index length"):
        StatSeries(
            index=["a", "b", "c"],
            mean=[1, 2, 3],
            quantiles={0.9: np.array([1.0, 2.0])},
        )


def test_statseries_to_dict_includes_quantiles():
    """Quantiles propagate through to_dict output."""
    series = StatSeries(
        index=["x", "y"],
        mean=np.array([1.0, 2.0]),
        std=np.array([0.1, 0.2]),
        quantiles={0.5: np.array([0.9, 1.9])},
    )

    as_dict = series.to_dict()
    assert as_dict["x"]["quantiles"][0.5] == pytest.approx(0.9)
    assert as_dict["y"]["quantiles"][0.5] == pytest.approx(1.9)


def test_statmatrix_quantile_shape_validation():
    """StatMatrix rejects quantile matrices with mismatched shape."""
    with pytest.raises(ValueError, match="quantile .*shape"):
        StatMatrix(
            index=["a", "b"],
            mean=np.ones((2, 2)),
            quantiles={0.1: np.ones((3, 3))},
        )


def test_estimate_uncertainty_not_implemented_strategy():
    """Unsupported resampling strategies surface explicit errors."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges([["a", "L0", "b", "L0", 1.0]], input_type="list")

    def metric_fn(network):
        return len(list(network.get_edges()))

    with pytest.raises(NotImplementedError, match="Bootstrap resampling"):
        estimate_uncertainty(
            net,
            metric_fn,
            n_runs=2,
            resampling=ResamplingStrategy.BOOTSTRAP,
            random_seed=123,
        )


def test_aggregate_samples_validation_errors():
    """_aggregate_samples should guard empty inputs and unknown sample types."""
    with pytest.raises(ValueError, match="No samples"):
        _aggregate_samples([])

    with pytest.raises(TypeError, match="Unsupported sample type"):
        _aggregate_samples([{"a"}, {"b"}])


def test_uncertainty_context_does_not_leak_changes():
    """Temporary context mutations should not persist after exit."""
    original_runs = get_uncertainty_config().default_n_runs
    with uncertainty_enabled(n_runs=7):
        inner_cfg = get_uncertainty_config()
        assert inner_cfg.default_n_runs == 7
    assert get_uncertainty_config().default_n_runs == original_runs
