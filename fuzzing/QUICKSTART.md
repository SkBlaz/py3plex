# Fuzzing Infrastructure - Quick Reference

## What Is This?

Fuzzing infrastructure for automatically discovering bugs, crashes, and security issues in py3plex's input parsing and network construction code.

## Quick Start

### 1. Install Fuzzing Tools

```bash
pip install atheris hypothesis
```

### 2. Run Quick Test (1 minute)

```bash
make fuzz-quick
```

### 3. Check Results

- ✅ **No crashes:** All good!
- ⚠️ **Crashes found:** Check `fuzzing/crashes/` directory

## What Gets Tested?

- Network loading from files (multiedgelist, edgelist, gpickle, gml)
- Edge and line parsing
- Delimiter handling
- Unicode and special characters
- Malformed input handling
- Memory safety (with Docker ASAN)

## Files and Directories

```
fuzzing/
├── fuzz_load_network.py        # Main fuzzer for network loading
├── fuzz_parse_line.py           # Fuzzer for line parsing
├── run_fuzzing.sh               # Automated fuzzing script
├── Dockerfile                   # ASAN-enabled fuzzing container
├── README.md                    # Detailed documentation
└── seeds/                       # Initial test cases
    ├── small_multiedgelist.txt
    ├── simple_edgelist.txt
    ├── minimal_multiplex.txt
    └── malformed_variants.txt

tests/
└── test_fuzzing_properties.py   # Hypothesis property-based tests
```

## Available Commands

| Command | Duration | Description |
|---------|----------|-------------|
| `make fuzz-quick` | 1 min | Quick smoke test |
| `make fuzz` | 5 min | Standard campaign |
| `make fuzz-long` | 1 hour | Extended campaign |
| `make fuzz-docker` | 5 min | ASAN fuzzing in Docker |
| `pytest tests/test_fuzzing_properties.py` | 2 min | Property-based tests |

## Manual Execution

```bash
# Run specific fuzzer
python fuzzing/fuzz_load_network.py fuzzing/seeds/ -max_total_time=300

# Run with different options
python fuzzing/fuzz_load_network.py fuzzing/seeds/ \
    -max_total_time=600 \
    -max_len=10000 \
    -timeout=10 \
    -print_final_stats=1
```

## Understanding Results

### Expected Errors (Not Bugs)
- `ValueError` - Invalid input format
- `TypeError` - Wrong data type
- `KeyError` - Missing field
- `FileNotFoundError` - File doesn't exist

### Real Bugs (Need Fixing)
- `AssertionError` - Logic error
- `MemoryError` - Memory leak
- `Segmentation fault` - Memory corruption
- Infinite loops
- Unhandled exceptions

## If Crashes Are Found

1. **Crashes saved to:** `fuzzing/crashes/crash-XXXXX`
2. **Reproduce:** `python fuzzing/fuzz_load_network.py fuzzing/seeds/ ./fuzzing/crashes/crash-XXXXX`
3. **Debug:** Add logging, use debugger
4. **Fix:** Patch the bug
5. **Test:** Add regression test
6. **Verify:** Re-run fuzzer

## Property-Based Tests

Run with pytest:
```bash
pytest tests/test_fuzzing_properties.py -v
```

Tests 8 categories:
- Multiedgelist parsing
- Edgelist parsing
- Delimiter handling
- Unicode node names
- Load/save roundtrip
- Self-loops
- Empty lines
- Arbitrary text

## Docker ASAN Fuzzing

For C/C++ components with memory error detection:

```bash
# Build container
docker build -t py3plex-fuzzing -f fuzzing/Dockerfile .

# Run fuzzing
docker run py3plex-fuzzing

# Run with volume mount
docker run -v $(pwd)/fuzzing/crashes:/src/py3plex/fuzzing/crashes \
           py3plex-fuzzing ./fuzzing/run_fuzzing.sh 600
```

ASAN detects:
- Heap/stack buffer overflows
- Use-after-free
- Memory leaks
- Double-free

## CI Integration (Optional)

See `.github/workflows/fuzzing.yml.disabled`

To enable:
1. Rename to `fuzzing.yml`
2. Uncomment the `on:` triggers
3. Adjust durations as needed
4. Commit and push

## Documentation

- **Detailed guide:** `fuzzing/README.md` (8.7KB)
- **LLM context:** `LLM.md` (section on Fuzzing Infrastructure)
- **Test file:** `tests/test_fuzzing_properties.py`

## Troubleshooting

### Atheris not installing
```bash
# Install build tools
sudo apt-get install build-essential python3-dev  # Ubuntu/Debian
xcode-select --install                             # macOS
```

### Fuzzer hangs
```bash
# Add timeout per input
python fuzzing/fuzz_load_network.py fuzzing/seeds/ \
    -timeout=10 -max_len=5000
```

### No coverage improvements
- Add more seed files
- Try different input formats
- Increase fuzzing duration

## Best Practices

1. ✅ Start with short campaigns (1-5 minutes)
2. ✅ Review crashes promptly
3. ✅ Add regression tests for bugs found
4. ✅ Run before major releases
5. ✅ Use Docker for ASAN fuzzing
6. ✅ Keep seed corpus updated
7. ❌ Don't ignore crashes without investigation
8. ❌ Don't run very long campaigns without monitoring

## Resources

- [Atheris Documentation](https://github.com/google/atheris)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [libFuzzer Options](https://llvm.org/docs/LibFuzzer.html)
- [ASAN Documentation](https://github.com/google/sanitizers/wiki/AddressSanitizer)

## Support

For questions or issues:
1. Check `fuzzing/README.md` for detailed guide
2. Review LLM.md for architecture context
3. Open GitHub issue with crash details

---

**Status:** ✅ Fuzzing infrastructure is production-ready  
**Last Updated:** 2025-10-22  
**Coverage:** Network loading, parsing, I/O, edge cases
