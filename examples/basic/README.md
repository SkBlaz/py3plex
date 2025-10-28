# Basic Examples

This directory contains examples for basic operations, network I/O, and network creation.

## Examples

### Input/Output Operations

- **`example_IO.py`** - Demonstrates reading different network formats (multiedgelist, gpickle, GML, edgelist, sparse matrices, multiplex edges)
- **`example_new_io.py`** - Modern I/O operations with various network formats
- **`example_save_to_edgelist.py`** - Save networks as edgelist format
- **`example_save_to_gpickle.py`** - Save networks as gpickle objects for fast loading

### Network Creation and Wrappers

- **`example_random_generator.py`** - Generate random networks using py3plex
- **`example_networkx_wrapper.py`** - Using NetworkX with py3plex
- **`example_nx_wrapper.py`** - Alternative NetworkX integration examples

### Network Manipulation

- **`example_inverse_network.py`** - Create inverse/complement networks
- **`example_layer_extraction.py`** - Extract specific layers from multilayer networks

## Usage

These examples demonstrate the fundamental operations you'll need to:
1. Load networks from various file formats
2. Save networks for later use
3. Create random networks for testing
4. Integrate with NetworkX
5. Perform basic transformations

## Quick Start

```bash
# Load a network from different formats
python example_IO.py

# Generate and save a random network
python example_random_generator.py
python example_save_to_gpickle.py
```

## Related Directories

- See [../visualization/](../visualization/) for plotting these networks
- See [../multilayer/](../multilayer/) for advanced multilayer operations
