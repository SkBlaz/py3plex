"""Weighted sampling must accept hashable node IDs without ordering them."""

import networkx as nx
import pytest

from py3plex.algorithms.centrality.approx_betweenness import (
    _brandes_sssp_weighted,
    approximate_betweenness_sampling,
)
from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import Q


LABELS = [
    [0, 1, "two", "three"],
    [(0, "L"), (1, "L"), ("two", "L"), ("three", "L")],
    [("a", 0), ("b", 0), ("b", "L"), ("c", "L")],
]


def diamond(labels, directed):
    graph = nx.DiGraph() if directed else nx.Graph()
    a, b, c, d = labels
    graph.add_weighted_edges_from([(a, b, 1), (a, c, 1), (b, d, 1), (c, d, 1)])
    return graph


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("labels", LABELS)
def test_weighted_sssp_with_tied_mixed_identifiers(labels, directed):
    graph = diamond(labels, directed)
    source = labels[0]
    order, predecessors, counts, distances = _brandes_sssp_weighted(graph, source)
    assert distances == nx.single_source_dijkstra_path_length(graph, source)
    assert len(order) == len(set(order)) == len(graph)
    for node in graph:
        paths = list(nx.all_shortest_paths(graph, source, node, weight="weight"))
        assert counts[node] == len(paths)
        assert set(predecessors[node]) == {path[-2] for path in paths if len(path) > 1}


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("labels", LABELS)
def test_sampling_matches_isomorphic_ordered_identifiers(labels, directed):
    graph = diamond(labels, directed)
    mapping = {node: index for index, node in enumerate(graph)}
    reference = nx.relabel_nodes(graph, mapping)
    actual, errors = approximate_betweenness_sampling(
        graph, n_samples=40, seed=0, weight="weight", diagnostics=True)
    expected, expected_errors = approximate_betweenness_sampling(
        reference, n_samples=40, seed=0, weight="weight", diagnostics=True)
    assert {mapping[node]: value for node, value in actual.items()} == pytest.approx(expected)
    assert {mapping[node]: value for node, value in errors.items()} == pytest.approx(expected_errors)


@pytest.mark.parametrize("directed", [False, True])
def test_dsl_weighted_sampling_with_mixed_replicas(directed):
    labels = LABELS[1]
    network = multi_layer_network(directed=directed)
    network.core_network = diamond(labels, directed)
    result = Q.nodes().compute("betweenness_centrality", approx=True, n_samples=40,
                               seed=0, weight="weight").execute(network)
    reference = nx.relabel_nodes(network.core_network, {node: i for i, node in enumerate(labels)})
    expected, _ = approximate_betweenness_sampling(reference, 40, seed=0, weight="weight")
    assert {i: result.attributes["betweenness_centrality"][node]
            for i, node in enumerate(labels)} == pytest.approx(expected)
