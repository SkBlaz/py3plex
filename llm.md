# py3plex LLM Documentation

> This file provides comprehensive documentation about py3plex, optimized for LLM agents and AI assistants.

## Project Overview

py3plex is a Python library (version 0.96) for analyzing and visualizing multilayer and multiplex networks. It provides:

**Core Features:**
- Native support for multilayer network structures
- SQL-like DSL for intuitive network queries
- Dplyr-style chainable graph operations API (filter, select, mutate, arrange, group_by, summarise)
- Sklearn-style pipeline API for composable workflows
- Fluent method chaining for network construction
- Pythonic interface (__len__, __iter__, __contains__, properties)
- Visualization capabilities for complex networks
- Community detection and centrality measures
- Integration with NetworkX

**Additional Features:**
- **CLI Tool:** Full-featured command-line interface (`py3plex --help`)
- **Built-in Datasets:** Similar to scikit-learn (`load_aarhus_cs()`, `make_random_multilayer()`)
- **Plugin System:** Extensible architecture for custom algorithms
- **Config-Driven Workflows:** YAML/JSON workflow definitions
- **R Interoperability:** Use py3plex from R via reticulate
- **Performance Profiling:** Built-in timing and benchmarking utilities
- **File Linting:** Validate graph data files before loading
- **Multiple I/O Formats:** EdgeList, GraphML, GML, JSON, CSV, Apache Arrow

**Key Ergonomics Features:**
- **DSL Queries:** `net.execute_query('SELECT nodes WHERE degree > 5')`
- **Dplyr Pipes:** `nodes(net).filter(lambda n: n["degree"] > 5).mutate(...).to_pandas()`
- **Method Chaining:** `net.add_nodes([...]).add_edges([...])`
- **Pipelines:** `Pipeline([("load", LoadStep(...)), ("stats", ComputeStats())])`
- **CLI:** `py3plex create --nodes 100 --layers 3 --output network.edgelist`

**Repository:** https://github.com/SkBlaz/py3plex  
**Documentation:** https://skblaz.github.io/py3plex/

---

## SQL-like DSL for Multilayer Networks

The Domain-Specific Language (DSL) in py3plex allows querying and analyzing multilayer networks using SQL-like syntax. This is a key feature that makes network analysis intuitive and accessible.

### DSL Syntax Overview

```
SELECT target WHERE conditions COMPUTE measures
```

**Components:**
- **SELECT**: Specify what to select (`nodes` or `edges`)
- **WHERE**: Filter results based on conditions (optional)
- **COMPUTE**: Calculate network measures for filtered results (optional)

### Core Functions

```python
from py3plex.dsl import (
    execute_query,       # Execute DSL query on network
    format_result,       # Format results as readable string
    select_nodes_by_layer,      # Convenience: get nodes in layer
    select_high_degree_nodes,   # Convenience: get high-degree nodes
    compute_centrality_for_layer,  # Convenience: compute centrality
    DSLSyntaxError,      # Exception for syntax errors
    DSLExecutionError,   # Exception for execution errors
)
```

### Supported Operations

**Comparison Operators:**
- `=` : Equal to
- `!=` : Not equal to
- `>` : Greater than
- `<` : Less than
- `>=` : Greater than or equal
- `<=` : Less than or equal

**Logical Operators:**
- `AND` : Both conditions must be true
- `OR` : Either condition must be true
- `NOT` : Negates the condition

**Computable Measures:**
- `degree` : Node degree
- `degree_centrality` : Normalized degree centrality
- `betweenness_centrality` : Betweenness centrality
- `closeness_centrality` : Closeness centrality
- `eigenvector_centrality` : Eigenvector centrality
- `pagerank` : PageRank score
- `clustering` : Clustering coefficient

---

## DSL Examples with Outputs

### Example 1: Basic Setup and Network Creation

```python
from py3plex.core import multinet
from py3plex.dsl import execute_query, format_result

# Create a multilayer network
network = multinet.multi_layer_network(directed=False)

# Add nodes to multiple layers
nodes = [
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
    {'source': 'Charlie', 'type': 'social'},
    {'source': 'David', 'type': 'social'},
    {'source': 'Eve', 'type': 'social'},
    {'source': 'Alice', 'type': 'work'},
    {'source': 'Bob', 'type': 'work'},
    {'source': 'Charlie', 'type': 'work'},
    {'source': 'Alice', 'type': 'transport'},
    {'source': 'Bob', 'type': 'transport'},
    {'source': 'David', 'type': 'transport'},
    {'source': 'Eve', 'type': 'transport'},
]
network.add_nodes(nodes)

# Add edges within layers
edges = [
    # Social layer
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Bob', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'Charlie', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'David', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
    # Work layer
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'Alice', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'Bob', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work'},
    # Transport layer
    {'source': 'Alice', 'target': 'Bob', 'source_type': 'transport', 'target_type': 'transport'},
    {'source': 'Bob', 'target': 'David', 'source_type': 'transport', 'target_type': 'transport'},
    {'source': 'Bob', 'target': 'Eve', 'source_type': 'transport', 'target_type': 'transport'},
    {'source': 'David', 'target': 'Eve', 'source_type': 'transport', 'target_type': 'transport'},
]
network.add_edges(edges)

print(f"Network: {network}")
print(f"Total nodes: {len(list(network.get_nodes()))}")
print(f"Total edges: {len(list(network.get_edges()))}")
```

**Output:**
```
Network: <multi_layer_network: type=multilayer, directed=False, nodes=12, edges=13, layers=3>
Total nodes: 12
Total edges: 13
```

---

### Example 2: Select Nodes by Layer

```python
result = execute_query(network, 'SELECT nodes WHERE layer="social"')
print(format_result(result))
```

**Output:**
```
Query: SELECT nodes WHERE layer="social"
Target: nodes
Count: 5

Nodes (showing 5 of 5):
  ('Alice', 'social')
  ('Bob', 'social')
  ('Charlie', 'social')
  ('David', 'social')
  ('Eve', 'social')
```

---

### Example 3: Filter Nodes by Degree

```python
result = execute_query(network, 'SELECT nodes WHERE degree > 2')
print(format_result(result))
```

**Output:**
```
Query: SELECT nodes WHERE degree > 2
Target: nodes
Count: 4

Nodes (showing 4 of 4):
  ('Bob', 'social')
  ('Charlie', 'social')
  ('David', 'social')
  ('Bob', 'transport')
```

---

### Example 4: Combine Layer and Degree Filters (AND)

```python
result = execute_query(network, 'SELECT nodes WHERE layer="transport" AND degree > 1')
print(format_result(result))
```

**Output:**
```
Query: SELECT nodes WHERE layer="transport" AND degree > 1
Target: nodes
Count: 3

Nodes (showing 3 of 3):
  ('Bob', 'transport')
  ('David', 'transport')
  ('Eve', 'transport')
```

---

### Example 5: Multiple Layer Selection (OR)

```python
result = execute_query(network, 'SELECT nodes WHERE layer="social" OR layer="work"')
print(format_result(result))
```

**Output:**
```
Query: SELECT nodes WHERE layer="social" OR layer="work"
Target: nodes
Count: 8

Nodes (showing 8 of 8):
  ('Alice', 'social')
  ('Bob', 'social')
  ('Charlie', 'social')
  ('David', 'social')
  ('Eve', 'social')
  ('Alice', 'work')
  ('Bob', 'work')
  ('Charlie', 'work')
```

---

### Example 6: Compute Betweenness Centrality

```python
result = execute_query(network, 'SELECT nodes WHERE layer="social" COMPUTE betweenness_centrality')
print(format_result(result))
```

**Output:**
```
Query: SELECT nodes WHERE layer="social" COMPUTE betweenness_centrality
Target: nodes
Count: 5

Nodes (showing 5 of 5):
  ('Alice', 'social')
  ('Bob', 'social')
  ('Charlie', 'social')
  ('David', 'social')
  ('Eve', 'social')

Computed measures:
  betweenness_centrality:
    ('David', 'social'): 0.5000
    ('Bob', 'social'): 0.1667
    ('Charlie', 'social'): 0.1667
    ('Eve', 'social'): 0.0000
    ('Alice', 'social'): 0.0000
```

---

### Example 7: Multiple Measures at Once

```python
result = execute_query(network, 'SELECT nodes WHERE degree > 2 COMPUTE degree_centrality closeness_centrality')
print(format_result(result))
```

**Output:**
```
Query: SELECT nodes WHERE degree > 2 COMPUTE degree_centrality closeness_centrality
Target: nodes
Count: 4

Nodes (showing 4 of 4):
  ('Bob', 'social')
  ('Charlie', 'social')
  ('David', 'social')
  ('Bob', 'transport')

Computed measures:
  degree_centrality:
    ('Bob', 'social'): 0.6667
    ('Charlie', 'social'): 0.6667
    ('David', 'social'): 0.6667
    ('Bob', 'transport'): 0.0000
  closeness_centrality:
    ('Bob', 'social'): 0.6667
    ('Charlie', 'social'): 0.6667
    ('David', 'social'): 0.6667
    ('Bob', 'transport'): 0.0000
```

---

### Example 8: Degree Range Filtering

```python
result = execute_query(network, 'SELECT nodes WHERE degree >= 2 AND degree <= 4')
print(format_result(result))
```

**Output:**
```
Query: SELECT nodes WHERE degree >= 2 AND degree <= 4
Target: nodes
Count: 10

Nodes (showing 10 of 10):
  ('Alice', 'social')
  ('Bob', 'social')
  ('Charlie', 'social')
  ('David', 'social')
  ('Alice', 'work')
  ('Bob', 'work')
  ('Charlie', 'work')
  ('Bob', 'transport')
  ('David', 'transport')
  ('Eve', 'transport')
```

---

### Example 9: Select All Nodes (No Filter)

```python
result = execute_query(network, 'SELECT nodes')
print(f"Total nodes: {result['count']}")
print(f"Nodes: {result['nodes']}")
```

**Output:**
```
Total nodes: 12
Nodes: [('Alice', 'social'), ('Bob', 'social'), ('Charlie', 'social'), ('David', 'social'), ('Eve', 'social'), ('Alice', 'work'), ('Bob', 'work'), ('Charlie', 'work'), ('Alice', 'transport'), ('Bob', 'transport'), ('David', 'transport'), ('Eve', 'transport')]
```

---

### Example 10: Using NOT Operator

```python
result = execute_query(network, 'SELECT nodes WHERE NOT layer="social"')
print(format_result(result))
```

**Output:**
```
Query: SELECT nodes WHERE NOT layer="social"
Target: nodes
Count: 7

Nodes (showing 7 of 7):
  ('Alice', 'work')
  ('Bob', 'work')
  ('Charlie', 'work')
  ('Alice', 'transport')
  ('Bob', 'transport')
  ('David', 'transport')
  ('Eve', 'transport')
```

---

### Example 11: Convenience Functions

```python
from py3plex.dsl import select_nodes_by_layer, select_high_degree_nodes, compute_centrality_for_layer

# Get all nodes in a specific layer
social_nodes = select_nodes_by_layer(network, 'social')
print(f"Nodes in 'social' layer: {len(social_nodes)}")
print(f"Nodes: {social_nodes}")

# Get high-degree nodes (degree > 3)
high_degree = select_high_degree_nodes(network, min_degree=3)
print(f"Nodes with degree > 3: {len(high_degree)}")

# Compute centrality for a layer
centrality = compute_centrality_for_layer(network, 'transport', 'degree_centrality')
print("Degree centrality for 'transport' layer:")
for node, value in sorted(centrality.items(), key=lambda x: x[1], reverse=True):
    print(f"  {node}: {value:.4f}")
```

**Output:**
```
Nodes in 'social' layer: 5
Nodes: [('Alice', 'social'), ('Bob', 'social'), ('Charlie', 'social'), ('David', 'social'), ('Eve', 'social')]
Nodes with degree > 3: 0
Degree centrality for 'transport' layer:
  ('Bob', 'transport'): 1.0000
  ('David', 'transport'): 0.6667
  ('Eve', 'transport'): 0.6667
  ('Alice', 'transport'): 0.3333
```

---

### Example 12: Compute PageRank

```python
result = execute_query(network, 'SELECT nodes COMPUTE pagerank')
print(format_result(result, limit=10))
```

**Output:**
```
Query: SELECT nodes COMPUTE pagerank
Target: nodes
Count: 12

Nodes (showing 10 of 12):
  ('Alice', 'social')
  ('Bob', 'social')
  ('Charlie', 'social')
  ('David', 'social')
  ('Eve', 'social')
  ('Alice', 'work')
  ('Bob', 'work')
  ('Charlie', 'work')
  ('Alice', 'transport')
  ('Bob', 'transport')
  ... and 2 more

Computed measures:
  pagerank:
    ('Bob', 'social'): 0.1186
    ('Charlie', 'social'): 0.1186
    ('David', 'social'): 0.1186
    ('Bob', 'transport'): 0.1099
    ('Alice', 'social'): 0.0955
    ('Eve', 'social'): 0.0730
    ('David', 'transport'): 0.0706
    ('Eve', 'transport'): 0.0706
    ('Alice', 'work'): 0.0540
    ('Bob', 'work'): 0.0540
```

---

### Example 13: Compute Clustering Coefficient

```python
result = execute_query(network, 'SELECT nodes WHERE layer="social" COMPUTE clustering')
print(format_result(result))
```

**Output:**
```
Query: SELECT nodes WHERE layer="social" COMPUTE clustering
Target: nodes
Count: 5

Nodes (showing 5 of 5):
  ('Alice', 'social')
  ('Bob', 'social')
  ('Charlie', 'social')
  ('David', 'social')
  ('Eve', 'social')

Computed measures:
  clustering:
    ('Alice', 'social'): 1.0000
    ('Charlie', 'social'): 0.6667
    ('Bob', 'social'): 0.3333
    ('David', 'social'): 0.3333
    ('Eve', 'social'): 0.0000
```

---

### Example 14: Error Handling

```python
from py3plex.dsl import DSLSyntaxError, DSLExecutionError

try:
    result = execute_query(network, 'INVALID QUERY')
except DSLSyntaxError as e:
    print(f"Syntax error: {e}")

try:
    result = execute_query(network, 'SELECT edges')  # Edge queries limited
except DSLExecutionError as e:
    print(f"Execution error: {e}")
```

**Output:**
```
Syntax error: Query must start with SELECT
```

---

### Example 15: Accessing Result Data Programmatically

```python
result = execute_query(network, 'SELECT nodes WHERE layer="social" COMPUTE betweenness_centrality')

# Access query metadata
print(f"Query: {result['query']}")
print(f"Target: {result['target']}")
print(f"Count: {result['count']}")

# Access selected nodes
for node in result['nodes']:
    print(f"Node: {node}")

# Access computed measures
if 'computed' in result:
    for measure, values in result['computed'].items():
        print(f"\n{measure}:")
        for node, value in sorted(values.items(), key=lambda x: x[1], reverse=True):
            print(f"  {node}: {value:.4f}")
```

**Output:**
```
Query: SELECT nodes WHERE layer="social" COMPUTE betweenness_centrality
Target: nodes
Count: 5
Node: ('Alice', 'social')
Node: ('Bob', 'social')
Node: ('Charlie', 'social')
Node: ('David', 'social')
Node: ('Eve', 'social')

betweenness_centrality:
  ('David', 'social'): 0.5000
  ('Bob', 'social'): 0.1667
  ('Charlie', 'social'): 0.1667
  ('Alice', 'social'): 0.0000
  ('Eve', 'social'): 0.0000
```

---

### Example 16: Hub Identification Workflow

```python
# Find hub nodes in each layer
layers = ['social', 'work', 'transport']

for layer in layers:
    result = execute_query(network, f'SELECT nodes WHERE layer="{layer}" AND degree >= 2')
    print(f"\nHubs in {layer} layer (degree >= 2): {result['count']}")
    for node in result['nodes']:
        degree = network.core_network.degree(node)
        print(f"  {node}: degree={degree}")
```

**Output:**
```
Hubs in social layer (degree >= 2): 4
  ('Alice', 'social'): degree=2
  ('Bob', 'social'): degree=3
  ('Charlie', 'social'): degree=3
  ('David', 'social'): degree=3

Hubs in work layer (degree >= 2): 3
  ('Alice', 'work'): degree=2
  ('Bob', 'work'): degree=2
  ('Charlie', 'work'): degree=2

Hubs in transport layer (degree >= 2): 3
  ('Bob', 'transport'): degree=3
  ('David', 'transport'): degree=2
  ('Eve', 'transport'): degree=2
```

---

### Example 17: Layer Comparison Analysis

```python
layers = ['social', 'work', 'transport']

print("Layer Comparison - Average Degree:")
for layer in layers:
    result = execute_query(network, f'SELECT nodes WHERE layer="{layer}" COMPUTE degree')
    degrees = result['computed']['degree']
    avg_degree = sum(degrees.values()) / len(degrees) if degrees else 0
    max_degree = max(degrees.values()) if degrees else 0
    print(f"  {layer}: avg={avg_degree:.2f}, max={max_degree}")
```

**Output:**
```
Layer Comparison - Average Degree:
  social: avg=2.40, max=3
  work: avg=2.00, max=2
  transport: avg=1.75, max=3
```

---

### Example 18: Transportation Network Analysis

```python
# Create transportation network
transport_net = multinet.multi_layer_network(directed=False)

# Stations
stations = ['A', 'B', 'C', 'D', 'E', 'F']
for station in stations:
    for layer in ['bus', 'metro', 'train']:
        transport_net.add_nodes([{'source': station, 'type': layer}])

# Connections
edges = [
    # Bus (dense)
    {'source': 'A', 'target': 'B', 'source_type': 'bus', 'target_type': 'bus'},
    {'source': 'B', 'target': 'C', 'source_type': 'bus', 'target_type': 'bus'},
    {'source': 'C', 'target': 'D', 'source_type': 'bus', 'target_type': 'bus'},
    {'source': 'D', 'target': 'E', 'source_type': 'bus', 'target_type': 'bus'},
    {'source': 'E', 'target': 'F', 'source_type': 'bus', 'target_type': 'bus'},
    # Metro (medium)
    {'source': 'A', 'target': 'C', 'source_type': 'metro', 'target_type': 'metro'},
    {'source': 'C', 'target': 'E', 'source_type': 'metro', 'target_type': 'metro'},
    # Train (sparse)
    {'source': 'A', 'target': 'F', 'source_type': 'train', 'target_type': 'train'},
]
transport_net.add_edges(edges)

# Compare layers
for layer in ['bus', 'metro', 'train']:
    result = execute_query(transport_net, f'SELECT nodes WHERE layer="{layer}" COMPUTE betweenness_centrality')
    print(f"\n{layer.upper()} layer centrality:")
    centralities = result['computed']['betweenness_centrality']
    for node, value in sorted(centralities.items(), key=lambda x: x[1], reverse=True)[:3]:
        print(f"  {node}: {value:.4f}")
```

**Output:**
```
BUS layer centrality:
  ('C', 'bus'): 0.6000
  ('D', 'bus'): 0.6000
  ('B', 'bus'): 0.4000

METRO layer centrality:
  ('C', 'metro'): 1.0000
  ('A', 'metro'): 0.0000
  ('E', 'metro'): 0.0000

TRAIN layer centrality:
  ('A', 'train'): 0.0000
  ('F', 'train'): 0.0000
  ('B', 'train'): 0.0000
```

---

## Result Dictionary Structure

The `execute_query` function returns a dictionary with the following structure:

```python
{
    'query': str,           # Original query string
    'target': str,          # 'nodes' or 'edges'
    'nodes': list,          # List of (node_id, layer) tuples (if target='nodes')
    'edges': list,          # List of edge tuples (if target='edges')
    'count': int,           # Number of items returned
    'computed': {           # Present only if COMPUTE was used
        'measure_name': {   # Dictionary mapping nodes to values
            (node_id, layer): float,
            ...
        },
        ...
    }
}
```

---

## Best Practices

1. **Filter by layer first** - Reduces computation for large networks
2. **Use convenience functions** - For common operations like `select_nodes_by_layer()`
3. **Cache computed measures** - Avoid recomputing expensive centrality measures
4. **Handle errors gracefully** - Wrap queries in try-except blocks
5. **Use `format_result()`** - For debugging and human-readable output

---

## Current Limitations

- Edge queries have limited support
- Complex nested conditions require multiple queries
- No aggregation functions (SUM, AVG, etc.)
- Measures are computed using NetworkX algorithms

---

## Dplyr-Style Chainable Graph Operations API

py3plex provides a dplyr-inspired API for fluent, method-chaining operations on nodes and edges. This allows functional-style data manipulation similar to R's dplyr or Python's pandas.

### Core Components

```python
from py3plex.graph_ops import (
    nodes,           # Create NodeFrame from network
    edges,           # Create EdgeFrame from network
    NodeFrame,       # Chainable view over nodes
    EdgeFrame,       # Chainable view over edges
    GroupedNodeFrame,  # For group_by + summarise
    GroupedEdgeFrame,  # For group_by + summarise on edges
)
```

### Supported Verbs (dplyr Mapping)

| dplyr          | py3plex              | Description                          |
|----------------|----------------------|--------------------------------------|
| `filter()`     | `.filter(pred)`      | Keep rows matching predicate         |
| `select()`     | `.select(*cols)`     | Keep only specified columns          |
| `mutate()`     | `.mutate(**funcs)`   | Add/modify columns                   |
| `arrange()`    | `.arrange(key)`      | Sort by column or function           |
| `head()`       | `.head(n)`           | Keep first n rows                    |
| `group_by()`   | `.group_by(*cols)`   | Group for aggregation                |
| `summarise()`  | `.summarise(**aggs)` | Compute group summaries              |

### Example 1: Basic Node Operations

```python
from py3plex.core import multinet
from py3plex.graph_ops import nodes
import numpy as np

# Create network
net = multinet.multi_layer_network(directed=False)
net.add_edges([
    {'source': 'A', 'target': 'B', 'source_type': 'ppi', 'target_type': 'ppi'},
    {'source': 'B', 'target': 'C', 'source_type': 'ppi', 'target_type': 'ppi'},
    {'source': 'A', 'target': 'C', 'source_type': 'ppi', 'target_type': 'ppi'},
    {'source': 'C', 'target': 'D', 'source_type': 'ppi', 'target_type': 'ppi'},
])

# Chainable operations
df = (
    nodes(net, layers=["ppi"])
    .filter(lambda n: n["degree"] > 1)
    .mutate(normalized_degree=lambda n: n["degree"] / 4)  # Normalize by total node count
    .arrange("degree", reverse=True)
    .head(3)
    .to_pandas()
)

print(df)
```

**Output:**
```
   id layer  degree  normalized_degree
0   C   ppi       3               0.75
1   A   ppi       2               0.50
2   B   ppi       2               0.50
```

---

### Example 2: Group By and Summarise

```python
from py3plex.graph_ops import nodes
import numpy as np

# Create multi-layer network
net = multinet.multi_layer_network(directed=False)
net.add_edges([
    {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'A', 'target': 'B', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'B', 'target': 'C', 'source_type': 'work', 'target_type': 'work'},
    {'source': 'C', 'target': 'D', 'source_type': 'work', 'target_type': 'work'},
])

# Group by layer and compute statistics
df = (
    nodes(net)
    .group_by("layer")
    .summarise(
        avg_degree=("degree", np.mean),
        max_degree=("degree", max),
        n_nodes=("id", len),
    )
    .to_pandas()
)

print(df)
```

**Output:**
```
    layer  avg_degree  max_degree  n_nodes
0  social    1.333333           2        3
1    work    1.500000           3        4
```

---

### Example 3: Edge Operations

```python
from py3plex.graph_ops import edges

# Filter and analyze edges
df_edges = (
    edges(net, layers=["work"])
    .filter(lambda e: e.get("weight", 1) >= 1)
    .select("source", "target", "source_layer")
    .head(10)
    .to_pandas()
)

print(df_edges)
```

**Output:**
```
  source target source_layer
0      A      B         work
1      B      C         work
2      C      D         work
```

---

### Example 4: Filter with Expression Strings

```python
# Use filter_expr for simple string-based filtering
df = (
    nodes(net)
    .filter_expr("degree > 1 and layer == 'work'")
    .to_pandas()
)
```

---

### Example 5: Extract Subgraph from Selection

```python
# Create a subgraph containing only high-degree nodes
subgraph = (
    nodes(net)
    .filter(lambda n: n["degree"] > 2)
    .to_subgraph()
)

print(f"Subgraph has {subgraph.node_count} nodes and {subgraph.edge_count} edges")
```

---

## Method Chaining for Network Construction

py3plex supports fluent method chaining for network construction:

```python
from py3plex.core import multinet

# Fluent network construction
net = (
    multinet.multi_layer_network(directed=False)
    .add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer2'},
    ])
    .add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer2'},
    ])
    .add_nodes([
        {'source': 'D', 'type': 'layer2'},
    ])
    .add_edges([
        {'source': 'C', 'target': 'D', 'source_type': 'layer2', 'target_type': 'layer2'},
    ])
)

print(net)
# <multi_layer_network: type=multilayer, directed=False, nodes=4, edges=3, layers=2>
```

---

## Pythonic Interface Features

py3plex's `multi_layer_network` class implements Python's special methods for intuitive usage:

### Dunder Methods

```python
net = multinet.multi_layer_network()
net.add_nodes([{'source': 'A', 'type': 'layer1'}])

# __len__: Get node count
len(net)  # Returns 1

# __bool__: Check if network is non-empty
if net:
    print("Network has nodes")

# __contains__: Check for node existence
('A', 'layer1') in net  # Returns True
('B', 'layer1') in net  # Returns False

# __iter__: Iterate over nodes
for node in net:
    print(node)  # Prints ('A', 'layer1')
```

### Property Accessors

```python
net.node_count   # Number of nodes
net.edge_count   # Number of edges
net.layer_count  # Number of unique layers
net.layers       # Sorted list of layer names
net.is_empty     # True if no nodes
```

### Factory Methods

```python
# Create from edges directly
net = multinet.multi_layer_network.from_edges([
    {'source': 'A', 'target': 'B', 'source_type': 'l1', 'target_type': 'l1'}
])

# Create from NetworkX graph
import networkx as nx
G = nx.Graph()
G.add_edge(('A', 'layer1'), ('B', 'layer1'))
net = multinet.multi_layer_network.from_networkx(G)
```

---

## Sklearn-Style Pipeline API

py3plex provides a scikit-learn style pipeline for composable network analysis workflows:

### Core Components

```python
from py3plex.pipeline import (
    Pipeline,        # Main pipeline class
    PipelineStep,    # Base class for custom steps
    LoadStep,        # Load network from file/generator
    AggregateLayers, # Aggregate across layers
    LeidenMultilayer,# Community detection
    LouvainCommunity,# Louvain community detection
    ComputeStats,    # Compute network statistics
    FilterNodes,     # Filter by degree/list
    SaveNetwork,     # Save to file
)
```

### Pipeline Example

```python
from py3plex.pipeline import Pipeline, LoadStep, ComputeStats, FilterNodes

# Define analysis pipeline
pipe = Pipeline([
    ("load", LoadStep(generator='random_er', num_nodes=100, num_layers=3, edge_prob=0.1)),
    ("filter", FilterNodes(min_degree=2)),
    ("stats", ComputeStats(include_layer_stats=True)),
])

# Execute pipeline
result = pipe.run()
print(result)
```

**Output:**
```
{'nodes': 87, 'edges': 312, 'density': 0.083, 'layers': 3, 
 'layer_densities': {'layer_0': 0.092, 'layer_1': 0.078, 'layer_2': 0.081}}
```

### Custom Pipeline Steps

```python
from py3plex.pipeline import PipelineStep

class ComputeCentrality(PipelineStep):
    def __init__(self, measure='betweenness'):
        self.measure = measure
    
    def transform(self, network):
        import networkx as nx
        if self.measure == 'betweenness':
            centrality = nx.betweenness_centrality(network.core_network)
        return {'network': network, 'centrality': centrality}

# Use in pipeline
pipe = Pipeline([
    ("load", LoadStep(path="network.graphml")),
    ("centrality", ComputeCentrality(measure='betweenness')),
])
```

---

## Config-Driven Workflows

For reproducible research, py3plex supports YAML-based workflow configuration:

```python
from py3plex.workflows import WorkflowConfig, run_workflow

# Define workflow in YAML
config_yaml = """
name: my_analysis
steps:
  - name: load
    type: load
    params:
      path: network.graphml
      input_type: graphml
  - name: community
    type: community
    params:
      algorithm: louvain
  - name: stats
    type: stats
output:
  format: json
  path: results.json
"""

# Run workflow
result = run_workflow(config_yaml)
```

---

## First-Class DSL Method on Network

The DSL can be accessed directly as a method on the network object:

```python
net = multinet.multi_layer_network()
# ... add nodes and edges ...

# Execute query directly on network
result = net.execute_query('SELECT nodes WHERE layer="social" AND degree > 2')

# With MATCH syntax (Cypher-like pattern matching, also supported by DSL)
result = net.execute_query('MATCH (a:layer1)-[r]->(b:layer1) RETURN a, b')
```

---

## Command-Line Interface (CLI)

py3plex provides a comprehensive CLI tool for multilayer network analysis. Run `py3plex --help` to see all available commands.

### Available Commands

| Command | Description |
|---------|-------------|
| `help` | Show detailed help information |
| `check` | Lint and validate graph data files |
| `create` | Create a new multilayer network |
| `load` | Load and inspect a multilayer network |
| `community` | Detect communities in the network |
| `centrality` | Compute node centrality measures |
| `stats` | Compute multilayer network statistics |
| `visualize` | Visualize the multilayer network |
| `aggregate` | Aggregate multilayer network into single layer |
| `convert` | Convert network between different formats |
| `selftest` | Run self-test to verify installation |
| `quickstart` | Interactive demo with example graph |
| `run-config` | Run workflow from YAML/JSON configuration |

### CLI Examples

```bash
# Quick start - interactive demo
py3plex quickstart

# Create a random multilayer network
py3plex create --nodes 100 --layers 3 --type random --probability 0.1 --output network.edgelist

# Load and inspect network
py3plex load network.edgelist --info --stats

# Detect communities
py3plex community network.edgelist --algorithm louvain --output communities.json

# Compute centrality measures
py3plex centrality network.edgelist --measure betweenness --top 20

# Visualize the network
py3plex visualize network.edgelist --output network.png --layout multilayer

# Convert between formats
py3plex convert network.edgelist --output network.graphml

# Validate a data file
py3plex check network.csv --strict
```

---

## Built-in Datasets

py3plex provides built-in datasets similar to scikit-learn, making it easy to get started with examples and testing.

### Available Functions

```python
from py3plex.datasets import (
    # Bundled datasets
    load_aarhus_cs,           # Aarhus CS department social network (61 nodes, 5 layers)
    load_synthetic_multilayer, # Synthetic multilayer network (50 nodes, 3 layers)
    
    # Synthetic generators
    make_random_multilayer,   # Random multilayer Erdős-Rényi
    make_random_multiplex,    # Random multiplex Erdős-Rényi
    make_clique_multiplex,    # Multiplex with clique structure
    make_social_network,      # Synthetic social network
    
    # Utilities
    list_datasets,            # List all available datasets
    get_data_dir,             # Get path to data directory
)
```

### Example Usage

```python
from py3plex.datasets import load_aarhus_cs, make_random_multilayer, list_datasets

# List available datasets
for name, desc in list_datasets():
    print(f"{name}: {desc}")

# Load bundled dataset
network = load_aarhus_cs()
print(f"Nodes: {len(list(network.get_nodes()))}")
print(f"Layers: {network.get_layers()}")

# Generate synthetic network
net = make_random_multilayer(n_nodes=100, n_layers=3, p=0.1, random_state=42)
```

**Output:**
```
aarhus_cs: Social network of Aarhus CS department (61 nodes, 5 layers)
synthetic_multilayer: Synthetic multilayer network (50 nodes, 3 layers)
Nodes: 305
Layers: ['coauthor', 'facebook', 'leisure', 'lunch', 'work']
```

---

## Plugin System

py3plex supports a plugin architecture for extending functionality with custom algorithms.

### Plugin Types

```python
from py3plex.plugins import (
    BasePlugin,        # Abstract base for all plugins
    CentralityPlugin,  # For custom centrality measures
    CommunityPlugin,   # For custom community detection
    LayoutPlugin,      # For custom layout algorithms
    MetricPlugin,      # For custom network metrics
    PluginRegistry,    # Registry for managing plugins
    discover_plugins,  # Auto-discover installed plugins
)
```

### Creating a Custom Plugin

```python
from py3plex.plugins import CentralityPlugin

class MyCustomCentrality(CentralityPlugin):
    @property
    def name(self) -> str:
        return "my_custom_centrality"
    
    @property
    def description(self) -> str:
        return "A custom centrality measure"
    
    def compute(self, network, **kwargs):
        # Implement your centrality algorithm
        centrality = {}
        for node in network.get_nodes():
            centrality[node] = network.core_network.degree(node)
        return centrality

# Register and use
from py3plex.plugins import PluginRegistry
registry = PluginRegistry()
registry.register(MyCustomCentrality())

# Use the plugin
plugin = registry.get("my_custom_centrality")
result = plugin.compute(network)
```

---

## I/O API

py3plex provides a flexible I/O system with format detection and a registry for custom formats.

### Supported Formats

| Format | Extension | Read | Write |
|--------|-----------|------|-------|
| EdgeList | `.edgelist`, `.txt` | ✓ | ✓ |
| Multi-EdgeList | `.multiedgelist` | ✓ | ✓ |
| GraphML | `.graphml` | ✓ | ✓ |
| GML | `.gml` | ✓ | ✓ |
| JSON | `.json` | ✓ | ✓ |
| CSV | `.csv` | ✓ | ✓ |
| Apache Arrow | `.arrow`, `.parquet` | ✓ | ✓ |

### I/O Functions

```python
from py3plex.io.api import (
    register_reader,    # Register custom reader
    register_writer,    # Register custom writer
)
from py3plex.io.schema import MultiLayerGraph  # Schema for graph data
```

### Loading and Saving Networks

```python
from py3plex.core import multinet

# Load from file
network = multinet.multi_layer_network().load_network(
    "network.edgelist",
    input_type="multiedgelist",
    directed=False
)

# Save to file (via NetworkX)
import networkx as nx
nx.write_graphml(network.core_network, "network.graphml")
```

---

## Profiling Utilities

py3plex includes built-in performance profiling tools for optimization and benchmarking.

### Available Functions

```python
from py3plex.profiling import (
    profile_performance,  # Decorator for timing functions
    timed_section,        # Context manager for timing code blocks
    benchmark,            # Decorator for benchmarking
    get_monitor,          # Get global performance monitor
)
```

### Example Usage

```python
from py3plex.profiling import profile_performance, timed_section, get_monitor

@profile_performance
def compute_centrality(network):
    # ... computation
    pass

# Time a specific code block
with timed_section("community_detection"):
    communities = detect_communities(network)

# Get performance report
monitor = get_monitor()
print(monitor.get_report())
```

**Output:**
```
Performance Report
================================================================================
Function                                   Calls   Total(s)     Avg(ms)     Min(ms)     Max(ms)
--------------------------------------------------------------------------------
compute_centrality                            10      1.234      123.4       100.2       150.3
```

---

## Exception Hierarchy

py3plex provides domain-specific exceptions for better error handling:

```python
from py3plex.exceptions import (
    # Base exception
    Py3plexException,           # Base for all py3plex exceptions
    
    # Network construction
    NetworkConstructionError,   # Network construction failures
    InvalidLayerError,          # Invalid layer specification
    InvalidNodeError,           # Invalid node specification
    InvalidEdgeError,           # Invalid edge specification
    
    # Parsing and I/O
    ParsingError,               # Input data parsing failures
    Py3plexIOError,             # File I/O failures
    Py3plexFormatError,         # Invalid format errors
    
    # Algorithm errors
    AlgorithmError,             # Algorithm execution failures
    CommunityDetectionError,    # Community detection failures
    CentralityComputationError, # Centrality computation failures
    DecompositionError,         # Network decomposition failures
    EmbeddingError,             # Embedding generation failures
    
    # Other errors
    VisualizationError,         # Visualization failures
    ConversionError,            # Format conversion failures
    IncompatibleNetworkError,   # Incompatible network format
    Py3plexMatrixError,         # Matrix operation failures
    Py3plexLayoutError,         # Layout computation failures
    ExternalToolError,          # External tool execution failures
)
```

### Example Usage

```python
from py3plex.exceptions import ParsingError, InvalidLayerError

try:
    network.load_network("invalid_file.csv", input_type="csv")
except ParsingError as e:
    print(f"Failed to parse file: {e}")

try:
    result = execute_query(network, 'SELECT nodes WHERE layer="nonexistent"')
except InvalidLayerError as e:
    print(f"Layer not found: {e}")
```

---

## Configuration

py3plex provides centralized configuration for visualization and layout settings:

```python
from py3plex import config

# Visualization settings
config.DEFAULT_NODE_SIZE = 15
config.DEFAULT_EDGE_ALPHA = 0.5
config.DEFAULT_LAYER_ALPHA = 0.15

# Color palettes
config.COLOR_PALETTES  # Dict of available palettes: 'rainbow', 'pastel', 'vibrant', 'colorblind_safe', 'wong'

# Multilayer geometry
config.MULTILAYER_LAYER_OFFSET = 1.5  # Spacing between layers
config.MULTILAYER_CIRCLE_SIZE = 1.05  # Layer background radius
```

---

## Linter and Validation

py3plex includes tools for validating graph data files before loading.

### File Linter

```python
from py3plex.linter import GraphFileLinter, LintIssue

# Lint a data file
linter = GraphFileLinter("network.csv")
issues = linter.lint()

for issue in issues:
    print(issue)
    # [WARNING] Line 5: Duplicate edge detected
    #   → Suggestion: Remove duplicate edges or use weighted edges
```

### Input Validation

```python
from py3plex.validation import (
    validate_file_exists,
    validate_csv_columns,
)

# Validate file exists
validate_file_exists("network.csv")

# Validate CSV has required columns
validate_csv_columns(
    "network.csv",
    required_columns=["source", "target", "source_type", "target_type"],
    optional_columns=["weight"]
)
```

---

## R Interoperability

py3plex can be used from R via the reticulate package:

```r
library(reticulate)
library(igraph)

py3plex <- import("py3plex")
r_interop <- import("py3plex.wrappers.r_interop")

# Create network
net <- py3plex$multi_layer_network()
net$add_nodes(list(
  list(source='Alice', type='social'),
  list(source='Bob', type='social')
))

# Convert to igraph for R analysis
g <- r_interop$to_igraph_for_r(net, mode='union')

# Use R igraph functions
deg <- degree(g)
between <- betweenness(g)
```

### R Interop Functions

| Function | Description |
|----------|-------------|
| `to_igraph_for_r()` | Convert py3plex network to igraph |
| `export_edgelist()` | Export edges as R data frame structure |
| `export_nodelist()` | Export nodes as R data frame structure |
| `export_adjacency()` | Export adjacency matrix |
| `get_network_stats()` | Get network statistics |
| `get_layer_names()` | Get layer names |

---

## Version Information

```python
import py3plex

print(py3plex.__version__)      # Current version: "0.96"
print(py3plex.__api_version__)  # API version: "0.96"
```

---

## File Locations

- **Core Modules:**
  - `py3plex/core/multinet.py` - Main multi_layer_network class
  - `py3plex/dsl.py` - SQL-like DSL implementation
  - `py3plex/graph_ops.py` - Dplyr-style chainable API
  - `py3plex/pipeline.py` - Sklearn-style pipeline
  - `py3plex/workflows.py` - Config-driven workflows

- **Utilities:**
  - `py3plex/cli.py` - Command-line interface
  - `py3plex/config.py` - Centralized configuration
  - `py3plex/exceptions.py` - Exception hierarchy
  - `py3plex/validation.py` - Input validation
  - `py3plex/linter.py` - File linting
  - `py3plex/profiling.py` - Performance profiling
  - `py3plex/logging_config.py` - Logging configuration

- **I/O and Data:**
  - `py3plex/io/` - I/O API and format handlers
  - `py3plex/datasets/` - Built-in datasets and generators

- **Extensibility:**
  - `py3plex/plugins/` - Plugin system

- **Interoperability:**
  - `py3plex/wrappers/r_interop.py` - R interoperability

- **Algorithms:**
  - `py3plex/algorithms/` - Network algorithms (community detection, centrality, etc.)

- **Visualization:**
  - `py3plex/visualization/` - Visualization tools and layouts

- **Documentation:**
  - `docfiles/user_guide/dsl.rst` - DSL documentation
  - `docfiles/r_interop.rst` - R interoperability guide

- **Examples:**
  - `examples/getting_started/` - Getting started tutorials
  - `examples/network_analysis/` - Network analysis examples
  - `examples/pipelines/` - Pipeline examples
  - `examples/workflows/` - Workflow examples
  - `examples/visualization/` - Visualization examples

- **Tests:**
  - `tests/test_dsl.py` - DSL tests
  - `tests/test_graph_ops.py` - Graph operations tests
  - `tests/test_pipeline.py` - Pipeline tests
  - `tests/test_ergonomics.py` - Ergonomics tests
  - `tests/test_cli.py` - CLI tests
  - `tests/test_plugin_system.py` - Plugin system tests
  - `tests/test_workflows.py` - Workflow tests
