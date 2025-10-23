# Fuzzing Infrastructure for Py3plex

This directory contains fuzzing harnesses and tools for discovering bugs, crashes, and security issues in py3plex's input parsing and network construction code.

## Overview

Fuzzing is a technique for automatically discovering bugs by feeding random or semi-random inputs to a program. This fuzzing infrastructure targets high-risk areas in py3plex:

1. **Network loaders/parsers** - `load_network()` with various input formats
2. **Edge/node parsers** - Functions that parse multilayer edge lists
3. **File I/O operations** - GraphML, pickle, and other format loaders
4. **Graph transformations** - Aggregation, layer slicing, and visualization

## Tools Used

### Primary: Atheris (Coverage-Guided Python Fuzzer)

[Atheris](https://github.com/google/atheris) is a coverage-guided Python fuzzing engine that uses libFuzzer under the hood. It's ideal for discovering:
- Crashes and unhandled exceptions
- Memory errors (when combined with ASAN)
- Logic bugs and edge cases
- Performance issues

### Complementary: Hypothesis (Property-Based Testing)

Py3plex already uses [Hypothesis](https://hypothesis.readthedocs.io/) for property-based testing (see `tests/test_properties.py` and `tests/test_multiplex_properties.py`). Hypothesis is excellent for:
- Testing structural invariants
- Automatic test case shrinking
- Stateful testing

## Installation

### Install Atheris

```bash
pip install atheris
```

Note: Atheris requires a C++ compiler and may need additional setup on some platforms. See [Atheris documentation](https://github.com/google/atheris#installation) for platform-specific instructions.

### Verify Installation

```bash
python -c "import atheris; print('Atheris version:', atheris.__version__)"
```

## Fuzzing Harnesses

### 1. `fuzz_load_network.py` - Network Loading Fuzzer

Fuzzes the main network loading path by feeding various input formats to `load_network()`.

**Target:** `py3plex.core.multinet.multi_layer_network.load_network()`

**Input Types Tested:**
- `multiedgelist` - Multilayer edge list format
- `edgelist` - Simple edge list format
- `gpickle` - Python pickle format
- `gml` - Graph Modeling Language

**Usage:**
```bash
python fuzzing/fuzz_load_network.py fuzzing/seeds/
```

**What It Tests:**
- File parsing with malformed data
- Edge case handling in different formats
- Memory safety during parsing
- Exception handling

### 2. `fuzz_parse_line.py` - Line/Edge Parsing Fuzzer

Fuzzes individual line parsing in multilayer edge lists.

**Target:** Line-by-line parsing in `multiedgelist` format

**Usage:**
```bash
python fuzzing/fuzz_parse_line.py fuzzing/seeds/
```

**What It Tests:**
- Delimiter handling
- Weight parsing edge cases
- Unicode and special character handling
- Line format variations

## Seed Corpus

The `seeds/` directory contains initial test cases to guide the fuzzer:

- `small_multiedgelist.txt` - Valid multilayer edges
- `simple_edgelist.txt` - Basic edge list
- `minimal_multiplex.txt` - Minimal multiplex network
- `malformed_variants.txt` - Known edge cases and malformed inputs

The fuzzer will use these as starting points and mutate them to explore new code paths.

## Running Fuzzing Campaigns

### Quick Test (1 minute)

```bash
# Run for 60 seconds
python fuzzing/fuzz_load_network.py fuzzing/seeds/ -max_total_time=60
```

### Short Campaign (10 minutes)

```bash
# Run for 10 minutes with progress output
python fuzzing/fuzz_load_network.py fuzzing/seeds/ -max_total_time=600 -print_final_stats=1
```

### Long Campaign (1 hour+)

```bash
# Run overnight or during CI
python fuzzing/fuzz_load_network.py fuzzing/seeds/ -max_total_time=3600
```

### Parallel Fuzzing

For faster coverage, run multiple fuzzer instances:

```bash
# Terminal 1
python fuzzing/fuzz_load_network.py fuzzing/seeds/ -jobs=4

# Terminal 2
python fuzzing/fuzz_parse_line.py fuzzing/seeds/ -jobs=4
```

## Interpreting Results

### Crashes and Findings

When Atheris finds a crash, it will:
1. Print the crash details
2. Save a test case to `crash-*` or `leak-*` file
3. Show the stack trace

**Example Output:**
```
==12345==ERROR: AddressSanitizer: heap-buffer-overflow
...
artifact_prefix='./'; Test unit written to ./crash-da39a3ee5e6b4b0d
```

### Reproducing Crashes

To reproduce a crash:

```bash
# Run the specific test case
python fuzzing/fuzz_load_network.py fuzzing/seeds/ ./crash-da39a3ee5e6b4b0d
```

Or manually:

```python
import atheris
with open('crash-da39a3ee5e6b4b0d', 'rb') as f:
    data = f.read()
    # Test the specific input
    fuzz_one_input(data)
```

### Expected vs. Real Bugs

**Expected (Not Bugs):**
- `ValueError` for invalid input formats
- `TypeError` for wrong data types
- `KeyError` for missing required fields
- `FileNotFoundError` for missing files

**Real Bugs (Should Be Fixed):**
- `AssertionError` - Logic errors
- `MemoryError` - Memory leaks or excessive allocation
- Segmentation faults - Memory corruption
- Infinite loops - Performance issues
- Unhandled exceptions - Missing error handling

## Adding New Fuzzing Targets

To add fuzzing for a new function:

1. Create a new fuzzer file in `fuzzing/`:

```python
#!/usr/bin/env python3
import sys
import atheris
from py3plex.your_module import your_function

def fuzz_one_input(data: bytes):
    # Your fuzzing logic here
    try:
        result = your_function(data)
    except (ValueError, TypeError):
        return  # Expected errors
    except Exception:
        raise  # Unexpected - let fuzzer report it

def main():
    atheris.Setup(sys.argv, fuzz_one_input)
    atheris.Fuzz()

if __name__ == "__main__":
    main()
```

2. Add seed files to `fuzzing/seeds/`
3. Run the fuzzer and report findings

## Advanced: Fuzzing C/C++ Components with ASAN

If py3plex has C/C++ components (e.g., Infomap bindings), fuzz them with AddressSanitizer:

### Build with ASAN

```bash
# Set compiler flags
export CFLAGS="-fsanitize=address -fno-omit-frame-pointer -g"
export CXXFLAGS="-fsanitize=address -fno-omit-frame-pointer -g"

# Rebuild
pip install -e . --force-reinstall --no-binary :all:
```

### Run Fuzzer with ASAN

```bash
# ASAN will detect memory errors
python fuzzing/fuzz_load_network.py fuzzing/seeds/
```

ASAN will report:
- Heap buffer overflows
- Stack buffer overflows
- Use-after-free errors
- Memory leaks
- Double-free errors

## Continuous Integration

### GitHub Actions (Optional)

Add fuzzing to CI (example workflow):

```yaml
name: Fuzzing

on: [push, pull_request]

jobs:
  fuzz:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -e .
          pip install atheris
      - name: Run fuzzing (short campaign)
        run: |
          python fuzzing/fuzz_load_network.py fuzzing/seeds/ -max_total_time=300
          python fuzzing/fuzz_parse_line.py fuzzing/seeds/ -max_total_time=300
      - name: Upload crashes
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: fuzzing-crashes
          path: crash-*
```

## Best Practices

1. **Start with short campaigns** - Run for 5-10 minutes initially
2. **Check coverage** - Use `-print_final_stats=1` to see code coverage
3. **Triage findings** - Not all crashes are bugs (some are expected errors)
4. **Add regression tests** - For every real bug found, add a test
5. **Update seeds** - Add interesting inputs to seed corpus
6. **Run regularly** - Integrate into CI/CD pipeline

## Troubleshooting

### Atheris Installation Fails

**Problem:** C++ compiler not found

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install build-essential python3-dev

# macOS
xcode-select --install

# Windows
# Install Visual Studio Build Tools
```

### Fuzzer Hangs

**Problem:** Fuzzer seems stuck

**Solution:**
- Add timeouts: `-timeout=10` (10 seconds per input)
- Reduce max length: `-max_len=10000`
- Check for infinite loops in code

### No New Coverage

**Problem:** Fuzzer not finding new paths

**Solution:**
- Improve seed corpus
- Try different input types
- Add more fuzzing targets
- Check if code is reachable

## Resources

- [Atheris Documentation](https://github.com/google/atheris)
- [libFuzzer Options](https://llvm.org/docs/LibFuzzer.html#options)
- [Fuzzing Best Practices](https://google.github.io/clusterfuzz/getting-started/local-instance/)
- [ASAN Documentation](https://github.com/google/sanitizers/wiki/AddressSanitizer)

## Contributing

Found a bug through fuzzing? Please:

1. Minimize the test case
2. Create a minimal reproduction
3. Add a regression test
4. Open a GitHub issue with details
5. Submit a fix if possible

## License

Same as py3plex (MIT License)
