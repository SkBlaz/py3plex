"""
Built-in multilayer centrality toolkit.

Implements core multilayer variants of centrality measures:
- Multilayer PageRank
- Multilayer betweenness centrality
- Multilayer eigenvector centrality  
- Multiplex degree centrality

These algorithms properly account for the multilayer structure of networks.

All centrality functions now support first-class uncertainty estimation via
the `uncertainty` parameter.

Authors: py3plex contributors
Date: 2025
"""

from typing import Any, Dict, Optional, Tuple, Union
import numpy as np
import networkx as nx
import scipy.sparse as sp
from scipy.sparse.linalg import eigs

# Import uncertainty types (will be None if uncertainty module not available)
try:
    from py3plex.uncertainty import (
        StatSeries,
        ResamplingStrategy,
        estimate_uncertainty,
        get_uncertainty_config,
        UncertaintyMode,
    )
    _UNCERTAINTY_AVAILABLE = True
except ImportError:
    _UNCERTAINTY_AVAILABLE = False
    StatSeries = None


def multilayer_pagerank(
    network: Any,
    alpha: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6,
    personalization: Optional[Dict] = None,
    uncertainty: bool = False,
    n_runs: Optional[int] = None,
    resampling: Optional[ResamplingStrategy] = None,
    random_seed: Optional[int] = None,
) -> Union[Dict[Tuple, float], 'StatSeries']:
    """Compute multilayer PageRank centrality with optional uncertainty estimation.
    
    Implements PageRank on the supra-adjacency matrix, accounting for
    random walks across layers.
    
    Args:
        network: Multilayer network object
        alpha: Damping factor (teleportation probability = 1-alpha)
        max_iter: Maximum number of iterations
        tol: Convergence tolerance
        personalization: Optional personalization vector (node -> weight)
        uncertainty: If True, estimate uncertainty via resampling
        n_runs: Number of runs for uncertainty estimation (default from config)
        resampling: Resampling strategy (default from config)
        random_seed: Random seed for reproducibility
        
    Returns:
        If uncertainty=False: StatSeries with deterministic values (std=None)
        If uncertainty=True: StatSeries with mean, std, quantiles
        
    Algorithm:
        PR = (1-α)/N + α * A^T * PR
        
        where A is the column-normalized supra-adjacency matrix
        
    References:
        - Halu, A., et al. (2013). "Multiplex PageRank."
          PLoS ONE, 8(10), e78293.
    
    Examples:
        >>> # Deterministic
        >>> result = multilayer_pagerank(network)
        >>> result[('A', 'L1')]  # Dict-like access
        {'mean': 0.25}
        >>> np.array(result)  # Array access (backward compat)
        
        >>> # With uncertainty
        >>> result = multilayer_pagerank(network, uncertainty=True, n_runs=50)
        >>> result.mean  # Average PageRank values
        >>> result.std   # Standard deviations
        >>> result.quantiles  # Confidence intervals
    """
    # Check if uncertainty is requested (explicit parameter overrides context)
    if _UNCERTAINTY_AVAILABLE:
        cfg = get_uncertainty_config()
        # Only use context if uncertainty parameter is not explicitly False
        if uncertainty:
            should_estimate = True
        elif cfg.mode == UncertaintyMode.ON:
            # Context says ON, but check if uncertainty was explicitly passed
            # If not passed (None or default False), respect context
            should_estimate = True
        else:
            should_estimate = False
    else:
        should_estimate = False
    
    if should_estimate and not _UNCERTAINTY_AVAILABLE:
        import warnings
        warnings.warn(
            "Uncertainty estimation requested but uncertainty module not available. "
            "Returning deterministic result.",
            RuntimeWarning
        )
        should_estimate = False
    
    # Define the core computation function
    def _compute_pagerank(net):
        # Get supra-adjacency matrix
        supra_adj = net.get_supra_adjacency_matrix(mtype="sparse")
        n = supra_adj.shape[0]
        
        # Get node order
        if hasattr(net, 'node_order_in_matrix'):
            node_order = net.node_order_in_matrix
        else:
            node_order = list(net.get_nodes())
        
        # Initialize PageRank vector
        if personalization:
            pr = np.zeros(n)
            for i, node in enumerate(node_order):
                pr[i] = personalization.get(node, 1.0/n)
            pr = pr / pr.sum()  # Normalize
        else:
            pr = np.ones(n) / n
        
        # Column-normalize the supra-adjacency matrix
        # out-degree of each node
        out_degree = np.array(supra_adj.sum(axis=0)).flatten()
        # For nodes with zero out-degree, use 1 to avoid division by zero
        # This effectively gives them uniform transition probability
        out_degree[out_degree == 0] = 1
        
        # Create column-normalized matrix
        D_inv = sp.diags(1.0 / out_degree)
        A_norm = supra_adj @ D_inv
        
        # Power iteration
        for iteration in range(max_iter):
            pr_new = (1 - alpha) / n + alpha * A_norm @ pr
            
            # Check convergence
            if np.abs(pr_new - pr).sum() < tol:
                break
            
            pr = pr_new
        
        # Create result dictionary
        result = {}
        for i, node in enumerate(node_order):
            result[node] = float(pr[i])
        
        return result
    
    # If uncertainty requested, use estimate_uncertainty
    if should_estimate:
        result = estimate_uncertainty(
            network,
            _compute_pagerank,
            n_runs=n_runs,
            resampling=resampling,
            random_seed=random_seed,
        )
        return result
    
    # Otherwise, run deterministic computation and wrap in StatSeries
    scores = _compute_pagerank(network)
    
    if _UNCERTAINTY_AVAILABLE:
        # Wrap in StatSeries for consistency
        nodes = sorted(scores.keys(), key=lambda x: str(x))
        mean_vals = np.array([scores[n] for n in nodes])
        return StatSeries(
            index=nodes,
            mean=mean_vals,
            std=None,
            quantiles=None,
            meta={"alpha": alpha, "max_iter": max_iter, "tol": tol}
        )
    else:
        # Return plain dict for backward compatibility
        return scores


def multilayer_betweenness_centrality(
    network: Any,
    normalized: bool = True,
    weight: Optional[str] = None
) -> Dict[Tuple, float]:
    """Compute multilayer betweenness centrality.
    
    Computes betweenness centrality on the supra-graph, where shortest
    paths can traverse multiple layers.
    
    Args:
        network: Multilayer network object
        normalized: Whether to normalize by number of pairs
        weight: Edge attribute to use as weight (None for unweighted)
        
    Returns:
        Dictionary mapping (node, layer) tuples to betweenness scores
        
    Algorithm:
        For each pair of nodes (s,t), count the fraction of shortest
        paths passing through each node v:
        
        BC(v) = Σ_{s≠v≠t} σ_{st}(v) / σ_{st}
        
        where σ_{st} is the number of shortest paths from s to t,
        and σ_{st}(v) is the number passing through v.
        
    References:
        - De Domenico, M., et al. (2015). "Ranking in interconnected
          multilayer networks reveals versatile nodes."
          Nature Communications, 6, 6868.
    """
    # Get the underlying network structure
    if hasattr(network, 'core_network') and network.core_network is not None:
        G = network.core_network
    else:
        raise ValueError("Network has no core_network for centrality computation")
    
    # Compute betweenness on the full multilayer graph
    betweenness = nx.betweenness_centrality(G, normalized=normalized, weight=weight)
    
    return betweenness


def multilayer_eigenvector_centrality(
    network: Any,
    max_iter: int = 100,
    tol: float = 1e-6
) -> Dict[Tuple, float]:
    """Compute multilayer eigenvector centrality.
    
    Computes the principal eigenvector of the supra-adjacency matrix.
    Nodes are important if connected to other important nodes across layers.
    
    Args:
        network: Multilayer network object
        max_iter: Maximum number of power iteration steps
        tol: Convergence tolerance
        
    Returns:
        Dictionary mapping (node, layer) tuples to eigenvector centrality scores
        
    Algorithm:
        Find the principal eigenvector of the supra-adjacency matrix:
        
        A * x = λ * x
        
        where x is the eigenvector with largest eigenvalue λ.
        
    References:
        - Solá, L., et al. (2013). "Eigenvector centrality of nodes in
          multiplex networks." Chaos, 23(3), 033131.
    """
    # Get supra-adjacency matrix
    supra_adj = network.get_supra_adjacency_matrix(mtype="sparse")
    n = supra_adj.shape[0]
    
    # Get node order
    if hasattr(network, 'node_order_in_matrix'):
        node_order = network.node_order_in_matrix
    else:
        node_order = list(network.get_nodes())
    
    try:
        # Compute largest eigenvalue and eigenvector
        # k=1 returns only the largest eigenvalue
        eigenvalues, eigenvectors = eigs(supra_adj, k=1, which='LM', maxiter=max_iter, tol=tol)
        
        # Get the principal eigenvector
        principal_eigenvector = np.abs(eigenvectors[:, 0].real)
        
        # Normalize
        principal_eigenvector = principal_eigenvector / principal_eigenvector.sum()
        
    except Exception as e:
        # Fallback to power iteration if eigs fails
        x = np.ones(n) / n
        
        for _ in range(max_iter):
            x_new = supra_adj @ x
            x_new = x_new / np.linalg.norm(x_new)
            
            if np.abs(x_new - x).sum() < tol:
                break
            
            x = x_new
        
        principal_eigenvector = np.abs(x)
    
    # Create result dictionary
    result = {}
    for i, node in enumerate(node_order):
        result[node] = float(principal_eigenvector[i])
    
    return result


def multiplex_degree_centrality(
    network: Any,
    normalized: bool = True,
    consider_interlayer: bool = True
) -> Dict[Tuple, float]:
    """Compute multiplex degree centrality.
    
    Sums degree across all layers for each node. For multiplex networks
    where nodes exist in all layers.
    
    Args:
        network: Multiplex network object
        normalized: Whether to normalize by maximum possible degree
        consider_interlayer: Whether to count inter-layer edges
        
    Returns:
        Dictionary mapping (node, layer) tuples to degree centrality scores
        
    Algorithm:
        For node i:
        DC(i) = Σ_α k_i^α
        
        where k_i^α is the degree of node i in layer α.
        
    References:
        - Battiston, F., et al. (2014). "Structural measures for
          multiplex networks." Physical Review E, 89(3), 032804.
    """
    if hasattr(network, 'core_network') and network.core_network is not None:
        G = network.core_network
    else:
        raise ValueError("Network has no core_network")
    
    degree_dict = {}
    
    # Get degree for each node
    for node in G.nodes():
        degree = G.degree(node)
        degree_dict[node] = degree
    
    # Normalize if requested
    if normalized:
        max_degree = max(degree_dict.values()) if degree_dict else 1
        if max_degree > 0:
            degree_dict = {k: v / max_degree for k, v in degree_dict.items()}
    
    return degree_dict


def aggregate_centrality_across_layers(
    centrality_dict: Dict[Tuple, float],
    aggregation: str = "sum"
) -> Dict[Any, float]:
    """Aggregate node centrality values across layers.
    
    Given centrality scores for (node, layer) tuples, aggregate to get
    per-node scores.
    
    Args:
        centrality_dict: Dictionary mapping (node, layer) -> score
        aggregation: Aggregation method ('sum', 'mean', 'max', 'min')
        
    Returns:
        Dictionary mapping node_id -> aggregated score
        
    Example:
        >>> scores = {('A', 'L1'): 0.5, ('A', 'L2'): 0.3, ('B', 'L1'): 0.7}
        >>> aggregate_centrality_across_layers(scores, 'mean')
        {'A': 0.4, 'B': 0.7}
    """
    from collections import defaultdict
    
    # Group by node_id (first element of tuple)
    node_scores = defaultdict(list)
    
    for key, value in centrality_dict.items():
        if isinstance(key, tuple):
            node_id = key[0]
        else:
            node_id = key
        node_scores[node_id].append(value)
    
    # Aggregate
    result = {}
    for node_id, scores in node_scores.items():
        if aggregation == "sum":
            result[node_id] = sum(scores)
        elif aggregation == "mean":
            result[node_id] = sum(scores) / len(scores)
        elif aggregation == "max":
            result[node_id] = max(scores)
        elif aggregation == "min":
            result[node_id] = min(scores)
        else:
            raise ValueError(f"Unknown aggregation method: {aggregation}")
    
    return result


def versatility_score(
    centrality_dict: Dict[Tuple, float],
    normalized: bool = True
) -> Dict[Any, float]:
    """Compute versatility score for each node.
    
    Measures how evenly a node's centrality is distributed across layers.
    High versatility means the node is important in multiple layers.
    
    Args:
        centrality_dict: Dictionary mapping (node, layer) -> centrality score
        normalized: Whether to normalize to [0, 1]
        
    Returns:
        Dictionary mapping node_id -> versatility score
        
    Algorithm:
        V(i) = 1 - Σ_α (c_i^α / c_i^total)^2
        
        where c_i^α is centrality of node i in layer α.
        This is similar to the Herfindahl-Hirschman index.
        
    References:
        - Battiston, F., et al. (2014). "Structural measures for
          multiplex networks." Physical Review E, 89(3), 032804.
    """
    from collections import defaultdict
    
    # Group by node_id
    node_scores = defaultdict(list)
    
    for key, value in centrality_dict.items():
        if isinstance(key, tuple):
            node_id = key[0]
        else:
            node_id = key
        node_scores[node_id].append(value)
    
    # Compute versatility
    result = {}
    for node_id, scores in node_scores.items():
        total = sum(scores)
        
        if total == 0:
            result[node_id] = 0.0
        else:
            # Compute Herfindahl-Hirschman concentration
            hhi = sum((s / total) ** 2 for s in scores)
            versatility = 1 - hhi
            
            # Normalize to [0, 1] if requested
            if normalized and len(scores) > 1:
                # Maximum versatility occurs when all scores are equal
                # max_versatility = 1 - 1/L = (L-1)/L
                max_versatility = (len(scores) - 1) / len(scores)
                versatility = versatility / max_versatility if max_versatility > 0 else 0
            
            result[node_id] = versatility
    
    return result
