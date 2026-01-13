"""Plugin system walkthrough: define, register, and use py3plex plugins.

Prerequisites: built-in py3plex dependencies only (networkx included).
Runtime: FAST (<5s)
"""

from __future__ import annotations

from typing import Any, Dict

from py3plex import multi_layer_network
from py3plex.plugins import (
    CentralityPlugin,
    CommunityPlugin,
    PluginRegistry,
)


# Example 1: Create a custom centrality plugin
@PluginRegistry.register("centrality", "closeness_simple")
class SimpleClosenessCentrality(CentralityPlugin):
    """A simple closeness centrality implementation.

    Demonstrates how to create a custom centrality measure.
    """

    @property
    def name(self) -> str:
        return "closeness_simple"

    @property
    def description(self) -> str:
        return "Simple closeness centrality based on shortest paths"

    @property
    def author(self) -> str:
        return "Py3plex Example"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supports_weighted(self) -> bool:
        return False

    @property
    def supports_directed(self) -> bool:
        return False

    def compute(self, network, **kwargs) -> Dict[Any, float]:
        """Compute closeness centrality for all nodes."""
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
    """Community detection based on connected components."""

    @property
    def name(self) -> str:
        return "connected_components"

    @property
    def description(self) -> str:
        return "Detects communities as connected components"

    @property
    def author(self) -> str:
        return "Py3plex Example"

    @property
    def version(self) -> str:
        return "1.0.0"

    def detect(self, network, **kwargs) -> Dict[Any, int]:
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


def create_sample_network():
    """Create a tiny two-component network for plugin demonstrations."""
    net = multi_layer_network()
    net.add_nodes(
        [
            {"source": "A", "type": "layer1"},
            {"source": "B", "type": "layer1"},
            {"source": "C", "type": "layer1"},
            {"source": "D", "type": "layer1"},
            {"source": "E", "type": "layer1"},
        ]
    )
    net.add_edges(
        [
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
    )
    return net


def list_available_plugins(registry: PluginRegistry) -> None:
    """Print all registered plugins grouped by type."""
    print("-" * 70)
    print("Available Plugins:")
    print("-" * 70)
    all_plugins = registry.list_plugins()
    for plugin_type, plugin_names in all_plugins.items():
        if plugin_names:
            print(f"  {plugin_type}:")
            for name in sorted(plugin_names):
                print(f"    - {name}")
    print()


def show_plugin_info(registry: PluginRegistry, plugin_type: str, name: str) -> None:
    """Print metadata for a specific plugin."""
    print("-" * 70)
    print("Plugin Information:")
    print("-" * 70)
    info = registry.get_plugin_info(plugin_type, name)
    print(f"  Name: {info['name']}")
    print(f"  Type: {info['type']}")
    print(f"  Version: {info['version']}")
    print(f"  Author: {info['author']}")
    print(f"  Description: {info['description']}")
    print()


def run_custom_plugins(registry: PluginRegistry, net) -> None:
    """Run the two custom plugins defined in this example."""
    print("-" * 70)
    print("Computing Closeness Centrality:")
    print("-" * 70)
    closeness_plugin = registry.get("centrality", "closeness_simple")
    closeness_scores = closeness_plugin.compute(net)
    for node, score in sorted(closeness_scores.items()):
        print(f"  Node {node}: {score:.4f}")
    print()

    print("-" * 70)
    print("Detecting Communities:")
    print("-" * 70)
    community_plugin = registry.get("community", "connected_components")
    communities = community_plugin.detect(net)
    for node, community_id in sorted(communities.items()):
        print(f"  Node {node}: Community {community_id}")
    print()


def run_builtin_plugins(registry: PluginRegistry, net) -> None:
    """Demonstrate using plugins shipped with py3plex."""
    print("-" * 70)
    print("Using Built-in Example Plugins:")
    print("-" * 70)

    import py3plex.plugins.examples  # noqa: F401

    example_degree = registry.get("centrality", "example_degree")
    degree_scores = example_degree.compute(net)
    print("  Degree Centrality:")
    for node, score in sorted(degree_scores.items()):
        print(f"    Node {node}: {score}")
    print()

    example_layout = registry.get("layout", "example_circular")
    positions = example_layout.compute_layout(net)
    print("  Circular Layout Positions:")
    for node, pos in sorted(positions.items()):
        print(f"    Node {node}: ({pos[0]:.3f}, {pos[1]:.3f})")
    print()


def main() -> int:
    """Main function demonstrating plugin usage."""
    print("=" * 70)
    print("Py3plex Plugin System Example")
    print("=" * 70)
    print()

    net = create_sample_network()
    print(f"Network created with {len(list(net.get_nodes()))} nodes and {len(list(net.get_edges()))} edges")
    print()

    registry = PluginRegistry()
    list_available_plugins(registry)
    show_plugin_info(registry, "centrality", "closeness_simple")
    run_custom_plugins(registry, net)
    run_builtin_plugins(registry, net)

    print("=" * 70)
    print("Plugin System Example Complete!")
    print("=" * 70)
    print()
    print("To create your own plugins:")
    print("  1. See PLUGIN_GUIDE.md for detailed instructions")
    print("  2. Check py3plex/plugins/examples.py for more examples")
    print("  3. Create plugins in ~/.py3plex/plugins/ for auto-discovery")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
