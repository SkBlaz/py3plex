"""Additional tests for the robustness module."""

import itertools

import numpy as np
import pytest

from py3plex.core import multinet
from py3plex.robustness import (
    EdgeAdd,
    EdgeDrop,
    NodeDrop,
    centrality_robustness,
    estimate_metric_distribution,
)


def _base_network() -> multinet.multi_layer_network:
    """Create a small multilayer network with two layers."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            ["a", "L0", "b", "L0", 1.0],
            ["b", "L0", "c", "L0", 1.0],
            ["c", "L0", "a", "L0", 1.0],
            ["a", "L1", "b", "L1", 1.0],
        ],
        input_type="list",
    )
    return net


def test_edge_add_respects_layer_filter():
    """EdgeAdd should only introduce edges inside the requested layer."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_nodes(
        [
            {"source": "x", "type": "L0"},
            {"source": "y", "type": "L0"},
            {"source": "u", "type": "L1"},
            {"source": "v", "type": "L1"},
        ]
    )
    rng = np.random.default_rng(0)

    perturbed = EdgeAdd(p=1.0, layer="L0").apply(net, rng)

    edges = list(perturbed.get_edges())
    assert edges  # at least one edge added for L0
    assert all(e[0][1] == e[1][1] == "L0" for e in edges)

    l1_nodes = {("u", "L1"), ("v", "L1")}
    assert l1_nodes.issubset(set(perturbed.get_nodes()))
    assert all(not (e[0] in l1_nodes and e[1] in l1_nodes) for e in edges)


def test_metric_distribution_merges_missing_keys():
    """estimate_metric_distribution should union keys across samples and fill missing with 0."""
    net = _base_network()
    counter = itertools.count()

    def alternating_metric(_):
        return {"a": 1.0} if next(counter) % 2 == 0 else {"b": 2.0}

    result = estimate_metric_distribution(
        network=net,
        metric_fn=alternating_metric,
        perturbation=EdgeDrop(p=0.0),
        n_samples=4,
        random_state=123,
    )

    summary = result["summary"]
    assert summary["a"]["mean"] == pytest.approx(0.5)  # [1,0,1,0]
    assert summary["b"]["mean"] == pytest.approx(1.0)  # [0,2,0,2]


def test_centrality_robustness_constant_rank_returns_none():
    """When rankings do not vary, Kendall tau should be reported as None."""
    net = _base_network()

    def constant_centrality(n):
        return {node: 1.0 for node in n.get_nodes()}

    result = centrality_robustness(
        network=net,
        centrality_fn=constant_centrality,
        perturbation=EdgeDrop(p=0.7),
        n_samples=5,
        random_state=7,
    )

    stability = result["rank_stability"]
    assert stability["kendall_tau_mean"] is None
    assert stability["kendall_tau_std"] is None
    assert all(stats["std"] == pytest.approx(0.0) for stats in result["node_stats"].values())


def test_centrality_robustness_fills_missing_nodes_with_zero():
    """Nodes missing from a sample centrality dict should be treated as zero."""
    net = _base_network()

    def positive_degree_only(n):
        degrees = {}
        for node in n.get_nodes():
            deg = n.core_network.degree(node)
            if deg > 0:
                degrees[node] = float(deg)
        return degrees

    result = centrality_robustness(
        network=net,
        centrality_fn=positive_degree_only,
        perturbation=EdgeDrop(p=1.0),  # drop all edges -> empty dicts per sample
        n_samples=3,
        random_state=5,
    )

    assert all(stats["mean"] == pytest.approx(0.0) for stats in result["node_stats"].values())
    assert result["rank_stability"]["kendall_tau_mean"] is None


def _single_edge_attrs(net: multinet.multi_layer_network, u, v) -> dict:
    """Return the attribute dict for a single-edge MultiGraph between u and v."""
    data = net.core_network.get_edge_data(u, v)
    assert data is not None, "expected an edge to exist"
    assert len(data) == 1, "test expects exactly one parallel edge"
    return next(iter(data.values()))


def test_edge_drop_p0_preserves_edge_and_node_attributes():
    """EdgeDrop(p=0) should behave like identity (including attrs) for kept edges."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_nodes(
        [
            {"source": "a", "type": "L0", "role": "src"},
            {"source": "b", "type": "L0", "role": "dst"},
        ]
    )
    net.add_edges(
        [
            {
                "source": "a",
                "target": "b",
                "source_type": "L0",
                "target_type": "L0",
                "weight": 2.5,
                "type": "special",
                "color": "red",
            }
        ]
    )

    rng = np.random.default_rng(0)
    perturbed = EdgeDrop(p=0.0).apply(net, rng)

    assert perturbed.core_network.nodes[("a", "L0")]["role"] == "src"
    assert perturbed.core_network.nodes[("b", "L0")]["role"] == "dst"
    attrs = _single_edge_attrs(perturbed, ("a", "L0"), ("b", "L0"))
    assert attrs["weight"] == pytest.approx(2.5)
    assert attrs["type"] == "special"
    assert attrs["color"] == "red"


def test_edge_add_p0_preserves_existing_edge_attributes():
    """EdgeAdd(p=0) should copy existing edges without clobbering attrs."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_nodes(
        [
            {"source": "a", "type": "L0"},
            {"source": "b", "type": "L0"},
            {"source": "c", "type": "L0"},
        ]
    )
    net.add_edges(
        [
            {
                "source": "a",
                "target": "b",
                "source_type": "L0",
                "target_type": "L0",
                "weight": 7.0,
                "type": "trusted",
                "color": "blue",
            }
        ]
    )

    rng = np.random.default_rng(123)
    perturbed = EdgeAdd(p=0.0).apply(net, rng)

    attrs = _single_edge_attrs(perturbed, ("a", "L0"), ("b", "L0"))
    assert attrs["weight"] == pytest.approx(7.0)
    assert attrs["type"] == "trusted"
    assert attrs["color"] == "blue"


def test_node_drop_p0_preserves_kept_edge_attributes():
    """NodeDrop(p=0) should preserve edge attrs since it keeps the entire graph."""
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_nodes(
        [
            {"source": "a", "type": "L0"},
            {"source": "b", "type": "L0"},
        ]
    )
    net.add_edges(
        [
            {
                "source": "a",
                "target": "b",
                "source_type": "L0",
                "target_type": "L0",
                "weight": 1.25,
                "type": "edge_type",
                "note": "keep-me",
            }
        ]
    )

    rng = np.random.default_rng(999)
    perturbed = NodeDrop(p=0.0).apply(net, rng)

    attrs = _single_edge_attrs(perturbed, ("a", "L0"), ("b", "L0"))
    assert attrs["weight"] == pytest.approx(1.25)
    assert attrs["type"] == "edge_type"
    assert attrs["note"] == "keep-me"
