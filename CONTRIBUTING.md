# Contributing to Py3plex

Thank you for considering contributing to py3plex! This document provides guidelines and best practices for contributing to the project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Standards](#code-standards)
5. [Documentation](#documentation)
6. [Testing](#testing)
7. [Pull Request Process](#pull-request-process)
8. [Issue Guidelines](#issue-guidelines)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic knowledge of network science and Python

### Setting Up Development Environment

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/py3plex.git
   cd py3plex
   ```

3. Set up the development environment:
   ```bash
   make setup
   make dev-install
   ```

4. Activate the virtual environment:
   ```bash
   source .venv/bin/activate  # Linux/macOS
   # or
   .venv\Scripts\activate  # Windows
   ```

## Development Workflow

### Branch Strategy

- `main`: Stable release branch
- `develop`: Development branch for integration
- Feature branches: `feature/your-feature-name`
- Bugfix branches: `bugfix/issue-number-description`

### Making Changes

1. Create a new branch from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/my-feature
   ```

2. Make your changes following the [code standards](#code-standards)

3. Test your changes:
   ```bash
   make test
   ```

4. Format and lint your code:
   ```bash
   make format
   make lint
   ```

5. Commit with clear messages:
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

6. Push to your fork:
   ```bash
   git push origin feature/my-feature
   ```

7. Create a Pull Request on GitHub

## Code Standards

### Style Guide (PEP 8)

- **Line length**: Maximum 88 characters (Black formatter default)
- **Indentation**: 4 spaces (no tabs)
- **Imports**: Grouped by standard library, third-party, and internal
  ```python
  import os
  import sys
  
  import numpy as np
  import networkx as nx
  
  from py3plex.core import multinet
  from py3plex.logging_config import get_logger
  ```
- **Naming conventions**:
  - Functions: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_CASE`
  - Private: `_leading_underscore`

### Type Hints (Required)

All new functions and methods must include type hints:

```python
from typing import Dict, List, Optional

def process_network(
    network: nx.Graph,
    layers: List[str],
    threshold: float = 0.5
) -> Dict[str, int]:
    """Process a multilayer network.
    
    Args:
        network: NetworkX graph to process
        layers: List of layer identifiers
        threshold: Edge weight threshold (default: 0.5)
        
    Returns:
        Dictionary mapping layers to node counts
        
    Raises:
        ValueError: If threshold is not between 0 and 1
    """
    if not 0 <= threshold <= 1:
        raise ValueError("Threshold must be between 0 and 1")
    # ... implementation ...
```

### Docstring Style (NumPy/Google)

Use NumPy or Google-style docstrings consistently:

```python
def my_function(param1: int, param2: str) -> bool:
    """
    Brief description of function.
    
    More detailed description if needed. Explain the purpose,
    behavior, and any important implementation details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When invalid input is provided
        NetworkError: When network operation fails
        
    Example:
        >>> result = my_function(42, "test")
        >>> print(result)
        True
        
    Note:
        Additional notes or warnings for users.
    """
    # Implementation
    pass
```

### Error Handling

Use py3plex's custom exception types:

```python
from py3plex.exceptions import (
    NetworkConstructionError,
    InvalidLayerError,
    VisualizationError,
)

def add_layer(network, layer_id):
    if layer_id in network.layers:
        raise InvalidLayerError(f"Layer '{layer_id}' already exists")
    
    try:
        # ... operation ...
    except KeyError as e:
        raise NetworkConstructionError(
            f"Failed to add layer: {e}"
        ) from e
```

Never use bare `except:` clauses. Always catch specific exceptions.

### Logging

Use structured logging instead of print statements:

```python
from py3plex.logging_config import get_logger

logger = get_logger(__name__)

def my_function():
    logger.info("Starting operation")
    logger.debug("Detailed debug information")
    logger.warning("Warning message")
    logger.error("Error occurred")
```

### Configuration

Use the centralized config module for defaults:

```python
from py3plex import config

def visualize_network(
    network,
    node_size: int = None,
    color_palette: str = None
):
    # Use config defaults if not provided
    node_size = node_size or config.DEFAULT_NODE_SIZE
    colors = config.get_color_palette(
        color_palette or config.DEFAULT_COLOR_PALETTE
    )
    # ... implementation ...
```

### Deprecation Warnings

When deprecating features, use the deprecation utilities:

```python
from py3plex.utils import deprecated, warn_if_deprecated

@deprecated(
    reason="This function is obsolete",
    version="0.95a",
    alternative="new_function()"
)
def old_function():
    pass

def my_function(old_param=None, new_param=None):
    if old_param is not None:
        warn_if_deprecated(
            "old_param",
            "Use new_param instead",
            "new_param"
        )
```

## Documentation

### Algorithm Citations

When implementing algorithms, **always** cite the original publication:

1. Add citation to function/class docstring:
   ```python
   def louvain_communities(G):
       """
       Detect communities using the Louvain algorithm.
       
       This implements the algorithm described in:
       Blondel, V. D., et al. (2008). Fast unfolding of communities 
       in large networks. Journal of Statistical Mechanics: Theory 
       and Experiment, 2008(10), P10008.
       https://doi.org/10.1088/1742-5468/2008/10/P10008
       
       Args:
           G: NetworkX graph
           
       Returns:
           Community assignment dictionary
       """
   ```

2. Update `docs/ALGORITHM_CITATIONS.md` with full citation

### README and Examples

- Update README.md if you add user-facing features
- Add examples to `examples/` directory
- Ensure examples run without errors
- Use `argparse` for command-line examples
- Use `pathlib` for file paths

### Architecture Documentation

For significant changes to architecture, update `docs/ARCHITECTURE.md`.

## Testing

### Writing Tests

- Place tests in `tests/` directory
- Use `test_*.py` naming convention
- Group related tests in classes
- Use descriptive test names

```python
import pytest
from py3plex.core import multinet

class TestMultilayerNetwork:
    """Tests for multilayer network operations."""
    
    def test_network_creation(self):
        """Test basic network creation."""
        mlnet = multinet.multi_layer_network()
        assert mlnet is not None
        
    def test_layer_addition(self):
        """Test adding layers to network."""
        mlnet = multinet.multi_layer_network()
        mlnet.add_layer(nx.Graph(), layer_id=0)
        assert mlnet.get_number_of_layers() == 1
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/test_core_functionality.py

# Run with coverage
pytest tests/ --cov=py3plex --cov-report=html
```

### Test Coverage

- Aim for 85%+ coverage for new code
- Mock external dependencies (Infomap, Node2Vec)
- Test both success and error cases
- Test edge cases and boundary conditions

## Pull Request Process

### Before Submitting

1. ✅ All tests pass: `make test`
2. ✅ Code is formatted: `make format`
3. ✅ Linting passes: `make lint`
4. ✅ Documentation is updated
5. ✅ CHANGELOG.md is updated (for user-facing changes)
6. ✅ Type hints are complete
7. ✅ Docstrings follow NumPy/Google style

### PR Description Template

```markdown
## Description
Brief description of changes

## Related Issue
Fixes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Testing
- [ ] All existing tests pass
- [ ] Added new tests for changes
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Type hints added
- [ ] Docstrings added/updated
- [ ] CHANGELOG.md updated
- [ ] Documentation updated
- [ ] Tests added/updated
```

### Review Process

1. Maintainers will review your PR
2. Address review comments
3. Once approved, maintainers will merge

## Issue Guidelines

### Reporting Bugs

Use the bug report template and include:

- **Description**: Clear description of the bug
- **Steps to reproduce**: Minimal code example
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: Python version, OS, py3plex version

### Feature Requests

Use the feature request template and include:

- **Problem**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Alternatives**: What alternatives have you considered?
- **Additional context**: Any other relevant information

### Questions

For questions, please use GitHub Discussions rather than issues.

## Additional Resources

- [Architecture Documentation](docs/ARCHITECTURE.md)
- [Algorithm Citations](docs/ALGORITHM_CITATIONS.md)
- [Development Guide](docs/development.md)
- [10-Minute Tutorial](docs/10min_tutorial.md)

## Recognition

Contributors will be acknowledged in:
- CHANGELOG.md (for significant contributions)
- GitHub contributors page
- Publication acknowledgments (when applicable)

Thank you for contributing to py3plex! 🎉
