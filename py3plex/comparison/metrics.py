"""Comparison metrics for multilayer networks.

This module provides various distance and similarity metrics for comparing
multilayer networks.
"""

from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import networkx as nx


class MetricRegistry:
    """Registry for comparison metrics.
    
    Allows registration of metric computation functions and retrieval by name.
    """
    
    def __init__(self):
        self._metrics: Dict[str, Callable] = {}
        self._descriptions: Dict[str, str] = {}
    
    def register(self, name: str, description: Optional[str] = None):
        """Decorator to register a metric function.
        
        Args:
            name: Name of the metric
            description: Optional description
            
        Returns:
            Decorator function
        """
        def decorator(fn: Callable) -> Callable:
            self._metrics[name] = fn
            if description:
                self._descriptions[name] = description
            return fn
        return decorator
    
    def get(self, name: str) -> Callable:
        """Get a metric function by name.
        
        Args:
            name: Metric name
            
        Returns:
            The metric function
            
        Raises:
            ValueError: If metric is not found
        """
        if name not in self._metrics:
            known = ", ".join(sorted(self._metrics.keys()))
            raise ValueError(f"Unknown metric '{name}'. Known metrics: {known}")
        return self._metrics[name]
    
    def has(self, name: str) -> bool:
        """Check if a metric is registered."""
        return name in self._metrics
    
    def list_metrics(self) -> List[str]:
        """List all registered metric names."""
        return list(self._metrics.keys())


# Global metric registry
metric_registry = MetricRegistry()


def _get_edges_set(graph, directed=False):
    if not directed:
        return {frozenset((u, v)) for u, v in graph.edges()}
    if graph.is_directed():
        return set(graph.edges())
    return {(u, v) for a, b in graph.edges() for u, v in ((a, b), (b, a))}


def _scope_graph(graph, layers):
    if layers is None:
        return graph
    allowed = set(layers)
    return graph.subgraph(
        node for node in graph if isinstance(node, tuple) and len(node) >= 2
        and node[1] in allowed
    )


def _edge_distance(a, b, directed):
    left, right = _get_edges_set(a, directed), _get_edges_set(b, directed)
    union = left | right
    return 1 - len(left & right) / len(union) if union else 0.0


def _get_nodes_by_layer(network: Any, layer: str) -> Set[Any]:
    """Get nodes belonging to a specific layer."""
    nodes = set()
    if hasattr(network, 'get_nodes'):
        try:
            for node in network.get_nodes():
                if isinstance(node, tuple) and len(node) >= 2 and node[1] == layer:
                    nodes.add(node)
        except Exception:
            return set()
    return nodes


def _get_layers(network: Any) -> Set[str]:
    """Get all layer names from a network."""
    layers = set()
    if hasattr(network, 'get_nodes'):
        try:
            for node in network.get_nodes():
                if isinstance(node, tuple) and len(node) >= 2:
                    layers.add(node[1])
        except Exception:
            return set()
    return layers


@metric_registry.register("multiplex_jaccard", 
                          description="Jaccard similarity of edge sets across all layers")
def multiplex_jaccard(
    network_a: Any,
    network_b: Any,
    layers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compute multiplex Jaccard similarity between two networks.
    
    The Jaccard similarity is computed as |intersection| / |union| of edge sets.
    
    Args:
        network_a: First multilayer network
        network_b: Second multilayer network
        layers: Optional list of layers to consider
        
    Returns:
        Dictionary with global_distance, layerwise_distance
    """
    G_a = network_a.core_network if hasattr(network_a, 'core_network') else network_a
    G_b = network_b.core_network if hasattr(network_b, 'core_network') else network_b
    
    # Treat uninitialized py3plex networks (`core_network=None`) as empty graphs.
    if G_a is None:
        G_a = nx.Graph()
    if G_b is None:
        G_b = nx.Graph()
    
    G_a, G_b = _scope_graph(G_a, layers), _scope_graph(G_b, layers)
    directed = G_a.is_directed() or G_b.is_directed()
    all_layers = _get_layers(network_a) | _get_layers(network_b)
    if layers is not None:
        all_layers &= set(layers)
    return {
        "global_distance": _edge_distance(G_a, G_b, directed),
        "layerwise_distance": {
            layer: _edge_distance(
                _scope_graph(G_a, [layer]), _scope_graph(G_b, [layer]), directed
            )
            for layer in sorted(all_layers, key=str)
        },
    }


@metric_registry.register("multilayer_resistance_distance",
                          description="Resistance distance based on supra-Laplacian matrix")
def multilayer_resistance_distance(
    network_a: Any,
    network_b: Any,
    layers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compute resistance distance between two multilayer networks.
    
    Uses the Frobenius norm of the difference between supra-Laplacian matrices.
    
    Args:
        network_a: First multilayer network
        network_b: Second multilayer network
        layers: Optional list of layers to consider
        
    Returns:
        Dictionary with global_distance
    """
    try:
        import numpy as np
        __import__("scipy.sparse")
    except ImportError:
        return {"global_distance": None, "error": "numpy/scipy required"}
    
    G_a = network_a.core_network if hasattr(network_a, 'core_network') else network_a
    G_b = network_b.core_network if hasattr(network_b, 'core_network') else network_b
    
    # Treat uninitialized py3plex networks (`core_network=None`) as empty graphs.
    if G_a is None:
        G_a = nx.Graph()
    if G_b is None:
        G_b = nx.Graph()
    
    G_a, G_b = _scope_graph(G_a, layers), _scope_graph(G_b, layers)
    if G_a.is_directed() or G_b.is_directed():
        return {"global_distance": None, "error": "Resistance distance requires undirected graphs"}
    nodes = list(dict.fromkeys([*G_a, *G_b]))
    if not nodes:
        return {"global_distance": 0.0}

    def laplacian(graph):
        graph = graph.copy()
        graph.add_nodes_from(nodes)
        return nx.laplacian_matrix(graph, nodelist=nodes).astype(float)

    difference = laplacian(G_a) - laplacian(G_b)
    norm = np.sqrt(difference.multiply(difference).sum())
    return {"global_distance": float(norm / len(nodes)**2)}


@metric_registry.register("layer_edge_overlap",
                          description="Edge overlap ratio per layer")
def layer_edge_overlap(
    network_a: Any,
    network_b: Any,
    layers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compute edge overlap ratio per layer.
    
    For each layer, computes the ratio of shared edges to total edges.
    
    Args:
        network_a: First multilayer network
        network_b: Second multilayer network
        layers: Optional list of layers to consider
        
    Returns:
        Dictionary with layerwise_distance
    """
    layerwise = multiplex_jaccard(network_a, network_b, layers)["layerwise_distance"]
    return {
        "global_distance": sum(layerwise.values()) / len(layerwise) if layerwise else 0.0,
        "layerwise_distance": layerwise,
    }


@metric_registry.register("degree_correlation",
                          description="Correlation of node degrees between networks")
def degree_correlation(
    network_a: Any,
    network_b: Any,
    layers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compute degree correlation between two networks.
    
    Computes Pearson correlation of node degrees for shared nodes.
    
    Args:
        network_a: First multilayer network
        network_b: Second multilayer network
        layers: Optional list of layers to consider
        
    Returns:
        Dictionary with global_distance (1 - correlation)
    """
    try:
        import numpy as np
    except ImportError:
        return {"global_distance": None, "error": "numpy required"}
    
    G_a = network_a.core_network if hasattr(network_a, 'core_network') else network_a
    G_b = network_b.core_network if hasattr(network_b, 'core_network') else network_b
    
    # Treat uninitialized py3plex networks (`core_network=None`) as empty graphs.
    if G_a is None:
        G_a = nx.Graph()
    if G_b is None:
        G_b = nx.Graph()
    
    # Nodes to compare: require some overlap, then compare over the union while
    # treating missing nodes as having degree 0 (so isolated/unobserved nodes
    # are still comparable).
    nodes_a = set(G_a.nodes())
    nodes_b = set(G_b.nodes())
    shared_nodes = nodes_a & nodes_b
    
    if layers:
        nodes_a = {
            n for n in nodes_a if isinstance(n, tuple) and len(n) >= 2 and n[1] in layers
        }
        nodes_b = {
            n for n in nodes_b if isinstance(n, tuple) and len(n) >= 2 and n[1] in layers
        }
        shared_nodes = nodes_a & nodes_b
    
    if len(shared_nodes) < 2:
        return {"global_distance": 1.0, "shared_nodes": 0}
    
    nodes_to_compare = nodes_a | nodes_b
    # Get degrees, defaulting to 0 for missing nodes.
    degrees_a = [G_a.degree(n) if n in nodes_a else 0 for n in nodes_to_compare]
    degrees_b = [G_b.degree(n) if n in nodes_b else 0 for n in nodes_to_compare]
    
    # Compute correlation
    if np.std(degrees_a) == 0 or np.std(degrees_b) == 0:
        correlation = 0.0
    else:
        correlation = np.corrcoef(degrees_a, degrees_b)[0, 1]
        if np.isnan(correlation):
            correlation = 0.0
    
    # Distance is 1 - |correlation|
    global_distance = 1.0 - abs(correlation)
    
    return {
        "global_distance": global_distance,
        "correlation": correlation,
        "shared_nodes": len(nodes_to_compare),
    }


@metric_registry.register("degree_change",
                          description="Per-node degree change between networks")
def degree_change(
    network_a: Any,
    network_b: Any,
    layers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compute per-node degree change between two networks.
    
    For each shared node, computes the difference in degree.
    
    Args:
        network_a: First multilayer network
        network_b: Second multilayer network
        layers: Optional list of layers to consider
        
    Returns:
        Dictionary with per_node_difference and global_distance (mean absolute change)
    """
    G_a = network_a.core_network if hasattr(network_a, 'core_network') else network_a
    G_b = network_b.core_network if hasattr(network_b, 'core_network') else network_b
    
    # Treat uninitialized py3plex networks (`core_network=None`) as empty graphs.
    if G_a is None:
        G_a = nx.Graph()
    if G_b is None:
        G_b = nx.Graph()
    
    # Get shared nodes
    nodes_a = set(G_a.nodes())
    nodes_b = set(G_b.nodes())
    shared_nodes = nodes_a & nodes_b
    
    if layers:
        shared_nodes = {
            n for n in shared_nodes
            if isinstance(n, tuple) and len(n) >= 2 and n[1] in layers
        }
    
    # Compute degree changes
    per_node_difference = {}
    for node in shared_nodes:
        deg_a = G_a.degree(node)
        deg_b = G_b.degree(node)
        per_node_difference[node] = deg_b - deg_a
    
    # Global distance is mean absolute change
    if per_node_difference:
        global_distance = sum(abs(v) for v in per_node_difference.values()) / len(per_node_difference)
    else:
        global_distance = 0.0
    
    return {
        "global_distance": global_distance,
        "per_node_difference": per_node_difference,
    }
