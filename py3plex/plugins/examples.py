"""
Example plugins demonstrating how to extend py3plex with custom algorithms.

These examples show how to create plugins for different types of network analysis.
"""

from py3plex.plugins import (
    CentralityPlugin,
    CommunityPlugin,
    LayoutPlugin,
    MetricPlugin,
    PluginRegistry,
)


@PluginRegistry.register("centrality", "example_degree")
class ExampleDegreeCentrality(CentralityPlugin):
    """
    Example centrality plugin computing simple degree centrality.
    
    This is a demonstration plugin showing the plugin interface.
    """

    @property
    def name(self) -> str:
        return "example_degree"

    @property
    def description(self) -> str:
        return "Example plugin computing degree centrality"

    @property
    def author(self) -> str:
        return "Py3plex Development Team"

    @property
    def supports_weighted(self) -> bool:
        return True

    @property
    def supports_directed(self) -> bool:
        return True

    @property
    def supports_multilayer(self) -> bool:
        return True

    def compute(self, network, normalized=False, **kwargs):
        """
        Compute degree centrality for all nodes.
        
        Args:
            network: A py3plex multi_layer_network object
            normalized: Whether to normalize by max possible degree
            **kwargs: Additional parameters
            
        Returns:
            Dictionary mapping node IDs to degree centrality scores
        """
        centrality = {}

        # Get all nodes from the network
        try:
            # Use the NetworkX graph directly
            G = network.core_network
            if G is None:
                return {}
            nodes = list(G.nodes())
        except AttributeError:
            raise ValueError("Network must be a py3plex multi_layer_network object")

        # Compute degree for each node
        for node in nodes:
            degree = G.degree(node)
            centrality[node] = degree

        # Optionally normalize
        if normalized and len(nodes) > 1:
            max_degree = len(nodes) - 1
            centrality = {k: v / max_degree for k, v in centrality.items()}

        return centrality


@PluginRegistry.register("community", "example_simple")
class ExampleSimpleCommunity(CommunityPlugin):
    """
    Example community detection plugin using simple connected components.
    
    This is a demonstration plugin showing the plugin interface.
    """

    DEFAULT_NUM_COMMUNITIES = 5  # Default number of communities to create

    @property
    def name(self) -> str:
        return "example_simple"

    @property
    def description(self) -> str:
        return "Example plugin for simple community detection"

    @property
    def author(self) -> str:
        return "Py3plex Development Team"

    def detect(self, network, num_communities=None, **kwargs):
        """
        Detect communities using a simple algorithm.
        
        Args:
            network: A py3plex multi_layer_network object
            num_communities: Number of communities to create (default: 5)
                            This is a demonstration parameter showing
                            how to make plugins configurable
            **kwargs: Additional parameters
            
        Returns:
            Dictionary mapping node IDs to community IDs
        """
        if num_communities is None:
            num_communities = self.DEFAULT_NUM_COMMUNITIES

        communities = {}

        try:
            # Use the NetworkX graph directly
            G = network.core_network
            if G is None:
                return {}
        except AttributeError:
            raise ValueError("Network must be a py3plex multi_layer_network object")

        if G.number_of_nodes() == 0:
            return {}

        import networkx as nx

        # Use connected components as a simple, deterministic community detector.
        if G.is_directed():
            components = list(nx.weakly_connected_components(G))
        else:
            components = list(nx.connected_components(G))

        # Deterministic community IDs by sorting components by their stringified contents.
        def _component_key(component):
            return sorted(str(node) for node in component)

        for community_idx, component in enumerate(sorted(components, key=_component_key)):
            assigned_id = community_idx % num_communities if num_communities else community_idx
            for node in component:
                communities[node] = assigned_id

        return communities


@PluginRegistry.register("metric", "example_density")
class ExampleNetworkDensity(MetricPlugin):
    """
    Example metric plugin computing network density.
    
    This is a demonstration plugin showing the plugin interface.
    """

    @property
    def name(self) -> str:
        return "example_density"

    @property
    def description(self) -> str:
        return "Example plugin computing network density"

    @property
    def author(self) -> str:
        return "Py3plex Development Team"

    @property
    def metric_type(self) -> str:
        return "global"

    def compute(self, network, **kwargs):
        """
        Compute network density.
        
        Args:
            network: A py3plex multi_layer_network object
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with density metric
        """
        try:
            # Use the NetworkX graph directly
            G = network.core_network
            num_nodes = G.number_of_nodes()
            num_edges = G.number_of_edges()
        except AttributeError:
            raise ValueError("Network must be a py3plex multi_layer_network object")

        if num_nodes < 2:
            density = 0.0
        else:
            max_edges = num_nodes * (num_nodes - 1)
            density = (2 * num_edges) / max_edges if max_edges > 0 else 0.0

        return {
            "density": density,
            "num_nodes": num_nodes,
            "num_edges": num_edges,
        }


@PluginRegistry.register("layout", "example_circular")
class ExampleCircularLayout(LayoutPlugin):
    """
    Example layout plugin arranging nodes in a circle.
    
    This is a demonstration plugin showing the plugin interface.
    """

    @property
    def name(self) -> str:
        return "example_circular"

    @property
    def description(self) -> str:
        return "Example plugin arranging nodes in a circular layout"

    @property
    def author(self) -> str:
        return "Py3plex Development Team"

    def compute_layout(self, network, dimensions=2, **kwargs):
        """
        Compute circular layout positions.
        
        Args:
            network: A py3plex multi_layer_network object
            dimensions: Number of dimensions (2 only for this example)
            **kwargs: Additional parameters
            
        Returns:
            Dictionary mapping node IDs to (x, y) positions
        """
        import math

        if dimensions != 2:
            raise ValueError("Example circular layout only supports 2D")

        try:
            # Use the NetworkX graph directly
            G = network.core_network
            nodes = list(G.nodes())
        except AttributeError:
            raise ValueError("Network must be a py3plex multi_layer_network object")

        positions = {}
        n = len(nodes)

        if n == 0:
            return positions

        # Arrange nodes in a circle
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / n
            x = math.cos(angle)
            y = math.sin(angle)
            positions[node] = (x, y)

        return positions
