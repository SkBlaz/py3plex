#!/usr/bin/env python
"""Demo script showing query provenance tracking in py3plex.

This script demonstrates the new provenance feature that tracks:
- Query execution metadata
- Performance timings
- Network fingerprints
- AST hashes for reproducibility
"""

from py3plex.core import multinet
from py3plex.dsl import Q
from py3plex.dsl_legacy import execute_query
import json


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


def demo_dsl_v2_provenance():
    """Demonstrate provenance tracking with DSL v2."""
    print("=" * 70)
    print("DSL v2 Provenance Demo")
    print("=" * 70)
    
    network = create_sample_network()
    
    # Execute a query with DSL v2
    query = Q.nodes().compute("degree", "betweenness_centrality")
    result = query.execute(network)
    
    # Access provenance
    prov = result.meta["provenance"]
    
    print(f"\nQuery Result Summary:")
    print(f"  Target: {result.target}")
    print(f"  Item count: {result.count}")
    print(f"  Computed attributes: {list(result.attributes.keys())}")
    
    print(f"\nProvenance Information:")
    print(f"  Engine: {prov['engine']}")
    print(f"  py3plex version: {prov['py3plex_version']}")
    print(f"  Timestamp: {prov['timestamp_utc']}")
    
    print(f"\nNetwork Fingerprint:")
    fp = prov['network_fingerprint']
    print(f"  Nodes: {fp['node_count']}")
    print(f"  Edges: {fp['edge_count']}")
    print(f"  Layers: {fp['layer_count']} ({', '.join(fp['layers'])})")
    
    print(f"\nQuery Information:")
    qi = prov['query']
    print(f"  Target: {qi['target']}")
    print(f"  AST Hash: {qi['ast_hash']}")
    print(f"  Summary: {qi['ast_summary']}")
    
    print(f"\nPerformance Breakdown:")
    perf = prov['performance']
    for stage, time_ms in sorted(perf.items()):
        if stage == "total_ms":
            print(f"  {stage}: {time_ms:.2f}ms (TOTAL)")
        else:
            print(f"  {stage}: {time_ms:.2f}ms")
    
    print()


def demo_legacy_dsl_provenance():
    """Demonstrate provenance tracking with legacy DSL."""
    print("=" * 70)
    print("Legacy DSL Provenance Demo")
    print("=" * 70)
    
    network = create_sample_network()
    
    # Execute a query with legacy DSL
    result = execute_query(network, 'SELECT nodes WHERE layer="social" COMPUTE degree')
    
    # Access provenance
    prov = result["meta"]["provenance"]
    
    print(f"\nQuery Result Summary:")
    print(f"  Target: {result.get('target', 'nodes')}")
    print(f"  Item count: {result['count']}")
    if 'computed' in result:
        print(f"  Computed measures: {list(result['computed'].keys())}")
    
    print(f"\nProvenance Information:")
    print(f"  Engine: {prov['engine']}")
    print(f"  py3plex version: {prov['py3plex_version']}")
    
    print(f"\nNetwork Fingerprint:")
    fp = prov['network_fingerprint']
    print(f"  Nodes: {fp['node_count']}")
    print(f"  Edges: {fp['edge_count']}")
    print(f"  Layers: {fp['layer_count']}")
    
    print(f"\nQuery Information:")
    qi = prov['query']
    print(f"  Target: {qi['target']}")
    print(f"  Raw query: {qi['raw_string']}")
    print(f"  Query hash: {qi['ast_hash']}")
    
    print(f"\nPerformance:")
    perf = prov['performance']
    print(f"  Parse time: {perf.get('parse', 0):.2f}ms")
    print(f"  Execute time: {perf.get('execute', 0):.2f}ms")
    print(f"  Total time: {perf.get('total_ms', 0):.2f}ms")
    
    print()


def demo_provenance_export():
    """Demonstrate exporting provenance to JSON."""
    print("=" * 70)
    print("Provenance Export Demo")
    print("=" * 70)
    
    network = create_sample_network()
    
    # Execute a query
    query = Q.nodes().compute("degree")
    result = query.execute(network)
    
    # Export provenance as JSON
    prov = result.meta["provenance"]
    json_str = json.dumps(prov, indent=2, default=str)
    
    print("\nProvenance exported as JSON:")
    print(json_str)
    print()


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("py3plex Query Provenance Demo")
    print("Version 1.1.0")
    print("=" * 70 + "\n")
    
    demo_dsl_v2_provenance()
    demo_legacy_dsl_provenance()
    demo_provenance_export()
    
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
