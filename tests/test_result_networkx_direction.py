"""NetworkX exports must preserve the source graph's edge direction."""

from copy import deepcopy
from types import SimpleNamespace

import networkx as nx
import pytest

from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.dsl.result import QueryResult


@pytest.mark.parametrize(
    "graph_type", [nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph]
)
@pytest.mark.parametrize("shape", ["chain", "reciprocal", "empty"])
@pytest.mark.parametrize("first_only", [False, True])
@pytest.mark.parametrize("weight", [0, 2.5])
def test_edge_export_preserves_graph_type_and_selected_direction(
    graph_type, shape, first_only, weight
):
    graph = graph_type()
    graph.add_nodes_from(
        [("A", {"label": "alpha"}), ("B", {"label": "beta"}), "C", "unused"]
    )
    pairs = {
        "chain": [("A", "B"), ("B", "C")],
        "reciprocal": [("A", "B"), ("B", "A")],
        "empty": [],
    }[shape]
    graph.add_edges_from(pairs, weight=weight)
    selected = list(graph.edges())
    if first_only:
        selected = selected[:1]
    result = QueryResult("edges", selected)
    original = deepcopy(
        (dict(graph.nodes(data=True)), list(graph.edges(data=True)), graph.graph)
    )
    assert result.target == "edges" and result.count == len(selected)

    exported = result.to_networkx(SimpleNamespace(core_network=graph))

    assert type(exported) is graph_type
    assert exported.is_directed() == graph.is_directed()
    assert exported.is_multigraph() == graph.is_multigraph()
    assert exported.number_of_edges() == len(selected)
    assert set(exported.nodes()) == {node for edge in selected for node in edge}
    for source, target in selected:
        assert exported.has_edge(source, target)
        assert exported.nodes[source] == graph.nodes[source]
        if graph.is_directed() and (target, source) not in selected:
            assert not exported.has_edge(target, source)
    assert all(data["weight"] == weight for _, _, data in exported.edges(data=True))
    assert (
        dict(graph.nodes(data=True)),
        list(graph.edges(data=True)),
        graph.graph,
    ) == original


@pytest.mark.parametrize(
    "graph_type", [nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph]
)
@pytest.mark.parametrize("empty", [False, True])
def test_node_export_still_preserves_graph_type_and_metrics(graph_type, empty):
    graph = graph_type()
    graph.add_edge("A", "B", weight=2.5)
    items = [] if empty else ["A", "B"]
    result = QueryResult("nodes", items, attributes={"score": [0, 7][: len(items)]})
    assert result.count == len(items)
    exported = result.to_networkx(SimpleNamespace(core_network=graph))
    assert type(exported) is graph_type
    assert set(exported) == set(items)
    if items:
        assert exported.nodes["A"]["score"] == 0
        assert exported.nodes["B"]["score"] == 7
        assert "score" not in graph.nodes["A"]


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("limit", [None, 0, 1])
def test_real_multilayer_edge_query_preserves_direction(directed, limit):
    net = multinet.multi_layer_network(directed=directed)
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "social",
                "target_type": "work",
                "weight": 2.5,
            }
        ]
    )
    query = Q.edges()
    if limit is not None:
        query = query.limit(limit)
    result = query.execute(net)
    assert result.target == "edges" and result.count == (0 if limit == 0 else 1)
    exported = result.to_networkx(net)
    assert exported.is_directed() == directed
    assert exported.number_of_edges() == result.count
    if result.count:
        assert exported.has_edge(("A", "social"), ("B", "work"))
        if directed:
            assert not exported.has_edge(("B", "work"), ("A", "social"))
