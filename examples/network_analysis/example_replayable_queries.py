#!/usr/bin/env python
"""Example demonstrating replayable query provenance in py3plex.

This example shows how to:
1. Execute queries with replayable provenance
2. Check if a result is replayable
3. Replay a query to reproduce results
4. Export and load provenance bundles
"""

from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.provenance import replay_from_bundle


def create_sample_network():
    """Create a sample multilayer network."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes to different layers
    nodes = [
        {'source': f'Node_{i}', 'type': 'social'} for i in range(1, 11)
    ] + [
        {'source': f'Node_{i}', 'type': 'work'} for i in range(5, 16)
    ]
    network.add_nodes(nodes)
    
    # Add edges within layers
    edges = [
        {'source': f'Node_{i}', 'target': f'Node_{i+1}', 
         'source_type': 'social', 'target_type': 'social', 'weight': 1.0}
        for i in range(1, 10)
    ] + [
        {'source': f'Node_{i}', 'target': f'Node_{i+2}', 
         'source_type': 'work', 'target_type': 'work', 'weight': 1.0}
        for i in range(5, 14)
    ]
    network.add_edges(edges)
    
    return network


def demo_replayable_provenance():
    """Demonstrate basic replayable provenance."""
    print("=" * 70)
    print("Demo 1: Replayable Provenance")
    print("=" * 70)
    
    network = create_sample_network()
    
    # Execute query with replayable provenance
    print("\n1. Execute query with replayable provenance...")
    result = (
        Q.nodes()
         .provenance(mode="replayable", capture="auto", seed=42)
         .compute("degree", "betweenness_centrality")
         .execute(network, progress=False)
    )
    
    print(f"   Query returned {result.count} nodes")
    print(f"   Computed attributes: {list(result.attributes.keys())}")
    
    # Check if replayable
    print(f"\n2. Check if result is replayable...")
    print(f"   result.is_replayable = {result.is_replayable}")
    
    # Access provenance
    prov = result.provenance
    print(f"\n3. Provenance information:")
    print(f"   Schema version: {prov['schema_version']}")
    print(f"   Mode: {prov['mode']}")
    print(f"   Engine: {prov['query']['engine']}")
    print(f"   Network: {prov['network_capture']['node_count']} nodes, "
          f"{prov['network_capture']['edge_count']} edges")
    print(f"   Capture method: {prov['network_capture']['capture_method']}")
    
    print()


def demo_query_replay():
    """Demonstrate query replay."""
    print("=" * 70)
    print("Demo 2: Query Replay")
    print("=" * 70)
    
    network = create_sample_network()
    
    # Execute query with replayable provenance
    print("\n1. Execute original query...")
    result1 = (
        Q.nodes()
         .provenance(mode="replayable", capture="snapshot", seed=42)
         .compute("degree")
         .execute(network, progress=False)
    )
    
    print(f"   Original result: {result1.count} nodes")
    
    # Show a few degree values
    print("   Sample degree values:")
    for node in list(result1.items)[:3]:
        degree = result1.attributes['degree'].get(node, 0)
        print(f"     {node}: degree={degree}")
    
    # Replay the query
    print("\n2. Replay the query...")
    result2 = result1.replay(strict=False)
    
    print(f"   Replayed result: {result2.count} nodes")
    
    # Compare results
    print("\n3. Compare results...")
    print(f"   Item counts match: {result1.count == result2.count}")
    print(f"   Items match: {set(result1.items) == set(result2.items)}")
    
    # Check degree values match
    degrees_match = True
    for node in result1.items:
        deg1 = result1.attributes['degree'].get(node)
        deg2 = result2.attributes['degree'].get(node)
        if deg1 != deg2:
            degrees_match = False
            break
    
    print(f"   Degree values match: {degrees_match}")
    print()


def demo_bundle_export_import():
    """Demonstrate bundle export and import."""
    print("=" * 70)
    print("Demo 3: Bundle Export and Import")
    print("=" * 70)
    
    network = create_sample_network()
    
    # Execute query with replayable provenance
    print("\n1. Execute query with replayable provenance...")
    result1 = (
        Q.nodes()
         .reproducible(True, seed=42)  # Sugar for provenance(mode="replayable")
         .compute("degree", "betweenness_centrality")
         .execute(network, progress=False)
    )
    
    print(f"   Query returned {result1.count} nodes")
    
    # Export bundle
    bundle_path = "/tmp/query_result_bundle.json.gz"
    print(f"\n2. Export bundle to {bundle_path}...")
    result1.export_bundle(bundle_path, compress=True)
    
    # Check file size
    import os
    file_size = os.path.getsize(bundle_path)
    print(f"   Bundle size: {file_size} bytes ({file_size / 1024:.2f} KB)")
    
    # Load and replay from bundle
    print(f"\n3. Load and replay from bundle...")
    result2 = replay_from_bundle(bundle_path, strict=False)
    
    print(f"   Replayed result: {result2.count} nodes")
    
    # Compare results
    print("\n4. Verify results match...")
    print(f"   Item counts match: {result1.count == result2.count}")
    
    # Clean up
    os.remove(bundle_path)
    print(f"\n   (Bundle file cleaned up)")
    print()


def demo_reproducible_sugar():
    """Demonstrate the reproducible() convenience method."""
    print("=" * 70)
    print("Demo 4: Reproducible() Convenience Method")
    print("=" * 70)
    
    network = create_sample_network()
    
    # Using .reproducible() is equivalent to .provenance(mode="replayable", ...)
    print("\n1. Execute query with .reproducible(seed=42)...")
    result = (
        Q.nodes()
         .reproducible(True, seed=42)
         .compute("degree")
         .execute(network, progress=False)
    )
    
    print(f"   result.is_replayable = {result.is_replayable}")
    print(f"   Query returned {result.count} nodes")
    
    # Show that it works the same as provenance()
    print("\n2. Equivalent to .provenance(mode='replayable', seed=42)...")
    result2 = (
        Q.nodes()
         .provenance(mode="replayable", seed=42)
         .compute("degree")
         .execute(network, progress=False)
    )
    
    print(f"   result2.is_replayable = {result2.is_replayable}")
    print(f"   Results equivalent: {result.count == result2.count}")
    print()


def demo_backward_compatibility():
    """Demonstrate backward compatibility."""
    print("=" * 70)
    print("Demo 5: Backward Compatibility")
    print("=" * 70)
    
    network = create_sample_network()
    
    # Execute query without provenance config (legacy mode)
    print("\n1. Execute query without provenance config...")
    result = (
        Q.nodes()
         .compute("degree")
         .execute(network, progress=False)
    )
    
    print(f"   Query executed successfully")
    print(f"   result.is_replayable = {result.is_replayable} (uses log mode)")
    print(f"   result.provenance is not None = {result.provenance is not None}")
    
    # Access legacy provenance
    prov = result.provenance
    print(f"\n2. Legacy provenance still available:")
    print(f"   Engine: {prov.get('engine', 'N/A')}")
    print(f"   Has timing info: {'performance' in prov}")
    print()


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("py3plex Replayable Query Provenance Examples")
    print("Version 1.1.0")
    print("=" * 70 + "\n")
    
    demo_replayable_provenance()
    demo_query_replay()
    demo_bundle_export_import()
    demo_reproducible_sugar()
    demo_backward_compatibility()
    
    print("=" * 70)
    print("All demos complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
