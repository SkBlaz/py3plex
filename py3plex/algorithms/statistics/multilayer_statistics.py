#!/usr/bin/env python3
"""
Multilayer Network Statistics

This module implements various statistics for multilayer and multiplex networks,
following standard definitions from multilayer network analysis literature.

References:
    - Kivelä et al. (2014), "Multilayer networks", J. Complex Networks 2(3), 203-271
    - De Domenico et al. (2013), "Mathematical formulation of multilayer networks", PRX 3, 041022
    - Mucha et al. (2010), "Community Structure in Time-Dependent, Multiscale, and Multiplex Networks", Science 328, 876-878

Authors: py3plex contributors
Date: 2025
"""

from typing import Any, Dict, List, Optional, Tuple, Union

import networkx as nx
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh
from scipy.stats import pearsonr


def layer_density(network: Any, layer: str) -> float:
    """
    Calculate layer density (ρₐ).

    Formula: ρₐ = (2Eₐ) / (Nₐ(Nₐ - 1))  [undirected]
             ρₐ = Eₐ / (Nₐ(Nₐ - 1))      [directed]

    Measures the fraction of possible edges present in a specific layer, indicating
    how densely connected that layer is.

    Variables:
        Eₐ = number of edges in layer α
        Nₐ = number of nodes in layer α

    Args:
        network: py3plex multi_layer_network object
        layer: Layer identifier

    Returns:
        Density value between 0 and 1

    Examples:
        >>> from py3plex.core import multinet
        >>> network = multinet.multi_layer_network(directed=False)
        >>> network.add_edges([
        ...     ['A', 'L1', 'B', 'L1', 1],
        ...     ['B', 'L1', 'C', 'L1', 1]
        ... ], input_type='list')
        >>> density = layer_density(network, 'L1')
        >>> print(f"Layer L1 density: {density:.3f}")

    Reference:
        Kivelä et al. (2014), J. Complex Networks 2(3), 203-271
    """
    # Get nodes and edges in the specified layer
    layer_nodes = set()
    layer_edges = 0

    for edge in network.get_edges(data=True):
        (n1, l1), (n2, l2) = edge[0], edge[1]
        if l1 == layer and l2 == layer:
            layer_nodes.add(n1)
            layer_nodes.add(n2)
            if n1 != n2:  # Don't count self-loops for density
                layer_edges += 1

    num_nodes = len(layer_nodes)
    if num_nodes < 2:
        return 0.0

    # For undirected networks, each edge is counted once
    if not network.directed:
        max_edges = num_nodes * (num_nodes - 1) / 2
        density = layer_edges / max_edges
    else:
        max_edges = num_nodes * (num_nodes - 1)
        density = layer_edges / max_edges

    return float(density)


def inter_layer_coupling_strength(network: Any, layer_i: str, layer_j: str) -> float:
    """
    Calculate inter-layer coupling strength (C^αβ).

    Formula: C^αβ = (1/N_αβ) Σᵢ wᵢ^αβ

    Average weight of inter-layer connections between corresponding nodes in two layers.
    Quantifies cross-layer connectivity.

    Variables:
        N_αβ = number of nodes present in both layers α and β
        wᵢ^αβ = weight of inter-layer edge connecting node i in layer α to node i in layer β

    Args:
        network: py3plex multi_layer_network object
        layer_i: First layer identifier (α)
        layer_j: Second layer identifier (β)

    Returns:
        Average coupling strength

    Examples:
        >>> coupling = inter_layer_coupling_strength(network, 'L1', 'L2')

    Reference:
        De Domenico et al. (2013), Physical Review X 3(4), 041022
    """
    coupling_weights = []

    for edge in network.get_edges(data=True):
        (n1, l1), (n2, l2) = edge[0], edge[1]
        # Inter-layer edge between the two specified layers
        if (l1 == layer_i and l2 == layer_j) or (l1 == layer_j and l2 == layer_i):
            weight = edge[2].get("weight", 1.0) if len(edge) > 2 else 1.0
            coupling_weights.append(weight)

    if not coupling_weights:
        return 0.0

    return float(np.mean(coupling_weights))


def node_activity(network: Any, node: Any) -> float:
    """
    Calculate node activity (aᵢ).

    Formula: aᵢ = (1/L) Σₐ 𝟙(vᵢ ∈ Vₐ)

    Fraction of layers in which node i is active (has at least one connection).

    Variables:
        L = total number of layers
        𝟙(vᵢ ∈ Vₐ) = indicator function (1 if node i is active in layer α, 0 otherwise)
        Vₐ = set of active nodes in layer α

    Args:
        network: py3plex multi_layer_network object
        node: Node identifier

    Returns:
        Activity value between 0 and 1

    Examples:
        >>> activity = node_activity(network, 'A')

    Reference:
        Kivelä et al. (2014), J. Complex Networks 2(3), 203-271
    """
    # Get all layers
    all_layers = set()
    for n, layer in network.get_nodes():
        all_layers.add(layer)

    # Get layers where this node is active
    active_layers = set()
    for edge in network.get_edges():
        (n1, l1), (n2, l2) = edge[0], edge[1]
        if n1 == node:
            active_layers.add(l1)
        if n2 == node:
            active_layers.add(l2)

    if not all_layers:
        return 0.0

    return float(len(active_layers) / len(all_layers))


def degree_vector(network: Any, node: Any, weighted: bool = False) -> Dict[str, float]:
    """
    Calculate degree vector (kᵢ).

    Formula: kᵢ = (kᵢ¹, kᵢ², …, kᵢᴸ)

    Node degree in each layer; can be analyzed via mean, variance, or entropy
    to capture node versatility.

    Variables:
        kᵢᵅ = degree of node i in layer α
        For undirected: kᵢᵅ = Σⱼ Aᵢⱼᵅ

    Args:
        network: py3plex multi_layer_network object
        node: Node identifier
        weighted: If True, return strength instead of degree

    Returns:
        Dictionary mapping layer to degree/strength

    Examples:
        >>> degrees = degree_vector(network, 'A')
        >>> print(f"Degree in layer L1: {degrees['L1']}")

    Reference:
        Kivelä et al. (2014), J. Complex Networks 2(3), 203-271
    """
    # Get all layers
    all_layers = set()
    for n, layer in network.get_nodes():
        all_layers.add(layer)

    # Initialize degree vector
    degrees = {layer: 0.0 for layer in all_layers}

    # Count degrees/strengths
    for edge in network.get_edges(data=True):
        (n1, l1), (n2, l2) = edge[0], edge[1]
        weight = edge[2].get("weight", 1.0) if len(edge) > 2 and weighted else 1.0

        # Intra-layer edges
        if l1 == l2:
            if n1 == node:
                degrees[l1] += weight
            if n2 == node and n1 != n2:  # Don't double-count for undirected
                if network.directed or n1 != node:
                    degrees[l2] += weight

    return degrees


def inter_layer_degree_correlation(network: Any, layer_i: str, layer_j: str) -> float:
    """
    Calculate inter-layer degree correlation (r^αβ).

    Formula: r^αβ = Σᵢ(kᵢᵅ - k̄ᵅ)(kᵢᵝ - k̄ᵝ) / [√(Σᵢ(kᵢᵅ - k̄ᵅ)²) √(Σᵢ(kᵢᵝ - k̄ᵝ)²)]

    Pearson correlation of node degrees between two layers; reveals if highly
    connected nodes in one layer are also central in others.

    Variables:
        kᵢᵅ = degree of node i in layer α
        k̄ᵅ = mean degree in layer α
        Sum over nodes present in both layers

    Args:
        network: py3plex multi_layer_network object
        layer_i: First layer identifier (α)
        layer_j: Second layer identifier (β)

    Returns:
        Pearson correlation coefficient between -1 and 1

    Examples:
        >>> corr = inter_layer_degree_correlation(network, 'L1', 'L2')

    Reference:
        Battiston et al. (2014), Nicosia & Latora (2015)
    """
    # Get nodes present in both layers
    nodes_i = set()
    nodes_j = set()

    for n, layer in network.get_nodes():
        if layer == layer_i:
            nodes_i.add(n)
        if layer == layer_j:
            nodes_j.add(n)

    common_nodes = nodes_i & nodes_j

    if len(common_nodes) < 2:
        return 0.0

    # Calculate degrees in each layer
    degrees_i = []
    degrees_j = []

    for node in sorted(common_nodes):
        deg_vec = degree_vector(network, node)
        degrees_i.append(deg_vec.get(layer_i, 0))
        degrees_j.append(deg_vec.get(layer_j, 0))

    # Calculate correlation
    if np.std(degrees_i) == 0 or np.std(degrees_j) == 0:
        return 0.0

    correlation, _ = pearsonr(degrees_i, degrees_j)
    return float(correlation)


def edge_overlap(network: Any, layer_i: str, layer_j: str) -> float:
    """
    Calculate edge overlap (ω^αβ).

    Formula: ω^αβ = |Eₐ ∩ Eᵦ| / |Eₐ ∪ Eᵦ|

    Jaccard similarity of edge sets between two layers; measures structural redundancy.

    Variables:
        Eₐ = set of edges in layer α
        Eᵦ = set of edges in layer β
        |·| = cardinality (number of elements)

    Args:
        network: py3plex multi_layer_network object
        layer_i: First layer identifier (α)
        layer_j: Second layer identifier (β)

    Returns:
        Overlap coefficient between 0 and 1 (Jaccard similarity)

    Examples:
        >>> overlap = edge_overlap(network, 'L1', 'L2')

    Reference:
        Kivelä et al. (2014), J. Complex Networks 2(3), 203-271
    """
    # Get edges in each layer (as unordered node pairs)
    edges_i = set()
    edges_j = set()

    for edge in network.get_edges():
        (n1, l1), (n2, l2) = edge[0], edge[1]

        # Only consider intra-layer edges
        if l1 == l2 == layer_i:
            # Store as sorted tuple for undirected comparison
            edge_pair = tuple(sorted([n1, n2])) if not network.directed else (n1, n2)
            edges_i.add(edge_pair)
        elif l1 == l2 == layer_j:
            edge_pair = tuple(sorted([n1, n2])) if not network.directed else (n1, n2)
            edges_j.add(edge_pair)

    # Calculate Jaccard similarity
    intersection = edges_i & edges_j
    union = edges_i | edges_j

    if not union:
        return 0.0

    return float(len(intersection) / len(union))


def layer_similarity(
    network: Any, layer_i: str, layer_j: str, method: str = "cosine"
) -> float:
    """
    Calculate layer similarity (S^αβ).

    Formula: S^αβ = ⟨Aₐ, Aᵦ⟩ / (‖Aₐ‖ ‖Aᵦ‖) = Σᵢⱼ AᵢⱼᵅAᵢⱼᵝ / √(Σᵢⱼ(Aᵢⱼᵅ)²) √(Σᵢⱼ(Aᵢⱼᵝ)²)

    Cosine or Jaccard similarity between adjacency matrices of two layers.

    Variables:
        Aₐ, Aᵦ = adjacency matrices for layers α and β
        ⟨·,·⟩ = Frobenius inner product
        ‖·‖ = Frobenius norm

    Args:
        network: py3plex multi_layer_network object
        layer_i: First layer identifier (α)
        layer_j: Second layer identifier (β)
        method: 'cosine' or 'jaccard'

    Returns:
        Similarity value between 0 and 1

    Examples:
        >>> similarity = layer_similarity(network, 'L1', 'L2', method='cosine')

    Reference:
        De Domenico et al. (2013), Physical Review X 3(4), 041022
    """
    if method == "jaccard":
        # Use edge overlap for Jaccard
        return edge_overlap(network, layer_i, layer_j)

    # Get common nodes
    nodes_i = set()
    nodes_j = set()

    for n, layer in network.get_nodes():
        if layer == layer_i:
            nodes_i.add(n)
        if layer == layer_j:
            nodes_j.add(n)

    common_nodes = sorted(nodes_i & nodes_j)

    if len(common_nodes) < 2:
        return 0.0

    # Build adjacency matrices for common nodes
    n = len(common_nodes)
    node_to_idx = {node: idx for idx, node in enumerate(common_nodes)}

    adj_i = np.zeros((n, n))
    adj_j = np.zeros((n, n))

    for edge in network.get_edges(data=True):
        (n1, l1), (n2, l2) = edge[0], edge[1]
        weight = edge[2].get("weight", 1.0) if len(edge) > 2 else 1.0

        if l1 == l2 == layer_i and n1 in node_to_idx and n2 in node_to_idx:
            adj_i[node_to_idx[n1], node_to_idx[n2]] = weight
        elif l1 == l2 == layer_j and n1 in node_to_idx and n2 in node_to_idx:
            adj_j[node_to_idx[n1], node_to_idx[n2]] = weight

    # Flatten matrices
    vec_i = adj_i.flatten()
    vec_j = adj_j.flatten()

    # Calculate cosine similarity
    norm_i = np.linalg.norm(vec_i)
    norm_j = np.linalg.norm(vec_j)

    if norm_i == 0 or norm_j == 0:
        return 0.0

    cosine_sim = np.dot(vec_i, vec_j) / (norm_i * norm_j)
    return float(cosine_sim)


def multilayer_clustering_coefficient(
    network: Any, node: Optional[Any] = None
) -> Union[float, Dict[Any, float]]:
    """
    Calculate multilayer clustering coefficient (Cᴹ).

    Formula: Cᵢᴹ = Tᵢ / Tᵢᵐᵃˣ

    Extends transitivity to account for triangles that span multiple layers.

    Variables:
        Tᵢ = number of closed triplets (triangles) involving node i across all layers
        Tᵢᵐᵃˣ = maximum possible triplets = Σₐ kᵢᵅ(kᵢᵅ - 1)/2 for undirected networks
        Average over all nodes: Cᴹ = (1/N) Σᵢ Cᵢᴹ

    Args:
        network: py3plex multi_layer_network object
        node: If specified, compute for single node; otherwise compute for all

    Returns:
        Clustering coefficient value or dict of values per node

    Examples:
        >>> clustering = multilayer_clustering_coefficient(network)
        >>> node_clustering = multilayer_clustering_coefficient(network, node='A')

    Reference:
        Battiston et al. (2014), Section III.C
    """
    # Build neighbor sets for each node-layer pair
    neighbors: Dict[tuple, set] = {}
    all_node_layers = set()

    for edge in network.get_edges():
        (n1, l1), (n2, l2) = edge[0], edge[1]

        # Only consider intra-layer edges for triangle counting
        if l1 == l2:
            nl1 = (n1, l1)
            nl2 = (n2, l2)

            all_node_layers.add(nl1)
            all_node_layers.add(nl2)

            if nl1 not in neighbors:
                neighbors[nl1] = set()
            if nl2 not in neighbors:
                neighbors[nl2] = set()

            neighbors[nl1].add(nl2)
            if not network.directed:
                neighbors[nl2].add(nl1)

    def count_triangles(node_layer):
        """Count triangles involving a node-layer pair."""
        if node_layer not in neighbors:
            return 0, 0

        nbrs = neighbors[node_layer]
        if len(nbrs) < 2:
            return 0, 0

        # Count triangles
        triangles = 0
        for n1 in nbrs:
            for n2 in nbrs:
                if n1 != n2 and n2 in neighbors.get(n1, set()):
                    triangles += 1

        # Each triangle is counted twice in undirected graphs
        if not network.directed:
            triangles = triangles // 2

        # Possible triplets
        possible = len(nbrs) * (len(nbrs) - 1)
        if not network.directed:
            possible = possible // 2

        return triangles, possible

    if node is not None:
        # Calculate for specific node across all layers
        total_triangles = 0
        total_possible = 0

        for n, layer in all_node_layers:
            if n == node:
                tri, poss = count_triangles((n, layer))
                total_triangles += tri
                total_possible += poss

        if total_possible == 0:
            return 0.0

        return float(total_triangles / total_possible)

    # Calculate for all nodes
    clustering_coeffs = {}

    # Group by node
    nodes = set(n for n, _ in all_node_layers)

    for n in nodes:
        total_triangles = 0
        total_possible = 0

        for nl in all_node_layers:
            if nl[0] == n:
                tri, poss = count_triangles(nl)
                total_triangles += tri
                total_possible += poss

        if total_possible > 0:
            clustering_coeffs[n] = float(total_triangles / total_possible)
        else:
            clustering_coeffs[n] = 0.0

    return clustering_coeffs


def versatility_centrality(
    network: Any,
    centrality_type: str = "degree",
    alpha: Optional[Dict[str, float]] = None,
) -> Dict[Any, float]:
    """
    Calculate versatility centrality (Vᵢ).

    Formula: Vᵢ = Σₐ wₐ Cᵢᵅ

    Weighted combination of node centrality values across layers; measures overall influence.

    Variables:
        wₐ = weight for layer α (typically 1/L for uniform weighting, Σₐ wₐ = 1)
        Cᵢᵅ = centrality of node i in layer α (can be degree, betweenness, closeness, etc.)

    Args:
        network: py3plex multi_layer_network object
        centrality_type: Type of centrality ('degree', 'betweenness', 'closeness')
        alpha: Layer weights (default: uniform weights)

    Returns:
        Dictionary mapping nodes to versatility centrality values

    Examples:
        >>> versatility = versatility_centrality(network, centrality_type='degree')

    Reference:
        De Domenico et al. (2015), Nature Communications 6, 6868
    """
    # Get all layers
    all_layers = set()
    for n, layer in network.get_nodes():
        all_layers.add(layer)

    # Set uniform weights if not provided
    if alpha is None:
        alpha = {layer: 1.0 / len(all_layers) for layer in all_layers}

    # Get all unique nodes
    all_nodes = set(n for n, _ in network.get_nodes())

    # Calculate centrality for each layer
    layer_centralities = {}

    for layer in all_layers:
        # Build subgraph for this layer
        layer_edges = []
        for edge in network.get_edges(data=True):
            (n1, l1), (n2, l2) = edge[0], edge[1]
            if l1 == l2 == layer:
                weight = edge[2].get("weight", 1.0) if len(edge) > 2 else 1.0
                layer_edges.append((n1, n2, {"weight": weight}))

        if not layer_edges:
            layer_centralities[layer] = {node: 0.0 for node in all_nodes}
            continue

        # Create NetworkX graph for this layer
        if network.directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()
        G.add_edges_from(layer_edges)

        # Calculate centrality
        try:
            if centrality_type == "degree":
                cent = nx.degree_centrality(G)
            elif centrality_type == "betweenness":
                cent = nx.betweenness_centrality(G, weight="weight")
            elif centrality_type == "closeness":
                cent = nx.closeness_centrality(G, distance="weight")
            else:
                cent = nx.degree_centrality(G)

            # Fill in zeros for nodes not in this layer
            layer_centralities[layer] = {
                node: cent.get(node, 0.0) for node in all_nodes
            }
        except:
            layer_centralities[layer] = {node: 0.0 for node in all_nodes}

    # Calculate versatility centrality
    versatility = {}
    for node in all_nodes:
        v = sum(
            alpha.get(layer, 0.0) * layer_centralities[layer][node]
            for layer in all_layers
        )
        versatility[node] = float(v)

    return versatility


def interdependence(network: Any, sample_size: int = 100) -> float:
    """
    Calculate interdependence (λ).

    Formula: λ = ⟨dᴹᴸ⟩ / ⟨dᵃᵛᵍ⟩

    Quantifies how much shortest-path communication depends on inter-layer connections.

    Variables:
        dᵢⱼᴹᴸ = shortest path from node i to node j in the full multilayer network
        dᵢⱼᵃᵛᵍ = (1/L) Σₐ dᵢⱼᵅ is the average shortest path across individual layers
        ⟨·⟩ = average over sampled node pairs

    Interpretation:
        λ < 1: multilayer connectivity reduces path lengths (positive interdependence)
        λ ≈ 1: inter-layer connections provide little benefit
        λ > 1: multilayer structure increases path lengths (rare)

    Args:
        network: py3plex multi_layer_network object
        sample_size: Number of node pairs to sample for estimation

    Returns:
        Interdependence ratio

    Examples:
        >>> interdep = interdependence(network, sample_size=50)

    Reference:
        Gomez et al. (2013), Buldyrev et al. (2010)
    """
    # Get all layers
    all_layers = set()
    for n, layer in network.get_nodes():
        all_layers.add(layer)

    # Get all unique nodes
    all_nodes = list(set(n for n, _ in network.get_nodes()))

    if len(all_nodes) < 2:
        return 0.0

    # Build full multilayer graph
    full_graph = nx.Graph() if not network.directed else nx.DiGraph()
    for edge in network.get_edges(data=True):
        (n1, l1), (n2, l2) = edge[0], edge[1]
        weight = edge[2].get("weight", 1.0) if len(edge) > 2 else 1.0
        # Use node-layer tuples as nodes in the graph
        full_graph.add_edge((n1, l1), (n2, l2), weight=weight)

    # Build layer-specific graphs
    layer_graphs = {}
    for layer in all_layers:
        if network.directed:
            G = nx.DiGraph()
        else:
            G = nx.Graph()

        for edge in network.get_edges(data=True):
            (n1, l1), (n2, l2) = edge[0], edge[1]
            if l1 == l2 == layer:
                weight = edge[2].get("weight", 1.0) if len(edge) > 2 else 1.0
                G.add_edge(n1, n2, weight=weight)

        layer_graphs[layer] = G

    # Sample node pairs
    sample_size = min(sample_size, len(all_nodes) * (len(all_nodes) - 1) // 2)

    multiplex_paths = []
    layer_paths = []

    np.random.seed(42)  # For reproducibility
    sampled_pairs: set = set()

    while len(sampled_pairs) < sample_size:
        n1, n2 = np.random.choice(all_nodes, size=2, replace=False)
        if (n1, n2) not in sampled_pairs and (n2, n1) not in sampled_pairs:
            sampled_pairs.add((n1, n2))

    for n1, n2 in sampled_pairs:
        # Multiplex shortest path (across all node-layer pairs)
        min_multiplex = float("inf")
        for l1 in all_layers:
            for l2 in all_layers:
                if (n1, l1) in full_graph and (n2, l2) in full_graph:
                    try:
                        path_len = nx.shortest_path_length(
                            full_graph, (n1, l1), (n2, l2), weight="weight"
                        )
                        min_multiplex = min(min_multiplex, path_len)
                    except nx.NetworkXNoPath:
                        pass

        if min_multiplex < float("inf"):
            multiplex_paths.append(min_multiplex)

        # Average shortest path across individual layers
        layer_path_lengths = []
        for layer in all_layers:
            G = layer_graphs[layer]
            if n1 in G and n2 in G:
                try:
                    path_len = nx.shortest_path_length(G, n1, n2, weight="weight")
                    layer_path_lengths.append(path_len)
                except nx.NetworkXNoPath:
                    pass

        if layer_path_lengths:
            layer_paths.append(np.mean(layer_path_lengths))

    if not multiplex_paths or not layer_paths:
        return 1.0

    avg_multiplex = np.mean(multiplex_paths)
    avg_layers = np.mean(layer_paths)

    if avg_layers == 0:
        return 1.0

    return float(avg_multiplex / avg_layers)


def supra_laplacian_spectrum(network: Any, k: int = 10) -> np.ndarray:
    """
    Calculate supra-Laplacian spectrum (Λ).

    Formula: ℒ = 𝒟 - 𝒜

    Eigenvalue spectrum of the supra-Laplacian matrix; captures diffusion properties.

    Variables:
        𝒜 = supra-adjacency matrix (NL × NL block matrix containing all layers and inter-layer couplings)
        𝒟 = supra-degree matrix (diagonal matrix with row sums of 𝒜)
        ℒ = supra-Laplacian matrix
        Λ = {λ₀, λ₁, ..., λₙₗ₋₁} with 0 = λ₀ ≤ λ₁ ≤ ... ≤ λₙₗ₋₁

    Args:
        network: py3plex multi_layer_network object
        k: Number of smallest eigenvalues to compute

    Returns:
        Array of k smallest eigenvalues

    Examples:
        >>> spectrum = supra_laplacian_spectrum(network, k=10)

    Reference:
        De Domenico et al. (2013), Gomez et al. (2013)
    """
    # Get supra-adjacency matrix
    supra_adj = network.get_supra_adjacency_matrix()

    # Convert to dense if sparse for small networks
    if sp.issparse(supra_adj):
        if supra_adj.shape[0] < 1000:
            supra_adj = supra_adj.toarray()

    # Calculate degree matrix
    if sp.issparse(supra_adj):
        degrees = np.array(supra_adj.sum(axis=1)).flatten()
        degree_matrix = sp.diags(degrees)
        laplacian = degree_matrix - supra_adj
    else:
        degrees = np.sum(supra_adj, axis=1)
        degree_matrix = np.diag(degrees)
        laplacian = degree_matrix - supra_adj

    # Calculate eigenvalues
    k = min(k, laplacian.shape[0] - 2)

    if k < 1:
        empty_result: np.ndarray = np.array([])
        return empty_result

    try:
        if sp.issparse(laplacian):
            eigenvalues, _ = eigsh(laplacian, k=k, which="SM")
        else:
            all_eigenvalues = np.linalg.eigvalsh(laplacian)
            eigenvalues = np.sort(all_eigenvalues)[:k]

        result: np.ndarray = eigenvalues
        return result
    except:
        empty_except: np.ndarray = np.array([])
        return empty_except


def algebraic_connectivity(network: Any) -> float:
    """
    Calculate algebraic connectivity (λ₂).

    Formula: λ₂(ℒ)

    Second smallest eigenvalue of the supra-Laplacian (Fiedler value).

    Indicates global connectivity and diffusion efficiency of the multilayer system.

    Properties:
        λ₀ = 0 always (associated with constant eigenvector)
        λ₁ > 0 if and only if the multilayer network is connected
        Larger λ₁ indicates better connectivity and faster diffusion/synchronization

    Args:
        network: py3plex multi_layer_network object

    Returns:
        Second smallest eigenvalue (Fiedler value)

    Examples:
        >>> alg_conn = algebraic_connectivity(network)

    Reference:
        Fiedler (1973), Sole-Ribalta et al. (2013)
    """
    spectrum = supra_laplacian_spectrum(network, k=2)

    if len(spectrum) < 2:
        return 0.0

    return float(spectrum[1])


def inter_layer_assortativity(network: Any, layer_i: str, layer_j: str) -> float:
    """
    Calculate inter-layer assortativity (rᴵ).

    Formula: r^αβ = cov(k^α, k^β) / (σₐ σᵦ) = corr(k^α, k^β)

    Measures whether nodes with similar degrees tend to connect across different layers.

    Variables:
        k^α = degree vector in layer α
        k^β = degree vector in layer β
        σₐ, σᵦ = standard deviations of degrees in layers α and β
        Equivalent to Pearson correlation of degree vectors

    Args:
        network: py3plex multi_layer_network object
        layer_i: First layer identifier (α)
        layer_j: Second layer identifier (β)

    Returns:
        Assortativity coefficient

    Examples:
        >>> assort = inter_layer_assortativity(network, 'L1', 'L2')

    Reference:
        Newman (2002), Nicosia & Latora (2015)
    """
    # This is essentially the same as inter-layer degree correlation
    return inter_layer_degree_correlation(network, layer_i, layer_j)


def entropy_of_multiplexity(network: Any) -> float:
    """
    Calculate entropy of multiplexity (Hₘ).

    Formula: Hₘ = -Σₐ pₐ log₂(pₐ), where pₐ = Eₐ / Σᵦ Eᵦ

    Shannon entropy of layer contributions; measures layer diversity.

    Variables:
        pₐ = proportion of edges in layer α
        Eₐ = number of edges in layer α
        log₂ gives entropy in bits

    Properties:
        Hₘ = 0 when all edges are in one layer (minimum entropy/diversity)
        Hₘ = log₂(L) when edges are uniformly distributed across L layers (maximum entropy)

    Args:
        network: py3plex multi_layer_network object

    Returns:
        Entropy value in bits

    Examples:
        >>> entropy = entropy_of_multiplexity(network)

    Reference:
        De Domenico et al. (2013), Shannon (1948)
    """
    # Count edges per layer
    layer_edge_counts: Dict[str, int] = {}

    for edge in network.get_edges():
        (n1, l1), (n2, l2) = edge[0], edge[1]
        # Only count intra-layer edges
        if l1 == l2:
            layer_edge_counts[l1] = layer_edge_counts.get(l1, 0) + 1

    if not layer_edge_counts:
        return 0.0

    total_edges = sum(layer_edge_counts.values())

    if total_edges == 0:
        return 0.0

    # Calculate entropy
    entropy = 0.0
    for count in layer_edge_counts.values():
        p = count / total_edges
        if p > 0:
            entropy -= p * np.log2(p)

    return float(entropy)


def multilayer_motif_frequency(network: Any, motif_size: int = 3) -> Dict[str, float]:
    """
    Calculate multilayer motif frequency (fₘ).

    Formula: fₘ = nₘ / Σₖ nₖ

    Frequency of recurring subgraph patterns across layers.

    Variables:
        nₘ = count of motif type m
        Σₖ nₖ = total count of all motifs

    Note: This is a simplified implementation counting basic patterns (intra-layer vs.
    inter-layer triangles). Complete multilayer motif enumeration includes many more
    configurations and is computationally expensive.

    Args:
        network: py3plex multi_layer_network object
        motif_size: Size of motifs to count (default: 3 for triangles)

    Returns:
        Dictionary of motif type frequencies

    Examples:
        >>> motifs = multilayer_motif_frequency(network, motif_size=3)

    Reference:
        Battiston et al. (2014), Section IV
    """
    if motif_size != 3:
        # Only triangles implemented for now
        return {"not_implemented": 0.0}

    # Count different types of triangles
    motif_counts: Dict[str, float] = {
        "intra_layer_triangles": 0.0,
        "inter_layer_triangles": 0.0,
    }

    # Get all node-layer pairs
    node_layers = list(network.get_nodes())

    # Build adjacency
    adj: Dict[tuple, set] = {}
    for edge in network.get_edges():
        (n1, l1), (n2, l2) = edge[0], edge[1]
        nl1 = (n1, l1)
        nl2 = (n2, l2)

        if nl1 not in adj:
            adj[nl1] = set()
        if nl2 not in adj:
            adj[nl2] = set()

        adj[nl1].add(nl2)
        if not network.directed:
            adj[nl2].add(nl1)

    # Count triangles
    for nl1 in node_layers:
        if nl1 not in adj:
            continue

        for nl2 in adj[nl1]:
            for nl3 in adj[nl1]:
                if nl2 != nl3 and nl3 in adj.get(nl2, set()):
                    # Found a triangle
                    layers = {nl1[1], nl2[1], nl3[1]}
                    if len(layers) == 1:
                        motif_counts["intra_layer_triangles"] += 1
                    else:
                        motif_counts["inter_layer_triangles"] += 1

    # Each triangle is counted 6 times (3 nodes × 2 directions)
    for key in motif_counts:
        motif_counts[key] = motif_counts[key] / 6.0

    # Calculate frequencies
    total = sum(motif_counts.values())
    if total == 0:
        return {k: 0.0 for k in motif_counts}

    return {k: float(v / total) for k, v in motif_counts.items()}


def resilience(
    network: Any,
    perturbation_type: str = "layer_removal",
    perturbation_param: Union[str, float] = None,
) -> float:
    """
    Calculate resilience (R).

    Formula: R = S' / S₀

    Ratio of largest connected component after perturbation to original size.

    Variables:
        S₀ = size of largest connected component in original network
        S' = size of largest connected component after perturbation

    Perturbation types:
        1. Layer removal: Remove all nodes/edges in a specific layer
        2. Coupling removal: Remove a fraction of inter-layer edges

    Properties:
        R = 1 indicates full resilience (no impact from perturbation)
        R = 0 indicates complete fragmentation
        0 < R < 1 indicates partial resilience

    Args:
        network: py3plex multi_layer_network object
        perturbation_type: 'layer_removal' or 'coupling_removal'
        perturbation_param: Layer to remove or fraction of inter-layer edges

    Returns:
        Resilience ratio between 0 and 1

    Examples:
        >>> r = resilience(network, 'layer_removal', perturbation_param='L1')
        >>> r = resilience(network, 'coupling_removal', perturbation_param=0.5)

    Reference:
        Buldyrev et al. (2010), Nature 464, 1025-1028
    """
    # Build full network graph
    original_graph = nx.Graph() if not network.directed else nx.DiGraph()

    for edge in network.get_edges(data=True):
        (n1, l1), (n2, l2) = edge[0], edge[1]
        weight = edge[2].get("weight", 1.0) if len(edge) > 2 else 1.0
        original_graph.add_edge((n1, l1), (n2, l2), weight=weight)

    # Calculate original largest component size
    if original_graph.number_of_nodes() == 0:
        return 1.0

    if network.directed:
        components = list(nx.weakly_connected_components(original_graph))
    else:
        components = list(nx.connected_components(original_graph))

    original_size = max(len(c) for c in components) if components else 0

    # Apply perturbation
    perturbed_graph = original_graph.copy()

    if perturbation_type == "layer_removal" and perturbation_param is not None:
        # Remove all nodes in the specified layer
        nodes_to_remove = [
            (n, l) for n, l in perturbed_graph.nodes() if l == perturbation_param
        ]
        perturbed_graph.remove_nodes_from(nodes_to_remove)

    elif perturbation_type == "coupling_removal" and perturbation_param is not None:
        # Remove fraction of inter-layer edges
        inter_layer_edges = [
            (n1, n2)
            for n1, n2 in perturbed_graph.edges()
            if n1[1] != n2[1]  # Different layers
        ]

        num_to_remove = int(len(inter_layer_edges) * perturbation_param)
        np.random.seed(42)
        edges_to_remove = np.random.choice(
            len(inter_layer_edges), size=num_to_remove, replace=False
        )
        edges_to_remove = [inter_layer_edges[i] for i in edges_to_remove]
        perturbed_graph.remove_edges_from(edges_to_remove)

    # Calculate perturbed largest component size
    if perturbed_graph.number_of_nodes() == 0:
        return 0.0

    if network.directed:
        components = list(nx.weakly_connected_components(perturbed_graph))
    else:
        components = list(nx.connected_components(perturbed_graph))

    perturbed_size = max(len(c) for c in components) if components else 0

    if original_size == 0:
        return 1.0

    return float(perturbed_size / original_size)


def multilayer_modularity(
    network: Any,
    communities: Dict[Tuple[Any, Any], int],
    gamma: Union[float, Dict[Any, float]] = 1.0,
    omega: Union[float, np.ndarray] = 1.0,
    weight: str = "weight",
) -> float:
    """
    Calculate multilayer modularity (Qᴹᴸ).

    This is a wrapper for the existing multilayer_modularity implementation
    in py3plex.algorithms.community_detection.multilayer_modularity.

    Formula: Qᴹᴸ = (1/2μ) Σᵢⱼₐᵦ [(Aᵢⱼᵅ - γₐPᵢⱼᵅ)δₐᵦ + ωₐᵦδᵢⱼ] δ(gᵢᵅ, gⱼᵝ)

    Extension of Newman-Girvan modularity to multiplex networks (Mucha et al., 2010).
    Measures community quality across layers.

    Variables:
        μ = total edge weight in supra-network
        Aᵢⱼᵅ = adjacency matrix element for layer α
        Pᵢⱼᵅ = kᵢᵅkⱼᵅ/(2mₐ) is the null model (configuration model)
        γₐ = resolution parameter for layer α
        ωₐᵦ = inter-layer coupling strength
        δₐᵦ = Kronecker delta (1 if α=β, 0 otherwise)
        δᵢⱼ = Kronecker delta (1 if i=j, 0 otherwise)
        δ(gᵢᵅ, gⱼᵝ) = 1 if node i in layer α and node j in layer β are in same community

    Args:
        network: py3plex multi_layer_network object
        communities: Dictionary mapping (node, layer) tuples to community IDs
        gamma: Resolution parameter(s)
        omega: Inter-layer coupling strength
        weight: Edge weight attribute

    Returns:
        Modularity value Q

    Examples:
        >>> communities = {('A', 'L1'): 0, ('B', 'L1'): 0, ('C', 'L1'): 1}
        >>> Q = multilayer_modularity(network, communities)

    Reference:
        Mucha et al. (2010), Science 328(5980), 876-878
    """
    from py3plex.algorithms.community_detection.multilayer_modularity import (
        multilayer_modularity as mm,
    )

    return mm(network, communities, gamma, omega, weight)


# Export all functions
__all__ = [
    "layer_density",
    "inter_layer_coupling_strength",
    "node_activity",
    "degree_vector",
    "inter_layer_degree_correlation",
    "edge_overlap",
    "layer_similarity",
    "multilayer_clustering_coefficient",
    "versatility_centrality",
    "interdependence",
    "multilayer_modularity",
    "supra_laplacian_spectrum",
    "algebraic_connectivity",
    "inter_layer_assortativity",
    "entropy_of_multiplexity",
    "multilayer_motif_frequency",
    "resilience",
]
