"""Correctness-focused tests for py3plex.core.multinet."""

from __future__ import annotations

import networkx as nx
import pytest

from py3plex.core import multinet


def test_add_nodes_preserves_attributes_on_core_network_node():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_nodes(
        [
            {"source": "A", "type": "L0", "weight": 2.5, "label": "alpha"},
            {"source": "B", "type": "L0", "custom": {"k": "v"}},
        ]
    )

    assert ("A", "L0") in net
    assert net.core_network.nodes[("A", "L0")]["weight"] == 2.5
    assert net.core_network.nodes[("A", "L0")]["label"] == "alpha"
    assert net.core_network.nodes[("B", "L0")]["custom"] == {"k": "v"}


def test_add_edges_list_sets_weight_and_default_type():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges([["A", "L0", "B", "L0", 3.0]], input_type="list")

    u = ("A", "L0")
    v = ("B", "L0")
    assert net.core_network.has_edge(u, v)

    # MultiGraph stores parallel edges, so inspect the first key's attributes.
    edge_data = net.core_network.get_edge_data(u, v)
    assert isinstance(edge_data, dict) and edge_data
    attrs = next(iter(edge_data.values()))
    assert attrs["weight"] == 3.0
    assert attrs["type"] == "default"


def test_add_edges_dict_preserves_edge_attributes_and_creates_nodes():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "L0",
                "target_type": "L1",
                "weight": 0.7,
                "type": "interaction",
                "evidence": "manual",
            }
        ],
        input_type="dict",
    )

    u = ("A", "L0")
    v = ("B", "L1")
    assert u in net and v in net
    assert net.core_network.has_edge(u, v)

    edge_data = net.core_network.get_edge_data(u, v)
    attrs = next(iter(edge_data.values()))
    assert attrs["weight"] == 0.7
    assert attrs["type"] == "interaction"
    assert attrs["evidence"] == "manual"


def test_get_edges_multiplex_filters_coupling_edges_by_default():
    net = multinet.multi_layer_network(network_type="multiplex", directed=False, verbose=False)
    net.add_edges(
        [
            # Coupling edge should be hidden by default.
            {
                "source": "A",
                "target": "A",
                "source_type": "L0",
                "target_type": "L1",
                "type": "coupling",
            },
            # Regular edge should be visible.
            {"source": "A", "target": "B", "source_type": "L0", "target_type": "L0"},
        ]
    )

    edges_default = list(net.get_edges())
    assert len(edges_default) == 1
    u, v, _key = edges_default[0]
    assert {u, v} == {("A", "L0"), ("B", "L0")}

    edges_with_coupling = list(net.get_edges(multiplex_edges=True))
    # Now includes both edges (with potential key differences).
    assert len(edges_with_coupling) == 2


def test_add_edges_invalid_input_type_raises_value_error():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    with pytest.raises(ValueError, match="Invalid input_type"):
        net.add_edges([], input_type="invalid")


def test_contains_and_iter_on_uninitialized_network_are_well_defined():
    net = multinet.multi_layer_network(directed=False, verbose=False)
    assert net.core_network is None
    assert ("A", "L0") not in net
    assert list(iter(net)) == []
    assert len(net) == 0


def test_property_add_edges_list_matches_networkx_multigraph_oracle():
    hypothesis = pytest.importorskip("hypothesis")
    strategies = pytest.importorskip("hypothesis.strategies")

    @hypothesis.given(
        strategies.lists(
            strategies.tuples(
                strategies.integers(min_value=0, max_value=3),
                strategies.sampled_from(["L0", "L1"]),
                strategies.integers(min_value=0, max_value=3),
                strategies.sampled_from(["L0", "L1"]),
                strategies.integers(min_value=0, max_value=5),
            ),
            max_size=10,
        )
    )
    def check(edges):
        # Convert into the list input format expected by add_edges(input_type="list")
        edge_list = [[u, lu, v, lv, float(w)] for u, lu, v, lv, w in edges]

        net = multinet.multi_layer_network(directed=False, verbose=False)
        net.add_edges(edge_list, input_type="list")

        oracle = nx.MultiGraph()
        for u, lu, v, lv, w in edge_list:
            oracle.add_edge((u, lu), (v, lv), weight=w, type="default")

        assert net.core_network.number_of_nodes() == oracle.number_of_nodes()
        assert net.core_network.number_of_edges() == oracle.number_of_edges()
        assert sorted(net.core_network.degree()) == sorted(oracle.degree())

    check()

