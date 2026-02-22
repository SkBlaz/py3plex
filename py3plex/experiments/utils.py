"""Utility helpers: canonical JSON serialisation, stable hashing, path-safe IDs.

These utilities are intentionally dependency-free (stdlib only) so they can be
used from anywhere in the experiments package without circular imports.
"""

import hashlib
import json
import re
from typing import Any


def _canonical_default(obj: Any) -> Any:
    """JSON serialisation hook for non-standard types."""
    if isinstance(obj, (set, frozenset)):
        return sorted(obj)
    if isinstance(obj, tuple):
        return list(obj)
    # floats are stringified with repr to avoid platform-dependent precision
    if isinstance(obj, float):
        return repr(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serialisable")


def canonical_json(data: Any) -> str:
    """Return a stable, deterministic JSON string.

    Rules applied:
    * Keys are sorted recursively.
    * Sets and tuples are converted to sorted/plain lists.
    * Floats are serialised with ``repr()`` to avoid platform-dependent rounding.
    * No trailing whitespace; no indent (compact form for hashing).

    Args:
        data: Any JSON-compatible Python object.

    Returns:
        Compact JSON string with sorted keys.
    """
    return json.dumps(data, sort_keys=True, default=_canonical_default, separators=(",", ":"))


def stable_hash(data: Any, *, length: int = 24) -> str:
    """Return a stable hex SHA-256 hash of the canonical JSON representation.

    Args:
        data: Python object to hash.
        length: Number of hex characters to return (full 64-char hash is always
            computed; ``length`` truncates the *display* prefix only).
            Pass ``length=64`` for the full hash.

    Returns:
        Hex string of the requested length.
    """
    raw = canonical_json(data)
    full = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return full[:length]


def path_safe_id(exp_id: str) -> str:
    """Return a filesystem-safe version of an experiment ID.

    Strips characters that are not alphanumeric or ``-_``.

    Args:
        exp_id: Arbitrary experiment identifier.

    Returns:
        String safe to use as a directory / file name.
    """
    return re.sub(r"[^a-zA-Z0-9\-_]", "_", exp_id)
