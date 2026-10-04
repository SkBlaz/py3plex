"""PageRank must redistribute scores held by nodes without outgoing edges."""

import networkx as nx
import pytest

from py3plex.algorithms.temporal import streaming_pagerank
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("cycle", [False, True])
@pytest.mark.parametrize("normalize", [False, True])
@pytest.mark.parametrize("seeded", [False, True])
@pytest.mark.parametrize("alpha", [0.2, 0.85])
@pytest.mark.parametrize("iterations", [1, 3])
def test_dangling_mass_matches_independent_power_iterations(
    directed, cycle, normalize, seeded, alpha, iterations
):
    net = TemporalMultiLayerNetwork(directed=directed)
    net.add_edge("A", "L", "B", "L", t=100.0)
    net.add_edge("B", "L", "C", "L", t=200.0)
    if cycle:
        net.add_edge("C", "L", "A", "L", t=150.0)

    nodes = [(name, "L") for name in "ABC"]
    initial = dict(zip(nodes, [0.6, 0.3, 0.1])) if seeded else None
    original = initial.copy() if initial is not None else None
    expected = initial.copy() if seeded else dict.fromkeys(nodes, 1 / 3)
    outgoing = {nodes[0]: [nodes[1]], nodes[1]: [nodes[2]], nodes[2]: []}
    if cycle:
        outgoing[nodes[2]].append(nodes[0])
    if not directed:
        for source, targets in list((u, list(v)) for u, v in outgoing.items()):
            for target in targets:
                outgoing[target].append(source)

    # Distribute each source's score, treating a sink as linked to every node.
    for _ in range(iterations):
        updated = dict.fromkeys(nodes, (1 - alpha) / len(nodes))
        for source in nodes:
            targets = outgoing[source] or nodes
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


@pytest.mark.parametrize("normalize", [False, True])
def test_dangling_chain_converges_to_networkx_pagerank(normalize):
    net = TemporalMultiLayerNetwork(directed=True)
    net.add_edge("A", "L", "B", "L", t=100.0)
    net.add_edge("B", "L", "C", "L", t=200.0)
    graph = nx.DiGraph()
    graph.add_edges_from([(("A", "L"), ("B", "L")), (("B", "L"), ("C", "L"))])
    expected = nx.pagerank(graph, alpha=0.85, tol=1e-12)
    scores = list(streaming_pagerank(
        net, window_size=100.0, normalize=normalize,
        max_iter_per_window=200, tolerance=0,
    ))[0][2]
    assert scores == pytest.approx(expected, abs=1e-10)


@pytest.mark.parametrize("normalize", [False, True])
@pytest.mark.parametrize("seeded", [False, True])
@pytest.mark.parametrize("alpha", [0.2, 0.85])
def test_dangling_mass_is_recomputed_when_sink_gains_an_outgoing_edge(normalize, seeded, alpha):
    net = TemporalMultiLayerNetwork(directed=True)
    for source, target, time in [("A", "B", 100.0), ("B", "C", 200.0), ("C", "A", 300.0)]:
        net.add_edge(source, "L", target, "L", t=time)
    a, b, c = [(name, "L") for name in "ABC"]
    initial = {a: 0.6, b: 0.3, c: 0.1} if seeded else None
    original = initial.copy() if initial is not None else None
    expected = initial.copy() if seeded else {a: 1 / 3, b: 1 / 3, c: 1 / 3}
    base = (1 - alpha) / 3
    first = {
        a: base + alpha * expected[c] / 3,
        b: base + alpha * (expected[a] + expected[c] / 3),
        c: base + alpha * (expected[b] + expected[c] / 3),
    }
    second = {
        a: base + alpha * first[c],
        b: base + alpha * first[a],
        c: base + alpha * first[b],
    }
    windows = list(streaming_pagerank(
        net, alpha=alpha, initial_scores=initial, window_size=100.0,
        normalize=normalize, max_iter_per_window=1, tolerance=0,
    ))
    assert len(windows) == 2
    assert windows[0][2] == pytest.approx(first)
    assert windows[1][2] == pytest.approx(second)
    assert initial == original
