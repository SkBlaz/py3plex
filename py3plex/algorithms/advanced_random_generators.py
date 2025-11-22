"""
Advanced random graph generators for multilayer networks.

Implements multilayer variants of:
- Erdős-Rényi (ER) models
- Barabási-Albert (BA) preferential attachment
- Stochastic Block Models (SBM)
- Multilayer SBM with inter-layer dependencies

Authors: py3plex contributors
Date: 2025
"""

from typing import Any, List, Optional
import numpy as np
import networkx as nx


def multilayer_barabasi_albert(
    n: int,
    m: int,
    num_layers: int,
    interlayer_prob: float = 0.1,
    directed: bool = False,
    seed: Optional[int] = None
) -> Any:
    """Generate multilayer Barabási-Albert preferential attachment network.
    
    Creates a scale-free network in each layer with preferential attachment,
    plus random inter-layer connections.
    
    Args:
        n: Number of nodes per layer
        m: Number of edges to attach from new node (m < n)
        num_layers: Number of layers
        interlayer_prob: Probability of inter-layer edges
        directed: Whether to create directed networks
        seed: Random seed for reproducibility
        
    Returns:
        NetworkX MultiGraph or MultiDiGraph with multilayer structure
        
    Algorithm:
        For each layer:
        1. Generate BA network with preferential attachment
        2. Add inter-layer edges between corresponding nodes
        
    References:
        - Barabási, A. L., & Albert, R. (1999). "Emergence of scaling in
          random networks." Science, 286(5439), 509-512.
        - Gómez, S., et al. (2013). "Diffusion dynamics on multiplex networks."
          Physical Review Letters, 110(2), 028701.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()
    
    # Generate BA network for each layer
    for layer in range(num_layers):
        layer_graph = nx.barabasi_albert_graph(n, m, seed=seed)
        
        # Add nodes with layer information
        for node in layer_graph.nodes():
            G.add_node((node, layer), layer=layer)
        
        # Add edges within layer
        for u, v in layer_graph.edges():
            G.add_edge((u, layer), (v, layer), layer=layer, edge_type='intra')
    
    # Add inter-layer edges
    if interlayer_prob > 0:
        for node in range(n):
            for l1 in range(num_layers):
                for l2 in range(l1 + 1, num_layers):
                    if np.random.random() < interlayer_prob:
                        G.add_edge(
                            (node, l1), (node, l2),
                            edge_type='inter',
                            layers=(l1, l2)
                        )
    
    return G


def multilayer_stochastic_block_model(
    block_sizes: List[int],
    block_probs: np.ndarray,
    num_layers: int,
    interlayer_prob: float = 0.1,
    directed: bool = False,
    seed: Optional[int] = None
) -> Any:
    """Generate multilayer stochastic block model network.
    
    Creates networks with community structure in each layer, where edges
    within and between blocks follow specified probabilities.
    
    Args:
        block_sizes: List of block sizes (number of nodes in each block)
        block_probs: Matrix of edge probabilities between blocks (k x k)
        num_layers: Number of layers
        interlayer_prob: Probability of inter-layer edges
        directed: Whether to create directed networks
        seed: Random seed for reproducibility
        
    Returns:
        NetworkX MultiGraph or MultiDiGraph with block structure
        
    Example:
        >>> # Two blocks with strong within-block, weak between-block connections
        >>> sizes = [50, 50]
        >>> probs = np.array([[0.8, 0.1], [0.1, 0.8]])
        >>> G = multilayer_stochastic_block_model(sizes, probs, num_layers=3)
        
    References:
        - Holland, P. W., et al. (1983). "Stochastic blockmodels."
          Social Networks, 5(2), 109-137.
        - Bazzi, M., et al. (2016). "Community detection in temporal multilayer
          networks." SIAM Journal on Applied Mathematics, 76(2), 504-537.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()
    
    # Generate SBM for each layer
    for layer in range(num_layers):
        layer_graph = nx.stochastic_block_model(
            block_sizes, block_probs, directed=directed, seed=seed
        )
        
        # Add nodes with layer information
        for node, data in layer_graph.nodes(data=True):
            G.add_node((node, layer), layer=layer, block=data.get('block', 0))
        
        # Add edges within layer
        for u, v in layer_graph.edges():
            G.add_edge((u, layer), (v, layer), layer=layer, edge_type='intra')
    
    # Add inter-layer edges (between corresponding nodes)
    if interlayer_prob > 0:
        total_nodes = sum(block_sizes)
        for node in range(total_nodes):
            for l1 in range(num_layers):
                for l2 in range(l1 + 1, num_layers):
                    if np.random.random() < interlayer_prob:
                        G.add_edge(
                            (node, l1), (node, l2),
                            edge_type='inter',
                            layers=(l1, l2)
                        )
    
    return G


def multilayer_sbm_with_dependencies(
    block_sizes: List[int],
    intralayer_probs: List[np.ndarray],
    interlayer_probs: np.ndarray,
    directed: bool = False,
    seed: Optional[int] = None
) -> Any:
    """Generate multilayer SBM with layer-dependent block probabilities.
    
    Each layer can have different within/between block connection probabilities,
    and inter-layer connections depend on block membership.
    
    Args:
        block_sizes: List of block sizes
        intralayer_probs: List of probability matrices, one per layer
        interlayer_probs: 3D array of inter-layer edge probabilities [layer1, layer2, block]
        directed: Whether to create directed networks
        seed: Random seed for reproducibility
        
    Returns:
        NetworkX MultiGraph or MultiDiGraph with dependent block structure
        
    Example:
        >>> sizes = [30, 30]
        >>> # Different connectivity patterns in each layer
        >>> layer1_probs = np.array([[0.9, 0.1], [0.1, 0.9]])
        >>> layer2_probs = np.array([[0.5, 0.5], [0.5, 0.5]])
        >>> intralayer = [layer1_probs, layer2_probs]
        >>> # Inter-layer connections depend on blocks
        >>> interlayer = np.zeros((2, 2, 2))
        >>> interlayer[0, 1, 0] = 0.8  # Block 0: strong coupling
        >>> interlayer[0, 1, 1] = 0.2  # Block 1: weak coupling
        >>> G = multilayer_sbm_with_dependencies(sizes, intralayer, interlayer)
        
    References:
        - Peixoto, T. P. (2015). "Inferring the mesoscale structure of layered,
          edge-valued, and time-varying networks." Physical Review E, 92(4), 042807.
    """
    if seed is not None:
        np.random.seed(seed)
    
    num_layers = len(intralayer_probs)
    total_nodes = sum(block_sizes)
    
    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()
    
    # Assign nodes to blocks (same across layers)
    node_blocks = []
    current_node = 0
    for block_id, block_size in enumerate(block_sizes):
        node_blocks.extend([block_id] * block_size)
    
    # Generate each layer with its own block probabilities
    for layer in range(num_layers):
        layer_probs = intralayer_probs[layer]
        
        # Add nodes
        for node in range(total_nodes):
            G.add_node((node, layer), layer=layer, block=node_blocks[node])
        
        # Add intra-layer edges based on block membership
        for u in range(total_nodes):
            for v in range(u + 1, total_nodes):
                block_u = node_blocks[u]
                block_v = node_blocks[v]
                prob = layer_probs[block_u, block_v]
                
                if np.random.random() < prob:
                    G.add_edge((u, layer), (v, layer), layer=layer, edge_type='intra')
    
    # Add inter-layer edges based on block-dependent probabilities
    for l1 in range(num_layers):
        for l2 in range(l1 + 1, num_layers):
            for node in range(total_nodes):
                block = node_blocks[node]
                prob = interlayer_probs[l1, l2, block]
                
                if np.random.random() < prob:
                    G.add_edge(
                        (node, l1), (node, l2),
                        edge_type='inter',
                        layers=(l1, l2)
                    )
    
    return G


def multilayer_erdos_renyi(
    n: int,
    p: float,
    num_layers: int,
    interlayer_prob: float = 0.1,
    directed: bool = False,
    seed: Optional[int] = None
) -> Any:
    """Generate multilayer Erdős-Rényi random network.
    
    Creates independent ER graphs in each layer with inter-layer connections.
    
    Args:
        n: Number of nodes per layer
        p: Intra-layer edge probability
        num_layers: Number of layers
        interlayer_prob: Probability of inter-layer edges
        directed: Whether to create directed networks
        seed: Random seed for reproducibility
        
    Returns:
        NetworkX MultiGraph or MultiDiGraph
        
    References:
        - Erdős, P., & Rényi, A. (1960). "On the evolution of random graphs."
          Publication of the Mathematical Institute of the Hungarian Academy
          of Sciences, 5(1), 17-60.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()
    
    # Generate ER network for each layer
    for layer in range(num_layers):
        layer_graph = nx.erdos_renyi_graph(n, p, seed=seed, directed=directed)
        
        # Add nodes with layer information
        for node in layer_graph.nodes():
            G.add_node((node, layer), layer=layer)
        
        # Add edges within layer
        for u, v in layer_graph.edges():
            G.add_edge((u, layer), (v, layer), layer=layer, edge_type='intra')
    
    # Add inter-layer edges
    if interlayer_prob > 0:
        for node in range(n):
            for l1 in range(num_layers):
                for l2 in range(l1 + 1, num_layers):
                    if np.random.random() < interlayer_prob:
                        G.add_edge(
                            (node, l1), (node, l2),
                            edge_type='inter',
                            layers=(l1, l2)
                        )
    
    return G


def multilayer_configuration_model(
    degree_sequences: List[List[int]],
    interlayer_edges: int = 0,
    directed: bool = False,
    seed: Optional[int] = None
) -> Any:
    """Generate multilayer network with specified degree sequences.
    
    Creates networks where each layer has a specific degree distribution.
    
    Args:
        degree_sequences: List of degree sequences, one per layer
        interlayer_edges: Number of random inter-layer edges to add
        directed: Whether to create directed networks
        seed: Random seed for reproducibility
        
    Returns:
        NetworkX MultiGraph or MultiDiGraph
        
    References:
        - Newman, M. E. (2003). "The structure and function of complex networks."
          SIAM Review, 45(2), 167-256.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if directed:
        G = nx.MultiDiGraph()
    else:
        G = nx.MultiGraph()
    
    num_layers = len(degree_sequences)
    
    # Generate configuration model for each layer
    for layer, degree_seq in enumerate(degree_sequences):
        try:
            if directed:
                # For directed, need in-degree and out-degree sequences
                # Here we use the same sequence for both
                layer_graph = nx.directed_configuration_model(
                    degree_seq, degree_seq, seed=seed
                )
            else:
                layer_graph = nx.configuration_model(degree_seq, seed=seed)
            
            # Remove self-loops and parallel edges
            layer_graph = nx.Graph(layer_graph)
            
            # Add nodes with layer information
            for node in layer_graph.nodes():
                G.add_node((node, layer), layer=layer)
            
            # Add edges within layer
            for u, v in layer_graph.edges():
                G.add_edge((u, layer), (v, layer), layer=layer, edge_type='intra')
        
        except nx.NetworkXError:
            # If degree sequence is not graphical, skip this layer
            pass
    
    # Add random inter-layer edges
    if interlayer_edges > 0:
        # Get all nodes
        all_nodes = list(G.nodes())
        nodes_per_layer = {}
        for node, layer in all_nodes:
            if layer not in nodes_per_layer:
                nodes_per_layer[layer] = []
            nodes_per_layer[layer].append(node)
        
        # Add random inter-layer edges
        edges_added = 0
        max_attempts = interlayer_edges * 10
        attempts = 0
        
        while edges_added < interlayer_edges and attempts < max_attempts:
            attempts += 1
            
            # Pick two random layers
            l1, l2 = np.random.choice(num_layers, size=2, replace=False)
            
            # Pick random nodes from each layer
            if l1 in nodes_per_layer and l2 in nodes_per_layer:
                node1 = np.random.choice(nodes_per_layer[l1])
                node2 = np.random.choice(nodes_per_layer[l2])
                
                # Add edge if it doesn't exist
                if not G.has_edge((node1, l1), (node2, l2)):
                    G.add_edge(
                        (node1, l1), (node2, l2),
                        edge_type='inter',
                        layers=(l1, l2)
                    )
                    edges_added += 1
    
    return G
