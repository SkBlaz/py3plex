"""The advertised GraphML loader must preserve complete multilayer graphs."""

import networkx as nx
import pytest

from py3plex.core.multinet import multi_layer_network


@pytest.mark.parametrize("source_directed", [False, True])
@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("parallel", [False, True])
def test_graphml_loading_preserves_data(tmp_path, source_directed, directed, parallel):
    source = nx.MultiDiGraph() if source_directed else nx.MultiGraph()
    source.graph["study"] = "GraphML"
    source.add_node("A", type="social", score=3.5)
    source.add_node("B", type="work", score=0.0)
    source.add_node("isolated", type="social", score=-1.0)
    source.add_edge("A", "B", key="first", weight=2.5, relation="contact")
    if parallel:
        source.add_edge("A", "B", key="second", weight=7.0, relation="friend")
    path = tmp_path / "network.graphml"
    nx.write_graphml(source, str(path))

    net = multi_layer_network(directed=directed)
    assert net.load_network(str(path), input_type="graphml") is net
    graph = net.core_network
    a, b = ("A", "social"), ("B", "work")
    assert graph.is_directed() is directed
    assert graph.is_multigraph()
    assert graph.graph["study"] == "GraphML"
    assert dict(graph.nodes(data=True)) == {
        ("A", "social"): {"type": "social", "score": 3.5},
        ("B", "work"): {"type": "work", "score": 0.0},
        ("isolated", "social"): {"type": "social", "score": -1.0},
    }
    assert graph[a][b]["first"] == {"weight": 2.5, "relation": "contact"}
    if parallel:
        assert graph[a][b]["second"] == {"weight": 7.0, "relation": "friend"}
    assert graph.has_edge(b, a) is (not source_directed or not directed)
    expected_edges = (2 if parallel else 1) * (2 if directed and not source_directed else 1)
    assert graph.number_of_edges() == expected_edges


@pytest.mark.parametrize("isolated", [False, True])
def test_graphml_without_edges(tmp_path, isolated):
    source = nx.Graph()
    if isolated:
        source.add_node("alone", type="L")
    path = tmp_path / "empty.graphml"
    nx.write_graphml(source, str(path))
    net = multi_layer_network().load_network(str(path), input_type="graphml")
    assert set(net.core_network) == ({("alone", "L")} if isolated else set())
    assert net.core_network.number_of_edges() == 0


def test_graphml_without_layer_attributes_uses_generic_layer(tmp_path):
    source = nx.Graph()
    source.add_edge("A", "B", weight=4.0)
    path = tmp_path / "untyped.graphml"
    nx.write_graphml(source, str(path))
    net = multi_layer_network().load_network(str(path), input_type="graphml")
    assert set(net.core_network) == {("A", "generic"), ("B", "generic")}
    assert next(iter(net.core_network.edges(data=True)))[2]["weight"] == 4.0


def test_graphml_default_layer(tmp_path):
    path = tmp_path / "defaults.graphml"
    path.write_text('''<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
      <key id="layer" for="node" attr.name="type" attr.type="string">
        <default>social</default>
      </key>
      <graph edgedefault="undirected"><node id="A"/><node id="B">
        <data key="layer">work</data></node><edge source="A" target="B"/>
      </graph></graphml>''')
    net = multi_layer_network().load_network(str(path), input_type="graphml")
    assert set(net.core_network) == {("A", "social"), ("B", "work")}
    assert net.core_network.graph["node_default"] == {"type": "social"}
