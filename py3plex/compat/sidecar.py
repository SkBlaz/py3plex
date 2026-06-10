"""
Sidecar bundle format for lossless preservation of graph data.

Sidecar bundles store graph data in a directory with:
- meta.json: Graph metadata and schema
- nodes.parquet (or nodes.csv): Node table
- edges.parquet (or edges.csv): Edge table

This allows lossless roundtrip even when target formats are lossy.
"""

import json
import warnings
from pathlib import Path
from typing import Any, Dict, Literal, Optional

import pandas as pd

from .ir import EdgeTable, GraphIR, GraphMeta, NodeTable


def export_sidecar(
    ir: GraphIR,
    path: str,
    *,
    format: Literal["json+parquet", "json+csv"] = "json+parquet",
) -> None:
    """
    Export GraphIR to sidecar bundle.
    
    Args:
        ir: GraphIR to export
        path: Path for sidecar bundle (directory will be created)
        format: Storage format:
            - "json+parquet": JSON metadata + Parquet tables (requires pyarrow)
            - "json+csv": JSON metadata + CSV tables (fallback)
    
    Raises:
        ImportError: If pyarrow is required but not available
    """
    bundle_path = Path(path)
    bundle_path.mkdir(parents=True, exist_ok=True)
    
    # Export metadata
    meta_dict = ir.meta.to_dict()
    meta_path = bundle_path / "meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta_dict, f, indent=2, default=_json_serializer)
    
    # Determine table format
    if format == "json+parquet":
        try:
            __import__("pyarrow")
            
            table_format = "parquet"
        except ImportError:
            warnings.warn(
                "pyarrow not available, falling back to CSV format. "
                "Install pyarrow for better performance: pip install pyarrow",
                UserWarning,
            )
            table_format = "csv"
    else:
        table_format = "csv"
    
    # Export nodes
    nodes_dict = ir.nodes.to_dict()
    _export_table(nodes_dict, bundle_path / f"nodes.{table_format}", table_format)
    
    # Export edges
    edges_dict = ir.edges.to_dict()
    _export_table(edges_dict, bundle_path / f"edges.{table_format}", table_format)
    
    # Write format info
    format_path = bundle_path / "format.txt"
    with open(format_path, "w") as f:
        f.write(table_format)


def import_sidecar(path: str) -> GraphIR:
    """
    Import GraphIR from sidecar bundle.
    
    Args:
        path: Path to sidecar bundle directory
    
    Returns:
        GraphIR reconstructed from bundle
    
    Raises:
        FileNotFoundError: If bundle components are missing
        ValueError: If bundle format is invalid
    """
    bundle_path = Path(path)
    
    if not bundle_path.exists():
        raise FileNotFoundError(f"Sidecar bundle not found: {path}")
    
    if not bundle_path.is_dir():
        raise ValueError(f"Sidecar bundle must be a directory: {path}")
    
    # Check for metadata first (most critical file)
    meta_path = bundle_path / "meta.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"Missing meta.json in sidecar bundle: {path}")
    
    # Read format
    format_path = bundle_path / "format.txt"
    if format_path.exists():
        with open(format_path, "r") as f:
            table_format = f.read().strip()
    else:
        # Try to infer format
        if (bundle_path / "nodes.parquet").exists():
            table_format = "parquet"
        elif (bundle_path / "nodes.csv").exists():
            table_format = "csv"
        else:
            raise FileNotFoundError("Cannot determine table format in sidecar bundle")
    
    # Read metadata
    with open(meta_path, "r") as f:
        meta_dict = json.load(f)
    meta = GraphMeta.from_dict(meta_dict)
    
    # Read nodes
    nodes_path = bundle_path / f"nodes.{table_format}"
    if not nodes_path.exists():
        raise FileNotFoundError(f"Missing nodes table in sidecar bundle: {path}")
    nodes_dict = _import_table(nodes_path, table_format)
    nodes = NodeTable.from_dict(nodes_dict)
    
    # Read edges
    edges_path = bundle_path / f"edges.{table_format}"
    if not edges_path.exists():
        raise FileNotFoundError(f"Missing edges table in sidecar bundle: {path}")
    edges_dict = _import_table(edges_path, table_format)
    edges = EdgeTable.from_dict(edges_dict)
    
    return GraphIR(nodes=nodes, edges=edges, meta=meta)


def _export_table(data: Dict[str, Any], path: Path, format: str) -> None:
    """Export table data to file."""
    if format == "parquet":
        # Convert to DataFrame and export
        df = _dict_to_dataframe(data)
        df.to_parquet(path, index=False)
    elif format == "csv":
        df = _dict_to_dataframe(data)
        df.to_csv(path, index=False)
    else:
        raise ValueError(f"Unknown table format: {format}")


def _import_table(path: Path, format: str) -> Dict[str, Any]:
    """Import table data from file."""
    if format == "parquet":
        df = pd.read_parquet(path)
    elif format == "csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unknown table format: {format}")
    
    return _dataframe_to_dict(df)


def _dict_to_dataframe(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert table dict to DataFrame.
    
    Handles nested structures like attrs which may be a DataFrame or list of dicts.
    """
    result = {}
    row_count = _infer_table_row_count(data)
    
    for key, value in data.items():
        if isinstance(value, pd.DataFrame):
            # Flatten DataFrame columns into result
            attrs_df = value.reindex(range(row_count)) if row_count is not None else value
            for col in attrs_df.columns:
                result[f"attrs_{col}"] = [
                    _encode_attr_value(item) for item in attrs_df[col].tolist()
                ]
        elif isinstance(value, list) and all(isinstance(item, dict) for item in value):
            # List of dicts (attrs as records)
            attrs_df = pd.DataFrame(value)
            if row_count is not None:
                attrs_df = attrs_df.reindex(range(row_count))
            for col in attrs_df.columns:
                result[f"attrs_{col}"] = [
                    _encode_attr_value(item) for item in attrs_df[col].tolist()
                ]
        else:
            result[key] = value
    
    return pd.DataFrame(result)


def _dataframe_to_dict(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Convert DataFrame back to table dict.
    
    Reconstructs nested structures like attrs.
    """
    result = {}
    attrs_cols = []
    
    for col in df.columns:
        if col.startswith("attrs_"):
            attrs_cols.append(col)
        else:
            result[col] = df[col].tolist()
    
    # Reconstruct attrs DataFrame if present
    if attrs_cols:
        attrs_data = {}
        for col in attrs_cols:
            attr_name = col.replace("attrs_", "", 1)
            attrs_data[attr_name] = df[col].tolist()
        # Convert dict to list of dicts (records format) for NodeTable.from_dict
        num_rows = len(df)
        attrs_records = []
        for i in range(num_rows):
            record = {k: _decode_attr_value(v[i]) for k, v in attrs_data.items()}
            attrs_records.append(record)
        result["attrs"] = attrs_records
    
    return result


def _infer_table_row_count(data: Dict[str, Any]) -> Optional[int]:
    """Infer table row count from non-attribute list columns."""
    for key, value in data.items():
        if key == "attrs":
            continue
        if isinstance(value, list):
            return len(value)
        if isinstance(value, pd.Series):
            return len(value)
        if isinstance(value, pd.DataFrame):
            return len(value)
    return None


def _encode_attr_value(value: Any) -> str:
    """Encode heterogeneous attribute values as JSON for stable Parquet export."""
    try:
        if pd.isna(value):
            return "null"
    except (TypeError, ValueError):
        pass
    return json.dumps(value, default=_json_serializer)


def _decode_attr_value(value: Any) -> Any:
    """Decode JSON-encoded attribute values from sidecar tables."""
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _json_serializer(obj: Any) -> Any:
    """
    Custom JSON serializer for non-standard types.
    """
    import numpy as np
    
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    elif hasattr(obj, "__dict__"):
        return obj.__dict__
    else:
        return str(obj)
