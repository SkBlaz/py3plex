"""
Conversion utilities for multilayer SBM.

This module handles conversion between py3plex multilayer networks
and internal sparse adjacency representations.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.sparse as sp
import networkx as nx


def extract_layer_adjacencies(
    network: Any,
    layers: Optional[List[str]] = None,
    directed: bool = False,
    weight_attr: str = "weight"
) -> Tuple[List[sp.spmatrix], List[str], Dict[Any, int]]:
    """
    Extract sparse adjacency matrices from py3plex multilayer network.
    
    Args:
        network: py3plex multi_layer_network object
        layers: List of layer names to extract (None = all layers)
        directed: Whether to treat network as directed
        weight_attr: Edge weight attribute name
        
    Returns:
        Tuple of (adjacency_list, layer_names, node_to_idx)
        - adjacency_list: List of sparse CSR matrices (one per layer)
        - layer_names: List of layer names in order
        - node_to_idx: Dict mapping node IDs to integer indices
    """
    # Get all nodes (aligned across layers for multiplex)
    # get_nodes() returns (node_id, layer) tuples, extract unique node IDs
    all_node_tuples = list(network.get_nodes())
    unique_node_ids = set()
    for node in all_node_tuples:
        if isinstance(node, tuple):
            unique_node_ids.add(node[0])
        else:
            unique_node_ids.add(node)
    
    all_nodes = sorted(unique_node_ids)
    node_to_idx = {node: idx for idx, node in enumerate(all_nodes)}
    n_nodes = len(all_nodes)
    
    # Get layers information without computing layouts (SBM doesn't need layout positions)
    layers_tuple = network.get_layers(compute_layouts=None)
    # get_layers() returns (layer_names, layer_graphs, other_info)
    layer_names = layers_tuple[0] if isinstance(layers_tuple, tuple) else list(layers_tuple)
    layer_graphs = layers_tuple[1] if isinstance(layers_tuple, tuple) and len(layers_tuple) > 1 else None
    
    # Filter to requested layers
    if layers is not None:
        layer_indices = [layer_names.index(l) for l in layers if l in layer_names]
        layer_names = [layer_names[i] for i in layer_indices]
        if layer_graphs:
            layer_graphs = [layer_graphs[i] for i in layer_indices]
    
    adjacency_list = []
    
    for idx, layer_name in enumerate(layer_names):
        # Get the layer graph
        if layer_graphs and idx < len(layer_graphs):
            layer_graph = layer_graphs[idx]
        else:
            # Fallback: extract from core network
            # This shouldn't happen normally
            layer_graph = nx.MultiGraph() if not directed else nx.MultiDiGraph()
            for u, v, data in network.core_network.edges(data=True):
                # Nodes in py3plex are (node_id, layer) tuples
                if isinstance(u, tuple) and isinstance(v, tuple):
                    if u[1] == layer_name and v[1] == layer_name:
                        layer_graph.add_edge(u[0], v[0], **data)
        
        # Extract edges from the layer graph
        edges = []
        weights = []
        
        for u, v, data in layer_graph.edges(data=True):
            # Nodes might be tuples (node_id, layer) or just node_id
            u_clean = u[0] if isinstance(u, tuple) else u
            v_clean = v[0] if isinstance(v, tuple) else v
            
            # Map to indices
            if u_clean not in node_to_idx or v_clean not in node_to_idx:
                continue
            
            u_idx = node_to_idx[u_clean]
            v_idx = node_to_idx[v_clean]
            w = data.get(weight_attr, 1.0)
            
            edges.append((u_idx, v_idx))
            weights.append(w)
            
            # For undirected, add reverse edge
            if not directed and u_idx != v_idx:
                edges.append((v_idx, u_idx))
                weights.append(w)
        
        # Build sparse adjacency matrix
        if len(edges) > 0:
            rows, cols = zip(*edges)
            A = sp.csr_matrix(
                (weights, (rows, cols)),
                shape=(n_nodes, n_nodes),
                dtype=np.float64
            )
        else:
            # Empty layer
            A = sp.csr_matrix((n_nodes, n_nodes), dtype=np.float64)
        
        adjacency_list.append(A)
    
    return adjacency_list, layer_names, node_to_idx


def build_node_alignment(
    network: Any
) -> Dict[str, List[Any]]:
    """
    Build node alignment information across layers.
    
    Args:
        network: py3plex multi_layer_network object
        
    Returns:
        Dict mapping layer names to lists of nodes present in that layer
    """
    alignment = {}
    
    # Get layers information without computing layouts
    layers_tuple = network.get_layers(compute_layouts=None)
    # get_layers() returns (layer_names, layer_graphs, other_info)
    layer_names = layers_tuple[0] if isinstance(layers_tuple, tuple) else list(layers_tuple)
    layer_graphs = layers_tuple[1] if isinstance(layers_tuple, tuple) and len(layers_tuple) > 1 else None
    
    for idx, layer_name in enumerate(layer_names):
        if layer_graphs and idx < len(layer_graphs):
            layer_graph = layer_graphs[idx]
            # Nodes might be tuples (node_id, layer) or just node_id
            nodes_in_layer = []
            for node in layer_graph.nodes():
                if isinstance(node, tuple):
                    nodes_in_layer.append(node[0])  # Extract node_id
                else:
                    nodes_in_layer.append(node)
            alignment[layer_name] = nodes_in_layer
        else:
            # Fallback: extract from core network
            nodes_in_layer = set()
            for node in network.core_network.nodes():
                if isinstance(node, tuple) and node[1] == layer_name:
                    nodes_in_layer.add(node[0])
            alignment[layer_name] = list(nodes_in_layer)
    
    return alignment


def check_node_aligned(network: Any) -> bool:
    """
    Check if all layers have the same nodes (node-aligned multiplex).
    
    Args:
        network: py3plex multi_layer_network object
        
    Returns:
        True if node-aligned, False otherwise
    """
    alignment = build_node_alignment(network)
    
    if not alignment:
        return True
    
    # Get reference node set from first layer
    layers = list(alignment.keys())
    reference_nodes = set(alignment[layers[0]])
    
    # Check all other layers
    for layer in layers[1:]:
        if set(alignment[layer]) != reference_nodes:
            return False
    
    return True
