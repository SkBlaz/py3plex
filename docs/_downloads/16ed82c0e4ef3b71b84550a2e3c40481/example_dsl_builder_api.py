"""Example: DSL v2 Python Builder API

This example demonstrates the complete DSL v2 Python builder API including:
- Q.nodes() and Q.edges() query builders
- Layer algebra with L[] proxy (union, difference, intersection)
- WHERE conditions with Django-style lookups (degree__gt, layer__ne, etc.)
- COMPUTE with aliases
- ORDER BY and LIMIT
- Parameterized queries with Param
- QueryResult exports (to_pandas, to_networkx, to_arrow, to_dict)
- EXPLAIN mode for query planning
- Error handling with suggestions

The builder API provides type hints, IDE autocomplete, and a chainable
interface for constructing complex queries without string parsing.
"""

from py3plex.core import multinet
from py3plex.dsl import (
    Q,
    L,
    Param,
    QueryResult,
    DslError,
    UnknownMeasureError,
    measure_registry,
)

print("=" * 80)
print("DSL V2 PYTHON BUILDER API EXAMPLES")
print("=" * 80)

# Create a sample multilayer network
print("\n[1] Creating sample multilayer network...")
print("-" * 80)

network = multinet.multi_layer_network(directed=False)

# Add nodes across multiple layers
nodes = []
people = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank']
layers = ['social', 'work', 'hobby']

for person in people:
    for layer in layers:
        nodes.append({'source': person, 'type': layer})

network.add_nodes(nodes)

# Add edges within layers
edges = [
    # Social connections (well connected)
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Charlie', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'David', 'target': 'Frank', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},

    # Work connections (moderately connected)
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'David', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work'},

    # Hobby connections (sparse)
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'hobby', 'target_type': 'hobby'},
    {'source': 'Eve', 'target': 'Frank', 'source_type': 'hobby', 'target_type': 'hobby'},
]

network.add_edges(edges)

print(f"Network created with {len(people)} people across {len(layers)} layers")
print(f"Total nodes: {len(list(network.get_nodes()))}")
print(f"Total edges: {len(list(network.get_edges()))}")

# Example 1: Basic query builder
print("\n" + "=" * 80)
print("[2] Example 1: Basic Query Builder")
print("-" * 80)
print("Code: Q.nodes().execute(network)")
print()

result = Q.nodes().execute(network)
print(f"Found {result.count} nodes")
print(f"First 5 nodes: {result.items[:5]}")

# Example 2: Filter by layer with WHERE
print("\n" + "=" * 80)
print("[3] Example 2: Filter by Layer")
print("-" * 80)
print('Code: Q.nodes().where(layer="social").execute(network)')
print()

result = Q.nodes().where(layer="social").execute(network)
print(f"Nodes in social layer: {result.count}")

# Example 3: Django-style field lookups
print("\n" + "=" * 80)
print("[4] Example 3: Django-Style Field Lookups")
print("-" * 80)
print("Code: Q.nodes().where(degree__gt=2).execute(network)")
print()

result = Q.nodes().where(degree__gt=2).execute(network)
print(f"High-degree nodes (degree > 2): {result.count}")
for node in result.items[:5]:
    print(f"  {node}")

# Example 4: Multiple conditions (combined with AND)
print("\n" + "=" * 80)
print("[5] Example 4: Multiple Conditions")
print("-" * 80)
print('Code: Q.nodes().where(layer="social", degree__gt=1).execute(network)')
print()

result = Q.nodes().where(layer="social", degree__gt=1).execute(network)
print(f"Social nodes with degree > 1: {result.count}")

# Example 5: Layer algebra - Union
print("\n" + "=" * 80)
print("[6] Example 5: Layer Algebra - Union")
print("-" * 80)
print('Code: Q.nodes().from_layers(L["social"] + L["work"]).execute(network)')
print()

result = Q.nodes().from_layers(L["social"] + L["work"]).execute(network)
print(f"Nodes in social OR work layers: {result.count}")

# Example 6: Layer algebra - Difference
print("\n" + "=" * 80)
print("[7] Example 6: Layer Algebra - Difference")
print("-" * 80)
print('Code: Q.nodes().from_layers(L["social"] - L["hobby"]).execute(network)')
print()

result = Q.nodes().from_layers(L["social"] - L["hobby"]).execute(network)
print(f"Nodes in social but not hobby: {result.count}")

# Example 7: Layer algebra - Intersection
print("\n" + "=" * 80)
print("[8] Example 7: Layer Algebra - Intersection")
print("-" * 80)
print('Code: Q.nodes().from_layers(L["social"] & L["work"]).execute(network)')
print()

result = Q.nodes().from_layers(L["social"] & L["work"]).execute(network)
print(f"Nodes in both social AND work: {result.count}")

# Example 8: Compute measures
print("\n" + "=" * 80)
print("[9] Example 8: Compute Network Measures")
print("-" * 80)
print('Code: Q.nodes().compute("degree", "clustering").execute(network)')
print()

result = Q.nodes().compute("degree", "clustering").execute(network)
print(f"Computed measures for {result.count} nodes")
print("Sample results (first 5):")
for node in result.items[:5]:
    degree = result.attributes.get('degree', {}).get(node, 'N/A')
    clustering = result.attributes.get('clustering', {}).get(node, 'N/A')
    print(f"  {node}: degree={degree}, clustering={clustering:.3f}" if clustering != 'N/A' else f"  {node}: degree={degree}")

# Example 9: Compute with alias
print("\n" + "=" * 80)
print("[10] Example 9: Compute with Alias")
print("-" * 80)
print('Code: Q.nodes().compute("betweenness_centrality", alias="bc").execute(network)')
print()

result = Q.nodes().compute("betweenness_centrality", alias="bc").execute(network)
print("Top 5 nodes by betweenness centrality:")
for node in result.items[:5]:
    bc = result.attributes.get('bc', {}).get(node, 0)
    print(f"  {node}: {bc:.4f}")

# Example 10: ORDER BY ascending
print("\n" + "=" * 80)
print("[11] Example 10: ORDER BY Ascending")
print("-" * 80)
print('Code: Q.nodes().compute("degree").order_by("degree").limit(5).execute(network)')
print()

result = Q.nodes().compute("degree").order_by("degree").limit(5).execute(network)
print("5 nodes with lowest degree:")
for node in result.items:
    degree = result.attributes.get('degree', {}).get(node, 0)
    print(f"  {node}: degree={degree}")

# Example 11: ORDER BY descending
print("\n" + "=" * 80)
print("[12] Example 11: ORDER BY Descending")
print("-" * 80)
print('Code: Q.nodes().compute("degree").order_by("-degree").limit(5).execute(network)')
print()

result = Q.nodes().compute("degree").order_by("-degree").limit(5).execute(network)
print("Top 5 nodes by degree:")
for node in result.items:
    degree = result.attributes.get('degree', {}).get(node, 0)
    print(f"  {node}: degree={degree}")

# Example 12: Parameterized queries
print("\n" + "=" * 80)
print("[13] Example 12: Parameterized Queries")
print("-" * 80)
print('Code: q = Q.nodes().where(layer="social", degree__gt=Param.int("min_degree"))')
print(' q.execute(network, min_degree=1)')
print()

# Create a reusable query template
q = Q.nodes().where(layer="social", degree__gt=Param.int("min_degree"))

print("Execute with min_degree=1:")
result = q.execute(network, min_degree=1)
print(f" Found {result.count} nodes")

print("\nExecute with min_degree=2:")
result = q.execute(network, min_degree=2)
print(f" Found {result.count} nodes")

# Example 13: Export to pandas DataFrame
print("\n" + "=" * 80)
print("[14] Example 13: Export to Pandas DataFrame")
print("-" * 80)
print('Code: result = Q.nodes().compute("degree", "clustering").execute(network)')
print(' df = result.to_pandas()')
print()

result = Q.nodes().where(layer="social").compute("degree", "clustering").execute(network)
df = result.to_pandas()
print("Pandas DataFrame:")
print(df.head(10))

# Example 14: Export to dictionary
print("\n" + "=" * 80)
print("[15] Example 14: Export to Dictionary")
print("-" * 80)
print('Code: result.to_dict()')
print()

result = Q.nodes().where(layer="work").compute("degree").limit(3).execute(network)
data = result.to_dict()
print(f"Dictionary with {len(data['nodes'])} items")
print(f"Keys: {list(data.keys())}")
print(f"Sample nodes: {data['nodes'][:3]}")
print(f"Sample degree values: {list(data['computed'].get('degree', {}).items())[:3]}")

# Example 15: Query to DSL string
print("\n" + "=" * 80)
print("[16] Example 15: Convert Builder to DSL String")
print("-" * 80)
print('Code: q = Q.nodes().where(layer="social", degree__gt=2).compute("degree")')
print(' dsl_string = q.to_dsl()')
print()

q = Q.nodes().where(layer="social", degree__gt=2).compute("degree").limit(10)
dsl_string = q.to_dsl()
print(f"DSL string: {dsl_string}")

# Example 16: EXPLAIN mode
print("\n" + "=" * 80)
print("[17] Example 16: EXPLAIN Mode - Query Planning")
print("-" * 80)
print('Code: plan = Q.nodes().compute("betweenness_centrality").explain().execute(network)')
print()

q = Q.nodes().where(layer="social").compute("betweenness_centrality")
plan = q.explain().execute(network)

print("Execution plan:")
for step in plan.steps:
    print(f"  {step.description} (complexity: {step.estimated_complexity})")

if plan.warnings:
    print("\nWarnings:")
    for warning in plan.warnings:
        print(f"   {warning}")

# Example 17: Complex query combining multiple features
print("\n" + "=" * 80)
print("[18] Example 17: Complex Query - Putting It All Together")
print("-" * 80)
print('Code: (Q.nodes()')
print(' .from_layers(L["social"] + L["work"])')
print(' .where(degree__gt=1)')
print(' .compute("betweenness_centrality", alias="bc")')
print(' .order_by("-bc")')
print(' .limit(5)')
print(' .execute(network))')
print()

result = (
    Q.nodes()
    .from_layers(L["social"] + L["work"])
    .where(degree__gt=1)
    .compute("betweenness_centrality", alias="bc")
    .order_by("-bc")
    .limit(5)
    .execute(network)
)

print("Top 5 influential nodes (social + work layers, degree > 1):")
for node in result.items:
    bc = result.attributes.get('bc', {}).get(node, 0)
    print(f"  {node}: betweenness={bc:.4f}")

# Example 18: Error handling with suggestions
print("\n" + "=" * 80)
print("[19] Example 18: Error Handling with Suggestions")
print("-" * 80)
print('Code: Q.nodes().compute("betweenes").execute(network) # Typo!')
print()

try:
    result = Q.nodes().compute("betweenes").execute(network)
except UnknownMeasureError as e:
    print(f"Error caught: {e}")
    print("\nThis demonstrates the 'Did you mean?' feature for typos")

# Example 19: Available measures
print("\n" + "=" * 80)
print("[20] Example 19: List Available Measures")
print("-" * 80)
print("Code: measure_registry.list_measures()")
print()

measures = measure_registry.list_measures()
print(f"Available measures ({len(measures)}):")
for measure in sorted(measures)[:10]:
    desc = measure_registry.get_description(measure)
    print(f"  • {measure}: {desc}")
print(f" ... and {len(measures) - 10} more")

# Summary
print("\n" + "=" * 80)
print("DSL V2 BUILDER API EXAMPLES COMPLETE")
print("=" * 80)
print("\nKey Features Demonstrated:")
print(" Q.nodes() and query builder pattern")
print(" Layer algebra with L[] (union, difference, intersection)")
print(" Django-style WHERE conditions (degree__gt, layer__ne, etc.)")
print(" COMPUTE with aliases")
print(" ORDER BY and LIMIT")
print(" Parameterized queries with Param")
print(" QueryResult exports (to_pandas, to_dict)")
print(" Query to DSL string conversion (to_dsl())")
print(" EXPLAIN mode for query planning")
print(" Error handling with suggestions")
print(" Complex multi-feature queries")
print("\nAdvantages of Builder API:")
print(" • Type hints and IDE autocomplete")
print(" • No string parsing errors")
print(" • Composable and reusable queries")
print(" • Better error messages")
print(" • Chainable, fluent interface")
print("\nFor more information:")
print(" • Documentation: docfiles/user_guide/dsl.rst")
print(" • String DSL examples: example_dsl_queries.py")
print(" • Advanced queries: example_dsl_advanced.py")
