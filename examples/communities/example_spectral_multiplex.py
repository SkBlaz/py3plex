"""Example: Multiplex (Aggregated) Laplacian Spectral Clustering via DSL v2

This example demonstrates how to use the multiplex spectral clustering
algorithm for multilayer networks via the DSL v2 API.

The multiplex variant:
1. Computes normalized Laplacians for each layer independently
2. Aggregates them with uniform weights (1/L)
3. Performs spectral embedding directly on nodes (no supra-graph)
4. Clusters node-level embeddings with k-means

Key differences from supra variant:
- No interlayer coupling parameter (omega)
- Lower memory complexity: O(n²) vs O((nL)²)
- Aggregates layer information instead of explicit coupling

Key parameters:
- k: Number of communities (mandatory)
- random_state: For reproducibility
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L

print("=" * 80)
print("MULTIPLEX SPECTRAL CLUSTERING - DSL V2 EXAMPLE")
print("=" * 80)

# ═══════════════════════════════════════════════════════════════════════════════
# Create a multilayer network with community structure
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[1] Creating multilayer network with two layers...")
print("-" * 80)

net = multinet.multi_layer_network(directed=False)

# Community 1: A, B, C (present in both layers)
# Community 2: D, E, F (present in both layers)

# Layer 1 (social): Strong community structure
net.add_edges([
    # Community 1
    ['A', 'social', 'B', 'social', 1.0],
    ['B', 'social', 'C', 'social', 1.0],
    ['C', 'social', 'A', 'social', 1.0],
    # Community 2
    ['D', 'social', 'E', 'social', 1.0],
    ['E', 'social', 'F', 'social', 1.0],
    ['F', 'social', 'D', 'social', 1.0],
    # Weak inter-community link
    ['C', 'social', 'D', 'social', 0.2],
], input_type='list')

# Layer 2 (work): Similar structure but weaker
net.add_edges([
    # Community 1
    ['A', 'work', 'B', 'work', 0.8],
    ['B', 'work', 'C', 'work', 0.8],
    ['C', 'work', 'A', 'work', 0.8],
    # Community 2
    ['D', 'work', 'E', 'work', 0.8],
    ['E', 'work', 'F', 'work', 0.8],
    ['F', 'work', 'D', 'work', 0.8],
    # Weak inter-community link
    ['C', 'work', 'D', 'work', 0.15],
], input_type='list')

nodes = list(net.get_nodes())
edges = list(net.get_edges())
print(f"Network created: {len(nodes)} node-layer pairs, {len(edges)} edges")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 1: Basic Multiplex Spectral Clustering
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[2] Example 1: Basic Multiplex Spectral Clustering")
print("-" * 80)
print("Query: Detect 2 communities using aggregated Laplacian")
print()

result = (
    Q.nodes()
     .from_layers(L["social"] + L["work"])
     .community(
         method="spectral_multilayer_multiplex",
         k=2,
         random_state=42,
     )
     .execute(net)
)

df = result.to_pandas()
print("Community assignments:")

# Get partition from network (attached by community detection)
partition = net.get_partition_by_name("default")

# Add community_id to the dataframe
df["community_id"] = df.apply(lambda row: partition.get((row["id"], row["layer"]), -1), axis=1)

print(df[["id", "layer", "community_id"]].sort_values(["id", "layer"]))

# ═══════════════════════════════════════════════════════════════════════════════
# Example 2: Inspect Communities
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[3] Example 2: Inspect Community Structure")
print("-" * 80)

partition = net.get_partition_by_name("default")
print(f"Partition contains {len(partition)} assignments")
print(f"Number of communities: {len(set(partition.values()))}")

# Extract unique communities
communities = {}
for (node, layer), comm_id in partition.items():
    if comm_id not in communities:
        communities[comm_id] = set()
    communities[comm_id].add(node)

print("\nCommunity membership (node-level):")
for comm_id, members in sorted(communities.items()):
    print(f"  Community {comm_id}: {sorted(members)}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 3: Single Layer (L=1 Reduction)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[4] Example 3: Single Layer (L=1 Reduction)")
print("-" * 80)
print("When applied to a single layer, reduces to standard spectral clustering")
print()

result = (
    Q.nodes()
     .from_layers(L["social"])  # Only social layer
     .community(
         method="spectral_multilayer_multiplex",
         k=2,
         random_state=42,
         partition_name="single_layer",
     )
     .execute(net)
)

partition_single = net.get_partition_by_name("single_layer")
print(f"Communities found: {len(set(partition_single.values()))}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 4: Comparison with Different k Values
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[5] Example 4: Varying Number of Communities (k)")
print("-" * 80)

for k_val in [2, 3, 4]:
    print(f"\nk = {k_val}:")
    
    result = (
        Q.nodes()
         .from_layers(L["social"] + L["work"])
         .community(
             method="spectral_multilayer_multiplex",
             k=k_val,
             random_state=42,
             partition_name=f"k_{k_val}",
         )
         .execute(net)
    )
    
    partition = net.get_partition_by_name(f"k_{k_val}")
    
    # Count community sizes
    from collections import Counter
    comm_sizes = Counter(partition.values())
    
    print(f"  Communities detected: {len(comm_sizes)}")
    print(f"  Size distribution: {sorted(comm_sizes.values(), reverse=True)}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 5: Comparison with Supra-Laplacian
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[6] Example 5: Comparison with Supra-Laplacian Variant")
print("-" * 80)

# Run supra variant for comparison
result_supra = (
    Q.nodes()
     .from_layers(L["social"] + L["work"])
     .community(
         method="spectral_multilayer_supra",
         k=2,
         omega=1.0,
         random_state=42,
         partition_name="supra",
     )
     .execute(net)
)

# Run multiplex variant
result_multiplex = (
    Q.nodes()
     .from_layers(L["social"] + L["work"])
     .community(
         method="spectral_multilayer_multiplex",
         k=2,
         random_state=42,
         partition_name="multiplex",
     )
     .execute(net)
)

partition_supra = net.get_partition_by_name("supra")
partition_multiplex = net.get_partition_by_name("multiplex")

print("Supra-Laplacian communities:")
communities_supra = {}
for (node, layer), comm_id in partition_supra.items():
    if comm_id not in communities_supra:
        communities_supra[comm_id] = set()
    communities_supra[comm_id].add(node)

for comm_id, members in sorted(communities_supra.items()):
    print(f"  Community {comm_id}: {sorted(members)}")

print("\nMultiplex communities:")
communities_multiplex = {}
for (node, layer), comm_id in partition_multiplex.items():
    if comm_id not in communities_multiplex:
        communities_multiplex[comm_id] = set()
    communities_multiplex[comm_id].add(node)

for comm_id, members in sorted(communities_multiplex.items()):
    print(f"  Community {comm_id}: {sorted(members)}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 6: Conflicting Layer Structure
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[7] Example 6: Network with Conflicting Layer Structure")
print("-" * 80)

# Create network where layers have different community structure
net2 = multinet.multi_layer_network(directed=False)

# Layer 1: Communities {A,B,C} and {D,E,F}
net2.add_edges([
    ['A', 'L1', 'B', 'L1', 1.0],
    ['B', 'L1', 'C', 'L1', 1.0],
    ['C', 'L1', 'A', 'L1', 1.0],
    ['D', 'L1', 'E', 'L1', 1.0],
    ['E', 'L1', 'F', 'L1', 1.0],
    ['F', 'L1', 'D', 'L1', 1.0],
], input_type='list')

# Layer 2: Communities {A,B,D} and {C,E,F} (different!)
net2.add_edges([
    ['A', 'L2', 'B', 'L2', 1.0],
    ['B', 'L2', 'D', 'L2', 1.0],
    ['D', 'L2', 'A', 'L2', 1.0],
    ['C', 'L2', 'E', 'L2', 1.0],
    ['E', 'L2', 'F', 'L2', 1.0],
    ['F', 'L2', 'C', 'L2', 1.0],
], input_type='list')

print("Created network with conflicting layer structure")

result = (
    Q.nodes()
     .from_layers(L["L1"] + L["L2"])
     .community(
         method="spectral_multilayer_multiplex",
         k=2,
         random_state=42,
     )
     .execute(net2)
)

partition = net2.get_partition_by_name("default")
communities = {}
for (node, layer), comm_id in partition.items():
    if comm_id not in communities:
        communities[comm_id] = set()
    communities[comm_id].add(node)

print("\nAggregated communities:")
for comm_id, members in sorted(communities.items()):
    print(f"  Community {comm_id}: {sorted(members)}")

print("\nNote: Multiplex method aggregates layer information,")
print("      producing a consensus community structure.")

# ═══════════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("MULTIPLEX SPECTRAL CLUSTERING - SUMMARY")
print("=" * 80)
print("\nKey takeaways:")
print("  ✓ Mandatory parameter: k (number of communities)")
print("  ✓ No omega parameter (no explicit interlayer coupling)")
print("  ✓ Lower memory complexity than supra variant: O(n²) vs O((nL)²)")
print("  ✓ Aggregates layer Laplacians with uniform weights")
print("  ✓ L=1: Reduces to standard spectral clustering")
print("  ✓ Deterministic with random_state")
print("  ✓ Good for networks with consistent community structure across layers")
print("\nDSL syntax:")
print("  Q.nodes()")
print("   .from_layers(L[\"layer1\"] + L[\"layer2\"])")
print("   .community(")
print("       method=\"spectral_multilayer_multiplex\",")
print("       k=<num_communities>,")
print("       random_state=<seed>")
print("   )")
print("   .execute(network)")
print("\nComparison with supra variant:")
print("  Supra:     Explicit interlayer coupling (omega)")
print("  Multiplex: Implicit aggregation (uniform weights)")
print("\nFor more information, see:")
print("  - py3plex.algorithms.community_detection.spectral_multilayer")
print("  - AGENTS.md (Section 15: Community Detection)")
