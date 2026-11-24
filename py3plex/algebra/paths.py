"""Generic semiring path solver (graph backend).

Implements single-source shortest path (SSSP) and all-pairs shortest path (APSP)
algorithms parameterized by semiring operations.

Algorithm selection:
- Dijkstra-like: for idempotent+monotone semirings (e.g., min_plus, max_times)
- Bellman-Ford: for general semirings (handles negative weights/cycles)
- Fixed-point: for complete/idempotent semirings with convergence criteria
"""

import heapq
from itertools import count
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

from py3plex.exceptions import Py3plexException
from .semiring import Semiring
from .lift import WeightLiftSpec, lift_edge_value


@dataclass
class PathResult:
    """Result of a path query.
    
    Attributes:
        distances: Dictionary mapping node -> best value
        predecessors: Optional predecessor map for path reconstruction
        source: Source node (for SSSP)
        target: Optional target node (for single-pair)
        semiring_name: Name of semiring used
        algorithm: Algorithm used ("dijkstra", "bellman_ford", "fixed_point")
        converged: Whether algorithm converged (for fixed-point)
        iterations: Number of iterations performed
    """
    distances: Dict[Any, Any]
    predecessors: Optional[Dict[Any, Any]] = None
    source: Optional[Any] = None
    target: Optional[Any] = None
    semiring_name: str = "min_plus"
    algorithm: str = "dijkstra"
    converged: bool = True
    iterations: int = 0
    witnesses: Optional[Dict[Any, tuple]] = None
    
    def get_path(self, target: Any) -> Optional[List[Any]]:
        """Reconstruct path to target node.
        
        Args:
            target: Destination node
            
        Returns:
            List of nodes in path from source to target, or None if no path
        """
        if self.witnesses is not None:
            path = self.witnesses.get(target)
            return list(path) if path is not None else None
        if self.predecessors is None:
            return None
        if target not in self.predecessors:
            return None
        if target not in self.distances:
            return None
        
        # Reconstruct path backwards
        path = []
        current = target
        visited = set()  # Cycle detection
        
        while current is not None:
            if current in visited:
                # Cycle detected (shouldn't happen with proper algorithms)
                return None
            visited.add(current)
            path.append(current)
            current = self.predecessors.get(current)
        
        path.reverse()
        return path if path[0] == self.source else None


def sssp_dijkstra(
    nodes: List[Any],
    edges: List[Tuple[Any, Any, Dict[str, Any]]],
    source: Any,
    semiring: Semiring,
    lift_spec: WeightLiftSpec,
    target: Optional[Any] = None,
    max_hops: Optional[int] = None,
) -> PathResult:
    """Single-source shortest path using Dijkstra-like algorithm.
    
    Requires: semiring with idempotent_add and monotone properties.
    Works with semirings where better() defines a total order.
    
    Args:
        nodes: List of node identifiers
        edges: List of (source, target, attributes) tuples
        source: Source node
        semiring: Semiring instance
        lift_spec: Weight lift specification
        target: Optional target (can stop early)
        max_hops: Optional maximum path length
        
    Returns:
        PathResult with distances and predecessors
    """
    if max_hops is not None:
        return sssp_bellman_ford(nodes, edges, source, semiring, lift_spec, target, max_hops)
    weighted = _lift_edges(edges, lift_spec)
    if not _greedy_safe(semiring, weighted):
        raise Py3plexException("Dijkstra requires non-improving edge extensions.")
    adjacency = {node: [] for node in nodes}
    for u, v, weight in weighted:
        adjacency[u].append((v, weight))

    distances = dict.fromkeys(nodes, semiring.zero())
    distances[source] = semiring.one()
    predecessors = dict.fromkeys(nodes)
    order = count()
    queue = [(0, next(order), source)]
    visited = set()
    while queue:
        _, _, current = heapq.heappop(queue)
        if current in visited:
            continue
        visited.add(current)
        for neighbor, weight in adjacency[current]:
            candidate = semiring.mul(distances[current], weight)
            combined = semiring.add(distances[neighbor], candidate)
            if combined != distances[neighbor]:
                distances[neighbor] = combined
                predecessors[neighbor] = current
                priority = -float(combined) if semiring.name == "max_times" else float(combined)
                heapq.heappush(queue, (priority, next(order), neighbor))
    return PathResult(distances, predecessors, source, target, semiring.name,
                      "dijkstra", iterations=len(visited))


def _lift_edges(edges, lift_spec):
    return [(u, v, weight) for u, v, attrs in edges
            if (weight := lift_edge_value(attrs, lift_spec)) is not None]


def _greedy_safe(semiring, edges):
    if not getattr(semiring, "props", {}).get("idempotent_add"):
        return False
    if semiring.name == "min_plus":
        return all(weight >= 0 for _, _, weight in edges)
    if semiring.name == "max_times":
        return all(0 <= weight <= 1 for _, _, weight in edges)
    return False


def sssp_bellman_ford(
    nodes: List[Any],
    edges: List[Tuple[Any, Any, Dict[str, Any]]],
    source: Any,
    semiring: Semiring,
    lift_spec: WeightLiftSpec,
    target: Optional[Any] = None,
    max_hops: Optional[int] = None,
    max_iterations: Optional[int] = None,
) -> PathResult:
    """Single-source shortest path using Bellman-Ford-like algorithm.
    
    Works for general semirings. Iterates until convergence or max iterations.
    
    Args:
        nodes: List of node identifiers
        edges: List of (source, target, attributes) tuples
        source: Source node
        semiring: Semiring instance
        lift_spec: Weight lift specification
        target: Optional target (cannot stop early in general case)
        max_hops: Optional maximum path length (affects edge filtering)
        max_iterations: Maximum iterations (defaults to |V|-1)
        
    Returns:
        PathResult with distances and predecessors
    """
    if max_hops is not None and max_hops < 0:
        raise ValueError("max_hops must be nonnegative.")
    weighted = _lift_edges(edges, lift_spec)
    zero, one = semiring.zero(), semiring.one()
    limit = max_hops if max_hops is not None else max_iterations
    if limit is None:
        limit = max(0, len(nodes) - 1)
    distances = dict.fromkeys(nodes, zero)
    distances[source] = one
    frontier = {source: one}
    frontier_paths = {source: (source,)}
    witnesses = frontier_paths.copy()
    iterations = 0
    for _ in range(limit):
        next_frontier = {}
        next_paths = {}
        for u, v, weight in weighted:
            if u not in frontier:
                continue
            candidate = semiring.mul(frontier[u], weight)
            previous = next_frontier.get(v, zero)
            combined = semiring.add(previous, candidate)
            if combined != previous:
                next_frontier[v] = combined
                next_paths[v] = frontier_paths[u] + (v,)
        iterations += 1
        if not next_frontier:
            break
        for v, value in next_frontier.items():
            combined = semiring.add(distances[v], value)
            if combined != distances[v]:
                distances[v] = combined
                witnesses[v] = next_paths[v]
        frontier, frontier_paths = next_frontier, next_paths

    converged = True
    if max_hops is None:
        converged = all(
            semiring.add(distances[v], semiring.mul(distances[u], weight)) == distances[v]
            for u, v, weight in weighted if distances[u] != zero
        )
        if not converged and max_iterations is None:
            raise Py3plexException("Unbounded semiring paths have a reachable improving cycle.")

    return PathResult(distances, source=source, target=target, semiring_name=semiring.name,
                      algorithm="bellman_ford", converged=converged,
                      iterations=iterations, witnesses=witnesses)


def sssp(
    nodes: List[Any],
    edges: List[Tuple[Any, Any, Dict[str, Any]]],
    source: Any,
    semiring: Semiring,
    lift_spec: WeightLiftSpec,
    target: Optional[Any] = None,
    max_hops: Optional[int] = None,
    algorithm: Optional[str] = None,
) -> PathResult:
    """Single-source shortest path with automatic algorithm selection.
    
    Args:
        nodes: List of node identifiers
        edges: List of (source, target, attributes) tuples
        source: Source node
        semiring: Semiring instance
        lift_spec: Weight lift specification
        target: Optional target node
        max_hops: Optional maximum path length
        algorithm: Optional algorithm override ("dijkstra", "bellman_ford")
        
    Returns:
        PathResult with distances and predecessors
    """
    if algorithm is None:
        weighted = _lift_edges(edges, lift_spec) if max_hops is None else []
        algorithm = "dijkstra" if max_hops is None and _greedy_safe(semiring, weighted) else "bellman_ford"

    if algorithm == "dijkstra":
        return sssp_dijkstra(nodes, edges, source, semiring, lift_spec, target, max_hops)
    elif algorithm == "bellman_ford":
        return sssp_bellman_ford(nodes, edges, source, semiring, lift_spec, target, max_hops)
    else:
        raise Py3plexException(f"Unknown algorithm: {algorithm}")
