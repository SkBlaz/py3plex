"""Robustness-oriented centrality analysis for multilayer networks.

This module provides centrality measures that quantify how important nodes or
layers are for global connectivity or dynamics based on removal impact.

The core idea is to measure robustness centrality as:
    R(node) = baseline_metric - metric_after_removal(node)

where the metric can be:
    - size of largest connected component
    - average shortest path length
    - final epidemic size or prevalence in a standard SIS/SIR run
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Union
import warnings

import networkx as nx
import numpy as np

from py3plex.core import multinet
from py3plex.dynamics import D, SIS, SIR
from py3plex.dynamics.errors import DynamicsError
from py3plex.exceptions import Py3plexException


def robustness_centrality(
    graph: multinet.multi_layer_network,
    target: str = "node",
    metric: str = "giant_component",
    sample_nodes: Optional[Iterable] = None,
    sample_layers: Optional[Iterable] = None,
    dynamics_params: Optional[dict] = None,
    seed: Optional[int] = None,
) -> Dict[Any, float]:
    """Compute robustness centrality profile for nodes or layers.

    For each target (node or layer), computes how much its removal disrupts
    the network according to the chosen metric.

    Parameters
    ----------
    graph : multi_layer_network
        The multilayer network to analyze.
    target : str, default="node"
        What to measure robustness of: "node" or "layer".
    metric : str, default="giant_component"
        The metric to use for measuring impact:
        - "giant_component": size of largest connected component
        - "avg_shortest_path": average shortest path length
        - "sis_final_prevalence": prevalence after SIS dynamics run
        - "sir_final_size": final number of recovered in SIR dynamics
    sample_nodes : Iterable, optional
        Optional subset of nodes to measure (for speed). If None, measures all nodes.
    sample_layers : Iterable, optional
        Optional subset of layers to measure (for speed). If None, measures all layers.
    dynamics_params : dict, optional
        Parameters passed to dynamics models when metric involves simulations.
        For "sis_final_prevalence": {"beta": 0.3, "mu": 0.1, "steps": 100}
        For "sir_final_size": {"beta": 0.2, "gamma": 0.05, "steps": 100}
    seed : int, optional
        Random seed for reproducibility (especially for dynamics-based metrics).

    Returns
    -------
    Dict[target_id, float]
        Dictionary mapping each target (node or layer) to its robustness score.
        Higher score means more critical (removal causes more disruption).

    Examples
    --------
    >>> from py3plex.core import multinet
    >>> from py3plex.centrality import robustness_centrality
    >>> 
    >>> net = multinet.multi_layer_network(directed=False)
    >>> edges = [["a", "L0", "b", "L0", 1.0], ["b", "L0", "c", "L0", 1.0]]
    >>> net.add_edges(edges, input_type="list")
    >>> 
    >>> # Measure node robustness based on giant component
    >>> scores = robustness_centrality(net, target="node", metric="giant_component")
    >>> print(scores[("b", "L0")])  # Node b is a bridge
    
    >>> # Measure layer robustness
    >>> scores = robustness_centrality(net, target="layer", metric="giant_component")

    Notes
    -----
    - The function computes the baseline metric once on the full graph.
    - For each target, it removes the target, recomputes the metric, and takes
      the difference: baseline - perturbed.
    - For dynamics metrics, it runs a simulation with fixed seed and parameters.
    - Each metric computation uses a fresh random state to ensure independence.
    """
    # Validate inputs
    if target not in ("node", "layer"):
        raise Py3plexException(
            f"Invalid target type: '{target}'",
            suggestions=[
                "Use target='node' to measure node robustness",
                "Use target='layer' to measure layer robustness"
            ],
            did_you_mean="node" if target.lower().startswith("n") else "layer"
        )
    
    valid_metrics = [
        "giant_component",
        "avg_shortest_path",
        "sis_final_prevalence",
        "sir_final_size",
    ]
    if metric not in valid_metrics:
        from py3plex.errors import find_similar
        did_you_mean = find_similar(metric, valid_metrics)
        raise Py3plexException(
            f"Unknown robustness metric: '{metric}'",
            suggestions=[
                f"Valid metrics: {', '.join(valid_metrics)}",
                "Use 'giant_component' for connectivity-based robustness",
                "Use 'sis_final_prevalence' or 'sir_final_size' for dynamics-based robustness"
            ],
            did_you_mean=did_you_mean
        )

    # py3plex.core.multinet.multi_layer_network may keep `core_network=None` until
    # something is added. In that case the graph is effectively empty, and any
    # removal has zero impact.
    if getattr(graph, "core_network", None) is None or len(graph) == 0:
        if target == "node":
            targets = list(sample_nodes) if sample_nodes is not None else []
        else:
            targets = list(sample_layers) if sample_layers is not None else []
        return {t: 0.0 for t in targets}
    
    # Create base RNG
    base_rng = np.random.default_rng(seed)
    
    # Compute baseline metric (use a fresh seed for baseline)
    baseline_seed = int(base_rng.integers(0, 2**31))
    baseline_rng = np.random.default_rng(baseline_seed)
    baseline = _compute_metric(graph, metric, dynamics_params, baseline_rng)
    
    # Determine targets to measure
    if target == "node":
        if sample_nodes is not None:
            targets = list(sample_nodes)
        else:
            targets = list(graph.get_nodes())
    else:  # target == "layer"
        if sample_layers is not None:
            targets = list(sample_layers)
        else:
            # Extract unique layers from nodes
            layers = set()
            for node in graph.get_nodes():
                if isinstance(node, tuple) and len(node) >= 2:
                    layers.add(node[1])
            targets = sorted(layers)
    
    # Compute robustness for each target
    results = {}
    
    for tgt in targets:
        # Remove target and recompute metric
        if target == "node":
            perturbed = _remove_node(graph, tgt)
        else:  # target == "layer"
            perturbed = _remove_layer(graph, tgt)
        
        # Compute metric on perturbed network (use a fresh seed)
        perturbed_seed = int(base_rng.integers(0, 2**31))
        perturbed_rng = np.random.default_rng(perturbed_seed)
        perturbed_value = _compute_metric(perturbed, metric, dynamics_params, perturbed_rng)
        
        # Robustness is the impact: baseline - perturbed
        # For metrics where higher is better (giant_component), this is positive
        # For metrics where lower is better (avg_shortest_path), we need to invert
        if metric == "avg_shortest_path":
            # Lower path length is better, so impact is perturbed - baseline
            # Handle cases where both values are infinite to avoid NaN.
            if not np.isfinite(perturbed_value) and not np.isfinite(baseline):
                robustness = 0.0
            else:
                robustness = perturbed_value - baseline
        else:
            # Higher is better (giant_component, prevalence, final_size)
            if not np.isfinite(perturbed_value) and not np.isfinite(baseline):
                robustness = 0.0
            else:
                robustness = baseline - perturbed_value
        
        results[tgt] = float(robustness)
    
    return results


def _compute_metric(
    graph: multinet.multi_layer_network,
    metric: str,
    dynamics_params: Optional[dict],
    rng: np.random.Generator,
) -> float:
    """Compute the specified metric on a network.
    
    Parameters
    ----------
    graph : multi_layer_network
        The network to measure.
    metric : str
        The metric to compute.
    dynamics_params : dict or None
        Parameters for dynamics simulations.
    rng : np.random.Generator
        Random number generator for dynamics.
    
    Returns
    -------
    float
        The metric value.
    """
    if metric == "giant_component":
        return _compute_giant_component(graph)
    elif metric == "avg_shortest_path":
        return _compute_avg_shortest_path(graph)
    elif metric == "sis_final_prevalence":
        return _compute_sis_prevalence(graph, dynamics_params, rng)
    elif metric == "sir_final_size":
        return _compute_sir_final_size(graph, dynamics_params, rng)
    else:
        # This should never happen if validation is correct
        raise Py3plexException(f"Unimplemented metric: {metric}")


def _compute_giant_component(graph: multinet.multi_layer_network) -> float:
    """Compute size of the largest connected component.
    
    Parameters
    ----------
    graph : multi_layer_network
        The network to measure.
    
    Returns
    -------
    float
        Size of the largest connected component (number of nodes).
    """
    G = getattr(graph, "core_network", None)
    if G is None:
        return 0.0
    
    if len(G) == 0:
        return 0.0
    
    if G.is_directed():
        components = list(nx.weakly_connected_components(G))
    else:
        components = list(nx.connected_components(G))
    
    if not components:
        return 0.0
    
    return float(max(len(c) for c in components))


def _compute_avg_shortest_path(graph: multinet.multi_layer_network) -> float:
    """Compute average shortest path length.
    
    For disconnected graphs, computes the average over connected pairs only.
    Returns infinity if graph is empty or has no connected pairs.
    
    Parameters
    ----------
    graph : multi_layer_network
        The network to measure.
    
    Returns
    -------
    float
        Average shortest path length, or float('inf') if not computable.
    
    Notes
    -----
    For very large components (>1000 nodes), this can be expensive. Consider
    using sampling or approximation methods for large networks.
    """
    G = getattr(graph, "core_network", None)
    if G is None:
        return float("inf")
    
    if len(G) == 0:
        return float('inf')
    
    # For disconnected graphs, compute average over each component
    if G.is_directed():
        components = list(nx.weakly_connected_components(G))
    else:
        components = list(nx.connected_components(G))
    
    if not components:
        return float('inf')
    
    total_length = 0.0
    total_pairs = 0
    
    for comp in components:
        if len(comp) < 2:
            continue
        
        # Skip very large components for performance
        if len(comp) > 1000:
            warnings.warn(
                f"Skipping large component with {len(comp)} nodes for performance. "
                "Consider using sampling for large networks.",
                RuntimeWarning
            )
            continue
        
        subgraph = G.subgraph(comp)
        try:
            # Use average_shortest_path_length for each component
            avg_len = nx.average_shortest_path_length(subgraph)
            n = len(comp)
            n_pairs = n * (n - 1)
            total_length += avg_len * n_pairs
            total_pairs += n_pairs
        except nx.NetworkXError:
            # Disconnected within component or other error
            continue
    
    if total_pairs == 0:
        return float('inf')
    
    return total_length / total_pairs


def _compute_sis_prevalence(
    graph: multinet.multi_layer_network,
    dynamics_params: Optional[dict],
    rng: np.random.Generator,
) -> float:
    """Compute final prevalence after SIS dynamics simulation.
    
    Parameters
    ----------
    graph : multi_layer_network
        The network to simulate on.
    dynamics_params : dict or None
        Parameters: {"beta": 0.3, "mu": 0.1, "steps": 100}
    rng : np.random.Generator
        Random number generator.
    
    Returns
    -------
    float
        Final prevalence (fraction of infected nodes).
    """
    # Default parameters
    params = {
        "beta": 0.3,
        "mu": 0.1,
        "steps": 100,
        "initial_infected": 0.01,
    }
    if dynamics_params:
        params.update(dynamics_params)
    
    try:
        # Build simulation
        sim = (
            D.process(SIS(beta=params["beta"], mu=params["mu"]))
            .initial(infected=params["initial_infected"])
            .steps(params["steps"])
            .measure("prevalence")
            .replicates(1)
            .seed(int(rng.integers(0, 2**31)))
        )
        
        # Run simulation
        result = sim.run(graph)
        
        # Get final prevalence (last time step)
        data = result.data
        if "prevalence" in data and len(data["prevalence"]) > 0:
            # Shape is (replicates, steps)
            final_prevalence = float(data["prevalence"][0, -1])
            return final_prevalence
        else:
            return 0.0
    except (DynamicsError, ValueError, KeyError) as e:
        # If simulation fails (e.g., empty network), return 0
        warnings.warn(f"SIS simulation failed: {e}", RuntimeWarning)
        return 0.0


def _compute_sir_final_size(
    graph: multinet.multi_layer_network,
    dynamics_params: Optional[dict],
    rng: np.random.Generator,
) -> float:
    """Compute final recovered (epidemic size) after SIR dynamics simulation.
    
    Parameters
    ----------
    graph : multi_layer_network
        The network to simulate on.
    dynamics_params : dict or None
        Parameters: {"beta": 0.2, "gamma": 0.05, "steps": 200}
    rng : np.random.Generator
        Random number generator.
    
    Returns
    -------
    float
        Final fraction of recovered nodes.
    """
    # Default parameters
    params = {
        "beta": 0.2,
        "gamma": 0.05,
        "steps": 200,
        "initial_infected": 0.01,
    }
    if dynamics_params:
        params.update(dynamics_params)
    
    try:
        # Build simulation - use state_counts to get R count
        sim = (
            D.process(SIR(beta=params["beta"], gamma=params["gamma"]))
            .initial(infected=params["initial_infected"])
            .steps(params["steps"])
            .measure("state_counts")
            .replicates(1)
            .seed(int(rng.integers(0, 2**31)))
        )
        
        # Run simulation
        result = sim.run(graph)
        
        # Get final recovered fraction (last time step)
        # state_counts returns dict with state -> count
        data = result.data
        if "state_counts" in data and len(data["state_counts"]) > 0:
            # Shape is (replicates, steps)
            # Each element is a dict
            final_counts = data["state_counts"][0, -1]
            # State 2 is recovered in SIR
            total_nodes = sum(final_counts.values())
            if total_nodes > 0:
                recovered_count = final_counts.get(2, 0)
                return float(recovered_count) / float(total_nodes)
        return 0.0
    except (DynamicsError, ValueError, KeyError) as e:
        # If simulation fails (e.g., empty network), return 0
        warnings.warn(f"SIR simulation failed: {e}", RuntimeWarning)
        return 0.0


def _remove_node(
    graph: multinet.multi_layer_network,
    node: Any,
) -> multinet.multi_layer_network:
    """Remove a node from the network.
    
    Creates a new network without the specified node and its incident edges.
    
    Parameters
    ----------
    graph : multi_layer_network
        The original network.
    node : Any
        The node to remove.
    
    Returns
    -------
    multi_layer_network
        New network with the node removed.
    """
    new_net = multinet.multi_layer_network(
        directed=graph.directed,
        network_type=graph.network_type,
        verbose=False,
    )
    
    new_net._initiate_network()
    
    # Copy all edges except those incident to the removed node
    edges_to_add = []
    for edge in graph.get_edges(data=True):
        source_node, target_node = edge[0], edge[1]
        edge_data = edge[2] if len(edge) > 2 else {}
        
        # Skip edges incident to the removed node
        if source_node == node or target_node == node:
            continue
        
        weight = edge_data.get("weight", 1.0)
        edges_to_add.append([
            source_node[0], source_node[1],
            target_node[0], target_node[1],
            weight,
        ])
    
    if edges_to_add:
        new_net.add_edges(edges_to_add, input_type="list")
    
    # Also preserve isolated nodes (except the removed one)
    nodes_in_edges = set()
    for edge in edges_to_add:
        nodes_in_edges.add((edge[0], edge[1]))
        nodes_in_edges.add((edge[2], edge[3]))
    
    for n in graph.get_nodes():
        if n != node and n not in nodes_in_edges:
            new_net.core_network.add_node(n)
    
    return new_net


def _remove_layer(
    graph: multinet.multi_layer_network,
    layer: str,
) -> multinet.multi_layer_network:
    """Remove all nodes and edges in a specific layer.
    
    Creates a new network without the specified layer.
    
    Parameters
    ----------
    graph : multi_layer_network
        The original network.
    layer : str
        The layer to remove.
    
    Returns
    -------
    multi_layer_network
        New network with the layer removed.
    """
    new_net = multinet.multi_layer_network(
        directed=graph.directed,
        network_type=graph.network_type,
        verbose=False,
    )
    
    new_net._initiate_network()
    
    # Copy all edges except those in the removed layer
    edges_to_add = []
    for edge in graph.get_edges(data=True):
        source_node, target_node = edge[0], edge[1]
        edge_data = edge[2] if len(edge) > 2 else {}
        
        # Check if edge is in the removed layer
        source_layer = source_node[1] if isinstance(source_node, tuple) else None
        target_layer = target_node[1] if isinstance(target_node, tuple) else None
        
        if source_layer == layer or target_layer == layer:
            continue
        
        weight = edge_data.get("weight", 1.0)
        edges_to_add.append([
            source_node[0], source_node[1],
            target_node[0], target_node[1],
            weight,
        ])
    
    if edges_to_add:
        new_net.add_edges(edges_to_add, input_type="list")
    
    # Also preserve isolated nodes (except those in the removed layer)
    nodes_in_edges = set()
    for edge in edges_to_add:
        nodes_in_edges.add((edge[0], edge[1]))
        nodes_in_edges.add((edge[2], edge[3]))
    
    for n in graph.get_nodes():
        node_layer = n[1] if isinstance(n, tuple) else None
        if node_layer != layer and n not in nodes_in_edges:
            new_net.core_network.add_node(n)
    
    return new_net
