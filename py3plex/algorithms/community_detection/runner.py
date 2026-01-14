"""Unified runner for community detection algorithms.

This module provides a standardized interface for running community detection
algorithms with budget control, used by racing strategies like Successive Halving.
"""

from __future__ import annotations

import time
import warnings
from typing import Any, Dict, Optional

from py3plex.algorithms.community_detection.budget import BudgetSpec, CommunityResult


def run_community_algorithm(
    algorithm_id: str, network: Any, budget: BudgetSpec, seed: int, **kwargs
) -> CommunityResult:
    """Run a community detection algorithm with budget constraints.

    Unified runner interface for community detection algorithms. Maps
    algorithm_id to specific implementations and applies budget constraints
    where supported.

    Args:
        algorithm_id: Algorithm identifier (e.g., "louvain", "leiden")
        network: Multilayer network object
        budget: Budget specification
        seed: Random seed for reproducibility
        **kwargs: Additional algorithm-specific parameters

    Returns:
        CommunityResult with partition and metadata

    Raises:
        ValueError: If algorithm_id is not recognized
        AlgorithmError: If algorithm execution fails

    Examples:
        >>> from py3plex.core import multinet
        >>> from py3plex.algorithms.community_detection.budget import BudgetSpec
        >>>
        >>> net = multinet.multi_layer_network(directed=False)
        >>> # ... add nodes and edges ...
        >>>
        >>> budget = BudgetSpec(max_iter=10, n_restarts=2, uq_samples=20)
        >>> result = run_community_algorithm("louvain", net, budget, seed=42)
        >>> print(f"Found {len(set(result.partition.values()))} communities")

    Notes:
        - Algorithms ignore budget parameters they don't support
        - UQ is enabled if budget.uq_samples > 1
        - Runtime includes all computation (algorithm + UQ if enabled)
    """
    from py3plex.exceptions import AlgorithmError

    start_time = time.time()
    warn_list = []

    # Parse algorithm name
    algo_name = algorithm_id.split(":")[0] if ":" in algorithm_id else algorithm_id

    try:
        # Route to specific algorithm implementation
        if algo_name in ("louvain", "multilayer_louvain"):
            result = _run_louvain(network, budget, seed, **kwargs)

        elif algo_name in ("leiden", "multilayer_leiden"):
            result = _run_leiden(network, budget, seed, **kwargs)

        elif algo_name == "label_propagation":
            result = _run_label_propagation(network, budget, seed, **kwargs)

        elif algo_name in ("sbm", "standard_sbm"):
            result = _run_sbm(network, budget, seed, **kwargs)

        elif algo_name in ("dc_sbm", "degree_corrected_sbm"):
            result = _run_dc_sbm(network, budget, seed, **kwargs)

        else:
            raise ValueError(
                f"Unknown algorithm '{algo_name}'. "
                f"Supported: louvain, leiden, label_propagation, sbm, dc_sbm"
            )

        partition = result["partition"]
        warn_list.extend(result.get("warnings", []))
        meta = result.get("meta", {})

    except Exception as e:
        raise AlgorithmError(
            f"Algorithm '{algo_name}' failed: {e}",
            algorithm_name=algo_name,
            suggestions=["Check network connectivity", "Verify network format"],
        ) from e

    runtime_ms = (time.time() - start_time) * 1000

    return CommunityResult(
        algo_id=algorithm_id,
        partition=partition,
        runtime_ms=runtime_ms,
        budget_used=budget,
        warnings=warn_list,
        meta=meta,
        seed_used=seed,
    )


def _run_louvain(
    network: Any, budget: BudgetSpec, seed: int, **kwargs
) -> Dict[str, Any]:
    """Run Louvain algorithm with budget constraints.

    Args:
        network: Multilayer network
        budget: Budget specification
        seed: Random seed
        **kwargs: Additional parameters

    Returns:
        Dict with 'partition', 'warnings', 'meta'
    """
    from py3plex.algorithms.community_detection import multilayer_louvain

    # Check if UQ is requested
    enable_uq = budget.uq_samples is not None and budget.uq_samples > 1

    if enable_uq:
        # Run with UQ
        from py3plex.algorithms.community_detection import (
            multilayer_louvain_distribution,
        )

        n_samples = budget.uq_samples or 50

        dist = multilayer_louvain_distribution(
            network,
            n_runs=n_samples,
            seed=seed,
        )

        consensus = dist.consensus_partition()

        # Convert array to dict
        partition = {node: int(consensus[i]) for i, node in enumerate(dist.nodes)}

        meta = {
            "uq_enabled": True,
            "n_samples": n_samples,
        }

    else:
        # Run without UQ
        partition, modularity = multilayer_louvain(
            network,
            random_state=seed,
        )

        meta = {
            "uq_enabled": False,
            "modularity": modularity,
        }

    return {
        "partition": partition,
        "warnings": [],
        "meta": meta,
    }


def _run_leiden(
    network: Any, budget: BudgetSpec, seed: int, **kwargs
) -> Dict[str, Any]:
    """Run Leiden algorithm with budget constraints.

    Args:
        network: Multilayer network
        budget: Budget specification
        seed: Random seed
        **kwargs: Additional parameters

    Returns:
        Dict with 'partition', 'warnings', 'meta'
    """
    from py3plex.algorithms.community_detection import leiden_multilayer

    # Check if UQ is requested
    enable_uq = budget.uq_samples is not None and budget.uq_samples > 1

    if enable_uq:
        # Run with UQ
        from py3plex.algorithms.community_detection import multilayer_leiden_uq

        n_samples = budget.uq_samples or 50

        uq_result = multilayer_leiden_uq(
            network,
            n_runs=n_samples,
            seed=seed,
        )

        partition = uq_result.consensus

        meta = {
            "uq_enabled": True,
            "n_samples": n_samples,
        }

    else:
        # Run without UQ
        leiden_result = leiden_multilayer(
            network,
            seed=seed,
        )

        partition = leiden_result.communities

        meta = {
            "uq_enabled": False,
        }

    return {
        "partition": partition,
        "warnings": [],
        "meta": meta,
    }


def _run_label_propagation(
    network: Any, budget: BudgetSpec, seed: int, **kwargs
) -> Dict[str, Any]:
    """Run Label Propagation algorithm with budget constraints.

    Args:
        network: Multilayer network
        budget: Budget specification
        seed: Random seed
        **kwargs: Additional parameters

    Returns:
        Dict with 'partition', 'warnings', 'meta'
    """
    from py3plex.algorithms.community_detection import label_propagation

    # Label propagation doesn't have native UQ support yet
    max_iter = budget.max_iter or 100

    try:
        communities = label_propagation(
            network,
            max_iter=max_iter,
            seed=seed,
        )

        # Convert to standard format
        partition = {}
        for i, node in enumerate(network.get_nodes()):
            # Try to extract community assignment
            if node in communities:
                partition[node] = communities[node]
            else:
                # Fallback: assign to unique singleton community based on node index
                partition[node] = 1000 + i  # Offset to avoid collision with real communities

        meta = {
            "max_iter": max_iter,
        }

    except Exception as e:
        warnings.warn(f"Label propagation failed, using fallback: {e}", stacklevel=2)
        # Fallback: singleton communities
        partition = {node: i for i, node in enumerate(network.get_nodes())}
        meta = {"fallback": True}

    return {
        "partition": partition,
        "warnings": [],
        "meta": meta,
    }


def _run_sbm(
    network: Any, budget: BudgetSpec, seed: int, **kwargs
) -> Dict[str, Any]:
    """Run standard SBM algorithm with budget constraints.

    Args:
        network: Multilayer network
        budget: Budget specification
        seed: Random seed
        **kwargs: Additional parameters

    Returns:
        Dict with 'partition', 'warnings', 'meta'
    """
    import numpy as np
    from py3plex.algorithms.sbm import fit_multilayer_sbm

    # Extract budget parameters
    max_iter = budget.max_iter or 500
    n_restarts = budget.n_restarts or 5
    
    # Determine K_range from kwargs or budget
    K_range = kwargs.pop("K_range", None)
    if K_range is None:
        # Default K range for model selection
        K_range = [2, 3, 4, 5, 6, 7, 8]
    
    # Check if UQ is requested
    enable_uq = budget.uq_samples is not None and budget.uq_samples > 1

    if enable_uq:
        # Run with UQ (multiple runs with different seeds)
        n_samples = budget.uq_samples or 50
        
        from py3plex._parallel import spawn_seeds
        uq_seeds = spawn_seeds(seed, n_samples)
        
        partitions = []
        log_likelihoods = []
        mdl_scores = []
        
        for uq_seed in uq_seeds:
            # Fit with model selection
            model, selection_info = fit_multilayer_sbm(
                network,
                n_blocks=K_range,
                model="sbm",
                layer_mode="shared_blocks",
                n_init=n_restarts,
                max_iter=max_iter,
                seed=uq_seed,
                verbose=False,
                return_posterior=True
            )
            
            partition_i = model.to_partition_vector()
            partitions.append(partition_i)
            
            log_likelihoods.append(model.elbo_history_[-1])
            
            # Compute MDL if available
            if 'best_result' in selection_info and 'bic' in selection_info['best_result']:
                mdl_scores.append(selection_info['best_result']['bic'])
        
        # Build consensus partition (use first one for now, can improve)
        partition = partitions[0]
        
        meta = {
            "uq_enabled": True,
            "n_samples": n_samples,
            "log_likelihood": float(np.mean(log_likelihoods)),
            "log_likelihood_std": float(np.std(log_likelihoods)),
            "K_selected": model.K_,
            "model_type": "sbm",
        }
        
        if mdl_scores:
            meta["mdl"] = float(np.mean(mdl_scores))
            meta["mdl_std"] = float(np.std(mdl_scores))

    else:
        # Run without UQ
        model, selection_info = fit_multilayer_sbm(
            network,
            n_blocks=K_range,
            model="sbm",
            layer_mode="shared_blocks",
            n_init=n_restarts,
            max_iter=max_iter,
            seed=seed,
            verbose=False,
            return_posterior=True
        )
        
        partition = model.to_partition_vector()
        
        meta = {
            "uq_enabled": False,
            "log_likelihood": float(model.elbo_history_[-1]),
            "K_selected": model.K_,
            "converged": model.converged_,
            "n_iter": model.n_iter_,
            "model_type": "sbm",
        }
        
        if 'best_result' in selection_info and 'bic' in selection_info['best_result']:
            meta["mdl"] = float(selection_info['best_result']['bic'])

    return {
        "partition": partition,
        "warnings": [],
        "meta": meta,
    }


def _run_dc_sbm(
    network: Any, budget: BudgetSpec, seed: int, **kwargs
) -> Dict[str, Any]:
    """Run Degree-Corrected SBM algorithm with budget constraints.

    Args:
        network: Multilayer network
        budget: Budget specification
        seed: Random seed
        **kwargs: Additional parameters

    Returns:
        Dict with 'partition', 'warnings', 'meta'
    """
    import numpy as np
    from py3plex.algorithms.sbm import fit_multilayer_sbm

    # Extract budget parameters
    max_iter = budget.max_iter or 500
    n_restarts = budget.n_restarts or 5
    
    # Determine K_range from kwargs or budget
    K_range = kwargs.pop("K_range", None)
    if K_range is None:
        # Default K range for model selection
        K_range = [2, 3, 4, 5, 6, 7, 8]
    
    # Check if UQ is requested
    enable_uq = budget.uq_samples is not None and budget.uq_samples > 1

    if enable_uq:
        # Run with UQ (multiple runs with different seeds)
        n_samples = budget.uq_samples or 50
        
        from py3plex._parallel import spawn_seeds
        uq_seeds = spawn_seeds(seed, n_samples)
        
        partitions = []
        log_likelihoods = []
        mdl_scores = []
        
        for uq_seed in uq_seeds:
            # Fit with model selection
            model, selection_info = fit_multilayer_sbm(
                network,
                n_blocks=K_range,
                model="dc_sbm",
                layer_mode="shared_blocks",
                n_init=n_restarts,
                max_iter=max_iter,
                seed=uq_seed,
                verbose=False,
                return_posterior=True
            )
            
            partition_i = model.to_partition_vector()
            partitions.append(partition_i)
            
            log_likelihoods.append(model.elbo_history_[-1])
            
            # Compute MDL if available
            if 'best_result' in selection_info and 'bic' in selection_info['best_result']:
                mdl_scores.append(selection_info['best_result']['bic'])
        
        # Build consensus partition (use first one for now, can improve)
        partition = partitions[0]
        
        meta = {
            "uq_enabled": True,
            "n_samples": n_samples,
            "log_likelihood": float(np.mean(log_likelihoods)),
            "log_likelihood_std": float(np.std(log_likelihoods)),
            "K_selected": model.K_,
            "model_type": "dc_sbm",
        }
        
        if mdl_scores:
            meta["mdl"] = float(np.mean(mdl_scores))
            meta["mdl_std"] = float(np.std(mdl_scores))

    else:
        # Run without UQ
        model, selection_info = fit_multilayer_sbm(
            network,
            n_blocks=K_range,
            model="dc_sbm",
            layer_mode="shared_blocks",
            n_init=n_restarts,
            max_iter=max_iter,
            seed=seed,
            verbose=False,
            return_posterior=True
        )
        
        partition = model.to_partition_vector()
        
        meta = {
            "uq_enabled": False,
            "log_likelihood": float(model.elbo_history_[-1]),
            "K_selected": model.K_,
            "converged": model.converged_,
            "n_iter": model.n_iter_,
            "model_type": "dc_sbm",
        }
        
        if 'best_result' in selection_info and 'bic' in selection_info['best_result']:
            meta["mdl"] = float(selection_info['best_result']['bic'])

    return {
        "partition": partition,
        "warnings": [],
        "meta": meta,
    }
