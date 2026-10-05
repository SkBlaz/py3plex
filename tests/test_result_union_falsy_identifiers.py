"""Union must distinguish false-valued identifiers from absent items."""

from copy import deepcopy

import pytest

from py3plex.dsl.algebra import ConflictResolution
from py3plex.dsl.result import QueryResult


@pytest.mark.parametrize("item", [0, False, 0.0, "", (), 1, "A"])
@pytest.mark.parametrize("value", [0, 7, {"mean": 7, "std": 0.5}])
@pytest.mark.parametrize("placement", ["left", "right", "both"])
def test_union_preserves_metrics_for_present_identifiers(item, value, placement):
    nonempty = QueryResult(
        "nodes", [item], attributes={"score": {item: value}}, computed_metrics={"score"}
    )
    empty = QueryResult("nodes", [])
    left = empty if placement == "right" else nonempty
    right = empty if placement == "left" else nonempty
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

    result = left | right

    assert result.target == "nodes" and result.count == 1
    assert result.items == [item]
    assert result.attributes["score"] == {item: value}
    assert result.computed_metrics == {"score"}
    assert result.meta["algebra_operation"] == "union"
    frame = result.to_pandas(expand_uncertainty=isinstance(value, dict))
    assert frame.iloc[0]["score"] == (
        value["mean"] if isinstance(value, dict) else value
    )
    if isinstance(value, dict):
        assert frame.iloc[0]["score_std"] == 0.5
    assert (
        left.items,
        left.attributes,
        left.meta,
        right.items,
        right.attributes,
        right.meta,
    ) == original


@pytest.mark.parametrize("item", [0, "", ()])
@pytest.mark.parametrize(
    "strategy,expected",
    [
        (ConflictResolution.PREFER_LEFT, 2),
        (ConflictResolution.PREFER_RIGHT, 8),
        (ConflictResolution.MEAN, 5),
    ],
)
def test_union_resolves_conflicts_for_false_valued_identifiers(
    item, strategy, expected
):
    left = QueryResult(
        "nodes",
        [item],
        attributes={"score": {item: 2}},
        meta={"conflict_resolution": strategy},
    )
    right = QueryResult("nodes", [item], attributes={"score": {item: 8}})
    result = left | right
    assert result.count == 1
    assert result.attributes["score"] == {item: expected}


def test_union_keeps_the_left_representative_for_equal_identifiers():
    left = QueryResult("nodes", [False], attributes={"score": {False: 2}})
    right = QueryResult("nodes", [0], attributes={"score": {0: 2}})
    result = left | right
    assert result.count == 1 and result.items[0] is False
    assert result.attributes["score"] == {False: 2}
    assert next(iter(result.attributes["score"])) is False


def test_missing_operand_does_not_supply_attributes_for_an_unrelated_key():
    left = QueryResult("nodes", [0], attributes={"left_score": {0: 2}})
    right = QueryResult("nodes", ["A"], attributes={"right_score": {None: 99, "A": 8}})
    result = left | right
    assert result.count == 2
    assert result.attributes == {"left_score": {0: 2}, "right_score": {"A": 8}}
