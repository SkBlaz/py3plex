"""
Unified SBM API for community detection.

This module provides a unified interface for all SBM variants,
compatible with the AutoCommunity framework and DSL integration.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from py3plex.algorithms.sbm import (
    fit_multilayer_sbm,
    mmsbm_fit,
    SBMFittedModel,
    sbm_seed_resampling_uq
)
from py3plex.algorithms.sbm.conversions import extract_layer_adjacencies, check_node_aligned


def sbm_fit(
    network: Any,
    n_blocks: Optional[int] = None,
    algorithm: str = "dc_sbm",
    mode: str = "shared_blocks",
    degree_corrected: bool = True,
    mixed_membership: bool = False,
    B_min: int = 2,
    B_max: int = 10,
    directed: bool = False,
    init: str = "spectral",
    n_init: int = 5,
    max_iter: int = 500,
    tol: float = 1e-5,
    seed: int = 0,
    uq: bool = False,
    uq_n_samples: int = 10,
    return_model: bool = False,
    verbose: bool = False,
    **kwargs
) -> Union[Dict[Tuple[Any, Any], int], Tuple[Dict[Tuple[Any, Any], int], SBMFittedModel]]:
    """
    Unified API for SBM-family community detection.
    
    This function provides a single entry point for all SBM variants:
    - SBM (standard)
    - DC-SBM (degree-corrected)
    - MMSBM (mixed-membership)
    - Multilayer SBM with various coupling modes
    
    Args:
        network: py3plex multi_layer_network object
        n_blocks: Number of blocks (if None, selects best from [B_min, B_max])
        algorithm: "sbm" or "dc_sbm" (default: "dc_sbm")
        mode: Multilayer coupling mode:
            - "independent": separate B per layer
            - "shared_blocks" or "shared": shared memberships, separate B (default)
            - "shared_affinity": shared memberships and B
            - "coupled": shared memberships with coupling penalty
        degree_corrected: Use degree-corrected SBM (overrides algorithm)
        mixed_membership: Return soft memberships (MMSBM style)
        B_min: Minimum number of blocks for model selection (default: 2)
        B_max: Maximum number of blocks for model selection (default: 10)
        directed: Whether network is directed
        init: Initialization method ("random", "kmeans", "spectral")
        n_init: Number of random restarts
        max_iter: Maximum iterations per fit
        tol: Convergence tolerance
        seed: Random seed
        uq: Enable uncertainty quantification (default: False)
            Note: UQ is only available when mixed_membership=False
        uq_n_samples: Number of UQ samples (if uq=True)
        return_model: If True, return (partition, model), else just partition
        verbose: Print progress
        **kwargs: Additional parameters passed to fit_multilayer_sbm
        
    Returns:
        If return_model=False: partition dict {(node, layer): community_id}
        If return_model=True: (partition, SBMFittedModel)
        If mixed_membership=True and return_model=True: model.memberships_ contains soft assignments
        
    Example:
        >>> # Basic DC-SBM with fixed K
        >>> partition = sbm_fit(net, n_blocks=3, algorithm="dc_sbm")
        >>> 
        >>> # Model selection
        >>> partition = sbm_fit(net, B_min=2, B_max=8, algorithm="dc_sbm")
        >>> 
        >>> # Mixed-membership SBM
        >>> partition, model = sbm_fit(
        ...     net, n_blocks=3, mixed_membership=True, return_model=True
        ... )
        >>> soft_memberships = model.memberships_
        >>> 
        >>> # Coupled multilayer
        >>> partition = sbm_fit(net, n_blocks=3, mode="coupled")
        >>> 
        >>> # With UQ
        >>> partition, model = sbm_fit(
        ...     net, n_blocks=3, uq=True, uq_n_samples=50, return_model=True
        ... )
    """
    # Handle algorithm parameter
    if degree_corrected:
        algorithm = "dc_sbm"
    
    # Normalize mode parameter
    if mode == "shared":
        mode = "shared_blocks"
    
    # Determine if we need model selection
    if n_blocks is None:
        # Model selection
        K_list = list(range(B_min, B_max + 1))
        model, selection_info = fit_multilayer_sbm(
            network=network,
            n_blocks=K_list,
            model=algorithm,
            layer_mode=mode,
            directed=directed,
            init=init,
            n_init=n_init,
            max_iter=max_iter,
            tol=tol,
            seed=seed,
            return_posterior=True,
            verbose=verbose,
            **kwargs
        )
    else:
        # Fixed K
        if mixed_membership:
            model = mmsbm_fit(
                network=network,
                n_blocks=n_blocks,
                model=algorithm,
                layer_mode=mode,
                directed=directed,
                init=init,
                n_init=n_init,
                max_iter=max_iter,
                tol=tol,
                seed=seed,
                verbose=verbose
            )
        else:
            model = fit_multilayer_sbm(
                network=network,
                n_blocks=n_blocks,
                model=algorithm,
                layer_mode=mode,
                directed=directed,
                init=init,
                n_init=n_init,
                max_iter=max_iter,
                tol=tol,
                seed=seed,
                return_posterior=False,
                verbose=verbose,
                **kwargs
            )
    
    # UQ if requested
    if uq and not mixed_membership:
        # Extract adjacency matrices for UQ
        A_layers, layers, node_to_idx = extract_layer_adjacencies(
            network, layers=None, directed=directed
        )
        
        uq_result = sbm_seed_resampling_uq(
            A_layers=A_layers,
            K=model.K_,
            layers=layers,
            node_to_idx=node_to_idx,
            n_samples=uq_n_samples,
            master_seed=seed,
            model=algorithm,
            layer_mode=mode,
            directed=directed,
            init=init,
            max_iter=max_iter,
            tol=tol,
            verbose=verbose,
            **kwargs
        )
        
        # Attach UQ results to model
        model.uq_result_ = uq_result
        
        # Use consensus partition
        consensus_partition_array = uq_result['consensus_partition']
        partition_dict = {}
        
        # Convert to {(node, layer): community} format
        for node, idx in node_to_idx.items():
            for layer in layers:
                partition_dict[(node, layer)] = int(consensus_partition_array[idx])
    else:
        # Standard partition
        hard_partition = model.hard_membership_
        partition_dict = {}
        
        # Convert to {(node, layer): community} format
        for node, idx in model.node_to_idx_.items():
            for layer in model.layers_:
                partition_dict[(node, layer)] = int(hard_partition[idx])
    
    if return_model:
        return partition_dict, model
    else:
        return partition_dict


def sbm_multilayer_fit(
    network: Any,
    n_blocks: int = 3,
    mode: str = "shared_blocks",
    **kwargs
) -> Dict[Tuple[Any, Any], int]:
    """
    Convenience wrapper for multilayer SBM.
    
    Args:
        network: py3plex multi_layer_network object
        n_blocks: Number of blocks
        mode: "independent", "shared_blocks", "shared_affinity", or "coupled"
        **kwargs: Additional parameters passed to sbm_fit
        
    Returns:
        Partition dict {(node, layer): community_id}
    """
    return sbm_fit(
        network=network,
        n_blocks=n_blocks,
        algorithm="dc_sbm",
        mode=mode,
        **kwargs
    )


__all__ = [
    'sbm_fit',
    'sbm_multilayer_fit',
]
