"""
SBM-specific metrics for community detection evaluation.

This module provides metrics specific to Stochastic Block Model (SBM) evaluations,
including log-likelihood and MDL (Minimum Description Length).
"""

from typing import Any, Dict


def sbm_log_likelihood(
    network: Any,
    partition: Dict[Any, int],
    meta: Dict[str, Any]
) -> float:
    """
    Extract SBM log-likelihood from algorithm metadata.
    
    This metric is only meaningful for SBM/DC-SBM algorithms that compute
    log-likelihood during fitting. For other algorithms, returns None.
    
    Args:
        network: Multilayer network (not used, for signature compatibility)
        partition: Community partition (not used, for signature compatibility)
        meta: Algorithm metadata dict containing 'log_likelihood' key
        
    Returns:
        Log-likelihood value (higher is better), or None if not available
        
    Notes:
        - This metric should be MAXIMIZED (higher is better)
        - Only available when algorithm is SBM or DC-SBM
        - Used by AutoCommunity for comparing SBM models
    """
    return meta.get('log_likelihood')


def sbm_mdl(
    network: Any,
    partition: Dict[Any, int],
    meta: Dict[str, Any]
) -> float:
    """
    Extract SBM MDL (Minimum Description Length) from algorithm metadata.
    
    MDL = -log_likelihood + (complexity penalty)
    
    This is essentially BIC (Bayesian Information Criterion) and represents
    a trade-off between model fit and complexity.
    
    Args:
        network: Multilayer network (not used, for signature compatibility)
        partition: Community partition (not used, for signature compatibility)
        meta: Algorithm metadata dict containing 'mdl' or 'bic' key
        
    Returns:
        MDL/BIC value (lower is better), or None if not available
        
    Notes:
        - This metric should be MINIMIZED (lower is better)
        - Only available when algorithm is SBM or DC-SBM
        - Used by AutoCommunity for model selection
        - Prefers simpler models over complex ones
    """
    return meta.get('mdl') or meta.get('bic')


def sbm_n_blocks(
    network: Any,
    partition: Dict[Any, int],
    meta: Dict[str, Any]
) -> int:
    """
    Extract the number of blocks selected by SBM model selection.
    
    Args:
        network: Multilayer network (not used)
        partition: Community partition (not used)
        meta: Algorithm metadata dict containing 'K_selected' key
        
    Returns:
        Number of blocks (communities), or None if not available
        
    Notes:
        - Useful for understanding model complexity
        - Available when SBM performs automatic model selection
    """
    return meta.get('K_selected')


# Metric registry for AutoCommunity
SBM_METRICS = {
    'sbm_log_likelihood': {
        'function': sbm_log_likelihood,
        'direction': 'maximize',
        'description': 'SBM log-likelihood (higher is better)',
        'requires': ['sbm', 'dc_sbm'],
    },
    'sbm_mdl': {
        'function': sbm_mdl,
        'direction': 'minimize',
        'description': 'SBM Minimum Description Length / BIC (lower is better)',
        'requires': ['sbm', 'dc_sbm'],
    },
    'sbm_n_blocks': {
        'function': sbm_n_blocks,
        'direction': 'none',  # Neither maximize nor minimize
        'description': 'Number of blocks selected by SBM',
        'requires': ['sbm', 'dc_sbm'],
    },
}
