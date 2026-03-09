"""
Zero-loss network serialization with Arrow and Parquet formats.

Demonstrates the new save_to_arrow/load_from_arrow and 
save_network_to_parquet/load_network_from_parquet functions that preserve
multilayer identity, attributes, network type, and directedness.

Runtime: FAST (< 5 seconds) - Standalone example suitable for CI
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add repository root to path for imports when running from a source checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from py3plex.core import multinet


def _require_pyarrow() -> bool:
    """Return True if pyarrow is available, printing a hint otherwise."""
    try:
        import pyarrow  # noqa: F401
    except ImportError:
        print("Warning: pyarrow not installed. Install with: pip install 'py3plex[arrow]'")
        return False
    return True


def create_multilayer_network() -> multinet.multi_layer_network:
    """Create a multilayer network with various attribute types."""
    net = multinet.multi_layer_network(directed=False)
    
    # Add nodes with different attribute types
    net.add_nodes([
        # Scalar attributes
        {'source': 'Alice', 'type': 'social', 'age': 30, 'active': True},
        {'source': 'Bob', 'type': 'social', 'age': 25, 'active': False},
        {'source': 'Carol', 'type': 'work', 'level': 5},
        
        # Complex attributes (will be JSON-encoded)
        {'source': 'Alice', 'type': 'work', 
         'tags': ['researcher', 'python'], 
         'metadata': {'department': 'CS', 'projects': ['A', 'B']}},
    ])
    
    # Add edges with attributes
    net.add_edges([
        # Intra-layer edges
        {'source': 'Alice', 'target': 'Bob', 
         'source_type': 'social', 'target_type': 'social',
         'weight': 1.5, 'timestamp': '2024-01-01'},
        
        {'source': 'Alice', 'target': 'Carol', 
         'source_type': 'work', 'target_type': 'work',
         'weight': 2.0, 'collaboration': ['project1', 'project2']},
        
        # Inter-layer edge
        {'source': 'Bob', 'target': 'Carol', 
         'source_type': 'social', 'target_type': 'work',
         'weight': 0.5},
    ])
    
    return net


def _normalize_attrs(attrs: dict) -> dict:
    """Normalize attrs so equality checks are stable across array/scalar wrappers."""
    normalized = {}
    for key, value in attrs.items():
        if key == "pos":
            continue
        if hasattr(value, "tolist"):
            normalized[key] = value.tolist()
        else:
            normalized[key] = value
    return normalized


def _layer_names(net: multinet.multi_layer_network) -> list[str]:
    """Return sorted layer names without comparing backend graph objects."""
    layers_info = net.get_layers()
    if isinstance(layers_info, tuple):
        return sorted(layers_info[0])
    return sorted(layers_info)


def example_arrow_roundtrip() -> None:
    """Example: Arrow format preserves everything."""
    print("=== Arrow Format (Single File) ===")
    
    from py3plex.io import save_to_arrow, load_from_arrow
    
    net = create_multilayer_network()
    
    print(f"Original network:")
    print(f"  Nodes: {len(list(net.get_nodes()))}")
    print(f"  Edges: {len(list(net.get_edges()))}")
    print(f"  Layers: {_layer_names(net)}")
    print(f"  Directed: {net.directed}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "network.arrow"
        
        # Save
        print(f"\nSaving to {filepath}...")
        save_to_arrow(net, str(filepath))
        
        # Load
        print(f"Loading from {filepath}...")
        loaded = load_from_arrow(str(filepath))
        
        # Verify preservation
        print(f"\nLoaded network:")
        print(f"  Nodes: {len(list(loaded.get_nodes()))}")
        print(f"  Edges: {len(list(loaded.get_edges()))}")
        print(f"  Layers: {_layer_names(loaded)}")
        print(f"  Directed: {loaded.directed}")
        
        # Check attributes
        print(f"\nAttribute preservation:")
        alice_social = dict(loaded.core_network.nodes[('Alice', 'social')])
        print(f"  Alice (social) age: {alice_social.get('age')}")
        print(f"  Alice (social) active: {alice_social.get('active')}")

        alice_work = dict(loaded.core_network.nodes[('Alice', 'work')])
        print(f"  Alice (work) tags: {alice_work.get('tags')}")
        print(f"  Alice (work) metadata: {alice_work.get('metadata')}")

        # Check edge attributes
        edge_attrs = loaded.core_network.get_edge_data(('Alice', 'social'), ('Bob', 'social'))[0]
        print(f"  Edge Alice-Bob weight: {edge_attrs.get('weight')}")
        print(f"  Edge Alice-Bob timestamp: {edge_attrs.get('timestamp')}")
        
        assert len(list(loaded.get_nodes())) == len(list(net.get_nodes()))
        assert len(list(loaded.get_edges())) == len(list(net.get_edges()))
        assert alice_social.get("age") == 30
        assert alice_social.get("active") is True
        assert alice_work.get("tags") == ["researcher", "python"]
        assert alice_work.get("metadata") == {
            "department": "CS",
            "projects": ["A", "B"],
        }
        assert edge_attrs.get("weight") == 1.5
        assert edge_attrs.get("timestamp") == "2024-01-01"

        print(f"\nOK All attributes preserved!")


def example_parquet_roundtrip() -> None:
    """Example: Parquet directory format."""
    print("\n=== Parquet Format (Directory) ===")
    
    from py3plex.io import save_network_to_parquet, load_network_from_parquet
    
    net = create_multilayer_network()
    
    print(f"Original network:")
    print(f"  Nodes: {len(list(net.get_nodes()))}")
    print(f"  Edges: {len(list(net.get_edges()))}")
    print(f"  Layers: {_layer_names(net)}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dirpath = Path(tmpdir) / "network_dir"
        
        # Save
        print(f"\nSaving to {dirpath}/...")
        save_network_to_parquet(net, str(dirpath))
        
        # Show directory structure
        print(f"\nDirectory contents:")
        for file in sorted(dirpath.iterdir()):
            size = file.stat().st_size
            print(f"  {file.name:20} ({size:,} bytes)")
        
        # Load
        print(f"\nLoading from {dirpath}/...")
        loaded = load_network_from_parquet(str(dirpath))
        
        # Verify preservation
        print(f"\nLoaded network:")
        print(f"  Nodes: {len(list(loaded.get_nodes()))}")
        print(f"  Edges: {len(list(loaded.get_edges()))}")
        print(f"  Layers: {_layer_names(loaded)}")
        
        print(f"\nOK Parquet roundtrip successful!")


def example_query_result_parquet() -> None:
    """Example: Export QueryResult to Parquet."""
    print("\n=== QueryResult Parquet Export ===")
    
    from py3plex.dsl import Q, save_to_parquet, load_from_parquet
    
    net = create_multilayer_network()
    
    # Compute statistics
    print("Computing node statistics...")
    result = (
        Q.nodes()
         .compute("degree")
         .execute(net)
    )
    
    print(f"Result: {result.count} items")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "node_stats.parquet"
        
        # Save
        print(f"\nSaving to {filepath}...")
        save_to_parquet(result, str(filepath))
        
        # Load
        print(f"Loading from {filepath}...")
        df = load_from_parquet(str(filepath))
        
        print(f"\nLoaded DataFrame:")
        print(df)
        
        print(f"\nOK QueryResult export successful!")


def example_network_comparison() -> None:
    """Example: Verify semantic equality after roundtrip."""
    print("\n=== Network Semantic Equality ===")
    
    from py3plex.io import save_to_arrow, load_from_arrow
    
    net1 = create_multilayer_network()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "network.arrow"
        
        # Roundtrip
        save_to_arrow(net1, str(filepath))
        net2 = load_from_arrow(str(filepath))
        
        # Compare
        print("Comparing original and loaded networks:")
        
        # Node comparison
        nodes1 = set(net1.get_nodes())
        nodes2 = set(net2.get_nodes())
        print(f"  Nodes equal: {nodes1 == nodes2}")
        
        # Edge comparison
        edges1 = set(net1.get_edges())
        edges2 = set(net2.get_edges())
        print(f"  Edges equal: {edges1 == edges2}")
        
        # Metadata comparison
        print(f"  Directed equal: {net1.directed == net2.directed}")
        print(f"  Layers equal: {_layer_names(net1) == _layer_names(net2)}")
        
        # Attribute comparison
        attrs_match = True
        for node, layer in net1.get_nodes():
            attrs1 = _normalize_attrs(dict(net1.core_network.nodes[(node, layer)]))
            attrs2 = _normalize_attrs(dict(net2.core_network.nodes[(node, layer)]))
            if attrs1 != attrs2:
                attrs_match = False
                print(f"  Attribute mismatch for ({node}, {layer})")
                print(f"    Original: {attrs1}")
                print(f"    Loaded: {attrs2}")
        
        print(f"  Attributes equal: {attrs_match}")
        
        assert nodes1 == nodes2
        assert edges1 == edges2
        assert attrs_match
        print(f"\nOK Networks are semantically identical!")


def main() -> int:
    """Run all examples."""
    print("py3plex Zero-Loss Serialization Examples")
    print("=" * 60)
    print()
    
    arrow_available = _require_pyarrow()
    if not arrow_available:
        print("Skipping examples; install pyarrow to run them.")
        return 0
    
    for step in (
        example_arrow_roundtrip,
        example_parquet_roundtrip,
        example_query_result_parquet,
        example_network_comparison,
    ):
        step()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("\nKey Features:")
    print("  - Zero-loss preservation of multilayer identity")
    print("  - Attribute type preservation (int, float, bool, str)")
    print("  - Complex attributes (dict, list) via JSON encoding")
    print("  - Network metadata (directed, network_type, layers)")
    print("  - QueryResult export to Parquet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
