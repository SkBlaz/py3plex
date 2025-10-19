#!/usr/bin/env python
"""
Command-line interface for py3plex.

This module provides a comprehensive CLI tool for multilayer network analysis
with full coverage of main algorithms.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import networkx as nx

from py3plex import __version__
from py3plex.core import multinet


def _load_network(file_path: str) -> "multinet.multi_layer_network":
    """Load a network from file, handling different formats.
    
    Args:
        file_path: Path to the network file
        
    Returns:
        Loaded multi_layer_network object
    """
    network = multinet.multi_layer_network()
    input_path = Path(file_path)
    
    # For formats not directly supported by py3plex, load with NetworkX first
    if input_path.suffix in [".graphml", ".gexf"]:
        if input_path.suffix == ".graphml":
            G = nx.read_graphml(str(file_path))
        else:  # .gexf
            G = nx.read_gexf(str(file_path))
        # Convert NetworkX graph to py3plex format
        # The core_network is a NetworkX graph, so we can assign directly
        network.core_network = G
        network.directed = G.is_directed()
    elif input_path.suffix == ".gpickle":
        network.load_network(file_path, input_type="gpickle")
    else:
        # Try as GML or edgelist
        try:
            network.load_network(file_path, input_type="gml")
        except:
            try:
                network.load_network(file_path, input_type="edgelist")
            except Exception as e:
                raise ValueError(f"Could not load network from {file_path}: {e}")
    
    return network


def _determine_input_type(file_path: str) -> str:
    """Determine network input type from file extension.
    
    Args:
        file_path: Path to the input file
        
    Returns:
        Input type string for load_network
    """
    input_path = Path(file_path)
    if input_path.suffix == ".graphml":
        return "graphml"
    elif input_path.suffix == ".gexf":
        return "gexf"
    elif input_path.suffix == ".gpickle":
        return "gpickle"
    else:
        return "gml"  # default


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for py3plex CLI.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="py3plex",
        description="Py3plex - A library for multilayer network analysis and visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a simple multilayer network
  py3plex create --nodes 100 --layers 3 --output network.graphml

  # Load and analyze a network
  py3plex load network.graphml --stats

  # Detect communities using Louvain
  py3plex community network.graphml --algorithm louvain --output communities.json

  # Compute centrality measures
  py3plex centrality network.graphml --measure degree --output centrality.json

  # Visualize a network
  py3plex visualize network.graphml --output network.png

  # Get multilayer statistics
  py3plex stats network.graphml --measure all --output stats.json

For more information, visit: https://github.com/SkBlaz/py3plex
        """,
    )

    parser.add_argument(
        "--version", action="version", version=f"py3plex {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # CREATE command
    create_parser = subparsers.add_parser(
        "create", help="Create a new multilayer network"
    )
    create_parser.add_argument(
        "--nodes", type=int, default=10, help="Number of nodes (default: 10)"
    )
    create_parser.add_argument(
        "--layers", type=int, default=2, help="Number of layers (default: 2)"
    )
    create_parser.add_argument(
        "--type",
        choices=["random", "er", "ba", "ws"],
        default="random",
        help="Network type: random (default), er (Erdős-Rényi), ba (Barabási-Albert), ws (Watts-Strogatz)",
    )
    create_parser.add_argument(
        "--probability",
        type=float,
        default=0.1,
        help="Edge probability for ER/WS networks (default: 0.1)",
    )
    create_parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output file (supports .graphml, .gexf, .gpickle)",
    )
    create_parser.add_argument("--seed", type=int, help="Random seed for reproducibility")

    # LOAD command
    load_parser = subparsers.add_parser(
        "load", help="Load and inspect a multilayer network"
    )
    load_parser.add_argument("input", help="Input network file")
    load_parser.add_argument(
        "--info", action="store_true", help="Display network information"
    )
    load_parser.add_argument(
        "--stats", action="store_true", help="Display basic statistics"
    )
    load_parser.add_argument(
        "--output", "-o", help="Save output to file (JSON format)"
    )

    # COMMUNITY command
    community_parser = subparsers.add_parser(
        "community", help="Detect communities in the network"
    )
    community_parser.add_argument("input", help="Input network file")
    community_parser.add_argument(
        "--algorithm",
        "-a",
        choices=["louvain", "infomap", "label_prop"],
        default="louvain",
        help="Community detection algorithm (default: louvain)",
    )
    community_parser.add_argument(
        "--output", "-o", help="Output file for community assignments (JSON)"
    )
    community_parser.add_argument(
        "--resolution",
        type=float,
        default=1.0,
        help="Resolution parameter for Louvain (default: 1.0)",
    )

    # CENTRALITY command
    centrality_parser = subparsers.add_parser(
        "centrality", help="Compute node centrality measures"
    )
    centrality_parser.add_argument("input", help="Input network file")
    centrality_parser.add_argument(
        "--measure",
        "-m",
        choices=["degree", "betweenness", "closeness", "eigenvector", "pagerank"],
        default="degree",
        help="Centrality measure (default: degree)",
    )
    centrality_parser.add_argument(
        "--output", "-o", help="Output file for centrality scores (JSON)"
    )
    centrality_parser.add_argument(
        "--top", type=int, help="Show only top N nodes"
    )

    # STATS command
    stats_parser = subparsers.add_parser(
        "stats", help="Compute multilayer network statistics"
    )
    stats_parser.add_argument("input", help="Input network file")
    stats_parser.add_argument(
        "--measure",
        "-m",
        choices=[
            "all",
            "density",
            "clustering",
            "layer_density",
            "node_activity",
            "versatility",
            "edge_overlap",
        ],
        default="all",
        help="Statistic to compute (default: all)",
    )
    stats_parser.add_argument(
        "--layer", help="Specific layer for layer-specific statistics"
    )
    stats_parser.add_argument(
        "--output", "-o", help="Output file for statistics (JSON)"
    )

    # VISUALIZE command
    viz_parser = subparsers.add_parser(
        "visualize", help="Visualize the multilayer network"
    )
    viz_parser.add_argument("input", help="Input network file")
    viz_parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output image file (e.g., network.png)",
    )
    viz_parser.add_argument(
        "--layout",
        choices=["spring", "circular", "kamada_kawai", "multilayer"],
        default="multilayer",
        help="Layout algorithm (default: multilayer)",
    )
    viz_parser.add_argument(
        "--width", type=int, default=12, help="Figure width in inches (default: 12)"
    )
    viz_parser.add_argument(
        "--height", type=int, default=8, help="Figure height in inches (default: 8)"
    )

    # AGGREGATE command
    aggregate_parser = subparsers.add_parser(
        "aggregate", help="Aggregate multilayer network into single layer"
    )
    aggregate_parser.add_argument("input", help="Input network file")
    aggregate_parser.add_argument(
        "--method",
        choices=["sum", "mean", "max", "min"],
        default="sum",
        help="Aggregation method for edge weights (default: sum)",
    )
    aggregate_parser.add_argument(
        "--output", "-o", required=True, help="Output file for aggregated network"
    )

    # CONVERT command
    convert_parser = subparsers.add_parser(
        "convert", help="Convert network between different formats"
    )
    convert_parser.add_argument("input", help="Input network file")
    convert_parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Output file (format determined by extension: .graphml, .gexf, .gpickle, .json)",
    )

    return parser


def cmd_create(args: argparse.Namespace) -> int:
    """Create a new multilayer network.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    try:
        import random

        if args.seed is not None:
            random.seed(args.seed)
            import numpy as np
            np.random.seed(args.seed)

        print(f"Creating {args.type} multilayer network with {args.nodes} nodes and {args.layers} layers...")

        network = multinet.multi_layer_network()

        # Create layers and add nodes
        for layer_idx in range(args.layers):
            layer_name = f"layer{layer_idx + 1}"

            # Add nodes to this layer using dict format
            nodes_dict = [{"source": f"node{i}", "type": layer_name} for i in range(args.nodes)]
            network.add_nodes(nodes_dict, input_type="dict")

            # Add edges based on network type
            if args.type == "random" or args.type == "er":
                # Erdős-Rényi random graph
                edges_dict = []
                for i in range(args.nodes):
                    for j in range(i + 1, args.nodes):
                        if random.random() < args.probability:
                            edges_dict.append({
                                "source": f"node{i}",
                                "target": f"node{j}",
                                "source_type": layer_name,
                                "target_type": layer_name,
                            })
                if edges_dict:
                    network.add_edges(edges_dict, input_type="dict")

            elif args.type == "ba":
                # Barabási-Albert preferential attachment
                m = max(1, int(args.nodes * args.probability))
                edges_dict = []
                degrees = {i: 0 for i in range(args.nodes)}

                # Start with a small complete graph
                for i in range(min(m + 1, args.nodes)):
                    degrees[i] = m
                    for j in range(i + 1, min(m + 1, args.nodes)):
                        edges_dict.append({
                            "source": f"node{i}",
                            "target": f"node{j}",
                            "source_type": layer_name,
                            "target_type": layer_name,
                        })

                # Add remaining nodes with preferential attachment
                for i in range(m + 1, args.nodes):
                    targets = []
                    degree_sum = sum(degrees.values())
                    if degree_sum > 0:
                        probs = [degrees[j] / degree_sum for j in range(i)]
                        targets = random.choices(range(i), weights=probs, k=min(m, i))

                    for target in targets:
                        edges_dict.append({
                            "source": f"node{i}",
                            "target": f"node{target}",
                            "source_type": layer_name,
                            "target_type": layer_name,
                        })
                        degrees[i] += 1
                        degrees[target] += 1

                if edges_dict:
                    network.add_edges(edges_dict, input_type="dict")

            elif args.type == "ws":
                # Watts-Strogatz small-world
                k = max(2, int(args.nodes * args.probability / 2) * 2)  # Ensure k is even
                edges_dict = []
                # Create ring lattice
                for i in range(args.nodes):
                    for j in range(1, k // 2 + 1):
                        target = (i + j) % args.nodes
                        edges_dict.append({
                            "source": f"node{i}",
                            "target": f"node{target}",
                            "source_type": layer_name,
                            "target_type": layer_name,
                        })
                if edges_dict:
                    network.add_edges(edges_dict, input_type="dict")

        # Save network
        output_path = Path(args.output)
        try:
            if output_path.suffix == ".graphml":
                nx.write_graphml(network.core_network, str(output_path))
            elif output_path.suffix == ".gexf":
                nx.write_gexf(network.core_network, str(output_path))
            elif output_path.suffix == ".gpickle":
                network.save_network(str(output_path), output_type="gpickle")
            elif output_path.suffix in [".edgelist", ".txt"]:
                network.save_network(str(output_path), output_type="edgelist")
            else:
                print(f"Warning: Unsupported format '{output_path.suffix}', using GraphML")
                nx.write_graphml(network.core_network, str(output_path.with_suffix(".graphml")))
        except Exception as e:
            print(f"Warning: Error saving with native format, trying alternate method: {e}")
            nx.write_graphml(network.core_network, str(output_path))

        print(f"Network saved to {args.output}")
        print(f"  Nodes: {network.core_network.number_of_nodes()}")
        print(f"  Edges: {network.core_network.number_of_edges()}")
        print(f"  Layers: {len(network.get_layers())}")

        return 0
    except Exception as e:
        print(f"Error creating network: {e}", file=sys.stderr)
        return 1


def cmd_load(args: argparse.Namespace) -> int:
    """Load and inspect a network.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    try:
        print(f"Loading network from {args.input}...")
        network = _load_network(args.input)

        output_data = {}

        if args.info or not args.stats:
            info = {
                "nodes": network.core_network.number_of_nodes(),
                "edges": network.core_network.number_of_edges(),
                "layers": network.get_layers()[0] if isinstance(network.get_layers(), tuple) else list(network.get_layers()),
                "directed": network.directed,
            }
            output_data["info"] = info

            print("\nNetwork Information:")
            print(f"  Nodes: {info['nodes']}")
            print(f"  Edges: {info['edges']}")
            print(f"  Layers: {len(info['layers'])} ({', '.join(info['layers'])})")
            print(f"  Directed: {info['directed']}")

        if args.stats:
            from py3plex.algorithms.statistics import multilayer_statistics as mls

            stats = {}
            try:
                layers = network.get_layers()[0] if isinstance(network.get_layers(), tuple) else list(network.get_layers())
                if layers:
                    stats["layer_densities"] = {
                        layer: float(mls.layer_density(network, layer))
                        for layer in layers
                    }

                # Overall clustering
                stats["clustering_coefficient"] = float(
                    nx.average_clustering(network.core_network.to_undirected())
                )

                # Degree distribution
                degrees = dict(network.core_network.degree())
                stats["avg_degree"] = float(sum(degrees.values()) / len(degrees)) if degrees else 0
                stats["max_degree"] = int(max(degrees.values())) if degrees else 0

            except Exception as e:
                print(f"Warning: Could not compute all statistics: {e}")

            output_data["statistics"] = stats

            print("\nBasic Statistics:")
            if "layer_densities" in stats:
                print("  Layer Densities:")
                for layer, density in stats["layer_densities"].items():
                    print(f"    {layer}: {density:.4f}")
            print(f"  Avg Clustering: {stats.get('clustering_coefficient', 0):.4f}")
            print(f"  Avg Degree: {stats.get('avg_degree', 0):.2f}")
            print(f"  Max Degree: {stats.get('max_degree', 0)}")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2)
            print(f"\nOutput saved to {args.output}")

        return 0
    except Exception as e:
        print(f"Error loading network: {e}", file=sys.stderr)
        return 1


def cmd_community(args: argparse.Namespace) -> int:
    """Detect communities in the network.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    try:
        print(f"Loading network from {args.input}...")
        network = _load_network(args.input)

        print(f"Detecting communities using {args.algorithm}...")

        communities = {}

        if args.algorithm == "louvain":
            from py3plex.algorithms.community_detection import community_wrapper

            partition = community_wrapper.louvain_communities(
                network.core_network, resolution=args.resolution
            )
            communities = {str(node): int(comm) for node, comm in partition.items()}

        elif args.algorithm == "infomap":
            try:
                from py3plex.algorithms.community_detection import community_wrapper

                partition = community_wrapper.infomap_communities(network)
                communities = {str(node): int(comm) for node, comm in partition.items()}
            except Exception as e:
                print(f"Error: Infomap not available: {e}", file=sys.stderr)
                print("Please use 'louvain' or 'label_prop' instead.", file=sys.stderr)
                return 1

        elif args.algorithm == "label_prop":
            # Use NetworkX label propagation
            partition = nx.algorithms.community.label_propagation_communities(
                network.core_network.to_undirected()
            )
            communities = {}
            for comm_id, comm_nodes in enumerate(partition):
                for node in comm_nodes:
                    communities[str(node)] = comm_id

        # Count communities
        num_communities = len(set(communities.values()))
        print(f"Found {num_communities} communities")

        # Community size distribution
        comm_sizes = {}
        for comm_id in communities.values():
            comm_sizes[comm_id] = comm_sizes.get(comm_id, 0) + 1

        print(f"Community sizes: min={min(comm_sizes.values())}, max={max(comm_sizes.values())}, avg={sum(comm_sizes.values())/len(comm_sizes):.1f}")

        output_data = {
            "algorithm": args.algorithm,
            "num_communities": num_communities,
            "communities": communities,
            "community_sizes": {int(k): int(v) for k, v in comm_sizes.items()},
        }

        if args.output:
            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2)
            print(f"Communities saved to {args.output}")
        else:
            # Print sample
            print("\nSample community assignments:")
            for i, (node, comm) in enumerate(list(communities.items())[:10]):
                print(f"  {node}: Community {comm}")
            if len(communities) > 10:
                print(f"  ... and {len(communities) - 10} more")

        return 0
    except Exception as e:
        print(f"Error detecting communities: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_centrality(args: argparse.Namespace) -> int:
    """Compute node centrality measures.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    try:
        print(f"Loading network from {args.input}...")
        network = _load_network(args.input)

        print(f"Computing {args.measure} centrality...")

        G = network.core_network.to_undirected() if network.directed else network.core_network

        if args.measure == "degree":
            centrality = dict(G.degree())
        elif args.measure == "betweenness":
            centrality = nx.betweenness_centrality(G)
        elif args.measure == "closeness":
            centrality = nx.closeness_centrality(G)
        elif args.measure == "eigenvector":
            try:
                centrality = nx.eigenvector_centrality(G, max_iter=1000)
            except:
                print("Warning: Eigenvector centrality failed, using degree instead")
                centrality = dict(G.degree())
        elif args.measure == "pagerank":
            centrality = nx.pagerank(G)

        # Convert to serializable format
        centrality_data = {str(node): float(score) for node, score in centrality.items()}

        # Sort by centrality
        sorted_nodes = sorted(centrality_data.items(), key=lambda x: x[1], reverse=True)

        print(f"\nTop {min(args.top or 10, len(sorted_nodes))} nodes by {args.measure} centrality:")
        for node, score in sorted_nodes[: args.top or 10]:
            print(f"  {node}: {score:.6f}")

        output_data = {
            "measure": args.measure,
            "centrality": centrality_data,
            "top_nodes": [
                {"node": node, "score": score}
                for node, score in sorted_nodes[: args.top or len(sorted_nodes)]
            ],
        }

        if args.output:
            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2)
            print(f"\nCentrality scores saved to {args.output}")

        return 0
    except Exception as e:
        print(f"Error computing centrality: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_stats(args: argparse.Namespace) -> int:
    """Compute multilayer network statistics.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    try:
        print(f"Loading network from {args.input}...")
        network = _load_network(args.input)

        from py3plex.algorithms.statistics import multilayer_statistics as mls

        stats = {}
        layers = network.get_layers()[0] if isinstance(network.get_layers(), tuple) else list(network.get_layers())

        print(f"Computing multilayer statistics...")

        if args.measure in ["all", "density", "layer_density"] and layers:
            stats["layer_densities"] = {}
            for layer in layers:
                try:
                    density = mls.layer_density(network, layer)
                    stats["layer_densities"][layer] = float(density)
                except Exception as e:
                    print(f"Warning: Could not compute density for layer {layer}: {e}")

        if args.measure in ["all", "clustering"]:
            try:
                G_undirected = network.core_network.to_undirected()
                stats["clustering_coefficient"] = float(nx.average_clustering(G_undirected))
            except Exception as e:
                print(f"Warning: Could not compute clustering: {e}")

        if args.measure in ["all", "node_activity"]:
            try:
                # Sample some nodes
                sample_nodes = list(network.core_network.nodes())[:10]
                stats["node_activity_sample"] = {}
                for node in sample_nodes:
                    # Extract base node name (remove layer suffix)
                    base_node = str(node).split("---")[0] if "---" in str(node) else str(node)
                    activity = mls.node_activity(network, base_node)
                    stats["node_activity_sample"][str(node)] = float(activity)
            except Exception as e:
                print(f"Warning: Could not compute node activity: {e}")

        if args.measure in ["all", "versatility"]:
            try:
                versatility = mls.versatility_centrality(network, centrality_type="degree")
                # Sample top nodes
                sorted_vers = sorted(versatility.items(), key=lambda x: x[1], reverse=True)[:10]
                stats["versatility_top10"] = {str(k): float(v) for k, v in sorted_vers}
            except Exception as e:
                print(f"Warning: Could not compute versatility: {e}")

        if args.measure in ["all", "edge_overlap"] and len(layers) >= 2:
            try:
                stats["edge_overlap"] = {}
                for i, layer_i in enumerate(layers[:3]):  # Limit to first 3 layers
                    for layer_j in layers[i + 1 : 3]:
                        overlap = mls.edge_overlap(network, layer_i, layer_j)
                        stats["edge_overlap"][f"{layer_i}-{layer_j}"] = float(overlap)
            except Exception as e:
                print(f"Warning: Could not compute edge overlap: {e}")

        # Print results
        print("\nMultilayer Network Statistics:")
        if "layer_densities" in stats:
            print("  Layer Densities:")
            for layer, density in stats["layer_densities"].items():
                print(f"    {layer}: {density:.4f}")

        if "clustering_coefficient" in stats:
            print(f"  Clustering Coefficient: {stats['clustering_coefficient']:.4f}")

        if "node_activity_sample" in stats:
            print(f"  Node Activity (sample):")
            for node, activity in list(stats["node_activity_sample"].items())[:5]:
                print(f"    {node}: {activity:.4f}")

        if "versatility_top10" in stats:
            print(f"  Versatility Centrality (top 10):")
            for node, score in list(stats["versatility_top10"].items())[:5]:
                print(f"    {node}: {score:.4f}")

        if "edge_overlap" in stats:
            print(f"  Edge Overlap:")
            for pair, overlap in stats["edge_overlap"].items():
                print(f"    {pair}: {overlap:.4f}")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(stats, f, indent=2)
            print(f"\nStatistics saved to {args.output}")

        return 0
    except Exception as e:
        print(f"Error computing statistics: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_visualize(args: argparse.Namespace) -> int:
    """Visualize the multilayer network.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    try:
        print(f"Loading network from {args.input}...")
        network = _load_network(args.input)

        print(f"Generating visualization with {args.layout} layout...")

        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt

        if args.layout == "multilayer":
            from py3plex.visualization import multilayer

            fig = plt.figure(figsize=(args.width, args.height))
            multilayer.draw_multilayer_default(
                [network],
                display=False,
                show_legend=True,
            )
        else:
            # Use NetworkX layouts
            if args.layout == "spring":
                pos = nx.spring_layout(network.core_network)
            elif args.layout == "circular":
                pos = nx.circular_layout(network.core_network)
            elif args.layout == "kamada_kawai":
                pos = nx.kamada_kawai_layout(network.core_network)

            fig = plt.figure(figsize=(args.width, args.height))
            nx.draw(
                network.core_network,
                pos,
                node_size=100,
                node_color="lightblue",
                edge_color="gray",
                alpha=0.7,
                with_labels=False,
            )

        plt.savefig(args.output, dpi=150, bbox_inches="tight")
        plt.close()

        print(f"Visualization saved to {args.output}")
        return 0
    except Exception as e:
        print(f"Error creating visualization: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_aggregate(args: argparse.Namespace) -> int:
    """Aggregate multilayer network into single layer.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    try:
        print(f"Loading network from {args.input}...")
        network = _load_network(args.input)

        print(f"Aggregating layers using {args.method} method...")

        # Aggregate the network
        aggregated = network.aggregate_layers(method=args.method)

        # Save aggregated network
        output_path = Path(args.output)
        if output_path.suffix == ".graphml":
            nx.write_graphml(aggregated, str(output_path))
        elif output_path.suffix == ".gexf":
            nx.write_gexf(aggregated, str(output_path))
        elif output_path.suffix == ".gpickle":
            nx.write_gpickle(aggregated, str(output_path))
        else:
            print(f"Warning: Unsupported format, using GraphML")
            nx.write_graphml(aggregated, str(output_path.with_suffix(".graphml")))

        print(f"Aggregated network saved to {args.output}")
        print(f"  Nodes: {aggregated.number_of_nodes()}")
        print(f"  Edges: {aggregated.number_of_edges()}")

        return 0
    except Exception as e:
        print(f"Error aggregating network: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def cmd_convert(args: argparse.Namespace) -> int:
    """Convert network between different formats.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    try:
        print(f"Loading network from {args.input}...")
        network = _load_network(args.input)

        output_path = Path(args.output)
        print(f"Converting to {output_path.suffix} format...")

        if output_path.suffix == ".graphml":
            nx.write_graphml(network.core_network, str(output_path))
        elif output_path.suffix == ".gexf":
            nx.write_gexf(network.core_network, str(output_path))
        elif output_path.suffix == ".gpickle":
            nx.write_gpickle(network.core_network, str(output_path))
        elif output_path.suffix == ".json":
            # Custom JSON export with network info
            data = {
                "nodes": [str(n) for n in network.core_network.nodes()],
                "edges": [
                    {"source": str(u), "target": str(v)}
                    for u, v in network.core_network.edges()
                ],
                "layers": network.get_layers()[0] if isinstance(network.get_layers(), tuple) else list(network.get_layers()),
                "directed": network.directed,
            }
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)
        else:
            print(f"Error: Unsupported output format '{output_path.suffix}'", file=sys.stderr)
            print("Supported formats: .graphml, .gexf, .gpickle, .json", file=sys.stderr)
            return 1

        print(f"Network converted and saved to {args.output}")
        return 0
    except Exception as e:
        print(f"Error converting network: {e}", file=sys.stderr)
        return 1


def main(argv=None) -> int:
    """Main entry point for the CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    # Dispatch to command handlers
    command_handlers = {
        "create": cmd_create,
        "load": cmd_load,
        "community": cmd_community,
        "centrality": cmd_centrality,
        "stats": cmd_stats,
        "visualize": cmd_visualize,
        "aggregate": cmd_aggregate,
        "convert": cmd_convert,
    }

    handler = command_handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"Error: Unknown command '{args.command}'", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
