# Py3plex: Comprehensive Documentation

**Version**: 0.95a  
**Last Updated**: October 2025  
**Authors**: Blaž Škrlj, Jan Kralj, Nada Lavrač  
**License**: MIT (Core), AGPLv3 (Infomap module)

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Core Modules](#core-modules)
4. [Interactive Examples](#interactive-examples)
5. [Advanced Usage](#advanced-usage)
6. [Contributing & Extending](#contributing--extending)
7. [API Reference](#api-reference)
8. [Citations & References](#citations--references)

---

## Overview

### What is Py3plex?

Py3plex is a Python library for **multiplex and multilayer 
network analysis**. Unlike traditional network tools focused on 
homogeneous graphs (single node/edge type), Py3plex specializes 
in heterogeneous networks with:

- **Multiple node types**: Proteins, genes, authors, venues
- **Multiple edge types**: Interactions, citations, friendships
- **Multiple layers**: Social platforms, transportation modes
- **Temporal dynamics**: Evolving communities, spreading processes
- **Semantic enrichment**: Ontology integration, knowledge graphs

### Why Py3plex?

Real-world systems exhibit **heterogeneity across dimensions**. 
Consider:

- **Biology**: Protein-protein interactions with multiple 
  evidence sources (yeast-two-hybrid, affinity purification, 
  co-expression)
- **Social Networks**: Users on Twitter, Facebook, LinkedIn 
  with different relationship types
- **Citations**: Author-paper-venue networks with co-authorship 
  and citation edges
- **Transportation**: Bus, train, air networks with shared 
  stations/airports

Traditional tools like NetworkX handle single-layer networks well 
but lack native multilayer support. Py3plex bridges this gap with:

1. **Native multilayer data structures** via `multi_layer_network`
2. **Layer-aware algorithms** (centrality, modularity, communities)
3. **Specialized visualizations** (diagonal projection, 
   supra-adjacency heatmaps)
4. **Network decomposition** using meta-paths and structural 
   patterns
5. **Semantic enrichment** by linking to external knowledge bases

### Core Capabilities

**Data Structures**:
- Multiplex networks (shared nodes, multiple layers)
- General multilayer networks (different nodes per layer)
- Temporal networks (dynamic edge activation)
- Heterogeneous networks (typed nodes and edges)

**Algorithms**:
- 17+ multilayer statistics (density, versatility, 
  interdependence)
- Multilayer centrality (degree, betweenness, closeness, 
  participation coefficient)
- Community detection (Louvain, Infomap, label propagation)
- Random walks (Node2Vec, DeepWalk primitives)
- Network embeddings (Node2Vec, meta-path based)

**Visualization**:
- Diagonal projection for large multilayer networks (10k+ nodes)
- Supra-adjacency matrix heatmaps
- Force-directed layouts (ForceAtlas2, spring, circular)
- Interactive 3D plots (Plotly integration)

### Architecture

```
Input → Parsers → multi_layer_network → Algorithms → Outputs
         ↓                                  ↓
    GraphML, GEXF,              Statistics, Communities,
    EdgeList, CSV               Centrality, Embeddings
                                           ↓
                                  Visualization, Export
```

**Key Design Principles**:
- **NetworkX foundation**: `.core_network` is always a NetworkX 
  graph
- **Layer encoding**: Layers stored in edge keys; node IDs 
  include layer via delimiter
- **Sparse matrices**: Automatic detection and use of SciPy 
  sparse matrices
- **Modular architecture**: Core, algorithms, visualization 
  operate independently

---

## Quick Start

### Installation

**From GitHub (recommended)**:
```bash
pip install git+https://github.com/SkBlaz/py3plex.git
```

**From source for development**:
```bash
git clone https://github.com/SkBlaz/py3plex.git
cd py3plex
pip install -e .
```

**Optional dependencies**:
```bash
# Advanced visualization
pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz]

# Development tools (testing, linting)
pip install -e ".[dev]"
```

### Requirements

- **Python**: 3.8 or higher
- **Core dependencies**: NetworkX ≥2.5, NumPy ≥0.8, SciPy ≥1.1.0
- **Visualization**: Matplotlib, Seaborn, Plotly (optional)
- **Machine Learning**: scikit-learn, gensim (optional)

### Minimal Working Example

```python
from py3plex.core import multinet

# Create a multilayer network
network = multinet.multi_layer_network()

# Add edges across two layers
network.add_edges([
    ['A', 'social', 'B', 'social', 1],
    ['B', 'social', 'C', 'social', 1],
    ['A', 'work', 'B', 'work', 1],
    ['A', 'work', 'C', 'work', 1],
], input_type="list")

# Display basic statistics
network.basic_stats()
# Output:
# Number of nodes: 3 (unique across layers)
# Number of edges: 4
# Number of layers: 2
```

**Expected Output**:
```
Nodes: 6 (node-layer replicas)
Edges: 4
Layers: ['social', 'work']
Density: 0.4 (within layers)
```

### Loading from File

```python
# Load from edge list (format: source, target, weight)
network = multinet.multi_layer_network().load_network(
    "data.edgelist", 
    input_type="edgelist", 
    directed=False
)

# Load from GraphML
network = multinet.multi_layer_network().load_network(
    "network.graphml",
    input_type="graphml"
)
```

**Supported formats**: EdgeList, GraphML, GEXF, CSV, GML, 
NetworkX pickle

### Visualization

```python
from py3plex.visualization.multilayer import (
    draw_multilayer_default
)

# Basic visualization
draw_multilayer_default([network], display=True)

# Customized layout
from py3plex.visualization.multilayer import visualize_multilayer
visualize_multilayer(
    network, 
    layout="kamada_kawai",
    node_size=20,
    edge_width=0.5,
    show=True
)
```

### Computing Statistics

```python
from py3plex.algorithms.statistics import (
    multilayer_statistics as mls
)

# Layer density
density = mls.layer_density(network, 'social')
print(f"Social layer density: {density:.3f}")

# Node activity (fraction of layers where node is active)
activity = mls.node_activity(network, 'A')
print(f"Node A activity: {activity:.3f}")

# Versatility centrality
versatility = mls.versatility_centrality(
    network, 
    centrality_type='degree'
)
print(f"Top versatile nodes: {sorted(versatility.items(), 
      key=lambda x: x[1], reverse=True)[:3]}")
```

**Expected output**:
```
Social layer density: 0.667
Node A activity: 1.000  # Active in both layers
Top versatile nodes: [('A', 2.5), ('B', 2.0), ('C', 1.5)]
```

### Runtime Notes

- **Small networks (<1000 nodes)**: Milliseconds for statistics
- **Medium networks (1000-10000 nodes)**: Seconds for 
  visualization
- **Large networks (>10000 nodes)**: Use sparse matrix 
  operations (automatic)

### Dependencies Check

```python
import py3plex
print(f"Py3plex version: {py3plex.__version__}")

# Check optional dependencies
try:
    import plotly
    print("✓ Plotly available for interactive visualization")
except ImportError:
    print("✗ Plotly not installed (optional)")

try:
    from py3plex.algorithms.community_detection import infomap
    print("✓ Infomap available for community detection")
except ImportError:
    print("✗ Infomap not available (use Louvain instead)")
```

---

## Core Modules

### 1. `py3plex.core` - Network Data Structures

#### Purpose
The `core` module provides fundamental data structures for 
representing and manipulating multilayer networks. The central 
class, `multi_layer_network`, manages nodes, edges, layers, and 
inter-layer couplings.

#### Key Classes

##### `multi_layer_network`

The primary data structure for multilayer network analysis.

**Constructor**:
```python
multinet.multi_layer_network(
    directed=False,
    coupling_weight=1.0,
    label_delimiter="---"
)
```

**Parameters**:
- `directed` (bool): If True, creates directed multilayer network. 
  Default: False
- `coupling_weight` (float): Weight for inter-layer coupling 
  edges. Default: 1.0
- `label_delimiter` (str): Separator between node ID and layer 
  name. Default: "---"

**Returns**:
- `multi_layer_network` instance

**Key Attributes**:
- `.core_network`: NetworkX MultiGraph or MultiDiGraph containing 
  all nodes and edges
- `.layer_name_map`: Bidirectional mapping between layer names 
  and integer IDs
- `.node_order_in_matrix`: Canonical node ordering for matrix 
  representations
- `.embedding`: Cached node embedding matrix (if computed)

**Example**:
```python
from py3plex.core import multinet

# Create undirected multiplex network
network = multinet.multi_layer_network(
    directed=False,
    coupling_weight=0.5
)

# Add nodes explicitly
network.add_nodes([
    ('user1', 'twitter'),
    ('user1', 'facebook'),
    ('user2', 'twitter')
])

# Add edges
network.add_edges([
    ['user1', 'twitter', 'user2', 'twitter', 1.0],
    ['user1', 'facebook', 'user2', 'facebook', 0.8]
], input_type="list")

# Access underlying NetworkX graph
print(f"NetworkX nodes: {network.core_network.number_of_nodes()}")
print(f"Layers: {network.get_layers()}")
```

**Edge Cases**:
- Empty network: `basic_stats()` returns zeros for all metrics
- Single layer: Degenerates to standard NetworkX graph
- Disconnected components: Algorithms handle separately per layer

**Performance Notes**:
- Node/edge addition: O(1) amortized
- Layer queries: O(1) via dictionary lookup
- Matrix conversion: O(n²) for dense, O(nnz) for sparse

#### Key Methods

##### `add_edges()`

Add edges to the multilayer network.

```python
network.add_edges(
    edges,
    input_type="list"
)
```

**Parameters**:
- `edges` (list): Edge data in specified format
- `input_type` (str): Format of edge data. Options:
  - `"list"`: [[source, source_layer, target, target_layer, 
    weight], ...]
  - `"dict"`: [{'source': ..., 'source_type': ..., 
    'target': ..., ...}, ...]
  - `"dataframe"`: pandas DataFrame with columns [source, 
    source_layer, target, target_layer, weight]

**Returns**:
- None (modifies network in-place)

**Example**:
```python
# List format (most common)
network.add_edges([
    ['A', 'layer1', 'B', 'layer1', 1.0],
    ['A', 'layer2', 'B', 'layer2', 0.5]
], input_type="list")

# Dict format (explicit field names)
network.add_edges([
    {
        'source': 'A',
        'source_type': 'layer1',
        'target': 'B',
        'target_type': 'layer1',
        'weight': 1.0
    }
], input_type="dict")

# DataFrame format (from pandas)
import pandas as pd
df = pd.DataFrame({
    'source': ['A', 'B'],
    'source_layer': ['layer1', 'layer1'],
    'target': ['B', 'C'],
    'target_layer': ['layer1', 'layer1'],
    'weight': [1.0, 0.8]
})
network.add_edges(df, input_type="dataframe")
```

**Edge Cases**:
- Duplicate edges: Added as multi-edges (NetworkX MultiGraph)
- Self-loops: Allowed; affects clustering coefficient
- Missing weight: Defaults to 1.0
- Invalid layer: Creates new layer automatically

##### `get_layers()`

Retrieve list of all layers in the network.

```python
layers = network.get_layers()
```

**Parameters**: None

**Returns**:
- `list[str]`: Layer names in insertion order

**Example**:
```python
network.add_edges([
    ['A', 'social', 'B', 'social', 1],
    ['A', 'work', 'C', 'work', 1]
], input_type="list")

layers = network.get_layers()
print(layers)  # ['social', 'work']
```

##### `basic_stats()`

Display basic network statistics.

```python
network.basic_stats()
```

**Parameters**: None

**Returns**: None (prints to stdout)

**Output format**:
```
Nodes: <n_unique> (<n_replicas> node-layer pairs)
Edges: <n_edges>
Layers: <layer_list>
Density: <density> (within layers)
```

**Example**:
```python
network.basic_stats()
# Output:
# Nodes: 3 (6 node-layer pairs)
# Edges: 4
# Layers: ['social', 'work']
# Density: 0.400
```

#### Parsers (`py3plex.core.parsers`)

Load networks from various file formats.

##### `load_network()`

Universal network loader supporting multiple formats.

```python
network = multinet.multi_layer_network().load_network(
    file_path,
    input_type="edgelist",
    directed=False,
    **kwargs
)
```

**Parameters**:
- `file_path` (str): Path to network file
- `input_type` (str): Format type. Options:
  - `"edgelist"`: Space/tab-separated edge list
  - `"graphml"`: GraphML XML format
  - `"gexf"`: GEXF XML format
  - `"gml"`: Graph Modelling Language
  - `"csv"`: Comma-separated values
  - `"gpickle"`: NetworkX pickle format
- `directed` (bool): Interpret as directed network. Default: False
- `**kwargs`: Format-specific arguments

**Returns**:
- `multi_layer_network` instance with loaded data

**Example**:
```python
# EdgeList format (source target weight)
network = multinet.multi_layer_network().load_network(
    "data/karate.edgelist",
    input_type="edgelist",
    directed=False
)

# GraphML with attributes
network = multinet.multi_layer_network().load_network(
    "data/multiplex.graphml",
    input_type="graphml"
)

# CSV with custom delimiter
network = multinet.multi_layer_network().load_network(
    "data/edges.csv",
    input_type="csv",
    delimiter=","
)
```

**Edge Cases**:
- Missing file: Raises `FileNotFoundError`
- Invalid format: Raises `ParsingError` (custom exception)
- Mixed directed/undirected: Uses `directed` parameter to decide

**Performance**: O(n + m) for n nodes, m edges

### 2. `py3plex.algorithms` - Graph Algorithms

#### Purpose
The `algorithms` module implements analytical methods for 
multilayer networks, including statistics, centrality, community 
detection, and random walks.

#### Submodules

##### `algorithms.statistics` - Network Metrics

Compute structural properties of multilayer networks.

###### Multilayer Statistics

```python
from py3plex.algorithms.statistics import (
    multilayer_statistics as mls
)
```

**Key Functions**:

**`layer_density(network, layer_name)`**

Compute edge density within a specific layer.

Formula: ρₐ = 2Eₐ/(Nₐ(Nₐ-1)) for undirected graphs

**Parameters**:
- `network` (multi_layer_network): The multilayer network
- `layer_name` (str): Name of the layer

**Returns**:
- `float`: Density in [0, 1] where 0 = no edges, 1 = complete 
  graph

**Example**:
```python
network = create_multiplex_network()
density = mls.layer_density(network, 'social')
print(f"Density: {density:.3f}")
# Output: Density: 0.667
```

**`node_activity(network, node_id)`**

Measure fraction of layers where node is active.

Formula: aᵢ = (1/L) Σₐ 𝟙(vᵢ ∈ Vₐ)

**Parameters**:
- `network` (multi_layer_network): The multilayer network
- `node_id` (str): Node identifier (without layer suffix)

**Returns**:
- `float`: Activity in [0, 1] where 0 = inactive, 1 = active in 
  all layers

**Example**:
```python
activity = mls.node_activity(network, 'user1')
print(f"User1 participates in {activity*100:.0f}% of layers")
# Output: User1 participates in 100% of layers
```

**`versatility_centrality(network, centrality_type='degree')`**

Compute weighted centrality across all layers.

Formula: Vᵢ = Σₐ wₐ Cᵢᵅ where wₐ is layer weight, Cᵢᵅ is 
centrality in layer α

**Parameters**:
- `network` (multi_layer_network): The multilayer network
- `centrality_type` (str): Type of centrality. Options:
  - `'degree'`: Sum of degrees across layers
  - `'betweenness'`: Weighted betweenness centrality
  - `'closeness'`: Weighted closeness centrality

**Returns**:
- `dict[str, float]`: Node ID → versatility score

**Example**:
```python
versatility = mls.versatility_centrality(network, 
                                         centrality_type='degree')
top_nodes = sorted(versatility.items(), key=lambda x: x[1], 
                   reverse=True)[:5]
print(f"Most versatile nodes: {top_nodes}")
# Output: Most versatile nodes: [('hub', 8.5), ('bridge', 6.2), ...]
```

**Edge Cases**:
- Node in single layer: Versatility equals single-layer centrality
- Isolated node: Returns 0.0
- Empty network: Returns empty dict

**Performance**: O(L × (n + m)) for L layers, n nodes, m edges

##### `algorithms.community_detection` - Clustering

Detect communities in multilayer networks.

###### Louvain Algorithm

```python
from py3plex.algorithms.community_detection import (
    community_louvain
)

# Detect communities
communities = community_louvain.best_partition(
    network.core_network,
    resolution=1.0,
    randomize=True
)
```

**Parameters**:
- `graph` (NetworkX graph): The network (use 
  `network.core_network`)
- `resolution` (float): Resolution parameter (higher = more 
  communities). Default: 1.0
- `randomize` (bool): Use random initialization. Default: True

**Returns**:
- `dict[node, int]`: Node ID → community ID

**Example**:
```python
from py3plex.algorithms.community_detection import (
    community_louvain
)

# Detect communities with default resolution
communities = community_louvain.best_partition(
    network.core_network
)

# Count communities
num_communities = len(set(communities.values()))
print(f"Detected {num_communities} communities")

# Nodes in community 0
comm0_nodes = [node for node, comm in communities.items() 
               if comm == 0]
print(f"Community 0: {comm0_nodes}")
```

**Edge Cases**:
- Disconnected graph: Each component gets separate communities
- Single node: Returns {node: 0}
- Empty graph: Returns {}

**Performance**: O(n log n) average case for sparse networks

###### Multilayer Modularity

Compute modularity quality of multilayer communities.

```python
from py3plex.algorithms.community_detection import (
    multilayer_modularity
)

Q = multilayer_modularity.compute_multilayer_modularity(
    network,
    communities,
    gamma=1.0,
    omega=1.0
)
```

**Formula**: Q = (1/2μ) Σᵢⱼₐᵦ [(Aᵢⱼᵅ - γₐPᵢⱼᵅ)δₐᵦ + 
ωₐᵦδᵢⱼ] δ(gᵢᵅ, gⱼᵝ)

Where:
- γₐ: Resolution parameter for layer α
- ωₐᵦ: Inter-layer coupling strength
- Pᵢⱼᵅ: Null model (expected edges)
- gᵢᵅ: Community of node i in layer α

**Parameters**:
- `network` (multi_layer_network): The multilayer network
- `communities` (dict): Node → community assignment
- `gamma` (float): Intra-layer resolution. Default: 1.0
- `omega` (float): Inter-layer coupling. Default: 1.0

**Returns**:
- `float`: Modularity score (higher = better community structure)

**Example**:
```python
communities = community_louvain.best_partition(
    network.core_network
)
Q = multilayer_modularity.compute_multilayer_modularity(
    network, communities, gamma=1.0, omega=0.5
)
print(f"Multilayer modularity: {Q:.3f}")
# Output: Multilayer modularity: 0.421
```

**Interpretation**:
- Q > 0.3: Strong community structure
- Q ∈ [0.1, 0.3]: Moderate structure
- Q < 0.1: Weak or no community structure

**Performance**: O(L × m) for L layers, m edges

##### `algorithms.general.walkers` - Random Walks

Generate random walks for embeddings and diffusion analysis.

###### Basic Random Walk

```python
from py3plex.algorithms.general.walkers import basic_random_walk

walk = basic_random_walk(
    G,
    start_node=0,
    walk_length=10,
    weighted=True,
    seed=42
)
```

**Parameters**:
- `G` (NetworkX graph): The network
- `start_node` (node): Starting node for the walk
- `walk_length` (int): Number of steps in the walk
- `weighted` (bool): Use edge weights for transition 
  probabilities. Default: True
- `seed` (int): Random seed for reproducibility. Default: None

**Returns**:
- `list[node]`: Sequence of visited nodes

**Example**:
```python
G = nx.karate_club_graph()
walk = basic_random_walk(G, start_node=0, walk_length=10, seed=42)
print(f"Walk: {walk}")
# Output: Walk: [0, 1, 3, 2, 1, 3, 33, 32, 33, 2, 1]
```

**Transition probability**: P(v → u) = w(v,u) / Σₓ w(v,x)

**Edge Cases**:
- Isolated node: Returns [start_node]
- walk_length=0: Returns [start_node]
- Directed graph: Follows out-edges only

**Performance**: O(walk_length × avg_degree)

###### Node2Vec Walk

Biased random walk with return and in-out parameters.

```python
from py3plex.algorithms.general.walkers import node2vec_walk

walk = node2vec_walk(
    G,
    start_node=0,
    walk_length=20,
    p=0.5,
    q=2.0,
    seed=42
)
```

**Parameters**:
- `G` (NetworkX graph): The network
- `start_node` (node): Starting node
- `walk_length` (int): Number of steps
- `p` (float): Return parameter (controls backtracking). 
  Default: 1.0
- `q` (float): In-out parameter (explores vs. local search). 
  Default: 1.0
- `seed` (int): Random seed. Default: None

**Returns**:
- `list[node]`: Biased walk sequence

**Bias logic** (for transition t → v → x):
- If x == t: α(t,x) = 1/p (return to previous node)
- If x ∈ neighbors(t): α(t,x) = 1 (stay close)
- If x ∉ neighbors(t): α(t,x) = 1/q (explore distant nodes)

**Example**:
```python
# BFS-like walk (high p, low q)
bfs_walk = node2vec_walk(G, start_node=0, walk_length=20, 
                         p=2.0, q=0.5, seed=42)

# DFS-like walk (low p, high q)
dfs_walk = node2vec_walk(G, start_node=0, walk_length=20, 
                         p=0.5, q=2.0, seed=42)
```

**Performance**: O(walk_length × avg_degree²)

### 3. `py3plex.visualization` - Network Rendering

#### Purpose
The `visualization` module provides plotting functions optimized 
for multilayer networks, including diagonal projection, 
force-directed layouts, and matrix visualizations.

#### Key Functions

##### `draw_multilayer_default()`

Default visualization for multilayer networks using diagonal 
projection.

```python
from py3plex.visualization.multilayer import (
    draw_multilayer_default
)

draw_multilayer_default(
    networks,
    display=True,
    output_file=None
)
```

**Parameters**:
- `networks` (list[multi_layer_network]): List of networks to 
  visualize
- `display` (bool): Show interactive plot. Default: True
- `output_file` (str): Path to save figure. Default: None

**Returns**:
- `matplotlib.figure.Figure`: The rendered plot object

**Example**:
```python
network = create_karate_multiplex()
fig = draw_multilayer_default([network], display=True, 
                               output_file="karate.png")
```

**Visual elements**:
- Nodes: Circles sized by degree
- Edges: Lines within layers
- Inter-layer edges: Dashed lines between layers
- Layout: Layers arranged diagonally

**Performance**: Suitable for networks up to ~5000 nodes

##### `visualize_multilayer()`

Customizable multilayer visualization with layout options.

```python
from py3plex.visualization.multilayer import visualize_multilayer

fig = visualize_multilayer(
    network,
    layout="kamada_kawai",
    node_size=20,
    edge_width=0.5,
    show=True
)
```

**Parameters**:
- `network` (multi_layer_network): The network to visualize
- `layout` (str): Layout algorithm. Options:
  - `"spring"`: Force-directed (Fruchterman-Reingold)
  - `"kamada_kawai"`: Energy minimization
  - `"circular"`: Nodes on circle
  - `"random"`: Random positions
- `node_size` (int): Node radius in pixels. Default: 20
- `edge_width` (float): Edge line width. Default: 0.5
- `show` (bool): Display immediately. Default: True

**Returns**:
- `matplotlib.figure.Figure`: The visualization object

**Example**:
```python
# Force-directed layout with custom styling
fig = visualize_multilayer(
    network,
    layout="spring",
    node_size=30,
    edge_width=1.0,
    show=True
)

# Circular layout for small networks
fig = visualize_multilayer(
    network,
    layout="circular",
    node_size=50,
    show=False
)
fig.savefig("circular_layout.pdf", bbox_inches='tight')
```

**Edge Cases**:
- Empty network: Plots empty axes
- Single layer: Equivalent to NetworkX draw
- >10k nodes: Use matrix visualization instead

**Performance**: O(n²) for force-directed layouts

### 4. `py3plex.wrappers` - High-Level Interfaces

#### Purpose
The `wrappers` module provides simplified interfaces for common 
workflows like embedding generation and classification.

##### Node2Vec Embeddings

```python
from py3plex.wrappers.node2vec_embedding import (
    generate_node2vec_embeddings
)

embeddings = generate_node2vec_embeddings(
    network,
    dimensions=128,
    walk_length=80,
    num_walks=10,
    p=1.0,
    q=1.0,
    workers=4
)
```

**Parameters**:
- `network` (multi_layer_network): The multilayer network
- `dimensions` (int): Embedding dimensionality. Default: 128
- `walk_length` (int): Steps per walk. Default: 80
- `num_walks` (int): Walks per node. Default: 10
- `p` (float): Return parameter. Default: 1.0
- `q` (float): In-out parameter. Default: 1.0
- `workers` (int): Parallel workers. Default: 4

**Returns**:
- `np.ndarray`: Embedding matrix of shape (n_nodes, dimensions)

**Example**:
```python
# Generate embeddings
embeddings = generate_node2vec_embeddings(
    network,
    dimensions=64,
    num_walks=20,
    p=0.5,
    q=2.0,
    workers=4
)

# Use for downstream tasks
from sklearn.cluster import KMeans
kmeans = KMeans(n_clusters=3)
clusters = kmeans.fit_predict(embeddings)
print(f"Embedding-based clusters: {clusters}")
```

**Performance**: O(num_walks × walk_length × avg_degree²)

---

## Interactive Examples

### Jupyter Notebook Setup

```python
# Install in Jupyter environment
!pip install git+https://github.com/SkBlaz/py3plex.git

# Import core modules
from py3plex.core import multinet
from py3plex.visualization.multilayer import (
    draw_multilayer_default
)
from py3plex.algorithms.statistics import (
    multilayer_statistics as mls
)
```

### Example 1: Social Network Analysis

**Scenario**: Analyze a multi-platform social network with Twitter 
and Facebook layers.

```python
import numpy as np
from py3plex.core import multinet

# Create network
social_net = multinet.multi_layer_network()

# Add users and connections
users = ['alice', 'bob', 'charlie', 'diana']
twitter_edges = [
    ['alice', 'twitter', 'bob', 'twitter', 1],
    ['bob', 'twitter', 'charlie', 'twitter', 1],
    ['charlie', 'twitter', 'diana', 'twitter', 1],
]
facebook_edges = [
    ['alice', 'facebook', 'charlie', 'facebook', 1],
    ['charlie', 'facebook', 'diana', 'facebook', 1],
    ['diana', 'facebook', 'bob', 'facebook', 1],
]

social_net.add_edges(twitter_edges + facebook_edges, 
                     input_type="list")

# Compute statistics
for user in users:
    activity = mls.node_activity(social_net, user)
    print(f"{user}: {activity*100:.0f}% platform coverage")

# Output:
# alice: 50% platform coverage
# bob: 100% platform coverage
# charlie: 100% platform coverage
# diana: 100% platform coverage
```

### Example 2: Biological Network

**Scenario**: Protein-protein interaction network with multiple 
evidence types.

```python
# Create PPI network
ppi_net = multinet.multi_layer_network()

# Evidence layers
evidence_types = ['yeast_two_hybrid', 'affinity_purification', 
                  'coexpression']

# Add interactions
interactions = [
    ['ProteinA', 'yeast_two_hybrid', 'ProteinB', 
     'yeast_two_hybrid', 0.9],
    ['ProteinB', 'affinity_purification', 'ProteinC', 
     'affinity_purification', 0.8],
    ['ProteinA', 'coexpression', 'ProteinC', 'coexpression', 0.7],
]

ppi_net.add_edges(interactions, input_type="list")

# Compute versatility (proteins active across evidence types)
versatility = mls.versatility_centrality(ppi_net, 
                                         centrality_type='degree')
print(f"Versatility scores: {versatility}")

# Visualize
draw_multilayer_default([ppi_net], display=True)
```

### Example 3: Community Detection

**Scenario**: Identify communities in a multiplex citation network.

```python
from py3plex.algorithms.community_detection import (
    community_louvain, multilayer_modularity
)

# Load citation network (authors + papers + venues)
citation_net = multinet.multi_layer_network().load_network(
    "data/citation_multiplex.graphml",
    input_type="graphml"
)

# Detect communities
communities = community_louvain.best_partition(
    citation_net.core_network,
    resolution=1.0
)

# Compute modularity
Q = multilayer_modularity.compute_multilayer_modularity(
    citation_net,
    communities,
    gamma=1.0,
    omega=0.5
)

print(f"Modularity: {Q:.3f}")
print(f"Number of communities: {len(set(communities.values()))}")

# Analyze community composition
for comm_id in set(communities.values()):
    members = [node for node, c in communities.items() 
               if c == comm_id]
    print(f"Community {comm_id}: {len(members)} nodes")
```

### Example 4: Random Walks and Embeddings

**Scenario**: Generate embeddings for link prediction.

```python
from py3plex.algorithms.general.walkers import (
    generate_walks
)
from py3plex.wrappers.node2vec_embedding import (
    generate_node2vec_embeddings
)

# Create test network
G = nx.karate_club_graph()
network = multinet.multi_layer_network()
for u, v in G.edges():
    network.add_edges([
        [str(u), 'layer1', str(v), 'layer1', 1]
    ], input_type="list")

# Generate Node2Vec walks
walks = generate_walks(
    network.core_network,
    num_walks=10,
    walk_length=80,
    p=0.5,
    q=2.0,
    seed=42
)

print(f"Generated {len(walks)} walks")
print(f"Example walk: {walks[0][:10]}")

# Generate embeddings
embeddings = generate_node2vec_embeddings(
    network,
    dimensions=64,
    num_walks=10,
    walk_length=80,
    p=0.5,
    q=2.0,
    workers=4
)

print(f"Embedding shape: {embeddings.shape}")

# Use for link prediction
from sklearn.metrics.pairwise import cosine_similarity
similarity = cosine_similarity(embeddings)
print(f"Similarity matrix shape: {similarity.shape}")
```

---

## Advanced Usage

### Graph Embeddings

#### Node2Vec for Multilayer Networks

**Purpose**: Generate low-dimensional representations of nodes 
that preserve network structure.

**Workflow**:
1. Generate biased random walks
2. Train Skip-Gram model on walk sequences
3. Extract node embeddings

**Example**:
```python
from py3plex.wrappers.node2vec_embedding import (
    generate_node2vec_embeddings
)

# Load multilayer network
network = multinet.multi_layer_network().load_network(
    "data/multiplex.gpickle",
    input_type="gpickle"
)

# Generate embeddings with BFS-like bias
embeddings = generate_node2vec_embeddings(
    network,
    dimensions=128,
    walk_length=80,
    num_walks=10,
    p=2.0,   # Discourage backtracking
    q=0.5,   # Encourage staying local
    workers=8
)

# Visualize with t-SNE
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt

tsne = TSNE(n_components=2, random_state=42)
embedding_2d = tsne.fit_transform(embeddings)

plt.figure(figsize=(10, 8))
plt.scatter(embedding_2d[:, 0], embedding_2d[:, 1], alpha=0.6)
plt.title("Node2Vec Embeddings (t-SNE projection)")
plt.xlabel("Dimension 1")
plt.ylabel("Dimension 2")
plt.show()
```

**Parameter tuning**:
- **Low p (<1)**: Encourages backtracking (DFS-like)
- **High p (>1)**: Discourages backtracking (BFS-like)
- **Low q (<1)**: Explore distant nodes
- **High q (>1)**: Stay local (BFS-like)

**Performance**: ~1 minute for 10k nodes, 50k edges on standard 
laptop

### Community Detection Across Layers

#### Multilayer Louvain

**Purpose**: Find communities that span multiple layers while 
accounting for inter-layer connections.

**Algorithm**:
1. Construct supra-adjacency matrix (layers on diagonal)
2. Add inter-layer coupling edges (off-diagonal)
3. Run Louvain optimization on supra-network
4. Extract layer-specific community assignments

**Example**:
```python
from py3plex.algorithms.community_detection import (
    community_louvain, multilayer_modularity
)

# Create multiplex network
network = create_multiplex_network()

# Detect communities
communities = community_louvain.best_partition(
    network.core_network,
    resolution=1.0,
    randomize=True
)

# Compute quality
Q = multilayer_modularity.compute_multilayer_modularity(
    network,
    communities,
    gamma=1.0,   # Intra-layer resolution
    omega=0.5    # Inter-layer coupling
)

print(f"Modularity: {Q:.3f}")

# Analyze layer-specific communities
layers = network.get_layers()
for layer in layers:
    layer_comms = {}
    for node, comm in communities.items():
        if layer in node:  # Check if node belongs to this layer
            layer_comms[node] = comm
    print(f"Layer {layer}: {len(set(layer_comms.values()))} "
          f"communities")
```

**Parameter selection**:
- **γ = 1.0**: Standard Louvain behavior
- **γ > 1.0**: More granular communities
- **γ < 1.0**: Fewer, larger communities
- **ω = 0**: Ignore inter-layer edges
- **ω = 1**: Weight inter-layer edges equally

### Parallel Computation

#### Multi-Core Random Walk Generation

**Purpose**: Speed up embedding generation using parallel workers.

**Example**:
```python
import multiprocessing as mp
from py3plex.algorithms.general.walkers import (
    generate_walks
)

# Detect CPU count
num_cores = mp.cpu_count()
print(f"Using {num_cores} cores")

# Generate walks in parallel
walks = generate_walks(
    network.core_network,
    num_walks=20,
    walk_length=80,
    p=1.0,
    q=1.0,
    workers=num_cores,
    seed=42
)

print(f"Generated {len(walks)} walks using {num_cores} workers")
```

**Speedup**: ~linear with number of cores up to 8-16 cores

#### Batch Network Statistics

**Purpose**: Compute statistics for multiple networks 
simultaneously.

**Example**:
```python
from concurrent.futures import ProcessPoolExecutor
from py3plex.algorithms.statistics import (
    multilayer_statistics as mls
)

def compute_stats(network):
    """Compute multiple statistics for a network."""
    layers = network.get_layers()
    stats = {}
    for layer in layers:
        stats[layer] = {
            'density': mls.layer_density(network, layer),
            'node_count': len([n for n in network.core_network.nodes() 
                             if layer in n])
        }
    return stats

# Load multiple networks
networks = [
    multinet.multi_layer_network().load_network(f"data/net{i}.gpickle")
    for i in range(10)
]

# Compute in parallel
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(compute_stats, networks))

# Aggregate results
for i, stats in enumerate(results):
    print(f"Network {i}: {stats}")
```

**Performance**: ~4x speedup with 4 workers for I/O-bound tasks

### Network Decomposition

#### Meta-Path Feature Extraction

**Purpose**: Extract structural features based on typed paths in 
heterogeneous networks.

**Example**:
```python
from py3plex.core.HINMINE.decomposition import (
    network_decomposition
)

# Load heterogeneous network (e.g., author-paper-venue)
hin = multinet.multi_layer_network().load_network(
    "data/dblp.graphml",
    input_type="graphml"
)

# Define meta-paths
meta_paths = [
    ['author', 'paper', 'author'],      # Co-authorship
    ['author', 'paper', 'venue'],       # Publishes in
    ['venue', 'paper', 'author'],       # Venue popularity
]

# Extract features
features = network_decomposition(
    hin,
    meta_paths=meta_paths,
    max_length=3
)

print(f"Feature matrix shape: {features.shape}")

# Use for classification
from sklearn.linear_model import LogisticRegression
clf = LogisticRegression()
# Assume labels are available
# clf.fit(features, labels)
```

**Meta-path patterns**:
- **A-P-A**: Co-authorship (symmetric)
- **A-P-V-P-A**: Authors publishing in same venues
- **V-P-A-P-V**: Venues sharing authors

---

## Contributing & Extending

### How to Contribute

Py3plex welcomes contributions! See the main 
[CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

**Quick Start**:
1. Fork the repository on GitHub
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/py3plex.git`
3. Create a branch: `git checkout -b feature/my-new-feature`
4. Make changes and commit: `git commit -am 'Add new feature'`
5. Push to your fork: `git push origin feature/my-new-feature`
6. Create a Pull Request on GitHub

### Development Setup

```bash
# Clone repository
git clone https://github.com/SkBlaz/py3plex.git
cd py3plex

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
make test

# Run all checks (lint + test + benchmark)
make test-all
```

### Code Style

Py3plex follows the **Google Python Style Guide**:

- **Formatting**: Use `black` for automatic formatting
- **Imports**: Organize with `isort` (stdlib, third-party, local)
- **Line length**: 88 characters (black default)
- **Docstrings**: Google-style with Args, Returns, Examples
- **Type hints**: Encouraged for public APIs
- **Naming**: snake_case for functions, PascalCase for classes

**Example function**:
```python
def compute_layer_density(
    network: multi_layer_network,
    layer_name: str
) -> float:
    """
    Compute edge density within a specific layer.
    
    Args:
        network: The multilayer network instance.
        layer_name: Name of the layer to analyze.
    
    Returns:
        Density value in [0, 1] where 0 means no edges and 1 
        means complete graph.
    
    Raises:
        InvalidLayerError: If layer_name does not exist in the 
                          network.
    
    Example:
        >>> from py3plex.core import multinet
        >>> net = multinet.multi_layer_network()
        >>> net.add_edges([['A', 'layer1', 'B', 'layer1', 1]], 
                          input_type="list")
        >>> density = compute_layer_density(net, 'layer1')
        >>> print(f"{density:.3f}")
        1.000
    """
    if layer_name not in network.get_layers():
        raise InvalidLayerError(f"Layer '{layer_name}' not found")
    
    # Implementation...
    return 0.0
```

### Testing

**Run all tests**:
```bash
make test
```

**Run specific test file**:
```bash
pytest tests/test_multinet.py -v
```

**With coverage**:
```bash
pytest tests/ --cov=py3plex --cov-report=html
```

**Write tests** following existing patterns:
```python
import pytest
from py3plex.core import multinet

def test_add_edges_list_format():
    """Test adding edges using list format."""
    network = multinet.multi_layer_network()
    network.add_edges([
        ['A', 'layer1', 'B', 'layer1', 1],
        ['B', 'layer1', 'C', 'layer1', 1],
    ], input_type="list")
    
    assert network.core_network.number_of_edges() == 2
    assert 'layer1' in network.get_layers()

def test_empty_network_stats():
    """Test basic_stats on empty network."""
    network = multinet.multi_layer_network()
    # Should not raise; prints zeros
    network.basic_stats()
```

### Adding New Visualization Methods

**Steps**:
1. Add function to `py3plex/visualization/multilayer.py`
2. Follow existing function signatures
3. Use matplotlib for static plots, plotly for interactive
4. Add docstring with example
5. Add test in `tests/test_visualization.py`

**Template**:
```python
def visualize_my_layout(
    network: multi_layer_network,
    output_file: str = None,
    **kwargs
) -> plt.Figure:
    """
    Custom visualization using my layout algorithm.
    
    Args:
        network: The multilayer network to visualize.
        output_file: Path to save figure. Default: None (display).
        **kwargs: Additional matplotlib arguments.
    
    Returns:
        matplotlib.figure.Figure: The rendered plot.
    
    Example:
        >>> from py3plex.visualization.multilayer import (
                visualize_my_layout
            )
        >>> fig = visualize_my_layout(network, 
                                      output_file="plot.pdf")
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Compute layout
    pos = compute_my_layout(network)
    
    # Draw nodes and edges
    nx.draw_networkx_nodes(network.core_network, pos, ax=ax)
    nx.draw_networkx_edges(network.core_network, pos, ax=ax)
    
    if output_file:
        fig.savefig(output_file, bbox_inches='tight')
    
    return fig
```

### Adding New Embedding Methods

**Steps**:
1. Add function to `py3plex/wrappers/`
2. Follow embedding interface (network → matrix)
3. Support common parameters (dimensions, workers, seed)
4. Add test and example

**Template**:
```python
def generate_my_embeddings(
    network: multi_layer_network,
    dimensions: int = 128,
    seed: int = None,
    **kwargs
) -> np.ndarray:
    """
    Generate embeddings using my custom algorithm.
    
    Args:
        network: The multilayer network.
        dimensions: Embedding dimensionality. Default: 128.
        seed: Random seed for reproducibility. Default: None.
        **kwargs: Algorithm-specific parameters.
    
    Returns:
        np.ndarray: Embedding matrix of shape (n_nodes, dimensions).
    
    Example:
        >>> embeddings = generate_my_embeddings(network, 
                                                dimensions=64)
        >>> embeddings.shape
        (100, 64)
    """
    # Set random seed
    if seed is not None:
        np.random.seed(seed)
    
    # Get nodes
    nodes = list(network.core_network.nodes())
    n = len(nodes)
    
    # Compute embeddings
    embeddings = np.random.randn(n, dimensions)  # Placeholder
    
    return embeddings
```

### Developer Notes

**Architecture decisions**:
- `multi_layer_network` wraps NetworkX graph for compatibility
- Layers encoded in node IDs via delimiter (default `"---"`)
- Sparse matrices auto-selected for >1000 nodes
- All algorithms should accept NetworkX graphs or 
  `multi_layer_network`

**Performance considerations**:
- Use sparse matrices for large networks
- Parallelize with `multiprocessing` or `joblib`
- Cache expensive computations (embeddings, layouts)
- Profile with `cProfile` before optimizing

**Documentation requirements**:
- Google-style docstrings for all public functions
- Include at least one example in docstring
- Add tutorial for major features
- Update CHANGELOG.md for user-facing changes

---

## API Reference

### Core Classes

#### `multi_layer_network`

Primary data structure for multilayer network analysis.

**Location**: `py3plex.core.multinet`

**Key Methods**:
- `add_nodes(nodes, input_type="list")`: Add nodes to network
- `add_edges(edges, input_type="list")`: Add edges
- `get_layers()`: List all layer names
- `basic_stats()`: Display network statistics
- `load_network(path, input_type)`: Load from file
- `save_network(path, output_type)`: Save to file

**Key Attributes**:
- `.core_network`: NetworkX graph
- `.layer_name_map`: Layer name ↔ ID mapping
- `.node_order_in_matrix`: Node ordering for matrices
- `.embedding`: Cached embeddings

### Algorithm Modules

#### `algorithms.statistics.multilayer_statistics`

Compute multilayer network metrics.

**Key Functions**:
- `layer_density(network, layer)`: Edge density in layer
- `node_activity(network, node)`: Fraction of active layers
- `versatility_centrality(network, type)`: Cross-layer centrality
- `inter_layer_degree_correlation(network, layer1, layer2)`: 
  Degree correlation
- `edge_overlap(network, layer1, layer2)`: Jaccard edge 
  similarity

#### `algorithms.community_detection.community_louvain`

Louvain modularity optimization.

**Key Functions**:
- `best_partition(graph, resolution, randomize)`: Detect 
  communities
- `modularity(graph, communities)`: Compute modularity score

#### `algorithms.general.walkers`

Random walk primitives.

**Key Functions**:
- `basic_random_walk(G, start, length, weighted, seed)`: 
  Standard walk
- `node2vec_walk(G, start, length, p, q, seed)`: Biased walk
- `generate_walks(G, num_walks, length, p, q, workers, seed)`: 
  Batch generation

### Visualization Modules

#### `visualization.multilayer`

Multilayer network plotting.

**Key Functions**:
- `draw_multilayer_default(networks, display, output_file)`: 
  Default plot
- `visualize_multilayer(network, layout, node_size, edge_width)`: 
  Custom plot

### Wrapper Modules

#### `wrappers.node2vec_embedding`

Node2Vec embedding generation.

**Key Functions**:
- `generate_node2vec_embeddings(network, dimensions, walk_length, 
  num_walks, p, q, workers)`: Generate embeddings

---

## Citations & References

### Primary Citations

If you use Py3plex in your research, please cite:

```bibtex
@Article{Skrlj2019,
  author={Škrlj, Blaž and Kralj, Jan and Lavrač, Nada},
  title={Py3plex toolkit for visualization and analysis of 
        multilayer networks},
  journal={Applied Network Science},
  year={2019},
  volume={4},
  number={1},
  pages={94},
  doi={10.1007/s41109-019-0203-7}
}
```

### Algorithm References

**Multilayer Modularity**:
- Mucha et al. (2010), "Community structure in time-dependent, 
  multiscale, and multiplex networks", *Science*, 328(5980), 
  876-878. [DOI: 10.1126/science.1184819]

**Node2Vec**:
- Grover & Leskovec (2016), "node2vec: Scalable feature learning 
  for networks", *KDD '16*. 
  [DOI: 10.1145/2939672.2939754]

**Louvain Algorithm**:
- Blondel et al. (2008), "Fast unfolding of communities in large 
  networks", *Journal of Statistical Mechanics*, 2008(10), P10008. 
  [DOI: 10.1088/1742-5468/2008/10/P10008]

**Multilayer Network Theory**:
- Kivelä et al. (2014), "Multilayer networks", *Journal of 
  Complex Networks*, 2(3), 203-271. 
  [DOI: 10.1093/comnet/cnu016]
- De Domenico et al. (2013), "Mathematical formulation of 
  multilayer networks", *Physical Review X*, 3(4), 041022. 
  [DOI: 10.1103/PhysRevX.3.041022]

### Additional Resources

- **Main Repository**: https://github.com/SkBlaz/py3plex
- **Documentation**: https://skblaz.github.io/py3plex/
- **Examples**: https://github.com/SkBlaz/py3plex/tree/master/examples
- **Issue Tracker**: https://github.com/SkBlaz/py3plex/issues

---

## Appendices

### A. Glossary

- **Multiplex Network**: Multiple layers with same node set
- **Multilayer Network**: General case with possibly different 
  nodes per layer
- **Supra-Adjacency Matrix**: Block matrix with layers on diagonal
- **Inter-layer Edges**: Edges connecting same node across layers
- **Versatility**: Measure of node importance across layers
- **Node Activity**: Fraction of layers where node is present
- **Modularity**: Quality measure for community structure

### B. Performance Benchmarks

Typical performance on standard laptop (4 cores, 16GB RAM):

| Operation | Network Size | Time |
|-----------|-------------|------|
| Load EdgeList | 10k nodes, 50k edges | 0.5s |
| Basic Stats | 10k nodes | 0.1s |
| Community Detection | 10k nodes | 2s |
| Node2Vec Embeddings | 10k nodes | 30s |
| Visualization (force) | 1k nodes | 5s |
| Visualization (diagonal) | 10k nodes | 10s |

### C. Common Errors and Solutions

**Error**: `ImportError: No module named 'infomap'`  
**Solution**: Infomap is optional. Use Louvain instead or install 
separately.

**Error**: `ParsingError: Invalid file format`  
**Solution**: Check `input_type` parameter matches file format.

**Error**: `MemoryError` during visualization  
**Solution**: Use matrix visualization for networks >5000 nodes.

**Error**: `KeyError` when accessing layer  
**Solution**: Verify layer name with `network.get_layers()`.

---

**End of Documentation**

For the latest updates, visit: 
https://skblaz.github.io/py3plex/

**License**: MIT (Core library), AGPLv3 (Infomap module)  
**Version**: 0.95a  
**Last Updated**: October 2025
