# Py3plex Centrality API Overview

This document provides a quick reference for multilayer centrality APIs in py3plex.

## Quick Start

### Basic Centrality Computation

```python
from py3plex.core import multinet
from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality, compute_all_centralities

# Create a multilayer network
network = multinet.multi_layer_network(directed=False)
network.add_edges([
    ['A', 'L1', 'B', 'L1', 1],
    ['B', 'L1', 'C', 'L1', 1],
    ['A', 'L2', 'C', 'L2', 2],
], input_type='list')

# Compute specific centrality measures
calc = MultilayerCentrality(network)
degree = calc.layer_degree_centrality(weighted=False)
closeness = calc.multilayer_closeness_centrality(wf_improved=True)
betweenness = calc.multilayer_betweenness_centrality(normalized=True)

# Compute all centralities at once (fast measures only by default)
all_centralities = compute_all_centralities(
    network,
    include_path_based=False,  # Skip expensive betweenness/closeness
    include_advanced=False,     # Skip expensive HITS/communicability
    wf_improved=True           # Use Wasserman-Faust scaling for closeness
)
```

### Versatility (Multilayer Eigenvector Centrality)

```python
import scipy.sparse as sp
from py3plex.algorithms.multilayer_algorithms.versatility import (
    versatility,
    versatility_katz,
    build_supra_adjacency
)

# Create layer adjacency matrices
L1 = sp.csr_matrix([[0, 1, 1], [1, 0, 1], [1, 1, 0]])  # Triangle
L2 = sp.csr_matrix([[0, 1, 0], [1, 0, 1], [0, 1, 0]])  # Path

# Compute versatility with interlayer coupling omega=0.1
v = versatility([L1, L2], interlayer=0.1, normalize="l1", seed=42)

# For reducible graphs, use Katz-based versatility
v_katz = versatility_katz([L1, L2], interlayer=0.1, alpha=None)
```

### Meta Flow Report (All-in-One Analysis)

```python
from py3plex.algorithms.meta_flow_report import run_meta_analysis

# Fast analysis (degree + eigenvector centralities only)
results = run_meta_analysis(
    network,
    include_centralities=True,
    include_path_based=False,  # Skip expensive measures
    include_advanced=False,
    wf_improved=True
)

# Full analysis (includes all measures - SLOW for large networks)
results_full = run_meta_analysis(
    network,
    include_centralities=True,
    include_path_based=True,   # Include betweenness/closeness
    include_advanced=True,      # Include HITS/communicability/k-core
    wf_improved=True
)
```

## Available Centrality Measures

### Always Available (Fast)

#### Degree-based measures:
- `layer_degree_centrality()` - Per-layer degree or strength
- `supra_degree_centrality()` - Degree on supra-graph (node-layer pairs)
- `overlapping_degree_centrality()` - Sum of degrees across layers (node-level)
- `participation_coefficient()` - How evenly degree is distributed across layers

#### Eigenvector-based measures:
- `multiplex_eigenvector_centrality()` - Eigenvector centrality on supra-graph
- `multiplex_eigenvector_versatility()` - Node-level aggregation of eigenvector centrality
- `katz_bonacich_centrality()` - Katz centrality with damping parameter α
- `pagerank_centrality()` - PageRank on supra-graph

### Optional (Computationally Expensive)

#### Path-based measures (`include_path_based=True`):
- `multilayer_closeness_centrality()` - Closeness on supra-graph (O(n³))
- `multilayer_betweenness_centrality()` - Betweenness on supra-graph (O(n³))

#### Advanced measures (`include_advanced=True`):
- `hits_centrality()` - HITS hubs and authorities
- `current_flow_closeness_centrality()` - Current-flow closeness (resistance distance)
- `current_flow_betweenness_centrality()` - Current-flow betweenness
- `subgraph_centrality()` - Matrix exponential diagonal (closed walks)
- `total_communicability()` - Matrix exponential row sum
- `multiplex_k_core()` - K-core decomposition

## Key Parameters

### Weight Handling

For path-based centralities (betweenness, closeness):
- Edge weights are converted to distances: `distance = 1/weight`
- Weights must be positive (> 0)
- Use `weighted=False` for unweighted analysis

### Wasserman-Faust Improved Scaling (`wf_improved`)

Controls closeness centrality behavior in disconnected graphs:
- `wf_improved=True` (default): Normalizes by reachable nodes only
- `wf_improved=False`: Unreachable nodes contribute infinite distance
- Affects magnitude and ordering of scores

### Interlayer Coupling (`omega`)

For versatility and supra-matrix functions:
- Higher omega = stronger layer coupling
- omega → 0: Layers are independent
- omega → ∞: Layers collapse into single aggregate
- Typical range: 0.01 to 10

## Import Paths

```python
# Main centrality class and compute_all function
from py3plex.algorithms.multilayer_algorithms.centrality import (
    MultilayerCentrality,
    compute_all_centralities
)

# Versatility functions
from py3plex.algorithms.multilayer_algorithms.versatility import (
    versatility,
    versatility_katz,
    build_supra_adjacency
)

# Supra-matrix function centralities
from py3plex.algorithms.multilayer_algorithms.supra_matrix_function_centrality import (
    communicability_centrality,
    katz_centrality
)

# Meta flow report (all-in-one analysis)
from py3plex.algorithms.meta_flow_report import (
    MetaFlowReport,
    run_meta_analysis
)

# Or via top-level algorithms module
from py3plex.algorithms import (
    MetaFlowReport,
    run_meta_analysis
)
```

## Examples

See the `examples/centrality_and_statistics/` directory:
- `example_multilayer_centrality.py` - Demonstrates MultilayerCentrality class
- `example_versatility.py` - Demonstrates versatility computation

## References

- De Domenico et al. (2013) "Mathematical Formulation of Multilayer Networks" Physical Review X 3, 041022
- De Domenico et al. (2015) "Ranking in interconnected multilayer networks reveals versatile nodes" Nature Communications 6, 6868
- Katz (1953) "A new status index derived from sociometric analysis" Psychometrika 18(1), 39-43
- Estrada & Hatano (2008) "Communicability in complex networks" Physical Review E 77(3), 036111

## Version

This API is available in py3plex 0.95a and later.
