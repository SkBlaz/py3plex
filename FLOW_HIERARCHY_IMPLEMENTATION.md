# Hierarchical Flow-Based Community Detection (HFCD) Implementation

## Overview

This document describes the implementation of a native hierarchical flow-based community detection algorithm in py3plex. The algorithm is **algorithm-first**, **scalable**, **multilayer-aware**, and **parameter-light**.

## Mathematical Foundation

### Flow Operator

For a multilayer graph, the algorithm constructs a transition operator P:

```
P = α P_intra + (1-α) P_inter
```

Where:
- `P_intra`: degree-normalized random walk within layers
- `P_inter`: interlayer coupling (identity-based)
- `α ∈ [0,1]`: interlayer coupling strength

### Flow Affinity

For diffusion time scale t:

```
F(t) = Σ_{k=1}^{t} P^k
```

Define symmetric flow similarity:

```
S_ij(t) = (F_ij(t) + F_ji(t)) / 2
```

### Flow Retention (Quality Metric)

For candidate community C at scale t:

```
FlowRetention(C, t) = (internal_flow) / (total_flow)
```

Communities maximize flow retention (probability mass trapped internally), not modularity.

### Hierarchy Emergence

As diffusion time t increases, flow spreads further, causing communities to merge naturally. Hierarchy levels correspond to stability plateaus in flow retention.

## Algorithm

1. **Initialize**: Each node is its own community
2. **For each scale t in schedule**:
   - Estimate flow affinities S(t) using Monte Carlo or exact method
   - Compute inter-community flow retention scores
   - Agglomeratively merge communities maximizing flow retention increase
   - Record merge events and stability
3. **Extract hierarchy**: Build dendrogram, identify stability plateaus

## Implementation Details

### File Structure

- **Core Algorithm**: `py3plex/algorithms/community_detection/flow_hierarchy.py` (750 LOC)
- **Tests**: `tests/test_flow_hierarchy.py` (28 comprehensive tests)
- **Examples**: 
  - `examples/flow_hierarchy_basic.py` (basic usage)
  - `examples/flow_hierarchy_multilayer.py` (multilayer with alpha variations)

### Key Classes and Functions

#### `FlowHierarchyResult`

Container for results with:
- `dendrogram`: List of merge events
- `hierarchy_levels`: Community assignments at each detected level
- `stability_scores`: Flow retention scores at each scale
- `merge_scales`: Scales at which merges occurred
- `metadata`: Algorithm configuration and runtime info
- `layer_stability`: Optional per-layer stability (multilayer)

Methods:
- `get_partition(scale=None)`: Get communities at specific scale
- `get_flat_partition(n_communities=None)`: Cut dendrogram for n communities
- `summary()`: Generate human-readable summary

#### `flow_hierarchical_communities()`

Main entry point with parameters:
- `network`: multi_layer_network instance
- `flow_type`: Type of flow dynamics (default: "random_walk")
- `scales`: Custom scale schedule (default: logarithmic)
- `multilayer`: Use multilayer formulation (default: True)
- `alpha`: Intralayer coupling strength (default: 0.8)
- `approx`: Approximation method - "mc" or "exact" (default: "mc")
- `n_walks`: Random walks per node for MC (default: 100)
- `max_scales`: Computational budget limit (optional)
- `seed`: Random seed for reproducibility (default: 42)

### Approximation Methods

#### Monte Carlo (approx="mc")
- **Memory**: O(n × walks) - memory-efficient
- **Speed**: Fast for large networks
- **Determinism**: Stochastic but reproducible with seed
- **Implementation**: Row-wise sparse sampling to avoid O(n²) memory

#### Exact (approx="exact")
- **Memory**: O(n²) - memory-intensive
- **Speed**: Slower for large networks
- **Determinism**: Fully deterministic
- **Implementation**: Direct matrix powers with memory warning

### Optimizations

1. **Row-wise Sparse Sampling**: Monte Carlo implementation uses sparse matrix rows directly, avoiding full matrix densification
2. **Matrix Symmetry**: Flow retention computation leverages symmetry to halve operations
3. **Configurable Memory Threshold**: `MAX_NODES_EXACT_MEMORY_WARNING` constant (default: 1000)
4. **Efficient Community Tracking**: Uses defaultdict for O(1) membership lookups

## Usage Examples

### Basic Usage

```python
from py3plex.core import multinet
from py3plex.algorithms.community_detection import flow_hierarchical_communities

# Create network
net = multinet.multi_layer_network(directed=False)
net.add_edges([
    ["A", "L1", "B", "L1", 1.0],
    ["B", "L1", "C", "L1", 1.0],
    ["C", "L1", "D", "L1", 1.0],
], input_type="list")

# Run detection
result = flow_hierarchical_communities(net, seed=42)

# Get best partition
partition = result.get_partition()
print(result.summary())
```

### Multilayer with Alpha Variations

```python
# High alpha (layer-independent)
result_high = flow_hierarchical_communities(net, alpha=0.9, seed=42)

# Low alpha (strong interlayer coupling)
result_low = flow_hierarchical_communities(net, alpha=0.2, seed=42)

# Compare number of communities
n_comms_high = len(set(result_high.get_partition().values()))
n_comms_low = len(set(result_low.get_partition().values()))
```

### Custom Scale Schedule

```python
# Use specific scales
result = flow_hierarchical_communities(
    net,
    scales=[1, 2, 4, 8, 16],
    approx="mc",
    n_walks=200,
    seed=42
)
```

## Testing

### Test Coverage

28 tests covering:
1. **Basic functionality**: Simple chains, cliques, trees
2. **Determinism**: Fixed seed reproducibility
3. **Multilayer**: Various coupling scenarios
4. **Parameter validation**: Invalid inputs rejected
5. **Edge cases**: Single node, disconnected components, empty networks
6. **Approximation methods**: Both MC and exact
7. **Hierarchy detection**: Plateau identification
8. **Result methods**: Convenience functions
9. **Integration**: Compatibility with other algorithms
10. **Properties**: Partition coverage, monotonic merging, non-negative stability

### Running Tests

```bash
# All tests
pytest tests/test_flow_hierarchy.py -v

# Specific test
pytest tests/test_flow_hierarchy.py::test_flow_hierarchy_simple_chain -v

# With coverage
pytest tests/test_flow_hierarchy.py --cov=py3plex.algorithms.community_detection.flow_hierarchy
```

## Performance Characteristics

### Time Complexity

O(t × m × k) where:
- t: maximum diffusion time scale
- m: number of edges
- k: number of merge iterations (typically O(n))

### Space Complexity

- **Monte Carlo**: O(n × walks) for flow accumulation
- **Exact**: O(n²) for transition matrix powers

### Recommended Limits

- **Exact mode**: n < 10,000 nodes
- **MC mode**: n < 100,000 nodes
- **n_walks**: 50-500 (higher reduces variance)

## Comparison with Other Algorithms

### vs. Louvain/Leiden
- **Quality metric**: Flow retention vs. modularity
- **Hierarchy**: Full dendrogram vs. flat partition
- **Scale**: Natural vs. resolution parameter
- **Determinism**: Seed-controlled vs. heuristic

### vs. Infomap
- **Foundation**: Random walk flow vs. information compression
- **Hierarchy**: Stability-based vs. code length
- **Multilayer**: Native support vs. limited

### vs. Markov Stability
- **Implementation**: Native py3plex vs. external dependency
- **Approximation**: MC + exact vs. typically exact
- **Integration**: First-class API vs. wrapper

## Limitations and Future Work

### Current Limitations

1. **Single quality metric**: Only flow retention implemented
2. **Scale schedule**: Logarithmic by default, no adaptive selection
3. **Interlayer coupling**: Identity-based, not learned
4. **Per-layer stability**: Metadata structure present but not computed

### Future Enhancements

1. **Learned coupling**: Optimize α per layer or node
2. **Analytical approximations**: Krylov/Lanczos methods
3. **AutoCommunity integration**: Add as hierarchical candidate
4. **Uncertainty estimation**: Bootstrap flow perturbations
5. **GPU acceleration**: CUDA-based random walk sampling

## References

1. Schaub et al., "Markov Dynamics as a Zooming Lens for Multiscale Community Detection", PLoS ONE 7(2): e32210 (2012)
2. Delvenne et al., "Stability of graph communities across time scales", PNAS 107(29): 12755-12760 (2010)
3. Lambiotte et al., "Random Walks, Markov Processes and the Multiscale Modular Organization of Complex Networks", IEEE Trans. Network Science and Engineering 1(2): 76-90 (2014)

## Contributing

When extending this algorithm:

1. **Add tests**: Cover new functionality in `tests/test_flow_hierarchy.py`
2. **Update docstrings**: Follow existing Google-style format
3. **Optimize**: Consider memory and time complexity
4. **Document**: Update this file with new features
5. **Validate**: Run full test suite before submitting

## License

This implementation is part of py3plex and follows the project's license.

---

**Implementation Date**: 2024
**Version**: 1.0.0
**Status**: Production-ready ✅
