"""Pandas export must preserve canonical edge identifiers and their metrics."""

from copy import deepcopy

import pytest

from py3plex.dsl.result import QueryResult


@pytest.mark.parametrize("storage", ["list", "canonical", "replica", "legacy_pair"])
@pytest.mark.parametrize("value", [0, None, 7, {"mean": 7, "std": 0.5}])
@pytest.mark.parametrize("expand", [False, True])
@pytest.mark.parametrize("tuple_ids", [False, True])
def test_four_field_edge_preserves_layers_and_metric(storage, value, expand, tuple_ids):
    source, target = ((1, 2), (3, 4)) if tuple_ids else ("A", "B")
    edge = (source, target, "social", "work")
    replica_pair = ((source, "social"), (target, "work"))
    keys = {"canonical": edge, "replica": replica_pair, "legacy_pair": (source, target)}
    values = [value] if storage == "list" else {keys[storage]: value}
    result = QueryResult("edges", [edge], attributes={"score": values})
    original = deepcopy((result.items, result.attributes, result.meta))
    assert result.target == "edges" and result.count == 1
    row = result.to_pandas(expand_uncertainty=expand).iloc[0]
    assert row["source"] == source
    assert row["target"] == target
    assert row["source_layer"] == "social"
    assert row["target_layer"] == "work"
    expected = value["mean"] if expand and isinstance(value, dict) else value
    assert row["score"] == expected
    if expand and isinstance(value, dict):
        assert row["score_std"] == 0.5
    assert (result.items, result.attributes, result.meta) == original


def test_full_edge_keys_take_precedence_and_keep_layers_distinct():
    edges = [("A", "B", "social", "work"), ("A", "B", "work", "social")]
    values = {edges[0]: 0, edges[1]: 9, ("A", "B"): -1,
              (("A", "social"), ("B", "work")): -2}
    result = QueryResult("edges", edges, attributes={"score": values})
    assert result.count == 2
    frame = result.to_pandas()
    assert frame["source_layer"].tolist() == ["social", "work"]
    assert frame["target_layer"].tolist() == ["work", "social"]
    assert frame["score"].tolist() == [0, 9]


@pytest.mark.parametrize("format", ["pair", "data", "key_data", "data_key"])
@pytest.mark.parametrize("value", [0, 7, {"mean": 7, "std": 0.5}])
def test_existing_replica_edge_formats_are_preserved(format, value):
    source, target = ("A", "social"), ("B", "work")
    pair = (source, target)
    formats = {
        "pair": pair,
        "data": pair + ({"weight": 2.5},),
        "key_data": pair + (0, {"weight": 2.5}),
        "data_key": pair + ({"weight": 2.5}, 0),
    }
    result = QueryResult("edges", [formats[format]], attributes={"score": {pair: value}})
    assert result.count == 1
    row = result.to_pandas().iloc[0]
    assert (row["source"], row["target"], row["source_layer"], row["target_layer"]) == (
        "A", "B", "social", "work"
    )
    assert row["score"] == value
    if format in ("data", "data_key"):
        assert row["weight"] == 2.5
