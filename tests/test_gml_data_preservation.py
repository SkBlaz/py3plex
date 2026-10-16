"""GML loading retains isolated replicas and serialized graph data."""

import networkx as nx
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.core.parsers import parse_gml


@pytest.mark.parametrize("graph_type", [nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph])
@pytest.mark.parametrize("connected", [False, True])
def test_gml_preserves_all_replicas_and_data(tmp_path, graph_type, connected):
    graph = graph_type(project="study", seed=0)
    graph.add_node("A", type="social", role="source")
    graph.add_node("B", type="work", role="target")
    graph.add_node("isolated", type="isolates", role="isolated")
    if connected:
        if graph.is_multigraph():
            graph.add_edge("A", "B", key="contact", weight=2.5)
            graph.add_edge("A", "B", key="message", weight=7.0)
            graph.add_edge("B", "B", key="loop", weight=3.0)
        else:
            graph.add_edge("A", "B", weight=2.5)
            graph.add_edge("B", "B", weight=3.0)
    path = str(tmp_path / "network.gml")
    nx.write_gml(graph, path)

    actual, labels = parse_gml(path, directed=graph.is_directed())
    expected = nx.relabel_nodes(graph, {n: (n, data["type"]) for n, data in graph.nodes(data=True)})
    expected = nx.MultiDiGraph(expected) if graph.is_directed() else nx.MultiGraph(expected)
    assert labels is None
    assert nx.utils.graphs_equal(actual, expected)

    net = multi_layer_network(directed=graph.is_directed())
    assert net.load_network(path, directed=graph.is_directed(), input_type="gml") is net
    assert nx.utils.graphs_equal(net.core_network, expected)


@pytest.mark.parametrize("directed", [False, True])
def test_empty_gml_preserves_graph_metadata(tmp_path, directed):
    graph = nx.MultiDiGraph(project="empty") if directed else nx.MultiGraph(project="empty")
    path = str(tmp_path / "empty.gml")
    nx.write_gml(graph, path)
    actual, _ = parse_gml(path, directed=directed)
    assert nx.utils.graphs_equal(actual, graph)
