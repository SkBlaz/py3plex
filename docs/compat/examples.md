# Cross-Compatibility Examples

Practical recipes for common conversion scenarios.

## Example 1: Basic NetworkX Roundtrip

Convert a py3plex graph to NetworkX and back:

```python
from py3plex.compat import convert
from py3plex.io.schema import MultiLayerGraph, Node, Layer, Edge

# Create py3plex graph
graph = MultiLayerGraph(directed=False)
graph.add_layer(Layer(id="social"))

for name in ["Alice", "Bob", "Charlie"]:
    graph.add_node(Node(id=name, attributes={"age": 30}))

graph.add_edge(Edge(src="Alice", dst="Bob", 
                   src_layer="social", dst_layer="social",
                   attributes={"weight": 0.8}))

# Convert to NetworkX
nx_graph = convert(graph, "networkx")
print(f"NetworkX: {nx_graph.number_of_nodes()} nodes, {nx_graph.number_of_edges()} edges")

# Use NetworkX algorithms
import networkx as nx
centrality = nx.betweenness_centrality(nx_graph)
print(f"Betweenness centrality: {centrality}")

# Convert back
restored = convert(nx_graph, "py3plex")
print(f"Restored: {len(restored.nodes)} nodes")
```

## Example 2: SciPy Sparse with Sidecar

Convert to sparse matrix while preserving attributes:

```python
from py3plex.compat import convert
import scipy.sparse.linalg

# Convert to sparse matrix with sidecar
matrix = convert(
    graph, 
    "scipy_sparse", 
    strict=False,
    sidecar="graph_bundle",
    format="csr"
)

# Compute eigenvalues using SciPy
eigenvalues, eigenvectors = scipy.sparse.linalg.eigs(matrix, k=5)
print(f"Top 5 eigenvalues: {eigenvalues}")

# Restore graph with all attributes
restored_graph = convert(
    matrix,
    "py3plex",
    node_ids=["Alice", "Bob", "Charlie"],
    sidecar="graph_bundle"
)

# Verify attributes preserved
node = next(n for n in restored_graph.nodes if n.id == "Alice")
print(f"Alice's age: {node.attributes.get('age')}")
```

## Example 3: Handling Multigraphs

Work with parallel edges:

```python
from py3plex.compat import convert, to_ir
from py3plex.io.schema import MultiLayerGraph, Node, Layer, Edge

# Create multigraph with parallel edges
graph = MultiLayerGraph(directed=True)
graph.add_layer(Layer(id="L1"))
graph.add_node(Node(id="A"))
graph.add_node(Node(id="B"))

# Multiple edges between same nodes
graph.add_edge(Edge(src="A", dst="B", src_layer="L1", dst_layer="L1",
                   attributes={"type": "email", "weight": 1.0}))
graph.add_edge(Edge(src="A", dst="B", src_layer="L1", dst_layer="L1",
                   attributes={"type": "call", "weight": 2.0}))

# Convert to NetworkX (preserves parallel edges)
nx_graph = convert(graph, "networkx")
print(f"NetworkX MultiDiGraph with {nx_graph.number_of_edges()} edges")

# Get all edges between A and B
import networkx as nx
edges = list(nx_graph.edges(keys=True, data=True))
for u, v, key, data in edges:
    if u == "A" and v == "B":
        print(f"Edge {key}: type={data.get('type')}, weight={data.get('weight')}")
```

## Example 4: Schema Validation

Validate graph schema before conversion:

```python
from py3plex.compat import to_ir
from py3plex.compat.schema import infer_schema, validate_against_schema, GraphSchema

# Convert to IR
ir = to_ir(graph)

# Infer schema
schema = infer_schema(ir)
print(f"Node ID type: {schema.node_id_type}")
print(f"Directed: {schema.directed}")
print(f"Multi: {schema.multi}")
print(f"Node attributes: {schema.node_attr_types}")
print(f"Edge attributes: {schema.edge_attr_types}")

# Check for unsafe types
if schema.unsafe_types:
    print(f"Warning: Unsafe types detected: {schema.unsafe_types}")
    print("These may not serialize cleanly")

# Validate against expected schema
expected = GraphSchema(
    directed=False,
    multi=False,
    node_id_type="str",
    edge_id_required=False
)

report = validate_against_schema(ir, expected)
if not report.valid:
    print("Validation failed:")
    for error in report.errors:
        print(f"  - {error}")
else:
    print("✓ Schema validation passed")
    if report.warnings:
        print("Warnings:")
        for warning in report.warnings:
            print(f"  - {warning}")
```

## Example 5: Custom Node IDs with SciPy

Preserve custom node IDs when converting to/from sparse matrices:

```python
from py3plex.compat import convert

# Graph with string node IDs
graph = create_graph_with_string_ids()

# Convert to sparse matrix with sidecar
matrix = convert(graph, "scipy_sparse", strict=False, sidecar="node_ids")

# Matrix uses integer indices 0, 1, 2, ...
print(f"Matrix shape: {matrix.shape}")

# Restore with original node IDs
restored = convert(matrix, "py3plex", sidecar="node_ids")

# Verify node IDs preserved
for node in restored.nodes:
    print(f"Node ID: {node.id} (type: {type(node.id).__name__})")
```

## Example 6: Working with IR Directly

Use Intermediate Representation for custom processing:

```python
from py3plex.compat.ir import to_ir, from_ir
import pandas as pd

# Convert to IR
ir = to_ir(graph)

# Inspect structure
print("Node table:")
print(pd.DataFrame({
    'node_id': ir.nodes.node_id,
    'node_order': ir.nodes.node_order
}))

print("\nEdge table:")
print(pd.DataFrame({
    'edge_id': ir.edges.edge_id,
    'src': ir.edges.src,
    'dst': ir.edges.dst,
    'edge_order': ir.edges.edge_order
}))

# Modify IR (e.g., filter nodes)
filtered_node_ids = ["Alice", "Bob"]
filtered_nodes = NodeTable(
    node_id=filtered_node_ids,
    node_order=[0, 1],
    attrs=ir.nodes.attrs.iloc[:2] if ir.nodes.attrs is not None else None
)

# Filter edges
filtered_edges = EdgeTable(
    edge_id=[e for i, e in enumerate(ir.edges.edge_id) 
             if ir.edges.src[i] in filtered_node_ids 
             and ir.edges.dst[i] in filtered_node_ids],
    src=[s for s in ir.edges.src if s in filtered_node_ids],
    dst=[d for d in ir.edges.dst if d in filtered_node_ids],
    edge_order=list(range(len([s for s in ir.edges.src if s in filtered_node_ids]))),
    attrs=None
)

# Create new IR
from py3plex.compat.ir import GraphIR, GraphMeta
filtered_ir = GraphIR(
    nodes=filtered_nodes,
    edges=filtered_edges,
    meta=ir.meta
)

# Convert back to graph
filtered_graph = from_ir(filtered_ir)
print(f"\nFiltered graph: {len(filtered_graph.nodes)} nodes")
```

## Example 7: Sidecar Bundle Management

Work with sidecar bundles directly:

```python
from py3plex.compat.sidecar import export_sidecar, import_sidecar
from py3plex.compat.ir import to_ir
from pathlib import Path

# Export to sidecar
ir = to_ir(graph)
export_sidecar(ir, "my_graph_bundle", format="json+parquet")

# Inspect bundle contents
bundle_path = Path("my_graph_bundle")
print("Bundle contents:")
for item in bundle_path.iterdir():
    print(f"  - {item.name} ({item.stat().st_size} bytes)")

# Import from sidecar
restored_ir = import_sidecar("my_graph_bundle")
print(f"Restored: {len(restored_ir.nodes.node_id)} nodes, {len(restored_ir.edges.edge_id)} edges")

# Clean up
import shutil
shutil.rmtree("my_graph_bundle")
```

## Example 8: NetworkX to igraph

Convert between external formats via py3plex:

```python
import networkx as nx
from py3plex.compat import convert

# Create NetworkX graph
G = nx.karate_club_graph()
print(f"NetworkX: {G.number_of_nodes()} nodes")

# Convert NetworkX → py3plex → igraph
try:
    # Convert to py3plex first
    py3_graph = convert(G, "py3plex")
    
    # Then to igraph
    ig_graph = convert(py3_graph, "igraph")
    
    # Use igraph algorithms
    communities = ig_graph.community_multilevel()
    print(f"Found {len(communities)} communities")
    
    # Convert back to NetworkX
    G2 = convert(ig_graph, "networkx")
    print(f"Restored to NetworkX: {G2.number_of_nodes()} nodes")
    
except ConversionNotSupportedError as e:
    print(f"Conversion failed: {e}")
```

## Example 9: Batch Conversion

Convert multiple graphs efficiently:

```python
from py3plex.compat import convert

graphs = load_multiple_graphs()  # Your graph loading function

# Convert all to NetworkX
nx_graphs = []
for i, graph in enumerate(graphs):
    try:
        nx_graph = convert(graph, "networkx")
        nx_graphs.append(nx_graph)
        print(f"✓ Converted graph {i}")
    except Exception as e:
        print(f"✗ Failed to convert graph {i}: {e}")

# Process with NetworkX
import networkx as nx
for i, G in enumerate(nx_graphs):
    density = nx.density(G)
    print(f"Graph {i} density: {density:.3f}")
```

## Example 10: Error Handling

Robust error handling for production use:

```python
from py3plex.compat import convert
from py3plex.compat.exceptions import (
    CompatibilityError,
    SchemaError,
    ConversionNotSupportedError
)

def safe_convert(graph, target, **kwargs):
    """
    Safely convert graph with comprehensive error handling.
    """
    try:
        result = convert(graph, target, **kwargs)
        return result, None
    
    except CompatibilityError as e:
        print(f"Compatibility issue: {e.reason}")
        print("Suggestions:")
        for suggestion in e.suggestions:
            print(f"  - {suggestion}")
        return None, "compatibility"
    
    except ConversionNotSupportedError as e:
        print(f"Conversion not supported: {e}")
        return None, "not_supported"
    
    except SchemaError as e:
        print(f"Schema error in field '{e.field}': {e}")
        return None, "schema"
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None, "unknown"

# Use in production
result, error_type = safe_convert(graph, "scipy_sparse", strict=True)
if result is not None:
    print("✓ Conversion successful")
    # Proceed with result
else:
    print(f"✗ Conversion failed: {error_type}")
    # Handle error appropriately
```

## Tips and Best Practices

### Tip 1: Check Dependencies First

```python
# Check if optional converter is available
try:
    import igraph
    igraph_available = True
except ImportError:
    igraph_available = False

if igraph_available:
    ig_graph = convert(graph, "igraph")
else:
    print("Using NetworkX fallback")
    nx_graph = convert(graph, "networkx")
```

### Tip 2: Use Sidecar for Exploratory Work

```python
# During exploration, use compat mode
matrix = convert(graph, "scipy_sparse", strict=False, sidecar="temp")

# Explore with SciPy
# ...

# Later, restore if needed
if need_attributes:
    restored = convert(matrix, "py3plex", sidecar="temp")
```

### Tip 3: Validate Before Expensive Operations

```python
from py3plex.compat.schema import infer_schema

schema = infer_schema(to_ir(graph))

# Check if conversion will succeed
if schema.multi and target == "scipy_sparse":
    print("Warning: Target doesn't support multigraphs")
    # Take appropriate action
```

## Common Pitfalls

### Pitfall 1: Forgetting Sidecar Path

```python
# ❌ Wrong: No sidecar in compat mode
matrix = convert(graph, "scipy_sparse", strict=False)
# Attributes are lost!

# ✓ Correct: Provide sidecar path
matrix = convert(graph, "scipy_sparse", strict=False, sidecar="data")
```

### Pitfall 2: Assuming Node ID Preservation

```python
# ❌ Wrong: SciPy uses integer indices
matrix = convert(graph, "scipy_sparse", strict=False)
# matrix[0, 1] - which nodes are these?

# ✓ Correct: Use sidecar to preserve IDs
matrix = convert(graph, "scipy_sparse", strict=False, sidecar="ids")
restored = convert(matrix, "py3plex", sidecar="ids")
```

### Pitfall 3: Ignoring Validation Warnings

```python
# ❌ Wrong: Ignore schema warnings
schema = infer_schema(ir)
# schema.unsafe_types = ['object'] - ignored!

# ✓ Correct: Handle warnings
if schema.unsafe_types:
    print("Warning: Complex types may not survive roundtrip")
    # Simplify attributes or use appropriate format
```
