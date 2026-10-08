"""Bridge roundtrips preserve node and layer identities."""

import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.io.multinet_bridge import (
    multilayergraph_to_multinet,
    multinet_to_multilayergraph,
)


@pytest.mark.parametrize(
    "node_id",
    [
        0,
        7,
        1.25,
        False,
        "",
        "null",
        "true",
        "false",
        "[1,2]",
        '{"a":1}',
        "left@@@right",
    ],
)
@pytest.mark.parametrize("layer", ["social", 3])
@pytest.mark.parametrize("directed", [False, True])
def test_bridge_preserves_endpoint_and_layer_identity(node_id, layer, directed):
    net = multi_layer_network(directed=directed)
    net.add_nodes([{"source": node_id, "type": layer, "score": 5}])
    net.add_edges(
        [
            {
                "source": node_id,
                "target": "anchor",
                "source_type": layer,
                "target_type": layer,
                "weight": 2,
            }
        ]
    )
    restored = multilayergraph_to_multinet(multinet_to_multilayergraph(net))
    assert set(restored.get_nodes()) == set(net.get_nodes())
    assert list(restored.get_edges(data=True)) == list(net.get_edges(data=True))
    assert restored.core_network.nodes[(node_id, layer)]["score"] == 5


@pytest.mark.parametrize("node_id", [0, False, "null", "true", "[1,2]", "left@@@right"])
@pytest.mark.parametrize("layer", ["social", 3])
def test_arrow_preserves_endpoint_and_layer_identity(node_id, layer, tmp_path):
    pytest.importorskip("pyarrow")
    from py3plex.io import load_from_arrow, save_to_arrow

    net = multi_layer_network(directed=True)
    net.add_edges(
        [
            {
                "source": node_id,
                "target": "anchor",
                "source_type": layer,
                "target_type": layer,
                "weight": 2,
            }
        ]
    )
    path = tmp_path / "identity.arrow"
    save_to_arrow(net, path)
    restored = load_from_arrow(path)
    assert set(restored.get_nodes()) == set(net.get_nodes())
    assert list(restored.get_edges(data=True)) == list(net.get_edges(data=True))
