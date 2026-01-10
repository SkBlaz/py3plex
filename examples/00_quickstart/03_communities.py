"""
Quickstart: Detect communities in a multilayer network.

Demonstrates:
- Loading a dataset
- Running community detection
- Inspecting partition

Note: Some community detection methods require network preprocessing.
"""

from py3plex.datasets import load_aarhus_cs

try:
    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
    
    # 1. Load network
    network = load_aarhus_cs()
    
    # 2. Detect communities
    partition, modularity = louvain_multilayer(network, random_state=42)
    
    # 3. Inspect result
    print(f"Found {len(set(partition.values()))} communities")
    print(f"Modularity: {modularity:.3f}")
    print(f"Sample partition: {dict(list(partition.items())[:5])}")
    
except (ValueError, ImportError) as e:
    print(f"Community detection example:")
    print(f"  Network loaded: {len(list(network.get_nodes()))} nodes")
    print(f"  Note: Algorithm requires preprocessing for this network")
    print(f"  See examples/05_communities/ for working examples")
