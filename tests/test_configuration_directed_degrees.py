"""Directed configuration null models must preserve each replica's in/out degrees."""

from collections import Counter
import copy

import networkx as nx
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import N
from py3plex.nullmodels import configuration_model, generate_null_model


def make_sink_network():
    network = multi_layer_network(directed=True, verbose=False)
    nodes = [("sink", "social"), ("b", "work"), ("c", 7), ("isolate", "social")]
    network.add_nodes([{"source": node, "type": layer} for node, layer in nodes])
    for source, layer in nodes[1:3]:
        network.add_edges(
            [
                {
                    "source": source,
                    "source_type": layer,
                    "target": "sink",
                    "target_type": "social",
                }
            ]
        )
    return network


def assert_degrees_preserved(original, randomized):
    assert randomized.is_directed()
    assert set(randomized.nodes()) == set(original.nodes())
    assert dict(randomized.in_degree()) == dict(original.in_degree())
    assert dict(randomized.out_degree()) == dict(original.out_degree())
    assert randomized.number_of_edges() == original.number_of_edges()


@pytest.mark.parametrize("seed", [0, 7, 42])
@pytest.mark.parametrize("networkx_input", [False, True])
def test_directed_sources_sinks_and_isolates_keep_their_degrees(seed, networkx_input):
    network = make_sink_network()
    original = copy.deepcopy(network.core_network)
    argument = network.core_network if networkx_input else network
    sampled = configuration_model(argument, seed=seed).core_network
    assert_degrees_preserved(original, sampled)
    assert nx.utils.graphs_equal(network.core_network, original)


@pytest.mark.parametrize("frontend", ["executor", "dsl"])
def test_configuration_frontends_preserve_directed_degrees(frontend):
    network = make_sink_network()
    if frontend == "executor":
        samples = generate_null_model(
            network, model="configuration", num_samples=2, seed=42, n_jobs=1
        )
    else:
        samples = N.configuration().samples(2).seed(42).execute(network)
    assert len(samples) == 2
    for sample in samples:
        assert_degrees_preserved(network.core_network, sample.core_network)


def test_directed_configuration_randomizes_instead_of_falling_back_to_copy():
    network = multi_layer_network(directed=True, verbose=False)
    network.add_edges(
        [
            {"source": u, "source_type": "L", "target": v, "target_type": "L"}
            for u in ["a", "b", "c"]
            for v in ["a", "b", "c"]
            if u != v
        ]
    )
    original = network.core_network
    samples = [
        configuration_model(network, seed=seed).core_network for seed in [0, 1, 2]
    ]
    for sample in samples:
        assert_degrees_preserved(original, sample)
    assert any(
        Counter(sample.edges()) != Counter(original.edges()) for sample in samples
    )
    first = configuration_model(network, seed=42).core_network
    second = configuration_model(network, seed=42).core_network
    assert Counter(first.edges()) == Counter(second.edges())


@pytest.mark.parametrize("directed", [False, True])
def test_configuration_degree_controls(directed):
    network = multi_layer_network(directed=directed, verbose=False)
    network.add_edges(
        [
            {"source": u, "source_type": "L", "target": v, "target_type": "L"}
            for u, v in [("a", "b"), ("b", "c"), ("c", "a")]
        ]
    )
    network.add_nodes([{"source": "isolate", "type": "L"}])
    sampled = configuration_model(network, seed=42).core_network
    assert sampled.is_directed() == directed
    if directed:
        assert_degrees_preserved(network.core_network, sampled)
    else:
        assert dict(sampled.degree()) == dict(network.core_network.degree())
