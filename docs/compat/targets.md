# Target-Specific Conversion Notes

This document provides detailed information about what each target format can and cannot represent, along with conversion strategies.

## NetworkX

**Target:** `"networkx"`  
**Package:** `networkx` (core dependency)  
**Status:** ✓ Fully supported

### What NetworkX Can Represent

- ✓ Directed and undirected graphs
- ✓ Multigraphs (parallel edges)
- ✓ Self-loops
- ✓ Node attributes (any Python object)
- ✓ Edge attributes (any Python object)
- ✓ Graph-level attributes
- ✓ Mixed node ID types (int, str, tuple, etc.)

### Conversion Strategy

NetworkX is the most feature-complete target and can represent almost everything py3plex supports.

**Key mappings:**
- py3plex edge IDs → NetworkX multigraph keys
- py3plex layer info → edge attributes `_py3plex_src_layer`, `_py3plex_dst_layer`
- Deterministic ordering → node/edge attributes `_py3plex_*_order`

### Example

```python
from py3plex.compat import convert

# py3plex → NetworkX
nx_graph = convert(py3plex_graph, "networkx")

# NetworkX graph types:
# - MultiDiGraph (directed + multigraph)
# - DiGraph (directed + simple)
# - MultiGraph (undirected + multigraph)
# - Graph (undirected + simple)

# NetworkX → py3plex
restored = convert(nx_graph, "py3plex")
```

### Limitations

- **Memory usage**: NetworkX stores graphs in memory (dict-of-dicts)
- **Performance**: Not optimized for very large graphs (>1M edges)
- **Type safety**: Python objects can be any type (no validation)

---

## SciPy Sparse Matrix

**Target:** `"scipy_sparse"`  
**Package:** `scipy` (core dependency)  
**Status:** ✓ Fully supported (with sidecar)

### What SciPy Sparse Can Represent

- ✓ Directed and undirected graphs (as matrices)
- ✓ Edge weights (matrix values)
- ✗ Multigraphs (parallel edges → sidecar or aggregation)
- ✗ Node IDs (indices only → sidecar)
- ✗ Node attributes → sidecar
- ✗ Edge attributes (except weight) → sidecar

### Conversion Strategy

SciPy sparse is a **lossy format** - use sidecar bundles for lossless roundtrip.

**Strict mode:**
```python
# Fails if graph has attributes or is multigraph
try:
    matrix = convert(graph, "scipy_sparse", strict=True)
except CompatibilityError:
    # Handle error
```

**Compat mode:**
```python
# Succeeds, preserves data in sidecar
matrix = convert(graph, "scipy_sparse", strict=False, sidecar="graph_data")

# Later: restore everything
restored = convert(matrix, "py3plex", sidecar="graph_data")
```

### Sparse Matrix Formats

Specify format with `format` parameter:

- `"csr"` (default): Compressed Sparse Row - fast row access
- `"csc"`: Compressed Sparse Column - fast column access
- `"coo"`: COOrdinate format - fast construction
- `"lil"`: List of Lists - fast incremental construction
- `"dok"`: Dictionary of Keys - fast random access

```python
matrix = convert(graph, "scipy_sparse", format="csr", strict=False)
```

### Edge Weight Extraction

By default, uses `"weight"` attribute:

```python
# Default: uses edge attribute "weight"
matrix = convert(graph, "scipy_sparse", weight="weight", strict=False)

# Use different attribute
matrix = convert(graph, "scipy_sparse", weight="similarity", strict=False)

# Missing weights default to 1.0
```

### Example: Spectral Analysis

```python
import scipy.sparse.linalg

# Convert to sparse matrix
matrix = convert(graph, "scipy_sparse", strict=False, sidecar="temp")

# Compute eigenvalues
eigenvalues, eigenvectors = scipy.sparse.linalg.eigs(matrix, k=10)

# Restore graph with attributes
graph = convert(matrix, "py3plex", sidecar="temp")
```

### Limitations

- **Lossy**: Requires sidecar for full roundtrip
- **Simple graphs only**: Multigraphs must be aggregated or use sidecar
- **Numeric weights**: Matrix values must be numeric (typically float)

---

## igraph

**Target:** `"igraph"`  
**Package:** `python-igraph` (optional: `pip install py3plex[igraph]`)  
**Status:** ✓ Fully supported

### What igraph Can Represent

- ✓ Directed and undirected graphs
- ✗ True multigraphs (parallel edges stored as attributes)
- ✓ Self-loops
- ✓ Node attributes (stored in property maps)
- ✓ Edge attributes (stored in property maps)
- ✓ Graph-level attributes
- ✓ Original node IDs (stored in `_py3plex_id` vertex attribute)

### Conversion Strategy

igraph doesn't support true multigraphs, but can store parallel edge information in attributes.

**Mapping:**
- py3plex node IDs → vertex attribute `_py3plex_id`
- py3plex node order → vertex attribute `_py3plex_order`
- py3plex edge ID → edge attribute `_py3plex_edge_id`
- py3plex layers → edge attributes `_py3plex_src_layer`, `_py3plex_dst_layer`

### Example

```python
try:
    from py3plex.compat import convert
    
    # py3plex → igraph
    ig_graph = convert(graph, "igraph")
    
    # Use igraph algorithms
    communities = ig_graph.community_multilevel()
    betweenness = ig_graph.betweenness()
    
    # igraph → py3plex
    restored = convert(ig_graph, "py3plex")
    
except ConversionNotSupportedError:
    print("Install igraph: pip install python-igraph")
```

### Limitations

- **No true multigraphs**: Parallel edges must be merged or tracked separately
- **Installation**: python-igraph has C dependencies (may require compilation)

---

## PyTorch Geometric (PyG)

**Target:** `"pyg"` or `"torch_geometric"`  
**Package:** `torch`, `torch-geometric` (optional: `pip install py3plex[pyg]`)  
**Status:** ⚠️ Stub implementation

### Planned Features

- ✓ Directed and undirected graphs
- ✓ Node features (as tensors)
- ✓ Edge features (as tensors)
- ✓ Heterogeneous graphs (multilayer support)
- ✗ String node IDs (PyG uses integer indices)

### Current Status

PyG converter is currently a **stub** (raises `NotImplementedError`). Contributions welcome!

### Example (Future)

```python
# Planned API
try:
    pyg_data = convert(graph, "pyg")
    
    # Use PyG for GNN training
    from torch_geometric.nn import GCNConv
    
    model = GCNConv(pyg_data.num_node_features, 64)
    out = model(pyg_data.x, pyg_data.edge_index)
    
except NotImplementedError:
    print("PyG converter not yet implemented")
```

---

## DGL (Deep Graph Library)

**Target:** `"dgl"`  
**Package:** `dgl` (optional: `pip install py3plex[dgl_compat]`)  
**Status:** ⚠️ Stub implementation

### Planned Features

- ✓ Directed and undirected graphs
- ✓ Node features (as tensors)
- ✓ Edge features (as tensors)
- ✓ Heterogeneous graphs (multilayer support)
- ✗ String node IDs (DGL uses integer indices)

### Current Status

DGL converter is currently a **stub** (raises `NotImplementedError`). Contributions welcome!

### Example (Future)

```python
# Planned API
try:
    dgl_graph = convert(graph, "dgl")
    
    # Use DGL for GNN training
    import dgl
    import torch
    
    # ... DGL operations ...
    
except NotImplementedError:
    print("DGL converter not yet implemented")
```

---

## Comparison Table

| Feature | NetworkX | SciPy | igraph | PyG | DGL |
|---------|----------|-------|--------|-----|-----|
| Directed | ✓ | ✓ | ✓ | ✓ | ✓ |
| Multigraph | ✓ | ✗ | ✗ | ? | ? |
| Self-loops | ✓ | ✓ | ✓ | ✓ | ✓ |
| Node IDs | ✓ | ✗ | ✓ (attr) | ✗ | ✗ |
| Node attrs | ✓ | ✗ | ✓ | ✓ | ✓ |
| Edge attrs | ✓ | ✗ | ✓ | ✓ | ✓ |
| Sidecar support | N/A | ✓ | N/A | N/A | N/A |
| Status | Full | Full | Full | Stub | Stub |

Legend:
- ✓ Fully supported
- ✗ Not supported (use sidecar if available)
- ? Planned/unclear
- N/A Not applicable

## Contributing New Converters

To add a new converter:

1. Create `py3plex/compat/converters/<format>_converter.py`
2. Implement `to_<format>_from_ir(ir: GraphIR) -> <TargetType>`
3. Implement `from_<format>_to_ir(obj: <TargetType>) -> GraphIR`
4. Add to `convert()` switch in `convert.py`
5. Add tests in `tests/test_compat_roundtrip.py`
6. Update this documentation

See `networkx_converter.py` for a reference implementation.
