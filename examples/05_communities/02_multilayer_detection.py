"""
Communities: Multilayer community detection.

Demonstrates:
- Community detection across layers
- Multilayer network structure
- Layer information

Note: This example shows network preparation. For working implementation,
see py3plex documentation on multilayer community detection.
"""

from py3plex.datasets import load_aarhus_cs

# 1. Load network
network = load_aarhus_cs()

# 2. Network info
node_ids = list(network.get_nodes())
layers = network.layers

# 3. Print network structure
print(f"Multilayer network loaded:")
print(f"  Nodes: {len(node_ids)}")
print(f"  Layers: {len(layers)}")
print(f"  Layer names: {layers}")

# 4. API pattern for multilayer community detection
print("\nMultilayer community detection API:")
print("  from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer")
print("  partition, modularity = louvain_multilayer(network, gamma=1.5, omega=0.5)")
print("\nNote: gamma controls resolution, omega controls inter-layer coupling")
