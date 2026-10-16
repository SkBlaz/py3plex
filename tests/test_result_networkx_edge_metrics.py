"""Computed endpoint-pair metrics must export onto each selected multiedge."""

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
@pytest.mark.parametrize("value", [0, None, 7, {"mean": 7, "std": 0.5}])
@pytest.mark.parametrize("selection", ["all", "first", "empty"])
def test_dictionary_metrics_attach_to_selected_edge_data(graph_type, value, selection):
    graph = graph_type()
    graph.add_edge("A", "B", weight=3.5)
    graph.add_edge("B", "C", weight=3.5)
    if graph.is_multigraph():
        graph.add_edge("A", "B", weight=3.5)
    selected = list(graph.edges())
    if selection == "first":
        selected = selected[:1]
    elif selection == "empty":
        selected = []
    scores = {("A", "B"): value, ("B", "C"): value, ("absent", "edge"): 99}
    result = QueryResult(
        "edges",
        selected,
        attributes={"score": scores, "rank": {("A", "B"): 2, ("B", "C"): 3}},
    )
    original = deepcopy((list(graph.edges(data=True)), result.items, result.attributes))
    assert result.target == "edges" and result.count == len(selected)

    exported = result.to_networkx(SimpleNamespace(core_network=graph))

    assert exported.number_of_edges() == len(selected)
    assert exported.is_multigraph() == graph.is_multigraph()
    assert not exported.has_edge("absent", "edge")
    for source, target, data in exported.edges(data=True):
        assert data["score"] == value
        assert data["rank"] == (2 if {source, target} == {"A", "B"} else 3)
        assert data["weight"] == 3.5
    assert (list(graph.edges(data=True)), result.items, result.attributes) == original


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("measure", ["edge_betweenness", "edge_betweenness_centrality"])
@pytest.mark.parametrize("limit", [0, 1])
def test_real_edge_metric_query_exports_to_networkx(directed, measure, limit):
    net = multinet.multi_layer_network(directed=directed)
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "social",
                "target_type": "social",
            }
        ]
    )
    result = Q.edges().compute(measure).limit(limit).execute(net)
    assert result.target == "edges" and result.count == limit
    exported = result.to_networkx(net)
    assert exported.number_of_edges() == result.count
    for source, target, data in exported.edges(data=True):
        metrics = result.attributes[measure]
        key = (source, target)
        if not exported.is_directed() and key not in metrics:
            key = (target, source)
        assert data[measure] == metrics[key]
    assert all(measure not in data for _, _, data in net.core_network.edges(data=True))
