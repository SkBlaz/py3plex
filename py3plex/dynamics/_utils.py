"""Internal utility functions for dynamics module.

This module provides helper functions for working with multilayer networks
and extracting network information needed by dynamics processes.
"""

from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import networkx as nx
import numpy as np


def iter_multilayer_nodes(graph: Any) -> Iterator[Any]:
    """Iterate over nodes in a multilayer or regular graph.
    
    Works with:
    - NetworkX graphs: iterates over G.nodes()
    - py3plex multilayer networks: iterates over core_network nodes
    
    Args:
        graph: NetworkX graph or py3plex multilayer network
    
    Yields:
        Node identifiers (may include layer information for multilayer)
    """
    if hasattr(graph, 'core_network'):
        # py3plex multilayer network
        yield from graph.core_network.nodes()
    elif hasattr(graph, 'nodes'):
        # NetworkX graph
        yield from graph.nodes()
    else:
        raise TypeError(f"Unsupported graph type: {type(graph)}")


def iter_multilayer_neighbors(
    graph: Any,
    node: Any,
) -> Iterator[Any]:
    """Iterate over neighbors of a node in multilayer or regular graph.
    
    For py3plex multilayer networks with nodes formatted as "nodeID---layerID",
    this returns all neighbors including inter-layer connections.
    
    Args:
        graph: NetworkX graph or py3plex multilayer network
        node: Node identifier
    
    Yields:
        Neighbor node identifiers
    """
    if hasattr(graph, 'core_network'):
        # py3plex multilayer network
        yield from graph.core_network.neighbors(node)
    elif hasattr(graph, 'neighbors'):
        # NetworkX graph
        yield from graph.neighbors(node)
    else:
        raise TypeError(f"Unsupported graph type: {type(graph)}")


def get_adjacency_matrix(
    graph: Any,
    nodelist: Optional[List[Any]] = None,
) -> Tuple[np.ndarray, Dict[Any, int]]:
    """Extract adjacency matrix from graph.
    
    Args:
        graph: NetworkX graph or py3plex multilayer network
        nodelist: Optional list of nodes to include (in order)
    
    Returns:
        Tuple of (adjacency_matrix, node_to_idx) where:
        - adjacency_matrix: NxN numpy array
        - node_to_idx: dict mapping node -> index
    """
    if hasattr(graph, 'core_network'):
        # py3plex multilayer network
        G = graph.core_network
    elif hasattr(graph, 'nodes'):
        # NetworkX graph
        G = graph
    else:
        raise TypeError(f"Unsupported graph type: {type(graph)}")
    
    if nodelist is None:
        nodelist = list(G.nodes())
    
    node_to_idx = {node: i for i, node in enumerate(nodelist)}
    adj = nx.to_numpy_array(G.subgraph(nodelist), nodelist=nodelist, dtype=float)
    if not np.all(np.isfinite(adj)) or np.any(adj < 0):
        raise ValueError("Dynamics requires finite nonnegative edge weights.")

    return adj, node_to_idx


def dict_state_to_vector(
    state: Dict[Any, Union[int, float]],
    node_to_idx: Dict[Any, int],
) -> np.ndarray:
    """Convert dictionary state to numpy vector.
    
    Args:
        state: Dictionary mapping node -> value
        node_to_idx: Dictionary mapping node -> index
    
    Returns:
        Numpy array of length len(node_to_idx)
    """
    n = len(node_to_idx)
    vector = np.zeros(n)
    for node, value in state.items():
        if node in node_to_idx:
            vector[node_to_idx[node]] = value
    return vector


def vector_to_dict_state(
    vector: np.ndarray,
    idx_to_node: Dict[int, Any],
) -> Dict[Any, Union[int, float]]:
    """Convert numpy vector to dictionary state.
    
    Args:
        vector: Numpy array
        idx_to_node: Dictionary mapping index -> node
    
    Returns:
        Dictionary mapping node -> value
    """
    return {idx_to_node[i]: vector[i] for i in range(len(vector))}


def get_node_layer_info(graph: Any) -> Optional[Dict[Any, str]]:
    """Extract layer information for nodes in a multilayer network.
    
    For py3plex networks with nodes formatted as "nodeID---layerID",
    extracts the layer for each node.
    
    Args:
        graph: NetworkX graph or py3plex multilayer network
    
    Returns:
        Dictionary mapping node -> layer_name, or None if not multilayer
    """
    if not hasattr(graph, 'core_network'):
        # Not a py3plex multilayer network
        return None
    
    # py3plex uses "---" as delimiter
    delimiter = "---"
    layer_info = {}
    
    for node in graph.core_network.nodes():
        node_str = str(node)
        if delimiter in node_str:
            # Extract layer
            parts = node_str.split(delimiter)
            if len(parts) >= 2:
                layer_info[node] = parts[-1]
        else:
            layer_info[node] = "default"
    
    return layer_info if layer_info else None


def iter_incoming_exposures(graph, node):
    """Yield an incoming weight for each edge, including parallel edges."""
    network = graph.core_network if hasattr(graph, "core_network") else graph
    adjacency = network.pred[node] if network.is_directed() else network.adj[node]
    for neighbor, attrs in adjacency.items():
        records = attrs.values() if network.is_multigraph() else (attrs,)
        for data in records:
            weight = float(data.get("weight", 1.0))
            if not np.isfinite(weight) or weight < 0:
                raise ValueError("Dynamics requires finite nonnegative edge weights.")
            yield neighbor, weight


def count_infected_neighbors(graph, node, state, infected_value=1) -> float:
    """Return total incoming weight from neighbors in the infected state."""
    return sum(weight for neighbor, weight in iter_incoming_exposures(graph, node)
               if state.get(neighbor) == infected_value)
