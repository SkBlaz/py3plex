"""
Metamorphic transformations for multilayer networks.

These transformations preserve specific properties while changing the network
representation. They are used to verify invariants in metamorphic testing.

All transformations are deterministic and seedable.
"""

import random
import networkx as nx
from typing import Dict, Any, List, Optional
from py3plex.core.multinet import multi_layer_network


def relabel_nodes(net: multi_layer_network, mapping: Dict[Any, Any]) -> multi_layer_network:
    """
    Relabel nodes in a multilayer network while preserving topology.
    
    This transformation is bijective and preserves:
    - Network structure (all edges)
    - Layer structure
    - Degree distribution
    - All topology-based metrics
    
    Args:
        net: Original multilayer network
        mapping: Dictionary mapping old node IDs to new node IDs
        
    Returns:
        New multilayer network with relabeled nodes
        
    Example:
        >>> net = tiny_two_layer()
        >>> mapping = {'A': 'node_0', 'B': 'node_1', 'C': 'node_2', 'D': 'node_3'}
        >>> relabeled = relabel_nodes(net, mapping)
    """
    # Create new network with same properties
    if net.directed:
        new_core = nx.MultiDiGraph()
    else:
        new_core = nx.MultiGraph()
    
    # Relabel nodes: (node, layer) -> (mapping[node], layer)
    for node, layer in net.get_nodes():
        new_node = mapping.get(node, node)
        new_core.add_node((new_node, layer), type="default")
    
    # Relabel edges
    for edge in net.core_network.edges(data=True, keys=True):
        u, v = edge[0], edge[1]
        u_node, u_layer = u
        v_node, v_layer = v
        
        new_u = (mapping.get(u_node, u_node), u_layer)
        new_v = (mapping.get(v_node, v_node), v_layer)
        
        # Preserve edge attributes
        edge_data = edge[3] if len(edge) > 3 else {}
        new_core.add_edge(new_u, new_v, **edge_data)
    
    # Create new network object
    new_net = multi_layer_network(
        network_type=net.network_type,
        directed=net.directed
    )
    new_net.load_network(new_core, input_type="nx", directed=net.directed)
    
    return new_net


def permute_layers(net: multi_layer_network, perm: Dict[int, int]) -> multi_layer_network:
    """
    Permute layer IDs in a multilayer network while preserving topology.
    
    This transformation preserves:
    - Network structure within and across layers
    - Intralayer and interlayer connectivity patterns
    - Degree distribution
    - All layer-agnostic metrics
    
    Args:
        net: Original multilayer network
        perm: Dictionary mapping old layer IDs to new layer IDs
        
    Returns:
        New multilayer network with permuted layer IDs
        
    Example:
        >>> net = small_three_layer()
        >>> perm = {0: 2, 1: 0, 2: 1}  # Rotate layers
        >>> permuted = permute_layers(net, perm)
    """
    # Create new network with same properties
    if net.directed:
        new_core = nx.MultiDiGraph()
    else:
        new_core = nx.MultiGraph()
    
    # Permute nodes: (node, layer) -> (node, perm[layer])
    for node, layer in net.get_nodes():
        new_layer = perm.get(layer, layer)
        new_core.add_node((node, new_layer), type="default")
    
    # Permute edges
    for edge in net.core_network.edges(data=True, keys=True):
        u, v = edge[0], edge[1]
        u_node, u_layer = u
        v_node, v_layer = v
        
        new_u = (u_node, perm.get(u_layer, u_layer))
        new_v = (v_node, perm.get(v_layer, v_layer))
        
        # Preserve edge attributes
        edge_data = edge[3] if len(edge) > 3 else {}
        new_core.add_edge(new_u, new_v, **edge_data)
    
    # Create new network object
    new_net = multi_layer_network(
        network_type=net.network_type,
        directed=net.directed
    )
    new_net.load_network(new_core, input_type="nx", directed=net.directed)
    
    return new_net


def shuffle_edge_order(net: multi_layer_network, seed: Optional[int] = None) -> multi_layer_network:
    """
    Shuffle the order of edges in the network representation.
    
    This transformation preserves:
    - All edges (same set of edges)
    - Network structure
    - All graph properties
    
    The only change is the internal ordering of edges in the data structure.
    This tests that algorithms are invariant to edge insertion order.
    
    Args:
        net: Original multilayer network
        seed: Random seed for reproducibility
        
    Returns:
        New multilayer network with shuffled edge order
    """
    if seed is not None:
        random.seed(seed)
    
    # Create new network
    if net.directed:
        new_core = nx.MultiDiGraph()
    else:
        new_core = nx.MultiGraph()
    
    # Copy nodes (order doesn't matter as much)
    for node in net.core_network.nodes(data=True):
        new_core.add_node(node[0], **node[1])
    
    # Collect and shuffle edges
    edges = list(net.core_network.edges(data=True, keys=True))
    random.shuffle(edges)
    
    # Add shuffled edges
    for edge in edges:
        u, v = edge[0], edge[1]
        edge_data = edge[3] if len(edge) > 3 else {}
        new_core.add_edge(u, v, **edge_data)
    
    # Create new network object
    new_net = multi_layer_network(
        network_type=net.network_type,
        directed=net.directed
    )
    new_net.load_network(new_core, input_type="nx", directed=net.directed)
    
    return new_net


def scale_weights(
    net: multi_layer_network,
    factor: float,
    weight_attr: str = 'weight'
) -> multi_layer_network:
    """
    Scale all edge weights by a positive factor.
    
    This transformation preserves:
    - Network topology
    - Relative ordering of weights
    - Shortest path routes (for positive weights)
    
    Args:
        net: Original multilayer network
        factor: Positive scaling factor
        weight_attr: Name of weight attribute (default: 'weight')
        
    Returns:
        New multilayer network with scaled weights
    """
    if factor <= 0:
        raise ValueError("Scaling factor must be positive")
    
    # Create new network
    if net.directed:
        new_core = nx.MultiDiGraph()
    else:
        new_core = nx.MultiGraph()
    
    # Copy nodes
    for node in net.core_network.nodes(data=True):
        new_core.add_node(node[0], **node[1])
    
    # Copy and scale edges
    for edge in net.core_network.edges(data=True, keys=True):
        u, v = edge[0], edge[1]
        edge_data = dict(edge[3]) if len(edge) > 3 else {}
        
        # Scale weight if present
        if weight_attr in edge_data:
            edge_data[weight_attr] = edge_data[weight_attr] * factor
        
        new_core.add_edge(u, v, **edge_data)
    
    # Create new network object
    new_net = multi_layer_network(
        network_type=net.network_type,
        directed=net.directed
    )
    new_net.load_network(new_core, input_type="nx", directed=net.directed)
    
    return new_net


def add_isolated_nodes(
    net: multi_layer_network,
    nodes: List[Any],
    layer: int = 0
) -> multi_layer_network:
    """
    Add isolated nodes (no edges) to a network.
    
    This transformation preserves:
    - All existing edges
    - All existing nodes
    - Connected component structure of original graph
    
    Args:
        net: Original multilayer network
        nodes: List of node IDs to add as isolated nodes
        layer: Layer to add nodes to (default: 0)
        
    Returns:
        New multilayer network with additional isolated nodes
    """
    # Create new network
    if net.directed:
        new_core = nx.MultiDiGraph(net.core_network)
    else:
        new_core = nx.MultiGraph(net.core_network)
    
    # Add isolated nodes
    for node in nodes:
        new_core.add_node((node, layer), type="default")
    
    # Create new network object
    new_net = multi_layer_network(
        network_type=net.network_type,
        directed=net.directed
    )
    new_net.load_network(new_core, input_type="nx", directed=net.directed)
    
    return new_net


def perturb_edges(
    net: multi_layer_network,
    drop_prob: float = 0.1,
    seed: Optional[int] = None
) -> multi_layer_network:
    """
    Randomly drop edges with a given probability.
    
    This is a stochastic perturbation that should be used with a fixed seed
    for reproducibility. Useful for testing stability envelopes.
    
    Args:
        net: Original multilayer network
        drop_prob: Probability of dropping each edge (default: 0.1)
        seed: Random seed for reproducibility (required for determinism)
        
    Returns:
        New multilayer network with some edges dropped
    """
    if seed is not None:
        random.seed(seed)
    
    # Create new network
    if net.directed:
        new_core = nx.MultiDiGraph()
    else:
        new_core = nx.MultiGraph()
    
    # Copy nodes
    for node in net.core_network.nodes(data=True):
        new_core.add_node(node[0], **node[1])
    
    # Copy edges with dropout
    for edge in net.core_network.edges(data=True, keys=True):
        # Drop edge with probability drop_prob
        if random.random() > drop_prob:
            u, v = edge[0], edge[1]
            edge_data = edge[3] if len(edge) > 3 else {}
            new_core.add_edge(u, v, **edge_data)
    
    # Create new network object
    new_net = multi_layer_network(
        network_type=net.network_type,
        directed=net.directed
    )
    new_net.load_network(new_core, input_type="nx", directed=net.directed)
    
    return new_net
