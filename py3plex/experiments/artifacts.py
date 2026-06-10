"""Artifact serialisation / deserialisation for experiment results.

Preferred format: Apache Arrow / Parquet when ``pyarrow`` is available.
Fallback: CSV + JSON (with a clear warning so users know they are in fallback
mode and can install ``pyarrow`` for richer type preservation).

All public functions in this module operate on a *directory* path that
corresponds to a single experiment (``store_dir / exp_id /``).
"""

from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

from .errors import ArtifactError, SchemaMismatch

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_PYARROW_AVAILABLE: Optional[bool] = None  # cached


def _has_pyarrow() -> bool:
    global _PYARROW_AVAILABLE
    if _PYARROW_AVAILABLE is None:
        try:
            import pyarrow  # noqa: F401

            _PYARROW_AVAILABLE = True
        except ImportError:
            _PYARROW_AVAILABLE = False
    return _PYARROW_AVAILABLE


def _schema_hash(columns: List[str]) -> str:
    """Return a short hash of the sorted column names."""
    h = hashlib.sha256(",".join(sorted(columns)).encode()).hexdigest()
    return h[:12]


# ---------------------------------------------------------------------------
# DataFrame → file
# ---------------------------------------------------------------------------


def save_result_table(
    df: "Any",  # pandas.DataFrame
    artifact_dir: Path,
    *,
    filename: str = "result_table",
) -> Dict[str, Any]:
    """Save a pandas DataFrame as Parquet (preferred) or CSV (fallback).

    Args:
        df: ``pandas.DataFrame`` to persist.
        artifact_dir: Directory in which the file will be created.
        filename: Base filename (without extension).

    Returns:
        Artifact metadata dict with ``format``, ``path`` (relative),
        ``rows``, ``columns``, and ``schema_hash``.

    Raises:
        ArtifactError: If the DataFrame cannot be serialised.
    """
    artifact_dir = Path(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    columns: List[str] = list(df.columns)
    rows: int = len(df)
    schema_hash = _schema_hash(columns)

    if _has_pyarrow():
        import pyarrow as pa
        import pyarrow.parquet as pq

        try:
            table = pa.Table.from_pandas(df, preserve_index=False)
            out_path = artifact_dir / f"{filename}.parquet"
            pq.write_table(table, str(out_path))
            return {
                "format": "parquet",
                "path": f"{filename}.parquet",
                "rows": rows,
                "columns": columns,
                "schema_hash": schema_hash,
            }
        except Exception as exc:
            raise ArtifactError(f"Failed to write Parquet artifact: {exc}") from exc
    else:
        warnings.warn(
            "pyarrow is not installed; falling back to CSV for result storage. "
            "Install pyarrow for richer type preservation: pip install pyarrow",
            stacklevel=3,
        )
        try:
            out_path = artifact_dir / f"{filename}.csv"
            df.to_csv(str(out_path), index=False)
            return {
                "format": "csv",
                "path": f"{filename}.csv",
                "rows": rows,
                "columns": columns,
                "schema_hash": schema_hash,
            }
        except Exception as exc:
            raise ArtifactError(f"Failed to write CSV artifact: {exc}") from exc


def load_result_table(
    artifact_dir: Path,
    artifact_meta: Dict[str, Any],
) -> "Any":  # pandas.DataFrame
    """Load a result table from disk given its artifact metadata.

    Args:
        artifact_dir: Directory where the artifact resides.
        artifact_meta: Dict previously returned by :func:`save_result_table`.

    Returns:
        ``pandas.DataFrame``.

    Raises:
        ArtifactError: If the file cannot be read.
        SchemaMismatch: If the stored schema hash differs from the loaded data.
    """
    try:
        import pandas as pd
    except ImportError as exc:
        raise ArtifactError(
            "pandas is required to load result tables. Install with: pip install pandas"
        ) from exc

    artifact_dir = Path(artifact_dir)
    fmt = artifact_meta.get("format", "csv")
    rel_path = artifact_meta.get("path", "")
    full_path = artifact_dir / rel_path

    if not full_path.exists():
        raise ArtifactError(f"Artifact file not found: {full_path}")

    try:
        if fmt == "parquet":
            if not _has_pyarrow():
                raise ArtifactError(
                    "pyarrow is required to read Parquet artifacts. "
                    "Install with: pip install pyarrow"
                )
            import pyarrow.parquet as pq

            table = pq.read_table(str(full_path))
            df = table.to_pandas()
        else:  # csv fallback
            df = pd.read_csv(str(full_path))
    except ArtifactError:
        raise
    except Exception as exc:
        raise ArtifactError(f"Failed to read artifact {full_path}: {exc}") from exc

    # Verify schema hash
    stored_hash = artifact_meta.get("schema_hash", "")
    actual_hash = _schema_hash(list(df.columns))
    if stored_hash and stored_hash != actual_hash:
        raise SchemaMismatch(
            f"Schema mismatch for {rel_path}: "
            f"stored={stored_hash!r}, actual={actual_hash!r}"
        )

    return df


# ---------------------------------------------------------------------------
# JSON metadata
# ---------------------------------------------------------------------------


def save_metadata(data: Dict[str, Any], path: Path) -> None:
    """Write a JSON metadata file.

    Args:
        data: JSON-serialisable dict.
        path: Destination file path.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True, default=str)


def load_metadata(path: Path) -> Dict[str, Any]:
    """Load a JSON metadata file.

    Args:
        path: Source file path.

    Returns:
        Parsed dict.

    Raises:
        ArtifactError: If the file cannot be read or parsed.
    """
    path = Path(path)
    if not path.exists():
        raise ArtifactError(f"Metadata file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        raise ArtifactError(f"Failed to load metadata from {path}: {exc}") from exc
