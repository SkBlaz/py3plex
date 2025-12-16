"""
10-minute executable tutorial for py3plex.

Runs through network creation, loading, analysis, community detection, and
visualization in one script. Prerequisites: py3plex installed with optional
matplotlib for plots; uses bundled `datasets/synthetic_multilayer.txt`.

SKIP_CI: slow - This tutorial takes more than 10 seconds to complete
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

# Add parent directory to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from py3plex.core import multinet
from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = REPO_ROOT / "datasets" / "synthetic_multilayer.txt"
EXAMPLE_IMAGES_DIR = REPO_ROOT / "example_images"
DEFAULT_SEED = 42


def example_1_create_network():
    """Example 1: Creating Your First Multilayer Network"""
    print("\n" + "="*60)
    print("Example 1: Creating a Multilayer Network")
    print("="*60)

    # Create a new multilayer network
    network = multinet.multi_layer_network()

    # Add edges within layers (this automatically creates nodes)
    # Format: [source_node, source_layer, target_node, target_layer, weight]
    network.add_edges([
        ['A', 'layer1', 'B', 'layer1', 1],
        ['B', 'layer1', 'C', 'layer1', 1],
        ['A', 'layer2', 'B', 'layer2', 1],
        ['B', 'layer2', 'D', 'layer2', 1]
    ], input_type="list")

    # Display basic statistics
    print("\nBasic Statistics:")
    network.basic_stats()

    return network


def example_2_load_network():
    """Example 2: Loading Networks from Files"""
    print("\n" + "="*60)
    print("Example 2: Loading Network from File")
    print("="*60)

    if not DATASET_PATH.exists():
        print(f"Warning: Dataset not found at {DATASET_PATH}")
        print("Skipping this example...")
        return None

    # Load from a multiedgelist file
    network = multinet.multi_layer_network().load_network(
        str(DATASET_PATH),
        input_type="multiedgelist",
        directed=False
    )

    # Check what we loaded
    print("\nLoaded network statistics:")
    network.basic_stats()

    return network


def example_3_explore_structure(network):
    """Example 3: Exploring Network Structure"""
    if network is None:
        print("\nSkipping Example 3 - no network loaded")
        return

    print("\n" + "="*60)
    print("Example 3: Exploring Network Structure")
    print("="*60)

    # Get first few nodes
    print("\nFirst 5 nodes:")
    for i, node in enumerate(network.get_nodes(data=True)):
        if i >= 5:
            break
        print(f"  {node}")

    # Get first few edges
    print("\nFirst 5 edges:")
    for i, edge in enumerate(network.get_edges(data=True)):
        if i >= 5:
            break
        print(f"  {edge}")

    # Try to get neighbors (if network has nodes)
    nodes = list(network.get_nodes())
    if nodes:
        # Nodes are tuples like ('1', '1') where first is node name, second is layer
        node_of_interest = nodes[0][0] if isinstance(nodes[0], tuple) else str(nodes[0])
        layer_names = network.get_layers()
        if layer_names:
            layer_id = str(layer_names[0])
            try:
                neighbors = list(network.get_neighbors(node_of_interest, layer_id=layer_id))
                print(f"\nNeighbors of {node_of_interest} in layer {layer_id}: {neighbors[:5]}")
            except Exception as e:
                print(f"\nCouldn't get neighbors: {e}")

    # Extract subnetworks
    layer_names = network.get_layers()
    if layer_names:
        try:
            first_layer = [str(layer_names[0])]
            layer_1 = network.subnetwork(first_layer, subset_by="layers")
            print(f"\nLayer {first_layer[0]} has {len(list(layer_1.get_nodes()))} nodes")
        except Exception as e:
            print(f"\nCouldn't extract subnetwork: {e}")


def example_4_compute_metrics(network):
    """Example 4: Computing Network Metrics"""
    if network is None:
        print("\nSkipping Example 4 - no network loaded")
        return

    print("\n" + "="*60)
    print("Example 4: Computing Network Metrics")
    print("="*60)

    layer_names = network.get_layers()
    if not layer_names:
        print("No layers found in network")
        return

    try:
        # Get a single layer
        first_layer = [str(layer_names[0])]
        layer_1 = network.subnetwork(first_layer, subset_by="layers")

        # Compute degree centrality
        degree_centrality = layer_1.monoplex_nx_wrapper("degree_centrality")
        print("\nDegree centrality (first 5):")
        for node, score in list(degree_centrality.items())[:5]:
            print(f"  {node}: {score:.3f}")

        # Compute betweenness centrality
        betweenness = layer_1.monoplex_nx_wrapper("betweenness_centrality")
        print("\nBetweenness centrality (first 5):")
        for node, score in list(betweenness.items())[:5]:
            print(f"  {node}: {score:.3f}")
    except Exception as e:
        print(f"Error computing metrics: {e}")
        import traceback
        traceback.print_exc()


def example_5_multilayer_statistics(network):
    """Example 5: Multilayer Network Statistics"""
    if network is None:
        print("\nSkipping Example 5 - no network loaded")
        return

    print("\n" + "="*60)
    print("Example 5: Multilayer Network Statistics")
    print("="*60)

    try:
        from py3plex.algorithms.statistics import multilayer_statistics as mls

        layer_names = network.get_layers()
        if len(layer_names) < 2:
            print("Need at least 2 layers for multilayer statistics")
            return

        layer1 = str(layer_names[0])
        layer2 = str(layer_names[1])

        # Basic Layer Statistics
        print("\n--- Basic Layer Statistics ---")
        density1 = mls.layer_density(network, layer1)
        density2 = mls.layer_density(network, layer2)
        print(f"Layer {layer1} density: {density1:.3f}")
        print(f"Layer {layer2} density: {density2:.3f}")

        entropy = mls.entropy_of_multiplexity(network)
        print(f"Layer diversity (entropy): {entropy:.3f} bits")

        # Node Activity
        print("\n--- Node Activity Across Layers ---")
        nodes = list(network.get_nodes())
        sample_nodes = [n[0] for n in nodes[:4]]  # Get first 4 unique node names
        for node in sample_nodes:
            activity = mls.node_activity(network, node)
            print(f"Node {node} is active in {activity*100:.0f}% of layers")

        # Cross-Layer Analysis
        print("\n--- Cross-Layer Analysis ---")
        similarity = mls.layer_similarity(network, layer1, layer2, method='cosine')
        print(f"Layer similarity (cosine): {similarity:.3f}")

        overlap = mls.edge_overlap(network, layer1, layer2)
        print(f"Edge overlap (Jaccard): {overlap:.3f}")

        # Network Versatility
        print("\n--- Network Versatility ---")
        versatility = mls.versatility_centrality(network, centrality_type='degree')
        print("Top 5 nodes by versatility:")
        for node, score in sorted(versatility.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {node}: {score:.3f}")

        # Network Robustness
        print("\n--- Network Robustness ---")
        resilience = mls.resilience(network, 'layer_removal', perturbation_param=layer1)
        print(f"Resilience after removing {layer1}: {resilience:.3f}")

    except ImportError:
        print("Multilayer statistics module not available")
    except Exception as e:
        print(f"Error computing multilayer statistics: {e}")
        import traceback
        traceback.print_exc()


def example_6_community_detection(network):
    """Example 6: Community Detection"""
    if network is None:
        print("\nSkipping Example 5 - no network loaded")
        return None

    print("\n" + "="*60)
    print("Example 6: Multilayer Community Detection")
    print("="*60)

    try:
        # Multilayer Louvain community detection
        print("Running multilayer Louvain algorithm...")
        partition = louvain_multilayer(network, gamma=1.0, omega=1.0, random_state=DEFAULT_SEED)
        num_communities = len(set(partition.values()))
        print(f"\nCommunities found: {num_communities}")

        # Display community assignments (first 5)
        print("\nCommunity assignments (first 5):")
        for node, community_id in list(partition.items())[:5]:
            print(f"  Node {node} -> Community {community_id}")

        # Count nodes per community
        community_sizes = Counter(partition.values())
        print("\nCommunity sizes (top 5):")
        for comm, size in community_sizes.most_common(5):
            print(f"  Community {comm}: {size} nodes")

        return partition
    except Exception as e:
        print(f"Error in community detection: {e}")
        import traceback
        traceback.print_exc()
        return None


def example_7_visualization(network, partition=None):
    """Example 7: Basic Visualization"""
    if network is None:
        print("\nSkipping Example 7 - no network loaded")
        return

    print("\n" + "="*60)
    print("Example 7: Visualization")
    print("="*60)

    try:
        # Check if matplotlib is available
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend for testing
        import matplotlib.pyplot as plt
        from py3plex.visualization.multilayer import hairball_plot
        from py3plex.visualization.colors import colors_default

        # Get network for visualization
        network_colors, graph = network.get_layers(style="hairball")

        # Create output directory
        EXAMPLE_IMAGES_DIR.mkdir(exist_ok=True)

        # Simple visualization
        output_file = EXAMPLE_IMAGES_DIR / "tutorial_network.png"
        plt.figure(figsize=(12, 12))
        hairball_plot(
            graph,
            network_colors,
            layout_algorithm="force",
            layout_parameters={"iterations": 100},
            node_size=5,
            edge_width=0.5,
            alpha_channel=0.8
        )
        plt.title("Multilayer Network Visualization", fontsize=16, fontweight='bold')
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"\nVisualization saved to {output_file}")

        # Visualization with communities
        if partition is not None:
            top_n = min(10, len(set(partition.values())))
            community_counts = Counter(partition.values())
            top_communities = [c for c, _ in community_counts.most_common(top_n)]

            color_map = dict(zip(top_communities, colors_default[:top_n]))
            network_colors = [
                color_map.get(partition.get(node), "lightgray")
                for node in network.get_nodes()
            ]

            output_file_comm = EXAMPLE_IMAGES_DIR / "tutorial_network_communities.png"
            plt.figure(figsize=(12, 12))
            hairball_plot(
                graph,
                network_colors,
                layout_algorithm="force",
                layout_parameters={"iterations": 100},
                node_size=5,
                edge_width=0.5,
                alpha_channel=0.8
            )
            plt.title("Multilayer Network with Communities", fontsize=16, fontweight='bold')
            plt.savefig(output_file_comm, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            print(f"Community visualization saved to {output_file_comm}")
    except ImportError as e:
        print(f"Visualization skipped - missing dependency: {e}")
    except Exception as e:
        print(f"Error in visualization: {e}")
        import traceback
        traceback.print_exc()


def complete_example():
    """Complete Example: Putting It All Together"""
    print("\n" + "="*60)
    print("Complete Example: Full Workflow")
    print("="*60)

    if not DATASET_PATH.exists():
        print(f"Dataset not found at {DATASET_PATH}")
        print("Using simple network instead...")

        # Create a simple network
        network = multinet.multi_layer_network()
        network.add_edges([
            ['A', 'layer1', 'B', 'layer1', 1],
            ['B', 'layer1', 'C', 'layer1', 1],
            ['A', 'layer2', 'B', 'layer2', 1],
            ['B', 'layer2', 'D', 'layer2', 1]
        ], input_type="list")
    else:
        # Load network
        network = multinet.multi_layer_network().load_network(
            str(DATASET_PATH),
            input_type="multiedgelist",
            directed=False,
        )

    # Analyze structure
    print("\n=== Network Statistics ===")
    network.basic_stats()

    # Compute centrality for one layer
    layer_names = network.get_layers()
    if layer_names:
        try:
            first_layer = [str(layer_names[0])]
            layer_1 = network.subnetwork(first_layer, subset_by="layers")
            degree_cent = layer_1.monoplex_nx_wrapper("degree_centrality")
            print(f"\n=== Top 5 Nodes by Degree (Layer {first_layer[0]}) ===")
            for node, score in sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"{node}: {score:.3f}")
        except Exception as e:
            print(f"Could not compute centrality: {e}")

    # Detect communities with multilayer method
    try:
        print("\n=== Multilayer Community Detection ===")
        partition = louvain_multilayer(network, gamma=1.0, omega=1.0, random_state=DEFAULT_SEED)
        print(f"Number of communities: {len(set(partition.values()))}")

        # Try visualization
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            from py3plex.visualization.multilayer import hairball_plot
            from py3plex.visualization.colors import colors_default

            network_colors, graph = network.get_layers(style="hairball")
            top_n = min(3, len(set(partition.values())))
            community_counts = Counter(partition.values())
            top_communities = [c for c, _ in community_counts.most_common(top_n)]
            color_map = dict(zip(top_communities, colors_default[:top_n]))
            network_colors = [
                color_map.get(partition.get(node), "lightgray")
                for node in network.get_nodes()
            ]

            EXAMPLE_IMAGES_DIR.mkdir(exist_ok=True)
            output_file = EXAMPLE_IMAGES_DIR / "complete_analysis.png"

            plt.figure(figsize=(12, 12))
            hairball_plot(
                graph,
                network_colors,
                layout_algorithm="force",
                layout_parameters={"iterations": 100},
                node_size=5,
                edge_width=0.5,
                alpha_channel=0.8
            )
            plt.title("Multilayer Network Analysis", fontsize=16, fontweight='bold')
            plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            print(f"\nComplete analysis saved to {output_file}")
        except ImportError:
            print("\nVisualization skipped - matplotlib not available")
    except Exception as e:
        print(f"Could not complete full analysis: {e}")


def main() -> int:
    """Run all tutorial examples"""
    print("\n" + "="*60)
    print("Py3plex 10-Minute Tutorial - Executable Examples")
    print("="*60)

    # Example 1: Create network from scratch
    network1 = example_1_create_network()

    # Example 2: Load network from file
    network2 = example_2_load_network()

    # Use the loaded network for remaining examples (or created one if load failed)
    network = network2 if network2 is not None else network1

    # Example 3: Explore structure
    example_3_explore_structure(network)

    # Example 4: Compute metrics
    example_4_compute_metrics(network)

    # Example 5: Multilayer statistics
    example_5_multilayer_statistics(network)

    # Example 6: Community detection
    partition = example_6_community_detection(network)

    # Example 7: Visualization
    example_7_visualization(network, partition)

    # Complete example
    complete_example()

    print("\n" + "="*60)
    print("Tutorial completed successfully! [OK]")
    print("="*60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
