"""
Multilayer Example: Aggregating Multiplex Networks

This example demonstrates how to:
1. Generate a random multiplex network (multiple layers, same nodes)
2. Extract individual layers as subnetworks
3. Aggregate the network with different normalization methods
4. Compare edge weights across aggregation strategies

Aggregation combines information from multiple layers into a single network,
useful for:
- Simplifying analysis while preserving multi-layer information
- Creating weighted networks that reflect layer contributions
- Comparing different layer importance metrics
- Reducing computational complexity

SKIP_CI: external_deps - Uses deprecated networkx.info() API
"""

import networkx as nx
from py3plex.core import random_generators

print("=" * 70)
print("MULTIPLEX NETWORK AGGREGATION")
print("=" * 70)

print("\nStep 1: Generating random multiplex network")
print("-" * 70)
print("  Nodes: 500")
print("  Layers: 8")
print("  Edge probability: 0.0005 (sparse network)")

# Generate a random multiplex Erdős-Rényi network
# Multiplex: same nodes across all layers, edges only within layers
ER_multilayer = random_generators.random_multiplex_ER(
    500,      # Number of nodes
    8,        # Number of layers
    0.0005,   # Edge probability per layer
    directed=False
)

print("\nGenerated network statistics:")
ER_multilayer.basic_stats()

print("\nStep 2: Extracting individual layers")
print("-" * 70)

# Extract specific layers as separate network objects
separate_layers = []
layers_to_be_extracted = [1, 2, 3, 4]

print(f"Extracting layers: {layers_to_be_extracted}")

for layer_id in layers_to_be_extracted:
    # Create a subnetwork containing only this layer
    subnetwork_layer = ER_multilayer.subnetwork(
        input_list=[layer_id],
        subset_by="layers"
    )
    separate_layers.append(subnetwork_layer)

print(f"[OK] Extracted {len(separate_layers)} separate layers")

print("\nStep 3: Aggregating with degree normalization")
print("-" * 70)

# Aggregate the multilayer network into a single network
# metric="count": Count how many layers an edge appears in
# normalize_by="degree": Normalize edge weights by node degrees
#   This reduces bias toward high-degree nodes
aggregated_network1 = ER_multilayer.aggregate_edges(
    metric="count",
    normalize_by="degree"
)

print("\nAggregated network (degree-normalized):")
print(nx.info(aggregated_network1))

print("\nSample edges with degree-normalized weights:")
for i, edge in enumerate(aggregated_network1.edges(data=True)):
    if i >= 5:  # Show first 5 edges
        break
    source, target, data = edge
    weight = data.get('weight', 1.0)
    print(f"  ({source}, {target}): weight = {weight:.4f}")

print("\nStep 4: Aggregating with raw counts")
print("-" * 70)

# Aggregate with raw counts (no normalization)
# normalize_by="raw": Use raw edge counts as weights
#   Higher weight = edge appears in more layers
aggregated_network2 = ER_multilayer.aggregate_edges(
    metric="count",
    normalize_by="raw"
)

print("\nAggregated network (raw counts):")
print(nx.info(aggregated_network2))

print("\nSample edges with raw count weights:")
for i, edge in enumerate(aggregated_network2.edges(data=True)):
    if i >= 5:  # Show first 5 edges
        break
    source, target, data = edge
    weight = data.get('weight', 1.0)
    print(f"  ({source}, {target}): weight = {weight:.4f}")

print("\n" + "=" * 70)
print("COMPARING AGGREGATION METHODS")
print("=" * 70)

# Note about edge sets
print("\nKey observations:")
print("  [OK] Both networks have the same edges (same topology)")
print("  [OK] Edge weights differ based on normalization method")
print("  [OK] Degree-normalized weights are typically smaller")
print("  [OK] Raw counts directly reflect layer multiplicity")

print("\nFull edge comparison (showing all edges):")
print("-" * 70)

print("\nRaw count aggregation edges:")
edge_count = 0
for edge in aggregated_network2.edges(data=True):
    source, target, data = edge
    weight = data.get('weight', 1.0)
    print(f"  ({source}, {target}): weight = {weight:.4f}")
    edge_count += 1

print(f"\nTotal edges: {edge_count}")

print("\nDegree-normalized aggregation edges:")
edge_count = 0
for edge in aggregated_network1.edges(data=True):
    source, target, data = edge
    weight = data.get('weight', 1.0)
    print(f"  ({source}, {target}): weight = {weight:.4f}")
    edge_count += 1

print(f"\nTotal edges: {edge_count}")

print("\n" + "=" * 70)
print("AGGREGATION COMPLETE")
print("=" * 70)

print("\nChoosing aggregation method:")
print("  - Degree normalization: Better for heterogeneous networks")
print("  - Raw counts: Better for homogeneous networks")
print("  - Consider your analysis goals when choosing")

print("\nUse cases:")
print("  - Degree-normalized: Centrality analysis, community detection")
print("  - Raw counts: Layer overlap analysis, multiplicity studies")
print("  - Both: Comparative analysis of layer importance")
