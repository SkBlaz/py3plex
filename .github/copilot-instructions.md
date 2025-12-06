# GitHub Copilot Instructions for py3plex

> This file provides context and guidelines for GitHub Copilot when working with the py3plex codebase.

## Project Overview

py3plex is a Python library for analyzing and visualizing multilayer and multiplex networks. It provides:

- **Core Features:** Native support for multilayer network structures, SQL-like DSL for network queries, dplyr-style chainable API, sklearn-style pipelines
- **Version:** 1.0 (see `pyproject.toml`)
- **Python Support:** 3.8+

## Repository Structure

```
py3plex/
├── py3plex/                 # Main package
│   ├── core/               # Core network classes (multinet.py)
│   ├── algorithms/         # Network algorithms
│   ├── visualization/      # Visualization tools
│   ├── dsl/               # SQL-like DSL for queries
│   ├── io/                # I/O handlers
│   ├── datasets/          # Built-in datasets
│   ├── plugins/           # Plugin system
│   ├── cli.py             # CLI entry point
│   ├── graph_ops.py       # Dplyr-style API
│   ├── pipeline.py        # Sklearn-style pipelines
│   └── workflows.py       # Config-driven workflows
├── tests/                  # Test suite
├── examples/               # Example scripts (50+)
├── docfiles/               # Documentation source
├── gui/                    # Web GUI (FastAPI + SvelteKit)
└── benchmarks/             # Performance benchmarks
```

## Key Code Patterns

### Network Creation

```python
from py3plex.core import multinet

# Create network
net = multinet.multi_layer_network(directed=False)

# Add nodes (dict-based API)
net.add_nodes([
    {'source': 'Alice', 'type': 'social'},
    {'source': 'Bob', 'type': 'social'},
])

# Add edges (dict-based API)
net.add_edges([
    {'source': 'Alice', 'target': 'Bob', 
     'source_type': 'social', 'target_type': 'social'},
])
```

### DSL Queries

```python
from py3plex.dsl import execute_query

# SQL-like syntax
result = execute_query(net, 'SELECT nodes WHERE layer="social"')
result = execute_query(net, 'SELECT nodes WHERE degree > 2 COMPUTE betweenness_centrality')
```

### Dplyr-Style Operations

```python
from py3plex.graph_ops import nodes

df = (
    nodes(net)
    .filter(lambda n: n["degree"] > 1)
    .mutate(score=lambda n: n["degree"] * 2)
    .arrange("degree", reverse=True)
    .to_pandas()
)
```

## Coding Conventions

1. **Type Hints:** Use type hints for all public functions
2. **Docstrings:** Use Google-style docstrings
3. **Testing:** Add tests to `tests/` for new features
4. **Exceptions:** Use domain-specific exceptions from `py3plex.exceptions`

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_dsl.py

# Run with coverage
python -m pytest tests/ --cov=py3plex
```

## Linting

```bash
# Format code
black py3plex/

# Lint
ruff check py3plex/

# Type checking
mypy py3plex/
```

## Common Tasks

### Adding a New Algorithm

1. Create file in `py3plex/algorithms/`
2. Add tests in `tests/test_<algorithm>.py`
3. Export from `py3plex/algorithms/__init__.py`
4. Document in `docfiles/`

### Adding a CLI Command

1. Add function in `py3plex/cli.py`
2. Register with Click decorator
3. Add tests in `tests/test_cli.py`

### Adding a Plugin

1. Extend `BasePlugin` or specific plugin type
2. Implement `name`, `description`, and `compute` methods
3. Register with `PluginRegistry`

## Important Files

- `py3plex/__init__.py` - Main exports
- `py3plex/core/multinet.py` - Core `multi_layer_network` class
- `py3plex/dsl/__init__.py` - DSL implementation
- `py3plex/cli.py` - CLI implementation
- `py3plex/config.py` - Configuration constants
- `py3plex/exceptions.py` - Exception hierarchy

## Dependencies

Core dependencies (from `pyproject.toml`):
- numpy, scipy, networkx - Core data structures
- matplotlib, seaborn - Visualization
- scikit-learn - ML utilities
- gensim - Embeddings

## Documentation

For comprehensive LLM documentation with examples, see `llm.md` in the repository root.
