"""Approximate betweenness centrality using sampling-based Brandes algorithm.

This module implements fast approximate betweenness centrality using
the sampling approach:
- Sample a subset of source nodes
- Run single-source shortest path (SSSP) from each sampled source
- Accumulate dependencies and scale to estimate full betweenness
- Optional per-node standard error when diagnostics=True

Reference:
    Brandes, U., & Pich, C. (2007). Centrality Estimation in Large Networks.
    International Journal of Bifurcation and Chaos, 17(7), 2303-2318.
"""

import math
import random
from collections import deque
from typing import Any, Dict, List, Optional, Tuple
import networkx as nx


def _brandes_sssp_unweighted(
    G: nx.Graph, source: Any
) -> Tuple[List[Any], Dict[Any, List[Any]], Dict[Any, float], Dict[Any, int]]:
    """Single-source shortest path for unweighted graph (BFS).
    
    Args:
        G: NetworkX graph
        source: Source node
        
    Returns:
        Tuple of (S, P, sigma, dist) where:
        - S: List of nodes in order of non-decreasing distance from source
        - P: Dict mapping each node to its predecessors on shortest paths
        - sigma: Dict mapping each node to number of shortest paths from source
        - dist: Dict mapping each node to distance from source (-1 if unreachable)
    """
    S = []
    P = {v: [] for v in G}
    sigma = dict.fromkeys(G, 0.0)
    sigma[source] = 1.0
    dist = dict.fromkeys(G, -1)
    dist[source] = 0
    Q = deque([source])

    while Q:
        v = Q.popleft()
        S.append(v)
        for w in G.neighbors(v):
            # First time we see w?
            if dist[w] < 0:
                dist[w] = dist[v] + 1
                Q.append(w)
            # Shortest path to w via v?
            if dist[w] == dist[v] + 1:
                sigma[w] += sigma[v]
                P[w].append(v)
    
    return S, P, sigma, dist


def _brandes_sssp_weighted(
    G: nx.Graph, source: Any, weight: str = "weight"
) -> Tuple[List[Any], Dict[Any, List[Any]], Dict[Any, float], Dict[Any, float]]:
    """Single-source shortest path for weighted graph (Dijkstra).
    
    Args:
        G: NetworkX graph
        source: Source node
        weight: Edge weight attribute name
        
    Returns:
        Tuple of (S, P, sigma, dist) where:
        - S: List of nodes in order of non-decreasing distance from source
        - P: Dict mapping each node to its predecessors on shortest paths
        - sigma: Dict mapping each node to number of shortest paths from source
        - dist: Dict mapping each node to distance from source (inf if unreachable)
    """
    import heapq
    
    S = []
    P = {v: [] for v in G}
    sigma = dict.fromkeys(G, 0.0)
    sigma[source] = 1.0
    dist = {v: float('inf') for v in G}
    dist[source] = 0.0
    seen = {source: 0.0}
    # Priority queue: (distance, node)
    Q = [(0.0, source)]
    
    while Q:
        (dist_v, v) = heapq.heappop(Q)
        if dist_v > seen.get(v, float('inf')):
            continue  # Already processed with shorter distance
        S.append(v)
        
        for w in G.neighbors(v):
            # Get edge weight
            vw_dist = dist[v] + G[v][w].get(weight, 1.0)
            if vw_dist < dist[w]:
                dist[w] = vw_dist
                seen[w] = vw_dist
                heapq.heappush(Q, (vw_dist, w))
                sigma[w] = 0.0
                P[w] = []
            if vw_dist == dist[w]:
                sigma[w] += sigma[v]
                P[w].append(v)
    
    return S, P, sigma, dist


def _brandes_dependency_accumulation(
    S: List[Any],
    P: Dict[Any, List[Any]],
    sigma: Dict[Any, float],
    source: Any
) -> Dict[Any, float]:
    """Accumulate dependencies from a single source.
    
    Args:
        S: Nodes in order of non-decreasing distance from source
        P: Predecessors on shortest paths
        sigma: Number of shortest paths from source to each node
        source: Source node
        
    Returns:
        Dict mapping each node to its dependency from this source
    """
    delta = dict.fromkeys(S, 0.0)
    contrib = dict.fromkeys(S, 0.0)
    
    # Process nodes in reverse order (increasing distance)
    while S:
        w = S.pop()
        for v in P[w]:
            if sigma[w] > 0:
                delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
        if w != source:
            contrib[w] = delta[w]
    
    return contrib


def approximate_betweenness_sampling(
    G: nx.Graph,
    n_samples: int,
    seed: Optional[int] = None,
    normalized: bool = True,
    weight: Optional[str] = None,
    diagnostics: bool = False
) -> Tuple[Dict[Any, float], Optional[Dict[Any, float]]]:
    """Compute approximate betweenness centrality using sampling.
    
    This is an unbiased estimator that samples source nodes uniformly
    and scales the contributions to estimate the full betweenness.
    
    Args:
        G: NetworkX graph
        n_samples: Number of source nodes to sample (with replacement)
        seed: Random seed for reproducible sampling
        normalized: Whether to normalize values
        weight: Edge weight attribute name (None for unweighted)
        diagnostics: Whether to compute per-node standard error
        
    Returns:
        Tuple of (betweenness_dict, stderr_dict) where:
        - betweenness_dict: Estimated betweenness for each node
        - stderr_dict: Per-node standard error (None if diagnostics=False)
        
    Note:
        - Time complexity: O(n_samples * (m + n log n)) for weighted graphs
        - Space complexity: O(n + m)
        - Deterministic when seed is set
    """
    rng = random.Random(seed)
    nodes = list(G.nodes())
    N = len(nodes)
    
    if N == 0:
        return {}, None
    
    # Sample sources with replacement
    sources = [nodes[rng.randrange(N)] for _ in range(n_samples)]
    
    # Accumulate sum and sum of squares for stderr
    sum_c = dict.fromkeys(nodes, 0.0)
    sumsq_c = dict.fromkeys(nodes, 0.0) if diagnostics else None
    
    # Choose SSSP function based on weights
    if weight is None:
        sssp_fn = _brandes_sssp_unweighted
    else:
        sssp_fn = lambda g, s: _brandes_sssp_weighted(g, s, weight)
    
    # Accumulate contributions from sampled sources
    for s in sources:
        S, P, sigma, dist = sssp_fn(G, s)
        contrib = _brandes_dependency_accumulation(S, P, sigma, s)
        
        for v, x in contrib.items():
            sum_c[v] += x
            if diagnostics:
                sumsq_c[v] += x * x
    
    # Scale to estimate sum over all sources
    # Estimator: (N-1) / n_samples * sum_over_samples
    # This is unbiased when sampling with replacement
    scale = (N - 1) / float(n_samples)
    betw = {v: scale * sum_c[v] for v in nodes}
    
    # Compute standard error if requested
    stderr = None
    if diagnostics:
        stderr = {}
        for v in nodes:
            mean = sum_c[v] / n_samples
            # Sample variance: E[X^2] - E[X]^2
            var = max(0.0, (sumsq_c[v] / n_samples) - mean * mean)
            # Standard error of scaled mean: scale * sqrt(var / n_samples)
            stderr[v] = scale * math.sqrt(var / n_samples) if var > 0 else 0.0
    
    # Apply normalization and undirected correction
    # For undirected graphs, betweenness counts each path twice
    if not G.is_directed():
        betw = {v: val / 2.0 for v, val in betw.items()}
        if stderr:
            stderr = {v: val / 2.0 for v, val in stderr.items()}
    
    # Normalize if requested
    if normalized:
        if N > 2:
            norm_factor = 1.0 / ((N - 1) * (N - 2))
            if not G.is_directed():
                norm_factor *= 2.0
            betw = {v: val * norm_factor for v, val in betw.items()}
            if stderr:
                stderr = {v: val * norm_factor for v, val in stderr.items()}
    
    return betw, stderr


def approximate_betweenness(
    G: nx.Graph,
    n_samples: int = 512,
    seed: Optional[int] = None,
    normalized: bool = True,
    weight: Optional[str] = None,
    **kwargs
) -> Dict[Any, float]:
    """Compute approximate betweenness centrality (without diagnostics).
    
    This is a convenience wrapper that returns only the betweenness values
    without standard errors.
    
    Args:
        G: NetworkX graph
        n_samples: Number of source nodes to sample (default: 512)
        seed: Random seed for reproducible sampling
        normalized: Whether to normalize values (default: True)
        weight: Edge weight attribute name (None for unweighted)
        **kwargs: Additional arguments (ignored for compatibility)
        
    Returns:
        Dict mapping each node to its approximate betweenness centrality
    """
    betw, _ = approximate_betweenness_sampling(
        G, n_samples, seed, normalized, weight, diagnostics=False
    )
    return betw
