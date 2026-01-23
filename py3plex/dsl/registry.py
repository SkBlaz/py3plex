"""Measure registry for DSL v2.

This module provides a registry for network measures that can be computed
via the COMPUTE clause in DSL queries.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
import networkx as nx

from .errors import UnknownMeasureError


def _convert_multigraph_to_simple(G: nx.Graph) -> nx.Graph:
    """Convert a MultiGraph to a simple Graph for measures that don't support MultiGraphs.
    
    When a graph has parallel edges (MultiGraph), this function merges them into
    a simple graph by keeping the edge with maximum weight.
    
    Args:
        G: Input graph (may be MultiGraph or Graph)
        
    Returns:
        Simple graph (Graph type). If input was already a simple graph, returns as-is.
    """
    if not isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
        return G
    
    simple_G = nx.Graph()
    for u, v, data in G.edges(data=True):
        if simple_G.has_edge(u, v):
            # If edge already exists, keep the one with maximum weight
            existing_weight = simple_G[u][v].get('weight', 1)
            new_weight = data.get('weight', 1)
            simple_G[u][v]['weight'] = max(existing_weight, new_weight)
        else:
            simple_G.add_edge(u, v, weight=data.get('weight', 1))
    
    return simple_G


class MeasureRegistry:
    """Registry for network measures.
    
    Allows registration of measure computation functions and retrieval
    by name. Supports aliases for common alternative names, target validation
    (node measures vs edge measures), and approximate implementations.
    """
    
    def __init__(self):
        self._measures: Dict[str, Callable] = {}
        self._aliases: Dict[str, str] = {}
        self._descriptions: Dict[str, str] = {}
        self._targets: Dict[str, str] = {}  # Measure name -> target (nodes/edges/both)
        self._approx_methods: Dict[str, Dict[str, Callable]] = {}  # measure -> {method: fn}
    
    def register(self, name: str, aliases: Optional[List[str]] = None,
                 description: Optional[str] = None, target: str = "nodes"):
        """Decorator to register a measure function.
        
        Args:
            name: Primary name for the measure
            aliases: Optional list of alternative names
            description: Optional description of the measure
            target: Target type for the measure ("nodes", "edges", or "both")
            
        Returns:
            Decorator function
        """
        def decorator(fn: Callable) -> Callable:
            self._measures[name] = fn
            self._targets[name] = target
            if description:
                self._descriptions[name] = description
            if aliases:
                for alias in aliases:
                    self._aliases[alias] = name
            return fn
        return decorator
    
    def register_approx(self, measure_name: str, method_name: str):
        """Decorator to register an approximate implementation for a measure.
        
        Args:
            measure_name: Name of the measure (must be already registered)
            method_name: Name of the approximation method (e.g., "sampling", "landmarks")
            
        Returns:
            Decorator function
            
        Example:
            >>> @measure_registry.register_approx("betweenness_centrality", "sampling")
            >>> def approx_betweenness_sampling(G, n_samples=100, seed=None, **kwargs):
            ...     # implementation
            ...     pass
        """
        def decorator(fn: Callable) -> Callable:
            if measure_name not in self._approx_methods:
                self._approx_methods[measure_name] = {}
            self._approx_methods[measure_name][method_name] = fn
            return fn
        return decorator
    
    def get(self, name: str, target: Optional[str] = None) -> Callable:
        """Get a measure function by name.
        
        Args:
            name: Measure name or alias
            target: Expected target type (nodes/edges) for validation
            
        Returns:
            The measure function
            
        Raises:
            UnknownMeasureError: If measure is not found
            DslExecutionError: If measure doesn't support the requested target
        """
        # Check direct name
        actual_name = name
        if name in self._measures:
            actual_name = name
        elif name in self._aliases:
            actual_name = self._aliases[name]
        else:
            # Raise error with suggestions
            raise UnknownMeasureError(name, list(self.list_measures()))
        
        # Validate target if specified
        if target is not None:
            measure_target = self._targets.get(actual_name, "nodes")
            if measure_target != "both" and measure_target != target:
                from .errors import DslExecutionError
                target_desc = "edge queries" if target == "edges" else "node queries"
                raise DslExecutionError(
                    f"Measure '{name}' is only supported for {measure_target} queries, "
                    f"not for {target_desc}. "
                    f"Use a {measure_target}-specific measure instead."
                )
        
        return self._measures[actual_name]
    
    def get_approx(self, name: str, method: str) -> Optional[Callable]:
        """Get an approximate implementation for a measure.
        
        Args:
            name: Measure name or alias
            method: Approximation method name
            
        Returns:
            The approximate measure function or None if not available
        """
        # Resolve alias
        actual_name = name
        if name in self._aliases:
            actual_name = self._aliases[name]
        
        if actual_name not in self._approx_methods:
            return None
        
        return self._approx_methods[actual_name].get(method)
    
    def has_approx(self, name: str, method: str) -> bool:
        """Check if an approximate implementation exists for a measure.
        
        Args:
            name: Measure name or alias
            method: Approximation method name
            
        Returns:
            True if approximate implementation exists
        """
        actual_name = name
        if name in self._aliases:
            actual_name = self._aliases[name]
        
        if actual_name not in self._approx_methods:
            return False
        
        return method in self._approx_methods[actual_name]
        
        # Validate target if specified
        if target is not None:
            measure_target = self._targets.get(actual_name, "nodes")
            if measure_target != "both" and measure_target != target:
                from .errors import DslExecutionError
                target_desc = "edge queries" if target == "edges" else "node queries"
                raise DslExecutionError(
                    f"Measure '{name}' is only supported for {measure_target} queries, "
                    f"not for {target_desc}. "
                    f"Use a {measure_target}-specific measure instead."
                )
        
        return self._measures[actual_name]
    
    def has(self, name: str) -> bool:
        """Check if a measure is registered.
        
        Args:
            name: Measure name or alias
            
        Returns:
            True if measure exists
        """
        return name in self._measures or name in self._aliases
    
    def list_measures(self) -> List[str]:
        """List all registered measure names (including aliases).
        
        Returns:
            List of measure names
        """
        return list(self._measures.keys()) + list(self._aliases.keys())
    
    def get_description(self, name: str) -> Optional[str]:
        """Get description for a measure.
        
        Args:
            name: Measure name
            
        Returns:
            Description or None
        """
        # Resolve alias
        if name in self._aliases:
            name = self._aliases[name]
        return self._descriptions.get(name)


# Global measure registry
measure_registry = MeasureRegistry()


# Register built-in measures
@measure_registry.register("degree", description="Node degree (number of edges)")
def _compute_degree(G: nx.Graph, nodes: Optional[List] = None) -> Dict[Any, int]:
    """Compute degree for nodes."""
    if nodes is not None:
        return {node: G.degree(node) for node in nodes if node in G}
    return dict(G.degree())


@measure_registry.register("degree_centrality", description="Normalized degree centrality")
def _compute_degree_centrality(G: nx.Graph, nodes: Optional[List] = None) -> Dict[Any, float]:
    """Compute degree centrality for nodes."""
    centrality = nx.degree_centrality(G)
    if nodes is not None:
        return {node: centrality.get(node, 0) for node in nodes}
    return centrality


@measure_registry.register("betweenness_centrality", aliases=["betweenness"],
                          description="Betweenness centrality (Brandes algorithm)")
def _compute_betweenness(G: nx.Graph, nodes: Optional[List] = None) -> Dict[Any, float]:
    """Compute betweenness centrality for nodes."""
    centrality = nx.betweenness_centrality(G)
    if nodes is not None:
        return {node: centrality.get(node, 0) for node in nodes}
    return centrality


@measure_registry.register("closeness_centrality", aliases=["closeness"],
                          description="Closeness centrality")
def _compute_closeness(G: nx.Graph, nodes: Optional[List] = None) -> Dict[Any, float]:
    """Compute closeness centrality for nodes."""
    centrality = nx.closeness_centrality(G)
    if nodes is not None:
        return {node: centrality.get(node, 0) for node in nodes}
    return centrality


@measure_registry.register("eigenvector_centrality", aliases=["eigenvector"],
                          description="Eigenvector centrality")
def _compute_eigenvector(G: nx.Graph, nodes: Optional[List] = None) -> Dict[Any, float]:
    """Compute eigenvector centrality for nodes."""
    try:
        centrality = nx.eigenvector_centrality(G, max_iter=1000)
    except nx.PowerIterationFailedConvergence:
        # Fallback for non-convergence - log warning and return zeros
        import warnings
        warnings.warn(
            "Eigenvector centrality failed to converge. "
            "Returning zero values. Consider using a different centrality measure.",
            RuntimeWarning
        )
        centrality = {node: 0.0 for node in G.nodes()}
    if nodes is not None:
        return {node: centrality.get(node, 0) for node in nodes}
    return centrality


@measure_registry.register("pagerank", description="PageRank centrality")
def _compute_pagerank(G: nx.Graph, nodes: Optional[List] = None) -> Dict[Any, float]:
    """Compute PageRank for nodes."""
    pagerank = nx.pagerank(G)
    if nodes is not None:
        return {node: pagerank.get(node, 0) for node in nodes}
    return pagerank


@measure_registry.register("clustering", aliases=["clustering_coefficient"],
                          description="Local clustering coefficient")
def _compute_clustering(G: nx.Graph, nodes: Optional[List] = None) -> Dict[Any, float]:
    """Compute clustering coefficient for nodes.
    
    Note: NetworkX clustering is not implemented for MultiGraphs.
    If G is a MultiGraph, we convert it to a simple Graph by removing
    parallel edges (keeping the edge with maximum weight if weights exist).
    """
    # Convert to simple graph if needed
    G = _convert_multigraph_to_simple(G)
    
    if nodes is not None:
        return nx.clustering(G, nodes)
    return nx.clustering(G)


@measure_registry.register("triangles", description="Number of triangles per node")
def _compute_triangles(G: nx.Graph, nodes: Optional[List] = None) -> Dict[Any, int]:
    """Compute number of triangles for each node.
    
    Note: NetworkX triangles is not implemented for MultiGraphs.
    If G is a MultiGraph, we convert it to a simple Graph by removing
    parallel edges (keeping the edge with maximum weight if weights exist).
    """
    # Convert to simple graph if needed
    G = _convert_multigraph_to_simple(G)
    
    if nodes is not None:
        return {node: nx.triangles(G, node) for node in nodes if node in G}
    return nx.triangles(G)


@measure_registry.register("communities", aliases=["community"],
                          description="Community detection (Louvain)")
def _compute_communities(G: nx.Graph, nodes: Optional[List] = None) -> Dict[Any, int]:
    """Compute community assignments for nodes using Louvain algorithm."""
    try:
        from py3plex.algorithms.community_detection.community_louvain import best_partition
    except ImportError:
        raise RuntimeError("Community detection requires python-louvain package")
    
    # Convert to simple graph if needed (Louvain doesn't support MultiGraphs)
    simple_G = _convert_multigraph_to_simple(G)
    
    if len(simple_G.nodes()) == 0:
        return {}
    
    partition = best_partition(simple_G)
    
    if nodes is not None:
        return {node: partition.get(node, -1) for node in nodes}
    return partition


# ============================================================================
# Edge-specific measures
# ============================================================================


@measure_registry.register("edge_betweenness_centrality", 
                          aliases=["edge_betweenness"],
                          description="Edge betweenness centrality",
                          target="edges")
def _compute_edge_betweenness(G: nx.Graph, edges: Optional[List] = None) -> Dict[Tuple, float]:
    """Compute edge betweenness centrality for edges.
    
    Args:
        G: NetworkX graph
        edges: Optional list of edges to compute for (if None, computes for all)
        
    Returns:
        Dictionary mapping (u, v) edge tuples to betweenness values
        
    Note:
        Returns dict with (u, v) keys (without data dict) to ensure hashability.
    """
    # Compute edge betweenness for the entire graph
    centrality = nx.edge_betweenness_centrality(G)
    
    if edges is not None:
        # Filter to requested edges
        result = {}
        for edge in edges:
            # Edge format: ((node, layer), (node, layer), {data}?)
            if isinstance(edge, tuple) and len(edge) >= 2:
                u, v = edge[0], edge[1]
                # Use (u, v) as key for hashability
                edge_key = (u, v)
                
                # Try both directions for undirected graphs
                if edge_key in centrality:
                    result[edge_key] = centrality[edge_key]
                elif (v, u) in centrality:
                    result[edge_key] = centrality[(v, u)]
                else:
                    result[edge_key] = 0.0
        return result
    
    # Return all edges
    return centrality


# ============================================================================
# Example: Registering measures as operators (demonstrating unified system)
# ============================================================================

# Import operator functions to show how measures can also be operators
from .operator_registry import register_operator
from .context import DSLExecutionContext


# Register a few built-in measures as operators to demonstrate the unified system
# This shows that the operator registry can coexist with the measure registry


def _multiplex_degree_operator(context: DSLExecutionContext) -> Dict[Any, int]:
    """Compute degree as an operator (demonstrates operator pattern).
    
    This is an example of how measures can be implemented as operators,
    receiving a DSLExecutionContext and computing results based on it.
    """
    G = context.graph.core_network
    nodes = context.current_nodes or []
    
    # Compute degree for nodes in the subgraph
    result = {}
    for node in nodes:
        if node in G:
            result[node] = G.degree(node)
        else:
            result[node] = 0
    
    return result


def _layer_count_operator(context: DSLExecutionContext) -> Dict[Any, int]:
    """Count the number of layers each node appears in.
    
    This is a multilayer-specific operator that demonstrates accessing
    layer information from the context.
    """
    # Count layers for each unique node ID
    node_layers = {}
    for node in context.current_nodes or []:
        if isinstance(node, tuple) and len(node) >= 2:
            node_id, layer = node[0], node[1]
            if node_id not in node_layers:
                node_layers[node_id] = set()
            node_layers[node_id].add(layer)
    
    # Assign layer counts
    result = {}
    for node in context.current_nodes or []:
        if isinstance(node, tuple) and len(node) >= 2:
            node_id = node[0]
            result[node] = len(node_layers.get(node_id, set()))
        else:
            result[node] = 0
    
    return result


# Register the operators
register_operator(
    "multiplex_degree",
    _multiplex_degree_operator,
    description="Compute degree considering multilayer structure",
    category="centrality",
)

register_operator(
    "layer_count",
    _layer_count_operator,
    description="Count number of layers each node appears in",
    category="multilayer",
)


# =============================================================================
# Approximate Implementations
# =============================================================================

# Import approximate algorithms
try:
    from py3plex.algorithms.centrality.approx_betweenness import approximate_betweenness_sampling
    from py3plex.algorithms.centrality.approx_closeness import approximate_closeness_landmarks
    from py3plex.algorithms.centrality.approx_pagerank import approximate_pagerank_power_iteration
    
    _APPROX_AVAILABLE = True
except ImportError:
    _APPROX_AVAILABLE = False


if _APPROX_AVAILABLE:
    # Register approximate betweenness (sampling method)
    @measure_registry.register_approx("betweenness_centrality", "sampling")
    def _approx_betweenness_sampling(G: nx.Graph, nodes: Optional[List] = None,
                                      n_samples: int = 100, seed: Optional[int] = None,
                                      normalized: bool = True, weight: Optional[str] = None,
                                      diagnostics: bool = False) -> Tuple[Dict[Any, float], Optional[Dict[Any, float]]]:
        """Compute approximate betweenness centrality using sampling.
        
        Args:
            G: NetworkX graph
            nodes: Optional list of nodes to compute for (filters result if provided)
            n_samples: Number of source samples
            seed: Random seed for reproducibility
            normalized: Whether to normalize values
            weight: Edge weight attribute name
            diagnostics: Whether to compute per-node stderr
            
        Returns:
            Tuple of (values_dict, stderr_dict or None)
        """
        betw, stderr = approximate_betweenness_sampling(
            G, n_samples=n_samples, seed=seed, normalized=normalized,
            weight=weight, diagnostics=diagnostics
        )
        
        if nodes is not None:
            betw = {node: betw.get(node, 0) for node in nodes}
            if stderr:
                stderr = {node: stderr.get(node, 0) for node in nodes}
        
        return betw, stderr
    
    # Register approximate closeness (landmarks method)
    @measure_registry.register_approx("closeness_centrality", "landmarks")
    def _approx_closeness_landmarks(G: nx.Graph, nodes: Optional[List] = None,
                                     n_landmarks: int = 64, seed: Optional[int] = None,
                                     weight: Optional[str] = None,
                                     diagnostics: bool = False) -> Tuple[Dict[Any, float], Optional[Dict[Any, float]]]:
        """Compute approximate closeness centrality using landmarks.
        
        Args:
            G: NetworkX graph
            nodes: Optional list of nodes to compute for
            n_landmarks: Number of landmark nodes
            seed: Random seed for reproducibility
            weight: Edge weight attribute name
            diagnostics: Whether to compute per-node stderr
            
        Returns:
            Tuple of (values_dict, stderr_dict or None)
        """
        close, stderr = approximate_closeness_landmarks(
            G, n_landmarks=n_landmarks, seed=seed, weight=weight, diagnostics=diagnostics
        )
        
        if nodes is not None:
            close = {node: close.get(node, 0) for node in nodes}
            if stderr:
                stderr = {node: stderr.get(node, 0) for node in nodes}
        
        return close, stderr
    
    # Register approximate pagerank (power iteration with explicit stopping)
    @measure_registry.register_approx("pagerank", "power_iteration")
    def _approx_pagerank_power(G: nx.Graph, nodes: Optional[List] = None,
                                alpha: float = 0.85, tol: float = 1e-6,
                                max_iter: int = 100,
                                personalization: Optional[Dict] = None,
                                diagnostics: bool = False) -> Tuple[Dict[Any, float], Optional[Dict]]:
        """Compute approximate PageRank using power iteration.
        
        Args:
            G: NetworkX graph
            nodes: Optional list of nodes to compute for
            alpha: Damping parameter
            tol: Convergence tolerance
            max_iter: Maximum iterations
            personalization: Personalization vector
            diagnostics: Whether to include convergence info
            
        Returns:
            Tuple of (values_dict, convergence_info_dict or None)
        """
        pr, conv = approximate_pagerank_power_iteration(
            G, alpha=alpha, tol=tol, max_iter=max_iter, personalization=personalization
        )
        
        if nodes is not None:
            pr = {node: pr.get(node, 0) for node in nodes}
        
        # Return convergence info as second element if diagnostics enabled
        return pr, (conv if diagnostics else None)


