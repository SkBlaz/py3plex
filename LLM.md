# Py3plex Developer and LLM Documentation

This document consolidates technical documentation for developers and LLM assistants working with py3plex.

---

## Table of Contents

1. [Visualization Module Import Guide](#visualization-module-import-guide)
2. [Examples CI Documentation](#examples-ci-documentation)
3. [Property-Based Tests](#property-based-tests)

---

## Visualization Module Import Guide

The py3plex visualization module has been enhanced to provide convenient imports while maintaining full backwards compatibility.

### What Changed

The `py3plex.visualization` module now exports commonly used functions and classes directly, making imports cleaner and more intuitive.

#### Before (still works!)

```python
from py3plex.visualization.multilayer import hairball_plot, plt
from py3plex.visualization.colors import colors_default
from py3plex.visualization.embedding_visualization import embedding_tools
```

#### After (new convenience imports)

```python
from py3plex.visualization import hairball_plot, plt, colors_default
# embedding_tools still imported from submodule:
from py3plex.visualization.embedding_visualization import embedding_tools
```

### Available Convenience Imports

#### Visualization Functions
- `hairball_plot` - Create hairball/force-directed network visualizations
- `draw_multilayer_default` - Draw multilayer networks with diagonal layout
- `draw_multiedges` - Draw networks with multiple edges between nodes
- `interactive_hairball_plot` - Interactive hairball visualization

#### Color Utilities
- `colors_default` - Default color palette (list of 200 colors)
- `colors_blue` - Blue color palette
- `all_color_names` - Dictionary of all named colors
- `hex_to_RGB` - Convert hex color to RGB
- `RGB_to_hex` - Convert RGB to hex color
- `linear_gradient` - Generate color gradients
- `color_dict` - Create color dictionaries

#### Other
- `plt` - matplotlib.pyplot for convenience

### Examples

#### Basic Visualization

```python
from py3plex.visualization import hairball_plot, colors_default, plt
from py3plex.core import multinet

# Create a network
network = multinet.multi_layer_network()
# ... load or create network ...

# Get network representation
colors, graph = network.get_layers(style="hairball")

# Plot
hairball_plot(graph, colors)
plt.show()
```

#### Using Color Utilities

```python
from py3plex.visualization import hex_to_RGB, RGB_to_hex, linear_gradient

# Convert colors
rgb = hex_to_RGB("#FF0000")  # [255, 0, 0]
hex_color = RGB_to_hex([255, 0, 0])  # "#ff0000"

# Generate gradient
gradient = linear_gradient("#FF0000", "#0000FF", n=10)
```

### Backwards Compatibility

All existing import patterns continue to work exactly as before. The new exports are provided for convenience and do not break any existing code.

```python
# Old way - still works perfectly
from py3plex.visualization.multilayer import hairball_plot
from py3plex.visualization.colors import colors_default

# New way - also works
from py3plex.visualization import hairball_plot, colors_default

# Both give you the exact same objects
```

### Module Structure

```
py3plex.visualization/
├── __init__.py (exports convenience imports)
├── multilayer.py (main visualization functions)
├── colors.py (color utilities)
├── embedding_visualization/
│   ├── __init__.py (exports embedding modules)
│   ├── embedding_tools.py
│   └── embedding_visualization.py
├── bezier.py (bezier curve utilities)
├── polyfit.py (polynomial fitting utilities)
└── layout_algorithms.py (layout computation)
```

### Testing

The new imports are covered by comprehensive tests in `tests/test_visualization_imports.py`:
- Convenience import functionality
- Backwards compatibility verification  
- Module structure validation
- Import path equivalence checks

Run the tests:
```bash
python -m pytest tests/test_visualization_imports.py -v
```

### Migration Guide

No migration needed! Your existing code will continue to work. However, you may want to simplify imports where possible:

#### Optional Simplifications

```python
# Instead of:
from py3plex.visualization.multilayer import hairball_plot, draw_multilayer_default
from py3plex.visualization.colors import colors_default

# You can now write:
from py3plex.visualization import hairball_plot, draw_multilayer_default, colors_default
```

This is purely optional and for convenience - both styles are fully supported.

---

## Examples CI Documentation

### Overview

The Examples CI workflow automatically runs fast-running examples from the `examples/` directory to ensure they continue to work with the latest codebase changes.

### How It Works

The workflow runs on every push and pull request to main branches. It:

1. Discovers all Python example files in the `examples/` directory
2. Filters examples based on skip markers (see below)
3. Runs each example with a 10-second timeout
4. Reports results as pass/fail
5. Uploads any generated artifacts (images, etc.)

### Skip Markers

To prevent long-running or problematic examples from running in CI, you can add a skip marker to the file header.

#### Supported Markers

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

#### When to Add Skip Markers

Add a skip marker if your example:

- **Takes longer than 10 seconds** to run
- **Requires external binaries** not installed in CI (node2vec, imagemagick, infomap)
- **Requires user interaction** (GUI windows, input prompts)
- **Requires large datasets** not available in the repository
- **Has external service dependencies** (APIs, databases)

#### Examples

##### Slow Example
```python
"""
Tutorial - Full Network Analysis

This comprehensive tutorial demonstrates all features.

SKIP_CI: slow - Full tutorial takes 30+ seconds
"""

from py3plex.core import multinet
# ... rest of code
```

##### External Dependencies
```python
# Network embedding example using Node2Vec
# SKIP_CI: external_deps - Requires node2vec binary

from py3plex.core import multinet
# ... rest of code
```

##### Interactive Visualization
```python
"""
Interactive network visualization example

SKIP_CI: interactive - Opens GUI window for user interaction
"""

from py3plex.core import multinet
# ... rest of code
```

### Making Examples CI-Friendly

#### Disable Interactive Visualizations in CI

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

#### Use Shorter Timeouts

Keep examples concise and fast:

```python
# Good - runs in < 5 seconds
network = random_multilayer_ER(100, 3, 0.05)

# Avoid - takes > 10 seconds
network = random_multilayer_ER(10000, 20, 0.5)
```

#### Handle Missing Optional Dependencies

Use try-except blocks for optional dependencies:

```python
try:
    import seaborn as sns
    # Code that uses seaborn
except ImportError:
    print("Seaborn not available - skipping visualization")
```

### Running Examples Locally

#### Run All Fast Examples

```bash
python .github/scripts/run_examples.py --fast-only --timeout 10
```

#### Run All Examples (Including Slow Ones)

```bash
python .github/scripts/run_examples.py --timeout 60
```

#### Run Examples from Specific Directory

```bash
python .github/scripts/run_examples.py --examples-dir examples/basic --timeout 10
```

### Checking CI Status

The Examples CI status badge is displayed in the README:

[![Examples](https://github.com/SkBlaz/py3plex/actions/workflows/examples.yml/badge.svg)](https://github.com/SkBlaz/py3plex/actions/workflows/examples.yml)

Click the badge to see detailed logs of which examples passed/failed.

### Troubleshooting

#### Example Fails in CI but Works Locally

Common causes:

1. **Missing dependencies**: CI has only core dependencies installed
2. **File paths**: Use `get_dataset_path()` instead of relative paths
3. **Timeouts**: Reduce dataset size or add skip marker
4. **Interactive code**: Check for `MPLBACKEND=Agg` and disable GUI

#### Adding New Dependencies

If your example requires a new dependency:

1. Add it to `requirements.txt`
2. Update the CI workflow if it's a system dependency
3. Consider adding error handling for optional dependencies

### Best Practices

1. **Keep examples simple**: Focus on demonstrating one concept
2. **Use small datasets**: Keep runtime under 5 seconds when possible
3. **Add docstrings**: Explain what the example demonstrates
4. **Test locally first**: Run the script before committing
5. **Add skip markers early**: Mark slow examples before pushing
6. **Handle errors gracefully**: Use try-except for optional features

### Technical Details

#### Runner Script

The runner script (`.github/scripts/run_examples.py`) handles:

- Example discovery and filtering
- Skip marker detection
- Timeout enforcement
- Result reporting
- Error capture and logging

#### Workflow Configuration

The workflow (`.github/workflows/examples.yml`):

- Runs on Ubuntu with Python 3.9 and 3.11
- Installs core dependencies
- Sets `MPLBACKEND=Agg` for non-interactive mode
- Times out after 20 minutes total
- Uploads generated artifacts

#### Skip Detection Logic

The script checks for `SKIP_CI` in:
- Python comments (`# SKIP_CI: reason`)
- Docstrings (`"""... SKIP_CI: reason ..."""`)
- First 50 lines of the file only

#### External Dependency Detection

In fast-only mode, the script automatically skips examples containing:
- `imagemagick` - Animation/GIF creation
- `node2vec` - Graph embeddings
- `infomap` - Community detection
- `show=True` - Interactive visualizations
- `animation.ArtistAnimation` - Matplotlib animations

---

## Property-Based Tests

### Overview

This section contains property-based tests using [Hypothesis](https://hypothesis.readthedocs.io/), a framework for property-based testing that generates diverse test inputs to validate invariants and contracts.

Property-based tests verify that code satisfies mathematical properties and invariants across a wide range of inputs, rather than testing specific hand-written examples. This approach is particularly valuable for multilayer network algorithms where edge cases and boundary conditions can be subtle.

**Total: 273+ property-based tests**

### Test Modules

#### Centrality Tests

##### `test_centrality_invariants.py` (17 tests)
Tests fundamental mathematical properties and invariants for multilayer centrality metrics.

**Properties tested:**
- Non-negativity of all centrality values
- Finiteness (no NaN or infinity)
- Participation coefficient bounds [0, 1]
- Normalization properties (L1, L2, Lp norms)
- Isomorphism invariance for degree and betweenness
- Consistency across operations
- Extended centrality metrics properties

##### `test_centrality_rankings.py` (13 tests)
Tests ranking stability, monotonicity, and scale invariance properties.

**Properties tested:**
- Network topology effects (star, path)
- Scale invariance of normalized centralities
- Linear scaling of weighted degree
- Monotonicity properties
- Ranking stability across computations
- Participation coefficient effects

#### Core Operations Tests

##### `test_edge_operations_properties.py` (9 tests)
Tests fundamental invariants for edge operations in multilayer networks.

**Properties tested:**
- Edge addition increases edge count
- Edge removal decreases edge count  
- Edge endpoints are valid nodes
- Edge weights are non-negative by default
- Edge weight preservation
- Undirected edge symmetry
- Inter-layer edge validity
- Edge addition idempotence
- Edge list consistency

##### `test_node_operations_properties.py` (10 tests)
Tests fundamental invariants for node operations in multilayer networks.

**Properties tested:**
- Node addition increases node count
- Node uniqueness within layer
- Node removal consistency
- Node layer assignment
- Same node across different layers
- Node count non-negative
- Isolated nodes preserved
- Node retrieval consistency
- Node degree non-negative
- Node neighborhood consistency

##### `test_weight_operations_properties.py` (10 tests)
Tests numerical properties of edge weights including normalization and scaling.

**Properties tested:**
- Weight assignment preserved
- Weight scaling linearity
- Weight sum non-negative
- Weight addition commutative
- Weight mean bounds
- Weight comparison transitivity
- Uniform weights constant mean
- Weight variance non-negative
- Weight multiplication identity
- Weight ordering preserved

##### `test_graph_transformation_properties.py` (11 tests)
Tests structural invariants under graph transformations.

**Properties tested:**
- Complement graph edge sum
- Subgraph preserves edges
- Connected components partition
- Layer union preserves nodes
- Edge reversal preserves connectivity
- Layer intersection subset
- Spanning tree connected
- Degree sequence sum even (Handshaking Lemma)
- Graph union commutative
- Empty layer removal idempotent
- Bipartite projection preserves nodes

#### Advanced Tests

##### `test_io_roundtrip.py`
Tests I/O round-trip invariants for loading NetworkX graphs into py3plex.

**Properties tested:**
- Node preservation: Nodes in input graph equal nodes in loaded network
- Edge preservation: Edges in input graph equal edges in loaded network  
- Non-negative counts: Node and edge counts are always ≥ 0
- Directedness: Directed flag is respected when loading

**Run:**
```bash
pytest tests/property/test_io_roundtrip.py -v
```

##### `test_versatility_properties.py`
Tests versatility (multilayer eigenvector centrality) invariants.

**Properties tested:**
- Single-layer reduction: With one layer, versatility matches NetworkX eigenvector centrality (up to sign)
- L1 normalization: When `normalize="l1"`, sum of absolute values equals 1
- L2 normalization: When `normalize="l2"`, L2 norm equals 1
- Scale invariance: Scaling edge weights by constant preserves normalized scores
- Finite values: Results always contain finite values (no NaN, no inf)
- Non-negativity: Non-negative weights produce non-negative scores (for connected graphs)

**Run:**
```bash
pytest tests/property/test_versatility_properties.py -v
```

##### `test_converters_properties.py` (19 tests)
Tests layout computation, coordinate normalization, and network preparation invariants.

**Properties tested:**
- Random layout preserves all nodes
- Layout coordinates normalized to [0, 1] range
- Layout coordinates always finite (no NaN/inf)
- Custom layout preserves provided positions
- Layout respects different graph structures
- Hairball preparation preserves network structure
- Hairball preparation enumerates layers correctly
- Parsing separates layers correctly
- Parsing identifies inter-layer edges
- Parsing handles empty layers gracefully
- Parsing preserves total node count
- Layout handles isolated nodes
- Layout handles single-edge graphs

**Run:**
```bash
pytest tests/property/test_converters_properties.py -v
```

##### `test_supporting_properties.py` (21 tests)
Tests layer splitting, multiplex edge addition, and utility function invariants.

**Properties tested:**
- Layer splitting preserves all nodes
- Layer splitting produces correct layer count
- Each layer has expected nodes after splitting
- Layer splitting preserves intra-layer edges
- Layer splitting excludes inter-layer edges
- Layer splitting returns dictionary of graphs
- Multiplex edges increase edge count
- Multiplex edges preserve node count
- Multiplex edges connect corresponding nodes across layers
- Multiplex edges only between different layers
- Multiplex edges connect same node IDs
- Single-layer networks unchanged by multiplex operation
- Multiplex edges with partial node overlap
- Empty network handling
- Multiplex edge addition idempotence

**Run:**
```bash
pytest tests/property/test_supporting_properties.py -v
```

##### `test_basic_statistics_properties.py` (23 tests)
Tests statistical invariants, hub identification, and network metric properties.

**Properties tested:**
- Hub identification returns at most top_n hubs
- Hub degrees always non-negative integers
- Hubs sorted by degree (highest first)
- Star graph center identified as top hub
- Complete graph has all nodes with equal degree
- Empty graph has all nodes with degree 0
- Core statistics report non-negative counts
- Node count matches actual node count
- Edge count matches actual edge count
- Mean degree within valid bounds
- Network density between 0 and 1
- Complete graph has density 1
- Empty graph has density 0
- Connected components count positive
- Star graph statistics have expected properties
- Path graph statistics have expected properties
- Handshaking lemma (sum of degrees = 2 × edges)

**Run:**
```bash
pytest tests/property/test_basic_statistics_properties.py -v
```

##### `test_io_converters_properties.py` (20 tests)
Tests conversion between MultiLayerGraph and NetworkX, preserving structure and attributes.

**Properties tested:**
- Union mode preserves all unique nodes
- Union mode merges edges from all layers
- Multiplex mode preserves layer information
- Multiplex mode preserves all edges
- Conversion returns correct NetworkX graph type
- Intersection mode is conservative (fewer or equal edges)
- Converted graphs have non-negative node/edge counts
- Empty layers handled correctly
- Connectivity patterns preserved
- Graph-level attributes preserved
- Node attributes preserved
- Union mode flattens layers
- Multiplex mode creates node-layer tuples

**Run:**
```bash
pytest tests/property/test_io_converters_properties.py -v
```

##### `test_random_generators_extended_properties.py` (20 tests)
Tests properties of random multilayer and multiplex network generators.

**Properties tested:**
- Random multilayer ER returns non-null network
- Correct node count in multilayer networks
- Non-negative edge counts
- Zero probability generates no edges
- One probability generates many edges
- Probability affects edge density
- Directed flag respected
- Random multiplex ER returns non-null network
- Correct node count in multiplex (n × l nodes)
- Multiplex has proper layer structure
- Minimal node count handling
- Single layer handling
- Probability extremes (0 and 1)

**Run:**
```bash
pytest tests/property/test_random_generators_extended_properties.py -v
```

##### `test_utils_properties.py` (15 tests)
Tests random number generator utilities and reproducibility.

**Properties tested:**
- get_rng returns numpy Generator
- Same seed produces identical random numbers
- Different seeds produce different random numbers
- None seed returns valid generator
- Passthrough of existing generator
- Generated numbers follow uniform distribution
- Generator supports various distributions (uniform, normal, integers)
- Multiple generators from same seed are independent
- Sequences are deterministic with same seed
- Seed 0 is valid
- Choice operations are deterministic
- Shuffle operations are deterministic
- Small seed values work correctly
- Large seed values work correctly

**Run:**
```bash
pytest tests/property/test_utils_properties.py -v
```

##### Other Test Modules

- `test_statistics_properties.py`: Layer density bounds (5 tests)
- `test_communities_properties.py`: Louvain community detection (needs python-louvain package)
- `test_random_generators_properties.py`: Random graph generators (needs parameter updates)

### CrossHair Contracts

The code includes assertions that can be analyzed by [CrossHair](https://github.com/pschanely/CrossHair), a tool that uses symbolic execution to find counterexamples to contracts.

#### In `py3plex/core/multinet.py`

**`load_network()` contracts:**
- **Precondition**: `input_type` must be in supported set
- **Precondition**: `input_file` required for non-NetworkX inputs
- **Postcondition**: `core_network` is initialized with non-negative node/edge counts
- **Postcondition**: When `directed=False`, graph is undirected

#### In `py3plex/algorithms/multilayer_algorithms/versatility.py`

**`versatility()` contracts:**
- **Precondition**: At least one layer required
- **Precondition**: All layers must be square and same size
- **Precondition**: `interlayer >= 0` for scalar coupling
- **Postcondition**: Result is numpy array of shape `(N,)`
- **Postcondition**: All values are finite
- **Postcondition**: L1/L2 normalization produces unit sum/norm

### Running Tests

#### Run all property tests
```bash
pytest tests/property/ -v -m property
```

#### Run specific test suites
```bash
# I/O tests only
pytest tests/property/test_io_roundtrip.py -v

# Versatility tests only  
pytest tests/property/test_versatility_properties.py -v
```

#### Run with Hypothesis settings
```bash
# More examples (slower but more thorough)
pytest tests/property/ -v --hypothesis-seed=42

# Show statistics
pytest tests/property/ -v --hypothesis-show-statistics
```

### CrossHair Analysis

To analyze contracts with CrossHair (when available):

```bash
# Check contracts in core module
crosshair check py3plex/core/multinet.py --analysis_kind=asserts --per_condition_timeout=3

# Check contracts in versatility
crosshair check py3plex/algorithms/multilayer_algorithms/versatility.py --analysis_kind=asserts --per_condition_timeout=3
```

Note: CrossHair analysis works best on pure functions without external I/O.

### Contributing

When adding new functionality to py3plex:

1. **Add property tests** for core invariants (normalization, bounds, symmetries)
2. **Add contracts** using assert statements with `# crosshair: analysis_kind=asserts` comment
3. **Use hypothesis strategies** to generate diverse inputs
4. **Test edge cases** explicitly (empty graphs, single nodes, disconnected components)

#### Property Test Template

```python
from hypothesis import given, strategies as st, settings
import pytest

@pytest.mark.property
@settings(deadline=None, max_examples=50)
@given(param=st.integers(min_value=1, max_value=100))
def test_my_property(param):
    """Test that my_function satisfies some mathematical property."""
    result = my_function(param)
    assert result >= 0, "Result must be non-negative"
    # Add more property checks
```

#### Writing Good Property Tests

**Choose the Right Properties:**
- **Invariants**: Properties that should always hold (e.g., node count ≥ 0)
- **Metamorphic**: Output changes predictably with input changes (e.g., scaling weights)
- **Round-trip**: Encode/decode should return original (e.g., save/load network)
- **Idempotence**: Applying operation twice = applying once (e.g., sorting)
- **Commutativity**: Order doesn't matter (e.g., A ∪ B = B ∪ A)

**Use Appropriate Strategies:**
```python
# Import from strategies module
from tests.property.strategies import (
    node_names,           # Generate node names
    layer_labels,         # Generate layer labels
    small_graphs,         # Generate small graphs
    weighted_graphs,      # Generate weighted graphs
    positive_weights,     # Generate positive weights
    probabilities,        # Generate probability values [0, 1]
)

# Example: Test with multiple strategies
@given(
    G=small_graphs(min_nodes=3, max_nodes=8),
    weight=positive_weights(min_value=0.1, max_value=10.0)
)
def test_weighted_property(G, weight):
    # Scale all edge weights
    for u, v in G.edges():
        G[u][v]['weight'] = weight
    # Test property...
```

**Handle Preconditions with `assume`:**
```python
from hypothesis import assume

@given(G=small_graphs())
def test_requires_connected(G):
    # Skip disconnected graphs
    assume(nx.is_connected(G))
    assume(G.number_of_nodes() >= 3)
    # Now test on connected graphs only
```

**Adjust Test Settings:**
```python
# Fast tests: more examples
@settings(max_examples=100, deadline=None)

# Slow tests: fewer examples but thorough
@settings(max_examples=20, deadline=None)

# Stateful tests: control step count
@settings(max_examples=20, stateful_step_count=15, deadline=None)
```

**Test Edge Cases Explicitly:**
```python
# Complement property tests with explicit edge cases
def test_empty_graph():
    G = nx.Graph()
    result = process_graph(G)
    assert result is not None

def test_single_node():
    G = nx.Graph()
    G.add_node(0)
    result = process_graph(G)
    assert result >= 0
```

#### Common Patterns

**Testing Symmetry:**
```python
@given(G=small_graphs())
def test_undirected_symmetry(G):
    """For undirected graphs, (u,v) exists iff (v,u) exists."""
    for u, v in G.edges():
        assert G.has_edge(v, u)
```

**Testing Bounds:**
```python
@given(G=small_graphs())
def test_centrality_bounds(G):
    """Normalized centrality values are in [0, 1]."""
    centrality = nx.degree_centrality(G)
    for value in centrality.values():
        assert 0.0 <= value <= 1.0
```

**Testing Conservation:**
```python
@given(G=small_graphs())
def test_node_preservation(G):
    """Operations preserve node count."""
    nodes_before = G.number_of_nodes()
    result = transform_graph(G)
    assert result.number_of_nodes() == nodes_before
```

### Test Organization

Property tests are organized by category:

- **`test_io_*.py`**: Input/output and serialization properties
- **`test_*_properties.py`**: Algorithm-specific properties
- **`test_stateful_*.py`**: Stateful testing with complex operation sequences
- **`test_*_invariants.py`**: Invariant checks across operations
- **`test_*_metamorphic.py`**: Metamorphic relations
- **`test_network_transformations.py`**: Graph transformation properties

### Performance Considerations

- Use `small_graphs` with `max_nodes ≤ 10` for fast tests
- Increase `max_examples` for fast, simple tests
- Decrease `max_examples` for slow, complex tests  
- Use `@settings(deadline=None)` to disable timeouts for slow operations
- Use `assume()` sparingly - excessive filtering slows tests

### References

- [Hypothesis documentation](https://hypothesis.readthedocs.io/)
- [Property-based testing primer](https://hypothesis.works/articles/what-is-property-based-testing/)
- [CrossHair documentation](https://github.com/pschanely/CrossHair)
- [Choosing properties for property-based testing](https://fsharpforfunandprofit.com/posts/property-based-testing-2/)

---

## New Property-Based Tests Added

This section describes the property-based tests added to expand test coverage for py3plex multilayer networks.

### Summary

**Latest additions:** 26 new property-based tests for centrality metrics across 2 modules:
- 16 tests for centrality invariants
- 10 tests for centrality rankings

**Previously added:** 40 property-based tests across 4 modules:
- 9 tests for edge operations
- 10 tests for node operations  
- 10 tests for weight operations
- 11 tests for graph transformations

**Total property-based tests: 151+** (increased from 125+)

### Latest Test Modules (Centrality Coverage)

#### 1. `test_centrality_invariants.py` (16 tests)

Tests fundamental mathematical properties and invariants for multilayer centrality metrics.

**Tests:**
1. `test_degree_centrality_non_negative` - Degree centrality values are always ≥ 0
2. `test_centrality_values_finite` - All centrality values are finite (no NaN/inf)
3. `test_participation_coefficient_bounded` - Participation coefficient in [0, 1]
4. `test_closeness_centrality_non_negative` - Closeness centrality is non-negative
5. `test_betweenness_centrality_non_negative` - Betweenness centrality is non-negative
6. `test_eigenvector_centrality_normalization` - L2 normalization produces unit norm
7. `test_lp_aggregated_centrality_properties` - Lp-aggregated centrality is valid
8. `test_degree_invariant_under_relabeling` - Degree multiset preserved under isomorphism
9. `test_betweenness_ranking_invariant` - Betweenness ranking preserved under relabeling
10. `test_layer_degree_sum_equals_overlapping` - Layer degrees sum to overlapping degree
11. `test_weighted_degree_greater_equal_unweighted` - Weighted ≥ unweighted (weights ≥ 1)
12. `test_information_centrality_properties` - Information centrality is valid
13. `test_collective_influence_properties` - Collective influence is non-negative
14. `test_harmonic_closeness_properties` - Harmonic closeness is non-negative
15. `test_compute_all_centralities_basic` - compute_all_centralities returns valid results
16. `test_compute_all_centralities_extended` - Extended mode includes more metrics

**Key Properties:**
- Non-negativity and finiteness
- Normalization correctness
- Isomorphism invariance
- Consistency across operations

#### 2. `test_centrality_rankings.py` (10 tests)

Tests ranking stability, monotonicity, and scale invariance of centrality metrics.

**Tests:**
1. `test_star_network_hub_highest_degree` - Hub node has highest degree in star networks
2. `test_star_network_hub_highest_betweenness` - Hub has highest betweenness
3. `test_path_network_endpoints_lowest_centrality` - Endpoints have lower centrality
4. `test_normalized_centrality_scale_invariant` - Rankings invariant to weight scaling
5. `test_weighted_degree_scales_linearly` - Weighted degree scales linearly
6. `test_adding_edges_increases_total_degree` - Monotonicity property
7. `test_more_layers_increases_overlapping_degree` - More layers = higher overlap
8. `test_degree_ranking_stability` - Rankings stable across computations
9. `test_centrality_consistent_node_set` - All measures return same node set
10. `test_uniform_distribution_increases_participation` - Uniform edges increase participation

**Key Properties:**
- Network topology effects
- Scale invariance
- Monotonicity
- Ranking stability

### Previous Test Modules

#### 3. `test_edge_operations_properties.py` (9 tests)

Tests fundamental invariants for edge manipulation in multilayer networks.

**Tests:**
1. `test_edge_addition_increases_edge_count` - Adding edges increases total count
2. `test_edge_removal_decreases_edge_count` - Removing edges decreases count
3. `test_edge_endpoints_are_nodes` - All edge endpoints must be valid nodes
4. `test_edge_weights_non_negative` - Default edge weights are non-negative
5. `test_edge_weight_preservation` - Explicitly set weights are preserved
6. `test_undirected_edge_symmetry` - Undirected networks have symmetric edges
7. `test_inter_layer_edge_validity` - Inter-layer edges connect different layers
8. `test_edge_addition_idempotence` - Adding same edges multiple times is idempotent
9. `test_edge_list_consistency` - Edge retrieval is consistent across calls

**Key Properties:**
- Monotonicity of edge counts
- Endpoint validity
- Weight preservation
- Symmetry in undirected graphs

#### 4. `test_node_operations_properties.py` (10 tests)

Tests fundamental invariants for node manipulation in multilayer networks.

**Tests:**
1. `test_node_addition_increases_node_count` - Adding nodes increases total count
2. `test_node_uniqueness_within_layer` - Nodes within a layer are unique
3. `test_node_removal_consistency` - Removing nodes removes incident edges
4. `test_node_layer_assignment` - Nodes are correctly associated with layers
5. `test_same_node_different_layers` - Same node ID can exist in multiple layers
6. `test_node_count_non_negative` - Node count is always non-negative
7. `test_isolated_nodes_preserved` - Nodes without edges are preserved
8. `test_node_retrieval_consistency` - Node retrieval is consistent across calls
9. `test_node_degree_non_negative` - Node degree is always non-negative
10. `test_node_neighborhood_consistency` - Neighborhoods match edges

**Key Properties:**
- Monotonicity of node counts
- Layer-node relationships
- Degree constraints
- Consistency of graph structure

#### 5. `test_weight_operations_properties.py` (10 tests)

Tests numerical properties of edge weights.

**Tests:**
1. `test_weight_assignment_preserved` - Assigned weights are preserved
2. `test_weight_scaling_linearity` - Scaling preserves weight ratios
3. `test_weight_sum_non_negative` - Sum of positive weights is positive
4. `test_weight_addition_commutative` - Weight addition is commutative
5. `test_weight_mean_bounds` - Mean weight bounded by min and max
6. `test_weight_comparison_transitivity` - Weight comparison is transitive
7. `test_uniform_weights_constant_mean` - Uniform weights have mean equal to value
8. `test_weight_variance_non_negative` - Variance is always non-negative
9. `test_weight_multiplication_identity` - Multiplying by 1 preserves weights
10. `test_weight_ordering_preserved` - Ordering of weights is preserved

**Key Properties:**
- Numerical stability
- Algebraic properties (commutativity, linearity)
- Statistical bounds
- Ordering preservation

#### 6. `test_graph_transformation_properties.py` (11 tests)

Tests structural invariants under graph transformations.

**Tests:**
1. `test_complement_graph_edge_sum` - Graph + complement = complete graph
2. `test_subgraph_preserves_edges` - Subgraph edges are subset of original
3. `test_connected_components_partition` - Components partition node set
4. `test_layer_union_preserves_nodes` - Union preserves node set
5. `test_edge_reversal_preserves_connectivity` - Reversal preserves connectivity
6. `test_layer_intersection_subset` - Intersection is subset of each layer
7. `test_spanning_tree_connected` - Spanning tree is connected
8. `test_degree_sequence_sum_even` - Handshaking Lemma (sum = 2|E|)
9. `test_graph_union_commutative` - Union is commutative
10. `test_empty_layer_removal_idempotent` - Empty layer removal is idempotent
11. `test_bipartite_projection_preserves_nodes` - Projection preserves nodes

**Key Properties:**
- Graph complement properties
- Subgraph relationships
- Component structure
- Classical graph theorems (Handshaking Lemma)

### Running the Tests

#### Run all new tests:
```bash
pytest tests/property/test_edge_operations_properties.py \
       tests/property/test_node_operations_properties.py \
       tests/property/test_weight_operations_properties.py \
       tests/property/test_graph_transformation_properties.py \
       -v
```

#### Run all property tests:
```bash
pytest tests/property/ -v
```

#### Run specific test category:
```bash
pytest tests/property/test_edge_operations_properties.py -v
```

### Test Framework

All tests use:
- **Hypothesis** for property-based testing
- **pytest** as the test runner
- **NetworkX** for graph operations
- **py3plex** multilayer network library

### Test Settings

- `deadline=None` - No time limit for slow convergence
- `max_examples=30-50` - Balance between thoroughness and speed
- `@pytest.mark.property` - Tagged for easy filtering

### Coverage

These tests expand coverage in:
- **Edge operations**: Basic graph manipulation
- **Node operations**: Node lifecycle and relationships
- **Weight operations**: Numerical properties
- **Graph transformations**: Structural invariants

### Mathematical Properties Verified

1. **Handshaking Lemma**: Σ deg(v) = 2|E|
2. **Subset relations**: Subgraph ⊆ Graph
3. **Partition property**: Components partition nodes
4. **Non-negativity**: Counts, weights ≥ 0
5. **Idempotence**: f(f(x)) = f(x) for certain operations
6. **Commutativity**: a + b = b + a for addition
7. **Linearity**: k(a + b) = ka + kb for scaling
8. **Transitivity**: a < b ∧ b < c ⟹ a < c

### Dependencies

- Python 3.8+
- pytest >= 7.0
- hypothesis >= 6.0
- networkx >= 2.5
- numpy >= 1.19.0
- scipy >= 1.5.0

---

## Advanced Property-Based Tests for py3plex

This document describes the comprehensive Hypothesis property-based test suite for py3plex's core multilayer network functionality.

### Overview

These tests use **property-based testing** with [Hypothesis](https://hypothesis.readthedocs.io/) to verify mathematical invariants and contracts across a wide range of generated inputs. This approach uncovers edge cases that manual testing might miss.

### Test Modules

#### 1. `test_centrality_invariants.py` - Centrality Metric Invariants

Tests fundamental mathematical properties and invariants for multilayer centrality metrics.

**Properties Tested:**
- **Non-negativity**: All centrality values ≥ 0
- **Finiteness**: No NaN or infinity values in results
- **Participation coefficient bounds**: Values in [0, 1]
- **Normalization**: L1/L2 norms equal 1 when requested (eigenvector centrality)
- **Lp-aggregated properties**: Correct aggregation with different norms (L1, L2, L∞)
- **Isomorphism invariance**: Degree rankings preserved under node relabeling
- **Betweenness ranking invariance**: Rankings consistent under isomorphic transformations
- **Consistency**: Layer degree sum equals overlapping degree
- **Monotonicity**: Weighted degree ≥ unweighted when weights ≥ 1
- **Extended metrics**: Information centrality, collective influence, harmonic closeness properties

**Run:**
```bash
pytest tests/property/test_centrality_invariants.py -v -m property
```

#### 2. `test_centrality_rankings.py` - Centrality Rankings & Metamorphic Relations

Tests ranking stability, monotonicity, and scale invariance properties of centrality metrics.

**Properties Tested:**
- **Star network topology**: Hub has highest degree and betweenness
- **Path network topology**: Endpoints have lower centrality than middle nodes
- **Scale invariance**: Normalized centrality rankings invariant to weight scaling
- **Linear scaling**: Weighted degree scales linearly with edge weights
- **Monotonicity**: Adding edges increases total degree
- **Layer effects**: More layers increase overlapping degree
- **Ranking stability**: Multiple computations produce identical rankings
- **Node set consistency**: All centrality measures return same node set
- **Participation coefficient**: Uniform distribution across layers increases participation

**Run:**
```bash
pytest tests/property/test_centrality_rankings.py -v -m property
```

#### 3. `test_io_metamorphic_roundtrip.py` - I/O Metamorphic Properties

Tests that network I/O operations preserve structure and that certain transformations don't affect topology.

**Properties Tested:**
- **NX import preserves nodes**: `load_network(G, input_type="nx")` preserves node set
- **NX import preserves edges**: Edge counts match after import
- **Directed flag respected**: `directed=True/False` creates appropriate graph types
- **Edgelist roundtrip**: Save → load cycle preserves structure
- **Node relabeling preserves topology**: Isomorphic graphs have same structural properties
- **Empty network handling**: Empty graphs are valid inputs
- **Non-negative counts**: All counts ≥ 0 (contract postcondition)
- **Weighted graph import**: Edge weights preserved during import

**Run:**
```bash
pytest tests/property/test_io_metamorphic_roundtrip.py -v -m property
```

#### 4. `test_isomorphism_invariance.py` - Permutation/Isomorphism Invariance

Tests that algorithms produce consistent results on isomorphic graphs (differing only in node labels).

**Properties Tested:**
- **Degree invariance**: Degree multiset identical under relabeling
- **Betweenness centrality ranking**: Sorted centrality values identical
- **Clustering coefficient invariance**: Clustering values preserved
- **Eigenvector centrality ranking**: Spearman ρ = 1 after relabeling
- **Versatility single-layer invariance**: Sorted scores identical for isomorphic graphs
- **Louvain community sizes**: Community size distributions identical
- **Shortest path lengths**: Path length distributions preserved
- **Monoplex wrapper degree**: Degree centrality via wrapper is invariant

**Run:**
```bash
pytest tests/property/test_isomorphism_invariance.py -v -m property
```

#### 5. `test_subnetwork_algebra.py` - Subnetwork Algebra & Idempotence

Tests algebraic properties of subnetwork operations.

**Properties Tested:**
- **Idempotence**: `subnetwork(subnetwork(S)) == subnetwork(S)` for layer selections
- **Union**: `subnetwork(A ∪ B)` contains `subnetwork(A)` and `subnetwork(B)`
- **Monotonicity**: `A ⊆ B` implies `subnetwork(A) ⊆ subnetwork(B)`
- **Node name preservation**: Selecting by node names preserves layer structure
- **Neighbor consistency**: `get_neighbors()` agrees with edges from `get_edges()`
- **Split idempotence**: `split_to_layers()` is stable across multiple calls
- **Subnetwork bounds**: `|nodes(subnetwork)| ≤ |nodes(original)|`

**Run:**
```bash
pytest tests/property/test_subnetwork_algebra.py -v -m property
```

#### 6. `test_multiplex_couplings.py` - Multiplex Coupling Invariants

Tests that multiplex mode correctly creates interlayer couplings.

**Properties Tested:**
- **Coupling existence**: Nodes with same name in ≥2 layers have interlayer edges
- **Coupling count**: Expected number of coupling edges for N nodes across L layers
- **Add order independence**: Couplings independent of node/edge addition order
- **Coupling weight preserved**: Coupling edges have specified `coupling_weight`
- **No self-couplings**: No coupling edges `(n, l) → (n, l)` in same layer
- **Multiplex vs multilayer**: Multiplex has ≥ edges due to couplings

**Run:**
```bash
pytest tests/property/test_multiplex_couplings.py -v -m property
```

#### 7. `test_versatility_metamorphic.py` - Versatility Spectral Metamorphics

Tests advanced properties of versatility (multilayer eigenvector centrality).

**Properties Tested:**
- **Single-layer reduction**: With L=1, ω=0, versatility matches eigenvector centrality (ρ ≥ 0.99)
- **L1 normalization**: `normalize='l1'` produces `sum(|v|) = 1`
- **L2 normalization**: `normalize='l2'` produces `||v||₂ = 1`
- **Scale invariance**: `versatility(α·A) = versatility(A)` for α > 0 (normalized)
- **Zero layer stability**: Appending all-zero layer doesn't change rankings
- **Finite values**: No NaN, no infinity in results
- **Interlayer coupling effect**: Increasing ω blends layer centralities
- **Non-negative results**: Non-negative weights → non-negative scores (Perron-Frobenius)
- **Normalization options**: All normalization modes ('l1', 'l2', 'none') produce valid results

**Run:**
```bash
pytest tests/property/test_versatility_metamorphic.py -v -m property
```

#### 8. `test_random_er_statistics.py` - Random Multilayer ER Statistics

Tests that `random_multilayer_ER` produces networks with expected statistical properties.

**Properties Tested:**
- **Edge count bounds**: Per-layer edge counts fall within binomial confidence bounds (Chebyshev)
- **Monotonicity in p**: Higher p → more edges on average
- **Node count**: N nodes per layer as expected
- **Layer count**: `split_to_layers()` produces L layers
- **Non-negative counts**: All counts ≥ 0
- **Extreme p values**: p=0 gives no edges, p=1 gives complete graphs
- **Single-layer comparison**: L=1 matches NetworkX Erdős-Rényi behavior
- **Layer independence**: Edge counts have variance consistent with independent sampling
- **Valid network**: Basic operations work on generated networks

**Run:**
```bash
pytest tests/property/test_random_er_statistics.py -v -m property -m slow
```

#### 9. `test_community_partition_invariants.py` - Community Partition Invariants

Tests properties of Louvain community detection wrapper.

**Properties Tested:**
- **Every node assigned**: `partition.keys() == G.nodes()`
- **No foreign nodes**: Partition contains only graph nodes
- **Size invariance**: Community sizes invariant under relabeling
- **Valid IDs**: Community IDs are non-negative integers
- **Component detection**: ≥K communities for K well-separated components
- **Coverage**: Union of communities == all nodes
- **At least one community**: Always ≥1 community found
- **At most n communities**: ≤n communities for n nodes
- **Wrapper consistency**: py3plex wrapper produces valid partitions
- **Determinism**: Same `random_state` produces same partition
- **Empty graph handling**: Valid behavior on graphs with no edges

**Run:**
```bash
pytest tests/property/test_community_partition_invariants.py -v -m property
```

**Note:** Requires `python-louvain` package (guarded with `pytest.importorskip`).

#### 10. `test_stateful_multinet_advanced.py` - Advanced Stateful Mutations

Uses Hypothesis `RuleBasedStateMachine` to test complex sequences of operations.

**Properties Tested via Invariants:**
- **Core network exists**: Always `None` or valid NetworkX graph
- **Non-negative counts**: Node/edge counts ≥ 0 throughout
- **Node consistency**: `get_nodes()` matches `core_network.nodes()`
- **Edge endpoint validity**: All edges have endpoints that exist as nodes
- **Undirected symmetry**: Undirected networks have symmetric adjacency

**Tested Operations:**
- Add nodes/edges via dict, list, and px_edge formats
- Load NetworkX graphs
- Subnetwork by layers
- Split to layers
- Remove nodes (consistency after removal)
- Multiple input formats equivalence
- Network type preservation

**Run:**
```bash
pytest tests/property/test_stateful_multinet_advanced.py -v -m property
```

### Shared Strategies (`strategies.py`)

Reusable Hypothesis strategies for generating test inputs:

#### Basic Primitives
- `node_names()`: Short ASCII lowercase node names
- `layer_labels()`: Short ASCII lowercase layer labels
- `finite_weights()`: Non-negative finite floats
- `positive_weights()`: Strictly positive floats

#### NetworkX Graphs
- `small_graphs()`: Small graphs (2-8 nodes) with optional connectivity
- `connected_graphs()`: Connected graphs
- `weighted_graphs()`: Graphs with random edge weights

#### Multilayer Structures
- `node_layer_tuples()`: `(node_name, layer_label)` tuples
- `layer_sets()`: Sets of layer labels
- `node_sets()`: Sets of node names
- `edge_dicts()`: Edge dictionaries for `add_edges()`
- `node_dicts()`: Node dictionaries for `add_nodes()`
- `multilayer_params()`: Parameters for random multilayer networks

#### Utilities
- `relabel_graph()`: Create isomorphic copy with permuted labels

### Running the Test Suite

#### All property tests
```bash
pytest tests/property/ -v -m property
```

#### Excluding slow tests
```bash
pytest tests/property/ -v -m "property and not slow"
```

#### Only slow tests
```bash
pytest tests/property/ -v -m "property and slow"
```

#### Specific module
```bash
pytest tests/property/test_io_metamorphic_roundtrip.py -v
```

#### With Hypothesis settings
```bash
# More examples (slower but more thorough)
pytest tests/property/ -v --hypothesis-seed=42

# Show statistics
pytest tests/property/ -v --hypothesis-show-statistics
```

#### Just the core property modules
```bash
pytest tests/property/test_centrality_invariants.py \
       tests/property/test_centrality_rankings.py \
       tests/property/test_io_metamorphic_roundtrip.py \
       tests/property/test_isomorphism_invariance.py \
       tests/property/test_subnetwork_algebra.py \
       tests/property/test_multiplex_couplings.py \
       tests/property/test_versatility_metamorphic.py \
       tests/property/test_random_er_statistics.py \
       tests/property/test_community_partition_invariants.py \
       tests/property/test_stateful_multinet_advanced.py \
       -v -m property
```

### Test Settings

Default settings (configured via `@settings` decorators):
- `deadline=None`: No per-test time limit (allows slow convergence)
- `max_examples=20-30`: Balance between thoroughness and speed
- `max_examples=20` for slow tests (marked with `@pytest.mark.slow`)
- `stateful_step_count=15`: Number of steps in stateful tests

### Invariants & Metamorphic Properties

#### Key Invariants Tested
1. **Non-negativity**: Counts, weights always ≥ 0
2. **Normalization**: L1/L2 norms equal 1 when requested
3. **Finiteness**: No NaN, no infinity in results
4. **Consistency**: Multiple access methods return same data
5. **Symmetry**: Undirected graphs have symmetric adjacency
6. **Endpoint validity**: Edges reference existing nodes

#### Key Metamorphic Relations
1. **Isomorphism**: Results invariant under node relabeling
2. **Scale**: Normalized results invariant under weight scaling
3. **Idempotence**: `f(f(x)) = f(x)` for projections
4. **Monotonicity**: `A ⊆ B ⟹ f(A) ⊆ f(B)` for subset operations
5. **Union**: `f(A ∪ B) ⊇ f(A) ∪ f(B)` for subnetworks

### Dependencies

Core requirements:
- `pytest >= 7.0`
- `hypothesis >= 6.0`
- `hypothesis-networkx >= 0.2.0` (optional, with fallback)
- `networkx >= 2.5`
- `numpy >= 1.19.0`
- `scipy >= 1.5.0`

Optional (tests guarded with `pytest.importorskip`):
- `python-louvain >= 0.16` (for community detection tests)

Install all test dependencies:
```bash
pip install -e .[tests]
```

### Contributing

When adding new features to py3plex:

1. **Add property tests** for core invariants
2. **Use shared strategies** from `strategies.py`
3. **Guard optional deps** with `pytest.importorskip()`
4. **Set appropriate timeouts** with `deadline=None` for slow convergence
5. **Mark slow tests** with `@pytest.mark.slow`
6. **Test edge cases** (empty, disconnected, single-node graphs)

### References

- [Hypothesis documentation](https://hypothesis.readthedocs.io/)
- [Property-based testing primer](https://hypothesis.works/articles/what-is-property-based-testing/)
- [Metamorphic testing](https://en.wikipedia.org/wiki/Metamorphic_testing)
- De Domenico et al. (2013, 2015): Versatility/multilayer centrality papers
