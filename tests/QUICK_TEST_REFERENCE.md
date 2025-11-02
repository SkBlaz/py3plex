# Quick Test Reference

Quick reference for common testing patterns in py3plex.

## Running Tests

```bash
# All tests
pytest tests/

# Specific file
pytest tests/test_exceptions.py

# Specific test
pytest tests/test_exceptions.py::TestExceptionRaising::test_raise_base_exception

# With markers
pytest tests/ -m "not slow"          # Skip slow tests
pytest tests/ -m "property"          # Only property-based tests
pytest tests/ -m "integration"       # Only integration tests

# With coverage
pytest tests/ --cov=py3plex --cov-report=html

# Verbose output
pytest tests/ -v

# Stop at first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l
```

## Common Patterns

### Basic Test
```python
def test_feature():
    """Test description."""
    # Arrange
    data = create_test_data()
    
    # Act
    result = function_under_test(data)
    
    # Assert
    assert result == expected_value
```

### Using Fixtures
```python
def test_with_temp_dir(temp_dir):
    """Test using temporary directory."""
    file_path = os.path.join(temp_dir, "test.txt")
    with open(file_path, "w") as f:
        f.write("test")
    assert os.path.exists(file_path)
```

### Testing Exceptions
```python
def test_exception():
    """Test that function raises ValueError."""
    with pytest.raises(ValueError) as exc_info:
        function_that_raises()
    assert "expected message" in str(exc_info.value)
```

### Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_doubling(input, expected):
    """Test function doubles input."""
    assert double(input) == expected
```

### Testing Warnings
```python
def test_deprecation_warning():
    """Test deprecation warning is issued."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        deprecated_function()
        
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
```

### Numerical Comparisons
```python
def test_approximate_value():
    """Test value is approximately correct."""
    result = calculate()
    assert result == pytest.approx(3.14159, rel=1e-5)
```

## Test Markers

Mark tests for selective execution:

```python
@pytest.mark.slow
def test_large_computation():
    """Slow test."""
    pass

@pytest.mark.integration
def test_full_pipeline():
    """Integration test."""
    pass

@pytest.mark.property
def test_invariant():
    """Property-based test."""
    pass
```

## Fixtures

Available in `conftest.py`:

```python
def test_example(temp_dir):
    """Use temporary directory fixture."""
    pass

def test_example2(temp_file):
    """Use temporary file fixture."""
    pass
```

## Common Assertions

```python
# Equality
assert result == expected
assert result != unexpected

# Identity
assert obj is same_obj
assert obj is not different_obj

# Membership
assert item in collection
assert item not in collection

# Type checking
assert isinstance(obj, ExpectedType)

# Boolean
assert condition
assert not condition

# Approximate equality
assert value == pytest.approx(expected, rel=1e-5)

# Array equality (numpy)
np.testing.assert_array_equal(arr1, arr2)
np.testing.assert_allclose(arr1, arr2, rtol=1e-5)
```

## Debug Output

```python
# Print during test (shows on failure)
print(f"Debug: {value}")

# Use pytest's output capture
def test_example(capsys):
    print("This is captured")
    captured = capsys.readouterr()
    assert "captured" in captured.out
```

## Skip/Xfail

```python
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

@pytest.mark.skipif(sys.version_info < (3, 9), reason="Requires Python 3.9+")
def test_new_feature():
    pass

@pytest.mark.xfail(reason="Known bug, fix in progress")
def test_known_issue():
    pass
```

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── test_module.py           # Module tests
│   ├── TestFeatureA         # Feature A tests
│   │   ├── test_basic
│   │   ├── test_edge_case
│   │   └── test_error
│   └── TestFeatureB         # Feature B tests
└── property/                # Property-based tests
```

## Documentation

See:
- `TEST_STYLE_GUIDE.md` - Complete style guide
- `TEST_IMPROVEMENTS.md` - Recent improvements
- `PROPERTY_TESTS.md` - Property-based testing guide
- Official docs: https://docs.pytest.org/
