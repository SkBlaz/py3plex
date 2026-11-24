"""Approximate PageRank using power iteration with explicit stopping criteria.

This module implements PageRank using the power iteration method with:
- Explicit iteration count and tolerance for early stopping
- Stable, reproducible convergence tracking
- Consistent provenance for approximation metadata

While "exact" PageRank is already iterative, this approximation mode
provides explicit control over convergence criteria and full transparency
in the provenance record.
"""

from typing import Any, Dict, Optional, Tuple
import networkx as nx


def approximate_pagerank_power_iteration(
    G: nx.Graph,
    alpha: float = 0.85,
    tol: float = 1e-6,
    max_iter: int = 100,
    personalization: Optional[Dict[Any, float]] = None,
    diagnostics: bool = False,
    weight: Optional[str] = "weight",
) -> Tuple[Dict[Any, float], Optional[Dict[str, Any]]]:
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
        diagnostics: Whether to return convergence diagnostics (default: False)
        weight: Edge weight attribute, or None for unit weights
        
    Returns:
        Tuple of (pagerank_dict, convergence_info) where:
        - pagerank_dict: PageRank score for each node
        - convergence_info: Dict with 'iterations', 'residual_l1', 'converged', 'tol', 'max_iter'
                           (None if diagnostics=False)
        
    Note:
        - Time complexity: O(max_iter * m) where m is number of edges
        - Space complexity: O(n) where n is number of nodes
        - Deterministic given same input parameters
    """
    nodes = list(G.nodes())
    n = len(nodes)
    
    if n == 0:
        return {}, None
    
    # Build node index for efficient array operations
    idx = {v: i for i, v in enumerate(nodes)}
    
    # Build weighted transitions, summing parallel arcs.
    transitions = [[] for _ in nodes]
    dangling = []
    for u, neighbors in G.adjacency():
        source = idx[u]
        outgoing = []
        for v, attrs in neighbors.items():
            edges = attrs.values() if G.is_multigraph() else (attrs,)
            strength = sum(edge.get(weight, 1.0) if weight is not None else 1.0 for edge in edges)
            outgoing.append((idx[v], strength))
        total = sum(strength for _, strength in outgoing)
        if total:
            transitions[source] = [(target, strength / total) for target, strength in outgoing]
        else:
            dangling.append(source)

    x = [1.0 / n] * n
    preference = ([personalization.get(node, 0.0) for node in nodes]
                  if personalization is not None else x)
    total = sum(preference)
    if total == 0:
        raise ZeroDivisionError("Personalization has zero mass on the graph.")
    preference = [value / total for value in preference]
    if max_iter < 1:
        raise ValueError("max_iter must be positive")

    # Power iteration
    for it in range(1, max_iter + 1):
        dangling_mass = alpha * sum(x[i] for i in dangling)
        x_new = [(1.0 - alpha + dangling_mass) * value for value in preference]
        for i, outgoing in enumerate(transitions):
            for j, probability in outgoing:
                x_new[j] += alpha * x[i] * probability

        # Compute L1 residual
        residual = sum(abs(x_new[i] - x[i]) for i in range(n))
        
        # Update current state
        x = x_new
        
        # Check convergence
        if residual < tol:
            break
    
    # Convert to dict
    pagerank = {nodes[i]: x[i] for i in range(n)}
    
    # Convergence info (only if diagnostics requested)
    conv_info = None
    if diagnostics:
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
    """Compute approximate PageRank (without diagnostics).
    
    This is a convenience wrapper that returns only the PageRank values
    without convergence diagnostics, consistent with other approximate
    centrality functions.
    
    Args:
        G: NetworkX graph
        alpha: Damping parameter (default: 0.85)
        tol: Convergence tolerance (default: 1e-6)
        max_iter: Maximum iterations (default: 100)
        **kwargs: Additional arguments (ignored for compatibility)
        
    Returns:
        Dict mapping each node to its approximate PageRank score
    """
    pagerank, _ = approximate_pagerank_power_iteration(
        G, alpha, tol, max_iter, diagnostics=False
    )
    return pagerank
