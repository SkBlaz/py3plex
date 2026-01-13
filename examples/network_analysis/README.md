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

### DSL Query Interface
- **`example_dsl_queries.py`** - Basic DSL query syntax and operations
- **`example_dsl_builder_api.py`** - Complete builder API examples with all DSL v2 features
- **`example_dsl_advanced.py`** - Advanced query patterns and optimizations
- **`example_dsl_mutate.py`** - Row-wise transformations and derived columns
- **`example_dsl_dplyr_operations.py`** - dplyr-style data manipulation operations
- **`example_dsl_edge_queries.py`** - Query and filter edges in multilayer networks
- **`example_dsl_layer_algebra.py`** - Layer set operations (union, intersection, difference)
- **`example_dsl_community_detection.py`** - Community detection via DSL
- **`example_dsl_community_filtering.py`** - Filter networks by community structure
- **`example_dsl_uncertainty_flagship.py`** - Uncertainty quantification in queries
- **`example_dsl_uncertainty_bootstrap_nullmodel.py`** - Bootstrap and null model analysis
- **`example_dsl_uq_ergonomics.py`** - Ergonomic uncertainty estimation patterns
- **`example_dsl_export.py`** - Export query results to various formats
- **`example_dsl_linting.py`** - Query linting and validation
- **`example_dsl_query_optimization.py`** - Query optimization techniques
- **`example_dsl_custom_operators.py`** - Define custom DSL operators
- **`example_dsl_operators_advanced.py`** - Advanced custom operator patterns
- **`example_dsl_enhancements_demo.py`** - DSL v2 enhancements showcase
- **`example_dsl_edge_grouping.py`** - Group and aggregate edge data
- **`example_dsl_dynamics.py`** - Network dynamics simulations via DSL
- **`example_dsl_dynamics_declarative.py`** - Declarative dynamics specifications
- **`example_dsl_trajectories.py`** - Query simulation trajectories
- **`example_pattern_matching.py`** - Pattern matching in multilayer networks

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

### Querying with DSL
```python
from py3plex.dsl import Q, L

# Query high-degree nodes in social layer
result = (
    Q.nodes()
     .from_layers(L["social"])
     .where(degree__gt=5)
     .compute("betweenness_centrality")
     .execute(network)
)

# Transform and create derived columns
result = (
    Q.nodes()
     .compute("degree", "clustering")
     .mutate(
         hub_score=lambda row: row.get("degree", 0) * row.get("clustering", 0)
     )
     .execute(network)
)
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
