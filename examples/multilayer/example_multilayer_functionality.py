"""
Multilayer Example: Core Multilayer Network Functionality

This example demonstrates fundamental multilayer network operations:
1. Loading a multilayer network
2. Displaying network statistics
3. Iterating through edges and nodes
4. Creating subnetworks using different filtering criteria
5. Computing centrality measures on subnetworks

These are the building blocks for more complex multilayer network analysis.
"""

import os
from py3plex.core import multinet
from py3plex.utils import get_dataset_path

print("=" * 70)
print("MULTILAYER NETWORK FUNCTIONALITY DEMONSTRATION")
print("=" * 70)

# Load a multilayer network
dataset_path = get_dataset_path("multiedgelist.txt")

if not os.path.exists(dataset_path):
    print(f"Error: Dataset file '{dataset_path}' not found.")
    print("This example requires a multiedgelist dataset.")
    exit(1)

print(f"\nLoading multilayer network from: {dataset_path}")
# Create and load a multilayer network object
A = multinet.multi_layer_network().load_network(
    dataset_path,
    input_type="multiedgelist",  # Format: node1 layer1 node2 layer2 weight
    directed=False
)

print("Network loaded successfully!\n")

# Display basic network statistics
print("=" * 70)
print("BASIC NETWORK STATISTICS")
print("=" * 70)
A.basic_stats()

# Example 1: Iterating through edges
print("\n" + "=" * 70)
print("EXAMPLE 1: ITERATING THROUGH EDGES")
print("=" * 70)
A.monitor("Edge iteration:")
print("Format: ((node1, layer1), (node2, layer2), {'weight': w})\n")

# Get all edges with their attributes
edge_count = 0
for edge in A.get_edges(data=True):
    if edge_count < 5:  # Show only first 5 edges as example
        print(f"  {edge}")
        edge_count += 1
    else:
        break

total_edges = len(list(A.get_edges()))
print(f"\n  ... (showing 5 of {total_edges} total edges)")

# Example 2: Iterating through nodes
print("\n" + "=" * 70)
print("EXAMPLE 2: ITERATING THROUGH NODES")
print("=" * 70)
A.monitor("Node iteration:")
print("Format: (node_id, layer_id, {attributes})\n")

# Get all nodes with their attributes
node_count = 0
for node in A.get_nodes(data=True):
    if node_count < 5:  # Show only first 5 nodes as example
        print(f"  {node}")
        node_count += 1
    else:
        break

total_nodes = len(list(A.get_nodes()))
print(f"\n  ... (showing 5 of {total_nodes} total node-layer pairs)")

# Example 3: Subnetwork by layer
print("\n" + "=" * 70)
print("EXAMPLE 3: EXTRACTING SUBNETWORK BY LAYER")
print("=" * 70)
print("Extracting all nodes in layer '1'...\n")

# Create a subnetwork containing only layer '1'
C1 = A.subnetwork(['1'], subset_by="layers")
layer1_nodes = list(C1.get_nodes())

print(f"Nodes in layer '1': {len(layer1_nodes)}")
A.monitor(f"Sample nodes: {layer1_nodes[:5]}")

# Example 4: Subnetwork by node name
print("\n" + "=" * 70)
print("EXAMPLE 4: EXTRACTING SUBNETWORK BY NODE NAME")
print("=" * 70)
print("Extracting node '1' across all layers...\n")

# Create a subnetwork containing node '1' in all layers
C2 = A.subnetwork(['1'], subset_by="node_names")
node1_instances = list(C2.get_nodes())

print(f"Instances of node '1': {len(node1_instances)}")
A.monitor(f"Node instances: {node1_instances}")

# Example 5: Subnetwork by specific node-layer pairs
print("\n" + "=" * 70)
print("EXAMPLE 5: EXTRACTING SPECIFIC NODE-LAYER PAIRS")
print("=" * 70)
print("Extracting specific node-layer combinations...\n")

# Create a subnetwork with specific node-layer pairs
C3 = A.subnetwork(
    [('1', '1'), ('2', '1')],  # (node, layer) tuples
    subset_by="node_layer_names"
)
specific_nodes = list(C3.get_nodes())

print(f"Selected node-layer pairs: {len(specific_nodes)}")
A.monitor(f"Selected pairs: {specific_nodes}")

# Example 6: Computing centrality on a subnetwork
print("\n" + "=" * 70)
print("EXAMPLE 6: COMPUTING CENTRALITY ON SUBNETWORK")
print("=" * 70)
print("Computing degree centrality for layer '1'...\n")

# Compute degree centrality using NetworkX wrapper
# This treats the subnetwork as a single-layer (monoplex) network
centralities = C1.monoplex_nx_wrapper("degree_centrality")

print(f"Computed centrality for {len(centralities)} nodes")
print("\nTop 5 nodes by degree centrality in layer '1':")
print("-" * 70)

# Sort and display top nodes
sorted_centralities = sorted(
    centralities.items(), 
    key=lambda x: x[1], 
    reverse=True
)[:5]

for rank, (node, cent) in enumerate(sorted_centralities, 1):
    print(f"  {rank}. Node {node}: {cent:.4f}")

print("\n" + "=" * 70)
print("MULTILAYER FUNCTIONALITY DEMONSTRATION COMPLETE")
print("=" * 70)

print("\nKey operations demonstrated:")
print("  ✓ Loading multilayer networks")
print("  ✓ Accessing network statistics")
print("  ✓ Iterating through edges and nodes")
print("  ✓ Creating subnetworks by layers")
print("  ✓ Creating subnetworks by node names")
print("  ✓ Creating subnetworks by node-layer pairs")
print("  ✓ Computing centrality measures")
