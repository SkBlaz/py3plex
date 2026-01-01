"""
Model selection for multilayer SBM.

This module provides utilities for selecting the number of blocks (K)
using various criteria.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd


def compute_bic(
    elbo: float,
    n_nodes: int,
    n_edges: int,
    n_layers: int,
    K: int,
    model: str = "sbm",
    layer_mode: str = "independent"
) -> float:
    """
    Compute Bayesian Information Criterion (BIC).
    
    BIC = -2 * log_likelihood + k * log(n)
    where k is the number of parameters.
    
    Args:
        elbo: Evidence Lower Bound (approximates log-likelihood)
        n_nodes: Number of nodes
        n_edges: Total number of edges across layers
        n_layers: Number of layers
        K: Number of blocks
        model: "sbm" or "dc_sbm"
        layer_mode: "independent" or "shared_affinity"
        
    Returns:
        BIC value (lower is better)
    """
    # Count parameters
    n_params = 0
    
    # Membership parameters: n_nodes * (K - 1)
    n_params += n_nodes * (K - 1)
    
    # Block affinity parameters
    if layer_mode == "shared_affinity":
        # Single B matrix: K * (K + 1) / 2 for undirected
        n_params += K * (K + 1) // 2
    else:
        # Per-layer B matrices
        n_params += n_layers * K * (K + 1) // 2
    
    # DC-SBM: add theta parameters
    if model == "dc_sbm":
        n_params += n_nodes
    
    # BIC = -2 * log_likelihood + k * log(n_samples)
    # Use n_edges as sample size (each edge is an observation)
    n_samples = max(n_edges, n_nodes)  # Use max to avoid log(0)
    
    bic = -2 * elbo + n_params * np.log(n_samples)
    
    return bic


def compute_icl(
    elbo: float,
    q: np.ndarray,
    n_nodes: int,
    n_edges: int,
    n_layers: int,
    K: int,
    model: str = "sbm",
    layer_mode: str = "independent"
) -> float:
    """
    Compute Integrated Classification Likelihood (ICL).
    
    ICL = BIC - entropy(q)
    
    ICL penalizes fuzzy cluster assignments, preferring clear separation.
    
    Args:
        elbo: Evidence Lower Bound
        q: Soft membership matrix (n x K)
        n_nodes: Number of nodes
        n_edges: Total number of edges
        n_layers: Number of layers
        K: Number of blocks
        model: "sbm" or "dc_sbm"
        layer_mode: Layer coupling mode
        
    Returns:
        ICL value (lower is better)
    """
    from .utils import safe_log
    
    # Compute BIC
    bic = compute_bic(elbo, n_nodes, n_edges, n_layers, K, model, layer_mode)
    
    # Compute entropy penalty
    q_safe = np.maximum(q, 1e-10)
    entropy = -np.sum(q * np.log(q_safe))
    
    # ICL = BIC - entropy
    icl = bic - entropy
    
    return icl


def select_best_model(
    results: List[Dict[str, Any]],
    criterion: str = "elbo"
) -> Tuple[int, Dict[str, Any]]:
    """
    Select best model from a list of fitted models.
    
    Args:
        results: List of result dictionaries, each containing:
            - K: Number of blocks
            - elbo: ELBO value
            - bic: BIC value (optional)
            - icl: ICL value (optional)
            - model: Fitted model object
        criterion: Selection criterion ("elbo", "bic", or "icl")
        
    Returns:
        Tuple of (best_index, best_result)
    """
    if not results:
        raise ValueError("No results to select from")
    
    if criterion == "elbo":
        # Higher ELBO is better
        scores = [r['elbo'] for r in results]
        best_idx = int(np.argmax(scores))
    elif criterion == "bic":
        # Lower BIC is better
        scores = [r.get('bic', np.inf) for r in results]
        best_idx = int(np.argmin(scores))
    elif criterion == "icl":
        # Lower ICL is better
        scores = [r.get('icl', np.inf) for r in results]
        best_idx = int(np.argmin(scores))
    else:
        raise ValueError(f"Unknown criterion: {criterion}")
    
    return best_idx, results[best_idx]


def create_selection_dataframe(
    results: List[Dict[str, Any]]
) -> pd.DataFrame:
    """
    Create a DataFrame summarizing model selection results.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        DataFrame with model comparison metrics
    """
    rows = []
    
    for result in results:
        row = {
            'K': result['K'],
            'elbo': result['elbo'],
            'n_iter': result.get('n_iter', None),
            'converged': result.get('converged', None),
        }
        
        if 'bic' in result:
            row['bic'] = result['bic']
        
        if 'icl' in result:
            row['icl'] = result['icl']
        
        if 'n_blocks_used' in result:
            row['n_blocks_used'] = result['n_blocks_used']
        
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Sort by K
    df = df.sort_values('K').reset_index(drop=True)
    
    return df


def model_selection_report(
    results: List[Dict[str, Any]],
    criterion: str = "elbo"
) -> Dict[str, Any]:
    """
    Generate a comprehensive model selection report.
    
    Args:
        results: List of result dictionaries
        criterion: Selection criterion
        
    Returns:
        Dictionary with report information
    """
    best_idx, best_result = select_best_model(results, criterion)
    df = create_selection_dataframe(results)
    
    report = {
        'best_K': best_result['K'],
        'best_index': best_idx,
        'criterion': criterion,
        'comparison_table': df,
        'best_result': best_result
    }
    
    return report
