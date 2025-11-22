"""
Base classes for py3plex plugins.

This module defines abstract base classes that all plugins must inherit from.
Each plugin type has specific requirements and interfaces.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BasePlugin(ABC):
    """
    Abstract base class for all py3plex plugins.
    
    All plugins must inherit from this class and implement the required methods.
    
    Attributes:
        name: Plugin name (unique identifier)
        version: Plugin version string
        author: Plugin author name/email
        description: Brief description of what the plugin does
    """

    def __init__(self):
        """Initialize the plugin."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the plugin name."""
        pass

    @property
    def version(self) -> str:
        """Return the plugin version."""
        return "1.0.0"

    @property
    def author(self) -> str:
        """Return the plugin author."""
        return "Unknown"

    @property
    def description(self) -> str:
        """Return the plugin description."""
        return "No description provided"

    def validate(self) -> bool:
        """
        Validate that the plugin can run (e.g., check dependencies).
        
        Returns:
            True if plugin is valid and can run, False otherwise
        """
        return True


class CentralityPlugin(BasePlugin):
    """
    Base class for centrality measure plugins.
    
    Centrality plugins compute importance scores for nodes in a network.
    
    Example:
        >>> class MyCustomCentrality(CentralityPlugin):
        ...     @property
        ...     def name(self):
        ...         return "my_centrality"
        ...     
        ...     def compute(self, network, **kwargs):
        ...         # Compute centrality for each node
        ...         centrality = {}
        ...         for node in network.get_nodes():
        ...             centrality[node] = compute_score(node)
        ...         return centrality
    """

    @abstractmethod
    def compute(self, network, **kwargs) -> Dict[str, float]:
        """
        Compute centrality scores for all nodes in the network.
        
        Args:
            network: A py3plex multi_layer_network object
            **kwargs: Additional algorithm-specific parameters
            
        Returns:
            Dictionary mapping node IDs to centrality scores
            
        Raises:
            ValueError: If network is invalid or incompatible
        """
        pass

    @property
    def supports_weighted(self) -> bool:
        """Whether this centrality supports weighted networks."""
        return False

    @property
    def supports_directed(self) -> bool:
        """Whether this centrality supports directed networks."""
        return False

    @property
    def supports_multilayer(self) -> bool:
        """Whether this centrality supports multilayer networks."""
        return False


class CommunityPlugin(BasePlugin):
    """
    Base class for community detection plugins.
    
    Community detection plugins identify groups of densely connected nodes.
    
    Example:
        >>> class MyCommunitDetector(CommunityPlugin):
        ...     @property
        ...     def name(self):
        ...         return "my_community_detector"
        ...     
        ...     def detect(self, network, **kwargs):
        ...         # Detect communities
        ...         communities = detect_communities(network)
        ...         return communities
    """

    @abstractmethod
    def detect(self, network, **kwargs) -> Dict[str, int]:
        """
        Detect communities in the network.
        
        Args:
            network: A py3plex multi_layer_network object
            **kwargs: Algorithm-specific parameters (resolution, seed, etc.)
            
        Returns:
            Dictionary mapping node IDs to community IDs
            
        Raises:
            ValueError: If network is invalid or incompatible
        """
        pass

    @property
    def supports_weighted(self) -> bool:
        """Whether this algorithm supports weighted networks."""
        return False

    @property
    def supports_overlapping(self) -> bool:
        """Whether this algorithm can find overlapping communities."""
        return False

    @property
    def supports_hierarchical(self) -> bool:
        """Whether this algorithm produces hierarchical communities."""
        return False


class LayoutPlugin(BasePlugin):
    """
    Base class for network layout plugins.
    
    Layout plugins compute 2D/3D positions for visualizing networks.
    
    Example:
        >>> class MyLayout(LayoutPlugin):
        ...     @property
        ...     def name(self):
        ...         return "my_layout"
        ...     
        ...     def compute_layout(self, network, **kwargs):
        ...         # Compute node positions
        ...         positions = {}
        ...         for node in network.get_nodes():
        ...             positions[node] = (x, y)
        ...         return positions
    """

    @abstractmethod
    def compute_layout(
        self, network, dimensions: int = 2, **kwargs
    ) -> Dict[str, tuple]:
        """
        Compute layout positions for network nodes.
        
        Args:
            network: A py3plex multi_layer_network object
            dimensions: Number of dimensions (2 or 3)
            **kwargs: Algorithm-specific parameters
            
        Returns:
            Dictionary mapping node IDs to position tuples (x, y) or (x, y, z)
            
        Raises:
            ValueError: If network is invalid or dimensions not supported
        """
        pass

    @property
    def supports_3d(self) -> bool:
        """Whether this layout supports 3D positions."""
        return False

    @property
    def supports_weighted(self) -> bool:
        """Whether this layout considers edge weights."""
        return False


class MetricPlugin(BasePlugin):
    """
    Base class for network metric plugins.
    
    Metric plugins compute global or local network properties.
    
    Example:
        >>> class MyMetric(MetricPlugin):
        ...     @property
        ...     def name(self):
        ...         return "my_metric"
        ...     
        ...     def compute(self, network, **kwargs):
        ...         # Compute metric
        ...         value = compute_network_property(network)
        ...         return {"metric_value": value}
    """

    @abstractmethod
    def compute(self, network, **kwargs) -> Dict[str, Any]:
        """
        Compute network metrics.
        
        Args:
            network: A py3plex multi_layer_network object
            **kwargs: Algorithm-specific parameters
            
        Returns:
            Dictionary of metric names to values
            
        Raises:
            ValueError: If network is invalid or incompatible
        """
        pass

    @property
    def metric_type(self) -> str:
        """
        Type of metric: 'global', 'local', or 'both'.
        
        Global metrics return single values for the whole network.
        Local metrics return values per node/edge.
        """
        return "global"
