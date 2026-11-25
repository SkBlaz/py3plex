"""
Multilayer Modularity Maximization (Mucha et al., 2010)

This module implements multilayer modularity quality function and optimization
algorithms for community detection in multilayer/multiplex networks.

References:
    Mucha et al., "Community Structure in Time-Dependent, Multiscale, and Multiplex
    Networks", Science 328:876-878 (2010)
"""

from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import scipy.sparse as sp


def _supra_replica_order(network):
    """Return replica IDs in the order of the already-built supra matrix."""
    if network.network_type == "multiplex":
        return list(network.node_order_in_matrix)
    return list(network.get_nodes())


def multilayer_modularity(
    network: Any,
    communities: Dict[Tuple[Any, Any], int],
    gamma: Union[float, Dict[Any, float]] = 1.0,
    omega: Union[float, np.ndarray] = 1.0,
    weight: str = "weight",
) -> float:
    """
    Calculate multilayer modularity quality function (Mucha et al., 2010).

    The multilayer modularity is defined as:
    Q = (1/2μ) Σ_{ijαβ} [(A^[α]_ij - γ^[α]P^[α]_ij)δ_αβ + δ_ij ω_αβ] δ(g_iα, g_jβ)

    where:
    - A^[α]_ij is the adjacency matrix of layer α
    - P^[α]_ij is the null model (e.g., Newman-Girvan: k_i^α k_j^α / 2m_α)
    - γ^[α] is the resolution parameter for layer α
    - ω_αβ is the inter-layer coupling strength
    - δ_αβ = 1 if α=β, else 0 (Kronecker delta)
    - δ_ij = 1 if i=j, else 0
    - δ(g_iα, g_jβ) = 1 if node i in layer α and node j in layer β are in same community
    - μ is the total edge weight in the supra-network

    Args:
        network: py3plex multi_layer_network object
        communities: Dictionary mapping (node, layer) tuples to community IDs
        gamma: Resolution parameter(s). Can be:
            - Single float: same resolution for all layers
            - Dict[layer, float]: layer-specific resolution parameters
        omega: Inter-layer coupling strength. Can be:
            - Single float: uniform coupling between all layer pairs
            - np.ndarray: layer-pair specific coupling matrix (L×L)
        weight: Edge weight attribute (default: "weight")

    Returns:
        Modularity value Q ∈ [-1, 1]

    Examples:
        >>> from py3plex.core import multinet
        >>> from py3plex.algorithms.community_detection.multilayer_modularity import multilayer_modularity
        >>>
        >>> # Create a simple multilayer network
        >>> network = multinet.multi_layer_network(directed=False)
        >>> network.add_edges([
        ...     ['A', 'L1', 'B', 'L1', 1],
        ...     ['B', 'L1', 'C', 'L1', 1],
        ...     ['A', 'L2', 'C', 'L2', 1]
        ... ], input_type='list')
        >>>
        >>> # Assign communities
        >>> communities = {
        ...     ('A', 'L1'): 0, ('B', 'L1'): 0, ('C', 'L1'): 1,
        ...     ('A', 'L2'): 0, ('C', 'L2'): 0
        ... }
        >>>
        >>> # Calculate modularity
        >>> Q = multilayer_modularity(network, communities, gamma=1.0, omega=1.0)
        >>> print(f"Modularity: {Q:.3f}")
    """
    adjacency = sp.csr_matrix(network.get_supra_adjacency_matrix())
    replicas = _supra_replica_order(network)
    layers = list(network.layers)
    indices = {layer: [] for layer in layers}
    membership = {layer: {} for layer in layers}
    for index, (node, layer) in enumerate(replicas):
        indices[layer].append(index)
        membership[layer][node] = communities.get((node, layer), -1)

    score = 0.0
    total = 0.0
    for i, layer in enumerate(layers):
        rows = indices[layer]
        block = adjacency[rows, :][:, rows].tocoo()
        mass = float(block.data.sum())
        total += mass
        groups = np.asarray(list(membership[layer].values()))
        assigned = groups != -1
        within = assigned[block.row] & (groups[block.row] == groups[block.col])
        score += block.data[within].sum()
        if mass > 0 and assigned.any():
            degree = np.bincount(block.row, weights=block.data, minlength=len(rows))
            _, labels = np.unique(groups[assigned], return_inverse=True)
            volumes = np.bincount(labels, weights=degree[assigned])
            resolution = gamma.get(layer, 1.0) if isinstance(gamma, dict) else gamma
            score -= resolution * np.dot(volumes, volumes) / mass

        for j, other in enumerate(layers):
            if i == j:
                continue
            coupling = omega[i, j] if isinstance(omega, np.ndarray) else omega
            common = membership[layer].keys() & membership[other].keys()
            total += coupling * len(common)
            if coupling > 0:
                score += coupling * sum(
                    membership[layer][node] != -1
                    and membership[layer][node] == membership[other][node]
                    for node in common
                )

    return float(score / total) if total else 0.0


def build_supra_modularity_matrix(
    network: Any,
    gamma: Union[float, Dict[Any, float]] = 1.0,
    omega: Union[float, np.ndarray] = 1.0,
    weight: str = "weight",
) -> Tuple[np.ndarray, List[Tuple[Any, Any]]]:
    """
    Build the supra-modularity matrix B for multilayer network.

    The supra-modularity matrix is:
    B_{iα,jβ} = (A^[α]_ij - γ^[α] k_i^α k_j^α / 2m_α) δ_αβ + δ_ij ω_αβ

    This matrix can be used for spectral community detection methods.

    Args:
        network: py3plex multi_layer_network object
        gamma: Resolution parameter(s)
        omega: Inter-layer coupling strength
        weight: Edge weight attribute

    Returns:
        Tuple of (modularity_matrix, node_layer_list)
        - modularity_matrix: Supra-modularity matrix B (NL × NL)
        - node_layer_list: List of (node, layer) tuples corresponding to matrix indices
    """
    # Get supra-adjacency matrix
    supra_matrix = network.get_supra_adjacency_matrix()

    if sp.issparse(supra_matrix):
        supra_matrix = supra_matrix.toarray()

    # Get node-layer mapping
    node_layer_list = _supra_replica_order(network)
    n_total = len(node_layer_list)

    # Extract layers
    layers = list(network.layers)
    layer_to_idx = {layer: i for i, layer in enumerate(layers)}
    n_layers = len(layers)

    # Convert parameters
    if isinstance(gamma, (int, float)):
        gamma_dict = {layer: float(gamma) for layer in layers}
    else:
        gamma_dict = gamma

    if isinstance(omega, (int, float)):
        omega_matrix = np.full((n_layers, n_layers), float(omega))
        np.fill_diagonal(omega_matrix, 0)
    else:
        omega_matrix = omega

    # Initialize modularity matrix
    B = np.zeros((n_total, n_total))

    # Compute layer-wise null models
    layer_stats = {}
    for layer in layers:
        layer_nodes = [
            (i, nl) for i, nl in enumerate(node_layer_list) if nl[1] == layer
        ]
        layer_indices = [i for i, nl in layer_nodes]

        # Extract layer adjacency
        layer_adj = supra_matrix[np.ix_(layer_indices, layer_indices)]
        layer_weight: float = np.sum(layer_adj)
        degrees = np.sum(layer_adj, axis=1)

        layer_stats[layer] = {
            "weight": layer_weight,
            "degrees": degrees,
            "indices": layer_indices,
            "nodes": [nl for i, nl in layer_nodes],
        }

    # Fill intra-layer blocks
    for layer in layers:
        stats = layer_stats[layer]
        indices = stats["indices"]
        degrees = stats["degrees"]
        layer_weight = stats["weight"]
        gamma_layer = gamma_dict.get(layer, 1.0)

        n_layer = len(indices)
        for i in range(n_layer):
            for j in range(n_layer):
                idx_i = indices[i]
                idx_j = indices[j]

                # A_ij - gamma * P_ij
                A_ij = supra_matrix[idx_i, idx_j]
                if layer_weight > 0:
                    P_ij = (degrees[i] * degrees[j]) / layer_weight
                else:
                    P_ij = 0.0

                B[idx_i, idx_j] = A_ij - gamma_layer * P_ij

    # Add inter-layer coupling
    for i in range(n_total):
        for j in range(n_total):
            node_i, layer_i = node_layer_list[i]
            node_j, layer_j = node_layer_list[j]

            # Only add coupling for same node across different layers
            if node_i == node_j and layer_i != layer_j:
                layer_i_idx = layer_to_idx[layer_i]
                layer_j_idx = layer_to_idx[layer_j]
                B[i, j] += omega_matrix[layer_i_idx, layer_j_idx]

    return B, node_layer_list


def louvain_multilayer(
    network: Any,
    gamma: Union[float, Dict[Any, float]] = 1.0,
    omega: Union[float, np.ndarray] = 1.0,
    weight: str = "weight",
    max_iter: int = 100,
    random_state: Optional[int] = None,
) -> Dict[Tuple[Any, Any], int]:
    """
    Generalized Louvain algorithm for multilayer networks.

    This implements the multilayer Louvain method as described in Mucha et al. (2010),
    which greedily maximizes the multilayer modularity quality function.

    Complexity:
        - Time: O(n × L × d × k) per iteration, where:
            - n = number of nodes per layer
            - L = number of layers
            - d = average degree
            - k = number of communities
        - Typical: O(n × L) iterations until convergence
        - Worst case: O((n×L)²) for dense networks
        - Space: O((n×L)²) for supra-adjacency matrix (use sparse for large networks)

    Args:
        network: py3plex multi_layer_network object
        gamma: Resolution parameter(s)
        omega: Inter-layer coupling strength
        weight: Edge weight attribute
        max_iter: Maximum number of iterations
        random_state: Random seed for reproducibility

    Returns:
        Dictionary mapping (node, layer) tuples to community IDs

    Examples:
        >>> from py3plex.core import multinet
        >>> from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
        >>>
        >>> network = multinet.multi_layer_network(directed=False)
        >>> network.add_edges([
        ...     ['A', 'L1', 'B', 'L1', 1],
        ...     ['B', 'L1', 'C', 'L1', 1],
        ...     ['A', 'L2', 'C', 'L2', 1]
        ... ], input_type='list')
        >>>
        >>> communities = louvain_multilayer(network, gamma=1.0, omega=1.0, random_state=42)
        >>> print(communities)

    Note:
        For reproducible results, always set random_state parameter.
    """
    if random_state is not None:
        np.random.seed(random_state)

    supra_matrix = network.get_supra_adjacency_matrix()
    if sp.issparse(supra_matrix):
        supra_matrix = supra_matrix.toarray()

    node_layer_list = _supra_replica_order(network)
    n_total = len(node_layer_list)
    communities = {nl: i for i, nl in enumerate(node_layer_list)}

    improved = True
    iteration = 0

    while improved and iteration < max_iter:
        improved = False
        iteration += 1

        # Randomize order of node-layer pairs
        order = np.random.permutation(n_total)

        # Try moving each node-layer to neighboring communities
        for idx in order:
            node_layer = node_layer_list[idx]
            current_com = communities[node_layer]

            # Get neighbors (both intra-layer and inter-layer)
            neighbors = set()
            for j, nl_j in enumerate(node_layer_list):
                if supra_matrix[idx, j] > 0:
                    neighbors.add(nl_j)

            # Also consider inter-layer connections (same node, different layer)
            node, layer = node_layer
            for nl in node_layer_list:
                if nl[0] == node and nl[1] != layer:
                    neighbors.add(nl)

            # Try moving to each neighbor's community
            neighbor_communities = {communities[nl] for nl in neighbors}
            neighbor_communities.discard(current_com)

            if not neighbor_communities:
                continue

            # Calculate current modularity contribution
            current_Q = multilayer_modularity(
                network, communities, gamma, omega, weight
            )

            best_com = current_com
            best_Q = current_Q

            # Try each neighbor community
            for test_com in neighbor_communities:
                # Temporarily move to test community
                communities[node_layer] = test_com
                test_Q = multilayer_modularity(
                    network, communities, gamma, omega, weight
                )

                if test_Q > best_Q:
                    best_Q = test_Q
                    best_com = test_com
                    improved = True

            # Keep best assignment
            communities[node_layer] = best_com

    # Renumber communities to be contiguous
    unique_coms = sorted(set(communities.values()))
    com_map = {old: new for new, old in enumerate(unique_coms)}
    communities = {nl: com_map[com] for nl, com in communities.items()}

    return communities
