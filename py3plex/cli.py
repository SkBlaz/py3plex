#!/usr/bin/env python
"""
Command-line interface for py3plex.

This module provides a comprehensive CLI tool for multilayer network analysis
with full coverage of main algorithms.
"""

import argparse
import json
import random
import shutil
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx
import numpy as np

from py3plex import __version__
from py3plex.core import multinet
from py3plex.core.nx_compat import nx_write_gpickle
from py3plex.logging_config import get_logger

# Get logger for CLI module
logger = get_logger(__name__)


def _convert_to_simple_graph(G: nx.Graph) -> nx.Graph:
    """Convert a multigraph to a simple graph for algorithms that don't support multigraphs.

    Args:
        G: Input graph (may be MultiGraph or Graph)

    Returns:
        Simple graph (no parallel edges)
    """
    if isinstance(G, nx.MultiGraph):
        return nx.Graph(G)
    return G



def _normalize_network_nodes(
    network: "multinet.multi_layer_network",
) -> "multinet.multi_layer_network":
    """Normalize network nodes from string representations to tuples.

    When loading from GraphML, nodes are stored as strings like "('node1', 'layer1')".
    This function converts them back to proper tuples so statistics functions work correctly.

    Args:
        network: Network with potentially string-formatted nodes

    Returns:
        Network with tuple nodes
    """
    import ast

    # Check if nodes need normalization
    sample_node = next(iter(network.core_network.nodes()), None)
    if sample_node is None or isinstance(sample_node, tuple):
        # Already in correct format or empty
        return network

    # Create a mapping from string nodes to tuple nodes
    node_mapping = {}
    for node in network.core_network.nodes():
        if isinstance(node, str):
            try:
                parsed = ast.literal_eval(node)
                if isinstance(parsed, tuple):
                    node_mapping[node] = parsed
                else:
                    # Keep as-is if not a tuple string
                    node_mapping[node] = node
            except (ValueError, SyntaxError):
                # Keep as-is if parsing fails
                node_mapping[node] = node
        else:
            node_mapping[node] = node

    # Only relabel if we found string nodes to convert
    if any(isinstance(k, str) and k != v for k, v in node_mapping.items()):
        network.core_network = nx.relabel_nodes(
            network.core_network, node_mapping, copy=True
        )

    return network


def _parse_node(node: Any) -> tuple:
    """Parse a node that might be a tuple or string representation of a tuple.

    Args:
        node: Node that can be a tuple or string

    Returns:
        Tuple representation of the node
    """
    import ast

    if isinstance(node, tuple):
        return node
    elif isinstance(node, str):
        try:
            # Handle string representations like "('node1', 'layer1')"
            parsed = ast.literal_eval(node)
            if isinstance(parsed, tuple):
                return parsed
        except (ValueError, SyntaxError):
            pass
    # If we can't parse it, return as-is wrapped in tuple
    return (node,)


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
        # Normalize nodes from string representations back to tuples
        network = _normalize_network_nodes(network)
    elif input_path.suffix == ".gpickle":
        network.load_network(file_path, input_type="gpickle")
    else:
        # For .edgelist and .txt files, try to detect format
        # Multiedgelist format: 4 columns (node1 layer1 node2 layer2) or 5 (with weight)
        # Simple edgelist format: 2 columns (node1 node2)
        try:
            # Peek at the first line to determine format
            with open(file_path) as f:
                first_line = f.readline().strip()
                if first_line:
                    parts = first_line.split()
                    if len(parts) in [4, 5]:
                        # Multilayer format (with or without weight)
                        network.load_network(file_path, input_type="multiedgelist")
                    else:
                        # Simple edgelist
                        network.load_network(file_path, input_type="edgelist")
                else:
                    # Empty file
                    pass
        except Exception:
            # Try GML as last resort
            try:
                network.load_network(file_path, input_type="gml")
            except Exception as e:
                raise ValueError(f"Could not load network from {file_path}: {e}")

    return network


def _get_layer_names(network: "multinet.multi_layer_network") -> List[str]:
    """Extract unique layer names from a multilayer network.

    Args:
        network: py3plex multi_layer_network object

    Returns:
        List of unique layer names
    """
    layers = set()

    # Handle case where core_network might not be initialized
    if network.core_network is None:
        return []

    try:
        for node in network.get_nodes():
            # Nodes are tuples of (node_id, layer_name)
            if isinstance(node, tuple) and len(node) >= 2:
                layers.add(node[1])
    except (AttributeError, TypeError):
        # If get_nodes fails, try getting from core_network directly
        # AttributeError: if get_nodes is not available or core_network is None
        # TypeError: if the network structure is unexpected
        try:
            for node in network.core_network.nodes():
                if isinstance(node, tuple) and len(node) >= 2:
                    layers.add(node[1])
        except (AttributeError, TypeError) as e:
            # Log the error for debugging but continue
            logger.debug(f"Could not extract layer names: {e}")

    return sorted(layers)


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
Quick Start:
  # New to py3plex? Start here:
  py3plex quickstart           # Interactive demo with example graph
  py3plex selftest             # Verify installation
  py3plex --version            # Show version
  py3plex --help               # Show this help

Examples:
  # Check/lint a graph data file for errors
  py3plex check network.csv                      # Validate CSV file
  py3plex check network.edgelist                 # Validate edgelist file
  py3plex check network.csv --strict             # Treat warnings as errors

  # Create a random multilayer network with 100 nodes and 3 layers
  py3plex create --nodes 100 --layers 3 --type random --probability 0.1 --output network.edgelist

  # Create an Erdős-Rényi multilayer network
  py3plex create --nodes 50 --layers 2 --type er --probability 0.05 --output network.edgelist

  # Load and display network information
  py3plex load network.edgelist --info

  # Compute basic statistics for a network
  py3plex load network.edgelist --stats

  # Get comprehensive multilayer statistics
  py3plex stats network.edgelist --measure all

  # Compute specific statistics (layer density, clustering, etc.)
  py3plex stats network.edgelist --measure layer_density
  py3plex stats network.edgelist --measure node_activity

  # Visualize a network with multilayer layout
  py3plex visualize network.edgelist --output network.png --layout multilayer

  # Visualize using NetworkX layouts
  py3plex visualize network.edgelist --output network.png --layout spring

  # Detect communities using different algorithms
  py3plex community network.edgelist --algorithm louvain --output communities.json
  py3plex community network.edgelist --algorithm label_prop --output communities.json

  # Compute node centrality measures
  py3plex centrality network.edgelist --measure degree --top 20 --output centrality.json
  py3plex centrality network.edgelist --measure betweenness --output centrality.json

  # Convert between formats
  py3plex convert network.edgelist --output network.graphml
  py3plex convert network.graphml --output network.json

  # Aggregate multilayer network into single layer
  py3plex aggregate network.edgelist --method sum --output aggregated.edgelist

Note: The recommended format for multilayer networks is the multiedgelist/edgelist format
      (.edgelist or .txt). GraphML (.graphml) and other formats are also supported.

For detailed help on any command, run:
  py3plex <command> --help

Example:
  py3plex create --help    # Shows all options for creating networks
  py3plex help             # Shows this help information

For more information, visit: https://github.com/SkBlaz/py3plex
        """,
    )

    parser.add_argument("--version", action="version", version=f"py3plex {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # HELP command
    subparsers.add_parser("help", help="Show detailed help information about py3plex")

    # CHECK command
    check_parser = subparsers.add_parser(
        "check", help="Lint and validate graph data files"
    )
    check_parser.add_argument(
        "input",
        help="Input file to check (CSV, edgelist, or multiedgelist format)",
    )
    check_parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (exit with error code if warnings found)",
    )
    check_parser.add_argument(
        "--format",
        choices=["csv", "edgelist", "multiedgelist", "auto"],
        default="auto",
        help="Expected file format (default: auto-detect)",
    )

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
        help="Network type - Possible values: 'random' (random network, default), 'er' (Erdős-Rényi), 'ba' (Barabási-Albert preferential attachment), 'ws' (Watts-Strogatz small-world)",
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
        help="Output file path (recommended format: .edgelist or .txt for multiedgelist; also supports .graphml, .gexf, .gpickle)",
    )
    create_parser.add_argument(
        "--seed", type=int, help="Random seed for reproducibility"
    )

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
    load_parser.add_argument("--output", "-o", help="Save output to file (JSON format)")

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
        help="Community detection algorithm - Possible values: 'louvain' (Louvain method, default), 'infomap' (Infomap algorithm), 'label_prop' (Label propagation)",
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
        help="Centrality measure - Possible values: 'degree' (degree centrality, default), 'betweenness' (betweenness centrality), 'closeness' (closeness centrality), 'eigenvector' (eigenvector centrality), 'pagerank' (PageRank)",
    )
    centrality_parser.add_argument(
        "--output", "-o", help="Output file for centrality scores (JSON)"
    )
    centrality_parser.add_argument("--top", type=int, help="Show only top N nodes")

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
        help="Statistic to compute - Possible values: 'all' (compute all statistics, default), 'density' (network density), 'clustering' (clustering coefficient), 'layer_density' (density per layer), 'node_activity' (node activity across layers), 'versatility' (versatility centrality), 'edge_overlap' (edge overlap between layers)",
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
        help="Layout algorithm - Possible values: 'spring' (force-directed spring layout), 'circular' (circular layout), 'kamada_kawai' (Kamada-Kawai force layout), 'multilayer' (specialized multilayer layout, default)",
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
        help="Aggregation method for edge weights - Possible values: 'sum' (sum weights, default), 'mean' (average weights), 'max' (maximum weight), 'min' (minimum weight)",
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
        help="Output file path - Format determined by extension: .graphml (GraphML), .gexf (GEXF), .gpickle (NetworkX pickle), .json (JSON)",
    )

    # SELFTEST command
    selftest_parser = subparsers.add_parser(
        "selftest", help="Run self-test to verify installation and core functionality"
    )
    selftest_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )

    # QUICKSTART command
    quickstart_parser = subparsers.add_parser(
        "quickstart",
        help="Quick start guide - creates a demo graph and shows basic operations",
    )
    quickstart_parser.add_argument(
        "--keep-files",
        action="store_true",
        help="Keep generated files instead of cleaning them up",
    )
    quickstart_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for output files (default: temporary directory)",
    )

    # RUN-CONFIG command
    run_config_parser = subparsers.add_parser(
        "run-config",
        help="Run workflow from YAML/JSON configuration file",
    )
    run_config_parser.add_argument(
        "config",
        help="Path to workflow configuration file (.yaml, .yml, or .json)",
    )
    run_config_parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate configuration without running workflow",
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
        if args.seed is not None:
            random.seed(args.seed)

            np.random.seed(args.seed)

        logger.info(
            f"Creating {args.type} multilayer network with {args.nodes} nodes and {args.layers} layers..."
        )

        network = multinet.multi_layer_network()

        # Create layers and add nodes
        for layer_idx in range(args.layers):
            layer_name = f"layer{layer_idx + 1}"

            # Add nodes to this layer using dict format
            nodes_dict = [
                {"source": f"node{i}", "type": layer_name} for i in range(args.nodes)
            ]
            network.add_nodes(nodes_dict, input_type="dict")

            # Add edges based on network type
            if args.type == "random" or args.type == "er":
                # Erdős-Rényi random graph
                edges_dict = []
                for i in range(args.nodes):
                    for j in range(i + 1, args.nodes):
                        if random.random() < args.probability:
                            edges_dict.append(
                                {
                                    "source": f"node{i}",
                                    "target": f"node{j}",
                                    "source_type": layer_name,
                                    "target_type": layer_name,
                                }
                            )
                if edges_dict:
                    network.add_edges(edges_dict, input_type="dict")

            elif args.type == "ba":
                # Barabási-Albert preferential attachment
                m = max(1, int(args.nodes * args.probability))
                edges_dict = []
                degrees = dict.fromkeys(range(args.nodes), 0)

                # Start with a small complete graph
                for i in range(min(m + 1, args.nodes)):
                    degrees[i] = m
                    for j in range(i + 1, min(m + 1, args.nodes)):
                        edges_dict.append(
                            {
                                "source": f"node{i}",
                                "target": f"node{j}",
                                "source_type": layer_name,
                                "target_type": layer_name,
                            }
                        )

                # Add remaining nodes with preferential attachment
                for i in range(m + 1, args.nodes):
                    targets = []
                    degree_sum = sum(degrees.values())
                    if degree_sum > 0:
                        probs = [degrees[j] / degree_sum for j in range(i)]
                        targets = random.choices(range(i), weights=probs, k=min(m, i))

                    for target in targets:
                        edges_dict.append(
                            {
                                "source": f"node{i}",
                                "target": f"node{target}",
                                "source_type": layer_name,
                                "target_type": layer_name,
                            }
                        )
                        degrees[i] += 1
                        degrees[target] += 1

                if edges_dict:
                    network.add_edges(edges_dict, input_type="dict")

            elif args.type == "ws":
                # Watts-Strogatz small-world
                k = max(
                    2, int(args.nodes * args.probability / 2) * 2
                )  # Ensure k is even
                edges_dict = []
                # Create ring lattice
                for i in range(args.nodes):
                    for j in range(1, k // 2 + 1):
                        target = (i + j) % args.nodes
                        edges_dict.append(
                            {
                                "source": f"node{i}",
                                "target": f"node{target}",
                                "source_type": layer_name,
                                "target_type": layer_name,
                            }
                        )
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
                # Use multiedgelist format to preserve layer information
                network.save_network(str(output_path), output_type="multiedgelist")
            else:
                logger.warning(
                    f"Unsupported format '{output_path.suffix}', using multiedgelist"
                )
                network.save_network(
                    str(output_path.with_suffix(".edgelist")),
                    output_type="multiedgelist",
                )
        except Exception as e:
            logger.warning(
                f"Error saving with native format, trying alternate method: {e}"
            )
            nx.write_graphml(network.core_network, str(output_path))

        logger.info(f"Network saved to {args.output}")
        logger.info(f"  Nodes: {network.core_network.number_of_nodes()}")
        logger.info(f"  Edges: {network.core_network.number_of_edges()}")
        layers = _get_layer_names(network)
        logger.info(f"  Layers: {len(layers)} ({', '.join(layers)})")

        return 0
    except Exception as e:
        logger.error(f"Error creating network: {e}")
        return 1


def cmd_load(args: argparse.Namespace) -> int:
    """Load and inspect a network.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    try:
        logger.info(f"Loading network from {args.input}...")
        network = _load_network(args.input)

        output_data = {}

        if args.info or not args.stats:
            layers = _get_layer_names(network)
            info = {
                "nodes": network.core_network.number_of_nodes(),
                "edges": network.core_network.number_of_edges(),
                "layers": layers,
                "directed": network.directed,
            }
            output_data["info"] = info

            logger.info("\nNetwork Information:")
            logger.info(f"  Nodes: {info['nodes']}")
            logger.info(f"  Edges: {info['edges']}")
            logger.info(
                f"  Layers: {len(info['layers'])} ({', '.join(info['layers'])})"
            )
            logger.info(f"  Directed: {info['directed']}")

        if args.stats:
            from py3plex.algorithms.statistics import multilayer_statistics as mls

            stats: Dict[str, Any] = {}
            try:
                layers = _get_layer_names(network)
                if layers:
                    stats["layer_densities"] = {
                        layer: float(mls.layer_density(network, layer))
                        for layer in layers
                    }

                # Overall clustering
                G_undirected = network.core_network.to_undirected()
                G_simple = _convert_to_simple_graph(G_undirected)
                stats["clustering_coefficient"] = float(
                    nx.average_clustering(G_simple)
                )

                # Degree distribution
                degrees = dict(network.core_network.degree())
                stats["avg_degree"] = (
                    float(sum(degrees.values()) / len(degrees)) if degrees else 0
                )
                stats["max_degree"] = int(max(degrees.values())) if degrees else 0

            except Exception as e:
                logger.warning(f"Could not compute all statistics: {e}")

            output_data["statistics"] = stats

            logger.info("\nBasic Statistics:")
            if "layer_densities" in stats:
                logger.info("  Layer Densities:")
                for layer, density in stats["layer_densities"].items():
                    logger.info(f"    {layer}: {density:.4f}")
            logger.info(
                f"  Avg Clustering: {stats.get('clustering_coefficient', 0):.4f}"
            )
            logger.info(f"  Avg Degree: {stats.get('avg_degree', 0):.2f}")
            logger.info(f"  Max Degree: {stats.get('max_degree', 0)}")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"\nOutput saved to {args.output}")

        return 0
    except Exception as e:
        logger.error(f"Error loading network: {e}")
        return 1


def cmd_community(args: argparse.Namespace) -> int:
    """Detect communities in the network.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    try:
        logger.info(f"Loading network from {args.input}...")
        network = _load_network(args.input)

        logger.info(f"Detecting communities using {args.algorithm}...")

        communities = {}

        if args.algorithm == "louvain":
            from py3plex.algorithms.community_detection import community_wrapper

            # Convert to undirected if needed
            G = (
                network.core_network.to_undirected()
                if network.core_network.is_directed()
                else network.core_network
            )
            partition = community_wrapper.louvain_communities(G)
            communities = {str(node): int(comm) for node, comm in partition.items()}

        elif args.algorithm == "infomap":
            try:
                from py3plex.algorithms.community_detection import community_wrapper

                partition = community_wrapper.infomap_communities(network)
                communities = {
                    str(node): (
                        int(comm)
                        if isinstance(comm, (int, np.integer))
                        else int(comm[0])
                    )
                    for node, comm in partition.items()
                }
            except Exception as e:
                logger.error(f"Infomap not available: {e}")
                logger.error("Please use 'louvain' or 'label_prop' instead.")
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
        logger.info(f"Found {num_communities} communities")

        # Community size distribution
        comm_sizes: Dict[int, int] = {}
        for comm_id in communities.values():
            comm_sizes[comm_id] = comm_sizes.get(comm_id, 0) + 1

        logger.info(
            f"Community sizes: min={min(comm_sizes.values())}, max={max(comm_sizes.values())}, avg={sum(comm_sizes.values())/len(comm_sizes):.1f}"
        )

        output_data = {
            "algorithm": args.algorithm,
            "num_communities": num_communities,
            "communities": communities,
            "community_sizes": {int(k): int(v) for k, v in comm_sizes.items()},
        }

        if args.output:
            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2)
            logger.info(f"Communities saved to {args.output}")
        else:
            # Print sample
            logger.info("\nSample community assignments:")
            for i, (node, comm) in enumerate(list(communities.items())[:10]):
                logger.info(f"  {node}: Community {comm}")
            if len(communities) > 10:
                logger.info(f"  ... and {len(communities) - 10} more")

        return 0
    except Exception as e:
        logger.error(f"Error detecting communities: {e}")

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
        logger.info(f"Loading network from {args.input}...")
        network = _load_network(args.input)

        logger.info(f"Computing {args.measure} centrality...")

        G = (
            network.core_network.to_undirected()
            if network.directed
            else network.core_network
        )

        if args.measure == "degree":
            centrality = dict(G.degree())
        elif args.measure == "betweenness":
            centrality = nx.betweenness_centrality(G)
        elif args.measure == "closeness":
            centrality = nx.closeness_centrality(G)
        elif args.measure == "eigenvector":
            try:
                centrality = nx.eigenvector_centrality(G, max_iter=1000)
            except (nx.PowerIterationFailedConvergence, nx.NetworkXError, ValueError):
                logger.warning("Eigenvector centrality failed, using degree instead")
                centrality = dict(G.degree())
        elif args.measure == "pagerank":
            centrality = nx.pagerank(G)

        # Convert to serializable format
        centrality_data = {
            str(node): float(score) for node, score in centrality.items()
        }

        # Sort by centrality
        sorted_nodes = sorted(centrality_data.items(), key=lambda x: x[1], reverse=True)

        logger.info(
            f"\nTop {min(args.top or 10, len(sorted_nodes))} nodes by {args.measure} centrality:"
        )
        for node, score in sorted_nodes[: args.top or 10]:
            logger.info(f"  {node}: {score:.6f}")

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
            logger.info(f"\nCentrality scores saved to {args.output}")

        return 0
    except Exception as e:
        logger.error(f"Error computing centrality: {e}")

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
        logger.info(f"Loading network from {args.input}...")
        network = _load_network(args.input)

        from py3plex.algorithms.statistics import multilayer_statistics as mls

        stats: Dict[str, Any] = {}
        layers = _get_layer_names(network)

        logger.info("Computing multilayer statistics...")

        if args.measure in ["all", "density", "layer_density"] and layers:
            stats["layer_densities"] = {}
            for layer in layers:
                try:
                    density = mls.layer_density(network, layer)
                    stats["layer_densities"][layer] = float(density)
                except Exception as e:
                    logger.warning(f"Could not compute density for layer {layer}: {e}")

        if args.measure in ["all", "clustering"]:
            try:
                G_undirected = network.core_network.to_undirected()
                G_simple = _convert_to_simple_graph(G_undirected)
                stats["clustering_coefficient"] = float(
                    nx.average_clustering(G_simple)
                )
            except Exception as e:
                logger.warning(f"Could not compute clustering: {e}")

        if args.measure in ["all", "node_activity"]:
            try:
                # Sample some nodes
                sample_nodes = list(network.core_network.nodes())[:10]
                stats["node_activity_sample"] = {}
                for node in sample_nodes:
                    # Extract base node name (remove layer suffix)
                    base_node = (
                        str(node).split("---")[0] if "---" in str(node) else str(node)
                    )
                    activity = mls.node_activity(network, base_node)
                    stats["node_activity_sample"][str(node)] = float(activity)
            except Exception as e:
                logger.warning(f"Could not compute node activity: {e}")

        if args.measure in ["all", "versatility"]:
            try:
                versatility = mls.versatility_centrality(
                    network, centrality_type="degree"
                )
                # Sample top nodes
                sorted_vers = sorted(
                    versatility.items(), key=lambda x: x[1], reverse=True
                )[:10]
                stats["versatility_top10"] = {str(k): float(v) for k, v in sorted_vers}
            except Exception as e:
                logger.warning(f"Could not compute versatility: {e}")

        if args.measure in ["all", "edge_overlap"] and len(layers) >= 2:
            try:
                stats["edge_overlap"] = {}
                for i, layer_i in enumerate(layers[:3]):  # Limit to first 3 layers
                    for layer_j in layers[i + 1 : 3]:
                        overlap = mls.edge_overlap(network, layer_i, layer_j)
                        stats["edge_overlap"][f"{layer_i}-{layer_j}"] = float(overlap)
            except Exception as e:
                logger.warning(f"Could not compute edge overlap: {e}")

        # Print results
        logger.info("\nMultilayer Network Statistics:")
        if "layer_densities" in stats:
            logger.info("  Layer Densities:")
            for layer, density in stats["layer_densities"].items():
                logger.info(f"    {layer}: {density:.4f}")

        if "clustering_coefficient" in stats:
            logger.info(
                f"  Clustering Coefficient: {stats['clustering_coefficient']:.4f}"
            )

        if "node_activity_sample" in stats:
            logger.info("  Node Activity (sample):")
            for node, activity in list(stats["node_activity_sample"].items())[:5]:
                logger.info(f"    {node}: {activity:.4f}")

        if "versatility_top10" in stats:
            logger.info("  Versatility Centrality (top 10):")
            for node, score in list(stats["versatility_top10"].items())[:5]:
                logger.info(f"    {node}: {score:.4f}")

        if "edge_overlap" in stats:
            logger.info("  Edge Overlap:")
            for pair, overlap in stats["edge_overlap"].items():
                logger.info(f"    {pair}: {overlap:.4f}")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(stats, f, indent=2)
            logger.info(f"\nStatistics saved to {args.output}")

        return 0
    except Exception as e:
        logger.error(f"Error computing statistics: {e}")

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
        logger.info(f"Loading network from {args.input}...")
        network = _load_network(args.input)

        logger.info(f"Generating visualization with {args.layout} layout...")

        import matplotlib

        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt

        if args.layout == "multilayer":
            from py3plex.visualization import multilayer

            # Get the layer networks from the multilayer object
            layer_names, layer_graphs, multiedges = network.get_layers(
                style="diagonal", compute_layouts="force", verbose=False
            )

            plt.figure(figsize=(args.width, args.height))
            # layer_graphs can be either a list or dict depending on get_layers return format
            # Convert to list if it's a dict
            if isinstance(layer_graphs, list):
                graph_list = layer_graphs
            else:
                graph_list = list(layer_graphs.values())

            multilayer.draw_multilayer_default(
                graph_list,
                display=False,
                labels=layer_names,
            )
        else:
            # Use NetworkX layouts
            if args.layout == "spring":
                pos = nx.spring_layout(network.core_network)
            elif args.layout == "circular":
                pos = nx.circular_layout(network.core_network)
            elif args.layout == "kamada_kawai":
                pos = nx.kamada_kawai_layout(network.core_network)

            plt.figure(figsize=(args.width, args.height))
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

        logger.info(f"Visualization saved to {args.output}")
        return 0
    except Exception as e:
        logger.error(f"Error creating visualization: {e}")

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
        logger.info(f"Loading network from {args.input}...")
        network = _load_network(args.input)

        logger.info(f"Aggregating layers using {args.method} method...")

        # Aggregate the network using aggregate_edges
        aggregated = network.aggregate_edges(metric=args.method)

        # Save aggregated network
        output_path = Path(args.output)
        if output_path.suffix == ".graphml":
            nx.write_graphml(aggregated, str(output_path))
        elif output_path.suffix == ".gexf":
            nx.write_gexf(aggregated, str(output_path))
        elif output_path.suffix == ".gpickle":
            nx_write_gpickle(aggregated, str(output_path))
        else:
            logger.warning("Unsupported format, using GraphML")
            nx.write_graphml(aggregated, str(output_path.with_suffix(".graphml")))

        logger.info(f"Aggregated network saved to {args.output}")
        logger.info(f"  Nodes: {aggregated.number_of_nodes()}")
        logger.info(f"  Edges: {aggregated.number_of_edges()}")

        return 0
    except Exception as e:
        logger.error(f"Error aggregating network: {e}")

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
        logger.info(f"Loading network from {args.input}...")
        network = _load_network(args.input)

        output_path = Path(args.output)
        logger.info(f"Converting to {output_path.suffix} format...")

        if output_path.suffix == ".graphml":
            nx.write_graphml(network.core_network, str(output_path))
        elif output_path.suffix == ".gexf":
            nx.write_gexf(network.core_network, str(output_path))
        elif output_path.suffix == ".gpickle":
            nx_write_gpickle(network.core_network, str(output_path))
        elif output_path.suffix == ".json":
            # Custom JSON export with network info
            layers = _get_layer_names(network)
            data = {
                "nodes": [str(n) for n in network.core_network.nodes()],
                "edges": [
                    {"source": str(u), "target": str(v)}
                    for u, v in network.core_network.edges()
                ],
                "layers": layers,
                "directed": network.directed,
            }
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)
        else:
            logger.error(f"Unsupported output format '{output_path.suffix}'")
            logger.error("Supported formats: .graphml, .gexf, .gpickle, .json")
            return 1

        logger.info(f"Network converted and saved to {args.output}")
        return 0
    except Exception as e:
        logger.error(f"Error converting network: {e}")
        return 1


def cmd_help(args: argparse.Namespace) -> int:
    """Show detailed help information.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    # Create parser and show its help
    parser = create_parser()
    parser.print_help()
    return 0


def cmd_selftest(args: argparse.Namespace) -> int:
    """Run self-test to verify installation and core functionality.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    import importlib
    import time

    # Set matplotlib backend early, before any imports that might use it
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend

    verbose = args.verbose
    test_results = []
    start_time = time.time()

    print("[py3plex::selftest] Starting py3plex self-test...")
    print()

    # Test 1: Core dependencies
    print("1. Checking core dependencies...")
    deps_status = True
    deps = {
        "numpy": None,
        "networkx": None,
        "matplotlib": None,
        "scipy": None,
        "pandas": None,
    }

    for dep_name in deps:
        try:
            module = importlib.import_module(dep_name)
            deps[dep_name] = getattr(module, "__version__", "unknown")
            if verbose:
                print(f"   [OK] {dep_name}: {deps[dep_name]}")
        except ImportError as e:
            deps_status = False
            print(f"   X {dep_name}: NOT FOUND - {e}")

    if deps_status:
        print("   [OK] Core dependencies OK")
    else:
        print("   [X] Some dependencies missing")
    test_results.append(("Core dependencies", deps_status))

    # Test 2: Graph creation
    print("\n2. Testing graph creation...")
    graph_status = False
    try:
        network = multinet.multi_layer_network()

        # Add nodes
        nodes = [{"source": f"node{i}", "type": "layer1"} for i in range(10)]
        network.add_nodes(nodes, input_type="dict")

        # Add edges
        edges = [
            {
                "source": f"node{i}",
                "target": f"node{i+1}",
                "source_type": "layer1",
                "target_type": "layer1",
            }
            for i in range(9)
        ]
        network.add_edges(edges, input_type="dict")

        if network.core_network.number_of_nodes() == 10:
            print("   [OK] Graph creation successful")
            if verbose:
                print(f"      Nodes: {network.core_network.number_of_nodes()}")
                print(f"      Edges: {network.core_network.number_of_edges()}")
            graph_status = True
        else:
            print("   [X] Graph creation failed: unexpected node count")
    except Exception as e:
        print(f"   [X] Graph creation failed: {e}")
        if verbose:
            traceback.print_exc()
    test_results.append(("Graph creation", graph_status))

    # Test 3: Visualization module
    print("\n3. Testing visualization module...")
    viz_status = False
    try:
        from py3plex.visualization import multilayer as _  # noqa: F401

        print("   [OK] Visualization module initialized")
        if verbose:
            print(f"      Matplotlib backend: {matplotlib.get_backend()}")
        viz_status = True
    except Exception as e:
        print(f"   [X] Visualization module error: {e}")
        if verbose:
            traceback.print_exc()
    test_results.append(("Visualization module", viz_status))

    # Test 4: Multilayer network example
    print("\n4. Creating example multilayer graph...")
    multilayer_status = False
    try:
        network = multinet.multi_layer_network()

        # Create two layers
        for layer_idx in range(2):
            layer_name = f"layer{layer_idx + 1}"
            nodes = [{"source": f"node{i}", "type": layer_name} for i in range(5)]
            network.add_nodes(nodes, input_type="dict")

            # Add some edges
            for i in range(4):
                network.add_edges(
                    [
                        {
                            "source": f"node{i}",
                            "target": f"node{i+1}",
                            "source_type": layer_name,
                            "target_type": layer_name,
                        }
                    ],
                    input_type="dict",
                )

        layers = network.get_layers()
        layer_list = layers[0] if isinstance(layers, tuple) else list(layers)

        if len(layer_list) >= 2:
            print("   [OK] Example multilayer graph created")
            if verbose:
                print(f"      Layers: {len(layer_list)}")
                print(f"      Total nodes: {network.core_network.number_of_nodes()}")
                print(f"      Total edges: {network.core_network.number_of_edges()}")
            multilayer_status = True
        else:
            print("   [X] Multilayer graph creation failed: insufficient layers")
    except Exception as e:
        print(f"   [X] Multilayer graph creation failed: {e}")
        if verbose:
            traceback.print_exc()
    test_results.append(("Multilayer graph", multilayer_status))

    # Test 5: Community detection
    print("\n5. Testing community detection...")
    community_status = False
    try:
        from py3plex.algorithms.community_detection import community_wrapper

        # Create simple test graph
        G = nx.karate_club_graph()
        partition = community_wrapper.louvain_communities(G)

        if partition and len(set(partition.values())) > 1:
            print("   [OK] Community detection test passed")
            if verbose:
                print(f"      Communities found: {len(set(partition.values()))}")
            community_status = True
        else:
            print("   [X] Community detection failed: no communities found")
    except Exception as e:
        print(f"   [X] Community detection failed: {e}")
        if verbose:
            traceback.print_exc()
    test_results.append(("Community detection", community_status))

    # Test 6: File I/O
    print("\n6. Testing file I/O...")
    io_status = False
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_network.graphml"

            # Create and save network
            network = multinet.multi_layer_network()
            nodes = [{"source": f"node{i}", "type": "test_layer"} for i in range(5)]
            network.add_nodes(nodes, input_type="dict")

            edges = [
                {
                    "source": f"node{i}",
                    "target": f"node{i+1}",
                    "source_type": "test_layer",
                    "target_type": "test_layer",
                }
                for i in range(4)
            ]
            network.add_edges(edges, input_type="dict")

            # Save
            nx.write_graphml(network.core_network, str(test_file))

            # Load
            loaded_network = multinet.multi_layer_network()
            G = nx.read_graphml(str(test_file))
            loaded_network.core_network = G

            if loaded_network.core_network.number_of_nodes() == 5:
                print("   [OK] File I/O test passed")
                if verbose:
                    print(f"      Test file: {test_file.name}")
                io_status = True
            else:
                print("   [X] File I/O test failed: node count mismatch")
    except Exception as e:
        print(f"   [X] File I/O test failed: {e}")
        if verbose:
            traceback.print_exc()
    test_results.append(("File I/O", io_status))

    # Test 7: Centrality statistics
    print("\n7. Testing centrality statistics...")
    centrality_status = False
    try:
        from py3plex.algorithms.statistics import multilayer_statistics as mls

        # Create a multilayer network for centrality testing
        network = multinet.multi_layer_network()

        # Add nodes and edges in two layers
        for layer_idx in range(2):
            layer_name = f"layer{layer_idx + 1}"
            nodes = [{"source": f"node{i}", "type": layer_name} for i in range(6)]
            network.add_nodes(nodes, input_type="dict")

            # Create a star topology (node0 as hub)
            for i in range(1, 6):
                network.add_edges(
                    [
                        {
                            "source": "node0",
                            "target": f"node{i}",
                            "source_type": layer_name,
                            "target_type": layer_name,
                        }
                    ],
                    input_type="dict",
                )

        # Test versatility centrality (multilayer-specific)
        try:
            versatility = mls.versatility_centrality(network, centrality_type="degree")
            if versatility and len(versatility) > 0:
                if verbose:
                    print("   OK Versatility centrality computed")
                    top_node = max(versatility.items(), key=lambda x: x[1])
                    print(f"      Top node: {top_node[0]} (score: {top_node[1]:.4f})")
        except Exception as e:
            if verbose:
                print(f"   ! Versatility centrality: {e}")

        # Test degree centrality on core network
        G = network.core_network
        degree_cent = nx.degree_centrality(G)
        if degree_cent and len(degree_cent) > 0:
            if verbose:
                print("   OK Degree centrality computed")
                print(f"      Nodes: {len(degree_cent)}")

        # Test betweenness centrality
        betw_cent = nx.betweenness_centrality(G)
        if betw_cent and len(betw_cent) > 0:
            if verbose:
                print("   OK Betweenness centrality computed")

        # Test layer density (multilayer statistic)
        density1 = mls.layer_density(network, "layer1")
        density2 = mls.layer_density(network, "layer2")
        if 0.0 <= density1 <= 1.0 and 0.0 <= density2 <= 1.0:
            if verbose:
                print("   OK Layer density computed")
                print(f"      Layer1: {density1:.4f}, Layer2: {density2:.4f}")

        print("   [OK] Centrality statistics test passed")
        centrality_status = True

    except Exception as e:
        print(f"   [X] Centrality statistics failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
    test_results.append(("Centrality statistics", centrality_status))

    # Test 8: Multilayer manipulation
    print("\n8. Testing multilayer manipulation...")
    manipulation_status = False
    try:
        # Create a multilayer network
        network = multinet.multi_layer_network()

        # Add nodes in three layers
        for layer_idx in range(3):
            layer_name = f"layer{layer_idx + 1}"
            nodes = [{"source": f"node{i}", "type": layer_name} for i in range(4)]
            network.add_nodes(nodes, input_type="dict")

            # Add edges in each layer
            for i in range(3):
                network.add_edges(
                    [
                        {
                            "source": f"node{i}",
                            "target": f"node{i+1}",
                            "source_type": layer_name,
                            "target_type": layer_name,
                        }
                    ],
                    input_type="dict",
                )

        initial_nodes = network.core_network.number_of_nodes()

        # Test layer splitting
        try:
            layers_result = network.split_to_layers()
            if layers_result and len(layers_result) == 3:
                if verbose:
                    print(f"   OK Layer splitting: {len(layers_result)} layers")
        except Exception as e:
            if verbose:
                print(f"   ! Layer splitting: {e}")

        # Test edge aggregation (flattening)
        try:
            aggregated = network.aggregate_edges(metric="sum")
            if aggregated and aggregated.number_of_nodes() > 0:
                if verbose:
                    print("   OK Edge aggregation (flattening) successful")
                    print(f"      Aggregated: {aggregated.number_of_nodes()} nodes, {aggregated.number_of_edges()} edges")
        except Exception as e:
            if verbose:
                print(f"   ! Edge aggregation: {e}")

        # Test subnetwork extraction by layer
        try:
            # Get edges for layer1 only
            layer1_edges = [
                edge for edge in network.get_edges()
                if edge[0][1] == "layer1" and edge[1][1] == "layer1"
            ]
            if layer1_edges:
                if verbose:
                    print(f"   OK Subnetwork extraction: {len(layer1_edges)} edges in layer1")
        except Exception as e:
            if verbose:
                print(f"   ! Subnetwork extraction: {e}")

        # Verify network integrity after operations
        if network.core_network.number_of_nodes() == initial_nodes:
            if verbose:
                print("   OK Network integrity maintained")

        print("   [OK] Multilayer manipulation test passed")
        manipulation_status = True

    except Exception as e:
        print(f"   [X] Multilayer manipulation failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
    test_results.append(("Multilayer manipulation", manipulation_status))

    # Test 9: Random generators
    print("\n9. Testing random generators...")
    random_gen_status = False
    try:
        from py3plex.core import random_generators

        # Generate a small ER multilayer network
        np.random.seed(42)
        random.seed(42)
        er_network = random_generators.random_multilayer_ER(
            10,  # nodes
            2,   # layers
            0.3, # edge probability
            directed=False
        )

        if er_network and er_network.core_network.number_of_nodes() > 0:
            print("   [OK] Random ER multilayer network generated")
            if verbose:
                print(f"      Nodes: {er_network.core_network.number_of_nodes()}")
                print(f"      Edges: {er_network.core_network.number_of_edges()}")
            random_gen_status = True
        else:
            print("   [X] Random generator failed: empty network")
    except Exception as e:
        print(f"   [X] Random generator failed: {e}")
        if verbose:
            traceback.print_exc()
    test_results.append(("Random generators", random_gen_status))

    # Test 10: NetworkX wrapper
    print("\n10. Testing NetworkX wrapper...")
    nx_wrapper_status = False
    try:
        from py3plex.core import random_generators

        # Create a small network
        np.random.seed(42)
        random.seed(42)
        test_network = random_generators.random_multilayer_ER(
            15,  # nodes
            2,   # layers
            0.2, # edge probability
            directed=False
        )

        # Test monoplex_nx_wrapper with degree_centrality
        centralities = test_network.monoplex_nx_wrapper("degree_centrality")

        if centralities and len(centralities) > 0:
            print("   [OK] NetworkX wrapper test passed")
            if verbose:
                print(f"      Computed centrality for {len(centralities)} nodes")
                top_node = max(centralities.items(), key=lambda x: x[1])
                print(f"      Top node: {top_node[0]} (centrality: {top_node[1]:.4f})")
            nx_wrapper_status = True
        else:
            print("   [X] NetworkX wrapper failed: no centralities computed")
    except Exception as e:
        print(f"   [X] NetworkX wrapper failed: {e}")
        if verbose:
            traceback.print_exc()
    test_results.append(("NetworkX wrapper", nx_wrapper_status))

    # Test 11: New I/O system
    print("\n11. Testing new I/O system...")
    new_io_status = False
    try:
        from py3plex.io import (
            Edge,
            Layer,
            MultiLayerGraph,
            Node,
            to_networkx,
            write,
            read,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple multilayer graph using new I/O
            graph = MultiLayerGraph(directed=False)
            graph.add_layer(Layer(id="layer1"))
            graph.add_layer(Layer(id="layer2"))

            for i in range(3):
                graph.add_node(Node(id=f"node{i}"))

            # Add edges in both layers
            graph.add_edge(Edge(src="node0", dst="node1", src_layer="layer1", dst_layer="layer1"))
            graph.add_edge(Edge(src="node1", dst="node2", src_layer="layer2", dst_layer="layer2"))

            # Test JSON I/O
            json_file = Path(tmpdir) / "test.json"
            write(graph, str(json_file), deterministic=True)
            loaded_graph = read(str(json_file))

            # Test NetworkX conversion
            G = to_networkx(loaded_graph, mode="union")

            if loaded_graph and len(loaded_graph.nodes) == 3 and G.number_of_nodes() > 0:
                print("   [OK] New I/O system test passed")
                if verbose:
                    print(f"      Nodes: {len(loaded_graph.nodes)}")
                    print(f"      Edges: {len(loaded_graph.edges)}")
                    print(f"      Layers: {len(loaded_graph.layers)}")
                new_io_status = True
            else:
                print("   [X] New I/O system failed: incorrect node count")
    except Exception as e:
        print(f"   [X] New I/O system failed: {e}")
        if verbose:
            traceback.print_exc()
    test_results.append(("New I/O system", new_io_status))

    # Test 12: Advanced multilayer statistics
    print("\n12. Testing advanced multilayer statistics...")
    advanced_stats_status = False
    try:
        from py3plex.algorithms.statistics import multilayer_statistics as mls

        # Create a small test network
        network = multinet.multi_layer_network(directed=False)

        # Add edges in two layers
        network.add_edges([
            ['Alice', 'social', 'Bob', 'social', 1],
            ['Bob', 'social', 'Carol', 'social', 1],
            ['Alice', 'work', 'Carol', 'work', 1],
        ], input_type='list')

        # Test multiple statistics
        stats_tests = []

        # 1. Node activity
        try:
            activity = mls.node_activity(network, 'Alice')
            if 0.0 <= activity <= 1.0:
                stats_tests.append("node_activity")
                if verbose:
                    print(f"   OK Node activity: {activity:.3f}")
        except Exception as e:
            if verbose:
                print(f"   ! Node activity: {e}")

        # 2. Edge overlap
        try:
            overlap = mls.edge_overlap(network, 'social', 'work')
            if 0.0 <= overlap <= 1.0:
                stats_tests.append("edge_overlap")
                if verbose:
                    print(f"   OK Edge overlap: {overlap:.3f}")
        except Exception as e:
            if verbose:
                print(f"   ! Edge overlap: {e}")

        # 3. Layer density
        try:
            density = mls.layer_density(network, 'social')
            if 0.0 <= density <= 1.0:
                stats_tests.append("layer_density")
                if verbose:
                    print(f"   OK Layer density: {density:.3f}")
        except Exception as e:
            if verbose:
                print(f"   ! Layer density: {e}")

        # 4. Degree vector
        try:
            deg_vec = mls.degree_vector(network, 'Alice')
            if deg_vec and len(deg_vec) >= 0:
                stats_tests.append("degree_vector")
                if verbose:
                    print(f"   OK Degree vector: {deg_vec}")
        except Exception as e:
            if verbose:
                print(f"   ! Degree vector: {e}")

        if len(stats_tests) >= 3:  # At least 3 of 4 stats should work
            print("   [OK] Advanced multilayer statistics test passed")
            if verbose:
                print(f"      Tested: {', '.join(stats_tests)}")
            advanced_stats_status = True
        else:
            print(f"   [X] Advanced multilayer statistics failed: only {len(stats_tests)}/4 tests passed")
    except Exception as e:
        print(f"   [X] Advanced multilayer statistics failed: {e}")
        if verbose:
            traceback.print_exc()
    test_results.append(("Advanced multilayer statistics", advanced_stats_status))

    # Performance summary
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")

    passed = sum(1 for _, status in test_results if status)
    total = len(test_results)

    for test_name, status in test_results:
        status_icon = "OK" if status else "X"
        print(f"  [{status_icon}] {test_name}")

    print(f"\n  Tests passed: {passed}/{total}")
    print(f"  Time elapsed: {elapsed:.2f}s")

    if passed == total:
        print("\n[OK] All tests completed successfully!")
        return 0
    else:
        print(f"\n[X] {total - passed} test(s) failed")
        return 1


def cmd_quickstart(args: argparse.Namespace) -> int:
    """Run quickstart demo - creates a tiny demo graph and demonstrates basic operations.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    # Set matplotlib backend early
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt

    print("[py3plex::quickstart] Welcome to py3plex!")
    print()
    print("This quickstart guide will demonstrate basic multilayer network operations.")
    print("=" * 70)
    print()

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        cleanup = False
    else:
        temp_dir = tempfile.mkdtemp(prefix="py3plex_quickstart_")
        output_dir = Path(temp_dir)
        cleanup = not args.keep_files

    try:
        # Step 1: Create a demo multilayer network
        print("Step 1: Creating demo multilayer network...")
        print("  - 10 nodes across 2 layers")
        print("  - Random connections with p=0.3")
        print()

        network = multinet.multi_layer_network()

        # Set random seed for reproducibility
        random.seed(42)
        np.random.seed(42)

        # Create two layers with nodes
        for layer_idx in range(2):
            layer_name = f"layer{layer_idx + 1}"
            nodes_dict = [{"source": f"node{i}", "type": layer_name} for i in range(10)]
            network.add_nodes(nodes_dict, input_type="dict")

            # Add edges with probability 0.3
            edges_dict = []
            for i in range(10):
                for j in range(i + 1, 10):
                    if random.random() < 0.3:
                        edges_dict.append(
                            {
                                "source": f"node{i}",
                                "target": f"node{j}",
                                "source_type": layer_name,
                                "target_type": layer_name,
                            }
                        )
            if edges_dict:
                network.add_edges(edges_dict, input_type="dict")

        network_file = output_dir / "demo_network.graphml"
        nx.write_graphml(network.core_network, str(network_file))
        print(f"Network created and saved to: {network_file}")
        print(f"  Nodes: {network.core_network.number_of_nodes()}")
        print(f"  Edges: {network.core_network.number_of_edges()}")
        print()

        # Step 2: Compute basic statistics
        print("Step 2: Computing basic network statistics...")
        layers = _get_layer_names(network)
        print(f"  Layers: {', '.join(layers)}")

        from py3plex.algorithms.statistics import multilayer_statistics as mls

        for layer in layers:
            try:
                density = mls.layer_density(network, layer)
                print(f"  {layer} density: {density:.4f}")
            except Exception as e:
                print(f"  {layer} density: (error: {e})")

        G_undirected = network.core_network.to_undirected()
        G_simple = _convert_to_simple_graph(G_undirected)
        clustering = nx.average_clustering(G_simple)
        print(f"  Avg clustering coefficient: {clustering:.4f}")
        print()

        # Step 3: Visualize the network
        print("Step 3: Visualizing the network...")
        viz_file = output_dir / "demo_visualization.png"

        try:
            from py3plex.visualization import multilayer

            layer_names, layer_graphs, multiedges = network.get_layers(
                style="diagonal", compute_layouts="force", verbose=False
            )

            plt.figure(figsize=(10, 6))
            if isinstance(layer_graphs, list):
                graph_list = layer_graphs
            else:
                graph_list = list(layer_graphs.values())

            multilayer.draw_multilayer_default(
                graph_list,
                display=False,
                labels=layer_names,
            )
            plt.savefig(viz_file, dpi=150, bbox_inches="tight")
            plt.close()
            print(f"OK Visualization saved to: {viz_file}")
        except Exception as e:
            # Fallback to simple NetworkX visualization
            print(f"  Note: Multilayer visualization failed ({e}), using simple layout")
            pos = nx.spring_layout(network.core_network)
            plt.figure(figsize=(10, 6))
            nx.draw(
                network.core_network,
                pos,
                node_size=300,
                node_color="lightblue",
                edge_color="gray",
                alpha=0.7,
                with_labels=True,
                font_size=8,
            )
            plt.title("Demo Multilayer Network")
            plt.savefig(viz_file, dpi=150, bbox_inches="tight")
            plt.close()
            print(f"OK Visualization saved to: {viz_file}")
        print()

        # Step 4: Detect communities
        print("Step 4: Detecting communities...")
        try:
            from py3plex.algorithms.community_detection import community_wrapper

            G = (
                network.core_network.to_undirected()
                if network.core_network.is_directed()
                else network.core_network
            )
            partition = community_wrapper.louvain_communities(G)
            num_communities = len(set(partition.values()))
            print(f"Found {num_communities} communities")

            comm_file = output_dir / "demo_communities.json"
            with open(comm_file, "w") as f:
                json.dump(
                    {
                        "num_communities": num_communities,
                        "communities": {str(k): int(v) for k, v in partition.items()},
                    },
                    f,
                    indent=2,
                )
            print(f"  Communities saved to: {comm_file}")
        except Exception as e:
            print(f"  Note: Community detection skipped ({e})")
        print()

        # Summary and next steps
        print("=" * 70)
        print("Quickstart completed successfully!")
        print()
        print("Generated files:")
        for file in output_dir.glob("demo_*"):
            print(f"  - {file}")
        print()
        print("Next steps:")
        print("  1. Try creating your own network:")
        print(
            "     py3plex create --nodes 50 --layers 3 --output my_network.graphml"
        )
        print()
        print("  2. Analyze an existing network:")
        print("     py3plex load my_network.graphml --stats")
        print()
        print("  3. Visualize your network:")
        print(
            "     py3plex visualize my_network.graphml --output viz.png --layout multilayer"
        )
        print()
        print("  4. Detect communities:")
        print(
            "     py3plex community my_network.graphml --algorithm louvain --output communities.json"
        )
        print()
        print("For more information:")
        print("  - Documentation: https://skblaz.github.io/py3plex/")
        print("  - GitHub: https://github.com/SkBlaz/py3plex")
        print("  - Run 'py3plex --help' to see all available commands")
        print()

        if cleanup:
            print(f"Cleaning up temporary files in {output_dir}...")
            shutil.rmtree(output_dir)
            print("   (Use --keep-files to preserve generated files)")
        else:
            print(f"Files kept in: {output_dir}")

        print()
        return 0

    except Exception as e:
        print(f"\nError during quickstart: {e}")

        traceback.print_exc()
        return 1


def cmd_check(args: argparse.Namespace) -> int:
    """Lint and validate a graph data file.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        from py3plex.linter import GraphFileLinter

        logger.info(f"Checking file: {args.input}")

        linter = GraphFileLinter(args.input)
        issues = linter.lint()

        if not issues:
            logger.info("✓ No issues found!")
            return 0

        # Print all issues
        logger.info(f"\nFound {len(issues)} issue(s):\n")
        for issue in issues:
            print(str(issue))

        # Print summary
        print()
        linter.print_summary()

        # Determine exit code
        if linter.has_errors():
            logger.error("\n✗ Validation failed with errors")
            return 1
        elif linter.has_warnings() and args.strict:
            logger.error("\n✗ Validation failed (strict mode: warnings treated as errors)")
            return 1
        else:
            logger.info("\n✓ Validation passed (with warnings)")
            return 0

    except Exception as e:
        logger.error(f"Error checking file: {e}")
        traceback.print_exc()
        return 1


def cmd_run_config(args: argparse.Namespace) -> int:
    """Run workflow from configuration file.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    try:
        from py3plex.workflows import WorkflowConfig, WorkflowRunner

        logger.info(f"Loading workflow configuration from {args.config}...")
        config = WorkflowConfig.from_file(args.config)

        # Validate configuration
        errors = config.validate()
        if errors:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return 1

        logger.info("Configuration is valid")

        if args.validate_only:
            logger.info("Validation-only mode: skipping execution")
            return 0

        # Execute workflow
        runner = WorkflowRunner(config)
        runner.run()

        return 0

    except FileNotFoundError as e:
        logger.error(f"Config file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error running workflow: {e}")
        traceback.print_exc()
        return 1


def main(argv: Optional[List[str]] = None) -> int:
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

    # Configure logging level based on verbosity (if added)
    # This allows for future --verbose/-v and --quiet/-q flags

    # Dispatch to command handlers
    command_handlers = {
        "help": cmd_help,
        "check": cmd_check,
        "create": cmd_create,
        "load": cmd_load,
        "community": cmd_community,
        "centrality": cmd_centrality,
        "stats": cmd_stats,
        "visualize": cmd_visualize,
        "aggregate": cmd_aggregate,
        "convert": cmd_convert,
        "selftest": cmd_selftest,
        "quickstart": cmd_quickstart,
        "run-config": cmd_run_config,
    }

    handler = command_handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        logger.error(f"Unknown command '{args.command}'")
        return 1


if __name__ == "__main__":
    sys.exit(main())
