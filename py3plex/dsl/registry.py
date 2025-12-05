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
