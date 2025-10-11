# py3plex I/O Module

Modern I/O system for multilayer graphs with schema validation, multiple formats, and library converters.

## Features

- **Schema Validation**: Dataclass-based with automatic validation of referential integrity and JSON serializability
- **Multiple Formats**: JSON, JSONL (streaming), CSV with sidecar support
- **Library Converters**: NetworkX and igraph with multiple projection modes
- **Deterministic Output**: Reproducible serialization with sorting
- **Extensible**: Plugin-based format registry for custom readers/writers

## Quick Start

```python
from py3plex.io import MultiLayerGraph, Node, Layer, Edge, read, write

# Create a graph
graph = MultiLayerGraph()
graph.add_layer(Layer(id="social"))
graph.add_node(Node(id="alice", attributes={"age": 30}))
graph.add_node(Node(id="bob", attributes={"age": 25}))
graph.add_edge(Edge(
    src="alice", dst="bob",
    src_layer="social", dst_layer="social",
    attributes={"weight": 0.8}
))

# Write to JSON
write(graph, "network.json", deterministic=True)

# Read back
graph2 = read("network.json")
```

## Documentation

See [`docs/io_system.md`](../../docs/io_system.md) for complete documentation.

## Examples

See [`examples/example_new_io.py`](../../examples/example_new_io.py) for working examples.

## Testing

```bash
pytest tests/test_io_schema.py -v
```

51+ tests covering:
- Schema validation and error handling
- Format round-trips (JSON, JSONL, CSV)
- Library conversions (NetworkX, igraph)
- Edge cases and data integrity

## Module Structure

```
py3plex/io/
├── __init__.py          # Public API exports
├── api.py               # read(), write(), registry functions
├── schema.py            # MultiLayerGraph, Node, Layer, Edge dataclasses
├── exceptions.py        # Custom exception types
├── converters.py        # NetworkX and igraph converters
└── formats/
    ├── __init__.py
    ├── json_format.py   # JSON and JSONL readers/writers
    └── csv_format.py    # CSV reader/writer with sidecar support
```

## Design Principles

1. **Minimal Changes**: Designed as an opt-in addition, existing code unchanged
2. **Type Safety**: Full type hints and schema validation
3. **Extensibility**: Plugin-based format registry
4. **Performance**: Streaming support for large graphs
5. **Reproducibility**: Deterministic serialization option

## Compatibility

- Python 3.8+
- Optional dependencies: NetworkX, igraph (only if using converters)
- Backward compatible with existing py3plex API
