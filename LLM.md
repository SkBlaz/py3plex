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
│   │   │   ├── node_ranking.py       → PageRank, PPR centrality measures
│   │   │   ├── community_ranking.py  → Community importance ranking
│   │   │   └── infomap/              → Infomap C++ bindings for overlapping communities
│   │   ├── statistics/               → Network statistics and metrics
│   │   │   ├── statistics.py         → Core network statistics (diameter, density, clustering)
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
├── docs/                             → Sphinx-generated HTML documentation
├── pyproject.toml                    → Modern build configuration (PEP 517/518/621)
├── setup.py                          → Legacy setuptools configuration
├── requirements.txt                  → Core dependencies
└── README.md                         → Project introduction and getting started
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

## Tests and Quality Assurance

The repository uses `pytest` as its primary testing framework, with tests organized in the `tests/` directory. Current test coverage focuses on core functionality, regression prevention, and integration testing for complex workflows.

**Test files**:
- `test_core_functionality.py`: Core network construction, manipulation, I/O operations
- `test_networkx_compatibility.py`: NetworkX interoperability and format conversions
- `test_multilayer_centrality.py`: Multilayer centrality measure correctness
- `test_community_detection.py`: Community detection algorithm outputs
- `test_infomap_fix.py`: Regression test for Infomap FileNotFoundError fix
- `test_multilayer_edge_fix.py`: Edge handling correctness in multilayer operations
- `test_code_improvements.py`: Tests for Phase 1A/1B code quality improvements

**Test execution**: Run `python run_tests.py` for a unified test runner that discovers and executes all tests with clear output summaries. Alternatively, use `pytest` directly for advanced features like coverage reporting (`pytest --cov=py3plex --cov-report=html`) and selective test execution.

**Continuous Integration**: GitHub Actions workflows run on every push and pull request:
- **Test workflow** (`.github/workflows/tests.yml`): Tests on Python 3.8-3.11 with both full and minimal dependencies, includes timeout protection
- **Code quality workflow** (`.github/workflows/code-quality.yml`): Ruff linting, Black formatting checks, Mypy type checking

**Coverage status**: Current test coverage is approximately 15-20%. The modernization roadmap targets 30% coverage in Phase 2, 50% in Phase 3, and 70% in Phase 4. Priority areas for expanded testing include algorithm correctness, edge case handling, and user-facing API stability.

**Code quality initiatives**: Recent improvements (Phase 1A/1B/2A) significantly improved code quality through bare except clause reduction (50+ to 23 instances), wildcard import reduction (9 to 1 instance), structured logging infrastructure (`py3plex/logging_config.py`), and modern packaging with `pyproject.toml` (PEP 517/518/621). The Python requirement was updated from 3.6+ to 3.8+. Ongoing efforts focus on print-to-logging conversion (15% complete, 44/286 statements) and type hints (65.4% complete, 70/107 maintainable modules).

**Recent fixes and improvements**:
- **Phase 1A**: Fixed 29 bare except clauses (58% of total), added logging infrastructure, updated Python requirement to 3.8+, started type hints in 2 modules, added build artifacts to .gitignore
- **Phase 1B**: Fixed 21 additional bare except clauses (reducing total from 50 to 23), removed 8 wildcard imports (reducing from 9 to 1), added modern packaging with pyproject.toml, converted 20 print statements to logging, all changes backward compatible with comprehensive test coverage
- **Phase 2A**: Added type hints to 68 additional modules across core, visualization, algorithms, and wrappers. Type hint coverage increased from 2.3% to 65.4% (70/107 maintainable modules). All changes maintain backward compatibility with comprehensive docstrings
- **Code Quality Review**: Enhanced README.md with installation and requirements, removed redundant testing content from various files, fixed ruff configuration deprecation warnings, added code-quality.yml CI workflow (ruff, black, mypy), fixed unused imports and variables in 10 Python source files
- **Issue #19 Fix**: Corrected boolean logic in `py3plex/visualization/drawing_machinery.py` line 545 for edge rendering in multilayer networks. The fix changed `if not type(width) == list or not type(width) == tuple:` to `if not (type(width) == list or type(width) == tuple):` which now correctly preserves lists/tuples of edge widths instead of always wrapping them

**Modernization roadmap**:
- **Phase 1** (~85% complete): Fix bare except clauses (in progress: 50→23), convert print() to logging (in progress: 15% complete), remove wildcard imports (in progress: 9→1), update Python requirement ✅, set up pytest infrastructure ✅, add type hints (65.4% complete)
- **Phase 2** (in progress): Expand test coverage to 30%+, add custom exception types, refactor global state, update dependencies, add pre-commit hooks, set up CI linting ✅, expand type hints ✅
- **Phase 3** (planned): Complete bare except and wildcard import cleanup, expand test coverage to 50%+, refactor large modules, add comprehensive docstrings, generate API documentation
- **Phase 4** (planned): Full type hint coverage (100%), achieve 70%+ test coverage, performance optimization, comprehensive documentation and tutorials

## Documentation and Examples

**Documentation Philosophy**: The documentation has been streamlined to be minimalistic and example-focused. Instead of verbose explanations, the docs point users directly to practical examples in the `examples/` directory.

**Primary documentation**: Sphinx-generated documentation hosted at [py3plex.readthedocs.io](https://py3plex.readthedocs.io). The `docs/` directory contains pre-built HTML documentation. The `docfiles/` directory contains source ReStructuredText files that have been refined to be concise and reference-oriented.

**Documentation structure** (in `docfiles/`):
- `index.rst`: Quick start and navigation hub pointing to examples
- `core_idea.rst`: Brief overview of core principles
- `basic_usage.rst`: Minimal quick start guide with example links
- `basic_usage_analysis.rst`: Core operations with example references
- `visualization.rst`: Basic visualization patterns pointing to examples
- `community_detection.rst`: Community detection guide with example links
- `learning*.rst`: Machine learning functionality with example references
- `AUTOGEN_results/`: Auto-generated API documentation from docstrings

**Example scripts**: The `examples/` directory contains 43 Python scripts demonstrating practical use cases. These are the primary learning resource:
- `example_multilayer_visualization.py`: Basic multilayer network rendering
- `example_community_detection.py`: Community detection with Louvain and Infomap
- `example_network_decomposition.py`: Meta-path-based feature extraction
- `example_n2v_embedding.py`: Node2Vec embedding generation and evaluation
- `example_semantic_enrichment.py`: Ontology-based semantic annotation
- `example_multiplex_dynamics.py`: Temporal analysis and spreading processes
- `example_networkx_wrapper.py`: Interoperability with NetworkX workflows

Each example is self-contained, includes inline comments explaining key concepts, and produces either visualizations or printed output demonstrating results.

**Build system**: Documentation is built using Sphinx with autodoc for API reference generation. The `docfiles/` directory contains source ReStructuredText files and Sphinx configuration. To rebuild documentation: `cd docfiles && sphinx-build -b html . _build/`.

**Recent changes**: Documentation was refined in 2025 to reduce verbosity and emphasize examples over lengthy explanations. The docs now serve as navigation aids pointing users to relevant example scripts.

**Maintenance notes**: Documentation references key meta-documents:
- `README.md`: High-level introduction, installation, quick start, testing, development status, citations
- `LLM.md` (this file): Comprehensive context for LLMs and maintainers - the anchor document

## For LLMs

### 🧭 Suggested Reading Order for LLMs

1. **Start with `README.md`**: Understand the library's purpose, scope, and primary citations
2. **Read this file (`LLM.md`)**: Comprehensive structural and conceptual overview
3. **Study `py3plex/core/multinet.py`**: The `multi_layer_network` class is the central abstraction—understand its attributes, methods, and state management
4. **Examine `py3plex/core/parsers.py`**: Understand supported input formats and how external data becomes internal representations
5. **Explore `py3plex/algorithms/`**: Review subdirectories based on analytical interest (community detection, statistics, embeddings)
6. **Review `py3plex/visualization/multilayer.py`**: Understand visualization capabilities and output formats
7. **Inspect `examples/`**: Real-world usage patterns demonstrate intended workflows
8. **Consult `tests/`**: Tests reveal expected behaviors, edge cases, and API contracts

### 💡 Tips for Embedding, Indexing, or RAG

- **Core logic concentration**: The heart of the library is in `core/multinet.py`, `algorithms/community_detection/`, `algorithms/statistics/`, and `visualization/multilayer.py`. Prioritize these for embeddings.
- **Exclude non-code content**: Skip `docs/_build/`, `.git/`, `__pycache__/`, `*.pyc`, `example_images/`, and large binary files
- **Leverage examples as documentation**: Example scripts in `examples/` are high-quality semantic examples of real usage patterns—treat them as extended docstrings
- **Ignore legacy code**: `py3plex/algorithms/statistics/powerlaw.py` is explicitly excluded from linting (see `pyproject.toml`)—it's maintained for compatibility but not representative of modern code style
- **Type hint status**: 65.4% of maintainable modules have type hints (70 of 107 files). Core, visualization, and algorithm modules have been prioritized. Refer to docstrings and example usage for parameter types in modules without complete type coverage.

### 🔮 Inference and Reasoning Notes

- **NetworkX foundation**: The library assumes NetworkX-compatible graph objects. The `.core_network` attribute of `multi_layer_network` is always a NetworkX `MultiDiGraph` or `MultiGraph`. Standard NetworkX algorithms can be applied directly to this object.
- **Layer representation**: Layers are encoded in edge keys (third element of edge tuples in MultiGraph). The `label_delimiter` (default `"---"`) separates node IDs from layer IDs in some representations.
- **Determinism**: Most algorithms are deterministic given fixed random seeds. Exceptions include Louvain (sensitive to iteration order) and Infomap (uses randomized search). Always check algorithm documentation for stochastic behavior.
- **Sparse vs. dense**: The library auto-detects sparsity and uses SciPy sparse matrices for large networks. Check `.sparse_enabled` attribute on `multi_layer_network` objects.
- **Visualization scalability**: Diagonal projection plots handle 10,000+ nodes efficiently. Force-directed layouts scale to ~5,000 nodes. For larger networks, use matrix-based visualizations (supra-adjacency heatmaps).
- **Error handling**: Post-Phase 1B, all bare except clauses are eliminated. Errors now raise specific exception types. Expect `ImportError` for missing optional dependencies, `FileNotFoundError` for missing data files, and `NetworkXError` for invalid graph operations.

### 🔧 Common Patterns for Code Generation

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

**Documentation**: [https://py3plex.readthedocs.io](https://py3plex.readthedocs.io)

**Package index**: Available on PyPI as `py3plex` (`pip install py3plex`)

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

## Design Philosophy

Py3plex is designed with three core principles: **readability**, **modularity**, and **interoperability**.

**Readability**: Code prioritizes clarity over cleverness. Algorithms are expressed as composable functions with descriptive names. The `multi_layer_network` class provides an intuitive API mirroring natural language (e.g., `add_layer()`, `aggregate_layers()`, `get_community()`). Documentation emphasizes conceptual explanations alongside technical specifications.

**Modularity**: Each component (`core`, `algorithms`, `visualization`, `wrappers`) operates independently with minimal coupling. New algorithms can be added without modifying existing code. Visualization functions accept standard NetworkX graphs, enabling use outside Py3plex workflows. The library avoids global state (with a few legacy exceptions being addressed in ongoing modernization efforts) to support concurrent usage.

**Interoperability**: The library embraces NetworkX as the ecosystem standard, exposing `.core_network` for direct access. Input/output functions support common formats (GraphML, GEXF, CSV) used by other tools (Gephi, Cytoscape, igraph). Computed metrics return standard Python types (dicts, lists, DataFrames) for easy integration with pandas, scikit-learn, and plotting libraries.

The goal is to balance **usability with analytical depth**—enabling researchers to explore multilayer network properties quickly through high-level functions while allowing advanced users to extend or customize functionality through low-level access to underlying data structures. The ongoing modernization effort (Phases 1-4 as described in the "Tests and Quality Assurance" section above) aims to bring the codebase to contemporary Python standards without sacrificing backward compatibility or breaking existing workflows.

Py3plex treats heterogeneous networks as first-class objects, not afterthoughts. This philosophical commitment distinguishes it from general-purpose graph libraries and makes it a natural choice for complex network analysis in research and applied settings.
