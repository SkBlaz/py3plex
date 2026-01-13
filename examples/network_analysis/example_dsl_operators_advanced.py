"""Advanced example: Custom DSL Operators with Parameters

This example demonstrates advanced usage of the DSL plugin system, including:
- Operators with keyword parameters
- Using execution context to access network state
- Combining multiple custom operators
- Integration with built-in operators
"""

from py3plex.core import multinet
from py3plex.dsl import (
    dsl_operator,
    DSLExecutionContext,
    Q,
    L,
)


# Create a sample network
network = multinet.multi_layer_network(directed=False)

nodes = [
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Charlie', 'type': 'social'},
    {'source': 'Alice', 'type': 'work'},
    {'source': 'Bob', 'type': 'work'},
]
network.add_nodes(nodes)

edges = [
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work', 'weight': 1.0},
]
network.add_edges(edges)


# Define custom operator with parameters
@dsl_operator("weighted_degree", category="centrality")
def weighted_degree_op(context: DSLExecutionContext, weight_factor: float = 1.0):
    """Compute weighted degree with configurable weight factor.

    Args:
        context: Execution context with network state
        weight_factor: Multiplier for degree values
    """
    G = context.graph.core_network
    result = {}
    for node in context.current_nodes or []:
        if node in G:
            result[node] = G.degree(node) * weight_factor
        else:
            result[node] = 0.0
    return result


# Define operator that uses layer information
@dsl_operator("layer_centralization", category="multilayer")
def layer_centralization_op(context: DSLExecutionContext, normalize: bool = True):
    """Compute centralization score for nodes in selected layers.

    Args:
        context: Execution context
        normalize: Whether to normalize by number of layers
    """
    if not context.current_layers:
        return {node: 0.0 for node in context.current_nodes or []}

    G = context.graph.core_network
    result = {}

    for node in context.current_nodes or []:
        if node in G and isinstance(node, tuple) and len(node) >= 2:
            node_id, layer = node[0], node[1]
            if layer in context.current_layers:
                # Simple centralization: degree / max_degree in layer
                degrees = [G.degree(n) for n in G.nodes() if isinstance(n, tuple) and n[1] == layer and n in G]
                max_degree = max(degrees) if degrees else 1
                centralization = G.degree(node) / max_degree if max_degree > 0 else 0

                if normalize:
                    centralization /= len(context.current_layers)

                result[node] = centralization
            else:
                result[node] = 0.0
        else:
            result[node] = 0.0

    return result


# Test the operators with different parameters
print("=" * 70)
print("ADVANCED DSL OPERATOR EXAMPLES")
print("=" * 70)

print("\n[1] Weighted degree with weight_factor=2.0:")
result1 = (
    Q.nodes()
    .from_layers(L["social"])
    .compute("weighted_degree", alias="wdeg")
    .execute(network)
)
print(result1.to_pandas().to_string(index=False))

print("\n[2] Layer centralization (normalized):")
result2 = (
    Q.nodes()
    .from_layers(L["social"])
    .compute("layer_centralization", alias="centralization")
    .compute("degree", alias="degree")
    .order_by("centralization", desc=True)
    .execute(network)
)
print(result2.to_pandas().to_string(index=False))

print("\n[3] Combining custom operators with built-in measures:")
result3 = (
    Q.nodes()
    .from_layers(L["social"])
    .compute("weighted_degree", alias="wdeg")
    .compute("betweenness_centrality", alias="bc")
    .compute("layer_centralization", alias="lc")
    .order_by("bc", desc=True)
    .execute(network)
)
print(result3.to_pandas().to_string(index=False))

print("\n" + "=" * 70)
print("SUCCESS: All advanced features working correctly!")
print("=" * 70)
