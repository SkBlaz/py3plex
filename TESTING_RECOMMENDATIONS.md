# Recommendations for Additional Test Coverage

This document provides specific, actionable recommendations for adding tests to modules that currently lack coverage.

## Quick Reference

### Modules Needing Tests (Priority Order)

1. ⚠️ **HIGH PRIORITY** - Core functionality
   - `py3plex/core/parsers.py`
   - `py3plex/core/converters.py`
   - `py3plex/io/api.py`

2. 🔶 **MEDIUM PRIORITY** - Supporting functionality
   - `py3plex/logging_config.py`
   - `py3plex/algorithms/multicentrality.py`
   - `py3plex/multinet/aggregation.py` (Note: `test_aggregation.py` exists but may need expansion)

3. 🔷 **LOW PRIORITY** - Utilities and wrappers
   - `py3plex/visualization/misc_tools.py`
   - `py3plex/algorithms/meta_flow_report.py`
   - `py3plex/wrappers/benchmark_nodes.py`
   - `py3plex/wrappers/train_node2vec_embedding.py`

## Detailed Recommendations

### 1. Core Parsers (`py3plex/core/parsers.py`)

**Why it matters:** Parsing is a critical entry point for data into the library. Bugs here affect all downstream operations.

**Recommended test file:** `tests/test_core_parsers_extended.py`

**Key areas to test:**

#### Format Parsing
```python
def test_parse_graphml_format():
    """Test parsing GraphML files."""
    # Test valid GraphML
    # Test invalid GraphML
    # Test empty GraphML
    pass

def test_parse_edge_list():
    """Test parsing edge list formats."""
    # Test basic edge list
    # Test weighted edges
    # Test directed vs undirected
    pass
```

#### Error Handling
```python
def test_parse_invalid_file_format():
    """Test parsing with invalid format raises ParsingError."""
    pass

def test_parse_nonexistent_file():
    """Test parsing nonexistent file raises appropriate error."""
    pass
```

#### Data Validation
```python
def test_node_id_validation():
    """Test that node IDs are validated during parsing."""
    pass

def test_edge_validation():
    """Test that edges reference valid nodes."""
    pass
```

**Estimated effort:** 4-6 hours  
**Estimated test count:** 15-20 tests

---

### 2. Core Converters (`py3plex/core/converters.py`)

**Why it matters:** Converters transform data between different representations. Errors can lead to data loss or corruption.

**Recommended test file:** `tests/test_core_converters_extended.py`

**Key areas to test:**

#### Format Conversions
```python
def test_networkx_to_py3plex_conversion():
    """Test converting NetworkX graph to py3plex format."""
    pass

def test_py3plex_to_networkx_conversion():
    """Test converting py3plex to NetworkX graph."""
    pass

def test_round_trip_conversion():
    """Test that round-trip conversion preserves data."""
    pass
```

#### Layout Computation
```python
def test_force_directed_layout():
    """Test force-directed layout computation."""
    pass

def test_random_layout():
    """Test random layout generation."""
    pass

def test_custom_coordinates_layout():
    """Test layout from custom coordinates."""
    pass
```

#### Contract Validation
```python
def test_converter_preconditions():
    """Test that preconditions are enforced (icontract)."""
    pass

def test_converter_postconditions():
    """Test that postconditions are satisfied."""
    pass
```

**Estimated effort:** 5-7 hours  
**Estimated test count:** 20-25 tests

---

### 3. I/O API (`py3plex/io/api.py`)

**Why it matters:** This is the public interface for I/O operations. Users directly interact with these functions.

**Recommended test file:** `tests/test_io_api_extended.py`

**Key areas to test:**

#### File I/O Operations
```python
def test_read_network_from_file():
    """Test reading network from various file formats."""
    pass

def test_write_network_to_file():
    """Test writing network to various file formats."""
    pass

def test_supported_formats_query():
    """Test querying supported format list."""
    pass
```

#### Format Detection
```python
def test_auto_format_detection():
    """Test automatic format detection from file extension."""
    pass

def test_explicit_format_specification():
    """Test explicitly specifying format."""
    pass
```

#### Error Handling
```python
def test_unsupported_format_error():
    """Test that unsupported format raises FormatUnsupportedError."""
    pass

def test_schema_validation_on_read():
    """Test that schema is validated when reading."""
    pass
```

**Estimated effort:** 3-4 hours  
**Estimated test count:** 12-15 tests

---

### 4. Logging Configuration (`py3plex/logging_config.py`)

**Why it matters:** Proper logging is essential for debugging and monitoring library usage.

**Recommended test file:** `tests/test_logging_config_extended.py`

**Key areas to test:**

#### Logger Setup
```python
def test_get_logger_returns_logger():
    """Test that get_logger returns a Logger instance."""
    pass

def test_logger_hierarchy():
    """Test that loggers follow proper hierarchy."""
    pass
```

#### Configuration
```python
def test_log_level_configuration():
    """Test setting different log levels."""
    pass

def test_handler_configuration():
    """Test configuring different handlers."""
    pass
```

#### Logging Behavior
```python
def test_log_message_format():
    """Test that log messages are formatted correctly."""
    pass

def test_logger_propagation():
    """Test log message propagation."""
    pass
```

**Estimated effort:** 2-3 hours  
**Estimated test count:** 8-10 tests

---

### 5. Multi-centrality (`py3plex/algorithms/multicentrality.py`)

**Why it matters:** Centrality measures are key graph analysis tools.

**Recommended test file:** `tests/test_multicentrality_extended.py`

**Key areas to test:**

#### Centrality Measures
```python
def test_degree_centrality():
    """Test degree centrality calculation."""
    pass

def test_betweenness_centrality():
    """Test betweenness centrality calculation."""
    pass

def test_closeness_centrality():
    """Test closeness centrality calculation."""
    pass
```

#### Correctness
```python
def test_centrality_on_known_graphs():
    """Test centrality on graphs with known results."""
    # Use well-studied graphs (star, path, cycle)
    pass

def test_centrality_properties():
    """Test mathematical properties of centrality measures."""
    pass
```

**Estimated effort:** 4-5 hours  
**Estimated test count:** 15-18 tests

---

### 6. Visualization Utilities (`py3plex/visualization/misc_tools.py`)

**Why it matters:** Supporting visualization functions affect output quality.

**Recommended test file:** `tests/test_visualization_misc.py`

**Key areas to test:**

Would need to examine the file first to provide specific recommendations. General approach:

```python
def test_utility_function_1():
    """Test specific utility function."""
    pass

def test_edge_cases():
    """Test edge cases for utilities."""
    pass
```

**Estimated effort:** 2-3 hours (after reviewing the file)  
**Estimated test count:** 8-12 tests

---

## Testing Best Practices for py3plex

### 1. Use Fixtures for Common Test Data

```python
import pytest
import networkx as nx

@pytest.fixture
def simple_graph():
    """Provide a simple test graph."""
    G = nx.Graph()
    G.add_edges_from([(1, 2), (2, 3), (3, 1)])
    return G

@pytest.fixture
def multilayer_network():
    """Provide a test multilayer network."""
    from py3plex.core import multinet
    network = multinet.multi_layer_network()
    # Add layers and edges
    return network
```

### 2. Test Both Success and Failure Cases

```python
def test_successful_operation():
    """Test that valid input succeeds."""
    result = function(valid_input)
    assert result is not None

def test_invalid_input_raises_error():
    """Test that invalid input raises appropriate error."""
    with pytest.raises(SomeException):
        function(invalid_input)
```

### 3. Use Parametrized Tests for Multiple Scenarios

```python
@pytest.mark.parametrize("input_format,expected_output", [
    ("csv", "parsed_csv"),
    ("json", "parsed_json"),
    ("graphml", "parsed_graphml"),
])
def test_parse_various_formats(input_format, expected_output):
    """Test parsing different formats."""
    result = parse(input_format)
    assert result == expected_output
```

### 4. Test Edge Cases

```python
def test_empty_network():
    """Test handling of empty network."""
    pass

def test_single_node_network():
    """Test handling of single-node network."""
    pass

def test_disconnected_network():
    """Test handling of disconnected components."""
    pass
```

### 5. Use Property-Based Testing Where Appropriate

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=1, max_value=100))
def test_centrality_range(num_nodes):
    """Test that centrality values are in valid range [0, 1]."""
    G = nx.complete_graph(num_nodes)
    centrality = calculate_centrality(G)
    assert all(0 <= v <= 1 for v in centrality.values())
```

### 6. Mock External Dependencies

```python
from unittest.mock import Mock, patch

def test_file_io_with_mock():
    """Test file I/O with mocked file system."""
    with patch('builtins.open', mock_open(read_data='test data')):
        result = read_file('fake_path.txt')
        assert result == 'test data'
```

## Coverage Goals

### Target Coverage Levels

- **Critical modules (parsers, converters, I/O):** 90%+ coverage
- **Algorithm modules:** 80%+ coverage
- **Utility modules:** 75%+ coverage
- **Visualization modules:** 70%+ coverage

### How to Measure Coverage

```bash
# Run tests with coverage
pytest tests/ --cov=py3plex --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html

# Run specific test file with coverage
pytest tests/test_core_parsers.py --cov=py3plex.core.parsers --cov-report=term-missing
```

## Implementation Timeline

### Phase 1 (Week 1-2): High Priority
- [ ] `test_core_parsers_extended.py`
- [ ] `test_core_converters_extended.py`
- [ ] `test_io_api_extended.py`

### Phase 2 (Week 3-4): Medium Priority
- [ ] `test_logging_config_extended.py`
- [ ] `test_multicentrality_extended.py`
- [ ] Review and expand `test_aggregation.py`

### Phase 3 (Week 5+): Lower Priority
- [ ] `test_visualization_misc.py`
- [ ] Wrapper tests (if needed)
- [ ] Additional property-based tests

## Resources and Tools

### Testing Tools
- **pytest** - Primary test runner
- **pytest-cov** - Coverage reporting
- **hypothesis** - Property-based testing
- **pytest-benchmark** - Performance testing

### Coverage Analysis
- **coverage.py** - Code coverage measurement
- **codecov** - Coverage tracking (CI/CD integration)

### CI/CD Integration
Consider adding to GitHub Actions:
```yaml
- name: Run tests with coverage
  run: |
    pytest tests/ --cov=py3plex --cov-report=xml
    
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Questions or Issues?

If you have questions about implementing these tests:
1. Review existing test files in `tests/` for examples
2. Check the TEST_COVERAGE_ANALYSIS.md for context
3. Refer to the py3plex documentation
4. Create an issue on GitHub for discussion

## Conclusion

Implementing these recommended tests will:
- ✅ Increase overall test coverage by 15-20%
- ✅ Improve reliability of core I/O functionality
- ✅ Catch bugs earlier in development
- ✅ Provide usage examples for developers
- ✅ Enable safer refactoring
- ✅ Improve documentation through test cases

Start with high-priority modules first, then work your way down based on available time and resources.
