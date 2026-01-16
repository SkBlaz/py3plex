"""Example demonstrating first-class joins in py3plex DSL v2.

This example shows how to:
1. Create queries and join them
2. Use different join types (inner, left, semi, anti)
3. Inspect join provenance
4. Handle join validation errors
"""

from py3plex.core import multinet
from py3plex.dsl import Q, L, InvalidJoinKeyError

# Create a sample multilayer network
network = multinet.multi_layer_network(directed=False)

# Add nodes
nodes = [
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Charlie', 'type': 'social'},
    {'source': 'Dave', 'type': 'work'},
    {'source': 'Eve', 'type': 'work'},
    {'source': 'Frank', 'type': 'work'},
]
network.add_nodes(nodes)

# Add edges
edges = [
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Dave', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'Eve', 'target': 'Frank', 'source_type': 'work', 'target_type': 'work'},
]
network.add_edges(edges)

print("=" * 60)
print("Example 1: Inner Join - Nodes with Communities")
print("=" * 60)

# Assign a simple community partition
network.assign_partition({
    ('Alice', 'social'): 1,
    ('Bob', 'social'): 1,
    ('Charlie', 'social'): 2,
    ('Dave', 'work'): 1,
    ('Eve', 'work'): 1,
    ('Frank', 'work'): 2,
})

# Query 1: Get all nodes with degree
nodes_query = Q.nodes().compute("degree")

# Query 2: Get community membership (Note: This is a simplification)
# In practice, you'd use Q.communities().members()
# For this example, we'll join with the same nodes
communities_query = Q.nodes()

# Join them
result = (
    nodes_query
    .join(communities_query, on=["id", "layer"], how="inner")
    .order_by("degree", desc=True)
    .execute(network)
)

print(f"Joined {len(result.items)} nodes")
print(f"Columns: {list(result.attributes.keys())}")
print(f"\nFirst 3 rows:")
df = result.to_pandas()
print(df.head(3))

# Check provenance
print(f"\nProvenance:")
if "provenance" in result.meta and "join" in result.meta["provenance"]:
    join_info = result.meta["provenance"]["join"]
    print(f"  Join type: {join_info['type']}")
    print(f"  Join keys: {join_info['on']}")
    print(f"  Row counts: {join_info['row_counts']}")

print("\n" + "=" * 60)
print("Example 2: Left Join - All nodes, with optional data")
print("=" * 60)

# Left join keeps all left rows, even without matches
social_nodes = Q.nodes().where(layer="social").compute("degree")
work_nodes = Q.nodes().where(layer="work")

result = (
    social_nodes
    .join(work_nodes, on=["id"], how="left")  # Join only on id
    .execute(network)
)

print(f"Left join produced {len(result.items)} rows")
print(f"(Should be all social nodes, even without work matches)")

print("\n" + "=" * 60)
print("Example 3: Semi Join - Find nodes that exist in both")
print("=" * 60)

# Semi-join returns left rows that have a match in right
all_nodes = Q.nodes()
high_degree = Q.nodes().compute("degree")  # .where(degree__gt=1)

result = (
    all_nodes
    .join(high_degree, on=["id", "layer"], how="semi")
    .execute(network)
)

print(f"Semi join found {len(result.items)} matching nodes")

print("\n" + "=" * 60)
print("Example 4: Anti Join - Find nodes NOT in second set")
print("=" * 60)

# Anti-join returns left rows that have NO match in right
all_nodes = Q.nodes()
social_only = Q.nodes().where(layer="social")

result = (
    all_nodes
    .join(social_only, on=["id", "layer"], how="anti")
    .execute(network)
)

print(f"Anti join found {len(result.items)} non-social nodes")
print(f"(Should be work layer nodes only)")

print("\n" + "=" * 60)
print("Example 5: Error Handling - Invalid Join Keys")
print("=" * 60)

try:
    # Try to join on a non-existent key
    bad_query = (
        Q.nodes()
        .join(Q.nodes(), on=["nonexistent_key"], how="inner")
    )
    bad_query.execute(network)
except InvalidJoinKeyError as e:
    print(f"Caught expected error:")
    print(f"  Message: {str(e).split('Stage:')[0].strip()}")
    print(f"  Stage: {e.stage}")
    print(f"  Missing keys: {e.missing_keys}")
    print(f"  Available fields: {e.available_fields[:5]}...")

print("\n" + "=" * 60)
print("Example 6: Post-Join Operations")
print("=" * 60)

# Chain operations after join
result = (
    Q.nodes().compute("degree")
    .join(Q.nodes(), on=["id", "layer"], how="inner")
    .where(layer="social")  # Filter after join
    .order_by("degree", desc=True)
    .limit(2)
    .execute(network)
)

print(f"Post-join filtering and limiting:")
print(f"  Filtered to layer=social, ordered by degree, limited to 2")
print(f"  Result: {len(result.items)} rows")

print("\n" + "=" * 60)
print("Example 7: Result-Level Join (Escape Hatch)")
print("=" * 60)

# Pre-execute both queries
left_result = Q.nodes().where(layer="social").compute("degree").execute(network)
right_result = Q.nodes().where(layer="social").execute(network)

print(f"Left result: {len(left_result.items)} rows")
print(f"Right result: {len(right_result.items)} rows")

# Join the results
joined_builder = left_result.join(right_result, on=["id", "layer"], how="inner")
final_result = joined_builder.execute(network)

print(f"Joined result: {len(final_result.items)} rows")

print("\n" + "=" * 60)
print("All examples completed successfully!")
print("=" * 60)
