import numpy as np
import pandas as pd
import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.io.canonical_format import (
    ConversionError as CanonicalConversionError,
    network_to_tables,
    tables_to_network,
)
from py3plex.io.multinet_bridge import (
    ConversionError as BridgeConversionError,
    multinet_to_multilayergraph,
    multilayergraph_to_multinet,
    multinet_to_multilayergraph_with_metadata,
)


def _build_sample_network() -> multi_layer_network:
    net = multi_layer_network(
        network_type="multilayer", directed=False, coupling_weight=2
    )
    net.add_nodes(
        [
            {
                "source": "A",
                "type": "social",
                "score": np.int64(5),
                "vector": np.array([1, 2, 3]),
                "profile": {"team": "core"},
            },
            {"source": "B", "type": "social"},
            {"source": "A", "type": "work", "active": True},
        ]
    )
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "social",
                "target_type": "social",
                "weight": np.float64(1.5),
                "tags": ["x", "y"],
            },
            {
                "source": "A",
                "target": "A",
                "source_type": "social",
                "target_type": "work",
                "payload": {"kind": "coupling"},
            },
        ]
    )
    return net


def test_canonical_tables_roundtrip_preserves_structure_and_attributes():
    net = _build_sample_network()

    nodes_df, edges_df, metadata = network_to_tables(net)

    assert set(nodes_df.columns) >= {"node", "layer", "score", "vector", "profile"}
    assert set(edges_df.columns) >= {
        "source",
        "target",
        "source_layer",
        "target_layer",
        "weight",
        "tags",
        "payload",
    }
    assert metadata["network_type"] == "multilayer"
    assert metadata["directed"] is False
    assert metadata["coupling_weight"] == 2
    assert metadata["node_count"] == 3
    assert metadata["edge_count"] == 2

    restored = tables_to_network(nodes_df, edges_df, metadata)

    assert set(restored.get_nodes()) == set(net.get_nodes())
    assert set(restored.get_edges()) == set(net.get_edges())

    restored_node_attrs = restored.core_network.nodes[("A", "social")]
    assert restored_node_attrs["score"] == 5
    assert restored_node_attrs["vector"] == [1, 2, 3]
    assert restored_node_attrs["profile"] == {"team": "core"}

    restored_edge_attrs = restored.core_network.get_edge_data(
        ("A", "social"), ("B", "social")
    )[0]
    assert restored_edge_attrs["weight"] == pytest.approx(1.5)
    assert restored_edge_attrs["tags"] == ["x", "y"]

    restored_payload_attrs = restored.core_network.get_edge_data(
        ("A", "social"), ("A", "work")
    )[0]
    assert restored_payload_attrs["payload"] == {"kind": "coupling"}


def test_canonical_tables_raises_on_uninitialized_empty_network():
    net = multi_layer_network(network_type="multilayer", directed=True)

    with pytest.raises(CanonicalConversionError):
        network_to_tables(net)

    nodes_df = pd.DataFrame(columns=["node", "layer"])
    edges_df = pd.DataFrame(columns=["source", "target", "source_layer", "target_layer"])

    restored = tables_to_network(
        nodes_df,
        edges_df,
        {"network_type": "multilayer", "directed": True, "coupling_weight": 1},
    )
    assert restored.core_network is None
    assert restored.directed is True


def test_tables_to_network_skips_nan_attributes():
    nodes_df = pd.DataFrame(
        [
            {"node": "n1", "layer": "social", "nan_attr": np.nan, "payload": '{"x": 1}'},
            {"node": "n2", "layer": "social", "nan_attr": np.nan},
        ]
    )
    edges_df = pd.DataFrame(
        [
            {
                "source": "n1",
                "target": "n2",
                "source_layer": "social",
                "target_layer": "social",
                "nan_edge_attr": np.nan,
                "weight": 2.0,
            }
        ]
    )

    restored = tables_to_network(
        nodes_df,
        edges_df,
        {"network_type": "multilayer", "directed": False, "coupling_weight": 1},
    )

    node_attrs = restored.core_network.nodes[("n1", "social")]
    assert "nan_attr" not in node_attrs
    assert node_attrs["payload"] == {"x": 1}

    edge_attrs = restored.core_network.get_edge_data(("n1", "social"), ("n2", "social"))[0]
    assert "nan_edge_attr" not in edge_attrs
    assert edge_attrs["weight"] == 2.0


def test_multinet_bridge_roundtrip_preserves_nodes_edges_and_attrs():
    net = _build_sample_network()

    graph = multinet_to_multilayergraph(net)

    assert graph.directed is False
    assert "social" in graph.layers
    assert "work" in graph.layers
    assert "A@@@social" in graph.nodes
    assert any(edge.src_layer == "social" and edge.dst_layer == "work" for edge in graph.edges)

    restored = multilayergraph_to_multinet(graph)

    assert set(restored.get_nodes()) == set(net.get_nodes())
    assert set(restored.get_edges()) == set(net.get_edges())
    assert restored.core_network.nodes[("A", "social")]["profile"] == {"team": "core"}


def test_multinet_bridge_metadata_tracks_json_encoded_columns_and_types():
    net = _build_sample_network()

    _, metadata = multinet_to_multilayergraph_with_metadata(net)

    assert metadata["network_type"] == "multilayer"
    assert metadata["directed"] is False
    assert metadata["coupling_weight"] == 2
    assert "node_vector" in metadata["json_encoded_columns"]
    assert "node_profile" in metadata["json_encoded_columns"]
    assert "edge_payload" in metadata["json_encoded_columns"]
    assert metadata["attribute_type_manifest"]["node_vector"] == "ndarray"
    assert metadata["attribute_type_manifest"]["edge_payload"] == "dict"


def test_conversion_functions_raise_domain_specific_errors_on_invalid_input():
    with pytest.raises(CanonicalConversionError):
        network_to_tables(None)

    with pytest.raises(BridgeConversionError):
        multinet_to_multilayergraph(None)
