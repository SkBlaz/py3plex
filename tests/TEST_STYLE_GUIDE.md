# Test Style Guide for py3plex

This document outlines the coding standards and best practices for writing tests in the py3plex project.

## General Principles

1. **Use pytest idioms**: Prefer pytest-style assertions and fixtures over unittest patterns
2. **Clear naming**: Test function names should clearly describe what is being tested
3. **Single responsibility**: Each test should test one specific behavior
4. **Good docstrings**: All test functions should have clear docstrings
5. **Arrange-Act-Assert**: Structure tests with clear setup, action, and verification phases

## Test Organization

### File Structure
```
tests/
├── conftest.py              # Shared fixtures
├── test_<module>.py         # Unit tests for specific modules
├── property/                # Property-based tests
│   ├── __init__.py
│   ├── strategies.py        # Hypothesis strategies
│   └── test_*.py            # Property tests
```

### Test Class Organization

Group related tests in classes:

```python
class TestFeatureName:
    """Test specific feature or component."""
    
    def test_basic_case(self):
        """Test the basic/happy path scenario."""
        pass
    
    def test_edge_case(self):
        """Test edge case or boundary condition."""
        pass
    
    def test_error_handling(self):
        """Test error handling and exceptions."""
        pass
```

## Code Style

### Assertions

**Good**: Use pytest's native assert with clear messages
```python
assert result == expected, f"Expected {expected}, got {result}"
assert len(nodes) > 0, "Network should have at least one node"
```

**Avoid**: Using unittest-style assertions
```python
# Don't do this
self.assertEqual(result, expected)
self.assertTrue(condition)
```

### Exception Testing

**Good**: Use pytest.raises with clear checks
```python
with pytest.raises(ValueError) as exc_info:
    function_that_raises()

assert "expected error message" in str(exc_info.value)
```

**Avoid**: Using try/except or unittest-style assertRaises
```python
# Don't do this
with self.assertRaises(ValueError):
    function_that_raises()
```

### Fixtures

**Good**: Use pytest fixtures for setup/teardown
```python
@pytest.fixture
def network():
    """Create a simple test network."""
    net = create_network()
    yield net
    # Cleanup happens automatically

def test_network_operation(network):
    """Test operation on network."""
    result = network.some_operation()
    assert result is not None
```

**Avoid**: Using setUp/tearDown methods
```python
# Don't do this
class TestNetwork(unittest.TestCase):
    def setUp(self):
        self.network = create_network()
    
    def tearDown(self):
        self.network.cleanup()
```

### Parametrized Tests

**Good**: Use @pytest.mark.parametrize for similar tests
```python
@pytest.mark.parametrize("input_val,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_doubling(input_val, expected):
    """Test that function doubles the input."""
    result = double(input_val)
    assert result == expected
```

**Avoid**: Repeating similar test functions
```python
# Don't do this
def test_double_one(self):
    assert double(1) == 2

def test_double_two(self):
    assert double(2) == 4

def test_double_three(self):
    assert double(3) == 6
```

## Docstrings

Every test should have a clear docstring:

```python
def test_network_creation_from_edgelist(temp_dir):
    """
    Test creating a multilayer network from an edgelist file.
    
    This test verifies that:
    - The network is successfully created
    - Nodes and edges are properly loaded
    - Layer information is preserved
    """
    # Test implementation
```

## Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.slow
def test_large_network_computation():
    """Test computation on large network (slow)."""
    pass

@pytest.mark.integration
def test_full_pipeline():
    """Test complete processing pipeline (integration)."""
    pass

@pytest.mark.property
def test_invariant():
    """Test mathematical invariant (property-based)."""
    pass
```

## Common Patterns

### Testing Files

```python
def test_file_operations(temp_dir):
    """Test file read/write operations."""
    file_path = os.path.join(temp_dir, "test.csv")
    
    # Arrange
    data = create_test_data()
    
    # Act
    write_to_file(file_path, data)
    result = read_from_file(file_path)
    
    # Assert
    assert result == data
```

### Testing Exceptions

```python
def test_invalid_input_raises_error():
    """Test that invalid input raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        process_invalid_input()
    
    assert "invalid" in str(exc_info.value).lower()
```

### Testing Numerical Results

```python
def test_calculation_accuracy():
    """Test numerical calculation with tolerance."""
    result = calculate_value()
    expected = 3.14159
    
    assert result == pytest.approx(expected, rel=1e-5)
```

## Anti-Patterns to Avoid

1. **Don't test implementation details**: Test behavior, not internal structure
2. **Don't use sleep() for timing**: Use proper mocking or async patterns
3. **Don't leave print() statements**: Use logging or pytest's capture fixtures
4. **Don't write tests that depend on execution order**: Each test should be independent
5. **Don't catch exceptions to avoid failure**: Let tests fail to reveal bugs

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_exceptions.py

# Run tests with specific marker
pytest tests/ -m "not slow"

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=py3plex --cov-report=html
```

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest best practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Hypothesis documentation](https://hypothesis.readthedocs.io/)
