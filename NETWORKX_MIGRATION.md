# NetworkX to Py3plex Migration Guide

This guide helps you transition from NetworkX to py3plex for multilayer network analysis.

## Why Migrate?

**NetworkX** is excellent for single-layer networks but lacks native support for:
- Multiple layers with different relationship types
- Inter-layer edges (coupling between layers)
- Multilayer-specific algorithms and metrics

**Py3plex** extends network analysis to multilayer structures while maintaining a familiar API.

## Quick Comparison

### NetworkX Single-Layer Graph

```python
import networkx as nx

G = nx.Graph()
G.add_nodes_from(['Alice', 'Bob', 'Carol'])
G.add_edges_from([
    ('Alice', 'Bob'),
    ('Bob', 'Carol'),
])
```

### Py3plex Equivalent (Single Layer)

```python
from py3plex import multi_layer_network

network = multi_layer_network()
network.add_nodes_from([
    ('Alice', 'layer1'),
    ('Bob', 'layer1'),
    ('Carol', 'layer1'),
])
network.add_edges_from([
    ('Alice', 'Bob', 'layer1'),
    ('Bob', 'Carol', 'layer1'),
])
```

**Key Difference**: Py3plex requires explicit layer specification.

## API Mapping

### Creating Networks

| NetworkX | Py3plex | Notes |
|----------|---------|-------|
| `G = nx.Graph()` | `net = multi_layer_network()` | Both undirected |
| `G = nx.DiGraph()` | `net = multi_layer_network(directed=True)` | Directed |
| `G = nx.MultiGraph()` | Similar but specify multiplex | Use `network_type="multiplex"` |

### Adding Nodes

| NetworkX | Py3plex | Notes |
|----------|---------|-------|
| `G.add_node('A')` | `net.add_node('A', 'layer1')` | Layer required |
| `G.add_node('A', color='red')` | Use node attributes (see below) | Different syntax |
| `G.add_nodes_from(['A', 'B'])` | `net.add_nodes_from([('A', 'L1'), ('B', 'L1')])` | Tuples required |

### Adding Edges

| NetworkX | Py3plex | Notes |
|----------|---------|-------|
| `G.add_edge('A', 'B')` | `net.add_edge('A', 'B', 'layer1')` | Layer required |
| `G.add_edge('A', 'B', weight=1.5)` | Edge attributes supported | Check IO preservation |
| `G.add_edges_from([('A','B')])` | `net.add_edges_from([('A','B','L1')])` | Include layer |

### Querying Networks

| NetworkX | Py3plex | Notes |
|----------|---------|-------|
| `G.nodes()` | `net.get_nodes()` | Returns generator |
| `G.edges()` | `net.get_edges()` | Returns generator |
| `G.number_of_nodes()` | `net.number_of_nodes()` | ✅ Same |
| `G.number_of_edges()` | `net.number_of_edges()` | ✅ Same |
| `G.neighbors('A')` | Check layer-specific neighbors | Different approach |
| `G.degree('A')` | Per-layer degree | Multilayer concept |

### Node/Edge Attributes

| NetworkX | Py3plex | Notes |
|----------|---------|-------|
| `G.nodes['A']['color'] = 'red'` | Different API (check docs) | Under development |
| `G.edges['A','B']['weight'] = 1.5` | Check edge attribute API | May differ |

## Conversion Functions

### From NetworkX to Py3plex

```python
import networkx as nx
from py3plex import multi_layer_network

def networkx_to_py3plex(G, layer_name="default"):
    """Convert a NetworkX graph to py3plex (single layer)."""
    network = multi_layer_network()
    
    # Add all nodes to the specified layer
    for node in G.nodes():
        network.add_node(node, layer_name)
    
    # Add all edges
    for u, v in G.edges():
        network.add_edge(u, v, layer_name)
    
    return network

# Usage
G = nx.karate_club_graph()
network = networkx_to_py3plex(G, "social")
```

### From Py3plex to NetworkX

```python
import networkx as nx

def py3plex_to_networkx(network, layer=None):
    """
    Convert py3plex network to NetworkX.
    If layer is specified, extract only that layer.
    If layer is None, create a merged NetworkX graph.
    """
    G = nx.Graph()
    
    if layer:
        # Extract single layer
        for node in network.get_nodes():
            if node[1] == layer:
                G.add_node(node[0])
        
        for edge in network.get_edges():
            # Check if edge is in the specified layer
            if len(edge) >= 3 and edge[2] == layer:
                G.add_edge(edge[0], edge[1])
    else:
        # Merge all layers (loses layer information)
        nodes_seen = set()
        for node in network.get_nodes():
            if node[0] not in nodes_seen:
                G.add_node(node[0])
                nodes_seen.add(node[0])
        
        edges_seen = set()
        for edge in network.get_edges():
            edge_tuple = (edge[0], edge[1])
            if edge_tuple not in edges_seen:
                G.add_edge(edge[0], edge[1])
                edges_seen.add(edge_tuple)
    
    return G

# Usage
G = py3plex_to_networkx(network, layer="social")  # Single layer
G_all = py3plex_to_networkx(network)  # Merged
```

## Working with Multilayer Networks

This is where py3plex shines - features NetworkX doesn't have:

### Multiple Layers (Different Relationship Types)

```python
from py3plex import multi_layer_network

network = multi_layer_network(network_type="multiplex")

# Same people, different interaction types
people = ['Alice', 'Bob', 'Carol']
layers = ['email', 'phone', 'meeting']

for layer in layers:
    for person in people:
        network.add_node(person, layer)

# Different relationships in each layer
network.add_edge('Alice', 'Bob', 'email')      # Email contact
network.add_edge('Bob', 'Carol', 'phone')      # Phone contact
network.add_edge('Alice', 'Carol', 'meeting')  # Meeting contact
```

### Inter-layer Edges (Coupling)

```python
# Connect same person across layers
network.add_edges_from([
    (('Alice', 'email'), ('Alice', 'phone')),
    (('Alice', 'phone'), ('Alice', 'meeting')),
])
```

### Per-Layer Analysis

```python
# Get layers
layers = network.get_layers()
print(f"Layers: {layers}")

# Analyze each layer separately
for layer in layers:
    layer_nodes = [n for n in network.get_nodes() if n[1] == layer]
    layer_edges = [e for e in network.get_edges() if e[2] == layer]
    print(f"Layer {layer}: {len(layer_nodes)} nodes, {len(layer_edges)} edges")
```

## Common Migration Patterns

### Pattern 1: Multiple NetworkX Graphs → One Multilayer Network

```python
import networkx as nx
from py3plex import multi_layer_network

# You have multiple NetworkX graphs (one per layer)
email_net = nx.Graph()
email_net.add_edges_from([('A', 'B'), ('B', 'C')])

phone_net = nx.Graph()
phone_net.add_edges_from([('A', 'C'), ('C', 'D')])

# Combine into multilayer network
network = multi_layer_network()

# Import email layer
for node in email_net.nodes():
    network.add_node(node, "email")
for u, v in email_net.edges():
    network.add_edge(u, v, "email")

# Import phone layer
for node in phone_net.nodes():
    network.add_node(node, "phone")
for u, v in phone_net.edges():
    network.add_edge(u, v, "phone")

print(f"Multilayer network: {network.number_of_nodes()} node-layer pairs")
```

### Pattern 2: Edge List with Layer Column

```python
# CSV format: source,target,layer,weight
# Alice,Bob,email,0.8
# Bob,Carol,phone,0.9

from py3plex.io import io_functions

# Load directly (if layer column is standard)
network = io_functions.read_edgelist("interactions.csv", delimiter=",")
```

### Pattern 3: Temporal Network → Multilayer

```python
# Time-sliced network: each time slice is a layer
from py3plex import multi_layer_network

network = multi_layer_network()

# Sample temporal interactions
interactions = [
    ('Alice', 'Bob', '2024-01-01'),
    ('Bob', 'Carol', '2024-01-01'),
    ('Alice', 'Carol', '2024-01-02'),
    ('Bob', 'Dave', '2024-01-02'),
]

# Each date becomes a layer
for source, target, date in interactions:
    network.add_node(source, date)
    network.add_node(target, date)
    network.add_edge(source, target, date)

# Now you can analyze temporal evolution
print(f"Layers (time slices): {network.get_layers()}")
```

## Algorithms and Analysis

### NetworkX Algorithms on Single Layers

```python
import networkx as nx

# Extract a layer as NetworkX graph
def extract_layer(network, layer_name):
    G = nx.Graph()
    for node in network.get_nodes():
        if node[1] == layer_name:
            G.add_node(node[0])
    for edge in network.get_edges():
        if len(edge) >= 3 and edge[2] == layer_name:
            G.add_edge(edge[0], edge[1])
    return G

# Use NetworkX algorithms
email_layer = extract_layer(network, "email")
centrality = nx.betweenness_centrality(email_layer)
communities = nx.community.louvain_communities(email_layer)
```

### Py3plex Multilayer Algorithms

```python
from py3plex.algorithms.statistics import multilayer_statistics

# Multilayer-specific metrics
versatility = multilayer_statistics.versatility_centrality(network)
# Measures how active a node is across multiple layers
```

## Performance Considerations

| Aspect | NetworkX | Py3plex | Notes |
|--------|----------|---------|-------|
| Single-layer | ⚡ Fast | 🐢 Slower | NetworkX optimized for single layer |
| Multilayer | ❌ N/A | ⚡ Fast | Py3plex designed for this |
| Memory | 💾 Efficient | 💾 More memory | Additional layer info |
| Algorithms | 📚 Many | 📖 Fewer | But multilayer-specific |

**Recommendation**: 
- Use NetworkX for single-layer analysis
- Use py3plex when you need multilayer features
- Can convert between them as needed

## Migration Checklist

- [ ] Identify if you really need multilayer (or just use NetworkX)
- [ ] Map your NetworkX graphs to layers
- [ ] Update `add_node()` calls to include layer parameter
- [ ] Update `add_edge()` calls to include layer parameter
- [ ] Convert attribute syntax (if using attributes)
- [ ] Test that query methods work with `.get_nodes()` instead of `.nodes()`
- [ ] Add inter-layer edges if modeling coupling
- [ ] Update visualization code (py3plex has different viz API)
- [ ] Check I/O format compatibility
- [ ] Run tests with both libraries to verify equivalence

## FAQs

### Q: Can I use NetworkX algorithms on py3plex networks?

**A**: Yes! Extract a layer as NetworkX graph (see code above) and use any NetworkX algorithm.

### Q: Should I migrate all my NetworkX code?

**A**: No! Only migrate if you need multilayer features. NetworkX is great for single-layer networks.

### Q: What about node/edge attributes?

**A**: Check py3plex documentation for current attribute API. It may differ from NetworkX.

### Q: Performance?

**A**: For single-layer networks, NetworkX is faster. For multilayer analysis, py3plex is designed for this use case.

### Q: Can I use both libraries together?

**A**: Absolutely! Use the conversion functions above to go back and forth.

## Getting Help

- **Examples**: See `examples/basic/example_networkx_wrapper.py`
- **Documentation**: [https://skblaz.github.io/py3plex/](https://skblaz.github.io/py3plex/)
- **Issues**: [https://github.com/SkBlaz/py3plex/issues](https://github.com/SkBlaz/py3plex/issues)

## Summary

**Key Takeaways**:
1. Py3plex requires explicit layer specification (this is intentional!)
2. You can convert between NetworkX and py3plex as needed
3. Use py3plex for multilayer analysis, NetworkX for single-layer
4. The APIs are similar enough for easy learning
5. Most NetworkX concepts translate directly to py3plex

Happy multilayer network analysis! 🎉
