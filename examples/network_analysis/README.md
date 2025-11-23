# Network Analysis

This directory contains examples for analyzing multilayer network properties, computing centrality metrics, and generating statistical reports.

## Examples in This Category

### Basic Statistics
- **`example_multilayer_statistics.py`** - Comprehensive multilayer network statistics (17 metrics)
- **`example_network_statistics.py`** - Compute network statistics and identify hubs
- **`example_statistical_report.py`** - Generate comprehensive statistical reports
- **`compare_multilayer_networks_example.py`** - Compare multiple multilayer networks statistically

### Centrality Measures
- **`example_multilayer_centrality.py`** - Multilayer-specific centrality measures
- **`example_centrality_toolkit.py`** - Complete centrality computation toolkit
- **`example_extended_centrality.py`** - Extended centrality metrics for multilayer networks
- **`example_versatility.py`** - Versatility (multilayer eigenvector centrality)
- **`example_multirank.py`** - MultiRank and multiplex PageRank variants
- **`example_centrality_bench.py`** - Benchmark and compare centrality algorithms

### Node and Layer Similarity
- **`example_networkx_node_similarity.py`** - Compare node similarity metrics from NetworkX
- **`example_layer_similarity.py`** - Measure similarity between network layers

### Advanced Metrics
- **`example_new_multiplex_metrics.py`** - New multiplex-specific metrics
- **`example_entanglement.py`** - Layer entanglement measures
- **`example_powerlaw_computation.py`** - Analyze power-law distributions
- **`example_meta_flow_report.py`** - Comprehensive meta-flow analysis and reporting

## Quick Start

### Computing Basic Statistics
```python
from py3plex.algorithms.statistics import multilayer_statistics as mls

# Get number of nodes
num_nodes = mls.get_number_of_nodes(network)

# Get layer overlap
overlap = mls.get_layer_overlap(network)
```

### Computing Centrality
```python
from py3plex.algorithms.hedonic_structural_measures import versatility

# Compute versatility (multilayer eigenvector centrality)
vers = versatility(network)
```

## Choosing the Right Metric

- **For hub identification**: Use degree centrality or versatility
- **For bridge detection**: Use betweenness centrality
- **For layer comparison**: Use layer similarity metrics
- **For comprehensive overview**: Use statistical reports

## Related Examples

- [Getting Started](../getting_started/) - Create networks to analyze
- [Communities](../communities/) - Detect community structure
- [Visualization](../visualization/) - Visualize analysis results
