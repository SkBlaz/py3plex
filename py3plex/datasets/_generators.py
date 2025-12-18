"""
Synthetic network generators for py3plex.

These generators create synthetic multilayer/multiplex networks
for testing, benchmarking, and teaching purposes.
"""

from typing import Optional

import networkx as nx
import numpy as np

from py3plex.core.multinet import multi_layer_network


def make_random_multilayer(
    n_nodes: int = 50,
    n_layers: int = 3,
    p: float = 0.1,
    directed: bool = False,
    random_state: Optional[int] = None,
) -> multi_layer_network:
    """
    Generate a random multilayer Erdős-Rényi network.

    Nodes are randomly distributed across layers, and edges are added
    according to the Erdős-Rényi model.

    Parameters
    ----------
    n_nodes : int, default=50
        Number of nodes in the network.
    n_layers : int, default=3
        Number of layers.
    p : float, default=0.1
        Probability of edge creation between any pair of nodes.
    directed : bool, default=False
        If True, create a directed network.
    random_state : int, optional
        Seed for random number generator for reproducibility.

    Returns
    -------
    multi_layer_network
        A multilayer network object.

    Examples
    --------
    >>> from py3plex.datasets import make_random_multilayer
    >>> net = make_random_multilayer(n_nodes=30, n_layers=2, p=0.15)
    >>> print(len(list(net.get_nodes())))  # Number of nodes
    """
    if n_nodes <= 0:
        raise ValueError("n_nodes must be positive")
    if n_layers <= 0:
        raise ValueError("n_layers must be positive")
    if not 0 <= p <= 1:
        raise ValueError("p must be in [0, 1]")

    if random_state is not None:
        np.random.seed(random_state)

    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()

    # Generate base ER graph
    network = nx.gnp_random_graph(n_nodes, p, seed=random_state, directed=directed)

    # Assign nodes to layers
    if n_nodes >= n_layers:
        layers = {}
        for i in range(n_layers):
            layers[i] = i
        for i in range(n_layers, n_nodes):
            layers[i] = np.random.randint(n_layers)
    else:
        layers = dict(zip(range(n_nodes), range(n_nodes)))

    # Add nodes
    for node in network.nodes():
        G.add_node((node, layers[node]), type="default")

    # Add edges
    for edge in network.edges():
        G.add_edge(
            (edge[0], layers[edge[0]]),
            (edge[1], layers[edge[1]]),
            type="default"
        )

    return multi_layer_network(network_type="multilayer").load_network(
        G, input_type="nx", directed=directed
    )


def make_random_multiplex(
    n_nodes: int = 50,
    n_layers: int = 3,
    p: float = 0.1,
    directed: bool = False,
    random_state: Optional[int] = None,
) -> multi_layer_network:
    """
    Generate a random multiplex Erdős-Rényi network.

    Each node appears in all layers, and edges are independently generated
    in each layer according to the Erdős-Rényi model.

    Parameters
    ----------
    n_nodes : int, default=50
        Number of nodes in the network.
    n_layers : int, default=3
        Number of layers.
    p : float, default=0.1
        Probability of edge creation between any pair of nodes in each layer.
    directed : bool, default=False
        If True, create a directed network.
    random_state : int, optional
        Seed for random number generator for reproducibility.

    Returns
    -------
    multi_layer_network
        A multiplex network object.

    Examples
    --------
    >>> from py3plex.datasets import make_random_multiplex
    >>> net = make_random_multiplex(n_nodes=30, n_layers=3, p=0.1)
    >>> print(len(net.get_layers()))  # Should be 3
    """
    if n_nodes <= 0:
        raise ValueError("n_nodes must be positive")
    if n_layers <= 0:
        raise ValueError("n_layers must be positive")
    if not 0 <= p <= 1:
        raise ValueError("p must be in [0, 1]")

    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()

    # Ensure every node is present in every layer, even if no edges are sampled
    for node in range(n_nodes):
        for layer_idx in range(n_layers):
            G.add_node((node, layer_idx), type="default")

    for layer_idx in range(n_layers):
        # Use multiplication to ensure good seed separation between layers
        layer_seed = (
            random_state * 1000 + layer_idx if random_state is not None else None
        )
        network = nx.fast_gnp_random_graph(n_nodes, p, seed=layer_seed, directed=directed)
        for edge in network.edges():
            G.add_edge(
                (edge[0], layer_idx),
                (edge[1], layer_idx),
                type="default"
            )

    return multi_layer_network(network_type="multiplex").load_network(
        G, input_type="nx", directed=directed
    )


def make_clique_multiplex(
    n_nodes: int = 20,
    n_layers: int = 3,
    clique_size: int = 5,
    n_cliques: int = 3,
    random_state: Optional[int] = None,
) -> multi_layer_network:
    """
    Generate a multiplex network with clique structure.

    Creates a network where each layer contains multiple cliques
    (fully connected subgraphs) with some nodes overlapping.

    Parameters
    ----------
    n_nodes : int, default=20
        Total number of nodes.
    n_layers : int, default=3
        Number of layers.
    clique_size : int, default=5
        Size of each clique.
    n_cliques : int, default=3
        Number of cliques per layer.
    random_state : int, optional
        Seed for random number generator for reproducibility.

    Returns
    -------
    multi_layer_network
        A multiplex network with clique structure.

    Examples
    --------
    >>> from py3plex.datasets import make_clique_multiplex
    >>> net = make_clique_multiplex(n_nodes=15, n_layers=2, clique_size=4)
    """
    if n_nodes <= 0:
        raise ValueError("n_nodes must be positive")
    if n_layers <= 0:
        raise ValueError("n_layers must be positive")
    if clique_size <= 0:
        raise ValueError("clique_size must be positive")
    if n_cliques <= 0:
        raise ValueError("n_cliques must be positive")

    if random_state is not None:
        np.random.seed(random_state)

    G = nx.MultiGraph()

    # In a multiplex network, every node exists in every layer (even if isolated).
    for node in range(n_nodes):
        for layer_idx in range(n_layers):
            G.add_node((node, layer_idx), type="default")

    for layer_idx in range(n_layers):
        for _ in range(n_cliques):
            # Select random nodes for this clique
            clique_nodes = np.random.choice(n_nodes, size=min(clique_size, n_nodes), replace=False)

            # Add all edges within the clique
            for i in range(len(clique_nodes)):
                for j in range(i + 1, len(clique_nodes)):
                    G.add_edge(
                        (int(clique_nodes[i]), layer_idx),
                        (int(clique_nodes[j]), layer_idx),
                        type="default",
                        weight=1
                    )

    return multi_layer_network(network_type="multiplex").load_network(
        G, input_type="nx", directed=False
    )


def make_social_network(
    n_people: int = 30,
    random_state: Optional[int] = None,
) -> multi_layer_network:
    """
    Generate a synthetic social multiplex network.

    Creates a network with typical social network layers:
    - friendship: Dense connections based on social proximity
    - work: Work-related connections (sparser)
    - family: Small, tight-knit clusters

    Parameters
    ----------
    n_people : int, default=30
        Number of people (nodes) in the network.
    random_state : int, optional
        Seed for random number generator for reproducibility.

    Returns
    -------
    multi_layer_network
        A multiplex social network.

    Examples
    --------
    >>> from py3plex.datasets import make_social_network
    >>> net = make_social_network(n_people=25)
    >>> print(net.get_layers())  # ['friendship', 'work', 'family']
    """
    if n_people <= 0:
        raise ValueError("n_people must be positive")

    if random_state is not None:
        np.random.seed(random_state)

    G = nx.MultiGraph()

    layer_names = ["friendship", "work", "family"]
    layer_map = {name: idx for idx, name in enumerate(layer_names)}

    # In a multiplex network, every person exists in every layer (even if isolated).
    for person in range(n_people):
        for layer_idx in layer_map.values():
            G.add_node((person, layer_idx), type="default")

    # Friendship layer: Power-law degree distribution (social network)
    friendship_graph = nx.barabasi_albert_graph(n_people, m=2, seed=random_state)
    for u, v in friendship_graph.edges():
        G.add_edge(
            (u, layer_map["friendship"]),
            (v, layer_map["friendship"]),
            type="friendship",
            weight=1
        )

    # Work layer: Random clusters (departments)
    n_departments = max(2, n_people // 10)
    department_assignments = np.random.randint(0, n_departments, n_people)
    for i in range(n_people):
        for j in range(i + 1, n_people):
            if department_assignments[i] == department_assignments[j]:
                if np.random.random() < 0.3:  # Not everyone knows everyone
                    G.add_edge(
                        (i, layer_map["work"]),
                        (j, layer_map["work"]),
                        type="work",
                        weight=1
                    )

    # Family layer: Small cliques (families)
    family_size = 4
    n_families = n_people // family_size
    shuffled_nodes = np.random.permutation(n_people)
    for fam_idx in range(n_families):
        start = fam_idx * family_size
        end = start + family_size
        family_members = shuffled_nodes[start:end]
        for i in range(len(family_members)):
            for j in range(i + 1, len(family_members)):
                G.add_edge(
                    (int(family_members[i]), layer_map["family"]),
                    (int(family_members[j]), layer_map["family"]),
                    type="family",
                    weight=1
                )

    return multi_layer_network(network_type="multiplex").load_network(
        G, input_type="nx", directed=False
    )
