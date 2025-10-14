# Multilayer Network Statistics - Quick Formula Reference

**Version:** 1.0  
**Date:** October 14, 2025  
**Status:** Verified against canonical literature

This document provides a quick reference for all 17 multilayer network statistics formulas implemented in py3plex. All formulas have been verified against canonical literature (Mucha et al. 2010, De Domenico et al. 2013, Kivelä et al. 2014, Boccaletti et al. 2014).

---

## Complete Formula List

### 1. Layer Density (ρₐ)

**Formula (Undirected):** 
```
ρₐ = (2Eₐ) / (Nₐ(Nₐ - 1))
```

**Formula (Directed):**
```
ρₐ = Eₐ / (Nₐ(Nₐ - 1))
```

**Variables:**
- `Eₐ` = number of edges in layer α
- `Nₐ` = number of nodes in layer α

**Function:** `layer_density(network, layer)`

**Reference:** Kivelä et al. (2014)

---

### 2. Inter-layer Coupling Strength (C^αβ)

**Formula:**
```
C^αβ = (1/N_αβ) Σᵢ wᵢ^αβ
```

**Variables:**
- `N_αβ` = number of nodes present in both layers α and β
- `wᵢ^αβ` = weight of inter-layer edge connecting node i in layer α to node i in layer β

**Function:** `inter_layer_coupling_strength(network, layer_i, layer_j)`

**Reference:** De Domenico et al. (2013)

---

### 3. Node Activity (aᵢ)

**Formula:**
```
aᵢ = (1/L) Σₐ 𝟙(vᵢ ∈ Vₐ)
```

**Variables:**
- `L` = total number of layers
- `𝟙(vᵢ ∈ Vₐ)` = indicator function (1 if node i is active in layer α, 0 otherwise)
- `Vₐ` = set of active nodes in layer α

**Function:** `node_activity(network, node)`

**Reference:** Kivelä et al. (2014), Battiston et al. (2014)

---

### 4. Degree Vector (kᵢ)

**Formula:**
```
kᵢ = (kᵢ¹, kᵢ², …, kᵢᴸ)
```

**Variables:**
- `kᵢᵅ` = degree of node i in layer α
- For undirected: `kᵢᵅ = Σⱼ Aᵢⱼᵅ`

**Function:** `degree_vector(network, node, weighted=False)`

**Reference:** Kivelä et al. (2014)

---

### 5. Inter-layer Degree Correlation (r^αβ)

**Formula:**
```
r^αβ = Σᵢ(kᵢᵅ - k̄ᵅ)(kᵢᵝ - k̄ᵝ) / [√(Σᵢ(kᵢᵅ - k̄ᵅ)²) √(Σᵢ(kᵢᵝ - k̄ᵝ)²)]
```

**Variables:**
- `kᵢᵅ` = degree of node i in layer α
- `k̄ᵅ` = mean degree in layer α
- Sum over nodes present in both layers

**Function:** `inter_layer_degree_correlation(network, layer_i, layer_j)`

**Reference:** Battiston et al. (2014), Nicosia & Latora (2015)

---

### 6. Edge Overlap (ω^αβ)

**Formula:**
```
ω^αβ = |Eₐ ∩ Eᵦ| / |Eₐ ∪ Eᵦ|
```

**Variables:**
- `Eₐ` = set of edges in layer α
- `Eᵦ` = set of edges in layer β
- `|·|` = cardinality (number of elements)

**Function:** `edge_overlap(network, layer_i, layer_j)`

**Reference:** Kivelä et al. (2014)

---

### 7. Layer Similarity (S^αβ)

**Formula:**
```
S^αβ = ⟨Aₐ, Aᵦ⟩ / (‖Aₐ‖ ‖Aᵦ‖)
     = Σᵢⱼ AᵢⱼᵅAᵢⱼᵝ / √(Σᵢⱼ(Aᵢⱼᵅ)²) √(Σᵢⱼ(Aᵢⱼᵝ)²)
```

**Variables:**
- `Aₐ, Aᵦ` = adjacency matrices for layers α and β
- `⟨·,·⟩` = Frobenius inner product
- `‖·‖` = Frobenius norm

**Function:** `layer_similarity(network, layer_i, layer_j, method='cosine')`

**Reference:** De Domenico et al. (2013)

---

### 8. Multilayer Clustering Coefficient (Cᴹ)

**Formula:**
```
Cᵢᴹ = Tᵢ / Tᵢᵐᵃˣ
```

**Variables:**
- `Tᵢ` = number of closed triplets (triangles) involving node i across all layers
- `Tᵢᵐᵃˣ` = maximum possible triplets = `Σₐ kᵢᵅ(kᵢᵅ - 1)/2` for undirected networks
- Average: `Cᴹ = (1/N) Σᵢ Cᵢᴹ`

**Function:** `multilayer_clustering_coefficient(network, node=None)`

**Reference:** Battiston et al. (2014)

---

### 9. Versatility Centrality (Vᵢ)

**Formula:**
```
Vᵢ = Σₐ wₐ Cᵢᵅ
```

**Variables:**
- `wₐ` = weight for layer α (typically `1/L` for uniform weighting, `Σₐ wₐ = 1`)
- `Cᵢᵅ` = centrality of node i in layer α

**Function:** `versatility_centrality(network, centrality_type='degree', alpha=None)`

**Reference:** De Domenico et al. (2015), Nature Communications 6, 6868

---

### 10. Interdependence (λ)

**Formula:**
```
λ = ⟨dᴹᴸ⟩ / ⟨dᵃᵛᵍ⟩
```

**Variables:**
- `dᵢⱼᴹᴸ` = shortest path from i to j in full multilayer network
- `dᵢⱼᵃᵛᵍ` = `(1/L) Σₐ dᵢⱼᵅ` = average shortest path across individual layers
- `⟨·⟩` = average over sampled node pairs

**Interpretation:**
- `λ < 1`: positive interdependence
- `λ ≈ 1`: little benefit from inter-layer connections
- `λ > 1`: multilayer structure increases path lengths

**Function:** `interdependence(network, sample_size=100)`

**Reference:** Gomez et al. (2013), Buldyrev et al. (2010)

---

### 11. Multilayer Modularity (Qᴹᴸ)

**Formula:**
```
Qᴹᴸ = (1/2μ) Σᵢⱼₐᵦ [(Aᵢⱼᵅ - γₐPᵢⱼᵅ)δₐᵦ + ωₐᵦδᵢⱼ] δ(gᵢᵅ, gⱼᵝ)
```

**Variables:**
- `μ` = total edge weight in supra-network
- `Aᵢⱼᵅ` = adjacency matrix element for layer α
- `Pᵢⱼᵅ` = `kᵢᵅkⱼᵅ/(2mₐ)` = null model (configuration model)
- `γₐ` = resolution parameter for layer α
- `ωₐᵦ` = inter-layer coupling strength
- `δₐᵦ` = Kronecker delta (1 if α=β, 0 otherwise)
- `δᵢⱼ` = Kronecker delta (1 if i=j, 0 otherwise)
- `δ(gᵢᵅ, gⱼᵝ)` = 1 if node i in layer α and node j in layer β are in same community

**Function:** `multilayer_modularity(network, communities, gamma=1.0, omega=1.0)`

**Reference:** Mucha et al. (2010), Science 328(5980), 876-878

---

### 12. Supra-Laplacian Spectrum (Λ)

**Formula:**
```
ℒ = 𝒟 - 𝒜
```

**Variables:**
- `𝒜` = supra-adjacency matrix (NL × NL block matrix)
- `𝒟` = supra-degree matrix (diagonal matrix with row sums of 𝒜)
- `ℒ` = supra-Laplacian matrix
- `Λ = {λ₀, λ₁, ..., λₙₗ₋₁}` with `0 = λ₀ ≤ λ₁ ≤ ... ≤ λₙₗ₋₁`

**Function:** `supra_laplacian_spectrum(network, k=10)`

**Reference:** De Domenico et al. (2013), Gomez et al. (2013)

---

### 13. Algebraic Connectivity (λ₂)

**Formula:**
```
λ₂(ℒ)
```

Second smallest eigenvalue of the supra-Laplacian (Fiedler value).

**Properties:**
- `λ₀ = 0` always
- `λ₁ > 0` iff network is connected
- Larger `λ₁` → better connectivity

**Function:** `algebraic_connectivity(network)`

**Reference:** Fiedler (1973), Sole-Ribalta et al. (2013)

---

### 14. Inter-layer Assortativity (rᴵ)

**Formula:**
```
r^αβ = cov(k^α, k^β) / (σₐ σᵦ) = corr(k^α, k^β)
```

**Variables:**
- `k^α` = degree vector in layer α
- `k^β` = degree vector in layer β
- `σₐ, σᵦ` = standard deviations of degrees

**Function:** `inter_layer_assortativity(network, layer_i, layer_j)`

**Reference:** Newman (2002), Nicosia & Latora (2015)

---

### 15. Entropy of Multiplexity (Hₘ)

**Formula:**
```
Hₘ = -Σₐ pₐ log₂(pₐ)
where pₐ = Eₐ / Σᵦ Eᵦ
```

**Variables:**
- `pₐ` = proportion of edges in layer α
- `Eₐ` = number of edges in layer α

**Properties:**
- `Hₘ = 0`: all edges in one layer (minimum diversity)
- `Hₘ = log₂(L)`: edges uniformly distributed (maximum diversity)

**Function:** `entropy_of_multiplexity(network)`

**Reference:** De Domenico et al. (2013), Shannon (1948)

---

### 16. Multilayer Motif Frequency (fₘ)

**Formula:**
```
fₘ = nₘ / Σₖ nₖ
```

**Variables:**
- `nₘ` = count of motif type m
- `Σₖ nₖ` = total count of all motifs

**Note:** Simplified implementation counts intra-layer vs. inter-layer triangles.

**Function:** `multilayer_motif_frequency(network, motif_size=3)`

**Reference:** Battiston et al. (2014)

---

### 17. Resilience (R)

**Formula:**
```
R = S' / S₀
```

**Variables:**
- `S₀` = size of largest connected component in original network
- `S'` = size of largest connected component after perturbation

**Properties:**
- `R = 1`: full resilience
- `R = 0`: complete fragmentation
- `0 < R < 1`: partial resilience

**Function:** `resilience(network, perturbation_type, perturbation_param)`

**Reference:** Buldyrev et al. (2010), Nature 464, 1025-1028

---

## Symbol Definitions

| Symbol | Meaning | Domain |
|--------|---------|--------|
| α, β, ℓ | Layer indices | {1, 2, ..., L} |
| i, j, k | Node indices | {1, 2, ..., N} |
| L | Number of layers | ℕ |
| N | Number of nodes | ℕ |
| Eₐ | Edges in layer α | ℕ |
| Aᵢⱼᵅ | Adjacency matrix element | ℝ (typically {0,1}) |
| kᵢᵅ | Degree in layer α | ℕ |
| γₐ | Resolution parameter | ℝ⁺ |
| ωₐᵦ | Inter-layer coupling | ℝ⁺ |
| δₐᵦ | Kronecker delta | {0, 1} |
| μ | Total edge weight | ℝ⁺ |
| 𝒜 | Supra-adjacency matrix | ℝ^(NL×NL) |
| ℒ | Supra-Laplacian matrix | ℝ^(NL×NL) |
| λₖ | k-th eigenvalue | ℝ |

---

## Usage Example

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
coupling = mls.inter_layer_coupling_strength(network, 'L1', 'L2')
```

---

## Canonical References

1. **Mucha et al. (2010)** - "Community Structure in Time-Dependent, Multiscale, and Multiplex Networks." *Science* 328(5980), 876-878.

2. **De Domenico et al. (2013)** - "Mathematical formulation of multilayer networks." *Physical Review X* 3(4), 041022.

3. **Kivelä et al. (2014)** - "Multilayer networks." *Journal of Complex Networks* 2(3), 203-271.

4. **Boccaletti et al. (2014)** - "The structure and dynamics of multilayer networks." *Physics Reports* 544(1), 1-122.

5. **Battiston et al. (2014)** - "Structural measures for multiplex networks." *Physical Review E* 89, 032804.

6. **De Domenico et al. (2015)** - "Ranking in interconnected multilayer networks reveals versatile nodes." *Nature Communications* 6, 6868.

7. **Nicosia & Latora (2015)** - "Measuring and modeling correlations in multiplex networks." *Physical Review E* 92, 032805.

8. **Gomez et al. (2013)** - "Diffusion dynamics on multiplex networks." *Physical Review Letters* 110, 028701.

9. **Buldyrev et al. (2010)** - "Catastrophic cascade of failures in interdependent networks." *Nature* 464, 1025-1028.

10. **Sole-Ribalta et al. (2013)** - "Spectral properties of the Laplacian of multiplex networks." *Physical Review E* 88, 032807.

---

## Verification Status

✅ **All formulas verified** (October 2025)

See `MULTILAYER_STATISTICS_VERIFICATION.md` for detailed verification report.

---

**Last Updated:** October 14, 2025  
**Maintainer:** py3plex team  
**Contact:** https://github.com/SkBlaz/py3plex
