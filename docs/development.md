# Development Guide

This guide covers development workflows, testing, and contributing to py3plex.

## Table of Contents

- [Getting Started with Development](#getting-started-with-development)
- [Makefile Commands](#makefile-commands)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Contributing](#contributing)

## Getting Started with Development

### Initial Setup

Clone the repository and install in development mode:

```bash
git clone https://github.com/SkBlaz/py3plex.git
cd py3plex

# Setup development environment (creates .venv and installs dependencies)
make setup

# Install package in editable mode with dev dependencies
make dev-install
```

### Learning py3plex

**New to py3plex?** Start with our [10-minute tutorial](10min_tutorial.md)!

You can also run the executable version:
```bash
cd examples
python tutorial_10min.py
```

For more examples, view the **examples** folder.

## Makefile Commands

For a streamlined development experience, use the provided Makefile. The Makefile provides a unified entrypoint for all development, testing, and publishing workflows.

### Key Features

- **Smart tool detection**: Automatically uses tools from `.venv/bin/` if available, otherwise falls back to globally installed tools (enabling CI compatibility)
- **Colorized output**: ANSI color codes for better readability (green for success, yellow for warnings, red for errors)
- **Virtual environment management**: `make setup` creates `.venv` and installs all dependencies
- **Cross-platform**: Works on Linux and macOS

### Available Commands

#### Environment Setup

```bash
# View all available commands
make help

# Create virtual environment and install dependencies
make setup

# Install package in editable mode with dev dependencies
make dev-install
```

#### Code Quality

```bash
# Auto-format code with isort, black, and ruff
make format

# Run linters and type checker
make lint
```

#### Testing

```bash
# Run tests with coverage
make test

# Open coverage report in browser
make coverage
```

#### Documentation

```bash
# Build documentation
make docs
```

#### Build & Publish

```bash
# Clean build artifacts and caches
make clean

# Build distribution packages
make build

# Publish to PyPI (requires TWINE_USERNAME and TWINE_PASSWORD)
make publish
```

#### Verification & CI

```bash
# Verify API exports
make api-check

# Run CI checks (lint + test)
make ci
```

### Development Workflow

1. `make setup` - Initial environment setup (one-time)
2. `make dev-install` - Install package in editable mode
3. `make format` - Auto-format code before committing
4. `make lint` - Check code quality
5. `make test` - Run tests with coverage
6. `make ci` - Full CI checks before pushing

## Testing

### Quick Testing

The simplest way to run tests:

```bash
python run_tests.py
```

### Development Testing with pytest

For more control and features:

```bash
# Install dev dependencies (if not already done)
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=py3plex --cov-report=html

# Run specific test file
pytest tests/test_core.py

# Run with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "test_network"
```

### Using the Makefile

```bash
# Run tests with coverage (recommended)
make test

# Open HTML coverage report
make coverage
```

## Code Quality

### Tools

The project uses several tools for maintaining code quality:

- **Black**: Code formatting (`black py3plex/`)
- **Ruff**: Fast linting (`ruff check py3plex/ --fix`)
- **isort**: Import sorting (`isort py3plex/`)
- **Mypy**: Type checking (`mypy py3plex/ --ignore-missing-imports`)
- **Pytest**: Testing with coverage

### Configuration

All tools are configured in `pyproject.toml`. The Makefile provides convenient commands for running them.

### Pre-commit Hooks

Optional but recommended:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install

# Run pre-commit manually on all files
pre-commit run --all-files
```

### Formatting Your Code

Before committing:

```bash
make format
```

This runs:
1. `isort` - Sorts imports
2. `black` - Formats code
3. `ruff --fix` - Applies automatic fixes

### Checking Code Quality

```bash
make lint
```

This runs:
1. `ruff` - Linting
2. `isort --check-only` - Import order check
3. `black --check` - Format check
4. `mypy` - Type checking

## Contributing

We welcome contributions! Here's how to get started:

### Opening Issues

- **Bug reports**: Include minimal reproduction steps, expected vs actual behavior, and environment details
- **Feature requests**: Describe the use case and proposed API
- **Questions**: Feel free to ask about usage or design decisions

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting: `make ci`
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

### Code Guidelines

- Follow existing code style (enforced by `black` and `ruff`)
- Add tests for new features
- Update documentation as needed
- Keep changes focused and atomic
- Write clear commit messages

### Testing Your Changes

```bash
# Format code
make format

# Run linting
make lint

# Run tests
make test

# Or run everything at once (recommended before PR)
make ci
```

## CI/CD

The project uses GitHub Actions for continuous integration:

- **Tests workflow**: Runs on Python 3.8-3.12 with full and minimal dependencies
- **Code quality workflow**: Runs linting, formatting checks, and type checking
- **Tutorial validation workflow**: Validates the 10-minute tutorial

All workflows use Makefile commands for consistency with local development.

## Documentation

### Building Documentation

Documentation is built using Sphinx:

```bash
# Using Makefile (recommended)
make docs

# Manual build
cd docfiles
sphinx-build -b html . _build/html
```

The built documentation will be in `docfiles/_build/html/`.

### Documentation Structure

- `docfiles/`: Source ReStructuredText files and Sphinx configuration
- `docs/`: Markdown tutorials and guides
- `examples/`: Executable example scripts (primary learning resource)

### Adding Documentation

1. Update or create `.rst` files in `docfiles/`
2. Add markdown guides to `docs/` for tutorials
3. Add example scripts to `examples/` with inline comments
4. Rebuild documentation with `make docs`

## Project Context

For comprehensive project context, development status, and guidance for maintainers and LLMs, see [LLM.md](../LLM.md).

## Resources

- **Repository**: https://github.com/SkBlaz/py3plex
- **Documentation**: https://skblaz.github.io/py3plex/
- **Issues**: https://github.com/SkBlaz/py3plex/issues
- **Examples**: https://github.com/SkBlaz/Py3Plex/tree/master/examples
