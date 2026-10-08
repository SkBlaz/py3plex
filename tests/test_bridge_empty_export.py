"""I/O conversion must handle empty networks without generating layouts."""

import networkx as nx
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.io.multinet_bridge import multinet_to_multilayergraph_with_metadata


@pytest.mark.parametrize("directed", [False, True])
@pytest.mark.parametrize("initialized", [False, True])
def test_empty_export_preserves_metadata(directed, initialized, monkeypatch):
    net = multi_layer_network(directed=directed, coupling_weight=2)
    if initialized:
        net.core_network = nx.MultiDiGraph() if directed else nx.MultiGraph()

    def forbidden(*args, **kwargs):
        raise AssertionError("Export must not compute visualization layouts")

    monkeypatch.setattr(net, "get_layers", forbidden)
    graph, metadata = multinet_to_multilayergraph_with_metadata(net)
    assert graph.directed is directed
    assert graph.nodes == {}
    assert graph.layers == {}
    assert graph.edges == []
    assert graph.attributes["coupling_weight"] == 2
    assert metadata["directed"] is directed
    assert metadata["attribute_type_manifest"] == {}
    assert metadata["json_encoded_columns"] == []


def test_export_discovers_isolated_and_interlayer_replicas(monkeypatch):
    net = multi_layer_network(directed=True)
    net.add_nodes([{"source": "isolated", "type": "isolates", "score": 7}])
    net.add_edges([{"source": "A", "target": "B", "source_type": "left",
                    "target_type": "right", "weight": 3}])

    def forbidden(*args, **kwargs):
        raise AssertionError("Export must not compute visualization layouts")

    monkeypatch.setattr(net, "get_layers", forbidden)
    graph, _ = multinet_to_multilayergraph_with_metadata(net)
    assert set(graph.layers) == {"isolates", "left", "right"}
    assert graph.nodes["isolated@@@isolates"].attributes["score"] == 7
    assert len(graph.edges) == 1
    edge = graph.edges[0]
    assert (edge.src_layer, edge.dst_layer) == ("left", "right")
    assert edge.attributes["weight"] == 3
