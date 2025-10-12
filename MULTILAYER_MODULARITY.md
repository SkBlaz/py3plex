# Multilayer Modularity Implementation

This document describes the multilayer modularity maximization implementation added to py3plex.

## Overview

This implementation adds comprehensive support for multilayer community detection based on **Mucha et al. (2010)**'s multilayer modularity framework. The implementation includes:

1. **Multilayer Modularity Calculation** - Quality function for evaluating community partitions
2. **Community Detection Algorithms** - Generalized Louvain algorithm for multilayer networks
3. **Synthetic Benchmark Generators** - Tools for creating test networks with ground-truth communities

## Features

### Multilayer Modularity (`multilayer_modularity.py`)

#### Core Functions

**`multilayer_modularity(network, communities, gamma, omega, weight)`**
- Calculates the multilayer modularity quality function
- Supports layer-specific resolution parameters (γ)
- Supports inter-layer coupling strengths (ω)
- Returns modularity value Q ∈ [-1, 1]

**`build_supra_modularity_matrix(network, gamma, omega, weight)`**
- Constructs the supra-modularity matrix for spectral methods
- Returns (N×L) × (N×L) matrix where N=nodes, L=layers
- Useful for eigendecomposition and spectral clustering

**`louvain_multilayer(network, gamma, omega, weight, max_iter, random_state)`**
- Generalized Louvain algorithm for multilayer networks
- Greedily maximizes multilayer modularity
- Returns community assignments for all (node, layer) pairs

#### Key Parameters

- **gamma (γ)**: Resolution parameter controlling community size
  - Can be single float (uniform) or dict of layer-specific values
  - Higher values → smaller communities
  - Lower values → larger communities

- **omega (ω)**: Inter-layer coupling strength
  - Can be single float (uniform) or matrix of layer-pair values
  - ω = 0: Independent layers (no coupling)
  - ω → ∞: Same communities across all layers
  - Typical range: [0.1, 10]

### Multilayer Benchmarks (`multilayer_benchmark.py`)

#### Synthetic Network Generators

**`generate_multilayer_lfr(...)`**
- Multilayer extension of Lancichinetti-Fortunato-Radicchi benchmark
- Features:
  - Power-law degree and community size distributions
  - Controllable mixing parameter (μ) for intra/inter-community edges
  - Community persistence across layers
  - Node overlap (partial node presence in layers)
  - Overlapping communities (nodes in multiple communities)
- Returns: (network, ground_truth_communities)

**`generate_coupled_er_multilayer(...)`**
- Coupled/interdependent Erdős-Rényi random graphs
- Features:
  - Layer-specific edge probabilities
  - Controllable inter-layer coupling
  - Partial coupling (interdependent networks)
- Useful for null model testing and baseline comparisons
- Returns: network

**`generate_sbm_multilayer(...)`**
- Multilayer stochastic block model
- Features:
  - Explicit block structure with intra/inter-block edge probabilities
  - Community persistence across layers
  - Clean ground-truth communities
- Returns: (network, ground_truth_communities)

## Mathematical Background

### Multilayer Modularity Formula

The multilayer modularity quality function is:

```
Q = (1/2μ) Σ_{ijαβ} [(A^[α]_ij - γ^[α]P^[α]_ij)δ_αβ + δ_ij ω_αβ] δ(g_iα, g_jβ)
```

Where:
- `A^[α]_ij`: Adjacency matrix of layer α
- `P^[α]_ij`: Null model (typically k_i^α k_j^α / 2m_α)
- `γ^[α]`: Resolution parameter for layer α
- `ω_αβ`: Inter-layer coupling strength
- `δ_αβ`: Kronecker delta (1 if α=β, else 0)
- `δ_ij`: Kronecker delta (1 if i=j, else 0)
- `δ(g_iα, g_jβ)`: 1 if same community, else 0
- `μ`: Total edge weight in supra-network

### Supra-Adjacency Matrix

The multilayer network is represented as a block matrix:

```
┌─────────────────────────┐
│ A^[1]  ωI     ...  ωI  │
│  ωI   A^[2]   ...  ωI  │
│  ...   ...   ...   ... │
│  ωI    ωI    ... A^[L] │
└─────────────────────────┘
```

Where:
- Diagonal blocks: Intra-layer adjacency matrices
- Off-diagonal blocks: Inter-layer coupling (ωI for identity coupling)

## Usage Examples

### Basic Modularity Calculation

```python
from py3plex.core import multinet
from py3plex.algorithms.community_detection.multilayer_modularity import multilayer_modularity

# Create network
network = multinet.multi_layer_network(directed=False)
network.add_edges([
    ['A', 'L1', 'B', 'L1', 1],
    ['B', 'L1', 'C', 'L1', 1],
    ['A', 'L2', 'C', 'L2', 1]
], input_type='list')

# Define communities
communities = {
    ('A', 'L1'): 0, ('B', 'L1'): 0, ('C', 'L1'): 1,
    ('A', 'L2'): 0, ('C', 'L2'): 0
}

# Calculate modularity
Q = multilayer_modularity(network, communities, gamma=1.0, omega=1.0)
print(f"Modularity: {Q:.3f}")
```

### Community Detection

```python
from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer

# Detect communities
communities = louvain_multilayer(
    network, 
    gamma=1.0, 
    omega=1.0,
    max_iter=100,
    random_state=42
)

# Show results
for (node, layer), com_id in communities.items():
    print(f"Node {node} in layer {layer}: Community {com_id}")
```

### Synthetic Benchmarks

```python
from py3plex.algorithms.community_detection.multilayer_benchmark import generate_multilayer_lfr

# Generate with ground-truth communities
network, ground_truth = generate_multilayer_lfr(
    n=100,
    layers=['L1', 'L2', 'L3'],
    mu=0.1,                    # 10% external edges
    avg_degree=10,
    community_persistence=0.8,  # 80% nodes keep community
    seed=42
)

# Detect and compare
detected = louvain_multilayer(network, gamma=1.0, omega=1.0)
# ... compare detected vs ground_truth ...
```

## Implementation Details

### Algorithm Complexity

**Multilayer Modularity Calculation:**
- Time: O((NL)²) where N=nodes, L=layers
- Space: O((NL)²) for supra-adjacency matrix

**Louvain Algorithm:**
- Time: O(k × (NL)²) where k=iterations (typically small)
- Space: O((NL)²)

**LFR Generation:**
- Time: O(N × avg_degree × L)
- Space: O(N × L + edges)

### Design Decisions

1. **Sparse Matrix Support**: Uses scipy.sparse when available for memory efficiency

2. **Flexible Parameters**: 
   - Single values → uniform across layers
   - Dicts/arrays → layer-specific values

3. **Community Format**: Uses (node, layer) tuples as keys for clarity

4. **Null Model**: Newman-Girvan null model (configuration model)

5. **Louvain Optimization**: Simplified implementation for clarity (not full GenLouvain optimization)

## Testing

The implementation includes comprehensive tests in `tests/test_multilayer_modularity.py`:

- **Modularity calculation tests**: Verify bounds, parameters, edge cases
- **Louvain algorithm tests**: Community detection, convergence, coupling effects
- **Benchmark generation tests**: Network properties, ground-truth validity
- **Mathematical consistency tests**: Modularity bounds, parameter effects

Run tests with:
```bash
python -m pytest tests/test_multilayer_modularity.py -v
```

Or with the project test runner:
```bash
python run_tests.py
```

## Documentation

Comprehensive documentation is available in:
- **Tutorial**: `docs/multilayer_modularity_tutorial.md` - Complete usage guide
- **Examples**: `examples/example_multilayer_modularity.py` - Working code examples
- **Docstrings**: All functions have detailed docstrings with examples

## Limitations and Future Work

### Current Limitations

1. **Louvain Implementation**: Simplified version, not as optimized as GenLouvain MATLAB code
   - Could benefit from multi-pass optimization
   - No tie-breaking strategies
   - Could be parallelized

2. **LFR Generator**: Simplified compared to original LFR
   - Approximate power-law distributions
   - Simplified community structure generation

3. **Memory**: Stores full supra-adjacency matrix
   - Could use sparse representations throughout
   - Block-diagonal structure could be exploited

### Future Enhancements

1. **Algorithms**:
   - Multi-resolution community detection
   - Consensus clustering across multiple runs
   - Label propagation for multilayer networks
   - Infomap for multilayer networks

2. **Benchmarks**:
   - More sophisticated mLFR with exact power laws
   - Temporal dynamics (community birth/death/merge/split)
   - Hierarchical community structure
   - More realistic inter-layer coupling models

3. **Metrics**:
   - Normalized Mutual Information for comparing partitions
   - Variation of Information
   - Adjusted Rand Index
   - Multilayer-specific quality measures

4. **Optimization**:
   - Parallel Louvain implementation
   - GPU acceleration for large networks
   - Incremental updates for dynamic networks

## References

1. **Mucha, P. J., et al.** (2010). "Community Structure in Time-Dependent, Multiscale, and Multiplex Networks." *Science* 328(5980): 876-878.
   - Original multilayer modularity formulation

2. **Jeub, L. G. S., et al.** (2011-2019). "GenLouvain: A Generalized Louvain Method for Community Detection."
   - MATLAB implementation of generalized Louvain

3. **Kivelä, M., et al.** (2014). "Multilayer networks." *Journal of Complex Networks* 2(3): 203-271.
   - Comprehensive review of multilayer network methods

4. **Lancichinetti, A., et al.** (2008). "Benchmark graphs for testing community detection algorithms." *Physical Review E* 78(4): 046110.
   - Original LFR benchmark

5. **Granell, C., et al.** (2015). "Benchmark model to assess community structure in evolving networks." *Physical Review E* 92(1): 012805.
   - Temporal network benchmarks

6. **Pamfil, A. R., et al.** (2019). "Relating modularity maximization and stochastic block models in multilayer networks." *SIAM Journal on Mathematics of Data Science* 1(4): 667-698.
   - Theoretical foundations for parameter selection

## License

This implementation is part of py3plex and follows the same license as the main project.

## Acknowledgments

Implementation based on the multilayer modularity framework by Mucha et al. (2010) and the GenLouvain MATLAB code by Jeub et al.
