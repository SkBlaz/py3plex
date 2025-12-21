# Cross-Compatibility Conversion Layer - Overview

## What is Lossless Conversion?

The py3plex compatibility layer provides **lossless** conversion between py3plex multilayer networks and common graph ecosystems. "Lossless" means:

1. **Structure preservation**: Directed/undirected, simple/multigraph, self-loops
2. **Identity preservation**: Node IDs, edge IDs (for multigraphs)
3. **Attribute preservation**: All node, edge, and graph-level metadata
4. **Semantic preservation**: Graph meaning unchanged by conversion

## Quick Start

### Basic Conversion

```python
from py3plex.compat import convert
from py3plex.io.schema import MultiLayerGraph, Node, Layer, Edge

# Create a py3plex graph
graph = MultiLayerGraph(directed=False)
graph.add_layer(Layer(id="social"))
graph.add_node(Node(id="Alice", attributes={"age": 30}))
graph.add_node(Node(id="Bob", attributes={"age": 25}))
graph.add_edge(Edge(
    src="Alice", dst="Bob",
    src_layer="social", dst_layer="social",
    attributes={"weight": 0.8}
))

# Convert to NetworkX
import networkx as nx
nx_graph = convert(graph, "networkx")
print(f"NetworkX graph: {nx_graph.number_of_nodes()} nodes, {nx_graph.number_of_edges()} edges")

# Convert back to py3plex
restored = convert(nx_graph, "py3plex")
print(f"Restored: {len(restored.nodes)} nodes, {len(restored.edges)} edges")
```

### Supported Targets

| Target | Format | Required Packages | Status |
|--------|--------|-------------------|--------|
| `networkx` | NetworkX graph | `networkx` (core dep) | ✓ Full |
| `scipy_sparse` | SciPy sparse matrix | `scipy` (core dep) | ✓ Full |
| `igraph` | igraph Graph | `python-igraph` (optional) | ✓ Full |
| `pyg` | PyTorch Geometric Data | `torch`, `torch-geometric` (optional) | Stub |
| `dgl` | DGL graph | `dgl` (optional) | Stub |

## Conversion Modes

### Strict Mode (Default)

In **strict mode**, conversion fails explicitly if the target format cannot represent all data:

```python
from py3plex.compat import convert
from py3plex.compat.exceptions import CompatibilityError

# Graph with attributes
graph = create_graph_with_attributes()

try:
    # SciPy sparse matrices can't store attributes
    matrix = convert(graph, "scipy_sparse", strict=True)
except CompatibilityError as e:
    print(f"Conversion failed: {e}")
    # Provides clear error + suggestions
```

**Use strict mode when:**
- Production pipelines requiring data integrity
- You need guarantees about information preservation
- Failures should be caught early

### Compatibility Mode

In **compatibility mode**, conversion uses **sidecar bundles** to preserve non-representable data:

```python
# Conversion succeeds, attributes go to sidecar
matrix = convert(graph, "scipy_sparse", strict=False, sidecar="my_graph_bundle")
# matrix contains connectivity, sidecar contains attributes

# Roundtrip restores everything
restored = convert(matrix, "py3plex", sidecar="my_graph_bundle")
# restored has all original attributes
```

**Use compat mode when:**
- Exploratory data analysis
- Target format limitations are expected
- You can manage sidecar bundles alongside data

## Sidecar Bundles

A **sidecar bundle** is a directory containing complete graph information:

```
my_graph/
├── meta.json           # Graph metadata (directed, layers, schema)
├── nodes.parquet       # Node table (IDs, order, attributes)
└── edges.parquet       # Edge table (IDs, endpoints, attributes)
```

### Creating Sidecar Bundles

```python
from py3plex.compat.sidecar import export_sidecar, import_sidecar
from py3plex.compat.ir import to_ir

# Export graph to sidecar
ir = to_ir(graph)
export_sidecar(ir, "my_graph", format="json+parquet")
# Falls back to CSV if pyarrow not installed

# Import from sidecar
restored_ir = import_sidecar("my_graph")
restored_graph = from_ir(restored_ir)
```

### Sidecar Formats

- **json+parquet** (default): Fast, efficient, requires `pyarrow`
- **json+csv**: Fallback, slower, no extra dependencies

## Intermediate Representation (IR)

All conversions flow through a canonical **Intermediate Representation (IR)**:

```python
from py3plex.compat.ir import GraphIR, to_ir, from_ir

# Convert any graph to IR
ir = to_ir(graph)

# IR provides canonical format
print(f"Nodes: {len(ir.nodes.node_id)}")
print(f"Edges: {len(ir.edges.edge_id)}")
print(f"Directed: {ir.meta.directed}")
print(f"Layers: {ir.meta.layers}")

# Convert IR to any supported format
nx_graph = to_networkx_from_ir(ir)
```

**Benefits:**
- Consistent semantics across formats
- Single source for validation
- Enables format-to-format conversion (e.g., NetworkX → igraph)

## Schema Validation

The compatibility layer provides explicit schema validation:

```python
from py3plex.compat.schema import infer_schema, validate_against_schema

# Infer schema from graph
schema = infer_schema(ir)
print(f"Node ID type: {schema.node_id_type}")
print(f"Edge attributes: {schema.edge_attr_types}")
print(f"Unsafe types: {schema.unsafe_types}")

# Validate graph against expected schema
report = validate_against_schema(ir, expected_schema)
if not report.valid:
    print("Validation errors:")
    for error in report.errors:
        print(f"  - {error}")
```

**Schema checks:**
- Node/edge ID types (int, str, mixed)
- Attribute data types
- Directed/undirected, simple/multigraph
- Multilayer structure (layers, layer count)

## Common Patterns

### NetworkX → py3plex

```python
import networkx as nx
from py3plex.compat import convert

# NetworkX graph
G = nx.karate_club_graph()

# Convert to py3plex
py3_graph = convert(G, "py3plex")
```

### py3plex → SciPy Sparse (with attributes)

```python
from py3plex.compat import convert

# Convert with sidecar for attributes
matrix = convert(
    graph, 
    "scipy_sparse", 
    strict=False,
    sidecar="graph_data"
)

# Use matrix for computation
eigenvalues = scipy.sparse.linalg.eigs(matrix, k=5)

# Restore with attributes
restored = convert(matrix, "py3plex", sidecar="graph_data")
```

### py3plex → igraph (optional)

```python
# Requires: pip install python-igraph
from py3plex.compat import convert

try:
    ig_graph = convert(graph, "igraph")
    # Use igraph algorithms
    communities = ig_graph.community_multilevel()
except ConversionNotSupportedError:
    print("Install igraph: pip install python-igraph")
```

## Error Handling

### CompatibilityError

Raised in strict mode when target cannot represent data:

```python
try:
    convert(multigraph, "scipy_sparse", strict=True)
except CompatibilityError as e:
    print(f"Error: {e.reason}")
    print("Suggestions:")
    for suggestion in e.suggestions:
        print(f"  - {suggestion}")
```

### ConversionNotSupportedError

Raised when optional dependencies are missing:

```python
try:
    convert(graph, "igraph")
except ConversionNotSupportedError as e:
    print(e)  # Clear installation instructions
```

### SchemaError

Raised when schema validation fails:

```python
from py3plex.compat.exceptions import SchemaError

try:
    validate_graph_schema(ir, strict_schema)
except SchemaError as e:
    print(f"Field: {e.field}")
    print(f"Expected: {e.expected}")
    print(f"Actual: {e.actual}")
```

## Best Practices

### 1. Use Strict Mode for Production

```python
# Production pipeline
try:
    nx_graph = convert(graph, "networkx", strict=True)
    # Process with NetworkX
except CompatibilityError as e:
    # Log error, alert operators
    raise
```

### 2. Validate Schemas Early

```python
from py3plex.compat.schema import infer_schema

# Check schema before expensive conversion
schema = infer_schema(to_ir(graph))
if "object" in schema.unsafe_types:
    print("Warning: Graph has complex attributes")
```

### 3. Manage Sidecar Bundles

```python
import shutil

# Clean up temporary sidecars
sidecar_path = "temp_conversion"
matrix = convert(graph, "scipy_sparse", strict=False, sidecar=sidecar_path)
# ... use matrix ...
shutil.rmtree(sidecar_path)
```

### 4. Preserve Node IDs

```python
# When converting to formats with integer indices
ir = to_ir(graph)
node_id_list = ir.nodes.node_id  # Save original IDs

# ... conversion ...

# Restore original IDs later
```

## Performance Tips

### Memory-Efficient Conversions

```python
# For large graphs, use sparse formats
matrix = convert(graph, "scipy_sparse", format="csr")
# CSR format is memory-efficient for sparse graphs
```

### Parquet for Large Attributes

```python
# Install pyarrow for faster sidecar I/O
# pip install pyarrow

export_sidecar(ir, "large_graph", format="json+parquet")
# Much faster than CSV for large attribute tables
```

## Limitations

### Current Limitations

1. **PyG/DGL converters**: Stub implementations (contribute welcome!)
2. **Temporal networks**: Not yet supported in IR
3. **Hypergraphs**: IR designed for pairwise edges
4. **Streaming**: No iterator-based conversion yet

### Format-Specific Limitations

- **SciPy sparse**: Cannot represent attributes, multigraphs (use sidecar)
- **igraph**: No true multigraph support (parallel edges merged)
- **NetworkX**: Large graphs may be memory-intensive

## Next Steps

- [Target-Specific Documentation](targets.md) - Detailed notes per format
- [Examples](examples.md) - Cookbook of conversion recipes
- [API Reference](../api/compat.md) - Complete API documentation
