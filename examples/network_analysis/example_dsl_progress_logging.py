"""Example: DSL Progress Logging

This example demonstrates how to enable progress logging for DSL queries
to see what steps are being executed during query execution.

Progress logging is useful for:
- Debugging complex queries
- Understanding query execution flow
- Monitoring long-running queries
- Educational purposes
"""

import logging
from py3plex.core import multinet
from py3plex.dsl import Q, L

# Configure logging to see progress messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("=" * 80)
print("DSL PROGRESS LOGGING EXAMPLE")
print("=" * 80)

# Create a sample multilayer network
print("\n[1] Creating sample multilayer network...")
print("-" * 80)

network = multinet.multi_layer_network(directed=False)

# Add nodes across multiple layers
nodes = []
people = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Henry']
layers = ['social', 'work', 'hobby']

for person in people:
    for layer in layers:
        nodes.append({'source': person, 'type': layer})

network.add_nodes(nodes)

# Add edges within layers
edges = [
    # Social connections
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Charlie', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'David', 'target': 'Frank', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Eve', 'target': 'Grace', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Frank', 'target': 'Henry', 'source_type': 'social', 'target_type': 'social'},

    # Work connections
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'David', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'Eve', 'target': 'Frank', 'source_type': 'work', 'target_type': 'work'},

    # Hobby connections
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'hobby', 'target_type': 'hobby'},
    {'source': 'Eve', 'target': 'Frank', 'source_type': 'hobby', 'target_type': 'hobby'},
    {'source': 'Grace', 'target': 'Henry', 'source_type': 'hobby', 'target_type': 'hobby'},
]

network.add_edges(edges)

print(f"Created network with {len(people)} people across {len(layers)} layers")
print(f"Total nodes: {len(list(network.get_nodes()))}")
print(f"Total edges: {len(list(network.get_edges()))}")

# Example 1: Simple query without progress logging (default)
print("\n" + "=" * 80)
print("[2] Example 1: Query WITHOUT Progress Logging (default)")
print("-" * 80)
print("Code: Q.nodes().from_layers(L['social']).execute(network)")
print()

result = Q.nodes().from_layers(L["social"]).execute(network)
print(f"Result: {result.count} nodes in social layer")

# Example 2: Simple query WITH progress logging
print("\n" + "=" * 80)
print("[3] Example 2: Query WITH Progress Logging")
print("-" * 80)
print("Code: Q.nodes().from_layers(L['social']).execute(network, progress=True)")
print()

result = Q.nodes().from_layers(L["social"]).execute(network, progress=True)
print(f"Result: {result.count} nodes in social layer")

# Example 3: Complex query with progress logging
print("\n" + "=" * 80)
print("[4] Example 3: Complex Query with Progress Logging")
print("-" * 80)
print("""Code: Q.nodes()
    .from_layers(L['social'] + L['work'])
    .where(degree__gt=1)
    .compute('degree')
    .compute('betweenness')
    .order_by('betweenness', desc=True)
    .limit(5)
    .execute(network, progress=True)""")
print()

result = (
    Q.nodes()
     .from_layers(L["social"] + L["work"])
     .where(degree__gt=1)
     .compute("degree")
     .compute("betweenness")
     .order_by("betweenness", desc=True)
     .limit(5)
     .execute(network, progress=True)
)

print(f"\nResult: Top 5 nodes by betweenness centrality")
for item in result.items:
    node_id = item[0]
    betweenness = result.attributes.get("betweenness", {}).get(item, 0)
    print(f"  - {node_id}: betweenness={betweenness:.4f}")

# Example 4: Progress logging helps understand execution order
print("\n" + "=" * 80)
print("[5] Example 4: Understanding Execution Order")
print("-" * 80)
print("Progress logging shows the order of operations:")
print("  1. Parameter binding")
print("  2. Temporal context application")
print("  3. Getting initial items (nodes/edges)")
print("  4. Layer filtering")
print("  5. WHERE condition filtering")
print("  6. Computing measures")
print("  7. Applying ORDER BY")
print("  8. Applying LIMIT")
print("  9. Creating result")
print()

result = (
    Q.nodes()
     .from_layers(L["hobby"])
     .compute("degree")
     .order_by("degree", desc=True)
     .limit(3)
     .execute(network, progress=True)
)

print(f"\nResult: Top 3 nodes in hobby layer")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("Progress logging can be enabled by adding 'progress=True' to execute():")
print("  - Useful for debugging and understanding query execution")
print("  - Shows detailed steps including filtering, computing, and sorting")
print("  - Includes counts and timing information")
print("  - Can be enabled/disabled on a per-query basis")
