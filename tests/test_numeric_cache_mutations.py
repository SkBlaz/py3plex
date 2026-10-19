"""Matrix exports must reflect public graph mutations after a cached export."""

import networkx as nx
import numpy as np
import pytest

from py3plex.core.multinet import multi_layer_network


def _edge(source, target, weight, layer="L", key="ab"):
    return dict(
        source=source,
        target=target,
        source_type=layer,
        target_type=layer,
        weight=weight,
        key=key,
    )


def _export(net, accessor):
    if accessor == "tensor":
        return net.get_tensor("csr").toarray()
    return np.asarray(net.get_supra_adjacency_matrix(mtype="dense"))


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("accessor", ["tensor", "supra"])
@pytest.mark.parametrize(
    "mutation",
    ["add_node", "add_edge", "update_weight", "remove_node", "remove_edge", "reload"],
)
def test_matrix_after_mutation_matches_current_graph(directed, accessor, mutation):
    net = multi_layer_network(directed=directed)
    net.add_nodes([dict(source=n, type="L") for n in ["A", "B", "C"]])
    net.add_edges([_edge("A", "B", 2.5)])
    original = _export(net, accessor)
    snapshot = original.copy()
    version = net.network_version

    if mutation == "add_node":
        net.add_nodes([dict(source="D", type="L")])
    elif mutation == "add_edge":
        net.add_edges([_edge("B", "C", -3.5, key="bc")])
    elif mutation == "update_weight":
        net.add_edges([_edge("A", "B", 7.25)])
    elif mutation == "remove_node":
        net.remove_nodes([dict(source="A", type="L")])
    elif mutation == "remove_edge":
        net.remove_edges([_edge("A", "B", 2.5)], input_type="dict")
    else:
        graph = nx.MultiDiGraph() if directed else nx.MultiGraph()
        graph.add_nodes_from([(n, "new") for n in ["W", "X", "Y", "Z"]])
        graph.add_edge(("W", "new"), ("Z", "new"), weight=9.0)
        net.load_network(graph, input_type="nx")

    assert net.network_version == version + 1
    expected = nx.to_numpy_array(net.core_network, nodelist=list(net.core_network))
    np.testing.assert_array_equal(_export(net, accessor), expected)
    assert len(net.node_order_in_matrix) == len(net.core_network)
    np.testing.assert_array_equal(original, snapshot)


@pytest.mark.parametrize("directed", [False, True])
def test_multiplex_matrix_refreshes_weighted_blocks(directed):
    net = multi_layer_network(network_type="multiplex", directed=directed)
    for layer in ["L1", "L2"]:
        net.add_nodes([dict(source=n, type=layer) for n in ["A", "B"]])
        net.add_edges([_edge("A", "B", 2.5, layer=layer)])
    net._couple_all_edges()
    original = net.get_tensor("csr").toarray()

    net.add_edges([_edge("A", "B", 8.0, layer="L2")])

    expected = nx.to_numpy_array(net.core_network, nodelist=list(net.core_network))
    actual = net.get_supra_adjacency_matrix().toarray()
    np.testing.assert_array_equal(actual, expected)
    assert actual[2, 3] == 8.0
    assert original[2, 3] == 2.5


def test_matrix_reads_without_mutation_reuse_cached_encoding():
    net = multi_layer_network(directed=False)
    net.add_edges([_edge("A", "B", 2.5)])
    original = net.get_supra_adjacency_matrix()
    version = net.network_version

    net.get_tensor("csr")

    assert net.get_supra_adjacency_matrix() is original
    assert net.network_version == version
