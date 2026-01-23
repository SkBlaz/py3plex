"""Approximate closeness centrality using landmark-based distance sampling.

This module implements fast approximate closeness centrality by:
- Sampling a subset of landmark nodes
- Computing distances from each landmark to all nodes
- Estimating average distance for each node from landmark distances
- Handling disconnected components appropriately

The method is particularly effective for large graphs where computing
all-pairs shortest paths is prohibitively expensive.
"""

import math
import random
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx


def _single_source_shortest_path_lengths(
    G: nx.Graph,
    source: Any,
    weight: Optional[str] = None,
    reverse_for_directed: bool = False
) -> Dict[Any, float]:
    """Compute shortest path lengths from a source node.
    
    Args:
        G: NetworkX graph
        source: Source node
        weight: Edge weight attribute name (None for unweighted)
        reverse_for_directed: If True and G is directed, reverse edge directions
            (useful for computing distances TO the landmark instead of FROM it)
        
    Returns:
        Dict mapping reachable nodes to their distances from source
    """
    if reverse_for_directed and G.is_directed():
        # Create reversed graph
        G_rev = G.reverse(copy=False)
        if weight:
            return nx.single_source_dijkstra_path_length(G_rev, source, weight=weight)
        else:
            return nx.single_source_shortest_path_length(G_rev, source)
    else:
        if weight:
            return nx.single_source_dijkstra_path_length(G, source, weight=weight)
        else:
            return nx.single_source_shortest_path_length(G, source)


def _allocate_landmarks(
    components: List[Set[Any]],
    n_landmarks: int
) -> List[int]:
    """Allocate landmarks to components proportionally by size.
    
    Args:
        components: List of connected components (sets of nodes)
        n_landmarks: Total number of landmarks to allocate
        
    Returns:
        List of landmark counts for each component (at least 1 for each non-trivial component)
    """
    if not components:
        return []
    
    # Compute component sizes
    sizes = [len(c) for c in components]
    total_size = sum(sizes)
    
    if total_size == 0:
        return [0] * len(components)
    
    # Allocate proportionally, with at least 1 for non-trivial components
    allocation = []
    remaining = n_landmarks
    
    for i, size in enumerate(sizes):
        if size == 1:
            # Singleton component - no landmarks needed
            allocation.append(0)
        elif i == len(sizes) - 1:
            # Last component gets remaining landmarks
            allocation.append(max(1, remaining))
        else:
            # Allocate proportionally, at least 1
            count = max(1, int(round(n_landmarks * size / total_size)))
            count = min(count, remaining - (len(sizes) - i - 1))  # Save at least 1 for each remaining
            allocation.append(count)
            remaining -= count
    
    return allocation


def approximate_closeness_landmarks(
    G: nx.Graph,
    n_landmarks: int,
    seed: Optional[int] = None,
    weight: Optional[str] = None,
    diagnostics: bool = False
) -> Tuple[Dict[Any, float], Optional[Dict[Any, float]]]:
    """Compute approximate closeness centrality using landmark sampling.
    
    For each node, this estimates closeness by computing average distance
    to randomly sampled landmark nodes. For undirected graphs, components
    are handled separately to avoid biasing estimates.
    
    Args:
        G: NetworkX graph
        n_landmarks: Number of landmark nodes to sample
        seed: Random seed for reproducible sampling
        weight: Edge weight attribute name (None for unweighted)
        diagnostics: Whether to compute per-node standard error
        
    Returns:
        Tuple of (closeness_dict, stderr_dict) where:
        - closeness_dict: Estimated closeness for each node
        - stderr_dict: Per-node standard error (None if diagnostics=False)
        
    Note:
        - For undirected graphs, landmarks are sampled per component
        - For directed graphs, landmarks are sampled globally
        - Closeness is defined as 1 / (average distance to reachable nodes)
        - Time complexity: O(n_landmarks * (m + n log n)) for weighted graphs
    """
    rng = random.Random(seed)
    nodes = list(G.nodes())
    N = len(nodes)
    
    if N == 0:
        return {}, None
    
    # Handle component-based sampling for undirected graphs
    if not G.is_directed():
        # Get connected components
        comps = list(nx.connected_components(G))
        
        # Allocate landmarks to components
        comp_landmarks = _allocate_landmarks(comps, n_landmarks)
        
        # Sample landmarks from each component
        landmarks = []
        for comp, k in zip(comps, comp_landmarks):
            comp_nodes = list(comp)
            for _ in range(k):
                landmarks.append(comp_nodes[rng.randrange(len(comp_nodes))])
        
        # Build component membership map for later lookup
        node_to_comp = {}
        for i, comp in enumerate(comps):
            for node in comp:
                node_to_comp[node] = i
    else:
        # Directed: sample landmarks globally
        landmarks = [nodes[rng.randrange(N)] for _ in range(n_landmarks)]
        node_to_comp = None
    
    # Compute distances from each landmark
    # For directed graphs, we want distances TO landmarks, so we reverse
    dist_maps = []
    for l in landmarks:
        dist = _single_source_shortest_path_lengths(
            G, l, weight=weight, reverse_for_directed=G.is_directed()
        )
        dist_maps.append(dist)
    
    # Estimate closeness for each node
    closeness = {}
    stderr = {} if diagnostics else None
    
    for v in nodes:
        # Collect distances from v to landmarks
        if node_to_comp is not None:
            # Undirected: use only landmarks from same component
            v_comp = node_to_comp[v]
            dists = []
            for i, dist in enumerate(dist_maps):
                landmark = landmarks[i]
                l_comp = node_to_comp[landmark]
                if l_comp == v_comp and v in dist:
                    dists.append(dist[v])
        else:
            # Directed: use all landmarks
            dists = [dist[v] for dist in dist_maps if v in dist]
        
        if not dists:
            # No reachable landmarks
            closeness[v] = 0.0
            if diagnostics:
                stderr[v] = 0.0
            continue
        
        # Compute mean distance
        mean_d = sum(dists) / len(dists)
        
        # Basic closeness estimator: 1 / mean_distance
        if mean_d == 0:
            base_closeness = 0.0
        else:
            base_closeness = 1.0 / mean_d
        
        # For directed graphs, adjust by reachable fraction
        if G.is_directed():
            reachable_frac = len(dists) / float(len(landmarks)) if landmarks else 0.0
            closeness[v] = base_closeness * reachable_frac
        else:
            closeness[v] = base_closeness
        
        # Compute standard error using delta method
        if diagnostics:
            if len(dists) > 1 and mean_d > 0:
                # Sample variance of distances
                var_d = sum((d - mean_d) ** 2 for d in dists) / (len(dists) - 1)
                # Standard error of mean
                se_mean = math.sqrt(var_d / len(dists))
                # Delta method: var(1/X) ≈ (se/mean^2)^2 for small se
                stderr[v] = se_mean / (mean_d * mean_d)
            else:
                stderr[v] = 0.0
    
    # Optional normalization (consistent with NetworkX)
    # NetworkX closeness_centrality normalizes by (N-1) for simple graphs
    # We keep raw estimates for now, but could add normalization flag if needed
    
    return closeness, stderr


def approximate_closeness(
    G: nx.Graph,
    n_landmarks: int = 64,
    seed: Optional[int] = None,
    weight: Optional[str] = None,
    **kwargs
) -> Dict[Any, float]:
    """Compute approximate closeness centrality (without diagnostics).
    
    This is a convenience wrapper that returns only the closeness values
    without standard errors.
    
    Args:
        G: NetworkX graph
        n_landmarks: Number of landmark nodes to sample (default: 64)
        seed: Random seed for reproducible sampling
        weight: Edge weight attribute name (None for unweighted)
        **kwargs: Additional arguments (ignored for compatibility)
        
    Returns:
        Dict mapping each node to its approximate closeness centrality
    """
    closeness, _ = approximate_closeness_landmarks(
        G, n_landmarks, seed, weight, diagnostics=False
    )
    return closeness
