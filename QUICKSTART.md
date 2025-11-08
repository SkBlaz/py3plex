# Py3plex Quickstart Guide

This guide gets you from zero to working multilayer network in **5 minutes**.

## Installation

```bash
pip install git+https://github.com/SkBlaz/py3plex.git
```

Verify installation:
```bash
py3plex selftest
```

## 5-Line Example (Simplest Possible)

```python
from py3plex import random_generators

# Create a random multilayer network
network = random_generators.random_multilayer_ER(20, 2, 0.2)

# Visualize it
network.visualize_network(show=True)
```

That's it! You now have a multilayer network with 20 nodes, 2 layers, and can see it.

## 10-Line Example (Build Your Own)

```python
from py3plex import multi_layer_network

# Create an empty network
network = multi_layer_network()

# Add nodes to two layers
network.add_nodes_from([
    ("Alice", "friends"),
    ("Bob", "friends"),
    ("Alice", "coworkers"),
    ("Bob", "coworkers"),
])

# Add edges within layers
network.add_edges_from([
    ("Alice", "Bob", "friends"),
    ("Alice", "Bob", "coworkers"),
])

# Check what we built
print(f"Nodes: {len(list(network.get_nodes()))}")
print(f"Edges: {len(list(network.get_edges()))}")
```

## Common Tasks

### Create a Multiplex Network

A multiplex network has the same nodes across all layers:

```python
from py3plex import multi_layer_network

network = multi_layer_network(network_type="multiplex")

# Add nodes (they exist in all layers once defined)
nodes = ["Alice", "Bob", "Carol"]
layers = ["email", "slack", "meeting"]

for layer in layers:
    for node in nodes:
        network.add_nodes_from([(node, layer)])

# Add layer-specific interactions
network.add_edges_from([
    ("Alice", "Bob", "email"),
    ("Bob", "Carol", "slack"),
    ("Alice", "Carol", "meeting"),
])
```

### Add Inter-layer Edges

Connect the same node across different layers (inter-layer coupling):

```python
# Add inter-layer connections
network.add_edges_from([
    (("Alice", "email"), ("Alice", "slack")),
    (("Bob", "email"), ("Bob", "slack")),
])
```

### Load from CSV/Edge List

```python
from py3plex.io import io_functions

# Load from edge list file
# Format: source target layer
network = io_functions.read_edgelist("my_network.txt")

# Save your network
io_functions.write_edgelist(network, "output.txt")
```

### NetworkX Interoperability

If you're coming from NetworkX:

```python
import networkx as nx
from py3plex import multi_layer_network

# Create a simple NetworkX graph
G = nx.karate_club_graph()

# Convert to py3plex (all nodes go to one layer)
network = multi_layer_network()
for node in G.nodes():
    network.add_node(node, "layer1")
for u, v in G.edges():
    network.add_edge(u, v, "layer1")
```

### Key Differences from NetworkX

| NetworkX | Py3plex | Notes |
|----------|---------|-------|
| `G.add_edge(u, v)` | `net.add_edge(u, v, layer)` | Layer required |
| `G.add_node(n)` | `net.add_node(n, layer)` | Layer required |
| Nodes: strings/ints | Nodes: (node, layer) tuples | Multilayer structure |
| `G.nodes()` | `net.get_nodes()` | Returns generator |
| `G.edges()` | `net.get_edges()` | Returns generator |

## Common Errors and Solutions

### Error: "Node not found"

**Problem**: Trying to add an edge between nodes that don't exist.

**Solution**: Add nodes before edges:
```python
network.add_nodes_from([("A", "layer1"), ("B", "layer1")])
network.add_edge("A", "B", "layer1")  # Now works!
```

### Error: "Layer not specified"

**Problem**: Forgot to specify which layer.

**Solution**: Always include the layer:
```python
# Wrong:
network.add_node("Alice")

# Right:
network.add_node("Alice", "layer1")
```

### Import Error

**Problem**: Can't find `multi_layer_network` or `random_generators`.

**Solution**: Use top-level imports:
```python
# Simple (recommended):
from py3plex import multi_layer_network, random_generators

# Or explicit:
from py3plex.core.multinet import multi_layer_network
from py3plex.core import random_generators
```

## Next Steps

- **Examples**: See `examples/` directory for 50+ working examples
- **Documentation**: Visit [https://skblaz.github.io/py3plex/](https://skblaz.github.io/py3plex/)
- **CLI Tool**: Run `py3plex quickstart` for interactive demo
- **Advanced Guide**: See [LLM.md](./LLM.md) for comprehensive API reference

## Quick Reference Card

```python
# Import
from py3plex import multi_layer_network, random_generators

# Create
network = multi_layer_network()

# Add nodes
network.add_node("node1", "layer1")
network.add_nodes_from([("n1", "L1"), ("n2", "L2")])

# Add edges
network.add_edge("n1", "n2", "layer1")
network.add_edges_from([("n1", "n2", "L1"), ("n2", "n3", "L1")])

# Query
network.get_nodes()        # All nodes
network.get_edges()        # All edges
network.get_layers()       # All layers
network.number_of_nodes()  # Count nodes
network.number_of_edges()  # Count edges

# Visualize
network.visualize_network(show=True)

# Save/Load
from py3plex.io import io_functions
io_functions.write_edgelist(network, "file.txt")
network = io_functions.read_edgelist("file.txt")
```

## Help

- **GitHub Issues**: [https://github.com/SkBlaz/py3plex/issues](https://github.com/SkBlaz/py3plex/issues)
- **CLI Help**: `py3plex --help`
- **Self-test**: `py3plex selftest`

Happy network analysis! 🎉
