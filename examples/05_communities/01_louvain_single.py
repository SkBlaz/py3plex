"""
Communities: Single-layer Louvain.

Demonstrates:
- Community detection on single layer
- Using Louvain algorithm from python-louvain package
- Extracting and analyzing layer-specific communities

This example uses the built-in Louvain implementation from community_louvain
module which works with NetworkX graphs.
"""

import networkx as nx

from py3plex.datasets import load_aarhus_cs
from py3plex.algorithms.community_detection.community_louvain import best_partition

# 1. Load network
network = load_aarhus_cs()

# 2. Show network info
print(f"Network loaded: {len(list(network.get_nodes()))} nodes")
print(f"Layers: {network.layers}")

# 3. Extract a single layer for community detection
# Louvain algorithm works on standard NetworkX graphs
# Select the layer with most edges for better community structure
layer_name = None
max_edges = 0
for layer in network.layers:
    layer_nodes = [n for n in network.core_network.nodes() if n[1] == layer]
    layer_subgraph = network.core_network.subgraph(layer_nodes)
    if layer_subgraph.number_of_edges() > max_edges:
        max_edges = layer_subgraph.number_of_edges()
        layer_name = layer

# Get nodes from selected layer
layer_nodes = [n for n in network.core_network.nodes() if n[1] == layer_name]
layer_subgraph = network.core_network.subgraph(layer_nodes)

# Create a clean copy with numeric weights (Louvain requires numeric weights)
layer_graph = nx.Graph()
for u, v, data in layer_subgraph.edges(data=True):
    try:
        weight = float(data.get('weight', 1))
    except (ValueError, TypeError):
        weight = 1.0
    layer_graph.add_edge(u, v, weight=weight)

print(f"\nRunning Louvain on layer '{layer_name}' (largest layer)")
print(f"  Layer nodes: {layer_graph.number_of_nodes()}")
print(f"  Layer edges: {layer_graph.number_of_edges()}")

# 4. Run Louvain community detection
partition = best_partition(layer_graph)

# 5. Analyze results
communities = {}
for node, comm_id in partition.items():
    if comm_id not in communities:
        communities[comm_id] = []
    communities[comm_id].append(node)

print(f"\nCommunity detection complete!")
print(f"  Communities found: {len(communities)}")
print(f"  Largest community: {max(len(nodes) for nodes in communities.values())} nodes")
print(f"  Smallest community: {min(len(nodes) for nodes in communities.values())} nodes")

# Show first few communities
print(f"\nSample communities (first 3):")
for comm_id in sorted(communities.keys())[:3]:
    nodes = communities[comm_id]
    # Extract just the node IDs (first element of tuple)
    node_ids = [n[0] for n in nodes]
    print(f"  Community {comm_id}: {len(nodes)} nodes - {node_ids[:5]}...")
