# Multilayer Network Statistics

This module implements 17 comprehensive statistics for multilayer and multiplex networks, following standard definitions from multilayer network analysis literature.

**Formula Verification:** All formulas have been verified against canonical literature (October 2025). See the references section below for bibliographic citations.

## Overview

The `multilayer_statistics.py` module provides functions to analyze structural properties, connectivity patterns, and resilience of multilayer networks. These statistics capture aspects unique to multilayer systems that cannot be measured by traditional single-layer network metrics.

## References

- Kivelä, M., et al. (2014). "Multilayer networks." *Journal of Complex Networks*, 2(3), 203-271.
- De Domenico, M., et al. (2013). "Mathematical formulation of multilayer networks." *Physical Review X*, 3(4), 041022.
- Mucha, P. J., et al. (2010). "Community Structure in Time-Dependent, Multiscale, and Multiplex Networks." *Science*, 328(5980), 876-878.

## Statistics Implemented

### 1. Layer Density (ρₐ)
**Formula:** ρₐ = (2Eₐ) / (Nₐ(Nₐ - 1))  (undirected)  
**Formula:** ρₐ = Eₐ / (Nₐ(Nₐ - 1))  (directed)

Measures the fraction of possible edges present in a specific layer, indicating how densely connected that layer is.

**Variables:**
- Eₐ = number of edges in layer α
- Nₐ = number of nodes in layer α

```python
density = mls.layer_density(network, 'layer1')
```

### 2. Inter-layer Coupling Strength (C^αβ)
**Formula:** C^αβ = (1/N_αβ) Σᵢ wᵢ^αβ

Average weight of inter-layer connections between corresponding nodes in two layers. Quantifies cross-layer connectivity.

**Variables:**
- N_αβ = number of nodes present in both layers α and β
- wᵢ^αβ = weight of inter-layer edge connecting node i in layer α to node i in layer β

```python
coupling = mls.inter_layer_coupling_strength(network, 'layer1', 'layer2')
```

### 3. Node Activity (aᵢ)
**Formula:** aᵢ = (1/L) Σₐ 𝟙(vᵢ ∈ Vₐ)

Fraction of layers in which a node is active (has at least one connection).

**Variables:**
- L = total number of layers
- 𝟙(vᵢ ∈ Vₐ) = indicator function (1 if node i is active in layer α, 0 otherwise)
- Vₐ = set of active nodes in layer α

```python
activity = mls.node_activity(network, 'node_A')
```

### 4. Degree Vector (kᵢ)
**Formula:** kᵢ = (kᵢ¹, kᵢ², …, kᵢᴸ)

Node degree in each layer, useful for analyzing node versatility across layers.

**Variables:**
- kᵢᵅ = degree of node i in layer α
- For undirected: kᵢᵅ = Σⱼ Aᵢⱼᵅ

```python
degrees = mls.degree_vector(network, 'node_A', weighted=False)
```

### 5. Inter-layer Degree Correlation (r^αβ)
**Formula:** r^αβ = Σᵢ(kᵢᵅ - k̄ᵅ)(kᵢᵝ - k̄ᵝ) / [√(Σᵢ(kᵢᵅ - k̄ᵅ)²) √(Σᵢ(kᵢᵝ - k̄ᵝ)²)]

Pearson correlation of node degrees between two layers, revealing if hubs in one layer are also hubs in another.

**Variables:**
- kᵢᵅ = degree of node i in layer α
- k̄ᵅ = mean degree in layer α
- Sum over nodes present in both layers

```python
correlation = mls.inter_layer_degree_correlation(network, 'layer1', 'layer2')
```

### 6. Edge Overlap (ω^αβ)
**Formula:** ω^αβ = |Eₐ ∩ Eᵦ| / |Eₐ ∪ Eᵦ|

Jaccard similarity of edge sets between two layers, measuring structural redundancy.

**Variables:**
- Eₐ = set of edges in layer α
- Eᵦ = set of edges in layer β
- |·| = cardinality (number of elements)

```python
overlap = mls.edge_overlap(network, 'layer1', 'layer2')
```

### 7. Layer Similarity (S^αβ)
**Formula:** S^αβ = ⟨Aₐ, Aᵦ⟩ / (‖Aₐ‖ ‖Aᵦ‖) = Σᵢⱼ AᵢⱼᵅAᵢⱼᵝ / √(Σᵢⱼ(Aᵢⱼᵅ)²) √(Σᵢⱼ(Aᵢⱼᵝ)²)

Cosine or Jaccard similarity between adjacency matrices of two layers.

**Variables:**
- Aₐ, Aᵦ = adjacency matrices for layers α and β
- ⟨·,·⟩ = Frobenius inner product
- ‖·‖ = Frobenius norm

```python
similarity = mls.layer_similarity(network, 'layer1', 'layer2', method='cosine')
```

### 8. Multilayer Clustering Coefficient (Cᴹ)
**Formula:** Cᵢᴹ = Tᵢ / Tᵢᵐᵃˣ

Extends traditional clustering coefficient to account for triangles spanning multiple layers.

**Variables:**
- Tᵢ = number of closed triplets (triangles) involving node i across all layers
- Tᵢᵐᵃˣ = maximum possible triplets = Σₐ kᵢᵅ(kᵢᵅ - 1)/2 for undirected networks
- Average over all nodes: Cᴹ = (1/N) Σᵢ Cᵢᴹ

```python
# For all nodes
clustering = mls.multilayer_clustering_coefficient(network)

# For specific node
clustering = mls.multilayer_clustering_coefficient(network, node='A')
```

### 9. Versatility Centrality (Vᵢ)
**Formula:** Vᵢ = Σₐ wₐ Cᵢᵅ

Weighted combination of node centrality values across layers, measuring overall influence.

**Variables:**
- wₐ = weight for layer α (typically 1/L for uniform weighting, Σₐ wₐ = 1)
- Cᵢᵅ = centrality of node i in layer α (can be degree, betweenness, closeness, etc.)

**Reference:** De Domenico et al. (2015) "Ranking in interconnected multilayer networks reveals versatile nodes," *Nature Communications* 6, 6868.

```python
versatility = mls.versatility_centrality(network, centrality_type='degree')

# With custom layer weights
alpha = {'layer1': 0.7, 'layer2': 0.3}
versatility = mls.versatility_centrality(network, centrality_type='degree', alpha=alpha)
```

### 10. Interdependence (λ)
**Formula:** λ = ⟨dᴹᴸ⟩ / ⟨dᵃᵛᵍ⟩

Quantifies how much shortest-path communication depends on inter-layer connections.

**Variables:**
- dᵢⱼᴹᴸ = shortest path from node i to node j in the full multilayer network
- dᵢⱼᵃᵛᵍ = (1/L) Σₐ dᵢⱼᵅ is the average shortest path across individual layers
- ⟨·⟩ = average over sampled node pairs

**Interpretation:**
- λ < 1: multilayer connectivity reduces path lengths (positive interdependence)
- λ ≈ 1: inter-layer connections provide little benefit
- λ > 1: multilayer structure increases path lengths (rare)

```python
interdep = mls.interdependence(network, sample_size=100)
```

### 11. Multilayer Modularity (Qᴹᴸ)
**Formula:** Qᴹᴸ = (1/2μ) Σᵢⱼₐᵦ [(Aᵢⱼᵅ - γₐPᵢⱼᵅ)δₐᵦ + ωₐᵦδᵢⱼ] δ(gᵢᵅ, gⱼᵝ)

Extension of Newman-Girvan modularity to multiplex networks (Mucha et al., 2010).

**Variables:**
- μ = total edge weight in supra-network
- Aᵢⱼᵅ = adjacency matrix element for layer α
- Pᵢⱼᵅ = kᵢᵅkⱼᵅ/(2mₐ) is the null model (configuration model)
- γₐ = resolution parameter for layer α
- ωₐᵦ = inter-layer coupling strength
- δₐᵦ = Kronecker delta (1 if α=β, 0 otherwise)
- δᵢⱼ = Kronecker delta (1 if i=j, 0 otherwise)
- δ(gᵢᵅ, gⱼᵝ) = 1 if node i in layer α and node j in layer β are in same community

```python
communities = {
    ('A', 'L1'): 0, ('B', 'L1'): 0,
    ('C', 'L1'): 1, ('D', 'L1'): 1
}
Q = mls.multilayer_modularity(network, communities, gamma=1.0, omega=1.0)
```

### 12. Supra-Laplacian Spectrum (Λ)
**Formula:** ℒ = 𝒟 - 𝒜

Eigenvalue spectrum of the supra-Laplacian matrix, capturing diffusion properties.

**Variables:**
- 𝒜 = supra-adjacency matrix (NL × NL block matrix containing all layers and inter-layer couplings)
- 𝒟 = supra-degree matrix (diagonal matrix with row sums of 𝒜)
- ℒ = supra-Laplacian matrix
- Λ = {λ₀, λ₁, ..., λₙₗ₋₁} with 0 = λ₀ ≤ λ₁ ≤ ... ≤ λₙₗ₋₁

**Reference:** De Domenico et al. (2013), Gomez et al. (2013) "Diffusion dynamics on multiplex networks."

```python
spectrum = mls.supra_laplacian_spectrum(network, k=10)
```

### 13. Algebraic Connectivity (λ₂)
**Formula:** λ₂(ℒ)

Second smallest eigenvalue of the supra-Laplacian (Fiedler value).

Indicates global connectivity and diffusion efficiency of the multilayer system.

**Properties:**
- λ₀ = 0 always (associated with constant eigenvector)
- λ₁ > 0 if and only if the multilayer network is connected
- Larger λ₁ indicates better connectivity and faster diffusion/synchronization

**Reference:** Fiedler (1973) "Algebraic connectivity of graphs"; Sole-Ribalta et al. (2013) "Spectral properties of the Laplacian of multiplex networks."

```python
alg_conn = mls.algebraic_connectivity(network)
```

### 14. Inter-layer Assortativity (rᴵ)
**Formula:** r^αβ = cov(k^α, k^β) / (σₐ σᵦ) = corr(k^α, k^β)

Measures whether nodes with similar degrees tend to connect across different layers.

**Variables:**
- k^α = degree vector in layer α
- k^β = degree vector in layer β
- σₐ, σᵦ = standard deviations of degrees in layers α and β
- Equivalent to Pearson correlation of degree vectors

**Reference:** Newman (2002) "Assortative mixing in networks"; Nicosia & Latora (2015) for multilayer context.

```python
assort = mls.inter_layer_assortativity(network, 'layer1', 'layer2')
```

### 15. Entropy of Multiplexity (Hₘ)
**Formula:** Hₘ = -Σₐ pₐ log₂(pₐ), where pₐ = Eₐ / Σᵦ Eᵦ

Shannon entropy of layer contributions, measuring layer diversity.

**Variables:**
- pₐ = proportion of edges in layer α
- Eₐ = number of edges in layer α
- log₂ gives entropy in bits

**Properties:**
- Hₘ = 0 when all edges are in one layer (minimum entropy/diversity)
- Hₘ = log₂(L) when edges are uniformly distributed across L layers (maximum entropy)

**Reference:** De Domenico et al. (2013), Section III.B; Shannon (1948) "A mathematical theory of communication."

```python
entropy = mls.entropy_of_multiplexity(network)
```

### 16. Multilayer Motif Frequency (fₘ)
**Formula:** fₘ = nₘ / Σₖ nₖ

Frequency of recurring subgraph patterns across layers.

**Variables:**
- nₘ = count of motif type m
- Σₖ nₖ = total count of all motifs

**Note:** This is a simplified implementation counting basic patterns (intra-layer vs. inter-layer triangles). Complete multilayer motif enumeration includes many more configurations and is computationally expensive.

**Reference:** Battiston et al. (2014), Section IV - Motifs in multiplex networks; Paranjape et al. (2017) for temporal multilayer motifs.

```python
motifs = mls.multilayer_motif_frequency(network, motif_size=3)
```

### 17. Resilience (R)
**Formula:** R = S' / S₀

Ratio of largest connected component after perturbation to original size.

**Variables:**
- S₀ = size of largest connected component in original network
- S' = size of largest connected component after perturbation

**Perturbation types:**
1. **Layer removal**: Remove all nodes/edges in a specific layer
2. **Coupling removal**: Remove a fraction of inter-layer edges

**Properties:**
- R = 1 indicates full resilience (no impact from perturbation)
- R = 0 indicates complete fragmentation
- 0 < R < 1 indicates partial resilience

**Reference:** Buldyrev et al. (2010) "Catastrophic cascade of failures in interdependent networks," *Nature* 464, 1025-1028.

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
