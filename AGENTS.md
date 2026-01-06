# py3plex AI Agent Documentation

> This file provides comprehensive documentation about py3plex, optimized for AI agents and assistants.

## Table of Contents

1. [Project Overview](#project-overview)
2. [SQL-like DSL for Multilayer Networks](#sql-like-dsl-for-multilayer-networks)
3. [DSL Examples with Outputs](#dsl-examples-with-outputs)
4. [Result Dictionary Structure](#result-dictionary-structure)
5. [Best Practices](#best-practices)
6. [Current Limitations](#current-limitations)
7. [DSL v2: Modern Builder API](#dsl-v2-modern-builder-api-q-uq-l)
8. [Dplyr-Style Chainable Graph Operations API](#dplyr-style-chainable-graph-operations-api)
9. [Method Chaining for Network Construction](#method-chaining-for-network-construction)
10. [Pythonic Interface Features](#pythonic-interface-features)
11. [Sklearn-Style Pipeline API](#sklearn-style-pipeline-api)
12. [Config-Driven Workflows](#config-driven-workflows)
13. [First-Class DSL Method on Network](#first-class-dsl-method-on-network)
14. [Command-Line Interface (CLI)](#command-line-interface-cli)
15. [Built-in Datasets](#built-in-datasets)
16. [Plugin System](#plugin-system)
17. [I/O API](#io-api)
18. [Profiling Utilities](#profiling-utilities)
19. [Exception Hierarchy](#exception-hierarchy)
20. [Configuration](#configuration)
21. [Linter and Validation](#linter-and-validation)
22. [R Interoperability](#r-interoperability)
23. [Dynamics Simulations](#dynamics-simulations)
24. [Uncertainty Quantification](#uncertainty-quantification)
25. [Replayable Provenance and Query Replay](#replayable-provenance-and-query-replay)
26. [Temporal Networks](#temporal-networks)
27. [Null Models](#null-models)
28. [Probabilistic Community Detection](#probabilistic-community-detection)
29. [Community Queries (First-Class Communities)](#community-queries-first-class-communities)
30. [Semiring Algebra (S Builder): Paths, Closure, Fixed-Point](#semiring-algebra-s-builder-paths-closure-fixed-point)
31. [Version Information](#version-information)
32. [File Locations](#file-locations)

---

## Project Overview

py3plex is a Python library (version 1.1.0) for analyzing and visualizing multilayer and multiplex networks. It provides:

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
- **Dynamics Simulations:** SIS, SIR, SEIR, Random Walk and custom processes
- **Uncertainty Quantification:** First-class uncertainty support with confidence intervals
- **Temporal Networks:** Time-stamped edges, snapshots, and sliding windows
- **Null Models:** Configuration model, random graphs for statistical testing

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

**Legacy DSL Returns:** Dictionary format
**DSL v2 Returns:** QueryResult object (with backward-compatible dict export)

### Legacy DSL Result Structure

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
    },
    'meta': {               # Metadata (added in version 1.1.0)
        'provenance': {...}  # Query execution provenance (see below)
    }
}
```

### DSL v2 QueryResult Structure

```python
result = Q.nodes().compute("degree").execute(network)

# QueryResult attributes
result.target          # "nodes" or "edges"
result.items           # List of node/edge items
result.attributes      # Dict of computed attributes
result.meta            # Metadata dict including provenance
result.count           # Number of items (same as len(result))

# Export formats
df = result.to_pandas()       # pandas DataFrame
G = result.to_networkx()      # NetworkX graph
arrow = result.to_arrow()     # Apache Arrow table
dict_result = result.to_dict()  # Plain dictionary
```

### Query Provenance (Version 1.1.0+)

Every query execution now includes provenance metadata in `result.meta["provenance"]` or `result["meta"]["provenance"]` (legacy). This enables reproducibility, debugging, and performance analysis.

**Provenance Structure:**

```python
{
    "engine": "dsl_v2_executor",  # or "dsl_legacy", "graph_ops", "pipeline_step"
    "py3plex_version": "1.1.0",
    "timestamp_utc": "2026-01-05T04:05:42.336000+00:00",
    "network_fingerprint": {
        "node_count": 100,
        "edge_count": 250,
        "layer_count": 3,
        "layers": ["social", "work", "family"]
    },
    "network_version": None,  # Mutation counter if available
    "query": {
        "target": "nodes",
        "ast_hash": "a1b2c3d4e5f6g7h8",  # Stable hash of query AST
        "ast_summary": "SELECT nodes WHERE degree>5 COMPUTE betweenness",
        "params": {}  # Parameter bindings used
    },
    "randomness": {
        "seed": None,  # Base seed if randomness is used
        "n_samples": None,  # For uncertainty quantification
        "method": None  # Resampling method if used
    },
    "backend": {
        "graph_backend": "networkx",
        "algo_backends": [],  # Algorithm backends used
        "fast_path": False  # Whether fast path optimizations were used
    },
    "performance": {
        "bind_parameters": 0.1,  # milliseconds per stage
        "get_items": 2.5,
        "filter_layers": 1.3,
        "filter_where": 3.2,
        "compute": 45.6,
        "total_ms": 53.5  # Total execution time
    },
    "warnings": []  # List of warning messages
}
```

**Key Provenance Fields:**

- **engine**: Execution engine used
- **py3plex_version**: Version for compatibility tracking
- **timestamp_utc**: When query was executed (ISO8601)
- **network_fingerprint**: Network summary (counts, layers)
- **query.ast_hash**: Stable query hash (invariant across runs)
- **query.ast_summary**: Human-readable query summary
- **performance.timings_ms**: Timing breakdown by stage

**Accessing Provenance:**

```python
# DSL v2
result = Q.nodes().compute("degree").execute(network)
prov = result.meta["provenance"]
print(f"Query took {prov['performance']['total_ms']:.2f}ms")
print(f"AST hash: {prov['query']['ast_hash']}")
print(f"Network: {prov['network_fingerprint']['node_count']} nodes, {prov['network_fingerprint']['layer_count']} layers")

# Legacy DSL
result = execute_query(network, 'SELECT nodes WHERE degree > 5')
prov = result["meta"]["provenance"]
print(f"Engine: {prov['engine']}")
```

**Backward Compatibility:** Provenance is additive and doesn't break existing code. All QueryResult operations continue to work unchanged.

---

## Best Practices

1. **Filter by layer first** - Reduces computation for large networks
2. **Use convenience functions** - For common operations like `select_nodes_by_layer()`
3. **Cache computed measures** - Avoid recomputing expensive centrality measures
4. **Handle errors gracefully** - Wrap queries in try-except blocks
5. **Use `format_result()`** - For debugging and human-readable output

---

## Current Limitations

- Complex nested conditions require multiple queries
- Measures are computed using NetworkX algorithms
- Some advanced graph algorithms may have performance limitations on very large networks

**Note:** Previous limitations on edge queries and aggregation functions have been resolved. py3plex now supports:
- Full-featured edge queries with filtering on endpoint properties (src_degree, dst_degree)
- Comprehensive aggregation operators: mean, median, sum, std, var, min, max, quantile(p), count
- Aggregations work on both nodes and edges with per_layer() and per_layer_pair() grouping

---

## DSL v2: Modern Builder API (Q, UQ, L)

py3plex DSL v2 introduces a modern, Pythonic builder API for constructing queries with enhanced ergonomics and new features like uncertainty quantification, pattern matching, and dynamics.

### DSL v2 Core Components

```python
from py3plex.dsl import (
    Q,        # Main query builder
    UQ,       # Uncertainty quantification builder
    L,        # Layer expression builder
    Param,    # Parameter placeholder
    C,        # Compare networks builder
    N,        # Null models builder
    P,        # Path queries builder
    F,        # Field expressions
)
from py3plex.dynamics import D  # Dynamics simulations builder
```

### Example 1: Basic Query with Q Builder

```python
from py3plex.dsl import Q, L
from py3plex.core import multinet

# Create network
net = multinet.multi_layer_network(directed=False)
net.add_edges([
    {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'B', 'target': 'C', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'C', 'target': 'D', 'source_type': 'social', 'target_type': 'social'},
    {'source': 'A', 'target': 'B', 'source_type': 'work', 'target_type': 'work'},
])

# Query with builder API
result = (
    Q.nodes()
     .from_layers(L["social"] + L["work"])
     .where(degree__gt=1)
     .compute("betweenness_centrality", "degree_centrality")
     .order_by("betweenness_centrality", desc=True)
     .limit(5)
     .execute(net)
)

# Convert to pandas
df = result.to_pandas()
print(df)
```

**Output:**
```
  node  layer  degree  betweenness_centrality  degree_centrality
0    B  social       2                0.500000           0.666667
1    B   work       1                0.000000           0.500000
2    A  social       1                0.000000           0.333333
...
```

---

### Example 2: Uncertainty Quantification with UQ

The flagship feature of DSL v2 is first-class uncertainty support via the `UQ` builder and `.uq()` method:

```python
from py3plex.dsl import Q, UQ

# Query with uncertainty quantification
result = (
    Q.nodes()
     .from_layers(L["social"])
     .where(degree__gt=1)
     .uq(method="perturbation", n_samples=100, ci=0.95, seed=42)
     .compute("betweenness_centrality", "pagerank")
     .execute(net)
)

# Access uncertainty statistics
df = result.to_pandas(expand_uncertainty=True)
print(df[["node", "betweenness_centrality", "betweenness_centrality_std",
          "betweenness_centrality_ci95_low", "betweenness_centrality_ci95_high"]])
```

**Output:**
```
  node  betweenness_centrality  betweenness_centrality_std  ci95_low  ci95_high
0    B                0.500000                    0.021134  0.458820   0.541102
1    C                0.333333                    0.018051  0.297902   0.368934
...
```

---

### Example 3: Layer Algebra with L Builder

```python
from py3plex.dsl import L

# Layer expressions
all_social = L["facebook"] + L["twitter"] + L["linkedin"]
work_layers = L["email"] + L["slack"]
all_layers = all_social + work_layers

# Use in query
result = (
    Q.nodes()
     .from_layers(all_social)
     .where(degree__gt=5)
     .execute(net)
)
```

---

### Example 4: Per-Layer Grouping and Coverage

```python
# Group by layer and find cross-layer hubs
result = (
    Q.nodes()
     .where(degree__gt=3)
     .per_layer()
        .compute("betweenness_centrality")
        .top_k(20, "betweenness_centrality__mean")
     .end_grouping()
     .coverage(mode="at_least", k=2)  # Present in ≥2 layers
     .execute(net)
)

# Get summary by layer
summary_df = result.group_summary()
print(summary_df)
```

**Output:**
```
    layer  count  avg_betweenness_centrality
0  social     15                    0.234567
1    work     12                    0.198234
...
```

---

### Example 5: Enrichment with Explain

```python
# Enrich results with explanatory features
result = (
    Q.nodes()
     .where(degree__gt=5)
     .compute("betweenness_centrality")
     .explain(neighbors_top=5, include_community=True)
     .execute(net)
)

df = result.to_pandas(expand_explanations=True)
print(df[["node", "betweenness_centrality", "community_id", "top_neighbors"]])
```

**Output:**
```
  node  betweenness_centrality  community_id                     top_neighbors
0    B                0.500000            42  [{'id': 'A', 'weight': 2.3}, ...]
...
```

---

### Example 6: Network Comparison

```python
from py3plex.dsl import C

# Compare two networks
comparison = (
    C.compare("baseline", "treatment")
     .using("multiplex_jaccard")
     .by_layer()
     .execute({"baseline": net1, "treatment": net2})
)

print(f"Jaccard similarity: {comparison.similarity}")
print(f"Layer-wise: {comparison.by_layer}")
```

---

### Example 7: Null Models

```python
from py3plex.dsl import N

# Generate configuration model null models
null_models = (
    N.configuration()
     .samples(100)
     .seed(42)
     .preserve_layers(True)
     .execute(net)
)

# Use for statistical testing
observed_stat = compute_network_statistic(net)
null_distribution = [compute_network_statistic(nm) for nm in null_models]
p_value = sum(ns >= observed_stat for ns in null_distribution) / len(null_distribution)
```

---

### Example 8: Path Queries

```python
from py3plex.dsl import P

# Find shortest paths across layers
paths = (
    P.shortest("Alice", "Bob")
     .crossing_layers()
     .max_length(5)
     .execute(net)
)

for path in paths.paths:
    print(f"Path: {' -> '.join(path)}, Length: {len(path)-1}")
```

---

### Example 9: Pattern Matching (Cypher-like)

```python
from py3plex.dsl import PatternQueryBuilder

# Find triangles in social layer
pattern = (
    PatternQueryBuilder()
     .node("a", layer="social")
     .edge("a", "b")
     .edge("b", "c")
     .edge("c", "a")
     .return_nodes("a", "b", "c")
)

matches = pattern.execute(net)
for match in matches:
    print(f"Triangle: {match['a']} - {match['b']} - {match['c']}")
```

---

### Example 10: Aggregations and Statistical Operators

py3plex DSL v2 provides first-class support for aggregations with a rich set of statistical operators:

```python
from py3plex.dsl import Q, L

# Basic aggregations on nodes
result = (
    Q.nodes()
     .compute("degree", "betweenness_centrality")
     .summarize(
         total_nodes="count()",
         avg_degree="mean(degree)",
         median_degree="median(degree)",
         std_degree="std(degree)",
         q95_degree="quantile(degree, 0.95)",
         max_bc="max(betweenness_centrality)"
     )
     .execute(net)
)

# Per-layer aggregations
result = (
    Q.nodes()
     .compute("degree")
     .per_layer()
     .aggregate(
         node_count="count()",
         avg_degree="mean(degree)",
         median_degree="median(degree)",
         q25="quantile(degree, 0.25)",
         q75="quantile(degree, 0.75)"
     )
     .execute(net)
)

# Edge aggregations per layer pair
result = (
    Q.edges()
     .per_layer_pair()
     .aggregate(
         edge_count="count()",
         total_weight="sum(weight)",
         avg_weight="mean(weight)",
         median_weight="median(weight)",
         max_weight="max(weight)"
     )
     .execute(net)
)

# Convert to pandas for further analysis
df = result.to_pandas()
print(df)
```

**Supported aggregation functions:**
- `count()` / `n()`: Count of items in group
- `mean(attr)`: Arithmetic mean
- `median(attr)`: Median value
- `sum(attr)`: Sum of values
- `min(attr)` / `max(attr)`: Minimum/maximum values
- `std(attr)` / `var(attr)`: Standard deviation and variance
- `quantile(attr, p)`: p-th quantile (e.g., `quantile(degree, 0.95)` for 95th percentile)

**Output:**
```
  layer  node_count  avg_degree  median_degree   q25   q75
0  social         5       2.400          2.0   2.0   3.0
1  work           3       2.000          2.0   2.0   2.0
```

---

### Example 11: Advanced Edge Queries with Endpoint Properties

Edge queries now support full parity with node queries, including filtering on endpoint properties:

```python
from py3plex.dsl import Q, L

# Filter edges by source node degree
high_degree_edges = (
    Q.edges()
     .where(src_degree__gt=3)
     .execute(net)
)

# Filter by both source and target degrees
result = (
    Q.edges()
     .where(src_degree__ge=2, dst_degree__ge=2)
     .execute(net)
)

# Combine endpoint properties with edge attributes
result = (
    Q.edges()
     .where(weight__gt=1.5, src_degree__gt=2)
     .order_by("-weight")
     .limit(10)
     .execute(net)
)

# Aggregate endpoint properties per layer pair
result = (
    Q.edges()
     .per_layer_pair()
     .aggregate(
         edge_count="count()",
         avg_src_degree="mean(src_degree)",
         avg_dst_degree="mean(dst_degree)",
         max_src_degree="max(src_degree)",
         avg_weight="mean(weight)"
     )
     .execute(net)
)

# Export to pandas
df = result.to_pandas()
print(df)
```

**Available endpoint properties for edges:**
- `src_degree` / `source_degree`: Degree of source node
- `dst_degree` / `target_degree`: Degree of target node
- `source_layer`: Layer of source node
- `target_layer`: Layer of target node
- `weight`: Edge weight (default: 1.0)
- Any custom edge attributes

**Output:**
```
  source_layer target_layer  edge_count  avg_src_degree  avg_dst_degree  avg_weight
0      social       social           4            2.75            2.75        2.50
1      work         work             3            2.00            2.00        6.00
```

---

### Example 12: Edge Coverage Analysis

Analyze edges that appear across multiple layer pairs:

```python
from py3plex.dsl import Q, L

# Find edges present in multiple layer pairs
result = (
    Q.edges()
     .per_layer_pair()
     .coverage(mode="at_least", k=2)  # Edges in at least 2 layer pairs
     .aggregate(
         layer_pair_count="count()",
         avg_weight="mean(weight)"
     )
     .execute(net)
)

# Get summary of grouped edges
summary = result.group_summary()
print(summary)
```

**Output:**
```
  edge              layer_pairs  count  avg_weight
0 (A, B)           2            2      3.0
1 (B, C)           2            2      4.0
```

---

### DSL v2 vs Legacy DSL

| Feature | Legacy DSL | DSL v2 |
|---------|-----------|--------|
| Syntax | String-based | Builder API (+ string) |
| Layer algebra | Limited | Full algebra (L[...] + L[...]) |
| Uncertainty | Not supported | First-class (.uq()) |
| Grouping | Not supported | per_layer(), per_layer_pair(), coverage() |
| Aggregations | Not supported | Full suite (mean, median, quantile, etc.) |
| Edge queries | Limited | Full parity with node queries |
| Endpoint properties | Not supported | src_degree, dst_degree, etc. |
| Pattern matching | Basic MATCH | Full Cypher-like |
| Dynamics | Not supported | D.process(...) |
| Null models | Not supported | N.configuration() |
| Type safety | Runtime errors | IDE autocomplete |

### DSL v2 Architecture

DSL v2 uses a unified AST (Abstract Syntax Tree) compilation model:

```
Builder API (Q, L, etc.)  ─┐
                          ├─→ AST ─→ Executor ─→ QueryResult
String DSL                ─┘
```

Both frontends compile to the same AST, ensuring consistent behavior.

---

## Dplyr-Style Chainable Graph Operations API

py3plex provides a dplyr-inspired API for fluent, method-chaining operations on nodes and edges. This allows functional-style data manipulation similar to R's dplyr or Python's pandas.

**NOTE:** As of version 1.1.0, the dplyr-style methods have been integrated directly into the DSL v2 builder (`Q.nodes()` and `Q.edges()`), providing a unified API. The standalone `graph_ops` module is still available for backward compatibility, but the recommended approach is to use the DSL builder with dplyr-style methods like `.filter()`, `.head()`, `.tail()`, `.sample()`, etc.

### Using Dplyr-Style Methods in DSL Builder

```python
from py3plex.dsl import Q, L
from py3plex.core import multinet

# Create network
net = multinet.multi_layer_network(directed=False)
net.add_edges([
    {'source': 'A', 'target': 'B', 'source_type': 'ppi', 'target_type': 'ppi'},
    {'source': 'B', 'target': 'C', 'source_type': 'ppi', 'target_type': 'ppi'},
    {'source': 'A', 'target': 'C', 'source_type': 'ppi', 'target_type': 'ppi'},
])

# Unified API with dplyr-style methods
df = (
    Q.nodes()
     .from_layers(L["ppi"])
     .compute("degree")
     .filter(degree__gt=1)               # Dplyr-style filter
     .mutate(norm_deg=lambda r: r["degree"] / 3)  # Mutate with lambdas
     .arrange("-degree")                  # Sort descending
     .head(3)                             # Take top 3
     .execute(net)
     .to_pandas()
)
```

**New Dplyr-Style Methods in DSL Builder:**
- `.filter()` - Alias for `.where()`, traditional dplyr naming
- `.filter_expr(expr)` - String-based filtering: `filter_expr("degree > 10 and layer == 'ppi'")`
- `.head(n)` - Keep first n results
- `.tail(n)` - Keep last n results  
- `.take(n)` - Alias for `.head(n)`, SQL-style
- `.sample(n, seed)` - Random sampling with optional seed
- `.slice(start, end)` - Array slicing like Python `[start:end]`
- `.first()` - Return only first result (limits to 1)
- `.last()` - Return only last result
- `.pluck(field)` - Extract single column
- `.collect()` - No-op for API compatibility

### Core Components (Standalone graph_ops)

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

## Dynamics Simulations

py3plex provides a comprehensive framework for simulating dynamical processes on multilayer networks.

### Core Components

```python
from py3plex.dynamics import (
    D,                      # Dynamics builder
    SIS, SIR, SEIR,        # Compartmental models
    RandomWalk,             # Random walk process
    DynamicsProcess,        # Base class for custom dynamics
    SimulationResult,       # Result container
)
```

### Example 1: Basic SIS Simulation

```python
from py3plex.dynamics import D, SIS

# Define and run SIS simulation
sim = (
    D.process(SIS(beta=0.3, mu=0.1))
     .initial(infected=0.01)  # 1% initially infected
     .steps(100)
     .measure("prevalence", "incidence")
     .replicates(20)
     .seed(42)
)

result = sim.run(network)
df = result.to_pandas()  # Tidy DataFrame with time series

print(df.head())
# time  replicate  prevalence  incidence
# 0     0          0.010000    0.010000
# 1     0          0.015234    0.005234
# ...
```

---

### Example 2: Multilayer SIR with Coupling

```python
from py3plex.dynamics import D, SIR
from py3plex.dsl import L

# SIR on multiple layers with node coupling
sim = (
    D.process(SIR(beta=0.2, gamma=0.05))
     .on_layers(L["offline"] + L["online"])
     .coupling(node_replicas="strong")  # State syncs across layers
     .initial(infected=0.01)
     .steps(200)
     .measure("prevalence", "prevalence_by_layer")
     .replicates(10)
)

result = sim.run(network)
df = result.to_pandas()
```

---

### Example 3: Random Walk Dynamics

```python
from py3plex.dynamics import D, RandomWalk

# Random walk with layer transitions
sim = (
    D.process(RandomWalk(transition_prob=0.1))  # 10% chance to switch layers
     .initial(walkers={"A": 1.0})  # Start walker at node A
     .steps(1000)
     .measure("visit_counts", "stationary_distribution")
)

result = sim.run(network)
```

---

### Example 4: Custom Dynamics Process

```python
from py3plex.dynamics import DynamicsProcess
import numpy as np

class ThresholdDynamics(DynamicsProcess):
    """Custom threshold activation model."""
    
    def __init__(self, threshold=0.3):
        self.threshold = threshold
    
    def step(self, network, state):
        """Execute one time step."""
        new_state = state.copy()
        
        for node in network.get_nodes():
            neighbors = list(network.core_network.neighbors(node))
            if not neighbors:
                continue
            
            active_neighbors = sum(state.get(n, 0) for n in neighbors)
            fraction_active = active_neighbors / len(neighbors)
            
            if fraction_active >= self.threshold:
                new_state[node] = 1
        
        return new_state

# Use custom dynamics
sim = (
    D.process(ThresholdDynamics(threshold=0.3))
     .initial(active={"A": 1, "B": 1})
     .steps(50)
     .measure("active_count")
)

result = sim.run(network)
```

---

### Available Process Models

| Model | Description | Parameters |
|-------|-------------|------------|
| `SIS` | Susceptible-Infected-Susceptible | `beta` (infection), `mu` (recovery) |
| `SIR` | Susceptible-Infected-Recovered | `beta` (infection), `gamma` (recovery) |
| `SEIR` | With Exposed state | `beta`, `sigma` (incubation), `gamma` |
| `RandomWalk` | Random walker on network | `transition_prob` (layer switch) |

### Available Measurements

- `prevalence`: Fraction of infected nodes
- `incidence`: New infections per step
- `prevalence_by_layer`: Prevalence separated by layer
- `visit_counts`: Node visit frequency (for random walks)
- `stationary_distribution`: Long-term visit probabilities

---

## Uncertainty Quantification

py3plex features first-class uncertainty support, treating uncertainty as a native property of statistics rather than an add-on.

### Core Components

```python
from py3plex.uncertainty import (
    StatSeries,             # Universal statistic type
    StatMatrix,             # Matrix statistics
    CommunityStats,         # Community detection results
    ResamplingStrategy,     # Resampling methods
    estimate_uncertainty,   # Generic uncertainty estimator
    uncertainty_enabled,    # Context manager
)
```

### Example 1: Explicit Uncertainty Parameter

```python
from py3plex.algorithms.centrality_toolkit import multilayer_pagerank
from py3plex.uncertainty import ResamplingStrategy

# Compute PageRank with uncertainty
result = multilayer_pagerank(
    network,
    uncertainty=True,
    n_runs=100,
    resampling=ResamplingStrategy.PERTURBATION,
    random_seed=42
)

# Access statistics
print(f"Mean: {result.mean}")
print(f"Std: {result.std}")
print(f"95% CI: {result.quantiles[0.025]} - {result.quantiles[0.975]}")
print(f"Certainty: {result.certainty}")  # 0.0 = uncertain, 1.0 = deterministic
```

---

### Example 2: Context Manager for Global Uncertainty

```python
from py3plex.uncertainty import uncertainty_enabled

# Enable uncertainty for entire pipeline
with uncertainty_enabled(n_runs=50):
    pr = multilayer_pagerank(network)
    bc = multilayer_betweenness_centrality(network)
    # Both have uncertainty information

    print(f"PageRank std: {pr.std}")
    print(f"Betweenness std: {bc.std}")
```

---

### Example 3: Custom Metric with Uncertainty

```python
from py3plex.uncertainty import estimate_uncertainty, ResamplingStrategy

def my_custom_metric(net):
    """Compute average clustering coefficient."""
    import networkx as nx
    clustering = nx.clustering(net.core_network)
    return sum(clustering.values()) / len(clustering)

# Estimate uncertainty
result = estimate_uncertainty(
    network,
    my_custom_metric,
    n_runs=50,
    resampling=ResamplingStrategy.PERTURBATION,
    perturbation_params={
        "edge_drop_p": 0.1,  # Drop 10% of edges per sample
        "node_drop_p": 0.05  # Drop 5% of nodes per sample
    }
)

print(f"Metric: {result['mean']:.4f} ± {result['std']:.4f}")
```

---

### Example 4: StatSeries for Backward Compatibility

```python
# StatSeries implements __array__ for numpy compatibility
result = multilayer_pagerank(network, uncertainty=True, n_runs=50)

# Works with numpy
import numpy as np
arr = np.array(result)  # Extracts mean values

# Dictionary-like access
node = result.index[0]
stats = result[node]
# {'mean': 0.25, 'std': 0.02, 'quantiles': {...}}
```

---

### Resampling Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `SEED` | Multiple random seeds | Stochastic algorithms |
| `PERTURBATION` | Drop edges/nodes | Structural uncertainty |
| `BOOTSTRAP` | Resample with replacement | Statistical inference |
| `JACKKNIFE` | Leave-one-out | Influence analysis |

---

## Replayable Provenance and Query Replay

py3plex provides **replayable provenance** that captures sufficient information to deterministically reproduce query results. This enables reproducible research, debugging, and result verification.

### Key Concepts

**Provenance Modes:**
- **log** (default): Lightweight metadata tracking (timestamps, network fingerprint, timing)
- **replayable**: Full provenance with network snapshot, AST serialization, and seed capture

**Capture Methods:**
- **auto**: Automatically decide based on network size (inline for small, fingerprint for large)
- **fingerprint**: Only capture metadata (node/edge counts, layers)
- **snapshot**: Always capture full network snapshot
- **delta**: Capture changes from a base network (future feature)

### Basic Usage

```python
from py3plex.dsl import Q

# Execute query with replayable provenance
result = (
    Q.nodes()
     .provenance(mode="replayable", capture="auto", seed=42)
     .compute("degree", "betweenness_centrality")
     .execute(network)
)

# Check if replayable
print(result.is_replayable)  # True

# Access provenance
prov = result.provenance
print(prov['mode'])  # "replayable"
print(prov['network_capture']['capture_method'])  # "snapshot_graph"

# Replay to reproduce results
result2 = result.replay(strict=False)
assert result.count == result2.count  # Deterministic reproduction
```

### Convenience Method

Use `.reproducible()` for simpler syntax:

```python
# Equivalent to .provenance(mode="replayable", capture="auto", seed=42)
result = (
    Q.nodes()
     .reproducible(True, seed=42)
     .compute("degree")
     .execute(network)
)
```

### Bundle Export and Import

Export results with provenance as portable bundles:

```python
from py3plex.provenance import replay_from_bundle

# Export bundle (compressed JSON)
result.export_bundle("result.json.gz", compress=True)

# Load and replay from bundle
result2 = replay_from_bundle("result.json.gz", strict=False)

# Or load without replaying
from py3plex.provenance import load_bundle
bundle = load_bundle("result.json.gz")
prov = bundle["provenance"]
```

### Provenance Schema (v1.0)

Replayable provenance includes:

1. **Query Information:**
   - Serialized AST for exact query reconstruction
   - Parameter bindings
   - Execution plan (stages and toggles)

2. **Network Snapshot:**
   - Nodes (id, layer, attributes)
   - Edges (source, target, layers, weight, attributes)
   - Stable ordering for hashing

3. **Randomness Configuration:**
   - Base seed for reproducibility
   - Derived seeds per stage (UQ, community detection, etc.)
   - SeedSequence entropy for advanced scenarios

4. **Environment:**
   - py3plex version
   - Python version and platform
   - Dependency versions (numpy, networkx, etc.)

5. **Performance:**
   - Timing per stage (bind_parameters, filter, compute, etc.)

### Deterministic Replay with Uncertainty

When using uncertainty quantification (.uq()), replayable provenance ensures identical confidence intervals:

```python
# Original query
result1 = (
    Q.nodes()
     .reproducible(True, seed=42)
     .uq(method="bootstrap", n_samples=100)
     .compute("betweenness_centrality")
     .execute(network)
)

# Replay produces identical CI bounds
result2 = result1.replay()

# Check mean and CI match
for node in result1.items:
    stats1 = result1.attributes['betweenness_centrality'][node]
    stats2 = result2.attributes['betweenness_centrality'][node]
    assert stats1['mean'] == stats2['mean']
    assert stats1['quantiles'] == stats2['quantiles']
```

### Size Guardrails

Provenance respects size limits to avoid memory issues:

```python
# Default thresholds
# - 10,000 nodes or 50,000 edges: inline snapshot
# - Above: fingerprint only (unless explicitly set to snapshot)

# Explicit control
result = (
    Q.nodes()
     .provenance(
         mode="replayable",
         capture="snapshot",  # Force snapshot even for large graphs
         max_bytes=20*1024*1024  # 20MB limit
     )
     .execute(network)
)
```

### Backward Compatibility

Queries without provenance config use log mode by default:

```python
# Legacy behavior (still works)
result = Q.nodes().compute("degree").execute(network)

# Has provenance but not replayable
assert result.provenance is not None
assert not result.is_replayable  # False (log mode)
```

### Limitations

- **Large Networks:** Auto-capture uses fingerprint for >10k nodes. Export to external bundle for replay.
- **Version Compatibility:** `strict=True` in replay() enforces exact version match. Use `strict=False` for minor versions.
- **Non-Deterministic Operations:** Some operations (e.g., hash-based ordering) may differ across Python versions.

### Agent Guidance

**When writing code that produces query results:**
1. Use `.reproducible(True, seed=...)` when reproducibility matters (papers, reports, debugging).
2. Default (log mode) is fine for exploratory analysis.
3. Always check `result.is_replayable` before calling `.replay()`.
4. Use `.export_bundle()` to save results for later verification.

**When reviewing provenance-related code:**
1. Preserve backward compatibility: existing queries must not break.
2. Add size warnings when capture exceeds thresholds.
3. Ensure determinism: use explicit seeds for all stochastic operations.
4. Test replay with bundle export/import roundtrips.
## Counterfactual Reasoning vs Uncertainty Quantification

py3plex provides distinct tools for **uncertainty quantification (UQ)** and **counterfactual reasoning**. Understanding the difference is crucial for correct analysis:

**Uncertainty Quantification (UQ):**
- **Question:** "What is the error bar on this estimate?"
- **Purpose:** Quantify uncertainty of a measurement/statistic
- **Output:** Confidence intervals, standard deviations
- **Example:** "PageRank is 0.25 ± 0.02 (95% CI: [0.21, 0.29])"

**Counterfactual Reasoning:**
- **Question:** "Would my conclusion hold if I perturbed the network?"
- **Purpose:** Test sensitivity of analytical conclusions to structural interventions
- **Output:** Robustness reports, stability metrics
- **Example:** "Node A is stably in top-5 across 80% of perturbations"

### When to Use Each

Use **UQ (`.uq()`)** when you need to:
- Report confidence intervals on metrics
- Quantify measurement uncertainty
- Compare statistics with error bars
- Assess reliability of estimates

Use **Counterfactual (`.robustness_check()`)** when you need to:
- Test if rankings are stable
- Validate conclusions under perturbations
- Identify fragile vs robust nodes/communities
- Assess sensitivity to network structure

### Example 1: Counterfactual Robustness Check

```python
from py3plex.dsl import Q
from py3plex.core import multinet

# Create network
net = multinet.multi_layer_network(directed=False)
net.add_edges([
    ['A', 'social', 'B', 'social', 1.0],
    ['B', 'social', 'C', 'social', 1.0],
    ['C', 'social', 'D', 'social', 1.0],
    # ... more edges
])

# Test if top-5 PageRank nodes are stable under perturbations
report = (Q.nodes()
         .compute("pagerank")
         .robustness_check(net, strength="medium", repeats=30, seed=42))

# Show human-readable report
report.show()

# Find stably-ranked nodes
stable_top_5 = report.stable_top_k(k=5, threshold=0.8)
print(f"Stable top-5: {stable_top_5}")

# Find fragile nodes (high variability)
fragile = report.fragile(n=5)
print(f"Most fragile nodes: {fragile}")
```

### Example 2: Comparing UQ vs Counterfactual

```python
# UQ: Estimate PageRank with uncertainty
uq_result = (Q.nodes()
            .uq(method="perturbation", n_samples=100, seed=42)
            .compute("pagerank")
            .execute(net))

# Access uncertainty estimates
df_uq = uq_result.to_pandas(expand_uncertainty=True)
print(df_uq[['id', 'pagerank', 'pagerank_std', 'pagerank_ci95_low', 'pagerank_ci95_high']])
# Output: Node A has PageRank 0.25 ± 0.02 (CI: [0.21, 0.29])

# Counterfactual: Test conclusion stability
cf_report = (Q.nodes()
            .compute("pagerank")
            .robustness_check(net, strength="medium", repeats=30, seed=42))

# Check if "A is in top-5" is a robust conclusion
stable = cf_report.stable_top_k(k=5, threshold=0.8)
print(f"Is A stably top-5? {'Yes' if 'A' in stable else 'No'}")
# Output: Tests the CONCLUSION ("A is top-5"), not the ESTIMATE ("A has PageRank X")
```

### Example 3: Try Different Intervention Strengths

```python
# Compare light/medium/heavy interventions
summary = (Q.nodes()
          .compute("degree", "betweenness_centrality")
          .try_strengths(net, repeats=30, seed=42))

print(summary)
# Output DataFrame:
#   strength  degree_avg_cv  degree_max_cv  betweenness_avg_cv  ...
#   light     0.05          0.12           0.08                ...
#   medium    0.12          0.25           0.18                ...
#   heavy     0.28          0.54           0.35                ...
```

### Example 4: Advanced Custom Interventions

```python
from py3plex.counterfactual import RemoveEdgesSpec, RewireDegreePreservingSpec

# Custom intervention: remove 15% of edges randomly
spec = RemoveEdgesSpec(proportion=0.15, mode="random")

result = (Q.nodes()
         .compute("closeness_centrality")
         .counterfactualize(net, spec, repeats=100, seed=42))

# Convert to report
report = result.to_report()
report.show()

# Or use degree-preserving rewiring
spec2 = RewireDegreePreservingSpec(n_swaps=100)
result2 = (Q.nodes()
          .compute("betweenness_centrality")
          .counterfactualize(net, spec2, repeats=50, seed=42))
```

### Intervention Presets

Py3plex provides dummy-proof presets for common interventions:

| Preset | Description | Use Case |
|--------|-------------|----------|
| `"quick"` | Minimal edge removal (2-10%) | Fast exploration |
| `"degree_safe"` | Degree-preserving rewiring (DEFAULT) | Test topology sensitivity |
| `"layer_safe"` | Preserve per-layer edge counts | Test layer-specific effects |
| `"weight_only"` | Shuffle weights only | Test weight sensitivity |
| `"targeted"` | Remove high-weight edges | Test hub importance |

```python
# Use preset with strength parameter
report = (Q.nodes()
         .compute("eigenvector_centrality")
         .robustness_check(
             net,
             shake="degree_safe",  # Preset
             strength="heavy",      # light/medium/heavy
             repeats=50,
             seed=42
         ))
```

### RobustnessReport Methods

```python
report = Q.nodes().compute("degree").robustness_check(net)

# Display human-readable summary
report.show(top_n=20, precision=4)

# Statistical summary
report.describe()

# Find stable top-k items
stable = report.stable_top_k(k=10, threshold=0.8)

# Find most fragile items
fragile = report.fragile(n=5)

# Per-layer sensitivity (if applicable)
layer_sens = report.layer_sensitivity()

# Export to pandas
df = report.to_pandas()

# Compare specific item across runs
comparison = report.compare_items(item_id='A')
print(comparison)
# {'item_id': 'A', 
#  'baseline': {'degree': 5}, 
#  'counterfactuals': {'degree': {'mean': 4.8, 'std': 0.6, ...}}}
```

### Key Differences Summary

| Aspect | UQ | Counterfactual |
|--------|----|--------------  |
| **What it tests** | Estimate uncertainty | Conclusion stability |
| **Output type** | Error bars, CIs | Stability metrics |
| **DSL method** | `.uq()` | `.robustness_check()` |
| **Provenance** | `provenance.uncertainty` | `provenance.counterfactual` |
| **Use for** | Reporting metrics | Validating conclusions |
## Distributional Community Detection

**New in v1.1:** Uncertainty-aware community detection via distributional partitions.

py3plex now supports distributional community detection that runs community detection multiple times (with resampling or different seeds) to produce a distribution over partitions. This enables:

- **Co-association matrices**: P(node_i and node_j in same community)
- **Consensus partitions**: Representative partition (medoid or clustering-based)
- **Node confidence scores**: Per-node stability measures
- **Boundary node identification**: Nodes with uncertain assignments

### Core Functions and Types

```python
from py3plex.algorithms.community_detection import multilayer_louvain_distribution
from py3plex.uncertainty import CommunityDistribution, perturb_network_edges, bootstrap_network_edges
```

### API Signature

```python
def multilayer_louvain_distribution(
    network: multi_layer_network,
    *,
    n_runs: int = 100,
    resampling: str = "seed",  # "seed" | "perturbation" | "bootstrap"
    perturbation_params: Optional[Dict[str, Any]] = None,  # e.g., {"edge_drop_p": 0.05}
    gamma: Union[float, Dict[Any, float]] = 1.0,
    gamma_grid: Optional[List[float]] = None,
    omega: Union[float, np.ndarray] = 1.0,
    weight: str = "weight",
    max_iter: int = 100,
    seed: Optional[int] = None,
    n_jobs: int = 1,
    weight_by: Optional[str] = "modularity",  # "modularity" | None
    coassoc_mode: str = "auto",  # "auto" | "dense" | "sparse"
    topk: int = 50,
) -> CommunityDistribution
```

### Return Type: CommunityDistribution

```python
class CommunityDistribution:
    # Properties
    n_nodes: int
    n_partitions: int
    nodes: List[Any]
    partitions: List[np.ndarray]
    weights: np.ndarray
    meta: Dict[str, Any]
    
    # Methods
    coassociation(mode="dense"|"sparse", topk=50) -> Union[np.ndarray, Dict]
    consensus_partition(method="medoid"|"cluster_coassoc") -> np.ndarray
    node_confidence(consensus=None) -> np.ndarray
    node_entropy(aligned=False) -> np.ndarray
    node_margin(consensus=None) -> np.ndarray
    align_labels(reference="medoid"|"first"|array, metric="overlap"|"nmi")
    node_membership_probs() -> np.ndarray  # Requires alignment
    to_dict(node_id) -> Dict[str, Any]
```

### Provenance Fields

The `meta` dict in `CommunityDistribution` contains provenance information:

```python
{
    'method': 'multilayer_louvain',
    'n_runs': 100,
    'resampling': 'perturbation',  # or 'seed', 'bootstrap'
    'gamma': 1.0,
    'gamma_grid': None,  # Optional: list of gamma values
    'omega': 1.0,
    'seed': 42,
    'n_jobs': 2,
    'weight_by': 'modularity',
    'layers': ['L1', 'L2'],
    'perturbation_params': {'edge_drop_p': 0.05},  # If perturbation
    'mean_modularity': 0.42,
    'std_modularity': 0.05,
}
```

### Example 1: Basic Distributional Community Detection

```python
from py3plex.core import multinet
from py3plex.algorithms.community_detection import multilayer_louvain_distribution

# Create or load network
net = multinet.multi_layer_network(directed=False)
net.add_edges([
    ['A', 'L1', 'B', 'L1', 1],
    ['B', 'L1', 'C', 'L1', 1],
    ['C', 'L1', 'D', 'L1', 1],
], input_type='list')

# Run distributional community detection
dist = multilayer_louvain_distribution(
    net,
    n_runs=100,
    resampling='perturbation',
    perturbation_params={'edge_drop_p': 0.05},
    seed=42,
    n_jobs=2
)

# Get consensus partition
consensus = dist.consensus_partition()
print(f"Communities: {consensus}")

# Get node confidence (stability)
confidence = dist.node_confidence()
print(f"Confidence: {confidence}")
```

---

### Example 2: Identifying Stable vs Boundary Nodes

```python
# Get confidence scores
confidence = dist.node_confidence()
entropy = dist.node_entropy()

# Identify stable core (high confidence)
stable_mask = confidence >= 0.8
stable_nodes = [dist.nodes[i] for i in range(dist.n_nodes) if stable_mask[i]]

# Identify boundary nodes (low confidence)
boundary_mask = confidence < 0.5
boundary_nodes = [dist.nodes[i] for i in range(dist.n_nodes) if boundary_mask[i]]

print(f"Stable core: {len(stable_nodes)} nodes")
print(f"Boundary: {len(boundary_nodes)} nodes")
```

---

### Example 3: Co-Association Matrix

```python
# Compute co-association matrix P(i, j in same community)
coassoc = dist.coassociation(mode='dense')

# Find nodes strongly associated with node 0
node_idx = 0
strong_assoc = [(i, coassoc[node_idx, i]) for i in range(dist.n_nodes) 
                 if i != node_idx and coassoc[node_idx, i] > 0.8]

print(f"Nodes strongly associated with {dist.nodes[node_idx]}:")
for i, prob in sorted(strong_assoc, key=lambda x: x[1], reverse=True):
    print(f"  {dist.nodes[i]}: P={prob:.3f}")
```

---

### Best Practices

1. **Use co-association for large networks**:
   - For n_nodes > 2000, use `coassoc_mode='sparse'` or `mode='auto'`
   - Dense co-association is O(n²) memory

2. **Prefer co-association-based confidence over aligned label probs**:
   - Co-association is label-permutation invariant (no alignment needed)
   - Alignment can be expensive and introduce artifacts

3. **Always set seed for reproducibility**:
   - Deterministic: same seed => identical results regardless of n_jobs
   - Uses numpy SeedSequence for proper parallel seed spawning

4. **Choose resampling strategy wisely**:
   - `'seed'`: Algorithm stochasticity (fastest, recommended default)
   - `'perturbation'`: Structural uncertainty (edge drop, slower)
   - `'bootstrap'`: Statistical bootstrap (slowest, edge resampling)

5. **Weight by modularity for quality-aware consensus**:
   - `weight_by='modularity'` weights better partitions more heavily
   - Set `weight_by=None` for uniform weighting

6. **Parallel execution preserves determinism**:
   - `n_jobs=1`: Serial execution
   - `n_jobs>1`: Parallel with deterministic seed spawning
   - Same seed + same n_runs => identical output regardless of n_jobs

### Copy/Paste Snippet

```python
# Quick start: uncertainty-aware community detection
from py3plex.core import multinet
from py3plex.algorithms.community_detection import multilayer_louvain_distribution

net = multinet.multi_layer_network(directed=False)
net.load_network('my_network.edgelist', directed=False, input_type='edgelist_hash')

# Run with 100 iterations, perturbation resampling
dist = multilayer_louvain_distribution(
    net,
    n_runs=100,
    resampling='perturbation',
    perturbation_params={'edge_drop_p': 0.05},
    seed=42,
    n_jobs=4  # Parallel
)

# Get results
consensus = dist.consensus_partition()
confidence = dist.node_confidence()

# Filter stable core
stable_mask = confidence >= 0.8
stable_nodes = [dist.nodes[i] for i in range(dist.n_nodes) if stable_mask[i]]

print(f"Communities: {len(set(consensus))}")
print(f"Stable core: {len(stable_nodes)}/{dist.n_nodes} nodes")
```

---

## Temporal Networks

py3plex provides native support for temporal multilayer networks with time-stamped edges and temporal queries.

### Core Components

```python
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork
from py3plex.temporal_utils import EdgeTimeInterval, extract_edge_time
```

### Example 1: Creating Temporal Networks

```python
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork

# Create temporal network
tnet = TemporalMultiLayerNetwork()

# Add time-stamped edges
tnet.add_edge('A', 'B', layer='social', time=100.0)
tnet.add_edge('B', 'C', layer='social', time=200.0)
tnet.add_edge('A', 'C', layer='social', time=150.0)

# Add interval edges
tnet.add_edge('A', 'B', layer='work', t_start=100.0, t_end=200.0)
```

---

### Example 2: Temporal Snapshots

```python
# Get snapshot at specific time
snapshot = tnet.snapshot_at(150.0)
print(f"Snapshot at t=150: {snapshot.number_of_nodes()} nodes, {snapshot.number_of_edges()} edges")

# Get snapshot for time range
snapshot = tnet.get_snapshot(time_range=(100.0, 200.0))
```

---

### Example 3: Sliding Windows

```python
# Iterate over temporal windows
for t_start, t_end, window_net in tnet.window_iter(window_size=50, step=25):
    print(f"Window [{t_start}, {t_end}]:")
    print(f"  Nodes: {window_net.number_of_nodes()}")
    print(f"  Edges: {window_net.number_of_edges()}")
    
    # Compute statistics on window
    avg_degree = sum(dict(window_net.degree()).values()) / window_net.number_of_nodes()
    print(f"  Avg degree: {avg_degree:.2f}")
```

---

### Example 4: Temporal DSL Queries

```python
from py3plex.dsl import Q

# Query edges in time window
result = (
    Q.edges()
     .where(t__between=(100.0, 200.0))
     .from_layers(L["social"])
     .execute(tnet.base_network)
)

# Query nodes active in time range
result = (
    Q.nodes()
     .where(t__gte=100.0, t__lte=200.0)
     .compute("degree")
     .execute(tnet.base_network)
)
```

---

### Example 5: Temporal Aggregation

```python
# Aggregate temporal network over time windows
import pandas as pd

time_windows = [(0, 100), (100, 200), (200, 300)]
stats = []

for t_start, t_end in time_windows:
    snapshot = tnet.get_snapshot(time_range=(t_start, t_end))
    stats.append({
        'window': f"{t_start}-{t_end}",
        'nodes': snapshot.number_of_nodes(),
        'edges': snapshot.number_of_edges(),
        'density': snapshot.number_of_edges() / (snapshot.number_of_nodes() ** 2)
    })

df = pd.DataFrame(stats)
print(df)
```

---

## Null Models

py3plex provides null model implementations for statistical testing and comparison.

### Core Components

```python
from py3plex.nullmodels import (
    configuration_model,      # Preserve degree sequence
    erdos_renyi_model,       # Random graph
    barabasi_albert_model,   # Preferential attachment
    stochastic_block_model,  # Community structure
)
```

### Example 1: Configuration Model

```python
from py3plex.nullmodels import configuration_model

# Generate configuration model null model
null_net = configuration_model(network, preserve_layers=True)

# Compute observed statistic
observed_clustering = compute_clustering(network)

# Generate null distribution
null_distribution = []
for i in range(100):
    null_net = configuration_model(network, preserve_layers=True, seed=i)
    null_clustering = compute_clustering(null_net)
    null_distribution.append(null_clustering)

# Compute p-value
import numpy as np
p_value = sum(nc >= observed_clustering for nc in null_distribution) / len(null_distribution)
print(f"p-value: {p_value:.4f}")
```

---

### Example 2: DSL Integration with Null Models

```python
from py3plex.dsl import N

# Generate null models via DSL
null_models = (
    N.configuration()
     .samples(100)
     .seed(42)
     .preserve_layers(True)
     .preserve_degree_sequence(True)
     .execute(network)
)

# Use for statistical testing
observed = compute_statistic(network)
null_stats = [compute_statistic(nm) for nm in null_models]

# Compute z-score
import numpy as np
z_score = (observed - np.mean(null_stats)) / np.std(null_stats)
print(f"Z-score: {z_score:.2f}")
```

---

## Internal Parallelization

**Note: Parallelization is fully internal and transparent - no API changes required.**

py3plex implements deterministic parallel execution for computationally expensive operations including null model generation and uncertainty quantification. The parallelization is completely internal and maintains full backward compatibility.

---

## Probabilistic Community Detection

py3plex provides probabilistic community detection with first-class uncertainty quantification, going beyond "hard labels" to provide membership distributions, node-level confidence, and community stability metrics.

### Key Features

- **Backward Compatible**: Deterministic mode returns hard labels as before
- **Probabilistic Memberships**: Per-node membership probability distributions
- **Node Uncertainty Metrics**: Entropy, confidence, margin for each node
- **Community Stability**: Persistence, size variability across ensemble
- **Partition Variability**: VI/ARI/NMI distributions between partitions
- **Multiple UQ Methods**: SEED (algorithmic stochasticity), PERTURBATION (structural uncertainty), BOOTSTRAP (resampling)
- **DSL Integration**: Works seamlessly with `.uq()` chaining

### Core Components

```python
from py3plex.uncertainty import (
    generate_community_ensemble,      # Generate partition ensemble
    ProbabilisticCommunityResult,     # Probabilistic result wrapper
    CommunityDistribution,            # Low-level distribution object
)
```

### Example 1: Deterministic Community Detection (Backward Compatible)

```python
from py3plex.dsl import Q
from py3plex.core import multinet

# Create network
net = multinet.multi_layer_network(directed=False)
# ... add nodes and edges ...

# Standard deterministic community detection
result = Q.nodes().compute("communities").execute(net)
communities = result.attributes['communities']

# Hard labels: Dict[node, community_id]
for node, comm_id in communities.items():
    print(f"{node} -> Community {comm_id}")
```

### Example 2: Probabilistic Communities with SEED Method

```python
# Probabilistic community detection (algorithmic stochasticity)
result = (
    Q.nodes()
    .uq(method="seed", n_samples=50, seed=42)
    .compute("communities")
    .execute(net)
)

communities = result.attributes['communities']

# Each node has uncertainty information
for node, data in communities.items():
    print(f"{node}:")
    print(f"  Hard label: {data['mean']}")
    print(f"  Confidence: {data['confidence']:.3f}")
    print(f"  Entropy: {data['entropy']:.3f}")
    print(f"  Margin: {data['margin']:.3f}")
    
    # Membership probabilities
    if 'probs' in data:
        print(f"  Probabilities: {data['probs']}")
```

### Example 3: Comparing Uncertainty Methods

```python
# SEED method: Algorithmic stochasticity (multiple random seeds)
result_seed = (
    Q.nodes()
    .uq(method="seed", n_samples=50, seed=42)
    .compute("communities")
    .execute(net)
)

# PERTURBATION method: Structural uncertainty (perturb edges)
result_pert = (
    Q.nodes()
    .uq(method="perturbation", n_samples=50, seed=42)
    .compute("communities")
    .execute(net)
)

# Compare entropy (uncertainty)
for node in result_seed.attributes['communities'].keys():
    ent_seed = result_seed.attributes['communities'][node]['entropy']
    ent_pert = result_pert.attributes['communities'][node]['entropy']
    print(f"{node}: SEED={ent_seed:.3f}, PERT={ent_pert:.3f}")
```

### Example 4: Accessing Advanced Metrics

```python
# Generate ensemble and get full result object
from py3plex.uncertainty import generate_community_ensemble, ProbabilisticCommunityResult

dist = generate_community_ensemble(
    net,
    algorithm='louvain',
    method='seed',
    n_samples=100,
    seed=42,
    verbose=True
)

result = ProbabilisticCommunityResult(dist)

# Node-level metrics
labels = result.labels              # Dict[node, community_id]
probs = result.probs               # Dict[node, Dict[comm_id, prob]]
entropy = result.entropy           # Dict[node, float]
confidence = result.confidence     # Dict[node, float]
margin = result.margin             # Dict[node, float]

# Community-level stability metrics
stability = result.community_stability
for comm_id, metrics in stability.items():
    print(f"Community {comm_id}:")
    print(f"  Persistence: {metrics['persistence']:.3f}")
    print(f"  Size (mean ± std): {metrics['size_mean']:.1f} ± {metrics['size_std']:.1f}")
    print(f"  Coefficient of variation: {metrics['size_cv']:.3f}")

# Partition-space variability metrics
part_metrics = result.partition_metrics
print(f"Variation of Information (VI):")
print(f"  Mean: {part_metrics['vi_mean']:.3f}")
print(f"  Std: {part_metrics['vi_std']:.3f}")

if 'ari_mean' in part_metrics:
    print(f"Adjusted Rand Index (ARI):")
    print(f"  Mean: {part_metrics['ari_mean']:.3f}")
    print(f"  Std: {part_metrics['ari_std']:.3f}")
```

### Example 5: Filtering by Uncertainty

```python
# Find boundary nodes (high uncertainty)
result = (
    Q.nodes()
    .uq(method="seed", n_samples=50, seed=42)
    .compute("communities")
    .execute(net)
)

communities = result.attributes['communities']

# High-uncertainty nodes (entropy > threshold)
boundary_nodes = [
    node for node, data in communities.items()
    if data['entropy'] > 0.5
]

# Confident core nodes (high confidence)
core_nodes = [
    node for node, data in communities.items()
    if data['confidence'] > 0.9
]

print(f"Boundary nodes: {boundary_nodes}")
print(f"Core nodes: {core_nodes}")
```

### Example 6: Pandas Export with Uncertainty

```python
import pandas as pd

result = (
    Q.nodes()
    .uq(method="seed", n_samples=50, seed=42)
    .compute("communities")
    .execute(net)
)

# Manual expansion of uncertainty columns
data = []
for node, comm_data in result.attributes['communities'].items():
    row = {
        'node': node[0],
        'layer': node[1],
        'community_id': comm_data['mean'],
        'community_confidence': comm_data['confidence'],
        'membership_entropy': comm_data['entropy'],
        'membership_margin': comm_data['margin'],
    }
    
    # Add top-k membership probabilities
    if 'probs' in comm_data and comm_data['probs']:
        sorted_probs = sorted(comm_data['probs'].items(), 
                            key=lambda x: x[1], reverse=True)
        for k, (comm_id, prob) in enumerate(sorted_probs[:3]):
            row[f'p_comm_{comm_id}'] = prob
    
    data.append(row)

df = pd.DataFrame(data)
print(df)
```

### Uncertainty Structure

When uncertainty is enabled, each node's community data is a dict with:

```python
{
    'mean': int,              # Hard label (most likely community)
    'label': int,             # Alias for 'mean'
    'probs': Dict[int, float], # Membership probabilities {comm_id: prob}
    'entropy': float,         # Entropy of membership distribution (bits)
    'confidence': float,      # Max probability (most likely community)
    'margin': float,          # Difference between top 2 probabilities
    'std': 0.0,              # Always 0 (communities are categorical)
    'certainty': float,       # Alias for 'confidence'
    'quantiles': {},          # Empty (not meaningful for categorical)
}
```

### UQ Methods

#### SEED Method (Algorithmic Stochasticity)
```python
.uq(method="seed", n_samples=50, seed=42)
```
Runs community detection with different random seeds. Captures algorithmic randomness (e.g., Louvain's randomized order). Best for assessing algorithm stability.

#### PERTURBATION Method (Structural Uncertainty)
```python
.uq(method="perturbation", n_samples=50, seed=42)
```
Perturbs network structure (adds/removes edges) before each run. Captures structural uncertainty. Best for assessing robustness to noise.

#### BOOTSTRAP Method (Resampling)
```python
.uq(method="bootstrap", n_samples=50, seed=42, 
    bootstrap_unit="edges")
```
Resamples edges or nodes with replacement. Captures sampling uncertainty. Best for assessing statistical variability.

### Supported Algorithms

- **Louvain** (default): Fast modularity optimization
- **Label Propagation**: Simple and fast spreading algorithm
- **Infomap**: Information-theoretic community detection (requires `infomap` package)

Specify algorithm in low-level API:
```python
from py3plex.uncertainty import generate_community_ensemble

dist = generate_community_ensemble(
    net,
    algorithm='infomap',  # or 'louvain', 'label_propagation'
    method='seed',
    n_samples=50,
    seed=42
)
```

### Interpretation Guidelines

#### Node Metrics
- **Entropy**: Measures assignment uncertainty
  - 0 = deterministic assignment
  - High = node is on community boundary
- **Confidence**: Probability of most likely community
  - 1.0 = always assigned to same community
  - <0.8 = uncertain, possibly boundary node
- **Margin**: Confidence gap between top 2 communities
  - High = clear winner
  - Low = competing communities

#### Community Metrics
- **Persistence**: Fraction of runs where community exists
  - High = stable community
  - Low = unstable, may split/merge
- **Size Variability (CV)**: Coefficient of variation of size
  - Low = stable size
  - High = growing/shrinking community

#### Partition Metrics
- **VI (Variation of Information)**: Distance between partitions
  - 0 = identical partitions
  - High = very different partitions
- **ARI (Adjusted Rand Index)**: Similarity between partitions
  - 1.0 = perfect agreement
  - 0 = random agreement

### Performance Considerations

- **n_samples**: More samples = better uncertainty estimates, but slower
  - 25-50 samples: Fast, good for exploration
  - 100+ samples: More accurate, publishable results
- **Algorithm**: Louvain is fastest, Infomap most accurate but slower
- **Method**: SEED is fastest, PERTURBATION adds overhead for network modification
- **Network size**: Scales linearly with n_samples

### Best Practices

1. **Always set seed** for reproducibility: `seed=42`
2. **Use enough samples**: At least 25 for exploration, 100+ for publication
3. **Choose method based on goal**:
   - SEED: Algorithm stability
   - PERTURBATION: Robustness to noise
   - BOOTSTRAP: Statistical significance
4. **Inspect high-entropy nodes**: They're often boundary nodes or bridges
5. **Check community persistence**: Low persistence suggests over-partitioning
6. **Compare methods**: Different methods highlight different uncertainty sources

### Backward Compatibility

The system is fully backward compatible:
- `Q.nodes().compute("communities")` returns hard labels as before
- Adding `.uq(...)` enables probabilistic mode
- Without `.uq()`, deterministic Louvain is used (single run)
- Deterministic mode returns `certainty=1.0`, `entropy=0.0`

### Related Documentation

- **Example**: `examples/network_analysis/example_dsl_probabilistic_communities.py`
- **Tests**: `tests/property/test_probabilistic_communities_properties.py`
- **Module**: `py3plex.uncertainty.community_result`
- **Engine**: `py3plex.uncertainty.community_ensemble`

---

## Internal Parallelization (continued)

### Key Features

- **Deterministic Results**: Same seed produces identical results regardless of `n_jobs` setting or execution order
- **Serial by Default**: No multiprocessing overhead when not needed (`n_jobs=1` by default)
- **Optional Parallelization**: Use `n_jobs` parameter to enable parallel execution
- **Platform Safe**: Uses spawn context for Windows compatibility
- **No API Changes**: All parallelization is internal; existing code works unchanged

### Configuration

Parallel execution defaults can be set in `py3plex.config`:

```python
from py3plex import config

# Set default number of parallel jobs (default: 1 for serial execution)
config.DEFAULT_N_JOBS = 4

# Set parallel backend (default: "multiprocessing")
config.DEFAULT_PARALLEL_BACKEND = "multiprocessing"  # or "joblib" if installed
```

### Parallelized Operations

The following operations support optional parallel execution via the `n_jobs` parameter:

**1. Null Model Generation:**
```python
from py3plex.nullmodels import generate_null_model

# Serial execution (default)
result = generate_null_model(network, model="configuration", num_samples=100, seed=42)

# Parallel execution
result = generate_null_model(network, model="configuration", num_samples=100, seed=42, n_jobs=4)
# Same deterministic result as serial execution
```

**2. Bootstrap Uncertainty Estimation:**
```python
from py3plex.uncertainty import bootstrap_metric

def degree_metric(net):
    return {node: net.core_network.degree(node) for node in net.get_nodes()}

# Serial execution (default)
boot = bootstrap_metric(network, degree_metric, n_boot=100, random_state=42)

# Parallel execution
boot = bootstrap_metric(network, degree_metric, n_boot=100, random_state=42, n_jobs=4)
# Same deterministic result as serial execution
```

**3. Null Model Statistical Testing:**
```python
from py3plex.uncertainty import null_model_metric

def degree_metric(net):
    return {node: net.core_network.degree(node) for node in net.get_nodes()}

# Serial execution (default)
null_stats = null_model_metric(network, degree_metric, n_null=200, random_state=42)

# Parallel execution
null_stats = null_model_metric(network, degree_metric, n_null=200, random_state=42, n_jobs=4)
# Same deterministic result as serial execution
```

### Determinism Guarantees

The parallel implementation uses numpy's `SeedSequence` to spawn independent, reproducible child seeds for each parallel task:

```python
# Example: Same seed produces identical results
result_serial = generate_null_model(network, num_samples=100, seed=42, n_jobs=1)
result_parallel = generate_null_model(network, num_samples=100, seed=42, n_jobs=4)

# Results are identical (same structure, node counts, edge counts)
assert len(result_serial.samples) == len(result_parallel.samples)
```

### Performance Considerations

- **Serial Default**: `n_jobs=1` runs without multiprocessing overhead
- **Optimal Parallelization**: Use `n_jobs=-1` to use all CPU cores
- **Task Granularity**: Parallel execution is most beneficial for:
  - Large numbers of samples (num_samples ≥ 10)
  - Complex networks (>100 nodes)
  - Expensive metric functions
- **Overhead**: Small networks or few samples may be faster in serial mode

### Picklability Requirements

**Important**: When using `n_jobs > 1`, custom metric functions must be picklable:

```python
# ✓ GOOD: Module-level function (picklable)
def my_metric(network):
    return {node: network.core_network.degree(node) for node in network.get_nodes()}

# Use with parallel execution
result = bootstrap_metric(network, my_metric, n_boot=100, n_jobs=4)
```

```python
# ✗ BAD: Local function (not picklable for multiprocessing)
def run_analysis():
    def my_metric(network):  # Defined inside function - not picklable!
        return {node: network.core_network.degree(node) for node in network.get_nodes()}
    
    # This will fail with n_jobs > 1
    result = bootstrap_metric(network, my_metric, n_boot=100, n_jobs=4)
```

**Solution**: Define metric functions at module level or use `n_jobs=1` for serial execution (no pickling required).

### Implementation Notes

The parallel infrastructure is located in `py3plex/_parallel.py` (internal module, not part of public API):
- `parallel_map()`: Parallel execution with serial fallback
- `spawn_seeds()`: Deterministic seed spawning via numpy's SeedSequence
- Supports multiprocessing (default) and joblib backends
- Optional tqdm progress bars (if tqdm is installed)

All parallel execution maintains order-independent aggregation to ensure deterministic results regardless of task completion order.

---

## Semiring Algebra (S Builder): Paths, Closure, Fixed-Point

**Location**: `py3plex.dsl.S`, `py3plex.algebra`

py3plex provides a comprehensive semiring algebra framework for generic path computation and graph analysis. A **semiring** is an algebraic structure (S, ⊕, ⊗, 0, 1) that generalizes different notions of "best path":

- **Boolean semiring**: reachability (path existence)
- **Min-plus (tropical)**: shortest paths (minimize distance)
- **Max-times**: most reliable paths (maximize probability product)
- **Max-plus**: longest/best paths (maximize value)

The S builder integrates seamlessly with DSL v2, multilayer networks, layer algebra, and provenance tracking.

### Core Concept

A semiring defines:
- `add` (⊕): how to combine alternative paths
- `mul` (⊗): how to extend a path with an edge
- `zero` (0): identity for add (no path)
- `one` (1): identity for mul (empty path)

**Example**: In min-plus semiring for shortest paths:
- `add(a, b) = min(a, b)` (choose shorter path)
- `mul(a, b) = a + b` (extend path by adding edge weight)
- `zero = +∞` (no path has infinite cost)
- `one = 0` (empty path has zero cost)

### Public API

#### Import

```python
from py3plex.dsl import S, L
from py3plex.algebra import (
    get_semiring,
    list_semirings,
    WeightLiftSpec,
)
```

#### Built-in Semirings

Available via `get_semiring(name)` or `list_semirings()`:

| Name | Add (⊕) | Mul (⊗) | Zero | One | Use Case |
|------|---------|---------|------|-----|----------|
| `boolean` | OR | AND | False | True | Reachability |
| `min_plus` | min | + | +∞ | 0 | Shortest paths |
| `max_plus` | max | + | -∞ | 0 | Longest paths |
| `max_times` | max | * | 0 | 1 | Most reliable paths |

#### S.paths() - Semiring Path Queries

Find best paths using semiring operations:

```python
# Shortest path (min-plus semiring)
result = (
    S.paths()
     .from_node("Alice")
     .to_node("Bob")
     .semiring("min_plus")
     .lift(attr="weight", default=1.0)
     .from_layers(L["social"] + L["work"])
     .crossing_layers(mode="allowed")
     .max_hops(5)
     .witness(True)  # Track path for reconstruction
     .execute(network)
)

# Access results
df = result.to_pandas()  # Columns: node, value, path (if witness=True)
print(df[df['node'] == 'Bob']['value'].iloc[0])  # Shortest distance
print(df[df['node'] == 'Bob']['path'].iloc[0])   # Actual path
```

**Builder Methods**:
- `.from_node(source)`: Set source node
- `.to_node(target)`: Set target node (optional for SSSP)
- `.semiring(name)`: Choose semiring ("min_plus", "boolean", "max_times", etc.)
- `.lift(attr, default, transform)`: Extract edge weights
  - `attr`: Edge attribute name (e.g., "weight", "cost")
  - `default`: Default value if missing
  - `transform`: Optional transformation ("log" or callable)
- `.from_layers(L[...])`: Filter by layers (layer algebra)
- `.crossing_layers(mode, penalty)`: Handle cross-layer edges
  - `mode`: "allowed", "forbidden", "penalty"
  - `penalty`: Additional cost for cross-layer edges
- `.max_hops(n)`: Limit path length
- `.k_best(k)`: Find k best paths (experimental)
- `.witness(True)`: Enable path reconstruction
- `.backend("graph"|"matrix")`: Choose backend (default: "graph")

#### Reachability Example (Boolean Semiring)

```python
# Check which nodes are reachable from a source
result = (
    S.paths()
     .from_node("Alice")
     .semiring("boolean")
     .lift(attr=None, default=True)  # No weights needed
     .execute(network)
)

reachable = result.to_pandas()
print(reachable[reachable['value'] == True]['node'].tolist())
```

#### Most Reliable Path (Max-Times Semiring)

```python
# Find path maximizing product of edge reliabilities
result = (
    S.paths()
     .from_node("Alice")
     .to_node("Bob")
     .semiring("max_times")
     .lift(attr="reliability", default=1.0)
     .execute(network)
)

reliability = result.to_pandas()
print(reliability[reliability['node'] == 'Bob']['value'].iloc[0])
```

#### S.closure() - Transitive Closure

Compute all-pairs relationships:

```python
# Reachability closure (boolean semiring)
result = (
    S.closure()
     .semiring("boolean")
     .from_layers(L["social"])
     .method("auto")  # "floyd_warshall", "iterative", or "auto"
     .execute(network)
)

df = result.to_pandas()  # Columns: source, target, value
reachable_pairs = df[df['value'] == True][['source', 'target']]

# All-pairs shortest paths (min-plus semiring)
result = (
    S.closure()
     .semiring("min_plus")
     .lift(attr="weight", default=1.0)
     .method("floyd_warshall")
     .execute(network)
)

distances = result.to_pandas()
```

### Multilayer Integration

#### Layer Filtering

```python
# Shortest paths only within "social" layer
result = (
    S.paths()
     .from_node("Alice")
     .semiring("min_plus")
     .lift(attr="weight", default=1.0)
     .from_layers(L["social"])  # Single layer
     .execute(network)
)

# Paths across social OR work layers
result = (
    S.paths()
     .from_node("Alice")
     .semiring("min_plus")
     .from_layers(L["social"] + L["work"])  # Union
     .execute(network)
)
```

#### Cross-Layer Edge Handling

```python
# Allow cross-layer edges
result = (
    S.paths()
     .from_node("Alice")
     .semiring("min_plus")
     .crossing_layers(mode="allowed")
     .execute(network)
)

# Forbid cross-layer edges (intralayer paths only)
result = (
    S.paths()
     .from_node("Alice")
     .crossing_layers(mode="forbidden")
     .execute(network)
)

# Penalize cross-layer edges (+10 cost)
result = (
    S.paths()
     .from_node("Alice")
     .crossing_layers(mode="penalty", penalty=10.0)
     .execute(network)
)
```

#### Per-Layer Semirings (Advanced)

```python
# Different semirings for different layers
result = (
    S.paths()
     .from_node("Alice")
     .semiring({
         "social": "min_plus",
         "work": "max_times",
     })
     .execute(network)
)
# Note: Per-layer semiring combination is experimental
```

### Provenance and Metadata

All semiring queries include comprehensive provenance:

```python
result = S.paths().from_node("Alice").semiring("min_plus").execute(network)

prov = result.meta['provenance']['algebra']

# Semiring info
print(prov['semiring']['name'])           # "min_plus"
print(prov['semiring']['properties'])     # {idempotent_add: True, ...}

# Weight lifting
print(prov['lift']['attr'])               # "weight"
print(prov['lift']['default'])            # 1.0

# Problem specification
print(prov['problem']['kind'])            # "paths"
print(prov['problem']['source'])          # "Alice"
print(prov['problem']['max_hops'])        # None or value

# Multilayer config
print(prov['multilayer']['layers_included'])        # ["social", "work"]
print(prov['multilayer']['crossing_layers_mode'])   # "allowed"

# Backend and algorithm
print(prov['backend']['name'])            # "graph"
print(prov['backend']['algorithm'])       # "dijkstra" or "bellman_ford"

# Performance
print(prov['performance']['total_time'])  # Execution time
print(prov['performance']['iterations'])  # Algorithm iterations

# Determinism
print(prov['determinism']['converged'])   # True/False
print(prov['determinism']['stable_ordering'])  # True
```

### Determinism and Performance

#### Algorithm Selection

The system automatically chooses the best algorithm based on semiring properties:

- **Dijkstra-like**: For idempotent+monotone semirings (min_plus, max_times)
  - O(E log V) with priority queue
  - Optimal for non-negative weights
- **Bellman-Ford**: For general semirings
  - O(V·E) iterations
  - Handles negative weights, detects convergence

Override with `.backend("graph")` or force algorithm selection via internal parameters.

#### Determinism Guarantees

- Node/edge iteration in stable order (sorted layer names, sorted node IDs)
- Tie-breaking uses semiring.better() or lexicographic node ID
- Parallel execution (via UQ) uses deterministic seed spawning
- Provenance includes determinism metadata

#### Performance Notes

- **Small graphs (<100 nodes)**: Floyd-Warshall for closure (O(n³))
- **Large graphs**: Iterative SSSP (O(n·algorithm_cost))
- **Sparse graphs**: Graph backend is efficient
- **Dense graphs**: Matrix backend (future) may be faster

### Backward Compatibility

The existing `P.shortest()` builder is powered by the semiring engine internally:

```python
# Equivalent calls:
result1 = P.shortest("Alice", "Bob").execute(network)

result2 = (
    S.paths()
     .from_node("Alice")
     .to_node("Bob")
     .semiring("min_plus")
     .lift(attr="weight", default=1.0)
     .execute(network)
)
# result1 uses semiring engine under the hood (future integration)
```

### Configuration

Default backend and semiring settings can be configured:

```python
from py3plex import config

# Future: config.set("algebra.default_backend", "graph")
# Future: config.set("algebra.default_semiring", "min_plus")
```

Current defaults:
- Backend: "graph"
- Semiring: "min_plus" for paths, "boolean" for closure

### Implementation Details

**Location**: `py3plex/algebra/`
- `semiring.py`: Semiring protocol and built-ins
- `registry.py`: Semiring registry
- `lift.py`: Weight lifting specifications
- `paths.py`: Generic SSSP/APSP solvers
- `closure.py`: Kleene star / transitive closure
- `backend.py`: Backend dispatch (graph/matrix)
- `witness.py`: Path witness tracking
- `fixed_point.py`: Fixed-point iteration engine

**DSL Integration**: `py3plex/dsl/`
- `ast.py`: Semiring AST nodes (SemiringPathStmt, SemiringClosureStmt, etc.)
- `builder.py`: S builder classes
- `executor_semiring.py`: Executor for semiring queries

### Advanced: Custom Semirings

Register custom semirings for domain-specific problems:

```python
from py3plex.algebra import register_semiring
from dataclasses import dataclass

@dataclass
class FuzzySemiring:
    name: str = "fuzzy"
    
    def add(self, a, b):
        return max(a, b)  # max for fuzzy union
    
    def mul(self, a, b):
        return min(a, b)  # min for fuzzy intersection
    
    def zero(self):
        return 0.0
    
    def one(self):
        return 1.0
    
    def better(self, a, b):
        return a > b
    
    @property
    def props(self):
        return {
            "commutative_add": True,
            "idempotent_add": True,
            "monotone": True,
        }

# Register
register_semiring("fuzzy", FuzzySemiring(), overwrite=False)

# Use
result = (
    S.paths()
     .from_node("Alice")
     .semiring("fuzzy")
     .lift(attr="membership", default=1.0)
     .execute(network)
)
```

---

## Version Information

```python
import py3plex

print(py3plex.__version__)      # Current version: "1.1.0"
```

**Version History:**
- **1.1.0** (Current): DSL v2, Dynamics, Uncertainty, Temporal networks, Null models
- **1.0.0**: Initial stable release with DSL v1, pipelines, CLI
- **0.96**: Pre-release version

---

## File Locations

- **Core Modules:**
  - `py3plex/core/multinet.py` - Main multi_layer_network class
  - `py3plex/core/temporal_multinet.py` - Temporal multilayer networks
  - `py3plex/dsl/` - DSL v2 implementation (builder API, AST, executor)
  - `py3plex/dsl_legacy.py` - Legacy string-based DSL (backward compatibility)
  - `py3plex/graph_ops.py` - Dplyr-style chainable API
  - `py3plex/pipeline.py` - Sklearn-style pipeline
  - `py3plex/workflows.py` - Config-driven workflows

- **Advanced Features:**
  - `py3plex/dynamics/` - Dynamics simulations (SIS, SIR, RandomWalk, custom)
  - `py3plex/uncertainty/` - Uncertainty quantification (StatSeries, bootstrap, null models)
  - `py3plex/temporal_utils.py` - Temporal network utilities
  - `py3plex/nullmodels/` - Null model implementations

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
  - `py3plex/algorithms/` - Network algorithms
    - `centrality/` - Centrality measures
    - `community_detection/` - Community detection algorithms
    - `temporal/` - Temporal network algorithms
    - `general/` - General graph algorithms

- **Visualization:**
  - `py3plex/visualization/` - Visualization tools and layouts

- **Documentation:**
  - `docfiles/user_guide/dsl.rst` - DSL documentation
  - `docfiles/r_interop.rst` - R interoperability guide
  - `AGENTS.md` - AI agent documentation (this file)
  - `README.md` - Quick start and flagship example

- **Examples:**
  - `examples/getting_started/` - Getting started tutorials
  - `examples/network_analysis/` - Network analysis examples
  - `examples/pipelines/` - Pipeline examples
  - `examples/workflows/` - Workflow examples
  - `examples/visualization/` - Visualization examples
  - `examples/dynamics/` - Dynamics simulation examples
  - `examples/uncertainty/` - Uncertainty quantification examples
  - `examples/temporal/` - Temporal network examples

- **Tests:**
  - `tests/test_dsl.py` - DSL tests
  - `tests/test_graph_ops.py` - Graph operations tests
  - `tests/test_pipeline.py` - Pipeline tests
  - `tests/test_ergonomics.py` - Ergonomics tests
  - `tests/test_cli.py` - CLI tests
  - `tests/test_plugin_system.py` - Plugin system tests
  - `tests/test_workflows.py` - Workflow tests
  - `tests/test_dynamics.py` - Dynamics tests
  - `tests/test_uncertainty.py` - Uncertainty tests
  - `tests/test_temporal.py` - Temporal network tests

---

## API-Specific Patterns and Best Practices

### Multi_layer_network API

**Node and Edge Addition:**
- The API uses `add_nodes()` and `add_edges()` (plural) - the `multi_layer_network` class doesn't expose singular forms
- Use `add_edges([...])` with list of dicts, NOT individual edge additions
- When serializing to JSON format with `to_json()`, the output uses `'edges'` key, not `'links'`
- Method signature: `add_edges([{'source': ..., 'target': ..., 'source_type': ..., 'target_type': ...}])`

**Example:**
```python
# Correct
net.add_edges([
    {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1'},
    {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1'},
])

# Incorrect - singular form doesn't exist
# net.add_edge('A', 'B', 'layer1', 'layer1')  # Don't do this!
```

---

### DSL Architecture Patterns

**DSL v2 vs Legacy:**
- **DSL v2:** Modern builder API in `py3plex/dsl/` (preferred) - use Q, L, UQ builders
- **Legacy DSL:** String-based parsing in `py3plex/dsl_legacy.py` (backward compatibility)
- Use `Q.nodes()` for builder API, `execute_query()` for legacy string queries
- DSL supports autocompute of centrality metrics - set `autocompute=False` to disable

**Layer Selection:**
- Canonical: `FROM layer="name"` or `Q.from_layers(L["name"])`
- Backward compat: `WHERE layer="name"`

**Edge Grouping and Coverage:**
- Use `per_layer()` for node queries to group by layer
- Use `per_layer_pair()` for edge queries to group by layer pairs
- Edge grouping groups by (src_layer, dst_layer) pairs
- Coverage filtering works for both nodes and edges: `coverage(mode="at_least", k=2)`
- QueryResult.meta["grouping"] contains structured grouping metadata
- Use `result.group_summary()` to get DataFrame summary of groups

**Temporal Extensions:**
- DSL supports temporal queries via `.window()` builder method
- Temporal filters: `t__between`, `t__gte`, `t__lte`, `t__gt`, `t__lt` in `where()` clause
- WindowSpec AST node represents temporal query specifications

**Example:**
```python
# DSL v2 with layer algebra
result = (
    Q.nodes()
     .from_layers(L["social"] + L["work"])
     .where(degree__gt=5)
     .per_layer()
        .compute("betweenness_centrality")
        .top_k(10, "betweenness_centrality")
     .end_grouping()
     .coverage(mode="at_least", k=2)
     .execute(net)
)

# Temporal query
result = (
    Q.edges()
     .where(t__between=(100.0, 200.0))
     .from_layers(L["social"])
     .execute(temporal_net)
)
```

---

### Error Handling Best Practices

Always use domain-specific exceptions:

```python
from py3plex.exceptions import (
    Py3plexIOError,           # For I/O errors
    Py3plexException,         # For general errors
    NetworkConstructionError, # For network construction failures
    ParsingError,             # For input parsing failures
)

# For I/O errors
try:
    net.load_network("file.csv")
except Py3plexIOError as e:
    print(f"Failed to read file: {e}")

# For general errors
try:
    result = execute_query(net, query)
except Py3plexException as e:
    print(f"Query failed: {e}")
```

**Never use generic exceptions for domain-specific errors:**
- Use `Py3plexIOError` instead of `FileNotFoundError` for I/O
- Use `NetworkConstructionError` instead of `ValueError` for construction errors

---

## Common Pitfalls and Solutions

### 1. NetworkX MultiGraph Limitations

**Problem:** NetworkX's `clustering()` doesn't support MultiGraph.

**Solution:** Convert to simple Graph first by merging parallel edges.

```python
import networkx as nx

# Wrong - will fail on MultiGraph
# clustering = nx.clustering(net.core_network)

# Correct - convert to simple graph first
simple_graph = nx.Graph(net.core_network)
clustering = nx.clustering(simple_graph)
```

---

### 2. Forward References in DSL

**Problem:** Type hints for classes defined later in the same file cause NameError.

**Solution:** Use string type hints for forward references.

```python
# Correct
def dynamics(self) -> "DynamicsBuilder":
    return DynamicsBuilder()

# Wrong - causes NameError
# def dynamics(self) -> DynamicsBuilder:  # DynamicsBuilder not defined yet
```

---

### 3. DSL Builder Method Chaining

**Problem:** Forgetting to call `.execute()` returns builder object, not results.

**Solution:** Always end query chains with `.execute(network)`.

```python
# Wrong - returns QueryBuilder, not results
result = Q.nodes().where(degree__gt=5)

# Correct - returns QueryResult
result = Q.nodes().where(degree__gt=5).execute(network)
```

---

### 4. Uncertainty Context Scope

**Problem:** Uncertainty context doesn't affect code outside the `with` block.

**Solution:** Ensure all uncertainty-enabled code is inside the context manager.

```python
from py3plex.uncertainty import uncertainty_enabled

# Wrong - pagerank computed outside context, no uncertainty
result = multilayer_pagerank(network)
with uncertainty_enabled(n_runs=50):
    pass

# Correct - all computations inside context
with uncertainty_enabled(n_runs=50):
    result = multilayer_pagerank(network)
    print(f"Std: {result.std}")
```

---

### 5. Temporal Edge Attributes

**Problem:** Mixing `t` with `t_start`/`t_end` causes confusion.

**Solution:** Use interval form (`t_start`, `t_end`) for consistency, or stick to one convention.

```python
# Preferred - interval form
tnet.add_edge('A', 'B', layer='social', t_start=100.0, t_end=200.0)

# Also valid - point-in-time
tnet.add_edge('A', 'B', layer='social', t=150.0)

# Don't mix both on same edge
```

---

### 6. Null Model Randomization

**Problem:** Forgetting to set random seed makes results non-reproducible.

**Solution:** Always specify `seed` parameter for reproducibility.

```python
# Non-reproducible
null_net = configuration_model(network)

# Reproducible
null_net = configuration_model(network, seed=42)
```

---

### 7. Layer Names with Special Characters

**Problem:** Layer names with spaces or special characters break DSL queries.

**Solution:** Use underscores or quote layer names.

```python
# Wrong - spaces break parsing
# L["social media"]

# Correct - use underscores
L["social_media"]

# Also correct - quote if needed
net.add_nodes([{'source': 'A', 'type': 'social_media'}])
```

---

### 8. Test Dependencies

**Problem:** Some tests require optional dependencies not in core install.

**Solution:** Install test extras or check for missing dependencies.

```bash
# Install test dependencies
pip install py3plex[tests]

# Or install specific extras
pip install py3plex[infomap,algos]
```

**Note:** Tests require `pytest-benchmark` (in `dev` dependencies). Some examples may use `sympy`.

---

### 9. Type Checking Requirements

**Problem:** mypy requires Python 3.9+ while project supports 3.8+.

**Solution:** Use Python 3.9+ for type checking, 3.8+ for runtime.

```bash
# Development with type checking
python3.9 -m mypy py3plex/

# Runtime supports 3.8+
python3.8 -m pytest tests/
```

---

### 10. Excluded Files from Linting

**Problem:** `powerlaw.py` intentionally excluded from linting due to legacy issues.

**Solution:** Don't try to fix linting in excluded files - they work as-is.

**Files excluded from linting:**
- `py3plex/algorithms/statistics/powerlaw.py`
- `examples/` directory (intentional)

---

## Security Guidelines

1. **Input Validation:** Always validate file paths and network data before processing
2. **No Arbitrary Code Execution:** Don't use `eval()` or `exec()` on user input
3. **File Operations:** Use safe file operations with proper error handling
4. **Dependencies:** Check new dependencies for known vulnerabilities with `gh-advisory-database` tool
5. **Domain Exceptions:** Use `Py3plexIOError` and related exceptions, never expose raw system errors to users

**Example of secure file loading:**
```python
from py3plex.exceptions import Py3plexIOError
from py3plex.validation import validate_file_exists
import os

def safe_load_network(path: str):
    # Validate input
    if not path or '..' in path:
        raise Py3plexIOError("Invalid file path")
    
    # Check file exists
    validate_file_exists(path)
    
    # Load with error handling
    try:
        net = multinet.multi_layer_network()
        net.load_network(path, input_type="edgelist")
        return net
    except Exception as e:
        raise Py3plexIOError(f"Failed to load network: {e}")
```

---

## Testing Strategy

**Test Organization:**
- **Unit Tests:** Fast, isolated tests in `tests/test_*.py`
- **Property Tests:** Hypothesis-based tests marked with `@pytest.mark.property`
- **Integration Tests:** Multi-component tests marked with `@pytest.mark.integration`
- **Slow Tests:** Marked with `@pytest.mark.slow` - skip during development

**Running Tests:**
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_dsl.py

# Run with coverage
pytest tests/ --cov=py3plex

# Skip slow tests
pytest tests/ -m "not slow"

# Run only property tests
pytest tests/ -m property

# Run targeted test
pytest tests/test_dsl.py -k "test_specific_function"
```

**Test Markers:**
- `@pytest.mark.property` - Property-based tests (Hypothesis)
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Potentially slow tests (>1 second)
- `@pytest.mark.unit` - Fast unit tests

---

## Performance Considerations

1. **Large Networks:** Consider memory usage for networks with >10k nodes
2. **Centrality Computation:** Betweenness/closeness are O(n³) for large networks
3. **DSL Autocompute:** Disable with `autocompute=False` if metrics are pre-computed
4. **Uncertainty Sampling:** Start with n_runs=10-20 for development, increase for production
5. **Temporal Snapshots:** Cache snapshots if querying same time range repeatedly
6. **Null Models:** Generate in parallel when possible using multiprocessing

**Benchmarking:**
```bash
# Run benchmarks
pytest benchmarks/ --benchmark-only

# Compare against baseline
pytest benchmarks/ --benchmark-compare
```

**Profiling:**
```python
from py3plex.profiling import profile_performance, timed_section

@profile_performance
def my_analysis(network):
    # Your code here
    pass

with timed_section("community_detection"):
    communities = detect_communities(network)
```

---

## References and Learning Resources

- **README.md:** Quick start with flagship biological network example
- **AGENTS.md:** Comprehensive AI agent documentation (this file)
- **docfiles/:** Detailed documentation source files
- **examples/:** 50+ working examples demonstrating all features
- **pyproject.toml:** All dependencies, build config, and tool settings
- **Technical Book:** `docs/py3plex_book.pdf` - 106-page handbook

**Key Examples to Study:**
- `examples/getting_started/quickstart.py` - Basic usage
- `examples/network_analysis/dsl_queries.py` - DSL examples
- `examples/uncertainty/uncertainty_quantification.py` - UQ examples
- `examples/dynamics/sir_simulation.py` - Dynamics examples
- `examples/temporal/temporal_analysis.py` - Temporal networks

---

## Contributing Guidelines

When adding new features:

1. **Minimal Changes:** Make the smallest possible change to achieve the goal
2. **Type Hints:** Add type hints for all public functions
3. **Docstrings:** Use Google-style docstrings
4. **Tests:** Add tests to `tests/` for new features
5. **Documentation:** Update AGENTS.md and relevant docfiles
6. **Backward Compatibility:** Never break existing APIs without deprecation
7. **Domain Exceptions:** Use exceptions from `py3plex.exceptions`
8. **Dependencies:** Check with `gh-advisory-database` before adding new dependencies

**Code Style:**
```bash
# Format code
black py3plex/

# Lint
ruff check py3plex/

# Type check
mypy py3plex/
```

---
