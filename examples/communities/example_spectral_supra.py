"""Example: Supra-Laplacian Spectral Clustering via DSL v2

This example demonstrates how to use the supra-Laplacian spectral clustering
algorithm for multilayer networks via the DSL v2 API.

The supra-Laplacian variant:
1. Constructs a full supra-adjacency matrix with interlayer coupling ω
2. Computes the normalized supra-Laplacian
3. Performs spectral embedding on node-layer replicas
4. Averages embeddings across layers
5. Clusters node-level embeddings with k-means

Key parameters:
- k: Number of communities (mandatory)
- omega: Interlayer coupling strength (controls synchronization across layers)
- random_state: For reproducibility
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L

print("=" * 80)
print("SUPRA-LAPLACIAN SPECTRAL CLUSTERING - DSL V2 EXAMPLE")
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
# Example 1: Basic Supra-Laplacian Spectral Clustering
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[2] Example 1: Basic Supra-Laplacian Spectral Clustering")
print("-" * 80)
print("Query: Detect 2 communities using supra-Laplacian with omega=0.8")
print()

result = (
    Q.nodes()
     .from_layers(L["social"] + L["work"])
     .community(
         method="spectral_multilayer_supra",
         k=2,
         omega=0.8,
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
# Example 2: Inspect Embeddings
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[3] Example 2: Inspect Node-Level Embeddings")
print("-" * 80)

# Access embeddings from metadata (via partition)
partition = net.get_partition_by_name("default")
print(f"Partition contains {len(partition)} assignments")
print(f"Number of communities: {len(set(partition.values()))}")

# Extract unique communities
communities = {}
for (node, layer), comm_id in partition.items():
    if comm_id not in communities:
        communities[comm_id] = set()
    communities[comm_id].add(node)

print("\nCommunity membership:")
for comm_id, members in sorted(communities.items()):
    print(f"  Community {comm_id}: {sorted(members)}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 3: Effect of Omega (Interlayer Coupling)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[4] Example 3: Effect of Omega on Synchronization")
print("-" * 80)

for omega_val in [0.0, 0.5, 2.0]:
    print(f"\nOmega = {omega_val}:")
    
    result = (
        Q.nodes()
         .from_layers(L["social"] + L["work"])
         .community(
             method="spectral_multilayer_supra",
             k=2,
             omega=omega_val,
             random_state=42,
             partition_name=f"omega_{omega_val}",
         )
         .execute(net)
    )
    
    partition = net.get_partition_by_name(f"omega_{omega_val}")
    
    # Check synchronization: same node should have same community across layers
    node_consistency = {}
    for (node, layer), comm in partition.items():
        if node not in node_consistency:
            node_consistency[node] = set()
        node_consistency[node].add(comm)
    
    consistent_nodes = sum(1 for comms in node_consistency.values() if len(comms) == 1)
    total_nodes = len(node_consistency)
    
    print(f"  Consistent nodes: {consistent_nodes}/{total_nodes} "
          f"({100 * consistent_nodes / total_nodes:.1f}%)")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 4: Single Layer (L=1 Reduction)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[5] Example 4: Single Layer (L=1 Reduction)")
print("-" * 80)
print("When applied to a single layer, reduces to standard spectral clustering")
print()

result = (
    Q.nodes()
     .from_layers(L["social"])  # Only social layer
     .community(
         method="spectral_multilayer_supra",
         k=2,
         omega=1.0,  # omega doesn't matter for single layer
         random_state=42,
         partition_name="single_layer",
     )
     .execute(net)
)

partition_single = net.get_partition_by_name("single_layer")
print(f"Communities found: {len(set(partition_single.values()))}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example 5: Comparison with Different k Values
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[6] Example 5: Varying Number of Communities (k)")
print("-" * 80)

for k_val in [2, 3, 4]:
    print(f"\nk = {k_val}:")
    
    result = (
        Q.nodes()
         .from_layers(L["social"] + L["work"])
         .community(
             method="spectral_multilayer_supra",
             k=k_val,
             omega=0.8,
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
# Summary
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("SUPRA-LAPLACIAN SPECTRAL CLUSTERING - SUMMARY")
print("=" * 80)
print("\nKey takeaways:")
print("  ✓ Mandatory parameter: k (number of communities)")
print("  ✓ Omega controls interlayer coupling (higher = stronger synchronization)")
print("  ✓ omega=0: Independent layers")
print("  ✓ omega=large: Node replicas synchronized across layers")
print("  ✓ L=1: Reduces to standard spectral clustering")
print("  ✓ Deterministic with random_state")
print("\nDSL syntax:")
print("  Q.nodes()")
print("   .from_layers(L[\"layer1\"] + L[\"layer2\"])")
print("   .community(")
print("       method=\"spectral_multilayer_supra\",")
print("       k=<num_communities>,")
print("       omega=<coupling_strength>,")
print("       random_state=<seed>")
print("   )")
print("   .execute(network)")
print("\nFor more information, see:")
print("  - py3plex.algorithms.community_detection.spectral_multilayer")
print("  - AGENTS.md (Section 15: Community Detection)")
