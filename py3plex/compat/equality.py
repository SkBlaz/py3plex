"""
Equality checking and comparison utilities for GraphIR.

Provides functions to compare GraphIR objects for equality and
generate diffs for debugging roundtrip conversions.
"""

from typing import List, Tuple

import pandas as pd

from .ir import GraphIR


def ir_equals(
    a: GraphIR,
    b: GraphIR,
    *,
    ignore_order: bool = False,
    tolerance: float = 1e-9,
) -> bool:
    """
    Check if two GraphIR objects are equal.
    
    Args:
        a: First GraphIR
        b: Second GraphIR
        ignore_order: If True, ignore node_order and edge_order differences
        tolerance: Numerical tolerance for float comparisons
    
    Returns:
        True if GraphIRs are equal, False otherwise
    
    Examples:
        >>> ir1 = to_ir(graph)
        >>> ir2 = to_ir(graph)
        >>> assert ir_equals(ir1, ir2)
    """
    # Check metadata
    if not _meta_equals(a.meta, b.meta):
        return False
    
    # Check node tables
    if not _node_table_equals(a.nodes, b.nodes, ignore_order=ignore_order, tolerance=tolerance):
        return False
    
    # Check edge tables
    if not _edge_table_equals(a.edges, b.edges, ignore_order=ignore_order, tolerance=tolerance):
        return False
    
    return True


def ir_diff(a: GraphIR, b: GraphIR) -> List[str]:
    """
    Generate a list of differences between two GraphIR objects.
    
    Args:
        a: First GraphIR
        b: Second GraphIR
    
    Returns:
        List of difference descriptions (empty if equal)
    
    Examples:
        >>> diffs = ir_diff(ir1, ir2)
        >>> if diffs:
        ...     for diff in diffs:
        ...         print(f"Difference: {diff}")
    """
    diffs = []
    
    # Check metadata
    diffs.extend(_meta_diff(a.meta, b.meta))
    
    # Check nodes
    diffs.extend(_node_table_diff(a.nodes, b.nodes))
    
    # Check edges
    diffs.extend(_edge_table_diff(a.edges, b.edges))
    
    return diffs


def _meta_equals(a, b) -> bool:
    """Check if GraphMeta objects are equal."""
    return (
        a.directed == b.directed
        and a.multi == b.multi
        and a.name == b.name
        and a.global_attrs == b.global_attrs
        and a.layers == b.layers
    )


def _meta_diff(a, b) -> List[str]:
    """Generate differences for GraphMeta."""
    diffs = []
    
    if a.directed != b.directed:
        diffs.append(f"directed: {a.directed} vs {b.directed}")
    
    if a.multi != b.multi:
        diffs.append(f"multi: {a.multi} vs {b.multi}")
    
    if a.name != b.name:
        diffs.append(f"name: '{a.name}' vs '{b.name}'")
    
    if a.layers != b.layers:
        diffs.append(f"layers: {a.layers} vs {b.layers}")
    
    if a.global_attrs != b.global_attrs:
        diffs.append(f"global_attrs differ: {set(a.global_attrs.keys()) ^ set(b.global_attrs.keys())}")
    
    return diffs


def _node_table_equals(a, b, ignore_order: bool, tolerance: float) -> bool:
    """Check if NodeTable objects are equal."""
    # Check counts
    if len(a.node_id) != len(b.node_id):
        return False
    
    # Check node IDs (order matters unless ignore_order)
    if not ignore_order:
        if a.node_id != b.node_id:
            return False
        if a.node_order != b.node_order:
            return False
    else:
        if set(a.node_id) != set(b.node_id):
            return False
    
    # Check attributes
    if a.attrs is None and b.attrs is None:
        return True
    elif a.attrs is None or b.attrs is None:
        return False
    
    # Compare DataFrames
    if not _dataframes_equal(a.attrs, b.attrs, tolerance):
        return False
    
    # Check layers
    if a.layer != b.layer:
        return False
    
    return True


def _node_table_diff(a, b) -> List[str]:
    """Generate differences for NodeTable."""
    diffs = []
    
    if len(a.node_id) != len(b.node_id):
        diffs.append(f"node count: {len(a.node_id)} vs {len(b.node_id)}")
    
    if set(a.node_id) != set(b.node_id):
        only_a = set(a.node_id) - set(b.node_id)
        only_b = set(b.node_id) - set(a.node_id)
        if only_a:
            diffs.append(f"nodes only in A: {list(only_a)[:5]}...")
        if only_b:
            diffs.append(f"nodes only in B: {list(only_b)[:5]}...")
    
    if a.node_order != b.node_order:
        diffs.append("node_order differs")
    
    if (a.attrs is None) != (b.attrs is None):
        diffs.append(f"node attrs: {'None' if a.attrs is None else 'present'} vs {'None' if b.attrs is None else 'present'}")
    
    if a.layer != b.layer:
        diffs.append("node layers differ")
    
    return diffs


def _edge_table_equals(a, b, ignore_order: bool, tolerance: float) -> bool:
    """Check if EdgeTable objects are equal."""
    # Check counts
    if len(a.edge_id) != len(b.edge_id):
        return False
    
    # Check edge IDs
    if not ignore_order:
        if a.edge_id != b.edge_id:
            return False
        if a.edge_order != b.edge_order:
            return False
    else:
        if set(a.edge_id) != set(b.edge_id):
            return False
    
    # Check endpoints
    if a.src != b.src or a.dst != b.dst:
        return False
    
    # Check attributes
    if a.attrs is None and b.attrs is None:
        return True
    elif a.attrs is None or b.attrs is None:
        return False
    
    if not _dataframes_equal(a.attrs, b.attrs, tolerance):
        return False
    
    # Check layers
    if a.src_layer != b.src_layer or a.dst_layer != b.dst_layer:
        return False
    
    return True


def _edge_table_diff(a, b) -> List[str]:
    """Generate differences for EdgeTable."""
    diffs = []
    
    if len(a.edge_id) != len(b.edge_id):
        diffs.append(f"edge count: {len(a.edge_id)} vs {len(b.edge_id)}")
    
    if set(a.edge_id) != set(b.edge_id):
        only_a = set(a.edge_id) - set(b.edge_id)
        only_b = set(b.edge_id) - set(a.edge_id)
        if only_a:
            diffs.append(f"edges only in A: {list(only_a)[:5]}...")
        if only_b:
            diffs.append(f"edges only in B: {list(only_b)[:5]}...")
    
    if a.src != b.src:
        diffs.append("edge sources differ")
    
    if a.dst != b.dst:
        diffs.append("edge destinations differ")
    
    if a.edge_order != b.edge_order:
        diffs.append("edge_order differs")
    
    if (a.attrs is None) != (b.attrs is None):
        diffs.append(f"edge attrs: {'None' if a.attrs is None else 'present'} vs {'None' if b.attrs is None else 'present'}")
    
    if a.src_layer != b.src_layer or a.dst_layer != b.dst_layer:
        diffs.append("edge layers differ")
    
    return diffs


def _dataframes_equal(df1: pd.DataFrame, df2: pd.DataFrame, tolerance: float) -> bool:
    """Check if two DataFrames are equal within tolerance."""
    # Check columns
    if set(df1.columns) != set(df2.columns):
        return False
    
    # Check shape
    if df1.shape != df2.shape:
        return False
    
    # Check values column by column
    for col in df1.columns:
        if df1[col].dtype.kind in ('f', 'i'):  # Numeric
            if not _numeric_series_equal(df1[col], df2[col], tolerance):
                return False
        else:  # Non-numeric
            if not df1[col].equals(df2[col]):
                # Try comparing with NaN handling
                if not (df1[col].isna() == df2[col].isna()).all():
                    return False
                mask = ~df1[col].isna()
                if not (df1[col][mask] == df2[col][mask]).all():
                    return False
    
    return True


def _numeric_series_equal(s1: pd.Series, s2: pd.Series, tolerance: float) -> bool:
    """Check if two numeric Series are equal within tolerance."""
    import numpy as np
    
    # Handle NaN values
    nan_mask1 = s1.isna()
    nan_mask2 = s2.isna()
    
    if not (nan_mask1 == nan_mask2).all():
        return False
    
    # Compare non-NaN values
    mask = ~nan_mask1
    if mask.any():
        return np.allclose(s1[mask], s2[mask], rtol=tolerance, atol=tolerance)
    
    return True
