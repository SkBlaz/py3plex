"""Metamorphic tests for DSL dynamics simulations."""

from __future__ import annotations

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.dsl import L, Q


@pytest.fixture
def tiny_chain_multilayer():
    """3-node chain on one layer."""
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes(
        [
            {"source": "A", "type": "layer_1"},
            {"source": "B", "type": "layer_1"},
            {"source": "C", "type": "layer_1"},
        ]
    )
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "layer_1",
                "target_type": "layer_1",
            },
            {
                "source": "B",
                "target": "C",
                "source_type": "layer_1",
                "target_type": "layer_1",
            },
        ]
    )
    return net


@pytest.fixture
def tiny_multiplex_two_layer():
    """Two-layer multiplex-like network (counts are over node replicas)."""
    net = multinet.multi_layer_network(directed=False)
    nodes = []
    for node in ("A", "B", "C"):
        nodes.append({"source": node, "type": "layer_1"})
        nodes.append({"source": node, "type": "layer_2"})
    net.add_nodes(nodes)
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "layer_1",
                "target_type": "layer_1",
            },
            {
                "source": "B",
                "target": "C",
                "source_type": "layer_1",
                "target_type": "layer_1",
            },
            {
                "source": "A",
                "target": "C",
                "source_type": "layer_2",
                "target_type": "layer_2",
            },
            {
                "source": "B",
                "target": "C",
                "source_type": "layer_2",
                "target_type": "layer_2",
            },
        ]
    )
    return net


@pytest.fixture
def network_with_isolate():
    """Chain component with one isolated node."""
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes(
        [
            {"source": "A", "type": "layer_1"},
            {"source": "B", "type": "layer_1"},
            {"source": "C", "type": "layer_1"},
            {"source": "Z", "type": "layer_1"},  # isolate
        ]
    )
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "layer_1",
                "target_type": "layer_1",
            },
            {
                "source": "B",
                "target": "C",
                "source_type": "layer_1",
                "target_type": "layer_1",
            },
        ]
    )
    return net


def _run_sir(net, *, beta=0.3, gamma=0.1, seed=42, steps=20, replicates=4, track=None):
    return (
        Q.dynamics("SIR", beta=beta, gamma=gamma)
        .seed_infections(fraction=0.2)
        .run(steps=steps, replicates=replicates, track=track or ["prevalence"])
        .random_seed(seed)
        .execute(net)
    )


def _run_sis(net, *, beta=0.3, mu=0.1, seed=42, steps=20, replicates=4, track=None):
    return (
        Q.dynamics("SIS", beta=beta, mu=mu)
        .seed_infections(fraction=0.2)
        .run(steps=steps, replicates=replicates, track=track or ["prevalence"])
        .random_seed(seed)
        .execute(net)
    )


def _state_counts_cube(result):
    """Return object array shaped (replicate, step) of state-count dicts."""
    return np.asarray(result.data["state_counts"], dtype=object)


def _state_count_series(result, state_code):
    counts = _state_counts_cube(result)
    out = np.zeros(counts.shape, dtype=int)
    for rep in range(counts.shape[0]):
        for step in range(counts.shape[1]):
            out[rep, step] = int(counts[rep, step].get(state_code, 0))
    return out


def _relabel_network(net, mapping):
    relabeled = multinet.multi_layer_network(directed=False)
    relabeled.add_nodes(
        [
            {"source": mapping[node], "type": layer}
            for node, layer in net.core_network.nodes()
        ]
    )
    relabeled.add_edges(
        [
            {
                "source": mapping[u[0]],
                "target": mapping[v[0]],
                "source_type": u[1],
                "target_type": v[1],
            }
            for u, v in net.core_network.edges()
        ]
    )
    return relabeled


def test_sir_determinism_with_fixed_seed(tiny_chain_multilayer):
    sim1 = _run_sir(tiny_chain_multilayer, seed=42, steps=25, replicates=5)
    sim2 = _run_sir(tiny_chain_multilayer, seed=42, steps=25, replicates=5)

    assert sim1.to_pandas("prevalence").equals(sim2.to_pandas("prevalence"))


def test_sis_determinism_with_fixed_seed(tiny_chain_multilayer):
    sim1 = _run_sis(tiny_chain_multilayer, seed=7, steps=25, replicates=5)
    sim2 = _run_sis(tiny_chain_multilayer, seed=7, steps=25, replicates=5)

    assert np.array_equal(sim1.data["prevalence"], sim2.data["prevalence"])


def test_sir_different_seeds_change_trajectory(tiny_chain_multilayer):
    sim1 = _run_sir(tiny_chain_multilayer, seed=1, steps=30, replicates=6)
    sim2 = _run_sir(tiny_chain_multilayer, seed=2, steps=30, replicates=6)

    assert not np.array_equal(sim1.data["prevalence"], sim2.data["prevalence"])


def test_sir_population_conservation(tiny_chain_multilayer):
    sim = _run_sir(
        tiny_chain_multilayer,
        seed=42,
        steps=20,
        replicates=4,
        track=["state_counts"],
    )
    counts = _state_counts_cube(sim)
    n = sim.meta["network_nodes"]
    for rep in range(counts.shape[0]):
        for step in range(counts.shape[1]):
            assert sum(counts[rep, step].values()) == n


def test_sis_population_conservation(tiny_chain_multilayer):
    sim = _run_sis(
        tiny_chain_multilayer,
        seed=42,
        steps=20,
        replicates=4,
        track=["state_counts"],
    )
    counts = _state_counts_cube(sim)
    n = sim.meta["network_nodes"]
    for rep in range(counts.shape[0]):
        for step in range(counts.shape[1]):
            assert sum(counts[rep, step].values()) == n


def test_zero_infection_rate_prevents_spread(tiny_chain_multilayer):
    sim = _run_sir(
        tiny_chain_multilayer,
        beta=0.0,
        gamma=0.1,
        seed=42,
        steps=20,
        replicates=3,
        track=["state_counts"],
    )
    infected = _state_count_series(sim, state_code=1)
    assert infected.max() <= 1


def test_zero_recovery_rate_prevents_recovery(tiny_chain_multilayer):
    sim = _run_sir(
        tiny_chain_multilayer,
        beta=0.3,
        gamma=0.0,
        seed=42,
        steps=20,
        replicates=3,
        track=["state_counts"],
    )
    recovered = _state_count_series(sim, state_code=2)
    assert np.all(recovered == 0)


def test_no_initial_infections_means_no_epidemic(tiny_chain_multilayer):
    sim = (
        Q.dynamics("SIR", beta=0.3, gamma=0.1)
        .seed_infections(fraction=0.0)
        .run(steps=20, replicates=3, track=["prevalence"])
        .random_seed(42)
        .execute(tiny_chain_multilayer)
    )
    assert np.all(np.asarray(sim.data["prevalence"]) == 0.0)


def test_layer_prevalence_aggregates_to_global_prevalence(tiny_multiplex_two_layer):
    sim = (
        Q.dynamics("SIR", beta=0.3, gamma=0.1)
        .on_layers(L["layer_1"] + L["layer_2"])
        .seed_infections(fraction=0.2)
        .run(steps=18, replicates=4, track=["prevalence", "prevalence_by_layer"])
        .random_seed(42)
        .execute(tiny_multiplex_two_layer)
    )

    # Semantics: these are node-replica counts/prevalence, not physical-node counts.
    layer_sizes = {
        "layer_1": 3,
        "layer_2": 3,
    }
    total_nodes = sum(layer_sizes.values())
    global_prev = np.asarray(sim.data["prevalence"])
    layer_prev = np.asarray(sim.data["prevalence_by_layer"], dtype=object)

    for rep in range(global_prev.shape[0]):
        for step in range(global_prev.shape[1]):
            weighted = 0.0
            for layer_name, size in layer_sizes.items():
                weighted += layer_prev[rep, step][layer_name] * size
            assert weighted / total_nodes == pytest.approx(global_prev[rep, step])


def test_isolated_node_cannot_be_infected_when_not_seeded(network_with_isolate):
    sim = (
        Q.dynamics("SIR", beta=1.0, gamma=0.0)
        .seed(Q.nodes().where(degree__gt=0).limit(1))
        .run(steps=20, replicates=3, track=["state_counts"])
        .random_seed(42)
        .execute(network_with_isolate)
    )
    infected = _state_count_series(sim, state_code=1)
    assert infected.max() <= 3  # connected component size; isolated node is never infected


def test_relabeling_nodes_preserves_aggregate_trajectory(tiny_chain_multilayer):
    mapping = {"A": "X", "B": "Y", "C": "Z"}
    relabeled = _relabel_network(tiny_chain_multilayer, mapping)

    sim1 = _run_sir(tiny_chain_multilayer, seed=42, steps=20, replicates=4)
    sim2 = _run_sir(relabeled, seed=42, steps=20, replicates=4)

    assert np.array_equal(sim1.data["prevalence"], sim2.data["prevalence"])


def test_dynamics_provenance_is_complete(tiny_chain_multilayer):
    sim = (
        Q.dynamics("SIR", beta=0.3, gamma=0.1)
        .seed_infections(fraction=0.2)
        .run(steps=15, replicates=4, track=["prevalence"])
        .random_seed(42)
        .execute(tiny_chain_multilayer)
    )
    prov = sim.meta["provenance"]

    assert prov["model"]["name"] == "SIR"
    assert prov["model"]["parameters"]["beta"] == pytest.approx(0.3)
    assert prov["model"]["parameters"]["gamma"] == pytest.approx(0.1)
    assert prov["randomness"]["seed"] == 42
    assert prov["run"]["steps"] == 15
    assert prov["run"]["replicates"] == 4
    assert prov["initial_conditions"]["strategy"] == "fraction"
    assert prov["network_fingerprint"]["node_count"] == sim.meta["network_nodes"]
    assert "py3plex_version" in prov
    assert "backend" in prov
