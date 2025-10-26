# Statistical Comparison Framework for Multilayer Networks

## Overview

The `stats_comparison` module provides a comprehensive framework for performing statistical comparisons between multilayer networks. This enables quantification of structural or topological differences across network ensembles or experimental conditions.

## Features

- **Pairwise and Multi-group Comparisons**: Compare 2 or more multilayer networks
- **Multiple Statistical Tests**:
  - Parametric: t-test, ANOVA
  - Non-parametric: Mann-Whitney U, Kruskal-Wallis
  - Permutation-based: Empirical null hypothesis testing
- **Effect Size Estimation**: Cohen's d, eta-squared
- **Multiple Comparison Correction**: Bonferroni, Holm-Bonferroni, FDR (Benjamini-Hochberg)
- **Bootstrap Confidence Intervals**: Estimate metric uncertainty
- **Comprehensive Metrics**: Density, degree, clustering, node activity, coupling strength, entropy

## Installation

The module is part of py3plex. Ensure you have the required dependencies:

```bash
pip install numpy scipy pandas networkx
```

## Quick Start

```python
from py3plex.core import multinet
from py3plex.algorithms.statistics.stats_comparison import compare_multilayer_networks

# Create networks
net1 = multinet.multi_layer_network(directed=False)
net1.add_edges([
    ['A', 'L1', 'B', 'L1', 1],
    ['B', 'L1', 'C', 'L1', 1],
    ['C', 'L1', 'A', 'L1', 1]
], input_type='list')

net2 = multinet.multi_layer_network(directed=False)
net2.add_edges([
    ['A', 'L1', 'B', 'L1', 1],
    ['B', 'L1', 'C', 'L1', 1]
], input_type='list')

# Compare networks
results = compare_multilayer_networks(
    [net1, net2],
    metrics=['density', 'average_degree'],
    test='permutation',
    n_permutations=1000,
    correction='fdr_bh',
    alpha=0.05
)

print(results)
```

## API Reference

### `compare_multilayer_networks()`

Main function for comparing multilayer networks.

**Parameters:**

- `networks` (List[MultilayerNetwork]): List of networks to compare (minimum 2)
- `metrics` (List[str], optional): Metrics to compute. Options:
  - `'density'`: Layer density
  - `'average_degree'`: Mean node degree
  - `'clustering'`: Clustering coefficient
  - `'node_activity'`: Node activity across layers
  - `'coupling_strength'`: Inter-layer coupling
  - `'entropy'`: Entropy of multiplexity
  - Default: `['average_degree', 'density', 'clustering']`
- `test` (str, optional): Statistical test type. Options:
  - `'permutation'`: Permutation test (default)
  - `'t-test'`: Student's t-test (2 groups)
  - `'mann-whitney'`: Mann-Whitney U test (2 groups)
  - `'anova'`: One-way ANOVA (2+ groups)
  - `'kruskal'`: Kruskal-Wallis H test (2+ groups)
- `n_permutations` (int, optional): Number of permutations (default: 1000)
- `alpha` (float, optional): Significance level (default: 0.05)
- `correction` (str, optional): Multiple comparison correction. Options:
  - `'bonferroni'`: Bonferroni correction
  - `'holm'`: Holm-Bonferroni correction
  - `'fdr_bh'`: Benjamini-Hochberg FDR (default)
  - `None`: No correction
- `node_mapping` (Dict, optional): Node correspondence mapping across networks
- `layer_scope` (str, optional): Layer scope (`'intralayer'`, `'interlayer'`, or `'both'`)
- `custom_metrics` (Dict[str, Callable], optional): Custom metric functions

**Returns:**

pandas.DataFrame with columns:
- `metric`: Metric name
- `layer`: Layer identifier or 'global'
- `statistic`: Test statistic value
- `p_value`: Raw p-value
- `adjusted_p_value`: Corrected p-value
- `effect_size`: Effect size measure
- `significant`: Boolean indicating significance (p < alpha)
- `mean_group_0`, `mean_group_1`, ...: Mean values per group

### `bootstrap_confidence_interval()`

Compute bootstrap confidence intervals for network metrics.

**Parameters:**

- `networks` (List[MultilayerNetwork]): List of networks
- `metric_func` (Callable): Function mapping network to scalar metric
- `n_bootstrap` (int, optional): Number of bootstrap samples (default: 1000)
- `confidence_level` (float, optional): Confidence level (default: 0.95)

**Returns:**

Dictionary mapping group indices to (lower, upper) CI bounds.

## Examples

### Example 1: Basic Comparison

```python
from py3plex.core import multinet
from py3plex.algorithms.statistics.stats_comparison import compare_multilayer_networks

# Create two networks with different densities
net1 = multinet.multi_layer_network(directed=False)
net1.add_edges([
    ['A', 'L1', 'B', 'L1', 1],
    ['B', 'L1', 'C', 'L1', 1],
    ['C', 'L1', 'A', 'L1', 1],  # Triangle
    ['A', 'L2', 'B', 'L2', 1]
], input_type='list')

net2 = multinet.multi_layer_network(directed=False)
net2.add_edges([
    ['A', 'L1', 'B', 'L1', 1],
    ['B', 'L1', 'C', 'L1', 1],  # Line
    ['A', 'L2', 'B', 'L2', 1]
], input_type='list')

# Compare using permutation test
results = compare_multilayer_networks(
    [net1, net2],
    metrics=['density', 'clustering'],
    test='permutation',
    n_permutations=10000
)

# Show significant differences
significant = results[results['significant']]
print(significant)
```

### Example 2: Multi-Group Comparison

```python
# Compare three or more networks
results = compare_multilayer_networks(
    [net1, net2, net3, net4],
    metrics=['density', 'average_degree'],
    test='kruskal',  # Non-parametric for multiple groups
    correction='holm'
)

# Filter by metric
density_results = results[results['metric'] == 'density']
print(density_results)
```

### Example 3: Bootstrap Confidence Intervals

```python
from py3plex.algorithms.statistics.stats_comparison import bootstrap_confidence_interval

def avg_clustering(network):
    """Compute average clustering coefficient."""
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    clustering = mls.multilayer_clustering_coefficient(network)
    return np.mean(list(clustering.values()))

# Get 95% CI for clustering
ci = bootstrap_confidence_interval(
    [net1, net2],
    avg_clustering,
    n_bootstrap=1000,
    confidence_level=0.95
)

for group, (lower, upper) in ci.items():
    print(f"{group}: [{lower:.4f}, {upper:.4f}]")
```

### Example 4: Custom Metrics

```python
def custom_metric(network):
    """Custom metric: ratio of inter-layer to intra-layer edges."""
    inter_edges = 0
    intra_edges = 0
    
    for edge in network.get_edges():
        (_, l1), (_, l2) = edge[0], edge[1]
        if l1 == l2:
            intra_edges += 1
        else:
            inter_edges += 1
    
    return inter_edges / (intra_edges + 1e-10)

results = compare_multilayer_networks(
    [net1, net2],
    metrics=[],  # No built-in metrics
    custom_metrics={'inter_intra_ratio': custom_metric},
    test='mann-whitney'
)
```

## Use Cases

### 1. Biological Networks
Compare disease vs. healthy protein interaction networks across multiple tissues.

```python
results = compare_multilayer_networks(
    disease_networks + healthy_networks,
    metrics=['density', 'clustering', 'node_activity'],
    test='mann-whitney',
    correction='fdr_bh'
)
```

### 2. Social Networks
Analyze structural differences in social networks before/after interventions.

```python
results = compare_multilayer_networks(
    [pre_intervention_net, post_intervention_net],
    metrics=['average_degree', 'coupling_strength'],
    test='permutation',
    n_permutations=10000
)
```

### 3. Temporal Networks
Compare network snapshots across time periods.

```python
results = compare_multilayer_networks(
    [t1_network, t2_network, t3_network],
    metrics=['density', 'entropy'],
    test='kruskal'
)
```

## Best Practices

### Choosing Statistical Tests

1. **Sample Size < 30**: Use permutation or non-parametric tests
2. **Normal Distribution**: Parametric tests (t-test, ANOVA) have more power
3. **Two Groups**: t-test (parametric) or Mann-Whitney (non-parametric)
4. **Multiple Groups**: ANOVA (parametric) or Kruskal-Wallis (non-parametric)
5. **Unknown Distribution**: Permutation test (most general)

### Multiple Comparison Correction

When testing multiple metrics or layers:

1. **Conservative**: Use Bonferroni (controls family-wise error rate)
2. **Less Conservative**: Use Holm-Bonferroni (sequential Bonferroni)
3. **Recommended**: Use FDR (Benjamini-Hochberg) - balances power and error control

### Effect Sizes

Always report effect sizes in addition to p-values:

- **Cohen's d**: |d| < 0.2 (small), 0.2-0.5 (medium), > 0.8 (large)
- **Eta-squared**: η² < 0.01 (small), 0.01-0.06 (medium), > 0.14 (large)

### Sample Size Considerations

- Minimum: 2 networks per group
- Recommended: 5-10 networks per group for reliable estimates
- With < 5 networks: Use permutation tests and bootstrap CI

## Computational Complexity

- **Permutation test**: O(n_perm × n_networks × n_metrics)
- **Parametric tests**: O(n_networks × n_metrics)
- **Bootstrap CI**: O(n_bootstrap × n_networks)

For large networks or many permutations, consider:
- Reducing `n_permutations` (1000 is usually sufficient)
- Parallelization (future enhancement)
- Limiting metrics to those of interest

## Troubleshooting

### Warning: "Test failed for metric/layer"

This occurs when:
- All values are identical (no variance)
- Sample size too small
- Solution: Check your data, increase sample size, or use permutation test

### Empty DataFrame Result

This occurs when:
- Networks have no edges
- Invalid metric names
- Solution: Verify networks have edges and metric names are correct

### High p-values despite visual differences

This can happen when:
- Sample size too small (low statistical power)
- High variance within groups
- Solution: Increase sample size, use effect sizes to quantify differences

## References

1. Kivelä, M., et al. (2014). "Multilayer networks." Journal of Complex Networks, 2(3), 203-271.
2. Good, P. (2013). "Permutation Tests: A Practical Guide to Resampling Methods for Testing Hypotheses."
3. Efron, B., & Tibshirani, R. J. (1994). "An Introduction to the Bootstrap."
4. Benjamini, Y., & Hochberg, Y. (1995). "Controlling the false discovery rate: a practical and powerful approach to multiple testing."

## See Also

- [Jupyter Notebook Example](../examples/statistical_comparison_example.ipynb)
- [Python Script Example](../examples/compare_multilayer_networks_example.py)
- [Multilayer Statistics Module](multilayer_statistics.py)
