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
│   ├── core/               # Core network classes (multinet.py, temporal_multinet.py)
│   ├── algorithms/         # Network algorithms (including temporal/)
│   ├── visualization/      # Visualization tools
│   ├── dsl/               # SQL-like DSL for queries
│   ├── io/                # I/O handlers
│   ├── datasets/          # Built-in datasets
│   ├── plugins/           # Plugin system
│   ├── dynamics/          # Network dynamics simulations
│   ├── uncertainty/       # Bootstrap and null model analysis
│   ├── nullmodels/        # Null model implementations
│   ├── multinet/          # Multilayer aggregation utilities
│   ├── cli.py             # CLI entry point
│   ├── graph_ops.py       # Dplyr-style API
│   ├── pipeline.py        # Sklearn-style pipelines
│   ├── temporal_utils.py  # Temporal network utilities
│   └── workflows.py       # Config-driven workflows
├── tests/                  # Test suite
├── examples/               # Example scripts (170+)
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

### Temporal Networks

```python
from py3plex.core.temporal_multinet import TemporalMultiLayerNetwork

# Create temporal network
tnet = TemporalMultiLayerNetwork()
tnet.add_edge('A', 'B', layer='social', time=1.0)
tnet.add_edge('B', 'C', layer='social', time=2.0)

# Query temporal slices
snapshot = tnet.get_snapshot(time_range=(0, 1.5))
```

### Dynamics Simulations

```python
from py3plex.dynamics import DynamicsSimulator, SIRModel

# Define and run dynamics
sim = DynamicsSimulator(network)
results = sim.run(model=SIRModel(beta=0.3, gamma=0.1), steps=100)
```

### Uncertainty Analysis

```python
from py3plex.uncertainty import bootstrap_centrality
from py3plex.nullmodels import configuration_model

# Bootstrap confidence intervals
ci = bootstrap_centrality(net, measure='betweenness', n_samples=100)

# Null model comparison
null_net = configuration_model(net)
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

For comprehensive AI agent documentation with examples, see `AGENTS.md` in the repository root.

## Behavioral Guidelines

### What TO Do

1. **Make Minimal Changes:** Always prefer the smallest possible change to fix an issue
2. **Test Before Committing:** Run relevant tests after making changes
3. **Follow Existing Patterns:** Match the style and patterns of surrounding code
4. **Preserve Backward Compatibility:** The library has users - don't break existing APIs
5. **Use Domain Exceptions:** Always use `Py3plexIOError` instead of `FileNotFoundError` for I/O errors
6. **Validate Edge Cases:** Consider multilayer networks with zero nodes, single layers, disconnected components
7. **Check Documentation:** Update relevant docstrings and documentation files when changing APIs

### What NOT To Do

1. **Don't Break Tests:** Never modify or remove tests to make your changes pass. Fix the code instead.
2. **Don't Change Working Code:** If something works, don't refactor it unless specifically asked
3. **Don't Remove Features:** Even if unused, features may have external users
4. **Don't Ignore Linters:** Address linting issues in modified files
5. **Don't Add Unnecessary Dependencies:** Use existing libraries when possible
6. **Don't Modify Examples:** The `examples/` directory is intentionally excluded from linting

## API-Specific Patterns

### Multi_layer_network API

- The API uses `add_nodes()` and `add_edges()` (plural) - the `multi_layer_network` class doesn't expose singular forms
- Use `add_edges([...])` with list of dicts, NOT individual edge additions
- When serializing to JSON format with `to_json()`, the output uses `'edges'` key, not `'links'`
- The method signature is: `add_edges([{'source': ..., 'target': ..., 'source_type': ..., 'target_type': ...}])`

### DSL Architecture

- **DSL v2:** Modern builder API in `py3plex/dsl/` (preferred)
- **Legacy DSL:** String-based parsing in `py3plex/dsl_legacy.py` (keep for backward compatibility)
- Use `Q.nodes()` for builder API, `execute_query()` for legacy string queries
- DSL supports autocompute of centrality metrics - set `autocompute=False` to disable
- Layer selection: `FROM layer="name"` (canonical) or `WHERE layer="name"` (backward compat)

### DSL Edge Grouping and Coverage

- Use `per_layer()` for node queries, `per_layer_pair()` for edge queries
- Edge grouping groups by (src_layer, dst_layer) pairs
- Coverage filtering works for both nodes and edges: coverage > threshold
- QueryResult.meta["grouping"] contains structured grouping metadata
- Use `result.group_summary()` to get DataFrame summary of groups

### DSL Temporal Extensions

- DSL supports temporal queries via `.window()` builder method
- Temporal filters: `t__between`, `t__gte`, `t__lte`, `t__gt`, `t__lt` in `where()` clause
- WindowSpec AST node represents temporal query specifications

### Error Handling

```python
# Use domain-specific exceptions
from py3plex.exceptions import Py3plexIOError, Py3plexException

# For I/O errors
raise Py3plexIOError(f"Failed to read file: {path}")

# For general errors
raise Py3plexException("Invalid network configuration")
```

## Common Pitfalls

1. **NetworkX MultiGraph Limitations:** NetworkX's `clustering()` doesn't support MultiGraph. Convert to simple Graph first by merging parallel edges.

2. **Forward References in DSL:** Use string type hints for classes defined later in the same file:
   ```python
   def dynamics(self) -> "DynamicsBuilder":  # String, not direct reference
   ```

3. **Test Dependencies:** Tests require `pytest-benchmark` (listed in `dev` dependencies). Some examples may use additional packages like `sympy`.

4. **Type Checking:** mypy requires Python 3.9+ (see `pyproject.toml`). The project supports 3.8+ for runtime.

5. **Excluded Files:** `powerlaw.py` is intentionally excluded from linting due to legacy code issues.

## Security Guidelines

1. **Input Validation:** Always validate file paths and network data before processing
2. **No Arbitrary Code Execution:** Don't use `eval()` or `exec()` on user input
3. **File Operations:** Use safe file operations with proper error handling
4. **Dependencies:** Check new dependencies for known vulnerabilities before adding

## Testing Strategy

- **Unit Tests:** Extensive test suite in `tests/test_*.py` with comprehensive coverage
- **Property Tests:** Use Hypothesis for property-based testing (marked with `@pytest.mark.property`)
- **Integration Tests:** Marked with `@pytest.mark.integration`
- **Slow Tests:** Marked with `@pytest.mark.slow` - skip during development
- **Run Subset:** `pytest tests/test_dsl.py -k "test_specific_function"` for targeted testing

## Performance Considerations

1. **Large Networks:** Consider memory usage for networks with >10k nodes
2. **Centrality Computation:** Betweenness/closeness are expensive for large networks
3. **DSL Autocompute:** Disable with `autocompute=False` if metrics are pre-computed
4. **Benchmarks:** Available in `benchmarks/` directory for performance testing

## References

- **README.md:** Quick start and flagship example
- **AGENTS.md:** Comprehensive AI agent documentation
- **docfiles/:** Detailed documentation source files
- **examples/:** Comprehensive collection of working examples demonstrating features
- **pyproject.toml:** All dependencies, build config, and tool settings
