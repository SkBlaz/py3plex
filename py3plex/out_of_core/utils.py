"""Utility helpers for out-of-core execution: hashing, chunk iteration."""

from __future__ import annotations

import hashlib
import itertools
from typing import Any, Iterable, Iterator, List, Tuple


def stable_hash(value: Any) -> str:
    """Return a stable, reproducible hex digest for *value*.

    Uses SHA-256 of the canonical str representation so that the result is
    independent of Python's hash randomisation (``PYTHONHASHSEED``).

    Args:
        value: A hashable value.  Tuples and strings are handled specially
               to produce compact, deterministic strings.

    Returns:
        Hex digest string (64 characters).
    """
    if isinstance(value, (list, tuple)):
        raw = "|".join(str(v) for v in value)
    else:
        raw = str(value)
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()


def chunk_iter(iterable: Iterable, size: int) -> Iterator[List]:
    """Yield successive *size*-sized lists from *iterable*.

    Args:
        iterable: Any iterable.
        size: Maximum number of items per chunk.

    Yields:
        Lists of up to *size* items.
    """
    if size <= 0:
        raise ValueError(f"size must be positive, got {size}")
    it = iter(iterable)
    while True:
        batch = list(itertools.islice(it, size))
        if not batch:
            break
        yield batch


def coerce_scalar(value: str, hint: type) -> Any:
    """Coerce a string *value* to *hint* type if possible, else return as-is.

    Args:
        value: Raw string value from CSV.
        hint: Target Python type (``int``, ``float``, ``bool``, ``str``).

    Returns:
        Coerced value or original string on failure.
    """
    if hint is bool:
        return value.lower() in ("1", "true", "yes", "on")
    try:
        return hint(value)
    except (ValueError, TypeError):
        return value


def sort_key_for_row(row: dict, key_fields: List[str]) -> Tuple:
    """Extract a sortable key tuple from *row* for the given *key_fields*.

    Supports mixed str/numeric columns by converting each value to a
    (type-rank, value) pair so that strings and numbers don't collide.

    Args:
        row: A dict representing one row.
        key_fields: Column names to include in the key.

    Returns:
        Tuple suitable for ``sorted()`` comparisons.
    """
    parts = []
    for f in key_fields:
        v = row.get(f)
        if v is None:
            parts.append((0, ""))  # nulls first
        elif isinstance(v, (int, float)):
            parts.append((1, float(v)))
        else:
            parts.append((2, str(v)))
    return tuple(parts)
