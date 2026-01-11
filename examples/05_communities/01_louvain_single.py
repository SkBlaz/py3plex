"""
Communities: Single-layer Louvain.

Demonstrates:
- Community detection on single layer
- Using Louvain algorithm
- Network preparation for community detection

Note: This example shows the API pattern. For working implementation,
see py3plex documentation on community detection with numeric node IDs.
"""

from py3plex.datasets import load_aarhus_cs

# 1. Load network
network = load_aarhus_cs()

# 2. Show network info
print(f"Network loaded: {len(list(network.get_nodes()))} nodes")
print(f"Layers: {len(network.layers)}")
print(f"Ready for community detection")

# 3. API pattern for community detection
print("\nCommunity detection API:")
print("  from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer")
print("  partition, modularity = louvain_multilayer(network, gamma=1.0)")
print("\nNote: Algorithm requires numeric node IDs for optimal performance")
