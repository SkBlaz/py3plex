"""Node export must retain available values from positional metric lists."""

from copy import deepcopy
from types import SimpleNamespace

import networkx as nx
import pytest

from py3plex.dsl.result import QueryResult


@pytest.mark.parametrize(
    "graph_type", [None, nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph]
)
@pytest.mark.parametrize("replicas", [False, True])
@pytest.mark.parametrize("length", [0, 1, 3, 4])
@pytest.mark.parametrize("value", [0, None, 7, {"mean": 7, "std": 0.5}])
def test_available_list_values_attach_to_corresponding_nodes(
    graph_type, replicas, length, value
):
    items = [(name, "social") for name in "ABC"] if replicas else list("ABC")
    values = [deepcopy(value) for _ in range(length)]
    result = QueryResult("nodes", items, attributes={"score": values})
    original = deepcopy((result.items, result.attributes))
    graph = None
    if graph_type is not None:
        graph = graph_type()
        graph.add_edges_from(zip(items, items[1:]))
        for node in items:
            graph.nodes[node]["existing"] = "source"
    assert result.target == "nodes" and result.count == 3

    exported = result.to_networkx(
        SimpleNamespace(core_network=graph) if graph is not None else None
    )

    assert set(exported) == set(items)
    for index, item in enumerate(items):
        if index < len(values):
            assert "score" in exported.nodes[item]
            assert exported.nodes[item]["score"] == values[index]
        else:
            assert "score" not in exported.nodes[item]
        if graph is not None:
            assert exported.nodes[item]["existing"] == "source"
            assert "score" not in graph.nodes[item]
    assert (result.items, result.attributes) == original


@pytest.mark.parametrize("values", [[0, 7], [0, 7, 8], [0, 7, 8, 9]])
def test_lists_follow_result_items_when_source_omits_a_node(values):
    graph = nx.Graph()
    graph.add_nodes_from(["C", "A"])
    graph.nodes["C"]["score"] = 99
    result = QueryResult("nodes", ["A", "B", "C"], attributes={"score": values})
    assert result.count == 3
    exported = result.to_networkx(SimpleNamespace(core_network=graph))
    assert set(exported) == {"A", "C"}
    assert exported.nodes["A"]["score"] == 0
    assert exported.nodes["C"]["score"] == (8 if len(values) >= 3 else 99)
    assert graph.nodes["C"]["score"] == 99


def test_exact_length_legacy_tuple_values_remain_supported():
    result = QueryResult("nodes", ["A", "B"], attributes={"score": (0, 7)})
    assert result.count == 2
    exported = result.to_networkx()
    assert exported.nodes["A"]["score"] == 0
    assert exported.nodes["B"]["score"] == 7
