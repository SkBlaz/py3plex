"""Bootstrap engine for uncertainty estimation.

This module provides a generic bootstrap helper that can be used to estimate
uncertainty for any graph metric via resampling.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union
import copy

import numpy as np
import networkx as nx

from py3plex.core import multinet
from py3plex._parallel import parallel_map, spawn_seeds
from py3plex import config


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
    graph, metric_fn, unit, mode, seed, index = args
    
    # Create RNG for this replicate
    rng = np.random.default_rng(seed)
    
    # Create bootstrap sample
    if unit == "edges":
        boot_graph = _resample_edges(graph, mode, rng)
    elif unit == "nodes":
        boot_graph = _resample_nodes(graph, mode, rng)
    elif unit == "layers":
        boot_graph = _resample_layers(graph, mode, rng)
    else:
        raise ValueError(f"Unknown unit: {unit}")
    
    # Compute metric on bootstrap sample
    try:
        boot_result = metric_fn(boot_graph)
    except Exception:
        # If metric fails on this bootstrap sample, use zeros
        boot_result = {item: 0.0 for item in index}
    
    # Convert to array (use 0 for missing items)
    result_array = np.array([boot_result.get(item, 0.0) for item in index])
    return result_array


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
    - The metric_fn must be able to handle graphs with different structure
    """
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
            "n_boot": n_boot,
            "method": f"bootstrap_{mode}_{unit}",
        }
    
    # Get sorted list of items for consistent indexing
    index = sorted(original_result.keys(), key=lambda x: str(x))
    n_items = len(index)
    
    # Determine number of jobs
    if n_jobs is None:
        n_jobs = getattr(config, 'DEFAULT_N_JOBS', 1)
    
    # Generate child seeds for deterministic parallel execution
    child_seeds = spawn_seeds(random_state, n_boot)
    
    # Prepare arguments for each bootstrap replicate
    replicate_args = [
        (graph, metric_fn, unit, mode, child_seed, index)
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
    
    # Compute statistics
    mean = np.mean(samples, axis=0)
    # For a single replicate, ddof=1 yields NaNs; treat as 0 variability.
    ddof = 1 if n_boot > 1 else 0
    std = np.std(samples, axis=0, ddof=ddof)
    
    # Compute confidence intervals using percentile method
    alpha = 1 - ci
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    ci_low = np.percentile(samples, lower_percentile, axis=0)
    ci_high = np.percentile(samples, upper_percentile, axis=0)
    
    return {
        "mean": mean,
        "std": std,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "index": index,
        "n_boot": n_boot,
        "method": f"bootstrap_{mode}_{unit}",
    }


def _resample_edges(
    graph: multinet.multi_layer_network,
    mode: str,
    rng: np.random.Generator,
) -> multinet.multi_layer_network:
    """Resample edges from a multilayer network.
    
    Parameters
    ----------
    graph : multi_layer_network
        Original network.
    mode : str
        "resample" for sampling with replacement, "permute" for shuffling.
    rng : np.random.Generator
        Random number generator.
    
    Returns
    -------
    multi_layer_network
        New network with resampled edges.
    """
    # Get all edges
    edges = list(graph.get_edges(data=True))
    n_edges = len(edges)
    
    if n_edges == 0:
        # Return empty network
        return multinet.multi_layer_network(
            directed=graph.directed,
            verbose=False
        )
    
    # Resample or permute
    if mode == "resample":
        # Sample with replacement
        indices = rng.choice(n_edges, size=n_edges, replace=True)
        resampled_edges = [edges[i] for i in indices]
    elif mode == "permute":
        # Shuffle edges
        indices = np.arange(n_edges)
        rng.shuffle(indices)
        resampled_edges = [edges[i] for i in indices]
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    # Create new network
    new_graph = multinet.multi_layer_network(
        directed=graph.directed,
        verbose=False
    )
    
    # Add resampled edges
    for edge_data in resampled_edges:
        if len(edge_data) == 3:
            u, v, data = edge_data
            # Extract layer information from node tuples
            if isinstance(u, tuple) and isinstance(v, tuple):
                source, source_layer = u
                target, target_layer = v
                weight = data.get('weight', 1.0)
                new_graph.add_edges([
                    [source, source_layer, target, target_layer, weight]
                ], input_type="list")
    
    return new_graph


def _resample_nodes(
    graph: multinet.multi_layer_network,
    mode: str,
    rng: np.random.Generator,
) -> multinet.multi_layer_network:
    """Resample nodes from a multilayer network.
    
    Parameters
    ----------
    graph : multi_layer_network
        Original network.
    mode : str
        "resample" for sampling with replacement, "permute" for shuffling.
    rng : np.random.Generator
        Random number generator.
    
    Returns
    -------
    multi_layer_network
        New network with subgraph induced by resampled nodes.
    """
    # Get all nodes
    nodes = list(graph.get_nodes())
    n_nodes = len(nodes)
    
    if n_nodes == 0:
        return multinet.multi_layer_network(
            directed=graph.directed,
            verbose=False
        )
    
    # Resample or permute
    if mode == "resample":
        # Sample with replacement
        indices = rng.choice(n_nodes, size=n_nodes, replace=True)
        resampled_nodes = [nodes[i] for i in indices]
    elif mode == "permute":
        # Shuffle nodes
        indices = np.arange(n_nodes)
        rng.shuffle(indices)
        resampled_nodes = [nodes[i] for i in indices]
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    # Get unique nodes (in case of duplicates from resampling)
    unique_nodes = list(set(resampled_nodes))
    
    # Create subgraph with these nodes
    # Get edges that connect the resampled nodes
    new_graph = multinet.multi_layer_network(
        directed=graph.directed,
        verbose=False
    )
    
    edges = []
    for edge_data in graph.get_edges(data=True):
        if len(edge_data) == 3:
            u, v, data = edge_data
            # Check if both nodes are in resampled set
            if isinstance(u, tuple) and isinstance(v, tuple):
                source, source_layer = u
                target, target_layer = v
                if u in unique_nodes and v in unique_nodes:
                    weight = data.get('weight', 1.0)
                    edges.append([source, source_layer, target, target_layer, weight])
    
    if edges:
        new_graph.add_edges(edges, input_type="list")
    
    return new_graph


def _resample_layers(
    graph: multinet.multi_layer_network,
    mode: str,
    rng: np.random.Generator,
) -> multinet.multi_layer_network:
    """Resample layers from a multilayer network.
    
    Parameters
    ----------
    graph : multi_layer_network
        Original network.
    mode : str
        "resample" for sampling with replacement, "permute" for shuffling.
    rng : np.random.Generator
        Random number generator.
    
    Returns
    -------
    multi_layer_network
        New network with resampled layers.
    """
    # Get all layer names
    try:
        layers_info = graph.get_layers()
        if isinstance(layers_info, tuple) and len(layers_info) >= 1:
            layer_names = layers_info[0]
        else:
            layer_names = []
    except Exception:
        layer_names = []
    
    n_layers = len(layer_names)
    
    if n_layers == 0:
        return multinet.multi_layer_network(
            directed=graph.directed,
            verbose=False
        )
    
    # Resample or permute
    if mode == "resample":
        # Sample with replacement
        indices = rng.choice(n_layers, size=n_layers, replace=True)
        resampled_layers = [layer_names[i] for i in indices]
    elif mode == "permute":
        # Shuffle layers
        indices = np.arange(n_layers)
        rng.shuffle(indices)
        resampled_layers = [layer_names[i] for i in indices]
    else:
        raise ValueError(f"Unknown mode: {mode}")
    
    # Get unique layers
    unique_layers = list(set(resampled_layers))
    
    # Create new network with edges from selected layers only
    new_graph = multinet.multi_layer_network(
        directed=graph.directed,
        verbose=False
    )
    
    edges = []
    for edge_data in graph.get_edges(data=True):
        if len(edge_data) == 3:
            u, v, data = edge_data
            if isinstance(u, tuple) and isinstance(v, tuple):
                source, source_layer = u
                target, target_layer = v
                # Keep edge if both layers are in resampled set
                if source_layer in unique_layers and target_layer in unique_layers:
                    weight = data.get('weight', 1.0)
                    edges.append([source, source_layer, target, target_layer, weight])
    
    if edges:
        new_graph.add_edges(edges, input_type="list")
    
    return new_graph
