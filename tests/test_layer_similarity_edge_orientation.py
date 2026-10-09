"""Edge overlap must use the source graph's direction semantics."""

from types import SimpleNamespace

import networkx as nx
import pytest

from py3plex.algorithms.layer_similarity import (
    all_pairs_jaccard_similarity,
    jaccard_layer_similarity,
    layer_correlation_matrix,
)


@pytest.mark.parametrize('graph_type', [nx.Graph, nx.MultiGraph, nx.DiGraph, nx.MultiDiGraph])
def test_edge_jaccard_respects_direction(graph_type):
    graph = graph_type()
    # Opposite insertion order makes NetworkX emit reversed endpoints in L2.
    graph.add_edge(('A', 'L1'), ('B', 'L1'))
    graph.add_edge(('B', 'L2'), ('A', 'L2'))
    graph.add_edge(('A', 'L1'), ('A', 'L1'))
    graph.add_edge(('A', 'L2'), ('A', 'L2'))
    if graph.is_multigraph():
        graph.add_edge(('A', 'L1'), ('B', 'L1'))
    network = SimpleNamespace(core_network=graph)
    expected = 1 / 3 if graph.is_directed() else 1.0
    assert jaccard_layer_similarity(network, 'L1', 'L2', element='edges') == expected
    assert all_pairs_jaccard_similarity(network, element='edges')[('L1', 'L2')] == expected
    matrix, layers = layer_correlation_matrix(network, method='jaccard', element='edges')
    assert matrix[layers.index('L1'), layers.index('L2')] == expected


def test_undirected_edge_jaccard_accepts_mixed_node_types():
    graph = nx.Graph()
    graph.add_edge((1, 'L1'), ('A', 'L1'))
    graph.add_edge(('A', 'L2'), (1, 'L2'))
    assert jaccard_layer_similarity(
        SimpleNamespace(core_network=graph), 'L1', 'L2', element='edges'
    ) == 1.0
