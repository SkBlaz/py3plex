"""Contract-focused tests for py3plex.algorithms.attribute_correlation."""

from __future__ import annotations

import math

import networkx as nx
import numpy as np
import pytest

from py3plex.algorithms import attribute_correlation as ac
from py3plex.core import multinet


class _DummyNetwork:
    def __init__(self, core_network: nx.Graph):
        self.core_network = core_network


def _make_two_layer_star():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    # L1 star centered at c: degrees [3,1,1,1]
    net.add_edges(
        [
            ["c", "L1", "a", "L1", 1.0],
            ["c", "L1", "b", "L1", 1.0],
            ["c", "L1", "d", "L1", 1.0],
        ],
        input_type="list",
    )
    # L2 same star structure
    net.add_edges(
        [
            ["c", "L2", "a", "L2", 1.0],
            ["c", "L2", "b", "L2", 1.0],
            ["c", "L2", "d", "L2", 1.0],
        ],
        input_type="list",
    )
    return net


def test_correlate_attributes_with_centrality_requires_scipy(monkeypatch):
    net = _make_two_layer_star()
    monkeypatch.setattr(ac, "SCIPY_AVAILABLE", False)

    with pytest.raises(ImportError, match="scipy is required"):
        ac.correlate_attributes_with_centrality(net, "attr", by_layer=False)


def test_correlate_attributes_with_centrality_per_layer_matches_perfect_degree_corr():
    pytest.importorskip("scipy")
    net = _make_two_layer_star()

    # Set attribute to the state-node degree; correlation should be 1.0 per layer.
    degrees = dict(net.core_network.degree())
    for node in net.core_network.nodes():
        net.core_network.nodes[node]["deg_attr"] = degrees[node]

    results = ac.correlate_attributes_with_centrality(
        net, "deg_attr", centrality_type="degree", correlation_method="pearson", by_layer=True
    )

    assert set(results.keys()) == {"L1", "L2"}
    for layer, (corr, pval) in results.items():
        assert corr == pytest.approx(1.0)
        assert 0.0 <= pval <= 1.0, f"invalid p-value for {layer}: {pval}"


def test_correlate_attributes_across_layers_common_nodes_oracle():
    pytest.importorskip("scipy")
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges([["a", "L1", "b", "L1", 1.0]], input_type="list")
    net.add_edges([["a", "L2", "b", "L2", 1.0]], input_type="list")

    # Provide attribute values for common node_ids across layers.
    for node_id, value in [("a", 1.0), ("b", 2.0), ("c", 3.0)]:
        for layer in ["L1", "L2"]:
            state_node = (node_id, layer)
            net.core_network.add_node(state_node)
            net.core_network.nodes[state_node]["x"] = value if layer == "L1" else 2 * value

    results = ac.correlate_attributes_across_layers(net, "x", correlation_method="pearson")

    assert len(results) == 1
    (layer_pair, (corr, pval)), = results.items()
    assert set(layer_pair) == {"L1", "L2"}
    assert corr == pytest.approx(1.0)
    assert 0.0 <= pval <= 1.0


def test_correlate_attributes_with_centrality_rejects_unknown_method():
    pytest.importorskip("scipy")
    G = nx.path_graph(4)
    dummy = _DummyNetwork(G)
    for node, degree in dict(G.degree()).items():
        G.nodes[node]["deg_attr"] = degree

    with pytest.raises(ValueError, match="Unknown correlation method"):
        ac.correlate_attributes_with_centrality(
            dummy,
            "deg_attr",
            centrality_type="degree",
            correlation_method="made_up",
            by_layer=False,
        )


def test_attribute_structural_contingency_has_valid_shape_and_mass():
    net = _make_two_layer_star()
    for node, degree in dict(net.core_network.degree()).items():
        net.core_network.nodes[node]["attr"] = float(degree)

    result = ac.attribute_structural_contingency(
        net, attribute_name="attr", structural_property="degree", bins=4
    )

    contingency = result["contingency_table"]
    assert contingency.shape == (4, 4)
    assert float(contingency.sum()) == len(nx.get_node_attributes(net.core_network, "attr"))
    assert np.all(contingency >= 0)
    assert result["attribute_bins"].shape == (5,)
    assert result["structural_bins"].shape == (5,)
    assert math.isfinite(float(result["chi2"]))
    assert 0.0 <= float(result["p_value"]) <= 1.0


def test_multilayer_assortativity_returns_per_layer_coefficients():
    net = _make_two_layer_star()
    results = ac.multilayer_assortativity(net, attribute_name=None, by_layer=True)

    assert set(results.keys()) == {"L1", "L2"}
    # A star is disassortative (high-degree nodes connect to low-degree ones).
    assert all(results[layer] <= 0 or math.isnan(results[layer]) for layer in results)


def test_property_degree_attribute_always_correlates_with_degree_when_nonconstant():
    pytest.importorskip("scipy")
    pytest.importorskip("hypothesis")
    from hypothesis import given, strategies as st, assume

    @given(
        n=st.integers(min_value=3, max_value=12),
        p=st.floats(min_value=0.05, max_value=0.8, allow_nan=False, allow_infinity=False),
        seed=st.integers(min_value=0, max_value=2**32 - 1),
    )
    def _property(n: int, p: float, seed: int):
        rng = np.random.default_rng(seed)
        G = nx.erdos_renyi_graph(n=n, p=p, seed=int(rng.integers(0, 2**32 - 1)))
        degrees = dict(G.degree())

        assume(len(set(degrees.values())) > 1)

        for node, degree in degrees.items():
            G.nodes[node]["deg_attr"] = degree

        dummy = _DummyNetwork(G)
        results = ac.correlate_attributes_with_centrality(
            dummy,
            "deg_attr",
            centrality_type="degree",
            correlation_method="pearson",
            by_layer=False,
        )
        corr, pval = results["global"]

        assert corr == pytest.approx(1.0)
        assert 0.0 <= pval <= 1.0

    _property()

