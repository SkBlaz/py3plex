"""
Serialize multilayer graphs with Apache Arrow and Parquet.

Covers Feather/Arrow and Parquet saves, a JSON comparison, and a lightweight
performance benchmark on a larger random graph. Prerequisites: py3plex installed;
pyarrow required for Arrow/Parquet sections (skipped if missing).

Runtime: FAST (< 5 seconds) - Standalone example suitable for CI
"""

from __future__ import annotations

import random
import sys
import tempfile
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from py3plex.io import Edge, Layer, MultiLayerGraph, Node, read, write

DEFAULT_SEED = 42


def _require_pyarrow() -> bool:
    """Return True if pyarrow is available, printing a hint otherwise."""
    try:
        import pyarrow  # noqa: F401
    except ImportError:
        print("Warning: pyarrow not installed. Install with: pip install 'py3plex[arrow]'")
        return False
    return True


def create_sample_network() -> MultiLayerGraph:
    """Create a sample multilayer social network."""
    graph = MultiLayerGraph(
        directed=True,
        attributes={
            "name": "Multi-platform Social Network",
            "description": "User interactions across multiple platforms",
            "created": "2024-01-01",
        },
    )

    # Add layers
    graph.add_layer(Layer(id="facebook", attributes={"platform": "Facebook"}))
    graph.add_layer(Layer(id="twitter", attributes={"platform": "Twitter"}))
    graph.add_layer(Layer(id="linkedin", attributes={"platform": "LinkedIn"}))

    # Add nodes (users)
    users = [
        ("alice", {"age": 28, "occupation": "Engineer", "city": "San Francisco"}),
        ("bob", {"age": 32, "occupation": "Designer", "city": "New York"}),
        ("charlie", {"age": 35, "occupation": "Manager", "city": "Seattle"}),
        ("diana", {"age": 29, "occupation": "Scientist", "city": "Boston"}),
        ("eve", {"age": 31, "occupation": "Writer", "city": "Austin"}),
    ]

    for user_id, attrs in users:
        graph.add_node(Node(id=user_id, attributes=attrs))

    # Add intra-layer edges
    edges = [
        # Facebook
        ("alice", "bob", "facebook", "facebook", 0.9),
        ("alice", "charlie", "facebook", "facebook", 0.8),
        ("bob", "charlie", "facebook", "facebook", 0.7),
        # Twitter
        ("charlie", "diana", "twitter", "twitter", 0.85),
        ("diana", "eve", "twitter", "twitter", 0.75),
        # LinkedIn
        ("bob", "diana", "linkedin", "linkedin", 0.65),
        ("charlie", "eve", "linkedin", "linkedin", 0.7),
    ]

    for src, dst, src_layer, dst_layer, weight in edges:
        graph.add_edge(
            Edge(
                src=src,
                dst=dst,
                src_layer=src_layer,
                dst_layer=dst_layer,
                attributes={"weight": weight},
            )
        )

    # Add inter-layer edges
    inter_edges = [
        ("alice", "diana", "facebook", "twitter", 0.6),
        ("bob", "eve", "twitter", "linkedin", 0.55),
    ]

    for src, dst, src_layer, dst_layer, weight in inter_edges:
        graph.add_edge(
            Edge(
                src=src,
                dst=dst,
                src_layer=src_layer,
                dst_layer=dst_layer,
                attributes={"weight": weight},
            )
        )

    return graph


def example_arrow_feather() -> None:
    """Example: Save and load with Arrow (Feather) format."""
    print("=== Arrow (Feather) Format ===")

    graph = create_sample_network()

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "network.arrow"

        # Write to Arrow format
        print(f"Writing graph to {filepath}...")
        start = time.time()
        write(graph, filepath, format="arrow")
        write_time = time.time() - start
        print(f"Write time: {write_time:.4f} seconds")

        # Check file sizes
        total_size = sum(p.stat().st_size for p in Path(tmpdir).iterdir())
        print(f"Total file size: {total_size:,} bytes")

        # Read from Arrow format
        print(f"Reading graph from {filepath}...")
        start = time.time()
        loaded_graph = read(filepath, format="arrow")
        read_time = time.time() - start
        print(f"Read time: {read_time:.4f} seconds")

        # Verify
        print(
            f"Loaded: {len(loaded_graph.nodes)} nodes, "
            f"{len(loaded_graph.layers)} layers, "
            f"{len(loaded_graph.edges)} edges"
        )
        print()


def example_parquet() -> None:
    """Example: Save and load with Parquet format."""
    print("=== Parquet Format ===")

    graph = create_sample_network()

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "network.parquet"

        # Write to Parquet format (compressed)
        print(f"Writing graph to {filepath}...")
        start = time.time()
        write(graph, filepath, format="parquet")
        write_time = time.time() - start
        print(f"Write time: {write_time:.4f} seconds")

        # Check file sizes
        total_size = sum(p.stat().st_size for p in Path(tmpdir).iterdir())
        print(f"Total file size: {total_size:,} bytes (compressed)")

        # Read from Parquet format
        print(f"Reading graph from {filepath}...")
        start = time.time()
        loaded_graph = read(filepath, format="parquet")
        read_time = time.time() - start
        print(f"Read time: {read_time:.4f} seconds")

        # Verify
        print(
            f"Loaded: {len(loaded_graph.nodes)} nodes, "
            f"{len(loaded_graph.layers)} layers, "
            f"{len(loaded_graph.edges)} edges"
        )
        print()


def example_format_comparison() -> None:
    """Compare Arrow with JSON format."""
    print("=== Format Comparison ===")

    graph = create_sample_network()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        arrow_path = tmpdir_path / "network.arrow"
        parquet_path = tmpdir_path / "network.parquet"
        json_path = tmpdir_path / "network.json"

        # Write all formats
        print("Writing to Arrow (Feather)...")
        start = time.time()
        write(graph, arrow_path, format="arrow")
        arrow_write_time = time.time() - start

        print("Writing to Parquet...")
        start = time.time()
        write(graph, parquet_path, format="parquet")
        parquet_write_time = time.time() - start

        print("Writing to JSON...")
        start = time.time()
        write(graph, json_path, format="json")
        json_write_time = time.time() - start

        # Read all formats
        print("\nReading from Arrow (Feather)...")
        start = time.time()
        arrow_graph = read(arrow_path, format="arrow")
        arrow_read_time = time.time() - start

        print("Reading from Parquet...")
        start = time.time()
        parquet_graph = read(parquet_path, format="parquet")
        parquet_read_time = time.time() - start

        print("Reading from JSON...")
        start = time.time()
        json_graph = read(json_path, format="json")
        json_read_time = time.time() - start

        # Get file sizes
        arrow_size = sum(
            p.stat().st_size for p in tmpdir_path.iterdir() if "arrow" in p.name
        )
        parquet_size = sum(
            p.stat().st_size for p in tmpdir_path.iterdir() if "parquet" in p.name
        )
        json_size = json_path.stat().st_size

        # Print comparison
        print("\n" + "=" * 60)
        print("Format Comparison Results:")
        print("=" * 60)
        print(f"{'Format':<15} {'Write (s)':<12} {'Read (s)':<12} {'Size (bytes)':<15}")
        print("-" * 60)
        print(
            f"{'Arrow':<15} {arrow_write_time:<12.4f} {arrow_read_time:<12.4f} {arrow_size:<15,}"
        )
        print(
            f"{'Parquet':<15} {parquet_write_time:<12.4f} {parquet_read_time:<12.4f} {parquet_size:<15,}"
        )
        print(
            f"{'JSON':<15} {json_write_time:<12.4f} {json_read_time:<12.4f} {json_size:<15,}"
        )
        print("=" * 60)

        # Speedup
        if json_write_time > 0:
            print(
                f"\nArrow write speedup vs JSON: {json_write_time/arrow_write_time:.2f}x"
            )
            print(
                f"Arrow read speedup vs JSON: {json_read_time/arrow_read_time:.2f}x"
            )
            print(f"Parquet compression vs JSON: {json_size/parquet_size:.2f}x")

        # Verify all formats produce same result
        assert len(arrow_graph.nodes) == len(json_graph.nodes)
        assert len(arrow_graph.edges) == len(json_graph.edges)
        print("\n All formats produce identical results")


def example_large_graph_performance() -> None:
    """Demonstrate performance on a larger graph."""
    print("\n=== Large Graph Performance ===")

    # Create a larger graph
    print("Creating large graph...")
    graph = MultiLayerGraph()

    # Add layers
    for i in range(10):
        graph.add_layer(Layer(id=f"layer_{i}"))

    # Add nodes
    for i in range(1000):
        graph.add_node(Node(id=f"node_{i}", attributes={"index": i, "data": i * 2}))

    # Add edges
    random.seed(DEFAULT_SEED)
    edges_added = set()
    for i in range(5000):
        src = f"node_{random.randint(0, 999)}"
        dst = f"node_{random.randint(0, 999)}"
        layer = f"layer_{random.randint(0, 9)}"
        edge_key = (src, dst, layer, layer, 0)
        if src != dst and edge_key not in edges_added:
            graph.add_edge(
                Edge(
                    src=src,
                    dst=dst,
                    src_layer=layer,
                    dst_layer=layer,
                    attributes={"weight": random.random()},
                )
            )
            edges_added.add(edge_key)

    print(
        f"Created graph: {len(graph.nodes)} nodes, "
        f"{len(graph.layers)} layers, "
        f"{len(graph.edges)} edges"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        arrow_path = tmpdir_path / "large.arrow"
        json_path = tmpdir_path / "large.json"

        # Benchmark Arrow
        print("\nBenchmarking Arrow...")
        start = time.time()
        write(graph, arrow_path, format="arrow")
        arrow_write = time.time() - start

        start = time.time()
        read(arrow_path, format="arrow")
        arrow_read = time.time() - start

        arrow_size = sum(
            p.stat().st_size for p in tmpdir_path.iterdir() if "arrow" in p.name
        )

        # Benchmark JSON
        print("Benchmarking JSON...")
        start = time.time()
        write(graph, json_path, format="json")
        json_write = time.time() - start

        start = time.time()
        read(json_path, format="json")
        json_read = time.time() - start

        json_size = json_path.stat().st_size

        # Results
        print("\n" + "=" * 60)
        print("Large Graph Performance Results:")
        print("=" * 60)
        print(f"{'Format':<15} {'Write (s)':<12} {'Read (s)':<12} {'Size (MB)':<15}")
        print("-" * 60)
        print(
            f"{'Arrow':<15} {arrow_write:<12.4f} {arrow_read:<12.4f} {arrow_size/1024/1024:<15.2f}"
        )
        print(
            f"{'JSON':<15} {json_write:<12.4f} {json_read:<12.4f} {json_size/1024/1024:<15.2f}"
        )
        print("=" * 60)
        print(f"Arrow write speedup: {json_write/arrow_write:.2f}x faster")
        print(f"Arrow read speedup: {json_read/arrow_read:.2f}x faster")
        print(f"Arrow size reduction: {json_size/arrow_size:.2f}x smaller")


def main() -> int:
    """Run all examples."""
    print("py3plex Apache Arrow Serialization Examples")
    print("=" * 60)
    print()

    arrow_available = _require_pyarrow()
    if not arrow_available:
        print("Skipping Arrow/Parquet sections; install pyarrow to run them.\n")
        return 0

    for step in (
        example_arrow_feather,
        example_parquet,
        example_format_comparison,
        example_large_graph_performance,
    ):
        step()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("\nKey Benefits of Apache Arrow:")
    print("  - Fast: Columnar format optimized for reading/writing")
    print("  - Compact: Efficient binary encoding, especially with Parquet")
    print("  - Interoperable: Works with pandas, polars, R, Julia, etc.")
    print("  - Type-safe: Schema preservation with strong typing")
    print("  - Standard: Industry-standard format for data interchange")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
