# Docstring Testing Guide

This document explains how docstring examples are tested in py3plex to ensure they remain correct and executable.

## Overview

Docstring examples in py3plex are automatically tested using pytest's built-in doctest support. This ensures that code examples in documentation are always accurate and up-to-date.

## Configuration

Doctest support is enabled in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests", "py3plex"]
addopts = [
    "--doctest-modules",
    "--doctest-continue-on-failure",
]
doctest_optionflags = [
    "NORMALIZE_WHITESPACE",
    "ELLIPSIS",
    "IGNORE_EXCEPTION_DETAIL",
]
```

## Running Doctests

### Run all doctests
```bash
pytest --doctest-modules py3plex/
```

### Run doctests for specific modules
```bash
pytest --doctest-modules py3plex/dsl.py
pytest --doctest-modules py3plex/core/multinet.py
```

### Run the dedicated doctest validation suite
```bash
pytest tests/test_doctests.py -v
```

## Writing Docstring Examples

### Executable Examples

Write examples that can be executed during testing:

```python
def add_nodes(self, nodes):
    """Add nodes to the network.
    
    Examples:
        >>> from py3plex.core import multinet
        >>> net = multinet.multi_layer_network()
        >>> net.add_nodes([{'source': 'A', 'type': 'layer1'}])
        >>> len(list(net.get_nodes()))
        1
    """
    pass
```

### Non-Executable Examples

For examples that require external files, optional dependencies, or complex setup, use the `# doctest: +SKIP` directive:

```python
def serialize_to_edgelist(self, edgelist_file):
    """Serialize network to edgelist file.
    
    Examples:
        Example requires file output - for illustration only.
        
        >>> net = multi_layer_network()  # doctest: +SKIP
        >>> net.add_nodes([{'source': 'A', 'type': 'L1'}])  # doctest: +SKIP
        >>> net.serialize_to_edgelist('output.txt')  # doctest: +SKIP
    """
    pass
```

### When to Use +SKIP

Use `# doctest: +SKIP` when examples:
- Require external files that don't exist
- Require optional dependencies (e.g., sympy, plotly)
- Create file outputs
- Require complex setup that would obscure the example
- Are for illustration purposes only

## Best Practices

1. **Keep examples simple**: Focus on demonstrating the main functionality
2. **Use realistic data**: Examples should show typical usage patterns
3. **Test the output**: Include assertions or expected output to verify correctness
4. **Self-contained**: Examples should be runnable without external dependencies when possible
5. **Document when skipping**: Add a brief note explaining why an example is marked with +SKIP

## Common Patterns

### Pattern 1: Creating a network and adding data
```python
>>> from py3plex.core import multinet
>>> net = multinet.multi_layer_network()
>>> net.add_nodes([{'source': 'A', 'type': 'layer1'}])
>>> net.add_edges([{
...     'source': 'A', 'target': 'B',
...     'source_type': 'layer1', 'target_type': 'layer1'
... }])
```

### Pattern 2: Testing return values
```python
>>> result = some_function(param)
>>> len(result) > 0
True
>>> isinstance(result, dict)
True
```

### Pattern 3: Using ELLIPSIS for partial output
```python
>>> print(network)  # doctest: +ELLIPSIS
<multi_layer_network: ... nodes=3, edges=2, ...>
```

## Current Status

- **Total docstring examples**: 27
- **Executable and passing**: 18
- **Skipped (non-executable)**: 9
- **Modules with doctests**: dsl, core.multinet, core.parsers, core.supporting

## Maintenance

When adding new functions or modifying existing ones:
1. Add or update docstring examples
2. Run `pytest --doctest-modules py3plex/` to verify
3. Mark non-executable examples with `# doctest: +SKIP`
4. Update this documentation if introducing new patterns

## Troubleshooting

### Import errors
Make sure all required dependencies are installed:
```bash
pip install -e ".[dev,tests]"
```

### Doctest failures
- Check if the expected output matches exactly
- Use `# doctest: +NORMALIZE_WHITESPACE` for whitespace differences
- Use `# doctest: +ELLIPSIS` and `...` for partial matching
- Check if the example requires setup that's missing

### File-related errors
Examples that create or read files should be marked with `# doctest: +SKIP`

## Integration with CI/CD

Doctests run automatically in the CI/CD pipeline as part of the test suite. Any doctest failures will cause the build to fail, ensuring documentation stays accurate.
