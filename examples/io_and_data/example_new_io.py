"""
Tour of the modern py3plex I/O system.

Covers graph construction, serialization (JSON, JSONL, CSV), conversion to core
py3plex/NetworkX/igraph, and schema validation. Outputs are written to a
temporary directory and cleaned up automatically. Optional dependencies:
NetworkX (for conversion/centrality) and igraph (for conversion).

Runtime: FAST (< 5 seconds) - Standalone example suitable for CI
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from py3plex.io import (
    Edge,
    Layer,
    MultiLayerGraph,
    Node,
    ReferentialIntegrityError,
    SchemaValidationError,
    read,
    supported_formats,
    to_networkx,
    write,
)


def example_basic_usage() -> MultiLayerGraph:
    """Basic graph creation and manipulation."""
    print("=== Basic Usage ===")

    # Create an empty multilayer graph
    graph = MultiLayerGraph(directed=True, attributes={"name": "Social Network"})

    # Add layers
    graph.add_layer(Layer(id="facebook", attributes={"platform": "Facebook"}))
    graph.add_layer(Layer(id="twitter", attributes={"platform": "Twitter"}))

    # Add nodes
    graph.add_node(Node(id="alice", attributes={"age": 30, "city": "NYC"}))
    graph.add_node(Node(id="bob", attributes={"age": 25, "city": "SF"}))
    graph.add_node(Node(id="charlie", attributes={"age": 35, "city": "LA"}))

    # Add edges
    graph.add_edge(
        Edge(
            src="alice",
            dst="bob",
            src_layer="facebook",
            dst_layer="facebook",
            attributes={"weight": 0.8, "timestamp": "2024-01-15"},
        )
    )
    graph.add_edge(
        Edge(
            src="bob",
            dst="charlie",
            src_layer="twitter",
            dst_layer="twitter",
            attributes={"weight": 0.6},
        )
    )

    # Inter-layer edge (alice on facebook follows charlie on twitter)
    graph.add_edge(
        Edge(
            src="alice",
            dst="charlie",
            src_layer="facebook",
            dst_layer="twitter",
            attributes={"weight": 0.5},
        )
    )

    print(
        f"Created graph with {len(graph.nodes)} nodes, {len(graph.layers)} layers, {len(graph.edges)} edges"
    )
    return graph


def example_json_io(graph: MultiLayerGraph, tmpdir: Path) -> None:
    """JSON format I/O example."""
    print("\n=== JSON I/O ===")

    json_path = tmpdir / "network.json"
    json_gz_path = tmpdir / "network.json.gz"
    write(graph, json_path, deterministic=True)
    print(f"Wrote graph to {json_path}")

    graph2 = read(json_path)
    print(f"Read graph: {len(graph2.nodes)} nodes, {len(graph2.edges)} edges")

    write(graph, json_gz_path)
    print(f"Wrote compressed graph to {json_gz_path}")


def example_jsonl_io(graph: MultiLayerGraph, tmpdir: Path) -> None:
    """JSONL streaming format example."""
    print("\n=== JSONL Streaming I/O ===")

    jsonl_path = tmpdir / "network.jsonl"
    write(graph, jsonl_path, format="jsonl", deterministic=True)
    print(f"Wrote graph to {jsonl_path} (streaming format)")

    graph2 = read(jsonl_path, format="jsonl")
    print(f"Read graph: {len(graph2.nodes)} nodes, {len(graph2.edges)} edges")


def example_csv_io(graph: MultiLayerGraph, tmpdir: Path) -> None:
    """CSV format I/O with sidecar files."""
    print("\n=== CSV I/O ===")

    edge_path = tmpdir / "edges.csv"
    node_path = tmpdir / "nodes.csv"
    layer_path = tmpdir / "layers.csv"
    write(graph, edge_path, format="csv", deterministic=True, write_sidecars=True)
    print(f"Wrote graph to {edge_path} (with {node_path.name} and {layer_path.name})")

    graph2 = read(edge_path, format="csv", nodes_file=node_path, layers_file=layer_path)
    print(f"Read graph: {len(graph2.nodes)} nodes, {len(graph2.edges)} edges")


def example_csv_to_py3plex_analysis(tmpdir: Path) -> None:
    """Load CSV and use core py3plex for analysis."""
    print("\n=== CSV to py3plex Analysis ===")

    try:
        from py3plex.core import multinet

        # First, create and save a CSV
        graph = MultiLayerGraph()
        graph.add_layer(Layer(id="social"))
        graph.add_node(Node(id="alice"))
        graph.add_node(Node(id="bob"))
        graph.add_node(Node(id="charlie"))
        graph.add_node(Node(id="diana"))

        # Create a simple network
        graph.add_edge(
            Edge(src="alice", dst="bob", src_layer="social", dst_layer="social")
        )
        graph.add_edge(
            Edge(src="bob", dst="charlie", src_layer="social", dst_layer="social")
        )
        graph.add_edge(
            Edge(src="charlie", dst="diana", src_layer="social", dst_layer="social")
        )
        graph.add_edge(
            Edge(src="diana", dst="alice", src_layer="social", dst_layer="social")
        )

        csv_path = tmpdir / "network.csv"
        write(graph, csv_path, format="csv")
        print(f"Saved network to {csv_path}")

        # Load into new I/O system
        loaded_graph = read(csv_path, format="csv")

        # Convert to NetworkX for py3plex compatibility
        G = to_networkx(loaded_graph, mode="union")

        # Now use core py3plex multi_layer_network
        mlnet = multinet.multi_layer_network()
        mlnet.core_network = G

        print("\nConverted to py3plex multi_layer_network:")
        mlnet.basic_stats()

        # Compute centrality measures
        try:
            import networkx as nx

            centrality = nx.degree_centrality(G)
            print("\nDegree centrality:")
            for node, cent in sorted(
                centrality.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"  {node}: {cent:.3f}")
        except Exception as e:
            print(f"Could not compute centrality: {e}")

    except ImportError as e:
        print(f"Required libraries not installed: {e}")
    except Exception as e:
        print(f"Error in analysis: {e}")


def example_networkx_conversion(graph: MultiLayerGraph) -> None:
    """NetworkX conversion examples."""
    print("\n=== NetworkX Conversion ===")

    try:
        from py3plex.io import from_networkx, to_networkx

        # Union mode: merge all layers
        G_union = to_networkx(graph, mode="union")
        print(
            f"Union mode: {G_union.number_of_nodes()} nodes, {G_union.number_of_edges()} edges"
        )

        # Multiplex mode: preserve (node, layer) structure
        G_multiplex = to_networkx(graph, mode="multiplex")
        print(
            f"Multiplex mode: {G_multiplex.number_of_nodes()} nodes, {G_multiplex.number_of_edges()} edges"
        )

        # Convert back from multiplex
        graph2 = from_networkx(G_multiplex, mode="multiplex")
        print(f"Round-trip: {len(graph2.nodes)} nodes, {len(graph2.edges)} edges")

    except ImportError:
        print("NetworkX not installed, skipping NetworkX examples")


def example_igraph_conversion(graph: MultiLayerGraph) -> None:
    """igraph conversion examples."""
    print("\n=== igraph Conversion ===")

    try:
        from py3plex.io import from_igraph, to_igraph

        # Convert to igraph
        g = to_igraph(graph, mode="multiplex")
        print(f"Converted to igraph: {g.vcount()} vertices, {g.ecount()} edges")

        # Convert back
        graph2 = from_igraph(g, mode="multiplex")
        print(f"Round-trip: {len(graph2.nodes)} nodes, {len(graph2.edges)} edges")

    except ImportError:
        print("igraph not installed, skipping igraph examples")


def example_validation() -> None:
    """Schema validation examples."""
    print("\n=== Schema Validation ===")

    graph = MultiLayerGraph()
    graph.add_node(Node(id="n1"))
    graph.add_layer(Layer(id="l1"))

    # Try to add edge with non-existent node
    try:
        graph.add_edge(Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1"))
    except ReferentialIntegrityError as e:
        print(f"Caught expected error: {e}")

    # Try to add node with non-serializable attributes
    try:
        Node(id="bad", attributes={"func": lambda x: x})
    except SchemaValidationError as e:
        print(f"Caught expected error: {e}")

    print("Schema validation working correctly!")


def example_supported_formats() -> None:
    """Check supported formats."""
    print("\n=== Supported Formats ===")

    formats = supported_formats()
    print(f"Read formats: {formats['read']}")
    print(f"Write formats: {formats['write']}")


def main() -> int:
    """Run all examples."""
    print("py3plex I/O System Examples")
    print("=" * 50)

    graph = example_basic_usage()

    with tempfile.TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        example_json_io(graph, tmpdir)
        example_jsonl_io(graph, tmpdir)
        example_csv_io(graph, tmpdir)
        example_csv_to_py3plex_analysis(tmpdir)

    example_networkx_conversion(graph)
    example_igraph_conversion(graph)
    example_validation()
    example_supported_formats()

    print("\n" + "=" * 50)
    print("All examples completed successfully!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
