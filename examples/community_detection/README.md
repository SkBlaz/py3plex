# Community Detection Examples

This directory contains examples for detecting and analyzing community structure in networks.

## Examples

### Monoplex Community Detection

- **`example_community_detection.py`** - Comprehensive community detection using Louvain and Infomap algorithms
- **`example_label_propagation.py`** - Label propagation algorithm for community detection

### Multiplex Community Detection

- **`example_community_multiplex.py`** - Community detection specifically for multiplex networks
- **`example_multiplex_community_detection.py`** - Alternative multiplex community detection methods

## Algorithms Supported

### Louvain
- Fast modularity optimization
- Works on monoplex and multiplex networks
- Hierarchical community structure
- Python-only (no external binary required)

### Infomap
- Information-theoretic approach
- Optimizes map equation
- Requires external binary (see installation notes)
- Native multiplex support

### Label Propagation
- Fast semi-supervised algorithm
- Propagates labels through network
- Good for large networks

## Usage

```bash
# Louvain community detection
python example_community_detection.py

# Multiplex-specific methods
python example_multiplex_community_detection.py
```

## Output

Community detection examples typically output:
- Partition dictionary: `{node: community_id}`
- Community statistics (size, modularity)
- Visualization with community colors

## Installation Notes

**Infomap binary** (optional):
- Download from https://www.mapequation.org/infomap/
- Place binary in PATH or specify path in examples
- Examples will gracefully fall back to Louvain if Infomap is unavailable

## Related Directories

- See [../visualization/](../visualization/) for visualizing detected communities
- See [../multilayer/](../multilayer/) for multilayer-specific operations
- See [../centrality_and_statistics/](../centrality_and_statistics/) for analyzing community structure
