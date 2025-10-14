# Py3plex Benchmarks

This directory contains performance benchmarks for py3plex operations.

## Running Benchmarks

### Run All Benchmarks

```bash
pytest benchmarks/ --benchmark-only -v
```

### Run Specific Benchmark Suite

```bash
pytest benchmarks/bench_aggregation.py --benchmark-only -v
```

### Run with Performance Comparison

```bash
# Compare against legacy implementation
pytest benchmarks/bench_aggregation.py::TestAggregationBenchmarks::test_speedup_vs_legacy_medium -v -s
```

### Generate Benchmark Report

```bash
pytest benchmarks/ --benchmark-only --benchmark-json=output.json
```

## Benchmark Suites

### `bench_aggregation.py`

Tests for vectorized multiplex aggregation (Spec A).

**Key benchmarks**:
- `test_speedup_target_1m_edges`: Primary target (1M edges, 4 layers, ≥3× speedup)
- `test_speedup_vs_legacy_medium`: 100K edges comparison
- `test_bench_vectorized_*`: Various dataset sizes

**Performance targets**:
- ✅ ≥3× speedup vs legacy loop-based approach
- ✅ Achieved: 8.04× on 1M edges

## Adding New Benchmarks

1. Create `bench_<module>.py` in this directory
2. Use pytest-benchmark fixtures for timing
3. Include both correctness and performance tests
4. Document performance targets in docstrings
5. Compare against baseline/legacy when applicable

## CI Integration

Benchmarks are run in CI to detect performance regressions:
- Comparison baseline: tag `v0.95a`
- Fail threshold: >10% slowdown
- Results saved as JSON artifacts
