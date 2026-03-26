"""Edge-case coverage tests for DSL result algebra and empty pipelines."""

from py3plex.core import multinet
from py3plex.dsl import L, Q
from py3plex.dsl.algebra import IdentityStrategy


def _make_small_multilayer_network():
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes(
        [
            {"source": "A", "type": "social"},
            {"source": "B", "type": "social"},
            {"source": "C", "type": "social"},
            {"source": "A", "type": "work"},
            {"source": "B", "type": "work"},
        ]
    )
    net.add_edges(
        [
            {
                "source": "A",
                "target": "B",
                "source_type": "social",
                "target_type": "social",
            },
            {
                "source": "A",
                "target": "B",
                "source_type": "work",
                "target_type": "work",
            },
        ]
    )
    return net


def _set_replica_identity(*results):
    for result in results:
        result.meta["identity_strategy"] = IdentityStrategy.BY_REPLICA


def test_chained_filters_return_empty_safely():
    net = _make_small_multilayer_network()

    result = (
        Q.nodes()
        .compute("degree")
        .where(degree__gt=100)
        .order_by("degree", desc=True)
        .limit(5)
        .execute(net)
    )

    assert len(result.items) == 0
    assert result.to_pandas().empty


def test_union_with_empty_result_preserves_nonempty_items():
    net = _make_small_multilayer_network()
    nonempty = Q.nodes().execute(net)
    empty = (
        Q.nodes()
        .from_layers(L["social"])
        .compute("degree")
        .where(degree__gt=100)
        .execute(net)
    )

    _set_replica_identity(nonempty, empty)

    union = nonempty | empty

    assert set(union.items) == set(nonempty.items)
    assert union.meta["algebra_operation"] == "union"
    assert union.meta["result_count"] == len(nonempty.items)


def test_intersection_with_empty_result_is_empty():
    net = _make_small_multilayer_network()
    nonempty = Q.nodes().execute(net)
    empty = (
        Q.nodes()
        .from_layers(L["social"])
        .compute("degree")
        .where(degree__gt=100)
        .execute(net)
    )

    _set_replica_identity(nonempty, empty)

    intersection = nonempty & empty

    assert intersection.items == []
    assert intersection.meta["algebra_operation"] == "intersection"
    assert intersection.meta["result_count"] == 0
