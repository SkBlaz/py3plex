# Performance Benchmark Tests

This document describes the performance benchmark tests for py3plex core multilayer data structures.

## Overview

Performance benchmarks are designed to:
1. **Pin down runtime** of core operations to detect performance regressions
2. **Measure scalability** with different network sizes and layer counts
3. **Provide baseline metrics** for performance optimization efforts
4. **Track improvements** in data structure efficiency over time

## Test Categories

### 1. Network Creation Benchmarks (`TestNetworkCreationBenchmarks`)

Tests the overhead of creating and initializing multilayer network objects.

**Key Tests:**
- `test_bench_network_init`: Basic network initialization
- `test_bench_network_with_type`: Network initialization with specific parameters

**Purpose:** Measure instantiation overhead and ensure it remains minimal.

### 2. Node/Edge Operations Benchmarks (`TestNodeEdgeOperationsBenchmarks`)

Tests fundamental operations on network nodes and edges.

**Key Tests:**
- `test_bench_add_single_edge`: Adding edges to the network
- `test_bench_get_nodes_iteration_small/medium`: Iterating through nodes
- `test_bench_get_edges_iteration_small/medium`: Iterating through edges

**Purpose:** Ensure basic graph operations remain efficient across different network sizes.

### 3. Layer Operations Benchmarks (`TestLayerOperationsBenchmarks`)

Tests operations specific to multilayer networks.

**Key Tests:**
- `test_bench_get_layers_small/medium`: Retrieving layer information
- `test_bench_split_to_layers_small`: Splitting network into individual layers

**Purpose:** Measure performance of multilayer-specific functionality.

### 4. Network Query Benchmarks (`TestNetworkQueryBenchmarks`)

Tests network analysis and statistical queries.

**Key Tests:**
- `test_bench_summary`: Computing network statistics
- `test_bench_get_unique_entity_counts`: Counting unique nodes and layers
- `test_bench_get_neighbors`: Finding neighbors of a node

**Purpose:** Ensure analytical operations remain performant.

### 5. Network Transformation Benchmarks (`TestNetworkTransformationBenchmarks`)

Tests conversion operations between different representations.

**Key Tests:**
- `test_bench_to_sparse_matrix`: Converting to sparse matrix format
- `test_bench_to_json`: Converting to JSON representation

**Purpose:** Track performance of format conversions commonly used in analysis pipelines.

### 6. Scalability Benchmarks (`TestScalabilityBenchmarks`)

Tests how performance scales with network size and complexity.

**Key Tests:**
- `test_node_iteration_scaling`: Tests linear scaling with node count
- `test_layer_count_scaling`: Tests scaling with number of layers

**Purpose:** Verify that operations scale reasonably (ideally linearly) with network size.

### 7. Multiplex Network Benchmarks (`TestMultiplexNetworkBenchmarks`)

Tests operations specific to multiplex networks with coupling edges.

**Key Tests:**
- `test_bench_get_edges_multiplex_no_coupling`: Edge iteration excluding coupling edges
- `test_bench_get_edges_multiplex_with_coupling`: Edge iteration including coupling edges

**Purpose:** Measure performance of multiplex-specific edge filtering.

## Network Sizes

Tests use three standard network sizes:

- **Small**: 100-150 nodes, 2 layers
- **Medium**: 1,000 nodes, 4 layers
- **Large**: 2,000+ nodes, 8-16 layers (in scaling tests)

## Running Benchmarks

### Run All Benchmarks
```bash
pytest tests/test_performance_core.py --benchmark-only -v
```

### Run Specific Category
```bash
pytest tests/test_performance_core.py::TestNetworkCreationBenchmarks --benchmark-only -v
```

### Generate JSON Report
```bash
pytest tests/test_performance_core.py --benchmark-only --benchmark-json=benchmark-results.json
```

### Compare with Baseline
```bash
# Run and save baseline
pytest tests/test_performance_core.py --benchmark-only --benchmark-save=baseline

# Run and compare
pytest tests/test_performance_core.py --benchmark-only --benchmark-compare=baseline
```

## CI Integration

Benchmarks run automatically on:
- Push to main/master/develop branches
- Pull requests to main/master/develop branches
- Manual workflow dispatch

Results are:
- Saved as JSON artifacts (retained for 90 days)
- Displayed in GitHub Actions summary
- Used to detect performance regressions

## Performance Targets

Expected performance characteristics:

1. **Network Creation**: < 1 microsecond for basic initialization
2. **Node/Edge Iteration**: Linear time O(n) with network size
3. **Layer Operations**: Linear or near-linear with layer count
4. **Queries**: Sub-second for networks up to 1,000 nodes
5. **Transformations**: < 200ms for sparse matrix conversion of 1,000 nodes

## Adding New Benchmarks

To add a new benchmark:

1. Add test method to appropriate class in `test_performance_core.py`
2. Use `benchmark` fixture: `def test_new_operation(self, benchmark): result = benchmark(operation)`
3. Add assertions to validate correctness
4. Document the purpose and expected performance
5. Run locally to establish baseline

Example:
```python
def test_bench_my_operation(self, benchmark):
    """Benchmark my new operation."""
    net = self._create_test_network()
    result = benchmark(net.my_operation, param1, param2)
    assert result is not None
```

## Interpreting Results

pytest-benchmark provides several metrics:

- **Min/Max**: Fastest and slowest execution times
- **Mean**: Average execution time (most reliable metric)
- **StdDev**: Standard deviation (lower is more consistent)
- **Median**: Middle value (robust to outliers)
- **IQR**: Interquartile range (measure of spread)
- **Outliers**: Number of executions significantly different from mean
- **OPS**: Operations per second (inverse of mean)

Focus on **Mean** and **StdDev** for overall performance assessment.

## Performance Regression Detection

A performance regression is detected when:
- Mean time increases by > 10% compared to baseline
- Scaling tests show non-linear behavior
- Operations that should be O(n) show O(n²) or worse characteristics

## Related Documentation

- Main benchmarks directory: `/benchmarks/`
- Aggregation benchmarks: `/benchmarks/bench_aggregation.py`
- Benchmark workflow: `/.github/workflows/benchmarks.yml`
- Benchmark badge in README.md
