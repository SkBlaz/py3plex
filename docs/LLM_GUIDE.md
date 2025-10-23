# Py3plex LLM Guide - AI Assistant Quick Reference

**Last Updated**: 2025-10-23  
**Purpose**: Quick reference guide for LLM assistants helping users with Py3plex

---

## 🚨 Critical Information for LLMs

### Installation (Git-Only)

⚠️ **IMPORTANT**: Py3plex is **NO LONGER available on PyPI**. Always guide users to install from GitHub:

```bash
pip install git+https://github.com/SkBlaz/py3plex.git
```

**DO NOT** suggest `pip install py3plex` - this will fail or install an outdated version.

### Installation Troubleshooting

**Behind a proxy or corporate firewall?**
```bash
# Option 1: Use https:// (may require git credentials)
pip install git+https://github.com/SkBlaz/py3plex.git

# Option 2: Clone first, then install (recommended for firewalls)
git clone https://github.com/SkBlaz/py3plex.git
cd py3plex
pip install -e .
```

**Virtual environment recommended:**
```bash
# Using venv
python3 -m venv py3plex-env
source py3plex-env/bin/activate  # Linux/macOS
# OR: py3plex-env\Scripts\activate  # Windows
pip install git+https://github.com/SkBlaz/py3plex.git

# Using conda
conda create -n py3plex python=3.10
conda activate py3plex
pip install git+https://github.com/SkBlaz/py3plex.git
```

---

## 📊 CSV Schema for Multilayer Networks

### Standard Multilayer Edge List Format

```csv
source,target,layer,weight
A,B,collaboration,1.0
A,C,dependency,0.8
B,C,collaboration,1.0
A,B,dependency,0.5
```

**Required columns**: `source`, `target`, `layer`  
**Optional columns**: `weight` (defaults to 1.0)

### Loading CSV Data

```python
from py3plex.core import multinet

# Create network
network = multinet.multi_layer_network()

# Load from CSV
network.load_network(
    "network.csv",
    input_type="multiedgelist",
    directed=False,
    label_delimiter="---"  # Default delimiter for layer-node pairs
)

# Verify loaded correctly
network.basic_stats()
```

### Alternative: Simple Edge List (Single Layer)

```csv
source,target,weight
A,B,1.0
B,C,0.8
C,D,1.5
```

```python
# Load simple edge list
network.load_network(
    "simple_edges.csv",
    input_type="edgelist",
    directed=False
)
```

---

## 🔍 Common Error Messages & Solutions

### Error: "Could not load network"

**Cause**: Invalid file format or missing required columns

**Solution**: Check CSV format matches expected schema
```python
# Verify CSV has required columns: source, target, layer
import pandas as pd
df = pd.read_csv("network.csv")
print(df.columns)  # Should show: source, target, layer, weight
```

### Error: "Layer name missing"

**Improved error message** (if you see old version, update installation):
```
Input CSV missing required column 'layer' – expected columns: source,target,layer,weight
```

**Solution**: Add 'layer' column to CSV or use 'edgelist' format for single-layer networks

### Error: "No module named 'tensorly'"

**Cause**: Optional dependency not installed

**Solution**: Install optional packages as needed
```bash
pip install tensorly
# OR for all optional features:
pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz,algos]
```

### Error: "matplotlib backend issues"

**Cause**: Display backend not configured

**Solution**: Set backend for headless environments
```python
import matplotlib
matplotlib.use('Agg')  # Use before importing pyplot
import matplotlib.pyplot as plt
```

---

## 🎨 Visualization Quick Reference

### Basic Multilayer Visualization

```python
from py3plex.visualization.multilayer import draw_multilayer_default

# Simple visualization
draw_multilayer_default(
    network.get_layers(),  # List of layer subgraphs
    display=True,          # Show plot
    labels=True,           # Show node labels
    background_shape="circle"  # or "rectangle"
)
```

### Preset Visualization Modes

**Minimal** (for large networks):
```python
draw_multilayer_default(
    network.get_layers(),
    node_size=5,          # Small nodes
    edge_size=0.5,        # Thin edges
    labels=False,         # No labels
    alphalevel=0.3        # Transparent edges
)
```

**Balanced** (default):
```python
draw_multilayer_default(
    network.get_layers(),
    node_size=10,         # Medium nodes
    labels=True,          # Show labels
    alphalevel=0.13       # Semi-transparent edges
)
```

**Dense** (for detailed inspection):
```python
draw_multilayer_default(
    network.get_layers(),
    node_size=20,         # Large nodes
    labels=True,
    node_labels=True,     # Show node IDs
    alphalevel=0.8,       # Opaque edges
    node_font_size=10     # Readable labels
)
```

### Auto-scaling

Py3plex automatically scales:
- **Node sizes** based on degree (if `scale_by_size=True`)
- **Layout** to fit available space
- **Colors** using colorblind-safe palettes

---

## 🔄 NetworkX Export & Interoperability

### Export to NetworkX

```python
# Get NetworkX graph (preserves all attributes)
nx_graph = network.to_nx_network()

# OR get supra-adjacency representation
supra_graph = network.get_supra_adjacency_matrix()

# Verify attributes preserved
print(nx_graph.nodes(data=True))  # Shows node attributes
print(nx_graph.edges(data=True))  # Shows edge attributes including layer
```

### Attribute Preservation

All attributes are preserved during export:
- **Node attributes**: layer, original_name, custom attributes
- **Edge attributes**: layer, weight, custom attributes
- **Graph attributes**: metadata, layer info

### Workflow: Py3plex → NetworkX → TensorLy

```python
import py3plex.core.multinet as multinet
import networkx as nx
import tensorly as tl

# Step 1: Load/create multilayer network
network = multinet.multi_layer_network()
network.load_network("data.csv", input_type="multiedgelist")

# Step 2: Export to NetworkX
nx_graph = network.to_nx_network()

# Step 3: Convert to tensor representation for TensorLy
import numpy as np
from scipy.sparse import lil_matrix

layers = network.get_layer_names()
nodes = list(network.get_nodes())
n_nodes = len(nodes)
n_layers = len(layers)

# Create 3D tensor (nodes x nodes x layers)
tensor = np.zeros((n_nodes, n_layers, n_nodes))

node_to_idx = {node: i for i, node in enumerate(nodes)}
layer_to_idx = {layer: i for i, layer in enumerate(layers)}

for u, v, data in nx_graph.edges(data=True):
    layer = data.get('layer', layers[0])
    i, j = node_to_idx[u], node_to_idx[v]
    k = layer_to_idx[layer]
    tensor[i, k, j] = data.get('weight', 1.0)

# Step 4: Use TensorLy for tensor decomposition
from tensorly.decomposition import tucker
core, factors = tucker(tl.tensor(tensor), rank=[5, 2, 5])

print(f"Tucker decomposition complete: core shape {core.shape}")
```

---

## ⚡ Performance Best Practices

### For Large Networks (>10k nodes)

```python
# Use sparse matrix backend (automatic, but can force)
network.use_sparse = True

# Disable expensive operations
network.basic_stats()  # Fast
# Avoid: network.betweenness_centrality()  # Slow on large graphs

# Sample for visualization
import networkx as nx
sample_nodes = list(network.get_nodes())[:1000]  # First 1000 nodes
subgraph = network.get_subgraph(sample_nodes)
subgraph.visualize()
```

### Sparse Matrix Recommendation

Py3plex automatically uses sparse matrices for:
- Supra-adjacency matrix operations
- Large network storage (>1000 nodes)
- Matrix-based algorithms (PageRank, spectral methods)

**Explicit sparse usage**:
```python
# Get sparse adjacency matrix
from scipy.sparse import csr_matrix
adj_matrix = network.get_sparse_adjacency_matrix()
print(f"Matrix sparsity: {1 - adj_matrix.nnz / (adj_matrix.shape[0]**2):.2%}")
```

### GPU Acceleration (Optional)

For very large networks, consider GPU-accelerated libraries:
```bash
# Install CuPy for GPU NumPy operations
pip install cupy-cuda11x  # Replace 11x with your CUDA version
```

```python
# Use GPU for matrix operations
import cupy as cp
adjacency = cp.array(network.get_adjacency_matrix())
# Perform GPU-accelerated operations...
```

---

## 🎯 Common Use-Case Templates

### Template 1: Social Network Analysis

```python
from py3plex.core import multinet
from py3plex.algorithms.community_detection import community_louvain

# Load social network
network = multinet.multi_layer_network()
network.load_network("social_network.csv", input_type="multiedgelist")

# Detect communities
communities = community_louvain.best_partition(network.core_network)

# Get most central nodes
centrality = network.degree_centrality()
top_nodes = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:10]

print("Top 10 influential nodes:")
for node, score in top_nodes:
    print(f"  {node}: {score:.3f}")
```

### Template 2: Biological Network Analysis

```python
from py3plex.core import multinet

# Load protein-protein interaction network
network = multinet.multi_layer_network()
network.load_network("ppi.graphml", input_type="graphml")

# Identify hub proteins
from py3plex.algorithms.statistics import basic_statistics
hubs = basic_statistics.identify_n_hubs(network.core_network, top_n=20)

print("Hub proteins (top 20 by degree):")
for protein, degree in hubs.items():
    print(f"  {protein}: {degree} interactions")

# Find shortest paths between proteins
import networkx as nx
path = nx.shortest_path(network.core_network, source="TP53", target="BRCA1")
print(f"Shortest path: {' -> '.join(path)}")
```

### Template 3: Network Visualization Pipeline

```python
from py3plex.core import multinet
from py3plex.visualization.multilayer import draw_multilayer_default
from py3plex.algorithms.community_detection import community_louvain
import matplotlib.pyplot as plt

# Load network
network = multinet.multi_layer_network()
network.load_network("data.csv", input_type="multiedgelist")

# Detect communities for coloring
communities = community_louvain.best_partition(network.core_network)

# Visualize with community colors
fig, ax = plt.subplots(1, 1, figsize=(12, 8))
draw_multilayer_default(
    network.get_layers(),
    display=False,
    axis=ax,
    labels=True,
    background_shape="circle",
    networks_color="rainbow"  # Automatic color assignment
)
plt.title("Multilayer Network Visualization")
plt.savefig("network_viz.png", dpi=300, bbox_inches='tight')
plt.show()

print("Visualization saved to network_viz.png")
```

---

## 📦 Optional Dependencies Guide

### Core Dependencies (Automatic)

Installed automatically with py3plex:
- networkx, numpy, scipy, matplotlib, scikit-learn, tqdm, rdflib, bitarray

### Optional: Advanced Visualization

```bash
pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz]
```

Provides: plotly (interactive plots), python-igraph (fast algorithms)

### Optional: Additional Algorithms

```bash
pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[algos]
```

Provides: python-louvain (Louvain method), cdlib (community detection library)

### Optional: Infomap Community Detection

```bash
pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[infomap]
```

Provides: infomap (overlapping community detection)

⚠️ **Note**: Infomap is AGPLv3 licensed (viral license). For commercial use, stick with Louvain or label propagation.

### Install All Optional Features

```bash
pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz,algos,infomap]
```

---

## 🤖 LLM Debugging Prompts

### When user says: "Py3plex installation failed"

**Ask**:
1. What's the exact error message?
2. Are you behind a corporate firewall/proxy?
3. Did you try: `pip install git+https://github.com/SkBlaz/py3plex.git`

**Common solutions**:
- Use virtual environment
- Clone repo first if firewall blocks git://
- Update pip: `pip install --upgrade pip`

### When user says: "My network won't load"

**Ask**:
1. What format is your data file? (CSV, GraphML, etc.)
2. What does the first few lines look like?
3. What's the exact error message?

**Common solutions**:
```python
# Check CSV format
import pandas as pd
df = pd.read_csv("your_file.csv")
print(df.head())  # Verify columns: source, target, layer

# Try different input types
network.load_network("file.csv", input_type="multiedgelist")  # Multilayer
network.load_network("file.csv", input_type="edgelist")  # Single layer
```

### When user says: "Visualization doesn't work"

**Ask**:
1. Are you in a Jupyter notebook or terminal?
2. What's the exact error?
3. Is matplotlib installed?

**Common solutions**:
```python
# For Jupyter notebooks
%matplotlib inline

# For headless servers
import matplotlib
matplotlib.use('Agg')

# Verify backend
import matplotlib.pyplot as plt
print(plt.get_backend())
```

### When user needs NetworkX export

**Guide them**:
```python
# Export entire network
nx_graph = network.to_nx_network()

# Export specific layer
layer_graph = network.get_layer("layer_name")

# Export as adjacency matrix
import numpy as np
adj_matrix = nx.to_numpy_array(nx_graph)
```

---

## 📚 Quick Reference Links

- **Main docs**: [https://skblaz.github.io/py3plex/](https://skblaz.github.io/py3plex/)
- **GitHub**: [https://github.com/SkBlaz/py3plex](https://github.com/SkBlaz/py3plex)
- **Issues**: [https://github.com/SkBlaz/py3plex/issues](https://github.com/SkBlaz/py3plex/issues)
- **Examples**: [https://github.com/SkBlaz/py3plex/tree/main/examples](https://github.com/SkBlaz/py3plex/tree/main/examples)

---

## 🆕 Version Information

Always guide users to the **latest version** from GitHub:
- Version on GitHub: **Latest** (v0.95+)
- PyPI version: **Deprecated** (do not recommend)

Check installed version:
```python
import py3plex
print(py3plex.__version__)  # Should be 0.95a or higher
```

Update to latest:
```bash
pip install --upgrade git+https://github.com/SkBlaz/py3plex.git
```

---

## 🎓 Learning Path for New Users

1. **Start here**: Installation from Git
2. **Next**: Load sample CSV data
3. **Then**: Basic visualization
4. **Finally**: Advanced analysis (communities, centrality, etc.)

**Sample CSV to get started**:
```csv
source,target,layer,weight
Alice,Bob,friendship,1.0
Bob,Charlie,friendship,1.0
Alice,Charlie,collaboration,0.8
Bob,David,collaboration,0.6
```

Save as `sample.csv` and load:
```python
from py3plex.core import multinet
network = multinet.multi_layer_network()
network.load_network("sample.csv", input_type="multiedgelist")
network.basic_stats()
```

---

**End of LLM Guide**
