"""Example: Multilayer Spectral Clustering

This example demonstrates both variants of spectral clustering for multilayer networks:

1. **Supra-Laplacian Spectral Clustering**: Constructs a supra-graph with 
   identity-weighted interlayer coupling
2. **Multiplex (Aggregated) Laplacian Spectral Clustering**: Aggregates 
   normalized Laplacians across layers

Both variants use the DSL v2 API for seamless integration.

Key Features:
- Deterministic spectral embeddings with fixed random_state
- Node-level community assignments
- Access to spectral embeddings for visualization
- Direct comparison of both variants
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.algorithms.community_detection import (
    spectral_multilayer_supra,
    spectral_multilayer_multiplex,
)

print("=" * 80)
print("MULTILAYER SPECTRAL CLUSTERING")
print("=" * 80)

# ═══════════════════════════════════════════════════════════════════════════════
# Create a multilayer network with clear community structure
# ═══════════════════════════════════════════════════════════════════════════════

print("\n[1] Creating multilayer network...")
print("-" * 80)

network = multinet.multi_layer_network(directed=False)

# Layer 1: Social network
# Community 1: Alice, Bob, Charlie (tightly connected)
# Community 2: David, Eve, Frank (tightly connected)
# Weak link: Charlie - David

social_edges = [
    # Community 1
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Charlie', 'target': 'Alice', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    
    # Community 2
    {'source': 'David', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Eve', 'target': 'Frank', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Frank', 'target': 'David', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    
    # Weak bridge
    {'source': 'Charlie', 'target': 'David', 'source_type': 'social', 'target_type': 'social', 'weight': 0.2},
]

network.add_edges(social_edges)

# Layer 2: Work network
# Different structure, potentially conflicting communities

work_edges = [
    {'source': 'Alice', 'target': 'David', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
    {'source': 'Bob', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
    {'source': 'Charlie', 'target': 'Frank', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
    {'source': 'Alice', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
    {'source': 'Bob', 'target': 'Frank', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
]

network.add_edges(work_edges)

print(f"Network created:")
print(f"  Nodes: {len(list(network.get_nodes()))}")
print(f"  Edges: {len(list(network.get_edges()))}")
print(f"  Layers: {list(network.get_layers())}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example A: Supra-Laplacian Spectral Clustering via DSL
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[2] Example A: Supra-Laplacian Spectral Clustering")
print("-" * 80)
print("This variant constructs a supra-graph with interlayer coupling (omega)")
print()

result_supra = (
    Q.nodes()
     .from_layers(L["social"] + L["work"])
     .community(
         method="spectral_multilayer_supra",
         k=3,
         omega=0.8,
         random_state=42,
     )
     .execute(network)
)

print("Results:")
print(f"  Method: {result_supra.meta['community_detection']['method']}")
print(f"  Communities detected: {result_supra.meta['community_detection']['n_communities']}")
print(f"  Parameters: k=3, omega=0.8")
print()

df_supra = result_supra.to_pandas()
print("Node assignments (Supra-Laplacian):")
print(df_supra.head(10))

# ═══════════════════════════════════════════════════════════════════════════════
# Example B: Multiplex (Aggregated) Laplacian Spectral Clustering via DSL
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[3] Example B: Multiplex (Aggregated) Laplacian Spectral Clustering")
print("-" * 80)
print("This variant aggregates layer Laplacians without constructing supra-graph")
print()

# Clear previous partition
network._partitions = {}

result_multiplex = (
    Q.nodes()
     .from_layers(L["social"] + L["work"])
     .community(
         method="spectral_multilayer_multiplex",
         k=3,
         random_state=42,
     )
     .execute(network)
)

print("Results:")
print(f"  Method: {result_multiplex.meta['community_detection']['method']}")
print(f"  Communities detected: {result_multiplex.meta['community_detection']['n_communities']}")
print(f"  Parameters: k=3")
print()

df_multiplex = result_multiplex.to_pandas()
print("Node assignments (Multiplex):")
print(df_multiplex[["node", "layer"]].head(10))

# ═══════════════════════════════════════════════════════════════════════════════
# Example C: Direct API Usage (without DSL)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[4] Example C: Direct API Usage")
print("-" * 80)
print("Using algorithms directly without DSL wrapper")
print()

# Supra variant
result_supra_direct = spectral_multilayer_supra(
    network,
    k=3,
    omega=0.8,
    random_state=42
)

print("Supra-Laplacian (direct):")
print(f"  Partition size: {len(result_supra_direct['partition_nodes'])}")
print(f"  Embedding shape: {result_supra_direct['embedding_nodes'].shape}")
print(f"  Eigenvalues: {result_supra_direct['eigenvalues']}")
print()

# Multiplex variant
result_multiplex_direct = spectral_multilayer_multiplex(
    network,
    k=3,
    random_state=42
)

print("Multiplex (direct):")
print(f"  Partition size: {len(result_multiplex_direct['partition_nodes'])}")
print(f"  Embedding shape: {result_multiplex_direct['embedding_nodes'].shape}")
print(f"  Eigenvalues: {result_multiplex_direct['eigenvalues']}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example D: Accessing Spectral Embeddings
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[5] Example D: Accessing Spectral Embeddings")
print("-" * 80)
print("Embeddings can be used for visualization or further analysis")
print()

# Get embeddings
embedding_nodes_supra = result_supra_direct["embedding_nodes"]
embedding_nodes_multiplex = result_multiplex_direct["embedding_nodes"]

print(f"Supra embedding shape: {embedding_nodes_supra.shape}")
print(f"First 3 nodes (supra):")
for i in range(min(3, embedding_nodes_supra.shape[0])):
    print(f"  Node {i}: {embedding_nodes_supra[i]}")

print()
print(f"Multiplex embedding shape: {embedding_nodes_multiplex.shape}")
print(f"First 3 nodes (multiplex):")
for i in range(min(3, embedding_nodes_multiplex.shape[0])):
    print(f"  Node {i}: {embedding_nodes_multiplex[i]}")

# ═══════════════════════════════════════════════════════════════════════════════
# Example E: Omega Sensitivity (Supra variant)
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[6] Example E: Omega Sensitivity Analysis")
print("-" * 80)
print("Demonstrating effect of interlayer coupling (omega) on clustering")
print()

omega_values = [0.0, 0.5, 1.0, 5.0]

print("Testing different omega values:")
for omega in omega_values:
    result = spectral_multilayer_supra(
        network,
        k=2,
        omega=omega,
        random_state=42
    )
    
    partition = result["partition_nodes"]
    n_communities = len(set(partition.values()))
    
    print(f"  omega={omega:.1f}: {n_communities} communities")

# ═══════════════════════════════════════════════════════════════════════════════
# Example F: Comparison of Variants
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[7] Example F: Comparison of Variants")
print("-" * 80)

print("\nKey Differences:")
print("+--------------------+---------------------------+---------------------------+")
print("| Property           | Supra-Laplacian           | Multiplex (Aggregated)    |")
print("+====================+===========================+===========================+")
print("| Coupling           | Identity links (omega)    | Implicit via aggregation  |")
print("| Memory             | O((nL)^2)                 | O(n^2)                    |")
print("| Embedding dim      | nL, then averaged to n    | n                         |")
print("| Layer distinction  | Explicit via supra-graph  | Averaged out              |")
print("| Omega parameter    | Required                  | Not applicable            |")
print("+--------------------+---------------------------+---------------------------+")

print("\nWhen to use each variant:")
print("  Supra-Laplacian:")
print("    - When layer-specific coupling is important")
print("    - When you need explicit interlayer link control (omega)")
print("    - For smaller networks where memory is not a constraint")
print()
print("  Multiplex (Aggregated):")
print("    - For larger networks (better scalability)")
print("    - When layer coupling is implicit through aggregation")
print("    - When you want simpler parameter tuning (no omega)")

# ═══════════════════════════════════════════════════════════════════════════════
# Example G: Determinism Check
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("[8] Example G: Determinism Check")
print("-" * 80)
print("Verifying reproducibility with fixed random_state")
print()

# Run twice with same seed
result1 = spectral_multilayer_multiplex(network, k=2, random_state=42)
result2 = spectral_multilayer_multiplex(network, k=2, random_state=42)

partition1 = result1["partition_nodes"]
partition2 = result2["partition_nodes"]

identical = partition1 == partition2
print(f"Partitions identical: {identical}")
print(f"This demonstrates deterministic behavior with fixed random_state.")

# ═══════════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 80)
print("MULTILAYER SPECTRAL CLUSTERING - SUMMARY")
print("=" * 80)

print("\nImplemented Variants:")
print("  1. Supra-Laplacian Spectral Clustering")
print("     - Method: 'spectral_multilayer_supra'")
print("     - Parameters: k (required), omega (required), random_state (optional)")
print()
print("  2. Multiplex (Aggregated) Laplacian Spectral Clustering")
print("     - Method: 'spectral_multilayer_multiplex'")
print("     - Parameters: k (required), random_state (optional)")

print("\nDSL v2 Integration:")
print("  Q.nodes()")
print("   .from_layers(L[\"layer1\"] + L[\"layer2\"])")
print("   .community(method=\"spectral_multilayer_*\", k=3, ...)")
print("   .execute(network)")

print("\nKey Points:")
print("  ✓ Deterministic with fixed random_state")
print("  ✓ Node-level community assignments")
print("  ✓ Access to spectral embeddings via result metadata")
print("  ✓ Both variants reduce to standard spectral clustering for L=1")
print("  ✓ k must be provided (no automatic selection)")

print("\nFor more information:")
print("  - Module: py3plex.algorithms.community_detection.spectral_multilayer")
print("  - Tests: tests/test_spectral_multilayer.py")
print("  - Documentation: See module docstrings")
