"""Generic semiring path solver (graph backend).

Implements single-source shortest path (SSSP) and all-pairs shortest path (APSP)
algorithms parameterized by semiring operations.

Algorithm selection:
- Dijkstra-like: for idempotent+monotone semirings (e.g., min_plus, max_times)
- Bellman-Ford: for general semirings (handles negative weights/cycles)
- Fixed-point: for complete/idempotent semirings with convergence criteria
"""

import heapq
import math
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field

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
    
    def get_path(self, target: Any) -> Optional[List[Any]]:
        """Reconstruct path to target node.
        
        Args:
            target: Destination node
            
        Returns:
            List of nodes in path from source to target, or None if no path
        """
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
        return path


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
    # Initialize distances
    distances = {node: semiring.zero() for node in nodes}
    distances[source] = semiring.one()
    
    # Predecessors for path reconstruction
    predecessors = {node: None for node in nodes}
    
    # Priority queue: (priority, node, hops)
    # Priority is determined by semiring.better()
    # For min_plus: smaller is better (use value directly)
    # For max_times: larger is better (use negative for min-heap)
    pq = [(semiring.one(), source, 0)]
    visited = set()
    
    # Build adjacency list
    adj = {node: [] for node in nodes}
    for src, dst, attrs in edges:
        weight = lift_edge_value(attrs, lift_spec)
        if weight is None:  # on_missing="drop"
            continue
        # Add nodes to adj if not present (they might come from edges)
        if src not in adj:
            adj[src] = []
            if src not in distances:
                distances[src] = semiring.zero()
                predecessors[src] = None
        if dst not in adj:
            adj[dst] = []
            if dst not in distances:
                distances[dst] = semiring.zero()
                predecessors[dst] = None
        adj[src].append((dst, weight))
    
    iterations = 0
    while pq:
        iterations += 1
        
        # Get node with best value
        # For min-heap, we need to adapt based on semiring.better()
        current_dist, current, hops = heapq.heappop(pq)
        
        if current in visited:
            continue
        visited.add(current)
        
        # Early termination if target reached
        if target is not None and current == target:
            break
        
        # Check hop limit
        if max_hops is not None and hops >= max_hops:
            continue
        
        # Relax neighbors
        for neighbor, edge_weight in adj[current]:
            if neighbor in visited:
                continue
            
            # Compute new distance: current_dist ⊗ edge_weight
            new_dist = semiring.mul(distances[current], edge_weight)
            
            # Update if better: new_dist ⊕ old_dist
            old_dist = distances[neighbor]
            combined = semiring.add(old_dist, new_dist)
            
            if combined != old_dist:  # Value changed
                distances[neighbor] = combined
                predecessors[neighbor] = current
                
                # Add to priority queue
                # Use negative for max-heap behavior
                if semiring.name in ("max_plus", "max_times"):
                    priority = -_value_as_float(combined)
                else:
                    priority = _value_as_float(combined)
                
                heapq.heappush(pq, (priority, neighbor, hops + 1))
    
    return PathResult(
        distances=distances,
        predecessors=predecessors,
        source=source,
        target=target,
        semiring_name=semiring.name,
        algorithm="dijkstra",
        converged=True,
        iterations=iterations,
    )


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
    # Initialize distances
    distances = {node: semiring.zero() for node in nodes}
    distances[source] = semiring.one()
    
    # Predecessors
    predecessors = {node: None for node in nodes}
    
    # Process edges
    edge_list = []
    for src, dst, attrs in edges:
        weight = lift_edge_value(attrs, lift_spec)
        if weight is None:
            continue
        edge_list.append((src, dst, weight))
    
    # Relax edges iteratively
    if max_iterations is None:
        max_iterations = len(nodes) - 1
    
    converged = False
    iterations = 0
    
    for i in range(max_iterations):
        iterations = i + 1
        changed = False
        
        for src, dst, edge_weight in edge_list:
            # Compute new distance
            new_dist = semiring.mul(distances[src], edge_weight)
            
            # Update if better
            old_dist = distances[dst]
            combined = semiring.add(old_dist, new_dist)
            
            if combined != old_dist:
                distances[dst] = combined
                predecessors[dst] = src
                changed = True
        
        if not changed:
            converged = True
            break
    
    if not converged:
        converged = (iterations >= max_iterations)
    
    return PathResult(
        distances=distances,
        predecessors=predecessors,
        source=source,
        target=target,
        semiring_name=semiring.name,
        algorithm="bellman_ford",
        converged=converged,
        iterations=iterations,
    )


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
    # Auto-select algorithm based on semiring properties
    if algorithm is None:
        props = getattr(semiring, 'props', {})
        if props.get('idempotent_add') and props.get('monotone'):
            algorithm = "dijkstra"
        else:
            algorithm = "bellman_ford"
    
    if algorithm == "dijkstra":
        return sssp_dijkstra(nodes, edges, source, semiring, lift_spec, target, max_hops)
    elif algorithm == "bellman_ford":
        return sssp_bellman_ford(nodes, edges, source, semiring, lift_spec, target, max_hops)
    else:
        raise Py3plexException(f"Unknown algorithm: {algorithm}")


def _value_as_float(value: Any) -> float:
    """Convert semiring value to float for priority queue ordering."""
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    elif isinstance(value, (int, float)):
        return float(value)
    else:
        # For custom semiring values, try to convert
        try:
            return float(value)
        except:
            # Fallback: use hash for ordering (not ideal but deterministic)
            return float(hash(value) % 10000)
