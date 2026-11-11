from copy import deepcopy
from types import SimpleNamespace
import networkx as nx
import pytest
from py3plex.dsl.result import QueryResult

@pytest.mark.parametrize("graph_type", [nx.MultiGraph,nx.MultiDiGraph])
@pytest.mark.parametrize("values", [{("a","b","one"):1,("a","b","two"):2}, [1,2]])
def test_parallel_metrics_stay_with_selected_edge(graph_type, values):
    graph = graph_type()
    graph.add_edge("a","b",key="one",original=True)
    graph.add_edge("a","b",key="two",original=True)
    result = QueryResult(target="edges",items=[("a","b","one"),("a","b","two")], attributes={"score":values})
    before = deepcopy(result.attributes)
    exported = result.to_networkx(SimpleNamespace(core_network=graph))
    assert exported["a"]["b"]["one"]["score"] == 1
    assert exported["a"]["b"]["two"]["score"] == 2
    assert all("score" not in data for _,_,data in graph.edges(data=True))
    assert result.attributes == before

def test_keyed_override_of_endpoint_fallback():
    graph=nx.MultiGraph()
    graph.add_edge("a","b",key="one")
    graph.add_edge("a","b",key="two")
    result=QueryResult(target="edges", items=[("a","b","one"),("a","b","two")], attributes={"score":{("a","b"):9,("a","b","one"):1}})
    exported=result.to_networkx(SimpleNamespace(core_network=graph))
    assert exported["a"]["b"]["one"]["score"] == 1
    assert exported["a"]["b"]["two"]["score"] == 9

def test_short_positional_edge_metrics_keep_source_for_missing_values():
    graph=nx.Graph()
    graph.add_edge("a","b",score=9)
    graph.add_edge("b","c",score=8)
    result=QueryResult(target="edges",items=[("a","b"),("b","c")],attributes={"score":[1]})
    exported=result.to_networkx(SimpleNamespace(core_network=graph))
    assert exported["a"]["b"]["score"] == 1
    assert exported["b"]["c"]["score"] == 8
