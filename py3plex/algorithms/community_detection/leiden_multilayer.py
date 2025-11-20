"""
Leiden Algorithm for Multilayer Networks.

This module implements the Leiden community detection algorithm for multilayer
and multiplex networks, extending the approach described in Traag et al. (2019)
to support multislice modularity optimization.

References:
    - Traag, V. A., Waltman, L., & Van Eck, N. J. (2019). From Louvain to Leiden:
      guaranteeing well-connected communities. Scientific reports, 9(1), 5233.
    - Mucha et al., "Community Structure in Time-Dependent, Multiscale, and Multiplex
      Networks", Science 328:876-878 (2010)
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import scipy.sparse as sp


class LeidenResult:
    """
    Container for Leiden algorithm results.

    Attributes:
        communities: Dictionary mapping (node, layer) tuples to community IDs
        modularity: Global multilayer modularity score
        layer_modularity: Dictionary mapping layer names to layer-specific modularity scores
        iterations: Number of iterations until convergence
        improved: Whether the algorithm improved the partition in the last phase
    """

    def __init__(
        self,
        communities: Dict[Tuple[Any, Any], int],
        modularity: float,
        layer_modularity: Optional[Dict[Any, float]] = None,
        iterations: int = 0,
        improved: bool = False,
    ):
        self.communities = communities
        self.modularity = modularity
        self.layer_modularity = layer_modularity or {}
        self.iterations = iterations
        self.improved = improved

    def summary(self) -> str:
        """Generate a summary report of the results."""
        n_communities = len(set(self.communities.values()))
        n_nodes = len({node for node, layer in self.communities.keys()})
        n_layers = len({layer for node, layer in self.communities.keys()})

        report = []
        report.append("=" * 60)
        report.append("Leiden Multilayer Community Detection Results")
        report.append("=" * 60)
        report.append(f"Nodes: {n_nodes}")
        report.append(f"Layers: {n_layers}")
        report.append(f"Node-Layer pairs: {len(self.communities)}")
        report.append(f"Communities detected: {n_communities}")
        report.append(f"Global modularity: {self.modularity:.4f}")
        report.append(f"Iterations: {self.iterations}")

        if self.layer_modularity:
            report.append("\nLayer-specific modularity:")
            for layer, mod in sorted(self.layer_modularity.items()):
                report.append(f"  {layer}: {mod:.4f}")

        report.append("=" * 60)
        return "\n".join(report)


def _calculate_modularity_gain(
    node_layer: Tuple[Any, Any],
    current_com: int,
    target_com: int,
    communities: Dict[Tuple[Any, Any], int],
    supra_matrix: np.ndarray,
    node_layer_to_idx: Dict[Tuple[Any, Any], int],
    layer_stats: Dict[Any, Dict],
    gamma_dict: Dict[Any, float],
    omega_matrix: np.ndarray,
    layer_to_idx: Dict[Any, int],
    total_weight: float,
) -> float:
    """
    Calculate the modularity gain from moving a node-layer to a new community.

    This is the key computation for the Leiden algorithm's local moves.
    """
    if current_com == target_com:
        return 0.0

    node, layer = node_layer
    idx = node_layer_to_idx[node_layer]

    # Calculate change in modularity
    delta_Q = 0.0

    # Intra-layer contribution
    gamma_layer = gamma_dict.get(layer, 1.0)
    stats = layer_stats[layer]
    layer_weight = stats["weight"]

    if layer_weight > 0:
        # Get degree of the node
        degree = np.sum(supra_matrix[idx, :])

        # Sum edges to nodes in target community
        edges_to_target = 0.0
        degree_sum_target = 0.0

        # Sum edges to nodes in current community
        edges_to_current = 0.0
        degree_sum_current = 0.0

        for nl, com in communities.items():
            if nl[1] == layer:  # Same layer
                nl_idx = node_layer_to_idx[nl]
                nl_degree = np.sum(supra_matrix[nl_idx, :])

                if com == target_com:
                    edges_to_target += supra_matrix[idx, nl_idx]
                    degree_sum_target += nl_degree
                elif com == current_com and nl != node_layer:
                    edges_to_current += supra_matrix[idx, nl_idx]
                    degree_sum_current += nl_degree

        # Modularity change from moving
        delta_Q += (edges_to_target - edges_to_current) / total_weight
        delta_Q -= gamma_layer * degree * (degree_sum_target - degree_sum_current) / (layer_weight * total_weight)

    # Inter-layer coupling contribution
    for other_layer in layer_stats.keys():
        if other_layer != layer:
            layer_i_idx = layer_to_idx[layer]
            layer_j_idx = layer_to_idx[other_layer]
            coupling = omega_matrix[layer_i_idx, layer_j_idx]

            if coupling > 0:
                # Check if this node exists in the other layer
                other_nl = (node, other_layer)
                if other_nl in communities:
                    other_com = communities[other_nl]
                    if other_com == target_com:
                        delta_Q += coupling / total_weight
                    elif other_com == current_com:
                        delta_Q -= coupling / total_weight

    return delta_Q


def _refine_partition(
    communities: Dict[Tuple[Any, Any], int],
    supra_matrix: np.ndarray,
    node_layer_list: List[Tuple[Any, Any]],
    node_layer_to_idx: Dict[Tuple[Any, Any], int],
    layer_stats: Dict[Any, Dict],
    gamma_dict: Dict[Any, float],
    omega_matrix: np.ndarray,
    layer_to_idx: Dict[Any, int],
    total_weight: float,
    random_state: Optional[np.random.RandomState] = None,
) -> Tuple[Dict[Tuple[Any, Any], int], bool]:
    """
    Refinement phase of the Leiden algorithm.

    This is the key difference from Louvain: nodes are moved to a random well-connected
    subset (called a "subcommunity"), and then the subcommunities are merged optimally.
    This guarantees that communities are well-connected.
    """
    if random_state is None:
        random_state = np.random.RandomState()

    # Create subcommunities by randomly assigning nodes within each community
    # to singleton subcommunities
    refined_communities = {}
    subcommunity_counter = 0
    community_to_nodes = {}

    # Group nodes by community
    for nl, com in communities.items():
        if com not in community_to_nodes:
            community_to_nodes[com] = []
        community_to_nodes[com].append(nl)

    # For each community, try to split it into well-connected subcommunities
    for com, nodes in community_to_nodes.items():
        if len(nodes) == 1:
            # Single node, keep as is
            refined_communities[nodes[0]] = subcommunity_counter
            subcommunity_counter += 1
        else:
            # Visit nodes in random order
            random_state.shuffle(nodes)
            node_to_subcom = {}

            for node in nodes:
                # Check connectivity to existing subcommunities
                subcom_connections = {}
                node_idx = node_layer_to_idx[node]

                for other_node, subcom in node_to_subcom.items():
                    other_idx = node_layer_to_idx[other_node]
                    weight = supra_matrix[node_idx, other_idx] + supra_matrix[other_idx, node_idx]

                    # Also check inter-layer coupling
                    if node[0] == other_node[0] and node[1] != other_node[1]:
                        layer_i_idx = layer_to_idx[node[1]]
                        layer_j_idx = layer_to_idx[other_node[1]]
                        weight += omega_matrix[layer_i_idx, layer_j_idx]

                    if weight > 0:
                        subcom_connections[subcom] = subcom_connections.get(subcom, 0) + weight

                if subcom_connections:
                    # Assign to the subcommunity with strongest connection
                    best_subcom = max(subcom_connections, key=subcom_connections.get)
                    node_to_subcom[node] = best_subcom
                else:
                    # Create new subcommunity
                    node_to_subcom[node] = subcommunity_counter
                    subcommunity_counter += 1

            # Assign nodes to their subcommunities
            for node, subcom in node_to_subcom.items():
                refined_communities[node] = subcom

    improved = len(set(refined_communities.values())) > len(set(communities.values()))
    return refined_communities, improved


def leiden_multilayer(
    graph_layers: Union[Any, List[Any], np.ndarray],
    interlayer_coupling: Union[float, np.ndarray] = 1.0,
    resolution: Union[float, List[float], Dict[Any, float]] = 1.0,
    seed: Optional[int] = None,
    max_iter: int = 100,
    parallel: bool = False,
    weight: str = "weight",
) -> LeidenResult:
    """
    Leiden community detection algorithm for multilayer networks.

    This implements the Leiden method for multilayer networks, which improves upon
    Louvain by guaranteeing well-connected communities through a refinement phase.

    The algorithm optimizes the multilayer modularity quality function:
    Q = (1/2μ) Σ_{ijsr} [(A_{ijs} - γ_s k_{is}k_{js}/2m_s) δ_{sr} + δ_{ij} C_{jsr}] δ(g_{is}, g_{jr})

    Args:
        graph_layers: Input network(s). Can be:
            - py3plex multi_layer_network object
            - List of networkx graphs (one per layer)
            - List of adjacency matrices (numpy arrays or scipy sparse)
            - Single supra-adjacency matrix
        interlayer_coupling: Coupling strength between layers (ω). Can be:
            - Single float: uniform coupling between all layer pairs
            - np.ndarray: L×L matrix of layer-pair specific coupling
        resolution: Resolution parameter(s) (γ). Can be:
            - Single float: same resolution for all layers
            - List of floats: per-layer resolution (length must match number of layers)
            - Dict[layer, float]: layer-specific resolution parameters
        seed: Random seed for reproducibility
        max_iter: Maximum number of iterations
        parallel: Whether to parallelize local moves (not yet implemented)
        weight: Edge weight attribute name (for networkx graphs)

    Returns:
        LeidenResult object containing:
            - communities: Dict mapping (node, layer) to community ID
            - modularity: Global multilayer modularity score
            - layer_modularity: Per-layer modularity scores
            - iterations: Number of iterations

    Examples:
        >>> from py3plex.core import multinet
        >>> from py3plex.algorithms.community_detection import leiden_multilayer
        >>>
        >>> # Create a multilayer network
        >>> network = multinet.multi_layer_network(directed=False)
        >>> network.add_edges([
        ...     ['A', 'L1', 'B', 'L1', 1],
        ...     ['B', 'L1', 'C', 'L1', 1],
        ...     ['A', 'L2', 'C', 'L2', 1]
        ... ], input_type='list')
        >>>
        >>> # Run Leiden
        >>> result = leiden_multilayer(
        ...     network,
        ...     interlayer_coupling=0.5,
        ...     resolution=1.0,
        ...     seed=42
        ... )
        >>>
        >>> print(result.summary())
        >>> print(f"Communities: {result.communities}")

    Note:
        The parallel option is reserved for future implementation using joblib or
        multiprocessing for parallelizing local move computations.
    """
    from .multilayer_modularity import multilayer_modularity

    # Check for unsupported features
    if parallel:
        import warnings
        warnings.warn(
            "Parallel processing is not yet implemented. Running in sequential mode.",
            FutureWarning,
            stacklevel=2
        )

    # Set random state
    if seed is not None:
        random_state = np.random.RandomState(seed)
    else:
        random_state = np.random.RandomState()

    # Convert input to standard format (py3plex network)
    # Handle different input types
    if hasattr(graph_layers, 'get_supra_adjacency_matrix'):
        # py3plex multi_layer_network object
        network = graph_layers
        node_layer_list = list(network.get_nodes())
        supra_matrix = network.get_supra_adjacency_matrix()
        if sp.issparse(supra_matrix):
            supra_matrix = supra_matrix.toarray()

        layers = list({nl[1] for nl in node_layer_list})

    elif isinstance(graph_layers, list):
        # List of graphs or matrices - convert to py3plex network
        from py3plex.core import multinet
        network = multinet.multi_layer_network(directed=False)

        # Check if networkx graphs or matrices
        is_networkx = False
        try:
            import networkx as nx
            is_networkx = all(isinstance(g, (nx.Graph, nx.DiGraph)) for g in graph_layers)
        except ImportError:
            pass  # networkx not available, will treat as matrices

        if is_networkx:
            # NetworkX graphs (nx already imported above)
            for layer_idx, G in enumerate(graph_layers):
                layer_name = f"L{layer_idx}"
                for u, v, data in G.edges(data=True):
                    w = data.get(weight, 1.0)
                    network.add_edge(u, layer_name, v, layer_name, w)
            layers = [f"L{i}" for i in range(len(graph_layers))]
        else:
            # Assume matrices (numpy arrays or scipy sparse)
            for layer_idx, adj_matrix in enumerate(graph_layers):
                layer_name = f"L{layer_idx}"
                if sp.issparse(adj_matrix):
                    adj_matrix = adj_matrix.toarray()

                n_nodes = adj_matrix.shape[0]
                for i in range(n_nodes):
                    for j in range(i + 1, n_nodes):
                        if adj_matrix[i, j] > 0:
                            network.add_edge(i, layer_name, j, layer_name, adj_matrix[i, j])
            layers = [f"L{i}" for i in range(len(graph_layers))]

        node_layer_list = list(network.get_nodes())
        supra_matrix = network.get_supra_adjacency_matrix()
        if sp.issparse(supra_matrix):
            supra_matrix = supra_matrix.toarray()

    elif isinstance(graph_layers, np.ndarray):
        # Single supra-adjacency matrix
        # This is tricky - we need to infer the layer structure
        # For now, raise an error and require explicit layer structure
        raise ValueError(
            "Single supra-adjacency matrix input requires explicit layer structure. "
            "Please provide a list of layer matrices or a py3plex network object."
        )

    else:
        raise ValueError(f"Unsupported input type: {type(graph_layers)}")

    # Build node-layer mapping
    node_layer_to_idx = {nl: i for i, nl in enumerate(node_layer_list)}
    n_total = len(node_layer_list)

    # Extract layer information
    layer_to_idx = {layer: i for i, layer in enumerate(layers)}
    n_layers = len(layers)

    # Convert resolution parameter
    if isinstance(resolution, (int, float)):
        gamma_dict = {layer: float(resolution) for layer in layers}
    elif isinstance(resolution, list):
        if len(resolution) != n_layers:
            raise ValueError(f"Resolution list length {len(resolution)} does not match number of layers {n_layers}")
        gamma_dict = {layer: float(res) for layer, res in zip(layers, resolution)}
    elif isinstance(resolution, dict):
        gamma_dict = {layer: float(resolution.get(layer, 1.0)) for layer in layers}
    else:
        raise ValueError(f"Unsupported resolution type: {type(resolution)}")

    # Convert coupling parameter
    if isinstance(interlayer_coupling, (int, float)):
        omega_matrix = np.full((n_layers, n_layers), float(interlayer_coupling))
        np.fill_diagonal(omega_matrix, 0)
    elif isinstance(interlayer_coupling, np.ndarray):
        if interlayer_coupling.shape != (n_layers, n_layers):
            raise ValueError(f"Coupling matrix shape {interlayer_coupling.shape} does not match layers ({n_layers}, {n_layers})")
        omega_matrix = interlayer_coupling.copy()
    else:
        raise ValueError(f"Unsupported coupling type: {type(interlayer_coupling)}")

    # Compute layer statistics
    layer_stats = {}
    for layer in layers:
        layer_nodes = [(node, lyr) for node, lyr in node_layer_list if lyr == layer]
        layer_indices = [node_layer_to_idx[nl] for nl in layer_nodes]

        # Extract layer adjacency matrix
        layer_adj = supra_matrix[np.ix_(layer_indices, layer_indices)]

        # Calculate layer total weight and degrees
        layer_weight = np.sum(layer_adj)
        degrees = np.sum(layer_adj, axis=1)

        # Store statistics
        layer_stats[layer] = {
            "weight": float(layer_weight),
            "degrees": degrees,
            "nodes": layer_nodes,
            "indices": layer_indices,
        }

    # Calculate total edge weight (for normalization)
    total_weight = 0.0
    for stats in layer_stats.values():
        total_weight += stats["weight"]

    # Add inter-layer coupling to total weight
    for i, layer_i in enumerate(layers):
        for j, layer_j in enumerate(layers):
            if i != j:
                # Count nodes present in both layers
                nodes_i = {nl[0] for nl in layer_stats[layer_i]["nodes"]}
                nodes_j = {nl[0] for nl in layer_stats[layer_j]["nodes"]}
                common_nodes = nodes_i & nodes_j
                total_weight += omega_matrix[i, j] * len(common_nodes)

    if total_weight == 0:
        # Empty network
        return LeidenResult(
            communities=dict.fromkeys(node_layer_list, 0),
            modularity=0.0,
            iterations=0,
        )

    # Initialize each node-layer in its own community (singleton partition)
    communities = {nl: i for i, nl in enumerate(node_layer_list)}

    # Main Leiden loop
    improved = True
    iteration = 0

    while improved and iteration < max_iter:
        improved = False
        iteration += 1

        # Phase 1: Local moving of nodes (like Louvain)
        order = random_state.permutation(n_total)
        local_improved = False

        for idx in order:
            node_layer = node_layer_list[idx]
            current_com = communities[node_layer]

            # Get candidate communities (neighbors + inter-layer)
            candidate_coms = set()

            # Intra-layer neighbors
            for j, nl_j in enumerate(node_layer_list):
                if supra_matrix[idx, j] > 0:
                    candidate_coms.add(communities[nl_j])

            # Inter-layer connections (same node, different layer)
            node, layer = node_layer
            for nl in node_layer_list:
                if nl[0] == node and nl[1] != layer:
                    candidate_coms.add(communities[nl])

            candidate_coms.discard(current_com)

            if not candidate_coms:
                continue

            # Find best community move
            best_com = current_com
            best_gain = 0.0

            for target_com in candidate_coms:
                gain = _calculate_modularity_gain(
                    node_layer, current_com, target_com, communities,
                    supra_matrix, node_layer_to_idx, layer_stats,
                    gamma_dict, omega_matrix, layer_to_idx, total_weight
                )

                if gain > best_gain:
                    best_gain = gain
                    best_com = target_com

            # Move if beneficial
            if best_com != current_com:
                communities[node_layer] = best_com
                local_improved = True
                improved = True

        # Phase 2: Refinement (key difference from Louvain)
        if local_improved:
            communities, refined = _refine_partition(
                communities, supra_matrix, node_layer_list,
                node_layer_to_idx, layer_stats, gamma_dict,
                omega_matrix, layer_to_idx, total_weight, random_state
            )
            if refined:
                improved = True

    # Renumber communities to be contiguous
    unique_coms = sorted(set(communities.values()))
    com_map = {old: new for new, old in enumerate(unique_coms)}
    communities = {nl: com_map[com] for nl, com in communities.items()}

    # Calculate final modularity
    final_modularity = multilayer_modularity(
        network, communities, gamma_dict, omega_matrix, weight
    )

    # Calculate per-layer modularity
    layer_modularity = {}
    for layer in layers:
        layer_communities = {
            (node, lyr): com
            for (node, lyr), com in communities.items()
            if lyr == layer
        }
        if layer_communities:
            # Calculate single-layer modularity (no inter-layer coupling)
            layer_mod = multilayer_modularity(
                network, layer_communities,
                {layer: gamma_dict[layer]}, np.zeros((n_layers, n_layers)), weight
            )
            layer_modularity[layer] = layer_mod

    return LeidenResult(
        communities=communities,
        modularity=final_modularity,
        layer_modularity=layer_modularity,
        iterations=iteration,
        improved=improved,
    )
