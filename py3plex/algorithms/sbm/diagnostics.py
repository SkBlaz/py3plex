"""
Diagnostics and convergence checks for multilayer SBM.

This module provides tools for assessing convergence and quality
of SBM fits.
"""

from typing import List, Dict, Any
import numpy as np


def check_convergence(
    elbo_history: List[float],
    window: int = 3,
    tol: float = 1e-5
) -> bool:
    """
    Check if ELBO has converged.
    
    Args:
        elbo_history: List of ELBO values over iterations
        window: Number of recent iterations to check
        tol: Relative change tolerance
        
    Returns:
        True if converged
    """
    if len(elbo_history) < window + 1:
        return False
    
    recent = elbo_history[-window-1:]
    changes = [abs(recent[i+1] - recent[i]) / (abs(recent[i]) + 1e-10)
               for i in range(len(recent) - 1)]
    
    return all(change < tol for change in changes)


def compute_posterior_summary(
    q: np.ndarray,
    theta: np.ndarray = None
) -> Dict[str, Any]:
    """
    Compute summary statistics of posterior distributions.
    
    Args:
        q: Soft membership matrix (n x K)
        theta: Node propensities (n,) for DC-SBM
        
    Returns:
        Dictionary with summary statistics
    """
    from .utils import node_entropy, membership_confidence
    
    summary = {}
    
    # Membership statistics
    summary['mean_entropy'] = np.mean(node_entropy(q))
    summary['max_entropy'] = np.max(node_entropy(q))
    summary['mean_confidence'] = np.mean(membership_confidence(q))
    summary['min_confidence'] = np.min(membership_confidence(q))
    
    # Block sizes
    hard_labels = np.argmax(q, axis=1)
    unique, counts = np.unique(hard_labels, return_counts=True)
    summary['block_sizes'] = dict(zip(unique.tolist(), counts.tolist()))
    summary['n_blocks_used'] = len(unique)
    
    # Theta statistics (DC-SBM)
    if theta is not None:
        summary['theta_mean'] = np.mean(theta)
        summary['theta_std'] = np.std(theta)
        summary['theta_min'] = np.min(theta)
        summary['theta_max'] = np.max(theta)
    
    return summary


def assess_convergence_quality(
    elbo_history: List[float],
    converged: bool,
    max_iter: int
) -> Dict[str, Any]:
    """
    Assess quality of convergence.
    
    Args:
        elbo_history: ELBO values over iterations
        converged: Whether algorithm converged
        max_iter: Maximum iterations allowed
        
    Returns:
        Dictionary with convergence diagnostics
    """
    diagnostics = {}
    
    diagnostics['converged'] = converged
    diagnostics['n_iter'] = len(elbo_history)
    diagnostics['final_elbo'] = elbo_history[-1] if elbo_history else None
    
    if len(elbo_history) > 1:
        diagnostics['elbo_improvement'] = elbo_history[-1] - elbo_history[0]
        diagnostics['is_monotonic'] = all(
            elbo_history[i+1] >= elbo_history[i] - 1e-6
            for i in range(len(elbo_history) - 1)
        )
    else:
        diagnostics['elbo_improvement'] = 0.0
        diagnostics['is_monotonic'] = True
    
    return diagnostics


def compute_uncertainty_metrics(
    q: np.ndarray
) -> Dict[str, np.ndarray]:
    """
    Compute uncertainty metrics for node assignments.
    
    Args:
        q: Soft membership matrix (n x K)
        
    Returns:
        Dictionary with uncertainty metrics per node
    """
    from .utils import node_entropy, membership_confidence
    
    metrics = {}
    
    # Entropy: higher = more uncertain
    metrics['entropy'] = node_entropy(q)
    
    # Confidence: probability of most likely block
    metrics['confidence'] = membership_confidence(q)
    
    # Second-best gap: difference between top 2 probabilities
    q_sorted = np.sort(q, axis=1)[:, ::-1]
    if q.shape[1] >= 2:
        metrics['top2_gap'] = q_sorted[:, 0] - q_sorted[:, 1]
    else:
        # When K=1, there's no second-best, set gap to max (1.0)
        metrics['top2_gap'] = np.ones(q.shape[0])
    
    return metrics
