"""Example: Custom DSL Operators with Plugin System

This example demonstrates how to extend the py3plex DSL with custom operators
using the @dsl_operator decorator. Custom operators receive a DSLExecutionContext
that provides access to the network, selected layers, and nodes.

Features demonstrated:
1. Registering custom operators with @dsl_operator
2. Accessing network data through DSLExecutionContext
3. Returning scalar and dict values from operators
4. Using custom operators in DSL queries
5. Listing and describing registered operators
"""

from py3plex.core import multinet
from py3plex.dsl import (
    dsl_operator,
    DSLExecutionContext,
    Q,
    L,
    list_operators,
    describe_operator,
)

print("=" * 80)
print("CUSTOM DSL OPERATORS - PLUGIN SYSTEM")
print("=" * 80)

# ============================================================================
# Step 1: Create a sample multilayer network
# ============================================================================

print("\n[1] Creating sample multilayer network...")
print("-" * 80)

network = multinet.multi_layer_network(directed=False)

# Add nodes to multiple layers
nodes = [
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Charlie', 'type': 'social'},
    {'source': 'David', 'type': 'social'},
    {'source': 'Alice', 'type': 'work'},
    {'source': 'Bob', 'type': 'work'},
    {'source': 'Charlie', 'type': 'work'},
    {'source': 'Alice', 'type': 'transport'},
    {'source': 'Bob', 'type': 'transport'},
]
network.add_nodes(nodes)

# Add edges
edges = [
    # Social layer
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Bob', 'target': 'David', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    
    # Work layer
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
    
    # Transport layer
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'transport', 'target_type': 'transport', 'weight': 1.0},
]
network.add_edges(edges)

print(f"Created network with {network.core_network.number_of_nodes()} nodes")
print(f"and {network.core_network.number_of_edges()} edges")

# ============================================================================
# Step 2: Define custom operators using @dsl_operator
# ============================================================================

print("\n[2] Defining custom DSL operators...")
print("-" * 80)


@dsl_operator("layer_activity", description="Count edges in current layers", category="analytics")
def layer_activity_op(context: DSLExecutionContext):
    """Compute activity score based on number of edges in selected layers.
    
    Returns a dict mapping each node to the number of edges it has
    in the currently selected layers.
    """
    if not context.current_layers:
        return {}
    
    # Get the core network
    G = context.graph.core_network
    
    # Count edges for each node in selected layers
    activity = {}
    for node in context.current_nodes or []:
        if node in G:
            # Node is a tuple (node_id, layer)
            node_id, layer = node
            if layer in context.current_layers:
                activity[node] = G.degree(node)
            else:
                activity[node] = 0
        else:
            activity[node] = 0
    
    return activity


@dsl_operator("layer_diversity", description="Measure presence across layers", category="analytics")
def layer_diversity_op(context: DSLExecutionContext):
    """Compute diversity score = number of layers a node appears in.
    
    Returns a dict mapping each node to its layer diversity score.
    """
    diversity = {}
    
    # Count layers for each unique node ID
    node_layers = {}
    for node in context.current_nodes or []:
        if isinstance(node, tuple) and len(node) >= 2:
            node_id, layer = node[0], node[1]
            if node_id not in node_layers:
                node_layers[node_id] = set()
            node_layers[node_id].add(layer)
    
    # Assign diversity scores
    for node in context.current_nodes or []:
        if isinstance(node, tuple) and len(node) >= 2:
            node_id = node[0]
            diversity[node] = len(node_layers.get(node_id, set()))
    
    return diversity


@dsl_operator("constant_score", description="Return constant value for testing", category="test")
def constant_score_op(context: DSLExecutionContext):
    """Return a constant score for all nodes.
    
    This is a simple example showing scalar return values.
    """
    return 42.0


print("Registered custom operators:")
for name, op in list_operators().items():
    info = describe_operator(name)
    print(f"  - {name}: {info['description']} (category: {info['category']})")

# ============================================================================
# Step 3: Use custom operators in DSL queries
# ============================================================================

print("\n[3] Using custom operators in queries...")
print("-" * 80)

# Query 1: Compute layer activity for social layer
print("\n[Query 1] Layer activity in social layer:")
result1 = (
    Q.nodes()
    .from_layers(L["social"])
    .compute("layer_activity", alias="activity")
    .compute("degree", alias="degree")  # Compare with built-in degree
    .order_by("activity", desc=True)
    .execute(network)
)

df1 = result1.to_pandas()
print(df1.to_string(index=False))

# Query 2: Compute layer diversity across all layers
print("\n[Query 2] Layer diversity for nodes present in multiple layers:")
result2 = (
    Q.nodes()
    .compute("layer_diversity", alias="diversity")
    .order_by("diversity", desc=True)
    .execute(network)
)

df2 = result2.to_pandas()
print(df2.head(5).to_string(index=False))

# Query 3: Use constant score (demonstrates scalar return)
print("\n[Query 3] Constant score (scalar return value):")
result3 = (
    Q.nodes()
    .from_layers(L["work"])
    .compute("constant_score", alias="score")
    .limit(3)
    .execute(network)
)

df3 = result3.to_pandas()
print(df3.to_string(index=False))

# ============================================================================
# Step 4: Combine custom and built-in operators
# ============================================================================

print("\n[4] Combining custom and built-in operators...")
print("-" * 80)

result4 = (
    Q.nodes()
    .from_layers(L["social"])
    .compute("layer_activity", alias="activity")
    .compute("betweenness_centrality", alias="betweenness")
    .order_by("betweenness", desc=True)
    .limit(5)
    .execute(network)
)

df4 = result4.to_pandas()
print("Top 5 nodes by betweenness with activity scores:")
print(df4.to_string(index=False))

# ============================================================================
# Step 5: Introspection
# ============================================================================

print("\n[5] Operator introspection...")
print("-" * 80)

all_ops = list_operators()
print(f"Total registered operators: {len(all_ops)}")

print("\nCustom operators (category: analytics):")
for name, op in all_ops.items():
    if op.category == "analytics":
        print(f"  - {name}")

print("\n[COMPLETE] Custom DSL operators example finished successfully!")
print("=" * 80)
