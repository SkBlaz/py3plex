"""Tests for DSL uncertainty defaults and wrapping behavior."""

from __future__ import annotations

import contextlib

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.dsl.operator_registry import register_operator, unregister_operator
from py3plex.uncertainty import get_uncertainty_config


@contextlib.contextmanager
def _preserve_uncertainty_defaults():
    """Temporarily preserve Q.uncertainty defaults to avoid global bleed."""
    original = Q.uncertainty.get_all()
    cfg = get_uncertainty_config()
    try:
        yield
    finally:
        Q.uncertainty.reset()
        for k, v in original.items():
            Q.uncertainty.defaults(**{k: v})
        # restore global context mode
        from py3plex.uncertainty import set_uncertainty_config, UncertaintyConfig

        set_uncertainty_config(
            UncertaintyConfig(
                mode=cfg.mode,
                default_n_runs=cfg.default_n_runs,
                default_resampling=cfg.default_resampling,
            )
        )


def _toy_net():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    edges = [
        ["a", "L0", "b", "L0", 1.0],
        ["b", "L0", "c", "L0", 1.0],
        ["a", "L1", "a", "L0", 1.0],  # inter-layer coupling
    ]
    net.add_edges(edges, input_type="list")
    return net


def test_uncertainty_defaults_auto_enable_bootstrap():
    """compute() picks up default uncertainty settings and returns mean/std."""
    with _preserve_uncertainty_defaults():
        Q.uncertainty.defaults(enabled=True, n_boot=3, ci=0.9, method="bootstrap")
        net = _toy_net()

        result = (
            Q.nodes()
            .compute("degree")  # no explicit uncertainty flag; uses defaults
            .order_by("-degree")
            .limit(2)
            .execute(net)
        )

        df = result.to_pandas()
        assert len(df) == 2
        # Degrees should be wrapped with mean/std keys
        wrapped = df["degree"].iloc[0]
        assert isinstance(wrapped, dict)
        assert "mean" in wrapped and "std" in wrapped
        assert wrapped["std"] >= 0
        assert result.meta.get("dsl_version") == "2.0"


def test_custom_operator_deterministic_wrapped_when_uncertainty_requested():
    """Custom operators get deterministic uncertainty scaffold when requested."""
    with _preserve_uncertainty_defaults():
        Q.uncertainty.defaults(enabled=False)
        op_name = "test_const_metric"

        @register_operator(op_name)
        def _const_metric(context, value: float = 1.0):
            # Return deterministic values for all current nodes
            return {node: value for node in context.current_nodes}

        net = _toy_net()
        try:
            result = (
                Q.nodes()
                .compute(op_name, uncertainty=True)
                .execute(net)
            )
            values = result.attributes[op_name]
            sample_val = next(iter(values.values()))
            assert isinstance(sample_val, dict)
            assert sample_val["mean"] == pytest.approx(1.0)
            assert sample_val.get("std", 0.0) == pytest.approx(0.0)
            # certainty marker present
            assert sample_val.get("certainty", 1.0) == 1.0
        finally:
            unregister_operator(op_name)
