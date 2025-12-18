"""Correctness-focused oracle tests for py3plex.comparison edge cases."""

from __future__ import annotations

import json

import networkx as nx
import pytest

from py3plex.comparison import metrics
from py3plex.comparison.result import ComparisonResult
from py3plex.core import multinet


def test_multiplex_jaccard_uninitialized_py3plex_networks_treated_as_empty():
    """py3plex multi_layer_network may have core_network=None until populated."""
    net_a = multinet.multi_layer_network(directed=False, verbose=False)
    net_b = multinet.multi_layer_network(directed=False, verbose=False)
    assert net_a.core_network is None
    assert net_b.core_network is None

    result = metrics.multiplex_jaccard(net_a, net_b)

    assert result["global_distance"] == 0.0
    assert result["layerwise_distance"] == {}


def test_layer_edge_overlap_uninitialized_vs_nonempty_is_max_distance_per_layer():
    net_empty = multinet.multi_layer_network(directed=False, verbose=False)
    net_full = multinet.multi_layer_network(directed=False, verbose=False)
    net_full.add_edges([["a", "L0", "b", "L0", 1.0]], input_type="list")

    result = metrics.layer_edge_overlap(net_empty, net_full)

    assert result["layerwise_distance"] == {"L0": 1.0}
    assert result["global_distance"] == 1.0


def test_multilayer_resistance_distance_matches_laplacian_frobenius_oracle():
    np = pytest.importorskip("numpy")
    pytest.importorskip("scipy")

    class _SimpleNetwork:
        def __init__(self, edges):
            self.core_network = nx.Graph()
            self.core_network.add_edges_from(edges)

        def get_nodes(self):
            return self.core_network.nodes()

    net_a = _SimpleNetwork([(1, 2), (2, 3)])
    net_b = _SimpleNetwork([(1, 2)])

    observed = metrics.multilayer_resistance_distance(net_a, net_b)["global_distance"]

    L_a = nx.laplacian_matrix(net_a.core_network).toarray().astype(float)
    L_b = nx.laplacian_matrix(net_b.core_network).toarray().astype(float)
    max_n = max(L_a.shape[0], L_b.shape[0])
    L_a_padded = np.zeros((max_n, max_n))
    L_b_padded = np.zeros((max_n, max_n))
    L_a_padded[: L_a.shape[0], : L_a.shape[0]] = L_a
    L_b_padded[: L_b.shape[0], : L_b.shape[0]] = L_b

    expected = np.linalg.norm(L_a_padded - L_b_padded, ord="fro") / (max_n**2)
    assert observed == pytest.approx(expected)


def test_comparison_result_to_json_stringifies_node_keys():
    result = ComparisonResult(
        metric_name="degree_change",
        network_a_name="A",
        network_b_name="B",
        global_distance=0.5,
        per_node_difference={(("a", "L0"), ("b", "L0")): 1.0},
    )

    payload = json.loads(result.to_json())
    assert "per_node_difference" in payload
    assert str((("a", "L0"), ("b", "L0"))) in payload["per_node_difference"]


def test_property_layer_edge_overlap_symmetry_and_global_average():
    hypothesis = pytest.importorskip("hypothesis")
    strategies = pytest.importorskip("hypothesis.strategies")

    @hypothesis.given(
        strategies.sets(
            strategies.tuples(
                strategies.integers(min_value=0, max_value=4),
                strategies.integers(min_value=0, max_value=4),
                strategies.sampled_from(["L0", "L1"]),
            ),
            max_size=8,
        ),
        strategies.sets(
            strategies.tuples(
                strategies.integers(min_value=0, max_value=4),
                strategies.integers(min_value=0, max_value=4),
                strategies.sampled_from(["L0", "L1"]),
            ),
            max_size=8,
        ),
    )
    def check(edges_a, edges_b):
        def normalize(edges):
            normalized = []
            for u, v, layer in edges:
                if u == v:
                    continue
                a = (u, layer)
                b = (v, layer)
                if a == b:
                    continue
                normalized.append(tuple(sorted((a, b))))
            # remove duplicates while preserving undirected uniqueness
            return list({tuple(edge) for edge in normalized})

        class _SimpleNetwork:
            def __init__(self, edges):
                self.core_network = nx.Graph()
                self.core_network.add_edges_from(edges)

            def get_nodes(self):
                return self.core_network.nodes()

        net_a = _SimpleNetwork(normalize(edges_a))
        net_b = _SimpleNetwork(normalize(edges_b))

        forward = metrics.layer_edge_overlap(net_a, net_b)
        backward = metrics.layer_edge_overlap(net_b, net_a)

        assert forward["global_distance"] == backward["global_distance"]
        assert forward["layerwise_distance"] == backward["layerwise_distance"]

        if forward["layerwise_distance"]:
            expected_global = sum(forward["layerwise_distance"].values()) / len(
                forward["layerwise_distance"]
            )
            assert forward["global_distance"] == pytest.approx(expected_global)
        else:
            assert forward["global_distance"] == 0.0

    check()

