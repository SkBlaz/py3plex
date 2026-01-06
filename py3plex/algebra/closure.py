"""Kleene star / transitive closure over semirings."""

from typing import Any, Dict, List, Tuple
from py3plex.exceptions import Py3plexException

from .semiring import Semiring
from .lift import WeightLiftSpec, lift_edge_value
from .paths import sssp


def closure_reachability(
    nodes: List[Any],
    edges: List[Tuple[Any, Any, Dict[str, Any]]],
    semiring: Semiring,
    lift_spec: WeightLiftSpec,
) -> Dict[Tuple[Any, Any], Any]:
    """Compute transitive closure using semiring operations.
    
    For boolean semiring, this is standard reachability closure.
    For min_plus, this is all-pairs shortest paths (APSP).
    
    Args:
        nodes: List of node identifiers
        edges: List of (source, target, attributes) tuples
        semiring: Semiring instance
        lift_spec: Weight lift specification
        
    Returns:
        Dictionary mapping (source, target) -> value
    """
    # Initialize result with direct edges
    result = {}
    
    # Set all pairs to zero (no path)
    for u in nodes:
        for v in nodes:
            if u == v:
                result[(u, v)] = semiring.one()
            else:
                result[(u, v)] = semiring.zero()
    
    # Add direct edges
    for src, dst, attrs in edges:
        weight = lift_edge_value(attrs, lift_spec)
        if weight is None:
            continue
        # Combine with existing (in case of parallel edges)
        result[(src, dst)] = semiring.add(result.get((src, dst), semiring.zero()), weight)
    
    # Floyd-Warshall-like closure
    # For each intermediate node k
    for k in nodes:
        for i in nodes:
            for j in nodes:
                # Try path i -> k -> j
                path_value = semiring.mul(result[(i, k)], result[(k, j)])
                # Update with best
                result[(i, j)] = semiring.add(result[(i, j)], path_value)
    
    return result


def closure_iterative(
    nodes: List[Any],
    edges: List[Tuple[Any, Any, Dict[str, Any]]],
    semiring: Semiring,
    lift_spec: WeightLiftSpec,
    max_iterations: int = 100,
) -> Dict[Tuple[Any, Any], Any]:
    """Compute transitive closure using iterative SSSP.
    
    Runs SSSP from each node. More efficient for sparse graphs.
    
    Args:
        nodes: List of node identifiers
        edges: List of (source, target, attributes) tuples
        semiring: Semiring instance
        lift_spec: Weight lift specification
        max_iterations: Maximum iterations per SSSP
        
    Returns:
        Dictionary mapping (source, target) -> value
    """
    result = {}
    
    for source in nodes:
        path_result = sssp(
            nodes=nodes,
            edges=edges,
            source=source,
            semiring=semiring,
            lift_spec=lift_spec,
            algorithm=None,  # Auto-select
        )
        
        for target, value in path_result.distances.items():
            result[(source, target)] = value
    
    return result


def closure(
    nodes: List[Any],
    edges: List[Tuple[Any, Any, Dict[str, Any]]],
    semiring: Semiring,
    lift_spec: WeightLiftSpec,
    method: str = "auto",
) -> Dict[Tuple[Any, Any], Any]:
    """Compute transitive closure.
    
    Args:
        nodes: List of node identifiers
        edges: List of (source, target, attributes) tuples
        semiring: Semiring instance
        lift_spec: Weight lift specification
        method: Algorithm selection:
                - "auto": choose based on graph size
                - "floyd_warshall": O(n³) dense algorithm
                - "iterative": Run SSSP from each node
        
    Returns:
        Dictionary mapping (source, target) -> value
    """
    n = len(nodes)
    
    if method == "auto":
        # Heuristic: use Floyd-Warshall for small graphs, iterative for large
        if n <= 100:
            method = "floyd_warshall"
        else:
            method = "iterative"
    
    if method == "floyd_warshall":
        return closure_reachability(nodes, edges, semiring, lift_spec)
    elif method == "iterative":
        return closure_iterative(nodes, edges, semiring, lift_spec)
    else:
        raise Py3plexException(f"Unknown closure method: {method}")
