"""
Example demonstrating multilayer centrality toolkit.

This example shows how to use the centrality toolkit for multilayer networks,
including betweenness centrality and versatility scores.
"""

from py3plex.core.multinet import multi_layer_network
from py3plex.algorithms.centrality_toolkit import (
    multilayer_betweenness_centrality,
    versatility_score,
)


def main():
    """Demonstrate multilayer centrality algorithms."""
    print("=== Centrality Toolkit Demo ===\n")
    
    # Create a simple multilayer network
    net = multi_layer_network(network_type='multilayer', directed=False)
    net.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'A', 'type': 'layer2'},
        {'source': 'B', 'type': 'layer2'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'B', 'source_type': 'layer2', 'target_type': 'layer2'},
    ])
    
    print(f"Network: {net.core_network.number_of_nodes()} nodes, "
          f"{net.core_network.number_of_edges()} edges\n")
    
    # Compute multilayer betweenness centrality
    try:
        betweenness = multilayer_betweenness_centrality(net)
        print(f"Betweenness centrality computed for {len(betweenness)} nodes")
        
        # Show top nodes by betweenness
        top_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:3]
        print("\nTop 3 nodes by betweenness centrality:")
        for node, score in top_nodes:
            print(f"  {node}: {score:.4f}")
        
        # Compute versatility score
        # Measures how evenly a node's centrality is distributed across layers
        versatility = versatility_score(betweenness)
        print("\nVersatility scores (participation balance):")
        for node, score in sorted(versatility.items(), key=lambda x: x[1], reverse=True)[:3]:
            print(f"  {node}: {score:.4f}")
        
        print("\nNote: Versatility measures how important a node is across")
        print("multiple layers, not just in a single layer.\n")
        
    except Exception as e:
        print(f"Error computing centrality: {e}\n")


if __name__ == "__main__":
    main()
