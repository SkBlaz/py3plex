# I/O and Data Management

This directory contains examples for loading, saving, and managing multilayer network data. Learn how to work with various file formats and optimize data handling.

## Examples in This Category

### Loading and Saving Networks
- **`example_IO.py`** - Load networks from different file formats (edgelist, GML, etc.)
- **`example_new_io.py`** - Use the modern I/O API for multilayer graphs
- **`example_save_to_arrow.py`** - High-performance serialization with Apache Arrow/Parquet formats
- **`example_save_to_edgelist.py`** - Save networks in various edgelist formats
- **`example_save_to_gpickle.py`** - Save and load networks using NetworkX pickle format

### Parsing and Format Conversion
- **`example_multiplex_generic_parser.py`** - Parse multiplex network data from custom formats
- **`example_schema_validation.py`** - Validate network data against schemas

### Performance and Safety Features
- **`example_immutable_mode.py`** - Use immutable network views (copy-on-write)
- **`example_lazy_evaluation_caching.py`** - Optimize computations with lazy evaluation and caching

## Common Use Cases

### Loading a Network from File
```python
from py3plex.core import multinet

# Load from edgelist
network = multinet.multi_layer_network().load_network(
    "network.edgelist", 
    directed=False
)
```

### Saving to Different Formats
```python
# Save as edgelist
network.save_network("output.edgelist")

# Save as gpickle
network.save_network("output.gpickle", format="gpickle")
```

## Performance Tips

- Use **lazy evaluation** for expensive computations that might not be needed
- Use **caching** to avoid recomputing network metrics
- Use **immutable mode** when you need to protect network structure from accidental modifications

## Related Examples

- [Getting Started](../getting_started/) - Basic network creation
- [Network Analysis](../network_analysis/) - After loading data, analyze it
