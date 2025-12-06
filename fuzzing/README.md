# Py3plex Fuzzing Tests

This directory contains fuzzing harnesses for py3plex using [Atheris](https://github.com/google/atheris), a coverage-guided Python fuzzing engine based on libFuzzer.

## Overview

Fuzzing is an automated testing technique that feeds random or malformed inputs to software to discover bugs, crashes, and security vulnerabilities. The py3plex fuzzing suite includes three main harnesses:

1. **Network Loading Fuzzer** (`fuzz_load_network.py`) - Tests network file loading and parsing
2. **Line Parsing Fuzzer** (`fuzz_parse_line.py`) - Tests individual edge/line parsing
3. **DSL Query Fuzzer** (`fuzz_dsl.py`) - Tests Domain-Specific Language query parsing and execution

## Installation

Install the required fuzzing dependencies:

```bash
# Install Atheris fuzzing engine
pip install atheris

# Install py3plex in development mode
pip install -e .
```

## Running Fuzzers

### Quick Start

Run all fuzzers for a short duration (60 seconds each):

```bash
cd fuzzing
./run_fuzzing.sh 60
```

### Full Fuzzing Campaign

Run a comprehensive fuzzing campaign (1 hour per fuzzer):

```bash
cd fuzzing
./run_fuzzing.sh 3600
```

### Individual Fuzzers

Run a specific fuzzer manually:

```bash
# Network loading fuzzer
python3 fuzzing/fuzz_load_network.py fuzzing/seeds/ -max_total_time=300

# Line parsing fuzzer
python3 fuzzing/fuzz_parse_line.py fuzzing/seeds/ -max_total_time=300

# DSL query fuzzer
python3 fuzzing/fuzz_dsl.py fuzzing/seeds/ -max_total_time=300
```

## DSL Fuzzer Details

The DSL fuzzer (`fuzz_dsl.py`) specifically targets the Domain-Specific Language module, which provides SQL-like queries for multilayer networks.

### What it Tests

- **String DSL Syntax**: SQL-like query parsing
  - `SELECT nodes WHERE layer="social" AND degree > 5`
  - `SELECT edges WHERE layer="work" COMPUTE betweenness_centrality`
  
- **Builder API**: Python chainable API
  - `Q.nodes().from_layers(L["social"]).where(degree__gt=5)`
  
- **Query Components**:
  - Tokenization and lexical analysis
  - Syntax validation
  - Condition evaluation (AND, OR, NOT)
  - Comparison operators (>, <, =, >=, <=, !=)
  - Measure computation (centrality, clustering, etc.)
  - Layer expressions (union, difference, intersection)
  - Export functionality (to_pandas, to_dict, etc.)

### Seed Corpus

The fuzzer uses a seed corpus in `seeds/` to bootstrap fuzzing:

- `dsl_basic_select.txt` - Simple SELECT queries
- `dsl_select_layer.txt` - Layer filtering
- `dsl_degree_filter.txt` - Degree-based filtering
- `dsl_and_operator.txt` - AND logical operators
- `dsl_or_operator.txt` - OR logical operators
- `dsl_not_operator.txt` - NOT logical operators
- `dsl_compute_degree.txt` - Degree computation
- `dsl_compute_betweenness.txt` - Betweenness centrality
- `dsl_select_edges.txt` - Edge selection
- `dsl_malformed_variants.txt` - Edge cases and malformed queries

### Expected Behavior

The DSL fuzzer is designed to handle errors gracefully. It catches and ignores expected exceptions:

- `DslSyntaxError` - Malformed query syntax
- `DslExecutionError` - Invalid operations
- `UnknownMeasureError` - Unknown measures
- `UnknownAttributeError` - Unknown attributes
- `UnknownLayerError` - Unknown layers
- `ParameterMissingError` - Missing parameters
- `TypeMismatchError` - Type mismatches

Real crashes (segfaults, memory corruption, assertion failures) will be reported and saved to `crashes/`.

## Interpreting Results

### Success

If fuzzing completes without finding crashes:

```
✅ No crashes found
Fuzzing completed successfully
```

### Crashes Found

If crashes are discovered:

```
⚠️  CRASHES FOUND!
Crash files saved to fuzzing/crashes/
```

Reproduce a crash:

```bash
python3 fuzzing/fuzz_dsl.py fuzzing/seeds/ fuzzing/crashes/crash-XXXXX
```

## Continuous Integration

The fuzzing harnesses can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run fuzzing tests
  run: |
    pip install atheris
    pip install -e .
    cd fuzzing
    ./run_fuzzing.sh 300  # 5-minute quick check
```

## Docker Support

A Dockerfile is provided for containerized fuzzing:

```bash
# Build the fuzzing container
docker build -t py3plex-fuzzer .

# Run fuzzing in container
docker run py3plex-fuzzer
```

## Extending Fuzzers

To add new fuzzing harnesses:

1. Create a new `fuzz_*.py` file following the pattern of existing fuzzers
2. Add seed files to `seeds/` directory
3. Update `run_fuzzing.sh` to include the new fuzzer
4. Document the new fuzzer in this README

## References

- [Atheris Documentation](https://github.com/google/atheris)
- [libFuzzer Documentation](https://llvm.org/docs/LibFuzzer.html)
- [Fuzzing Best Practices](https://google.github.io/clusterfuzz/reference/coverage-guided-vs-blackbox/)

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:

```bash
# Install py3plex in development mode
pip install -e .
```

### Atheris Not Found

```bash
# Install Atheris
pip install atheris
```

### Memory Issues

If fuzzing uses too much memory, reduce the max input size or duration:

```bash
./run_fuzzing.sh 60  # Shorter duration
```

## License

Same as py3plex (MIT License)
