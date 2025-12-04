"""
Multilayer Example: Aggregating Multiplex Networks

This example demonstrates network aggregation using two approaches:
1. Pipeline-based approach with chaining (simpler, more elegant)
2. Direct method calls for advanced customization

Aggregation combines information from multiple layers into a single network,
useful for:
- Simplifying analysis while preserving multi-layer information
- Creating weighted networks that reflect layer contributions
- Reducing computational complexity

SKIP_CI: external_deps - Uses deprecated networkx.info() API
"""

import networkx as nx
from py3plex.core import random_generators
from py3plex.pipeline import Pipeline, LoadStep, AggregateLayers, ComputeStats

print("=" * 70)
print("MULTIPLEX NETWORK AGGREGATION")
print("=" * 70)

# ============================================================================
# Approach 1: Pipeline-based aggregation (elegant chaining)
# ============================================================================
print("\n" + "=" * 70)
print("Approach 1: Pipeline-based Aggregation (Chaining)")
print("=" * 70)

# Using Pipeline for elegant chaining: generate -> aggregate -> compute stats
pipe = Pipeline([
    ("generate", LoadStep(generator='random_er', n=100, l=4, p=0.03)),
    ("aggregate", AggregateLayers(method='sum')),
    ("stats", ComputeStats()),
])

print("\nPipeline structure:", pipe)
print("\nRunning pipeline...")
result = pipe.run()

print("\nPipeline results:")
print(f"  Nodes: {result['nodes']}")
print(f"  Edges: {result['edges']}")
print(f"  Density: {result['density']:.4f}")

# ============================================================================
# Approach 2: Direct method calls for comparison
# ============================================================================
print("\n" + "=" * 70)
print("Approach 2: Direct Method Calls (Advanced)")
print("=" * 70)

print("\nGenerating random multiplex network...")
print("  Nodes: 500, Layers: 8, Edge probability: 0.0005")

ER_multilayer = random_generators.random_multiplex_ER(
    500, 8, 0.0005, directed=False
)

print("\nGenerated network statistics:")
ER_multilayer.basic_stats()

print("\nExtracting individual layers...")
separate_layers = []
for layer_id in [1, 2, 3, 4]:
    subnetwork_layer = ER_multilayer.subnetwork(
        input_list=[layer_id], subset_by="layers"
    )
    separate_layers.append(subnetwork_layer)
print(f"[OK] Extracted {len(separate_layers)} separate layers")

print("\nAggregating with degree normalization...")
aggregated_network1 = ER_multilayer.aggregate_edges(
    metric="count", normalize_by="degree"
)
print(f"Aggregated network: {aggregated_network1.number_of_nodes()} nodes, "
      f"{aggregated_network1.number_of_edges()} edges")

print("\nAggregating with raw counts...")
aggregated_network2 = ER_multilayer.aggregate_edges(
    metric="count", normalize_by="raw"
)
print(f"Aggregated network: {aggregated_network2.number_of_nodes()} nodes, "
      f"{aggregated_network2.number_of_edges()} edges")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 70)
print("COMPARISON SUMMARY")
print("=" * 70)

print("\nPipeline approach:")
print("  ✓ Concise, readable, chainable")
print("  ✓ Best for standard workflows")

print("\nDirect method approach:")
print("  ✓ Full control over parameters")
print("  ✓ Best for advanced customization (degree vs raw normalization)")

print("\nChoosing aggregation method:")
print("  - Degree normalization: Better for heterogeneous networks")
print("  - Raw counts: Better for homogeneous networks")
