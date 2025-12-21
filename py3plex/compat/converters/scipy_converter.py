"""
SciPy sparse matrix converter with sidecar bundle support.

This converter handles conversion to/from sparse matrices, with
sidecar bundles to preserve attributes and multigraph structure
that cannot be represented in matrices.
"""

import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import scipy.sparse as sp

from ..exceptions import CompatibilityError
from ..ir import EdgeTable, GraphIR, GraphMeta, NodeTable


def to_scipy_sparse_from_ir(
    ir: GraphIR,
    *,
    weight: str = "weight",
    strict: bool = True,
    sidecar: Optional[str] = None,
    format: str = "csr",
    **kwargs,
) -> sp.spmatrix:
    """
    Convert GraphIR to SciPy sparse matrix.
    
    Args:
        ir: GraphIR to convert
        weight: Edge attribute to use as matrix values (default: "weight")
        strict: If True, raise exception if multigraph or attributes cannot be represented
        sidecar: Path for sidecar bundle to preserve non-matrix data (required in non-strict mode)
        format: Sparse matrix format ("csr", "csc", "coo", etc.)
        **kwargs: Additional arguments
    
    Returns:
        SciPy sparse matrix
    
    Raises:
        CompatibilityError: In strict mode, if graph cannot be represented as matrix
    """
    # Check for multigraph
    if ir.meta.multi and strict:
        raise CompatibilityError(
            "Cannot represent multigraph as sparse matrix in strict mode",
            reason="Sparse matrices cannot represent parallel edges",
            suggestions=[
                "Set strict=False and provide sidecar path to preserve multi-edges",
                "Aggregate parallel edges before conversion (e.g., sum weights)",
            ],
        )
    
    # Check for attributes (excluding weight)
    has_node_attrs = ir.nodes.attrs is not None and len(ir.nodes.attrs.columns) > 0
    has_edge_attrs = ir.edges.attrs is not None and len(
        [col for col in ir.edges.attrs.columns if col != weight]
    ) > 0
    
    if strict and (has_node_attrs or has_edge_attrs):
        raise CompatibilityError(
            "Cannot represent node/edge attributes in sparse matrix in strict mode",
            reason="Sparse matrices only represent connectivity and edge weights",
            suggestions=[
                "Set strict=False and provide sidecar path to preserve attributes",
                "Remove attributes before conversion if they are not needed",
            ],
        )
    
    # In non-strict mode with attributes or multigraph, require sidecar
    if not strict and (ir.meta.multi or has_node_attrs or has_edge_attrs):
        if sidecar is None:
            warnings.warn(
                "Non-strict mode with attributes/multigraph but no sidecar path provided. "
                "Data loss will occur. Provide sidecar path to preserve all data.",
                UserWarning,
            )
        else:
            # Export sidecar bundle
            from ..sidecar import export_sidecar
            
            export_sidecar(ir, sidecar)
            warnings.warn(
                f"Sidecar bundle exported to {sidecar} to preserve attributes/multigraph data",
                UserWarning,
            )
    
    # Build node ID to index mapping
    node_to_idx = {node_id: idx for idx, node_id in enumerate(ir.nodes.node_id)}
    n_nodes = len(ir.nodes.node_id)
    
    # Build edge lists
    row_indices = []
    col_indices = []
    data_values = []
    
    for idx in range(len(ir.edges.edge_id)):
        src = ir.edges.src[idx]
        dst = ir.edges.dst[idx]
        
        src_idx = node_to_idx[src]
        dst_idx = node_to_idx[dst]
        
        # Get weight value
        if ir.edges.attrs is not None and weight in ir.edges.attrs.columns:
            value = ir.edges.attrs.iloc[idx][weight]
            if pd.isna(value):
                value = 1.0
        else:
            value = 1.0
        
        row_indices.append(src_idx)
        col_indices.append(dst_idx)
        data_values.append(value)
        
        # For undirected graphs, add symmetric entry
        if not ir.meta.directed and src_idx != dst_idx:
            row_indices.append(dst_idx)
            col_indices.append(src_idx)
            data_values.append(value)
    
    # Create sparse matrix in COO format first
    matrix = sp.coo_matrix(
        (data_values, (row_indices, col_indices)),
        shape=(n_nodes, n_nodes),
        dtype=float,
    )
    
    # Convert to requested format
    if format == "csr":
        matrix = matrix.tocsr()
    elif format == "csc":
        matrix = matrix.tocsc()
    elif format == "coo":
        pass  # already in COO
    elif format == "lil":
        matrix = matrix.tolil()
    elif format == "dok":
        matrix = matrix.todok()
    elif format == "bsr":
        matrix = matrix.tobsr()
    else:
        warnings.warn(f"Unknown format {format}, returning CSR", UserWarning)
        matrix = matrix.tocsr()
    
    return matrix


def from_scipy_sparse_to_ir(
    matrix: sp.spmatrix,
    *,
    node_ids: Optional[List[Any]] = None,
    directed: bool = True,
    weight_attr: str = "weight",
    sidecar: Optional[str] = None,
    **kwargs,
) -> GraphIR:
    """
    Convert SciPy sparse matrix to GraphIR.
    
    Args:
        matrix: Sparse matrix to convert
        node_ids: Optional list of node identifiers (default: 0, 1, 2, ...)
        directed: Whether to treat matrix as directed
        weight_attr: Name for edge weight attribute
        sidecar: Path to sidecar bundle to load additional data
        **kwargs: Additional arguments
    
    Returns:
        GraphIR representation
    """
    if not sp.issparse(matrix):
        raise TypeError("matrix must be a scipy sparse matrix")
    
    n_nodes = matrix.shape[0]
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Matrix must be square")
    
    # Generate node IDs if not provided
    if node_ids is None:
        node_ids = list(range(n_nodes))
    elif len(node_ids) != n_nodes:
        raise ValueError(f"node_ids length {len(node_ids)} must match matrix shape {n_nodes}")
    
    # Convert to COO format for easy iteration
    coo = matrix.tocoo()
    
    # Build edge list
    edge_id_list = []
    src_list = []
    dst_list = []
    edge_order_list = []
    weights = []
    
    edge_idx = 0
    for row, col, value in zip(coo.row, coo.col, coo.data):
        # Skip lower triangle for undirected graphs to avoid duplicates
        if not directed and col < row:
            continue
        
        src_node = node_ids[row]
        dst_node = node_ids[col]
        
        edge_id_list.append(f"e{edge_idx}")
        src_list.append(src_node)
        dst_list.append(dst_node)
        edge_order_list.append(edge_idx)
        weights.append(value)
        edge_idx += 1
    
    # Build tables
    nodes = NodeTable(
        node_id=node_ids,
        node_order=list(range(n_nodes)),
        attrs=None,
    )
    
    # Create edge attributes DataFrame with weights
    edge_attrs_df = pd.DataFrame({weight_attr: weights}) if weights else None
    
    edges = EdgeTable(
        edge_id=edge_id_list,
        src=src_list,
        dst=dst_list,
        edge_order=edge_order_list,
        attrs=edge_attrs_df,
    )
    
    meta = GraphMeta(
        directed=directed,
        multi=False,  # Sparse matrix is always simple graph
        created_by="scipy_sparse_converter",
    )
    
    ir = GraphIR(nodes=nodes, edges=edges, meta=meta)
    
    # If sidecar provided, merge its data
    if sidecar is not None:
        from ..sidecar import import_sidecar
        
        sidecar_ir = import_sidecar(sidecar)
        ir = _merge_sidecar_data(ir, sidecar_ir)
    
    return ir


def _merge_sidecar_data(base_ir: GraphIR, sidecar_ir: GraphIR) -> GraphIR:
    """
    Merge sidecar data into base IR.
    
    This adds attributes and metadata from sidecar to the base IR
    created from the sparse matrix.
    """
    # Merge node attributes
    if sidecar_ir.nodes.attrs is not None:
        # Create mapping from node_id to sidecar attributes
        sidecar_node_attrs = {}
        for idx, node_id in enumerate(sidecar_ir.nodes.node_id):
            sidecar_node_attrs[node_id] = sidecar_ir.nodes.attrs.iloc[idx].to_dict()
        
        # Add attributes to base nodes
        if base_ir.nodes.attrs is None:
            # Create new DataFrame
            node_attrs_records = []
            for node_id in base_ir.nodes.node_id:
                attrs = sidecar_node_attrs.get(node_id, {})
                node_attrs_records.append(attrs)
            base_ir.nodes.attrs = pd.DataFrame(node_attrs_records)
        else:
            # Merge with existing DataFrame
            for idx, node_id in enumerate(base_ir.nodes.node_id):
                if node_id in sidecar_node_attrs:
                    for key, value in sidecar_node_attrs[node_id].items():
                        if key not in base_ir.nodes.attrs.columns:
                            base_ir.nodes.attrs[key] = None
                        base_ir.nodes.attrs.at[idx, key] = value
    
    # Merge edge attributes
    if sidecar_ir.edges.attrs is not None:
        # Create mapping from (src, dst) to sidecar attributes
        sidecar_edge_attrs = {}
        for idx in range(len(sidecar_ir.edges.edge_id)):
            src = sidecar_ir.edges.src[idx]
            dst = sidecar_ir.edges.dst[idx]
            key = (src, dst)
            attrs = sidecar_ir.edges.attrs.iloc[idx].to_dict()
            sidecar_edge_attrs[key] = attrs
        
        # Add attributes to base edges
        if base_ir.edges.attrs is None:
            edge_attrs_records = []
            for idx in range(len(base_ir.edges.edge_id)):
                src = base_ir.edges.src[idx]
                dst = base_ir.edges.dst[idx]
                key = (src, dst)
                attrs = sidecar_edge_attrs.get(key, {})
                edge_attrs_records.append(attrs)
            base_ir.edges.attrs = pd.DataFrame(edge_attrs_records)
        else:
            # Merge with existing DataFrame
            for idx in range(len(base_ir.edges.edge_id)):
                src = base_ir.edges.src[idx]
                dst = base_ir.edges.dst[idx]
                key = (src, dst)
                if key in sidecar_edge_attrs:
                    for attr_key, value in sidecar_edge_attrs[key].items():
                        if attr_key not in base_ir.edges.attrs.columns:
                            base_ir.edges.attrs[attr_key] = None
                        base_ir.edges.attrs.at[idx, attr_key] = value
    
    # Merge metadata
    base_ir.meta.layers = sidecar_ir.meta.layers
    base_ir.meta.global_attrs.update(sidecar_ir.meta.global_attrs)
    if sidecar_ir.meta.name:
        base_ir.meta.name = sidecar_ir.meta.name
    
    return base_ir
