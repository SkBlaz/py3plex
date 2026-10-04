"""Symmetric difference must retain metrics from each surviving item's source."""

from copy import deepcopy

import pytest

from py3plex.dsl.algebra import IdentityStrategy
from py3plex.dsl.result import QueryResult


def _items(kind, names):
    if kind == "replicas":
        return [(name, "social") for name in names]
    if kind == "edges":
        return [((name, "social"), ("hub", "work")) for name in names]
    return list(names)


def _result(kind, names, values, storage):
    items = _items(kind, names)
    attributes = values if storage == "list" else dict(zip(items, values))
    return QueryResult(
        "edges" if kind == "edges" else "nodes",
        items,
        attributes={"score": attributes},
        meta={"identity_strategy": IdentityStrategy.BY_REPLICA},
        computed_metrics={"score"},
    )


@pytest.mark.parametrize("kind", ["nodes", "replicas", "edges"])
@pytest.mark.parametrize(
    "left_storage,right_storage",
    [("list", "list"), ("list", "dict"), ("dict", "list"), ("dict", "dict")],
)
@pytest.mark.parametrize("uncertainty", [False, True])
@pytest.mark.parametrize("overlap", [False, True])
def test_symmetric_difference_preserves_source_metrics(
    kind, left_storage, right_storage, uncertainty, overlap
):
    right_names = ["B", "C"] if overlap else ["C", "D"]
    left_values = [0, 20]
    right_values = [200, 30]
    if uncertainty:
        left_values = [{"mean": value, "std": 0.5} for value in left_values]
        right_values = [{"mean": value, "std": 0.5} for value in right_values]
    left = _result(kind, ["A", "B"], left_values, left_storage)
    right = _result(kind, right_names, right_values, right_storage)
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
    expected = dict(zip(left.items, left_values))
    expected.update(zip(right.items, right_values))
    for item in set(left.items) & set(right.items):
        expected.pop(item)

    result = left ^ right

    assert result.target == left.target and result.count == len(expected)
    assert set(result.items) == set(expected)
    assert result.attributes["score"] == expected
    assert result.computed_metrics == {"score"}
    assert result.meta["algebra_operation"] == "symmetric_difference"
    frame = result.to_pandas(expand_uncertainty=uncertainty)
    assert frame["score"].tolist() == [
        expected[item]["mean"] if uncertainty else expected[item]
        for item in result.items
    ]
    if uncertainty:
        assert frame["score_std"].tolist() == [0.5] * result.count
    assert (
        left.items,
        left.attributes,
        left.meta,
        right.items,
        right.attributes,
        right.meta,
    ) == original


@pytest.mark.parametrize("kind", ["nodes", "replicas", "edges"])
@pytest.mark.parametrize("side", ["left", "right"])
def test_empty_operand_preserves_nonempty_list_metrics(kind, side):
    nonempty = _result(kind, ["A", "B"], [0, 20], "list")
    empty = _result(kind, [], [], "list")
    result = empty ^ nonempty if side == "left" else nonempty ^ empty
    assert result.count == 2
    assert result.attributes["score"] == dict(zip(nonempty.items, [0, 20]))


@pytest.mark.parametrize(
    "strategy", [IdentityStrategy.BY_ID, IdentityStrategy.BY_REPLICA]
)
def test_metrics_follow_survivors_with_explicit_identity(strategy):
    left = QueryResult(
        "nodes",
        [("A", "social"), ("B", "social")],
        attributes={"score": [10, 20]},
        meta={"identity_strategy": strategy},
    )
    right = QueryResult(
        "nodes", [("B", "work"), ("C", "work")], attributes={"score": [200, 30]}
    )
    expected = {("A", "social"): 10, ("C", "work"): 30}
    if strategy == IdentityStrategy.BY_REPLICA:
        expected.update({("B", "social"): 20, ("B", "work"): 200})
    result = left ^ right
    assert result.count == len(expected)
    assert result.attributes["score"] == expected


def test_short_lists_and_operand_specific_attributes_are_supported():
    left = QueryResult("nodes", ["A", "B"], attributes={"left_score": [0]})
    right = QueryResult("nodes", ["C"], attributes={"right_score": [30]})
    result = left ^ right
    assert result.count == 3
    assert result.attributes == {"left_score": {"A": 0}, "right_score": {"C": 30}}
    frame = result.to_pandas().set_index("id")
    assert frame.loc["A", "left_score"] == 0
    assert frame.loc["C", "right_score"] == 30


def test_identical_operands_produce_empty_attributes():
    left = _result("replicas", ["A", "B"], [10, 20], "list")
    result = left ^ left
    assert result.count == 0
    assert result.attributes == {"score": {}}
    assert result.to_pandas().empty
