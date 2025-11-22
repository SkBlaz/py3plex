"""
Layer similarity metrics for multilayer networks.

Compute similarity between layers using:
- Jaccard similarity
- Spectral similarity  
- Frobenius distance of supra matrices

These metrics help analyze layer relationships and redundancy.

Authors: py3plex contributors
Date: 2025
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.sparse as sp
from collections import defaultdict


def jaccard_layer_similarity(
    network: Any,
    layer1: Any,
    layer2: Any,
    element: str = "nodes"
) -> float:
    """Compute Jaccard similarity between two layers.
    
    Measures overlap of nodes or edges between layers.
    
    Args:
        network: Multilayer network object
        layer1: First layer identifier
        layer2: Second layer identifier
        element: What to compare ('nodes' or 'edges')
        
    Returns:
        Jaccard similarity in [0, 1]
        
    Formula:
        J(A, B) = |A ∩ B| / |A ∪ B|
        
    Example:
        >>> net = load_network(...)
        >>> similarity = jaccard_layer_similarity(net, 'social', 'email', 'nodes')
        >>> print(f"Node overlap: {similarity:.2f}")
        
    References:
        - Jaccard, P. (1912). "The distribution of the flora in the alpine zone."
          New Phytologist, 11(2), 37-50.
    """
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise ValueError("Network has no core_network")
    
    G = network.core_network
    
    # Extract layer elements
    if element == "nodes":
        set1 = {node[0] for node in G.nodes() 
                if isinstance(node, tuple) and len(node) >= 2 and node[1] == layer1}
        set2 = {node[0] for node in G.nodes() 
                if isinstance(node, tuple) and len(node) >= 2 and node[1] == layer2}
    
    elif element == "edges":
        set1 = {(u[0], v[0]) for u, v in G.edges() 
                if isinstance(u, tuple) and isinstance(v, tuple) and 
                len(u) >= 2 and len(v) >= 2 and u[1] == layer1 and v[1] == layer1}
        set2 = {(u[0], v[0]) for u, v in G.edges() 
                if isinstance(u, tuple) and isinstance(v, tuple) and 
                len(u) >= 2 and len(v) >= 2 and u[1] == layer2 and v[1] == layer2}
    else:
        raise ValueError(f"Unknown element type: {element}")
    
    # Compute Jaccard similarity
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0


def all_pairs_jaccard_similarity(
    network: Any,
    element: str = "nodes"
) -> Dict[Tuple[Any, Any], float]:
    """Compute Jaccard similarity for all layer pairs.
    
    Args:
        network: Multilayer network object
        element: What to compare ('nodes' or 'edges')
        
    Returns:
        Dictionary mapping (layer1, layer2) to similarity score
        
    Example:
        >>> net = load_network(...)
        >>> similarities = all_pairs_jaccard_similarity(net, 'edges')
        >>> for (l1, l2), sim in similarities.items():
        ...     print(f"{l1}-{l2}: {sim:.3f}")
    """
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise ValueError("Network has no core_network")
    
    G = network.core_network
    
    # Extract all layers
    layers = set()
    for node in G.nodes():
        if isinstance(node, tuple) and len(node) >= 2:
            layers.add(node[1])
    
    layers = sorted(layers)
    
    # Compute pairwise similarities
    results = {}
    for i, l1 in enumerate(layers):
        for l2 in layers[i+1:]:
            sim = jaccard_layer_similarity(network, l1, l2, element)
            results[(l1, l2)] = sim
    
    return results


def spectral_layer_similarity(
    network: Any,
    layer1: Any,
    layer2: Any,
    k: int = 10
) -> float:
    """Compute spectral similarity between two layers.
    
    Compares the eigenvalue spectra of layer adjacency matrices.
    Similar spectra indicate similar structural properties.
    
    Args:
        network: Multilayer network object
        layer1: First layer identifier
        layer2: Second layer identifier
        k: Number of eigenvalues to compare
        
    Returns:
        Spectral similarity in [0, 1]
        
    Algorithm:
        1. Compute top k eigenvalues for each layer
        2. Compare eigenvalue sequences using correlation or distance
        
    References:
        - Wilson, R. C., & Zhu, P. (2008). "A study of graph spectra for
          comparing graphs and trees." Pattern Recognition, 41(9), 2833-2841.
    """
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise ValueError("Network has no core_network")
    
    G = network.core_network
    
    # Extract layer subgraphs
    nodes1 = [node for node in G.nodes() 
              if isinstance(node, tuple) and len(node) >= 2 and node[1] == layer1]
    nodes2 = [node for node in G.nodes() 
              if isinstance(node, tuple) and len(node) >= 2 and node[1] == layer2]
    
    if not nodes1 or not nodes2:
        return 0.0
    
    subgraph1 = G.subgraph(nodes1)
    subgraph2 = G.subgraph(nodes2)
    
    try:
        # Compute adjacency matrices
        import networkx as nx
        from py3plex.core.nx_compat import nx_to_scipy_sparse_matrix
        
        adj1 = nx_to_scipy_sparse_matrix(subgraph1)
        adj2 = nx_to_scipy_sparse_matrix(subgraph2)
        
        # Compute eigenvalues
        from scipy.sparse.linalg import eigsh
        
        k1 = min(k, adj1.shape[0] - 2)
        k2 = min(k, adj2.shape[0] - 2)
        
        if k1 <= 0 or k2 <= 0:
            return 0.0
        
        eigs1 = eigsh(adj1, k=k1, return_eigenvectors=False, which='LM')
        eigs2 = eigsh(adj2, k=k2, return_eigenvectors=False, which='LM')
        
        # Sort eigenvalues
        eigs1 = np.sort(np.abs(eigs1))[::-1]
        eigs2 = np.sort(np.abs(eigs2))[::-1]
        
        # Pad shorter sequence
        max_len = max(len(eigs1), len(eigs2))
        eigs1_padded = np.pad(eigs1, (0, max_len - len(eigs1)))
        eigs2_padded = np.pad(eigs2, (0, max_len - len(eigs2)))
        
        # Compute similarity (normalized correlation)
        if np.std(eigs1_padded) > 0 and np.std(eigs2_padded) > 0:
            correlation = np.corrcoef(eigs1_padded, eigs2_padded)[0, 1]
            # Convert correlation to similarity in [0, 1]
            similarity = (correlation + 1) / 2
        else:
            similarity = 0.0
        
        return similarity
    
    except Exception:
        # Fallback: use degree distribution similarity
        degrees1 = [d for n, d in subgraph1.degree()]
        degrees2 = [d for n, d in subgraph2.degree()]
        
        if not degrees1 or not degrees2:
            return 0.0
        
        # Compare degree distributions using KL divergence
        hist1, bins = np.histogram(degrees1, bins=20, density=True)
        hist2, _ = np.histogram(degrees2, bins=bins, density=True)
        
        # Add small constant to avoid log(0)
        hist1 = hist1 + 1e-10
        hist2 = hist2 + 1e-10
        
        # Normalize
        hist1 = hist1 / hist1.sum()
        hist2 = hist2 / hist2.sum()
        
        # KL divergence
        kl = np.sum(hist1 * np.log(hist1 / hist2))
        
        # Convert to similarity
        similarity = np.exp(-kl)
        
        return similarity


def frobenius_distance_layers(
    network: Any,
    layer1: Any,
    layer2: Any,
    normalized: bool = True
) -> float:
    """Compute Frobenius distance between layer adjacency matrices.
    
    Measures element-wise difference between adjacency matrices.
    Small distance indicates similar connection patterns.
    
    Args:
        network: Multilayer network object
        layer1: First layer identifier
        layer2: Second layer identifier
        normalized: Whether to normalize by matrix size
        
    Returns:
        Frobenius distance (smaller = more similar)
        
    Formula:
        ||A - B||_F = sqrt(sum((A_ij - B_ij)^2))
        
    References:
        - Schieber, T. A., et al. (2017). "Quantification of network structural
          dissimilarities." Nature Communications, 8, 13928.
    """
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise ValueError("Network has no core_network")
    
    G = network.core_network
    
    # Extract layer subgraphs
    nodes1 = [node for node in G.nodes() 
              if isinstance(node, tuple) and len(node) >= 2 and node[1] == layer1]
    nodes2 = [node for node in G.nodes() 
              if isinstance(node, tuple) and len(node) >= 2 and node[1] == layer2]
    
    if not nodes1 or not nodes2:
        return float('inf')
    
    # Get node IDs (first element of tuple)
    node_ids1 = {node[0] for node in nodes1}
    node_ids2 = {node[0] for node in nodes2}
    
    # Find common nodes
    common_nodes = sorted(node_ids1 & node_ids2)
    
    if not common_nodes:
        return float('inf')
    
    # Build adjacency matrices for common nodes
    n = len(common_nodes)
    node_idx = {node: i for i, node in enumerate(common_nodes)}
    
    adj1 = np.zeros((n, n))
    adj2 = np.zeros((n, n))
    
    # Fill adjacency matrix for layer1
    for u, v in G.edges():
        if (isinstance(u, tuple) and isinstance(v, tuple) and 
            len(u) >= 2 and len(v) >= 2 and 
            u[1] == layer1 and v[1] == layer1):
            
            u_id, v_id = u[0], v[0]
            if u_id in node_idx and v_id in node_idx:
                i, j = node_idx[u_id], node_idx[v_id]
                adj1[i, j] = 1
                if not G.is_directed():
                    adj1[j, i] = 1
    
    # Fill adjacency matrix for layer2
    for u, v in G.edges():
        if (isinstance(u, tuple) and isinstance(v, tuple) and 
            len(u) >= 2 and len(v) >= 2 and 
            u[1] == layer2 and v[1] == layer2):
            
            u_id, v_id = u[0], v[0]
            if u_id in node_idx and v_id in node_idx:
                i, j = node_idx[u_id], node_idx[v_id]
                adj2[i, j] = 1
                if not G.is_directed():
                    adj2[j, i] = 1
    
    # Compute Frobenius distance
    diff = adj1 - adj2
    frobenius = np.linalg.norm(diff, 'fro')
    
    if normalized:
        # Normalize by matrix size
        frobenius = frobenius / np.sqrt(n * n)
    
    return frobenius


def layer_correlation_matrix(
    network: Any,
    method: str = "jaccard",
    element: str = "nodes"
) -> Tuple[np.ndarray, List[Any]]:
    """Compute correlation/similarity matrix for all layers.
    
    Args:
        network: Multilayer network object
        method: Similarity method ('jaccard', 'spectral', 'frobenius')
        element: For Jaccard, what to compare ('nodes' or 'edges')
        
    Returns:
        Tuple of (similarity_matrix, layer_names)
        
    Example:
        >>> net = load_network(...)
        >>> sim_matrix, layers = layer_correlation_matrix(net, 'jaccard')
        >>> import matplotlib.pyplot as plt
        >>> plt.imshow(sim_matrix, cmap='hot')
        >>> plt.colorbar()
        >>> plt.xticks(range(len(layers)), layers)
        >>> plt.yticks(range(len(layers)), layers)
        >>> plt.show()
    """
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise ValueError("Network has no core_network")
    
    G = network.core_network
    
    # Extract all layers
    layers = set()
    for node in G.nodes():
        if isinstance(node, tuple) and len(node) >= 2:
            layers.add(node[1])
    
    layers = sorted(layers)
    n = len(layers)
    
    # Initialize similarity matrix
    sim_matrix = np.eye(n)  # Diagonal is 1 (self-similarity)
    
    # Compute pairwise similarities
    for i, l1 in enumerate(layers):
        for j in range(i+1, n):
            l2 = layers[j]
            
            if method == "jaccard":
                sim = jaccard_layer_similarity(network, l1, l2, element)
            elif method == "spectral":
                sim = spectral_layer_similarity(network, l1, l2)
            elif method == "frobenius":
                dist = frobenius_distance_layers(network, l1, l2, normalized=True)
                # Convert distance to similarity
                sim = 1 / (1 + dist)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            sim_matrix[i, j] = sim
            sim_matrix[j, i] = sim
    
    return sim_matrix, layers


def layer_dissimilarity_index(
    network: Any,
    method: str = "jaccard"
) -> float:
    """Compute overall dissimilarity index for multilayer network.
    
    Measures how different layers are on average. High values indicate
    diverse layer structures; low values suggest redundancy.
    
    Args:
        network: Multilayer network object
        method: Similarity method to use
        
    Returns:
        Dissimilarity index (average pairwise dissimilarity)
        
    Example:
        >>> net = load_network(...)
        >>> dissim = layer_dissimilarity_index(net)
        >>> print(f"Layer diversity: {dissim:.3f}")
    """
    sim_matrix, layers = layer_correlation_matrix(network, method)
    
    if len(layers) < 2:
        return 0.0
    
    # Extract upper triangle (excluding diagonal)
    n = len(layers)
    similarities = []
    for i in range(n):
        for j in range(i+1, n):
            similarities.append(sim_matrix[i, j])
    
    # Average dissimilarity
    avg_similarity = np.mean(similarities)
    dissimilarity = 1 - avg_similarity
    
    return dissimilarity
