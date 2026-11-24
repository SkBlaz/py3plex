"""Null model algorithms for multilayer networks.

This module provides various null model generation algorithms for
randomizing multilayer networks while preserving specific properties.
"""

from typing import Any, Callable, Dict, List, Optional
import random
import networkx as nx

from py3plex.core import multinet
from py3plex.exceptions import AlgorithmError


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
    """Copy the graph and network representation without sharing mutable edges."""
    if not hasattr(network, "core_network"):
        return network.copy()
    sample = multinet.multi_layer_network(
        network_type=network.network_type, directed=network.directed,
        coupling_weight=network.coupling_weight, verbose=network.verbose,
    )
    if network.core_network is not None:
        sample.core_network = network.core_network.copy()
    return sample


def _with_graph(network, graph):
    sample = multinet.multi_layer_network(
        network_type=getattr(network, "network_type", "multilayer"),
        directed=graph.is_directed(),
        coupling_weight=getattr(network, "coupling_weight", 1),
        verbose=getattr(network, "verbose", True),
    )
    sample.core_network = graph
    return sample


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
    graph = network.core_network if hasattr(network, "core_network") else network
    if graph is None or not graph:
        return _copy_network(network)

    nodes = list(graph)
    if graph.is_directed():
        sampled = nx.directed_configuration_model(
            [graph.in_degree(node) for node in nodes],
            [graph.out_degree(node) for node in nodes], seed=seed,
        )
    else:
        sampled = nx.configuration_model([graph.degree(node) for node in nodes], seed=seed)
    sampled = nx.relabel_nodes(sampled, dict(enumerate(nodes)))
    sampled.add_nodes_from(graph.nodes(data=True))
    return _with_graph(network, sampled)


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
    graph = network.core_network if hasattr(network, "core_network") else network
    if graph is None or not graph:
        return _copy_network(network)
    directed = graph.is_directed()
    nodes = list(graph)
    n = len(nodes)
    capacity = n * (n - 1) / (1 if directed else 2)
    unique = nx.DiGraph(graph) if directed else nx.Graph(graph)
    unique.remove_edges_from(nx.selfloop_edges(unique))
    probability = unique.number_of_edges() / capacity if capacity else 0
    sample = nx.gnp_random_graph(n, probability, seed=seed, directed=directed)
    sample = nx.relabel_nodes(sample, dict(enumerate(nodes)))
    if graph.is_multigraph():
        sample = nx.MultiDiGraph(sample) if directed else nx.MultiGraph(sample)
    sample.add_nodes_from(graph.nodes(data=True))
    return _with_graph(network, sample)


@model_registry.register("layer_shuffle",
                         description="Shuffle layer assignments while preserving structure")
def layer_shuffle_model(
    network: Any,
    seed: Optional[int] = None,
    **kwargs,
) -> Any:
    """Generate a randomized network by shuffling layer assignments.
    
    Preserves edge incidence, layer sizes, and each physical node's replica count.
    A seeded swap chain changes individual replica assignments.
    
    Args:
        network: Multilayer network to randomize
        seed: Optional random seed
        **kwargs: Additional parameters
        
    Returns:
        Randomized network
    """
    graph = network.core_network if hasattr(network, "core_network") else network
    if graph is None or len(graph) < 2:
        return _copy_network(network)
    if any(not isinstance(node, tuple) or len(node) != 2 for node in graph):
        raise ValueError("Layer shuffling requires (node, layer) replicas.")

    nodes = list(graph)
    occupied = set(nodes)
    assignment = nodes.copy()
    rng = random.Random(seed)
    for _ in range(10 * len(nodes)):
        i, j = rng.sample(range(len(nodes)), 2)
        a, layer_a = assignment[i]
        b, layer_b = assignment[j]
        first, second = (a, layer_b), (b, layer_a)
        old = {assignment[i], assignment[j]}
        if first == second or ({first, second} - old) & occupied:
            continue
        occupied.difference_update(old)
        occupied.update((first, second))
        assignment[i], assignment[j] = first, second

    sampled = nx.relabel_nodes(graph, dict(zip(nodes, assignment)), copy=True)
    return _with_graph(network, sampled)


def _swap_directed_edges(graph, num_swaps, seed, preserve_coupling):
    """Swap the targets of two arcs, preserving both directed degree sequences."""
    is_multi = graph.is_multigraph()
    records = (
        graph.edges(keys=True, data=True) if is_multi
        else ((u, v, None, data) for u, v, data in graph.edges(data=True))
    )
    arcs = [(u, v, key) for u, v, key, data in records
            if not (preserve_coupling and data.get("type") == "coupling")]
    rng = random.Random(seed)
    completed = 0
    if num_swaps < 0:
        raise ValueError("num_swaps must be non-negative")
    for _ in range(num_swaps * 10):
        if completed == num_swaps or len(arcs) < 2:
            break
        first, second = rng.sample(range(len(arcs)), 2)
        u, v, key1 = arcs[first]
        x, y, key2 = arcs[second]
        if u == x or v == y or u == y or x == v:
            continue
        if graph.has_edge(u, y) or graph.has_edge(x, v):
            continue

        if is_multi:
            data1 = graph.edges[u, v, key1]
            data2 = graph.edges[x, y, key2]
            graph.remove_edge(u, v, key1)
            graph.remove_edge(x, y, key2)
            graph.add_edge(u, y, key=key1)
            graph.add_edge(x, v, key=key2)
            graph.edges[u, y, key1].update(data1)
            graph.edges[x, v, key2].update(data2)
        else:
            data1 = graph.edges[u, v]
            data2 = graph.edges[x, y]
            graph.remove_edge(u, v)
            graph.remove_edge(x, y)
            graph.add_edge(u, y)
            graph.add_edge(x, v)
            graph.edges[u, y].update(data1)
            graph.edges[x, v].update(data2)
        arcs[first] = (u, y, key1)
        arcs[second] = (x, v, key2)
        completed += 1

    if completed != num_swaps:
        raise AlgorithmError(
            f"Directed edge swap completed {completed} of {num_swaps} requested swaps."
        )


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
    G = network.core_network if hasattr(network, 'core_network') else network
    
    if G is None or len(G.nodes()) == 0:
        return _copy_network(network)
    
    # Create a copy of the graph for swapping
    random_G = G.copy()
    
    # Calculate number of swaps
    m = len(random_G.edges())
    if num_swaps is None:
        num_swaps = 10 * m
    
    if random_G.is_directed():
        network_type = getattr(network, "network_type", "multilayer")
        _swap_directed_edges(random_G, num_swaps, seed, network_type == "multiplex")
        sample = multinet.multi_layer_network(
            network_type=network_type,
            directed=True,
            coupling_weight=getattr(network, "coupling_weight", 1),
        )
        sample.core_network = random_G
        return sample

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
