"""Correctness-focused oracle/property tests for robustness centrality."""

from __future__ import annotations

import networkx as nx
import pytest

from py3plex.centrality import robustness_centrality
from py3plex.centrality.robustness import _compute_avg_shortest_path
from py3plex.core import multinet

try:
    from hypothesis import given, settings, strategies as st
except ImportError:  # pragma: no cover - optional dependency
    given = None


def test_uninitialized_empty_network_returns_empty_or_zero_scores():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    assert net.core_network is None

    assert robustness_centrality(net, target="node", metric="giant_component") == {}

    sample_nodes = [("a", "L0"), ("b", "L0")]
    scores = robustness_centrality(
        net, target="node", metric="giant_component", sample_nodes=sample_nodes
    )
    assert scores == {("a", "L0"): 0.0, ("b", "L0"): 0.0}

    sample_layers = ["L0", "L_missing"]
    scores_layers = robustness_centrality(
        net, target="layer", metric="giant_component", sample_layers=sample_layers
    )
    assert scores_layers == {"L0": 0.0, "L_missing": 0.0}


def test_uninitialized_network_still_validates_inputs():
    net = multinet.multi_layer_network(directed=False, verbose=False)

    with pytest.raises(ValueError, match="target must be"):
        robustness_centrality(net, target="bad_target")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="metric must be one of"):
        robustness_centrality(net, metric="bad_metric")  # type: ignore[arg-type]


def test_giant_component_uses_weak_components_for_directed_graphs():
    net = multinet.multi_layer_network(directed=True, verbose=False)
    net.add_edges(
        [
            ["a", "L0", "b", "L0", 1.0],
            ["b", "L0", "c", "L0", 1.0],
        ],
        input_type="list",
    )

    scores = robustness_centrality(net, target="node", metric="giant_component", seed=0)

    assert scores[("b", "L0")] == pytest.approx(2.0)
    assert scores[("a", "L0")] == pytest.approx(1.0)
    assert scores[("c", "L0")] == pytest.approx(1.0)


def test_compute_avg_shortest_path_matches_reference_weighted_components():
    """Oracle: match NetworkX avg shortest path over connected pairs only."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    # Two components: path of 3 nodes (avg=4/3) and edge of 2 nodes (avg=1)
    net.add_edges(
        [
            ["a", "L0", "b", "L0", 1.0],
            ["b", "L0", "c", "L0", 1.0],
            ["x", "L0", "y", "L0", 1.0],
        ],
        input_type="list",
    )

    observed = _compute_avg_shortest_path(net)

    # Reference weighted by number of unordered connected pairs in each component.
    G = net.core_network
    total = 0.0
    pairs = 0
    for comp in nx.connected_components(G):
        if len(comp) < 2:
            continue
        sub = G.subgraph(comp)
        avg = nx.average_shortest_path_length(sub)
        n = len(comp)
        w = n * (n - 1) // 2
        total += avg * w
        pairs += w

    expected = total / pairs
    assert observed == pytest.approx(expected)


if given:

    @st.composite
    def simple_undirected_graphs(draw):
        n = draw(st.integers(min_value=1, max_value=6))
        nodes = [f"n{i}" for i in range(n)]

        possible_edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        if not possible_edges:
            chosen = set()
        else:
            chosen = draw(
                st.sets(st.sampled_from(possible_edges), max_size=len(possible_edges))
            )
        edges = [(nodes[i], nodes[j]) for i, j in chosen]
        return nodes, edges

    @given(simple_undirected_graphs())
    @settings(max_examples=60, deadline=None)
    def test_property_giant_component_robustness_matches_reference(data):
        nodes, edges = data
        net = multinet.multi_layer_network(directed=False, verbose=False)
        net.add_nodes([{"source": n, "type": "L0"} for n in nodes])
        if edges:
            net.add_edges([[u, "L0", v, "L0", 1.0] for (u, v) in edges], input_type="list")

        scores = robustness_centrality(net, target="node", metric="giant_component", seed=123)

        G = net.core_network
        if len(G) == 0:
            assert scores == {}
            return

        baseline = max(len(c) for c in nx.connected_components(G)) if len(G) else 0

        expected = {}
        for node in list(G.nodes()):
            H = G.copy()
            H.remove_node(node)
            if len(H) == 0:
                lcc = 0
            else:
                lcc = max((len(c) for c in nx.connected_components(H)), default=0)
            expected[node] = float(baseline - lcc)

        assert set(scores.keys()) == set(expected.keys())
        for node, value in expected.items():
            assert scores[node] == pytest.approx(value)

else:

    def test_property_giant_component_robustness_matches_reference():
        pytest.skip("hypothesis not installed")
