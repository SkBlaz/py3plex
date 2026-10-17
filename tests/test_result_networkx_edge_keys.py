"""Explicitly selected parallel-edge keys must retain their own source data."""

from copy import deepcopy
from types import SimpleNamespace

import networkx as nx
import pytest

from py3plex.dsl.result import QueryResult


@pytest.mark.parametrize("graph_type", [nx.MultiGraph, nx.MultiDiGraph])
@pytest.mark.parametrize("named_keys", [False, True])
@pytest.mark.parametrize("with_data", [False, True])
@pytest.mark.parametrize("selection", ["first", "second", "both", "empty"])
def test_selected_keys_preserve_individual_edge_data(
    graph_type, named_keys, with_data, selection
):
    graph = graph_type()
    keys = ["first", "second"] if named_keys else [0, 1]
    graph.add_edge("A", "B", key=keys[0], weight=2, label="first")
    graph.add_edge("A", "B", key=keys[1], weight=8, label="second")
    graph.nodes["A"]["label"] = "alpha"
    chosen = {"first": keys[:1], "second": keys[1:], "both": keys, "empty": []}[
        selection
    ]
    items = [("A", "B", key) for key in chosen]
    if with_data:
        items = [item + (graph.get_edge_data(*item).copy(),) for item in items]
    result = QueryResult("edges", items)
    original = deepcopy((list(graph.edges(keys=True, data=True)), result.items))
    assert result.target == "edges" and result.count == len(chosen)

    exported = result.to_networkx(SimpleNamespace(core_network=graph))

    assert exported.is_multigraph()
    assert exported.number_of_edges() == len(chosen)
    assert set(exported.get_edge_data("A", "B", default={})) == set(chosen)
    for key in chosen:
        assert exported.get_edge_data("A", "B", key) == graph.get_edge_data(
            "A", "B", key
        )
    if chosen:
        assert exported.nodes["A"] == graph.nodes["A"]
    assert (list(graph.edges(keys=True, data=True)), result.items) == original


@pytest.mark.parametrize(
    "graph_type", [nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph]
)
@pytest.mark.parametrize("with_data", [False, True])
def test_unkeyed_formats_still_use_source_edge_data(graph_type, with_data):
    graph = graph_type()
    graph.add_edge("A", "B", weight=2)
    item = ("A", "B", {"weight": 2}) if with_data else ("A", "B")
    result = QueryResult("edges", [item])
    assert result.count == 1
    exported = result.to_networkx(SimpleNamespace(core_network=graph))
    assert exported.number_of_edges() == 1
    assert [data["weight"] for _, _, data in exported.edges(data=True)] == [2]


def test_edge_attribute_named_key_is_separate_from_edge_identity():
    graph = nx.MultiGraph()
    graph.add_edge("A", "B", key="selected", weight=8)
    graph["A"]["B"]["selected"]["key"] = "attribute"
    result = QueryResult("edges", [("A", "B", "selected")])
    assert result.count == 1
    exported = result.to_networkx(SimpleNamespace(core_network=graph))
    assert exported.get_edge_data("A", "B", "selected") == {
        "weight": 8,
        "key": "attribute",
    }
