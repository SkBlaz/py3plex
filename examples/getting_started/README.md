# Getting Started with Py3plex

This directory contains introductory examples to help you get started with py3plex. These examples demonstrate the core concepts and basic usage patterns.

## 🚀 Quick Start Guide

**New to py3plex?** Follow this path:

1. **5-Minute Introduction**: [dsl_patterns_quick_reference.py](dsl_patterns_quick_reference.py) 
   - 8 essential DSL patterns (executable, copy-paste ready)
   - Covers 80% of typical use cases
   - **⭐ Start here for fastest onboarding**

2. **10-Minute Tutorial**: [tutorial_10min.py](tutorial_10min.py)
   - Complete workflow from data loading to visualization
   - Understand multilayer network basics

3. **Interactive Learning**: [example_ergonomics_demo.py](example_ergonomics_demo.py)
   - Use `.hint()` for context-aware suggestions
   - Learn DSL interactively as you code
   - Pedagogical error messages guide you

4. **Deep Dive**: See [AGENTS.md](../../AGENTS.md#quick-start-golden-paths) for comprehensive documentation

## 🎯 Essential Patterns (from dsl_patterns_quick_reference.py)

The `dsl_patterns_quick_reference.py` file contains **8 copy-paste patterns** for immediate use:

| Pattern | Use Case | When to Use |
|---------|----------|-------------|
| **1. Basic Filtering** | Find high-degree nodes | Start here for most analyses |
| **2. Cross-Layer Hubs** | Nodes appearing in multiple layers | Multilayer structure insights |
| **3. Uncertainty Quantification** | Confidence intervals for metrics | Research publications |
| **4. Community Detection** | Find network communities | Structural analysis |
| **5. Custom Metrics** | Derive new metrics from existing | Feature engineering |
| **6. Layer Algebra** | Complex layer selection | Advanced multilayer queries |
| **7. Per-Layer Aggregation** | Compare layers statistically | Layer-level analysis |
| **8. Interactive Hints** | Learn DSL as you build | Onboarding & discovery |

**💡 Pro Tip**: Run `dsl_patterns_quick_reference.py` to see all patterns with live output!

## Examples in This Category

### Tutorials
- **`tutorial_10min.py`** - 10-minute tutorial covering network creation, analysis, and visualization

### Using Built-in Datasets
- **`example_datasets.py`** - Load bundled datasets and generate synthetic networks (similar to scikit-learn's datasets module)

### Creating Networks
- **`example_random_generator.py`** - Generate random multilayer Erdős-Rényi networks
- **`example_random_generators_advanced.py`** - Advanced random network generators with custom parameters
- **`example_multilayer_functionality.py`** - Core multilayer network operations (adding nodes, edges, layers)

### Using NetworkX Integration
- **`example_networkx_wrapper.py`** - Apply NetworkX algorithms to multilayer networks
- **`example_networkx_wrapper_kwargs.py`** - NetworkX wrapper with keyword arguments support
- **`example_nx_wrapper.py`** - Compute betweenness centrality using NetworkX

## What's Next?

After completing these examples, explore:
- **[I/O and Data](../io_and_data/)** - Learn to load and save networks in various formats
- **[Network Analysis](../network_analysis/)** - Analyze network properties and compute metrics
- **[Visualization](../visualization/)** - Create beautiful visualizations of your networks

## Runtime Information

All examples in this directory are **FAST** (< 5 seconds) and standalone - perfect for learning!
