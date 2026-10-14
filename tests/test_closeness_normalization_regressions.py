"""A census of landmarks must reproduce the exact closeness definition."""

import math

import networkx as nx
import pytest

from py3plex.algorithms.centrality import approx_closeness
from py3plex.core import multinet
from py3plex.dsl import Q


@pytest.fixture
def landmark_census(monkeypatch):
    class CensusRandom:
        def __init__(self, seed):
            self.index = 0

        def randrange(self, n):
            value = self.index % n
            self.index += 1
            return value

    monkeypatch.setattr(approx_closeness.random, 'Random', CensusRandom)
    # Isolate estimator correctness from the separate allocation policy.
    monkeypatch.setattr(approx_closeness, '_allocate_landmarks',
                        lambda components, budget: [len(c) if len(c) > 1 else 0
                                                    for c in components])


@pytest.mark.parametrize('graph_type', [nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph])
@pytest.mark.parametrize('weight', [None, 'cost'])
@pytest.mark.parametrize('disconnected', [False, True])
def test_landmark_census_matches_networkx(landmark_census, graph_type, weight, disconnected):
    simple = nx.path_graph(4)
    for u, v in simple.edges:
        simple[u][v]['cost'] = u + 1
    if disconnected:
        simple.add_edge(10, 11, cost=2)
        simple.add_node('isolated')
    # Bidirectional graphs isolate normalization from inward/outward semantics.
    graph = graph_type(simple.to_directed() if graph_type().is_directed() else simple)
    values, errors = approx_closeness.approximate_closeness_landmarks(
        graph, n_landmarks=len(graph), seed=0, weight=weight, diagnostics=True
    )
    assert values == pytest.approx(nx.closeness_centrality(graph, distance=weight))
    assert all(math.isfinite(value) and value >= 0 for value in errors.values())


@pytest.mark.parametrize('isolates', [0, 2])
def test_diagnostics_exclude_self_and_apply_component_scale(landmark_census, isolates):
    graph = nx.path_graph(3)
    graph.add_nodes_from(range(10, 10 + isolates))
    values, errors = approx_closeness.approximate_closeness_landmarks(
        graph, n_landmarks=3, diagnostics=True
    )
    # Endpoint distances to the other nodes are [1, 2]: mean=1.5, SE(mean)=0.5.
    scale = 2 / (len(graph) - 1)
    assert values[0] == pytest.approx(scale / 1.5)
    assert errors[0] == pytest.approx(scale * 0.5 / 1.5 ** 2)
    assert errors[1] == 0  # Both non-self distances from the middle node are 1.


def test_dsl_landmark_census_matches_exact_metric(landmark_census):
    network = multinet.multi_layer_network(directed=False)
    network.add_edges([['a', 'social', 'b', 'social', 1],
                       ['b', 'social', 'c', 'social', 1]], input_type='list')
    network.add_nodes([{'source': 'isolated', 'type': 'work'}])
    exact = Q.nodes().compute('closeness_centrality').execute(network)
    approx = Q.nodes().compute('closeness_centrality', approx=True,
                               n_landmarks=4, seed=0).execute(network)
    assert approx.attributes['closeness_centrality'] == pytest.approx(
        exact.attributes['closeness_centrality']
    )
