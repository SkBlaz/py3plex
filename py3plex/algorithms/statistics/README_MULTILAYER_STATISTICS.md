# Multilayer Network Statistics

This module implements 17 comprehensive statistics for multilayer and multiplex networks, following standard definitions from multilayer network analysis literature.

## Overview

The `multilayer_statistics.py` module provides functions to analyze structural properties, connectivity patterns, and resilience of multilayer networks. These statistics capture aspects unique to multilayer systems that cannot be measured by traditional single-layer network metrics.

## References

- Kivelä, M., et al. (2014). "Multilayer networks." *Journal of Complex Networks*, 2(3), 203-271.
- De Domenico, M., et al. (2013). "Mathematical formulation of multilayer networks." *Physical Review X*, 3(4), 041022.
- Mucha, P. J., et al. (2010). "Community Structure in Time-Dependent, Multiscale, and Multiplex Networks." *Science*, 328(5980), 876-878.

## Statistics Implemented

### 1. Layer Density (ρᵢ)
**Formula:** ρᵢ = (2Eᵢ) / (Nᵢ(Nᵢ - 1))

Measures the fraction of possible edges present in a specific layer, indicating how densely connected that layer is.

```python
density = mls.layer_density(network, 'layer1')
```

### 2. Inter-layer Coupling Strength (Cᵢⱼ)
**Formula:** Cᵢⱼ = (1/N) Σₖ wₖᵢⱼ

Average weight of inter-layer connections between corresponding nodes in two layers.

```python
coupling = mls.inter_layer_coupling_strength(network, 'layer1', 'layer2')
```

### 3. Node Activity (aᵢ)
**Formula:** aᵢ = (1/L) Σₗ I(vᵢ ∈ layerₗ)

Fraction of layers in which a node is active (has at least one connection).

```python
activity = mls.node_activity(network, 'node_A')
```

### 4. Degree Vector (kᵢ)
**Formula:** kᵢ = [kᵢ¹, kᵢ², …, kᵢᴸ]

Node degree in each layer, useful for analyzing node versatility across layers.

```python
degrees = mls.degree_vector(network, 'node_A', weighted=False)
```

### 5. Inter-layer Degree Correlation (rᵢⱼ)
**Formula:** rᵢⱼ = corr(kᵢˡ, kᵢᵐ)

Pearson correlation of node degrees between two layers, revealing if hubs in one layer are also hubs in another.

```python
correlation = mls.inter_layer_degree_correlation(network, 'layer1', 'layer2')
```

### 6. Edge Overlap (ωᵢⱼ)
**Formula:** ωᵢⱼ = |Eᵢ ∩ Eⱼ| / |Eᵢ ∪ Eⱼ|

Jaccard similarity of edge sets between two layers, measuring structural redundancy.

```python
overlap = mls.edge_overlap(network, 'layer1', 'layer2')
```

### 7. Layer Similarity (Sᵢⱼ)
**Formula:** Sᵢⱼ = ⟨Aᵢ, Aⱼ⟩ / (‖Aᵢ‖‖Aⱼ‖)

Cosine or Jaccard similarity between adjacency matrices of two layers.

```python
similarity = mls.layer_similarity(network, 'layer1', 'layer2', method='cosine')
```

### 8. Multilayer Clustering Coefficient (Cᴹ)
**Formula:** Cᴹ = (1/N) Σᵢ (multilayer triangles involving i) / (possible triplets)

Extends traditional clustering coefficient to account for triangles spanning multiple layers.

```python
# For all nodes
clustering = mls.multilayer_clustering_coefficient(network)

# For specific node
clustering = mls.multilayer_clustering_coefficient(network, node='A')
```

### 9. Versatility Centrality (Vᵢ)
**Formula:** Vᵢ = Σₗ αₗ Cᵢˡ

Weighted combination of node centrality values across layers, measuring overall influence.

```python
versatility = mls.versatility_centrality(network, centrality_type='degree')

# With custom layer weights
alpha = {'layer1': 0.7, 'layer2': 0.3}
versatility = mls.versatility_centrality(network, centrality_type='degree', alpha=alpha)
```

### 10. Interdependence (λ)
**Formula:** λ = (shortest path in multiplex) / (avg shortest path in single layers)

Quantifies how much shortest-path communication depends on inter-layer connections.

```python
interdep = mls.interdependence(network, sample_size=100)
```

### 11. Multilayer Modularity (Qᴹᴸ)
**Formula:** Qᴹᴸ = (1/2μ) Σᵢⱼₗ [(Aᵢⱼˡ - γˡPᵢⱼˡ) δ(gᵢˡ, gⱼˡ) + δᵢⱼ Cˡˡ' δ(gᵢˡ, gⱼˡ')]

Extension of Newman-Girvan modularity to multiplex networks (Mucha et al., 2010).

```python
communities = {
    ('A', 'L1'): 0, ('B', 'L1'): 0,
    ('C', 'L1'): 1, ('D', 'L1'): 1
}
Q = mls.multilayer_modularity(network, communities, gamma=1.0, omega=1.0)
```

### 12. Supra-Laplacian Spectrum (Λ)
**Formula:** Lˢ = Dˢ - Aˢ

Eigenvalue spectrum of the supra-Laplacian matrix, capturing diffusion properties.

```python
spectrum = mls.supra_laplacian_spectrum(network, k=10)
```

### 13. Algebraic Connectivity (λ₂)
Second smallest eigenvalue of the supra-Laplacian (Fiedler value).

```python
alg_conn = mls.algebraic_connectivity(network)
```

### 14. Inter-layer Assortativity (rᴵ)
**Formula:** rᴵ = cov(kᵢˡ, kᵢᵐ) / (σₗσₘ)

Degree mixing patterns across different layers.

```python
assort = mls.inter_layer_assortativity(network, 'layer1', 'layer2')
```

### 15. Entropy of Multiplexity (Hₘ)
**Formula:** Hₘ = -Σₗ pₗ log(pₗ), where pₗ = Eₗ / ΣₖEₖ

Shannon entropy of layer contributions, measuring layer diversity.

```python
entropy = mls.entropy_of_multiplexity(network)
```

### 16. Multilayer Motif Frequency (fₘ)
**Formula:** fₘ = nₘ / Σₖ nₖ

Frequency of recurring subgraph patterns across layers.

```python
motifs = mls.multilayer_motif_frequency(network, motif_size=3)
```

### 17. Resilience (R)
**Formula:** R = (S' / S₀) after perturbation

Ratio of largest connected component after perturbation to original size.

```python
# Layer removal
r = mls.resilience(network, 'layer_removal', perturbation_param='layer1')

# Inter-layer coupling removal
r = mls.resilience(network, 'coupling_removal', perturbation_param=0.5)
```

## Usage Example

See `examples/example_multilayer_statistics.py` for a comprehensive demonstration.

```python
from py3plex.core import multinet
from py3plex.algorithms.statistics import multilayer_statistics as mls

# Create network
network = multinet.multi_layer_network(directed=False)
network.add_edges([
    ['A', 'L1', 'B', 'L1', 1],
    ['B', 'L1', 'C', 'L1', 1],
    ['A', 'L2', 'C', 'L2', 1]
], input_type='list')

# Calculate statistics
density = mls.layer_density(network, 'L1')
activity = mls.node_activity(network, 'A')
versatility = mls.versatility_centrality(network)
```

## Testing

Run the test suite:

```bash
python -m pytest tests/test_multilayer_statistics.py -v
```

The test suite includes:
- 24 unit tests covering all 17 statistics
- Edge case handling tests
- Integration tests with realistic networks

## Notes

- All functions work with both directed and undirected networks
- Statistics automatically handle weighted edges when available
- Empty layers or missing data are handled gracefully
- Some statistics (e.g., interdependence) support sampling for large networks
