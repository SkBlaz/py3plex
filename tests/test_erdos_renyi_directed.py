"""Directed Erdős–Rényi null models must sample ordered node pairs."""

import networkx as nx
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.nullmodels import erdos_renyi_model, generate_null_model


def make_network(directed, edges, nodes=None):
    network = multi_layer_network(directed=directed, verbose=False)
    if nodes is None:
        nodes = [(i, "L") for i in range(4)]
    network.add_nodes([{"source": node, "type": layer} for node, layer in nodes])
    network.add_edges(
        [
            {
                "source": nodes[u][0],
                "source_type": nodes[u][1],
                "target": nodes[v][0],
                "target_type": nodes[v][1],
            }
            for u, v in edges
        ]
    )
    return network


def test_complete_directed_network_keeps_both_orientations():
    network = make_network(True, [(u, v) for u in range(4) for v in range(4) if u != v])
    randomized = erdos_renyi_model(network, seed=42)
    graph = randomized.core_network
    assert graph.is_directed()
    assert graph.number_of_edges() == 12
    assert set(graph.edges()) == set(network.core_network.edges())


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("seed", [0, 7, 42])
def test_sparse_model_matches_networkx_sampling_with_input_density(directed, seed):
    nodes = [("A", "social"), ("B", "social"), ("A", "work"), ("C", "work")]
    network = make_network(directed, [(0, 1), (2, 0), (3, 2)], nodes)
    original = network.core_network.copy()
    # Density on a simple digraph counts ordered pairs; reciprocal arcs are independent.
    expected = nx.gnp_random_graph(
        4, nx.density(original), seed=seed, directed=directed
    )
    expected = nx.relabel_nodes(expected, dict(enumerate(nodes)))
    graph = erdos_renyi_model(network, seed=seed).core_network
    assert graph.is_directed() == directed
    assert set(graph.nodes()) == set(nodes)
    assert set(graph.edges()) == set(expected.edges())
    assert nx.number_of_selfloops(graph) == 0
    assert set(network.core_network.edges()) == set(original.edges())
    assert set(network.core_network.nodes()) == set(original.nodes())


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("n_nodes", [1, 4])
def test_edgeless_network_retains_isolated_nodes(directed, n_nodes):
    network = make_network(directed, [], [(i, "L") for i in range(n_nodes)])
    graph = erdos_renyi_model(network, seed=42).core_network
    assert graph.is_directed() == directed
    assert graph.number_of_nodes() == n_nodes
    assert graph.number_of_edges() == 0


def test_executor_keeps_complete_directed_samples_complete():
    network = make_network(True, [(u, v) for u in range(4) for v in range(4) if u != v])
    result = generate_null_model(
        network, model="erdos_renyi", num_samples=2, seed=42, n_jobs=1
    )
    assert result.num_samples == 2
    for sample in result:
        assert sample.core_network.is_directed()
        assert set(sample.core_network.edges()) == set(network.core_network.edges())
