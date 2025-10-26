# Statistical Comparison Framework - Implementation Summary

## Overview
This implementation adds comprehensive statistical comparison capabilities to py3plex for multilayer networks, as requested in issue #[issue_number].

## What Was Implemented

### Core Module: `stats_comparison.py`
A new module at `py3plex/algorithms/statistics/stats_comparison.py` with 650+ lines of code implementing:

1. **Main Function: `compare_multilayer_networks()`**
   - Compares 2 or more multilayer networks
   - Supports 6 built-in metrics + custom metrics
   - Implements 5 statistical tests
   - Returns pandas DataFrame with comprehensive results

2. **Statistical Tests**
   - Permutation test (non-parametric, general)
   - Student's t-test (parametric, 2 groups)
   - Mann-Whitney U test (non-parametric, 2 groups)
   - ANOVA (parametric, multiple groups)
   - Kruskal-Wallis H (non-parametric, multiple groups)

3. **Effect Size Calculations**
   - Cohen's d for pairwise comparisons
   - Eta-squared for multi-group comparisons

4. **Multiple Comparison Corrections**
   - Bonferroni correction
   - Holm-Bonferroni correction
   - FDR (Benjamini-Hochberg)

5. **Bootstrap Confidence Intervals**
   - `bootstrap_confidence_interval()` function
   - Estimates uncertainty in metrics

6. **Supported Metrics**
   - `density`: Layer density
   - `average_degree`: Mean node degree
   - `clustering`: Clustering coefficient
   - `node_activity`: Node activity across layers
   - `coupling_strength`: Inter-layer coupling
   - `entropy`: Entropy of multiplexity

### Test Suite: `test_stats_comparison.py`
Comprehensive test suite with 26 tests covering:
- Basic two-network comparisons
- Multi-network comparisons (3+ groups)
- All statistical tests
- All correction methods
- Effect size calculations
- Bootstrap confidence intervals
- Edge cases and error handling
- Helper function validation

All tests pass successfully.

### Documentation

1. **Markdown Documentation** (`docs/statistical_comparison.md`)
   - Complete API reference
   - Usage examples
   - Best practices
   - Troubleshooting guide
   - References to literature

2. **Jupyter Notebook** (`examples/statistical_comparison_example.ipynb`)
   - 7 detailed examples covering:
     - Basic two-network comparison
     - Multi-group comparison
     - Directed networks
     - Bootstrap confidence intervals
     - Different statistical tests
     - Multiple comparison correction
     - Synthetic network benchmarks

3. **Python Script** (`examples/compare_multilayer_networks_example.py`)
   - Working example script
   - Demonstrates practical usage
   - Shows output formatting

## Key Design Decisions

1. **Pandas DataFrame Output**: Results are returned as pandas DataFrames for easy manipulation and analysis

2. **Flexible Metric System**: Users can provide custom metric functions in addition to built-in metrics

3. **Comprehensive Output**: Each result includes:
   - Test statistic
   - Raw p-value
   - Adjusted p-value
   - Effect size
   - Mean values per group
   - Significance flag

4. **Error Handling**: Graceful handling of edge cases (empty networks, single nodes, etc.)

5. **Integration**: Seamlessly integrates with existing `multilayer_statistics` module

## Testing

- **26 new tests** in `test_stats_comparison.py` (100% pass rate)
- **30 existing tests** in `test_multilayer_statistics.py` (100% pass rate, no regressions)
- **Security**: CodeQL analysis shows 0 alerts
- **Example scripts**: All examples run successfully

## Usage Example

```python
from py3plex.core import multinet
from py3plex.algorithms.statistics.stats_comparison import compare_multilayer_networks

# Create networks
net1 = multinet.multi_layer_network(directed=False)
net1.add_edges([['A', 'L1', 'B', 'L1', 1], ...], input_type='list')

net2 = multinet.multi_layer_network(directed=False)
net2.add_edges([['A', 'L1', 'B', 'L1', 1], ...], input_type='list')

# Compare
results = compare_multilayer_networks(
    [net1, net2],
    metrics=['density', 'average_degree'],
    test='permutation',
    n_permutations=1000,
    correction='fdr_bh',
    alpha=0.05
)

# Show significant differences
print(results[results['significant']])
```

## Files Modified/Added

### New Files
1. `py3plex/algorithms/statistics/stats_comparison.py` - Core implementation
2. `tests/test_stats_comparison.py` - Test suite
3. `examples/statistical_comparison_example.ipynb` - Jupyter examples
4. `examples/compare_multilayer_networks_example.py` - Python script example
5. `docs/statistical_comparison.md` - Documentation

### Modified Files
1. `py3plex/algorithms/statistics/__init__.py` - Added exports for new module

## Performance Characteristics

- **Permutation test**: O(n_perm × n_networks × n_metrics)
- **Parametric tests**: O(n_networks × n_metrics)
- **Bootstrap CI**: O(n_bootstrap × n_networks)

Typical performance:
- Comparing 2 networks with 3 metrics: < 1 second
- Permutation test (1000 perms): 1-2 seconds
- Bootstrap CI (1000 samples): 1-2 seconds

## Future Enhancements (Not Implemented)

The following were mentioned in the issue but not implemented in this PR:
- Network distance metrics (Jensen-Shannon, spectral distance, graph edit distance)
- Layer alignment tests
- Temporal multilayer network support with repeated measures
- Null model generation with degree preservation
- Parallelization for large-scale comparisons
- Visualization integration (distribution plots, heatmaps)

These could be added in future PRs as extensions to this framework.

## Validation

The implementation follows:
- Kivelä et al. (2014) definitions for multilayer network metrics
- Standard statistical test implementations from scipy
- Best practices from permutation testing literature (Good, 2013)
- Bootstrap methodology from Efron & Tibshirani (1994)
- Multiple testing correction per Benjamini & Hochberg (1995)

## Code Quality

- ✅ All tests pass (56/56)
- ✅ No security vulnerabilities (CodeQL)
- ✅ Comprehensive documentation
- ✅ Clear API design
- ✅ Example usage demonstrated
- ✅ No regressions in existing tests
- ✅ Code review feedback addressed

## Conclusion

This implementation provides a solid, well-tested foundation for statistical comparison of multilayer networks in py3plex. It covers the core requirements from the issue and provides extensive documentation and examples for users.
