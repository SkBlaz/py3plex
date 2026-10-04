"""Undirected PageRank counts a self-loop as one outgoing transition."""

import networkx as nx
import pytest

from py3plex.algorithms.temporal import streaming_pagerank
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork


def make_network(directed, self_loop):
    net = TemporalMultiLayerNetwork(directed=directed)
    for source, target, time in [("A", "B", 100.0), ("B", "C", 200.0), ("C", "A", 200.0)]:
        net.add_edge(source, "L", target, "L", t=time)
    if self_loop:
        net.add_edge("A", "L", "A", "L", t=150.0)
    return net


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("self_loop", [False, True])
@pytest.mark.parametrize("normalize", [False, True])
@pytest.mark.parametrize("seeded", [False, True])
@pytest.mark.parametrize("alpha", [0.2, 0.85])
@pytest.mark.parametrize("iterations", [1, 3])
def test_self_loop_matches_independent_transition_calculation(
    directed, self_loop, normalize, seeded, alpha, iterations
):
    net = make_network(directed, self_loop)
    a, b, c = [(name, "L") for name in "ABC"]
    nodes = [a, b, c]
    initial = {a: 0.6, b: 0.3, c: 0.1} if seeded else None
    original = initial.copy() if initial is not None else None
    expected = initial.copy() if seeded else dict.fromkeys(nodes, 1 / 3)
    outgoing = {a: [b], b: [c], c: [a]} if directed else {a: [b, c], b: [a, c], c: [a, b]}
    if self_loop:
        outgoing[a].append(a)
    for _ in range(iterations):
        updated = dict.fromkeys(nodes, (1 - alpha) / len(nodes))
        for source, targets in outgoing.items():
            for target in targets:
                updated[target] += alpha * expected[source] / len(targets)
        expected = updated

    windows = list(streaming_pagerank(
        net, alpha=alpha, initial_scores=initial, window_size=100.0,
        normalize=normalize, max_iter_per_window=iterations, tolerance=0,
    ))
    assert len(windows) == 1
    assert windows[0][2] == pytest.approx(expected)
    assert sum(windows[0][2].values()) == pytest.approx(1.0)
    assert initial == original


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("self_loop", [False, True])
@pytest.mark.parametrize("normalize", [False, True])
def test_self_loop_stationary_scores_match_networkx(directed, self_loop, normalize):
    net = make_network(directed, self_loop)
    graph = nx.DiGraph() if directed else nx.Graph()
    graph.add_edges_from([(("A", "L"), ("B", "L")), (("B", "L"), ("C", "L")), (("C", "L"), ("A", "L"))])
    if self_loop:
        graph.add_edge(("A", "L"), ("A", "L"))
    expected = nx.pagerank(graph, alpha=0.85, tol=1e-12, max_iter=500)
    scores = list(streaming_pagerank(
        net, window_size=100.0, normalize=normalize,
        max_iter_per_window=300, tolerance=0,
    ))[0][2]
    assert scores == pytest.approx(expected, abs=1e-10)
