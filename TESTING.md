# Testing Instructions for Py3plex

This document explains how to run tests for the py3plex project.

## Test Files

- `tests/test_infomap_fix.py` - Integration test for the infomap community detection fix
- `tests/test_core_functionality.py` - Core functionality tests (requires full dependencies)

## Quick Test Run

### Option 1: Simple Test Runner (Recommended)

```bash
python run_tests.py
```

This will run all available tests and provide a clear summary.

### Option 2: Run Individual Tests

Run the infomap fix test (minimal dependencies):
```bash
python tests/test_infomap_fix.py
```

Run core functionality tests (requires full installation):
```bash
python -c "from tests.test_core_functionality import test_imports; test_imports()"
```

### Option 3: Using unittest

If you prefer unittest:
```bash
python -m unittest discover tests/ -v
```

## Dependencies

### Minimal Testing (infomap fix only)
No additional dependencies required beyond Python 3.6+

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

To set up automated testing, add a GitHub Actions workflow or configure your preferred CI system to:

1. Install Python 3.6+
2. Install dependencies: `pip install -e .`
3. Run tests: `python run_tests.py`

## Contributing

When adding new tests:
1. Create test files with the `test_*.py` naming pattern in the `tests/` directory
2. Use descriptive function names starting with `test_`
3. Ensure tests can run independently
4. Document any special requirements