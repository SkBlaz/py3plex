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

from typing import Any, Dict, Optional, Tuple, Union

import networkx as nx
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh
from scipy.stats import pearsonr

# Optional formal verification support
try:
    from icontract import ensure, require

    ICONTRACT_AVAILABLE = True
except ImportError:
    # Create no-op decorators when icontract is not available
    def require(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def ensure(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    ICONTRACT_AVAILABLE = False


@require(lambda network: network is not None, "network must not be None")
@require(
    lambda network: hasattr(network, "get_edges"), "network must have get_edges method"
)
@require(
    lambda layer: isinstance(layer, str) and len(layer) > 0,
    "layer must be a non-empty string",
)
@ensure(lambda result: 0.0 <= result <= 1.0, "density must be between 0 and 1")
@ensure(lambda result: not np.isnan(result), "density must not be NaN")
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

    Contracts:
        - Precondition: network must not be None
        - Precondition: layer must be a non-empty string
        - Postcondition: result is in [0, 1] (fundamental property of density)
        - Postcondition: result is not NaN
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


@require(lambda network: network is not None, "network must not be None")
@require(
    lambda network: hasattr(network, "get_edges"), "network must have get_edges method"
)
@require(
    lambda layer_i: isinstance(layer_i, str) and len(layer_i) > 0,
    "layer_i must be a non-empty string",
)
@require(
    lambda layer_j: isinstance(layer_j, str) and len(layer_j) > 0,
    "layer_j must be a non-empty string",
)
@ensure(lambda result: result >= 0.0, "coupling strength must be non-negative")
@ensure(lambda result: not np.isnan(result), "coupling strength must not be NaN")
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

    Contracts:
        - Precondition: network must not be None
        - Precondition: layer_i and layer_j must be non-empty strings
        - Postcondition: result is non-negative (weights are non-negative)
        - Postcondition: result is not NaN
    """
    coupling_weights = []

    for edge in network.get_edges(data=True):
        (_, l1), (_, l2) = edge[0], edge[1]
        # Inter-layer edge between the two specified layers
        if (l1 == layer_i and l2 == layer_j) or (l1 == layer_j and l2 == layer_i):
            weight = edge[2].get("weight", 1.0) if len(edge) > 2 else 1.0
            coupling_weights.append(weight)

    if not coupling_weights:
        return 0.0

    return float(np.mean(coupling_weights))


@require(lambda network: network is not None, "network must not be None")
@require(
    lambda network: hasattr(network, "get_nodes") and hasattr(network, "get_edges"),
    "network must have get_nodes and get_edges methods",
)
@require(lambda node: node is not None, "node must not be None")
@ensure(lambda result: 0.0 <= result <= 1.0, "activity must be between 0 and 1")
@ensure(lambda result: not np.isnan(result), "activity must not be NaN")
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

    Contracts:
        - Precondition: network must not be None
        - Precondition: node must not be None
        - Postcondition: result is in [0, 1] (fraction of layers)
        - Postcondition: result is not NaN
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
    degrees = dict.fromkeys(all_layers, 0.0)

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

    def count_triangles(node_layer: Tuple[Any, Any]) -> Tuple[int, int]:
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
    nodes = {n for n, _ in all_node_layers}

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
    all_nodes = {n for n, _ in network.get_nodes()}

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
            layer_centralities[layer] = dict.fromkeys(all_nodes, 0.0)
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
        except Exception:
            # If centrality calculation fails, use zeros
            layer_centralities[layer] = dict.fromkeys(all_nodes, 0.0)

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
    all_nodes = list({n for n, _ in network.get_nodes()})

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
    Uses sparse eigenvalue computation when beneficial.

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

    Notes:
        - Uses sparse eigsh() for sparse matrices (more efficient)
        - Falls back to dense computation for small matrices (n < 100) or when k is large relative to n
        - Laplacian is always symmetric for undirected graphs (PSD with smallest eigenvalue = 0)
    """
    # Get supra-adjacency matrix
    supra_adj = network.get_supra_adjacency_matrix()
    n = supra_adj.shape[0]

    # Determine if we should use sparse or dense computation
    # Sparse is beneficial when: matrix is sparse, n is large, and k is much smaller than n
    # Threshold k < n//2 chosen empirically: eigsh() overhead worth it when computing < half eigenvalues
    use_sparse = sp.issparse(supra_adj) and n >= 100 and k < n // 2

    # Calculate degree matrix and Laplacian
    if use_sparse:
        # Keep as sparse
        degrees = np.array(supra_adj.sum(axis=1)).flatten()
        degree_matrix = sp.diags(degrees, format='csr')
        laplacian = degree_matrix - supra_adj
    else:
        # Convert to dense
        if sp.issparse(supra_adj):
            supra_adj = supra_adj.toarray()
        degrees = np.sum(supra_adj, axis=1)
        degree_matrix = np.diag(degrees)
        laplacian = degree_matrix - supra_adj

    # Adjust k to be valid
    k = min(k, n - 2)

    if k < 1:
        return np.array([])

    try:
        if use_sparse:
            # Use sparse eigenvalue solver (eigsh for symmetric matrices)
            eigenvalues, _ = eigsh(laplacian, k=k, which="SM", tol=1e-10)
            # Sort eigenvalues (eigsh may not return them sorted)
            eigenvalues = np.sort(eigenvalues)
        else:
            # Dense computation - get all eigenvalues then select smallest k
            all_eigenvalues = np.linalg.eigvalsh(laplacian)
            eigenvalues = np.sort(all_eigenvalues)[:k]

        return eigenvalues
    except Exception:
        return np.array([])


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
        (_, l1), (_, l2) = edge[0], edge[1]
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
        return dict.fromkeys(motif_counts, 0.0)

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
        edge_indices = np.random.choice(
            len(inter_layer_edges), size=num_to_remove, replace=False
        )
        edges_to_remove = [inter_layer_edges[i] for i in edge_indices]
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


def multiplex_betweenness_centrality(
    network: Any, normalized: bool = True, weight: Optional[str] = None
) -> Dict[Tuple[Any, Any], float]:
    """
    Calculate multiplex betweenness centrality.

    Computes betweenness centrality on the supra-graph, accounting for paths
    that traverse inter-layer couplings. This extends the standard betweenness
    definition to multiplex networks where paths can cross layers.

    Formula: Bᵢᵅ = Σₛ≠ᵢ≠ₜ (σₛₜ(iα) / σₛₜ)

    where σₛₜ is the total number of shortest paths from s to t, and
    σₛₜ(iα) is the number of those paths passing through node i in layer α.

    Args:
        network: py3plex multi_layer_network object
        normalized: Whether to normalize by the number of node pairs
        weight: Edge weight attribute name (None for unweighted)

    Returns:
        Dictionary mapping (node, layer) tuples to betweenness centrality values

    Examples:
        >>> betweenness = multiplex_betweenness_centrality(network)
        >>> top_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]

    Reference:
        De Domenico et al. (2015), "Structural reducibility of multilayer networks"
    """
    G = network.core_network
    if G is None or len(G) == 0:
        return {}
    betweenness = nx.betweenness_centrality(G, normalized=normalized, weight=weight)
    return betweenness


def multiplex_closeness_centrality(
    network: Any, normalized: bool = True, weight: Optional[str] = None,
    variant: str = "standard"
) -> Dict[Tuple[Any, Any], float]:
    """
    Calculate multiplex closeness centrality.

    Computes closeness centrality on the supra-graph, where shortest paths
    can traverse inter-layer edges. This captures how quickly a node-layer
    can reach all other node-layers in the multiplex network.

    Standard closeness formula: Cᵢᵅ = (N*L - 1) / Σⱼᵝ≠ᵢᵅ d(iα, jβ)

    Harmonic closeness formula: HCᵢᵅ = Σⱼᵝ≠ᵢᵅ 1/d(iα, jβ)

    where d(iα, jβ) is the shortest path distance from node i in layer α
    to node j in layer β, and N*L is the total number of node-layer pairs.

    Args:
        network: py3plex multi_layer_network object
        normalized: Whether to normalize by network size
        weight: Edge weight attribute name (None for unweighted)
        variant: Closeness variant to use. Options:
                - 'standard': Classic closeness (reciprocal of sum of distances).
                  Can produce biased values for nodes in disconnected components.
                - 'harmonic': Harmonic closeness (sum of reciprocal distances).
                  Recommended for disconnected multilayer networks.
                - 'auto': Automatically selects 'harmonic' if the network has
                  multiple connected components, otherwise uses 'standard'.
                Default is 'standard' for backward compatibility.

    Returns:
        Dictionary mapping (node, layer) tuples to closeness centrality values

    Examples:
        >>> closeness = multiplex_closeness_centrality(network)
        >>> central_nodes = {k: v for k, v in closeness.items() if v > 0.5}

        >>> # For disconnected networks, use harmonic variant
        >>> closeness = multiplex_closeness_centrality(network, variant='harmonic')

    Reference:
        De Domenico et al. (2015), "Structural reducibility of multilayer networks"
        Boldi, P., & Vigna, S. (2014). Axioms for Centrality. Internet Math.
    """
    G = network.core_network
    
    # Handle 'auto' variant: check if graph is disconnected
    if variant == "auto":
        if G is None or len(G) == 0:
            is_connected = True
        elif G.is_directed():
            is_connected = nx.is_weakly_connected(G)
        else:
            is_connected = nx.is_connected(G)
        
        if not is_connected:
            variant = "harmonic"
        else:
            variant = "standard"
    
    # Use distance (inverse weight) if weights are provided
    distance = weight if weight else None
    
    if variant == "harmonic":
        closeness = nx.harmonic_centrality(G, distance=distance)
    else:
        closeness = nx.closeness_centrality(G, distance=distance)
    
    return closeness


def community_participation_coefficient(
    network: Any, communities: Dict[Tuple[Any, Any], int], node: Any
) -> float:
    """
    Calculate participation coefficient for a node across community structure.

    Measures how evenly a node's connections are distributed across different
    communities, across all layers. A node with connections to many communities
    has high participation.

    Formula: Pᵢ = 1 - Σₛ (kᵢₛ / kᵢ)²

    where kᵢₛ is the number of connections node i has to community s,
    and kᵢ is the total degree of node i across all layers.

    Args:
        network: py3plex multi_layer_network object
        communities: Dictionary mapping (node, layer) to community ID
        node: Node identifier (not node-layer tuple)

    Returns:
        Participation coefficient value between 0 and 1

    Examples:
        >>> communities = detect_communities(network)
        >>> pc = community_participation_coefficient(network, communities, 'Alice')
        >>> print(f"Participation: {pc:.3f}")

    Reference:
        Guimerà & Amaral (2005), "Functional cartography of complex metabolic networks"
    """
    # Get all node-layer pairs for this node
    node_layers = [nl for nl in network.get_nodes() if nl[0] == node]

    # Count connections to each community
    community_connections = {}
    total_degree = 0

    for node_layer in node_layers:
        # Get neighbors of this node-layer
        if node_layer in network.core_network:
            for neighbor in network.core_network.neighbors(node_layer):
                if neighbor in communities:
                    comm_id = communities[neighbor]
                    community_connections[comm_id] = (
                        community_connections.get(comm_id, 0) + 1
                    )
                    total_degree += 1

    if total_degree == 0:
        return 0.0

    # Calculate participation coefficient
    pc = 1.0 - sum(
        (count / total_degree) ** 2 for count in community_connections.values()
    )

    return pc


def community_participation_entropy(
    network: Any, communities: Dict[Tuple[Any, Any], int], node: Any
) -> float:
    """
    Calculate participation entropy for a node across community structure.

    Shannon entropy-based measure of how evenly a node distributes its
    connections across different communities. Higher entropy indicates
    more diverse community participation.

    Formula: Hᵢ = -Σₛ (kᵢₛ / kᵢ) log(kᵢₛ / kᵢ)

    where kᵢₛ is connections to community s, kᵢ is total degree.

    Args:
        network: py3plex multi_layer_network object
        communities: Dictionary mapping (node, layer) to community ID
        node: Node identifier (not node-layer tuple)

    Returns:
        Entropy value (higher = more diverse participation)

    Examples:
        >>> entropy = community_participation_entropy(network, communities, 'Alice')
        >>> print(f"Participation entropy: {entropy:.3f}")

    Reference:
        Based on Shannon entropy applied to community structure
    """
    # Get all node-layer pairs for this node
    node_layers = [nl for nl in network.get_nodes() if nl[0] == node]

    # Count connections to each community
    community_connections = {}
    total_degree = 0

    for node_layer in node_layers:
        if node_layer in network.core_network:
            for neighbor in network.core_network.neighbors(node_layer):
                if neighbor in communities:
                    comm_id = communities[neighbor]
                    community_connections[comm_id] = (
                        community_connections.get(comm_id, 0) + 1
                    )
                    total_degree += 1

    if total_degree == 0:
        return 0.0

    # Calculate entropy
    entropy = 0.0
    for count in community_connections.values():
        if count > 0:
            p = count / total_degree
            entropy -= p * np.log(p)

    return entropy


def layer_redundancy_coefficient(
    network: Any, layer_i: str, layer_j: str
) -> float:
    """
    Calculate layer redundancy coefficient.

    Measures the proportion of edges in one layer that are redundant
    (also present) in another layer. Values close to 1 indicate high
    redundancy, while values close to 0 indicate complementary layers.

    Formula: Rᵅᵝ = |Eᵅ ∩ Eᵝ| / |Eᵅ|

    where Eᵅ and Eᵝ are edge sets of layers α and β.

    Args:
        network: py3plex multi_layer_network object
        layer_i: First layer identifier
        layer_j: Second layer identifier

    Returns:
        Redundancy coefficient between 0 and 1

    Examples:
        >>> redundancy = layer_redundancy_coefficient(network, 'social', 'work')
        >>> print(f"Redundancy: {redundancy:.2%}")

    Reference:
        Nicosia & Latora (2015), "Measuring and modeling correlations in multiplex networks"
    """
    # Get edges from both layers
    edges_i = set()
    edges_j = set()

    for edge in network.get_edges():
        # edge format: (source, target, layer) or similar
        if len(edge) >= 3:
            source, target, layer = edge[0], edge[1], edge[2]
            edge_key = tuple(sorted([source, target]))  # Undirected edge

            if layer == layer_i:
                edges_i.add(edge_key)
            elif layer == layer_j:
                edges_j.add(edge_key)

    if len(edges_i) == 0:
        return 0.0

    # Calculate overlap
    overlap = len(edges_i & edges_j)
    redundancy = overlap / len(edges_i)

    return redundancy


def unique_redundant_edges(
    network: Any, layer_i: str, layer_j: str
) -> Tuple[int, int]:
    """
    Count unique and redundant edges between two layers.

    Returns the number of edges unique to the first layer and the number
    of edges present in both layers (redundant).

    Args:
        network: py3plex multi_layer_network object
        layer_i: First layer identifier
        layer_j: Second layer identifier

    Returns:
        Tuple of (unique_edges, redundant_edges)

    Examples:
        >>> unique, redundant = unique_redundant_edges(network, 'social', 'work')
        >>> print(f"Unique: {unique}, Redundant: {redundant}")
    """
    # Get edges from both layers
    edges_i = set()
    edges_j = set()

    for edge in network.get_edges():
        if len(edge) >= 3:
            source, target, layer = edge[0], edge[1], edge[2]
            edge_key = tuple(sorted([source, target]))

            if layer == layer_i:
                edges_i.add(edge_key)
            elif layer == layer_j:
                edges_j.add(edge_key)

    redundant = len(edges_i & edges_j)
    unique = len(edges_i - edges_j)

    return unique, redundant


def multiplex_rich_club_coefficient(
    network: Any, k: int, normalized: bool = True
) -> float:
    """
    Calculate multiplex rich-club coefficient.

    Measures the tendency of high-degree nodes to be more densely connected
    to each other than expected by chance, accounting for the multiplex structure.

    Formula: φᴹ(k) = Eᴹ(>k) / (Nᴹ(>k) * (Nᴹ(>k)-1) / 2)

    where Eᴹ(>k) is the number of edges among nodes with overlapping degree > k,
    and Nᴹ(>k) is the number of such nodes.

    Args:
        network: py3plex multi_layer_network object
        k: Degree threshold
        normalized: Whether to normalize by random expectation

    Returns:
        Rich-club coefficient value

    Examples:
        >>> rich_club = multiplex_rich_club_coefficient(network, k=10)
        >>> print(f"Rich-club coefficient: {rich_club:.3f}")

    Reference:
        Alstott et al. (2014), "powerlaw: A Python Package for Analysis of Heavy-Tailed Distributions"
        Extended to multiplex networks
    """
    # Calculate overlapping degree for each node
    node_degrees = {}
    for node_layer in network.get_nodes():
        node = node_layer[0]
        degree = network.core_network.degree(node_layer)
        node_degrees[node] = node_degrees.get(node, 0) + degree

    # Find nodes with degree > k
    rich_nodes = {node for node, deg in node_degrees.items() if deg > k}

    if len(rich_nodes) < 2:
        return 0.0

    # Count edges among rich nodes
    rich_edges = 0
    for edge in network.get_edges():
        if len(edge) >= 3:
            source, target = edge[0], edge[1]
            if source in rich_nodes and target in rich_nodes:
                rich_edges += 1

    # Calculate coefficient
    num_rich = len(rich_nodes)
    max_possible_edges = num_rich * (num_rich - 1) / 2

    if max_possible_edges == 0:
        return 0.0

    phi = rich_edges / max_possible_edges

    return phi


def percolation_threshold(
    network: Any, removal_strategy: str = "random", trials: int = 10
) -> float:
    """
    Estimate percolation threshold for the multiplex network.

    Determines the fraction of nodes that must be removed before the network
    fragments into disconnected components. Uses sampling to estimate threshold.

    Args:
        network: py3plex multi_layer_network object
        removal_strategy: 'random', 'degree', or 'betweenness'
        trials: Number of trials for averaging

    Returns:
        Estimated percolation threshold (fraction of nodes)

    Examples:
        >>> threshold = percolation_threshold(network, removal_strategy='degree')
        >>> print(f"Percolation threshold: {threshold:.2%}")

    Reference:
        Buldyrev et al. (2010), "Catastrophic cascade of failures in interdependent networks"
    """
    import random

    thresholds = []

    for _ in range(trials):
        G = network.core_network.copy()
        nodes = list(G.nodes())
        num_nodes = len(nodes)

        if num_nodes == 0:
            continue

        # Sort nodes by removal strategy
        if removal_strategy == "degree":
            nodes_sorted = sorted(nodes, key=lambda n: G.degree(n), reverse=True)
        elif removal_strategy == "betweenness":
            bc = nx.betweenness_centrality(G)
            nodes_sorted = sorted(nodes, key=lambda n: bc.get(n, 0), reverse=True)
        else:  # random
            nodes_sorted = nodes.copy()
            random.shuffle(nodes_sorted)

        # Find when giant component disappears
        components = list(nx.connected_components(G.to_undirected()))
        original_size = max(len(c) for c in components) if components else 0

        removed = 0
        for node in nodes_sorted:
            G.remove_node(node)
            removed += 1

            components = list(nx.connected_components(G.to_undirected()))
            largest_size = max(len(c) for c in components) if components else 0

            # Threshold: when giant component < 50% of original
            if largest_size < 0.5 * original_size:
                thresholds.append(removed / num_nodes)
                break

    return float(np.mean(thresholds)) if thresholds else 1.0


def targeted_layer_removal(
    network: Any, layer: str, return_resilience: bool = False
) -> Union[Any, Tuple[Any, float]]:
    """
    Simulate targeted removal of an entire layer.

    Removes all edges in a specified layer and returns the modified network
    or resilience score.

    Args:
        network: py3plex multi_layer_network object
        layer: Layer identifier to remove
        return_resilience: If True, return resilience score instead of network

    Returns:
        Modified network or resilience score

    Examples:
        >>> resilience = targeted_layer_removal(network, 'social', return_resilience=True)
        >>> print(f"Resilience after removing social layer: {resilience:.3f}")

    Reference:
        Buldyrev et al. (2010), "Catastrophic cascade of failures"
    """
    from copy import deepcopy

    G = network.core_network.copy()

    # Original size of largest component
    components = list(nx.connected_components(G.to_undirected()))
    original_size = max(len(c) for c in components) if components else 0

    # Remove edges from the specified layer
    edges_to_remove = []
    for edge in network.get_edges():
        if len(edge) >= 3 and edge[2] == layer:
            source_layer = (edge[0], edge[2])
            target_layer = (edge[1], edge[2])
            if G.has_edge(source_layer, target_layer):
                edges_to_remove.append((source_layer, target_layer))

    G.remove_edges_from(edges_to_remove)

    if return_resilience:
        # Calculate resilience
        components = list(nx.connected_components(G.to_undirected()))
        new_size = max(len(c) for c in components) if components else 0

        if original_size == 0:
            resilience = 1.0
        else:
            resilience = new_size / original_size

        return resilience
    else:
        # Return modified network
        modified_network = deepcopy(network)
        modified_network.core_network = G
        return modified_network


def compute_modularity_score(
    network: Any,
    communities: Dict[Tuple[Any, Any], int],
    gamma: float = 1.0,
    omega: float = 1.0,
) -> float:
    """
    Compute explicit multislice modularity score.

    Direct computation of the modularity quality function for a given
    community partition, without running detection algorithms.

    Formula: Q = (1/2μ) Σᵢⱼₐᵦ [(Aᵢⱼᵅ - γ·kᵢᵅkⱼᵅ/(2mₐ))δₐᵦ + ω·δᵢⱼ] δ(cᵢᵅ, cⱼᵝ)

    Args:
        network: py3plex multi_layer_network object
        communities: Dictionary mapping (node, layer) to community ID
        gamma: Resolution parameter (default: 1.0)
        omega: Inter-layer coupling strength (default: 1.0)

    Returns:
        Modularity score Q (higher is better)

    Examples:
        >>> communities = {('A', 'L1'): 0, ('B', 'L1'): 0, ('C', 'L1'): 1}
        >>> Q = compute_modularity_score(network, communities)
        >>> print(f"Modularity: {Q:.3f}")

    Reference:
        Mucha et al. (2010), Science 328, 876-878
    """
    return multilayer_modularity(network, communities, gamma, omega)


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


def layer_connectivity_entropy(network: Any, layer: str) -> float:
    """
    Calculate entropy of layer connectivity (H_connectivity).

    Formula: H_c = -Σᵢ (kᵢ/Σⱼkⱼ) log₂(kᵢ/Σⱼkⱼ)

    Shannon entropy of degree distribution within a layer; measures
    heterogeneity of node connectivity patterns.

    Variables:
        kᵢ = degree of node i in the layer
        Σⱼkⱼ = sum of all degrees (2 * edges for undirected)

    Properties:
        H_c = 0 when all nodes have the same degree (uniform distribution)
        H_c is maximized when degree distribution is highly uneven

    Args:
        network: py3plex multi_layer_network object
        layer: Layer identifier

    Returns:
        Entropy value in bits

    Examples:
        >>> from py3plex.core import multinet
        >>> network = multinet.multi_layer_network(directed=False)
        >>> network.add_edges([
        ...     ['A', 'L1', 'B', 'L1', 1],
        ...     ['B', 'L1', 'C', 'L1', 1]
        ... ], input_type='list')
        >>> entropy = layer_connectivity_entropy(network, 'L1')
        >>> print(f"Connectivity entropy: {entropy:.3f}")

    Reference:
        Solé-Ribalta et al. (2013), "Spectral properties of complex networks"
        Shannon (1948), "A Mathematical Theory of Communication"
    """
    # Check if network has any edges
    if not hasattr(network, 'core_network') or network.core_network is None:
        return 0.0
    
    # Get degree distribution for the layer
    degree_counts: Dict[Any, int] = {}

    for edge in network.get_edges():
        (n1, l1), (n2, l2) = edge[0], edge[1]
        if l1 == l2 == layer:
            degree_counts[n1] = degree_counts.get(n1, 0) + 1
            if n1 != n2:  # Don't double count self-loops
                degree_counts[n2] = degree_counts.get(n2, 0) + 1

    if not degree_counts:
        return 0.0

    # Calculate total degree
    total_degree = sum(degree_counts.values())

    if total_degree == 0:
        return 0.0

    # Calculate entropy
    entropy = 0.0
    for degree in degree_counts.values():
        if degree > 0:
            p = degree / total_degree
            entropy -= p * np.log2(p)

    return float(entropy)


def inter_layer_dependence_entropy(
    network: Any, layer_i: str, layer_j: str
) -> float:
    """
    Calculate inter-layer dependence entropy (H_dep).

    Formula: H_dep = -Σₙ pₙ log₂(pₙ), where pₙ is the proportion of inter-layer
    edges for each node n connecting layers i and j.

    Measures heterogeneity in how nodes couple the two layers; high entropy
    indicates diverse coupling patterns, low entropy indicates uniform coupling.

    Variables:
        pₙ = proportion of inter-layer edges incident to node n
        Total over all nodes connecting the two layers

    Args:
        network: py3plex multi_layer_network object
        layer_i: First layer identifier
        layer_j: Second layer identifier

    Returns:
        Entropy value in bits

    Examples:
        >>> entropy = inter_layer_dependence_entropy(network, 'L1', 'L2')
        >>> print(f"Inter-layer dependence entropy: {entropy:.3f}")

    Reference:
        De Domenico et al. (2015), "Ranking in interconnected multilayer networks"
    """
    # Check if network has any edges
    if not hasattr(network, 'core_network') or network.core_network is None:
        return 0.0
    
    # Count inter-layer edges per node
    node_coupling: Dict[Any, int] = {}

    for edge in network.get_edges():
        (n1, l1), (n2, l2) = edge[0], edge[1]
        # Inter-layer edges between specified layers
        if (l1 == layer_i and l2 == layer_j) or (l1 == layer_j and l2 == layer_i):
            node_coupling[n1] = node_coupling.get(n1, 0) + 1
            if n1 != n2:
                node_coupling[n2] = node_coupling.get(n2, 0) + 1

    if not node_coupling:
        return 0.0

    total_coupling = sum(node_coupling.values())

    if total_coupling == 0:
        return 0.0

    # Calculate entropy
    entropy = 0.0
    for count in node_coupling.values():
        if count > 0:
            p = count / total_coupling
            entropy -= p * np.log2(p)

    return float(entropy)


def cross_layer_redundancy_entropy(network: Any) -> float:
    """
    Calculate cross-layer redundancy entropy (H_redundancy).

    Formula: H_r = -Σᵢⱼ rᵢⱼ log₂(rᵢⱼ), where rᵢⱼ is the normalized edge overlap
    between layers i and j.

    Measures diversity in structural redundancy across layer pairs; high entropy
    indicates varied overlap patterns, low entropy indicates uniform redundancy.

    Variables:
        rᵢⱼ = edge_overlap(i,j) / Σₐᵦ edge_overlap(α,β)
        Normalized overlap proportion for each layer pair

    Args:
        network: py3plex multi_layer_network object

    Returns:
        Entropy value in bits

    Examples:
        >>> entropy = cross_layer_redundancy_entropy(network)
        >>> print(f"Cross-layer redundancy entropy: {entropy:.3f}")

    Reference:
        Bianconi (2018), "Multilayer Networks: Structure and Function"
    """
    # Check if network has any nodes
    if not hasattr(network, 'core_network') or network.core_network is None:
        return 0.0
    
    # Get all layers
    all_layers = set()
    try:
        for n, layer in network.get_nodes():
            all_layers.add(layer)
    except (AttributeError, TypeError):
        return 0.0

    layers_list = sorted(all_layers)

    if len(layers_list) < 2:
        return 0.0

    # Calculate edge overlap for all layer pairs
    overlaps = []
    for i, layer_i in enumerate(layers_list):
        for j, layer_j in enumerate(layers_list):
            if i < j:
                overlap = edge_overlap(network, layer_i, layer_j)
                overlaps.append(overlap)

    if not overlaps or sum(overlaps) == 0:
        return 0.0

    total_overlap = sum(overlaps)

    # Calculate entropy
    entropy = 0.0
    for overlap in overlaps:
        if overlap > 0:
            p = overlap / total_overlap
            entropy -= p * np.log2(p)

    return float(entropy)


def cross_layer_mutual_information(
    network: Any,
    layer_i: str,
    layer_j: str,
    bins: int = 10,
) -> float:
    """
    Calculate cross-layer mutual information (I(Lᵢ; Lⱼ)).

    Formula: I(Lᵢ; Lⱼ) = H(Lᵢ) + H(Lⱼ) - H(Lᵢ, Lⱼ)

    Measures statistical dependence between degree distributions in two layers;
    quantifies how much knowing a node's degree in one layer tells us about
    its degree in another layer.

    Variables:
        H(Lᵢ) = entropy of degree distribution in layer i
        H(Lⱼ) = entropy of degree distribution in layer j
        H(Lᵢ, Lⱼ) = joint entropy of degree distributions

    Properties:
        I = 0 when layers are independent
        I > 0 indicates statistical dependence (higher = stronger)
        I(Lᵢ; Lⱼ) ≤ min(H(Lᵢ), H(Lⱼ))

    Args:
        network: py3plex multi_layer_network object
        layer_i: First layer identifier
        layer_j: Second layer identifier
        bins: Number of bins for discretizing degree distributions

    Returns:
        Mutual information value in bits

    Examples:
        >>> mi = cross_layer_mutual_information(network, 'L1', 'L2', bins=10)
        >>> print(f"Mutual information: {mi:.3f} bits")

    Reference:
        Cover & Thomas (2006), "Elements of Information Theory"
        De Domenico et al. (2015), "Structural reducibility"
    """
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

    # Get degree vectors for common nodes
    degrees_i = []
    degrees_j = []

    for node in common_nodes:
        deg_vec = degree_vector(network, node)
        degrees_i.append(deg_vec.get(layer_i, 0))
        degrees_j.append(deg_vec.get(layer_j, 0))

    # Convert to numpy arrays
    degrees_i_arr = np.array(degrees_i)
    degrees_j_arr = np.array(degrees_j)

    # Discretize into bins
    if np.max(degrees_i_arr) == np.min(degrees_i_arr):
        # All same degree in layer i
        return 0.0
    if np.max(degrees_j_arr) == np.min(degrees_j_arr):
        # All same degree in layer j
        return 0.0

    # Create histogram bins
    bins_i = np.linspace(
        np.min(degrees_i_arr), np.max(degrees_i_arr) + 1e-10, bins + 1
    )
    bins_j = np.linspace(
        np.min(degrees_j_arr), np.max(degrees_j_arr) + 1e-10, bins + 1
    )

    # Discretize degrees
    disc_i = np.digitize(degrees_i_arr, bins_i) - 1
    disc_j = np.digitize(degrees_j_arr, bins_j) - 1

    # Calculate marginal entropies
    def calc_entropy(values):
        _, counts = np.unique(values, return_counts=True)
        probs = counts / len(values)
        return -np.sum(probs * np.log2(probs + 1e-10))

    H_i = calc_entropy(disc_i)
    H_j = calc_entropy(disc_j)

    # Calculate joint entropy
    joint_values = list(zip(disc_i, disc_j))
    _, counts = np.unique(joint_values, axis=0, return_counts=True)
    joint_probs = counts / len(joint_values)
    H_ij = -np.sum(joint_probs * np.log2(joint_probs + 1e-10))

    # Mutual information
    mi = H_i + H_j - H_ij

    return float(max(0.0, mi))  # Ensure non-negative due to numerical issues


def layer_influence_centrality(
    network: Any,
    layer: str,
    method: str = "coupling",
    sample_size: int = 100,
) -> float:
    """
    Calculate layer influence centrality (Iᵅ).

    Formula (coupling): Iᵅ = Σᵦ≠ᵅ C^αβ / (L-1)
    Formula (flow): Iᵅ = Σᵦ≠ᵅ F^αβ / (L-1)

    Quantifies how much a layer influences other layers through inter-layer
    connections (coupling method) or information flow (flow method).

    Variables:
        C^αβ = inter-layer coupling strength between layers α and β
        F^αβ = flow from layer α to layer β (random walk transition probability)
        L = total number of layers

    Properties:
        Higher values indicate layers that strongly influence others
        Useful for identifying critical layers in the multilayer structure

    Args:
        network: py3plex multi_layer_network object
        layer: Layer identifier
        method: 'coupling' for structural influence, 'flow' for dynamic influence
        sample_size: Number of random walk steps for flow simulation

    Returns:
        Influence centrality value

    Examples:
        >>> influence = layer_influence_centrality(network, 'L1', method='coupling')
        >>> print(f"Layer L1 influence: {influence:.3f}")

    Reference:
        Cozzo et al. (2013), "Mathematical formulation of multilayer networks"
        De Domenico et al. (2014), "Identifying modular flows"
    """
    # Get all layers
    all_layers = set()
    for n, layer_name in network.get_nodes():
        all_layers.add(layer_name)

    if len(all_layers) < 2:
        return 0.0

    if method == "coupling":
        # Coupling-based influence
        total_coupling = 0.0
        for other_layer in all_layers:
            if other_layer != layer:
                coupling = inter_layer_coupling_strength(network, layer, other_layer)
                total_coupling += coupling

        return float(total_coupling / (len(all_layers) - 1))

    elif method == "flow":
        # Flow-based influence using random walk simulation
        # Build transition matrix on supra-graph
        G = network.core_network

        if len(G) == 0:
            return 0.0

        # Get nodes in the target layer
        layer_nodes = [(n, l) for n, l in G.nodes() if l == layer]

        if not layer_nodes:
            return 0.0

        # Random walk simulation
        total_flow = 0.0

        for _ in range(sample_size):
            # Start from random node in target layer
            current = layer_nodes[np.random.randint(len(layer_nodes))]

            # Take one step
            neighbors = list(G.neighbors(current))
            if neighbors:
                next_node = neighbors[np.random.randint(len(neighbors))]
                # Check if we moved to a different layer
                if next_node[1] != layer:
                    total_flow += 1.0

        # Normalize by sample size
        return float(total_flow / sample_size)

    else:
        raise ValueError(f"Unknown method: {method}. Use 'coupling' or 'flow'.")


def multilayer_betweenness_surface(
    network: Any,
    normalized: bool = True,
    weight: Optional[str] = None,
) -> np.ndarray:
    """
    Calculate multilayer betweenness surface (tensor representation).

    Computes betweenness centrality for each node-layer pair and organizes
    the results as a 2D array (nodes × layers) that can be visualized as
    a heatmap or surface plot.

    Formula: Surface[i,α] = Bᵢᵅ

    where Bᵢᵅ is the betweenness centrality of node i in layer α.

    Args:
        network: py3plex multi_layer_network object
        normalized: Whether to normalize betweenness values
        weight: Edge weight attribute name (None for unweighted)

    Returns:
        2D numpy array of shape (num_nodes, num_layers) containing betweenness values.
        Also returns tuple of (node_labels, layer_labels) for axis labeling.

    Examples:
        >>> surface, (nodes, layers) = multilayer_betweenness_surface(network)
        >>> import matplotlib.pyplot as plt
        >>> plt.imshow(surface, aspect='auto', cmap='viridis')
        >>> plt.xlabel('Layers')
        >>> plt.ylabel('Nodes')
        >>> plt.xticks(range(len(layers)), layers)
        >>> plt.yticks(range(len(nodes)), nodes)
        >>> plt.colorbar(label='Betweenness Centrality')
        >>> plt.title('Multilayer Betweenness Surface')
        >>> plt.show()

    Reference:
        De Domenico et al. (2015), "Structural reducibility of multilayer networks"
    """
    # Get betweenness for all node-layer pairs
    betweenness = multiplex_betweenness_centrality(
        network, normalized=normalized, weight=weight
    )

    if not betweenness:
        return np.array([]), ([], [])

    # Extract unique nodes and layers
    node_layer_pairs = list(betweenness.keys())
    nodes = sorted(set(nl[0] for nl in node_layer_pairs))
    layers = sorted(set(nl[1] for nl in node_layer_pairs))

    # Create 2D surface array
    surface = np.zeros((len(nodes), len(layers)))

    node_to_idx = {node: idx for idx, node in enumerate(nodes)}
    layer_to_idx = {layer: idx for idx, layer in enumerate(layers)}

    for (node, layer), value in betweenness.items():
        i = node_to_idx[node]
        j = layer_to_idx[layer]
        surface[i, j] = value

    return surface, (nodes, layers)


def interlayer_degree_correlation_matrix(network: Any) -> Tuple[np.ndarray, list]:
    """
    Calculate inter-layer degree correlation matrix.

    Computes Pearson correlation coefficients for node degrees between all
    pairs of layers, organized as a symmetric correlation matrix.

    Formula: Matrix[α,β] = r^αβ = corr(k^α, k^β)

    where k^α and k^β are degree vectors for layers α and β over common nodes.

    Properties:
        - Diagonal elements are 1.0 (self-correlation)
        - Off-diagonal elements in [-1, 1]
        - Symmetric matrix
        - Positive values indicate positive degree correlation
        - Negative values indicate negative degree correlation

    Args:
        network: py3plex multi_layer_network object

    Returns:
        Tuple of (correlation_matrix, layer_labels):
            - correlation_matrix: 2D numpy array of shape (num_layers, num_layers)
            - layer_labels: List of layer names corresponding to matrix indices

    Examples:
        >>> corr_matrix, layers = interlayer_degree_correlation_matrix(network)
        >>> import matplotlib.pyplot as plt
        >>> import seaborn as sns
        >>> sns.heatmap(corr_matrix, annot=True, xticklabels=layers,
        ...             yticklabels=layers, cmap='coolwarm', center=0,
        ...             vmin=-1, vmax=1)
        >>> plt.title('Inter-layer Degree Correlation Matrix')
        >>> plt.show()

    Reference:
        Nicosia & Latora (2015), "Measuring and modeling correlations in multiplex networks"
        Battiston et al. (2014), "Structural measures for multiplex networks"
    """
    # Get all layers
    all_layers = set()
    for n, layer in network.get_nodes():
        all_layers.add(layer)

    layers = sorted(all_layers)
    n_layers = len(layers)

    if n_layers < 2:
        return np.array([[1.0]]), layers

    # Initialize correlation matrix
    corr_matrix = np.eye(n_layers)

    # Calculate correlations for each layer pair
    for i, layer_i in enumerate(layers):
        for j, layer_j in enumerate(layers):
            if i < j:
                corr = inter_layer_degree_correlation(network, layer_i, layer_j)
                corr_matrix[i, j] = corr
                corr_matrix[j, i] = corr  # Symmetric

    return corr_matrix, layers


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
    "multiplex_betweenness_centrality",
    "multiplex_closeness_centrality",
    "community_participation_coefficient",
    "community_participation_entropy",
    "layer_redundancy_coefficient",
    "unique_redundant_edges",
    "multiplex_rich_club_coefficient",
    "percolation_threshold",
    "targeted_layer_removal",
    "compute_modularity_score",
    "layer_connectivity_entropy",
    "inter_layer_dependence_entropy",
    "cross_layer_redundancy_entropy",
    "cross_layer_mutual_information",
    "layer_influence_centrality",
    "multilayer_betweenness_surface",
    "interlayer_degree_correlation_matrix",
]
