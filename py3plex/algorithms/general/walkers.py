"""
Random walk primitives for graph-based algorithms.

This module provides foundation for higher-level algorithms like Node2Vec,
DeepWalk, and diffusion processes. Implements both basic and second-order
(biased) random walks with proper edge weight handling and multilayer support.

Key Features:
    - Basic random walks with weighted edge sampling
    - Second-order (Node2Vec-style) biased random walks with p/q parameters
    - Multiple simultaneous walks with deterministic reproducibility
    - Support for directed, weighted, and multilayer networks
    - Efficient sparse adjacency handling

References:
    - Grover, A., & Leskovec, J. (2016). node2vec: Scalable feature learning for networks.
      KDD '16. https://doi.org/10.1145/2939672.2939754
    - Perozzi, B., Al-Rfou, R., & Skiena, S. (2014). DeepWalk: Online learning of social
      representations. KDD '14. https://doi.org/10.1145/2623330.2623732
"""

from typing import Any, List, Optional, Tuple, Union

import networkx as nx
import numpy as np

from py3plex.utils import get_rng


def basic_random_walk(
    G: nx.Graph,
    start_node: Union[int, str],
    walk_length: int,
    weighted: bool = True,
    seed: Optional[int] = None,
) -> List[Union[int, str]]:
    """
    Perform a basic random walk on a graph with proper edge weight handling.

    The next step is sampled proportionally to the normalized edge weights
    of the current node. For unweighted graphs, transitions are uniform.

    Args:
        G: NetworkX graph (directed or undirected, weighted or unweighted)
        start_node: Node to start the walk from
        walk_length: Number of steps in the walk
        weighted: Whether to use edge weights (default: True)
        seed: Random seed for reproducibility (default: None)

    Returns:
        List of nodes representing the walk path (includes start_node)

    Raises:
        ValueError: If start_node not in graph or walk_length < 1

    Examples:
        >>> G = nx.Graph()
        >>> G.add_weighted_edges_from([(0, 1, 1.0), (1, 2, 2.0), (1, 3, 1.0)])
        >>> walk = basic_random_walk(G, 0, walk_length=3, seed=42)
        >>> len(walk)
        4
        >>> walk[0]
        0

    Note:
        - Handles disconnected nodes by terminating walk early
        - Edge weights must be positive for weighted walks
        - Sum of transition probabilities from any node equals 1.0
    """
    if start_node not in G:
        raise ValueError(f"Start node {start_node} not in graph")
    if walk_length < 1:
        raise ValueError(f"Walk length must be >= 1, got {walk_length}")

    rng = get_rng(seed)
    walk = [start_node]
    current = start_node

    for _ in range(walk_length):
        neighbors = list(G.neighbors(current))

        # Handle isolated nodes
        if len(neighbors) == 0:
            break

        # Get edge weights if weighted
        if weighted and G.is_multigraph():
            # For multigraphs, sum weights across all edges between node pairs
            weight_list = []
            for neighbor in neighbors:
                edge_data = G.get_edge_data(current, neighbor)
                if isinstance(edge_data, dict):
                    # Single edge
                    weight_list.append(edge_data.get("weight", 1.0))
                else:
                    # Multiple edges (multigraph)
                    total_weight = sum(d.get("weight", 1.0) for d in edge_data.values())
                    weight_list.append(total_weight)
            weights = np.array(weight_list)
        elif weighted:
            weights = np.array(
                [G[current][neighbor].get("weight", 1.0) for neighbor in neighbors]
            )
        else:
            weights = np.ones(len(neighbors))

        # Normalize to probabilities
        probabilities = weights / weights.sum()

        # Sample next node (use index to avoid numpy array issues with tuple nodes)
        idx = rng.choice(len(neighbors), p=probabilities)
        current = neighbors[idx]
        walk.append(current)

    return walk


def node2vec_walk(
    G: nx.Graph,
    start_node: Union[int, str],
    walk_length: int,
    p: float = 1.0,
    q: float = 1.0,
    weighted: bool = True,
    seed: Optional[int] = None,
) -> List[Union[int, str]]:
    """
    Perform a second-order (biased) random walk following Node2Vec logic.

    When transitioning from node t → v → x, the probability of choosing x
    is biased by parameters p (return) and q (in-out):
    - If x == t (return to previous): weight / p
    - If x is neighbor of t (stay close): weight / 1
    - If x is not neighbor of t (explore): weight / q

    Args:
        G: NetworkX graph (directed or undirected, weighted or unweighted)
        start_node: Node to start the walk from
        walk_length: Number of steps in the walk
        p: Return parameter (higher p = less likely to return to previous node)
        q: In-out parameter (higher q = less likely to explore further)
        weighted: Whether to use edge weights (default: True)
        seed: Random seed for reproducibility (default: None)

    Returns:
        List of nodes representing the walk path (includes start_node)

    Raises:
        ValueError: If p <= 0 or q <= 0 or start_node not in graph

    Examples:
        >>> G = nx.Graph()
        >>> G.add_edges_from([(0, 1), (1, 2), (1, 3), (0, 2)])
        >>> # Low p, high q: tends to backtrack
        >>> walk = node2vec_walk(G, 0, walk_length=5, p=0.1, q=10.0, seed=42)
        >>> # High p, low q: tends to explore outward
        >>> walk2 = node2vec_walk(G, 0, walk_length=5, p=10.0, q=0.1, seed=42)

    Note:
        - First step is always a basic random walk (no previous node)
        - Properly normalizes probabilities at each step
        - Handles disconnected nodes by terminating early

    References:
        Grover & Leskovec (2016), node2vec: Scalable feature learning for networks
    """
    if start_node not in G:
        raise ValueError(f"Start node {start_node} not in graph")
    if walk_length < 1:
        raise ValueError(f"Walk length must be >= 1, got {walk_length}")
    if p <= 0:
        raise ValueError(f"Parameter p must be positive, got {p}")
    if q <= 0:
        raise ValueError(f"Parameter q must be positive, got {q}")

    rng = get_rng(seed)
    walk = [start_node]

    # First step is a basic random walk (no previous context)
    if walk_length == 0:
        return walk

    neighbors = list(G.neighbors(start_node))
    if len(neighbors) == 0:
        return walk

    if weighted:
        weights = np.array(
            [G[start_node][neighbor].get("weight", 1.0) for neighbor in neighbors]
        )
    else:
        weights = np.ones(len(neighbors))

    probabilities = weights / weights.sum()
    idx = rng.choice(len(neighbors), p=probabilities)
    current = neighbors[idx]
    walk.append(current)

    # Subsequent steps use second-order bias
    for _ in range(walk_length - 1):
        prev = walk[-2]
        current = walk[-1]
        neighbors = list(G.neighbors(current))

        if len(neighbors) == 0:
            break

        # Get neighbors of previous node for bias computation
        prev_neighbors = set(G.neighbors(prev))

        # Compute biased weights
        biased_weight_list = []
        for neighbor in neighbors:
            if weighted:
                edge_weight = G[current][neighbor].get("weight", 1.0)
            else:
                edge_weight = 1.0

            # Apply Node2Vec bias
            if neighbor == prev:
                # Return to previous node
                biased_weight = edge_weight / p
            elif neighbor in prev_neighbors:
                # Stay close (common neighbor)
                biased_weight = edge_weight
            else:
                # Explore further (not a neighbor of prev)
                biased_weight = edge_weight / q

            biased_weight_list.append(biased_weight)

        biased_weights = np.array(biased_weight_list)
        probabilities = biased_weights / biased_weights.sum()

        idx = rng.choice(len(neighbors), p=probabilities)
        next_node = neighbors[idx]
        walk.append(next_node)

    return walk


def generate_walks(
    G: nx.Graph,
    num_walks: int,
    walk_length: int,
    start_nodes: Optional[List[Union[int, str]]] = None,
    p: float = 1.0,
    q: float = 1.0,
    weighted: bool = True,
    return_edges: bool = False,
    seed: Optional[int] = None,
) -> Union[
    List[List[Union[int, str]]], List[List[Tuple[Union[int, str], Union[int, str]]]]
]:
    """
    Generate multiple random walks from specified or all nodes.

    This interface supports multiple simultaneous walks with deterministic
    reproducibility under fixed RNG seed. Can return either node sequences
    or edge sequences.

    Args:
        G: NetworkX graph
        num_walks: Number of walks to generate per start node
        walk_length: Number of steps in each walk
        start_nodes: Nodes to start walks from (if None, uses all nodes)
        p: Return parameter for Node2Vec (1.0 = no bias)
        q: In-out parameter for Node2Vec (1.0 = no bias)
        weighted: Whether to use edge weights
        return_edges: Return edge sequences instead of node sequences
        seed: Random seed for reproducibility

    Returns:
        List of walks, where each walk is either:
        - List of nodes (if return_edges=False)
        - List of edges as tuples (if return_edges=True)

    Examples:
        >>> G = nx.karate_club_graph()
        >>> # Generate 10 walks from each node
        >>> walks = generate_walks(G, num_walks=10, walk_length=5, seed=42)
        >>> len(walks)
        340

        >>> # Generate walks with Node2Vec bias
        >>> walks = generate_walks(G, num_walks=5, walk_length=10, p=0.5, q=2.0, seed=42)

        >>> # Get edge sequences
        >>> edge_walks = generate_walks(G, num_walks=3, walk_length=5, return_edges=True, seed=42)

    Note:
        - With same seed, generates identical walks across runs
        - If p == q == 1.0, uses basic random walk (faster)
        - Empty walks are included if node has no neighbors
    """
    if start_nodes is None:
        start_nodes = list(G.nodes())

    rng = get_rng(seed)
    walks: List[Any] = []

    # Use basic walk if no bias
    use_biased = p != 1.0 or q != 1.0

    for _ in range(num_walks):
        # Shuffle start nodes for better mixing
        shuffled_nodes = start_nodes.copy()
        rng.shuffle(shuffled_nodes)

        for node in shuffled_nodes:
            # Generate walk with a unique seed for reproducibility
            walk_seed = int(rng.integers(0, 2**31))

            if use_biased:
                walk = node2vec_walk(G, node, walk_length, p, q, weighted, walk_seed)
            else:
                walk = basic_random_walk(G, node, walk_length, weighted, walk_seed)

            if return_edges:
                # Convert node sequence to edge sequence
                edge_walk = [(walk[i], walk[i + 1]) for i in range(len(walk) - 1)]
                walks.append(edge_walk)
            else:
                walks.append(walk)

    return walks


def general_random_walk(G, start_node, iterations=1000, teleportation_prob=0):
    """
    Legacy random walk with teleportation (for backward compatibility).

    .. deprecated:: 0.95a
        Use :func:`basic_random_walk` or :func:`node2vec_walk` instead.
        This function will be removed in version 1.0.

    Args:
        G: NetworkX graph
        start_node: Starting node
        iterations: Number of steps
        teleportation_prob: Probability of teleporting to random visited node

    Returns:
        List of visited nodes (excluding start_node)
    """
    import warnings

    warnings.warn(
        "general_random_walk is deprecated. Use basic_random_walk or node2vec_walk instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    rng = np.random.default_rng()
    x = 0
    trace = []

    while x < iterations:
        neighbors = list(G.neighbors(start_node))
        num_neighbors = len(neighbors)

        if num_neighbors == 0:
            break

        # Check teleportation
        if (
            teleportation_prob > 0
            and len(trace) > 0
            and rng.random() < teleportation_prob
        ):
            idx = rng.choice(len(trace))
            start_node = trace[idx]
            continue

        # Sample next neighbor uniformly
        idx = rng.choice(len(neighbors))
        new_pivot = neighbors[idx]
        trace.append(new_pivot)
        start_node = new_pivot
        x += 1

    return trace


def layer_specific_random_walk(
    G: nx.Graph,
    start_node: Union[int, str],
    walk_length: int,
    layer: Optional[str] = None,
    cross_layer_prob: float = 0.0,
    weighted: bool = True,
    seed: Optional[int] = None,
) -> List[Union[int, str]]:
    """
    Perform random walk with layer constraints for multilayer networks.

    In a multilayer network represented in py3plex format (where node names
    include layer information), this function can constrain walks to specific
    layers with occasional inter-layer transitions.

    Args:
        G: NetworkX graph (multilayer network in py3plex format)
        start_node: Node to start walk from (may include layer info)
        walk_length: Number of steps in the walk
        layer: Target layer to constrain walk to (None = no constraint)
        cross_layer_prob: Probability of crossing to different layer (0-1)
        weighted: Whether to use edge weights
        seed: Random seed for reproducibility

    Returns:
        List of nodes representing the walk path

    Examples:
        >>> # Multilayer network with layer-specific walks
        >>> from py3plex.core import multinet
        >>> network = multinet.multi_layer_network()
        >>> network.add_layer("social")
        >>> network.add_layer("biological")
        >>> # ... add nodes and edges ...
        >>> walk = layer_specific_random_walk(
        ...     network.core_network,
        ...     "nodeA---social",
        ...     walk_length=10,
        ...     layer="social",
        ...     cross_layer_prob=0.1
        ... )

    Note:
        - If layer is None, behaves like basic_random_walk
        - cross_layer_prob controls inter-layer transitions
        - Node format should follow py3plex convention: "nodeID---layerID"
    """
    if start_node not in G:
        raise ValueError(f"Start node {start_node} not in graph")
    if walk_length < 1:
        raise ValueError(f"Walk length must be >= 1, got {walk_length}")
    if not (0 <= cross_layer_prob <= 1):
        raise ValueError(f"cross_layer_prob must be in [0, 1], got {cross_layer_prob}")

    rng = get_rng(seed)
    walk = [start_node]
    current = start_node

    # Extract layer delimiter (py3plex default is "---")
    delimiter = "---"

    for _ in range(walk_length):
        neighbors = list(G.neighbors(current))

        if len(neighbors) == 0:
            break

        # Filter neighbors by layer if specified
        if layer is not None and rng.random() > cross_layer_prob:
            # Stay within layer
            layer_neighbors = [
                n
                for n in neighbors
                if delimiter in str(n) and str(n).split(delimiter)[-1] == layer
            ]
            if len(layer_neighbors) > 0:
                neighbors = layer_neighbors

        # Get weights
        if weighted:
            weights = np.array(
                [G[current][neighbor].get("weight", 1.0) for neighbor in neighbors]
            )
        else:
            weights = np.ones(len(neighbors))

        probabilities = weights / weights.sum()
        idx = rng.choice(len(neighbors), p=probabilities)
        current = neighbors[idx]
        walk.append(current)

    return walk
