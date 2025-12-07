"""Measure registry for DSL v2.

This module provides a registry for network measures that can be computed
via the COMPUTE clause in DSL queries.
"""

from typing import Any, Callable, Dict, List, Optional
import networkx as nx

from .errors import UnknownMeasureError


class MeasureRegistry:
    """Registry for network measures.
    
    Allows registration of measure computation functions and retrieval
    by name. Supports aliases for common alternative names.
    """
    
    def __init__(self):
        self._measures: Dict[str, Callable] = {}
        self._aliases: Dict[str, str] = {}
        self._descriptions: Dict[str, str] = {}
    
    def register(self, name: str, aliases: Optional[List[str]] = None,
                 description: Optional[str] = None):
        """Decorator to register a measure function.
        
        Args:
            name: Primary name for the measure
            aliases: Optional list of alternative names
            description: Optional description of the measure
            
        Returns:
            Decorator function
        """
        def decorator(fn: Callable) -> Callable:
            self._measures[name] = fn
            if description:
                self._descriptions[name] = description
            if aliases:
                for alias in aliases:
                    self._aliases[alias] = name
            return fn
        return decorator
    
    def get(self, name: str) -> Callable:
        """Get a measure function by name.
        
        Args:
            name: Measure name or alias
            
        Returns:
            The measure function
            
        Raises:
            UnknownMeasureError: If measure is not found
        """
        # Check direct name
        if name in self._measures:
            return self._measures[name]
        
        # Check aliases
        if name in self._aliases:
            return self._measures[self._aliases[name]]
        
        # Raise error with suggestions
        raise UnknownMeasureError(name, list(self.list_measures()))
    
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
    """Compute clustering coefficient for nodes."""
    if nodes is not None:
        return nx.clustering(G, nodes)
    return nx.clustering(G)


@measure_registry.register("communities", aliases=["community"],
                          description="Community detection (Louvain)")
def _compute_communities(G: nx.Graph, nodes: Optional[List] = None) -> Dict[Any, int]:
    """Compute community assignments for nodes using Louvain algorithm."""
    try:
        from py3plex.algorithms.community_detection.community_louvain import best_partition
    except ImportError:
        raise RuntimeError("Community detection requires python-louvain package")
    
    # Convert to simple graph if needed
    if isinstance(G, nx.MultiGraph):
        simple_G = nx.Graph()
        for u, v, data in G.edges(data=True):
            if simple_G.has_edge(u, v):
                existing_weight = simple_G[u][v].get('weight', 1)
                new_weight = data.get('weight', 1)
                simple_G[u][v]['weight'] = max(existing_weight, new_weight)
            else:
                simple_G.add_edge(u, v, weight=data.get('weight', 1))
    else:
        simple_G = G
    
    if len(simple_G.nodes()) == 0:
        return {}
    
    partition = best_partition(simple_G)
    
    if nodes is not None:
        return {node: partition.get(node, -1) for node in nodes}
    return partition


# ============================================================================
# Example: Migrating built-in operators to new system
# ============================================================================
# 
# Below are examples of how to use the new operator registry system alongside
# the existing measure registry. These operators demonstrate the new API.
#

from .operator_registry import register_operator, DSLExecutionContext


# Example 1: Simple operator that uses context
def _operator_node_count(context: DSLExecutionContext) -> int:
    """Count the number of nodes in the current selection.
    
    Args:
        context: Execution context with graph, current_nodes, etc.
        
    Returns:
        Number of selected nodes
    """
    if context.current_nodes is not None:
        return len(context.current_nodes)
    elif hasattr(context.graph, 'get_nodes'):
        return len(list(context.graph.get_nodes()))
    return 0


register_operator(
    "node_count",
    _operator_node_count,
    description="Count nodes in current selection",
    category="statistics"
)


# Example 2: Operator with parameters
def _operator_layer_degree(context: DSLExecutionContext, layer: Optional[str] = None) -> Dict[Any, int]:
    """Compute degree for nodes in a specific layer.
    
    Args:
        context: Execution context
        layer: Optional layer name (defaults to all current layers)
        
    Returns:
        Dict mapping nodes to their degrees
    """
    if not hasattr(context.graph, 'core_network'):
        return {}
    
    G = context.graph.core_network
    nodes = context.current_nodes or []
    
    # Filter nodes by layer if specified
    if layer is not None:
        nodes = [n for n in nodes if isinstance(n, tuple) and len(n) >= 2 and n[1] == layer]
    
    # Compute degrees
    return {node: G.degree(node) if node in G else 0 for node in nodes}


register_operator(
    "layer_degree",
    _operator_layer_degree,
    description="Compute node degree within a specific layer",
    category="centrality"
)


# Example 3: Operator that accesses multiple context fields
def _operator_layer_stats(context: DSLExecutionContext) -> Dict[str, Any]:
    """Compute statistics about current layer selection.
    
    Args:
        context: Execution context
        
    Returns:
        Dict with layer statistics
    """
    stats = {
        "num_layers": len(context.current_layers) if context.current_layers else 0,
        "num_nodes": len(context.current_nodes) if context.current_nodes else 0,
    }
    
    if hasattr(context.graph, 'core_network') and context.graph.core_network:
        G = context.graph.core_network
        nodes = context.current_nodes or []
        stats["num_edges"] = sum(1 for n in nodes if n in G for _ in G.neighbors(n)) // 2
    
    return stats


register_operator(
    "layer_stats",
    _operator_layer_stats,
    description="Compute statistics about layer selection",
    category="statistics"
)

