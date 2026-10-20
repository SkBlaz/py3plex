"""Layer discovery must retain valid, mutually unorderable identifiers."""

import pytest

from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import Q
from py3plex.dsl.layers import LayerSet


@pytest.mark.parametrize(
    "layers, expected",
    [
        (["work", "social", "work"], ["social", "work"]),
        ([2, 0, 1, 0], [0, 1, 2]),
        (["social", 0, "social", "0"], ["social", 0, "0"]),
        ([None, "social", None], [None, "social"]),
        ([("a", 1), ("a", "one")], [("a", 1), ("a", "one")]),
        ([], []),
    ],
)
def test_layers_preserve_identifiers_and_order(layers, expected):
    net = multi_layer_network(verbose=False)
    net.add_nodes([{"source": i, "type": layer} for i, layer in enumerate(layers)])
    before = list(net.core_network.nodes(data=True))

    assert net.layers == expected
    assert net.layer_names == expected
    assert net.layer_count == len(expected)
    assert net.layers == expected  # Repeated introspection is stable.
    assert list(net.core_network.nodes(data=True)) == before


def test_string_layer_query_on_network_with_numeric_layers():
    net = multi_layer_network(verbose=False)
    net.add_nodes(
        [
            {"source": "alice", "type": "social"},
            {"source": "bob", "type": 0},
        ]
    )

    assert LayerSet("*").resolve(net) == {"social", "0"}
    result = Q.nodes().from_layers(LayerSet("social")).execute(net)
    assert result.items == [("alice", "social")]
