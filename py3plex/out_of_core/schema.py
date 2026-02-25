"""Canonical column schema for out-of-core edge and node tables."""

from typing import Dict, Tuple

# Canonical edge table schema
# Required columns and their expected Python types.
EDGE_REQUIRED_COLUMNS: Dict[str, type] = {
    "source": str,
    "target": str,
    "source_layer": str,
    "target_layer": str,
}

# Optional edge table columns
EDGE_OPTIONAL_COLUMNS: Dict[str, type] = {
    "weight": float,
}

# Canonical node table schema (optional in MVP)
NODE_REQUIRED_COLUMNS: Dict[str, type] = {
    "id": str,
    "layer": str,
}

# All canonical edge column names (required + optional)
ALL_EDGE_COLUMNS = set(EDGE_REQUIRED_COLUMNS) | set(EDGE_OPTIONAL_COLUMNS)

# Supported edge formats
SUPPORTED_EDGE_FORMATS = ("csv", "parquet", "arrow", "jsonl")


def validate_edge_row(row: dict) -> None:
    """Validate that a row dict has all required edge columns.

    Args:
        row: Dictionary representing one edge row.

    Raises:
        SchemaError: If required columns are missing.
    """
    from .errors import SchemaError

    missing = set(EDGE_REQUIRED_COLUMNS) - set(row)
    if missing:
        raise SchemaError(
            f"Edge row missing required columns: {sorted(missing)}. "
            f"Required: {sorted(EDGE_REQUIRED_COLUMNS)}."
        )


def coerce_edge_row(row: dict) -> dict:
    """Coerce edge row values to canonical types where possible.

    Args:
        row: Raw edge row dict.

    Returns:
        Row with coerced types.
    """
    result = dict(row)
    for col, typ in EDGE_REQUIRED_COLUMNS.items():
        if col in result and result[col] is not None:
            try:
                result[col] = typ(result[col])
            except (ValueError, TypeError):
                pass
    if "weight" in result and result["weight"] is not None:
        try:
            result["weight"] = float(result["weight"])
        except (ValueError, TypeError):
            result["weight"] = None
    return result


def canonical_undirected_edge_key(source: str, target: str) -> Tuple[str, str]:
    """Return a canonical (sorted) edge key for undirected networks.

    Args:
        source: Source node id.
        target: Target node id.

    Returns:
        Tuple (min_node, max_node).
    """
    if source <= target:
        return (source, target)
    return (target, source)
