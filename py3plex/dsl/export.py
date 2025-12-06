"""Export utilities for DSL v2.

This module provides functionality for exporting query results to files
in various formats (CSV, JSON, etc.).
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .ast import ExportSpec
from .errors import DslExecutionError


def export_result(result: Any, spec: ExportSpec) -> None:
    """Export query result to a file according to the export specification.
    
    This is the main entry point for file exports. It normalizes the result
    into a tabular format and dispatches to format-specific writers.
    
    Args:
        result: Query result (QueryResult, dict, or other supported type)
        spec: Export specification with path, format, columns, and options
        
    Raises:
        DslExecutionError: If export fails or result type is not supported
    """
    # Normalize result to rows and columns
    try:
        rows, columns = _normalize_result_to_rows(result, spec.columns)
    except Exception as e:
        raise DslExecutionError(
            f"Cannot export result of type {type(result).__name__}: {e}. "
            "Only QueryResult, dict, and list-of-dicts are supported for export."
        )
    
    # Ensure output directory exists
    try:
        output_path = Path(spec.path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise DslExecutionError(f"Cannot create output directory for '{spec.path}': {e}")
    
    # Dispatch to format-specific writer
    try:
        if spec.fmt == "csv":
            _write_csv(rows, columns, spec)
        elif spec.fmt == "json":
            _write_json(rows, columns, spec)
        elif spec.fmt == "tsv":
            # TSV is just CSV with tab delimiter
            spec_copy = ExportSpec(
                path=spec.path,
                fmt="csv",
                columns=spec.columns,
                options={**spec.options, "delimiter": "\t"},
            )
            _write_csv(rows, columns, spec_copy)
        else:
            raise DslExecutionError(
                f"Unsupported export format: '{spec.fmt}'. "
                "Supported formats: csv, json, tsv"
            )
    except DslExecutionError:
        raise
    except Exception as e:
        raise DslExecutionError(
            f"Failed to write export to '{spec.path}' (format: {spec.fmt}): {e}"
        )


def _normalize_result_to_rows(
    result: Any, columns_hint: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Normalize a result object to rows and columns.
    
    Supports:
        - QueryResult objects
        - dict[key] -> value (single-column)
        - dict[(node, layer)] -> value (multi-column)
        - list[dict] (already tabular)
        - pandas DataFrame (if available)
        
    Args:
        result: Result object to normalize
        columns_hint: Optional column selection/ordering hint
        
    Returns:
        Tuple of (rows as list of dicts, column names as list)
        
    Raises:
        ValueError: If result type is not supported
    """
    from .result import QueryResult
    
    # Case 1: QueryResult object
    if isinstance(result, QueryResult):
        return _normalize_query_result(result, columns_hint)
    
    # Case 2: Dict mapping (centrality-style results)
    if isinstance(result, dict):
        return _normalize_dict_result(result, columns_hint)
    
    # Case 3: List of dicts (already tabular)
    if isinstance(result, list) and all(isinstance(r, dict) for r in result):
        return _normalize_list_of_dicts(result, columns_hint)
    
    # Case 4: pandas DataFrame
    try:
        import pandas as pd
        if isinstance(result, pd.DataFrame):
            return _normalize_dataframe(result, columns_hint)
    except ImportError:
        pass
    
    raise ValueError(
        f"Unsupported result type: {type(result).__name__}. "
        "Supported types: QueryResult, dict, list[dict], pandas.DataFrame"
    )


def _normalize_query_result(
    result: 'QueryResult', columns_hint: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Normalize QueryResult to rows and columns."""
    rows = []
    
    # Base column is the item ID
    id_col = "id"
    
    for idx, item in enumerate(result.items):
        row = {id_col: str(item)}
        
        # Add computed attributes
        for attr_name, values in result.attributes.items():
            if isinstance(values, dict):
                row[attr_name] = values.get(item, None)
            elif isinstance(values, list) and idx < len(values):
                row[attr_name] = values[idx]
            else:
                row[attr_name] = None
        
        rows.append(row)
    
    # Determine column order
    if rows:
        all_columns = list(rows[0].keys())
    else:
        all_columns = [id_col] + list(result.attributes.keys())
    
    # Apply column hint if provided
    if columns_hint:
        columns = [c for c in columns_hint if c in all_columns]
    else:
        columns = all_columns
    
    return rows, columns


def _normalize_dict_result(
    result: Dict[Any, Any], columns_hint: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Normalize dict result (centrality-style) to rows and columns.
    
    Handles:
        - dict[node] -> score: becomes [{"node": ..., "score": ...}, ...]
        - dict[(node, layer)] -> score: becomes [{"node": ..., "layer": ..., "score": ...}, ...]
    """
    rows = []
    
    if not result:
        return [], []
    
    # Check the first key to determine structure (defensive handling of empty dict)
    try:
        first_key = next(iter(result.keys()))
    except StopIteration:
        return [], []
    
    if isinstance(first_key, tuple):
        # Multi-column key (e.g., (node, layer))
        if len(first_key) == 2:
            # Assume (node, layer) -> score
            for (node, layer), score in result.items():
                rows.append({"node": str(node), "layer": str(layer), "score": score})
            columns = ["node", "layer", "score"]
        else:
            # Generic tuple key
            for key, value in result.items():
                row = {f"key_{i}": str(k) for i, k in enumerate(key)}
                row["value"] = value
                rows.append(row)
            columns = [f"key_{i}" for i in range(len(first_key))] + ["value"]
    else:
        # Single-column key: node -> score
        for key, value in result.items():
            rows.append({"key": str(key), "value": value})
        columns = ["key", "value"]
    
    # Apply column hint if provided
    if columns_hint:
        columns = [c for c in columns_hint if c in columns]
    
    return rows, columns


def _normalize_list_of_dicts(
    result: List[Dict[str, Any]], columns_hint: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Normalize list of dicts to rows and columns."""
    if not result:
        return [], []
    
    # Infer columns from all rows
    all_keys = set()
    for row in result:
        all_keys.update(row.keys())
    
    columns = sorted(all_keys)
    
    # Apply column hint if provided
    if columns_hint:
        columns = [c for c in columns_hint if c in columns]
    
    return result, columns


def _normalize_dataframe(
    df: 'pd.DataFrame', columns_hint: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Normalize pandas DataFrame to rows and columns.
    
    Args:
        df: pandas DataFrame to normalize
        columns_hint: Optional column selection/ordering hint
        
    Returns:
        Tuple of (rows as list of dicts, column names as list)
    """
    # Apply column hint if provided
    if columns_hint:
        available_cols = [c for c in columns_hint if c in df.columns]
        df = df[available_cols]
    
    columns = list(df.columns)
    rows = df.to_dict('records')
    
    return rows, columns


def _write_csv(rows: List[Dict[str, Any]], columns: List[str], spec: ExportSpec) -> None:
    """Write rows to CSV file.
    
    Args:
        rows: List of row dictionaries
        columns: Column names (determines order)
        spec: Export specification
    """
    delimiter = spec.options.get("delimiter", ",")
    
    with open(spec.path, 'w', newline='', encoding='utf-8') as f:
        if not rows:
            # Write header only if no rows
            f.write(delimiter.join(columns) + "\n")
            return
        
        writer = csv.DictWriter(f, fieldnames=columns, delimiter=delimiter, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def _write_json(rows: List[Dict[str, Any]], columns: List[str], spec: ExportSpec) -> None:
    """Write rows to JSON file.
    
    Args:
        rows: List of row dictionaries
        columns: Column names (for filtering)
        spec: Export specification
    """
    orient = spec.options.get("orient", "records")
    indent = spec.options.get("indent", 2)
    
    # Filter rows to only include specified columns
    filtered_rows = []
    for row in rows:
        filtered_row = {k: v for k, v in row.items() if k in columns}
        filtered_rows.append(filtered_row)
    
    if orient == "records":
        # List of dicts (default)
        output = filtered_rows
    elif orient == "columns":
        # Dict of lists
        output = {col: [row.get(col) for row in filtered_rows] for col in columns}
    elif orient == "index":
        # Dict of dicts indexed by row number
        output = {i: row for i, row in enumerate(filtered_rows)}
    elif orient == "split":
        # Dict with 'columns', 'index', 'data'
        output = {
            "columns": columns,
            "index": list(range(len(filtered_rows))),
            "data": [[row.get(col) for col in columns] for row in filtered_rows],
        }
    elif orient == "values":
        # List of lists
        output = [[row.get(col) for col in columns] for row in filtered_rows]
    else:
        raise ValueError(f"Unsupported JSON orient: '{orient}'")
    
    with open(spec.path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=indent)
