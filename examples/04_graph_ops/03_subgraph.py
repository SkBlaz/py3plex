"""
Graph ops: Subgraph extraction.

Demonstrates:
- Selecting subset of nodes
- Creating subgraph view
- Working with filtered networks
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.graph_ops import nodes

# 1. Load network
network = load_aarhus_cs()

# 2. Extract high-degree subgraph
subgraph = (
    nodes(network)
    .filter(lambda n: n["degree"] > 8)
    .to_subgraph()
)

# 3. Print subgraph info
print(f"Created subgraph with {len(list(subgraph.get_nodes()))} nodes")
print(f"Original network: {len(list(network.get_nodes()))} nodes")
