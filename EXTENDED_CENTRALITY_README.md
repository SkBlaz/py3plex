# Extended Centrality Metrics for Multilayer Networks

This PR implements 12 new extended centrality metrics (metrics 18-30 from issue) for multilayer and multiplex network analysis in py3plex.

## What's New

### Implemented Centrality Metrics

1. **Information Centrality** (Stephenson-Zelen style) - `information_centrality()`
2. **Communicability Betweenness** (Estrada-style) - `communicability_betweenness_centrality()`
3. **Accessibility** (entropy-based h-step reach) - `accessibility_centrality(h=2)`
4. **Percolation Centrality** (bond percolation) - `percolation_centrality(edge_activation_prob=0.5, trials=100)`
5. **Spreading Centrality** (SIR epidemic model) - `spreading_centrality(beta=0.2, mu=0.1, trials=50, steps=100)`
6. **Collective Influence** (CI_ℓ) - `collective_influence(radius=2)`
7. **Load Centrality** (shortest-path load) - `load_centrality()`
8. **Flow Betweenness** (max-flow based) - `flow_betweenness_centrality(samples=100)`
9. **Harmonic Closeness** (handles disconnections) - `harmonic_closeness_centrality()`
10. **Edge Betweenness** - `edge_betweenness_centrality()`
11. **Bridging Centrality** - `bridging_centrality()`
12. **Local Efficiency** - `local_efficiency_centrality()`
13. **Lp-Aggregated Centrality** (framework) - `lp_aggregated_centrality(layer_centralities, p=2, weights=None)`

### Quick Start

```python
from py3plex.core import multinet
from py3plex.algorithms.multilayer_algorithms.centrality import (
    MultilayerCentrality,
    compute_all_centralities
)

# Create your multilayer network
network = multinet.multi_layer_network(directed=False)
# ... add edges ...

# Option 1: Use individual metrics
calc = MultilayerCentrality(network)
info_cent = calc.information_centrality()
spreading = calc.spreading_centrality(beta=0.2, mu=0.1)
harmonic = calc.harmonic_closeness_centrality()

# Option 2: Compute all extended metrics at once
results = compute_all_centralities(network, include_extended=True)
```

### Files Changed

- **Core Implementation**: `py3plex/algorithms/multilayer_algorithms/centrality.py` (+907 lines)
  - Added 12 new centrality methods to `MultilayerCentrality` class
  - Updated `compute_all_centralities()` with `include_extended` parameter
  - Comprehensive docstrings with formulas and references

- **Tests**: `tests/test_multilayer_centrality.py` (+277 lines)
  - New test class `TestExtendedCentralityMetrics` with 25+ test methods
  - Tests for return types, value ranges, and parameter variations
  - Integration tests for `compute_all_centralities`

- **Documentation**: `docfiles/tutorials/multilayer_centrality.rst` (+130 lines)
  - Added "Extended Measures" section with descriptions
  - Comprehensive code examples for each metric
  - Updated references with relevant scientific papers
  - New application examples

- **Examples**: `examples/centrality_and_statistics/example_extended_centrality.py` (+246 lines)
  - Individual examples for each metric
  - Complete workflow demonstration
  - Sample output formatting

- **Validation**: `validate_centrality_metrics.py` (+183 lines)
  - Standalone validation script
  - Tests all 12 new metrics
  - Provides clear pass/fail feedback

- **Summary**: `IMPLEMENTATION_SUMMARY.md` (+271 lines)
  - Detailed implementation documentation
  - API reference for all new methods
  - Performance considerations
  - Usage examples and best practices

## Testing

Run the validation script to verify the implementation:

```bash
# Install dependencies
pip install numpy scipy networkx

# Run validation
python validate_centrality_metrics.py

# Run unit tests
python -m pytest tests/test_multilayer_centrality.py -v
```

## Documentation

See detailed documentation in:
- **Tutorial**: `docfiles/tutorials/multilayer_centrality.rst`
- **Implementation Summary**: `IMPLEMENTATION_SUMMARY.md`
- **Examples**: `examples/centrality_and_statistics/example_extended_centrality.py`

## Performance Notes

- **Fast** (O(n²) or better): Information, Harmonic, Accessibility
- **Moderate** (O(n²) to O(n³)): Load, Bridging, Local Efficiency
- **Monte Carlo** (configurable samples): Percolation, Spreading, Flow Betweenness

All metrics include fallback implementations and handle edge cases gracefully.

## Dependencies

- numpy >= 1.19.0
- scipy >= 1.5.0
- networkx >= 2.5

## Notes

- Metrics 17 (Current-Flow Closeness) and 19 (Subgraph Centrality) already existed in the codebase
- All implementations follow existing py3plex patterns and conventions
- Code includes comprehensive error handling with informative messages
- All metrics are tested and documented

## References

Key papers for the implemented metrics:
- Stephenson & Zelen (1989) - Information centrality
- Estrada et al. (2009) - Communicability betweenness
- Morone & Makse (2015) - Collective influence
- Latora & Marchiori (2001) - Local efficiency

See `docfiles/tutorials/multilayer_centrality.rst` for complete reference list.
