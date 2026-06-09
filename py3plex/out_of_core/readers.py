"""Chunked readers for CSV and optionally Arrow/Parquet edge/node tables."""

from __future__ import annotations

import csv
import os
from typing import Any, Callable, Dict, Iterator, List, Optional

from .errors import OutOfCoreIOError
from .schema import (
    coerce_edge_row,
    validate_edge_row,
)


# ---------------------------------------------------------------------------
# Predicate pushdown helpers
# ---------------------------------------------------------------------------

_COMPARISON_OPS = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "ge": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "le": lambda a, b: a <= b,
}


def _make_predicate(field: str, op: str, value: Any) -> Callable[[dict], bool]:
    """Build a row-level predicate function.

    Args:
        field: Column name.
        op: One of eq/ne/gt/gte/ge/lt/lte/le.
        value: Comparison value (must already be the correct type).

    Returns:
        A callable that takes a row dict and returns bool.
    """
    cmp = _COMPARISON_OPS.get(op)
    if cmp is None:
        raise ValueError(f"Unsupported comparison op: {op!r}")

    def predicate(row: dict) -> bool:
        v = row.get(field)
        if v is None:
            return False
        try:
            return cmp(v, value)
        except TypeError:
            return False

    return predicate


def build_predicates(conditions: List[Dict[str, Any]]) -> List[Callable[[dict], bool]]:
    """Build a list of predicate functions from condition dicts.

    Each condition dict must have keys: ``field``, ``op``, ``value``.

    Args:
        conditions: List of condition specification dicts.

    Returns:
        List of predicate callables (AND semantics when applied together).
    """
    return [_make_predicate(c["field"], c["op"], c["value"]) for c in conditions]


def apply_predicates(row: dict, predicates: List[Callable[[dict], bool]]) -> bool:
    """Return True iff *row* satisfies all *predicates* (AND semantics)."""
    return all(p(row) for p in predicates)


# ---------------------------------------------------------------------------
# CSV reader
# ---------------------------------------------------------------------------

class CsvEdgeReader:
    """Chunked CSV edge-table reader with predicate pushdown.

    Args:
        path: Path to the CSV file.
        chunk_size: Rows per chunk (default 10 000).
        validate: Whether to validate required columns on first chunk.
        encoding: File encoding (default utf-8).
    """

    def __init__(
        self,
        path: str,
        chunk_size: int = 10_000,
        validate: bool = True,
        encoding: str = "utf-8",
    ) -> None:
        # Defer file-existence check to scan() so construction is always cheap
        self.path = path
        self.chunk_size = chunk_size
        self.validate = validate
        self.encoding = encoding

    def scan(
        self,
        predicates: Optional[List[Callable[[dict], bool]]] = None,
        columns: Optional[List[str]] = None,
    ) -> Iterator[dict]:
        """Yield rows matching *predicates*, optionally projecting *columns*.

        Args:
            predicates: List of predicate callables (AND semantics).  If None
                        all rows are returned.
            columns: Column names to include in each yielded dict.  If None
                     all columns are included.

        Yields:
            Row dicts.
        """
        if not os.path.isfile(self.path):
            raise OutOfCoreIOError(f"CSV file not found: {self.path!r}")
        predicates = predicates or []
        try:
            with open(self.path, "r", encoding=self.encoding, newline="") as fh:
                reader = csv.DictReader(fh)
                validated = not self.validate
                for raw_row in reader:
                    row = coerce_edge_row(raw_row)
                    if not validated:
                        validate_edge_row(row)
                        validated = True
                    if predicates and not apply_predicates(row, predicates):
                        continue
                    if columns:
                        row = {k: row[k] for k in columns if k in row}
                    yield row
        except (OSError, IOError) as exc:
            raise OutOfCoreIOError(f"Failed to read CSV {self.path!r}: {exc}") from exc

    def chunks(
        self,
        predicates: Optional[List[Callable[[dict], bool]]] = None,
        columns: Optional[List[str]] = None,
    ) -> Iterator[List[dict]]:
        """Yield lists of up to *chunk_size* filtered rows."""
        from .utils import chunk_iter
        yield from chunk_iter(self.scan(predicates=predicates, columns=columns), size=self.chunk_size)


# ---------------------------------------------------------------------------
# Arrow / Parquet reader (optional acceleration)
# ---------------------------------------------------------------------------

def _has_pyarrow() -> bool:
    try:
        import pyarrow  # noqa: F401
        return True
    except ImportError:
        return False


class ArrowEdgeReader:
    """Edge reader backed by PyArrow dataset scanner (Parquet / Arrow IPC).

    Falls back gracefully to CSV reader error if pyarrow is not installed.

    Args:
        path: Path to a Parquet file, directory of Parquet files, or Arrow
              IPC file.
        format: ``"parquet"`` or ``"arrow"`` (default ``"parquet"``).
        chunk_size: Rows per batch.
    """

    def __init__(
        self,
        path: str,
        format: str = "parquet",
        chunk_size: int = 10_000,
    ) -> None:
        if not _has_pyarrow():
            raise OutOfCoreIOError(
                "pyarrow is required to read Parquet/Arrow files. "
                "Install it with: pip install pyarrow"
            )
        if not os.path.exists(path):
            raise OutOfCoreIOError(f"Path not found: {path!r}")
        self.path = path
        self.format = format
        self.chunk_size = chunk_size

    def scan(
        self,
        predicates: Optional[List[Callable[[dict], bool]]] = None,
        columns: Optional[List[str]] = None,
    ) -> Iterator[dict]:
        """Yield rows from a Parquet/Arrow dataset.

        Args:
            predicates: Row-level predicates (applied in Python after read).
            columns: Columns to project.

        Yields:
            Row dicts.
        """
        import pyarrow.dataset as ds

        dataset = ds.dataset(self.path, format=self.format)
        scanner = dataset.scanner(
            columns=columns,
            batch_size=self.chunk_size,
        )
        predicates = predicates or []
        for batch in scanner.to_batches():
            table = batch.to_pydict()
            nrows = len(next(iter(table.values()), []))
            for i in range(nrows):
                row = {k: v[i] for k, v in table.items()}
                if predicates and not apply_predicates(row, predicates):
                    continue
                yield row

    def chunks(
        self,
        predicates: Optional[List[Callable[[dict], bool]]] = None,
        columns: Optional[List[str]] = None,
    ) -> Iterator[List[dict]]:
        """Yield lists of up to *chunk_size* rows."""
        from .utils import chunk_iter
        yield from chunk_iter(self.scan(predicates=predicates, columns=columns), self.chunk_size)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def make_edge_reader(path: str, format: str, chunk_size: int = 10_000):
    """Return the appropriate reader for *format*.

    Args:
        path: Path to the edge data.
        format: One of ``"csv"``, ``"parquet"``, ``"arrow"``, ``"jsonl"``.
        chunk_size: Rows per chunk.

    Returns:
        A reader with ``.scan()`` and ``.chunks()`` methods.
    """
    fmt = format.lower()
    if fmt == "csv":
        return CsvEdgeReader(path, chunk_size=chunk_size)
    if fmt in ("parquet", "arrow"):
        return ArrowEdgeReader(path, format=fmt, chunk_size=chunk_size)
    if fmt == "jsonl":
        return JsonlEdgeReader(path, chunk_size=chunk_size)
    raise OutOfCoreIOError(f"Unsupported edge format: {format!r}")


# ---------------------------------------------------------------------------
# JSONL reader (simple fallback)
# ---------------------------------------------------------------------------

class JsonlEdgeReader:
    """Chunked JSONL edge reader.

    Args:
        path: Path to the JSONL file (one JSON object per line).
        chunk_size: Rows per chunk.
    """

    def __init__(self, path: str, chunk_size: int = 10_000) -> None:
        if not os.path.isfile(path):
            raise OutOfCoreIOError(f"JSONL file not found: {path!r}")
        self.path = path
        self.chunk_size = chunk_size

    def scan(
        self,
        predicates: Optional[List[Callable[[dict], bool]]] = None,
        columns: Optional[List[str]] = None,
    ) -> Iterator[dict]:
        """Yield rows from JSONL file matching predicates."""
        import json as _json
        predicates = predicates or []
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    row = coerce_edge_row(_json.loads(line))
                    if predicates and not apply_predicates(row, predicates):
                        continue
                    if columns:
                        row = {k: row[k] for k in columns if k in row}
                    yield row
        except (OSError, IOError) as exc:
            raise OutOfCoreIOError(f"Failed to read JSONL {self.path!r}: {exc}") from exc

    def chunks(
        self,
        predicates: Optional[List[Callable[[dict], bool]]] = None,
        columns: Optional[List[str]] = None,
    ) -> Iterator[List[dict]]:
        """Yield lists of up to *chunk_size* rows."""
        from .utils import chunk_iter
        yield from chunk_iter(self.scan(predicates=predicates, columns=columns), self.chunk_size)
