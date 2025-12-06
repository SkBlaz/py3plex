"""Example: Custom DSL Operators via Plugin System.

This example demonstrates how to extend the py3plex DSL with custom operators
using the @dsl_operator decorator.
"""

from py3plex.core import multinet
from py3plex.dsl import (
    dsl_operator,
    DSLExecutionContext,
    Q,
    list_operators,
    describe_operator,
)


# Create a sample multilayer network
def create_sample_network():
    """Create a sample network for demonstration."""
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes in multiple layers
    nodes = [
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
        {'source': 'David', 'type': 'social'},
        {'source': 'Alice', 'type': 'work'},
        {'source': 'Bob', 'type': 'work'},
        {'source': 'Eve', 'type': 'work'},
    ]
    network.add_nodes(nodes)
    
    # Add edges
    edges = [
        # Social layer
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Charlie', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        # Work layer
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Bob', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Alice', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work'},
    ]
    network.add_edges(edges)
    
    return network


# Example 1: Simple custom operator
@dsl_operator("layer_versatility", description="Measure node versatility across layers", category="multilayer")
def layer_versatility_op(context: DSLExecutionContext) -> dict:
    """
    Compute a simple 'versatility' score: number of layers a node appears in.
    
    Args:
        context: Execution context with graph and node information
    
    Returns:
        Dictionary mapping nodes to versatility scores
    """
    # Count layers for each node
    versatility = {}
    
    for node in context.current_nodes:
        if isinstance(node, tuple) and len(node) >= 2:
            node_id = node[0]
            if node_id not in versatility:
                versatility[node_id] = set()
            versatility[node_id].add(node[1])  # Add layer
    
    # Convert to count
    return {node: len(versatility.get(node[0] if isinstance(node, tuple) else node, set())) 
            for node in context.current_nodes}


# Example 2: Operator with parameters
@dsl_operator("weighted_score", description="Compute weighted score", category="custom")
def weighted_score_op(context: DSLExecutionContext, weight: float = 1.0) -> dict:
    """
    Apply a weight to node degrees.
    
    Args:
        context: Execution context
        weight: Multiplicative weight factor
    
    Returns:
        Dictionary mapping nodes to weighted scores
    """
    G = context.graph.core_network
    scores = {}
    
    for node in context.current_nodes:
        if node in G:
            degree = G.degree(node)
            scores[node] = degree * weight
        else:
            scores[node] = 0.0
    
    return scores


# Example 3: Operator that uses layer information
@dsl_operator("layer_resilience", description="Compute layer resilience score", category="dynamics")
def layer_resilience_op(context: DSLExecutionContext, alpha: float = 0.1) -> dict:
    """
    Toy resilience metric: combination of degree and layer count.
    
    Args:
        context: Execution context
        alpha: Weight parameter for combining metrics
    
    Returns:
        Dictionary mapping nodes to resilience scores
    """
    G = context.graph.core_network
    scores = {}
    
    # Get layer counts
    layer_counts = {}
    for node in context.current_nodes:
        if isinstance(node, tuple) and len(node) >= 2:
            node_id = node[0]
            if node_id not in layer_counts:
                layer_counts[node_id] = set()
            layer_counts[node_id].add(node[1])
    
    # Compute resilience: degree + alpha * layer_count
    for node in context.current_nodes:
        if node in G:
            degree = G.degree(node)
            node_id = node[0] if isinstance(node, tuple) else node
            layer_count = len(layer_counts.get(node_id, set()))
            scores[node] = degree + alpha * layer_count
        else:
            scores[node] = 0.0
    
    return scores


def main():
    """Run examples."""
    print("=" * 70)
    print("Custom DSL Operators Example")
    print("=" * 70)
    
    # Create network
    network = create_sample_network()
    print(f"\nCreated network with {len(list(network.get_nodes()))} nodes")
    
    # Example 1: Use layer_versatility operator
    print("\n" + "-" * 70)
    print("Example 1: Layer Versatility")
    print("-" * 70)
    
    query1 = (
        Q.nodes()
        .compute("layer_versatility", alias="versatility")
        .compute("degree", alias="degree")
        .order_by("versatility", desc=True)
    )
    
    result1 = query1.execute(network)
    df1 = result1.to_pandas()
    print(df1.head(10))
    
    # Example 2: Use weighted_score with parameter
    print("\n" + "-" * 70)
    print("Example 2: Weighted Score (weight=2.5)")
    print("-" * 70)
    
    # Note: Parameter passing to custom operators in builder API 
    # would require additional builder support. For now, operators
    # use default parameters.
    query2 = (
        Q.nodes()
        .compute("weighted_score", alias="weighted")
        .compute("degree", alias="degree")
        .order_by("weighted", desc=True)
        .limit(5)
    )
    
    result2 = query2.execute(network)
    df2 = result2.to_pandas()
    print(df2)
    
    # Example 3: Use layer_resilience
    print("\n" + "-" * 70)
    print("Example 3: Layer Resilience")
    print("-" * 70)
    
    query3 = (
        Q.nodes()
        .compute("layer_resilience", alias="resilience")
        .order_by("resilience", desc=True)
        .limit(5)
    )
    
    result3 = query3.execute(network)
    df3 = result3.to_pandas()
    print(df3)
    
    # Example 4: Introspection - list all operators
    print("\n" + "-" * 70)
    print("Example 4: Introspection - List Custom Operators")
    print("-" * 70)
    
    ops = list_operators(category="multilayer")
    print(f"\nOperators in 'multilayer' category:")
    for name, op in ops.items():
        print(f"  - {name}: {op.description}")
    
    ops = list_operators(category="dynamics")
    print(f"\nOperators in 'dynamics' category:")
    for name, op in ops.items():
        print(f"  - {name}: {op.description}")
    
    # Example 5: Describe a specific operator
    print("\n" + "-" * 70)
    print("Example 5: Describe Operator")
    print("-" * 70)
    
    info = describe_operator("layer_versatility")
    if info:
        print(f"\nOperator: {info['name']}")
        print(f"Description: {info['description']}")
        print(f"Category: {info['category']}")
        print(f"Function: {info['function']}")
    
    # Example 6: Mix custom and built-in operators
    print("\n" + "-" * 70)
    print("Example 6: Mix Custom and Built-in Operators")
    print("-" * 70)
    
    query6 = (
        Q.nodes()
        .compute("layer_versatility", alias="versatility")
        .compute("betweenness_centrality", alias="betweenness")
        .compute("degree", alias="degree")
        .order_by("betweenness", desc=True)
        .limit(5)
    )
    
    result6 = query6.execute(network)
    df6 = result6.to_pandas()
    print(df6)
    
    print("\n" + "=" * 70)
    print("Examples completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
