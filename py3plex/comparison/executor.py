"""Executor for network comparison operations.

This module provides the main execution function for comparing multilayer networks.
"""

from typing import Any, Dict, List, Optional, Set

from .metrics import metric_registry
from .result import ComparisonResult


def compare_networks(
    network_a: Any,
    network_b: Any,
    metric: str = "multiplex_jaccard",
    layers: Optional[List[str]] = None,
    measures: Optional[List[str]] = None,
    network_a_name: str = "network_a",
    network_b_name: str = "network_b",
) -> ComparisonResult:
    """Compare two multilayer networks using the specified metric.
    
    Args:
        network_a: First multilayer network
        network_b: Second multilayer network
        metric: Comparison metric name (default: "multiplex_jaccard")
        layers: Optional list of layers to consider
        measures: Optional list of measure types to compute
                  (e.g., ["global_distance", "layerwise_distance", "per_node_difference"])
        network_a_name: Name/key for the first network (for results)
        network_b_name: Name/key for the second network (for results)
        
    Returns:
        ComparisonResult with comparison results
        
    Raises:
        ValueError: If metric is not registered
    """
    measures = measures or ["global_distance"]
    
    # Get the metric function
    metric_fn = metric_registry.get(metric)
    
    # Execute the comparison
    raw_result = metric_fn(network_a, network_b, layers=layers)
    
    # Build result based on requested measures
    global_distance = None
    layerwise_distance = None
    per_node_difference = None
    
    if "global_distance" in measures:
        global_distance = raw_result.get("global_distance")
    
    if "layerwise_distance" in measures:
        layerwise_distance = raw_result.get("layerwise_distance")
    
    if "per_node_difference" in measures:
        per_node_difference = raw_result.get("per_node_difference")
    
    # Build metadata
    meta = {
        "metric": metric,
        "layers": layers,
        "measures": measures,
    }
    
    # Add any extra info from the raw result
    for key in raw_result:
        if key not in ("global_distance", "layerwise_distance", "per_node_difference"):
            meta[key] = raw_result[key]
    
    return ComparisonResult(
        metric_name=metric,
        network_a_name=network_a_name,
        network_b_name=network_b_name,
        global_distance=global_distance,
        layerwise_distance=layerwise_distance,
        per_node_difference=per_node_difference,
        meta=meta,
    )


def execute_compare_stmt(
    networks: Dict[str, Any],
    stmt: "CompareStmt",
) -> ComparisonResult:
    """Execute a COMPARE statement from the DSL.
    
    Args:
        networks: Dictionary mapping network names to network objects
        stmt: CompareStmt AST node
        
    Returns:
        ComparisonResult with comparison results
        
    Raises:
        ValueError: If network names are not found in the dictionary
    """
    from py3plex.dsl.ast import CompareStmt
    
    # Get networks from the dictionary
    if stmt.network_a not in networks:
        raise ValueError(f"Network '{stmt.network_a}' not found. Available: {list(networks.keys())}")
    if stmt.network_b not in networks:
        raise ValueError(f"Network '{stmt.network_b}' not found. Available: {list(networks.keys())}")
    
    network_a = networks[stmt.network_a]
    network_b = networks[stmt.network_b]
    
    # Get layers from layer expression
    layers = None
    if stmt.layer_expr:
        layers = stmt.layer_expr.get_layer_names()
    
    # Get measures
    measures = stmt.measures if stmt.measures else ["global_distance"]
    
    return compare_networks(
        network_a=network_a,
        network_b=network_b,
        metric=stmt.metric_name,
        layers=layers,
        measures=measures,
        network_a_name=stmt.network_a,
        network_b_name=stmt.network_b,
    )
