"""
Communities: Multilayer community detection.

Demonstrates:
- Community detection across layers using multilayer modularity
- Working with multilayer network structure
- Interpreting communities that span multiple layers

This example uses the multilayer Louvain algorithm which maximizes
multilayer modularity quality function (Mucha et al., 2010).

Note: The multilayer Louvain algorithm can be slow for large networks.
For production use, consider using faster implementations like leiden_multilayer.
"""

from py3plex.datasets import load_aarhus_cs
from py3plex.algorithms.community_detection.multilayer_modularity import (
    multilayer_modularity,
)
from py3plex.algorithms.community_detection.community_louvain import best_partition

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

# 4. For demonstration, we'll use a simple approach:
#    Run Louvain on each layer independently, then evaluate multilayer modularity
print(f"\nRunning layer-wise community detection...")

# Get communities for each layer using standard Louvain
import networkx as nx

layer_communities = {}
for layer in layers:
    # Extract layer
    layer_nodes = [n for n in network.core_network.nodes() if n[1] == layer]
    layer_subgraph = network.core_network.subgraph(layer_nodes)
    
    # Create clean graph with numeric weights
    layer_graph = nx.Graph()
    for u, v, data in layer_subgraph.edges(data=True):
        try:
            weight = float(data.get('weight', 1))
        except (ValueError, TypeError):
            weight = 1.0
        layer_graph.add_edge(u, v, weight=weight)
    
    # Run Louvain
    if layer_graph.number_of_nodes() > 0:
        partition = best_partition(layer_graph)
        layer_communities[layer] = partition
        num_comms = len(set(partition.values()))
        print(f"  Layer {layer}: {layer_graph.number_of_nodes()} nodes, {num_comms} communities")

# 5. Convert to multilayer partition format: {(node, layer): community_id}
multilayer_partition = {}
for layer, partition in layer_communities.items():
    for node_tuple, comm_id in partition.items():
        # node_tuple is already (node, layer) format
        multilayer_partition[node_tuple] = comm_id

# 6. Evaluate with multilayer modularity
print(f"\nEvaluating multilayer modularity...")
Q = multilayer_modularity(network, multilayer_partition, gamma=1.0, omega=0.5)

print(f"\nResults:")
print(f"  Total node-layer pairs: {len(multilayer_partition)}")
print(f"  Multilayer modularity Q: {Q:.4f}")
print(f"  (Q > 0 indicates good community structure)")

# Show sample communities
unique_communities = set(multilayer_partition.values())
print(f"  Unique communities: {len(unique_communities)}")

# Sample from first community
first_comm = list(unique_communities)[0]
sample_nodes = [(n, l) for (n, l), c in multilayer_partition.items() if c == first_comm][:5]
print(f"\nSample from community {first_comm}:")
for node, layer in sample_nodes:
    print(f"  Node {node} in layer {layer}")
