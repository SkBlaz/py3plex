# Leiden Algorithm for Multilayer Networks

## Overview

This implementation provides the **Leiden community detection algorithm** for multilayer and multiplex networks. The Leiden algorithm is an improvement over the Louvain method that guarantees well-connected communities through a refinement phase.

## Key Features

### ✅ Implemented Features

1. **Multiple Input Formats**
   - py3plex `multi_layer_network` objects
   - List of NetworkX graphs (one per layer)
   - List of adjacency matrices (NumPy arrays or SciPy sparse)

2. **Flexible Configuration**
   - **Resolution parameter (γ)**: Control community granularity
     - Single value for all layers
     - List of values (one per layer)
     - Dictionary mapping layer names to values
   - **Interlayer coupling (ω)**: Control cross-layer community consistency
     - Single value for uniform coupling
     - Matrix for layer-pair specific coupling

3. **Algorithm Features**
   - Multislice modularity optimization (Mucha et al., 2010)
   - Local move phase (like Louvain)
   - Refinement phase (key Leiden innovation)
   - Support for weighted and directed edges
   - Reproducible results with random seed

4. **Output**
   - `LeidenResult` object containing:
     - Community assignments per (node, layer) pair
     - Global multilayer modularity score
     - Per-layer modularity scores
     - Iteration count
     - Summary report method

## Usage Examples

### Basic Usage

```python
from py3plex.core import multinet
from py3plex.algorithms.community_detection import leiden_multilayer

# Create a multilayer network
network = multinet.multi_layer_network(directed=False)
network.add_edges([
    ['A', 'L1', 'B', 'L1', 1],
    ['B', 'L1', 'C', 'L1', 1],
    ['A', 'L2', 'C', 'L2', 1]
], input_type='list')

# Run Leiden algorithm
result = leiden_multilayer(
    network,
    interlayer_coupling=0.5,
    resolution=1.0,
    seed=42
)

# Print results
print(result.summary())
print(f"Communities: {result.communities}")
```

### Layer-Specific Resolution

```python
# Different resolution per layer
result = leiden_multilayer(
    network,
    interlayer_coupling=0.5,
    resolution={'L1': 1.5, 'L2': 0.8},  # Higher resolution in L1
    seed=42
)
```

### Custom Coupling Matrix

```python
import numpy as np

# Custom coupling between layers
coupling_matrix = np.array([
    [0.0, 1.0, 0.5],  # L1 coupling
    [1.0, 0.0, 0.3],  # L2 coupling
    [0.5, 0.3, 0.0]   # L3 coupling
])

result = leiden_multilayer(
    network,
    interlayer_coupling=coupling_matrix,
    resolution=1.0,
    seed=42
)
```

## Algorithm Details

### Multislice Modularity

The algorithm maximizes the multilayer modularity quality function:

```
Q = (1/2μ) Σ_{ijsr} [(A_{ijs} - γ_s k_{is}k_{js}/2m_s) δ_{sr} + δ_{ij} C_{jsr}] δ(g_{is}, g_{jr})
```

Where:
- `A_{ijs}` = adjacency matrix of layer s
- `γ_s` = resolution parameter for layer s
- `k_{is}` = degree of node i in layer s
- `m_s` = total edge weight in layer s
- `C_{jsr}` = interlayer coupling between layers s and r
- `δ` = Kronecker delta
- `μ` = total edge weight in supra-network

### Leiden vs. Louvain

| Feature | Louvain | Leiden |
|---------|---------|--------|
| Local move phase | ✅ | ✅ |
| Refinement phase | ❌ | ✅ |
| Guarantees well-connected communities | ❌ | ✅ |
| Computational complexity | O(n log n) | O(n log n) |

The refinement phase ensures that communities remain well-connected by:
1. Creating subcommunities within each community
2. Optimally merging subcommunities
3. Preventing poorly connected communities

## Performance Considerations

### Complexity

- **Time**: O(n × L × d × k) per iteration
  - n = nodes per layer
  - L = number of layers
  - d = average degree
  - k = number of communities
- **Space**: O((n×L)²) for supra-adjacency matrix

### Optimization Tips

1. **Use sparse matrices** for large networks (handled automatically)
2. **Set max_iter** appropriately (default: 100)
3. **Use seed** for reproducible results
4. **Consider layer-specific resolution** for heterogeneous networks

## Testing

Run the test suite:

```bash
python -m unittest tests/test_leiden_multilayer.py
```

Run the examples:

```bash
python examples/community_detection/example_leiden_multilayer.py
```

## API Reference

### `leiden_multilayer()`

**Parameters:**
- `graph_layers`: Network input (py3plex network, list of graphs, or list of matrices)
- `interlayer_coupling`: Coupling strength (float or matrix), default: 1.0
- `resolution`: Resolution parameter (float, list, or dict), default: 1.0
- `seed`: Random seed for reproducibility, default: None
- `max_iter`: Maximum iterations, default: 100
- `parallel`: Enable parallelization (reserved for future), default: False
- `weight`: Edge weight attribute name, default: "weight"

**Returns:**
- `LeidenResult` object with communities, modularity, and metadata

### `LeidenResult`

**Attributes:**
- `communities`: Dict mapping (node, layer) → community_id
- `modularity`: Global modularity score
- `layer_modularity`: Dict mapping layer → modularity
- `iterations`: Number of iterations
- `improved`: Whether last phase improved partition

**Methods:**
- `summary()`: Generate text summary of results

## Future Extensions

The following features are planned for future releases:

### 🚧 Not Yet Implemented

1. **Temporal Leiden**: Support for evolving/dynamic networks
2. **GPU Acceleration**: CuGraph integration for large-scale networks
3. **Parallel Processing**: Multi-core optimization (joblib/multiprocessing)
4. **Community Tracking**: NMI and other metrics across layers
5. **Integration with Embeddings**: Graph2Vec, Node2Vec compatibility
6. **Hierarchical Leiden**: Multi-resolution community detection
7. **Additional Input Formats**: Direct support for:
   - Single supra-adjacency matrix with layer structure
   - NetworkX MultiGraph objects
   - Edge list files

## References

1. **Leiden Algorithm**:
   Traag, V. A., Waltman, L., & Van Eck, N. J. (2019). 
   "From Louvain to Leiden: guaranteeing well-connected communities." 
   Scientific Reports, 9(1), 5233.

2. **Multilayer Modularity**:
   Mucha, P. J., Richardson, T., Macon, K., Porter, M. A., & Onnela, J. P. (2010). 
   "Community structure in time-dependent, multiscale, and multiplex networks." 
   Science, 328(5980), 876-878.

3. **Louvain Algorithm**:
   Blondel, V. D., Guillaume, J. L., Lambiotte, R., & Lefebvre, E. (2008). 
   "Fast unfolding of communities in large networks." 
   Journal of Statistical Mechanics: Theory and Experiment, 2008(10), P10008.

## License

This implementation is part of the py3plex library and follows the same license (MIT).

## Contributing

Contributions are welcome! Please submit issues and pull requests to the py3plex repository.
