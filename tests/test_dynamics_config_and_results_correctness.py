"""Correctness coverage for py3plex.dynamics config parsing and result containers."""

import networkx as nx
import numpy as np
import pytest

from py3plex.dynamics.config import _evaluate_expression, build_dynamics_from_config
from py3plex.dynamics.core import DynamicsResult, TemporalGraph


def test_evaluate_expression_allows_scientific_notation_params():
    """Expressions should accept params whose string form uses scientific notation."""
    expr = "1-(1-beta)**infected_neighbors"
    neighbor_counts = {"I": 1}
    params = {"beta": 1e-6}

    prob = _evaluate_expression(expr, neighbor_counts, params)

    assert prob == pytest.approx(1e-6)


def test_build_dynamics_from_config_scientific_notation_does_not_raise_on_step():
    """Config-driven dynamics should step without ValueError for small float params."""
    G = nx.path_graph(2)
    config = {
        "type": "compartmental",
        "compartments": ["S", "I"],
        "parameters": {"beta": 1e-6, "mu": 0.1},
        "rules": {
            "S": "infected_neighbors > 0 ? p=1-(1-beta)**infected_neighbors -> I : stay",
            "I": "stay",
        },
        "initial": {"I": 0.0},
    }

    dynamics = build_dynamics_from_config(G, config)
    dynamics.set_seed(0)

    # Force a neighborhood where infection probability is evaluated (k=1).
    state = {0: "I", 1: "S"}
    new_state = dynamics.step(state, t=0)

    # With beta=1e-6 and seed=0, RNG draw is > beta so infection should not occur.
    assert new_state[1] == "S"


def test_temporal_graph_requires_exactly_one_source():
    with pytest.raises(ValueError):
        TemporalGraph()
    with pytest.raises(ValueError):
        TemporalGraph(snapshots=[nx.Graph()], get_graph_fn=lambda t: nx.Graph())


def test_temporal_graph_snapshots_indexing_and_len():
    G0 = nx.path_graph(2)
    G1 = nx.path_graph(3)
    temporal = TemporalGraph(snapshots=[G0, G1])

    assert len(temporal) == 2
    assert temporal.get_graph(0) is G0
    assert temporal.get_graph(1) is G1
    with pytest.raises(IndexError):
        temporal.get_graph(2)


def test_dynamics_result_state_counts_and_prevalence_invariants():
    trajectory = [
        {0: "S", 1: "I"},
        {0: "I", 1: "I"},
        {0: "R", 1: "I"},
    ]
    result = DynamicsResult(trajectory)

    prevalence = result.get_measure("prevalence")
    assert np.allclose(prevalence, np.array([0.5, 1.0, 0.5]))

    counts = result.get_measure("state_counts")
    assert set(counts) == {"S", "I", "R"}
    assert np.array_equal(counts["S"], np.array([1, 0, 0]))
    assert np.array_equal(counts["I"], np.array([1, 2, 1]))
    assert np.array_equal(counts["R"], np.array([0, 0, 1]))

    for t in range(len(trajectory)):
        assert counts["S"][t] + counts["I"][t] + counts["R"][t] == 2

    with pytest.raises(ValueError, match="Unknown measure"):
        result.get_measure("not_a_measure")


def test_dynamics_result_empty_trajectory_rejects_measures():
    result = DynamicsResult([])
    with pytest.raises(ValueError, match="Empty trajectory"):
        result.get_measure("prevalence")


def test_property_evaluate_expression_matches_reference_formula():
    hypothesis = pytest.importorskip("hypothesis")
    strategies = pytest.importorskip("hypothesis.strategies")

    @hypothesis.given(
        beta=strategies.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        k=strategies.integers(min_value=0, max_value=10),
    )
    @hypothesis.settings(max_examples=50)
    def check(beta, k):
        expr = "1-(1-beta)**infected_neighbors"
        neighbor_counts = {"I": k}
        params = {"beta": beta}
        prob = _evaluate_expression(expr, neighbor_counts, params)
        ref = 1.0 - (1.0 - beta) ** k
        assert prob == pytest.approx(ref)
        assert 0.0 <= prob <= 1.0

    check()

