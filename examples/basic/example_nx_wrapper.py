"""
Basic Example: Using NetworkX Betweenness Centrality

This example demonstrates how to:
1. Generate a random multilayer network
2. Apply NetworkX's betweenness centrality algorithm
3. Display and interpret the results

Betweenness centrality measures how often a node appears on
shortest paths between other nodes - indicating "bridge" nodes.
"""

from py3plex.core import random_generators

print("Generating random multilayer Erdős-Rényi network...")
print("Parameters: 300 nodes, 6 layers, edge probability 0.05")

# Generate a toy multilayer network
multilayer_network = random_generators.random_multilayer_ER(
    300,      # Number of nodes
    6,        # Number of layers  
    0.05,     # Edge probability
    directed=False  # Undirected network
)

print("Network generated successfully!")
print("\nComputing betweenness centrality...")
print("(This measures how often nodes act as bridges between other nodes)\n")

# Compute betweenness centrality using NetworkX wrapper
# Betweenness centrality identifies nodes that are important for connectivity
# Higher values indicate nodes that connect different parts of the network
centralities = multilayer_network.monoplex_nx_wrapper("betweenness_centrality")

print(f"Total nodes analyzed: {len(centralities)}")
print("\nTop 10 nodes by betweenness centrality:")
print("-" * 70)

# Sort and display top nodes
top_nodes = sorted(centralities.items(), key=lambda x: x[1], reverse=True)[:10]

for rank, (node, centrality) in enumerate(top_nodes, 1):
    print(f"{rank:2d}. Node {node}: {centrality:.6f}")

print("\n" + "=" * 70)
print("Interpretation:")
print("  - Higher values indicate nodes that bridge different network regions")
print("  - These nodes are critical for network connectivity")
print("  - Removing high-betweenness nodes can fragment the network")
print("=" * 70)
