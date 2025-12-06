# DSL Plugin System Documentation

## Overview

The py3plex DSL now supports a **pluggable operator system** that allows users to define custom operators in Python and use them directly in DSL scripts alongside built-in operators.

## Quick Start

### 1. Define a Custom Operator

Use the `@dsl_operator` decorator to register a Python function as a DSL operator:

```python
from py3plex.dsl import dsl_operator, DSLExecutionContext

@dsl_operator("layer_resilience", category="dynamics")
def layer_resilience_op(context: DSLExecutionContext, alpha: float = 0.1):
    """Compute resilience score for nodes across layers."""
    G = context.graph.core_network
    scores = {}
    
    for node in context.current_nodes:
        if node in G:
            degree = G.degree(node)
            # Add custom logic here
            scores[node] = degree * (1 + alpha)
        else:
            scores[node] = 0.0
    
    return scores
```

### 2. Use the Operator in DSL Queries

#### Builder API

```python
from py3plex.dsl import Q

# Use your custom operator
query = (
    Q.nodes()
    .from_layers(L["social"] + L["work"])
    .compute("layer_resilience", alias="resilience")
    .order_by("resilience", desc=True)
    .limit(10)
)

result = query.execute(network)
df = result.to_pandas()
```

#### String DSL (future enhancement)

```sql
SELECT nodes
FROM LAYER("social") + LAYER("work")
COMPUTE layer_resilience AS resilience
ORDER BY resilience DESC
LIMIT 10
```

## Core Concepts

### DSLExecutionContext

Every operator receives a `DSLExecutionContext` as its first argument, which provides:

- **`context.graph`**: The multilayer network being queried
- **`context.current_nodes`**: List of nodes selected by the query (None = all nodes)
- **`context.current_layers`**: List of active layers (None = all layers)
- **`context.params`**: Global query parameters (e.g., random seed)
- **`context.target`**: Query target type ("nodes" or "edges")

### Operator Registration

The `@dsl_operator` decorator supports several options:

```python
@dsl_operator(
    name="my_operator",           # Operator name (defaults to function name)
    description="...",            # Description for documentation
    category="centrality",        # Category for grouping
    overwrite=False               # Allow overwriting existing operators
)
def my_operator(context: DSLExecutionContext, param1: float = 1.0) -> dict:
    """Compute something."""
    return {node: value for node in context.current_nodes}
```

### Return Values

Operators should return a dictionary mapping nodes/edges to computed values:

```python
{
    ('Alice', 'social'): 0.75,
    ('Bob', 'social'): 0.82,
    ...
}
```

If you return a scalar value, it will be broadcast to all nodes/edges.

## Examples

### Example 1: Simple Constant Score

```python
@dsl_operator("constant_score")
def constant_score(context: DSLExecutionContext, value: float = 5.0) -> dict:
    """Return constant score for all nodes."""
    return {node: value for node in context.current_nodes}
```

### Example 2: Node Versatility (Layer Participation)

```python
@dsl_operator("layer_versatility", category="multilayer")
def layer_versatility_op(context: DSLExecutionContext) -> dict:
    """Count how many layers each node appears in."""
    versatility = {}
    
    for node in context.current_nodes:
        if isinstance(node, tuple) and len(node) >= 2:
            node_id = node[0]
            if node_id not in versatility:
                versatility[node_id] = set()
            versatility[node_id].add(node[1])  # Add layer
    
    # Convert to count
    return {
        node: len(versatility.get(node[0] if isinstance(node, tuple) else node, set())) 
        for node in context.current_nodes
    }
```

### Example 3: Weighted Score

```python
@dsl_operator("weighted_score", category="custom")
def weighted_score_op(context: DSLExecutionContext, weight: float = 1.0) -> dict:
    """Apply weight to node degrees."""
    G = context.graph.core_network
    
    return {
        node: G.degree(node) * weight if node in G else 0.0
        for node in context.current_nodes
    }
```

### Example 4: Layer-Aware Resilience

```python
@dsl_operator("layer_resilience", category="dynamics")
def layer_resilience_op(context: DSLExecutionContext, alpha: float = 0.1) -> dict:
    """Compute resilience: degree + alpha * layer_count."""
    G = context.graph.core_network
    
    # Count layers per node
    layer_counts = {}
    for node in context.current_nodes:
        if isinstance(node, tuple) and len(node) >= 2:
            node_id = node[0]
            if node_id not in layer_counts:
                layer_counts[node_id] = set()
            layer_counts[node_id].add(node[1])
    
    # Compute resilience
    scores = {}
    for node in context.current_nodes:
        if node in G:
            degree = G.degree(node)
            node_id = node[0] if isinstance(node, tuple) else node
            layer_count = len(layer_counts.get(node_id, set()))
            scores[node] = degree + alpha * layer_count
        else:
            scores[node] = 0.0
    
    return scores
```

## Introspection API

The plugin system provides utilities for discovering and inspecting operators:

### List All Operators

```python
from py3plex.dsl import list_operators

# List all operators
ops = list_operators()
for name, op in ops.items():
    print(f"{name}: {op.description}")

# Filter by category
centrality_ops = list_operators(category="centrality")
```

### Describe an Operator

```python
from py3plex.dsl import describe_operator

info = describe_operator("layer_resilience")
print(f"Name: {info['name']}")
print(f"Description: {info['description']}")
print(f"Category: {info['category']}")
print(f"Function: {info['function']}")
```

### Check if Operator Exists

```python
from py3plex.dsl import get_operator

op = get_operator("my_operator")
if op is not None:
    print(f"Operator found: {op.description}")
```

## Direct Registration (Without Decorator)

You can also register operators directly:

```python
from py3plex.dsl import register_operator, DSLExecutionContext

def my_function(context: DSLExecutionContext) -> dict:
    return {node: 1.0 for node in context.current_nodes}

register_operator(
    "my_operator",
    my_function,
    description="My custom operator",
    category="custom"
)
```

## Backward Compatibility

The plugin system maintains full backward compatibility with existing DSL features:

- **Measure Registry**: Existing measures (degree, betweenness, etc.) continue to work
- **Fallback Mechanism**: If an operator is not found in the operator registry, the system falls back to the measure registry
- **Unified Error Messages**: Unknown operators show suggestions from both registries

### Migrated Built-in Operators

Some built-in measures have been migrated to the new operator system as examples:

- `multiplex_degree` - Node degree computation
- `multiplex_betweenness` - Betweenness centrality
- `multiplex_pagerank` - PageRank centrality

These demonstrate how measure functions can be adapted to the operator system.

## Best Practices

### 1. Use Type Hints

```python
@dsl_operator("my_op")
def my_op(context: DSLExecutionContext, param: float = 1.0) -> dict:
    ...
```

### 2. Provide Docstrings

```python
@dsl_operator("my_op")
def my_op(context: DSLExecutionContext) -> dict:
    """
    Compute a custom metric for nodes.
    
    Args:
        context: Execution context with graph and node information
    
    Returns:
        Dictionary mapping nodes to computed values
    """
    ...
```

### 3. Handle Edge Cases

```python
@dsl_operator("safe_op")
def safe_op(context: DSLExecutionContext) -> dict:
    G = context.graph.core_network
    scores = {}
    
    for node in context.current_nodes:
        if node in G:
            # Compute for valid nodes
            scores[node] = compute_something(node)
        else:
            # Fallback for missing nodes
            scores[node] = 0.0
    
    return scores
```

### 4. Use Categories for Organization

Organize operators into logical categories:

- **`centrality`**: Centrality measures
- **`dynamics`**: Dynamic processes (epidemics, diffusion, etc.)
- **`multilayer`**: Multilayer-specific metrics
- **`custom`**: User-defined operators
- **`io`**: Import/export operations

### 5. Return Consistent Types

Always return a dictionary mapping nodes to values, even for scalar results:

```python
# Good
return {node: 42.0 for node in context.current_nodes}

# Also works (auto-converted)
return 42.0  # Applied to all nodes
```

## Advanced Usage

### Accessing Layer Information

```python
@dsl_operator("layer_aware_metric")
def layer_aware_metric(context: DSLExecutionContext) -> dict:
    """Use layer information in computation."""
    scores = {}
    
    for node in context.current_nodes:
        if isinstance(node, tuple) and len(node) >= 2:
            node_id, layer = node[0], node[1]
            # Use both node ID and layer
            scores[node] = compute_for_layer(node_id, layer)
    
    return scores
```

### Using Graph Attributes

```python
@dsl_operator("attribute_based_metric")
def attribute_based_metric(context: DSLExecutionContext) -> dict:
    """Use node attributes in computation."""
    G = context.graph.core_network
    scores = {}
    
    for node in context.current_nodes:
        if node in G:
            # Access node attributes
            attrs = G.nodes[node]
            weight = attrs.get('weight', 1.0)
            scores[node] = compute_with_weight(node, weight)
    
    return scores
```

### Combining Multiple Metrics

```python
@dsl_operator("combined_metric")
def combined_metric(context: DSLExecutionContext, alpha: float = 0.5) -> dict:
    """Combine degree and clustering coefficient."""
    G = context.graph.core_network
    import networkx as nx
    
    degrees = dict(G.degree())
    clustering = nx.clustering(G)
    
    return {
        node: alpha * degrees.get(node, 0) + (1 - alpha) * clustering.get(node, 0)
        for node in context.current_nodes
    }
```

## Testing Custom Operators

Use pytest to test your custom operators:

```python
import pytest
from py3plex.core import multinet
from py3plex.dsl import dsl_operator, Q, DSLExecutionContext

@pytest.fixture
def sample_network():
    net = multinet.multi_layer_network()
    # ... add nodes and edges ...
    return net

def test_my_operator(sample_network):
    @dsl_operator("test_op")
    def test_op(context: DSLExecutionContext) -> dict:
        return {node: 42.0 for node in context.current_nodes}
    
    query = Q.nodes().compute("test_op", alias="score")
    result = query.execute(sample_network)
    
    df = result.to_pandas()
    assert all(df["score"] == 42.0)
```

## Troubleshooting

### "Operator already registered" Error

If you see this error, either:
1. Use a different name
2. Set `overwrite=True` in the decorator
3. Unregister the old operator first (useful in tests)

```python
from py3plex.dsl import operator_registry

operator_registry.unregister("my_op")
```

### Unknown Operator Error

Check available operators:

```python
from py3plex.dsl import list_operators

print(list_operators())
```

### Type Errors in Context

Ensure you're accessing context fields correctly:

```python
# Check if nodes exist
if context.current_nodes:
    for node in context.current_nodes:
        ...

# Check if layers are specified
if context.current_layers:
    print(f"Active layers: {context.current_layers}")
```

## See Also

- [DSL v2 Documentation](../docfiles/user_guide/dsl.rst)
- [Example Script](../examples/network_analysis/example_dsl_custom_operators.py)
- [Plugin System Tests](../tests/test_dsl_plugin_operators.py)
- [DSL Builder API](../py3plex/dsl/builder.py)

## Future Enhancements

Planned improvements to the plugin system:

1. **Parameter Passing**: Support passing parameters to operators in DSL scripts
2. **String DSL Integration**: Use custom operators in string-based DSL queries
3. **Operator Composition**: Chain operators together
4. **Async Operators**: Support for asynchronous computation
5. **Operator Validation**: Type checking and parameter validation
6. **Auto-documentation**: Generate docs from operator docstrings
