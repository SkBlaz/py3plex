"""Community ensemble generation for uncertainty quantification.

This module provides functions to generate ensembles of community partitions
using different resampling strategies (SEED, PERTURBATION, BOOTSTRAP).

The ensemble can then be wrapped in a CommunityDistribution for analysis.

Examples
--------
>>> from py3plex.uncertainty import generate_community_ensemble
>>> from py3plex.core import multinet
>>> 
>>> # Create network
>>> net = multinet.multi_layer_network(directed=False)
>>> # ... add nodes/edges ...
>>> 
>>> # Generate ensemble with multiple seeds
>>> dist = generate_community_ensemble(
...     net,
...     algorithm='louvain',
...     method='seed',
...     n_samples=50,
...     seed=42
... )
>>> 
>>> # Generate ensemble with perturbation
>>> dist = generate_community_ensemble(
...     net,
...     algorithm='louvain',
...     method='perturbation',
...     n_samples=50,
...     perturbation_rate=0.1,
...     seed=42
... )
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple
import warnings

import numpy as np
import networkx as nx

from .partition import CommunityDistribution, partition_dict_to_array
from .resampling_graph import perturb_network_edges, bootstrap_network_edges
from py3plex.exceptions import AlgorithmError


def generate_community_ensemble(
    network: Any,
    algorithm: str = 'louvain',
    method: str = 'seed',
    n_samples: int = 50,
    seed: Optional[int] = None,
    perturbation_rate: float = 0.1,
    bootstrap_unit: str = 'edges',
    algorithm_params: Optional[Dict[str, Any]] = None,
    n_jobs: int = 1,
    verbose: bool = False,
) -> CommunityDistribution:
    """Generate an ensemble of community partitions with UQ.
    
    This is the main entry point for probabilistic community detection.
    It generates multiple partitions using the specified resampling strategy
    and returns a CommunityDistribution for analysis.
    
    Parameters
    ----------
    network : multi_layer_network
        The network to analyze.
    algorithm : str, default='louvain'
        Community detection algorithm. Supported:
        - 'louvain': Louvain modularity optimization
        - 'label_propagation': Label propagation
        - 'infomap': Infomap (requires infomap package)
    method : str, default='seed'
        Resampling method for uncertainty estimation:
        - 'seed': Run algorithm with different random seeds (Monte Carlo)
        - 'perturbation': Perturb edges before each run
        - 'bootstrap': Bootstrap resample nodes or edges
    n_samples : int, default=50
        Number of partitions to generate in the ensemble.
    seed : int, optional
        Base random seed for reproducibility. If provided, generates
        deterministic sequence of seeds for parallel runs.
    perturbation_rate : float, default=0.1
        For method='perturbation': fraction of edges to perturb (0.0 to 1.0).
    bootstrap_unit : str, default='edges'
        For method='bootstrap': what to resample ('edges', 'nodes', 'layers').
    algorithm_params : dict, optional
        Additional parameters to pass to the community detection algorithm.
    n_jobs : int, default=1
        Number of parallel jobs. Currently not implemented (sequential).
    verbose : bool, default=False
        If True, print progress information.
    
    Returns
    -------
    CommunityDistribution
        Distribution over community partitions with metadata.
    
    Raises
    ------
    AlgorithmError
        If algorithm or method is not supported, or if n_samples < 1.
    
    Examples
    --------
    >>> from py3plex.uncertainty import generate_community_ensemble
    >>> from py3plex.core import multinet
    >>> 
    >>> net = multinet.multi_layer_network(directed=False)
    >>> # ... create network ...
    >>> 
    >>> # Seed-based ensemble (pure algorithmic stochasticity)
    >>> dist = generate_community_ensemble(
    ...     net, algorithm='louvain', method='seed',
    ...     n_samples=100, seed=42
    ... )
    >>> 
    >>> # Perturbation-based ensemble (structural uncertainty)
    >>> dist = generate_community_ensemble(
    ...     net, algorithm='louvain', method='perturbation',
    ...     n_samples=50, perturbation_rate=0.05, seed=42
    ... )
    >>> 
    >>> # Get probabilistic result
    >>> from py3plex.uncertainty import ProbabilisticCommunityResult
    >>> result = ProbabilisticCommunityResult(dist)
    >>> labels = result.labels
    >>> probs = result.probs
    >>> entropy = result.entropy
    """
    # Validate inputs
    if n_samples < 1:
        raise AlgorithmError(
            f"n_samples must be >= 1, got {n_samples}",
            suggestions=["Use n_samples >= 50 for meaningful uncertainty estimates"]
        )
    
    if method not in ['seed', 'perturbation', 'bootstrap']:
        raise AlgorithmError(
            f"Unknown resampling method: {method}",
            suggestions=["Use 'seed', 'perturbation', or 'bootstrap'"]
        )
    
    # Get algorithm function
    algorithm_fn = _get_community_algorithm(algorithm)
    algorithm_params = algorithm_params or {}
    
    # Generate seed sequence for reproducibility
    if seed is not None:
        rng = np.random.default_rng(seed)
        seeds = rng.integers(0, 2**31 - 1, size=n_samples)
    else:
        seeds = [None] * n_samples
    
    # Generate partitions
    partitions = []
    modularity_scores = []  # Track quality scores if available
    
    if verbose:
        print(f"Generating {n_samples} partitions using method={method}...")
    
    for i in range(n_samples):
        if verbose and (i + 1) % 10 == 0:
            print(f"  Progress: {i + 1}/{n_samples}")
        
        # Get network variant based on resampling method
        if method == 'seed':
            # Use original network, different seed
            net_variant = network
            run_seed = seeds[i]
        
        elif method == 'perturbation':
            # Perturb network structure
            net_variant = _perturb_network(
                network,
                perturbation_rate=perturbation_rate,
                seed=seeds[i]
            )
            run_seed = seeds[i]
        
        elif method == 'bootstrap':
            # Bootstrap resample network
            net_variant = _bootstrap_network(
                network,
                unit=bootstrap_unit,
                seed=seeds[i]
            )
            run_seed = seeds[i]
        
        else:
            raise AlgorithmError(f"Unknown method: {method}")
        
        # Run community detection
        try:
            partition_dict, quality_score = algorithm_fn(
                net_variant,
                seed=run_seed,
                **algorithm_params
            )
            
            if quality_score is not None:
                modularity_scores.append(quality_score)
        
        except Exception as e:
            warnings.warn(
                f"Community detection failed for sample {i+1}/{n_samples}: {e}. "
                f"Skipping this sample.",
                stacklevel=2
            )
            continue
        
        # Convert to array format
        # Need canonical node ordering
        if i == 0:
            # Establish canonical ordering from first partition
            nodes_list = sorted(partition_dict.keys())
        
        partition_array = partition_dict_to_array(partition_dict, nodes_list)
        partitions.append(partition_array)
    
    if len(partitions) == 0:
        raise AlgorithmError(
            "No valid partitions generated. All runs failed.",
            suggestions=[
                "Check network connectivity",
                "Verify algorithm parameters",
                "Try different algorithm"
            ]
        )
    
    if verbose:
        print(f"Successfully generated {len(partitions)} partitions")
    
    # Create weights from modularity scores if available
    if len(modularity_scores) == len(partitions) and len(modularity_scores) > 0:
        # Use modularity as weights (higher is better)
        weights = np.array(modularity_scores, dtype=float)
        # Convert to probabilities (softmax-like)
        if np.max(weights) > np.min(weights):
            weights = weights - np.min(weights)
            weights = np.exp(weights / (np.max(weights) + 1e-10))
            weights = weights / np.sum(weights)
        else:
            weights = None  # Uniform weights
    else:
        weights = None
    
    # Create metadata
    meta = {
        'method': method,
        'algorithm': algorithm,
        'n_runs': len(partitions),
        'n_requested': n_samples,
        'resampling': method,
        'seed': seed,
        'perturbation_rate': perturbation_rate if method == 'perturbation' else None,
        'bootstrap_unit': bootstrap_unit if method == 'bootstrap' else None,
        'algorithm_params': algorithm_params,
    }
    
    # Create CommunityDistribution
    dist = CommunityDistribution(
        partitions=partitions,
        nodes=nodes_list,
        weights=weights,
        meta=meta
    )
    
    return dist


def _get_community_algorithm(algorithm: str) -> Callable:
    """Get community detection algorithm function.
    
    Returns a function that takes (network, seed, **params) and returns
    (partition_dict, quality_score).
    """
    if algorithm == 'louvain':
        return _run_louvain
    elif algorithm == 'label_propagation':
        return _run_label_propagation
    elif algorithm == 'infomap':
        return _run_infomap
    else:
        raise AlgorithmError(
            f"Unknown community detection algorithm: {algorithm}",
            algorithm_name=algorithm,
            valid_algorithms=['louvain', 'label_propagation', 'infomap']
        )


def _run_louvain(
    network: Any,
    seed: Optional[int] = None,
    resolution: float = 1.0,
    **kwargs
) -> Tuple[Dict[Any, int], Optional[float]]:
    """Run Louvain community detection.
    
    Returns
    -------
    partition_dict : dict
        Mapping from (node, layer) to community ID.
    modularity : float
        Modularity score.
    """
    try:
        from py3plex.algorithms.community_detection.community_louvain import (
            best_partition,
            modularity as compute_modularity
        )
    except ImportError:
        raise AlgorithmError(
            "Louvain algorithm requires python-louvain package",
            suggestions=["Install with: pip install python-louvain"]
        )
    
    # Get core network
    G = network.core_network
    
    # Convert to simple graph if MultiGraph
    if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
        simple_G = nx.Graph()
        for u, v, data in G.edges(data=True):
            if simple_G.has_edge(u, v):
                existing_weight = simple_G[u][v].get('weight', 1)
                new_weight = data.get('weight', 1)
                simple_G[u][v]['weight'] = max(existing_weight, new_weight)
            else:
                simple_G.add_edge(u, v, weight=data.get('weight', 1))
        G = simple_G
    
    # Run Louvain
    if seed is not None:
        # Louvain is stochastic but doesn't accept seed parameter directly
        # We set numpy random seed (Louvain uses numpy internally)
        np.random.seed(seed)
    
    partition = best_partition(G, resolution=resolution, **kwargs)
    
    # Compute modularity
    try:
        mod = compute_modularity(partition, G)
    except:
        mod = None
    
    return partition, mod


def _run_label_propagation(
    network: Any,
    seed: Optional[int] = None,
    **kwargs
) -> Tuple[Dict[Any, int], None]:
    """Run label propagation algorithm.
    
    Returns
    -------
    partition_dict : dict
        Mapping from (node, layer) to community ID.
    quality : None
        Label propagation doesn't have a quality score.
    """
    G = network.core_network
    
    # Convert to simple graph if needed
    if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
        simple_G = nx.Graph()
        for u, v, data in G.edges(data=True):
            if not simple_G.has_edge(u, v):
                simple_G.add_edge(u, v, weight=data.get('weight', 1))
        G = simple_G
    
    # Label propagation is in NetworkX
    if seed is not None:
        # Set seed for reproducibility
        import random
        random.seed(seed)
        np.random.seed(seed)
    
    communities_gen = nx.algorithms.community.label_propagation_communities(G)
    communities = list(communities_gen)
    
    # Convert to partition dict
    partition = {}
    for comm_id, community in enumerate(communities):
        for node in community:
            partition[node] = comm_id
    
    return partition, None


def _run_infomap(
    network: Any,
    seed: Optional[int] = None,
    **kwargs
) -> Tuple[Dict[Any, int], Optional[float]]:
    """Run Infomap algorithm.
    
    Returns
    -------
    partition_dict : dict
        Mapping from (node, layer) to community ID.
    codelength : float
        Infomap codelength (lower is better).
    """
    try:
        import infomap
    except ImportError:
        raise AlgorithmError(
            "Infomap algorithm requires infomap package",
            suggestions=["Install with: pip install infomap"]
        )
    
    G = network.core_network
    
    # Create Infomap object
    if seed is not None:
        im = infomap.Infomap(f"--seed {seed}")
    else:
        im = infomap.Infomap()
    
    # Add network
    for u, v, data in G.edges(data=True):
        weight = data.get('weight', 1.0)
        im.add_link(u, v, weight)
    
    # Run
    im.run()
    
    # Extract partition
    partition = {}
    for node in im.tree:
        if node.is_leaf:
            partition[node.node_id] = node.module_id
    
    codelength = im.codelength
    
    return partition, codelength


def _perturb_network(
    network: Any,
    perturbation_rate: float,
    seed: Optional[int] = None
) -> Any:
    """Create perturbed variant of network.
    
    Parameters
    ----------
    network : multi_layer_network
        Original network.
    perturbation_rate : float
        Fraction of edges to perturb (add/remove).
    seed : int, optional
        Random seed.
    
    Returns
    -------
    multi_layer_network
        Perturbed network (copy).
    """
    # Create a copy of the network
    from py3plex.core import multinet
    
    # Get edges - format is ((source, source_layer), (target, target_layer))
    edges = list(network.get_edges())
    
    # Perturb
    rng = np.random.default_rng(seed)
    n_perturb = max(1, int(len(edges) * perturbation_rate))
    
    # Remove random edges
    edges_to_remove = rng.choice(len(edges), size=min(n_perturb, len(edges)), replace=False)
    remaining_edges = [e for i, e in enumerate(edges) if i not in edges_to_remove]
    
    # Create new network
    net_new = multinet.multi_layer_network(directed=network.directed)
    
    # Add nodes
    nodes = list(network.get_nodes())
    net_new.add_nodes([{'source': n[0], 'type': n[1]} for n in nodes])
    
    # Add remaining edges
    for edge in remaining_edges:
        (source, source_type), (target, target_type) = edge
        net_new.add_edges([{
            'source': source,
            'target': target,
            'source_type': source_type,
            'target_type': target_type,
            'weight': 1.0
        }])
    
    # Add new random edges (same number as removed)
    node_list = list(nodes)
    for _ in range(n_perturb):
        if len(node_list) < 2:
            break
        # Random pair
        idx1, idx2 = rng.choice(len(node_list), size=2, replace=False)
        n1, n2 = node_list[idx1], node_list[idx2]
        
        # Add edge if not exists
        if not net_new.core_network.has_edge(n1, n2):
            net_new.add_edges([{
                'source': n1[0],
                'target': n2[0],
                'source_type': n1[1],
                'target_type': n2[1],
                'weight': 1.0
            }])
    
    return net_new


def _bootstrap_network(
    network: Any,
    unit: str,
    seed: Optional[int] = None
) -> Any:
    """Create bootstrap sample of network.
    
    Parameters
    ----------
    network : multi_layer_network
        Original network.
    unit : str
        What to resample: 'edges', 'nodes', or 'layers'.
    seed : int, optional
        Random seed.
    
    Returns
    -------
    multi_layer_network
        Bootstrap network (resampled).
    """
    from py3plex.core import multinet
    
    rng = np.random.default_rng(seed)
    
    if unit == 'edges':
        # Resample edges with replacement
        edges = list(network.get_edges())
        n_edges = len(edges)
        sampled_indices = rng.choice(n_edges, size=n_edges, replace=True)
        sampled_edges = [edges[i] for i in sampled_indices]
        
        # Create new network
        net_new = multinet.multi_layer_network(directed=network.directed)
        
        # Add all nodes
        nodes = list(network.get_nodes())
        net_new.add_nodes([{'source': n[0], 'type': n[1]} for n in nodes])
        
        # Add sampled edges
        for edge in sampled_edges:
            (source, source_type), (target, target_type) = edge
            net_new.add_edges([{
                'source': source,
                'target': target,
                'source_type': source_type,
                'target_type': target_type,
                'weight': 1.0
            }])
        
        return net_new
    
    elif unit == 'nodes':
        # Resample nodes with replacement
        nodes = list(network.get_nodes())
        n_nodes = len(nodes)
        sampled_indices = rng.choice(n_nodes, size=n_nodes, replace=True)
        sampled_nodes = [nodes[i] for i in sampled_indices]
        sampled_node_set = set(sampled_nodes)
        
        # Create new network
        net_new = multinet.multi_layer_network(directed=network.directed)
        
        # Add sampled nodes
        net_new.add_nodes([{'source': n[0], 'type': n[1]} for n in sampled_nodes])
        
        # Add edges between sampled nodes
        edges = list(network.get_edges())
        for edge in edges:
            (source, source_type), (target, target_type) = edge
            if (source, source_type) in sampled_node_set and (target, target_type) in sampled_node_set:
                net_new.add_edges([{
                    'source': source,
                    'target': target,
                    'source_type': source_type,
                    'target_type': target_type,
                    'weight': 1.0
                }])
        
        return net_new
    
    else:
        raise AlgorithmError(
            f"Unknown bootstrap unit: {unit}",
            suggestions=["Use 'edges' or 'nodes'"]
        )
