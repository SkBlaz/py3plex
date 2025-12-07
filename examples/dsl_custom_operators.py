"""Example: Custom DSL Operators

This example demonstrates how to create custom DSL operators using the
@dsl_operator decorator.
"""

from py3plex.core import multinet
from py3plex.dsl import (
    dsl_operator,
    DSLExecutionContext,
    Q,
    list_operators,
    describe_operator,
)


# Example 1: Simple custom operator
@dsl_operator("layer_resilience", description="Compute layer resilience score", category="dynamics")
def layer_resilience_op(context: DSLExecutionContext, alpha: float = 0.1) -> float:
    """Compute a toy resilience score for the currently selected layers.
    
    Args:
        context: Execution context with graph, layers, nodes
        alpha: Resilience factor
        
    Returns:
        Resilience score
    """
    # Access the current layer selection
    layers = context.current_layers or []
    nodes = context.current_nodes or []
    
    # Simple computation: resilience = num_layers * num_nodes * alpha
    return len(layers) * len(nodes) * alpha


# Example 2: Operator that accesses the graph
@dsl_operator("edge_density", description="Compute edge density", category="statistics")
def edge_density_op(context: DSLExecutionContext) -> float:
    """Compute edge density for the current node selection.
    
    Args:
        context: Execution context
        
    Returns:
        Edge density (0 to 1)
    """
    if not hasattr(context.graph, 'core_network'):
        return 0.0
    
    G = context.graph.core_network
    nodes = context.current_nodes or []
    
    if len(nodes) < 2:
        return 0.0
    
    # Count edges between selected nodes
    edge_count = 0
    for node in nodes:
        if node in G:
            for neighbor in G.neighbors(node):
                if neighbor in nodes:
                    edge_count += 1
    
    # Avoid double counting for undirected graphs
    if not G.is_directed():
        edge_count //= 2
    
    # Maximum possible edges
    max_edges = len(nodes) * (len(nodes) - 1)
    if not G.is_directed():
        max_edges //= 2
    
    return edge_count / max_edges if max_edges > 0 else 0.0


# Example 3: Operator with multiple parameters
@dsl_operator("weighted_score", description="Compute weighted node score", category="scoring")
def weighted_score_op(context: DSLExecutionContext, weight: float = 1.0, bias: float = 0.0) -> dict:
    """Compute a weighted score for each node.
    
    Args:
        context: Execution context
        weight: Weight multiplier
        bias: Bias term to add
        
    Returns:
        Dict mapping nodes to scores
    """
    if not hasattr(context.graph, 'core_network'):
        return {}
    
    G = context.graph.core_network
    nodes = context.current_nodes or []
    
    # Simple scoring: score = degree * weight + bias
    scores = {}
    for node in nodes:
        if node in G:
            degree = G.degree(node)
            scores[node] = degree * weight + bias
        else:
            scores[node] = bias
    
    return scores


def main():
    """Demonstrate custom DSL operators."""
    
    # Create a sample multilayer network
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes in two layers
    nodes = [
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'D', 'type': 'layer1'},
        {'source': 'A', 'type': 'layer2'},
        {'source': 'B', 'type': 'layer2'},
        {'source': 'C', 'type': 'layer2'},
    ]
    network.add_nodes(nodes)
    
    # Add edges
    edges = [
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'C', 'target': 'D', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'A', 'target': 'B', 'source_type': 'layer2', 'target_type': 'layer2'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer2', 'target_type': 'layer2'},
    ]
    network.add_edges(edges)
    
    print("=" * 70)
    print("Custom DSL Operators Example")
    print("=" * 70)
    
    # List all operators (including custom ones)
    print("\n1. Listing all registered operators:")
    print("-" * 70)
    all_ops = list_operators()
    print(f"Total operators registered: {len(all_ops)}")
    
    # Show custom operators
    custom_ops = list_operators(category="dynamics")
    print(f"\nDynamics operators: {', '.join(custom_ops.keys())}")
    
    stats_ops = list_operators(category="statistics")
    print(f"Statistics operators: {', '.join(stats_ops.keys())}")
    
    scoring_ops = list_operators(category="scoring")
    print(f"Scoring operators: {', '.join(scoring_ops.keys())}")
    
    # Describe an operator
    print("\n2. Describing an operator:")
    print("-" * 70)
    info = describe_operator("layer_resilience")
    if info:
        print(f"Name: {info['name']}")
        print(f"Description: {info['description']}")
        print(f"Category: {info['category']}")
        print(f"Parameters: {info['parameters']}")
    
    # Use custom operators in DSL queries
    print("\n3. Using custom operators in DSL queries:")
    print("-" * 70)
    
    # Note: The operator integration with COMPUTE is demonstrated here
    # The actual query execution would need the full DSL parser integration
    # For now, we show the operators are registered and accessible
    
    print("\nCustom operators are now available for use in DSL scripts!")
    print("\nExample DSL usage (conceptual):")
    print("  SELECT nodes")
    print("  FROM LAYER('layer1')")
    print("  COMPUTE layer_resilience(alpha=0.2)")
    print("  ORDER BY layer_resilience DESC")
    
    print("\n" + "=" * 70)
    print("Example completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
