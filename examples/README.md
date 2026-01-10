# Py3plex Examples

This directory contains **minimal, focused examples** demonstrating core py3plex functionality.

## Philosophy

> Examples are onboarding instruments, not encyclopedias.

Each example:
- Demonstrates **exactly 1-2 concepts**
- Runs in **< 2 seconds**
- Is **25-40 lines** of code
- Uses **small datasets** (load_aarhus_cs or synthetic)
- Has **clear comments** explaining each step

## Structure

### 00_quickstart/
**Goal:** First 5 minutes with py3plex

- `01_load_and_query.py` - Load dataset + basic DSL query
- `02_create_and_visualize.py` - Create network from scratch
- `03_communities.py` - Simple community detection

### 01_network_construction/
**Goal:** How to build networks

- `01_from_edges.py` - Build from edge list
- `02_fluent_building.py` - Method chaining
- `03_from_networkx.py` - Convert from NetworkX

### 02_basic_queries/
**Goal:** Mental model of querying

- `01_legacy_string_dsl.py` - Legacy string syntax (backward compat)
- `02_select_by_layer.py` - Layer filtering
- `03_filter_by_degree.py` - Degree filtering
- `04_compute_centrality.py` - Single metric computation

### 03_dsl_v2/
**Goal:** Modern recommended querying (DSL v2)

- `01_builder_basic.py` - Q.nodes() builder pattern
- `02_layer_algebra.py` - Layer unions/intersections
- `03_grouping_aggregation.py` - Per-layer grouping
- `04_explain.py` - Query explanation

### 04_graph_ops/
**Goal:** dplyr-style operations

- `01_filter_mutate.py` - Filter + add columns
- `02_group_summarise.py` - Group by + aggregation
- `03_subgraph.py` - Subgraph extraction

### 05_communities/
**Goal:** Community detection

- `01_louvain_single.py` - Single-layer Louvain
- `02_multilayer_detection.py` - Multilayer communities
- `03_auto_community.py` - AutoCommunity (flagship)

### 06_dynamics/
**Goal:** Dynamical processes

- `01_sis_epidemic.py` - SIS epidemic model
- `02_multilayer_epidemic.py` - Multilayer spreading
- `03_custom_model.py` - Custom dynamics

### 07_uncertainty/
**Goal:** Uncertainty quantification

- `01_uq_centrality.py` - UQ-enabled centrality
- `02_bootstrap.py` - Bootstrap sampling
- `03_comparison.py` - UQ vs deterministic

## Running Examples

All examples are standalone scripts:

```bash
# Run single example
python examples/00_quickstart/01_load_and_query.py

# Run all examples in a folder
python -m pytest examples/00_quickstart/ -v
```

## Dependencies

All examples use **base dependencies only** (no optional packages required), except:
- `05_communities/03_auto_community.py` - Requires `pip install py3plex[algos]`

## For Advanced Use Cases

These examples cover **essential patterns**. For advanced topics, see:

- **Documentation:** https://skblaz.github.io/py3plex/
- **Book (PDF):** docs/py3plex_book.pdf (106 pages)
- **Notebooks:** notebooks/ directory
- **Benchmarks:** benchmarks/ directory

## Contributing

When adding examples:
- Keep it minimal (1 concept per file)
- Use load_aarhus_cs() when possible
- Run in < 2 seconds
- Follow existing structure
- Update this README
