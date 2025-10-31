#!/usr/bin/env python3
"""
Example demonstrating the improved monoplex_nx_wrapper with kwargs support.

This example shows how to use the monoplex_nx_wrapper to call NetworkX centrality
functions with custom parameters, which is essential for weighted multilayer networks.
"""

from py3plex.core import multinet

# Create a simple multilayer network with weighted edges
network = multinet.multi_layer_network()

# Add weighted edges
edges = [
    {"source": "A", "target": "B", "source_type": "layer1", "target_type": "layer1", "weight": 2.0},
    {"source": "B", "target": "C", "source_type": "layer1", "target_type": "layer1", "weight": 3.0},
    {"source": "C", "target": "D", "source_type": "layer1", "target_type": "layer1", "weight": 1.0},
    {"source": "A", "target": "D", "source_type": "layer1", "target_type": "layer1", "weight": 1.5},
    {"source": "B", "target": "D", "source_type": "layer1", "target_type": "layer1", "weight": 2.5},
]

network.add_edges(edges)

print("=" * 70)
print("Demonstrating monoplex_nx_wrapper with kwargs support")
print("=" * 70)

# Example 1: Basic degree centrality (no kwargs needed)
print("\n1. Degree Centrality (unweighted):")
print("-" * 50)
degree_cent = network.monoplex_nx_wrapper("degree_centrality")
for node, centrality in sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:3]:
    print(f"   {node}: {centrality:.4f}")

# Example 2: Betweenness centrality without weights
print("\n2. Betweenness Centrality (unweighted):")
print("-" * 50)
betweenness_unweighted = network.monoplex_nx_wrapper("betweenness_centrality")
for node, centrality in sorted(betweenness_unweighted.items(), key=lambda x: x[1], reverse=True)[:3]:
    print(f"   {node}: {centrality:.4f}")

# Example 3: Betweenness centrality WITH weights (using kwargs)
print("\n3. Betweenness Centrality (weighted):")
print("-" * 50)
print("   Using kwargs={'weight': 'weight'} to consider edge weights")
betweenness_weighted = network.monoplex_nx_wrapper(
    "betweenness_centrality",
    kwargs={"weight": "weight"}
)
for node, centrality in sorted(betweenness_weighted.items(), key=lambda x: x[1], reverse=True)[:3]:
    print(f"   {node}: {centrality:.4f}")

# Example 4: Multiple kwargs at once
print("\n4. Betweenness Centrality (weighted + not normalized):")
print("-" * 50)
print("   Using kwargs={'weight': 'weight', 'normalized': False}")
betweenness_custom = network.monoplex_nx_wrapper(
    "betweenness_centrality",
    kwargs={"weight": "weight", "normalized": False}
)
for node, centrality in sorted(betweenness_custom.items(), key=lambda x: x[1], reverse=True)[:3]:
    print(f"   {node}: {centrality:.4f}")

# Example 5: Closeness centrality with distance parameter
print("\n5. Closeness Centrality (using weight as distance):")
print("-" * 50)
print("   Using kwargs={'distance': 'weight'}")
closeness_weighted = network.monoplex_nx_wrapper(
    "closeness_centrality",
    kwargs={"distance": "weight"}
)
for node, centrality in sorted(closeness_weighted.items(), key=lambda x: x[1], reverse=True)[:3]:
    print(f"   {node}: {centrality:.4f}")

# Example 6: PageRank with custom alpha
print("\n6. PageRank (custom damping factor):")
print("-" * 50)
print("   Using kwargs={'alpha': 0.90} instead of default 0.85")
pagerank_custom = network.monoplex_nx_wrapper(
    "pagerank",
    kwargs={"alpha": 0.90}
)
for node, centrality in sorted(pagerank_custom.items(), key=lambda x: x[1], reverse=True)[:3]:
    print(f"   {node}: {centrality:.4f}")

print("\n" + "=" * 70)
print("✅ All examples completed successfully!")
print("=" * 70)
print("\nKey takeaway:")
print("  The kwargs parameter now allows you to pass any NetworkX function")
print("  parameters, enabling weighted centrality calculations and custom")
print("  configurations for multiplex networks.")
