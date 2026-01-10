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
high_degree_nodes = (
    nodes(network)
    .filter(lambda n: n["degree"] > 8)
    .select("id")
    .to_list()
)

# 3. Print subgraph info
print(f"Extracted subgraph with {len(high_degree_nodes)} nodes")
print(f"Node IDs: {high_degree_nodes[:10]}")
