# Contributing to py3plex

Thank you for your interest in contributing to py3plex! This guide covers both human and AI-assisted contributions.

## Quick Start

```bash
# Clone and install
git clone https://github.com/SkBlaz/py3plex.git
cd py3plex
pip install -e ".[dev]"

# Run tests
python -m pytest tests/

# Lint code
black py3plex/
ruff check py3plex/
```

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git

### Installation

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev,tests]"

# Install pre-commit hooks
pre-commit install
```

## Code Style

### Python Style

- **Formatter**: Black (line length 88)
- **Linter**: Ruff
- **Type Checker**: mypy
- **Docstrings**: Google style

### Example

```python
def compute_centrality(
    network: "multi_layer_network",
    measure: str = "betweenness",
    **kwargs: Any,
) -> Dict[Node, float]:
    """Compute centrality for network nodes.
    
    Args:
        network: The multilayer network to analyze.
        measure: Centrality measure ('betweenness', 'closeness', etc.).
        **kwargs: Additional arguments passed to NetworkX.
    
    Returns:
        Dictionary mapping nodes to centrality values.
    
    Raises:
        CentralityComputationError: If computation fails.
    
    Example:
        >>> net = multi_layer_network()
        >>> net.add_edges([...])
        >>> scores = compute_centrality(net, measure='betweenness')
    """
    ...
```

## Testing

### Running Tests

```bash
# All tests
python -m pytest tests/

# Specific test file
python -m pytest tests/test_dsl.py

# With coverage
python -m pytest tests/ --cov=py3plex --cov-report=html

# Verbose output
python -m pytest tests/ -v

# Run only fast tests
python -m pytest tests/ -m "not slow"
```

### Writing Tests

```python
# tests/test_my_feature.py
import pytest
from py3plex.core import multinet

class TestMyFeature:
    def test_basic_functionality(self):
        """Test basic use case."""
        net = multinet.multi_layer_network()
        net.add_nodes([{'source': 'A', 'type': 'layer1'}])
        assert net.node_count == 1
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        net = multinet.multi_layer_network()
        assert net.is_empty
    
    def test_error_handling(self):
        """Test that appropriate errors are raised."""
        net = multinet.multi_layer_network()
        with pytest.raises(InvalidNodeError):
            net.add_nodes([{}])  # Missing required fields
```

## Pull Request Process

### Before Submitting

1. **Update tests**: Add or update tests for your changes
2. **Run the test suite**: `python -m pytest tests/`
3. **Lint your code**: `black py3plex/ && ruff check py3plex/`
4. **Update documentation**: If changing public API

### PR Guidelines

- Keep PRs focused on a single change
- Write clear commit messages
- Reference related issues
- Add tests for new functionality
- Update `llm.md` if adding significant features

## Project Structure

```
py3plex/
├── py3plex/                # Main package
│   ├── core/              # Core network classes
│   ├── algorithms/        # Network algorithms
│   ├── visualization/     # Visualization tools
│   ├── dsl/              # Query language
│   ├── io/               # I/O handlers
│   ├── datasets/         # Built-in datasets
│   ├── plugins/          # Plugin system
│   └── cli.py            # CLI implementation
├── tests/                 # Test suite
├── examples/              # Example scripts
├── docfiles/              # Documentation source
└── benchmarks/            # Performance benchmarks
```

## Key Files for New Contributors

| File | Purpose |
|------|---------|
| `py3plex/__init__.py` | Main exports, version |
| `py3plex/core/multinet.py` | Core `multi_layer_network` class |
| `py3plex/dsl/__init__.py` | DSL implementation |
| `py3plex/exceptions.py` | Exception hierarchy |
| `llm.md` | Comprehensive LLM documentation |

## Adding New Features

### New Algorithm

1. Create `py3plex/algorithms/my_algorithm.py`
2. Implement with type hints and docstrings
3. Add tests in `tests/test_my_algorithm.py`
4. Export in `py3plex/algorithms/__init__.py`
5. Document in `docfiles/`

### New CLI Command

1. Add function in `py3plex/cli.py`:
   ```python
   @cli.command()
   @click.argument("input_file")
   @click.option("--output", "-o", help="Output file")
   def my_command(input_file, output):
       """Description of my command."""
       ...
   ```
2. Add tests in `tests/test_cli.py`
3. Document in `docfiles/deployment/cli_usage.rst`

### New Plugin Type

1. Create class extending `BasePlugin` in `py3plex/plugins/`
2. Register with `PluginRegistry`
3. Add tests in `tests/test_plugin_system.py`

## For AI Assistants

If you're an AI assistant contributing to this project:

1. **Read first**: Review `llm.md` for comprehensive documentation
2. **Follow patterns**: Match existing code style and patterns
3. **Test thoroughly**: Add tests for all new functionality
4. **Minimal changes**: Make focused, minimal modifications
5. **Document**: Update relevant documentation

### Key Context Files

- `llm.md` - Full LLM-optimized documentation
- `CLAUDE.md` - Claude-specific context
- `.github/copilot-instructions.md` - Copilot instructions

## Getting Help

- **Issues**: Open an issue on GitHub
- **Documentation**: https://skblaz.github.io/py3plex/
- **Examples**: See `examples/` directory

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
