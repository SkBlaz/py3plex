"""Uncertainty estimation helpers.

This module provides the main helper function for estimating uncertainty
in network statistics via resampling or perturbation strategies.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np

from py3plex.core import multinet
from py3plex.robustness.perturbations import EdgeDrop, NodeDrop, compose
from py3plex.robustness.experiments import estimate_metric_distribution

from .types import ResamplingStrategy, StatSeries, StatMatrix
from .context import get_uncertainty_config


def estimate_uncertainty(
    network: multinet.multi_layer_network,
    metric_fn: Callable[[multinet.multi_layer_network], Union[Dict[Any, float], float, np.ndarray]],
    *,
    n_runs: Optional[int] = None,
    resampling: Optional[ResamplingStrategy] = None,
    random_seed: Optional[int] = None,
    perturbation_params: Optional[Dict[str, Any]] = None,
) -> Union[StatSeries, float]:
    """Estimate uncertainty for a network statistic.
    
    This is the main entry point for adding uncertainty to any statistic.
    It runs the metric function multiple times with different random seeds
    or network perturbations, then computes mean, std, and quantiles.
    
    Parameters
    ----------
    network : multi_layer_network
        The network to analyze.
    metric_fn : callable
        Function that computes a statistic. Must accept a network and return:
        - dict[node, float] for per-node statistics
        - float for scalar statistics
        - np.ndarray for array statistics
    n_runs : int, optional
        Number of runs for uncertainty estimation. If None, uses the
        default from the current uncertainty config.
    resampling : ResamplingStrategy, optional
        Strategy for resampling. If None, uses default from config.
    random_seed : int, optional
        Random seed for reproducibility.
    perturbation_params : dict, optional
        Parameters for perturbation strategies. For example:
        {"edge_drop_p": 0.05, "node_drop_p": 0.02}
    
    Returns
    -------
    StatSeries or float
        If metric_fn returns a dict: StatSeries with uncertainty info
        If metric_fn returns a scalar: float (mean value)
        The returned object has mean, std, and quantiles populated.
    
    Examples
    --------
    >>> from py3plex.uncertainty import estimate_uncertainty, ResamplingStrategy
    >>> from py3plex.core import multinet
    >>> 
    >>> # Create a simple network
    >>> net = multinet.multi_layer_network(directed=False)
    >>> net.add_edges([["a", "L0", "b", "L0", 1.0]], input_type="list")
    >>> 
    >>> # Define a metric function
    >>> def my_metric(network):
    ...     # Return per-node degree
    ...     degrees = {}
    ...     for node in network.get_nodes():
    ...         degrees[node] = network.core_network.degree(node)
    ...     return degrees
    >>> 
    >>> # Estimate uncertainty
    >>> result = estimate_uncertainty(
    ...     net,
    ...     my_metric,
    ...     n_runs=50,
    ...     resampling=ResamplingStrategy.PERTURBATION,
    ...     perturbation_params={"edge_drop_p": 0.1}
    ... )
    >>> result.mean  # Mean degree values
    >>> result.std   # Std deviation of degrees
    >>> result.quantiles  # Confidence intervals
    
    Notes
    -----
    - For SEED strategy: runs the metric with different random seeds
    - For PERTURBATION strategy: applies edge/node drops then recomputes
    - For BOOTSTRAP: resamples nodes/edges with replacement (not yet implemented)
    - For JACKKNIFE: leave-one-out resampling (not yet implemented)
    """
    # Get defaults from config if not specified
    cfg = get_uncertainty_config()
    if n_runs is None:
        n_runs = cfg.default_n_runs
    if resampling is None:
        resampling = cfg.default_resampling
    
    # Validate n_runs
    if n_runs <= 0:
        raise ValueError("n_runs must be positive")
    
    # Initialize RNG
    rng = np.random.default_rng(random_seed)
    
    # Choose strategy
    if resampling == ResamplingStrategy.SEED:
        return _estimate_via_seeds(network, metric_fn, n_runs, rng)
    elif resampling == ResamplingStrategy.PERTURBATION:
        return _estimate_via_perturbation(
            network, metric_fn, n_runs, rng, perturbation_params
        )
    elif resampling == ResamplingStrategy.BOOTSTRAP:
        raise NotImplementedError("Bootstrap resampling not yet implemented")
    elif resampling == ResamplingStrategy.JACKKNIFE:
        raise NotImplementedError("Jackknife resampling not yet implemented")
    else:
        raise ValueError(f"Unknown resampling strategy: {resampling}")


def _estimate_via_seeds(
    network: multinet.multi_layer_network,
    metric_fn: Callable,
    n_runs: int,
    rng: np.random.Generator,
) -> Union[StatSeries, float]:
    """Estimate uncertainty by running with different random seeds.
    
    This strategy runs the metric function multiple times on the same network,
    but with different random seeds if the algorithm is stochastic.
    """
    samples: List[Union[Dict, float, np.ndarray]] = []
    
    for _ in range(n_runs):
        # Generate a random seed for this run
        seed = int(rng.integers(0, 2**31))
        
        # For now, we can't easily inject seed into arbitrary functions
        # So we just run the function multiple times
        # If the function is deterministic, std will be 0
        result = metric_fn(network)
        samples.append(result)
    
    return _aggregate_samples(samples)


def _estimate_via_perturbation(
    network: multinet.multi_layer_network,
    metric_fn: Callable,
    n_runs: int,
    rng: np.random.Generator,
    perturbation_params: Optional[Dict[str, Any]] = None,
) -> Union[StatSeries, float]:
    """Estimate uncertainty via network perturbations.
    
    This strategy perturbs the network structure (drop edges/nodes) and
    recomputes the metric on each perturbed network.
    """
    # Default perturbation parameters
    params = {
        "edge_drop_p": 0.05,
        "node_drop_p": 0.0,
    }
    if perturbation_params:
        params.update(perturbation_params)
    
    # Build perturbation
    perturbations = []
    if params["edge_drop_p"] > 0:
        perturbations.append(EdgeDrop(p=params["edge_drop_p"]))
    if params["node_drop_p"] > 0:
        perturbations.append(NodeDrop(p=params["node_drop_p"]))
    
    if not perturbations:
        # No perturbation, fall back to seed strategy
        return _estimate_via_seeds(network, metric_fn, n_runs, rng)
    
    if len(perturbations) == 1:
        perturbation = perturbations[0]
    else:
        perturbation = compose(*perturbations)
    
    # Use the existing estimate_metric_distribution from robustness module
    result = estimate_metric_distribution(
        network=network,
        metric_fn=metric_fn,
        perturbation=perturbation,
        n_samples=n_runs,
        random_state=int(rng.integers(0, 2**31)),
    )
    
    # Convert to StatSeries or float
    samples = result["samples"]
    return _aggregate_samples(samples)


def _aggregate_samples(
    samples: List[Union[Dict, float, np.ndarray]]
) -> Union[StatSeries, float]:
    """Aggregate samples into StatSeries or scalar with uncertainty info.
    
    Parameters
    ----------
    samples : list
        List of sample results. Each can be:
        - dict[node, float]: per-node values
        - float: scalar value
        - np.ndarray: array of values
    
    Returns
    -------
    StatSeries or float
        Aggregated result with mean, std, quantiles.
    """
    if not samples:
        raise ValueError("No samples to aggregate")
    
    # Check the type of the first sample
    first = samples[0]
    
    if isinstance(first, dict):
        # Per-node statistics - return StatSeries
        # Get all nodes that appear in any sample
        all_nodes = set()
        for s in samples:
            if isinstance(s, dict):
                all_nodes.update(s.keys())
        
        index = sorted(all_nodes, key=lambda x: str(x))
        n = len(index)
        
        # Build matrix of values: (n_samples, n_nodes)
        values = np.zeros((len(samples), n))
        for i, sample in enumerate(samples):
            if isinstance(sample, dict):
                for j, node in enumerate(index):
                    values[i, j] = sample.get(node, 0.0)
        
        # Compute statistics
        mean = np.mean(values, axis=0)
        std = np.std(values, axis=0)
        
        # Compute 95% CI (2.5th and 97.5th percentiles)
        q025 = np.percentile(values, 2.5, axis=0)
        q975 = np.percentile(values, 97.5, axis=0)
        
        return StatSeries(
            index=index,
            mean=mean,
            std=std,
            quantiles={0.025: q025, 0.975: q975},
            meta={"n_samples": len(samples)},
        )
    
    elif isinstance(first, (int, float, np.number)):
        # Scalar statistics - return float (mean)
        values = np.array([float(s) for s in samples], dtype=float)
        return float(np.mean(values))
    
    elif isinstance(first, np.ndarray):
        # Array statistics - return StatSeries with integer index
        # Assume all samples have the same shape
        n = len(first)
        index = list(range(n))
        
        values = np.array([np.asarray(s) for s in samples])
        
        mean = np.mean(values, axis=0)
        std = np.std(values, axis=0)
        q025 = np.percentile(values, 2.5, axis=0)
        q975 = np.percentile(values, 97.5, axis=0)
        
        return StatSeries(
            index=index,
            mean=mean,
            std=std,
            quantiles={0.025: q025, 0.975: q975},
            meta={"n_samples": len(samples)},
        )
    
    else:
        raise TypeError(
            f"Unsupported sample type: {type(first)}. "
            "Expected dict, float, or np.ndarray"
        )
