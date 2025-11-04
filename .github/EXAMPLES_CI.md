# Examples CI Documentation

## Overview

The Examples CI workflow automatically runs fast-running examples from the `examples/` directory to ensure they continue to work with the latest codebase changes.

## How It Works

The workflow runs on every push and pull request to main branches. It:

1. Discovers all Python example files in the `examples/` directory
2. Filters examples based on skip markers (see below)
3. Runs each example with a 10-second timeout
4. Reports results as pass/fail
5. Uploads any generated artifacts (images, etc.)

## Skip Markers

To prevent long-running or problematic examples from running in CI, you can add a skip marker to the file header.

### Supported Markers

Add one of these markers anywhere in the first 50 lines of your example file (in comments or docstrings):

```python
# SKIP_CI: slow - Takes more than 10 seconds to complete
```

```python
# SKIP_CI: external_deps - Requires external binaries (node2vec, imagemagick, etc.)
```

```python
# SKIP_CI: interactive - Requires user interaction
```

```python
"""
Example docstring

SKIP_CI: slow - This tutorial takes more than 10 seconds
"""
```

### When to Add Skip Markers

Add a skip marker if your example:

- **Takes longer than 10 seconds** to run
- **Requires external binaries** not installed in CI (node2vec, imagemagick, infomap)
- **Requires user interaction** (GUI windows, input prompts)
- **Requires large datasets** not available in the repository
- **Has external service dependencies** (APIs, databases)

### Examples

#### Slow Example
```python
"""
Tutorial - Full Network Analysis

This comprehensive tutorial demonstrates all features.

SKIP_CI: slow - Full tutorial takes 30+ seconds
"""

from py3plex.core import multinet
# ... rest of code
```

#### External Dependencies
```python
# Network embedding example using Node2Vec
# SKIP_CI: external_deps - Requires node2vec binary

from py3plex.core import multinet
# ... rest of code
```

#### Interactive Visualization
```python
"""
Interactive network visualization example

SKIP_CI: interactive - Opens GUI window for user interaction
"""

from py3plex.core import multinet
# ... rest of code
```

## Making Examples CI-Friendly

### Disable Interactive Visualizations in CI

Check for the `MPLBACKEND=Agg` environment variable to detect CI mode:

```python
import os

# Generate network
network = generate_network()

# Skip interactive visualization in CI
if os.environ.get('MPLBACKEND') == 'Agg':
    print("Running in CI mode - skipping interactive visualization")
else:
    network.visualize_network(show=True)
```

### Use Shorter Timeouts

Keep examples concise and fast:

```python
# Good - runs in < 5 seconds
network = random_multilayer_ER(100, 3, 0.05)

# Avoid - takes > 10 seconds
network = random_multilayer_ER(10000, 20, 0.5)
```

### Handle Missing Optional Dependencies

Use try-except blocks for optional dependencies:

```python
try:
    import seaborn as sns
    # Code that uses seaborn
except ImportError:
    print("Seaborn not available - skipping visualization")
```

## Running Examples Locally

### Run All Fast Examples

```bash
python .github/scripts/run_examples.py --fast-only --timeout 10
```

### Run All Examples (Including Slow Ones)

```bash
python .github/scripts/run_examples.py --timeout 60
```

### Run Examples from Specific Directory

```bash
python .github/scripts/run_examples.py --examples-dir examples/basic --timeout 10
```

## Checking CI Status

The Examples CI status badge is displayed in the README:

[![Examples](https://github.com/SkBlaz/py3plex/actions/workflows/examples.yml/badge.svg)](https://github.com/SkBlaz/py3plex/actions/workflows/examples.yml)

Click the badge to see detailed logs of which examples passed/failed.

## Troubleshooting

### Example Fails in CI but Works Locally

Common causes:

1. **Missing dependencies**: CI has only core dependencies installed
2. **File paths**: Use `get_dataset_path()` instead of relative paths
3. **Timeouts**: Reduce dataset size or add skip marker
4. **Interactive code**: Check for `MPLBACKEND=Agg` and disable GUI

### Adding New Dependencies

If your example requires a new dependency:

1. Add it to `requirements.txt`
2. Update the CI workflow if it's a system dependency
3. Consider adding error handling for optional dependencies

## Best Practices

1. **Keep examples simple**: Focus on demonstrating one concept
2. **Use small datasets**: Keep runtime under 5 seconds when possible
3. **Add docstrings**: Explain what the example demonstrates
4. **Test locally first**: Run the script before committing
5. **Add skip markers early**: Mark slow examples before pushing
6. **Handle errors gracefully**: Use try-except for optional features

## Technical Details

### Runner Script

The runner script (`.github/scripts/run_examples.py`) handles:

- Example discovery and filtering
- Skip marker detection
- Timeout enforcement
- Result reporting
- Error capture and logging

### Workflow Configuration

The workflow (`.github/workflows/examples.yml`):

- Runs on Ubuntu with Python 3.9 and 3.11
- Installs core dependencies
- Sets `MPLBACKEND=Agg` for non-interactive mode
- Times out after 20 minutes total
- Uploads generated artifacts

### Skip Detection Logic

The script checks for `SKIP_CI` in:
- Python comments (`# SKIP_CI: reason`)
- Docstrings (`"""... SKIP_CI: reason ..."""`)
- First 50 lines of the file only

### External Dependency Detection

In fast-only mode, the script automatically skips examples containing:
- `imagemagick` - Animation/GIF creation
- `node2vec` - Graph embeddings
- `infomap` - Community detection
- `show=True` - Interactive visualizations
- `animation.ArtistAnimation` - Matplotlib animations
