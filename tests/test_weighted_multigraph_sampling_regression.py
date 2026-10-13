"""Parallel edge weights must participate in approximate shortest paths."""

import networkx as nx
import pytest

from py3plex.algorithms.centrality.approx_betweenness import (
    _brandes_sssp_weighted,
    approximate_betweenness_sampling,
)
from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import Q


def weighted_graph(directed, weight):
    graph = nx.MultiDiGraph() if directed else nx.MultiGraph()
    graph.add_edge(0, 1, key="expensive", **{weight: 7})
    graph.add_edge(0, 1, key="cheap", **{weight: 2})
    graph.add_edge(1, 2, **{weight: 3})
    graph.add_edge(0, 2, **{weight: 9})
    graph.add_edge(2, 3)  # Missing weights have unit distance.
    return graph


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("weight", ["weight", "cost"])
def test_weighted_multigraph_shortest_path_oracle(directed, weight):
    graph = weighted_graph(directed, weight)
    for source in graph:
        order, predecessors, counts, distances = _brandes_sssp_weighted(graph, source, weight)
        expected = nx.single_source_dijkstra_path_length(graph, source, weight=weight)
        assert distances == {node: expected.get(node, float("inf")) for node in graph}
        assert set(order) == set(expected)
        for node in expected:
            paths = list(nx.all_shortest_paths(graph, source, node, weight=weight))
            assert counts[node] == len(paths)
            assert set(predecessors[node]) == {path[-2] for path in paths if len(path) > 1}


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("weight", ["weight", "cost"])
def test_weighted_sampling_matches_minimum_edge_projection(directed, weight):
    graph = weighted_graph(directed, weight)
    reference = nx.DiGraph() if directed else nx.Graph()
    reference.add_nodes_from(graph)
    for u, v, data in graph.edges(data=True):
        value = data.get(weight, 1)
        if not reference.has_edge(u, v) or value < reference[u][v][weight]:
            reference.add_edge(u, v, **{weight: value})
    actual, errors = approximate_betweenness_sampling(
        graph, 40, seed=0, weight=weight, diagnostics=True)
    expected, expected_errors = approximate_betweenness_sampling(
        reference, 40, seed=0, weight=weight, diagnostics=True)
    assert actual == pytest.approx(expected)
    assert errors == pytest.approx(expected_errors)


@pytest.mark.parametrize("directed", [False, True])
def test_public_multilayer_weighted_approximation(directed):
    network = multi_layer_network(directed=directed)
    network.add_edges([[0, "L", 1, "L", 7], [0, "L", 1, "L", 2],
                       [1, "L", 2, "L", 3], [0, "L", 2, "L", 9],
                       [2, "L", 3, "L", 1]], input_type="list")
    assert network.core_network.is_multigraph()
    result = Q.nodes().compute("betweenness_centrality", approx=True, n_samples=40,
                               seed=0, weight="weight").execute(network)
    reference = nx.DiGraph() if directed else nx.Graph()
    reference.add_weighted_edges_from([(0, 1, 2), (1, 2, 3), (0, 2, 9), (2, 3, 1)])
    expected, _ = approximate_betweenness_sampling(reference, 40, seed=0, weight="weight")
    assert {node: result.attributes["betweenness_centrality"][(node, "L")]
            for node in reference} == pytest.approx(expected)
