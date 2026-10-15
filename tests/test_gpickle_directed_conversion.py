"""Explicit gpickle direction applies to simple and parallel-edge graphs alike."""

import networkx as nx
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.core.nx_compat import nx_write_gpickle
from py3plex.core.parsers import parse_gpickle


@pytest.mark.parametrize("graph_type", [nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph])
@pytest.mark.parametrize("directed", [False, True])
def test_gpickle_honors_requested_direction(tmp_path, graph_type, directed):
    graph = graph_type(project="direction-conversion", seed=0)
    a, b, isolated = ("A", "social"), ("B", "work"), ("isolated", "work")
    graph.add_nodes_from([(a, {"role": "source"}), (b, {"role": "target"}), (isolated, {})])
    if graph.is_multigraph():
        graph.add_edge(a, b, key="contact", weight=2.5)
        graph.add_edge(a, b, key="message", weight=7.0)
        graph.add_edge(b, b, key="loop", weight=3.0)
    else:
        graph.add_edge(a, b, weight=2.5)
        graph.add_edge(b, b, weight=3.0)
    path = str(tmp_path / "network.gpickle")
    nx_write_gpickle(graph, path)
    expected = nx.MultiDiGraph(graph) if directed else nx.MultiGraph(graph)

    actual, labels = parse_gpickle(path, directed=directed)
    assert labels is None
    assert actual.is_directed() is directed
    assert nx.utils.graphs_equal(actual, expected)

    # The public loader must agree with both its flag and the parser result.
    net = multi_layer_network()
    net.load_network(path, input_type="gpickle", directed=directed)
    assert net.directed is directed
    assert nx.utils.graphs_equal(net.core_network, expected)
