# Benchmarks and Tutorials

This directory contains tutorials, benchmarking tools, and comparison examples.

## Examples

### Tutorials

- **`tutorial_10min.py`** - Quick start tutorial covering:
  - Loading networks
  - Basic operations
  - Visualization
  - Community detection
  - Statistics
  - Best practices

### Benchmarking and Comparison

- **`compare_multilayer_networks_example.py`** - Compare multiple multilayer networks:
  - Structural properties
  - Statistical measures
  - Similarity metrics
  
- **`statistical_comparison_example.ipynb`** - Jupyter notebook for statistical analysis and comparison

## Quick Start Tutorial

The `tutorial_10min.py` is the recommended starting point for new users. It covers:

1. **Installation verification**
2. **Loading networks** from various formats
3. **Basic statistics** and properties
4. **Visualization** with different layouts
5. **Community detection** with Louvain
6. **Multilayer operations** (if applicable)
7. **Exporting results**

## Network Comparison

The comparison examples help you:
- Compare multiple networks side-by-side
- Identify structural differences
- Compute similarity/distance metrics
- Generate comparison reports

### Comparison Metrics
- **Structural**: Nodes, edges, density, diameter
- **Statistical**: Degree distribution, clustering, centrality
- **Similarity**: Jaccard, cosine, correlation
- **Multilayer-specific**: Layer overlap, interlayer connectivity

## Usage

```bash
# Run the 10-minute tutorial
python tutorial_10min.py

# Compare multiple networks
python compare_multilayer_networks_example.py

# Interactive statistical analysis (Jupyter)
jupyter notebook statistical_comparison_example.ipynb
```

## Learning Path

**For beginners:**
1. Start with `tutorial_10min.py`
2. Explore [../basic/](../basic/) for I/O operations
3. Try [../visualization/](../visualization/) examples
4. Move to domain-specific directories

**For advanced users:**
- Use comparison tools to benchmark your networks
- Adapt tutorial code for your specific use case
- Contribute new comparison metrics

## Benchmarking Best Practices

When comparing networks:
1. **Normalize** for network size when appropriate
2. **Use multiple metrics** to capture different aspects
3. **Visualize distributions** not just averages
4. **Consider null models** for statistical significance
5. **Document parameters** and preprocessing steps

## Contributing Tutorials

When adding new tutorials:
- Keep them concise and focused
- Include comments explaining each step
- Use small example datasets
- Show expected output
- List prerequisites and dependencies

## Related Directories

These tutorials reference examples from:
- [../basic/](../basic/) - I/O operations
- [../visualization/](../visualization/) - Plotting
- [../community_detection/](../community_detection/) - Community algorithms
- [../centrality_and_statistics/](../centrality_and_statistics/) - Metrics
- All other directories for specialized topics

## Documentation

For more comprehensive documentation:
- **Main docs**: https://skblaz.github.io/py3plex/
- **10-minute tutorial**: `docs/10min_tutorial.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Contributing**: `docs/CONTRIBUTING.md`
