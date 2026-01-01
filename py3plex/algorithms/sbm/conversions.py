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
    all_nodes = sorted(network.get_nodes())
    node_to_idx = {node: idx for idx, node in enumerate(all_nodes)}
    n_nodes = len(all_nodes)
    
    # Get layers to process
    if layers is None:
        layers = list(network.get_layers())
    
    adjacency_list = []
    
    for layer in layers:
        # Get edges for this layer
        edges = []
        weights = []
        
        # Extract edges from the network for this layer
        layer_graph = network.get_layer_subgraph(layer)
        
        for u, v, data in layer_graph.edges(data=True):
            u_idx = node_to_idx[u]
            v_idx = node_to_idx[v]
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
    
    return adjacency_list, layers, node_to_idx


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
    
    for layer in network.get_layers():
        layer_graph = network.get_layer_subgraph(layer)
        alignment[layer] = list(layer_graph.nodes())
    
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
