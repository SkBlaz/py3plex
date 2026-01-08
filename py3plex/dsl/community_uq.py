"""Community detection with uncertainty quantification executor.

This module provides the execution logic for running community detection
with UQ enabled, integrating with the DSL .community().uq() pattern.

Examples
--------
>>> from py3plex.dsl import Q
>>> from py3plex.uncertainty.noise_models import EdgeDrop
>>> 
>>> result = (
...     Q.nodes()
...      .community(method="leiden", gamma=1.2, random_state=42)
...      .uq(method="perturbation", noise_model=EdgeDrop(p=0.1), n_samples=50, seed=42)
...      .execute(network)
... )
>>> 
>>> # Access UQ results
>>> uq = result.meta["uq"]
>>> print(uq.stability_summary())
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import logging
import warnings

import numpy as np

from py3plex.uncertainty import (
    PartitionUQ,
    partition_dict_to_array,
)
from py3plex.uncertainty.noise_models import NoiseModel
from py3plex.exceptions import AlgorithmError


logger = logging.getLogger(__name__)


def execute_community_with_uq(
    network: Any,
    method: str,
    uq_method: str,
    n_samples: int,
    seed: Optional[int] = None,
    noise_model: Optional[NoiseModel] = None,
    store: str = "sketch",
    sparse_topk: int = 50,
    sparse_threshold: float = 0.7,
    progress: bool = False,
    **algorithm_params
) -> Tuple[Dict[Any, int], PartitionUQ]:
    """Execute community detection with uncertainty quantification.
    
    This function runs community detection multiple times with different
    randomness sources (seed variation or network perturbation) to quantify
    uncertainty in the partition.
    
    Parameters
    ----------
    network : multi_layer_network
        Input network
    method : str
        Community detection algorithm: "leiden", "louvain", etc.
    uq_method : str
        UQ method: "seed", "perturbation", "bootstrap"
    n_samples : int
        Number of partition samples to generate
    seed : int, optional
        Base random seed for reproducibility
    noise_model : NoiseModel, optional
        Noise model for perturbation method (required if uq_method="perturbation")
    store : str, default="sketch"
        Storage mode: "none", "samples", or "sketch"
    sparse_topk : int, default=50
        Top-k neighbors for sparse co-assignment
    sparse_threshold : float, default=0.7
        Minimum co-assignment probability to store
    progress : bool, default=False
        Whether to log progress
    **algorithm_params
        Additional parameters for the community detection algorithm
        (gamma, omega, etc.)
        
    Returns
    -------
    consensus_partition : dict
        Consensus partition mapping (node, layer) -> community_id
    partition_uq : PartitionUQ
        Uncertainty quantification results
        
    Raises
    ------
    AlgorithmError
        If method is unsupported or parameters are invalid
        
    Examples
    --------
    >>> from py3plex.core import multinet
    >>> from py3plex.uncertainty.noise_models import EdgeDrop
    >>> 
    >>> net = multinet.multi_layer_network(directed=False)
    >>> # ... add edges ...
    >>> 
    >>> consensus, uq = execute_community_with_uq(
    ...     net,
    ...     method="leiden",
    ...     uq_method="perturbation",
    ...     n_samples=100,
    ...     seed=42,
    ...     noise_model=EdgeDrop(p=0.1),
    ...     gamma=1.2,
    ...     omega=0.8
    ... )
    """
    if progress:
        logger.info(
            f"Starting community UQ: method={method}, uq_method={uq_method}, "
            f"n_samples={n_samples}"
        )
    
    # Validate parameters
    if uq_method == "perturbation" and noise_model is None:
        raise AlgorithmError(
            "noise_model required for perturbation UQ",
            suggestions=["Provide EdgeDrop, WeightNoise, or LayerDrop"]
        )
    
    # Get community detection function
    community_func = _get_community_function(method)
    
    # Generate node ordering (canonical)
    node_ids = list(network.get_nodes())
    
    # Collect partition samples
    partitions = []
    
    if progress:
        logger.info(f"Generating {n_samples} partition samples...")
    
    for i in range(n_samples):
        # Determine seed for this sample
        sample_seed = seed + i if seed is not None else None
        
        # Generate sample network
        if uq_method == "seed":
            # Pure seed variation (no network modification)
            sample_net = network
        elif uq_method == "perturbation":
            # Apply noise model
            sample_net = noise_model.apply(network, seed=sample_seed)
        elif uq_method == "bootstrap":
            # TODO: Implement bootstrap resampling
            warnings.warn(
                "Bootstrap UQ not yet fully implemented, falling back to seed variation",
                stacklevel=2
            )
            sample_net = network
        else:
            raise AlgorithmError(
                f"Unknown UQ method: {uq_method}",
                valid_algorithms=["seed", "perturbation", "bootstrap"]
            )
        
        # Run community detection
        partition_dict = community_func(
            sample_net,
            seed=sample_seed,
            **algorithm_params
        )
        
        # Convert to array with canonical node ordering
        partition_array = partition_dict_to_array(partition_dict, node_ids)
        partitions.append(partition_array)
        
        if progress and (i + 1) % max(1, n_samples // 10) == 0:
            logger.info(f"  Generated {i + 1}/{n_samples} samples")
    
    if progress:
        logger.info("Computing UQ statistics...")
    
    # Create PartitionUQ from samples
    partition_uq = PartitionUQ.from_samples(
        partitions=partitions,
        node_ids=node_ids,
        store=store,
        sparse_topk=sparse_topk,
        sparse_threshold=sparse_threshold,
        meta={
            "method": method,
            "uq_method": uq_method,
            "n_samples": n_samples,
            "seed": seed,
            "noise_model": str(noise_model) if noise_model else None,
            "algorithm_params": algorithm_params,
        }
    )
    
    # Convert consensus partition back to dict format
    consensus_dict = {}
    for i, node_id in enumerate(node_ids):
        label = int(partition_uq.consensus_partition[i])
        consensus_dict[node_id] = label
    
    if progress:
        logger.info(
            f"UQ complete: {partition_uq.n_communities} communities, "
            f"VI={partition_uq.vi_mean:.3f}±{partition_uq.vi_std:.3f}"
        )
    
    return consensus_dict, partition_uq


def _get_community_function(method: str):
    """Get community detection function for method.
    
    Parameters
    ----------
    method : str
        Algorithm name
        
    Returns
    -------
    callable
        Function that takes (network, seed, **params) -> partition_dict
    """
    if method == "leiden":
        from py3plex.algorithms.community_detection.leiden_multilayer import (
            leiden_multilayer
        )
        
        def leiden_wrapper(network, seed=None, gamma=1.0, omega=1.0, **kwargs):
            """Wrapper for leiden_multilayer."""
            # Filter out n_iterations as leiden uses max_iter
            if 'n_iterations' in kwargs:
                kwargs['max_iter'] = kwargs.pop('n_iterations')
            
            result = leiden_multilayer(
                network,
                resolution=gamma,
                interlayer_coupling=omega,
                seed=seed,
                **kwargs
            )
            return result.communities
        
        return leiden_wrapper
    
    elif method == "louvain":
        from py3plex.algorithms.community_detection.community_louvain import (
            multilayer_louvain
        )
        
        def louvain_wrapper(network, seed=None, gamma=1.0, omega=1.0, **kwargs):
            """Wrapper for multilayer_louvain."""
            # Louvain returns partition dict directly
            partition = multilayer_louvain(
                network,
                resolution_parameter=gamma,
                interlayer_weight=omega,
                seed=seed,
                **kwargs
            )
            return partition
        
        return louvain_wrapper
    
    else:
        raise AlgorithmError(
            f"Unsupported community detection method for UQ: {method}",
            algorithm_name=method,
            valid_algorithms=["leiden", "louvain"],
            suggestions=[
                "Use 'leiden' for production-ready UQ",
                "Use 'louvain' for faster approximation"
            ]
        )
