"""Example: Community Queries with py3plex DSL v2.

This example demonstrates the new first-class community support in py3plex.
"""

from py3plex.core import multinet
from py3plex.dsl import Q, detect_communities

print("=" * 80)
print("FIRST-CLASS COMMUNITY SUPPORT IN PY3PLEX DSL")
print("=" * 80)

# Create a network with clear community structure
print("\n[1] Creating network with community structure...")
network = multinet.multi_layer_network(directed=False)

# Add nodes (3 communities)
nodes = [
    # Community 1: Alice, Bob, Charlie
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Charlie', 'type': 'social'},
    # Community 2: David, Eve, Frank, Grace
    {'source': 'David', 'type': 'social'},
    {'source': 'Eve', 'type': 'social'},
    {'source': 'Frank', 'type': 'social'},
    {'source': 'Grace', 'type': 'social'},
    # Community 3: Henry, Ivy
    {'source': 'Henry', 'type': 'social'},
    {'source': 'Ivy', 'type': 'social'},
]
network.add_nodes(nodes)

# Add edges (dense within communities, sparse between)
edges = [
    # Community 1 (fully connected)
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    # Community 2 (fully connected)
    {'source': 'David', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'David', 'target': 'Frank', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'David', 'target': 'Grace', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Eve', 'target': 'Frank', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Eve', 'target': 'Grace', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Frank', 'target': 'Grace', 'source_type': 'social', 'target_type': 'social'},
    # Community 3 (single edge)
    {'source': 'Henry', 'target': 'Ivy', 'source_type': 'social', 'target_type': 'social'},
    # Bridge edges
    {'source': 'Charlie', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Grace', 'target': 'Henry', 'source_type': 'social', 'target_type': 'social'},
]
network.add_edges(edges)

print(f"Created network: {len(list(network.get_nodes()))} nodes, {len(list(network.get_edges()))} edges")

# Detect communities
print("\n[2] Detecting communities...")
communities_info = detect_communities(network)
partition = communities_info['partition']
network.assign_partition(partition)
print(f"Detected {len(set(partition.values()))} communities")

# Query communities with DSL v2
print("\n[3] Querying communities with DSL v2...")
print("-" * 80)

result = Q.communities().execute(network)
print(f"Total communities: {len(result.items)}")
print(f"Community IDs: {result.items}")

# Show community details as pandas DataFrame
df = result.to_pandas()
print("\nCommunity Details:")
print(df[['community_id', 'size', 'intra_edges', 'inter_edges', 'density_intra']])

# Filter large communities
print("\n[4] Filtering large communities (size > 2)...")
print("-" * 80)

result = Q.communities().where(size__gt=2).execute(network)
print(f"Large communities: {result.items}")

df = result.to_pandas()
print("\nLarge Community Details:")
print(df[['community_id', 'size', 'density_intra']])

# Compute community metrics
print("\n[5] Computing community conductance...")
print("-" * 80)

result = (
    Q.communities()
     .compute("conductance")
     .order_by("conductance")
     .execute(network)
)

df = result.to_pandas()
print("\nCommunities by Conductance (lower = more cohesive):")
print(df[['community_id', 'size', 'conductance']])

# Bridge to member nodes
print("\n[6] Getting members of large communities...")
print("-" * 80)

result = (
    Q.communities()
     .where(size__gt=2)
     .members()  # Bridge to nodes
     .compute("degree")
     .execute(network)
)

df = result.to_pandas()
print(f"Found {len(df)} members in large communities")
print("\nMembers with degree:")
print(df[['id', 'layer', 'degree']])

# Bridge to boundary edges
print("\n[7] Getting boundary edges between communities...")
print("-" * 80)

result = (
    Q.communities()
     .boundary_edges()  # Bridge to edges
     .execute(network)
)

print(f"Found {len(result.items)} boundary edges")
df = result.to_pandas()
print("\nBoundary Edges:")
print(df[['source', 'target', 'source_layer', 'target_layer']])

print("\n" + "=" * 80)
print("COMMUNITY QUERIES DEMONSTRATION COMPLETE")
print("=" * 80)
print("\nKey Takeaways:")
print(" Communities are now first-class DSL targets")
print(" Filter communities by size, density, connectivity")
print(" Compute community-level metrics")
print(" Bridge seamlessly to nodes and edges")
print(" Export to pandas for further analysis")
