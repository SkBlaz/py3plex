"""
Multilayer Synthetic Graph Generation for Community Detection Benchmarks

This module implements synthetic multilayer/multiplex graph generators with
ground-truth community structure for benchmarking community detection algorithms.

Includes:
- Multilayer LFR (Lancichinetti-Fortunato-Radicchi) benchmark
- Coupled/Interdependent Erdős-Rényi models
- Support for overlapping communities across layers
- Support for partial node presence across layers

References:
    Lancichinetti et al., "Benchmark graphs for testing community detection
    algorithms", Phys. Rev. E 78, 046110 (2008)

    Granell et al., "Benchmark model to assess community structure in evolving
    networks", Phys. Rev. E 92, 012805 (2015)
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union

import networkx as nx
import numpy as np


def generate_multilayer_lfr(
    n: int,
    layers: List[str],
    tau1: float = 2.0,
    tau2: float = 1.5,
    mu: Union[float, List[float]] = 0.1,
    avg_degree: Union[float, List[float]] = 10.0,
    min_community: int = 20,
    max_community: Optional[int] = None,
    community_persistence: float = 1.0,
    node_overlap: float = 1.0,
    overlapping_nodes: int = 0,
    overlapping_membership: int = 2,
    directed: bool = False,
    seed: Optional[int] = None,
) -> Tuple[Any, Dict[Tuple[Any, str], Set[int]]]:
    """
    Generate multilayer LFR benchmark networks with controllable community structure.

    This extends the LFR benchmark to multilayer networks, allowing control over:
    - Community persistence across layers (how many nodes keep their community)
    - Node overlap across layers (which nodes appear in which layers)
    - Overlapping communities (nodes belonging to multiple communities)

    Args:
        n: Number of nodes
        layers: List of layer names
        tau1: Power-law exponent for degree distribution (typically 2-3)
        tau2: Power-law exponent for community size distribution (typically 1-2)
        mu: Mixing parameter (fraction of edges outside community).
            Can be float (same for all layers) or list of floats per layer.
            Range: [0, 1], where 0 = perfect communities, 1 = random
        avg_degree: Average degree per layer.
            Can be float (same for all layers) or list of floats per layer.
        min_community: Minimum community size
        max_community: Maximum community size (default: n/2)
        community_persistence: Probability that a node keeps its community from
            one layer to the next. Range: [0, 1]
            - 1.0 = identical communities across all layers
            - 0.0 = completely independent communities per layer
        node_overlap: Fraction of nodes present in all layers. Range: [0, 1]
            - 1.0 = all nodes in all layers (full multiplex)
            - <1.0 = some nodes absent from some layers
        overlapping_nodes: Number of nodes that belong to multiple communities
            within each layer
        overlapping_membership: Number of communities each overlapping node belongs to
        directed: Whether to generate directed networks
        seed: Random seed for reproducibility

    Returns:
        Tuple of (network, ground_truth_communities)
        - network: py3plex multi_layer_network object
        - ground_truth_communities: Dict mapping (node, layer) to Set of community IDs

    Examples:
        >>> from py3plex.algorithms.community_detection.multilayer_benchmark import generate_multilayer_lfr
        >>>
        >>> # Generate with identical communities across layers
        >>> network, communities = generate_multilayer_lfr(
        ...     n=100,
        ...     layers=['L1', 'L2', 'L3'],
        ...     mu=0.1,
        ...     community_persistence=1.0
        ... )
        >>>
        >>> # Generate with evolving communities
        >>> network, communities = generate_multilayer_lfr(
        ...     n=100,
        ...     layers=['T0', 'T1', 'T2'],
        ...     mu=0.1,
        ...     community_persistence=0.7  # 70% nodes keep community
        ... )
    """
    if seed is not None:
        np.random.seed(seed)

    from py3plex.core import multinet

    if max_community is None:
        max_community = n // 2

    # Convert single values to lists
    n_layers = len(layers)
    if isinstance(mu, (int, float)):
        mu = [float(mu)] * n_layers
    if isinstance(avg_degree, (int, float)):
        avg_degree = [float(avg_degree)] * n_layers

    # Determine which nodes appear in which layers
    if node_overlap < 1.0:
        # Some nodes don't appear in all layers
        node_layers = {}
        for node in range(n):
            if np.random.random() < node_overlap:
                # Node appears in all layers
                node_layers[node] = set(layers)
            else:
                # Node appears in subset of layers
                n_present = np.random.randint(1, n_layers + 1)
                node_layers[node] = set(
                    np.random.choice(layers, n_present, replace=False)
                )
    else:
        # All nodes in all layers (full multiplex)
        node_layers = {node: set(layers) for node in range(n)}

    # Generate initial community structure (for first layer or reference)
    communities = _generate_power_law_communities(
        n, tau2, min_community, max_community, seed
    )

    # Handle overlapping communities
    if overlapping_nodes > 0:
        communities = _add_overlapping_nodes(
            communities, overlapping_nodes, overlapping_membership, seed
        )

    # Generate layer-specific communities
    layer_communities = {}
    prev_communities = communities

    for i, layer in enumerate(layers):
        if i == 0:
            # First layer uses the base communities
            layer_communities[layer] = prev_communities.copy()
        else:
            # Subsequent layers: nodes persist with probability community_persistence
            new_communities = {}
            for node in range(n):
                if node in prev_communities:
                    if np.random.random() < community_persistence:
                        # Keep same community(ies)
                        new_communities[node] = prev_communities[node].copy()
                    else:
                        # Reassign to different community
                        all_coms = set()
                        for coms in prev_communities.values():
                            all_coms.update(coms)
                        if all_coms:
                            new_com = np.random.choice(list(all_coms))
                            new_communities[node] = {new_com}
            layer_communities[layer] = new_communities
            prev_communities = new_communities

    # Generate network structure for each layer
    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()

    for layer_idx, layer in enumerate(layers):
        layer_mu = mu[layer_idx]
        layer_avg_deg = avg_degree[layer_idx]
        layer_coms = layer_communities[layer]

        # Get nodes present in this layer
        layer_nodes = [node for node in range(n) if layer in node_layers[node]]

        if not layer_nodes:
            continue

        # Generate degree sequence with power law
        degrees = _generate_power_law_degrees(
            len(layer_nodes), tau1, layer_avg_deg, seed
        )

        # Build community graph
        edges = _generate_lfr_edges(
            layer_nodes, degrees, layer_coms, layer_mu, directed, seed
        )

        # Add edges to multilayer network
        for u, v in edges:
            G.add_edge((u, layer), (v, layer), weight=1)

    # Create py3plex network
    network = multinet.multi_layer_network(
        network_type="multiplex", directed=directed
    ).load_network(G, input_type="nx", directed=directed)

    # Convert communities to (node, layer) format
    ground_truth = {}
    for layer in layers:
        if layer in layer_communities:
            for node, coms in layer_communities[layer].items():
                if layer in node_layers[node]:
                    ground_truth[(node, layer)] = coms

    return network, ground_truth


def generate_coupled_er_multilayer(
    n: int,
    layers: List[str],
    p: Union[float, List[float]] = 0.1,
    omega: float = 1.0,
    coupling_probability: float = 1.0,
    directed: bool = False,
    seed: Optional[int] = None,
) -> Any:
    """
    Generate coupled/interdependent Erdős-Rényi multilayer networks.

    Creates random Erdős-Rényi graphs in each layer and couples nodes across
    layers with specified coupling strength and probability.

    Args:
        n: Number of nodes
        layers: List of layer names
        p: Edge probability per layer.
            Can be float (same for all layers) or list of floats per layer.
        omega: Inter-layer coupling strength (weight of identity links)
        coupling_probability: Probability that a node has inter-layer coupling.
            Range: [0, 1]
            - 1.0 = all nodes coupled (full multiplex)
            - <1.0 = partial coupling (interdependent networks)
        directed: Whether to generate directed networks
        seed: Random seed for reproducibility

    Returns:
        py3plex multi_layer_network object

    Examples:
        >>> from py3plex.algorithms.community_detection.multilayer_benchmark import generate_coupled_er_multilayer
        >>>
        >>> # Full multiplex ER network
        >>> network = generate_coupled_er_multilayer(
        ...     n=100,
        ...     layers=['L1', 'L2', 'L3'],
        ...     p=0.1,
        ...     omega=1.0,
        ...     coupling_probability=1.0
        ... )
        >>>
        >>> # Partially coupled (interdependent)
        >>> network = generate_coupled_er_multilayer(
        ...     n=100,
        ...     layers=['L1', 'L2'],
        ...     p=0.1,
        ...     omega=0.5,
        ...     coupling_probability=0.5  # Only 50% nodes coupled
        ... )
    """
    if seed is not None:
        np.random.seed(seed)

    from py3plex.core import multinet

    n_layers = len(layers)

    # Convert single value to list
    if isinstance(p, (int, float)):
        p = [float(p)] * n_layers

    # Create base graph
    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()

    # Generate ER graph for each layer
    for layer_idx, layer in enumerate(layers):
        layer_p = p[layer_idx]

        # Generate random edges
        for i in range(n):
            for j in range(i + 1, n) if not directed else range(n):
                if i != j and np.random.random() < layer_p:
                    G.add_edge((i, layer), (j, layer), weight=1)

    # Add inter-layer coupling
    if omega > 0:
        coupled_nodes = np.random.choice(
            n, size=int(n * coupling_probability), replace=False
        )

        for node in coupled_nodes:
            # Add coupling between all layer pairs for this node
            for i in range(n_layers):
                for j in range(i + 1, n_layers):
                    # Identity coupling: node i in layer_i to node i in layer_j
                    G.add_edge(
                        (node, layers[i]),
                        (node, layers[j]),
                        weight=omega,
                        type="coupling",
                    )

    # Create py3plex network
    network = multinet.multi_layer_network(
        network_type="multiplex", directed=directed
    ).load_network(G, input_type="nx", directed=directed)

    return network


def generate_sbm_multilayer(
    n: int,
    layers: List[str],
    communities: List[Set[int]],
    p_in: Union[float, List[float]] = 0.3,
    p_out: Union[float, List[float]] = 0.05,
    community_persistence: float = 1.0,
    directed: bool = False,
    seed: Optional[int] = None,
) -> Tuple[Any, Dict[Tuple[Any, str], int]]:
    """
    Generate multilayer stochastic block model (SBM) networks.

    Creates networks where nodes are divided into communities with different
    intra- and inter-community connection probabilities.

    Args:
        n: Number of nodes
        layers: List of layer names
        communities: List of node sets defining initial communities
        p_in: Intra-community edge probability per layer
        p_out: Inter-community edge probability per layer
        community_persistence: Probability nodes keep their community across layers
        directed: Whether to generate directed networks
        seed: Random seed for reproducibility

    Returns:
        Tuple of (network, ground_truth_communities)
        - network: py3plex multi_layer_network object
        - ground_truth_communities: Dict mapping (node, layer) to community ID

    Examples:
        >>> from py3plex.algorithms.community_detection.multilayer_benchmark import generate_sbm_multilayer
        >>>
        >>> # Define initial communities
        >>> communities = [
        ...     {0, 1, 2, 3, 4},  # Community 0
        ...     {5, 6, 7, 8, 9}   # Community 1
        ... ]
        >>>
        >>> network, ground_truth = generate_sbm_multilayer(
        ...     n=10,
        ...     layers=['L1', 'L2'],
        ...     communities=communities,
        ...     p_in=0.7,
        ...     p_out=0.1,
        ...     community_persistence=0.8
        ... )
    """
    if seed is not None:
        np.random.seed(seed)

    from py3plex.core import multinet

    n_layers = len(layers)
    n_communities = len(communities)

    # Convert single values to lists
    if isinstance(p_in, (int, float)):
        p_in = [float(p_in)] * n_layers
    if isinstance(p_out, (int, float)):
        p_out = [float(p_out)] * n_layers

    # Initialize node-to-community mapping
    node_to_com_initial = {}
    for com_id, com_nodes in enumerate(communities):
        for node in com_nodes:
            node_to_com_initial[node] = com_id

    # Generate layer-specific community assignments
    layer_communities = {}
    for i, layer in enumerate(layers):
        if i == 0:
            # First layer uses initial communities
            layer_communities[layer] = node_to_com_initial.copy()
        else:
            # Subsequent layers: persist with probability
            new_assignment = {}
            for node in range(n):
                if node in layer_communities[layers[i - 1]]:
                    if np.random.random() < community_persistence:
                        # Keep same community
                        new_assignment[node] = layer_communities[layers[i - 1]][node]
                    else:
                        # Reassign to random community
                        new_assignment[node] = np.random.randint(n_communities)
            layer_communities[layer] = new_assignment

    # Generate network
    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()

    for layer_idx, layer in enumerate(layers):
        layer_p_in = p_in[layer_idx]
        layer_p_out = p_out[layer_idx]
        node_to_com = layer_communities[layer]

        # Generate edges based on SBM
        for i in range(n):
            for j in range(i + 1, n) if not directed else range(n):
                if i == j:
                    continue

                com_i = node_to_com.get(i, -1)
                com_j = node_to_com.get(j, -1)

                # Determine connection probability
                if com_i == com_j:
                    prob = layer_p_in
                else:
                    prob = layer_p_out

                if np.random.random() < prob:
                    G.add_edge((i, layer), (j, layer), weight=1)

    # Create py3plex network
    network = multinet.multi_layer_network(
        network_type="multiplex", directed=directed
    ).load_network(G, input_type="nx", directed=directed)

    # Convert to ground truth format
    ground_truth = {}
    for layer in layers:
        for node, com in layer_communities[layer].items():
            ground_truth[(node, layer)] = com

    return network, ground_truth


# Helper functions


def _generate_power_law_communities(
    n: int,
    tau: float,
    min_size: int,
    max_size: int,
    seed: Optional[int] = None,
) -> Dict[int, Set[int]]:
    """Generate communities with power-law size distribution."""
    if seed is not None:
        np.random.seed(seed)

    communities = {}
    assigned: Set[int] = set()
    com_id = 0

    while len(assigned) < n:
        # Sample community size from power law
        size = int(np.random.pareto(tau - 1) * min_size)
        size = max(min_size, min(size, max_size))
        size = min(size, n - len(assigned))

        if size < min_size:
            size = n - len(assigned)

        # Assign random unassigned nodes to this community
        available = [node for node in range(n) if node not in assigned]
        if not available:
            break

        com_nodes = np.random.choice(
            available, size=min(size, len(available)), replace=False
        )
        communities[com_id] = {com_id}  # Each node initially has one community

        for node in com_nodes:
            assigned.add(node)

        com_id += 1

    # Convert to node -> community mapping
    node_to_com = {}
    for node in range(n):
        # Find which community this node belongs to (simplified assignment)
        node_to_com[node] = {node % com_id}  # Simple round-robin for now

    return node_to_com


def _add_overlapping_nodes(
    communities: Dict[int, Set[int]],
    n_overlapping: int,
    n_memberships: int,
    seed: Optional[int] = None,
) -> Dict[int, Set[int]]:
    """Add overlapping community memberships to nodes."""
    if seed is not None:
        np.random.seed(seed)

    nodes = list(communities.keys())
    if n_overlapping > len(nodes):
        n_overlapping = len(nodes)

    overlapping_nodes = np.random.choice(nodes, n_overlapping, replace=False)

    all_communities = set()
    for coms in communities.values():
        all_communities.update(coms)
    all_communities_list: List[int] = list(all_communities)

    for node in overlapping_nodes:
        # Add additional communities
        current_coms = communities[node]
        available_coms = [c for c in all_communities_list if c not in current_coms]

        if available_coms:
            n_add = min(n_memberships - len(current_coms), len(available_coms))
            if n_add > 0:
                new_coms = np.random.choice(available_coms, n_add, replace=False)
                communities[node].update(new_coms)

    return communities


def _generate_power_law_degrees(
    n: int,
    tau: float,
    avg_degree: float,
    seed: Optional[int] = None,
) -> np.ndarray:
    """Generate degree sequence with power-law distribution."""
    if seed is not None:
        np.random.seed(seed)

    # Sample from power law
    degrees = np.random.pareto(tau - 1, n) * (avg_degree / 2)
    degrees = np.maximum(degrees, 1)  # At least degree 1
    degrees = degrees.astype(int)

    # Ensure even sum for undirected graph
    total: int = int(np.sum(degrees))
    if total % 2 != 0:
        degrees[0] += 1

    result: np.ndarray = degrees
    return result


def _generate_lfr_edges(
    nodes: List[int],
    degrees: np.ndarray,
    communities: Dict[int, Set[int]],
    mu: float,
    directed: bool,
    seed: Optional[int] = None,
) -> List[Tuple[int, int]]:
    """Generate edges for LFR benchmark with mixing parameter mu."""
    if seed is not None:
        np.random.seed(seed)

    edges = []
    node_to_idx = {node: i for i, node in enumerate(nodes)}

    # Build community structure
    com_to_nodes: dict = {}
    for node, coms in communities.items():
        if node in node_to_idx:
            for com in coms:
                if com not in com_to_nodes:
                    com_to_nodes[com] = []
                com_to_nodes[com].append(node)

    # Generate edges for each node
    for i, node in enumerate(nodes):
        deg = degrees[i]

        # Determine internal vs external edges
        n_internal = int(deg * (1 - mu))
        n_external = int(deg - n_internal)

        # Get node's communities
        node_coms = communities.get(node, {0})

        # Internal edges (within community)
        internal_candidates = []
        for com in node_coms:
            if com in com_to_nodes:
                internal_candidates.extend([n for n in com_to_nodes[com] if n != node])

        if internal_candidates:
            internal_targets = np.random.choice(
                internal_candidates,
                size=min(n_internal, len(internal_candidates)),
                replace=False,
            )
            for target in internal_targets:
                if node < target or directed:
                    edges.append((node, target))

        # External edges (outside community)
        external_candidates = [
            n for n in nodes if n != node and n not in internal_candidates
        ]

        if external_candidates:
            external_targets = np.random.choice(
                external_candidates,
                size=min(n_external, len(external_candidates)),
                replace=False,
            )
            for target in external_targets:
                if node < target or directed:
                    edges.append((node, target))

    return edges
