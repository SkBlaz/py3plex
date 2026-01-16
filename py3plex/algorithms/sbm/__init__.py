"""
Multilayer Stochastic Block Model (SBM) for py3plex.

This module provides implementations of SBM and Degree-Corrected SBM (DC-SBM)
for multiplex and multilayer networks, with variational inference, model selection,
and uncertainty quantification.

Main API:
    - fit_multilayer_sbm: Fit SBM to a multilayer network
    - mmsbm_fit: Fit Mixed-Membership SBM (soft assignments)
    - select_multilayer_sbm_model: Model selection across multiple K values
    - SBMFittedModel: Fitted model with predictions and diagnostics
    - sbm_seed_resampling_uq: UQ via seed resampling
    - align_labels_hungarian: Label alignment across runs

Example:
    >>> from py3plex.core import multinet
    >>> from py3plex.algorithms.sbm import fit_multilayer_sbm
    >>>
    >>> # Create network
    >>> net = multinet.multi_layer_network(directed=False)
    >>> net.add_edges([...])
    >>>
    >>> # Fit DC-SBM with 3 blocks
    >>> model = fit_multilayer_sbm(
    ...     net,
    ...     n_blocks=3,
    ...     model="dc_sbm",
    ...     layer_mode="shared_blocks"
    ... )
    >>>
    >>> # Get partition
    >>> partition = model.to_partition_vector()
    >>> 
    >>> # Mixed-membership SBM
    >>> model = mmsbm_fit(net, n_blocks=3)
    >>> soft_memberships = model.memberships_  # Soft assignments
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from .multilayer_sbm import SBMFittedModel, fit_single_sbm
from .conversions import extract_layer_adjacencies, check_node_aligned
from .model_selection import (
    compute_bic,
    compute_icl,
    select_best_model,
    create_selection_dataframe,
    model_selection_report
)
from .utils import sparse_edge_count
from .uq import (
    align_labels_hungarian,
    compute_node_stability,
    sbm_seed_resampling_uq,
    compute_co_assignment_matrix
)


def fit_multilayer_sbm(
    network: Any,
    n_blocks: Union[int, List[int]] = None,
    model: str = "dc_sbm",
    layer_mode: str = "independent",
    interlayer: str = "none",
    directed: bool = False,
    likelihood: str = "poisson",
    degree_prior: str = "gamma",
    block_prior: str = "dirichlet",
    affinity_prior: str = "gamma",
    init: str = "spectral",
    n_init: int = 5,
    max_iter: int = 500,
    tol: float = 1e-5,
    seed: int = 0,
    return_posterior: bool = True,
    verbose: bool = True
) -> Union[SBMFittedModel, Tuple[SBMFittedModel, Dict[str, Any]]]:
    """
    Fit Multilayer Stochastic Block Model to a network.
    
    This function fits SBM or DC-SBM to node-aligned multiplex networks.
    It supports various layer coupling modes and model selection over K.
    
    Args:
        network: py3plex multi_layer_network object (must be node-aligned)
        n_blocks: Number of blocks (int) or list for model selection
        model: "sbm" or "dc_sbm"
        layer_mode: Layer coupling mode:
            - "independent": separate B per layer
            - "shared_blocks": shared memberships, separate B
            - "shared_affinity": shared memberships and B
            - "coupled": shared memberships, separate B with coupling penalty
        interlayer: Interlayer edge handling (currently only "none" supported)
        directed: Whether network is directed
        likelihood: "bernoulli" or "poisson"
        degree_prior: Prior for degree parameters ("gamma" for DC-SBM)
        block_prior: Prior for block assignments ("dirichlet")
        affinity_prior: Prior for block affinities ("gamma")
        init: Initialization method ("random", "kmeans", "spectral")
        n_init: Number of random restarts
        max_iter: Maximum iterations per fit
        tol: Convergence tolerance
        seed: Random seed
        return_posterior: If True and n_blocks is list, return selection info
        verbose: Print progress
        
    Returns:
        If n_blocks is int: SBMFittedModel
        If n_blocks is list: (best_model, selection_info)
        
    Raises:
        ValueError: If network is not node-aligned
        ValueError: If interlayer != "none" (not yet implemented)
        
    Examples:
        >>> # Fit with fixed K
        >>> model = fit_multilayer_sbm(net, n_blocks=3, model="dc_sbm")
        >>>
        >>> # Model selection
        >>> model, info = fit_multilayer_sbm(
        ...     net,
        ...     n_blocks=[2, 3, 4, 5],
        ...     model="dc_sbm",
        ...     n_init=3
        ... )
        >>> print(info['comparison_table'])
    """
    # Validate network
    if not check_node_aligned(network):
        raise ValueError(
            "Network is not node-aligned. All layers must have the same nodes. "
            "Non-aligned multiplex networks are not yet supported."
        )
    
    if interlayer != "none":
        raise ValueError(
            f"Interlayer mode '{interlayer}' not yet supported. "
            "Currently only 'none' is implemented."
        )
    
    # Extract adjacency matrices
    A_layers, layers, node_to_idx = extract_layer_adjacencies(
        network,
        layers=None,
        directed=directed,
        weight_attr="weight"
    )
    
    n_nodes = len(node_to_idx)
    n_layers = len(layers)
    total_edges = sum(sparse_edge_count(A, directed) for A in A_layers)
    
    if verbose:
        print(f"Fitting multilayer SBM:")
        print(f"  Model: {model}")
        print(f"  Nodes: {n_nodes}")
        print(f"  Layers: {n_layers}")
        print(f"  Edges: {total_edges}")
        print(f"  Layer mode: {layer_mode}")
    
    # Single K or model selection?
    if isinstance(n_blocks, int):
        # Single K
        best_model = _fit_with_restarts(
            A_layers=A_layers,
            K=n_blocks,
            layers=layers,
            node_to_idx=node_to_idx,
            model=model,
            layer_mode=layer_mode,
            directed=directed,
            likelihood=likelihood,
            init=init,
            n_init=n_init,
            max_iter=max_iter,
            tol=tol,
            seed=seed,
            verbose=verbose
        )
        
        return best_model
    
    elif isinstance(n_blocks, (list, tuple)):
        # Model selection over multiple K
        if verbose:
            print(f"  K candidates: {n_blocks}")
        
        results = []
        
        for K in n_blocks:
            if verbose:
                print(f"\n--- Fitting K={K} ---")
            
            model_K = _fit_with_restarts(
                A_layers=A_layers,
                K=K,
                layers=layers,
                node_to_idx=node_to_idx,
                model=model,
                layer_mode=layer_mode,
                directed=directed,
                likelihood=likelihood,
                init=init,
                n_init=n_init,
                max_iter=max_iter,
                tol=tol,
                seed=seed + K,  # Different seed per K
                verbose=verbose
            )
            
            # Compute selection criteria
            final_elbo = model_K.elbo_history_[-1]
            bic = compute_bic(
                final_elbo, n_nodes, total_edges, n_layers, K, model, layer_mode
            )
            icl = compute_icl(
                final_elbo, model_K.memberships_, n_nodes, total_edges,
                n_layers, K, model, layer_mode
            )
            
            summary = model_K.get_summary()
            
            result = {
                'K': K,
                'model': model_K,
                'elbo': final_elbo,
                'bic': bic,
                'icl': icl,
                'converged': model_K.converged_,
                'n_iter': model_K.n_iter_,
                'n_blocks_used': summary['n_blocks_used']
            }
            
            results.append(result)
            
            if verbose:
                print(f"  ELBO: {final_elbo:.4f}, BIC: {bic:.4f}, ICL: {icl:.4f}")
        
        # Select best model
        selection_info = model_selection_report(results, criterion='elbo')
        best_model = selection_info['best_result']['model']
        
        if verbose:
            print(f"\n=== Best model: K={selection_info['best_K']} ===")
        
        if return_posterior:
            return best_model, selection_info
        else:
            return best_model
    
    else:
        raise ValueError(
            f"n_blocks must be int or list, got {type(n_blocks)}"
        )


def _fit_with_restarts(
    A_layers: List,
    K: int,
    layers: List[str],
    node_to_idx: Dict[Any, int],
    model: str,
    layer_mode: str,
    directed: bool,
    likelihood: str,
    init: str,
    n_init: int,
    max_iter: int,
    tol: float,
    seed: int,
    verbose: bool
) -> SBMFittedModel:
    """
    Fit SBM with multiple random restarts and keep best.
    
    Args:
        (see fit_multilayer_sbm)
        
    Returns:
        Best fitted model (highest ELBO)
    """
    best_model = None
    best_elbo = -np.inf
    
    for i in range(n_init):
        if verbose and n_init > 1:
            print(f"  Restart {i+1}/{n_init}")
        
        model_i = fit_single_sbm(
            A_layers=A_layers,
            K=K,
            layers=layers,
            node_to_idx=node_to_idx,
            model=model,
            layer_mode=layer_mode,
            directed=directed,
            likelihood=likelihood,
            init=init,
            seed=seed + i,
            max_iter=max_iter,
            tol=tol,
            verbose=verbose and n_init == 1
        )
        
        final_elbo = model_i.elbo_history_[-1]
        
        if final_elbo > best_elbo:
            best_elbo = final_elbo
            best_model = model_i
            
            if verbose and n_init > 1:
                print(f"    ELBO: {final_elbo:.4f} (best so far)")
    
    return best_model


def select_multilayer_sbm_model(
    network: Any,
    K_list: List[int],
    criterion: str = "elbo",
    **fit_kwargs
) -> Tuple[SBMFittedModel, Dict[str, Any]]:
    """
    Select best SBM model from a list of K values.
    
    This is a convenience wrapper around fit_multilayer_sbm for model selection.
    
    Args:
        network: py3plex multi_layer_network
        K_list: List of K values to try
        criterion: Selection criterion ("elbo", "bic", "icl")
        **fit_kwargs: Additional arguments to fit_multilayer_sbm
        
    Returns:
        Tuple of (best_model, selection_info)
        
    Example:
        >>> model, info = select_multilayer_sbm_model(
        ...     net,
        ...     K_list=[2, 3, 4, 5],
        ...     model="dc_sbm",
        ...     criterion="bic"
        ... )
    """
    # Force return_posterior=True
    fit_kwargs['return_posterior'] = True
    fit_kwargs['n_blocks'] = K_list
    
    best_model, selection_info = fit_multilayer_sbm(network, **fit_kwargs)
    
    # Re-select with specified criterion if different from default
    if criterion != "elbo":
        from .model_selection import select_best_model
        
        results = []
        for row_idx, row in selection_info['comparison_table'].iterrows():
            K = row['K']
            # Find corresponding result
            for r in selection_info['best_result']:
                if isinstance(r, dict) and r.get('K') == K:
                    results.append(r)
                    break
        
        if results:
            best_idx, best_result = select_best_model(results, criterion)
            best_model = best_result['model']
            selection_info['best_K'] = best_result['K']
            selection_info['criterion'] = criterion
    
    return best_model, selection_info


def mmsbm_fit(
    network: Any,
    n_blocks: int,
    model: str = "dc_sbm",
    layer_mode: str = "shared_blocks",
    directed: bool = False,
    init: str = "spectral",
    n_init: int = 5,
    max_iter: int = 500,
    tol: float = 1e-5,
    seed: int = 0,
    verbose: bool = True
) -> SBMFittedModel:
    """
    Fit Mixed-Membership Stochastic Block Model (MMSBM).
    
    This is a wrapper around fit_multilayer_sbm that emphasizes the
    soft membership interpretation. The returned model contains soft
    membership probabilities in model.memberships_ (n_nodes x K).
    
    MMSBM allows nodes to belong to multiple communities with different
    probabilities, unlike hard clustering approaches.
    
    Args:
        network: py3plex multi_layer_network object (must be node-aligned)
        n_blocks: Number of blocks (int)
        model: "sbm" or "dc_sbm" (default: "dc_sbm")
        layer_mode: Layer coupling mode (default: "shared_blocks")
        directed: Whether network is directed
        init: Initialization method ("random", "kmeans", "spectral")
        n_init: Number of random restarts
        max_iter: Maximum iterations per fit
        tol: Convergence tolerance
        seed: Random seed
        verbose: Print progress
        
    Returns:
        SBMFittedModel with soft memberships in .memberships_ attribute
        
    Example:
        >>> # Fit MMSBM
        >>> model = mmsbm_fit(net, n_blocks=3, model="dc_sbm")
        >>> 
        >>> # Access soft memberships
        >>> soft_memberships = model.memberships_  # (n_nodes x K)
        >>> print(soft_memberships[0])  # Node 0's membership probabilities
        >>> 
        >>> # Hard partition (for compatibility)
        >>> partition = model.to_partition_vector()
    """
    # Call fit_multilayer_sbm with single K
    model = fit_multilayer_sbm(
        network=network,
        n_blocks=n_blocks,
        model=model,
        layer_mode=layer_mode,
        interlayer="none",
        directed=directed,
        init=init,
        n_init=n_init,
        max_iter=max_iter,
        tol=tol,
        seed=seed,
        return_posterior=False,
        verbose=verbose
    )
    
    return model


__all__ = [
    'fit_multilayer_sbm',
    'mmsbm_fit',
    'select_multilayer_sbm_model',
    'SBMFittedModel',
    'compute_bic',
    'compute_icl',
    'align_labels_hungarian',
    'compute_node_stability',
    'sbm_seed_resampling_uq',
    'compute_co_assignment_matrix',
]
