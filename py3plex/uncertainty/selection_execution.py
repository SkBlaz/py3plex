"""Execution engine for SelectionUQ.

This module provides the main execution function that runs a selection query
multiple times under perturbation/resampling to compute uncertainty.
"""

import copy
import logging
from typing import Any, Callable, Dict, List, Optional

from .selection_types import SelectionOutput
from .selection_reducers import (
    InclusionReducer,
    SizeReducer,
    StabilityReducer,
    RankReducer,
    TopKOverlapReducer,
    GroupedReducer,
)
from .selection_uq import SelectionUQ
from .noise_models import NoiseModel


logger = logging.getLogger(__name__)


def execute_selection_uq(
    base_callable: Callable[[Any, Dict], SelectionOutput],
    network: Any,
    params: Optional[Dict] = None,
    method: str = "perturbation",
    n_samples: int = 50,
    seed: Optional[int] = None,
    noise_model: Optional[NoiseModel] = None,
    ci: float = 0.95,
    consensus_threshold: float = 0.5,
    borderline_epsilon: float = 0.1,
    store_mode: str = "sketch",
    max_items_tracked: Optional[int] = None,
    grouped: bool = False,
    **kwargs,
) -> SelectionUQ:
    """Execute a selection query with uncertainty quantification.
    
    Parameters
    ----------
    base_callable : callable
        Function that takes (network, params) and returns SelectionOutput
    network : multi_layer_network
        Input network
    params : dict, optional
        Parameters for base_callable
    method : str
        UQ method: "perturbation", "seed", "bootstrap", "jackknife"
    n_samples : int
        Number of samples to generate
    seed : int, optional
        Random seed for reproducibility
    noise_model : NoiseModel, optional
        Noise model for perturbation method
    ci : float
        Confidence interval level (e.g., 0.95)
    consensus_threshold : float
        Threshold for consensus selection (default: 0.5)
    borderline_epsilon : float
        Epsilon for borderline detection (default: 0.1)
    store_mode : str
        Storage mode: "none", "sketch", "samples"
    max_items_tracked : int, optional
        Maximum number of items to track (memory cap)
    grouped : bool
        Whether query has grouping (per_layer/per_layer_pair)
    **kwargs
        Additional method-specific parameters
        
    Returns
    -------
    SelectionUQ or dict
        If grouped=False: SelectionUQ instance
        If grouped=True: dict mapping group_key -> SelectionUQ
        
    Examples
    --------
    >>> from py3plex.uncertainty.noise_models import EdgeDrop
    >>> from py3plex.uncertainty.selection_execution import execute_selection_uq
    >>> 
    >>> def my_query(net, params):
    ...     # Run query and return SelectionOutput
    ...     return SelectionOutput(items=['a', 'b'], target='nodes')
    >>> 
    >>> uq = execute_selection_uq(
    ...     base_callable=my_query,
    ...     network=net,
    ...     method="perturbation",
    ...     noise_model=EdgeDrop(p=0.05),
    ...     n_samples=100,
    ...     seed=42
    ... )
    """
    import random
    import numpy as np
    
    params = params or {}
    
    # Set random seed for reproducibility
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
    
    # Determine if we need to track ranks
    store_samples = (store_mode == "samples")
    
    # Initialize reducers
    if grouped:
        # Use grouped reducers
        inclusion_reducer = GroupedReducer(InclusionReducer)
        size_reducer = GroupedReducer(SizeReducer, {"store_samples": store_samples})
        stability_reducer = GroupedReducer(
            StabilityReducer,
            {"consensus_threshold": consensus_threshold, "store_samples": store_samples}
        )
        rank_reducer = GroupedReducer(
            RankReducer,
            {"store_samples": store_samples}
        )
        topk_overlap_reducer = GroupedReducer(
            TopKOverlapReducer,
            {"store_samples": store_samples}
        )
    else:
        # Use regular reducers
        inclusion_reducer = InclusionReducer()
        size_reducer = SizeReducer(store_samples=store_samples)
        stability_reducer = StabilityReducer(
            consensus_threshold=consensus_threshold,
            store_samples=store_samples
        )
        rank_reducer = RankReducer(store_samples=store_samples)
        topk_overlap_reducer = TopKOverlapReducer(store_samples=store_samples)
    
    # Track first sample to detect if ranking is present
    has_ranks = False
    has_topk = False
    target = "nodes"
    k = None
    
    # Run samples
    logger.info(f"Running {n_samples} samples with method={method}")
    
    for i in range(n_samples):
        # Apply noise/perturbation
        if method == "perturbation" and noise_model is not None:
            sample_seed = (seed + i) if seed is not None else None
            perturbed_net = noise_model.apply(network, seed=sample_seed)
        elif method == "seed":
            # Seed-based: just vary random seed in callable
            perturbed_net = network
            if seed is not None:
                params_copy = params.copy()
                params_copy["_uq_seed"] = seed + i
            else:
                params_copy = params
        elif method == "bootstrap":
            # TODO: Implement bootstrap network resampling
            raise NotImplementedError("Bootstrap method not yet implemented for selections")
        elif method == "jackknife":
            # TODO: Implement jackknife resampling
            raise NotImplementedError("Jackknife method not yet implemented for selections")
        else:
            perturbed_net = network
            params_copy = params
        
        # Execute query
        try:
            if method == "seed":
                selection = base_callable(perturbed_net, params_copy)
            else:
                selection = base_callable(perturbed_net, params)
        except Exception as e:
            logger.warning(f"Sample {i} failed: {e}")
            continue
        
        # Detect characteristics from first sample
        if i == 0:
            target = selection.target
            k = selection.k
            has_ranks = (selection.ranks is not None)
            has_topk = (selection.k is not None)
        
        # Update reducers
        inclusion_reducer.update(selection)
        size_reducer.update(selection)
        stability_reducer.update(selection)
        
        if has_ranks:
            rank_reducer.update(selection)
        
        if has_topk:
            topk_overlap_reducer.update(selection)
    
    # Finalize reducers
    inclusion_result = inclusion_reducer.finalize()
    size_result = size_reducer.finalize()
    stability_result = stability_reducer.finalize()
    
    rank_result = None
    topk_overlap_result = None
    
    if has_ranks:
        rank_result = rank_reducer.finalize()
    
    if has_topk:
        topk_overlap_result = topk_overlap_reducer.finalize()
    
    # Build metadata
    ci_alpha = 1 - ci
    meta = {
        "method": method,
        "n_samples": n_samples,
        "seed": seed,
        "ci_level": ci,
    }
    
    if noise_model is not None:
        meta["noise_model"] = repr(noise_model)
    
    # Handle grouped results
    if grouped:
        # Build SelectionUQ per group
        result = {}
        
        all_groups = set(inclusion_result.keys())
        
        for group_key in all_groups:
            group_inclusion = inclusion_result.get(group_key, {})
            group_size = size_result.get(group_key, {})
            group_stability = stability_result.get(group_key, {})
            group_rank = rank_result.get(group_key) if rank_result else None
            group_topk_overlap = topk_overlap_result.get(group_key) if topk_overlap_result else None
            
            group_uq = SelectionUQ.from_reducers(
                inclusion_result=group_inclusion,
                size_result=group_size,
                stability_result=group_stability,
                rank_result=group_rank,
                topk_overlap_result=group_topk_overlap,
                consensus_threshold=consensus_threshold,
                borderline_epsilon=borderline_epsilon,
                ci_method="wilson",
                ci_alpha=ci_alpha,
                target=target,
                k=k,
                store_mode=store_mode,
                meta=meta.copy(),
            )
            
            result[group_key] = group_uq
        
        return result
    else:
        # Build single SelectionUQ
        return SelectionUQ.from_reducers(
            inclusion_result=inclusion_result,
            size_result=size_result,
            stability_result=stability_result,
            rank_result=rank_result,
            topk_overlap_result=topk_overlap_result,
            consensus_threshold=consensus_threshold,
            borderline_epsilon=borderline_epsilon,
            ci_method="wilson",
            ci_alpha=ci_alpha,
            target=target,
            k=k,
            store_mode=store_mode,
            meta=meta,
        )
