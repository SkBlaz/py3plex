"""Regression tests for benchmark runner seed inheritance."""

from types import SimpleNamespace

import pytest

from py3plex.algorithms.community_detection.autocommunity import AutoCommunity
from py3plex.benchmarks.runners import AutoCommunityRunner


@pytest.mark.parametrize("n_samples", [2, 5])
@pytest.mark.parametrize("seed, overrides, expected_seed", [
    (0, {}, 0),
    (7, {}, 7),
    (None, {}, 42),
    (0, {"seed": 13}, 13),
    (7, {"seed": 0}, 0),
    (None, {"seed": 0}, 0),
    (0, {"seed": None}, None),
])
def test_autocommunity_uq_seed_inheritance(
    monkeypatch, seed, overrides, expected_seed, n_samples
):
    """Check the real fluent configuration while substituting algorithm execution."""
    network = object()
    received = []
    uq_spec = {"method": "seed", "n_samples": n_samples, **overrides}
    original_spec = uq_spec.copy()

    def capture_execute(builder, supplied_network):
        assert supplied_network is network
        received.append(builder)
        return SimpleNamespace(consensus_partition={"A": 0}, algorithm={"name": "stub"})

    monkeypatch.setattr(AutoCommunity, "execute", capture_execute)
    result = AutoCommunityRunner().run(network, seed=seed, uq_spec=uq_spec, mode="pareto")

    assert len(received) == 1
    assert received[0]._seed == (0 if seed is None else seed)
    assert received[0]._uq_config == {
        "method": "seed", "n_samples": n_samples, "seed": expected_seed,
    }
    assert uq_spec == original_spec
    assert result.partition == {"A": 0}


@pytest.mark.parametrize("n_samples", [0, 1])
def test_autocommunity_single_run_does_not_enable_uq(monkeypatch, n_samples):
    def capture_execute(builder, network):
        assert builder._seed == 0
        assert builder._uq_config is None
        return SimpleNamespace(consensus_partition={}, algorithm={"name": "stub"})

    monkeypatch.setattr(AutoCommunity, "execute", capture_execute)
    AutoCommunityRunner().run(object(), seed=0, uq_spec={"n_samples": n_samples})
