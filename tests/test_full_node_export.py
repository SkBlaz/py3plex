import networkx as nx
from types import SimpleNamespace

from py3plex.dsl.result import QueryResult


def test_full_node_export_and_equal_length_partial_selection(monkeypatch):
    graph = nx.MultiDiGraph()
    graph.add_node("isolated", color="blue")
    graph.add_edge("a", "b", key="x", weight=3)
    graph.add_edge("a", "b", key="y", weight=4)
    source = SimpleNamespace(core_network=graph)
    result = QueryResult(target="nodes", items=["b", "a", "isolated"], attributes={"v": [2, 3]})
    with monkeypatch.context() as patch:
        def unexpected_view(*args):
            raise AssertionError("full export constructed a subgraph view")
        patch.setattr(graph, "subgraph", unexpected_view)
        copy = result.to_networkx(source)
    assert type(copy) is type(graph)
    assert list(copy.edges(keys=True, data=True)) == list(graph.edges(keys=True, data=True))
    assert copy.nodes["a"]["v"] == 3
    assert "v" not in graph.nodes["a"]
    copy.nodes["isolated"]["color"] = "red"
    assert graph.nodes["isolated"]["color"] == "blue"
    partial = QueryResult(target="nodes", items=["a", "a", "b"], attributes={})
    assert set(partial.to_networkx(source)) == {"a", "b"}
