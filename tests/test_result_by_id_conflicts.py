"""Conflict strategies must apply to metrics matched by physical identity."""

from copy import deepcopy
import math
import operator

import pytest

from py3plex.core import multinet
from py3plex.dsl import L, Q
from py3plex.dsl.algebra import (
    AttributeConflictError,
    ConflictResolution,
    IdentityStrategy,
)
from py3plex.dsl.result import QueryResult


def _items(target, identity):
    if target == "nodes":
        left = ("A", "social")
        right = ("A", "work")
    else:
        left = ("A", "B", "social", "social")
        right = ("A", "B", "work", "work")
    return left, right if identity == IdentityStrategy.BY_ID else left


@pytest.mark.parametrize("combine", [operator.or_, operator.and_])
@pytest.mark.parametrize("target", ["nodes", "edges"])
@pytest.mark.parametrize("identity", list(IdentityStrategy))
@pytest.mark.parametrize("strategy", list(ConflictResolution))
@pytest.mark.parametrize("uncertainty", [False, True])
def test_conflicts_follow_strategy_under_selected_identity(
    combine, target, identity, strategy, uncertainty
):
    item1, item2 = _items(target, identity)
    value1 = {"mean": 0, "std": 0.5} if uncertainty else 0
    value2 = {"mean": 8, "std": 0.5} if uncertainty else 8
    left = QueryResult(
        target,
        [item1],
        attributes={"score": {item1: value1}},
        meta={"identity_strategy": identity, "conflict_resolution": strategy},
    )
    right = QueryResult(target, [item2], attributes={"score": {item2: value2}})
    original = deepcopy(
        (
            left.items,
            left.attributes,
            left.meta,
            right.items,
            right.attributes,
            right.meta,
        )
    )

    if strategy == ConflictResolution.ERROR:
        with pytest.raises(AttributeConflictError, match="score"):
            combine(left, right)
    else:
        result = combine(left, right)
        assert result.target == target and result.count == 1
        assert result.items == [item1]
        value = result.attributes["score"][item1]
        if strategy in (ConflictResolution.PREFER_LEFT, ConflictResolution.MIN):
            assert value == value1
        elif strategy in (ConflictResolution.PREFER_RIGHT, ConflictResolution.MAX):
            assert value == value2
        elif strategy == ConflictResolution.KEEP_BOTH:
            assert value == {"left": value1, "right": value2}
        elif uncertainty:
            assert value["mean"] == 4
            assert value["std"] == pytest.approx(math.hypot(0.5, 0.5) / 2)
        else:
            assert value == 4
        assert result.meta["identity_strategy"] == identity.value
    assert (
        left.items,
        left.attributes,
        left.meta,
        right.items,
        right.attributes,
        right.meta,
    ) == original


@pytest.mark.parametrize("combine", [operator.or_, operator.and_])
@pytest.mark.parametrize("identity", list(IdentityStrategy))
@pytest.mark.parametrize(
    "left_values,right_values",
    [({}, {"score": 8}), ({"score": 0}, {}), ({"score": None}, {"score": 8})],
)
def test_missing_values_do_not_create_conflicts(
    combine, identity, left_values, right_values
):
    item1, item2 = _items("nodes", identity)
    left = QueryResult(
        "nodes",
        [item1],
        attributes={name: {item1: value} for name, value in left_values.items()},
        meta={"identity_strategy": identity},
    )
    right = QueryResult(
        "nodes",
        [item2],
        attributes={name: {item2: value} for name, value in right_values.items()},
    )
    result = combine(left, right)
    assert result.count == 1
    expected = left_values.get("score")
    if expected is None:
        expected = right_values["score"]
    assert result.attributes["score"] == {item1: expected}


@pytest.mark.parametrize("combine", [operator.or_, operator.and_])
@pytest.mark.parametrize("uncertainty", [False, True])
def test_equal_values_do_not_raise_under_by_id(combine, uncertainty):
    item1, item2 = _items("nodes", IdentityStrategy.BY_ID)
    value = {"mean": 0, "std": 0.5} if uncertainty else 0
    left = QueryResult(
        "nodes",
        [item1],
        attributes={"score": {item1: value}},
        meta={"identity_strategy": IdentityStrategy.BY_ID},
    )
    right = QueryResult(
        "nodes", [item2], attributes={"score": {item2: deepcopy(value)}}
    )
    result = combine(left, right)
    assert result.count == 1
    assert result.attributes["score"] == {item1: value}


@pytest.mark.parametrize("combine", [operator.or_, operator.and_])
@pytest.mark.parametrize("prefer_right", [False, True])
def test_real_layer_degrees_conflict_when_matched_by_physical_id(combine, prefer_right):
    net = multinet.multi_layer_network(directed=False)
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
                "target": "C",
                "source_type": "work",
                "target_type": "work",
            },
            {
                "source": "A",
                "target": "D",
                "source_type": "work",
                "target_type": "work",
            },
        ]
    )
    left = Q.nodes().from_layers(L["social"]).compute("degree").execute(net)
    right = Q.nodes().from_layers(L["work"]).compute("degree").execute(net)
    assert left.target == right.target == "nodes"
    assert left.count == 2 and right.count == 3
    left.meta["identity_strategy"] = IdentityStrategy.BY_ID
    if prefer_right:
        left.meta["conflict_resolution"] = ConflictResolution.PREFER_RIGHT
        result = combine(left, right)
        assert result.target == "nodes"
        assert result.attributes["degree"][("A", "social")] == 2
    else:
        with pytest.raises(AttributeConflictError, match="degree"):
            combine(left, right)
