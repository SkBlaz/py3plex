"""Executor for path query operations.

This module provides the main execution function for path queries.
"""

from typing import Any, Dict, List, Optional, Union

from .algorithms import path_registry
from .result import PathResult


def find_paths(
    network: Any,
    source: Union[str, Any],
    target: Optional[Union[str, Any]] = None,
    path_type: str = "shortest",
    layers: Optional[List[str]] = None,
    cross_layer: bool = False,
    limit: Optional[int] = None,
    **params,
) -> PathResult:
    """Find paths in a multilayer network.
    
    Args:
        network: Multilayer network
        source: Source node identifier
        target: Optional target node identifier
        path_type: Type of path query ("shortest", "all", "random_walk", "flow")
        layers: Optional list of layers to consider
        cross_layer: Whether to allow cross-layer paths
        limit: Maximum number of results
        **params: Additional parameters for the path algorithm
        
    Returns:
        PathResult with found paths
        
    Raises:
        ValueError: If path_type is not registered
    """
    # Get the path algorithm function
    path_fn = path_registry.get(path_type)
    
    # Execute the path query
    raw_result = path_fn(
        network=network,
        source=source,
        target=target,
        layers=layers,
        cross_layer=cross_layer,
        limit=limit,
        **params,
    )
    
    # Extract paths
    paths = raw_result.get("paths", [])
    
    # Apply limit if specified
    if limit is not None and paths:
        paths = paths[:limit]
    
    # Build metadata
    meta = {
        "path_type": path_type,
        "layers": layers,
        "cross_layer": cross_layer,
        "params": params,
    }
    
    # Add any extra info from the raw result
    for key in raw_result:
        if key not in ("paths", "visit_frequency", "flow_values"):
            meta[key] = raw_result[key]
    
    return PathResult(
        path_type=path_type,
        source=source,
        target=target,
        paths=paths,
        visit_frequency=raw_result.get("visit_frequency"),
        flow_values=raw_result.get("flow_values"),
        meta=meta,
    )


def execute_path_stmt(
    network: Any,
    stmt: "PathStmt",
) -> PathResult:
    """Execute a PATH statement from the DSL.
    
    Args:
        network: Multilayer network
        stmt: PathStmt AST node
        
    Returns:
        PathResult with found paths
    """
    # Get layers from layer expression
    layers = None
    if stmt.layer_expr:
        layers = stmt.layer_expr.get_layer_names()
    
    return find_paths(
        network=network,
        source=stmt.source,
        target=stmt.target,
        path_type=stmt.path_type,
        layers=layers,
        cross_layer=stmt.cross_layer,
        limit=stmt.limit,
        **stmt.params,
    )
