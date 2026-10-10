"""Layer label conversion must retain serialized graph data."""

import networkx as nx
import pytest

from py3plex.core.nx_compat import nx_read_gpickle, nx_write_gpickle
from py3plex.core.parsers import parse_gpickle


@pytest.mark.parametrize("graph_type", [nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph])
def test_layer_separator_preserves_nodes_attributes_and_edge_keys(tmp_path, graph_type):
    graph = graph_type(project="study", settings={"seed": 42})
    graph.add_node("social_A", role="source", labels="Alice")
    graph.add_node("work_B", role="target")
    graph.add_node("work_isolated", role="isolated")
    if graph.is_multigraph():
        graph.add_edge("social_A", "work_B", key="first", weight=2.5, kind="contact")
        graph.add_edge("social_A", "work_B", key="second", weight=7.0, kind="message")
        graph.add_edge("work_B", "work_B", key="loop", weight=3.0)
    else:
        graph.add_edge("social_A", "work_B", weight=2.5, kind="contact")
        graph.add_edge("work_B", "work_B", weight=3.0)
    path = str(tmp_path / "layers.gpickle")
    nx_write_gpickle(graph, path)

    result, _ = parse_gpickle(path, directed=graph.is_directed(), layer_separator="_")
    assert result.is_directed() == graph.is_directed()
    assert result.is_multigraph()
    assert result.graph == graph.graph
    assert dict(result.nodes(data=True)) == {
        ("A", "social"): graph.nodes["social_A"],
        ("B", "work"): graph.nodes["work_B"],
        ("isolated", "work"): graph.nodes["work_isolated"],
    }
    assert result.number_of_edges() == graph.number_of_edges()
    if graph.is_multigraph():
        for key in ("first", "second"):
            assert result[("A", "social")][("B", "work")][key] == graph["social_A"]["work_B"][key]
        assert result[("B", "work")][("B", "work")]["loop"] == {"weight": 3.0}
    else:
        assert list(result[("A", "social")][("B", "work")].values()) == [
            {"weight": 2.5, "kind": "contact"}
        ]
    if graph.is_directed():
        assert not result.has_edge(("B", "work"), ("A", "social"))
    assert nx.utils.graphs_equal(nx_read_gpickle(path), graph)
