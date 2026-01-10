"""
Quickstart: Detect communities in a multilayer network.

Demonstrates:
- Loading a dataset
- Running community detection
- Inspecting partition
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer

# 1. Load network
network = load_aarhus_cs()

# 2. Detect communities
partition, modularity = louvain_multilayer(network, random_state=42)

# 3. Inspect result
print(f"Found {len(set(partition.values()))} communities")
print(f"Modularity: {modularity:.3f}")
print(f"Sample partition: {dict(list(partition.items())[:5])}")
