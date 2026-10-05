"""Result difference must keep positional attributes aligned with retained items."""

from copy import deepcopy

import pytest

from py3plex.dsl.algebra import IdentityStrategy
from py3plex.dsl.result import QueryResult


CASES = [
    ("nodes", ["A", "B", "C"]),
    ("nodes", [("A", "L"), ("B", "L"), ("C", "L")]),
    ("edges", [(("A", "L"), ("B", "L")), (("B", "L"), ("C", "L")), (("C", "L"), ("D", "L"))]),
]


@pytest.mark.parametrize("target,items", CASES)
@pytest.mark.parametrize("removed", [[0, 2], [0], [0, 1, 2]])
@pytest.mark.parametrize("storage", ["list", "dict"])
@pytest.mark.parametrize("uncertain", [False, True])
def test_difference_preserves_item_attribute_pairs(target, items, removed, storage, uncertain):
    values = [10, 20, 30]
    if uncertain:
        values = [{"mean": value, "std": 0.5} for value in values]
    expected = dict(zip(items, values))
    attributes = {"score": values if storage == "list" else expected.copy()}
    left = QueryResult(target, items, attributes=attributes,
                       meta={"identity_strategy": IdentityStrategy.BY_REPLICA},
                       computed_metrics={"score"})
    right = QueryResult(target, [items[i] for i in removed],
                        meta={"identity_strategy": IdentityStrategy.BY_REPLICA})
    original = deepcopy((left.items, left.attributes, left.meta, right.items, right.meta))
    result = left - right
    assert result.target == target
    assert set(result.items) == set(items) - set(right.items)
    assert result.count == len(items) - len(removed)
    assert result.computed_metrics == {"score"}
    if storage == "list":
        assert result.attributes["score"] == [expected[item] for item in result.items]
    else:
        assert result.attributes["score"] == {item: expected[item] for item in result.items}
    frame = result.to_pandas()
    if result.items:
        assert frame["score"].tolist() == [expected[item] for item in result.items]
    else:
        assert frame.empty
    assert (left.items, left.attributes, left.meta, right.items, right.meta) == original


@pytest.mark.parametrize("target,items", CASES)
@pytest.mark.parametrize("values", [[], [10]])
def test_difference_preserves_missing_values_in_short_lists(target, items, values):
    left = QueryResult(target, items, attributes={"score": values},
                       meta={"identity_strategy": IdentityStrategy.BY_REPLICA})
    right = QueryResult(target, [items[0]],
                        meta={"identity_strategy": IdentityStrategy.BY_REPLICA})
    result = left - right
    assert result.count == 2
    assert result.attributes["score"] == [None, None]
    assert result.to_pandas()["score"].isna().all()
    assert left.attributes["score"] == values
