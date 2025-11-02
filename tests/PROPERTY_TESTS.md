# Advanced Property-Based Tests for py3plex

This document describes the comprehensive Hypothesis property-based test suite for py3plex's core multilayer network functionality.

## Overview

These tests use **property-based testing** with [Hypothesis](https://hypothesis.readthedocs.io/) to verify mathematical invariants and contracts across a wide range of generated inputs. This approach uncovers edge cases that manual testing might miss.

## Test Modules

### 1. `test_centrality_invariants.py` - Centrality Metric Invariants (NEW)

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

### 2. `test_centrality_rankings.py` - Centrality Rankings & Metamorphic Relations (NEW)

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

### 3. `test_io_metamorphic_roundtrip.py` - I/O Metamorphic Properties

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

### 4. `test_isomorphism_invariance.py` - Permutation/Isomorphism Invariance

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

### 5. `test_subnetwork_algebra.py` - Subnetwork Algebra & Idempotence

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

### 6. `test_multiplex_couplings.py` - Multiplex Coupling Invariants

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

### 7. `test_versatility_metamorphic.py` - Versatility Spectral Metamorphics

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

### 8. `test_random_er_statistics.py` - Random Multilayer ER Statistics

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

### 9. `test_community_partition_invariants.py` - Community Partition Invariants

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

### 10. `test_stateful_multinet_advanced.py` - Advanced Stateful Mutations

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

## Shared Strategies (`strategies.py`)

Reusable Hypothesis strategies for generating test inputs:

### Basic Primitives
- `node_names()`: Short ASCII lowercase node names
- `layer_labels()`: Short ASCII lowercase layer labels
- `finite_weights()`: Non-negative finite floats
- `positive_weights()`: Strictly positive floats

### NetworkX Graphs
- `small_graphs()`: Small graphs (2-8 nodes) with optional connectivity
- `connected_graphs()`: Connected graphs
- `weighted_graphs()`: Graphs with random edge weights

### Multilayer Structures
- `node_layer_tuples()`: `(node_name, layer_label)` tuples
- `layer_sets()`: Sets of layer labels
- `node_sets()`: Sets of node names
- `edge_dicts()`: Edge dictionaries for `add_edges()`
- `node_dicts()`: Node dictionaries for `add_nodes()`
- `multilayer_params()`: Parameters for random multilayer networks

### Utilities
- `relabel_graph()`: Create isomorphic copy with permuted labels

## Running the Test Suite

### All property tests
```bash
pytest tests/property/ -v -m property
```

### Excluding slow tests
```bash
pytest tests/property/ -v -m "property and not slow"
```

### Only slow tests
```bash
pytest tests/property/ -v -m "property and slow"
```

### Specific module
```bash
pytest tests/property/test_io_metamorphic_roundtrip.py -v
```

### With Hypothesis settings
```bash
# More examples (slower but more thorough)
pytest tests/property/ -v --hypothesis-seed=42

# Show statistics
pytest tests/property/ -v --hypothesis-show-statistics
```

### Just the core property modules
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

## Test Settings

Default settings (configured via `@settings` decorators):
- `deadline=None`: No per-test time limit (allows slow convergence)
- `max_examples=20-30`: Balance between thoroughness and speed
- `max_examples=20` for slow tests (marked with `@pytest.mark.slow`)
- `stateful_step_count=15`: Number of steps in stateful tests

## Invariants & Metamorphic Properties

### Key Invariants Tested
1. **Non-negativity**: Counts, weights always ≥ 0
2. **Normalization**: L1/L2 norms equal 1 when requested
3. **Finiteness**: No NaN, no infinity in results
4. **Consistency**: Multiple access methods return same data
5. **Symmetry**: Undirected graphs have symmetric adjacency
6. **Endpoint validity**: Edges reference existing nodes

### Key Metamorphic Relations
1. **Isomorphism**: Results invariant under node relabeling
2. **Scale**: Normalized results invariant under weight scaling
3. **Idempotence**: `f(f(x)) = f(x)` for projections
4. **Monotonicity**: `A ⊆ B ⟹ f(A) ⊆ f(B)` for subset operations
5. **Union**: `f(A ∪ B) ⊇ f(A) ∪ f(B)` for subnetworks

## Dependencies

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

## Contributing

When adding new features to py3plex:

1. **Add property tests** for core invariants
2. **Use shared strategies** from `strategies.py`
3. **Guard optional deps** with `pytest.importorskip()`
4. **Set appropriate timeouts** with `deadline=None` for slow convergence
5. **Mark slow tests** with `@pytest.mark.slow`
6. **Test edge cases** (empty, disconnected, single-node graphs)

## References

- [Hypothesis documentation](https://hypothesis.readthedocs.io/)
- [Property-based testing primer](https://hypothesis.works/articles/what-is-property-based-testing/)
- [Metamorphic testing](https://en.wikipedia.org/wiki/Metamorphic_testing)
- De Domenico et al. (2013, 2015): Versatility/multilayer centrality papers
- Issue: https://github.com/SkBlaz/py3plex/issues/[TBD]
