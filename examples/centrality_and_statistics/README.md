# Centrality and Statistics Examples

This directory contains examples for computing network metrics, centrality measures, and statistical properties.

## Examples

### Centrality Measures

- **`example_multilayer_centrality.py`** - Comprehensive multilayer centrality measures (degree, betweenness, closeness, eigenvector, PageRank)
- **`example_networkx_node_similarity.py`** - Node similarity metrics using NetworkX

### Network Statistics

- **`example_network_statistics.py`** - Basic network statistics (degree distribution, clustering, etc.)
- **`example_multilayer_statistics.py`** - 17+ multilayer-specific statistics including:
  - Supra-Laplacian spectrum
  - Algebraic connectivity
  - Multilayer clustering coefficient
  - Layer activity
  - Edge overlap
  - And many more...

### Advanced Metrics

- **`example_entanglement.py`** - Entanglement analysis for multilayer networks
- **`example_powerlaw_computation.py`** - Fitting power-law distributions to degree sequences

## Key Metrics

### Multilayer Centrality
- **Multilayer degree**: Node importance across layers
- **Multilayer betweenness**: Bridge nodes between layers
- **Multilayer closeness**: Average distance across layers
- **Multilayer eigenvector**: Influence considering layer structure
- **Multilayer PageRank**: Importance with layer transitions

### Multilayer Statistics
See `example_multilayer_statistics.py` for the complete list of 17 statistics, including:
- **Structural**: Supra-Laplacian, algebraic connectivity
- **Layer-based**: Layer activity, layer similarity
- **Clustering**: Multilayer clustering coefficient
- **Paths**: Average path length across layers

## Usage

```bash
# Compute multilayer centrality
python example_multilayer_centrality.py

# Get comprehensive network statistics
python example_multilayer_statistics.py

# Analyze entanglement
python example_entanglement.py

# Check degree distribution
python example_powerlaw_computation.py
```

## Documentation

For complete documentation on multilayer statistics:
- See `py3plex/algorithms/statistics/README_MULTILAYER_STATISTICS.md`
- API documentation: https://skblaz.github.io/py3plex/

## Related Directories

- See [../multilayer/](../multilayer/) for multilayer operations
- See [../community_detection/](../community_detection/) for modularity statistics
- See [../benchmarks_and_tutorials/](../benchmarks_and_tutorials/) for statistical comparisons
