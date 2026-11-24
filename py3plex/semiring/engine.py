"""Semiring path and closure algorithms.

Definition (Path algebra).
For a walk w = (e1, e2, ..., ek), its semiring weight is:
W(w) = lift(e1) ⊗ lift(e2) ⊗ ... ⊗ lift(ek).
For two alternative walks w and w', the combined value is W(w) ⊕ W(w').

Definition (Closure).
Given semiring adjacency A (where A[u,v] aggregates all edges u→v via ⊕), the closure is:
A* = I ⊕ A ⊕ A^2 ⊕ A^3 ⊕ ...
where I has I[u,u]=1 and I[u,v]=0 for u≠v, and multiplication/addition are semiring matrix ops.
"""

import warnings
from typing import Any, Callable, Dict, List, Optional, Tuple
from .core import SemiringSpec, SemiringExecutionError
from .types import PathResult
from py3plex.algebra.paths import sssp
from py3plex.algebra.lift import WeightLiftSpec
from py3plex.exceptions import Py3plexException


class _AlgebraAdapter:
    def __init__(self, spec):
        self.name = spec.name
        self.add = spec.plus
        self.mul = spec.times
        self.zero = lambda: spec.zero
        self.one = lambda: spec.one
        self.props = {"idempotent_add": spec.is_idempotent_plus}


def semiring_paths(
    network: Any,
    semiring: SemiringSpec,
    source: Any,
    target: Optional[Any] = None,
    lift: Optional[Callable[[Dict[str, Any]], Any]] = None,
    layer_filter: Optional[List[str]] = None,
    max_hops: Optional[int] = None,
    algorithm: str = "auto",
    witness: bool = False,
) -> Dict[Any, PathResult]:
    """Compute single-source semiring paths.
    
    Args:
        network: Multilayer network
        semiring: SemiringSpec instance
        source: Source node
        target: Optional target node (if None, compute to all nodes)
        lift: Optional edge weight extraction function
        layer_filter: Optional list of layers to consider
        max_hops: Maximum path length (required for non-idempotent semirings)
        algorithm: "auto", "dijkstra", or "bellman_ford"
        witness: Whether to track path witnesses
        
    Returns:
        Dictionary mapping nodes to PathResult instances
        
    Raises:
        SemiringExecutionError: On invalid configuration or execution errors
    """
    # Validate inputs
    if not hasattr(network, 'get_nodes') or not hasattr(network, 'get_edges'):
        raise SemiringExecutionError(
            "Network must have get_nodes() and get_edges() methods"
        )
    
    # Check max_hops requirement for non-idempotent semirings
    if not semiring.is_idempotent_plus and max_hops is None:
        if semiring.leq is None:
            raise SemiringExecutionError(
                f"Semiring '{semiring.name}' is non-idempotent and has no ordering (leq). "
                "max_hops parameter is required to ensure termination.",
                suggestions=[
                    "Provide max_hops parameter (e.g., max_hops=network.number_of_nodes())",
                    "Use an idempotent semiring if unbounded iteration is needed"
                ]
            )
        else:
            # Provide a safe default but warn
            max_hops = len(list(network.get_nodes()))
            warnings.warn(
                f"max_hops not specified for non-idempotent semiring '{semiring.name}'. "
                f"Using default max_hops={max_hops}. Specify explicitly for clarity.",
                UserWarning
            )
    
    nodes, edges = _extract_graph(network, layer_filter)
    source = _resolve_node(nodes, source)
    target = _resolve_node(nodes, target) if target is not None else None
    if lift is None:
        lift = lambda edge: edge.get("weight", semiring.one)
    weighted = [(edge["source"], edge["target"], {"value": lift(edge)}) for edge in edges]
    try:
        result = sssp(
            list(nodes), weighted, source, _AlgebraAdapter(semiring),
            WeightLiftSpec(attr="value"), target, max_hops,
            None if algorithm == "auto" else algorithm,
        )
    except Py3plexException as error:
        raise SemiringExecutionError(str(error)) from error

    return {node: PathResult(value, result.get_path(node) if witness else None)
            for node, value in result.distances.items()}


def _resolve_node(nodes, selector):
    if selector in nodes:
        return selector
    replicas = [node for node in nodes if isinstance(node, tuple) and node[0] == selector]
    if len(replicas) == 1:
        return replicas[0]
    raise SemiringExecutionError(f"Select an unambiguous node replica for {selector!r}.")


def semiring_closure(
    network: Any,
    semiring: SemiringSpec,
    lift: Optional[Callable[[Dict[str, Any]], Any]] = None,
    layer_filter: Optional[List[str]] = None,
    max_hops: Optional[int] = None,
    size_threshold: int = 100,
) -> Dict[Tuple[Any, Any], Any]:
    """Compute all-pairs semiring closure.
    
    Args:
        network: Multilayer network
        semiring: SemiringSpec instance
        lift: Optional edge weight extraction function
        layer_filter: Optional list of layers to consider
        max_hops: Maximum path length for bounded closure
        size_threshold: Maximum nodes for Floyd-Warshall (use bounded otherwise)
        
    Returns:
        Dictionary mapping (source, target) pairs to semiring values
        
    Raises:
        SemiringExecutionError: On invalid configuration
    """
    nodes, edges = _extract_graph(network, layer_filter)
    node_list = list(nodes)
    n = len(node_list)
    
    # Check size threshold
    if n > size_threshold and max_hops is None:
        raise SemiringExecutionError(
            f"Network has {n} nodes (> threshold {size_threshold}). "
            "max_hops parameter required for bounded closure.",
            suggestions=[
                f"Provide max_hops parameter (e.g., max_hops={min(10, n)})",
                f"Increase size_threshold if you want full closure"
            ]
        )
    
    if lift is None:
        lift = lambda e: e.get('weight', semiring.one)
    
    if max_hops is not None:
        return _bounded_closure(node_list, edges, semiring, lift, max_hops)
    if not semiring.is_idempotent_plus:
        raise SemiringExecutionError("max_hops parameter is required for non-idempotent closure.")
    result = _floyd_warshall(node_list, edges, semiring, lift)
    if semiring.name == "min_plus" and any(result[node, node] < 0 for node in nodes):
        raise SemiringExecutionError("Unbounded semiring closure contains a negative cycle.")
    return result


def _extract_graph(network: Any, layer_filter: Optional[List[str]] = None):
    """Normalize py3plex replicas and legacy dictionary records."""
    if hasattr(network, "core_network") and network.core_network is None:
        return set(), []
    allowed = None if layer_filter is None else set(layer_filter)
    nodes = set()
    for record in network.get_nodes():
        if isinstance(record, dict):
            if allowed is None or record.get("type") in allowed:
                nodes.add(record["source"])
        elif allowed is None or record[1] in allowed:
            nodes.add(record)

    edges = []
    if hasattr(network, "core_network"):
        records = network.core_network.edges(data=True)
    else:
        records = network.get_edges()
    for record in records:
        if isinstance(record, dict):
            edge = record
        else:
            u, v, attrs = record
            edge = {**attrs, "source": u, "target": v,
                    "source_type": u[1], "target_type": v[1]}
        u, v = edge["source"], edge["target"]
        if u in nodes and v in nodes:
            edges.append(edge)
            if u != v and not getattr(network, "directed", True):
                edges.append({**edge, "source": v, "target": u,
                              "source_type": edge.get("target_type"),
                              "target_type": edge.get("source_type")})
    return nodes, edges


def _floyd_warshall(
    nodes: List[Any],
    edges: List[Dict[str, Any]],
    semiring: SemiringSpec,
    lift: Callable,
) -> Dict[Tuple[Any, Any], Any]:
    """Floyd-Warshall for closure."""
    n = len(nodes)
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    
    # Initialize with identity and direct edges
    closure = {}
    for i, u in enumerate(nodes):
        for j, v in enumerate(nodes):
            if i == j:
                closure[(u, v)] = semiring.one
            else:
                closure[(u, v)] = semiring.zero
    
    # Add direct edges
    for e in edges:
        u, v = e['source'], e['target']
        if u in node_to_idx and v in node_to_idx:
            weight = lift(e)
            closure[(u, v)] = semiring.plus(closure[(u, v)], weight)
    
    # Floyd-Warshall iterations
    for k in range(n):
        for i in range(n):
            for j in range(n):
                u, v, w = nodes[i], nodes[j], nodes[k]
                # closure[i][j] = closure[i][j] ⊕ (closure[i][k] ⊗ closure[k][j])
                through_k = semiring.times(closure[(u, w)], closure[(w, v)])
                closure[(u, v)] = semiring.plus(closure[(u, v)], through_k)
    
    return closure


def _bounded_closure(
    nodes: List[Any],
    edges: List[Dict[str, Any]],
    semiring: SemiringSpec,
    lift: Callable,
    max_hops: int,
) -> Dict[Tuple[Any, Any], Any]:
    """Bounded closure with max_hops iterations."""
    weighted = [(edge["source"], edge["target"], {"value": lift(edge)}) for edge in edges]
    adapter = _AlgebraAdapter(semiring)
    spec = WeightLiftSpec(attr="value")
    return {(u, v): value for u in nodes
            for v, value in sssp(nodes, weighted, u, adapter, spec, max_hops=max_hops).distances.items()}
