"""Loading must honor directedness already configured on the network."""

import networkx as nx
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.core.nx_compat import nx_write_gpickle


@pytest.mark.parametrize("input_type", ["edgelist", "multiedgelist", "gml", "gpickle"])
@pytest.mark.parametrize("directed", [False, True])
def test_load_inherits_constructor_directedness(tmp_path, input_type, directed):
    path = tmp_path / ("network." + input_type)
    if input_type in {"edgelist", "multiedgelist"}:
        path.write_text("A L B L 2.5\n")
    else:
        graph = nx.MultiDiGraph() if directed else nx.MultiGraph()
        graph.add_nodes_from([("A", {"type": "L"}), ("B", {"type": "L"})])
        graph.add_edge("A", "B", weight=2.5)
        if input_type == "gml":
            nx.write_gml(graph, str(path))
        else:
            graph = nx.relabel_nodes(graph, {"A": ("A", "L"), "B": ("B", "L")})
            nx_write_gpickle(graph, str(path))

    net = multi_layer_network(directed=directed)
    assert net.load_network(str(path), input_type=input_type) is net
    assert net.directed is directed
    assert net.core_network.is_directed() is directed
    assert net.core_network.has_edge(("A", "L"), ("B", "L"))
    assert net.core_network.has_edge(("B", "L"), ("A", "L")) is (not directed)


@pytest.mark.parametrize("directed", [False, True])
def test_explicit_load_directedness_overrides_constructor(tmp_path, directed):
    path = tmp_path / "network.edges"
    path.write_text("A L B L 2.5\n")
    net = multi_layer_network(directed=not directed)
    net.load_network(str(path), input_type="multiedgelist", directed=directed)
    assert net.directed is directed
    assert net.core_network.is_directed() is directed

    # An omitted argument on subsequent loads retains the current setting.
    net.load_network(str(path), input_type="multiedgelist")
    assert net.directed is directed
    assert net.core_network.is_directed() is directed
