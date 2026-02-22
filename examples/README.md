# Py3plex Examples

This directory contains 250+ example scripts demonstrating various features of py3plex.
Examples are organised by topic to provide an intuitive learning path.

## Quick Start Paths

**Choose your learning style:**

### Path 1: Pattern-First (Fastest)
For experienced developers who want to dive straight in:
1. **[DSL Patterns Quick Reference](getting_started/dsl_patterns_quick_reference.py)** - 8 essential patterns (5 minutes)
2. **[Ergonomics Demo](getting_started/example_ergonomics_demo.py)** - Interactive query building with `.hint()`
3. **[AGENTS.md](../AGENTS.md#quick-start-golden-paths)** - Comprehensive documentation

### Path 2: Tutorial-First (Recommended)
For learners who prefer a guided introduction:
1. **[10-Minute Tutorial](getting_started/tutorial_10min.py)** - Complete workflow demonstration
2. **[Built-in Datasets](getting_started/example_datasets.py)** - Load and analyse sample networks
3. **[DSL Patterns Quick Reference](getting_started/dsl_patterns_quick_reference.py)** - Copy-paste patterns

### Path 3: Example-Driven (Exploratory)
For learning by browsing real code:
1. Browse by topic below (e.g., [Network Analysis](network_analysis/))
2. Run examples that match your use case
3. Adapt patterns to your data

## Most Common DSL Patterns

The [dsl_patterns_quick_reference.py](getting_started/dsl_patterns_quick_reference.py) file provides
**executable, copy-paste ready patterns** that cover 80% of use cases:

| Pattern | Code Snippet | Use Case |
|---------|--------------|----------|
| Basic Filtering | `Q.nodes().where(degree__gt=5)` | Filter nodes by properties |
| Cross-Layer Hubs | `.per_layer().top_k(10).coverage(mode="all")` | Nodes in multiple layers |
| Uncertainty | `.uq(method="bootstrap", n_samples=100, seed=42)` | Confidence intervals |
| Layer Algebra | `.from_layers(L["social"] + L["work"])` | Combine layers |
| Custom Metrics | `.mutate(normalized=lambda r: r["x"]/max(r["x"], 1))` | Derive new metrics |
| Aggregation | `.per_layer().aggregate(avg="mean(degree)")` | Layer statistics |
| Export | `.to_pandas()`, `.to_networkx()`, `.to_arrow()` | Save results |

Run the file: `python getting_started/dsl_patterns_quick_reference.py` to see all patterns with live output.

## Browse Examples by Topic

### [Getting Started](getting_started/)
New to py3plex? Start here.
- 10-minute tutorial covering essentials
- Creating and manipulating networks
- Basic NetworkX integration
- **15 examples** - All fast and beginner-friendly

### [I/O and Data](io_and_data/)
Load, save, and manage network data.
- Load from multiple formats (edgelist, GML, GraphML, etc.)
- Save networks in various formats
- Data validation and schema checking
- Performance optimisation (caching, lazy evaluation)
- **11 examples**

### [Network Analysis](network_analysis/)
Analyse network properties and compute metrics.
- Network statistics and metrics
- Centrality measures (degree, betweenness, eigenvector, etc.)
- Community detection (Louvain, Leiden, label propagation, SBM, AutoCommunity)
- Temporal network queries and windowed analysis
- Uncertainty quantification and bootstrap methods
- Node and layer similarity
- Statistical reports and comparisons
- Case studies (social networks, transportation, master regulators)
- **100+ examples** - Comprehensive analysis toolkit

### [DSL Zoo](dsl_zoo/)
Minimal, copy-paste DSL patterns.
- 60+ standalone one-purpose scripts
- Covers filtering, grouping, coverage, UQ, export, temporal, community, semiring, etc.
- Each file is self-contained and fast to run
- **65 examples**

### [Visualization](visualization/)
Create network visualisations.
- Multiple layout styles (diagonal, hairball, radial, etc.)
- Interactive visualisations with Plotly
- Community colouring
- Animations and dynamic views
- **18 examples**

### [Advanced](advanced/)
Specialised techniques for power users.
- Network embeddings (Node2Vec)
- Dynamics and spreading processes (SIR, SIS, random walks)
- Network decomposition and classification
- Tensor operations and matrix methods
- Geometric analysis (Ricci curvature)
- **34 examples**

### [Pipelines](pipelines/)
Automation, workflows, and plugins.
- Config-driven workflows (YAML/JSON)
- Sklearn-style pipelines
- Plugin development and usage
- Null models and uncertainty workflows
- **12 examples**

## Running Examples

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

See [Getting Started](getting_started/) for guided learning paths.

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
4. **Use environment checks** for visualisations:
   ```python
   import os
   if os.environ.get('MPLBACKEND') != 'Agg':
       network.visualize_network(show=True)
   ```

## Example Organisation

Examples are organised by **user goals** rather than technical features:
- Good: Topic-based - "I want to detect communities"
- Avoid: Feature-based - "centrality_and_statistics"

This makes it easier for users to find relevant examples for their specific use case.
