"""Composable streaming operators for out-of-core query execution."""

from __future__ import annotations

import heapq
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional

from .utils import sort_key_for_row


# ---------------------------------------------------------------------------
# Aggregation spec resolution
# ---------------------------------------------------------------------------

def _resolve_agg(spec) -> Callable[[List[dict]], Any]:
    """Resolve an aggregation spec to a callable.

    Accepted forms:
    - A callable already: returned as-is.
    - ``"count"``: count of rows.
    - ``"sum:<field>"``: sum of numeric field.
    - ``"mean:<field>"``: arithmetic mean of numeric field.
    - ``"min:<field>"``: minimum value.
    - ``"max:<field>"``: maximum value.
    - ``"count_distinct:<field>"``: number of distinct values of a field.
    """
    if callable(spec):
        return spec
    if not isinstance(spec, str):
        raise ValueError(f"Aggregation spec must be a callable or string, got {spec!r}")
    parts = spec.split(":", 1)
    func_name = parts[0].strip().lower()
    field = parts[1].strip() if len(parts) > 1 else None

    if func_name == "count":
        return lambda buf: len(buf)
    if func_name == "sum":
        if field is None:
            raise ValueError("sum aggregation requires a field: 'sum:<field>'")
        return lambda buf, _f=field: sum(float(r.get(_f) or 0) for r in buf)
    if func_name == "mean":
        if field is None:
            raise ValueError("mean aggregation requires a field: 'mean:<field>'")
        def _mean(buf, _f=field):
            vals = [float(r.get(_f) or 0) for r in buf]
            return sum(vals) / len(vals) if vals else 0.0
        return _mean
    if func_name == "min":
        if field is None:
            raise ValueError("min aggregation requires a field: 'min:<field>'")
        return lambda buf, _f=field: min(float(r.get(_f) or 0) for r in buf) if buf else None
    if func_name == "max":
        if field is None:
            raise ValueError("max aggregation requires a field: 'max:<field>'")
        return lambda buf, _f=field: max(float(r.get(_f) or 0) for r in buf) if buf else None
    if func_name in ("count_distinct", "distinct_count"):
        if field is None:
            raise ValueError("count_distinct requires a field: 'count_distinct:<field>'")
        return lambda buf, _f=field: len({r.get(_f) for r in buf})
    raise ValueError(f"Unknown aggregation function {func_name!r} in spec {spec!r}")


def _resolve_aggs(aggregations: Dict[str, Any]) -> Dict[str, Callable]:
    """Return a new dict with all specs resolved to callables."""
    return {k: _resolve_agg(v) for k, v in aggregations.items()}

def filter_rows(
    rows: Iterable[dict],
    predicates,
) -> Iterator[dict]:
    """Yield rows that satisfy all *predicates* (AND semantics).

    Args:
        rows: Input row iterator.
        predicates: A single callable or a list of predicate callables.

    Yields:
        Matching rows.
    """
    # Accept both a single callable and a list of callables
    if callable(predicates):
        preds: List[Callable[[dict], bool]] = [predicates]
    else:
        preds = list(predicates)
    for row in rows:
        if all(p(row) for p in preds):
            yield row


def project(
    rows: Iterable[dict],
    columns: List[str],
) -> Iterator[dict]:
    """Yield rows with only the specified *columns* retained.

    Args:
        rows: Input row iterator.
        columns: Column names to keep.

    Yields:
        Projected row dicts.
    """
    for row in rows:
        yield {k: row[k] for k in columns if k in row}


def add_field(
    rows: Iterable[dict],
    field: str,
    compute_fn: Callable[[dict], Any],
) -> Iterator[dict]:
    """Yield rows with an additional field computed by *compute_fn*.

    The computation must be deterministic and depend only on the input row.

    Args:
        rows: Input row iterator.
        field: New field name.
        compute_fn: Callable that takes a row dict and returns the new value.

    Yields:
        Rows with the new field added.
    """
    for row in rows:
        row = dict(row)
        row[field] = compute_fn(row)
        yield row


def limit(rows: Iterable[dict], n: int) -> Iterator[dict]:
    """Yield at most *n* rows.

    Args:
        rows: Input row iterator.
        n: Maximum number of rows to yield.

    Yields:
        Up to *n* rows.
    """
    for i, row in enumerate(rows):
        if i >= n:
            break
        yield row


# ---------------------------------------------------------------------------
# External sort (spill-based)
# ---------------------------------------------------------------------------

def external_sort(
    rows: Iterable[dict],
    key_fields: List[str],
    asc: bool = True,
    memory_limit_mb: float = 64.0,
    workdir: Optional[str] = None,
) -> Iterator[dict]:
    """Sort *rows* by *key_fields*, spilling to disk if needed.

    Args:
        rows: Input row iterator.
        key_fields: Fields to sort by.
        asc: If True sort ascending, else descending.
        memory_limit_mb: Approximate memory limit (controls run size).
        workdir: Directory for spill files.

    Yields:
        Rows in sorted order.
    """
    from .spill import SpillManager

    # Rough heuristic: assume ~1 KB per row average → rows_per_run = limit_mb * 1024
    rows_per_run = max(1000, int(memory_limit_mb * 1024))
    with SpillManager(workdir=workdir) as sm:
        yield from sm.external_sort(
            iter(rows),
            key_fields=key_fields,
            asc=asc,
            memory_limit_rows=rows_per_run,
        )


# ---------------------------------------------------------------------------
# Bounded top-N (heap-based) – avoids full sort when only top rows are needed
# ---------------------------------------------------------------------------

def top_n(
    rows: Iterable[dict],
    n: int,
    key_fields: List[str],
    asc: bool = True,
) -> List[dict]:
    """Return the top *n* rows sorted by *key_fields* using a bounded heap.

    Memory usage is O(n) regardless of input size, making this preferable
    over a full external sort when only the first few results are needed.

    Args:
        rows: Input row iterator.
        n: Number of rows to return.
        key_fields: Fields to sort by.
        asc: Ascending if True, descending if False.

    Returns:
        List of up to *n* rows in sorted order.
    """
    if n <= 0:
        return []

    heap: list = []
    counter = [0]

    for row in rows:
        k = sort_key_for_row(row, key_fields)
        c = counter[0]
        counter[0] += 1
        if asc:
            # We want smallest k → use max-heap negated so we can pop largest
            entry = (_negate_key(k), c, row)
            if len(heap) < n:
                heapq.heappush(heap, entry)
            else:
                # If current key < worst in heap: replace
                if _negate_key(k) > heap[0][0]:
                    heapq.heapreplace(heap, entry)
        else:
            # We want largest k → use min-heap (natural order)
            entry = (k, c, row)
            if len(heap) < n:
                heapq.heappush(heap, entry)
            else:
                if k > heap[0][0]:
                    heapq.heapreplace(heap, entry)

    # Extract in correct order
    results = [r for _, _, r in heap]
    results.sort(
        key=lambda r: sort_key_for_row(r, key_fields),
        reverse=not asc,
    )
    return results


def _negate_key(key: tuple) -> tuple:
    """Return inverted key for min-heap top-N selection."""
    inv = []
    for type_rank, val in key:
        if isinstance(val, (int, float)):
            inv.append((type_rank, -val))
        else:
            inv.append((-type_rank, val))
    return tuple(inv)


# ---------------------------------------------------------------------------
# External group-by (spill-based)
# ---------------------------------------------------------------------------

def external_groupby(
    rows: Iterable[dict],
    key_fields: List[str],
    aggregations: Dict[str, Any],
    memory_limit_mb: float = 64.0,
    workdir: Optional[str] = None,
) -> Iterator[dict]:
    """Group *rows* by *key_fields* and aggregate, spilling to disk if needed.

    Args:
        rows: Input row iterator.
        key_fields: Fields to group by.
        aggregations: Mapping output_name → callable(group_rows) → value OR
                      string spec such as ``"count"``, ``"sum:<field>"``.
        memory_limit_mb: Memory bound for spill runs.
        workdir: Directory for spill files.

    Yields:
        Aggregated row dicts (one per group).
    """
    from .spill import SpillManager

    resolved = _resolve_aggs(aggregations)
    rows_per_run = max(1000, int(memory_limit_mb * 1024))
    with SpillManager(workdir=workdir) as sm:
        yield from sm.external_groupby(
            iter(rows),
            key_fields=key_fields,
            aggregations=resolved,
            memory_limit_rows=rows_per_run,
        )


# ---------------------------------------------------------------------------
# External distinct
# ---------------------------------------------------------------------------

def external_distinct(
    rows: Iterable[dict],
    key_fields: List[str],
    memory_limit_mb: float = 64.0,
    workdir: Optional[str] = None,
) -> Iterator[dict]:
    """Yield rows with distinct values of *key_fields*, spilling if needed.

    Uses external sort to group identical keys, then keeps the first row
    per group.

    Args:
        rows: Input row iterator.
        key_fields: Fields that define uniqueness.
        memory_limit_mb: Memory bound.
        workdir: Directory for spill files.

    Yields:
        One representative row per distinct key combination.
    """
    from .spill import SpillManager

    rows_per_run = max(1000, int(memory_limit_mb * 1024))
    with SpillManager(workdir=workdir) as sm:
        sorted_rows = sm.external_sort(
            iter(rows),
            key_fields=key_fields,
            asc=True,
            memory_limit_rows=rows_per_run,
        )
        last_key: Optional[tuple] = None
        for row in sorted_rows:
            key = tuple(row.get(f) for f in key_fields)
            if key != last_key:
                last_key = key
                yield row
