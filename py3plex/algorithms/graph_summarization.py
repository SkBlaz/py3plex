"""
Graph summarization tools for multilayer networks.

Implements automatic coarse-graining of multilayer networks:
- Collapse low-degree nodes
- Detect structurally equivalent nodes
- Compress layers by similarity

These tools help reduce network complexity while preserving key structural properties.

Authors: py3plex contributors
Date: 2025
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import networkx as nx
from collections import defaultdict
import scipy.sparse as sp


def collapse_low_degree_nodes(
    network: Any,
    degree_threshold: int = 1,
    aggregation_method: str = "star"
) -> Any:
    """Collapse low-degree nodes to reduce network complexity.
    
    Nodes with degree below threshold are either removed or merged into
    their neighbors, preserving overall connectivity patterns.
    
    Args:
        network: Multilayer network object
        degree_threshold: Minimum degree to keep a node
        aggregation_method: How to handle connections ('star', 'clique', 'remove')
            - 'star': Connect neighbors to a representative node
            - 'clique': Create clique among neighbors
            - 'remove': Simply remove low-degree nodes
            
    Returns:
        Summarized network with low-degree nodes collapsed
        
    Algorithm:
        1. Identify nodes with degree < threshold
        2. For each low-degree node:
           - Collect its neighbors
           - Apply aggregation method
           - Remove the node
           
    Example:
        >>> net = load_network(...)
        >>> summarized = collapse_low_degree_nodes(net, degree_threshold=2)
    """
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise ValueError("Network has no core_network")
    
    G = network.core_network.copy()
    
    # Find low-degree nodes
    low_degree_nodes = [
        node for node, degree in G.degree()
        if degree < degree_threshold
    ]
    
    for node in low_degree_nodes:
        neighbors = list(G.neighbors(node))
        
        if aggregation_method == "star":
            # Connect all neighbors to the first neighbor (representative)
            if len(neighbors) > 1:
                representative = neighbors[0]
                for neighbor in neighbors[1:]:
                    if not G.has_edge(representative, neighbor):
                        G.add_edge(representative, neighbor, collapsed=True)
        
        elif aggregation_method == "clique":
            # Create clique among neighbors
            for i, n1 in enumerate(neighbors):
                for n2 in neighbors[i+1:]:
                    if not G.has_edge(n1, n2):
                        G.add_edge(n1, n2, collapsed=True)
        
        # Remove the low-degree node
        G.remove_node(node)
    
    # Update network
    from py3plex.core.multinet import multi_layer_network
    summarized = multi_layer_network(
        directed=network.directed,
        network_type=network.network_type
    )
    summarized.load_network(G, input_type="nx", directed=network.directed)
    
    return summarized


def detect_structural_equivalence(
    network: Any,
    method: str = "exact",
    threshold: float = 0.9
) -> Dict[Any, int]:
    """Detect structurally equivalent nodes in multilayer network.
    
    Structurally equivalent nodes have identical connection patterns.
    Can be used to identify redundant nodes for compression.
    
    Args:
        network: Multilayer network object
        method: Equivalence detection method ('exact', 'regular', 'automorphic')
        threshold: Similarity threshold for approximate methods (0-1)
        
    Returns:
        Dictionary mapping nodes to equivalence class IDs
        
    Algorithm:
        - 'exact': Nodes are equivalent if they have identical neighborhoods
        - 'regular': Nodes are equivalent if they have isomorphic neighborhoods
        - 'automorphic': Based on automorphism groups
        
    References:
        - Lorrain, F., & White, H. C. (1971). "Structural equivalence of
          individuals in social networks." The Journal of Mathematical
          Sociology, 1(1), 49-80.
        - Everett, M. G., & Borgatti, S. P. (1994). "Regular equivalence."
          Social Networks, 16(1), 29-43.
    """
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise ValueError("Network has no core_network")
    
    G = network.core_network
    equivalence_classes = {}
    
    if method == "exact":
        # Exact structural equivalence: identical neighborhoods
        node_signatures = {}
        
        for node in G.nodes():
            # Create signature: frozenset of neighbors
            neighbors = frozenset(G.neighbors(node))
            signature = (neighbors, G.degree(node))
            
            if signature not in node_signatures:
                node_signatures[signature] = []
            node_signatures[signature].append(node)
        
        # Assign equivalence class IDs
        for class_id, (signature, nodes) in enumerate(node_signatures.items()):
            for node in nodes:
                equivalence_classes[node] = class_id
    
    elif method == "regular":
        # Regular equivalence: similarity of neighborhoods
        nodes = list(G.nodes())
        n = len(nodes)
        
        # Create adjacency matrix
        adj_matrix = nx.to_numpy_array(G, nodelist=nodes)
        
        # Compute node similarities based on neighborhood structure
        similarities = np.zeros((n, n))
        for i in range(n):
            for j in range(i, n):
                # Jaccard similarity of neighborhoods
                neighbors_i = set(G.neighbors(nodes[i]))
                neighbors_j = set(G.neighbors(nodes[j]))
                
                if len(neighbors_i) == 0 and len(neighbors_j) == 0:
                    sim = 1.0
                else:
                    intersection = len(neighbors_i & neighbors_j)
                    union = len(neighbors_i | neighbors_j)
                    sim = intersection / union if union > 0 else 0.0
                
                similarities[i, j] = sim
                similarities[j, i] = sim
        
        # Cluster nodes by similarity
        from scipy.cluster.hierarchy import linkage, fcluster
        
        # Convert similarity to distance
        distances = 1 - similarities
        
        # Hierarchical clustering
        linkage_matrix = linkage(distances[np.triu_indices(n, k=1)], method='average')
        clusters = fcluster(linkage_matrix, 1 - threshold, criterion='distance')
        
        for node, cluster_id in zip(nodes, clusters):
            equivalence_classes[node] = int(cluster_id)
    
    elif method == "automorphic":
        # Use NetworkX's faster automorphism detection
        try:
            import networkx.algorithms.isomorphism as iso
            
            # This is a simplified version - full automorphism is expensive
            # Group nodes by degree as a first approximation
            degree_groups = defaultdict(list)
            for node in G.nodes():
                degree_groups[G.degree(node)].append(node)
            
            class_id = 0
            for degree, nodes in degree_groups.items():
                for node in nodes:
                    equivalence_classes[node] = class_id
                class_id += 1
        
        except ImportError:
            # Fallback to degree-based grouping
            degree_groups = defaultdict(list)
            for node in G.nodes():
                degree_groups[G.degree(node)].append(node)
            
            for class_id, nodes in enumerate(degree_groups.values()):
                for node in nodes:
                    equivalence_classes[node] = class_id
    
    return equivalence_classes


def compress_equivalent_nodes(
    network: Any,
    equivalence_classes: Dict[Any, int]
) -> Any:
    """Compress network by merging structurally equivalent nodes.
    
    Args:
        network: Multilayer network object
        equivalence_classes: Dictionary mapping nodes to equivalence class IDs
        
    Returns:
        Compressed network with equivalent nodes merged
        
    Algorithm:
        1. Group nodes by equivalence class
        2. For each class, merge all nodes into a representative
        3. Aggregate edge weights if needed
    """
    if not hasattr(network, 'core_network') or network.core_network is None:
        raise ValueError("Network has no core_network")
    
    G = network.core_network
    
    # Group nodes by equivalence class
    class_members = defaultdict(list)
    for node, class_id in equivalence_classes.items():
        class_members[class_id].append(node)
    
    # Create compressed graph
    if G.is_directed():
        G_compressed = nx.DiGraph()
    else:
        G_compressed = nx.Graph()
    
    # Use first node in each class as representative
    representatives = {}
    for class_id, members in class_members.items():
        rep = members[0]
        representatives[class_id] = rep
        G_compressed.add_node(rep, equivalence_class=class_id, size=len(members))
    
    # Add edges between representatives
    for u, v, data in G.edges(data=True):
        u_class = equivalence_classes[u]
        v_class = equivalence_classes[v]
        
        u_rep = representatives[u_class]
        v_rep = representatives[v_class]
        
        # Skip self-loops in compressed graph
        if u_rep == v_rep:
            continue
        
        # Add or update edge
        if G_compressed.has_edge(u_rep, v_rep):
            # Aggregate weights
            current_weight = G_compressed[u_rep][v_rep].get('weight', 1)
            new_weight = data.get('weight', 1)
            G_compressed[u_rep][v_rep]['weight'] = current_weight + new_weight
        else:
            G_compressed.add_edge(u_rep, v_rep, **data)
    
    # Update network
    from py3plex.core.multinet import multi_layer_network
    compressed = multi_layer_network(
        directed=network.directed,
        network_type=network.network_type
    )
    compressed.load_network(G_compressed, input_type="nx", directed=network.directed)
    
    return compressed


def compress_layers_by_similarity(
    network: Any,
    similarity_threshold: float = 0.8,
    similarity_metric: str = "jaccard"
) -> Any:
    """Compress similar layers in multilayer network.
    
    Identifies layers with similar structure and merges them to reduce
    dimensionality while preserving key network properties.
    
    Args:
        network: Multilayer network object
        similarity_threshold: Minimum similarity to merge layers (0-1)
        similarity_metric: Metric to use ('jaccard', 'overlap', 'structural')
        
    Returns:
        Network with similar layers merged
        
    Algorithm:
        1. Compute pairwise layer similarities
        2. Cluster layers by similarity
        3. Merge layers in each cluster
        
    Example:
        >>> net = load_multilayer_network(...)
        >>> compressed = compress_layers_by_similarity(net, threshold=0.8)
    """
    # Get layers
    if hasattr(network, 'core_network') and network.core_network is not None:
        G = network.core_network
    else:
        raise ValueError("Network has no core_network")
    
    # Extract layer information from nodes
    layers = defaultdict(set)
    layer_edges = defaultdict(set)
    
    for node in G.nodes():
        if isinstance(node, tuple) and len(node) >= 2:
            node_id, layer = node[0], node[1]
            layers[layer].add(node_id)
    
    for u, v in G.edges():
        if isinstance(u, tuple) and isinstance(v, tuple) and len(u) >= 2 and len(v) >= 2:
            if u[1] == v[1]:  # Same layer
                layer = u[1]
                layer_edges[layer].add((u[0], v[0]))
    
    if len(layers) < 2:
        return network  # Nothing to compress
    
    # Compute pairwise layer similarities
    layer_list = list(layers.keys())
    n_layers = len(layer_list)
    similarities = np.zeros((n_layers, n_layers))
    
    for i in range(n_layers):
        for j in range(i, n_layers):
            l1, l2 = layer_list[i], layer_list[j]
            
            if similarity_metric == "jaccard":
                # Jaccard similarity of node sets
                nodes1, nodes2 = layers[l1], layers[l2]
                intersection = len(nodes1 & nodes2)
                union = len(nodes1 | nodes2)
                sim = intersection / union if union > 0 else 0.0
            
            elif similarity_metric == "overlap":
                # Overlap coefficient of node sets
                nodes1, nodes2 = layers[l1], layers[l2]
                intersection = len(nodes1 & nodes2)
                min_size = min(len(nodes1), len(nodes2))
                sim = intersection / min_size if min_size > 0 else 0.0
            
            elif similarity_metric == "structural":
                # Edge-based structural similarity
                edges1, edges2 = layer_edges[l1], layer_edges[l2]
                intersection = len(edges1 & edges2)
                union = len(edges1 | edges2)
                sim = intersection / union if union > 0 else 0.0
            
            similarities[i, j] = sim
            similarities[j, i] = sim
    
    # Cluster layers by similarity
    from scipy.cluster.hierarchy import linkage, fcluster
    
    # Convert to distance
    distances = 1 - similarities
    
    # Hierarchical clustering
    linkage_matrix = linkage(distances[np.triu_indices(n_layers, k=1)], method='average')
    clusters = fcluster(linkage_matrix, 1 - similarity_threshold, criterion='distance')
    
    # Group layers by cluster
    layer_clusters = defaultdict(list)
    for layer, cluster_id in zip(layer_list, clusters):
        layer_clusters[cluster_id].append(layer)
    
    # Create compressed network
    if G.is_directed():
        G_compressed = nx.MultiDiGraph()
    else:
        G_compressed = nx.MultiGraph()
    
    # Map old layers to new layers
    layer_mapping = {}
    for cluster_id, cluster_layers in layer_clusters.items():
        # Use first layer as representative
        rep_layer = cluster_layers[0]
        for layer in cluster_layers:
            layer_mapping[layer] = rep_layer
    
    # Add nodes with remapped layers
    for node in G.nodes():
        if isinstance(node, tuple) and len(node) >= 2:
            node_id, old_layer = node[0], node[1]
            new_layer = layer_mapping[old_layer]
            G_compressed.add_node((node_id, new_layer))
    
    # Add edges with remapped layers
    for u, v, data in G.edges(data=True):
        if isinstance(u, tuple) and isinstance(v, tuple) and len(u) >= 2 and len(v) >= 2:
            u_new = (u[0], layer_mapping[u[1]])
            v_new = (v[0], layer_mapping[v[1]])
            G_compressed.add_edge(u_new, v_new, **data)
    
    # Update network
    from py3plex.core.multinet import multi_layer_network
    compressed = multi_layer_network(
        directed=network.directed,
        network_type=network.network_type
    )
    compressed.load_network(G_compressed, input_type="nx", directed=network.directed)
    
    return compressed


def summarize_network(
    network: Any,
    degree_threshold: int = 1,
    equivalence_threshold: float = 0.9,
    layer_similarity_threshold: float = 0.8
) -> Tuple[Any, Dict[str, Any]]:
    """Apply comprehensive network summarization.
    
    Combines multiple summarization techniques to create a compact
    representation of the multilayer network.
    
    Args:
        network: Multilayer network object
        degree_threshold: Threshold for collapsing low-degree nodes
        equivalence_threshold: Threshold for detecting equivalent nodes
        layer_similarity_threshold: Threshold for merging similar layers
        
    Returns:
        Tuple of (summarized_network, summary_statistics)
        
    Example:
        >>> net = load_network(...)
        >>> summarized, stats = summarize_network(net)
        >>> print(f"Compression ratio: {stats['compression_ratio']:.2f}")
    """
    original_nodes = network.core_network.number_of_nodes()
    original_edges = network.core_network.number_of_edges()
    
    # Step 1: Collapse low-degree nodes
    net1 = collapse_low_degree_nodes(network, degree_threshold)
    
    # Step 2: Detect and compress equivalent nodes
    equivalence = detect_structural_equivalence(net1, method="regular", threshold=equivalence_threshold)
    net2 = compress_equivalent_nodes(net1, equivalence)
    
    # Step 3: Compress similar layers
    net3 = compress_layers_by_similarity(net2, layer_similarity_threshold)
    
    # Compute statistics
    final_nodes = net3.core_network.number_of_nodes()
    final_edges = net3.core_network.number_of_edges()
    
    stats = {
        'original_nodes': original_nodes,
        'original_edges': original_edges,
        'final_nodes': final_nodes,
        'final_edges': final_edges,
        'compression_ratio': original_nodes / final_nodes if final_nodes > 0 else float('inf'),
        'edge_reduction': (original_edges - final_edges) / original_edges if original_edges > 0 else 0,
    }
    
    return net3, stats
