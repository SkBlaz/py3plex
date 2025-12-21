# Conversion Layer Design Document

## Current State Analysis

### Existing Graph Representations

py3plex uses two main graph representations:

1. **MultiLayerGraph** (`py3plex.io.schema.MultiLayerGraph`)
   - Dataclass-based representation
   - Explicit Node, Edge, and Layer objects
   - Strong typing with validation
   - Already supports JSON serialization
   - Located in: `py3plex/io/schema.py`

2. **multi_layer_network** (`py3plex.core.multinet.multi_layer_network`)
   - NetworkX-based representation
   - Wraps NetworkX MultiGraph/MultiDiGraph
   - Used for algorithms and computations
   - Located in: `py3plex/core/multinet.py`

### Existing Conversion Utilities

Found in `py3plex/io/converters.py`:
- `to_networkx()`: Converts MultiLayerGraph to NetworkX with projection modes
- `from_networkx()`: Converts NetworkX to MultiLayerGraph
- Supports union/intersection/multiplex projection modes

NetworkX compatibility layer in `py3plex/core/nx_compat.py`:
- Version-agnostic NetworkX operations
- Scipy sparse matrix conversion helpers

### Current Gaps

1. **No Lossless Guarantee**: Existing converters may lose information
2. **No Schema Validation**: No explicit validation of conversion compatibility
3. **Limited Format Support**: Only NetworkX and basic scipy support
4. **No Deterministic Ordering**: Node/edge order not guaranteed in roundtrips
5. **No Sidecar System**: No mechanism to preserve data when target is lossy
6. **No Unified Interface**: Different converters have different APIs

## Design Goals

The new compatibility layer addresses these gaps with:

1. **Lossless Roundtrips**: Full preservation of structure, semantics, and attributes
2. **Explicit Failure Modes**: Clear errors in strict mode, sidecar fallback in compat mode
3. **Intermediate Representation (IR)**: Canonical format for all conversions
4. **Schema Validation**: Type checking and compatibility verification
5. **Deterministic Ordering**: Stable node/edge ordering for reproducibility
6. **Sidecar Bundles**: Preserve data when target format is lossy
7. **Unified API**: Single `convert()` entry point for all conversions

## Architecture

### Layer Structure

```
py3plex/compat/
├── __init__.py              # Public API exports
├── exceptions.py            # Custom exception types
├── ir.py                    # Intermediate Representation
├── schema.py                # Schema validation
├── convert.py               # Main conversion entry point
├── sidecar.py               # Sidecar bundle I/O
└── converters/
    ├── __init__.py
    ├── networkx_converter.py    # NetworkX (required)
    ├── scipy_converter.py       # SciPy sparse (required)
    ├── igraph_converter.py      # igraph (optional)
    ├── pyg_converter.py         # PyTorch Geometric (optional)
    └── dgl_converter.py         # DGL (optional)
```

### Intermediate Representation (IR)

All conversions flow through a canonical IR:

```python
@dataclass
class GraphIR:
    nodes: NodeTable    # node_id, node_order, attrs, layer
    edges: EdgeTable    # edge_id, src, dst, edge_order, attrs, src_layer, dst_layer
    meta: GraphMeta     # directed, multi, name, global_attrs, layers
```

Benefits:
- Converters only need to implement to/from IR
- Consistent semantics across all formats
- Single source of truth for validation
- Enables n-to-n conversions with 2n implementations

### Conversion Modes

**Strict Mode** (`strict=True`):
- Raises `CompatibilityError` if target cannot represent all data
- Ensures no silent data loss
- Default for production use

**Compatibility Mode** (`strict=False`):
- Uses sidecar bundles to preserve non-representable data
- Warns about fallback mechanisms
- For exploratory/interactive use

### Sidecar Bundle Format

When target format is lossy (e.g., scipy sparse matrix can't store node attributes):

```
my_graph/
├── meta.json           # GraphMeta + schema version
├── nodes.parquet       # NodeTable (or nodes.csv fallback)
└── edges.parquet       # EdgeTable (or edges.csv fallback)
```

Roundtrip: `graph → target + sidecar → graph` preserves everything

## Semantic Preservation

### Graph Properties

| Property | IR Field | NetworkX | SciPy | igraph |
|----------|----------|----------|-------|--------|
| Directed | meta.directed | ✓ | ✓ | ✓ |
| Multigraph | meta.multi | ✓ | ✗ (sidecar) | ✗ (merge) |
| Self-loops | Normal edges | ✓ | ✓ | ✓ |
| Node IDs | nodes.node_id | ✓ | ✗ (sidecar) | ✓ (attr) |
| Edge IDs | edges.edge_id | ✓ (key) | ✗ (sidecar) | ✓ (attr) |

### Attribute Preservation

- **Node attributes**: Preserved in all formats except SciPy (→ sidecar)
- **Edge attributes**: Preserved in all formats except SciPy matrix values
- **Graph attributes**: Preserved in NetworkX/igraph graph metadata
- **Missing values**: Represented as NaN in pandas, None in dicts

### Type Coercion

| Python Type | Pandas dtype | NetworkX | SciPy | Notes |
|-------------|--------------|----------|-------|-------|
| int | int64 | ✓ | ✓ | Native |
| float | float64 | ✓ | ✓ | Native |
| str | object | ✓ | ✗ | Sidecar for SciPy |
| bool | bool | ✓ | ✗ | Sidecar for SciPy |
| list | object | ✓ | ✗ | Unsafe (warning) |
| dict | object | ✓ | ✗ | Unsafe (warning) |

"Unsafe types" (object, complex, datetime) trigger warnings.

## Deterministic Ordering

To ensure reproducibility:

1. **Node order**: `nodes.node_order` field stores original index
2. **Edge order**: `edges.edge_order` field stores original index
3. **Sorting**: IR provides `sort_nodes()` and `sort_edges()` methods
4. **Metadata**: Order info preserved in `_py3plex_node_order` attributes

Guarantees:
- `to_ir(from_ir(ir)) == ir` (structure and order)
- Cross-platform reproducibility (no dict ordering issues)
- Deterministic iteration for algorithms

## Error Handling

### CompatibilityError

Raised in strict mode when target cannot represent data:

```python
raise CompatibilityError(
    "Cannot represent multigraph as sparse matrix",
    reason="Sparse matrices cannot represent parallel edges",
    suggestions=[
        "Set strict=False with sidecar path",
        "Aggregate parallel edges before conversion"
    ]
)
```

Clear error message + actionable suggestions.

### SchemaError

Raised when schema validation fails:

```python
raise SchemaError(
    "Node ID type mismatch",
    field="node_id",
    expected="int",
    actual="str"
)
```

Precise field-level errors.

### ConversionNotSupportedError

Raised when optional dependencies are missing:

```python
raise ConversionNotSupportedError(
    "igraph conversion requires python-igraph. "
    "Install with: pip install python-igraph"
)
```

Clear installation instructions.

## Testing Strategy

### Roundtrip Property Tests

Using Hypothesis to generate random graphs:

```python
@given(strategies.multilayer_graph())
def test_networkx_roundtrip(graph):
    ir = to_ir(graph)
    nx_graph = to_networkx_from_ir(ir)
    ir2 = from_networkx_to_ir(nx_graph)
    assert ir_equals(ir, ir2)
```

### Golden Test Graphs

Hand-crafted graphs for edge cases:
- Multi-edges with distinct attributes
- String/tuple node IDs
- Missing attribute values
- Self-loops
- Disconnected components

### Sidecar Roundtrip Tests

Verify lossless preservation:
```python
def test_scipy_with_sidecar(graph):
    matrix = to_scipy(graph, sidecar="bundle")
    restored = from_scipy(matrix, sidecar="bundle")
    assert graphs_equal(graph, restored)
```

## Performance Considerations

### Memory Usage

- IR uses pandas DataFrames (efficient for tabular data)
- Sparse matrices for large graphs (SciPy converter)
- Streaming support for sidecar I/O (parquet format)

### Time Complexity

- `to_ir()`: O(|V| + |E|) (single pass)
- `from_ir()`: O(|V| + |E|) (single pass)
- Converter operations: O(|V| + |E|) (dominated by graph construction)

### Optimization Opportunities

- Lazy evaluation for large graphs
- Chunked I/O for sidecar bundles
- COO → CSR conversion optimization for SciPy

## Future Extensions

### Additional Converters

- **graph-tool**: Property map support for typed attributes
- **CuGraph**: GPU-accelerated graph analytics
- **NetworKit**: High-performance C++ backend

### Enhanced Validation

- JSON Schema validation for sidecar metadata
- Type inference for attribute coercion
- Compatibility matrix for format pairs

### Streaming Support

- Iterator-based node/edge processing
- Chunked sidecar I/O
- Memory-mapped parquet files

### Provenance Tracking

- Record conversion history in metadata
- Schema evolution tracking
- Audit trail for data transformations

## References

- NetworkX documentation: https://networkx.org/
- SciPy sparse matrices: https://docs.scipy.org/doc/scipy/reference/sparse.html
- Apache Arrow/Parquet: https://arrow.apache.org/
- PyTorch Geometric: https://pytorch-geometric.readthedocs.io/
