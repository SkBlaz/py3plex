import networkx as nx
import pytest

from py3plex.algorithms.advanced_random_generators import multilayer_erdos_renyi
from py3plex.algorithms.centrality.approx_pagerank import approximate_pagerank_power_iteration


def test_seeded_erdos_renyi_layers_get_distinct_draws():
    def layers():
        graph = multilayer_erdos_renyi(25, 0.2, 3, seed=42)
        return [
            {frozenset((u, v)) for (u, source), (v, target) in graph.edges()
             if source == target == layer}
            for layer in range(3)
        ]

    draws = layers()
    assert draws == layers()
    assert len({frozenset(edges) for edges in draws}) == 3


def test_approximate_pagerank_matches_weighted_personalized_reference():
    graph = nx.MultiDiGraph()
    graph.add_weighted_edges_from([(0, 1, 2), (0, 1, 3), (0, 2, 1), (1, 0, 1)])
    preference = {0: 2, 2: 1}
    expected = nx.pagerank(graph, personalization=preference, tol=1e-12, max_iter=1000)
    actual, _ = approximate_pagerank_power_iteration(
        graph, personalization=preference, tol=1e-12, max_iter=1000
    )
    assert actual == pytest.approx(expected, abs=1e-10)
