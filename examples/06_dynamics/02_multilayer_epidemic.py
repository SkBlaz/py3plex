"""
Dynamics: Multilayer epidemic spreading.

Demonstrates:
- Preparing multilayer network for epidemic simulation
- Cross-layer structure

Note: This example shows network setup.
For simulation API, see py3plex.dynamics module documentation.
"""

from py3plex.datasets import load_aarhus_cs

# 1. Load multilayer network
network = load_aarhus_cs()

# 2. Network info
node_ids = list(network.get_nodes())
layers = network.get_layers()[0]

# 3. Print network structure
print(f"Multilayer network loaded:")
print(f"  Nodes: {len(node_ids)}")
print(f"  Layers: {len(layers)}")
print(f"  Layer names: {layers}")
print("\nThis network is ready for multilayer epidemic simulation")
print("See py3plex.dynamics module for SIR/SIS simulation API")
