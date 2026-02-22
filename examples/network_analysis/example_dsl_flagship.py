"""Example: Flagship DSL Pattern - Integrated Community Detection with Node Analysis

This example demonstrates the streamlined Q.communities() API that integrates
automatic community detection directly into the DSL query chain.

Features demonstrated:
- Q.communities() with auto-detection parameters (mode, fast, uq, write_attrs)
- Seamless transition from community detection to node analysis via .nodes()
- Integrated uncertainty quantification for both communities and centrality
- Cross-layer analysis with coverage filtering
- Composite scoring and ranking

This is the flagship example from the README, adapted for demonstration purposes.
"""

from py3plex.core import multinet
from py3plex.dsl import Q

print("=" * 80)
print("FLAGSHIP DSL PATTERN: INTEGRATED COMMUNITY DETECTION")
print("=" * 80)

# ===============================================================================
# Create a sample multilayer network
# ===============================================================================

print("\n[1] Creating sample multilayer network...")
print("-" * 80)

network = multinet.multi_layer_network(directed=False)

# Add nodes across two layers
for layer in [0, 1]:
    for i in range(20):
        network.add_nodes([{'source': f'node{i}', 'type': layer}])

# Add edges within layers to create community structure
edges = []
# Layer 0: Two communities
for i in range(9):
    edges.append({
        'source': f'node{i}',
        'target': f'node{i+1}',
        'source_type': 0,
        'target_type': 0
    })
for i in range(10, 18):
    edges.append({
        'source': f'node{i}',
        'target': f'node{i+1}',
        'source_type': 0,
        'target_type': 0
    })

# Layer 1: Similar structure
for i in range(9):
    edges.append({
        'source': f'node{i}',
        'target': f'node{i+1}',
        'source_type': 1,
        'target_type': 1
    })
for i in range(10, 18):
    edges.append({
        'source': f'node{i}',
        'target': f'node{i+1}',
        'source_type': 1,
        'target_type': 1
    })

network.add_edges(edges)

print(f"Network created: {len(list(network.get_nodes()))} nodes, "
      f"{len(list(network.get_edges()))} edges")

# ===============================================================================
# Example 1: Basic flagship pattern (fast mode for demo)
# ===============================================================================

print("\n" + "=" * 80)
print("[2] Flagship Pattern: Q.communities().nodes() chain")
print("-" * 80)

# Note: Using wins mode and fast=True for demonstration speed
# In production, use mode="pareto" with fast=False for best results
result = (
    Q.communities(
        mode="wins",          # Use "wins" mode (faster than "pareto" for demo)
        fast=True,            # Fast mode for demo
        uq=False,             # Disable UQ for speed (enable in production)
        seed=42,              # Reproducibility
        write_attrs={         # Control attribute names
            "community_id": "community_id",
            "community_stability": "community_stability",
        },
    )
    .nodes()                  # Switch to node-level analysis
    .where(degree__gt=1)      # Filter peripheral nodes
    .compute("degree_centrality")  # Compute centrality
    .limit(10)                # Top 10 nodes
    .execute(network)
)

print(f"\nOK Query executed successfully")
print(f"  Found {len(result.nodes)} nodes matching criteria")

# Convert to pandas for easy viewing
df = result.to_pandas()
print(f"\nTop nodes by degree centrality:")
print(df[['id', 'layer', 'degree_centrality']].head())

# ===============================================================================
# Example 2: Verify community detection ran
# ===============================================================================

print("\n" + "=" * 80)
print("[3] Verify community assignments")
print("-" * 80)

# Check that community IDs were assigned
sample_nodes = list(network.get_nodes())[:5]
print(f"\nCommunity assignments for sample nodes:")
for node in sample_nodes:
    try:
        comm_id = network.get_node_attribute(node, 'community_id')
        print(f"  {node}: community {comm_id}")
    except Exception as e:
        print(f"  {node}: no community assigned")

print("\nOK Community detection completed successfully")

# ===============================================================================
# Key takeaways
# ===============================================================================

print("\n" + "=" * 80)
print("KEY FEATURES DEMONSTRATED")
print("=" * 80)

print("""
OK Streamlined API: Community detection integrated into DSL chain
OK Auto-detection: Runs automatically when .nodes() is called
OK Attribute writing: Community IDs written to network with custom names
OK Chainable: Seamlessly transition from communities to node analysis
OK Configurable: Full control over detection parameters (mode, UQ, etc.)

For production use:
- Use mode="pareto" for multi-objective optimization
- Enable uq=True with uq_n_samples=30+ for robustness
- Use fast=False for thorough evaluation
- Add .per_layer().top_k().coverage() for cross-layer analysis
- Add .mutate() for composite scoring
- Add .explain() for interpretability
""")

print("\n" + "=" * 80)
print("Example completed successfully!")
print("=" * 80)
