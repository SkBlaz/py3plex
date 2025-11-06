"""
Basic Example: Using NetworkX Functions on Multilayer Networks

This example demonstrates how to:
1. Generate a random multilayer network
2. Apply NetworkX algorithms to the network using the wrapper
3. Compute and display node centrality measures

The monoplex_nx_wrapper allows you to use any NetworkX algorithm
on the aggregated (flattened) version of your multilayer network.

Runtime: FAST (< 5 seconds) - Standalone example suitable for CI
"""

from py3plex.core import random_generators

print("Generating random multilayer Erdős-Rényi network...")
print("Parameters: 300 nodes, 6 layers, edge probability 0.05")

# Generate a toy multilayer network
# Using undirected edges for this example
ER_net = random_generators.random_multilayer_ER(
    300,      # Number of nodes
    6,        # Number of layers
    0.05,     # Edge probability
    directed=False
)

print("Network generated successfully!")
print("\nComputing degree centrality for all nodes...")
print("(This aggregates the network across all layers)")

# Compute node centralities using NetworkX's degree_centrality function
# The monoplex_nx_wrapper applies the NetworkX function to the aggregated network
# Any NetworkX function can be used: "betweenness_centrality", "closeness_centrality", etc.
centralities = ER_net.monoplex_nx_wrapper("degree_centrality")

print(f"\nTotal nodes analyzed: {len(centralities)}")
print("\nTop 5 nodes by degree centrality:")
print("-" * 50)

# Sort centralities and display the top 5 nodes
top_nodes = sorted(centralities.items(), key=lambda x: x[1], reverse=True)[:5]

for rank, (node, centrality) in enumerate(top_nodes, 1):
    print(f"{rank}. Node {node}: {centrality:.4f}")

print("\nNote: Centrality values range from 0 to 1, where 1 means")
print("the node is connected to all other nodes in the network.")
