from types import SimpleNamespace
import networkx as nx
import pytest
from py3plex.dsl.result import QueryResult

@pytest.mark.parametrize("graph_type", [nx.Graph,nx.DiGraph,nx.MultiGraph,nx.MultiDiGraph])
@pytest.mark.parametrize("target_layer", ["L","other"])
def test_four_field_edge_keeps_replica_identity_and_source_data(graph_type,target_layer):
    u,v=("a","L"),("b",target_layer)
    graph=graph_type()
    graph.add_node(u,label="source")
    graph.add_edge(u,v,weight=7)
    edge=("a","b","L",target_layer)
    result=QueryResult(target="edges",items=[edge],attributes={"score":{edge:3}})
    exported=result.to_networkx(SimpleNamespace(core_network=graph))
    assert type(exported) is graph_type
    assert set(exported) == {u,v}
    assert exported.nodes[u]["label"] == "source"
    assert list(exported.edges(data=True))[0][2] == {"weight":7,"score":3}
    if graph.is_directed():
        assert not exported.has_edge(v,u)
    assert "score" not in list(graph.edges(data=True))[0][2]

def test_four_field_edges_without_source_network():
    graph=QueryResult(target="edges",items=[("a","b","L","other")]).to_networkx()
    assert graph.has_edge(("a","L"),("b","other"))
