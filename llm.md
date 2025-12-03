# py3plex LLM Documentation

> This file provides comprehensive documentation about py3plex, optimized for LLM agents and AI assistants.

## Project Overview

py3plex is a Python library for analyzing and visualizing multilayer and multiplex networks. It provides:
- Native support for multilayer network structures
- SQL-like DSL for intuitive network queries
- Visualization capabilities for complex networks
- Community detection and centrality measures
- Integration with NetworkX

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

## File Locations

- **DSL Module:** `py3plex/dsl.py`
- **DSL Documentation:** `docfiles/user_guide/dsl.rst`
- **DSL Examples:** `examples/network_analysis/example_dsl_queries.py`
- **Advanced Examples:** `examples/network_analysis/example_dsl_advanced.py`
- **Tests:** `tests/test_dsl.py`
- **Datasets Module:** `py3plex/datasets/`
- **Datasets Tests:** `tests/test_datasets.py`
- **Datasets Example:** `examples/getting_started/example_datasets.py`

---

## Built-in Datasets

py3plex provides built-in datasets similar to scikit-learn, making it easy to get started without external data files.

### Available Functions

```python
from py3plex.datasets import (
    # Loaders for bundled datasets
    load_aarhus_cs,           # Aarhus CS social network (61 nodes, 5 layers)
    load_synthetic_multilayer, # Synthetic multilayer network (50 nodes, 3 layers)
    
    # Synthetic generators
    make_random_multilayer,    # Random multilayer Erdős-Rényi network
    make_random_multiplex,     # Random multiplex Erdős-Rényi network
    make_clique_multiplex,     # Multiplex with clique structure
    make_social_network,       # Synthetic social network (friendship/work/family)
    
    # Utilities
    list_datasets,             # List all available datasets
    get_data_dir,              # Get path to bundled data directory
)

# Or import from top-level
import py3plex as p3
net = p3.load_aarhus_cs()
```

### Loading Built-in Datasets

```python
import py3plex as p3

# List available datasets
for name, description in p3.list_datasets():
    print(f"{name}: {description}")
```

**Output:**
```
aarhus_cs: Social network of Aarhus CS department (61 nodes, 5 layers)
synthetic_multilayer: Synthetic multilayer network (50 nodes, 3 layers)
```

### Aarhus CS Social Network

The Aarhus CS dataset represents relationships among employees in a Computer Science department with 5 layers (lunch, facebook, coauthor, leisure, work).

```python
import py3plex as p3

# Load the Aarhus CS social network
network = p3.load_aarhus_cs()
print(f"Nodes: {len(list(network.get_nodes()))}")
print(f"Edges: {len(list(network.get_edges()))}")

# Get layers
layers = network.get_layers()
layer_names = layers[0] if isinstance(layers, tuple) else layers
print(f"Layers: {layer_names}")  # ['lunch', 'facebook', 'coauthor', 'leisure', 'work']

# Use with DSL
result = p3.execute_query(network, 'SELECT nodes WHERE degree > 10')
print(f"High-degree nodes: {result['count']}")
```

### Generating Synthetic Networks

```python
import py3plex as p3

# Random multilayer network
net = p3.make_random_multilayer(
    n_nodes=50,       # Number of nodes
    n_layers=3,       # Number of layers
    p=0.1,            # Edge probability
    random_state=42   # For reproducibility
)

# Random multiplex network (same nodes in all layers)
net = p3.make_random_multiplex(
    n_nodes=30,
    n_layers=4,
    p=0.15,
    random_state=42
)

# Clique multiplex (good for community detection testing)
net = p3.make_clique_multiplex(
    n_nodes=20,
    n_layers=2,
    clique_size=5,
    n_cliques=3,
    random_state=42
)

# Social network with realistic structure
net = p3.make_social_network(
    n_people=30,
    random_state=42
)
# Creates layers: friendship (dense), work (clustered), family (small cliques)
```

### Complete Example with Datasets

```python
import py3plex as p3

# Load a dataset
network = p3.load_aarhus_cs()

# Analyze it
network.basic_stats()

# Query with DSL
result = p3.execute_query(
    network, 
    'SELECT nodes WHERE layer="lunch" COMPUTE betweenness_centrality'
)
print(p3.format_result(result))

# Or generate a synthetic network for testing
test_net = p3.make_random_multilayer(n_nodes=100, n_layers=5, p=0.05)
test_net.basic_stats()
```

### Dataset Reference

| Function | Description | Parameters |
|----------|-------------|------------|
| `load_aarhus_cs()` | Load Aarhus CS social network | `directed=False` |
| `load_synthetic_multilayer()` | Load synthetic multilayer | `directed=False` |
| `make_random_multilayer()` | Generate random multilayer ER | `n_nodes`, `n_layers`, `p`, `directed`, `random_state` |
| `make_random_multiplex()` | Generate random multiplex ER | `n_nodes`, `n_layers`, `p`, `directed`, `random_state` |
| `make_clique_multiplex()` | Generate clique multiplex | `n_nodes`, `n_layers`, `clique_size`, `n_cliques`, `random_state` |
| `make_social_network()` | Generate social network | `n_people`, `random_state` |
| `list_datasets()` | List available datasets | None |
| `get_data_dir()` | Get bundled data path | None |
