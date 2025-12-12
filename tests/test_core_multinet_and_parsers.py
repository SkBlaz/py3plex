"""Unit tests for py3plex.core utilities."""

import pytest
import scipy.sparse as sp

from py3plex.core.multinet import multi_layer_network
from py3plex.core.parsers import (
    parse_edgelist_multi_types,
    parse_simple_edgelist,
)


def _basic_network():
    """Helper to create a small undirected multilayer network."""
    net = multi_layer_network(directed=False)
    net.add_nodes(
        [
            {"source": "A", "type": "layer1"},
            {"source": "B", "type": "layer1"},
            {"source": "A", "type": "layer2"},
        ]
    )
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "layer1",
                "target_type": "layer1",
            },
            {
                "source": "A",
                "target": "A",
                "source_type": "layer1",
                "target_type": "layer2",
            },
        ]
    )
    return net


def test_pythonic_interface_helpers():
    net = _basic_network()

    assert len(net) == 3
    assert bool(net) is True
    assert net.node_count == 3
    assert net.edge_count == 2
    assert net.layer_count == 2
    assert net.layers == ["layer1", "layer2"]
    assert ("A", "layer1") in net
    assert (("A", "layer1"), ("B", "layer1")) in net
    assert ("missing", "layer1") not in net
    assert (("B", "layer1"), ("missing", "layer1")) not in net
    assert set(iter(net)) == {("A", "layer1"), ("B", "layer1"), ("A", "layer2")}


def test_monoplex_nx_wrapper_runs_networkx_function():
    net = _basic_network()

    centrality = net.monoplex_nx_wrapper("degree_centrality")

    assert centrality[("A", "layer1")] == pytest.approx(1.0)
    assert centrality[("B", "layer1")] == pytest.approx(0.5)
    assert centrality[("A", "layer2")] == pytest.approx(0.5)


def test_monoplex_nx_wrapper_rejects_unknown_method():
    net = _basic_network()

    with pytest.raises(AttributeError):
        net.monoplex_nx_wrapper("nonexistent_metric")


def test_get_tensor_handles_format_conversion_and_warnings():
    net = _basic_network()

    tensor_csr = net.get_tensor(sparsity_type="csr")
    assert sp.isspmatrix_csr(tensor_csr)

    with pytest.warns(UserWarning):
        tensor_unknown = net.get_tensor(sparsity_type="unsupported")

    assert tensor_unknown.shape == tensor_csr.shape
    assert sp.issparse(tensor_unknown)


def test_parsers_read_weights_and_edge_types(tmp_path):
    simple_path = tmp_path / "simple.txt"
    simple_path.write_text("# comment\nu v 2.5\nx y\n")

    simple_graph, _ = parse_simple_edgelist(str(simple_path), directed=False)

    assert simple_graph.number_of_edges() == 2
    assert simple_graph.get_edge_data(("u", "null"), ("v", "null"))["weight"] == 2.5
    assert simple_graph.get_edge_data(("x", "null"), ("y", "null"))["weight"] == 1.0

    multi_type_path = tmp_path / "multi_types.txt"
    multi_type_path.write_text("a b\nc d\n")

    multi_graph, _ = parse_edgelist_multi_types(str(multi_type_path), directed=False)
    first_edge = multi_graph.get_edge_data("a", "b")[0]
    second_edge = multi_graph.get_edge_data("c", "d")[0]

    assert first_edge["type"] is None
    assert first_edge["weight"] == "1"
    assert second_edge["type"] is None
    assert second_edge["weight"] == "1"

    multi_type_invalid = tmp_path / "multi_types_invalid.txt"
    multi_type_invalid.write_text("p q 3.0\n")

    with pytest.raises(IndexError):
        parse_edgelist_multi_types(str(multi_type_invalid), directed=False)
