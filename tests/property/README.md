# Property-Based Tests for py3plex

This directory contains property-based tests using [Hypothesis](https://hypothesis.readthedocs.io/), a framework for property-based testing that generates diverse test inputs to validate invariants and contracts.

## Overview

Property-based tests verify that code satisfies mathematical properties and invariants across a wide range of inputs, rather than testing specific hand-written examples. This approach is particularly valuable for multilayer network algorithms where edge cases and boundary conditions can be subtle.

**Total: 125+ property-based tests**

## Test Modules

### Core Operations Tests (NEW)

#### `test_edge_operations_properties.py` (9 tests)
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

#### `test_node_operations_properties.py` (10 tests)
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

#### `test_weight_operations_properties.py` (10 tests)
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

#### `test_graph_transformation_properties.py` (11 tests)
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

### Advanced Tests

### `test_io_roundtrip.py`
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

### `test_versatility_properties.py`
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

### Other Test Modules

- `test_statistics_properties.py`: Layer density bounds (needs multilayer format fixes)
- `test_communities_properties.py`: Louvain community detection (needs python-louvain package)
- `test_random_generators_properties.py`: Random graph generators (needs parameter updates)

## CrossHair Contracts

The code includes assertions that can be analyzed by [CrossHair](https://github.com/pschanely/CrossHair), a tool that uses symbolic execution to find counterexamples to contracts.

### In `py3plex/core/multinet.py`

**`load_network()` contracts:**
- **Precondition**: `input_type` must be in supported set
- **Precondition**: `input_file` required for non-NetworkX inputs
- **Postcondition**: `core_network` is initialized with non-negative node/edge counts
- **Postcondition**: When `directed=False`, graph is undirected

### In `py3plex/algorithms/multilayer_algorithms/versatility.py`

**`versatility()` contracts:**
- **Precondition**: At least one layer required
- **Precondition**: All layers must be square and same size
- **Precondition**: `interlayer >= 0` for scalar coupling
- **Postcondition**: Result is numpy array of shape `(N,)`
- **Postcondition**: All values are finite
- **Postcondition**: L1/L2 normalization produces unit sum/norm

## Running Tests

### Run all property tests
```bash
pytest tests/property/ -v -m property
```

### Run specific test suites
```bash
# I/O tests only
pytest tests/property/test_io_roundtrip.py -v

# Versatility tests only  
pytest tests/property/test_versatility_properties.py -v
```

### Run with Hypothesis settings
```bash
# More examples (slower but more thorough)
pytest tests/property/ -v --hypothesis-seed=42

# Show statistics
pytest tests/property/ -v --hypothesis-show-statistics
```

## CrossHair Analysis

To analyze contracts with CrossHair (when available):

```bash
# Check contracts in core module
crosshair check py3plex/core/multinet.py --analysis_kind=asserts --per_condition_timeout=3

# Check contracts in versatility
crosshair check py3plex/algorithms/multilayer_algorithms/versatility.py --analysis_kind=asserts --per_condition_timeout=3
```

Note: CrossHair analysis works best on pure functions without external I/O.

## Contributing

When adding new functionality to py3plex:

1. **Add property tests** for core invariants (normalization, bounds, symmetries)
2. **Add contracts** using assert statements with `# crosshair: analysis_kind=asserts` comment
3. **Use hypothesis strategies** to generate diverse inputs
4. **Test edge cases** explicitly (empty graphs, single nodes, disconnected components)

### Property Test Template

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

### Writing Good Property Tests

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

### Common Patterns

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

## Test Organization

Property tests are organized by category:

- **`test_io_*.py`**: Input/output and serialization properties
- **`test_*_properties.py`**: Algorithm-specific properties
- **`test_stateful_*.py`**: Stateful testing with complex operation sequences
- **`test_*_invariants.py`**: Invariant checks across operations
- **`test_*_metamorphic.py`**: Metamorphic relations
- **`test_network_transformations.py`**: Graph transformation properties

## Performance Considerations

- Use `small_graphs` with `max_nodes ≤ 10` for fast tests
- Increase `max_examples` for fast, simple tests
- Decrease `max_examples` for slow, complex tests  
- Use `@settings(deadline=None)` to disable timeouts for slow operations
- Use `assume()` sparingly - excessive filtering slows tests

## References

- [Hypothesis documentation](https://hypothesis.readthedocs.io/)
- [Property-based testing primer](https://hypothesis.works/articles/what-is-property-based-testing/)
- [CrossHair documentation](https://github.com/pschanely/CrossHair)
- [Choosing properties for property-based testing](https://fsharpforfunandprofit.com/posts/property-based-testing-2/)
