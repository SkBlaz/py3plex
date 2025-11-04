# Py3plex Examples

This directory contains 50+ example scripts demonstrating the capabilities of py3plex for multilayer network analysis.

## Running Examples

Examples can be run from any directory once py3plex is installed:

```bash
# From the repository root
python examples/basic/example_random_generator.py

# From the examples directory
cd examples/basic
python example_random_generator.py

# From any other location
cd /tmp
python /path/to/py3plex/examples/basic/example_random_generator.py
```

### Prerequisites

Install py3plex from GitHub:

```bash
pip install git+https://github.com/SkBlaz/py3plex.git
```

Or for development, install in editable mode from the repository root:

```bash
pip install -e .
```

## Example Categories

### Basic Examples (`basic/`)
- Network creation and manipulation
- Loading and saving networks
- Basic network operations
- I/O operations

### Visualization (`visualization/`)
- Network visualization techniques
- Multilayer visualization
- Community visualization
- Animation and interactive plots

### Community Detection (`community_detection/`)
- Louvain algorithm
- Leiden algorithm
- Label propagation
- Multilayer community detection

### Centrality and Statistics (`centrality_and_statistics/`)
- Node centrality measures
- Network statistics
- Multilayer centrality
- Power-law analysis

### Decomposition and Classification (`decomposition_and_classification/`)
- Network decomposition
- HINMINE decomposition
- Semantic enrichment
- Node classification

### Embeddings (`embeddings/`)
- Node2Vec embeddings
- Embedding visualization
- Custom embeddings

### Dynamics (`dynamics/`)
- Random walks
- Spreading dynamics
- SIR models
- Temporal networks

### Multilayer (`multilayer/`)
- Multilayer network operations
- Supra-adjacency matrices
- Layer manipulation
- Tensorial operations

### Benchmarks and Tutorials (`benchmarks_and_tutorials/`)
- 10-minute tutorial
- Comparison benchmarks
- Complete workflows

## Path Resolution

All examples use utility functions from `py3plex.utils` to resolve file paths correctly:

```python
from py3plex.utils import get_dataset_path, get_multilayer_dataset_path

# Load a dataset
network = multinet.multi_layer_network().load_network(
    get_dataset_path("test.edgelist"),
    directed=False,
    input_type="edgelist"
)

# Load a multilayer dataset
network = multinet.multi_layer_network().load_network(
    get_multilayer_dataset_path("MLKing/MLKing2013_multiplex.edges"),
    directed=True,
    input_type="multiplex_edges"
)
```

### Available Path Utilities

- `get_dataset_path(filename)` - Resolves paths in the `datasets/` directory
- `get_multilayer_dataset_path(path)` - Resolves paths in the `multilayer_datasets/` directory
- `get_example_image_path(filename)` - Resolves paths in the `example_images/` directory
- `get_background_knowledge_path(filename)` - Resolves paths in the `background_knowledge/` directory
- `get_data_path(relative_path)` - Resolves any path relative to the repository root

These functions work by locating the installed py3plex package and constructing absolute paths from there. This ensures examples work regardless of the current working directory.

## CI Mode

Examples automatically detect CI environments and adjust behavior:

```python
import os

if os.environ.get('MPLBACKEND') == 'Agg':
    print("Running in CI mode - skipping interactive visualization")
else:
    network.visualize_network(show=True)
```

Some examples are marked with `SKIP_CI` to prevent them from running in automated tests:

```python
# SKIP_CI: slow - Takes more than 10 seconds to complete
# SKIP_CI: external_deps - Requires external binaries
# SKIP_CI: interactive - Requires user interaction
```

See [EXAMPLES_CI.md](../.github/EXAMPLES_CI.md) for more details.

## Common Patterns

### Creating a Network

```python
from py3plex.core import multinet

# Create an empty network
network = multinet.multi_layer_network()

# Add edges (automatically creates nodes and layers)
network.add_edges([
    ['A', 'layer1', 'B', 'layer1', 1],
    ['B', 'layer1', 'C', 'layer1', 1],
], input_type="list")
```

### Loading from File

```python
from py3plex.core import multinet
from py3plex.utils import get_dataset_path

# Load from edgelist
network = multinet.multi_layer_network().load_network(
    get_dataset_path("test.edgelist"),
    directed=False,
    input_type="edgelist"
)

# Load from pickle
network = multinet.multi_layer_network().load_network(
    get_dataset_path("imdb.gpickle"),
    directed=True,
    input_type="gpickle"
)
```

### Visualization

```python
# Simple visualization
network.visualize_network(show=True)

# Diagonal multilayer layout
network.visualize_network(style="diagonal")

# Hairball plot
network.visualize_network(style="hairball")

# Custom visualization
from py3plex.visualization.multilayer import hairball_plot
hairball_plot(
    network.core_network,
    layout_algorithm="force",
    layout_parameters={"iterations": 100}
)
```

### Community Detection

```python
from py3plex.algorithms.community_detection import community_wrapper as cw

# Louvain algorithm
partition = cw.louvain_communities(network.core_network)

# Infomap algorithm (requires external binary)
partition = cw.infomap_communities(
    network,
    binary="./infomap",
    multiplex=False
)
```

## Troubleshooting

### ModuleNotFoundError: No module named 'py3plex'

Make sure py3plex is installed:

```bash
pip install git+https://github.com/SkBlaz/py3plex.git
```

For development, use editable install from the repository root:

```bash
pip install -e .
```

### File Not Found Errors

Always use the path utility functions instead of hardcoded paths:

```python
# ✗ Wrong - hardcoded path
network.load_network("datasets/test.edgelist", ...)

# ✓ Correct - using utility function
from py3plex.utils import get_dataset_path
network.load_network(get_dataset_path("test.edgelist"), ...)
```

### Visualization Not Working

Some examples require matplotlib and other visualization dependencies:

```bash
pip install matplotlib networkx scipy
```

For CI/headless environments, set the matplotlib backend:

```bash
export MPLBACKEND=Agg
python example_visualization.py
```

### Missing External Dependencies

Some examples require external binaries:

- Node2Vec embeddings: Install from https://github.com/snap-stanford/snap
- Infomap: Install from https://www.mapequation.org/infomap/
- ImageMagick: For animation examples

These examples are marked with `SKIP_CI: external_deps` and will be skipped in automated testing.

## Contributing Examples

When adding new examples:

1. Use path utility functions for all file operations
2. Add docstrings explaining what the example demonstrates
3. Keep examples focused on a single concept
4. Add `SKIP_CI` marker if the example is slow or has external dependencies
5. Handle missing optional dependencies gracefully
6. Test from different directories to ensure paths work

See [EXAMPLES_CI.md](../.github/EXAMPLES_CI.md) for detailed guidelines.

## Getting Help

- Documentation: https://skblaz.github.io/py3plex/
- Issues: https://github.com/SkBlaz/py3plex/issues
- Discussions: https://github.com/SkBlaz/py3plex/discussions
