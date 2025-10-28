# Py3plex Quick Reference Guide

A concise reference for common py3plex operations and configurations.

## Installation

```bash
# Basic installation
pip install py3plex

# Development installation
git clone https://github.com/SkBlaz/py3plex.git
cd py3plex
make setup
make dev-install
```

## Quick Start

```python
import networkx as nx
from py3plex.core import multinet

# Create multilayer network
mlnet = multinet.multi_layer_network()

# Add layers
G1 = nx.erdos_renyi_graph(100, 0.05)
G2 = nx.erdos_renyi_graph(100, 0.05)
mlnet.add_layer(G1, layer_id=0)
mlnet.add_layer(G2, layer_id=1)

# Add interlayer edges
mlnet.add_edges([(i, i, 0, 1) for i in range(100)])

# Basic info
print(f"Nodes: {mlnet.get_number_of_nodes()}")
print(f"Edges: {mlnet.get_number_of_edges()}")
print(f"Layers: {mlnet.get_number_of_layers()}")
```

## Configuration

```python
from py3plex import config

# Visualization settings
config.DEFAULT_NODE_SIZE = 15
config.DEFAULT_EDGE_ALPHA = 0.3

# Get color palette
colors = config.get_color_palette('colorblind_safe')

# Layout settings
config.MULTILAYER_LAYER_SPACING = 2.0
config.FORCE_LAYOUT_ITERATIONS = 150

# Performance
config.USE_SPARSE_MATRICES = True
config.ENABLE_LAYOUT_CACHE = True

# Random seed for reproducibility
config.RANDOM_SEED = 42
```

## Common Operations

### Loading Networks

```python
from py3plex.core import multinet

# From edge list file
mlnet = multinet.multi_layer_network()
mlnet.load_network("network.edgelist", directed=True)

# From GML
mlnet.load_network("network.gml", input_type="gml")

# From NetworkX graphs
mlnet.add_layer(nx_graph, layer_id="social")
```

### Community Detection

```python
from py3plex.algorithms.community_detection import community_wrapper

# Louvain algorithm
communities = community_wrapper.louvain_communities(
    mlnet.core_network,
    resolution=1.0
)

# Multilayer modularity
from py3plex.algorithms.community_detection import multilayer_modularity

communities = multilayer_modularity.multilayer_louvain(
    mlnet,
    seed=42
)
```

### Centrality Measures

```python
import networkx as nx

# PageRank
pr = nx.pagerank(mlnet.core_network, alpha=0.85)

# Degree centrality
dc = nx.degree_centrality(mlnet.core_network)

# Betweenness centrality
bc = nx.betweenness_centrality(mlnet.core_network)
```

### Visualization

```python
from py3plex.visualization import multilayer
import matplotlib.pyplot as plt

# Multilayer visualization
fig, ax = multilayer.draw_multilayer_default(
    mlnet.get_layers(),
    display=False,
    node_size=config.DEFAULT_NODE_SIZE,
    alphalevel=config.DEFAULT_EDGE_ALPHA
)
plt.savefig("network.png", dpi=300, bbox_inches='tight')
plt.show()
```

### Network Statistics

```python
from py3plex.algorithms.statistics import basic_statistics

# Core statistics
stats = basic_statistics.core_network_statistics(
    mlnet.core_network,
    name="MyNetwork"
)

# Network density
density = mlnet.core_network.number_of_edges() / (
    mlnet.core_network.number_of_nodes() ** 2
)

# Degree distribution
degrees = dict(mlnet.core_network.degree())
```

## Error Handling

```python
from py3plex.exceptions import (
    NetworkConstructionError,
    InvalidLayerError,
    VisualizationError
)

try:
    mlnet.add_layer(graph, layer_id=existing_id)
except InvalidLayerError as e:
    print(f"Layer already exists: {e}")

try:
    mlnet.load_network("missing.txt")
except NetworkConstructionError as e:
    print(f"Failed to load network: {e}")
```

## Logging

```python
from py3plex.logging_config import get_logger
import logging

# Module logger
logger = get_logger(__name__)
logger.info("Processing network...")
logger.warning("Large network detected")
logger.error("Operation failed")

# Configure logging level
logger.setLevel(logging.DEBUG)
```

## Reproducibility

```python
from py3plex import config
from py3plex.utils import get_rng

# Set global seed
config.RANDOM_SEED = 42

# Get random number generator
rng = get_rng(42)
values = rng.random(10)

# Use in layouts
from py3plex.visualization.layout_algorithms import compute_force_directed_layout

positions = compute_force_directed_layout(
    graph,
    seed=config.RANDOM_SEED
)
```

## Performance Tips

```python
from py3plex import config

# Enable sparse matrices for large networks
config.USE_SPARSE_MATRICES = True
config.SPARSE_MATRIX_THRESHOLD = 1000

# Cache layouts
config.ENABLE_LAYOUT_CACHE = True
config.CACHE_SIZE_LIMIT = 100

# Batch visualization operations
config.VISUALIZATION_BATCH_SIZE = 1000

# Use random layout for very large networks (faster)
from py3plex.visualization.layout_algorithms import compute_random_layout

positions = compute_random_layout(graph, seed=42)
```

## Deprecation Handling

```python
from py3plex.utils import deprecated, warn_if_deprecated

# Mark deprecated functions
@deprecated(
    reason="Replaced by new_function",
    version="0.95a",
    alternative="new_function()"
)
def old_function():
    pass

# Warn about deprecated parameters
def my_function(old_param=None, new_param=None):
    if old_param is not None:
        warn_if_deprecated(
            "old_param",
            "Use new_param instead",
            "new_param"
        )
```

## Common Issues

### Import Errors
```python
# Missing dependencies
try:
    from some_optional_package import function
except ImportError:
    print("Optional package not available")
    # Use fallback
```

### Large Networks
```python
# For networks with >10,000 nodes:
# 1. Use sparse matrices
config.USE_SPARSE_MATRICES = True

# 2. Use faster layouts
positions = compute_random_layout(graph)

# 3. Reduce visualization complexity
config.DEFAULT_EDGE_ALPHA = 0.05  # Lower alpha
config.DEFAULT_EDGE_WIDTH = 0.5   # Thinner edges
```

### Memory Issues
```python
# Use generators for iteration
for node in mlnet.core_network.nodes():
    # Process one at a time
    pass

# Clear unused data
del large_matrix
import gc
gc.collect()
```

## Version Information

```python
import py3plex

print(f"Version: {py3plex.__version__}")
print(f"API Version: {py3plex.__api_version__}")
```

## Resources

- **Documentation**: [docs/README.md](README.md)
- **Examples**: [examples/](../examples/)
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Citations**: [ALGORITHM_CITATIONS.md](ALGORITHM_CITATIONS.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

## Getting Help

- **GitHub Issues**: https://github.com/SkBlaz/py3plex/issues
- **Discussions**: https://github.com/SkBlaz/py3plex/discussions
- **Documentation**: https://skblaz.github.io/py3plex/

---

For detailed documentation, see the [docs/](.) directory.
