"""Tests for comparison metrics and executor utilities."""

import pytest
import networkx as nx

from py3plex.comparison import executor, metrics


class _SimpleNetwork:
    """Minimal network wrapper exposing the interface used by comparison metrics."""

    def __init__(self, edges):
        self.core_network = nx.Graph()
        self.core_network.add_edges_from(edges)

    def get_nodes(self):
        return self.core_network.nodes()


def test_multiplex_jaccard_layerwise_and_global_distances():
    net_a = _SimpleNetwork(
        [
            (("a", "L1"), ("b", "L1")),
            (("c", "L2"), ("d", "L2")),
        ]
    )
    net_b = _SimpleNetwork(
        [
            (("a", "L1"), ("b", "L1")),
        ]
    )

    result = metrics.multiplex_jaccard(net_a, net_b)

    assert pytest.approx(0.5) == result["global_distance"]
    assert result["layerwise_distance"]["L1"] == 0.0
    assert result["layerwise_distance"]["L2"] == 1.0


def test_layer_edge_overlap_averages_per_layer_distance():
    net_a = _SimpleNetwork(
        [
            (("a", "L1"), ("b", "L1")),
            (("c", "L2"), ("d", "L2")),
        ]
    )
    net_b = _SimpleNetwork(
        [
            (("a", "L1"), ("b", "L1")),
        ]
    )

    result = metrics.layer_edge_overlap(net_a, net_b)

    assert pytest.approx(0.5) == result["global_distance"]
    assert result["layerwise_distance"]["L1"] == 0.0
    assert result["layerwise_distance"]["L2"] == 1.0


def test_degree_correlation_requires_at_least_two_shared_nodes():
    net_a = _SimpleNetwork(
        [
            (("a", "L1"), ("b", "L1")),
        ]
    )
    net_b = _SimpleNetwork(
        [
            (("a", "L1"), ("c", "L1")),
        ]
    )

    result = metrics.degree_correlation(net_a, net_b)

    assert result["global_distance"] == 1.0
    assert result["shared_nodes"] == 0


def test_compare_networks_unknown_metric_raises_value_error():
    net_a = _SimpleNetwork([])
    net_b = _SimpleNetwork([])

    with pytest.raises(ValueError, match="Unknown metric"):
        executor.compare_networks(net_a, net_b, metric="nonexistent")


def test_compare_networks_respects_requested_measures_only():
    net_a = _SimpleNetwork(
        [
            (("a", "L"), ("b", "L")),
            (("b", "L"), ("c", "L")),
        ]
    )
    net_b = _SimpleNetwork(
        [
            (("a", "L"), ("b", "L")),
            (("b", "L"), ("c", "L")),
            (("b", "L"), ("d", "L")),
        ]
    )

    result = executor.compare_networks(
        net_a,
        net_b,
        metric="degree_change",
        measures=["per_node_difference"],
        network_a_name="A",
        network_b_name="B",
    )

    assert result.global_distance is None
    assert result.layerwise_distance == {}
    assert result.per_node_difference == {
        ("a", "L"): 0,
        ("b", "L"): 1,
        ("c", "L"): 0,
    }
    assert result.meta["metric"] == "degree_change"
    assert result.meta["measures"] == ["per_node_difference"]
