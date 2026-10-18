"""Sparse and monoplex conversions must retain graph data and direction."""

import networkx as nx
import numpy as np
import pytest
import scipy.io
import scipy.sparse as sp

from py3plex.core.multinet import multi_layer_network
from py3plex.core.nx_compat import nx_to_scipy_sparse_matrix


@pytest.mark.parametrize("initial_directed", [False, True])
@pytest.mark.parametrize("override", [False, True])
def test_sparse_conversion_preserves_weights_and_direction(
    tmp_path, initial_directed, override
):
    directed = not initial_directed if override else initial_directed
    values = np.array([[0, 2.5, 0], [0, -0.75, 4.25], [0, 0, 0]])
    if not directed:
        values[1, 0] = values[0, 1]
        values[2, 1] = values[1, 2]
    path = tmp_path / "weighted.mat"
    scipy.io.savemat(path, {"network": sp.csr_matrix(values), "group": [[0, 1, 0]]})
    net = multi_layer_network(directed=initial_directed, dummy_layer="contacts")
    net.load_network(str(path), input_type="sparse")
    assert net.sparse_enabled

    net.sparse_to_px(directed=directed if override else None)

    assert net.directed is directed
    assert net.core_network.is_directed() is directed
    assert net.core_network.is_multigraph()
    assert not net.sparse_enabled
    nodes = [(i, "contacts") for i in range(3)]
    actual = nx_to_scipy_sparse_matrix(net.core_network, nodelist=nodes)
    np.testing.assert_array_equal(actual.toarray(), values)


@pytest.mark.parametrize("directed", [False, True])
def test_sparse_roundtrip_preserves_isolated_rows(directed):
    net = multi_layer_network(directed=directed)
    net.add_nodes([{"source": i, "type": "L"} for i in range(4)])
    net.add_edges([[0, "L", 1, "L", 3.5]], input_type="list")
    net.to_sparse_matrix(replace_core=True)

    net.sparse_to_px()

    assert set(net.core_network) == {(i, "null") for i in range(4)}
    assert set(nx.isolates(net.core_network)) == {(2, "null"), (3, "null")}


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("size", [0, 3])
def test_sparse_conversion_without_edges_preserves_nodes(directed, size):
    net = multi_layer_network(directed=directed)
    net.core_network = sp.csr_matrix((size, size))
    net.sparse_enabled = True

    net.sparse_to_px()

    assert set(net.core_network) == {(i, "null") for i in range(size)}
    assert net.core_network.number_of_edges() == 0
    assert net.core_network.is_directed() is directed
    assert not net.sparse_enabled


@pytest.mark.parametrize(
    "graph_type", [nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph]
)
def test_dummy_layers_preserves_graph_node_and_edge_data(graph_type):
    graph = graph_type(project="experiment")
    graph.add_node("isolated", label="control")
    graph.add_node("A", color="red")
    graph.add_edge("A", "B", weight=2.5, evidence="measured")
    graph.add_edge("B", "B", weight=-0.75)
    if graph.is_multigraph():
        graph.add_edge("A", "B", key="replicate", weight=7.5)
    original = graph.copy()
    net = multi_layer_network(directed=graph.is_directed(), dummy_layer="measurements")
    net.core_network = graph

    assert net.add_dummy_layers() is net

    converted = net.core_network
    assert set(converted) == {(node, "measurements") for node in graph}
    assert converted.graph == graph.graph
    assert converted.is_directed() is graph.is_directed()
    assert converted.is_multigraph()
    for node, data in graph.nodes(data=True):
        assert converted.nodes[(node, "measurements")] == data
    assert converted.number_of_edges() == graph.number_of_edges()
    if graph.is_multigraph():
        for u, v, key, data in graph.edges(keys=True, data=True):
            assert converted[(u, "measurements")][(v, "measurements")][key] == data
    else:
        for u, v, data in graph.edges(data=True):
            assert converted[(u, "measurements")][(v, "measurements")][0] == data
    # Relabeling the wrapper must not relabel or modify a caller-owned graph.
    assert nx.utils.graphs_equal(graph, original)
