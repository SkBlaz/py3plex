# CLAUDE.md - Claude AI Context for py3plex

> This file provides context for Claude (Anthropic AI) when working with the py3plex codebase.

## Quick Reference

**py3plex** is a Python library for multilayer network analysis and visualization.

| Aspect | Details |
|--------|---------|
| **Language** | Python 3.8+ |
| **Version** | 1.0 |
| **License** | MIT |
| **Main Class** | `multi_layer_network` |
| **Package** | `py3plex` |

## Build & Test Commands

```bash
# Install in development mode
pip install -e .

# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_dsl.py -v

# Lint and format
black py3plex/
ruff check py3plex/
mypy py3plex/

# Build documentation
cd docfiles && make html
```

## Project Architecture

```
py3plex/
├── core/multinet.py     # multi_layer_network class - MAIN ENTRY POINT
├── dsl/                 # SQL-like query language
├── graph_ops.py         # Dplyr-style chainable API (filter, mutate, arrange)
├── pipeline.py          # Sklearn-style pipelines
├── workflows.py         # YAML/JSON workflow definitions
├── cli.py               # Command-line interface (Click-based)
├── plugins/             # Extensible plugin system
├── datasets/            # Built-in datasets (load_aarhus_cs, make_random_multilayer)
├── algorithms/          # Network algorithms (community, centrality, embeddings)
├── visualization/       # Plotting and layouts
├── io/                  # File I/O (edgelist, graphml, gml, json, arrow)
├── exceptions.py        # Domain-specific exceptions
├── config.py            # Visualization/layout configuration
└── profiling.py         # Performance monitoring
```

## Core Concepts

### 1. Multilayer Networks

Nodes exist in layers, edges connect nodes within or across layers:

```python
from py3plex.core import multinet

net = multinet.multi_layer_network(directed=False)
net.add_nodes([{'source': 'A', 'type': 'layer1'}])
net.add_edges([{'source': 'A', 'target': 'B', 
                'source_type': 'layer1', 'target_type': 'layer1'}])
```

### 2. DSL Queries (SQL-like)

```python
from py3plex.dsl import execute_query

# Basic query
result = execute_query(net, 'SELECT nodes WHERE layer="social"')

# With computation
result = execute_query(net, 'SELECT nodes WHERE degree > 2 COMPUTE betweenness_centrality')
```

### 3. Graph Operations (dplyr-style)

```python
from py3plex.graph_ops import nodes

df = (nodes(net)
      .filter(lambda n: n["degree"] > 1)
      .mutate(score=lambda n: n["degree"] * 2)
      .group_by("layer")
      .summarise(avg=("degree", np.mean))
      .to_pandas())
```

### 4. Pipelines (sklearn-style)

```python
from py3plex.pipeline import Pipeline, LoadStep, ComputeStats

pipe = Pipeline([
    ("load", LoadStep(generator='random_er', num_nodes=100)),
    ("stats", ComputeStats()),
])
result = pipe.run()
```

## Key Design Decisions

1. **Dict-based API**: Nodes/edges use dictionaries with 'source', 'target', 'type' keys
2. **NetworkX Backend**: Uses `networkx.Graph` or `DiGraph` as `core_network`
3. **Layered Architecture**: Nodes are tuples `(node_id, layer_id)`
4. **Fluent Interface**: Methods return `self` for chaining
5. **Plugin System**: Extend via `CentralityPlugin`, `CommunityPlugin`, etc.

## Exception Hierarchy

```python
Py3plexException (base)
├── NetworkConstructionError
├── ParsingError
├── AlgorithmError
│   ├── CommunityDetectionError
│   ├── CentralityComputationError
│   └── DecompositionError
├── VisualizationError
└── Py3plexIOError
```

## CLI Usage

```bash
py3plex --help                    # Show all commands
py3plex create --nodes 100        # Create random network
py3plex load file.edgelist        # Load and inspect
py3plex community file.edgelist   # Detect communities
py3plex centrality file.edgelist  # Compute centrality
py3plex visualize file.edgelist   # Visualize network
py3plex quickstart                # Interactive demo
```

## Testing Patterns

```python
# Unit test pattern
def test_feature():
    net = multinet.multi_layer_network()
    net.add_nodes([{'source': 'A', 'type': 'l1'}])
    assert len(list(net.get_nodes())) == 1

# Property-based test (Hypothesis)
from hypothesis import given, strategies as st

@given(st.integers(1, 100))
def test_random_network(n):
    net = make_random_multilayer(n_nodes=n, n_layers=2)
    assert net.node_count >= n
```

## Documentation Resources

- **Full LLM docs**: See `llm.md` in repository root
- **API Reference**: `docfiles/apidocs.rst`
- **Examples**: `examples/` directory (50+ scripts)
- **Online docs**: https://skblaz.github.io/py3plex/

## Common Modifications

### Adding a new algorithm

1. Create `py3plex/algorithms/my_algo.py`
2. Add tests in `tests/test_my_algo.py`
3. Export in `py3plex/algorithms/__init__.py`

### Adding a CLI command

1. Add function in `py3plex/cli.py` with `@cli.command()` decorator
2. Add tests in `tests/test_cli.py`

### Adding a dataset

1. Add to `py3plex/datasets/__init__.py`
2. Create loader function following `load_aarhus_cs` pattern
