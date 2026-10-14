"""Approximate closeness must use inward distances like the exact public metric."""

import networkx as nx
import pytest

from py3plex.algorithms.centrality.approx_closeness import approximate_closeness_landmarks
from py3plex.core import multinet
from py3plex.dsl import Q


@pytest.mark.parametrize('graph_type', [nx.DiGraph, nx.MultiDiGraph])
@pytest.mark.parametrize('weight', [None, 'cost'])
@pytest.mark.parametrize('diagnostics', [False, True])
def test_directed_source_sink_closeness(graph_type, weight, diagnostics):
    graph = graph_type()
    graph.add_edge('source', 'middle', cost=2)
    graph.add_edge('middle', 'sink', cost=3)
    graph.add_node('isolated')
    before = list(graph.edges(data=True))
    exact = nx.closeness_centrality(graph, distance=weight)
    values, errors = approximate_closeness_landmarks(
        graph, n_landmarks=200, seed=42, weight=weight, diagnostics=diagnostics
    )
    assert values['source'] == exact['source'] == 0
    assert values['isolated'] == exact['isolated'] == 0
    assert values['sink'] > 0
    assert values['middle'] > 0
    assert list(graph.edges(data=True)) == before
    if diagnostics:
        assert errors['source'] == errors['isolated'] == 0
    else:
        assert errors is None


def test_dsl_approximate_and_exact_closeness_agree_on_direction():
    network = multinet.multi_layer_network(directed=True)
    network.add_edges([
        ['source', 'social', 'middle', 'social', 1],
        ['middle', 'social', 'sink', 'social', 1],
    ], input_type='list')
    exact = Q.nodes().compute('closeness_centrality').execute(network)
    approx = Q.nodes().compute(
        'closeness_centrality', approx=True, n_landmarks=200, seed=42
    ).execute(network)
    assert approx.attributes['closeness_centrality'][('source', 'social')] == 0
    assert exact.attributes['closeness_centrality'][('source', 'social')] == 0
    assert approx.attributes['closeness_centrality'][('sink', 'social')] > 0
    assert exact.attributes['closeness_centrality'][('sink', 'social')] > 0
