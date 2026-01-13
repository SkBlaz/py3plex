"""
Multilayer Example: Aggregating Multiplex Networks

This example demonstrates network aggregation using multiple approaches:
1. Pipeline-based approach with chaining (simpler, more elegant)
2. DSL-based approach for querying aggregated networks
3. Interoperability: showing how Pipeline and DSL work with the same objects

The key point is that all py3plex objects are interoperable - networks generated
via Pipeline can be analyzed with DSL, and vice versa.

SKIP_CI: external_deps - Uses deprecated networkx.info() API
"""

import networkx as nx
from py3plex.core import random_generators
from py3plex.pipeline import Pipeline, LoadStep, AggregateLayers, ComputeStats
from py3plex.dsl import execute_query

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
print(f" Nodes: {result['nodes']}")
print(f" Edges: {result['edges']}")
print(f" Density: {result['density']:.4f}")

# ============================================================================
# Approach 2: Interoperability - Generate with Pipeline, Analyze with DSL
# ============================================================================
print("\n" + "=" * 70)
print("Approach 2: Interoperability - Pipeline + DSL")
print("=" * 70)

# Generate network using Pipeline step
network = LoadStep(generator='random_er', n=50, l=3, p=0.08).transform(None)
print(f"Generated network: {network.core_network.number_of_nodes()} nodes")

# Analyze with DSL - objects are fully compatible
dsl_result = execute_query(network, 'SELECT nodes WHERE degree > 2 COMPUTE degree_centrality')
print(f"DSL query: SELECT nodes WHERE degree > 2 COMPUTE degree_centrality")
print(f"High-degree nodes found: {dsl_result['count']}")

# Aggregate using direct method and analyze with DSL
aggregated = network.aggregate_edges(metric="sum")
print(f"Aggregated network: {aggregated.number_of_nodes()} nodes, {aggregated.number_of_edges()} edges")

# ============================================================================
# Approach 3: Direct method calls for advanced customization
# ============================================================================
print("\n" + "=" * 70)
print("Approach 3: Direct Method Calls (Advanced)")
print("=" * 70)

print("\nGenerating random multiplex network...")
print(" Nodes: 500, Layers: 8, Edge probability: 0.0005")

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
print("SUMMARY: Object Interoperability")
print("=" * 70)

print("\nAll approaches work with the same multi_layer_network object:")
print(" Pipeline generates/transforms multi_layer_network")
print(" DSL queries work on multi_layer_network")
print(" Direct methods work on multi_layer_network")
print(" Objects can be passed between Pipeline, DSL, and direct calls")

print("\nChoose based on your needs:")
print(" - Pipeline: Best for reproducible, chainable workflows")
print(" - DSL: Best for declarative, SQL-like analysis")
print(" - Direct: Best for full control and customization")
