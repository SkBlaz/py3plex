import networkx as nx
import pytest

from types import SimpleNamespace

from py3plex.dynamics.ast import InitialSpec, SimulationStmt
from py3plex.dynamics.errors import MissingInitialConditionError, SimulationConfigError, UnknownMeasureError
from py3plex.dynamics.executor import run_simulation


def _network_with_layered_nodes(n=2, layer="L"):
    """Build a minimal multilayer-style network object with core_network."""
    g = nx.Graph()
    for i in range(n):
        g.add_node((f"n{i}", layer))
    if n > 1:
        g.add_edge(("n0", layer), (f"n{n-1}", layer))
    return SimpleNamespace(core_network=g)


def test_missing_initial_condition_detected_by_executor():
    """SimulationStmt without required initial keys should fail fast."""
    net = _network_with_layered_nodes()
    stmt = SimulationStmt(process_name="SIS", steps=2, measures=["prevalence"])

    with pytest.raises(MissingInitialConditionError):
        run_simulation(net, stmt)


def test_invalid_step_count_raises_config_error():
    """steps < 1 must raise SimulationConfigError even before execution."""
    net = _network_with_layered_nodes()
    stmt = SimulationStmt(
        process_name="SIS",
        steps=0,
        measures=["prevalence"],
        initial={"infected": InitialSpec(constant=1)},
    )

    with pytest.raises(SimulationConfigError, match="steps"):
        run_simulation(net, stmt)


def test_unknown_measure_lists_known_options():
    """Unknown measures should raise with helpful listing."""
    net = _network_with_layered_nodes()
    stmt = SimulationStmt(
        process_name="SIS",
        steps=1,
        measures=["bogus_measure"],
        initial={"infected": InitialSpec(constant=1)},
    )

    with pytest.raises(UnknownMeasureError, match="bogus_measure"):
        run_simulation(net, stmt)


def test_empty_network_returns_warning_and_empty_data():
    """Executor should return empty result when network has no nodes."""
    net = SimpleNamespace(core_network=None)
    stmt = SimulationStmt(
        process_name="SIS",
        steps=1,
        measures=["prevalence"],
        initial={"infected": InitialSpec(constant=0)},
        seed=7,
    )

    result = run_simulation(net, stmt)

    assert result.meta.get("warning") == "Empty network"
    assert result.data["prevalence"].size == 0


def test_named_initial_infection_targets_specific_node():
    """InitialSpec with constant node id should infect that node replica."""
    net = _network_with_layered_nodes(n=2, layer="L")
    stmt = SimulationStmt(
        process_name="SIS",
        steps=1,
        measures=["prevalence"],
        initial={"infected": InitialSpec(constant="n1")},
        params={"beta": 0.0, "mu": 0.0},
        seed=3,
    )

    result = run_simulation(net, stmt)

    assert result.data["prevalence"].shape == (1, 1)
    assert result.data["prevalence"][0, 0] == pytest.approx(0.5)


def test_fractional_initial_infection_infects_at_least_one_node():
    """Very small infected fraction should still infect at least one node."""
    net = _network_with_layered_nodes(n=5, layer="L")
    stmt = SimulationStmt(
        process_name="SIS",
        steps=1,
        measures=["prevalence"],
        initial={"infected": InitialSpec(constant=0.01)},
        params={"beta": 0.0, "mu": 0.0},
        seed=11,
    )

    result = run_simulation(net, stmt)

    # One infected out of five nodes -> prevalence 0.2
    assert result.data["prevalence"].shape == (1, 1)
    assert result.data["prevalence"][0, 0] == pytest.approx(0.2)


def test_fractional_initial_infection_zero_keeps_all_susceptible():
    """0.0 fraction should infect nobody (not force a 1-node infection)."""
    net = _network_with_layered_nodes(n=3, layer="L")
    stmt = SimulationStmt(
        process_name="SIS",
        steps=1,
        measures=["prevalence"],
        initial={"infected": InitialSpec(constant=0.0)},
        params={"beta": 0.0, "mu": 0.0},
        seed=0,
    )

    result = run_simulation(net, stmt)

    assert result.data["prevalence"].shape == (1, 1)
    assert result.data["prevalence"][0, 0] == pytest.approx(0.0)
