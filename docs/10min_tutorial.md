# 10-Minute Tutorial: Getting Started with Py3plex

This tutorial provides a quick introduction to py3plex, covering the most common tasks you'll need to work with multilayer networks.

## What You'll Learn

In just 10 minutes, you'll learn how to:
1. Create and load multilayer networks
2. Perform basic network analysis
3. Detect communities
4. Visualize your networks

## Prerequisites

Make sure py3plex is installed:
```bash
pip install git+https://github.com/SkBlaz/py3plex.git
```

## 1. Creating Your First Multilayer Network (2 minutes)

Let's start by creating a simple multilayer network from scratch:

```python
from py3plex.core import multinet

# Create a new multilayer network
network = multinet.multi_layer_network()

# Add edges within layers (this automatically creates nodes)
# Format: [source_node, source_layer, target_node, target_layer, weight]
network.add_edges([
    ['A', 'layer1', 'B', 'layer1', 1],
    ['B', 'layer1', 'C', 'layer1', 1],
    ['A', 'layer2', 'B', 'layer2', 1],
    ['B', 'layer2', 'D', 'layer2', 1]
], input_type="list")

# Display basic statistics
network.basic_stats()
```

**Output:**
```
Number of nodes: 5
Number of edges: 4
Number of layers: 2
```

## 2. Loading Networks from Files (1 minute)

Py3plex supports multiple input formats. Here's how to load from an edge list:

```python
from py3plex.core import multinet

# Load from a multiedgelist file
# Format: source target layer
network = multinet.multi_layer_network().load_network(
    "datasets/multiedgelist.txt",
    input_type="multiedgelist",
    directed=False
)

# Check what we loaded
network.basic_stats()
```

**Supported formats:**
- `multiedgelist`: source, target, layer
- `edgelist`: simple source, target pairs
- `gpickle`: NetworkX pickle format
- `gml`, `graphml`: Standard graph formats

## 3. Exploring Network Structure (2 minutes)

### Iterate Through Nodes and Edges

```python
# Loop through all nodes
print("Nodes:")
for node in network.get_nodes(data=True):
    print(node)

# Loop through all edges
print("\nEdges:")
for edge in network.get_edges(data=True):
    print(edge)

# Get neighbors of a specific node in a layer
node_of_interest = "1"
layer_id = "1"
neighbors = list(network.get_neighbors(node_of_interest, layer_id=layer_id))
print(f"\nNeighbors of {node_of_interest} in layer {layer_id}:", neighbors)
```

### Extract Subnetworks

```python
# Extract a single layer
layer_1 = network.subnetwork(['1'], subset_by="layers")
print("Layer 1 nodes:", list(layer_1.get_nodes()))

# Extract specific nodes
node_subset = network.subnetwork(['1', '2'], subset_by="node_names")
print("Node subset:", list(node_subset.get_nodes()))

# Extract specific node-layer pairs
specific_pairs = network.subnetwork(
    [('1', '1'), ('2', '1')], 
    subset_by="node_layer_names"
)
print("Specific pairs:", list(specific_pairs.get_nodes()))
```

## 4. Computing Network Metrics (2 minutes)

### Basic Centrality Measures

```python
# Get a single layer as NetworkX graph
layer_1 = network.subnetwork(['1'], subset_by="layers")

# Compute degree centrality using NetworkX wrapper
degree_centrality = layer_1.monoplex_nx_wrapper("degree_centrality")
print("Degree centrality:", degree_centrality)

# Compute betweenness centrality
betweenness = layer_1.monoplex_nx_wrapper("betweenness_centrality")
print("Betweenness centrality:", betweenness)
```

### Multilayer Centrality

For multilayer-specific centrality measures:

```python
from py3plex.algorithms.multilayer_algorithms.multilayer_centrality import (
    multilayer_degree_centrality,
    multilayer_betweenness_centrality
)

# Compute multilayer degree centrality
ml_degree = multilayer_degree_centrality(network)
print("Multilayer degree centrality:", ml_degree)

# Compute multilayer betweenness centrality
ml_betweenness = multilayer_betweenness_centrality(network)
print("Multilayer betweenness centrality:", ml_betweenness)
```

## 5. Community Detection (2 minutes)

Identify communities in your multilayer network:

```python
from py3plex.algorithms.community_detection import community_wrapper as cw

# Louvain community detection
partition = cw.louvain_communities(network)
print("Communities found:", len(set(partition.values())))

# Display community assignments
for node, community_id in list(partition.items())[:5]:
    print(f"Node {node} -> Community {community_id}")

# Count nodes per community
from collections import Counter
community_sizes = Counter(partition.values())
print("\nCommunity sizes:", dict(community_sizes))
```

## 6. Basic Visualization (1 minute)

Visualize your multilayer network:

```python
from py3plex.visualization.multilayer import hairball_plot
import matplotlib.pyplot as plt

# Get network for visualization
network_colors, graph = network.get_layers(style="hairball")

# Create a simple hairball plot
plt.figure(figsize=(10, 10))
hairball_plot(
    graph,
    network_colors,
    layout_algorithm="force",
    layout_parameters={"iterations": 50}
)
plt.title("Multilayer Network Visualization")
plt.savefig("my_network.png", dpi=150, bbox_inches='tight')
plt.close()
print("Visualization saved to my_network.png")
```

For more advanced visualizations with community colors:

```python
from py3plex.visualization.colors import colors_default

# Get communities
partition = cw.louvain_communities(network)

# Select top N communities
top_n = 5
community_counts = Counter(partition.values())
top_communities = [c for c, _ in community_counts.most_common(top_n)]

# Assign colors
color_map = dict(zip(
    top_communities,
    colors_default[:top_n]
))

network_colors = [
    color_map.get(partition.get(node), "gray")
    for node in network.get_nodes()
]

# Plot with community colors
plt.figure(figsize=(10, 10))
hairball_plot(graph, network_colors, layout_algorithm="force")
plt.title("Multilayer Network with Communities")
plt.savefig("my_network_communities.png", dpi=150, bbox_inches='tight')
plt.close()
print("Community visualization saved to my_network_communities.png")
```

## Complete Example: Putting It All Together

Here's a complete workflow:

```python
from py3plex.core import multinet
from py3plex.algorithms.community_detection import community_wrapper as cw
from py3plex.visualization.multilayer import hairball_plot
from py3plex.visualization.colors import colors_default
from collections import Counter
import matplotlib.pyplot as plt

# Load network
network = multinet.multi_layer_network().load_network(
    "datasets/multiedgelist.txt",
    input_type="multiedgelist",
    directed=False
)

# Analyze structure
print("=== Network Statistics ===")
network.basic_stats()

# Compute centrality for one layer
layer_1 = network.subnetwork(['1'], subset_by="layers")
degree_cent = layer_1.monoplex_nx_wrapper("degree_centrality")
print("\n=== Top 5 Nodes by Degree (Layer 1) ===")
for node, score in sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"{node}: {score:.3f}")

# Detect communities
partition = cw.louvain_communities(network)
print(f"\n=== Communities ===")
print(f"Number of communities: {len(set(partition.values()))}")

# Visualize with communities
network_colors, graph = network.get_layers(style="hairball")
top_n = 3
community_counts = Counter(partition.values())
top_communities = [c for c, _ in community_counts.most_common(top_n)]
color_map = dict(zip(top_communities, colors_default[:top_n]))
network_colors = [
    color_map.get(partition.get(node), "lightgray")
    for node in network.get_nodes()
]

plt.figure(figsize=(12, 12))
hairball_plot(graph, network_colors, layout_algorithm="force")
plt.title("Multilayer Network Analysis")
plt.savefig("complete_analysis.png", dpi=150, bbox_inches='tight')
plt.close()
print("\nComplete analysis saved to complete_analysis.png")
```

## Next Steps

Now that you've completed this tutorial, explore more advanced features:

- **Multilayer Modularity**: See `docs/multilayer_modularity_tutorial.md`
- **Multilayer Centrality**: See `docs/multilayer_centrality_tutorial.md`
- **More Examples**: Check the `examples/` directory for 40+ examples
- **Full Documentation**: Visit [https://skblaz.github.io/py3plex/](https://skblaz.github.io/py3plex/)

## Common Issues

### File Not Found
Make sure you're running from the repository root or use absolute paths:
```python
import os
base_path = "/path/to/py3plex"
network = multinet.multi_layer_network().load_network(
    os.path.join(base_path, "datasets/multiedgelist.txt"),
    input_type="multiedgelist",
    directed=False
)
```

### Visualization Not Showing
If using Jupyter, add `%matplotlib inline` at the top of your notebook. For scripts, use `plt.show()` instead of `plt.close()`.

### Missing Dependencies
Some features require optional dependencies:
```bash
# For advanced visualization
pip install plotly

# For community detection with Infomap
pip install infomap

# For all extras
pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz,algos]
```

## Tips for Success

1. **Start Simple**: Begin with small test networks before scaling to large datasets
2. **Check Stats**: Always run `basic_stats()` after loading to verify your network
3. **Use Subnetworks**: Extract layers or subsets for faster prototyping
4. **Seed Your Random**: Use `seed` parameters in algorithms for reproducible results
5. **Visualize Early**: Quick plots help catch data loading issues early

Happy network analysis! 🎉
