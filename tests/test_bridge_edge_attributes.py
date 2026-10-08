"""Bridge exports preserve individual edge keys and attributes."""

from copy import deepcopy

import networkx as nx
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.io.multinet_bridge import (
    multilayergraph_to_multinet,
    multinet_to_multilayergraph_with_metadata,
)


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("network_type", ["multilayer", "multiplex"])
def test_bridge_preserves_parallel_edges(directed, network_type):
    net = multi_layer_network(directed=directed, network_type=network_type)
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "social",
                "target_type": "social",
                "key": 3,
                "weight": 1.0,
                "label": "first",
            },
            {
                "source": "A",
                "target": "B",
                "source_type": "social",
                "target_type": "social",
                "key": 8,
                "weight": 9.0,
                "label": "second",
                "payload": {"sample": 2},
            },
            {
                "source": "A",
                "target": "A",
                "source_type": "social",
                "target_type": "social",
                "key": 5,
                "weight": 2.0,
            },
            {
                "source": "A",
                "target": "C",
                "source_type": "social",
                "target_type": "work",
                "key": 4,
                "weight": 4.0,
            },
        ]
    )
    net.add_edges(
        [
            {
                "source": "A",
                "target": "A",
                "source_type": "social",
                "target_type": "work",
                "key": 7,
                "type": "coupling",
                "weight": 0.5,
            }
        ]
    )
    before = deepcopy(list(net.core_network.edges(keys=True, data=True)))
    graph, metadata = multinet_to_multilayergraph_with_metadata(net)
    assert len(graph.edges) == 5
    assert {edge.key for edge in graph.edges} == {3, 8, 5, 4, 7}
    parallel = {edge.key: edge for edge in graph.edges if edge.dst == "B@@@social"}
    assert parallel[3].attributes["label"] == "first"
    assert parallel[8].attributes["weight"] == 9.0
    assert "edge_payload" in metadata["json_encoded_columns"]
    assert metadata["attribute_type_manifest"]["edge_payload"] == "dict"

    restored = multilayergraph_to_multinet(graph)
    assert restored.directed is directed
    assert restored.network_type == network_type
    assert list(net.core_network.edges(keys=True, data=True)) == before
    assert list(restored.core_network.edges(keys=True, data=True)) == before


@pytest.mark.parametrize("directed", [False, True])
def test_bridge_supports_simple_networkx_graphs(directed):
    net = multi_layer_network(directed=directed)
    net.core_network = nx.DiGraph() if directed else nx.Graph()
    net.core_network.add_edge(
        ("A", "social"), ("B", "social"), weight=7, payload={"sample": 1}
    )
    graph, metadata = multinet_to_multilayergraph_with_metadata(net)
    assert len(graph.edges) == 1
    assert graph.edges[0].attributes == {"weight": 7, "payload": '{"sample": 1}'}
    assert "edge_payload" in metadata["json_encoded_columns"]
    restored = multilayergraph_to_multinet(graph)
    assert restored.core_network.get_edge_data(("A", "social"), ("B", "social"))[0] == {
        "weight": 7,
        "payload": {"sample": 1},
    }


@pytest.mark.parametrize("directed", [False, True])
def test_arrow_roundtrip_preserves_parallel_edge_data(directed, tmp_path):
    pytest.importorskip("pyarrow")
    from py3plex.io import load_from_arrow, save_to_arrow

    net = multi_layer_network(directed=directed)
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "social",
                "target_type": "social",
                "key": 3,
                "weight": 1.0,
                "label": "first",
            },
            {
                "source": "A",
                "target": "B",
                "source_type": "social",
                "target_type": "social",
                "key": 8,
                "weight": 9.0,
                "label": "second",
            },
        ]
    )
    path = tmp_path / "parallel.arrow"
    save_to_arrow(net, path)
    restored = load_from_arrow(path)
    assert restored.directed is directed
    assert list(restored.core_network.edges(keys=True, data=True)) == list(
        net.core_network.edges(keys=True, data=True)
    )
