"""Path algorithms for multilayer networks.

This module provides various path finding and flow algorithms for
multilayer networks.
"""

from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import random
from collections import defaultdict
import networkx as nx


class PathRegistry:
    """Registry for path algorithms.
    
    Allows registration of path finding functions and retrieval by name.
    """
    
    def __init__(self):
        self._algorithms: Dict[str, Callable] = {}
        self._descriptions: Dict[str, str] = {}
    
    def register(self, name: str, description: Optional[str] = None):
        """Decorator to register an algorithm function.
        
        Args:
            name: Name of the algorithm
            description: Optional description
            
        Returns:
            Decorator function
        """
        def decorator(fn: Callable) -> Callable:
            self._algorithms[name] = fn
            if description:
                self._descriptions[name] = description
            return fn
        return decorator
    
    def get(self, name: str) -> Callable:
        """Get an algorithm function by name.
        
        Args:
            name: Algorithm name
            
        Returns:
            The algorithm function
            
        Raises:
            ValueError: If algorithm is not found
        """
        if name not in self._algorithms:
            known = ", ".join(sorted(self._algorithms.keys()))
            raise ValueError(f"Unknown path algorithm '{name}'. Known: {known}")
        return self._algorithms[name]
    
    def has(self, name: str) -> bool:
        """Check if an algorithm is registered."""
        return name in self._algorithms
    
    def list_algorithms(self) -> List[str]:
        """List all registered algorithm names."""
        return list(self._algorithms.keys())


# Global path registry
path_registry = PathRegistry()


def _find_node_by_name(G: nx.Graph, name: str) -> Optional[Any]:
    """Find a node in the graph by its base name.
    
    Nodes are tuples (base_name, layer), so we search for matching base names.
    
    Args:
        G: NetworkX graph
        name: Node base name to search for
        
    Returns:
        First matching node tuple, or None if not found
    """
    for node in G.nodes():
        if isinstance(node, tuple) and len(node) >= 2:
            if str(node[0]) == str(name):
                return node
        elif str(node) == str(name):
            return node
    return None


def _find_all_nodes_by_name(G: nx.Graph, name: str) -> List[Any]:
    """Find all nodes in the graph with a given base name.
    
    Args:
        G: NetworkX graph
        name: Node base name to search for
        
    Returns:
        List of matching node tuples
    """
    matches = []
    for node in G.nodes():
        if isinstance(node, tuple) and len(node) >= 2:
            if str(node[0]) == str(name):
                matches.append(node)
        elif str(node) == str(name):
            matches.append(node)
    return matches


@path_registry.register("shortest",
                        description="Find shortest path between two nodes")
def shortest_path(
    network: Any,
    source: Any,
    target: Any,
    layers: Optional[List[str]] = None,
    cross_layer: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """Find shortest path between two nodes in a multilayer network.
    
    Args:
        network: Multilayer network
        source: Source node (name or tuple)
        target: Target node (name or tuple)
        layers: Optional list of layers to consider
        cross_layer: Whether to allow cross-layer paths
        **kwargs: Additional parameters
        
    Returns:
        Dictionary with paths and metadata
    """
    G = network.core_network if hasattr(network, 'core_network') else network
    
    if G is None or len(G.nodes()) == 0:
        return {"paths": [], "error": "Empty network"}
    
    # Find source and target nodes
    source_nodes = _find_all_nodes_by_name(G, source)
    target_nodes = _find_all_nodes_by_name(G, target)
    
    if not source_nodes:
        return {"paths": [], "error": f"Source node '{source}' not found"}
    if not target_nodes:
        return {"paths": [], "error": f"Target node '{target}' not found"}
    
    # Filter by layers if specified
    if layers:
        source_nodes = [n for n in source_nodes if isinstance(n, tuple) and n[1] in layers]
        target_nodes = [n for n in target_nodes if isinstance(n, tuple) and n[1] in layers]
    
    # Find shortest paths from all source nodes to all target nodes
    paths = []
    for src in source_nodes:
        for tgt in target_nodes:
            if src == tgt:
                continue
            try:
                path = nx.shortest_path(G, src, tgt)
                paths.append(path)
            except nx.NetworkXNoPath:
                continue
    
    # Sort by length and return shortest
    if paths:
        paths.sort(key=len)
        return {"paths": [paths[0]], "all_paths": paths}
    
    return {"paths": []}


@path_registry.register("all",
                        description="Find all simple paths between two nodes")
def all_paths(
    network: Any,
    source: Any,
    target: Any,
    layers: Optional[List[str]] = None,
    cross_layer: bool = False,
    max_length: Optional[int] = None,
    limit: Optional[int] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Find all simple paths between two nodes.
    
    Args:
        network: Multilayer network
        source: Source node
        target: Target node
        layers: Optional list of layers to consider
        cross_layer: Whether to allow cross-layer paths
        max_length: Maximum path length
        limit: Maximum number of paths to return
        **kwargs: Additional parameters
        
    Returns:
        Dictionary with paths
    """
    G = network.core_network if hasattr(network, 'core_network') else network
    
    if G is None or len(G.nodes()) == 0:
        return {"paths": []}
    
    # Find source and target nodes
    source_nodes = _find_all_nodes_by_name(G, source)
    target_nodes = _find_all_nodes_by_name(G, target)
    
    if not source_nodes or not target_nodes:
        return {"paths": []}
    
    # Filter by layers if specified
    if layers:
        source_nodes = [n for n in source_nodes if isinstance(n, tuple) and n[1] in layers]
        target_nodes = [n for n in target_nodes if isinstance(n, tuple) and n[1] in layers]
    
    # Set default max length if not specified
    if max_length is None:
        max_length = len(G.nodes())
    
    # Find all paths
    paths = []
    count = 0
    
    for src in source_nodes:
        for tgt in target_nodes:
            if src == tgt:
                continue
            try:
                for path in nx.all_simple_paths(G, src, tgt, cutoff=max_length):
                    paths.append(path)
                    count += 1
                    if limit and count >= limit:
                        return {"paths": paths}
            except nx.NetworkXError:
                continue
    
    return {"paths": paths}


@path_registry.register("random_walk",
                        description="Perform random walk and compute node visit frequencies")
def random_walk(
    network: Any,
    source: Any,
    steps: int = 100,
    teleport: float = 0.0,
    layers: Optional[List[str]] = None,
    cross_layer: bool = True,
    seed: Optional[int] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Perform a random walk on the multilayer network.
    
    Args:
        network: Multilayer network
        source: Starting node
        steps: Number of steps to walk
        teleport: Teleportation probability (restart at source)
        layers: Optional list of layers to consider
        cross_layer: Whether to allow cross-layer transitions
        seed: Optional random seed
        **kwargs: Additional parameters
        
    Returns:
        Dictionary with visit_frequency and walk path
    """
    if seed is not None:
        random.seed(seed)
    
    G = network.core_network if hasattr(network, 'core_network') else network
    
    if G is None or len(G.nodes()) == 0:
        return {"visit_frequency": {}, "paths": []}
    
    # Find source node
    source_nodes = _find_all_nodes_by_name(G, source)
    if not source_nodes:
        return {"visit_frequency": {}, "error": f"Source '{source}' not found"}
    
    if layers:
        source_nodes = [n for n in source_nodes if isinstance(n, tuple) and n[1] in layers]
    
    if not source_nodes:
        return {"visit_frequency": {}}
    
    # Start random walk
    current = source_nodes[0]
    visit_count: Dict[Any, int] = defaultdict(int)
    walk_path = [current]
    
    for _ in range(steps):
        visit_count[current] += 1
        
        # Check for teleportation
        if random.random() < teleport:
            current = source_nodes[0]
            walk_path.append(current)
            continue
        
        # Get neighbors
        neighbors = list(G.neighbors(current))
        
        # Filter by layers if not allowing cross-layer
        if not cross_layer and layers:
            neighbors = [
                n for n in neighbors
                if isinstance(n, tuple) and n[1] in layers
            ]
        
        if not neighbors:
            # Restart at source if stuck
            current = source_nodes[0]
        else:
            current = random.choice(neighbors)
        
        walk_path.append(current)
    
    # Compute frequencies
    total_visits = sum(visit_count.values())
    visit_frequency = {
        node: count / total_visits
        for node, count in visit_count.items()
    }
    
    return {
        "visit_frequency": visit_frequency,
        "paths": [walk_path],
    }


@path_registry.register("flow",
                        description="Compute maximum flow between two nodes")
def multilayer_flow(
    network: Any,
    source: Any,
    target: Any,
    layers: Optional[List[str]] = None,
    capacity_attr: str = "weight",
    **kwargs,
) -> Dict[str, Any]:
    """Compute maximum flow between two nodes.
    
    Args:
        network: Multilayer network
        source: Source node
        target: Target node (sink)
        layers: Optional list of layers to consider
        capacity_attr: Edge attribute for capacity (default: "weight")
        **kwargs: Additional parameters
        
    Returns:
        Dictionary with flow_value and flow_values per edge
    """
    G = network.core_network if hasattr(network, 'core_network') else network
    
    if G is None or len(G.nodes()) == 0:
        return {"flow_value": 0, "flow_values": {}}
    
    # Find source and target nodes
    source_nodes = _find_all_nodes_by_name(G, source)
    target_nodes = _find_all_nodes_by_name(G, target)
    
    if not source_nodes or not target_nodes:
        return {"flow_value": 0, "flow_values": {}}
    
    # Filter by layers if specified
    if layers:
        source_nodes = [n for n in source_nodes if isinstance(n, tuple) and n[1] in layers]
        target_nodes = [n for n in target_nodes if isinstance(n, tuple) and n[1] in layers]
    
    if not source_nodes or not target_nodes:
        return {"flow_value": 0, "flow_values": {}}
    
    # Create a directed graph for flow computation
    DG = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        capacity = data.get(capacity_attr, 1.0)
        DG.add_edge(u, v, capacity=capacity)
        DG.add_edge(v, u, capacity=capacity)  # Undirected -> bidirectional
    
    # Find max flow from first source to first target
    src = source_nodes[0]
    tgt = target_nodes[0]
    
    try:
        flow_value, flow_dict = nx.maximum_flow(DG, src, tgt, capacity="capacity")
        
        # Convert flow_dict to edge flow values
        flow_values = {}
        for u, neighbors in flow_dict.items():
            for v, flow in neighbors.items():
                if flow > 0:
                    flow_values[(u, v)] = flow
        
        return {
            "flow_value": flow_value,
            "flow_values": flow_values,
        }
    except nx.NetworkXError:
        return {"flow_value": 0, "flow_values": {}}
