# Quickstart Documentation Code Execution Scripts

This directory contains automated tools for executing code snippets in the quickstart documentation and generating expected outputs.

## Overview

The py3plex quickstart documentation (`quickstart.rst`) contains 21 Python code snippets demonstrating various features. These scripts ensure that all code snippets have corresponding Expected Output sections, providing a complete, reproducible documentation experience.

## Scripts

### 1. `generate_all_outputs.py` - Main Output Generator

**Purpose:** Executes all quickstart code snippets and generates formatted RST output blocks.

**Usage:**
```bash
python docfiles/generate_all_outputs.py
```

**Output:** Creates `/tmp/quickstart_outputs.txt` with formatted RST output blocks ready for integration into `quickstart.rst`.

**Features:**
- Executes all runnable snippets with actual py3plex code
- Generates sample outputs for file-based operations
- Provides explanatory notes for snippets requiring external dependencies
- Formats output as RST code blocks for easy copy-paste

### 2. `run_quickstart_snippets.py` - Snippet Execution Framework

**Purpose:** Comprehensive framework for extracting, categorizing, and executing code snippets.

**Usage:**
```bash
python docfiles/run_quickstart_snippets.py [--update] [--report /path/to/report.md]
```

**Options:**
- `--update`: Update quickstart.rst with captured outputs (not fully implemented)
- `--report`: Path to save execution report (default: `/tmp/quickstart_report.md`)

**Features:**
- Parses RST files to extract Python code blocks
- Categorizes snippets by executability
- Executes snippets in a controlled environment
- Captures stdout/stderr
- Generates detailed execution reports

### 3. `generate_quickstart_outputs.py` - Test/Debug Script

**Purpose:** Simple test script for debugging individual snippet execution.

**Usage:**
```bash
python docfiles/generate_quickstart_outputs.py
```

**Output:** Prints outputs directly to console for quick verification.

## Makefile Integration

Added target to Makefile for easy execution:

```bash
make docs-quickstart
```

This runs `generate_all_outputs.py` and displays completion message.

## Code Snippet Categories

The scripts categorize snippets into:

1. **Runnable** (10 snippets): Can execute without external files
   - Example: Creating networks, statistics, random walks
   
2. **Requires Files** (4 snippets): Need external data files
   - Example: Loading from edgelist, GraphML
   - Scripts create sample files for testing
   
3. **Visualization** (3 snippets): Produce visual output
   - Example: draw_multilayer_default, hairball_plot
   - Noted as "produces plot, no text output"
   
4. **Requires Binary** (1 snippet): Need external binary installation
   - Example: Infomap community detection
   
5. **Setup Only** (3 snippets): Just imports/assignments
   - Example: Import statements, variable assignments

## Current Status

✅ **100% Coverage Achieved** (as of 2025-11-22)

All 21 code snippets in `quickstart.rst` now have:
- Expected Output sections with actual execution results, OR
- Explanatory notes about requirements/behavior

## Maintenance

### When to Update Outputs

Update outputs when:
- API changes affect example code
- New features are added to examples
- Bug fixes change behavior
- Adding new examples to quickstart

### How to Update

1. Run output generator:
   ```bash
   make docs-quickstart
   ```

2. Review generated outputs:
   ```bash
   cat /tmp/quickstart_outputs.txt
   ```

3. Update `quickstart.rst` with new outputs

4. Build and verify documentation:
   ```bash
   make docs
   # or
   sphinx-build -b html docfiles /tmp/docs_build
   ```

5. Check the rendered HTML:
   ```bash
   open /tmp/docs_build/quickstart.html
   ```

## Future Enhancements

Potential improvements:

- [ ] Automated integration of outputs into RST files
- [ ] CI/CD integration to verify snippets still execute
- [ ] Extend to other documentation files (10min_tutorial.rst, etc.)
- [ ] Add screenshot capture for visualization snippets
- [ ] Support for Jupyter notebook output format
- [ ] Doctest integration for inline examples

## Implementation Notes

### Why Manual Integration?

While the scripts can generate outputs, they don't automatically update `quickstart.rst` because:
- RST parsing and updating is complex and error-prone
- Manual review ensures quality and accuracy
- Context matters - some snippets need additional explanation
- Preserves documentation style and formatting

### Execution Environment

Scripts execute in a controlled environment:
- Temporary directory for file operations
- Sample data files created on-the-fly
- Logging suppressed for clean output
- Shared namespace to simulate progressive execution

### Error Handling

Scripts handle:
- Import errors (missing optional dependencies)
- API mismatches (outdated examples)
- File not found errors (file-based snippets)
- Execution errors (invalid operations)

Errors are captured and formatted as notes in the output.

## Questions?

For issues or questions about these scripts:
1. Check the execution report: `/tmp/quickstart_report.md`
2. Review script docstrings and comments
3. Test individual snippets with `generate_quickstart_outputs.py`
4. Open an issue on GitHub with details

---

Last updated: 2025-11-22
