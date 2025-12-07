"""Example: Community Detection with DSL Filtering

This example demonstrates how to combine community detection algorithms
with DSL queries to analyze community structure in multilayer networks.

Key workflow:
1. Detect communities using Louvain algorithm
2. Store community IDs as node attributes
3. Use DSL to filter and analyze specific communities
4. Export results for further analysis

This pattern is useful for:
- Finding hubs within specific communities
- Comparing statistics across communities
- Exporting community-specific data for visualization or ML pipelines
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L
from py3plex.algorithms.community_detection import community_louvain

print("=" * 70)
print("COMMUNITY DETECTION WITH DSL FILTERING")
print("=" * 70)

# ============================================================================
# Create a sample multilayer network with community structure
# ============================================================================

print("\n[1] Creating network with community structure...")
print("-" * 70)

network = multinet.multi_layer_network(directed=False)

# Add nodes - 3 distinct communities with different characteristics
nodes = [
    # Community 1: Hub-and-spoke structure (4 nodes)
    {'source': 'Alice', 'type': 'social'},    # Will be hub
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Charlie', 'type': 'social'},
    {'source': 'Diana', 'type': 'social'},
    
    # Community 2: Dense cluster (4 nodes)
    {'source': 'Eve', 'type': 'social'},
    {'source': 'Frank', 'type': 'social'},
    {'source': 'Grace', 'type': 'social'},
    {'source': 'Henry', 'type': 'social'},
    
    # Community 3: Small tight group (3 nodes)
    {'source': 'Ivy', 'type': 'social'},
    {'source': 'Jack', 'type': 'social'},
    {'source': 'Kate', 'type': 'social'},
]
network.add_nodes(nodes)

edges = [
    # Community 1: Hub structure (Alice connects to all)
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Diana', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    
    # Community 2: Dense structure (complete subgraph)
    {'source': 'Eve', 'target': 'Frank', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Eve', 'target': 'Grace', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Eve', 'target': 'Henry', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Frank', 'target': 'Grace', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Frank', 'target': 'Henry', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Grace', 'target': 'Henry', 'source_type': 'social', 'target_type': 'social'},
    
    # Community 3: Triangle (complete graph)
    {'source': 'Ivy', 'target': 'Jack', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Ivy', 'target': 'Kate', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Jack', 'target': 'Kate', 'source_type': 'social', 'target_type': 'social'},
    
    # Bridges between communities (weak ties)
    {'source': 'Diana', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Henry', 'target': 'Ivy', 'source_type': 'social', 'target_type': 'social'},
]
network.add_edges(edges)

print(f"Network created: {len(list(network.get_nodes()))} nodes, {len(list(network.get_edges()))} edges")

# ============================================================================
# Step 1: Detect communities using Louvain algorithm
# ============================================================================

print("\n[2] Detecting communities with Louvain algorithm...")
print("-" * 70)

communities = community_louvain.best_partition(network.core_network)
num_communities = len(set(communities.values()))

print(f"Detected {num_communities} communities:")
for comm_id in sorted(set(communities.values())):
    members = [str(node[0]) for node, cid in communities.items() if cid == comm_id]
    print(f"  Community {comm_id}: {', '.join(sorted(members))}")

# ============================================================================
# Step 2: Store community IDs as node attributes
# ============================================================================

print("\n[3] Storing community IDs as node attributes...")
print("-" * 70)

for node, comm_id in communities.items():
    network.core_network.nodes[node]['community'] = comm_id

print("✓ Community IDs stored successfully")

# ============================================================================
# Step 3: Use DSL to filter by community and find hubs
# ============================================================================

print("\n[4] Finding high-degree nodes in community 0 using DSL...")
print("-" * 70)

result = (
    Q.nodes()
     .where(community=0)  # Filter by community ID
     .compute("degree", "betweenness_centrality")
     .order_by("-degree")
     .limit(10)
     .execute(network)
)

print(f"Query returned {result.count} nodes from community 0:")
df = result.to_pandas()

print(f"{'Node':<15} {'Degree':<10} {'Betweenness':<15}")
print("-" * 40)
for _, row in df.iterrows():
    node_name = row['id'][0]
    degree = row['degree']
    betweenness = row['betweenness_centrality']
    print(f"{node_name:<15} {degree:<10} {betweenness:<15.4f}")

# ============================================================================
# Step 4: Analyze all communities and export
# ============================================================================

print("\n[5] Analyzing all nodes and exporting to CSV...")
print("-" * 70)

# Get all nodes with their metrics
result = (
    Q.nodes()
     .compute("degree", "betweenness_centrality")
     .order_by("-degree")
     .execute(network)
)

df = result.to_pandas()

# Add community information
df['community'] = df['id'].apply(
    lambda x: network.core_network.nodes[x].get('community', -1)
)

# Extract node name for readability
df['name'] = df['id'].apply(lambda x: x[0])

# Reorder columns
df = df[['name', 'community', 'degree', 'betweenness_centrality']]

print("Community hub analysis:")
print(df.to_string(index=False))

# Export to CSV
output_file = "community_hubs.csv"
df.to_csv(output_file, index=False)
print(f"\n✓ Results exported to {output_file}")

# ============================================================================
# Step 5: Compare statistics across communities
# ============================================================================

print("\n[6] Comparing statistics across communities...")
print("-" * 70)

for comm_id in sorted(set(communities.values())):
    result = (
        Q.nodes()
         .where(community=comm_id)
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )
    
    df_comm = result.to_pandas()
    
    print(f"Community {comm_id}:")
    print(f"  Size: {result.count} nodes")
    print(f"  Avg degree: {df_comm['degree'].mean():.2f}")
    print(f"  Avg betweenness: {df_comm['betweenness_centrality'].mean():.4f}")
    print(f"  Max degree: {df_comm['degree'].max()}")

# ============================================================================
# Summary
# ============================================================================

print("\n" + "=" * 70)
print("EXAMPLE COMPLETE")
print("=" * 70)
print("\nKey takeaways:")
print("  1. Use Louvain (or any algorithm) to detect communities")
print("  2. Store community IDs as node attributes in core_network")
print("  3. Use DSL .where(community=X) to filter by community")
print("  4. Chain with .compute(), .order_by(), .limit() for analysis")
print("  5. Export with .to_pandas() and save to CSV for further work")
print("\nThis pattern enables powerful community-specific analyses!")
