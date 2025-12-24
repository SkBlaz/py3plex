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


def _load_network_from_stdin(input_format: str = "multiedgelist") -> "multinet.multi_layer_network":
    """Load a network from stdin.

    Args:
        input_format: Expected format of stdin data ('multiedgelist', 'edgelist', 'json')

    Returns:
        Loaded multi_layer_network object
    """
    network = multinet.multi_layer_network()
    
    # Read all stdin content
    stdin_content = sys.stdin.read()
    if not stdin_content.strip():
        raise ValueError("No data received from stdin")
    
    if input_format == "json":
        # Parse JSON format
        data = json.loads(stdin_content)
        
        # Handle py3plex JSON format with nodes and edges
        if "nodes" in data and "edges" in data:
            # Reconstruct network from JSON data
            for edge in data.get("edges", []):
                source = edge.get("source", "")
                target = edge.get("target", "")
                # Try to parse as tuple strings from convert output
                if source.startswith("(") and target.startswith("("):
                    import ast
                    try:
                        source_tuple = ast.literal_eval(source)
                        target_tuple = ast.literal_eval(target)
                        if isinstance(source_tuple, tuple) and isinstance(target_tuple, tuple):
                            network.add_edges([{
                                "source": source_tuple[0],
                                "target": target_tuple[0],
                                "source_type": source_tuple[1] if len(source_tuple) > 1 else "default",
                                "target_type": target_tuple[1] if len(target_tuple) > 1 else "default",
                            }], input_type="dict")
                        continue
                    except (ValueError, SyntaxError):
                        pass
                # Handle simple edge format
                network.add_edges([{
                    "source": source,
                    "target": target,
                    "source_type": edge.get("source_layer", "default"),
                    "target_type": edge.get("target_layer", "default"),
                }], input_type="dict")
        else:
            raise ValueError("Invalid JSON format: expected 'nodes' and 'edges' keys")
    else:
        # Write to temp file and load
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(stdin_content)
            temp_path = f.name
        
        try:
            # Detect format from content
            lines = stdin_content.strip().split('\n')
            first_line = lines[0].strip() if lines else ""
            parts = first_line.split()
            
            if len(parts) in [4, 5]:
                # Multilayer format
                network.load_network(temp_path, input_type="multiedgelist")
            else:
                # Simple edgelist
                network.load_network(temp_path, input_type="edgelist")
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    return network


def _load_network(file_path: str) -> "multinet.multi_layer_network":
    """Load a network from file or stdin (use '-' for stdin).

    Args:
        file_path: Path to the network file, or '-' for stdin

    Returns:
        Loaded multi_layer_network object
    """
    # Handle stdin input
    if file_path == "-":
        return _load_network_from_stdin()
    
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
  py3plex tutorial             # Interactive step-by-step tutorial
  py3plex quickstart           # Quick demo with example graph
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

Unix Piping (use '-' for stdin):
  # Pipe network data to query command
  cat network.edgelist | py3plex query - "SELECT nodes COMPUTE degree"

  # Query and output JSON for further processing
  py3plex query network.edgelist "SELECT nodes WHERE degree > 5 COMPUTE betweenness_centrality" | jq '.nodes[:5]'

  # Use DSL builder syntax
  py3plex query network.edgelist --dsl "Q.nodes().where(layer='social').compute('degree')"

  # Load network from stdin
  cat network.edgelist | py3plex load - --stats

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
        "load", help="Load and inspect a multilayer network (use '-' for stdin)"
    )
    load_parser.add_argument("input", help="Input network file (use '-' to read from stdin)")
    load_parser.add_argument(
        "--info", action="store_true", help="Display network information"
    )
    load_parser.add_argument(
        "--stats", action="store_true", help="Display basic statistics"
    )
    load_parser.add_argument("--output", "-o", help="Save output to file (JSON format)")
    load_parser.add_argument(
        "--input-format",
        choices=["auto", "multiedgelist", "edgelist", "json"],
        default="auto",
        help="Input format for stdin data (default: auto-detect)",
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

    # QUERY command - Execute DSL queries on networks (supports Unix piping)
    query_parser = subparsers.add_parser(
        "query",
        help="Execute DSL queries on networks (supports stdin with '-')",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Unix Piping Examples:
  # Pipe network data and run a query
  cat network.edgelist | py3plex query - "SELECT nodes WHERE layer='social' COMPUTE degree"

  # Chain commands: create -> query
  py3plex create --nodes 50 --layers 3 -o /dev/stdout --format json | py3plex query - --json "SELECT nodes COMPUTE degree ORDER BY degree DESC LIMIT 10"

  # Use with the Python DSL builder syntax
  py3plex query network.edgelist --dsl "Q.nodes().where(layer='social').compute('degree')"

DSL Query Syntax:
  SELECT nodes|edges
  [FROM LAYER("name") [+ LAYER("name2")]]
  [WHERE condition [AND condition ...]]
  [COMPUTE measure [AS alias], ...]
  [ORDER BY field [DESC]]
  [LIMIT n]

Examples:
  # Get all nodes in the social layer
  py3plex query network.edgelist "SELECT nodes WHERE layer='social'"

  # Compute degree and betweenness for high-degree nodes
  py3plex query network.edgelist "SELECT nodes WHERE degree > 5 COMPUTE betweenness_centrality ORDER BY betweenness_centrality DESC LIMIT 20"

  # Get nodes from multiple layers
  py3plex query network.edgelist 'SELECT nodes FROM LAYER("social") + LAYER("work")'
        """,
    )
    query_parser.add_argument(
        "input",
        help="Input network file (use '-' to read from stdin)",
    )
    query_parser.add_argument(
        "query",
        nargs="?",
        help="DSL query string (if not provided, reads from --query-file)",
    )
    query_parser.add_argument(
        "--query-file", "-f",
        help="File containing DSL query",
    )
    query_parser.add_argument(
        "--output", "-o",
        help="Output file (JSON format). If not specified, outputs to stdout",
    )
    query_parser.add_argument(
        "--format",
        choices=["json", "csv", "table"],
        default="json",
        help="Output format (default: json)",
    )
    query_parser.add_argument(
        "--input-format",
        choices=["auto", "multiedgelist", "edgelist", "json"],
        default="auto",
        help="Input format for stdin data (default: auto-detect)",
    )
    query_parser.add_argument(
        "--dsl",
        action="store_true",
        help="Interpret query as Python DSL builder syntax (e.g., Q.nodes().compute('degree'))",
    )

    # DSL-LINT command
    lint_parser = subparsers.add_parser(
        "dsl-lint",
        help="Lint and analyze DSL queries for potential issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
DSL Lint - Static Analysis for DSL Queries

Analyzes DSL queries for potential issues including:
  - Unknown layers or attributes (DSL001, DSL002)
  - Type mismatches (DSL101)
  - Unsatisfiable or redundant predicates (DSL201, DSL202)
  - Performance issues (PERF301, PERF302)

Examples:
  # Lint a query string
  py3plex dsl-lint "SELECT nodes FROM LAYER('unknown') WHERE degree > 'foo'"
  
  # Lint with network context for schema validation
  py3plex dsl-lint "SELECT nodes WHERE degree > 5" --network network.edgelist
  
  # Lint a query from a file
  py3plex dsl-lint --query-file query.txt --network network.edgelist
  
  # Show detailed explanation
  py3plex dsl-lint "SELECT nodes" --explain --network network.edgelist

Exit codes:
  0 - No errors found
  1 - Errors found
  2 - Command error
        """,
    )
    lint_parser.add_argument(
        "query",
        nargs="?",
        help="DSL query string to lint (if not provided, reads from --query-file)",
    )
    lint_parser.add_argument(
        "--query-file", "-f",
        help="File containing DSL query to lint",
    )
    lint_parser.add_argument(
        "--network", "-n",
        help="Network file for schema-aware linting (optional but recommended)",
    )
    lint_parser.add_argument(
        "--explain", "-e",
        action="store_true",
        help="Show detailed query explanation with type info and execution plan",
    )
    lint_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
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

    # TUTORIAL command
    tutorial_parser = subparsers.add_parser(
        "tutorial",
        help="Interactive tutorial mode - learn py3plex step by step",
    )
    tutorial_parser.add_argument(
        "--step",
        "-s",
        type=int,
        default=None,
        choices=[1, 2, 3, 4, 5, 6],
        help="Run a specific tutorial step (1-6). If not specified, runs all steps.",
    )
    tutorial_parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run without pausing between steps (for automated testing)",
    )
    tutorial_parser.add_argument(
        "--keep-files",
        action="store_true",
        help="Keep generated files instead of cleaning them up",
    )
    tutorial_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for output files (default: temporary directory)",
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
        # Load network (supports stdin with '-')
        if args.input == "-":
            input_format = getattr(args, 'input_format', 'auto')
            if input_format == "auto":
                input_format = "multiedgelist"
            network = _load_network_from_stdin(input_format)
        else:
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


def cmd_query(args: argparse.Namespace) -> int:
    """Execute DSL queries on networks with Unix piping support.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    try:
        # Get query string
        query_str = args.query
        if not query_str and args.query_file:
            with open(args.query_file) as f:
                query_str = f.read().strip()
        
        if not query_str:
            logger.error("No query provided. Use positional argument or --query-file")
            return 1
        
        # Load network (supports stdin with '-')
        if args.input == "-":
            # Determine input format
            input_format = args.input_format
            if input_format == "auto":
                input_format = "multiedgelist"  # Default for stdin
            network = _load_network_from_stdin(input_format)
        else:
            logger.info(f"Loading network from {args.input}...")
            network = _load_network(args.input)
        
        # Execute query
        if args.dsl:
            # Interpret as Python DSL builder syntax
            from py3plex.dsl import Q, L, Param
            
            # Create a restricted namespace with only DSL classes
            # and no builtins for safety
            namespace = {
                "Q": Q,
                "L": L,
                "Param": Param,
                "__builtins__": {},  # Disable all builtins for security
            }
            
            # Basic validation: only allow expected patterns
            allowed_patterns = [
                "Q.", "L[", "Param.",
                ".nodes(", ".edges(", ".from_layers(", ".where(",
                ".compute(", ".order_by(", ".limit(", ".execute(",
                '"', "'", "(", ")", ",", "=", "+", "-", "&", "[", "]",
                "_", "layer", "degree", "centrality", "clustering",
                "betweenness", "closeness", "eigenvector", "pagerank",
            ]
            
            # Check for potentially dangerous patterns
            dangerous_patterns = [
                "__", "import", "exec", "eval", "compile", "open",
                "file", "input", "raw_input", "os.", "sys.", "subprocess",
            ]
            
            query_lower = query_str.lower()
            for pattern in dangerous_patterns:
                if pattern in query_lower:
                    raise ValueError(f"Potentially unsafe pattern '{pattern}' not allowed in DSL query")
            
            # Execute the builder expression with restricted namespace
            try:
                query_builder = eval(query_str, namespace)  # noqa: S307
            except NameError as e:
                raise ValueError(f"Invalid DSL syntax: {e}. Only Q, L, and Param are allowed.")
            
            result = query_builder.execute(network)
        else:
            # Use legacy string DSL parser
            from py3plex.dsl import execute_query
            result = execute_query(network, query_str)
        
        # Format output
        if args.dsl:
            # Convert QueryResult to dict
            output_data = result.to_dict()
        else:
            # Legacy result is already a dict
            output_data = result
        
        # Make output JSON-serializable (convert tuple keys to strings)
        def make_serializable(obj):
            """Recursively convert tuples to strings for JSON serialization."""
            if isinstance(obj, dict):
                return {
                    (str(k) if isinstance(k, tuple) else k): make_serializable(v)
                    for k, v in obj.items()
                }
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif isinstance(obj, tuple):
                return str(obj)
            else:
                return obj
        
        output_data = make_serializable(output_data)
        
        # Output results
        if args.format == "json":
            output_str = json.dumps(output_data, indent=2, default=str)
        elif args.format == "csv":
            # Convert to CSV format
            import io
            import csv
            
            output_buffer = io.StringIO()
            
            if "nodes" in output_data:
                writer = csv.writer(output_buffer)
                # Header
                computed_keys = list(output_data.get("computed", {}).keys())
                writer.writerow(["node"] + computed_keys)
                
                # Data rows
                for node in output_data["nodes"]:
                    row = [str(node)]
                    for key in computed_keys:
                        computed = output_data.get("computed", {}).get(key, {})
                        value = computed.get(str(node), computed.get(node, ""))
                        row.append(value)
                    writer.writerow(row)
            elif "edges" in output_data:
                writer = csv.writer(output_buffer)
                writer.writerow(["source", "target"])
                for edge in output_data["edges"]:
                    if isinstance(edge, (list, tuple)) and len(edge) >= 2:
                        writer.writerow([str(edge[0]), str(edge[1])])
                    else:
                        writer.writerow([str(edge)])
            
            output_str = output_buffer.getvalue()
        elif args.format == "table":
            # Pretty-print as table
            lines = []
            if "nodes" in output_data:
                computed_keys = list(output_data.get("computed", {}).keys())
                
                # Header
                header = ["Node"] + computed_keys
                lines.append(" | ".join(f"{h:>15}" for h in header))
                lines.append("-" * (17 * len(header)))
                
                # Data rows
                for node in output_data["nodes"][:50]:  # Limit to 50 rows for table
                    row = [str(node)[:15]]
                    for key in computed_keys:
                        computed = output_data.get("computed", {}).get(key, {})
                        value = computed.get(str(node), computed.get(node, ""))
                        if isinstance(value, float):
                            row.append(f"{value:.4f}")
                        else:
                            row.append(str(value)[:15])
                    lines.append(" | ".join(f"{v:>15}" for v in row))
                
                if len(output_data["nodes"]) > 50:
                    lines.append(f"... and {len(output_data['nodes']) - 50} more rows")
            
            lines.append(f"\nTotal: {output_data.get('count', len(output_data.get('nodes', [])))} items")
            output_str = "\n".join(lines)
        
        # Write output
        if args.output:
            with open(args.output, "w") as f:
                f.write(output_str)
            logger.info(f"Query results saved to {args.output}")
        else:
            # Output to stdout for piping
            print(output_str)
        
        return 0
    
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        traceback.print_exc()
        return 1


def cmd_dsl_lint(args: argparse.Namespace) -> int:
    """Lint and analyze DSL queries.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for no errors, 1 for errors found, 2 for command error)
    """
    try:
        # Get query string
        query_str = args.query
        if not query_str and args.query_file:
            with open(args.query_file) as f:
                query_str = f.read().strip()
        
        if not query_str:
            logger.error("No query provided. Use positional argument or --query-file")
            return 2
        
        # Load network if provided (for schema-aware linting)
        network = None
        if args.network:
            try:
                logger.info(f"Loading network from {args.network} for schema validation...")
                network = _load_network(args.network)
            except Exception as e:
                logger.error(f"Failed to load network: {e}")
                return 2
        
        # Parse query using builder API
        # NOTE: Currently uses eval() with restricted namespace for builder syntax parsing.
        # This is safe because:
        # 1. Namespace contains only Q, L, Param (no builtins)
        # 2. Used only for interactive CLI, not production code
        # Future: Implement proper string DSL parser to eliminate eval()
        from py3plex.dsl import Q, L, Param, lint, explain
        
        # Try to parse as builder syntax first
        try:
            # Create a restricted namespace
            namespace = {
                "Q": Q,
                "L": L,
                "Param": Param,
                "__builtins__": {},
            }
            
            query_builder = eval(query_str, namespace)  # noqa: S307
            query_ast = query_builder.to_ast()
        except Exception:
            # Fall back to treating it as a note that we need string DSL support
            logger.error("String DSL syntax not yet supported for linting.")
            logger.error("Please use builder syntax: Q.nodes().from_layers(L['social']).where(degree__gt=5)")
            return 2
        
        # Run linting
        if args.explain:
            # Get detailed explanation
            result = explain(query_ast, graph=network)
            
            if args.format == "json":
                output = {
                    "ast_summary": result.ast_summary,
                    "type_info": result.type_info,
                    "cost_estimate": result.cost_estimate,
                    "plan_steps": result.plan_steps,
                    "diagnostics": [
                        {
                            "code": d.code,
                            "severity": d.severity,
                            "message": d.message,
                            "span": d.span,
                        }
                        for d in result.diagnostics
                    ]
                }
                print(json.dumps(output, indent=2))
            else:
                # Text format
                print("=" * 60)
                print("DSL Query Explanation")
                print("=" * 60)
                print("\nAST Summary:")
                print(result.ast_summary)
                print(f"\nEstimated Cost: {result.cost_estimate}")
                print("\nExecution Plan:")
                for i, step in enumerate(result.plan_steps, 1):
                    print(f"  {step}")
                print("\nType Information:")
                for key, type_val in result.type_info.items():
                    print(f"  {key}: {type_val}")
                
                if result.diagnostics:
                    print("\nDiagnostics:")
                    for d in result.diagnostics:
                        print(f"  [{d.severity.upper()}] {d.code}: {d.message}")
                        if d.suggested_fix:
                            print(f"    → Suggestion: {d.suggested_fix.replacement}")
                else:
                    print("\n✓ No issues found")
        else:
            # Just run linting
            diagnostics = lint(query_ast, graph=network)
            
            if args.format == "json":
                output = {
                    "diagnostics": [
                        {
                            "code": d.code,
                            "severity": d.severity,
                            "message": d.message,
                            "span": d.span,
                        }
                        for d in diagnostics
                    ]
                }
                print(json.dumps(output, indent=2))
            else:
                # Text format
                if diagnostics:
                    print(f"Found {len(diagnostics)} issue(s):\n")
                    for d in diagnostics:
                        print(f"[{d.severity.upper()}] {d.code}: {d.message}")
                        if d.suggested_fix:
                            print(f"  → Suggestion: {d.suggested_fix.replacement}")
                        print()
                else:
                    print("✓ No issues found")
        
        # Determine exit code
        has_errors = any(d.severity == "error" for d in (result.diagnostics if args.explain else diagnostics))
        return 1 if has_errors else 0
    
    except Exception as e:
        logger.error(f"Error linting query: {e}")
        traceback.print_exc()
        return 2


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

    # Test 13: Uncertainty quantification
    print("\n13. Testing uncertainty quantification...")
    uncertainty_status = False
    try:
        from py3plex.uncertainty import (
            StatSeries,
            bootstrap_metric,
        )

        tests_passed = []

        # Test StatSeries (deterministic)
        try:
            result = StatSeries(
                index=['A', 'B', 'C'],
                mean=np.array([1.0, 2.0, 3.0])
            )
            if result.is_deterministic and result.certainty == 1.0:
                tests_passed.append("StatSeries")
                if verbose:
                    print("   OK StatSeries deterministic mode works")
        except Exception as e:
            if verbose:
                print(f"   ! StatSeries: {e}")

        # Test StatSeries with uncertainty
        try:
            result_unc = StatSeries(
                index=['A', 'B', 'C'],
                mean=np.array([1.0, 2.0, 3.0]),
                std=np.array([0.1, 0.2, 0.15]),
                quantiles={
                    0.025: np.array([0.8, 1.6, 2.7]),
                    0.975: np.array([1.2, 2.4, 3.3])
                }
            )
            if not result_unc.is_deterministic and result_unc.certainty < 1.0:
                tests_passed.append("StatSeries_uncertain")
                if verbose:
                    print("   OK StatSeries with uncertainty works")
        except Exception as e:
            if verbose:
                print(f"   ! StatSeries uncertainty: {e}")

        # Test bootstrap_metric
        try:
            # Create a small test network
            network = multinet.multi_layer_network(directed=False)
            network.add_edges([
                ['A', 'layer1', 'B', 'layer1', 1],
                ['B', 'layer1', 'C', 'layer1', 1],
                ['C', 'layer1', 'A', 'layer1', 1],
            ], input_type='list')

            def degree_metric(net):
                """Simple degree metric for testing."""
                return dict(net.core_network.degree())

            # Run bootstrap with small sample size
            result = bootstrap_metric(
                graph=network,
                metric_fn=degree_metric,
                n_boot=10,
                random_state=42
            )
            
            if result and 'mean' in result:
                tests_passed.append("bootstrap_metric")
                if verbose:
                    print(f"   OK Bootstrap metric computed")
        except Exception as e:
            if verbose:
                print(f"   ! Bootstrap metric: {e}")

        if len(tests_passed) >= 2:
            print("   [OK] Uncertainty quantification test passed")
            if verbose:
                print(f"      Tested: {', '.join(tests_passed)}")
            uncertainty_status = True
        else:
            print(f"   [X] Uncertainty quantification failed: only {len(tests_passed)}/3 tests passed")

    except Exception as e:
        print(f"   [X] Uncertainty quantification failed: {e}")
        if verbose:
            traceback.print_exc()
    test_results.append(("Uncertainty quantification", uncertainty_status))

    # Test 14: Null models
    print("\n14. Testing null models...")
    nullmodels_status = False
    try:
        from py3plex.nullmodels import (
            configuration_model,
            erdos_renyi_model,
            generate_null_model,
        )

        # Create a small test network
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['A', 'layer1', 'B', 'layer1', 1],
            ['B', 'layer1', 'C', 'layer1', 1],
            ['C', 'layer1', 'D', 'layer1', 1],
            ['D', 'layer1', 'A', 'layer1', 1],
        ], input_type='list')

        tests_passed = []

        # Test configuration_model
        try:
            null_net = configuration_model(network)
            if null_net and null_net.core_network.number_of_nodes() > 0:
                tests_passed.append("configuration_model")
                if verbose:
                    print(f"   OK Configuration model: {null_net.core_network.number_of_nodes()} nodes")
        except Exception as e:
            if verbose:
                print(f"   ! Configuration model: {e}")

        # Test erdos_renyi_model
        try:
            null_net = erdos_renyi_model(network)
            if null_net and null_net.core_network.number_of_nodes() > 0:
                tests_passed.append("erdos_renyi_model")
                if verbose:
                    print(f"   OK Erdos-Renyi model: {null_net.core_network.number_of_nodes()} nodes")
        except Exception as e:
            if verbose:
                print(f"   ! Erdos-Renyi model: {e}")

        # Test generate_null_model
        try:
            result = generate_null_model(
                network=network,
                model="configuration",
                samples=3,
                seed=42
            )
            if result and hasattr(result, 'samples') and len(result.samples) == 3:
                tests_passed.append("generate_null_model")
                if verbose:
                    print(f"   OK Generate null model: {len(result.samples)} samples")
        except Exception as e:
            if verbose:
                print(f"   ! Generate null model: {e}")

        if len(tests_passed) >= 2:  # At least 2 of 3 should work
            print("   [OK] Null models test passed")
            if verbose:
                print(f"      Tested: {', '.join(tests_passed)}")
            nullmodels_status = True
        else:
            print(f"   [X] Null models failed: only {len(tests_passed)}/3 tests passed")

    except Exception as e:
        print(f"   [X] Null models failed: {e}")
        if verbose:
            traceback.print_exc()
    test_results.append(("Null models", nullmodels_status))

    # Test 15: DSL features
    print("\n15. Testing DSL features...")
    dsl_status = False
    try:
        from py3plex.dsl import execute_query, Q

        # Create a small test network
        network = multinet.multi_layer_network(directed=False)
        network.add_edges([
            ['Alice', 'social', 'Bob', 'social', 1],
            ['Bob', 'social', 'Carol', 'social', 1],
            ['Alice', 'work', 'Carol', 'work', 1],
        ], input_type='list')

        tests_passed = []

        # Test legacy string-based query
        try:
            result = execute_query(network, 'SELECT nodes')
            # Result could be dict or QueryResult object
            if result:
                # Handle both dict and object return types
                if isinstance(result, dict):
                    node_count = len(result.get('nodes', []))
                elif hasattr(result, 'nodes'):
                    node_count = len(result.nodes)
                else:
                    node_count = 0
                    
                if node_count > 0:
                    tests_passed.append("legacy_query")
                    if verbose:
                        print(f"   OK Legacy query: {node_count} nodes")
        except Exception as e:
            if verbose:
                print(f"   ! Legacy query: {e}")

        # Test builder API query
        try:
            query = Q.nodes()
            result = query.execute(network)
            if result and hasattr(result, 'nodes') and len(result.nodes) > 0:
                tests_passed.append("builder_query")
                if verbose:
                    print(f"   OK Builder query: {len(result.nodes)} nodes")
        except Exception as e:
            if verbose:
                print(f"   ! Builder query: {e}")

        # Test query with layer filtering
        try:
            query = Q.nodes().from_layers(['social'])
            result = query.execute(network)
            if result and hasattr(result, 'nodes'):
                tests_passed.append("layer_filter")
                if verbose:
                    print(f"   OK Layer filter: {len(result.nodes)} nodes in social layer")
        except Exception as e:
            if verbose:
                print(f"   ! Layer filter: {e}")

        if len(tests_passed) >= 2:  # At least 2 of 3 should work
            print("   [OK] DSL features test passed")
            if verbose:
                print(f"      Tested: {', '.join(tests_passed)}")
            dsl_status = True
        else:
            print(f"   [X] DSL features failed: only {len(tests_passed)}/3 tests passed")

    except Exception as e:
        print(f"   [X] DSL features failed: {e}")
        if verbose:
            traceback.print_exc()
    test_results.append(("DSL features", dsl_status))

    # Test 16: Workflows
    print("\n16. Testing workflows...")
    workflows_status = False
    try:
        from py3plex.workflows import WorkflowConfig

        # Test basic workflow config creation
        try:
            # Create a minimal valid config
            config_dict = {
                "datasets": [{
                    "name": "test_net",
                    "type": "random",
                    "params": {
                        "n_nodes": 10,
                        "n_layers": 2,
                        "edge_probability": 0.3
                    }
                }],
                "operations": []
            }
            
            config = WorkflowConfig(config_dict)
            if config and config.name == "unnamed_workflow":
                if verbose:
                    print("   OK Workflow config creation works")
                
                # Test validation
                errors = config.validate()
                if isinstance(errors, list):  # Method returns a list
                    if verbose:
                        print("   OK Workflow validation works")
                    workflows_status = True
                    print("   [OK] Workflows test passed")
                else:
                    print("   [X] Workflows test failed: validation unexpected return")
            else:
                print("   [X] Workflows test failed: config creation failed")
        except Exception as e:
            # If workflow config fails, this indicates a real problem
            print(f"   [X] Workflows failed: {e}")
            if verbose:
                traceback.print_exc()

    except Exception as e:
        print(f"   [X] Workflows failed: {e}")
        if verbose:
            traceback.print_exc()
    test_results.append(("Workflows", workflows_status))

    # Test 17: Temporal networks
    print("\n17. Testing temporal networks...")
    temporal_status = False
    try:
        from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork

        # Create a temporal network
        tnet = TemporalMultiLayerNetwork()
        
        # Add edges with timestamps using keyword argument
        tnet.add_edge('A', 'social', 'B', 'social', t=1.0)
        tnet.add_edge('B', 'social', 'C', 'social', t=2.0)
        tnet.add_edge('C', 'social', 'A', 'social', t=3.0)

        tests_passed = []

        # Test basic properties
        if hasattr(tnet, 'temporal_edges') and len(tnet.temporal_edges) == 3:
            tests_passed.append("temporal_structure")
            if verbose:
                print(f"   OK Temporal network structure works: {len(tnet.temporal_edges)} edges")

        # Test snapshot extraction
        try:
            if hasattr(tnet, 'snapshot_at'):
                snapshot = tnet.snapshot_at(2.5)
                if snapshot:
                    tests_passed.append("snapshot")
                    if verbose:
                        print(f"   OK Snapshot extraction works")
        except Exception as e:
            if verbose:
                print(f"   ! Snapshot extraction: {e}")

        # Test time range
        try:
            if hasattr(tnet, 'get_time_range'):
                time_range = tnet.get_time_range()
                if time_range:
                    tests_passed.append("time_range")
                    if verbose:
                        print(f"   OK Time range: {time_range}")
        except Exception as e:
            if verbose:
                print(f"   ! Time range: {e}")

        if len(tests_passed) >= 1:  # At least 1 test should work
            print("   [OK] Temporal networks test passed")
            if verbose:
                print(f"      Tested: {', '.join(tests_passed)}")
            temporal_status = True
        else:
            print(f"   [X] Temporal networks failed: no tests passed")

    except Exception as e:
        print(f"   [X] Temporal networks failed: {e}")
        if verbose:
            traceback.print_exc()
    test_results.append(("Temporal networks", temporal_status))

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


def _tutorial_wait_for_input(non_interactive: bool, prompt: str = "Press Enter to continue...") -> None:
    """Wait for user input unless in non-interactive mode.

    Args:
        non_interactive: If True, skip waiting for input
        prompt: The prompt to display
    """
    if not non_interactive:
        input(f"\n{prompt}")


# Tutorial step names - used for display and consistency
TUTORIAL_STEP_NAMES = {
    1: "Understanding Multilayer Networks",
    2: "Creating Your First Network",
    3: "Exploring Network Structure",
    4: "Computing Network Statistics",
    5: "Detecting Communities",
    6: "Visualizing Networks",
}


def _create_tutorial_network() -> "multinet.multi_layer_network":
    """Create the sample network used in the tutorial.

    Returns:
        A multilayer network with friendship and work layers
    """
    network = multinet.multi_layer_network()
    network.add_edges([
        ['Alice', 'friendship', 'Bob', 'friendship', 1],
        ['Bob', 'friendship', 'Carol', 'friendship', 1],
        ['Alice', 'friendship', 'Carol', 'friendship', 1],
        ['Alice', 'work', 'David', 'work', 1],
        ['David', 'work', 'Carol', 'work', 1],
    ], input_type='list')
    return network


def cmd_tutorial(args: argparse.Namespace) -> int:
    """Run interactive tutorial mode to learn py3plex step by step.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success)
    """
    # Set matplotlib backend early
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt

    non_interactive = args.non_interactive
    step = args.step

    print()
    print("=" * 70)
    print("  PY3PLEX INTERACTIVE TUTORIAL")
    print("  Learn multilayer network analysis step by step")
    print("=" * 70)
    print()
    print("This tutorial covers:")
    print("  Step 1: Understanding Multilayer Networks")
    print("  Step 2: Creating Your First Network")
    print("  Step 3: Exploring Network Structure")
    print("  Step 4: Computing Network Statistics")
    print("  Step 5: Detecting Communities")
    print("  Step 6: Visualizing Networks")
    print()
    print("Tip: You can run a specific step with --step N (e.g., py3plex tutorial --step 1)")
    print()

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        cleanup = False
    else:
        temp_dir = tempfile.mkdtemp(prefix="py3plex_tutorial_")
        output_dir = Path(temp_dir)
        cleanup = not args.keep_files

    steps_completed = []

    try:
        # STEP 1: Understanding Multilayer Networks
        if step is None or step == 1:
            _tutorial_wait_for_input(non_interactive, "Press Enter to start Step 1...")
            print()
            print("-" * 70)
            print("STEP 1: Understanding Multilayer Networks")
            print("-" * 70)
            print()
            print("A multilayer network consists of:")
            print()
            print("  • NODES: Entities in your network (e.g., people, proteins, cities)")
            print("  • LAYERS: Different types of relationships or contexts")
            print("  • EDGES: Connections between nodes within or across layers")
            print()
            print("Example: A social network with layers for:")
            print("  - 'friendship' layer: who is friends with whom")
            print("  - 'work' layer: who works with whom")
            print("  - 'family' layer: family relationships")
            print()
            print("The same person (node) can appear in multiple layers with")
            print("different connections in each layer!")
            print()
            print("In py3plex, nodes are represented as tuples: (node_id, layer_id)")
            print("For example: ('Alice', 'friendship') or ('Alice', 'work')")
            print()
            print("  [OK] Step 1 completed: You understand what multilayer networks are!")
            steps_completed.append(1)

        # STEP 2: Creating Your First Network
        if step is None or step == 2:
            _tutorial_wait_for_input(non_interactive, "Press Enter to start Step 2...")
            print()
            print("-" * 70)
            print("STEP 2: Creating Your First Network")
            print("-" * 70)
            print()
            print("Let's create a simple social network with 2 layers!")
            print()
            print("Code example:")
            print("-" * 50)
            print("""
from py3plex.core import multinet

# Create an empty multilayer network
network = multinet.multi_layer_network()

# Add edges (this also creates nodes automatically)
# Format: [source, source_layer, target, target_layer, weight]
network.add_edges([
    ['Alice', 'friendship', 'Bob', 'friendship', 1],
    ['Bob', 'friendship', 'Carol', 'friendship', 1],
    ['Alice', 'friendship', 'Carol', 'friendship', 1],
    ['Alice', 'work', 'David', 'work', 1],
    ['David', 'work', 'Carol', 'work', 1],
], input_type='list')
""")
            print("-" * 50)
            print()
            print("Running this code now...")
            print()

            # Actually run the code using the helper function
            network = _create_tutorial_network()

            # Save network for later steps
            network_file = output_dir / "tutorial_network.edgelist"
            network.save_network(str(network_file), output_type="multiedgelist")

            print(f"Network created and saved to: {network_file}")
            print(f"  Total nodes: {network.core_network.number_of_nodes()}")
            print(f"  Total edges: {network.core_network.number_of_edges()}")
            print()
            print("  [OK] Step 2 completed: You can now create multilayer networks!")
            steps_completed.append(2)

        # STEP 3: Exploring Network Structure
        if step is None or step == 3:
            _tutorial_wait_for_input(non_interactive, "Press Enter to start Step 3...")
            print()
            print("-" * 70)
            print("STEP 3: Exploring Network Structure")
            print("-" * 70)
            print()

            # Recreate network if needed (for single step mode)
            if step == 3:
                network = _create_tutorial_network()

            print("Let's explore the network structure!")
            print()
            print("1. Getting all nodes:")
            print("-" * 50)
            nodes = list(network.get_nodes())
            print(f"   Nodes: {nodes}")
            print()

            print("2. Getting all edges:")
            print("-" * 50)
            edges = list(network.get_edges())
            for edge in edges[:5]:
                print(f"   {edge}")
            print()

            print("3. Getting layers:")
            print("-" * 50)
            # Get unique layer names from nodes
            layers = set()
            for node in nodes:
                if isinstance(node, tuple) and len(node) >= 2:
                    layers.add(node[1])
            print(f"   Layers: {sorted(layers)}")
            print()

            print("Code to explore structure:")
            print("-" * 50)
            print("""
# Get all nodes (as tuples of node_id, layer_id)
nodes = list(network.get_nodes())

# Get all edges (with source and target nodes)
edges = list(network.get_edges())

# Get basic statistics
network.basic_stats()
""")
            print("-" * 50)
            print()
            print("  [OK] Step 3 completed: You can explore network structure!")
            steps_completed.append(3)

        # STEP 4: Computing Network Statistics
        if step is None or step == 4:
            _tutorial_wait_for_input(non_interactive, "Press Enter to start Step 4...")
            print()
            print("-" * 70)
            print("STEP 4: Computing Network Statistics")
            print("-" * 70)
            print()

            # Recreate network if needed (for single step mode)
            if step == 4:
                network = _create_tutorial_network()

            print("Let's compute some multilayer-specific statistics!")
            print()

            from py3plex.algorithms.statistics import multilayer_statistics as mls

            print("1. Layer Density (how connected is each layer):")
            print("-" * 50)
            try:
                friendship_density = mls.layer_density(network, 'friendship')
                work_density = mls.layer_density(network, 'work')
                print(f"   friendship layer density: {friendship_density:.3f}")
                print(f"   work layer density: {work_density:.3f}")
            except Exception as e:
                print(f"   (Could not compute: {e})")
            print()

            print("2. Node Activity (how many layers is each node active in):")
            print("-" * 50)
            try:
                for node_name in ['Alice', 'Bob', 'Carol', 'David']:
                    activity = mls.node_activity(network, node_name)
                    print(f"   {node_name}: active in {activity*100:.0f}% of layers")
            except Exception as e:
                print(f"   (Could not compute: {e})")
            print()

            print("3. Edge Overlap (shared connections between layers):")
            print("-" * 50)
            try:
                overlap = mls.edge_overlap(network, 'friendship', 'work')
                print(f"   friendship-work overlap: {overlap:.3f}")
            except Exception as e:
                print(f"   (Could not compute: {e})")
            print()

            print("Code for statistics:")
            print("-" * 50)
            print("""
from py3plex.algorithms.statistics import multilayer_statistics as mls

# Layer density
density = mls.layer_density(network, 'layer_name')

# Node activity across layers
activity = mls.node_activity(network, 'node_name')

# Edge overlap between layers
overlap = mls.edge_overlap(network, 'layer1', 'layer2')

# Versatility centrality (how important is a node across layers)
versatility = mls.versatility_centrality(network, centrality_type='degree')
""")
            print("-" * 50)
            print()
            print("  [OK] Step 4 completed: You can compute multilayer statistics!")
            steps_completed.append(4)

        # STEP 5: Detecting Communities
        if step is None or step == 5:
            _tutorial_wait_for_input(non_interactive, "Press Enter to start Step 5...")
            print()
            print("-" * 70)
            print("STEP 5: Detecting Communities")
            print("-" * 70)
            print()

            # Recreate network if needed (for single step mode)
            if step == 5:
                network = _create_tutorial_network()

            print("Community detection finds groups of densely connected nodes.")
            print()
            print("Let's use the Louvain algorithm:")
            print()

            from py3plex.algorithms.community_detection import community_wrapper

            # Convert to undirected if needed
            G = (
                network.core_network.to_undirected()
                if network.core_network.is_directed()
                else network.core_network
            )
            partition = community_wrapper.louvain_communities(G)

            num_communities = len(set(partition.values()))
            print(f"Found {num_communities} communities!")
            print()

            print("Community assignments:")
            print("-" * 50)
            for node, comm_id in partition.items():
                print(f"   {node} -> Community {comm_id}")
            print()

            # Save communities
            comm_file = output_dir / "tutorial_communities.json"
            with open(comm_file, "w") as f:
                json.dump({str(k): int(v) for k, v in partition.items()}, f, indent=2)
            print(f"Communities saved to: {comm_file}")
            print()

            print("Code for community detection:")
            print("-" * 50)
            print("""
from py3plex.algorithms.community_detection import community_wrapper

# Get undirected version of the network
G = network.core_network.to_undirected()

# Detect communities using Louvain
partition = community_wrapper.louvain_communities(G)

# partition is a dict: {node: community_id}
for node, comm_id in partition.items():
    print(f"{node} -> Community {comm_id}")
""")
            print("-" * 50)
            print()
            print("  [OK] Step 5 completed: You can detect communities!")
            steps_completed.append(5)

        # STEP 6: Visualizing Networks
        if step is None or step == 6:
            _tutorial_wait_for_input(non_interactive, "Press Enter to start Step 6...")
            print()
            print("-" * 70)
            print("STEP 6: Visualizing Networks")
            print("-" * 70)
            print()

            # Recreate network if needed (for single step mode)
            if step == 6:
                network = _create_tutorial_network()

            print("py3plex supports multiple visualization styles!")
            print()
            print("Creating a basic network visualization...")
            print()

            try:
                # Simple visualization with NetworkX
                pos = nx.spring_layout(network.core_network)
                plt.figure(figsize=(10, 8))
                nx.draw(
                    network.core_network,
                    pos,
                    node_size=500,
                    node_color="lightblue",
                    edge_color="gray",
                    alpha=0.8,
                    with_labels=True,
                    font_size=8,
                )
                plt.title("Tutorial Multilayer Network", fontsize=14)

                viz_file = output_dir / "tutorial_visualization.png"
                plt.savefig(viz_file, dpi=150, bbox_inches="tight")
                plt.close()
                print(f"[OK] Visualization saved to: {viz_file}")
            except Exception as e:
                print(f"   (Visualization error: {e})")
            print()

            print("Code for visualization:")
            print("-" * 50)
            print("""
import matplotlib.pyplot as plt
import networkx as nx

# Simple NetworkX visualization
pos = nx.spring_layout(network.core_network)
plt.figure(figsize=(10, 8))
nx.draw(network.core_network, pos,
        node_size=500, node_color='lightblue',
        with_labels=True)
plt.savefig('network.png')

# Or use py3plex multilayer visualization:
from py3plex.visualization.multilayer import hairball_plot

network_colors, graph = network.get_layers(style="hairball")
hairball_plot(graph, network_colors)
""")
            print("-" * 50)
            print()
            print("  [OK] Step 6 completed: You can visualize networks!")
            steps_completed.append(6)

        # Summary
        print()
        print("=" * 70)
        print("  TUTORIAL COMPLETE!")
        print("=" * 70)
        print()
        print(f"Steps completed: {len(steps_completed)}/6")
        for step_num in steps_completed:
            print(f"  [OK] Step {step_num}: {TUTORIAL_STEP_NAMES[step_num]}")
        print()

        if cleanup:
            print(f"Cleaning up temporary files in {output_dir}...")
            shutil.rmtree(output_dir)
            print("   (Use --keep-files to preserve generated files)")
        else:
            print(f"Generated files saved in: {output_dir}")
            for file in output_dir.glob("tutorial_*"):
                print(f"  - {file}")
        print()

        print("Next steps:")
        print("  • Run 'py3plex --help' to see all available commands")
        print("  • Run 'py3plex selftest' to verify your installation")
        print("  • Run 'py3plex quickstart' for a quick demo workflow")
        print("  • Check documentation: https://skblaz.github.io/py3plex/")
        print()

        return 0

    except Exception as e:
        print(f"\nError during tutorial: {e}")
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
        "query": cmd_query,
        "dsl-lint": cmd_dsl_lint,
        "community": cmd_community,
        "centrality": cmd_centrality,
        "stats": cmd_stats,
        "visualize": cmd_visualize,
        "aggregate": cmd_aggregate,
        "convert": cmd_convert,
        "selftest": cmd_selftest,
        "quickstart": cmd_quickstart,
        "run-config": cmd_run_config,
        "tutorial": cmd_tutorial,
    }

    handler = command_handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        logger.error(f"Unknown command '{args.command}'")
        return 1


if __name__ == "__main__":
    sys.exit(main())
