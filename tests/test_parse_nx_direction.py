"""NetworkX loading must honor direction without changing the input graph."""

import networkx as nx
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.core.parsers import parse_nx


@pytest.mark.parametrize("graph_type", [nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph])
@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("via_loader", [False, True])
def test_networkx_direction_conversion(graph_type, directed, via_loader):
    source = graph_type(study="direction")
    a, b, isolated = ("A", "L1"), ("B", "L2"), ("isolated", "L1")
    source.add_node(isolated, label="retained")
    source.add_edge(a, b, weight=2.5)
    if source.is_multigraph():
        source.add_edge(a, b, key="parallel", weight=7.0)
    original = source.copy()

    if via_loader:
        net = multi_layer_network(directed=not directed)
        net.load_network(source, input_type="nx", directed=directed)
        result = net.core_network
        assert net.directed is directed
    else:
        result, labels = parse_nx(source, directed=directed)
        assert labels is None

    assert result.is_directed() is directed
    assert result.is_multigraph() is source.is_multigraph()
    assert result.graph == source.graph
    assert dict(result.nodes(data=True)) == dict(source.nodes(data=True))
    assert result.has_edge(a, b)
    # An undirected input becomes reciprocal arcs when directed=True.
    assert result.has_edge(b, a) is (not source.is_directed() or not directed)
    if result.is_multigraph():
        assert result[a][b]["parallel"]["weight"] == 7.0
        assert result.number_of_edges() == (4 if directed and not source.is_directed() else 2)
    else:
        assert result[a][b]["weight"] == 2.5
        assert result.number_of_edges() == (2 if directed and not source.is_directed() else 1)
    if source.is_directed() == directed:
        assert result is source  # Preserve the existing zero-copy path.
    assert nx.utils.graphs_equal(source, original)
