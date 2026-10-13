"""Exact finite-population oracles for sampled betweenness scaling."""

import math
from itertools import product

import networkx as nx
import pytest

from py3plex.algorithms.centrality import approx_betweenness as implementation
from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import Q


class CensusRandom:
    """Draw every source once, eliminating Monte Carlo error."""

    def __init__(self, seed=None):
        self.next_source = 0

    def randrange(self, size):
        result = self.next_source % size
        self.next_source += 1
        return result


@pytest.mark.parametrize("directed,normalized,weighted", product([False, True], repeat=3))
def test_source_census_equals_exact_betweenness(monkeypatch, directed, normalized, weighted):
    graph = nx.DiGraph() if directed else nx.Graph()
    graph.add_weighted_edges_from([(0, 1, 1), (1, 2, 1), (0, 2, 4), (2, 3, 2)])
    graph.add_node(4)  # Include an unreachable source in the sampling population.
    monkeypatch.setattr(implementation.random, "Random", CensusRandom)
    weight = "weight" if weighted else None
    actual, _ = implementation.approximate_betweenness_sampling(
        graph, n_samples=len(graph), normalized=normalized, weight=weight)
    expected = nx.betweenness_centrality(graph, normalized=normalized, weight=weight)
    assert actual == pytest.approx(expected)


@pytest.mark.parametrize("normalized", [False, True])
def test_dsl_source_census_matches_exact(monkeypatch, normalized):
    network = multi_layer_network(directed=True)
    network.add_edges([["a", "L", "b", "L", 1], ["b", "L", "c", "L", 1]],
                      input_type="list")
    monkeypatch.setattr(implementation.random, "Random", CensusRandom)
    result = Q.nodes().compute("betweenness_centrality", approx=True, n_samples=3,
                               seed=0, normalized=normalized).execute(network)
    expected = nx.betweenness_centrality(network.core_network, normalized=normalized)
    assert result.attributes["betweenness_centrality"] == pytest.approx(expected)


@pytest.mark.parametrize("directed,normalized", product([False, True], repeat=2))
def test_reported_stderr_matches_source_distribution(monkeypatch, directed, normalized):
    # For a three-node path, the center's dependency is 1 at each endpoint
    # source and 0 at the center source. The population variance is 2/9.
    graph = nx.path_graph(3, create_using=nx.DiGraph if directed else nx.Graph)
    if directed:
        graph.add_edges_from([(1, 0), (2, 1)])
    monkeypatch.setattr(implementation.random, "Random", CensusRandom)
    errors = []
    for budget in [3, 12]:
        scores, stderr = implementation.approximate_betweenness_sampling(
            graph, n_samples=budget, normalized=normalized, diagnostics=True)
        multiplier = 3.0 if directed else 1.5
        if normalized:
            multiplier *= 0.5 if directed else 1.0
        assert stderr[1] == pytest.approx(multiplier * math.sqrt((2 / 9) / budget))
        assert scores == pytest.approx(nx.betweenness_centrality(graph, normalized=normalized))
        errors.append(stderr[1])
    assert errors[0] / errors[1] == pytest.approx(2.0)
