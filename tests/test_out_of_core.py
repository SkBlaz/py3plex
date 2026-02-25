"""Tests for the out-of-core streaming query execution package.

Covers:
- OutOfCoreNetwork construction (CSV, bad paths, formats)
- Schema validation and coercion
- CsvEdgeReader chunked scanning with predicate pushdown
- Streaming operators (filter, project, limit, top_n, external_sort,
  external_groupby, external_distinct)
- Spill utilities (SpillContext)
- OutOfCoreBackend query patterns:
  - edge selection with layer/attribute filters
  - node degree computation with filtering
  - per_layer aggregations
  - coverage(mode="at_least", k=N)
  - order_by + limit
  - UnsupportedOutOfCoreOperation for centrality measures
- QueryResultOutOfCore (count, head, to_pandas)
- CLI subcommands (convert, info, scan)
- Utils (stable_hash, chunk_iter)
"""

from __future__ import annotations

import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Generator, List
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_csv(rows: List[dict], path: str) -> None:
    """Write a list of dicts to a CSV file."""
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _sample_edges(n_social: int = 3, n_work: int = 3) -> List[dict]:
    """Return a small set of sample edge rows."""
    rows = []
    nodes = ["A", "B", "C", "D", "E"]
    for i in range(n_social):
        rows.append(
            {
                "source": nodes[i % len(nodes)],
                "target": nodes[(i + 1) % len(nodes)],
                "source_layer": "social",
                "target_layer": "social",
                "weight": str(float(i + 1)),
            }
        )
    for i in range(n_work):
        rows.append(
            {
                "source": nodes[i % len(nodes)],
                "target": nodes[(i + 2) % len(nodes)],
                "source_layer": "work",
                "target_layer": "work",
                "weight": str(float(i + 0.5)),
            }
        )
    return rows


@pytest.fixture
def edge_csv(tmp_path: Path) -> str:
    """Return path to a small edge CSV file."""
    rows = _sample_edges()
    path = str(tmp_path / "edges.csv")
    _write_csv(rows, path)
    return path


@pytest.fixture
def coverage_edge_csv(tmp_path: Path) -> str:
    """Return path to a CSV where edge (A,B) appears in two layer pairs."""
    rows = [
        {
            "source": "A",
            "target": "B",
            "source_layer": "social",
            "target_layer": "social",
            "weight": "1.0",
        },
        {
            "source": "A",
            "target": "B",
            "source_layer": "work",
            "target_layer": "work",
            "weight": "2.0",
        },
        {
            "source": "C",
            "target": "D",
            "source_layer": "social",
            "target_layer": "social",
            "weight": "0.5",
        },
    ]
    path = str(tmp_path / "cov_edges.csv")
    _write_csv(rows, path)
    return path


# ===========================================================================
# Errors
# ===========================================================================


class TestErrors:
    def test_unsupported_error_message(self):
        from py3plex.out_of_core.errors import UnsupportedOutOfCoreOperation

        err = UnsupportedOutOfCoreOperation("betweenness_centrality")
        msg = str(err)
        assert "betweenness_centrality" in msg
        assert "Supported operations" in msg
        assert "Suggestion" in msg

    def test_unsupported_error_with_suggestion(self):
        from py3plex.out_of_core.errors import UnsupportedOutOfCoreOperation

        err = UnsupportedOutOfCoreOperation("foo", suggestion="try bar")
        assert "try bar" in str(err)

    def test_out_of_core_io_error(self):
        from py3plex.out_of_core.errors import OutOfCoreIOError

        with pytest.raises(OutOfCoreIOError):
            raise OutOfCoreIOError("file missing")

    def test_schema_error(self):
        from py3plex.out_of_core.errors import SchemaError

        with pytest.raises(SchemaError):
            raise SchemaError("bad schema")

    def test_all_errors_inherit_from_base(self):
        from py3plex.out_of_core.errors import (
            OutOfCoreError,
            OutOfCoreIOError,
            SchemaError,
            UnsupportedOutOfCoreOperation,
        )

        for cls in (OutOfCoreIOError, SchemaError, UnsupportedOutOfCoreOperation):
            assert issubclass(cls, OutOfCoreError)

    def test_unsupported_error_has_operation_attr(self):
        from py3plex.out_of_core.errors import UnsupportedOutOfCoreOperation

        err = UnsupportedOutOfCoreOperation("pagerank")
        assert err.operation == "pagerank"


# ===========================================================================
# Schema
# ===========================================================================


class TestSchema:
    def test_required_columns_present(self):
        from py3plex.out_of_core.schema import EDGE_REQUIRED_COLUMNS

        assert "source" in EDGE_REQUIRED_COLUMNS
        assert "target" in EDGE_REQUIRED_COLUMNS
        assert "source_layer" in EDGE_REQUIRED_COLUMNS
        assert "target_layer" in EDGE_REQUIRED_COLUMNS

    def test_validate_edge_row_ok(self):
        from py3plex.out_of_core.schema import validate_edge_row

        validate_edge_row(
            {
                "source": "A",
                "target": "B",
                "source_layer": "social",
                "target_layer": "social",
            }
        )

    def test_validate_edge_row_missing_column(self):
        from py3plex.out_of_core.errors import SchemaError
        from py3plex.out_of_core.schema import validate_edge_row

        with pytest.raises(SchemaError, match="source_layer"):
            validate_edge_row({"source": "A", "target": "B"})

    def test_coerce_edge_row_weight(self):
        from py3plex.out_of_core.schema import coerce_edge_row

        row = {
            "source": "A",
            "target": "B",
            "source_layer": "s",
            "target_layer": "s",
            "weight": "3.14",
        }
        coerced = coerce_edge_row(row)
        assert isinstance(coerced["weight"], float)
        assert abs(coerced["weight"] - 3.14) < 1e-9

    def test_canonical_undirected_edge_key_ordering(self):
        from py3plex.out_of_core.schema import canonical_undirected_edge_key

        assert canonical_undirected_edge_key("B", "A") == ("A", "B")
        assert canonical_undirected_edge_key("A", "B") == ("A", "B")
        assert canonical_undirected_edge_key("C", "C") == ("C", "C")

    def test_supported_formats_tuple(self):
        from py3plex.out_of_core.schema import SUPPORTED_EDGE_FORMATS

        assert "csv" in SUPPORTED_EDGE_FORMATS
        assert "parquet" in SUPPORTED_EDGE_FORMATS


# ===========================================================================
# Utils
# ===========================================================================


class TestUtils:
    def test_stable_hash_determinism(self):
        from py3plex.out_of_core.utils import stable_hash

        h1 = stable_hash("hello_world")
        h2 = stable_hash("hello_world")
        assert h1 == h2
        assert isinstance(h1, str)

    def test_stable_hash_different_inputs(self):
        from py3plex.out_of_core.utils import stable_hash

        assert stable_hash("abc") != stable_hash("xyz")

    def test_chunk_iter_basic(self):
        from py3plex.out_of_core.utils import chunk_iter

        data = list(range(10))
        chunks = list(chunk_iter(iter(data), size=3))
        assert chunks == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]

    def test_chunk_iter_exact_multiple(self):
        from py3plex.out_of_core.utils import chunk_iter

        data = list(range(6))
        chunks = list(chunk_iter(iter(data), size=2))
        assert chunks == [[0, 1], [2, 3], [4, 5]]

    def test_chunk_iter_empty(self):
        from py3plex.out_of_core.utils import chunk_iter

        assert list(chunk_iter(iter([]), size=5)) == []


# ===========================================================================
# Readers
# ===========================================================================


class TestCsvEdgeReader:
    def test_scan_all_rows(self, edge_csv: str):
        from py3plex.out_of_core.readers import CsvEdgeReader

        reader = CsvEdgeReader(edge_csv)
        rows = list(reader.scan())
        assert len(rows) == 6  # 3 social + 3 work

    def test_scan_with_layer_predicate(self, edge_csv: str):
        from py3plex.out_of_core.readers import CsvEdgeReader, build_predicates

        reader = CsvEdgeReader(edge_csv)
        preds = build_predicates(
            [{"field": "source_layer", "op": "eq", "value": "social"}]
        )
        rows = list(reader.scan(predicates=preds))
        assert all(r["source_layer"] == "social" for r in rows)
        assert len(rows) == 3

    def test_scan_with_weight_gt_predicate(self, edge_csv: str):
        from py3plex.out_of_core.readers import CsvEdgeReader, build_predicates

        reader = CsvEdgeReader(edge_csv)
        # Weight is stored as float after coercion
        preds = build_predicates([{"field": "weight", "op": "gt", "value": 2.0}])
        rows = list(reader.scan(predicates=preds))
        for r in rows:
            assert float(r["weight"]) > 2.0

    def test_scan_missing_file_raises(self):
        from py3plex.out_of_core.errors import OutOfCoreIOError
        from py3plex.out_of_core.readers import CsvEdgeReader

        reader = CsvEdgeReader("/nonexistent/path.csv")
        with pytest.raises(OutOfCoreIOError):
            list(reader.scan())

    def test_scan_bad_schema_raises(self, tmp_path: Path):
        from py3plex.out_of_core.errors import SchemaError
        from py3plex.out_of_core.readers import CsvEdgeReader

        path = str(tmp_path / "bad.csv")
        with open(path, "w") as fh:
            fh.write("colA,colB\n1,2\n")
        reader = CsvEdgeReader(path)
        with pytest.raises(SchemaError):
            list(reader.scan())

    def test_scan_chunks(self, edge_csv: str):
        from py3plex.out_of_core.readers import CsvEdgeReader

        reader = CsvEdgeReader(edge_csv, chunk_size=2)
        rows = list(reader.scan())
        # Total row count should still be correct regardless of chunk_size
        assert len(rows) == 6

    def test_make_edge_reader_csv(self, edge_csv: str):
        from py3plex.out_of_core.readers import make_edge_reader

        reader = make_edge_reader(edge_csv, "csv")
        rows = list(reader.scan())
        assert len(rows) == 6


class TestPredicateBuilding:
    def test_build_all_ops(self):
        from py3plex.out_of_core.readers import build_predicates

        conditions = [
            {"field": "weight", "op": "gt", "value": 1.0},
            {"field": "weight", "op": "lt", "value": 10.0},
            {"field": "weight", "op": "gte", "value": 1.0},
            {"field": "weight", "op": "lte", "value": 5.0},
            {"field": "weight", "op": "eq", "value": 2.0},
        ]
        preds = build_predicates(conditions)
        assert len(preds) == 5

    def test_apply_predicates_pass(self):
        from py3plex.out_of_core.readers import apply_predicates, build_predicates

        preds = build_predicates([{"field": "x", "op": "gt", "value": 3}])
        assert apply_predicates({"x": 5}, preds) is True

    def test_apply_predicates_fail(self):
        from py3plex.out_of_core.readers import apply_predicates, build_predicates

        preds = build_predicates([{"field": "x", "op": "gt", "value": 10}])
        assert apply_predicates({"x": 5}, preds) is False

    def test_apply_predicates_missing_field(self):
        from py3plex.out_of_core.readers import apply_predicates, build_predicates

        preds = build_predicates([{"field": "weight", "op": "gt", "value": 0}])
        assert apply_predicates({"source": "A"}, preds) is False

    def test_invalid_op_raises(self):
        from py3plex.out_of_core.readers import build_predicates

        with pytest.raises(ValueError, match="Unsupported"):
            build_predicates([{"field": "x", "op": "nonsense", "value": 1}])


# ===========================================================================
# Operators
# ===========================================================================


class TestOperators:
    def test_filter_rows(self):
        from py3plex.out_of_core.operators import filter_rows

        data = [{"x": 1}, {"x": 5}, {"x": 3}]
        result = list(filter_rows(iter(data), lambda r: r["x"] > 2))
        assert result == [{"x": 5}, {"x": 3}]

    def test_project(self):
        from py3plex.out_of_core.operators import project

        data = [{"a": 1, "b": 2, "c": 3}]
        result = list(project(iter(data), ["a", "c"]))
        assert result == [{"a": 1, "c": 3}]

    def test_limit(self):
        from py3plex.out_of_core.operators import limit

        data = list(range(100))
        result = list(limit(iter({"v": i} for i in data), 5))
        assert len(result) == 5

    def test_top_n_returns_largest(self):
        from py3plex.out_of_core.operators import top_n

        data = [{"v": i} for i in range(20)]
        result = top_n(iter(data), n=3, key_fields=["v"], asc=False)
        assert len(result) == 3
        assert result[0]["v"] >= result[1]["v"] >= result[2]["v"]

    def test_top_n_smallest(self):
        from py3plex.out_of_core.operators import top_n

        data = [{"v": i} for i in range(20)]
        result = top_n(iter(data), n=3, key_fields=["v"], asc=True)
        assert len(result) == 3
        assert result[0]["v"] <= result[1]["v"] <= result[2]["v"]

    def test_external_sort_ascending(self, tmp_path: Path):
        from py3plex.out_of_core.operators import external_sort

        data = [{"k": v} for v in [5, 1, 3, 2, 4]]
        result = list(
            external_sort(iter(data), key_fields=["k"], asc=True, workdir=str(tmp_path))
        )
        vals = [r["k"] for r in result]
        assert vals == sorted(vals)

    def test_external_sort_descending(self, tmp_path: Path):
        from py3plex.out_of_core.operators import external_sort

        data = [{"k": v} for v in [5, 1, 3, 2, 4]]
        result = list(
            external_sort(iter(data), key_fields=["k"], asc=False, workdir=str(tmp_path))
        )
        vals = [r["k"] for r in result]
        assert vals == sorted(vals, reverse=True)

    def test_external_groupby_count(self, tmp_path: Path):
        from py3plex.out_of_core.operators import external_groupby

        data = [
            {"layer": "social", "w": 1.0},
            {"layer": "social", "w": 2.0},
            {"layer": "work", "w": 0.5},
        ]
        groups = list(
            external_groupby(
                iter(data),
                key_fields=["layer"],
                aggregations={"edge_count": "count"},
                workdir=str(tmp_path),
            )
        )
        layer_counts = {g["layer"]: g["edge_count"] for g in groups}
        assert layer_counts["social"] == 2
        assert layer_counts["work"] == 1

    def test_external_groupby_sum(self, tmp_path: Path):
        from py3plex.out_of_core.operators import external_groupby

        data = [
            {"layer": "social", "w": 1.0},
            {"layer": "social", "w": 2.0},
            {"layer": "work", "w": 3.0},
        ]
        groups = list(
            external_groupby(
                iter(data),
                key_fields=["layer"],
                aggregations={"total_w": "sum:w"},
                workdir=str(tmp_path),
            )
        )
        by_layer = {g["layer"]: g["total_w"] for g in groups}
        assert abs(by_layer["social"] - 3.0) < 1e-9
        assert abs(by_layer["work"] - 3.0) < 1e-9

    def test_external_distinct(self, tmp_path: Path):
        from py3plex.out_of_core.operators import external_distinct

        data = [
            {"layer": "social", "v": 1},
            {"layer": "social", "v": 2},
            {"layer": "work", "v": 1},
        ]
        result = list(
            external_distinct(iter(data), key_fields=["layer"], workdir=str(tmp_path))
        )
        layers = [r["layer"] for r in result]
        assert sorted(layers) == ["social", "work"]


# ===========================================================================
# Spill utilities
# ===========================================================================


class TestSpill:
    def test_spill_context_creates_tempdir(self, tmp_path: Path):
        from py3plex.out_of_core.spill import SpillContext

        ctx = SpillContext(workdir=str(tmp_path))
        path = ctx.new_spill_file(suffix=".csv")
        # Directory should exist
        assert os.path.isdir(os.path.dirname(path))

    def test_spill_context_cleanup(self, tmp_path: Path):
        from py3plex.out_of_core.spill import SpillContext

        ctx = SpillContext(workdir=str(tmp_path))
        path = ctx.new_spill_file(suffix=".csv")
        # Create the file
        with open(path, "w") as fh:
            fh.write("test")
        assert os.path.isfile(path)
        ctx.cleanup()
        assert not os.path.isfile(path)


# ===========================================================================
# OutOfCoreNetwork
# ===========================================================================


class TestOutOfCoreNetwork:
    def test_from_edges_csv_ok(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        assert net.edges_path == edge_csv
        assert net.edges_format == "csv"
        assert net.directed is False
        assert net.is_out_of_core is True

    def test_from_edges_csv_missing_file(self):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.errors import OutOfCoreIOError

        with pytest.raises(OutOfCoreIOError):
            OutOfCoreNetwork.from_edges_csv("/nonexistent/path.csv")

    def test_unsupported_format_raises(self, tmp_path: Path):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.errors import OutOfCoreIOError

        with pytest.raises(OutOfCoreIOError, match="Unsupported"):
            OutOfCoreNetwork(
                edges_path=str(tmp_path / "edges.xyz"),
                edges_format="xyz",
            )

    def test_fingerprint_marked_estimated_when_no_counts(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        assert net.fingerprint.get("estimated") is True

    def test_fingerprint_not_estimated_when_counts_given(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork

        net = OutOfCoreNetwork(
            edges_path=edge_csv,
            edges_format="csv",
            fingerprint={"node_count": 5, "edge_count": 6},
        )
        assert net.fingerprint.get("estimated") is not True

    def test_info_returns_dict(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        info = net.info()
        assert info["edges_path"] == edge_csv
        assert info["edges_format"] == "csv"

    def test_repr_contains_format(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        assert "csv" in repr(net)


# ===========================================================================
# OutOfCoreBackend – edge queries
# ===========================================================================


class TestEdgeQueries:
    def test_select_all_edges(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute({"target": "edges"})
        assert result.count == 6
        assert result.target == "edges"

    def test_edge_layer_filter(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute(
            {"target": "edges", "layer_names": ["social"]}
        )
        assert result.count == 3
        for item in result.items:
            assert item[2] == "social"  # source_layer

    def test_edge_weight_filter(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute(
            {
                "target": "edges",
                "conditions": [{"field": "weight", "op": "gt", "value": 2.0}],
            }
        )
        for item in result.items:
            # weight is in attributes
            pass
        assert all(w > 2.0 for w in result.attributes.get("weight", []))

    def test_edge_limit(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute({"target": "edges", "limit_n": 2})
        assert result.count == 2

    def test_edge_order_by_weight_asc(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute(
            {
                "target": "edges",
                "order_by": {"key": "weight", "asc": True},
            }
        )
        weights = result.attributes.get("weight", [])
        assert weights == sorted(weights)

    def test_edge_order_by_limit(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute(
            {
                "target": "edges",
                "order_by": {"key": "weight", "asc": False},
                "limit_n": 2,
            }
        )
        assert result.count == 2
        weights = result.attributes.get("weight", [])
        # First should be largest
        assert weights[0] >= weights[1]

    def test_edge_items_are_tuples_of_4(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute({"target": "edges"})
        for item in result.items:
            assert len(item) == 4


# ===========================================================================
# OutOfCoreBackend – node degree queries
# ===========================================================================


class TestNodeDegreeQueries:
    def test_nodes_all_have_degree(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute({"target": "nodes"})
        assert result.count > 0
        assert "degree" in result.attributes
        assert all(d >= 1 for d in result.attributes["degree"])

    def test_nodes_degree_gt_filter(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute(
            {
                "target": "nodes",
                "conditions": [{"field": "degree", "op": "gte", "value": 2}],
            }
        )
        assert all(d >= 2 for d in result.attributes["degree"])

    def test_nodes_with_layer_filter(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute(
            {"target": "nodes", "layer_names": ["social"]}
        )
        assert result.count > 0
        for item in result.items:
            assert item[1] == "social"

    def test_node_items_are_tuples_of_2(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute({"target": "nodes"})
        for item in result.items:
            assert len(item) == 2  # (node_id, layer)

    def test_node_degree_limit(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute(
            {"target": "nodes", "limit_n": 2}
        )
        assert result.count <= 2


# ===========================================================================
# OutOfCoreBackend – per_layer aggregations
# ===========================================================================


class TestAggregations:
    def test_edge_count_per_layer(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute(
            {
                "target": "edges",
                "groupby": {
                    "key_fields": ["source_layer", "target_layer"],
                    "aggregations": {"edge_count": "count"},
                },
            }
        )
        # Should have 2 layer pairs: (social,social) and (work,work)
        assert result.count == 2
        assert "edge_count" in result.attributes
        total = sum(result.attributes["edge_count"])
        assert total == 6

    def test_edge_weight_sum_per_layer(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute(
            {
                "target": "edges",
                "groupby": {
                    "key_fields": ["source_layer", "target_layer"],
                    "aggregations": {"total_weight": "sum:weight"},
                },
            }
        )
        assert "total_weight" in result.attributes

    def test_groupby_meta_in_result(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute(
            {
                "target": "edges",
                "groupby": {
                    "key_fields": ["source_layer"],
                    "aggregations": {"edge_count": "count"},
                },
            }
        )
        assert "grouping" in result.meta


# ===========================================================================
# OutOfCoreBackend – coverage
# ===========================================================================


class TestCoverage:
    def test_coverage_at_least_2(self, coverage_edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(coverage_edge_csv)
        result = OutOfCoreBackend(net).execute(
            {
                "target": "edges",
                "coverage": {"mode": "at_least", "k": 2},
            }
        )
        # Only (A,B) is in both social and work layer pairs
        assert result.count == 2  # appears in 2 rows (both layer copies)
        base_edges = {
            (min(i[0], i[1]), max(i[0], i[1])) for i in result.items
        }
        assert ("A", "B") in base_edges

    def test_coverage_at_least_1(self, coverage_edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(coverage_edge_csv)
        result = OutOfCoreBackend(net).execute(
            {
                "target": "edges",
                "coverage": {"mode": "at_least", "k": 1},
            }
        )
        # All edges qualify
        assert result.count == 3

    def test_coverage_too_high_returns_empty(self, coverage_edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(coverage_edge_csv)
        result = OutOfCoreBackend(net).execute(
            {
                "target": "edges",
                "coverage": {"mode": "at_least", "k": 10},
            }
        )
        assert result.count == 0


# ===========================================================================
# UnsupportedOutOfCoreOperation
# ===========================================================================


class TestUnsupportedOps:
    @pytest.mark.parametrize(
        "measure",
        [
            "betweenness_centrality",
            "closeness_centrality",
            "eigenvector_centrality",
            "pagerank",
            "clustering",
        ],
    )
    def test_centrality_measures_raise(self, edge_csv: str, measure: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.errors import UnsupportedOutOfCoreOperation
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        with pytest.raises(UnsupportedOutOfCoreOperation, match=measure):
            OutOfCoreBackend(net).execute(
                {"target": "edges", "compute": [measure]}
            )


# ===========================================================================
# QueryResultOutOfCore
# ===========================================================================


class TestQueryResultOutOfCore:
    def test_count_property(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute({"target": "edges"})
        assert result.count == len(result.items)

    def test_head_limits_items(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute({"target": "edges"})
        top2 = result.head(2)
        assert top2.count == 2

    def test_to_pandas_edges(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute({"target": "edges"})
        df = result.to_pandas()
        assert "source" in df.columns
        assert "target" in df.columns
        assert "source_layer" in df.columns
        assert len(df) == 6

    def test_to_pandas_nodes(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute({"target": "nodes"})
        df = result.to_pandas()
        assert "id" in df.columns
        assert "layer" in df.columns

    def test_to_pandas_with_limit(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute({"target": "edges"})
        df = result.to_pandas(limit=2)
        assert len(df) == 2

    def test_repr_contains_count(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute({"target": "edges"})
        assert "count=" in repr(result)

    def test_meta_contains_provenance(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute({"target": "edges"})
        assert "provenance" in result.meta
        prov = result.meta["provenance"]
        assert prov.get("engine") == "dsl_v2_executor_out_of_core"

    def test_provenance_backend_flags(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        result = OutOfCoreBackend(net).execute({"target": "edges"})
        backend = result.meta["provenance"].get("backend", {})
        assert backend.get("graph_backend") == "out_of_core"


# ===========================================================================
# CLI commands
# ===========================================================================


class TestCLIInfo:
    def test_info_command_runs(self, edge_csv: str, capsys):
        from py3plex.out_of_core.cli import cmd_ooc_info

        class Args:
            input = edge_csv
            format = "csv"
            json = False

        rc = cmd_ooc_info(Args())
        assert rc == 0
        captured = capsys.readouterr()
        assert "social" in captured.out or "work" in captured.out

    def test_info_command_json(self, edge_csv: str, capsys):
        from py3plex.out_of_core.cli import cmd_ooc_info

        class Args:
            input = edge_csv
            format = "csv"
            json = True

        rc = cmd_ooc_info(Args())
        assert rc == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "row_count" in data
        assert data["row_count"] == 6

    def test_info_missing_file(self, capsys):
        from py3plex.out_of_core.cli import cmd_ooc_info

        class Args:
            input = "/nonexistent.csv"
            format = "csv"
            json = False

        rc = cmd_ooc_info(Args())
        assert rc != 0


class TestCLIScan:
    def test_scan_default_limit(self, edge_csv: str, capsys):
        from py3plex.out_of_core.cli import cmd_ooc_scan

        class Args:
            input = edge_csv
            format = "csv"
            limit = 3
            json = False

        rc = cmd_ooc_scan(Args())
        assert rc == 0
        captured = capsys.readouterr()
        assert "3 row(s)" in captured.out

    def test_scan_json_output(self, edge_csv: str, capsys):
        from py3plex.out_of_core.cli import cmd_ooc_scan

        class Args:
            input = edge_csv
            format = "csv"
            limit = 2
            json = True

        rc = cmd_ooc_scan(Args())
        assert rc == 0
        captured = capsys.readouterr()
        rows = json.loads(captured.out)
        assert len(rows) == 2
        assert "source" in rows[0]

    def test_scan_missing_file(self, capsys):
        from py3plex.out_of_core.cli import cmd_ooc_scan

        class Args:
            input = "/nonexistent.csv"
            format = "csv"
            limit = 5
            json = False

        rc = cmd_ooc_scan(Args())
        assert rc != 0


class TestCLIConvert:
    def test_convert_csv_to_csv(self, edge_csv: str, tmp_path: Path, capsys):
        from py3plex.out_of_core.cli import cmd_ooc_convert

        output_path = str(tmp_path / "out" / "edges_clean.csv")

        class Args:
            input = edge_csv
            output = output_path
            format = "csv"
            directed = False

        rc = cmd_ooc_convert(Args())
        assert rc == 0
        assert os.path.isfile(output_path)
        # Verify output is valid CSV with required columns
        with open(output_path, newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) == 6
        assert "source" in rows[0]

    def test_convert_writes_ooc_json(self, edge_csv: str, tmp_path: Path):
        from py3plex.out_of_core.cli import cmd_ooc_convert

        output_path = str(tmp_path / "converted.csv")

        class Args:
            input = edge_csv
            output = output_path
            format = "csv"
            directed = False

        cmd_ooc_convert(Args())
        info_path = output_path + ".ooc.json"
        assert os.path.isfile(info_path)
        with open(info_path) as fh:
            info = json.load(fh)
        assert info["row_count"] == 6

    def test_convert_missing_input(self, tmp_path: Path, capsys):
        from py3plex.out_of_core.cli import cmd_ooc_convert

        class Args:
            input = "/nonexistent.csv"
            output = str(tmp_path / "out.csv")
            format = "csv"
            directed = False

        rc = cmd_ooc_convert(Args())
        assert rc != 0

    def test_convert_bad_schema_fails(self, tmp_path: Path, capsys):
        from py3plex.out_of_core.cli import cmd_ooc_convert

        bad_csv = str(tmp_path / "bad.csv")
        with open(bad_csv, "w") as fh:
            fh.write("colA,colB\n1,2\n")

        class Args:
            input = bad_csv
            output = str(tmp_path / "out.csv")
            format = "csv"
            directed = False

        rc = cmd_ooc_convert(Args())
        assert rc != 0


class TestCLIDispatch:
    def test_dispatch_ooc_no_subcommand(self, capsys):
        import argparse

        from py3plex.out_of_core.cli import dispatch_ooc

        ns = argparse.Namespace(ooc_command=None)
        rc = dispatch_ooc(ns)
        assert rc == 1

    def test_main_cli_ooc_info(self, edge_csv: str, capsys):
        """Integration: ooc info via main CLI."""
        from py3plex import cli

        rc = cli.main(["ooc", "info", edge_csv])
        assert rc == 0


class TestCLIScanEmpty:
    def test_scan_empty_file(self, tmp_path: Path, capsys):
        from py3plex.out_of_core.cli import cmd_ooc_scan

        # Create a CSV with header only (no rows)
        path = str(tmp_path / "empty.csv")
        with open(path, "w") as fh:
            fh.write("source,target,source_layer,target_layer\n")

        class Args:
            input = path
            format = "csv"
            limit = 5
            json = False

        rc = cmd_ooc_scan(Args())
        assert rc == 0
        captured = capsys.readouterr()
        assert "no rows" in captured.out


# ===========================================================================
# Determinism
# ===========================================================================


class TestDeterminism:
    """Verify that repeated executions yield identical results."""

    def test_edge_query_deterministic(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        plan = {"target": "edges", "order_by": {"key": "weight", "asc": True}}

        result1 = OutOfCoreBackend(net).execute(plan)
        result2 = OutOfCoreBackend(net).execute(plan)
        assert result1.items == result2.items
        assert result1.attributes == result2.attributes

    def test_node_degree_query_deterministic(self, edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(edge_csv)
        plan = {"target": "nodes"}

        result1 = OutOfCoreBackend(net).execute(plan)
        result2 = OutOfCoreBackend(net).execute(plan)
        assert result1.items == result2.items

    def test_coverage_query_deterministic(self, coverage_edge_csv: str):
        from py3plex.out_of_core import OutOfCoreNetwork
        from py3plex.out_of_core.executor import OutOfCoreBackend

        net = OutOfCoreNetwork.from_edges_csv(coverage_edge_csv)
        plan = {"target": "edges", "coverage": {"mode": "at_least", "k": 2}}

        result1 = OutOfCoreBackend(net).execute(plan)
        result2 = OutOfCoreBackend(net).execute(plan)
        assert sorted(result1.items) == sorted(result2.items)


# ===========================================================================
# Imports / public API
# ===========================================================================


class TestPublicAPI:
    def test_package_imports(self):
        from py3plex.out_of_core import (
            OutOfCoreError,
            OutOfCoreIOError,
            OutOfCoreNetwork,
            SchemaError,
            UnsupportedOutOfCoreOperation,
        )

        assert OutOfCoreNetwork is not None
        assert UnsupportedOutOfCoreOperation is not None

    def test_executor_importable(self):
        from py3plex.out_of_core.executor import OutOfCoreBackend, QueryResultOutOfCore

        assert OutOfCoreBackend is not None
        assert QueryResultOutOfCore is not None

    def test_operators_importable(self):
        from py3plex.out_of_core.operators import (
            external_distinct,
            external_groupby,
            external_sort,
            filter_rows,
            limit,
            project,
            top_n,
        )

    def test_readers_importable(self):
        from py3plex.out_of_core.readers import (
            CsvEdgeReader,
            apply_predicates,
            build_predicates,
            make_edge_reader,
        )
