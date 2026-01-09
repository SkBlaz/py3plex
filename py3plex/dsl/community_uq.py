"""Community detection with uncertainty quantification executor.

This module provides the execution logic for running community detection
with UQ enabled, integrating with the DSL .community().uq() pattern.

This implementation uses the canonical UQ execution spine (run_uq) for
consistency and maintainability.

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
from py3plex.uncertainty.noise_models import NoiseModel, NoNoise
from py3plex.uncertainty.plan import UQPlan
from py3plex.uncertainty.runner import run_uq
from py3plex.uncertainty.partition_types import PartitionOutput
from py3plex.uncertainty.partition_reducers import (
    NodeMarginalReducer,
    StabilityReducer,
)
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
    
    This implementation uses the canonical UQ execution spine for consistency
    with the PartitionUQ specification.
    
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
    n_nodes = len(node_ids)
    
    # Create node ID to index mapping for later use
    node_to_idx = {nid: i for i, nid in enumerate(node_ids)}
    
    # Define base callable for UQ spine
    def base_callable(net, rng):
        """Run community detection once with given RNG.
        
        This is the base_callable for UQPlan. It must:
        - Be deterministic given RNG
        - Return PartitionOutput
        """
        # Generate seed from RNG for community algorithm
        algo_seed = int(rng.integers(0, 2**31)) if rng is not None else None
        
        # Run community detection
        partition_dict = community_func(
            net,
            seed=algo_seed,
            **algorithm_params
        )
        
        # Convert to PartitionOutput
        return PartitionOutput(labels=partition_dict)
    
    # Set up noise model
    if uq_method == "seed":
        noise_model_actual = NoNoise()
        strategy = "seed"
    elif uq_method == "perturbation":
        if noise_model is None:
            raise AlgorithmError("noise_model required for perturbation")
        noise_model_actual = noise_model
        strategy = "perturbation"
    elif uq_method == "bootstrap":
        warnings.warn(
            "Bootstrap UQ not yet fully implemented, falling back to seed variation",
            stacklevel=2
        )
        noise_model_actual = NoNoise()
        strategy = "bootstrap"
    else:
        raise AlgorithmError(
            f"Unknown UQ method: {uq_method}",
            valid_algorithms=["seed", "perturbation", "bootstrap"]
        )
    
    # Create reducers
    marginal_reducer = NodeMarginalReducer(n_nodes=n_nodes, node_ids=node_ids)
    
    # For two-pass approach with StabilityReducer:
    # 1. First pass: compute marginals and consensus
    # 2. Second pass: compute stability against consensus
    # For now, use marginal_reducer only (matches from_samples behavior)
    
    # Create UQ plan
    plan = UQPlan(
        base_callable=base_callable,
        strategy=strategy,
        noise_model=noise_model_actual,
        n_samples=n_samples,
        seed=seed if seed is not None else 42,
        reducers=[marginal_reducer],
        storage_mode=store,
        backend="python"
    )
    
    if progress:
        logger.info(f"Running UQ spine with {n_samples} samples...")
    
    # Execute UQ
    uq_result = run_uq(plan, network)
    
    if progress:
        logger.info("Creating PartitionUQ from results...")
    
    # Create PartitionUQ from UQ result
    partition_uq = PartitionUQ.from_uq_result(
        uq_result=uq_result,
        node_ids=node_ids,
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
    
    elif method == "label_propagation_supra":
        from py3plex.algorithms.community_detection.label_propagation import (
            multilayer_label_propagation_supra
        )
        
        def lp_supra_wrapper(network, seed=None, omega=1.0, **kwargs):
            """Wrapper for multilayer_label_propagation_supra."""
            # Extract relevant parameters
            max_iter = kwargs.get('max_iter', 100)
            projection = kwargs.get('projection', 'none')
            
            result = multilayer_label_propagation_supra(
                network,
                omega=omega,
                max_iter=max_iter,
                random_state=seed,
                projection=projection,
            )
            return result.get("partition_supra", {})
        
        return lp_supra_wrapper
    
    elif method == "label_propagation_consensus":
        from py3plex.algorithms.community_detection.label_propagation import (
            multiplex_label_propagation_consensus
        )
        
        def lp_consensus_wrapper(network, seed=None, **kwargs):
            """Wrapper for multiplex_label_propagation_consensus."""
            max_iter = kwargs.get('max_iter', 25)
            inner_max_iter = kwargs.get('inner_max_iter', 50)
            
            result = multiplex_label_propagation_consensus(
                network,
                max_iter=max_iter,
                inner_max_iter=inner_max_iter,
                random_state=seed,
            )
            # Consensus algorithm returns node-level partition
            # But DSL expects (node, layer) tuples
            # Use labels_by_layer which has the correct format
            return result.get("labels_by_layer", {})
        
        return lp_consensus_wrapper
    
    elif method == "spectral_multilayer_supra":
        from py3plex.algorithms.community_detection.spectral_multilayer import (
            spectral_multilayer_supra
        )
        
        def spectral_supra_wrapper(network, seed=None, omega=1.0, k=None, **kwargs):
            """Wrapper for spectral_multilayer_supra."""
            if k is None:
                raise AlgorithmError(
                    "k parameter required for spectral clustering",
                    suggestions=["Provide k (number of communities)"]
                )
            
            result = spectral_multilayer_supra(
                network,
                k=k,
                omega=omega,
                random_state=seed,
                **kwargs
            )
            
            # Convert node-level partition to (node, layer) format
            partition_node_layer = {}
            layer_data = network.get_layers()
            all_layers = layer_data[0] if isinstance(layer_data, tuple) else layer_data
            for node in result["partition_nodes"]:
                comm_id = result["partition_nodes"][node]
                for layer in all_layers:
                    partition_node_layer[(node, layer)] = comm_id
            
            return partition_node_layer
        
        return spectral_supra_wrapper
    
    elif method == "spectral_multilayer_multiplex":
        from py3plex.algorithms.community_detection.spectral_multilayer import (
            spectral_multilayer_multiplex
        )
        
        def spectral_multiplex_wrapper(network, seed=None, k=None, **kwargs):
            """Wrapper for spectral_multilayer_multiplex."""
            if k is None:
                raise AlgorithmError(
                    "k parameter required for spectral clustering",
                    suggestions=["Provide k (number of communities)"]
                )
            
            result = spectral_multilayer_multiplex(
                network,
                k=k,
                random_state=seed,
                **kwargs
            )
            
            # Convert node-level partition to (node, layer) format
            partition_node_layer = {}
            layer_data = network.get_layers()
            all_layers = layer_data[0] if isinstance(layer_data, tuple) else layer_data
            for node in result["partition_nodes"]:
                comm_id = result["partition_nodes"][node]
                for layer in all_layers:
                    partition_node_layer[(node, layer)] = comm_id
            
            return partition_node_layer
        
        return spectral_multiplex_wrapper
    
    else:
        raise AlgorithmError(
            f"Unsupported community detection method for UQ: {method}",
            algorithm_name=method,
            valid_algorithms=[
                "leiden", "louvain", 
                "label_propagation_supra", "label_propagation_consensus",
                "spectral_multilayer_supra", "spectral_multilayer_multiplex"
            ],
            suggestions=[
                "Use 'leiden' for production-ready UQ",
                "Use 'louvain' for faster approximation",
                "Use 'label_propagation_supra' for hard-label supra-graph LPA",
                "Use 'label_propagation_consensus' for consensus LPA",
                "Use 'spectral_multilayer_supra' for supra-Laplacian spectral clustering",
                "Use 'spectral_multilayer_multiplex' for aggregated Laplacian spectral clustering"
            ]
        )
