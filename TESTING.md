# Testing Instructions for Py3plex

This document explains how to run tests for the py3plex project.

## Quick Start

The simplest way to run tests:

```bash
python run_tests.py
```

This will run all available tests and provide a clear summary.

## Test Files

The test suite includes:

- `tests/test_infomap_fix.py` - Integration test for the infomap community detection fix
- `tests/test_core_functionality.py` - Core functionality tests (requires full dependencies)
- `tests/test_code_improvements.py` - Tests for Phase 1A/1B code improvements
- `tests/test_networkx_compatibility.py` - NetworkX compatibility tests
- `tests/test_multilayer_centrality.py` - Multilayer network centrality tests
- `tests/test_multilayer_edge_fix.py` - Edge handling tests

## Running Tests

### Option 1: Recommended Test Runner

```bash
python run_tests.py
```

This will run all available tests and provide a clear summary.

### Option 2: Using Pytest (Development)

If you have dev dependencies installed:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=py3plex --cov-report=html

# Run specific test file
pytest tests/test_infomap_fix.py

# Run with verbose output
pytest -v
```

### Option 3: Run Individual Tests

Run the infomap fix test (minimal dependencies):
```bash
python tests/test_infomap_fix.py
```

Run core functionality tests (requires full installation):
```bash
python -c "from tests.test_core_functionality import test_imports; test_imports()"
```

### Option 4: Using unittest

If you prefer unittest:
```bash
python -m unittest discover tests/ -v
```

## Development Testing Workflow

When developing new features:

1. **Write tests first** (Test-Driven Development)
2. **Run tests frequently** during development
3. **Use pytest watch mode** for continuous testing:
   ```bash
   pytest-watch  # requires: pip install pytest-watch
   ```
4. **Check coverage** to ensure new code is tested:
   ```bash
   pytest --cov=py3plex --cov-report=term-missing
   ```

## Linting and Formatting

Before committing code, ensure it passes linting:

```bash
# Format code with black
black py3plex/

# Lint with ruff
ruff check py3plex/ --fix

# Type check with mypy
mypy py3plex/ --ignore-missing-imports
```

See [STATUS.md](./STATUS.md) for more details on development tools.

## Dependencies

### Minimal Testing (infomap fix only)
No additional dependencies required beyond Python 3.8+

### Full Testing
Install the full package with dependencies:
```bash
pip install -e .
```

Or install test dependencies manually:
```bash
pip install numpy scipy networkx matplotlib plotnine cython tqdm gensim scikit-learn bitarray seaborn rdflib
```

## Test Results

- ✅ **test_infomap_fix.py**: Tests the FileNotFoundError fix for infomap community detection
- ⚠️ **test_core_functionality.py**: Requires matplotlib and other visualization dependencies

## Continuous Integration

### GitHub Actions (Automated)

The repository uses GitHub Actions for automated testing and code quality checks:

#### Test Workflow
Runs on every push and pull request to `main`, `master`, or `develop` branches:
- **Multiple Python versions**: Tests on Python 3.8, 3.9, 3.10, and 3.11
- **Full test suite**: Runs all tests using `python run_tests.py`
- **Minimal dependencies test**: Ensures core functionality works with minimal deps
- **Test timeout protection**: Prevents hanging tests

#### Code Quality Workflow
Automated code quality checks:
- **Ruff linting**: Fast Python linter checking PEP 8 compliance and common issues
- **Black formatting**: Ensures consistent code formatting  
- **Mypy type checking**: Static type checking (informational only)

The codebase has been formatted and linted. Ruff is configured to ignore certain legacy code patterns and issues in unused code paths to allow for incremental modernization.

View CI status: [![Tests](https://github.com/SkBlaz/py3plex/actions/workflows/tests.yml/badge.svg)](https://github.com/SkBlaz/py3plex/actions/workflows/tests.yml)

### Manual CI Setup

To set up automated testing on other CI systems:

1. Install Python 3.8+
2. Install dependencies: `pip install -e .`
3. Run tests: `python run_tests.py`

## Contributing

When adding new tests:
1. Create test files with the `test_*.py` naming pattern in the `tests/` directory
2. Use descriptive function names starting with `test_`
3. Ensure tests can run independently
4. Document any special requirements
5. Add markers for slow or integration tests:
   ```python
   import pytest
   
   @pytest.mark.slow
   def test_long_running_operation():
       pass
   
   @pytest.mark.integration
   def test_external_service():
       pass
   ```
6. Include docstrings explaining what the test validates

For contribution guidelines and project roadmap, see [STATUS.md](./STATUS.md).