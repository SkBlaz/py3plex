"""Semiring shortest paths example using min_plus semiring.

This example demonstrates:
- Creating a multilayer network
- Using S.paths() builder with min_plus semiring
- Finding shortest paths
- Extracting results to pandas
"""

from py3plex.core import multinet
from py3plex.dsl import S, L


def main():
    """Run min_plus shortest path example."""
    print("=" * 60)
    print("Semiring Shortest Paths (min_plus)")
    print("=" * 60)
    
    # Create a simple multilayer network
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    nodes = [
        {'source': 'A', 'type': 'transport'},
        {'source': 'B', 'type': 'transport'},
        {'source': 'C', 'type': 'transport'},
        {'source': 'D', 'type': 'transport'},
    ]
    network.add_nodes(nodes)
    
    # Add edges with weights
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'transport', 'target_type': 'transport', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'transport', 'target_type': 'transport', 'weight': 2.0},
        {'source': 'A', 'target': 'D', 'source_type': 'transport', 'target_type': 'transport', 'weight': 5.0},
        {'source': 'D', 'target': 'C', 'source_type': 'transport', 'target_type': 'transport', 'weight': 1.0},
    ]
    network.add_edges(edges)
    
    print("\nNetwork structure:")
    print(f"  Nodes: {[n['source'] for n in nodes]}")
    print(f"  Edges: A-B (1.0), B-C (2.0), A-D (5.0), D-C (1.0)")
    
    # Compute shortest paths from A using semiring algebra
    print("\nComputing shortest paths from A using min_plus semiring...")
    
    result = (
        S.paths()
         .from_node('A')
         .semiring('min_plus')
         .lift(attr='weight', default=1.0)
         .from_layers(L['transport'])
         .witness(True)  # Request path witnesses
         .execute(network)
    )
    
    # Display results
    print("\nShortest distances from A:")
    print("-" * 40)
    
    for item in result.items:
        node = item['node']
        distance = item['value']
        path = item.get('path', None)
        
        if distance == float('inf'):
            print(f"  {node}: unreachable")
        else:
            path_str = " -> ".join(str(n) for n in path) if path else "N/A"
            print(f"  {node}: distance={distance:.1f}, path={path_str}")
    
    # Check provenance
    print("\nProvenance:")
    prov = result.meta.get('provenance', {})
    if 'algebra' in prov:
        print(f"  Semiring: {prov['algebra'].get('semiring', {}).get('name', 'unknown')}")
        print(f"  Algorithm: {prov.get('algorithm', 'unknown')}")
    
    print("\n" + "=" * 60)
    print("✓ Example completed successfully")
    print("=" * 60)


if __name__ == "__main__":
    main()
