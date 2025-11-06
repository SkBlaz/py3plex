# Py3plex Examples

This directory contains 50+ example scripts demonstrating various features of py3plex.

## Running Examples

You can run any example directly with Python:

```bash
python examples/basic/example_random_generator.py
```

## Example Categories

Examples are categorized by their runtime characteristics and dependencies:

### Fast Standalone Examples (✓ Run in CI)

These examples:
- Complete in under 5 seconds
- Don't require external dataset files
- Are automatically tested in CI

**List of fast standalone examples:**
- `basic/example_random_generator.py` - Generate random multilayer networks
- `basic/example_networkx_wrapper.py` - Apply NetworkX algorithms
- `basic/example_nx_wrapper.py` - Betweenness centrality example
- `basic/example_new_io.py` - I/O system demonstration
- `basic/example_networkx_wrapper_kwargs.py` - NetworkX wrapper with kwargs
- `benchmarks_and_tutorials/compare_multilayer_networks_example.py` - Statistical comparison
- `centrality_and_statistics/example_multilayer_statistics.py` - Network statistics
- `centrality_and_statistics/example_networkx_node_similarity.py` - Node similarity
- `centrality_and_statistics/example_versatility.py` - Multilayer eigenvector centrality
- `multilayer/example_manipulation.py` - Network manipulation
- `multilayer/example_multilayer_modularity.py` - Community detection
- `multilayer/example_multilayer_vectorized_aggregation.py` - Aggregation performance
- `multilayer/example_vectorized_aggregation.py` - Vectorized operations
- `visualization/benchmark_layouts.py` - Layout benchmarking

### Examples Requiring Datasets (⊘ Skipped in CI)

These examples require specific dataset files and are marked with `SKIP_CI: external_deps`:
- Examples in `community_detection/` (except those marked FAST)
- Examples in `decomposition_and_classification/`
- Examples in `dynamics/` that load datasets
- Examples in `embeddings/` that require data files
- Visualization examples that load specific networks

### Slow Examples (⊘ Skipped in CI)

These examples take more than 10 seconds to complete and are marked with `SKIP_CI: slow`:
- Community detection with large networks
- Comprehensive analysis workflows
- Simulation-heavy examples (e.g., epidemic spreading)

### Interactive Examples (⊘ Skipped in CI)

These examples require user interaction or display GUIs and are marked with `SKIP_CI: interactive`:
- Examples that use `show=True` for matplotlib
- Animation examples requiring imagemagick

## Adding New Examples

When creating a new example:

1. **Add a descriptive docstring** at the top explaining what the example demonstrates
2. **Mark the runtime category** in the docstring:
   - `Runtime: FAST (< 5 seconds) - Standalone example suitable for CI` for fast standalone examples
3. **Add SKIP_CI marker if needed**:
   - `SKIP_CI: external_deps` - If it requires dataset files
   - `SKIP_CI: slow` - If it takes more than 10 seconds
   - `SKIP_CI: interactive` - If it requires user interaction
4. **Use environment checks** for optional visualizations:
   ```python
   import os
   if os.environ.get('MPLBACKEND') == 'Agg':
       print("Running in CI mode - skipping visualization")
   else:
       network.visualize_network(show=True)
   ```

## CI Testing

The examples CI workflow runs all fast standalone examples to ensure they work correctly. This helps catch:
- Import errors
- API breaking changes
- Basic functionality issues

To test examples locally as CI does:
```bash
python .github/scripts/run_examples.py --fast-only --timeout 30
```

## Documentation

For detailed API documentation, visit: https://skblaz.github.io/py3plex/

## Contributing

When updating examples, ensure:
- Examples are self-contained and well-documented
- Runtime classifications are accurate
- SKIP_CI markers are appropriate
- The example works in both interactive and CI modes
