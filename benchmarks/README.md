# Performance Benchmarks for py3plex

This directory contains micro-benchmarks for evaluating py3plex performance.

## Available Benchmarks

### 1. `benchmark_multiplex_centrality.py`

Comprehensive performance benchmark for the multiplex network workflow:
- **Build multiplex network** (using random ER graphs)
- **Compute centrality measures** (degree, PageRank, closeness, etc.)
- **Serialize network** to disk

#### Usage

```bash
# Run from repository root
cd /path/to/py3plex
python benchmarks/benchmark_multiplex_centrality.py
```

Or run from the benchmarks directory:

```bash
cd benchmarks
python benchmark_multiplex_centrality.py
```

#### Output

The benchmark produces:

1. **Performance Table**: Timing and memory metrics for N ∈ {1e3, 1e4, 1e5} edges
   - Construction time
   - Centrality computation time
   - Serialization time
   - Peak RSS memory usage

2. **Flamegraph Instructions**: How to profile the code with py-spy or cProfile

3. **Optimization Suggestions**: 2-3 concrete optimizations with complexity analysis

#### Example Output

```
================================================================================
 BENCHMARK RESULTS: Multiplex Network Construction & Centrality
================================================================================

Edges      Nodes    Layers   Construct(s)   Centrality(s)   Serialize(s)   Peak Mem(MB)
--------------------------------------------------------------------------------
1000       71       4        0.0015         0.0180          0.0004         139.5       
10000      224      4        0.0096         0.3772          0.0024         144.6       
100000     708      4        0.0879         11.3348         0.0218         189.3       
--------------------------------------------------------------------------------

SUMMARY:
  Total edges tested: 111,000
  Total time: 11.8535s
  Peak memory: 189.3 MB
```

#### Key Findings

From the benchmark results:

1. **Centrality computation dominates** (99% of total time for 100K edges)
2. **Construction is fast** (<1% of total time)
3. **Memory scales reasonably** (139 MB → 189 MB for 100× edge increase)
4. **Serialization is efficient** (~0.2% of total time)

#### Profiling with Flamegraphs

For detailed performance analysis, use flamegraphs:

```bash
# Option 1: py-spy (recommended)
pip install py-spy
sudo py-spy record -o flamegraph.svg --format speedscope -- python benchmark_multiplex_centrality.py

# Option 2: cProfile + flameprof
python -m cProfile -o profile.out benchmark_multiplex_centrality.py
flameprof profile.out > flamegraph.svg

# View the flamegraph
firefox flamegraph.svg
# Or upload to https://speedscope.app
```

### 2. `bench_aggregation.py`

Benchmark suite for vectorized multiplex aggregation comparing new vectorized implementation against legacy loop-based approach.

See the file for usage details.

## Requirements

- Python 3.8+
- numpy
- scipy
- networkx
- matplotlib
- py3plex (installed in development mode)

## Adding New Benchmarks

When adding new benchmarks:

1. Follow the naming convention: `benchmark_<feature>.py` or `bench_<feature>.py`
2. Include detailed docstrings explaining what is benchmarked
3. Provide clear output with timing and memory metrics
4. Include suggestions for optimization when relevant
5. Use `pytest-benchmark` for integration with CI/CD

## CI Integration

Benchmarks can be run as part of CI using:

```bash
pytest benchmarks/ --benchmark-only
```

Or use the Makefile:

```bash
make benchmark
```
