"""Approximate PageRank using power iteration with explicit stopping criteria.

This module implements PageRank using the power iteration method with:
- Explicit iteration count and tolerance for early stopping
- Stable, reproducible convergence tracking
- Consistent provenance for approximation metadata

While "exact" PageRank is already iterative, this approximation mode
provides explicit control over convergence criteria and full transparency
in the provenance record.
"""

import math
from typing import Any, Dict, Optional, Tuple
import networkx as nx


def approximate_pagerank_power_iteration(
    G: nx.Graph,
    alpha: float = 0.85,
    tol: float = 1e-6,
    max_iter: int = 100,
    personalization: Optional[Dict[Any, float]] = None
) -> Tuple[Dict[Any, float], Dict[str, Any]]:
    """Compute PageRank using power iteration with explicit convergence.
    
    This implementation provides:
    - Explicit stopping criteria (tol, max_iter)
    - Convergence diagnostics in returned metadata
    - Deterministic, reproducible results
    
    Args:
        G: NetworkX graph
        alpha: Damping parameter (default: 0.85)
        tol: Convergence tolerance for L1 norm (default: 1e-6)
        max_iter: Maximum number of iterations (default: 100)
        personalization: Optional personalization vector (dict mapping nodes to values)
        
    Returns:
        Tuple of (pagerank_dict, convergence_info) where:
        - pagerank_dict: PageRank score for each node
        - convergence_info: Dict with 'iterations', 'residual_l1', 'converged', 'tol', 'max_iter'
        
    Note:
        - Time complexity: O(max_iter * m) where m is number of edges
        - Space complexity: O(n) where n is number of nodes
        - Deterministic given same input parameters
    """
    nodes = list(G.nodes())
    n = len(nodes)
    
    if n == 0:
        return {}, {"iterations": 0, "residual_l1": 0.0, "converged": True, "tol": tol, "max_iter": max_iter}
    
    # Build node index for efficient array operations
    idx = {v: i for i, v in enumerate(nodes)}
    
    # Build out-degree and adjacency structure
    out_deg = [0] * n
    nbrs = [[] for _ in range(n)]
    
    if G.is_directed():
        for u in nodes:
            ui = idx[u]
            for v in G.successors(u):
                vi = idx[v]
                nbrs[ui].append(vi)
            out_deg[ui] = len(nbrs[ui])
    else:
        for u in nodes:
            ui = idx[u]
            for v in G.neighbors(u):
                vi = idx[v]
                nbrs[ui].append(vi)
            out_deg[ui] = len(nbrs[ui])
    
    # Initialize PageRank vector
    x = [1.0 / n] * n
    
    # Handle personalization
    if personalization:
        # Normalize personalization vector
        pers_sum = sum(personalization.values())
        if pers_sum == 0:
            pers_sum = 1.0
        teleport = [(1.0 - alpha) * personalization.get(nodes[i], 0.0) / pers_sum for i in range(n)]
    else:
        # Uniform teleportation
        teleport_value = (1.0 - alpha) / n
        teleport = [teleport_value] * n
    
    # Power iteration
    for it in range(1, max_iter + 1):
        x_new = list(teleport)  # Start with teleport values
        
        # Handle dangling nodes (no outgoing edges)
        dangling_mass = alpha * sum(x[i] for i in range(n) if out_deg[i] == 0) / n
        for i in range(n):
            x_new[i] += dangling_mass
        
        # Distribute rank from each node to its neighbors
        for i in range(n):
            if out_deg[i] == 0:
                continue
            share = alpha * x[i] / out_deg[i]
            for j in nbrs[i]:
                x_new[j] += share
        
        # Compute L1 residual
        residual = sum(abs(x_new[i] - x[i]) for i in range(n))
        
        # Update current state
        x = x_new
        
        # Check convergence
        if residual < tol:
            break
    
    # Convert to dict
    pagerank = {nodes[i]: x[i] for i in range(n)}
    
    # Convergence info
    converged = (residual < tol)
    conv_info = {
        "iterations": it,
        "residual_l1": residual,
        "converged": converged,
        "tol": tol,
        "max_iter": max_iter
    }
    
    return pagerank, conv_info


def approximate_pagerank(
    G: nx.Graph,
    alpha: float = 0.85,
    tol: float = 1e-6,
    max_iter: int = 100,
    **kwargs
) -> Dict[Any, float]:
    """Compute approximate PageRank (without convergence info).
    
    This is a convenience wrapper that returns only the PageRank values
    without convergence diagnostics.
    
    Args:
        G: NetworkX graph
        alpha: Damping parameter (default: 0.85)
        tol: Convergence tolerance (default: 1e-6)
        max_iter: Maximum iterations (default: 100)
        **kwargs: Additional arguments (ignored for compatibility)
        
    Returns:
        Dict mapping each node to its approximate PageRank score
    """
    pagerank, _ = approximate_pagerank_power_iteration(G, alpha, tol, max_iter)
    return pagerank
