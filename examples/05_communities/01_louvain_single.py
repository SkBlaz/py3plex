"""
Communities: Single-layer Louvain.

Demonstrates:
- Community detection on single layer
- Using Louvain algorithm
- Inspecting partition
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer

# 1. Load network
network = load_aarhus_cs()

# 2. Run Louvain
partition, modularity = louvain_multilayer(
    network,
    gamma=1.0,
    random_state=42
)

# 3. Print results
num_communities = len(set(partition.values()))
print(f"Communities found: {num_communities}")
print(f"Modularity: {modularity:.3f}")
print(f"Sample partition: {dict(list(partition.items())[:10])}")
