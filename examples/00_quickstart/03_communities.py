"""
Quickstart: Community detection in multilayer networks.

Demonstrates:
- Loading a dataset
- Network structure
- Community detection API

Note: This shows the API pattern for community detection.
"""

from py3plex.datasets import load_aarhus_cs

# 1. Load network
network = load_aarhus_cs()

# 2. Network info
nodes = list(network.get_nodes())
print(f"Network loaded: {len(nodes)} nodes")
print(f"Layers: {len(network.layers)}")

# 3. Community detection API pattern
print("\nCommunity detection API:")
print("  from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer")
print("  partition, modularity = louvain_multilayer(network)")
print("\nSee examples/05_communities/ for detailed examples")
