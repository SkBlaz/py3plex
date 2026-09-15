"""Coverage for conversion dispatch and source format inference."""

import networkx as nx
import pytest
import scipy.sparse as sp

from py3plex.compat import convert
from py3plex.compat.exceptions import ConversionNotSupportedError
from py3plex.io.schema import Edge, Layer, MultiLayerGraph, Node


def _graph():
    graph = MultiLayerGraph(directed=False)
    graph.add_layer(Layer(id="L"))
    graph.add_node(Node(id="A"))
    graph.add_node(Node(id="B"))
    graph.add_edge(Edge(src="A", dst="B", src_layer="L", dst_layer="L"))
    return graph


def test_convert_supports_scipy_source_and_core_network_target():
    matrix = sp.csr_matrix([[0, 1], [1, 0]], dtype=float)

    multilayer_graph = convert(matrix, "py3plex")
    assert len(multilayer_graph.nodes) == 2
    assert len(multilayer_graph.edges) == 2

    core_network = convert(matrix, "multi_layer_network")
    assert core_network.network.number_of_nodes() == 2
    assert core_network.network.number_of_edges() == 2


def test_convert_rejects_unknown_source_format():
    with pytest.raises(TypeError, match="Cannot infer format"):
        convert(object(), "py3plex")


@pytest.mark.parametrize("target", ["igraph", "pyg", "torch_geometric", "dgl"])
def test_optional_targets_report_missing_dependencies(target):
    with pytest.raises(ConversionNotSupportedError):
        convert(_graph(), target)


def test_networkx_source_is_inferred_for_multilayer_graph_target():
    graph = nx.Graph()
    graph.add_edge("A", "B")

    converted = convert(graph, "multilayer_graph")

    assert len(converted.nodes) == 2
    assert len(converted.edges) == 1
