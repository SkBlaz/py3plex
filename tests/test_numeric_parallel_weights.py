"""Numeric adjacency must add parallel edge weights rather than overwrite them."""

import networkx as nx
import numpy as np
import pytest

from py3plex.core.multinet import multi_layer_network


def _export(net, accessor):
    if accessor == "tensor":
        return net.get_tensor("csr").toarray()
    matrix = net.get_supra_adjacency_matrix(mtype=accessor)
    return matrix.toarray() if accessor == "sparse" else np.asarray(matrix)


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("accessor", ["tensor", "sparse", "dense"])
@pytest.mark.parametrize("reverse_insertion", [False, True])
def test_parallel_weights_match_networkx_adjacency(
    directed, accessor, reverse_insertion
):
    net = multi_layer_network(directed=directed)
    nodes = [(0, "L1"), ("0", "L1"), (0, "L2"), ("isolated", "L2")]
    net.add_nodes([dict(source=node, type=layer) for node, layer in nodes])
    edges = [
        (nodes[0], nodes[1], 2.5),
        (nodes[0], nodes[1], 3.25),
        (nodes[1], nodes[0], 4.5),  # Reciprocal arc, or another undirected edge.
        (nodes[0], nodes[0], 0.5),
        (nodes[0], nodes[0], 1.25),  # Parallel self-loops contribute once each.
        (nodes[0], nodes[2], -2.0),
        (nodes[0], nodes[2], 5.0),  # Cross-layer edges also sum.
        (nodes[1], nodes[2], 4.0),
        (nodes[1], nodes[2], 0.0),  # Zero must not erase existing weight.
        (nodes[2], nodes[2], 3.0),
        (nodes[2], nodes[2], -3.0),  # Cancellation is a zero matrix entry.
    ]
    if reverse_insertion:
        edges.reverse()
    for (u, lu), (v, lv), weight in edges:
        net.add_edges(
            [dict(source=u, target=v, source_type=lu, target_type=lv, weight=weight)]
        )
    before = list(net.core_network.edges(keys=True, data=True))
    expected = nx.to_numpy_array(net.core_network, nodelist=nodes)

    actual = _export(net, accessor)

    np.testing.assert_array_equal(actual, expected)
    assert actual.shape == (4, 4)
    assert np.count_nonzero(actual[3]) == 0
    assert list(net.core_network.edges(keys=True, data=True)) == before


@pytest.mark.parametrize("directed", [False, True])
def test_parallel_weights_keep_existing_per_edge_normalization(directed):
    net = multi_layer_network(directed=directed)
    # Missing, invalid and None weights already default to 1 per edge; strings
    # are converted to floats. Summation must follow that existing conversion.
    for attributes in [{}, {"weight": "2.5"}, {"weight": "invalid"}, {"weight": None}]:
        net.add_edges(
            [
                dict(
                    source="A",
                    target="B",
                    source_type="L",
                    target_type="L",
                    **attributes,
                )
            ]
        )

    actual = net.get_tensor("csr").toarray()

    expected = np.array([[0.0, 5.5], [0.0 if directed else 5.5, 0.0]])
    np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("weight", [0.0, -2.5, 4.25])
def test_single_edges_keep_their_weights(directed, weight):
    net = multi_layer_network(directed=directed)
    net.add_edges(
        [dict(source="A", target="B", source_type="L", target_type="L", weight=weight)]
    )

    np.testing.assert_array_equal(
        net.get_tensor("csr").toarray(), nx.to_numpy_array(net.core_network)
    )
