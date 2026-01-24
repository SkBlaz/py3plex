#!/usr/bin/env python
"""
Example: Community Detection
==============================

This example demonstrates running community detection on a multilayer network
and examining the results.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from py3plex.core import multinet
from py3plex.algorithms.community_detection import multilayer_louvain


def main():
    """Run community detection example."""
    print("Example: Community Detection on Multilayer Network")
    print("=" * 60)
    
    # Create a small test network with clear community structure
    print("\n1. Creating network with community structure...")
    net = multinet.multi_layer_network(directed=False)
    
    # Add two communities in layer 1
    edges_layer1 = [
        ('A', 'B', 'social', 'social'),
        ('B', 'C', 'social', 'social'),
        ('C', 'A', 'social', 'social'),  # Community 1
        ('D', 'E', 'social', 'social'),
        ('E', 'F', 'social', 'social'),
        ('F', 'D', 'social', 'social'),  # Community 2
    ]
    
    # Add edges
    for src, dst, src_layer, dst_layer in edges_layer1:
        net.add_edges([{
            'source': src,
            'target': dst,
            'source_type': src_layer,
            'target_type': dst_layer
        }])
    
    # Add sparse connection between communities
    net.add_edges([{
        'source': 'C',
        'target': 'D',
        'source_type': 'social',
        'target_type': 'social'
    }])
    
    print(f"   Added {len(list(net.get_nodes()))} nodes")
    print(f"   Added {len(list(net.get_edges()))} edges")
    
    # Run community detection
    print("\n2. Running Louvain community detection...")
    partition, _ = multilayer_louvain(net, random_state=42)
    
    # Analyze results
    print("\n3. Community assignments:")
    print("-" * 60)
    
    # Group nodes by community
    communities = {}
    for node, comm_id in partition.items():
        if comm_id not in communities:
            communities[comm_id] = []
        communities[comm_id].append(node)
    
    print(f"   Found {len(communities)} communities\n")
    
    for comm_id in sorted(communities.keys()):
        nodes = sorted(communities[comm_id])
        print(f"   Community {comm_id}: {', '.join(str(n) for n in nodes)}")
    
    # Calculate basic statistics
    print("\n4. Community statistics:")
    print("-" * 60)
    sizes = [len(nodes) for nodes in communities.values()]
    print(f"   Average community size: {sum(sizes) / len(sizes):.1f}")
    print(f"   Largest community: {max(sizes)} nodes")
    print(f"   Smallest community: {min(sizes)} nodes")
    
    print("\n✓ Community detection complete!")


if __name__ == "__main__":
    main()
