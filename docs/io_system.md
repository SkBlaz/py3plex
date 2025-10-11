# Multilayer Graph I/O System

This document describes the new I/O system for py3plex multilayer graphs.

## Overview

The I/O system provides:

- **Schema validation** with dataclass-based representations
- **Multiple file formats**: JSON, JSONL, CSV
- **Library converters**: NetworkX, igraph
- **Streaming support** for large graphs
- **Deterministic serialization** for reproducibility

## Quick Start

```python
from py3plex.io import (
    MultiLayerGraph, Node, Layer, Edge,
    read, write
)

# Create a multilayer graph
graph = MultiLayerGraph()
graph.add_layer(Layer(id="social"))
graph.add_node(Node(id="alice", attributes={"age": 30}))
graph.add_node(Node(id="bob", attributes={"age": 25}))
graph.add_edge(Edge(
    src="alice", dst="bob",
    src_layer="social", dst_layer="social",
    attributes={"weight": 0.8}
))

# Write to file
write(graph, "network.json")

# Read from file
graph2 = read("network.json")
```

## Schema Classes

### MultiLayerGraph

The main container for multilayer graphs.

```python
from py3plex.io import MultiLayerGraph

graph = MultiLayerGraph(
    directed=True,
    attributes={"name": "My Network"}
)
```

**Attributes:**
- `nodes`: Dictionary mapping node IDs to Node objects
- `layers`: Dictionary mapping layer IDs to Layer objects
- `edges`: List of Edge objects
- `directed`: Boolean indicating if graph is directed
- `attributes`: Dictionary of graph-level attributes

**Methods:**
- `add_node(node)`: Add a node to the graph
- `add_layer(layer)`: Add a layer to the graph
- `add_edge(edge)`: Add an edge to the graph
- `to_dict()`: Convert to dictionary (for serialization)
- `from_dict(data)`: Create from dictionary (class method)

### Node

Represents a node in the multilayer graph.

```python
from py3plex.io import Node

node = Node(
    id="alice",
    attributes={"age": 30, "city": "NYC"}
)
```

**Attributes:**
- `id`: Unique identifier (any hashable type)
- `attributes`: Dictionary of node attributes (must be JSON-serializable)

### Layer

Represents a layer in the multilayer graph.

```python
from py3plex.io import Layer

layer = Layer(
    id="facebook",
    attributes={"platform": "Facebook", "type": "social"}
)
```

**Attributes:**
- `id`: Unique identifier (any hashable type)
- `attributes`: Dictionary of layer attributes (must be JSON-serializable)

### Edge

Represents an edge in the multilayer graph.

```python
from py3plex.io import Edge

edge = Edge(
    src="alice",
    dst="bob",
    src_layer="facebook",
    dst_layer="facebook",
    key=0,  # For multigraphs
    attributes={"weight": 0.8, "timestamp": "2024-01-15"}
)
```

**Attributes:**
- `src`: Source node ID
- `dst`: Destination node ID
- `src_layer`: Source layer ID
- `dst_layer`: Destination layer ID
- `key`: Edge key for multigraphs (default: 0)
- `attributes`: Dictionary of edge attributes (must be JSON-serializable)

## Schema Validation

The I/O system performs automatic validation:

### Referential Integrity

All edges must reference existing nodes and layers:

```python
graph = MultiLayerGraph()
graph.add_node(Node(id="n1"))
graph.add_layer(Layer(id="l1"))

# This raises ReferentialIntegrityError (n2 doesn't exist)
graph.add_edge(Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1"))
```

### JSON Serializability

All attributes must be JSON-serializable:

```python
# This raises SchemaValidationError
node = Node(id="n1", attributes={"func": lambda x: x})
```

### Edge Uniqueness

Edges are unique by `(src, dst, src_layer, dst_layer, key)`:

```python
graph.add_edge(Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1"))
# This raises SchemaValidationError (duplicate edge)
graph.add_edge(Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1"))
```

## File Formats

### JSON Format

Canonical, human-readable format with full attribute preservation.

**Write:**
```python
write(graph, "network.json", deterministic=True, indent=2)
```

**Read:**
```python
graph = read("network.json")
```

**Format:**
```json
{
  "nodes": [
    {"id": "alice", "attributes": {"age": 30}}
  ],
  "layers": [
    {"id": "social", "attributes": {}}
  ],
  "edges": [
    {
      "src": "alice",
      "dst": "bob",
      "src_layer": "social",
      "dst_layer": "social",
      "key": 0,
      "attributes": {"weight": 0.8}
    }
  ],
  "directed": true,
  "attributes": {}
}
```

**Gzip compression:** Use `.json.gz` extension for automatic compression.

### JSONL Format

Streaming format for large graphs. One JSON object per line.

**Write:**
```python
write(graph, "network.jsonl", format="jsonl")
```

**Read:**
```python
graph = read("network.jsonl", format="jsonl")
```

**Format:**
```
{"directed": true, "attributes": {}}
{"id": "alice", "attributes": {"age": 30}, "type": "node"}
{"id": "social", "attributes": {}, "type": "layer"}
{"src": "alice", "dst": "bob", "src_layer": "social", "dst_layer": "social", "key": 0, "attributes": {"weight": 0.8}, "type": "edge"}
```

**Gzip compression:** Use `.jsonl.gz` extension.

### CSV Format

Edge list format with optional sidecar files for node/layer attributes.

**Write:**
```python
write(graph, "edges.csv", format="csv", write_sidecars=True)
```

**Read:**
```python
graph = read("edges.csv", format="csv",
             nodes_file="nodes.csv",
             layers_file="layers.csv")
```

**Edge file format (`edges.csv`):**
```csv
src,dst,src_layer,dst_layer,key,weight
alice,bob,social,social,0,0.8
```

Required columns: `src`, `dst`, `src_layer`, `dst_layer`
Optional columns: `key`, any custom edge attributes

**Node file format (`nodes.csv`):**
```csv
id,age,city
alice,30,NYC
bob,25,SF
```

**Layer file format (`layers.csv`):**
```csv
id,platform
social,Facebook
```

## Library Converters

### NetworkX

Convert between MultiLayerGraph and NetworkX graphs.

**Projection Modes:**

1. **Union**: Merge all layers into single graph
   ```python
   from py3plex.io import to_networkx, from_networkx
   
   G = to_networkx(graph, mode="union")
   # Nodes: node IDs only
   # Edges: merged from all layers (layer info in edge attributes)
   ```

2. **Multiplex**: Preserve full multilayer structure
   ```python
   G = to_networkx(graph, mode="multiplex")
   # Nodes: (node_id, layer_id) tuples
   # Edges: between (node, layer) tuples
   ```

3. **Intersection**: Keep only edges in ALL layers
   ```python
   G = to_networkx(graph, mode="intersection")
   # Only intra-layer edges present in all layers
   ```

**Round-trip conversion:**
```python
G = to_networkx(graph, mode="multiplex")
graph2 = from_networkx(G, mode="multiplex")
```

### igraph

Convert between MultiLayerGraph and igraph graphs.

```python
from py3plex.io import to_igraph, from_igraph

# Convert to igraph
g = to_igraph(graph, mode="multiplex")

# Convert back
graph2 = from_igraph(g, mode="multiplex")
```

Supports `"union"` and `"multiplex"` modes similar to NetworkX.

## API Functions

### read()

Read a multilayer graph from a file.

```python
graph = read(
    filepath,              # Path to input file
    format=None,           # Format name (auto-detected from extension if None)
    **kwargs               # Format-specific arguments
)
```

**Arguments:**
- `filepath`: Path to input file
- `format`: Format name (`"json"`, `"jsonl"`, `"csv"`, or `None` for auto-detection)
- `**kwargs`: Additional format-specific arguments (e.g., `nodes_file` for CSV)

**Returns:** `MultiLayerGraph`

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `FormatUnsupportedError`: If format is not supported

### write()

Write a multilayer graph to a file.

```python
write(
    graph,                 # MultiLayerGraph to write
    filepath,              # Path to output file
    format=None,           # Format name (auto-detected from extension if None)
    deterministic=False,   # Sort nodes/edges for reproducibility
    **kwargs               # Format-specific arguments
)
```

**Arguments:**
- `graph`: MultiLayerGraph to write
- `filepath`: Path to output file
- `format`: Format name or `None` for auto-detection
- `deterministic`: If `True`, sort nodes/edges for consistent output
- `**kwargs`: Format-specific arguments (e.g., `write_sidecars` for CSV)

### supported_formats()

Get list of supported formats.

```python
formats = supported_formats(read=True, write=True)
# Returns: {'read': ['csv', 'json', 'jsonl'], 'write': ['csv', 'json', 'jsonl']}
```

### register_reader() / register_writer()

Register custom format handlers.

```python
from py3plex.io import register_reader, register_writer

def my_reader(filepath, **kwargs):
    # Custom reading logic
    return MultiLayerGraph(...)

def my_writer(graph, filepath, **kwargs):
    # Custom writing logic
    pass

register_reader("myformat", my_reader)
register_writer("myformat", my_writer)
```

## Best Practices

### For Small Graphs (< 10K edges)

Use JSON format for human readability and full attribute preservation:

```python
write(graph, "network.json", deterministic=True, indent=2)
```

### For Large Graphs (> 100K edges)

Use JSONL or CSV for efficient streaming:

```python
write(graph, "network.jsonl.gz", format="jsonl")  # Compressed streaming
```

### For Sharing Data

Use CSV with sidecars for maximum compatibility:

```python
write(graph, "edges.csv", format="csv", write_sidecars=True, deterministic=True)
```

### For Version Control

Always use `deterministic=True` to ensure reproducible output:

```python
write(graph, "network.json", deterministic=True)
```

### For Interoperability

Use library converters for seamless integration:

```python
from py3plex.io import to_networkx
import networkx as nx

# Convert to NetworkX for analysis
G = to_networkx(graph, mode="multiplex")
communities = nx.algorithms.community.louvain_communities(G)
```

## Error Handling

```python
from py3plex.io import (
    SchemaValidationError,
    ReferentialIntegrityError,
    FormatUnsupportedError
)

try:
    graph = read("network.xyz")
except FormatUnsupportedError as e:
    print(f"Format not supported: {e}")

try:
    graph.add_edge(Edge(src="n1", dst="n2", src_layer="l1", dst_layer="l1"))
except ReferentialIntegrityError as e:
    print(f"Invalid reference: {e}")

try:
    node = Node(id="n1", attributes={"bad": object()})
except SchemaValidationError as e:
    print(f"Validation failed: {e}")
```

## Performance Considerations

### Memory Usage

- JSON: Loads entire graph into memory
- JSONL: Can stream for reading (still loads all into memory currently)
- CSV: Minimal memory overhead

### File Size

- JSON (uncompressed): ~2-3x edge count in bytes
- JSON (gzip): ~5-10x compression ratio
- JSONL (gzip): Similar to JSON.gz
- CSV: ~1-2x edge count in bytes

### Read/Write Speed

For large graphs (1M+ edges):
- JSONL: Fastest
- CSV: Fast
- JSON: Moderate (prettification overhead)

## Migration Guide

### From Old py3plex API

Old:
```python
from py3plex.core import multinet

net = multinet.multi_layer_network()
net.load_network("network.json", input_type="json")
```

New:
```python
from py3plex.io import read

graph = read("network.json")
```

### From NetworkX

Old:
```python
import networkx as nx
G = nx.read_edgelist("edges.txt")
```

New:
```python
from py3plex.io import read, from_networkx

# Option 1: Read directly
graph = read("edges.csv")  # CSV format

# Option 2: Convert from NetworkX
import networkx as nx
G = nx.read_edgelist("edges.txt")
graph = from_networkx(G, mode="union", default_layer="layer1")
```

## Examples

See `examples/example_new_io.py` for comprehensive usage examples.

## Testing

The I/O system includes 51+ unit tests covering:
- Schema validation
- Format round-trips
- Library conversions
- Error handling
- Edge cases

Run tests:
```bash
pytest tests/test_io_schema.py -v
```
