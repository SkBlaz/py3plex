# Documentation Examples Pipeline

This directory contains the infrastructure for maintaining a 1:1 mapping between:
1. **Runnable examples** in `examples/docs/`
2. **Automated CI tests** that execute those examples
3. **Rendered outputs** embedded in `docfiles/**/*.rst`

## Overview

The Examples-as-Tests-as-Docs pipeline ensures that:
- Every documentation example is executable
- All outputs in documentation are automatically captured from CI runs
- Documentation stays in sync with code behavior
- CI fails if outputs diverge from what's shown in docs

## Directory Structure

```
examples/
├── docs/                    # Executable documentation examples
│   ├── 01_basic_query.py   # Example 1
│   └── ...                 # More examples
└── docs_outputs/           # Auto-generated outputs (tracked in git)
    ├── manifest.json       # Metadata about all examples
    ├── 01_basic_query.txt  # Captured output for example 1
    └── ...                 # More outputs

scripts/
├── generate_docs_outputs.py  # Runs examples and captures outputs
└── validate_docs_outputs.py  # Validates RST files reference correct outputs

docfiles/
└── **/*.rst               # Documentation files with embedded outputs
```

## Writing Documentation Examples

### Example Structure

Each example in `examples/docs/` should:
1. Be a standalone, executable Python script
2. Use descriptive numbered names (e.g., `01_basic_query.py`, `02_community_detection.py`)
3. Include clear print statements to generate useful output
4. Avoid interactive prompts or external dependencies
5. Complete in under 30 seconds

### Example Template

```python
#!/usr/bin/env python
"""
Example: Brief description
===========================

Longer description of what this example demonstrates.
"""

from py3plex.core import multinet
from py3plex.dsl import Q

def main():
    # Create network
    print("Creating a multilayer network...")
    net = multinet.multi_layer_network(directed=False)
    
    # ... do something interesting ...
    
    # Print clear output
    print("\nResults:")
    print("=" * 40)
    print(f"Nodes: {len(net.get_nodes())}")
    print(f"Edges: {len(net.get_edges())}")

if __name__ == "__main__":
    main()
```

### Embedding Outputs in RST

In your RST documentation file, reference both the source code and output:

```rst
Example Title
=============

Description of what this example does.

**Source code:**

.. literalinclude:: ../examples/docs/01_basic_query.py
   :language: python
   :linenos:

**Output:**

.. literalinclude:: ../examples/docs_outputs/01_basic_query.txt
   :language: none
```

## Running the Pipeline

### Generate Outputs Locally

```bash
python scripts/generate_docs_outputs.py
```

This will:
1. Find all `.py` files in `examples/docs/`
2. Execute each one in a clean environment
3. Capture stdout and stderr
4. Save outputs to `examples/docs_outputs/`
5. Update `manifest.json` with metadata

### Validate Outputs

```bash
python scripts/validate_docs_outputs.py
```

This will:
1. Load `manifest.json`
2. Scan all RST files in `docfiles/`
3. Verify that referenced outputs exist
4. Check that all outputs are referenced in docs
5. Fail if any inconsistencies are found

### Run Tests

```bash
pytest tests/test_docs_examples.py
```

This runs automated tests that verify:
- All examples can execute successfully
- Output files are created correctly
- Validation passes
- Manifest structure is correct

## CI Integration

The GitHub Actions workflow `.github/workflows/docs-examples.yml` runs on:
- Every push to main/develop
- Every pull request
- Manual workflow dispatch

The CI pipeline:
1. **Generates outputs**: Runs all examples and captures outputs
2. **Validates**: Ensures RST files reference correct outputs
3. **Uploads artifacts**: Saves outputs for debugging
4. **Checks divergence**: On PRs, fails if outputs have changed without being committed

### CI Failure Scenarios

The CI will fail if:
1. Any example script fails to execute
2. Any RST file references a non-existent output
3. Any output file exists but is not referenced in RST
4. On PRs, if outputs have changed but weren't committed

### Fixing CI Failures

If the CI fails because outputs have diverged:

```bash
# Regenerate outputs locally
python scripts/generate_docs_outputs.py

# Verify the changes
git diff examples/docs_outputs/

# If correct, commit the updated outputs
git add examples/docs_outputs/
git commit -m "Update documentation example outputs"
```

## Best Practices

### DO:
- ✅ Keep examples focused on one concept
- ✅ Use clear, descriptive output messages
- ✅ Test examples locally before committing
- ✅ Commit both code AND output changes together
- ✅ Use print statements to show key results
- ✅ Keep examples fast (<30 seconds)

### DON'T:
- ❌ Hand-edit output files (always regenerate)
- ❌ Include interactive prompts in examples
- ❌ Rely on external files or network resources
- ❌ Make examples depend on each other
- ❌ Include random/non-deterministic output without seeding
- ❌ Leave output files uncommitted after changing code

## Troubleshooting

### Example fails to execute

1. Check that all imports are available
2. Verify the example runs standalone: `python examples/docs/your_example.py`
3. Check for missing dependencies
4. Look at the error in `examples/docs_outputs/manifest.json`

### Validation fails

1. Check that RST files use correct path: `../examples/docs_outputs/filename.txt`
2. Verify output files exist: `ls examples/docs_outputs/`
3. Run validation with verbose flag: `python scripts/validate_docs_outputs.py --verbose`

### CI says outputs diverged

This means you changed example code but didn't regenerate outputs:

```bash
python scripts/generate_docs_outputs.py
git add examples/docs_outputs/
git commit -m "Update docs outputs"
```

## Implementation Details

### Manifest Structure

The `manifest.json` file tracks metadata for all examples:

```json
{
  "version": "1.0",
  "generated": "2024-01-24T12:34:56Z",
  "examples": {
    "01_basic_query": {
      "success": true,
      "output_file": "01_basic_query.txt",
      "has_stderr": false,
      "duration_seconds": 1.23
    }
  }
}
```

### Output File Format

Output files are plain text containing:
- Everything printed to stdout during execution
- Stderr (if any) with clear markers
- No ANSI color codes or control characters

### Validation Logic

The validation script:
1. Parses RST files to find `.. literalinclude::` directives
2. Checks that paths point to `examples/docs_outputs/`
3. Verifies referenced files exist and are in manifest
4. Ensures no orphaned output files (not referenced in any RST)

## Future Enhancements

Potential improvements for this system:

- **Diff visualization**: Show side-by-side comparison of old vs new outputs
- **Selective regeneration**: Only re-run examples that changed
- **Output caching**: Cache outputs based on code hash
- **Integration tests**: Run examples as part of main test suite
- **Jupyter notebooks**: Support converting notebooks to examples
- **Interactive examples**: Add web-based interactive versions

## Questions?

For issues or questions about this system:
1. Check the [AGENTS.md](../AGENTS.md) documentation
2. Run `python scripts/generate_docs_outputs.py --help`
3. Check CI logs for specific failure details
4. File an issue on GitHub with the `documentation` label
