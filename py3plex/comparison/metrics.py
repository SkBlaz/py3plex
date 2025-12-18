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


def _get_edges_set(G: nx.Graph) -> Set[Tuple[Any, Any]]:
    """Get edges as a set of frozensets for undirected comparison."""
    edges = set()
    for u, v in G.edges():
        edges.add(frozenset([u, v]))
    return edges


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
    
    # Get all layers
    layers_a = _get_layers(network_a)
    layers_b = _get_layers(network_b)
    all_layers = layers_a | layers_b
    
    if layers:
        all_layers = all_layers & set(layers)
    
    # Compute global Jaccard
    edges_a = _get_edges_set(G_a)
    edges_b = _get_edges_set(G_b)

    if layers is not None:
        allowed_layers = all_layers

        def _in_allowed_layers(edge: Set[Any]) -> bool:
            if len(edge) != 2:
                return False
            u, v = tuple(edge)
            return (
                isinstance(u, tuple)
                and isinstance(v, tuple)
                and len(u) >= 2
                and len(v) >= 2
                and u[1] in allowed_layers
                and v[1] in allowed_layers
            )

        edges_a = {edge for edge in edges_a if _in_allowed_layers(edge)}
        edges_b = {edge for edge in edges_b if _in_allowed_layers(edge)}
    
    intersection = len(edges_a & edges_b)
    union = len(edges_a | edges_b)
    
    global_jaccard = intersection / union if union > 0 else 1.0
    global_distance = 1.0 - global_jaccard
    
    # Compute per-layer Jaccard
    layerwise_distance = {}
    for layer in sorted(all_layers):
        # Get edges within this layer
        layer_edges_a = set()
        layer_edges_b = set()
        
        for u, v in G_a.edges():
            if isinstance(u, tuple) and isinstance(v, tuple):
                if len(u) >= 2 and len(v) >= 2:
                    if u[1] == layer and v[1] == layer:
                        layer_edges_a.add(frozenset([u, v]))
        
        for u, v in G_b.edges():
            if isinstance(u, tuple) and isinstance(v, tuple):
                if len(u) >= 2 and len(v) >= 2:
                    if u[1] == layer and v[1] == layer:
                        layer_edges_b.add(frozenset([u, v]))
        
        layer_intersection = len(layer_edges_a & layer_edges_b)
        layer_union = len(layer_edges_a | layer_edges_b)
        
        layer_jaccard = layer_intersection / layer_union if layer_union > 0 else 1.0
        layerwise_distance[layer] = 1.0 - layer_jaccard
    
    return {
        "global_distance": global_distance,
        "layerwise_distance": layerwise_distance,
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
        from scipy import sparse
    except ImportError:
        return {"global_distance": None, "error": "numpy/scipy required"}
    
    G_a = network_a.core_network if hasattr(network_a, 'core_network') else network_a
    G_b = network_b.core_network if hasattr(network_b, 'core_network') else network_b
    
    # Treat uninitialized py3plex networks (`core_network=None`) as empty graphs.
    if G_a is None:
        G_a = nx.Graph()
    if G_b is None:
        G_b = nx.Graph()
    
    # Get Laplacian matrices
    try:
        L_a = nx.laplacian_matrix(G_a).toarray().astype(float)
        L_b = nx.laplacian_matrix(G_b).toarray().astype(float)
    except Exception:
        return {"global_distance": None, "error": "Could not compute Laplacian"}
    
    # Pad matrices to same size if needed
    n_a, n_b = L_a.shape[0], L_b.shape[0]
    if n_a != n_b:
        max_n = max(n_a, n_b)
        L_a_padded = np.zeros((max_n, max_n))
        L_b_padded = np.zeros((max_n, max_n))
        L_a_padded[:n_a, :n_a] = L_a
        L_b_padded[:n_b, :n_b] = L_b
        L_a, L_b = L_a_padded, L_b_padded
    elif n_a == 0:
        return {"global_distance": 0.0}
    
    # Frobenius norm of difference
    diff = L_a - L_b
    frobenius_norm = np.linalg.norm(diff, ord='fro')
    
    # Normalize by matrix size
    n = L_a.shape[0]
    global_distance = frobenius_norm / (n**2) if n else 0.0
    
    return {"global_distance": global_distance}


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
    G_a = network_a.core_network if hasattr(network_a, 'core_network') else network_a
    G_b = network_b.core_network if hasattr(network_b, 'core_network') else network_b
    
    # Treat uninitialized py3plex networks (`core_network=None`) as empty graphs.
    if G_a is None:
        G_a = nx.Graph()
    if G_b is None:
        G_b = nx.Graph()
    
    # Get all layers
    layers_a = _get_layers(network_a)
    layers_b = _get_layers(network_b)
    all_layers = layers_a | layers_b
    
    if layers:
        all_layers = all_layers & set(layers)
    
    layerwise_distance = {}
    for layer in sorted(all_layers):
        # Get edges within this layer
        layer_edges_a = set()
        layer_edges_b = set()
        
        for u, v in G_a.edges():
            if isinstance(u, tuple) and isinstance(v, tuple):
                if len(u) >= 2 and len(v) >= 2:
                    if u[1] == layer and v[1] == layer:
                        layer_edges_a.add(frozenset([u, v]))
        
        for u, v in G_b.edges():
            if isinstance(u, tuple) and isinstance(v, tuple):
                if len(u) >= 2 and len(v) >= 2:
                    if u[1] == layer and v[1] == layer:
                        layer_edges_b.add(frozenset([u, v]))
        
        overlap = len(layer_edges_a & layer_edges_b)
        total = len(layer_edges_a | layer_edges_b)
        
        # Distance is 1 - overlap_ratio
        overlap_ratio = overlap / total if total > 0 else 1.0
        layerwise_distance[layer] = 1.0 - overlap_ratio
    
    # Compute global as average of layerwise
    if layerwise_distance:
        global_distance = sum(layerwise_distance.values()) / len(layerwise_distance)
    else:
        global_distance = 0.0
    
    return {
        "global_distance": global_distance,
        "layerwise_distance": layerwise_distance,
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
