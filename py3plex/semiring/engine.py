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
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from .core import SemiringSpec, SemiringExecutionError
from .types import PathResult


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
    
    # Select algorithm
    if algorithm == "auto":
        # Use Dijkstra for min_plus or idempotent with non-negative weights
        if semiring.name == "min_plus" or (semiring.is_idempotent_plus and semiring.leq):
            algorithm = "dijkstra"
        else:
            algorithm = "bellman_ford"
    
    # Extract graph data
    nodes, edges = _extract_graph(network, layer_filter)
    
    # Default lift function
    if lift is None:
        lift = lambda e: e.get('weight', semiring.one)
    
    # Run selected algorithm
    if algorithm == "dijkstra":
        return _dijkstra(nodes, edges, semiring, source, target, lift, witness)
    elif algorithm == "bellman_ford":
        return _bellman_ford(nodes, edges, semiring, source, target, lift, max_hops, witness)
    else:
        raise SemiringExecutionError(
            f"Unknown algorithm: '{algorithm}'",
            suggestions=["Use 'auto', 'dijkstra', or 'bellman_ford'"]
        )


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
    
    # Use Floyd-Warshall for small graphs
    if n <= size_threshold:
        return _floyd_warshall(node_list, edges, semiring, lift)
    else:
        # Bounded closure with max_hops
        return _bounded_closure(node_list, edges, semiring, lift, max_hops)


# ============================================================================
# Helper Functions
# ============================================================================

def _extract_graph(network: Any, layer_filter: Optional[List[str]] = None) -> Tuple[Set[Any], List[Dict[str, Any]]]:
    """Extract nodes and edges from network."""
    nodes = set()
    edges = []
    
    for node_data in network.get_nodes():
        if layer_filter is None or node_data.get('type') in layer_filter:
            nodes.add(node_data['source'])
    
    for edge_data in network.get_edges():
        if layer_filter is None or (
            edge_data.get('source_type') in layer_filter and
            edge_data.get('target_type') in layer_filter
        ):
            edges.append(edge_data)
            nodes.add(edge_data['source'])
            nodes.add(edge_data['target'])
    
    return nodes, edges


def _dijkstra(
    nodes: Set[Any],
    edges: List[Dict[str, Any]],
    semiring: SemiringSpec,
    source: Any,
    target: Optional[Any],
    lift: Callable,
    witness: bool,
) -> Dict[Any, PathResult]:
    """Dijkstra-like algorithm for semirings with ordering."""
    import heapq
    
    # Initialize distances
    dist = {node: semiring.zero for node in nodes}
    dist[source] = semiring.one
    
    # Track predecessors if witness requested
    pred = {node: None for node in nodes} if witness else None
    
    # Build adjacency list
    adj = {node: [] for node in nodes}
    for e in edges:
        u, v = e['source'], e['target']
        if u in nodes and v in nodes:
            adj[u].append((v, lift(e)))
    
    # Priority queue: (distance, node)
    pq = [(semiring.one, source)]
    visited = set()
    
    while pq:
        d_u, u = heapq.heappop(pq)
        
        if u in visited:
            continue
        visited.add(u)
        
        if target and u == target:
            break
        
        for v, weight in adj.get(u, []):
            new_dist = semiring.times(dist[u], weight)
            
            # Check if this is better
            if semiring.leq and semiring.leq(new_dist, dist[v]):
                if not _eq_with_default(new_dist, dist[v], semiring.eq):
                    dist[v] = new_dist
                    if pred is not None:
                        pred[v] = u
                    heapq.heappush(pq, (new_dist, v))
    
    # Build results
    results = {}
    for node in nodes:
        path_list = None
        if witness and pred is not None:
            path_list = _reconstruct_path(pred, source, node)
        results[node] = PathResult(value=dist[node], path=path_list)
    
    return results


def _bellman_ford(
    nodes: Set[Any],
    edges: List[Dict[str, Any]],
    semiring: SemiringSpec,
    source: Any,
    target: Optional[Any],
    lift: Callable,
    max_hops: Optional[int],
    witness: bool,
) -> Dict[Any, PathResult]:
    """Bellman-Ford relaxation for general semirings."""
    # Initialize
    dist = {node: semiring.zero for node in nodes}
    dist[source] = semiring.one
    
    pred = {node: None for node in nodes} if witness else None
    
    # Relaxation iterations
    n_iterations = max_hops if max_hops else len(nodes) - 1
    
    for iteration in range(n_iterations):
        changed = False
        for e in edges:
            u, v = e['source'], e['target']
            if u not in nodes or v not in nodes:
                continue
            
            edge_weight = lift(e)
            new_dist = semiring.times(dist[u], edge_weight)
            combined = semiring.plus(dist[v], new_dist)
            
            if not _eq_with_default(combined, dist[v], semiring.eq):
                dist[v] = combined
                if pred is not None:
                    pred[v] = u
                changed = True
        
        if not changed:
            break
    
    # Build results
    results = {}
    for node in nodes:
        path_list = None
        if witness and pred is not None:
            path_list = _reconstruct_path(pred, source, node)
        results[node] = PathResult(value=dist[node], path=path_list)
    
    return results


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
    closure = {}
    
    # Initialize with identity
    for u in nodes:
        for v in nodes:
            if u == v:
                closure[(u, v)] = semiring.one
            else:
                closure[(u, v)] = semiring.zero
    
    # Build adjacency
    adj = {node: [] for node in nodes}
    for e in edges:
        u, v = e['source'], e['target']
        if u in set(nodes) and v in set(nodes):
            adj[u].append((v, lift(e)))
    
    # Iterate up to max_hops
    for hop in range(max_hops):
        changed = False
        new_closure = closure.copy()
        
        for u in nodes:
            for v, weight in adj.get(u, []):
                for w in nodes:
                    # new_closure[u][w] = old[u][w] ⊕ (old[u][v] ⊗ old[v][w])
                    through_v = semiring.times(closure[(u, v)], closure[(v, w)])
                    combined = semiring.plus(new_closure[(u, w)], through_v)
                    
                    if not _eq_with_default(combined, new_closure[(u, w)], semiring.eq):
                        new_closure[(u, w)] = combined
                        changed = True
        
        closure = new_closure
        if not changed:
            break
    
    return closure


def _reconstruct_path(pred: Dict[Any, Any], source: Any, target: Any) -> Optional[List[Any]]:
    """Reconstruct path from predecessor map."""
    if pred[target] is None and target != source:
        return None
    
    path = []
    current = target
    while current is not None:
        path.append(current)
        if current == source:
            break
        current = pred[current]
    
    return list(reversed(path)) if path else None


def _eq_with_default(a: Any, b: Any, eq_fn: Optional[Callable] = None) -> bool:
    """Equality check with optional custom function."""
    if eq_fn:
        return eq_fn(a, b)
    return a == b
