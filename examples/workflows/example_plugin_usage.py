"""
Example demonstrating how to use the py3plex plugin system.

This example shows:
1. How to create custom plugins
2. How to register and use plugins
3. How to list available plugins
4. How to get plugin information
"""

from py3plex import multi_layer_network
from py3plex.plugins import (
    CentralityPlugin,
    CommunityPlugin,
    PluginRegistry,
)


# Example 1: Create a custom centrality plugin
@PluginRegistry.register("centrality", "closeness_simple")
class SimpleClosenessCentrality(CentralityPlugin):
    """
    A simple closeness centrality implementation.
    
    This plugin demonstrates how to create a custom centrality measure.
    """

    @property
    def name(self):
        return "closeness_simple"

    @property
    def description(self):
        return "Simple closeness centrality based on shortest paths"

    @property
    def author(self):
        return "Py3plex Example"

    @property
    def version(self):
        return "1.0.0"

    @property
    def supports_weighted(self):
        return False

    @property
    def supports_directed(self):
        return False

    def compute(self, network, **kwargs):
        """
        Compute closeness centrality for all nodes.
        
        Closeness is the inverse of the average shortest path length to all other nodes.
        """
        import networkx as nx

        # Convert to NetworkX for easier computation
        G = network.core_network

        centrality = {}
        nodes = list(G.nodes())

        if len(nodes) == 0:
            return centrality

        # Compute closeness for each node
        for node in nodes:
            # Get shortest path lengths to all other nodes
            try:
                lengths = nx.single_source_shortest_path_length(G, node)
                # Remove the node itself
                lengths.pop(node, None)

                if lengths:
                    avg_length = sum(lengths.values()) / len(lengths)
                    centrality[node] = 1.0 / avg_length if avg_length > 0 else 0.0
                else:
                    centrality[node] = 0.0
            except Exception:
                centrality[node] = 0.0

        return centrality


# Example 2: Create a custom community detection plugin
@PluginRegistry.register("community", "connected_components")
class ConnectedComponentsCommunity(CommunityPlugin):
    """
    Community detection based on connected components.
    
    This plugin treats each connected component as a separate community.
    """

    @property
    def name(self):
        return "connected_components"

    @property
    def description(self):
        return "Detects communities as connected components"

    @property
    def author(self):
        return "Py3plex Example"

    @property
    def version(self):
        return "1.0.0"

    def detect(self, network, **kwargs):
        """
        Detect communities using connected components.
        """
        import networkx as nx

        # Convert to NetworkX
        G = network.core_network

        # Convert to undirected for connected components
        if G.is_directed():
            G = G.to_undirected()

        communities = {}

        # Find connected components
        for i, component in enumerate(nx.connected_components(G)):
            for node in component:
                communities[node] = i

        return communities


def main():
    """Main function demonstrating plugin usage."""
    print("=" * 70)
    print("Py3plex Plugin System Example")
    print("=" * 70)
    print()

    # Create a simple network
    print("Creating a sample network...")
    net = multi_layer_network()

    # Add nodes
    nodes = [
        {"source": "A", "type": "layer1"},
        {"source": "B", "type": "layer1"},
        {"source": "C", "type": "layer1"},
        {"source": "D", "type": "layer1"},
        {"source": "E", "type": "layer1"},
    ]
    net.add_nodes(nodes)

    # Add edges to create two components
    edges = [
        {
            "source": "A",
            "target": "B",
            "source_type": "layer1",
            "target_type": "layer1",
        },
        {
            "source": "B",
            "target": "C",
            "source_type": "layer1",
            "target_type": "layer1",
        },
        {
            "source": "D",
            "target": "E",
            "source_type": "layer1",
            "target_type": "layer1",
        },
    ]
    net.add_edges(edges)

    print(f"Network created with {len(list(net.get_nodes()))} nodes and {len(list(net.get_edges()))} edges")
    print()

    # Get the registry
    registry = PluginRegistry()

    # Example 3: List all available plugins
    print("-" * 70)
    print("Available Plugins:")
    print("-" * 70)
    all_plugins = registry.list_plugins()
    for plugin_type, plugin_names in all_plugins.items():
        if plugin_names:
            print(f"  {plugin_type}:")
            for name in plugin_names:
                print(f"    - {name}")
    print()

    # Example 4: Get plugin information
    print("-" * 70)
    print("Plugin Information:")
    print("-" * 70)
    info = registry.get_plugin_info("centrality", "closeness_simple")
    print(f"  Name: {info['name']}")
    print(f"  Type: {info['type']}")
    print(f"  Version: {info['version']}")
    print(f"  Author: {info['author']}")
    print(f"  Description: {info['description']}")
    print()

    # Example 5: Use the closeness centrality plugin
    print("-" * 70)
    print("Computing Closeness Centrality:")
    print("-" * 70)
    closeness_plugin = registry.get("centrality", "closeness_simple")
    closeness_scores = closeness_plugin.compute(net)
    for node, score in sorted(closeness_scores.items()):
        print(f"  Node {node}: {score:.4f}")
    print()

    # Example 6: Use the community detection plugin
    print("-" * 70)
    print("Detecting Communities:")
    print("-" * 70)
    community_plugin = registry.get("community", "connected_components")
    communities = community_plugin.detect(net)
    for node, community_id in sorted(communities.items()):
        print(f"  Node {node}: Community {community_id}")
    print()

    # Example 7: Use built-in example plugins
    print("-" * 70)
    print("Using Built-in Example Plugins:")
    print("-" * 70)

    # Import example plugins
    import py3plex.plugins.examples  # noqa: F401

    # Use example degree centrality
    example_degree = registry.get("centrality", "example_degree")
    degree_scores = example_degree.compute(net)
    print("  Degree Centrality:")
    for node, score in sorted(degree_scores.items()):
        print(f"    Node {node}: {score}")
    print()

    # Use example circular layout
    example_layout = registry.get("layout", "example_circular")
    positions = example_layout.compute_layout(net)
    print("  Circular Layout Positions:")
    for node, pos in sorted(positions.items()):
        print(f"    Node {node}: ({pos[0]:.3f}, {pos[1]:.3f})")
    print()

    print("=" * 70)
    print("Plugin System Example Complete!")
    print("=" * 70)
    print()
    print("To create your own plugins:")
    print("  1. See PLUGIN_GUIDE.md for detailed instructions")
    print("  2. Check py3plex/plugins/examples.py for more examples")
    print("  3. Create plugins in ~/.py3plex/plugins/ for auto-discovery")
    print()


if __name__ == "__main__":
    main()
