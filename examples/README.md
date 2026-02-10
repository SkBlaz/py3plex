# Py3plex Examples

This directory contains 170+ example scripts demonstrating various features of py3plex. Examples are organized by topic to provide an intuitive learning path.

## 🚀 Quick Start Paths

**Choose your learning style:**

### Path 1: Pattern-First (Fastest ⚡)
Perfect for experienced developers who want to dive right in:
1. **[DSL Patterns Quick Reference](getting_started/dsl_patterns_quick_reference.py)** - 8 essential patterns (5 minutes)
2. **[Ergonomics Demo](getting_started/example_ergonomics_demo.py)** - Interactive query building with `.hint()`
3. **[AGENTS.md](../AGENTS.md#quick-start-golden-paths)** - Comprehensive documentation

### Path 2: Tutorial-First (Recommended 🎓)
Perfect for learners who prefer guided introduction:
1. **[10-Minute Tutorial](getting_started/tutorial_10min.py)** - Complete workflow demonstration
2. **[Built-in Datasets](getting_started/example_datasets.py)** - Load and analyze sample networks
3. **[DSL Patterns Quick Reference](getting_started/dsl_patterns_quick_reference.py)** - Copy-paste patterns

### Path 3: Example-Driven (Exploratory 🔍)
Perfect for learning by browsing real code:
1. Browse by topic below (e.g., [Network Analysis](network_analysis/))
2. Run examples that match your use case
3. Adapt patterns to your data

## 📚 Most Common DSL Patterns

The [dsl_patterns_quick_reference.py](getting_started/dsl_patterns_quick_reference.py) file provides **executable, copy-paste ready patterns** that cover 80% of use cases:

| Pattern | Code Snippet | Use Case |
|---------|--------------|----------|
| **Basic Filtering** | `Q.nodes().where(degree__gt=5)` | Filter nodes by properties |
| **Cross-Layer Hubs** | `.per_layer().top_k(10).coverage(mode="all")` | Nodes in multiple layers |
| **Uncertainty** | `.uq(method="bootstrap", n_samples=100, seed=42)` | Confidence intervals |
| **Layer Algebra** | `.from_layers(L["social"] + L["work"])` | Combine layers |
| **Custom Metrics** | `.mutate(normalized=lambda r: r["x"]/max(r["x"], 1))` | Derive new metrics |
| **Aggregation** | `.per_layer().aggregate(avg="mean(degree)")` | Layer statistics |
| **Export** | `.to_pandas()`, `.to_networkx()`, `.to_arrow()` | Save results |

**💡 Run the file**: `python getting_started/dsl_patterns_quick_reference.py` to see all patterns with live output!

## Browse Examples by Topic

Examples are organized into intuitive categories based on what you want to accomplish:

### [Getting Started](getting_started/)
**New to py3plex? Start here!**
- 10-minute tutorial covering essentials
- Creating and manipulating networks
- Basic NetworkX integration
- **7 examples** - All fast and beginner-friendly

### [I/O and Data](io_and_data/)
**Load, save, and manage network data**
- Load from multiple formats (edgelist, GML, GraphML, etc.)
- Save networks in various formats
- Data validation and schema checking
- Performance optimization (caching, lazy evaluation)
- **8 examples** - Essential for data workflows

### [Network Analysis](network_analysis/)
**Analyze network properties and compute metrics**
- Network statistics and metrics
- Centrality measures (degree, betweenness, eigenvector, etc.)
- Node and layer similarity
- Statistical reports and comparisons
- **16 examples** - Comprehensive analysis toolkit

### [Communities](communities/)
**Detect and analyze community structure**
- Louvain, Leiden, Infomap algorithms
- Label propagation
- Multilayer modularity
- Multiplex community detection
- **6 examples** - State-of-the-art methods

### [Visualization](visualization/)
**Create beautiful network visualizations**
- Multiple layout styles (diagonal, hairball, radial, etc.)
- Interactive visualizations with Plotly
- Community coloring
- Animations and dynamic views
- **17 examples** - Rich visualization toolkit

### [Advanced](advanced/)
**Specialized techniques for power users**
- Network embeddings (Node2Vec)
- Dynamics and spreading processes
- Network decomposition and classification
- Tensor operations and matrix methods
- Geometric analysis (Ricci curvature)
- **29 examples** - Advanced algorithms

### [Workflows](workflows/)
**Complete pipelines and extensibility**
- Config-driven analysis workflows
- Plugin system for custom algorithms
- End-to-end Jupyter notebooks
- Batch processing
- **2 examples + notebooks** - Production-ready workflows

##  Running Examples

Run any example directly with Python:

```bash
python examples/network_analysis/example_multilayer_statistics.py
```

## Example Types

Examples are marked with runtime characteristics:

- **FAST** (< 5 seconds) - Quick to run, great for learning
- **SKIP_CI: slow** - Takes 10+ seconds to complete
- **SKIP_CI: external_deps** - Requires external dataset files
- **SKIP_CI: interactive** - Requires user interaction or displays GUI

## Learning Paths

Different learning paths based on your goals:

### Path 1: Complete Beginner
1. Start with [Getting Started](getting_started/) - basics and tutorial
2. Try [I/O and Data](io_and_data/) - loading real data
3. Explore [Network Analysis](network_analysis/) - analyzing networks
4. Learn [Visualization](visualization/) - making it beautiful

### Path 2: Network Scientist
1. Review [Getting Started](getting_started/) - quick overview
2. Focus on [Network Analysis](network_analysis/) - metrics and centrality
3. Dive into [Communities](communities/) - finding structure
4. Try [Advanced](advanced/) - cutting-edge techniques

### Path 3: Software Engineer
1. Check [Getting Started](getting_started/) - understand the API
2. Explore [I/O and Data](io_and_data/) - data pipelines
3. Study [Workflows](workflows/) - automation and plugins
4. Use [Visualization](visualization/) - creating outputs

## Testing Examples

The examples CI workflow runs all fast standalone examples to ensure they work correctly.

Test examples locally as CI does:
```bash
python .github/scripts/run_examples.py --fast-only --timeout 30
```

## Additional Resources

- **API Documentation**: https://skblaz.github.io/py3plex/
- **Plugin Guide**: [Plugin System Documentation](../docfiles/plugin_system.rst)
- **CLI Tutorial**: Run `py3plex quickstart` for interactive demo

## Contributing Examples

When creating a new example:

1. **Place it in the right category** based on its primary purpose
2. **Add a descriptive docstring** explaining what it demonstrates
3. **Mark runtime characteristics**:
   - `Runtime: FAST (< 5 seconds)` for fast examples
   - `SKIP_CI: slow` if it takes 10+ seconds
   - `SKIP_CI: external_deps` if it needs dataset files
   - `SKIP_CI: interactive` if it requires user interaction
4. **Use environment checks** for visualizations:
   ```python
   import os
   if os.environ.get('MPLBACKEND') != 'Agg':
       network.visualize_network(show=True)
   ```
5. **Add README updates** if creating new workflows

## Example Organization

Examples are organized by **user goals** rather than technical features:
- GOOD: Topic-based: "I want to detect communities"
- BAD: Feature-based: "centrality_and_statistics"

This makes it easier for users to find relevant examples for their specific use case.
