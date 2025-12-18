"""Null model engine for statistical significance testing.

This module provides utilities for generating null models of multilayer networks
and computing z-scores and p-values for observed metrics.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
import copy

import numpy as np
import networkx as nx

from py3plex.core import multinet


def null_model_metric(
    graph: multinet.multi_layer_network,
    metric_fn: Callable[[multinet.multi_layer_network], Dict[Any, float]],
    n_null: int = 200,
    model: str = "degree_preserving",
    random_state: Optional[int] = None,
) -> Dict[str, np.ndarray]:
    """Compute metric on null models for statistical significance testing.
    
    This function generates null models of the network (e.g., via degree-preserving
    rewiring) and computes the metric on each null network. It then computes
    z-scores and p-values for the observed metric values.
    
    Parameters
    ----------
    graph : multi_layer_network
        The multilayer network to analyze.
    metric_fn : callable
        Function that takes a network and returns a dict mapping items (usually
        nodes) to metric values. Must have signature:
        metric_fn(network) -> Dict[item_id, float]
    n_null : int, default=200
        Number of null model replicates to generate.
    model : str, default="degree_preserving"
        Null model type:
        - "degree_preserving": Rewire edges while preserving degree sequence
        - "erdos_renyi": Random graph with same density
        - "configuration": Configuration model matching degree distribution
    random_state : int, optional
        Random seed for reproducibility.
    
    Returns
    -------
    dict
        Dictionary with keys:
        - "observed": np.ndarray of shape (n_items,) with observed metric values
        - "mean_null": np.ndarray of shape (n_items,) with mean null values
        - "std_null": np.ndarray of shape (n_items,) with std of null values
        - "zscore": np.ndarray of shape (n_items,) with z-scores
        - "pvalue": np.ndarray of shape (n_items,) with two-tailed p-values
        - "index": List of item IDs
        - "n_null": Number of null replicates used
        - "model": String describing the null model
    
    Examples
    --------
    >>> from py3plex.core import multinet
    >>> from py3plex.uncertainty.null_models import null_model_metric
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
    >>> # Compute null model statistics
    >>> null_result = null_model_metric(
    ...     net, degree_metric, n_null=100, model="degree_preserving"
    ... )
    >>> null_result["zscore"]  # Z-scores for each node
    >>> null_result["pvalue"]  # P-values for each node
    
    Notes
    -----
    - Z-scores indicate how many standard deviations the observed value is from
      the null distribution mean
    - P-values are two-tailed by default: P(|Z| >= |Z_observed|) under the null.
      For one-tailed tests, users can compute p_one_sided = p_two_sided / 2 and
      check the sign of z-score to determine the direction.
    - High |z-score| and low p-value indicate statistical significance
    """
    rng = np.random.default_rng(random_state)
    
    # Compute observed metric
    observed_result = metric_fn(graph)
    if not isinstance(observed_result, dict):
        raise TypeError(
            "metric_fn must return a dict mapping items to values. "
            f"Got {type(observed_result)}"
        )
    
    # Handle empty result
    if not observed_result:
        return {
            "observed": np.array([]),
            "mean_null": np.array([]),
            "std_null": np.array([]),
            "zscore": np.array([]),
            "pvalue": np.array([]),
            "index": [],
            "n_null": n_null,
            "model": model,
        }
    
    # Get sorted list of items for consistent indexing
    index = sorted(observed_result.keys(), key=lambda x: str(x))
    n_items = len(index)
    
    # Convert observed to array
    observed = np.array([observed_result[item] for item in index])
    
    # Pre-allocate array for null samples: (n_null, n_items)
    null_samples = np.zeros((n_null, n_items))
    
    # Generate null models and compute metrics
    for i in range(n_null):
        # Generate null model
        if model == "degree_preserving":
            null_graph = _generate_degree_preserving_null(graph, rng)
        elif model == "erdos_renyi":
            null_graph = _generate_erdos_renyi_null(graph, rng)
        elif model == "configuration":
            null_graph = _generate_configuration_null(graph, rng)
        else:
            raise ValueError(
                f"Unknown null model: {model}. "
                "Must be 'degree_preserving', 'erdos_renyi', or 'configuration'"
            )
        
        # Compute metric on null model
        try:
            null_result = metric_fn(null_graph)
        except Exception:
            # If metric fails on this null model, use zeros
            null_result = {item: 0.0 for item in index}
        
        # Fill in values (use 0 for missing items)
        for j, item in enumerate(index):
            null_samples[i, j] = null_result.get(item, 0.0)
    
    # Compute null statistics
    mean_null = np.mean(null_samples, axis=0)
    # For a single replicate, ddof=1 yields NaNs; treat as 0 variability.
    ddof = 1 if n_null > 1 else 0
    std_null = np.std(null_samples, axis=0, ddof=ddof)
    
    # Compute z-scores (handle zero std)
    with np.errstate(divide='ignore', invalid='ignore'):
        zscore = (observed - mean_null) / std_null
        zscore = np.where(std_null == 0, 0.0, zscore)
    
    # Compute two-tailed p-values
    # P(|Z| >= |Z_observed|) = 2 * P(Z >= |Z_observed|) for symmetric distribution
    # Use empirical p-value: fraction of null samples more extreme than observed
    pvalue = np.zeros(n_items)
    for j in range(n_items):
        obs_val = observed[j]
        null_vals = null_samples[:, j]
        
        # Two-tailed: count how many null values are as extreme or more extreme
        n_more_extreme = np.sum(np.abs(null_vals - mean_null[j]) >= np.abs(obs_val - mean_null[j]))
        pvalue[j] = (n_more_extreme + 1) / (n_null + 1)  # Add 1 to avoid p=0
    
    return {
        "observed": observed,
        "mean_null": mean_null,
        "std_null": std_null,
        "zscore": zscore,
        "pvalue": pvalue,
        "index": index,
        "n_null": n_null,
        "model": model,
    }


def _generate_degree_preserving_null(
    graph: multinet.multi_layer_network,
    rng: np.random.Generator,
) -> multinet.multi_layer_network:
    """Generate a degree-preserving null model via edge rewiring.
    
    Parameters
    ----------
    graph : multi_layer_network
        Original network.
    rng : np.random.Generator
        Random number generator.
    
    Returns
    -------
    multi_layer_network
        Null model with same degree sequence but rewired edges.
    
    Notes
    -----
    Uses double-edge swap: repeatedly pick two edges (u1,v1) and (u2,v2),
    and rewire them to (u1,v2) and (u2,v1) if this doesn't create self-loops
    or duplicate edges.
    """
    # Create a new network with same properties
    null_graph = multinet.multi_layer_network(
        directed=graph.directed,
        verbose=False
    )
    
    # Get all edges
    edges = list(graph.get_edges(data=True))
    n_edges = len(edges)
    
    if n_edges == 0:
        return null_graph
    
    # Convert to list format for easier manipulation
    edge_list = []
    for edge_data in edges:
        if len(edge_data) == 3:
            u, v, data = edge_data
            if isinstance(u, tuple) and isinstance(v, tuple):
                source, source_layer = u
                target, target_layer = v
                weight = data.get('weight', 1.0)
                edge_list.append([source, source_layer, target, target_layer, weight])
    
    if not edge_list:
        return null_graph
    
    # Perform edge swaps (rewiring)
    # Number of swaps should be proportional to number of edges
    n_swaps = max(10, n_edges * 2)
    
    # Build edge set once for efficient duplicate checking
    edge_set = {(e[0], e[1], e[2], e[3]) for e in edge_list}
    
    for _ in range(n_swaps):
        # Pick two random edges
        if len(edge_list) < 2:
            break
        
        idx1, idx2 = rng.choice(len(edge_list), size=2, replace=False)
        edge1 = edge_list[idx1]
        edge2 = edge_list[idx2]
        
        # Extract components
        s1, l1, t1, tl1, w1 = edge1
        s2, l2, t2, tl2, w2 = edge2
        
        # Try to swap: (s1,t1) (s2,t2) -> (s1,t2) (s2,t1)
        # Only if no self-loops and within same layer constraints
        if (s1 != t2 and s2 != t1 and  # No self-loops
            l1 == tl2 and l2 == tl1):  # Layer compatibility
            
            # Create new edges
            new_edge1 = [s1, l1, t2, tl2, w1]
            new_edge2 = [s2, l2, t1, tl1, w2]
            
            # Check if these edges don't already exist (avoid duplicates)
            if ((s1, l1, t2, tl2) not in edge_set and
                (s2, l2, t1, tl1) not in edge_set):
                # Perform swap - update both list and set
                edge_list[idx1] = new_edge1
                edge_list[idx2] = new_edge2
                
                # Update edge set
                edge_set.discard((s1, l1, t1, tl1))
                edge_set.discard((s2, l2, t2, tl2))
                edge_set.add((s1, l1, t2, tl2))
                edge_set.add((s2, l2, t1, tl1))
    
    # Build null network from rewired edges
    if edge_list:
        null_graph.add_edges(edge_list, input_type="list")
    
    return null_graph


def _generate_erdos_renyi_null(
    graph: multinet.multi_layer_network,
    rng: np.random.Generator,
) -> multinet.multi_layer_network:
    """Generate an Erdős-Rényi null model with same density.
    
    Parameters
    ----------
    graph : multi_layer_network
        Original network.
    rng : np.random.Generator
        Random number generator.
    
    Returns
    -------
    multi_layer_network
        Null model with random edges at same density.
    """
    # Build node sets per layer from existing node-layer identifiers.
    nodes_by_layer: Dict[str, List[Any]] = {}
    for node in graph.get_nodes():
        if isinstance(node, tuple) and len(node) == 2:
            node_id, layer = node
            nodes_by_layer.setdefault(str(layer), []).append(node_id)
        else:
            nodes_by_layer.setdefault("default", []).append(node)

    # Deduplicate node IDs per layer (preserve stable iteration order).
    for layer, ids in list(nodes_by_layer.items()):
        seen = set()
        unique_ids = []
        for node_id in ids:
            if node_id in seen:
                continue
            seen.add(node_id)
            unique_ids.append(node_id)
        nodes_by_layer[layer] = unique_ids

    # Compute density using intra-layer edges only (this null model generates intra-layer edges).
    intra_edges = 0
    for edge in graph.get_edges(data=False):
        u, v = edge[:2]
        if isinstance(u, tuple) and isinstance(v, tuple) and len(u) == 2 and len(v) == 2:
            if u[1] == v[1]:
                intra_edges += 1

    total_max_edges = 0
    for layer, ids in nodes_by_layer.items():
        n = len(ids)
        if graph.directed:
            total_max_edges += n * (n - 1)
        else:
            total_max_edges += n * (n - 1) // 2

    if total_max_edges <= 0:
        return multinet.multi_layer_network(directed=graph.directed, verbose=False)

    p = intra_edges / total_max_edges
    p = float(np.clip(p, 0.0, 1.0))

    null_graph = multinet.multi_layer_network(directed=graph.directed, verbose=False)

    edges = []
    for layer, ids in nodes_by_layer.items():
        for i, u in enumerate(ids):
            start_j = i + 1 if not graph.directed else 0
            for j in range(start_j, len(ids)):
                v = ids[j]
                if u != v and rng.random() < p:
                    edges.append([u, layer, v, layer, 1.0])

    if edges:
        null_graph.add_edges(edges, input_type="list")

    return null_graph


def _generate_configuration_null(
    graph: multinet.multi_layer_network,
    rng: np.random.Generator,
) -> multinet.multi_layer_network:
    """Generate a configuration model null preserving degree distribution.
    
    Parameters
    ----------
    graph : multi_layer_network
        Original network.
    rng : np.random.Generator
        Random number generator.
    
    Returns
    -------
    multi_layer_network
        Null model matching degree distribution.
    
    Notes
    -----
    This is a simplified version that uses NetworkX's configuration model
    on the core network, then maps back to multilayer structure.
    """
    # Get the core network
    if not hasattr(graph, 'core_network') or graph.core_network is None:
        return multinet.multi_layer_network(
            directed=graph.directed,
            verbose=False
        )
    
    G = graph.core_network
    
    # Get degree sequence
    if graph.directed:
        in_degrees = [d for n, d in G.in_degree()]
        out_degrees = [d for n, d in G.out_degree()]
        # For simplicity, use degree-preserving rewiring
        return _generate_degree_preserving_null(graph, rng)
    else:
        degrees = [d for n, d in G.degree()]
        
        # Use NetworkX configuration model
        try:
            config_graph = nx.configuration_model(degrees, seed=int(rng.integers(0, 2**31)))
            # Remove self-loops and parallel edges
            config_graph = nx.Graph(config_graph)
            config_graph.remove_edges_from(nx.selfloop_edges(config_graph))
        except Exception:
            # Fall back to degree-preserving rewiring
            return _generate_degree_preserving_null(graph, rng)
        
        # Map back to multilayer network
        null_graph = multinet.multi_layer_network(
            directed=graph.directed,
            verbose=False
        )
        
        # Get original layer information
        try:
            layers_info = graph.get_layers()
            if isinstance(layers_info, tuple) and len(layers_info) >= 1:
                layer_names = layers_info[0]
                default_layer = layer_names[0] if layer_names else "L0"
            else:
                default_layer = "L0"
        except Exception:
            default_layer = "L0"
        
        # Add edges from configuration model
        edges = []
        node_list = list(G.nodes())
        for u, v in config_graph.edges():
            if u < len(node_list) and v < len(node_list):
                source = node_list[u]
                target = node_list[v]
                if isinstance(source, tuple) and len(source) == 2:
                    source_id, source_layer = source
                else:
                    source_id, source_layer = source, default_layer
                if isinstance(target, tuple) and len(target) == 2:
                    target_id, target_layer = target
                else:
                    target_id, target_layer = target, default_layer
                edges.append([source_id, source_layer, target_id, target_layer, 1.0])
        
        if edges:
            null_graph.add_edges(edges, input_type="list")
        
        return null_graph
