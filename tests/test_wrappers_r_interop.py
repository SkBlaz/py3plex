from __future__ import annotations

import numpy as np
import pytest

networkx = pytest.importorskip("networkx")

from py3plex.core import multinet  # noqa: E402
from py3plex.wrappers import r_interop  # noqa: E402


def _sample_network() -> multinet.multi_layer_network:
    net = multinet.multi_layer_network(directed=False, verbose=False)
    net.add_edges(
        [
            {"source": "a", "target": "b", "source_type": "L1", "target_type": "L1", "weight": 2.0},
            {"source": "b", "target": "c", "source_type": "L2", "target_type": "L2"},
        ]
    )
    return net


def test_export_edgelist_derives_layer_from_nodes_when_missing_attributes():
    net = _sample_network()

    edges = r_interop.export_edgelist(net, include_attributes=True)
    edge_map = {(e["src"], e["dst"]): e for e in edges}

    e1 = edge_map[(("a", "L1"), ("b", "L1"))]
    assert e1["src_layer"] == "L1"
    assert e1["dst_layer"] == "L1"
    assert e1["weight"] == 2.0

    e2 = edge_map[(("b", "L2"), ("c", "L2"))]
    assert e2["src_layer"] == "L2"
    assert e2["dst_layer"] == "L2"
    assert "weight" not in e2  # no weight provided


def test_get_network_stats_matches_network_properties():
    net = _sample_network()

    stats = r_interop.get_network_stats(net)

    assert stats["num_nodes"] == 4  # nodes are (id, layer) tuples
    assert stats["num_edges"] == 2
    assert stats["num_layers"] == 2
    assert stats["directed"] is False


def test_export_adjacency_matches_network_when_igraph_available():
    igraph = pytest.importorskip("igraph")
    net = _sample_network()

    adj = r_interop.export_adjacency(net)
    mat = np.asarray(adj)

    assert mat.shape == (4, 4)
    # Edges: (a,L1)-(b,L1) and (b,L2)-(c,L2)
    expected = np.zeros((4, 4))
    expected[0, 1] = expected[1, 0] = 1.0
    expected[2, 3] = expected[3, 2] = 1.0
    np.testing.assert_allclose(mat, expected)
