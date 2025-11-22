"""
Stability and robustness tests for multilayer networks.

Built-in methods for:
- Targeted node removal
- Random edge perturbation
- Layer-wise damage analysis
with visual plots.

These tools help analyze network resilience and identify critical components.

Authors: py3plex contributors
Date: 2025
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
import networkx as nx
from collections import defaultdict
import copy


def targeted_node_removal(
    network: Any,
    removal_strategy: str = "degree",
    num_removals: Optional[int] = None,
    fraction: float = 0.1,
    metrics: Optional[List[str]] = None
) -> Dict[str, List[float]]:
    """Test network robustness under targeted node removal.
    
    Removes nodes according to a strategy and tracks network properties.
    
    Args:
        network: Multilayer network object
        removal_strategy: Strategy for node selection:
            - 'degree': Remove highest degree nodes first
            - 'betweenness': Remove highest betweenness nodes first
            - 'random': Random removal
            - 'eigenvector': Remove highest eigenvector centrality nodes first
        num_removals: Number of nodes to remove (overrides fraction)
        fraction: Fraction of nodes to remove (default: 0.1)
        metrics: List of metrics to track ('size', 'diameter', 'clustering', 'efficiency')
        
    Returns:
        Dictionary mapping metric names to lists of values after each removal
        
    Algorithm:
        1. Compute node ranking according to strategy
        2. Remove nodes one by one in ranked order
        3. After each removal, compute network metrics
        4. Return metric trajectories
        
    Example:
        >>> net = load_network(...)
        >>> results = targeted_node_removal(net, 'degree', fraction=0.2)
        >>> print(results['size'])  # Size of largest component over time
        
    References:
        - Albert, R., et al. (2000). "Error and attack tolerance of complex
          networks." Nature, 406(6794), 378-382.
        - Buldyrev, S. V., et al. (2010). "Catastrophic cascade of failures in
          interdependent networks." Nature, 464(7291), 1025-1028.
    """
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise ValueError("Network has no core_network")
    
    if metrics is None:
        metrics = ['size', 'edges', 'components']
    
    G = network.core_network.copy()
    
    # Determine number of removals
    if num_removals is None:
        num_removals = int(G.number_of_nodes() * fraction)
    
    # Compute node ranking
    if removal_strategy == "degree":
        node_scores = dict(G.degree())
    elif removal_strategy == "betweenness":
        node_scores = nx.betweenness_centrality(G)
    elif removal_strategy == "eigenvector":
        try:
            node_scores = nx.eigenvector_centrality(G, max_iter=1000)
        except:
            # Fallback to degree if eigenvector fails
            node_scores = dict(G.degree())
    elif removal_strategy == "random":
        node_scores = {node: np.random.random() for node in G.nodes()}
    else:
        raise ValueError(f"Unknown removal strategy: {removal_strategy}")
    
    # Sort nodes by score (descending)
    ranked_nodes = sorted(node_scores.items(), key=lambda x: x[1], reverse=True)
    nodes_to_remove = [node for node, score in ranked_nodes[:num_removals]]
    
    # Track metrics over removals
    results = {metric: [] for metric in metrics}
    
    # Initial state
    for metric in metrics:
        results[metric].append(_compute_metric(G, metric))
    
    # Remove nodes one by one
    for node in nodes_to_remove:
        if node in G:
            G.remove_node(node)
            
            # Compute metrics after removal
            for metric in metrics:
                results[metric].append(_compute_metric(G, metric))
    
    return results


def random_edge_perturbation(
    network: Any,
    perturbation_type: str = "removal",
    num_perturbations: Optional[int] = None,
    fraction: float = 0.1,
    metrics: Optional[List[str]] = None,
    seed: Optional[int] = None
) -> Dict[str, List[float]]:
    """Test network robustness under random edge perturbation.
    
    Args:
        network: Multilayer network object
        perturbation_type: Type of perturbation:
            - 'removal': Remove random edges
            - 'addition': Add random edges
            - 'rewiring': Rewire random edges
        num_perturbations: Number of edges to perturb (overrides fraction)
        fraction: Fraction of edges to perturb (default: 0.1)
        metrics: List of metrics to track
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary mapping metric names to lists of values after each perturbation
        
    Example:
        >>> net = load_network(...)
        >>> results = random_edge_perturbation(net, 'removal', fraction=0.3)
        >>> print(results['components'])
        
    References:
        - Schneider, C. M., et al. (2011). "Mitigation of malicious attacks on
          networks." PNAS, 108(10), 3838-3841.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise ValueError("Network has no core_network")
    
    if metrics is None:
        metrics = ['size', 'edges', 'diameter']
    
    G = network.core_network.copy()
    
    # Determine number of perturbations
    if num_perturbations is None:
        num_perturbations = int(G.number_of_edges() * fraction)
    
    # Track metrics
    results = {metric: [] for metric in metrics}
    
    # Initial state
    for metric in metrics:
        results[metric].append(_compute_metric(G, metric))
    
    # Apply perturbations
    for _ in range(num_perturbations):
        if perturbation_type == "removal":
            if G.number_of_edges() > 0:
                edges = list(G.edges())
                edge_to_remove = edges[np.random.randint(len(edges))]
                G.remove_edge(*edge_to_remove)
        
        elif perturbation_type == "addition":
            nodes = list(G.nodes())
            if len(nodes) >= 2:
                u = nodes[np.random.randint(len(nodes))]
                v = nodes[np.random.randint(len(nodes))]
                if u != v and not G.has_edge(u, v):
                    G.add_edge(u, v)
        
        elif perturbation_type == "rewiring":
            if G.number_of_edges() > 0:
                # Remove a random edge
                edges = list(G.edges())
                edge_to_remove = edges[np.random.randint(len(edges))]
                G.remove_edge(*edge_to_remove)
                
                # Add a random edge
                nodes = list(G.nodes())
                if len(nodes) >= 2:
                    u = nodes[np.random.randint(len(nodes))]
                    v = nodes[np.random.randint(len(nodes))]
                    if u != v and not G.has_edge(u, v):
                        G.add_edge(u, v)
        
        # Compute metrics after perturbation
        for metric in metrics:
            results[metric].append(_compute_metric(G, metric))
    
    return results


def layer_wise_damage(
    network: Any,
    damage_strategy: str = "node_removal",
    damage_fraction: float = 0.2,
    metrics: Optional[List[str]] = None
) -> Dict[str, Dict[str, float]]:
    """Analyze impact of damage to individual layers.
    
    Tests what happens when each layer is damaged independently.
    
    Args:
        network: Multilayer network object
        damage_strategy: How to damage layers:
            - 'node_removal': Remove fraction of nodes
            - 'edge_removal': Remove fraction of edges
            - 'full_removal': Remove entire layer
        damage_fraction: Fraction of layer to damage (0-1)
        metrics: List of metrics to compute
        
    Returns:
        Dictionary mapping layer names to metric dictionaries
        
    Example:
        >>> net = load_multilayer_network(...)
        >>> results = layer_wise_damage(net, 'node_removal', 0.3)
        >>> for layer, metrics in results.items():
        ...     print(f"{layer}: size={metrics['size']}")
        
    References:
        - Buldyrev, S. V., et al. (2010). "Catastrophic cascade of failures in
          interdependent networks." Nature, 464(7291), 1025-1028.
        - Gao, J., et al. (2012). "Networks formed from interdependent networks."
          Nature Physics, 8(1), 40-48.
    """
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise ValueError("Network has no core_network")
    
    if metrics is None:
        metrics = ['size', 'edges', 'components']
    
    G = network.core_network
    
    # Extract layer information
    layers = defaultdict(list)
    layer_edges = defaultdict(list)
    
    for node in G.nodes():
        if isinstance(node, tuple) and len(node) >= 2:
            layer = node[1]
            layers[layer].append(node)
    
    for u, v in G.edges():
        if isinstance(u, tuple) and isinstance(v, tuple) and len(u) >= 2 and len(v) >= 2:
            if u[1] == v[1]:  # Same layer edge
                layer = u[1]
                layer_edges[layer].append((u, v))
    
    results = {}
    
    # Test damage to each layer
    for layer, layer_nodes in layers.items():
        G_damaged = G.copy()
        
        if damage_strategy == "node_removal":
            # Remove fraction of nodes from this layer
            num_to_remove = int(len(layer_nodes) * damage_fraction)
            if num_to_remove > 0 and len(layer_nodes) > 0:
                num_to_remove = min(num_to_remove, len(layer_nodes))
                nodes_to_remove = np.random.choice(layer_nodes, num_to_remove, replace=False)
                for node in nodes_to_remove:
                    G_damaged.remove_node(node)
        
        elif damage_strategy == "edge_removal":
            # Remove fraction of edges from this layer
            edges_in_layer = layer_edges[layer]
            num_to_remove = int(len(edges_in_layer) * damage_fraction)
            if num_to_remove > 0 and len(edges_in_layer) > 0:
                num_to_remove = min(num_to_remove, len(edges_in_layer))
                edges_to_remove = [edges_in_layer[i] for i in np.random.choice(
                    len(edges_in_layer), num_to_remove, replace=False
                )]
                for u, v in edges_to_remove:
                    if G_damaged.has_edge(u, v):
                        G_damaged.remove_edge(u, v)
        
        elif damage_strategy == "full_removal":
            # Remove entire layer
            for node in layer_nodes:
                G_damaged.remove_node(node)
        
        # Compute metrics after damage
        layer_results = {}
        for metric in metrics:
            layer_results[metric] = _compute_metric(G_damaged, metric)
        
        results[layer] = layer_results
    
    return results


def _compute_metric(G: nx.Graph, metric: str) -> float:
    """Compute a network metric.
    
    Args:
        G: NetworkX graph
        metric: Name of metric to compute
        
    Returns:
        Metric value
    """
    if G.number_of_nodes() == 0:
        return 0.0
    
    if metric == "size":
        # Size of largest connected component
        if G.number_of_nodes() == 0:
            return 0
        components = list(nx.connected_components(G.to_undirected()))
        return len(max(components, key=len)) if components else 0
    
    elif metric == "edges":
        return G.number_of_edges()
    
    elif metric == "components":
        return nx.number_connected_components(G.to_undirected())
    
    elif metric == "diameter":
        try:
            if nx.is_connected(G.to_undirected()):
                return nx.diameter(G.to_undirected())
            else:
                # Diameter of largest component
                components = list(nx.connected_components(G.to_undirected()))
                if components:
                    largest = max(components, key=len)
                    subgraph = G.subgraph(largest).to_undirected()
                    return nx.diameter(subgraph)
                return 0
        except:
            return 0
    
    elif metric == "clustering":
        try:
            return nx.average_clustering(G.to_undirected())
        except:
            return 0.0
    
    elif metric == "efficiency":
        try:
            return nx.global_efficiency(G)
        except:
            return 0.0
    
    else:
        return 0.0


def cascade_failure_simulation(
    network: Any,
    initial_failures: List[Any],
    failure_threshold: float = 0.5,
    max_iterations: int = 100
) -> Dict[str, Any]:
    """Simulate cascade failures in multilayer network.
    
    Models how initial failures can propagate through the network based
    on load redistribution or connectivity dependencies.
    
    Args:
        network: Multilayer network object
        initial_failures: List of nodes to fail initially
        failure_threshold: Threshold for cascading failure (0-1)
        max_iterations: Maximum cascade iterations
        
    Returns:
        Dictionary with cascade statistics:
            - 'failed_nodes': List of all failed nodes
            - 'iterations': Number of cascade iterations
            - 'final_size': Size of largest surviving component
            
    Algorithm:
        1. Remove initial failed nodes
        2. For each iteration:
           - Identify nodes with too many failed neighbors
           - Remove these nodes (they fail)
           - Repeat until no new failures
           
    References:
        - Motter, A. E., & Lai, Y. C. (2002). "Cascade-based attacks on complex
          networks." Physical Review E, 66(6), 065102.
        - Parshani, R., et al. (2010). "Interdependent networks: reducing the
          coupling strength leads to a change from a first to second order
          percolation transition." Physical Review Letters, 105(4), 048701.
    """
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise ValueError("Network has no core_network")
    
    G = network.core_network.copy()
    
    failed_nodes = set(initial_failures)
    
    # Remove initial failures
    for node in initial_failures:
        if node in G:
            G.remove_node(node)
    
    # Cascade iterations
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        new_failures = []
        
        # Check each remaining node
        for node in list(G.nodes()):
            # Get original neighbors (before any failures)
            original_neighbors = list(network.core_network.neighbors(node))
            
            # Count failed neighbors
            failed_neighbor_count = sum(1 for n in original_neighbors if n in failed_nodes)
            
            # Check if node should fail
            if len(original_neighbors) > 0:
                failure_ratio = failed_neighbor_count / len(original_neighbors)
                if failure_ratio >= failure_threshold:
                    new_failures.append(node)
        
        # No new failures - cascade stops
        if not new_failures:
            break
        
        # Apply new failures
        for node in new_failures:
            failed_nodes.add(node)
            if node in G:
                G.remove_node(node)
    
    # Compute final statistics
    if G.number_of_nodes() > 0:
        components = list(nx.connected_components(G.to_undirected()))
        final_size = len(max(components, key=len)) if components else 0
    else:
        final_size = 0
    
    return {
        'failed_nodes': list(failed_nodes),
        'num_failed': len(failed_nodes),
        'iterations': iteration,
        'final_size': final_size,
        'survival_rate': final_size / network.core_network.number_of_nodes()
    }
