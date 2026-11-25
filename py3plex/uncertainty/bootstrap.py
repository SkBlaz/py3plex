"""Bootstrap engine for uncertainty estimation.

This module provides a generic bootstrap helper that can be used to estimate
uncertainty for any graph metric via resampling.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

import numpy as np

from py3plex.core import multinet
from py3plex._parallel import parallel_map, spawn_seeds
from py3plex import config
from .resampling_graph import _add_sample_edge, _bootstrap_edges, _bootstrap_units, _edge_sample_base, _edge_pool


class _AggregateDegree:
    """Unweighted total degree over the full graph for selected replicas."""

    def __init__(self, items):
        self.items = items

    def __call__(self, network):
        graph = network.core_network
        return {node: graph.degree(node) for node in self.items if node in graph}

    @staticmethod
    def edge_draws(pool, index, child_seeds):
        # An undirected loop and a directed loop both contribute two to total
        # degree. Endpoints outside the selection contribute to a spare bin.
        positions = {node: i for i, node in enumerate(index)}
        bins = len(index) + 1

        def endpoints(records):
            return np.fromiter(
                (positions.get(node, len(index))
                 for u, v, _, _ in records for node in (u, v)),
                dtype=np.intp, count=2 * len(records),
            ).reshape(-1, 2)

        interactions, coupling = pool
        edges = endpoints(interactions)
        fixed = np.bincount(endpoints(coupling).ravel(), minlength=bins)
        samples = np.empty((len(child_seeds), len(index)))
        for row, seed in enumerate(child_seeds):
            if len(edges):
                draws = np.random.default_rng(seed).integers(len(edges), size=len(edges))
                degree = fixed + np.bincount(edges[draws].ravel(), minlength=bins)
            else:
                degree = fixed
            samples[row] = degree[:-1]
        return samples


def _bootstrap_single_replicate(args):
    """Generate and compute metric for a single bootstrap replicate.
    
    This is a module-level function so it can be pickled for multiprocessing.
    
    Parameters
    ----------
    args : tuple
        Tuple of (graph, metric_fn, unit, mode, seed, index)
        
    Returns
    -------
    np.ndarray
        Metric values for this replicate, indexed by the index list
    """
    graph, metric_fn, unit, mode, seed, index, pool = args
    
    # Create RNG for this replicate
    rng = np.random.default_rng(seed)
    
    # Create bootstrap sample
    if unit == "edges":
        boot_graph = _resample_edges(graph, mode, rng, pool)
    elif unit == "nodes":
        boot_graph = _resample_nodes(graph, mode, rng)
    elif unit == "layers":
        boot_graph = _resample_layers(graph, mode, rng)
    else:
        raise ValueError(f"Unknown unit: {unit}")
    
    result = metric_fn(boot_graph)
    return np.asarray([result.get(item, np.nan) for item in index], dtype=float)


def bootstrap_metric(
    graph: multinet.multi_layer_network,
    metric_fn: Callable[[multinet.multi_layer_network], Dict[Any, float]],
    n_boot: int = 50,  # Standardized to match DSL default
    unit: str = "edges",
    mode: str = "resample",
    ci: float = 0.95,
    random_state: Optional[int] = None,
    n_jobs: Optional[int] = None,
) -> Dict[str, np.ndarray]:
    """Bootstrap a metric for uncertainty estimation.
    
    This function resamples the graph by unit (edges, nodes, or layers) and
    recomputes the metric on each bootstrap sample to estimate uncertainty.
    
    Parameters
    ----------
    graph : multi_layer_network
        The multilayer network to analyze.
    metric_fn : callable
        Function that takes a network and returns a dict mapping items (usually
        nodes) to metric values. Must have signature:
        metric_fn(network) -> Dict[item_id, float]
    n_boot : int, default=200
        Number of bootstrap replicates.
    unit : str, default="edges"
        What to resample: "edges", "nodes", or "layers".
    mode : str, default="resample"
        Resampling mode:
        - "resample": Sample with replacement (classic bootstrap)
        - "permute": Permute the units (permutation test)
    ci : float, default=0.95
        Confidence interval level (e.g., 0.95 for 95% CI).
    random_state : int, optional
        Random seed for reproducibility.
    n_jobs : int, optional
        Number of parallel jobs. If None, uses config.DEFAULT_N_JOBS.
        If 1, runs serially. If >1, runs in parallel.
    
    Returns
    -------
    dict
        Dictionary with keys:
        - "mean": np.ndarray of shape (n_items,) with mean values
        - "std": np.ndarray of shape (n_items,) with standard errors
        - "ci_low": np.ndarray of shape (n_items,) with lower CI bounds
        - "ci_high": np.ndarray of shape (n_items,) with upper CI bounds
        - "index": List of item IDs
        - "n_boot": Number of bootstrap replicates used
        - "method": String describing the bootstrap method
    
    Examples
    --------
    >>> from py3plex.core import multinet
    >>> from py3plex.uncertainty.bootstrap import bootstrap_metric
    >>> 
    >>> # Create a network
    >>> net = multinet.multi_layer_network(directed=False)
    >>> net.add_edges([["a", "L0", "b", "L0", 1.0]], input_type="list")
    >>> 
    >>> # Define metric function
    >>> def degree_metric(network):
    ...     result = {}
    ...     for node in network.get_nodes():
    ...         result[node] = network.core_network.degree(node)
    ...     return result
    >>> 
    >>> # Bootstrap
    >>> boot_result = bootstrap_metric(
    ...     net, degree_metric, n_boot=100, unit="edges"
    ... )
    >>> boot_result["mean"]  # Mean degree values
    >>> boot_result["ci_low"]  # Lower CI bounds
    
    Notes
    -----
    - For "edges" unit: resamples edges with replacement
    - For "nodes" unit: resamples nodes with replacement
    - For "layers" unit: resamples layers with replacement
    - Replicate metric failures propagate. Missing items are summarized only
      over draws where they exist, with counts reported in sample_counts.
    - With permute, topology and attributes are preserved; only edge insertion
      order changes.
    """
    if unit not in {"edges", "nodes", "layers"}:
        raise ValueError(f"Unknown unit: {unit}")
    if mode not in {"resample", "permute"}:
        raise ValueError(f"Unknown mode: {mode}")
    if not 0 < ci < 1:
        raise ValueError("ci must be between 0 and 1")
    if n_boot <= 0:
        raise ValueError("n_boot must be positive")

    # Compute original metric to get item IDs
    original_result = metric_fn(graph)
    if not isinstance(original_result, dict):
        raise TypeError(
            "metric_fn must return a dict mapping items to values. "
            f"Got {type(original_result)}"
        )
    
    # Handle empty result
    if not original_result:
        return {
            "mean": np.array([]),
            "std": np.array([]),
            "ci_low": np.array([]),
            "ci_high": np.array([]),
            "index": [],
            "sample_counts": np.array([], dtype=int),
            "n_boot": n_boot,
            "method": f"bootstrap_{mode}_{unit}",
        }
    
    # Get sorted list of items for consistent indexing
    index = sorted(original_result.keys(), key=lambda x: str(x))
    len(index)
    
    # Determine number of jobs
    if n_jobs is None:
        n_jobs = getattr(config, 'DEFAULT_N_JOBS', 1)
    
    # Generate child seeds for deterministic parallel execution
    child_seeds = spawn_seeds(random_state, n_boot)
    
    # Prepare arguments for each bootstrap replicate
    pool = _edge_pool(graph) if n_jobs == 1 and unit == "edges" else None
    if isinstance(metric_fn, _AggregateDegree) and pool is not None and mode == "resample":
        samples = metric_fn.edge_draws(pool, index, child_seeds)
    else:
        replicate_args = [
            (graph, metric_fn, unit, mode, child_seed, index, pool)
            for child_seed in child_seeds
        ]

        # Run bootstrap replicates in parallel or serial
        samples_list = parallel_map(
            _bootstrap_single_replicate,
            replicate_args,
            n_jobs=n_jobs,
            backend=getattr(config, 'DEFAULT_PARALLEL_BACKEND', 'multiprocessing'),
        )

        # Stack results into array: (n_boot, n_items)
        samples = np.array(samples_list)

    # Missing items are summarized conditionally on presence.
    alpha = (1 - ci) / 2
    mean, std, ci_low, ci_high = np.full((4, len(index)), np.nan)
    finite = np.isfinite(samples)
    sample_counts = finite.sum(axis=0)
    complete = sample_counts == n_boot
    if complete.any():
        dense = samples if complete.all() else samples[:, complete]
        mean[complete] = dense.mean(axis=0)
        std[complete] = dense.std(axis=0, ddof=int(n_boot > 1))
        ci_low[complete], ci_high[complete] = np.quantile(dense, [alpha, 1 - alpha], axis=0)
    for i in np.flatnonzero(~complete):
        present = samples[finite[:, i], i]
        if present.size:
            mean[i] = present.mean()
            std[i] = present.std(ddof=int(present.size > 1))
            ci_low[i], ci_high[i] = np.quantile(present, [alpha, 1 - alpha])

    return {
        "mean": mean,
        "std": std,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "index": index,
        "sample_counts": sample_counts,
        "n_boot": n_boot,
        "method": f"bootstrap_{mode}_{unit}",
    }


def _resample_edges(graph, mode, rng, pool=None):
    if mode == "resample":
        return _bootstrap_edges(graph, rng, pool)
    sample, edges = _edge_sample_base(graph, pool=pool)
    for index in rng.permutation(len(edges)):
        _add_sample_edge(sample.core_network, *edges[index])
    return sample


def _resample_nodes(graph, mode, rng):
    if mode == "resample":
        return _bootstrap_units(graph, "nodes", rng)
    return _resample_edges(graph, mode, rng)


def _resample_layers(graph, mode, rng):
    if mode == "resample":
        return _bootstrap_units(graph, "layers", rng)
    return _resample_edges(graph, mode, rng)
