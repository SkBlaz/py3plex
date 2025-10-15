# LLM Context Summary

This repository defines **Py3plex**, a modular Python library for analysis and visualization of heterogeneous and multilayer networks. Heterogeneous networks are complex networks with additional information assigned to nodes, edges, or both—including multiple node types, edge types, and layered structures. Py3plex provides utilities for constructing, decomposing, analyzing, and visualizing such networks with built-in support for computing structural metrics, performing community detection, network classification, and integrating multilayer network data with external knowledge sources.

The library operates in the domain of network science, graph theory, and complex systems analysis. It is research-oriented, lightweight, and extensible, designed to complement existing frameworks like NetworkX while adding specialized capabilities for multilayer and heterogeneous network analysis. The computational ecosystem includes NumPy, SciPy, NetworkX, Matplotlib, Plotly, and various machine learning libraries for embeddings and classification tasks.

## Overview

Py3plex solves the fundamental challenge of analyzing and visualizing networks that contain multiple node types, edge types, or layers of interaction—a common pattern in social networks, biological systems, transportation networks, and knowledge graphs. Traditional network analysis tools focus on homogeneous networks (single node and edge type), but real-world systems often exhibit heterogeneity across multiple dimensions. Py3plex bridges this gap by providing specialized data structures, algorithms, and visualization techniques designed specifically for multilayer networks.

The library's inputs include edge lists, adjacency matrices, GraphML files, GEXF files, CSV data, and NetworkX graph objects. It can handle both multiplex networks (multiple layers with shared node sets) and general heterogeneous networks (different node types across layers). Outputs include computed metrics (centrality, clustering, community structure), decomposed network representations, node embeddings, publication-ready visualizations, and exported graph formats.

Py3plex abstracts network operations around a central `multi_layer_network` class that manages inter-layer and intra-layer edges, layer-specific node attributes, and coupling between layers. The library provides analytical methods for computing multilayer centrality measures, community detection across layers, network decomposition using meta-paths, and temporal dynamics. Visualization tools include diagonal projection plots, supra-adjacency matrix heatmaps, force-directed multilayer layouts, and interactive network renderings.

The library builds primarily on NetworkX as the underlying graph representation while reimplementing and extending algorithms specifically for multilayer scenarios. It includes integrations with Infomap for overlapping community detection, label propagation for semi-supervised learning, and Node2Vec for embedding generation. The architecture emphasizes modularity—each component (core data structures, algorithms, visualization, I/O) operates independently but shares standardized interfaces.

Key distinguishing features include: (1) native support for heterogeneous node and edge types with type-aware algorithms, (2) diagonal projection visualization designed for large multilayer networks, (3) network decomposition based on meta-paths and structural patterns, (4) semantic enrichment by linking network nodes to external knowledge bases, and (5) integration of statistical testing frameworks for comparing network properties.

## Structure

```
py3plex/
├── py3plex/                          → Main library source code
│   ├── __init__.py                   → Package entry point
│   ├── logging_config.py             → Logging infrastructure for the library
│   ├── core/                         → Core data structures and network management
│   │   ├── multinet.py               → multi_layer_network class (1223 lines)
│   │   ├── parsers.py                → Input parsers (GML, GraphML, CSV, GEXF, JSON)
│   │   ├── converters.py             → Network format converters
│   │   ├── nx_compat.py              → NetworkX compatibility utilities
│   │   ├── random_generators.py      → Random multilayer network generators
│   │   ├── supporting.py             → Helper functions for edge operations
│   │   └── HINMINE/                  → HIN mining and decomposition
│   │       ├── decomposition.py      → Graph decomposition algorithms
│   │       └── IO.py                 → I/O for HINMINE objects
│   ├── algorithms/                   → Graph algorithms and computational methods
│   │   ├── community_detection/      → Community detection algorithms
│   │   │   ├── community_wrapper.py  → High-level interface for Louvain, Infomap
│   │   │   ├── community_louvain.py  → Louvain modularity optimization
│   │   │   ├── multilayer_modularity.py → Multilayer modularity (Mucha et al. 2010)
│   │   │   ├── multilayer_benchmark.py  → Synthetic multilayer benchmarks (mLFR, SBM)
│   │   │   ├── node_ranking.py       → PageRank, PPR centrality measures
│   │   │   ├── community_ranking.py  → Community importance ranking
│   │   │   └── infomap/              → Infomap C++ bindings for overlapping communities
│   │   ├── statistics/               → Network statistics and metrics
│   │   │   ├── statistics.py         → Core network statistics (diameter, density, clustering)
│   │   │   ├── multilayer_statistics.py → Multilayer network statistics (17 measures)
│   │   │   ├── topology.py           → Topological measures (degree distribution)
│   │   │   ├── enrichment.py         → Statistical enrichment analysis
│   │   │   ├── correlation_networks.py → Correlation-based network construction
│   │   │   ├── powerlaw.py           → Power-law fitting for degree distributions
│   │   │   └── bayesian*.py          → Bayesian statistical testing frameworks
│   │   ├── multilayer_algorithms/    → Algorithms specific to multilayer networks
│   │   ├── network_classification/   → Network-level classification
│   │   ├── node_ranking/             → Node importance and centrality algorithms
│   │   ├── hedwig/                   → Semantic subgroup discovery
│   │   ├── temporal_multiplex/       → Temporal network analysis
│   │   └── term_parsers/             → NLP term extraction utilities
│   ├── visualization/                → Plotting and rendering utilities
│   │   ├── multilayer.py             → Multilayer network visualization
│   │   ├── drawing_machinery.py      → Core drawing functions
│   │   ├── layout_algorithms.py      → Layout computation (force-directed, random)
│   │   ├── colors.py                 → Color scheme generators
│   │   ├── bezier.py                 → Bezier curve utilities for edges
│   │   ├── benchmark_visualizations.py → Performance visualization tools
│   │   ├── fa2/                      → ForceAtlas2 layout implementation
│   │   └── embedding_visualization/  → Embedding space visualization
│   └── wrappers/                     → High-level interfaces and integrations
│       ├── node2vec_embedding.py     → Node2Vec embedding generation
│       └── benchmark_nodes.py        → Node classification benchmarking
├── examples/                         → 43 example scripts demonstrating usage
├── tests/                            → Unit and integration tests
├── docs/                             → Markdown tutorials and guides
│   ├── 10min_tutorial.md             → 10-minute getting started tutorial
│   ├── development.md                → Development guide with Makefile commands
│   ├── multilayer_modularity_tutorial.md → Multilayer modularity guide
│   ├── multilayer_centrality_tutorial.md → Centrality measures guide
│   └── algorithm_selection_guide.md  → Algorithm selection and complexity
├── docfiles/                         → Sphinx documentation source files (RST)
│   ├── index.rst                     → Documentation entry point
│   ├── *.rst                         → ReStructuredText documentation files
│   └── _build/                       → Sphinx build output (HTML)
├── Makefile                          → Production-grade build system (development, testing, publishing)
├── pyproject.toml                    → Modern build configuration (PEP 517/518/621)
├── setup.py                          → Legacy setuptools configuration
├── requirements.txt                  → Core dependencies
├── README.md                         → Project introduction and quick start (minimalistic)
└── LLM.md                            → Comprehensive context for LLMs and maintainers
```

The library is structured around modular packages with clear separation of concerns. The `core/` package defines the fundamental `multi_layer_network` class and handles all I/O operations. The `algorithms/` package provides analytical capabilities organized by function (community detection, statistics, classification). The `visualization/` package supplies rendering tools optimized for multilayer networks. The `wrappers/` package offers simplified interfaces for common workflows like embedding generation.

Inter-module relationships follow a layered architecture: `core` provides foundational data structures used by all other modules, `algorithms` depend on `core` for network access, and `visualization` consumes outputs from both `core` and `algorithms`. Each module operates independently but shares the `multi_layer_network` object as the primary data interchange format, ensuring consistency across analytical and visualization pipelines.

## Key Files

| File | Purpose |
|------|----------|
| `core/multinet.py` | Defines the `multi_layer_network` class—the central data structure managing nodes, edges, layers, and inter-layer couplings. Provides methods for network construction, manipulation, querying, and export. |
| `core/parsers.py` | Input/output parsers for loading networks from GML, GraphML, GEXF, CSV, JSON, and NetworkX formats. Handles type inference and layer assignment. |
| `core/HINMINE/decomposition.py` | Implements network decomposition algorithms for heterogeneous information networks, including meta-path extraction and cycle enumeration. |
| `algorithms/community_detection/community_wrapper.py` | High-level interface for community detection, wrapping Louvain and Infomap algorithms with multilayer-aware parameter handling. |
| `algorithms/community_detection/community_louvain.py` | Louvain modularity optimization for community detection, adapted for multilayer networks with configurable resolution parameters. |
| `algorithms/community_detection/multilayer_modularity.py` | Multilayer modularity calculation, supra-modularity matrix construction, and generalized Louvain algorithm (Mucha et al. 2010). |
| `algorithms/community_detection/multilayer_benchmark.py` | Synthetic benchmark generators for multilayer networks: mLFR, coupled ER, multilayer SBM with ground-truth communities. |
| `algorithms/statistics/statistics.py` | Computes fundamental network statistics: degree distribution, diameter, clustering coefficient, density, connected components, flow hierarchy. |
| `algorithms/statistics/topology.py` | Topological analysis including degree sequence, assortativity, small-world properties, and scale-free network testing. |
| `algorithms/statistics/enrichment.py` | Statistical enrichment analysis for identifying over-represented patterns, motifs, or node attributes in network subgraphs. |
| `algorithms/node_ranking/node_ranking.py` | Centrality measures including PageRank, betweenness, closeness, and eigenvector centrality adapted for multilayer networks. |
| `algorithms/multilayer_algorithms/` | Specialized algorithms for multilayer analysis: inter-layer coupling strength, layer similarity, aggregation strategies. |
| `visualization/multilayer.py` | Core visualization functions for multilayer networks: diagonal projection plots, supra-adjacency heatmaps, layered spring layouts, and 3D interactive renderings. |
| `visualization/drawing_machinery.py` | Low-level drawing primitives for node placement, edge routing, label rendering, and visual attribute mapping. |
| `visualization/layout_algorithms.py` | Layout computation algorithms including force-directed (FA2), spring, circular, and spectral layouts optimized for multilayer structures. |
| `wrappers/node2vec_embedding.py` | Generates Node2Vec embeddings for multilayer networks using biased random walks and skip-gram models. |
| `logging_config.py` | Centralized logging configuration providing structured logging across all modules with configurable verbosity levels. |

The `multi_layer_network` class in `multinet.py` is the heart of the library, providing methods like `add_layer()`, `add_nodes()`, `add_edges()`, `aggregate_layers()`, `get_layers()`, and `get_community()`. It maintains internal state including layer-to-integer mappings, node orderings for matrix representations, and cached computational results. The class integrates seamlessly with NetworkX by exposing a `.core_network` attribute containing the underlying `MultiDiGraph` or `MultiGraph` object.

## Dependencies and Ecosystem

| Category | Libraries | Purpose |
|----------|-----------|---------|
| **Graph computation** | `networkx>=2.5` | Core graph data structures, basic algorithms, standard formats |
| **Numerical processing** | `numpy>=0.8`, `scipy>=1.1.0` | Matrix operations, sparse matrices, linear algebra, optimization |
| **Data handling** | `pandas`, `bitarray>=2.0.0` | Tabular data manipulation, efficient boolean arrays |
| **Machine learning** | `scikit-learn`, `gensim` | Classification, clustering, embeddings (Word2Vec, Node2Vec) |
| **Visualization** | `matplotlib`, `seaborn`, `plotnine`, `plotly` | Static plots, heatmaps, grammar-of-graphics, interactive 3D visualizations |
| **Semantic web** | `rdflib>=0.1` | RDF graph parsing for semantic enrichment and ontology integration |
| **Compilation** | `cython>=0.20` | Performance-critical modules (Infomap bindings) |
| **Utilities** | `tqdm>0.0` | Progress bars for long-running computations |
| **Testing** | `pytest>=7.0`, `pytest-cov>=4.0` | Unit testing framework, coverage reporting |
| **Code quality** | `black>=23.0`, `ruff>=0.1.0`, `mypy>=1.0` | Formatting, linting, type checking (development only) |

**Python version support**: Python 3.8, 3.9, 3.10, 3.11, 3.12

**Optional dependencies**: Some features require additional packages installed separately:
- **Plotly** for interactive 3D visualizations (automatically detected)
- **Infomap binary** for advanced overlapping community detection (must be compiled from source or downloaded)
- **Deep learning frameworks** (TensorFlow, PyTorch) for neural network-based methods (not included by default)

The library follows a graceful degradation strategy: visualization modules check for Matplotlib availability and switch to server mode if unavailable, Infomap features degrade to Louvain if the binary is missing, and optional dependencies are imported within try-except blocks to prevent hard failures.

## Architecture and Data Flow

The library's computational architecture follows a pipeline pattern optimized for exploratory network analysis workflows. Data flow begins with network construction or ingestion, proceeds through analytical transformations, and culminates in visualization or export.

```
Data Sources (CSV, GraphML, GEXF, EdgeList, NetworkX)
    ↓
core.parsers → multi_layer_network object
    ↓
[Network Object with layers, nodes, edges, attributes]
    ↓
    ├→ algorithms.statistics.* → computed metrics (DataFrame)
    ├→ algorithms.community_detection.* → community assignments (dict)
    ├→ algorithms.node_ranking.* → centrality scores (dict)
    ├→ core.HINMINE.decomposition → meta-path features (matrix)
    └→ wrappers.node2vec → embeddings (matrix)
    ↓
    ├→ visualization.multilayer.* → rendered plots (Matplotlib/Plotly)
    ├→ core.parsers → exported files (GraphML, GEXF, pickle)
    └→ pandas.DataFrame → tabular reports (CSV)
```

**State management**: The `multi_layer_network` class maintains mutable state including:
- `core_network`: NetworkX graph object storing all nodes and edges
- `layer_name_map`: Bidirectional mapping between layer names and integer IDs
- `node_order_in_matrix`: Canonical ordering for matrix representations
- `embedding`: Cached node embedding matrix (if computed)
- `labels`: Node classification labels (if provided)

**Extensibility hooks**: Users can extend functionality by:
1. Subclassing `multi_layer_network` to add custom methods
2. Implementing custom parsers following the `parse_*()` function signature
3. Adding new layout algorithms to `visualization/layout_algorithms.py`
4. Defining custom centrality measures using the `.core_network` NetworkX object

**Caching mechanisms**: The library employs caching for expensive operations:
- HINMINE graph structures cache to `.{md5_checksum}` files to avoid re-parsing
- Computed layouts can be stored in network attributes for reuse
- Embeddings are stored in `.embedding` attribute after first computation

**Configuration**: Global behavior is controlled through:
- `logging_config.py`: Logging verbosity and output formats
- Constructor parameters on `multi_layer_network`: `directed`, `coupling_weight`, `label_delimiter`
- Environment variables: None currently used, but extensible

## Algorithms and Analytical Capabilities

### Core Network Statistics
- **Degree distributions**: In-degree, out-degree, degree sequences with power-law fitting
- **Clustering coefficients**: Global, local, and layer-specific clustering
- **Path-based metrics**: Diameter, average shortest path length, eccentricity
- **Connectivity**: Connected components, strongly/weakly connected analysis
- **Density and sparsity**: Edge density, maximum flow, minimum cuts
- **Assortativity**: Degree assortativity, attribute-based mixing patterns

### Multilayer Network Statistics (`multilayer_statistics.py`)
Comprehensive suite of 17 statistics for multilayer networks following Kivelä et al. (2014) and De Domenico et al. (2013):

- **Layer Density (ρₐ)**: `ρₐ = 2Eₐ/(Nₐ(Nₐ-1))` - Fraction of possible edges present in layer α
- **Inter-layer Coupling Strength (C^αβ)**: `C^αβ = (1/N) Σᵢ wᵢ^αβ` - Average weight of inter-layer connections between nodes in layers α and β
- **Node Activity (aᵢ)**: `aᵢ = (1/L) Σₐ 𝟙(vᵢ ∈ Vₐ)` - Fraction of layers where node i is active
- **Degree Vector (kᵢ)**: `kᵢ = (kᵢ¹, kᵢ², ..., kᵢᴸ)` - Node degree in each layer for versatility analysis
- **Inter-layer Degree Correlation (r^αβ)**: `r^αβ = corr(k^α, k^β)` - Pearson correlation of node degrees between layers α and β
- **Edge Overlap (ω^αβ)**: `ω^αβ = |Eₐ ∩ Eᵦ| / |Eₐ ∪ Eᵦ|` - Jaccard similarity of edge sets between layers
- **Layer Similarity (S^αβ)**: `S^αβ = ⟨Aₐ, Aᵦ⟩ / (‖Aₐ‖‖Aᵦ‖)` - Cosine similarity of adjacency matrices
- **Multilayer Clustering Coefficient (Cᴹ)**: `Cᵢᴹ = Tᵢ/Tᵢᵐᵃˣ` - Transitivity accounting for cross-layer triangles
- **Versatility Centrality (Vᵢ)**: `Vᵢ = Σₐ wₐ Cᵢᵅ` - Weighted centrality across all layers (De Domenico et al. 2015)
- **Interdependence (λ)**: `λ = ⟨d^ML⟩ / ⟨d^avg⟩` - Ratio of multilayer to single-layer shortest paths
- **Multilayer Modularity (Qᴹᴸ)**: `Q = (1/2μ) Σᵢⱼₐᵦ [(Aᵢⱼᵅ - γₐPᵢⱼᵅ)δₐᵦ + ωₐᵦδᵢⱼ] δ(gᵢᵅ, gⱼᵝ)` - Community quality across layers (Mucha et al. 2010)
- **Supra-Laplacian Spectrum (Λ)**: `ℒ = 𝒟 - 𝒜` - Eigenvalue spectrum of supra-Laplacian for diffusion analysis
- **Algebraic Connectivity (λ₂)**: Second smallest eigenvalue of supra-Laplacian (Fiedler value)
- **Inter-layer Assortativity (rᴵ)**: `r^αβ = cov(k^α, k^β)/(σₐσᵦ)` - Degree mixing patterns across layers
- **Entropy of Multiplexity (Hₘ)**: `Hₘ = -Σₐ pₐ log₂(pₐ)` where `pₐ = Eₐ/ΣₖEₖ` - Shannon entropy of layer diversity
- **Multilayer Motif Frequency (fₘ)**: `fₘ = nₘ / Σₖ nₖ` - Frequency of cross-layer subgraph patterns
- **Resilience (R)**: `R = S'/S₀` - Ratio of largest component size after perturbation to original

**Note**: Formulas verified against canonical literature (Mucha et al. 2010, De Domenico et al. 2013, Kivelä et al. 2014, Boccaletti et al. 2014) in October 2025.

Example usage:
```python
from py3plex.algorithms.statistics import multilayer_statistics as mls

# Calculate layer density
density = mls.layer_density(network, 'layer1')

# Node activity across layers
activity = mls.node_activity(network, 'node_A')

# Versatility centrality
versatility = mls.versatility_centrality(network, centrality_type='degree')

# Inter-layer correlation
correlation = mls.inter_layer_degree_correlation(network, 'layer1', 'layer2')

# Network resilience
resilience = mls.resilience(network, 'layer_removal', perturbation_param='layer1')
```

### Centrality Measures (Multilayer-Aware)
- **Degree centrality**: Node importance by connection count, layer-weighted variants
- **Betweenness centrality**: Nodes critical for inter-layer and intra-layer paths
- **Closeness centrality**: Average distance to all other nodes across layers
- **Eigenvector centrality**: Influence based on network connectivity structure
- **PageRank**: Web-page ranking adapted for multilayer networks with teleportation
- **Personalized PageRank (PPR)**: Query-based node importance with custom restart distributions

### Community Detection
- **Louvain algorithm**: Modularity optimization for non-overlapping communities (`community_louvain.py`)
- **Infomap**: Information-theoretic community detection supporting overlapping communities and multilayer structures (via C++ bindings)
- **Label propagation**: Semi-supervised community detection using known labels
- **Community ranking**: Scoring communities by internal cohesion and external separation

### Network Decomposition and Classification
- **Meta-path extraction**: Enumerate typed paths connecting node pairs in heterogeneous networks
- **Cycle enumeration**: Identify closed walks of specified lengths and type patterns
- **HINMINE decomposition**: Decompose heterogeneous networks into structural features for classification
- **Network-level classification**: Predict properties of entire networks using graph kernels

### Embedding Generation
- **Node2Vec**: Random walk-based embeddings with configurable walk length, return parameter (p), and in-out parameter (q)
- **Embedding visualization**: t-SNE, UMAP projections for high-dimensional embeddings
- **Link prediction**: Use embeddings to predict missing edges

### Temporal Analysis
- **Temporal multilayer networks**: Track edge activation times and evolution dynamics
- **Spreading processes**: Simulate information or disease propagation across layers
- **Dynamic community detection**: Track community stability over time

### Semantic Enrichment
- **Ontology integration**: Link network nodes to RDF ontologies for semantic annotation
- **Enrichment testing**: Statistical tests for over-represented ontology terms in subgraphs
- **Hedwig subgroup discovery**: Identify semantically coherent subgraphs using background knowledge

**Implementation notes**: Most algorithms are original implementations optimized for multilayer networks, often wrapping or extending NetworkX functions. Computationally intensive operations (e.g., Infomap) use Cython bindings to compiled C++ code. Statistical functions leverage NumPy vectorization. Community detection and centrality measures explicitly account for inter-layer edges and layer-specific parameters.

**Mathematical foundations**: The library implements algorithms from the network science literature, including Newman's modularity (Louvain), Rosvall's map equation (Infomap), Grover and Leskovec's Node2Vec biased random walks, and various centrality formulations adapted for multiplex networks as described in Kivelä et al. (2014) and De Domenico et al. (2013-2016).

## Development Environment

**Testing**: Use `make test` to run pytest with coverage reporting. Tests are in the `tests/` directory. CI runs on Python 3.8-3.12 across Ubuntu, macOS, and Windows.

**Development Workflow**: See `docs/development.md` for comprehensive development guide including Makefile commands, testing, and contributing guidelines.

**Key Commands**:
```bash
make setup        # Create virtual environment and install dependencies
make dev-install  # Install package in editable mode with dev dependencies
make format       # Auto-format code (isort + black + ruff --fix)
make lint         # Run linters (ruff + isort + black + mypy)
make test         # Run pytest with coverage reporting
make ci           # Run lint + test (full CI suite)
make docs         # Build Sphinx documentation
```

**For LLMs**: Use `make test` or `make lint` rather than directly invoking pytest or ruff. The Makefile handles tool detection and environment configuration automatically.

## Documentation

**Key Resources**:
- **README.md**: Minimalistic introduction, installation, quick start
- **docs/10min_tutorial.md**: 10-minute getting started tutorial
- **docs/development.md**: Development guide with Makefile commands, testing, contributing
- **docs/algorithm_selection_guide.md**: Algorithm selection and complexity
- **examples/**: 43 Python scripts demonstrating practical use cases
- **Sphinx docs**: [https://skblaz.github.io/py3plex/](https://skblaz.github.io/py3plex/) - API reference and guides

**Documentation Priority**:
1. `LLM.md` (this file) - Most comprehensive and current
2. `docs/` directory - Markdown tutorials and development guides
3. `examples/` directory - Working code examples
4. `README.md` - Quick start (minimalistic, points to other docs)
5. Sphinx documentation - API reference (may be incomplete)

## For LLMs

### 🧭 Suggested Reading Order

1. `README.md` - Library purpose and quick start
2. `LLM.md` (this file) - Comprehensive overview
3. `Makefile` - Build and test workflow
4. `py3plex/core/multinet.py` - Central `multi_layer_network` class
5. `examples/` - Real-world usage patterns
6. `tests/` - Expected behaviors and API contracts

### 💡 Embedding/Indexing Tips

- **Core logic**: Prioritize `core/multinet.py`, `algorithms/community_detection/`, `algorithms/statistics/`, and `visualization/multilayer.py`
- **Exclude**: Skip `docs/_build/`, `.git/`, `__pycache__/`, `*.pyc`, `example_images/`, and large binary files
- **Examples as docs**: Scripts in `examples/` are high-quality semantic examples
- **Type hints**: 65.4% coverage (70/107 maintainable modules). Refer to docstrings for modules without complete type coverage.

### 🔮 Key Insights

- **NetworkX foundation**: `.core_network` attribute is always a NetworkX `MultiDiGraph` or `MultiGraph`
- **Layer representation**: Layers encoded in edge keys; `label_delimiter` (default `"---"`) separates node IDs from layer IDs
- **Determinism**: Most algorithms are deterministic with fixed seeds. Louvain and Infomap use randomized search.
- **Sparse vs. dense**: Auto-detects sparsity and uses SciPy sparse matrices for large networks
- **Scalability**: Diagonal projection plots handle 10k+ nodes; force-directed layouts scale to ~5k nodes

**Development workflow**:
```bash
# Initial setup
make setup
make dev-install

# Code quality
make format    # Auto-format code
make lint      # Check code quality
make test      # Run tests with coverage
make ci        # Full CI checks (lint + test)
```

**Network construction**:
```python
from py3plex.core import multinet
network = multinet.multi_layer_network()
network.add_layer("layer1")
network.add_nodes([("A", "layer1"), ("B", "layer1")])
network.add_edges([(("A", "layer1"), ("B", "layer1"))])
```

**Loading from file**:
```python
network = multinet.multi_layer_network().load_network("data.graphml")
```

**Community detection**:
```python
from py3plex.algorithms.community_detection import community_wrapper
communities = community_wrapper.best_partition(network.core_network)
```

**Visualization**:
```python
from py3plex.visualization.multilayer import draw_multilayer_default
draw_multilayer_default([network], display=True)
```

## Metadata and Provenance

**Authors**: Blaž Škrlj (primary developer), Jan Kralj, Nada Lavrač (contributors and co-authors)

**Affiliation**: Jožef Stefan Institute (IJS), Ljubljana, Slovenia

**License**: MIT License (permissive open-source)

**Python compatibility**: Requires Python 3.8 or higher. Tested on Python 3.8, 3.9, 3.10, 3.11, 3.12.

**Platform support**: Cross-platform (Linux, macOS, Windows). Some compiled extensions (Infomap) require platform-specific builds.

**Version**: 0.95a (alpha/beta development stage, pre-1.0 release)

**Repository**: [https://github.com/SkBlaz/py3plex](https://github.com/SkBlaz/py3plex)

**Documentation**: [https://skblaz.github.io/py3plex/](https://skblaz.github.io/py3plex/)

**Installation**: Install from GitHub using `pip install git+https://github.com/SkBlaz/py3plex.git`

**Related publications**:
1. Škrlj, B., Kralj, J., & Lavrač, N. (2019). "Py3plex toolkit for visualization and analysis of multilayer networks." *Applied Network Science*, 4(1), 94. DOI: [10.1007/s41109-019-0203-7](https://doi.org/10.1007/s41109-019-0203-7)
2. Škrlj, B., Kralj, J., & Lavrač, N. (2019). "Py3plex: A Library for Scalable Multilayer Network Analysis and Visualization." *Complex Networks and Their Applications VII*, Springer, pp. 757-768. ISBN: 978-3-030-05411-3

**Citation format**:
```bibtex
@Article{Skrlj2019,
  author={Škrlj, Blaž and Kralj, Jan and Lavrač, Nada},
  title={Py3plex toolkit for visualization and analysis of multilayer networks},
  journal={Applied Network Science},
  year={2019},
  volume={4},
  number={1},
  pages={94},
  doi={10.1007/s41109-019-0203-7}
}
```

## Recommended Use Cases

Py3plex is particularly well-suited for:

- **Social network analysis**: Analyzing multi-platform social networks (Twitter + Facebook + LinkedIn), differentiating relationship types (friend, follower, colleague), tracking information diffusion across platforms
- **Biological networks**: Protein-protein interaction networks with multiple evidence types, gene regulatory networks with transcription/translation layers, metabolic pathway analysis
- **Citation and knowledge networks**: Scholarly citation networks with author-paper-venue layers, knowledge graph analysis with entity types and relation types, co-authorship and citation dynamics
- **Transportation and infrastructure**: Multi-modal transportation networks (bus, train, air), urban mobility patterns across modes, supply chain networks with different transaction types
- **Communication networks**: Email + Slack + meeting interaction networks, telecommunications with voice/data/SMS layers, organizational communication structure analysis
- **Temporal and dynamic networks**: Evolving social networks over time, dynamic community evolution, spreading process simulation (epidemics, information cascades)
- **Multiplex economic networks**: Trade networks with multiple commodities, financial transaction networks with different instrument types, ownership and board interlocking networks

The library excels in scenarios requiring: (1) visualization of networks too complex for standard tools, (2) structural feature extraction from heterogeneous networks for machine learning, (3) comparative analysis of multilayer networks across conditions or time points, (4) semantic enrichment of network data with domain ontologies.

## Known Limitations and Best Practices

### External Binary Dependencies
- **Infomap** and **Node2Vec** require external binaries not managed by pip
- **Mitigation**: Use absolute paths, check binary existence, or use pure-Python alternatives (e.g., Louvain, pecanpy)

### Licensing
- Main repository: BSD-3-Clause (permissive)
- Bundled Infomap code: AGPLv3 (copyleft, viral)
- **Impact**: Use Louvain or label propagation for commercial projects to avoid AGPL restrictions

### Reproducibility
- Many algorithms use randomization (Louvain, Infomap, layouts)
- **Mitigation**: Always set `random_state=42` in algorithms and use `np.random.seed(42)` globally

### Memory and Scalability
- ✅ **Sparse matrices**: Default for supra-adjacency (resolved)
- **Visualization**: Force layouts scale to ~5k nodes; use matrix visualizations for larger networks

### PyPI vs GitHub
- PyPI version (0.95, June 2023) lags behind GitHub
- **Recommendation**: Install from GitHub for latest features: `pip install git+https://github.com/SkBlaz/py3plex.git`

### Documentation Priority
1. `LLM.md` (this file) - Most comprehensive and current
2. `docs/` directory - Markdown tutorials and development guides
3. `examples/` directory - Working code examples
4. GitHub `README.md` - Quick start
5. Sphinx documentation - API reference (may be incomplete)

### Best Practices Summary
1. Install from GitHub for latest features
2. Check binary existence and use absolute paths
3. Avoid Infomap for commercial projects (use Louvain)
4. Always set random seeds for reproducibility
5. Use sparse matrices for large networks
6. Check node count before using force layouts
7. Prefer GitHub docs over hosted Sphinx docs
8. Pin versions in production
| Documentation staleness | Low | ✅ Resolved | Sphinx config updated to 0.95a, auto-build CI |
| NetworkX 3.x compatibility | Low | ✅ Resolved | Compatibility layer implemented |
| Type hints coverage | Medium | In progress | Partial coverage, mypy in CI but not enforcing |
| CI platform coverage | Low | ✅ Resolved | Ubuntu, macOS, Windows testing (Python 3.8-3.12) |

### Best Practices Summary

1. **Installation**: Install from GitHub for latest features and fixes
2. **Binary dependencies**: Check binary existence, use absolute paths
3. **Licensing**: Avoid Infomap for commercial/proprietary projects
4. **Reproducibility**: Always set random seeds in production code
5. **Memory**: Use sparse matrices, check network size before operations
6. **Visualization**: Check node count, use appropriate layout algorithms
7. **Documentation**: Prefer GitHub docs and examples over hosted Sphinx docs
8. **Updates**: Pin versions in production, test when upgrading

---

## Development Roadmap

**For detailed roadmap information**, see:
- **Quick Status**: `docs/ROADMAP_STATUS_SUMMARY.md` - Section-by-section completion status
- **Detailed Analysis**: `docs/OPEN_ISSUES_ANALYSIS_2025-10-14.md` - Comprehensive breakdown
- **Implementation Summaries**: `docs/ROADMAP_V2_SUMMARY.md`, `docs/ROADMAP_COMPLETION_2025-10-12.md`

**Key Completed Items** (2025):
- ✅ External binaries removed from repository (~5MB reduction)
- ✅ Unified random seeding (`get_rng()` helper)
- ✅ Sparse supra-adjacency matrices (default, with memory warnings)
- ✅ Multi-platform CI (Ubuntu, macOS, Windows; Python 3.8-3.12)
- ✅ Type hints (65.4% coverage, 70/107 modules)
- ✅ Modern build system (pyproject.toml, Makefile)
- ✅ Logging infrastructure
- ✅ CHANGELOG.md created
- ✅ Coverage badge and Codecov integration
- ✅ Automatic documentation building (GitHub Actions + Pages)
- ✅ Mypy type checking enforced in CI (all 112 source files pass)
- ✅ Documentation cleanup (October 2025) - Removed redundant temporary files, consolidated into README.md and LLM.md

**Top Remaining Priorities**:
1. Move AGPL Infomap code to separate optional package
2. Add deprecation warnings for legacy APIs
3. Prepare 1.0.0 release
4. Expand test coverage to 30%+
5. Standardize algorithm output schemas

**Current Focus**: Modernization Phase 2 (98% complete)

## Repository Status

**For detailed status information**, see:
- `docs/ROADMAP_STATUS_SUMMARY.md` - Concise status overview
- `docs/OPEN_ISSUES_ANALYSIS_2025-10-14.md` - Comprehensive breakdown

**Modernization Progress** (October 2025):
- Phase 1: ✅ Complete (bare except clauses, wildcard imports, Python 3.8+)
- Phase 2: ~98% Complete (logging, type hints 65.4%, test infrastructure, modern I/O, mypy enforcement)
- Phase 3: Planned (complete wildcard cleanup, 50%+ test coverage)
- Phase 4: Planned (100% type hints, 70%+ test coverage, performance optimization)

## Performance Optimization

**Recent Work** (October 2025):
- ✅ **Vectorized Multiplex Aggregation**: 8× speedup on 1M edges (`py3plex/multinet/aggregation.py`)
- See `docs/SPEC_A_IMPLEMENTATION_SUMMARY.md` for details

**Planned Optimizations**:
- Streaming supra-adjacency (2× speedup target)
- Backend registry for igraph/cugraph integration
- ForceAtlas2 layout modernization
- Comprehensive benchmark harness with CI integration
