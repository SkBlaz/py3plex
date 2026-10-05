"""Streaming normalized degree must use the standard n - 1 divisor."""

import networkx as nx
import pytest

from py3plex.algorithms.temporal.centrality import streaming_degree_centrality
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("normalize", [False, True])
@pytest.mark.parametrize("shape", ["path", "star", "triangle", "parallel", "loop"])
@pytest.mark.parametrize("width", [1.0, 5.0])
@pytest.mark.parametrize("step", [None, 0.5])
def test_streaming_degree_matches_each_cumulative_snapshot(
    directed, normalize, shape, width, step
):
    pairs = {
        "path": [("A", "B"), ("B", "C"), ("C", "D")],
        "star": [("A", "B"), ("A", "C"), ("A", "D")],
        "triangle": [("A", "B"), ("B", "C"), ("C", "A")],
        "parallel": [("A", "B"), ("A", "B"), ("B", "C")],
        "loop": [("A", "A"), ("A", "B"), ("B", "C")],
    }[shape]
    net = TemporalMultiLayerNetwork(directed=directed)
    for time, (source, target) in zip([0.0, 1.0, 3.0], pairs):
        net.add_edge(source, "social", target, "social", t=time)
    snapshots = list(
        net.window_iter(window_size=width, step=step, return_type="snapshot")
    )

    results = list(
        streaming_degree_centrality(
            net, window_size=width, step=step, normalize=normalize
        )
    )

    assert len(results) == len(snapshots) > 0
    for (start, end, scores), (expected_start, expected_end, snapshot) in zip(
        results, snapshots
    ):
        assert (start, end) == (expected_start, expected_end)
        graph = snapshot.core_network
        assert graph.number_of_nodes() > 1
        expected = nx.degree_centrality(graph) if normalize else dict(graph.degree())
        assert scores == pytest.approx(expected)


def test_complete_undirected_triangle_has_unit_degree_centrality():
    net = TemporalMultiLayerNetwork(directed=False)
    for time, (source, target) in enumerate([("A", "B"), ("B", "C"), ("C", "A")]):
        net.add_edge(source, "social", target, "social", t=time)
    results = list(streaming_degree_centrality(net, window_size=5.0))
    assert len(results) == 1
    assert results[0][2] == {("A", "social"): 1, ("B", "social"): 1, ("C", "social"): 1}


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("normalize", [False, True])
def test_empty_network_remains_empty(directed, normalize):
    net = TemporalMultiLayerNetwork(directed=directed)
    assert (
        list(streaming_degree_centrality(net, window_size=1.0, normalize=normalize))
        == []
    )
