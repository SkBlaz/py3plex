"""Null model algorithms for multilayer networks.

This module provides various null model generation algorithms for
randomizing multilayer networks while preserving specific properties.
"""

from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import random
import networkx as nx

from py3plex.core import multinet


class ModelRegistry:
    """Registry for null model algorithms.
    
    Allows registration of model generation functions and retrieval by name.
    """
    
    def __init__(self):
        self._models: Dict[str, Callable] = {}
        self._descriptions: Dict[str, str] = {}
    
    def register(self, name: str, description: Optional[str] = None):
        """Decorator to register a model function.
        
        Args:
            name: Name of the model
            description: Optional description
            
        Returns:
            Decorator function
        """
        def decorator(fn: Callable) -> Callable:
            self._models[name] = fn
            if description:
                self._descriptions[name] = description
            return fn
        return decorator
    
    def get(self, name: str) -> Callable:
        """Get a model function by name.
        
        Args:
            name: Model name
            
        Returns:
            The model function
            
        Raises:
            ValueError: If model is not found
        """
        if name not in self._models:
            known = ", ".join(sorted(self._models.keys()))
            raise ValueError(f"Unknown null model '{name}'. Known models: {known}")
        return self._models[name]
    
    def has(self, name: str) -> bool:
        """Check if a model is registered."""
        return name in self._models
    
    def list_models(self) -> List[str]:
        """List all registered model names."""
        return list(self._models.keys())


# Global model registry
model_registry = ModelRegistry()


def _copy_network(network: Any) -> Any:
    """Create a copy of a multilayer network.
    
    Args:
        network: Multilayer network to copy
        
    Returns:
        Copy of the network
    """
    if hasattr(network, 'copy'):
        return network.copy()
    
    # Manual copy for py3plex networks
    new_network = multinet.multi_layer_network(
        directed=network.directed if hasattr(network, 'directed') else False
    )
    
    # Check if network has core_network initialized
    if not hasattr(network, 'core_network') or network.core_network is None:
        return new_network
    
    # Copy nodes
    if hasattr(network, 'get_nodes'):
        try:
            nodes = list(network.get_nodes())
            for node in nodes:
                if isinstance(node, tuple) and len(node) >= 2:
                    new_network.add_nodes([{'source': node[0], 'type': node[1]}])
        except (AttributeError, TypeError):
            # Network may not have nodes yet
            pass
    
    # Copy edges
    if hasattr(network, 'core_network') and network.core_network:
        for u, v, data in network.core_network.edges(data=True):
            if isinstance(u, tuple) and isinstance(v, tuple):
                edge = {
                    'source': u[0],
                    'target': v[0],
                    'source_type': u[1],
                    'target_type': v[1],
                }
                if 'weight' in data:
                    edge['weight'] = data['weight']
                new_network.add_edges([edge])
    
    return new_network


@model_registry.register("configuration",
                         description="Configuration model preserving degree sequence")
def configuration_model(
    network: Any,
    preserve_degree: bool = True,
    preserve_layer_sizes: bool = True,
    seed: Optional[int] = None,
    **kwargs,
) -> Any:
    """Generate a randomized network using the configuration model.
    
    Preserves the degree sequence of the original network.
    
    Args:
        network: Multilayer network to randomize
        preserve_degree: Whether to preserve degree sequence (always True for configuration model)
        preserve_layer_sizes: Whether to preserve layer sizes
        seed: Optional random seed
        **kwargs: Additional parameters
        
    Returns:
        Randomized network
    """
    if seed is not None:
        random.seed(seed)
    
    G = network.core_network if hasattr(network, 'core_network') else network
    
    if G is None or len(G.nodes()) == 0:
        return _copy_network(network)
    
    # Get degree sequence
    degree_sequence = [d for n, d in G.degree()]
    
    # Create configuration model graph
    try:
        # Generate a simple graph that preserves the *exact* degree sequence.
        # nx.configuration_model can generate self-loops / parallel edges; converting
        # to a simple Graph would silently change degrees, violating the contract.
        random_G = nx.random_degree_sequence_graph(degree_sequence, seed=seed)
    except Exception:
        # Fallback: return copy of original
        return _copy_network(network)
    
    # Map back to original node labels
    nodes = list(G.nodes())
    mapping = {i: nodes[i] for i in range(len(nodes))}
    random_G = nx.relabel_nodes(random_G, mapping)
    
    # Create new py3plex network
    new_network = multinet.multi_layer_network(
        directed=network.directed if hasattr(network, 'directed') else False
    )
    
    # Add nodes
    for node in nodes:
        if isinstance(node, tuple) and len(node) >= 2:
            new_network.add_nodes([{'source': node[0], 'type': node[1]}])
    
    # Add edges from random graph
    for u, v in random_G.edges():
        if isinstance(u, tuple) and isinstance(v, tuple):
            edge = {
                'source': u[0],
                'target': v[0],
                'source_type': u[1],
                'target_type': v[1],
            }
            new_network.add_edges([edge])
    
    return new_network


@model_registry.register("erdos_renyi",
                         description="Erdős-Rényi random graph model")
def erdos_renyi_model(
    network: Any,
    preserve_density: bool = True,
    seed: Optional[int] = None,
    **kwargs,
) -> Any:
    """Generate a randomized network using the Erdős-Rényi model.
    
    Creates a random graph with the same number of nodes and similar edge density.
    
    Args:
        network: Multilayer network to randomize
        preserve_density: Whether to preserve edge density
        seed: Optional random seed
        **kwargs: Additional parameters
        
    Returns:
        Randomized network
    """
    if seed is not None:
        random.seed(seed)
    
    G = network.core_network if hasattr(network, 'core_network') else network
    
    if G is None or len(G.nodes()) == 0:
        return _copy_network(network)
    
    n = len(G.nodes())
    m = len(G.edges())
    
    # Calculate edge probability
    max_edges = n * (n - 1) / 2
    p = m / max_edges if max_edges > 0 else 0
    
    # Create ER graph
    random_G = nx.gnp_random_graph(n, p, seed=seed)
    
    # Map to original node labels
    nodes = list(G.nodes())
    mapping = {i: nodes[i] for i in range(len(nodes))}
    random_G = nx.relabel_nodes(random_G, mapping)
    
    # Create new py3plex network
    new_network = multinet.multi_layer_network(
        directed=network.directed if hasattr(network, 'directed') else False
    )
    
    # Add nodes
    for node in nodes:
        if isinstance(node, tuple) and len(node) >= 2:
            new_network.add_nodes([{'source': node[0], 'type': node[1]}])
    
    # Add edges from random graph
    for u, v in random_G.edges():
        if isinstance(u, tuple) and isinstance(v, tuple):
            edge = {
                'source': u[0],
                'target': v[0],
                'source_type': u[1],
                'target_type': v[1],
            }
            new_network.add_edges([edge])
    
    return new_network


@model_registry.register("layer_shuffle",
                         description="Shuffle layer assignments while preserving structure")
def layer_shuffle_model(
    network: Any,
    seed: Optional[int] = None,
    **kwargs,
) -> Any:
    """Generate a randomized network by shuffling layer assignments.
    
    Preserves the edge structure but randomly reassigns nodes to layers.
    
    Args:
        network: Multilayer network to randomize
        seed: Optional random seed
        **kwargs: Additional parameters
        
    Returns:
        Randomized network
    """
    if seed is not None:
        random.seed(seed)
    
    G = network.core_network if hasattr(network, 'core_network') else network
    
    if G is None or len(G.nodes()) == 0:
        return _copy_network(network)
    
    # Get all unique layers
    layers = set()
    for node in G.nodes():
        if isinstance(node, tuple) and len(node) >= 2:
            layers.add(node[1])
    
    layers = list(layers)
    
    # Create shuffled layer mapping
    shuffled_layers = layers.copy()
    random.shuffle(shuffled_layers)
    layer_mapping = dict(zip(layers, shuffled_layers))
    
    # Create new py3plex network
    new_network = multinet.multi_layer_network(
        directed=network.directed if hasattr(network, 'directed') else False
    )
    
    # Add nodes with shuffled layers
    for node in G.nodes():
        if isinstance(node, tuple) and len(node) >= 2:
            new_layer = layer_mapping.get(node[1], node[1])
            new_network.add_nodes([{'source': node[0], 'type': new_layer}])
    
    # Add edges with shuffled layers
    for u, v, data in G.edges(data=True):
        if isinstance(u, tuple) and isinstance(v, tuple):
            new_u_layer = layer_mapping.get(u[1], u[1])
            new_v_layer = layer_mapping.get(v[1], v[1])
            edge = {
                'source': u[0],
                'target': v[0],
                'source_type': new_u_layer,
                'target_type': new_v_layer,
            }
            if 'weight' in data:
                edge['weight'] = data['weight']
            new_network.add_edges([edge])
    
    return new_network


@model_registry.register("edge_swap",
                         description="Random edge swapping preserving degrees")
def edge_swap_model(
    network: Any,
    num_swaps: Optional[int] = None,
    seed: Optional[int] = None,
    **kwargs,
) -> Any:
    """Generate a randomized network by randomly swapping edges.
    
    Preserves the degree sequence by swapping edge endpoints.
    
    Args:
        network: Multilayer network to randomize
        num_swaps: Number of edge swaps (default: 10 * number of edges)
        seed: Optional random seed
        **kwargs: Additional parameters
        
    Returns:
        Randomized network
    """
    if seed is not None:
        random.seed(seed)
    
    G = network.core_network if hasattr(network, 'core_network') else network
    
    if G is None or len(G.nodes()) == 0:
        return _copy_network(network)
    
    # Create a copy of the graph for swapping
    random_G = G.copy()
    
    # Calculate number of swaps
    m = len(random_G.edges())
    if num_swaps is None:
        num_swaps = 10 * m
    
    # Perform edge swaps
    try:
        nx.double_edge_swap(random_G, nswap=num_swaps, max_tries=num_swaps * 10, seed=seed)
    except (nx.NetworkXAlgorithmError, nx.NetworkXError):
        # Swapping failed - return copy of original
        pass
    
    # Create new py3plex network
    new_network = multinet.multi_layer_network(
        directed=network.directed if hasattr(network, 'directed') else False
    )
    
    # Add nodes
    for node in random_G.nodes():
        if isinstance(node, tuple) and len(node) >= 2:
            new_network.add_nodes([{'source': node[0], 'type': node[1]}])
    
    # Add edges
    for u, v, data in random_G.edges(data=True):
        if isinstance(u, tuple) and isinstance(v, tuple):
            edge = {
                'source': u[0],
                'target': v[0],
                'source_type': u[1],
                'target_type': v[1],
            }
            if 'weight' in data:
                edge['weight'] = data['weight']
            new_network.add_edges([edge])
    
    return new_network
