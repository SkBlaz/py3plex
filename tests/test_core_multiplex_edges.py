"""Correctness tests for multiplex edge handling and removal helpers."""

import pytest

from py3plex.core import multinet


def _build_simple_multiplex():
    """Create a small multiplex network with two layers and one real edge."""
    net = multinet.multi_layer_network(
        network_type="multiplex", directed=False, verbose=False
    )
    # Two nodes present in both layers
    net.add_nodes(
        [
            {"source": "a", "type": "L1"},
            {"source": "a", "type": "L2"},
            {"source": "b", "type": "L1"},
            {"source": "b", "type": "L2"},
        ]
    )
    # One intra-layer edge
    net.add_edges(
        [{"source": "a", "target": "b", "source_type": "L1", "target_type": "L1"}]
    )
    # Create coupling edges between layers
    net._couple_all_edges()
    return net


def test_get_edges_excludes_coupling_edges_by_default():
    """multiplex_edges=False should filter out coupling edges."""
    net = _build_simple_multiplex()

    edges = list(net.get_edges(data=True, multiplex_edges=False))

    assert len(edges) == 1  # only the intra-layer edge remains
    _, _, _, attr = edges[0]
    assert attr.get("type") != "coupling"


def test_get_edges_can_include_coupling_edges_when_requested():
    """multiplex_edges=True should include coupling edges."""
    net = _build_simple_multiplex()

    edges = list(net.get_edges(data=True, multiplex_edges=True))
    coupling_edges = [edge for edge in edges if edge[-1].get("type") == "coupling"]

    assert coupling_edges, "Coupling edges should be present when requested"
    # Ensure the original intra-layer edge is still present
    assert len(edges) > len(coupling_edges)


def test_remove_edges_supports_dict_input_type():
    """remove_edges should accept dict input without raising and remove the edge."""
    net = multinet.multi_layer_network(network_type="multilayer", directed=False, verbose=False)
    edge_dict = {
        "source": "x",
        "target": "y",
        "source_type": "L",
        "target_type": "L",
    }
    net.add_edges([edge_dict])
    assert net.edge_count == 1

    net.remove_edges(edge_dict, input_type="dict")

    assert net.edge_count == 0


def test_remove_edges_invalid_input_type_raises():
    net = multinet.multi_layer_network(verbose=False)
    with pytest.raises(ValueError, match="Invalid input_type"):
        net.remove_edges([], input_type="unknown")
