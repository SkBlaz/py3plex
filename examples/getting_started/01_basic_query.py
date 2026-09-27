#!/usr/bin/env python3
"""
Basic Network Creation Example

This example demonstrates:
- Creating a simple multilayer network
- Adding nodes and edges
- Querying network structure

Output: Deterministic network statistics
"""

from py3plex.core.multinet import multi_layer_network
from py3plex.dsl import Q


def main():
    # Create a simple network
    print("Creating a multilayer network...")
    network = multi_layer_network(directed=False)
    
    # Add nodes to two layers
    nodes = [
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
        {'source': 'Alice', 'type': 'work'},
        {'source': 'Bob', 'type': 'work'},
        {'source': 'Diana', 'type': 'work'},
    ]
    network.add_nodes(nodes)
    print(f"Added {len(nodes)} nodes")
    
    # Add edges
    edges = [
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Bob', 'target': 'Diana', 'source_type': 'work', 'target_type': 'work'},
    ]
    network.add_edges(edges)
    print(f"Added {len(edges)} edges")
    print()
    
    # Display network statistics
    print("Network Statistics:")
    print("=" * 40)
    
    # Count nodes per layer
    result = (
        Q.nodes()
        .execute(network)
    )
    print(f"Total node instances: {len(result.items)}")
    
    # Count edges
    edge_result = (
        Q.edges()
        .execute(network)
    )
    print(f"Total edges: {len(edge_result.items)}")
    print()
    
    # Show nodes with their degrees
    print("Node Degrees:")
    print("=" * 40)
    degree_result = (
        Q.nodes()
        .compute("degree")
        .order_by("degree", desc=True)
        .execute(network)
    )
    
    df = degree_result.to_pandas()
    for _, row in df.head(10).iterrows():
        node = row['id']
        layer = row['layer']
        degree = row['degree']
        print(f"  {str(node):10s} ({str(layer):8s}): {degree}")


if __name__ == "__main__":
    main()
