# Community Detection

This directory contains examples for detecting and analyzing community structure in multilayer networks. Discover groups of densely connected nodes using various algorithms.

## Examples in This Category

### Community Detection Algorithms
- **`example_community_detection.py`** - Louvain and Infomap algorithms for single-layer communities
- **`example_label_propagation.py`** - Label propagation algorithm for fast community detection
- **`example_leiden_multilayer.py`** - Leiden algorithm for multilayer networks (state-of-the-art)
- **`example_community_multiplex.py`** - Community detection in multiplex networks
- **`example_multiplex_community_detection.py`** - Multiplex-specific community detection methods

### Automatic Algorithm Selection
- **`example_auto_select_basic.py`** - Automatic algorithm selection with multi-metric evaluation
- **`example_auto_select_uq.py`** - Auto-select with uncertainty quantification for stability
- **`example_auto_select_custom.py`** - Custom metrics and candidates for tailored selection

### Modularity-Based Methods
- **`example_multilayer_modularity.py`** - Compute multilayer modularity and detect communities

## Quick Start

### Detecting Communities with Louvain
```python
from py3plex.algorithms.community_detection import louvain_communities

# Detect communities
communities = louvain_communities(network)
```

### Multilayer Leiden Algorithm
```python
from py3plex.algorithms.community_detection.community_wrapper import leiden_multilayer

# Detect multilayer communities
communities = leiden_multilayer(network, resolution=1.0)
```

## Choosing the Right Algorithm

- **Unsure which algorithm to use?**: Use `auto_select_community` for automatic selection
- **Fast, single-layer**: Label propagation
- **Quality, single-layer**: Louvain or Infomap
- **Multilayer networks**: Leiden multilayer (recommended)
- **Maximize modularity**: Modularity-based methods

### Automatic Algorithm Selection

When you're unsure which algorithm to use, `auto_select_community` automatically evaluates multiple algorithms and selects the best one based on multiple quality metrics:

```python
from py3plex.algorithms.community_detection import auto_select_community

# Automatic selection
result = auto_select_community(network, fast=True, seed=42)

# Access the best partition
partition = result.partition

# View leaderboard and explanation
print(result.explain())
print(result.leaderboard)
```

## Algorithm Characteristics

| Algorithm | Speed | Quality | Multilayer | Deterministic |
|-----------|-------|---------|------------|---------------|
| Label Propagation | Very Fast | Good | No | No |
| Louvain | Fast | Excellent | No | No |
| Leiden | Fast | Excellent | Yes | No |
| Infomap | Medium | Excellent | No | No |
| Modularity | Medium | Good | Yes | Yes |

## Visualization

After detecting communities, visualize them:
```python
# See visualization/example_community_visualization.py
from py3plex.visualization.multilayer import draw_multilayer_default

draw_multilayer_default(network, communities=communities)
```

## Related Examples

- [Network Analysis](../network_analysis/) - Analyze community properties
- [Visualization](../visualization/) - Visualize detected communities
- [Advanced](../advanced/) - Network decomposition and classification
