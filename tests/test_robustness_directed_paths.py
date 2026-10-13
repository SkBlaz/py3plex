"""Analytical checks for robustness over reachable directed pairs."""

import math

import networkx as nx
import pytest

from py3plex.centrality import robustness_centrality
from py3plex.centrality.robustness import _compute_avg_shortest_path
from py3plex.core.multinet import multi_layer_network


@pytest.mark.parametrize("graph_type", [nx.DiGraph, nx.MultiDiGraph, nx.Graph, nx.MultiGraph])
def test_average_path_length_counts_only_reachable_pairs(graph_type):
    net = multi_layer_network(directed=graph_type().is_directed(), verbose=False)
    net.core_network = graph_type()
    net.core_network.add_edges_from([("a", "b"), ("b", "c"), ("d", "e")])
    net.core_network.add_node("isolated")
    # Chain contributes distances 1, 1, 2; separate edge contributes 1.
    # Undirected graphs double both the distance sum and the pair count.
    assert _compute_avg_shortest_path(net) == pytest.approx(5 / 4)


def test_directed_robustness_matches_reachable_pair_distance_changes():
    net = multi_layer_network(directed=True, verbose=False)
    net.add_edges([["a", "L", "b", "L", 1], ["b", "L", "c", "L", 1]], input_type="list")
    before = net.core_network.copy()
    scores = robustness_centrality(net, metric="avg_shortest_path", seed=42)
    assert scores[("a", "L")] == pytest.approx(-1 / 3)
    assert scores[("c", "L")] == pytest.approx(-1 / 3)
    assert math.isinf(scores[("b", "L")]) and scores[("b", "L")] > 0
    assert nx.utils.graphs_equal(net.core_network, before)


def test_strongly_connected_directed_average_matches_networkx():
    net = multi_layer_network(directed=True, verbose=False)
    net.core_network = nx.DiGraph([(0, 1), (1, 2), (2, 0)])
    assert _compute_avg_shortest_path(net) == pytest.approx(
        nx.average_shortest_path_length(net.core_network)
    )
