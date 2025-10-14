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
- `test_community_detection.py`: Community detection algorithm outputs (if exists)
- `test_infomap_fix.py`: Regression test for Infomap FileNotFoundError fix
- `test_multilayer_edge_fix.py`: Edge handling correctness in multilayer operations
- `test_code_improvements.py`: Tests for Phase 1A/1B code quality improvements
- `test_logging_conversion.py`: Tests for Phase 2C logging infrastructure and conversion
- `test_issue_19_fix.py`: Regression test for issue #19 edge rendering fix
- `test_io_schema.py`: Tests for new I/O system schema validation, formats, and converters (51 tests)
- `test_io_integration.py`: Integration tests for I/O system with realistic multilayer networks (4 tests)

**Test execution via Makefile** (recommended):
```bash
make test        # Run pytest with coverage reporting
make ci          # Run lint + test (full CI suite)
make coverage    # Open HTML coverage report in browser
```

The Makefile provides a unified interface for all development tasks and works in both local and CI environments. It automatically detects whether tools are installed in `.venv` or globally (as in CI).

**Alternative test execution**:
- `python run_tests.py`: Unified test runner with clear output summaries
- `pytest`: Direct pytest execution for advanced features like selective test execution

**Continuous Integration**: GitHub Actions workflows run on every push and pull request:
- **Test workflow** (`.github/workflows/tests.yml`): Uses `make setup` and runs tests on Python 3.8-3.12 with both full and minimal dependencies
- **Code quality workflow** (`.github/workflows/code-quality.yml`): Uses `make lint` for Ruff linting, Black formatting checks, isort, and Mypy type checking
- **Tutorial validation workflow** (`.github/workflows/tutorial-validation.yml`): ✅ **NEW** (2025-10-12) - Validates the 10-minute tutorial on Python 3.8, 3.10, and 3.12

**Coverage status**: Current test coverage is approximately 15-20%. The modernization roadmap targets 30% coverage in Phase 2, 50% in Phase 3, and 70% in Phase 4. Priority areas for expanded testing include algorithm correctness, edge case handling, and user-facing API stability. A new test suite (`test_logging_conversion.py`) has been added to verify the logging infrastructure.

## Makefile Build System

**Overview**: A production-grade Makefile provides a unified entrypoint for all development, testing, and publishing workflows. The Makefile streamlines common tasks behind memorable commands and ensures consistent execution between local development and CI environments.

**Key Features**:
- **Smart tool detection**: Automatically uses tools from `.venv/bin/` if available, otherwise falls back to globally installed tools (enabling CI compatibility)
- **Colorized output**: ANSI color codes for better readability (green for success, yellow for warnings, red for errors)
- **Virtual environment management**: `make setup` creates `.venv` and installs all dependencies
- **Cross-platform**: Works on Linux and macOS

**Available Targets** (13 total):
```bash
make help         # Display all available commands
make setup        # Create virtual environment and install dependencies
make dev-install  # Install package in editable mode with dev dependencies
make format       # Auto-format code (isort + black + ruff --fix)
make lint         # Run linters (ruff + isort + black + mypy)
make test         # Run pytest with coverage reporting
make coverage     # Open HTML coverage report in browser
make docs         # Build Sphinx documentation
make clean        # Remove build artifacts and caches
make build        # Build source and wheel distributions
make publish      # Upload to PyPI (requires TWINE_USERNAME/PASSWORD env vars)
make api-check    # Verify py3plex API exports expected symbols
make ci           # Run lint + test in sequence (full CI suite)
```

**Smart Tool Detection Example**:
```makefile
RUFF := $(shell if [ -f $(VENV_BIN)/ruff ]; then echo $(VENV_BIN)/ruff; else echo ruff; fi)
```
This allows the Makefile to work in both scenarios:
- **Local Development**: Uses `.venv/bin/ruff` when virtual environment exists
- **CI Environment**: Falls back to globally installed `ruff` (via `pip install`)

**CI Integration**: GitHub Actions workflows use Makefile targets:
```yaml
# .github/workflows/code-quality.yml
- name: Run lint checks via Makefile
  run: make lint

# .github/workflows/tests.yml
- name: Setup development environment via Makefile
  run: make setup
```

**Development Workflow**:
1. `make setup` - Initial environment setup (one-time)
2. `make dev-install` - Install package in editable mode
3. `make format` - Auto-format code before committing
4. `make lint` - Check code quality
5. `make test` - Run tests with coverage
6. `make ci` - Full CI checks before pushing

**For LLMs and Downstream Bots**: The Makefile provides a standardized interface. To run tests or lint code in this repository, use `make test` or `make lint` rather than directly invoking pytest or ruff. The Makefile handles tool detection and environment configuration automatically.

**Coverage status**: Current test coverage is approximately 15-20%. The modernization roadmap targets 30% coverage in Phase 2, 50% in Phase 3, and 70% in Phase 4. Priority areas for expanded testing include algorithm correctness, edge case handling, and user-facing API stability. A new test suite (`test_logging_conversion.py`) has been added to verify the logging infrastructure.

**Code quality initiatives**: Recent improvements (Phase 1A/1B/2A/2B/2C) significantly improved code quality through complete bare except clause elimination (50+ to 0 instances), wildcard import reduction (9 to 1 instance), structured logging infrastructure (`py3plex/logging_config.py`), and modern packaging with `pyproject.toml` (PEP 517/518/621). The Python requirement was updated from 3.6+ to 3.8+. Major progress made on print-to-logging conversion (74% complete, 170/229 statements) and type hints (65.4% complete, 70/107 maintainable modules).

**Recent fixes and improvements**:
- **Phase 1A**: Fixed 29 bare except clauses (58% of total), added logging infrastructure, updated Python requirement to 3.8+, started type hints in 2 modules, added build artifacts to .gitignore
- **Phase 1B**: Fixed 21 additional bare except clauses (reducing total from 50 to 23), removed 8 wildcard imports (reducing from 9 to 1), added modern packaging with pyproject.toml, converted 20 print statements to logging, all changes backward compatible with comprehensive test coverage
- **Phase 2A**: Added type hints to 68 additional modules across core, visualization, algorithms, and wrappers. Type hint coverage increased from 2.3% to 65.4% (70/107 maintainable modules). All changes maintain backward compatibility with comprehensive docstrings
- **Phase 2B**: Completed bare except clause cleanup - eliminated all remaining 23 instances (100% completion). Fixed 6 modules with specific exception types while preserving fallback behaviors. Added custom exception types module (`py3plex/exceptions.py`) with 13 domain-specific exceptions. Added pre-commit hooks configuration. Updated all dependencies to modern versions compatible with Python 3.8+ (numpy 1.19+, scipy 1.5+, matplotlib 3.3+, gensim 4.0+, scikit-learn 0.24+)
- **Phase 2C**: Major print→logging conversion from 15% to 74% (170/229 statements). Converted 13 modules including topology.py, benchmark_visualizations.py, node2vec_embedding.py, train_node2vec_embedding.py, community_ranking.py, entanglement.py, benchmark_nodes.py, layout_algorithms.py, drawing_machinery.py, bayesiantests.py, correlation_networks.py, critical_distances.py, and hedwig/__init__.py. Added `test_logging_conversion.py` to verify logging infrastructure. Identified and documented global state (only 2 instances in test code, legitimate use for multiprocessing).
- **Code Quality Review**: Enhanced README.md with installation and requirements, removed redundant testing content from various files, fixed ruff configuration deprecation warnings, added code-quality.yml CI workflow (ruff, black, mypy), fixed unused imports and variables in 10 Python source files
- **Issue #19 Fix**: Corrected boolean logic in `py3plex/visualization/drawing_machinery.py` line 545 for edge rendering in multilayer networks
- **I/O System Implementation**: Added comprehensive I/O system in `py3plex/io/` module with schema validation, multiple file formats (JSON, JSONL, CSV), and library converters (NetworkX, igraph). Includes 55 passing tests, dataclass-based schema with automatic referential integrity checking, deterministic serialization, and full backward compatibility. See `examples/example_new_io.py` for usage.

**Modernization roadmap**:
- **Phase 1** (✅ complete): Fix bare except clauses ✅, convert print() to logging (74% complete), remove wildcard imports (9→1 complete), update Python requirement ✅, set up pytest infrastructure ✅, add type hints (65.4% complete)
- **Phase 2** (~95% complete): Expand test coverage to 30%+ (in progress), add custom exception types ✅, refactor global state ✅ (identified and documented), update dependencies ✅, add pre-commit hooks ✅, set up CI linting ✅, expand type hints ✅, complete bare except cleanup ✅, print→logging conversion (74% complete), modern I/O system ✅, **coverage badge** ✅, **multi-platform CI** ✅, **auto doc building** ✅
- **Phase 3** (planned): Complete wildcard import cleanup, expand test coverage to 50%+, refactor large modules, add comprehensive docstrings, generate API documentation, complete print→logging conversion (remaining 26%)
- **Phase 4** (planned): Full type hint coverage (100%), achieve 70%+ test coverage, performance optimization, comprehensive documentation and tutorials

### Development Status

**Current Status**: Phase 2 Near Complete (~95% complete)

Recent achievements:
- ✅ Modern packaging added (pyproject.toml)
- ✅ Logging infrastructure created and tested
- ✅ Python requirement updated to 3.8+
- ✅ Bare except clauses: eliminated (50+ → 0, 100% reduction)
- 🔄 Wildcard imports: reduced from 9 → 1 (89% reduction)
- ✅ Print → Logging conversion: 74% complete (170/229 statements)
- ✅ Type hints: 65.4% complete (70/107 maintainable modules)
- ✅ Modern I/O system with schema validation (py3plex/io/)
- ✅ **Coverage badge and Codecov integration** (2025-10-13)
- ✅ **Multi-platform CI testing** (Ubuntu, macOS, Windows) (2025-10-13)
- ✅ **Automatic documentation building** (GitHub Actions + Pages) (2025-10-13)

**Phase 2 Achievements**:
- Converted 13 modules to use structured logging
- Added test suite for logging infrastructure
- Identified and documented global state (minimal, only 2 instances)
- Implemented comprehensive I/O system with 55 tests
- Updated documentation to reflect modernization progress

**Remaining Phase 2 Work**:
- Complete print→logging conversion (26% remaining, mostly in legacy and test code)
- Continue expanding test coverage toward 30%+ goal

## I/O System (`py3plex/io/`)

**Overview**: A modern I/O subsystem added to py3plex for multilayer graph serialization, validation, and interoperability. The system provides dataclass-based schema representations with automatic validation, multiple file format support, and bidirectional conversion with popular graph libraries.

**Architecture**:
```
py3plex/io/
├── __init__.py          # Public API exports
├── schema.py            # MultiLayerGraph, Node, Layer, Edge dataclasses (412 lines)
├── api.py               # read(), write(), registry functions (222 lines)
├── exceptions.py        # SchemaValidationError, ReferentialIntegrityError, FormatUnsupportedError
├── converters.py        # NetworkX, igraph converters (482 lines)
└── formats/
    ├── json_format.py   # JSON/JSONL readers/writers with gzip (249 lines)
    └── csv_format.py    # CSV edge list with sidecar files (299 lines)
```

**Key Classes**:
- `MultiLayerGraph`: Main container with automatic validation (referential integrity, JSON-serializability, edge uniqueness)
- `Node`, `Layer`, `Edge`: Typed dataclasses with to_dict()/from_dict() serialization
- Custom exceptions with clear error messages for validation failures

**File Formats**:
- **JSON**: Canonical format with full attribute preservation, deterministic output, gzip compression (.json, .json.gz)
- **JSONL**: Streaming format (one object per line) for memory efficiency, gzip support (.jsonl, .jsonl.gz)
- **CSV**: Edge list with required columns (src, dst, src_layer, dst_layer), optional sidecars (nodes.csv, layers.csv)

**Library Converters**:
- **NetworkX**: `to_networkx()`, `from_networkx()` with three projection modes (union, intersection, multiplex)
- **igraph**: `to_igraph()`, `from_igraph()` with union and multiplex modes

**API Functions**:
- `read(filepath, format=None, **kwargs)`: Load graph from file with auto-format detection
- `write(graph, filepath, format=None, deterministic=False, **kwargs)`: Save graph with optional deterministic sorting
- `register_reader(format_name, reader_func)`, `register_writer(format_name, writer_func)`: Plugin registration
- `supported_formats(read=True, write=True)`: List available formats

**Usage Example**:
```python
from py3plex.io import MultiLayerGraph, Node, Layer, Edge, read, write

# Create graph
graph = MultiLayerGraph()
graph.add_layer(Layer(id="social"))
graph.add_node(Node(id="alice", attributes={"age": 30}))
graph.add_edge(Edge(src="alice", dst="bob", src_layer="social", dst_layer="social"))

# Save/load
write(graph, "network.json", deterministic=True)
graph2 = read("network.json")

# Convert to py3plex core
from py3plex.io import to_networkx
from py3plex.core import multinet
G = to_networkx(graph, mode="union")
mlnet = multinet.multi_layer_network()
mlnet.core_network = G
```

**Testing**: 55 passing tests across `test_io_schema.py` (51 tests) and `test_io_integration.py` (4 tests). Comprehensive coverage of schema validation, format round-trips, library conversions, and error handling.

**Integration**: The I/O system is fully backward compatible—it's an opt-in module (`from py3plex.io import ...`) that coexists with existing I/O methods. Users can convert between the new schema-based format and the core `multi_layer_network` class via NetworkX as an intermediate representation.

**Example**: See `examples/example_new_io.py` for demonstrations of all features including CSV-to-py3plex workflow for computing centralities.


## Documentation and Examples

**Documentation Philosophy**: The documentation has been streamlined to be minimalistic and example-focused. The README.md is kept brief and points to comprehensive guides in the `docs/` directory.

**Documentation layers**:
1. **README.md**: Minimalistic introduction, installation, and quick start - points to other docs
2. **docs/**: Markdown tutorials and development guides
   - `10min_tutorial.md`: Comprehensive 10-minute introduction
   - `development.md`: Full development guide with Makefile commands, testing, contributing
   - `multilayer_modularity_tutorial.md`: Multilayer modularity guide
   - `multilayer_centrality_tutorial.md`: Centrality measures guide
   - `algorithm_selection_guide.md`: Algorithm selection and complexity
3. **docfiles/**: Sphinx source files (RST) that build to HTML documentation
   - `index.rst`: Documentation entry point with TOC
   - `*.rst`: ReStructuredText files that include markdown docs via mdinclude
   - `AUTOGEN_results/`: Auto-generated API documentation from docstrings
4. **examples/**: 43 Python scripts - the primary hands-on learning resource
5. **LLM.md**: Comprehensive context for LLMs and maintainers

**Primary documentation**: Sphinx-generated documentation hosted on GitHub Pages at [https://skblaz.github.io/py3plex/](https://skblaz.github.io/py3plex/).

**Documentation structure in docfiles/**:
- `index.rst`: Quick start and navigation hub
- `10min_tutorial.rst`: Links to `docs/10min_tutorial.md`
- `development.rst`: Links to `docs/development.md`
- `core_idea.rst`: Brief overview of core principles
- `basic_usage.rst`: Minimal quick start guide with example links
- `basic_usage_analysis.rst`: Core operations with example references
- `visualization.rst`: Basic visualization patterns pointing to examples
- `community_detection.rst`: Community detection guide with example links
- `learning*.rst`: Machine learning functionality with example references
- `AUTOGEN_results/`: Auto-generated API documentation from docstrings

**Example scripts**: The `examples/` directory contains 43 Python scripts demonstrating practical use cases. These are the primary learning resource:
- `tutorial_10min.py`: Executable version of the 10-minute tutorial
- `example_multilayer_visualization.py`: Basic multilayer network rendering
- `example_community_detection.py`: Community detection with Louvain and Infomap
- `example_network_decomposition.py`: Meta-path-based feature extraction
- `example_n2v_embedding.py`: Node2Vec embedding generation and evaluation
- `example_semantic_enrichment.py`: Ontology-based semantic annotation
- `example_multiplex_dynamics.py`: Temporal analysis and spreading processes
- `example_networkx_wrapper.py`: Interoperability with NetworkX workflows

Each example is self-contained, includes inline comments explaining key concepts, and produces either visualizations or printed output demonstrating results.

**Build system**: Documentation is built using Sphinx with autodoc for API reference generation. The `docfiles/` directory contains source ReStructuredText files and Sphinx configuration. To rebuild documentation: `make docs` (or `cd docfiles && sphinx-build -b html . _build/`).

**Recent changes**: Documentation was refined in 2025 to reduce verbosity and emphasize examples over lengthy explanations. The docs now serve as navigation aids pointing users to relevant example scripts. In October 2025, the README was streamlined to be minimalistic, with detailed development workflows moved to `docs/development.md`.

**Maintenance notes**: Documentation references key meta-documents:
- `README.md`: Minimalistic introduction, installation, quick start - points to other docs
- `docs/development.md`: Comprehensive development guide with Makefile commands, testing, contributing
- `docs/10min_tutorial.md`: 10-minute getting started tutorial
- `LLM.md` (this file): Comprehensive context for LLMs and maintainers - the anchor document

## For LLMs

### 🧭 Suggested Reading Order for LLMs

1. **Start with `README.md`**: Understand the library's purpose, scope, and primary citations
2. **Read this file (`LLM.md`)**: Comprehensive structural and conceptual overview
3. **Review the `Makefile`**: Understand the standardized build and test workflow
4. **Study `py3plex/core/multinet.py`**: The `multi_layer_network` class is the central abstraction—understand its attributes, methods, and state management
5. **Examine `py3plex/core/parsers.py`**: Understand supported input formats and how external data becomes internal representations
6. **Explore `py3plex/algorithms/`**: Review subdirectories based on analytical interest (community detection, statistics, embeddings)
7. **Review `py3plex/visualization/multilayer.py`**: Understand visualization capabilities and output formats
8. **Inspect `examples/`**: Real-world usage patterns demonstrate intended workflows
9. **Consult `tests/`**: Tests reveal expected behaviors, edge cases, and API contracts

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

## Multilayer Modularity and Community Detection

Py3plex includes a comprehensive implementation of **multilayer modularity maximization** based on Mucha et al. (2010), providing both the theoretical framework and practical tools for analyzing community structure in multilayer/multiplex networks.

### Mathematical Framework

The multilayer modularity quality function extends Newman's modularity to networks with multiple layers:

$$Q_{\text{multilayer}} = \frac{1}{2\mu} \sum_{i,j}\sum_{\alpha,\beta} \Big[ \big(A^{[\alpha]}_{ij} - \gamma^{[\alpha]}P^{[\alpha]}_{ij}\big)\,\delta_{\alpha\beta} + \delta_{ij}\,\omega_{\alpha\beta}\Big]\,\delta\big(g_{i,\alpha},\,g_{j,\beta}\big)$$

Where:
- $A^{[\alpha]}_{ij}$ is the adjacency matrix of layer α
- $P^{[\alpha]}_{ij}$ is the null model (typically $k_i^\alpha k_j^\alpha / 2m_\alpha$)
- $\gamma^{[\alpha]}$ is the resolution parameter for layer α (controls community size)
- $\omega_{\alpha\beta}$ is the inter-layer coupling strength (controls alignment across layers)
- $\delta_{\alpha\beta}$ = 1 if α=β, else 0 (Kronecker delta)
- $\delta_{ij}$ = 1 if i=j, else 0
- $\delta(g_{i,\alpha}, g_{j,\beta})$ = 1 if same community, else 0
- $\mu$ is the total edge weight in the supra-network

### Core Implementation Files

| File | Purpose |
|------|---------|
| `algorithms/community_detection/multilayer_modularity.py` | Implements multilayer modularity calculation, supra-modularity matrix construction, and generalized Louvain algorithm for community detection (433 lines) |
| `algorithms/community_detection/multilayer_benchmark.py` | Provides synthetic benchmark generators: multilayer LFR, coupled Erdős-Rényi, and multilayer stochastic block models with ground-truth communities (622 lines) |

### Key Features

**1. Multilayer Modularity Calculation**
- `multilayer_modularity()` - Calculate quality function with layer-specific resolution (γ) and inter-layer coupling (ω)
- `build_supra_modularity_matrix()` - Construct supra-modularity matrix for spectral methods
- Supports both uniform and layer-specific parameter configurations
- Returns modularity Q ∈ [-1, 1]

**2. Generalized Louvain Algorithm**
- `louvain_multilayer()` - Greedy modularity maximization adapted for multilayer networks
- Handles inter-layer dependencies through coupling terms
- Configurable coupling strength to control layer independence
- Random initialization for robust results

**3. Synthetic Benchmark Generators**
- `generate_multilayer_lfr()` - Multilayer LFR benchmark with:
  - Power-law degree and community size distributions
  - Controllable mixing parameter (μ) for intra/inter-community edges
  - Community persistence across layers (0.0 = independent, 1.0 = identical)
  - Node overlap (partial presence in layers)
  - Overlapping communities (multiple memberships)
- `generate_coupled_er_multilayer()` - Coupled/interdependent Erdős-Rényi models with:
  - Layer-specific edge probabilities
  - Controllable inter-layer coupling
  - Partial coupling for interdependent networks
- `generate_sbm_multilayer()` - Multilayer stochastic block models with:
  - Explicit block structure with intra/inter-block probabilities
  - Community evolution across layers
  - Clean ground-truth communities for validation

### Usage Examples

**Calculate multilayer modularity**:
```python
from py3plex.algorithms.community_detection.multilayer_modularity import multilayer_modularity

# Define communities (node-layer pairs to community IDs)
communities = {
    ('A', 'L1'): 0, ('B', 'L1'): 0, ('C', 'L1'): 1,
    ('A', 'L2'): 0, ('C', 'L2'): 0
}

# Calculate modularity with uniform parameters
Q = multilayer_modularity(network, communities, gamma=1.0, omega=1.0)

# Or with layer-specific resolution
gamma_dict = {'L1': 0.5, 'L2': 2.0}
Q = multilayer_modularity(network, communities, gamma=gamma_dict, omega=1.0)
```

**Detect communities with Louvain**:
```python
from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer

# Detect communities
communities = louvain_multilayer(
    network,
    gamma=1.0,      # Resolution parameter
    omega=1.0,      # Coupling strength (0=independent, ∞=identical)
    max_iter=100,
    random_state=42
)

# Result: {(node, layer): community_id, ...}
```

**Generate synthetic benchmarks**:
```python
from py3plex.algorithms.community_detection.multilayer_benchmark import (
    generate_multilayer_lfr,
    generate_coupled_er_multilayer,
    generate_sbm_multilayer
)

# Multilayer LFR with ground truth
network, ground_truth = generate_multilayer_lfr(
    n=100,
    layers=['L1', 'L2', 'L3'],
    mu=0.1,                    # 10% external edges
    avg_degree=10,
    community_persistence=0.8,  # 80% nodes keep community
    overlapping_nodes=10,      # 10 nodes in multiple communities
    seed=42
)

# Coupled ER for null model testing
network = generate_coupled_er_multilayer(
    n=100,
    layers=['L1', 'L2'],
    p=0.1,                     # Edge probability
    omega=1.0,                 # Coupling strength
    coupling_probability=0.5   # 50% nodes coupled
)

# Multilayer SBM with clean block structure
communities_gt = [{0,1,2,3,4}, {5,6,7,8,9}]
network, ground_truth = generate_sbm_multilayer(
    n=10,
    layers=['L1', 'L2'],
    communities=communities_gt,
    p_in=0.7,   # Intra-block probability
    p_out=0.05, # Inter-block probability
    community_persistence=0.9
)
```

### Parameters and Tuning

**Resolution (γ)**: Controls community size within layers
- Higher values → smaller, more granular communities
- Lower values → larger, coarser communities
- Can be set per layer for heterogeneous structure

**Coupling (ω)**: Controls community alignment across layers
- ω = 0: Layers completely independent (no alignment)
- ω ∈ (0, 5): Moderate coupling (allows variation)
- ω > 5: Strong coupling (forces similar communities)
- ω → ∞: Identical communities across all layers

### Performance Characteristics

- **Time Complexity**:
  - Modularity calculation: O((NL)²) where N=nodes, L=layers
  - Louvain algorithm: O(k × (NL)²) where k=iterations (typically small)
  - LFR generation: O(N × avg_degree × L)

- **Space Complexity**: O((NL)²) for supra-adjacency matrix
  - Uses scipy.sparse when available for memory efficiency

### Scientific Foundation

Implementation based on:
- **Mucha, P. J., et al.** (2010). "Community Structure in Time-Dependent, Multiscale, and Multiplex Networks." *Science* 328(5980): 876-878.
- **Kivelä, M., et al.** (2014). "Multilayer networks." *Journal of Complex Networks* 2(3): 203-271.
- **Lancichinetti, A., et al.** (2008). "Benchmark graphs for testing community detection algorithms." *Physical Review E* 78(4): 046110.
- **Granell, C., et al.** (2015). "Benchmark model to assess community structure in evolving networks." *Physical Review E* 92(1): 012805.

The implementation follows the GenLouvain MATLAB framework by Jeub et al., adapted for Python and integrated with py3plex's multilayer network data structures. It provides production-ready tools for temporal network analysis, multiplex social networks, and interdependent infrastructure networks.

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

## Design Philosophy

Py3plex is designed with three core principles: **readability**, **modularity**, and **interoperability**.

**Readability**: Code prioritizes clarity over cleverness. Algorithms are expressed as composable functions with descriptive names. The `multi_layer_network` class provides an intuitive API mirroring natural language (e.g., `add_layer()`, `aggregate_layers()`, `get_community()`). Documentation emphasizes conceptual explanations alongside technical specifications.

**Modularity**: Each component (`core`, `algorithms`, `visualization`, `wrappers`) operates independently with minimal coupling. New algorithms can be added without modifying existing code. Visualization functions accept standard NetworkX graphs, enabling use outside Py3plex workflows. The library avoids global state (with a few legacy exceptions being addressed in ongoing modernization efforts) to support concurrent usage.

**Interoperability**: The library embraces NetworkX as the ecosystem standard, exposing `.core_network` for direct access. Input/output functions support common formats (GraphML, GEXF, CSV) used by other tools (Gephi, Cytoscape, igraph). Computed metrics return standard Python types (dicts, lists, DataFrames) for easy integration with pandas, scikit-learn, and plotting libraries.

The goal is to balance **usability with analytical depth**—enabling researchers to explore multilayer network properties quickly through high-level functions while allowing advanced users to extend or customize functionality through low-level access to underlying data structures. The ongoing modernization effort (Phases 1-4 as described in the "Tests and Quality Assurance" section above) aims to bring the codebase to contemporary Python standards without sacrificing backward compatibility or breaking existing workflows.

Py3plex treats heterogeneous networks as first-class objects, not afterthoughts. This philosophical commitment distinguishes it from general-purpose graph libraries and makes it a natural choice for complex network analysis in research and applied settings.

## Known Limitations and Best Practices (2025 Update)

This section documents known limitations, compatibility concerns, and recommended practices for working with py3plex. These represent areas where users should exercise caution or employ specific workarounds.

### External Binary Dependencies and Portability

**Issue**: Several features depend on external compiled binaries that are not managed by pip/PyPI:

- **Infomap community detection**: Requires the Infomap binary (typically in `../bin/Infomap` or `./infomap`). The binary path is hardcoded in function signatures (e.g., `binary="../bin/Infomap"` in `community_wrapper.py`).
- **Node2Vec embeddings**: Requires a separate Node2Vec C++ binary (default: `./node2vec`).

**Impact**: Installation is fragile across operating systems and environments. Users must manually:
1. Download or compile the appropriate binary for their platform
2. Place it in the expected location or override the `binary` parameter
3. Ensure the binary has execute permissions on Unix-like systems

**Mitigation**:
- Always use absolute paths or explicitly set the `binary` parameter when calling these functions
- Consider using pure-Python alternatives when available (e.g., `community_louvain` instead of Infomap for basic community detection)
- For Node2Vec, consider using the `node2vec` or `pecanpy` Python packages as alternatives
- Check binary existence before running analyses to provide better error messages

**Example**:
```python
import os
from py3plex.algorithms.community_detection import community_wrapper as cw

# Bad: Relies on relative path assumption
# partition = cw.infomap_communities(network, binary="../bin/Infomap")

# Good: Check existence and use absolute path
infomap_path = "/usr/local/bin/Infomap"
if os.path.exists(infomap_path) and os.access(infomap_path, os.X_OK):
    partition = cw.infomap_communities(network, binary=infomap_path)
else:
    # Fallback to Louvain
    partition = cw.louvain_communities(network)
```

### Licensing Compatibility Concerns

**Issue**: Mixed licensing creates potential compatibility problems:
- **Main repository**: BSD-3-Clause (permissive, commercial-friendly)
- **Bundled Infomap code** (`py3plex/algorithms/infomap/`): AGPLv3 (copyleft, viral)

**Impact**: 
- AGPLv3 is incompatible with proprietary software distribution
- The "viral" nature of AGPL means any software that uses Infomap features must also be AGPL-licensed
- This creates ambiguity about py3plex's true licensing status
- Organizations with strict licensing policies may not be able to use py3plex if Infomap is bundled

**Mitigation**:
- For commercial or proprietary projects, avoid using Infomap-based functions
- Use alternative community detection algorithms (Louvain, label propagation) which are BSD-3-Clause
- Consider requesting a separate py3plex distribution without bundled Infomap code
- If using Infomap, ensure your project is compatible with AGPLv3 requirements (source disclosure, same license for derivative works)
- Contact Infomap authors for commercial licensing options if needed

**Current status**: This is a known issue without immediate resolution. Users must make informed decisions based on their use case.

### Reproducibility and Random Seeds

**Issue**: Many algorithms use randomization but examples and documentation don't consistently set random seeds:
- Community detection (Louvain, Infomap) uses randomized optimization
- Force-directed layout algorithms use random initialization
- Network generation functions have stochastic components
- Examples in the repository often omit seed parameters

**Impact**:
- Research results are not reproducible across runs
- Difficult to debug issues when results vary between executions
- Visualization positions change on every run, complicating visual comparison
- Benchmarking results may be inconsistent

**Mitigation**:
- Always set random seeds when reproducibility matters:
  ```python
  import random
  import numpy as np
  
  # Set seeds for reproducibility
  random.seed(42)
  np.random.seed(42)
  
  # For algorithms that accept random_state parameter
  from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
  communities = louvain_multilayer(network, random_state=42)
  ```
- For NetworkX-based algorithms, use NetworkX's seed parameter where available
- Be aware that some C++ binaries (Infomap) may not support seed setting from Python
- Document the seeds used in your analysis for reproducibility

**Examples needing improvement**:
- `examples/example_community_detection.py`: No seed set for Louvain or layout
- `examples/example_multilayer_visualization.py`: Force layout positions vary
- Many example scripts lack seed documentation

### NetworkX 3.x Compatibility

**Issue**: NetworkX 3.x introduced breaking changes that historically caused issues:
- API changes in graph methods (e.g., `degree()` return type)
- Deprecated functions removed
- Different default behaviors for some algorithms

**Current status**: Recent fixes have addressed major compatibility issues. The codebase now works with NetworkX 2.5+ including 3.x versions.

**Mitigation**:
- Keep NetworkX updated to the latest stable version (currently specified as `>=2.5` in dependencies)
- If encountering issues, check the `py3plex/core/nx_compat.py` module for compatibility wrappers
- Report any NetworkX-related issues to the project's issue tracker
- The library is actively maintained for NetworkX compatibility

### Memory and Scalability: Supra-Adjacency Matrices

**Status**: ✅ RESOLVED (as of 2025)

**Previous Issue**: The supra-adjacency matrix representation could cause memory problems on large multilayer networks:
- For a network with N nodes and L layers, the supra-adjacency matrix is (N×L) × (N×L)
- Dense matrix representation requires O(N²L²) memory
- Example: 10,000 nodes × 10 layers = 100,000 × 100,000 = 10 billion entries (~80 GB for float64)

**Current Implementation**: The library now handles large networks gracefully:
- ✅ **Sparse by default**: `get_supra_adjacency_matrix(mtype="sparse")` is the default behavior
- ✅ **Automatic memory warnings**: Dense matrices >1GB trigger warnings, >10GB trigger strong warnings
- ✅ **Size estimation**: Memory requirements are calculated before construction
- ✅ **Clear guidance**: Warning messages direct users to sparse alternatives

**Best Practices**:
```python
# Recommended: Use sparse matrices (default)
supra_adj = network.get_supra_adjacency_matrix(mtype="sparse")

# For small networks only: dense matrices
if num_nodes * num_layers < 1000:
    supra_adj_dense = network.get_supra_adjacency_matrix(mtype="dense")

# For very large networks: analyze per-layer
for layer in network.get_layers():
    layer_subgraph = network.subgraph(
        [n for n in network.get_nodes() if n[1] == layer]
    )
    # Analyze individual layer
```

**Warning Example**:
```python
# When requesting dense for large network:
ResourceWarning: Dense supra-adjacency matrix will be approximately 12.5 GB 
(5000 nodes × 10 layers = 50000 × 50000 matrix). This may cause memory issues. 
Consider using mtype='sparse' instead, or analyzing layers independently.
```

### Visualization Scalability Warnings

**Issue**: Visualization functions use O(N²) or O(N²L²) layout algorithms without warnings:
- Force-directed layouts (ForceAtlas2, spring layout) compute pairwise repulsive forces
- Time complexity is O(N²) per iteration, often 100-1000 iterations
- Interactive rendering can be slow for networks with >5,000 nodes
- The library does not check network size before starting layout computation

**Impact**:
- Long computation times (minutes to hours) for large networks
- UI freezing in interactive environments (Jupyter notebooks)
- Memory pressure from storing layout positions and intermediate states
- Users may not realize why their visualization is taking so long

**Mitigation**:
- Check network size before using force-directed layouts:
  ```python
  if len(network.get_nodes()) > 5000:
      # Use faster layout for large networks
      layout_algorithm = "circular"  # or "random", "spectral"
  else:
      layout_algorithm = "force"
  ```
- For large networks (>10,000 nodes):
  - Use matrix visualizations (heatmaps, adjacency matrices) instead
  - Consider network sampling or aggregation
  - Use hierarchical visualization (zoom into subgraphs)
  - Export to specialized tools (Gephi, Cytoscape) for layout
- Reduce iteration count for force layouts: `layout_parameters={"iterations": 50}`
- Use Barnes-Hut optimization when available (ForceAtlas2 with `barnesHutOptimize=True`)

**Recommended thresholds**:
- <1,000 nodes: Force layouts work well
- 1,000-5,000 nodes: Use reduced iterations, expect 10-60 seconds
- 5,000-10,000 nodes: Consider alternatives or sampling
- >10,000 nodes: Use non-force layouts or matrix visualizations

### PyPI Release Status and Version Lag

**Issue**: The PyPI release (version 0.95, June 2023) significantly lags behind the active GitHub development:
- GitHub repository has commits through 2025
- Recent features not available via `pip install py3plex`
- Bug fixes and improvements require installing from GitHub
- Documentation may reference features not in PyPI release

**Current features not in PyPI 0.95**:
- Comprehensive multilayer centrality measures (2025)
- Multilayer modularity maximization and Louvain algorithm (2025)
- Modern I/O system with schema validation (`py3plex/io/`, 2025)
- Phase 2 code quality improvements (logging infrastructure, type hints, exception handling)
- NetworkX 3.x compatibility fixes

**Mitigation**:
- **For latest features**, install from GitHub:
  ```bash
  pip install git+https://github.com/SkBlaz/py3plex.git
  ```
- **For stability**, use PyPI version but be aware of limitations:
  ```bash
  pip install py3plex
  ```
- Check the GitHub repository's commit history to understand what's new
- Monitor for future PyPI releases that may include recent improvements
- Consider contributing to help prepare a new PyPI release

**Status**: The development team is aware of this lag. A new PyPI release incorporating 2025 improvements is anticipated but not yet scheduled.

### Documentation Staleness

**Issue**: Some documentation references outdated versions and missing recent features:
- ~~Official docs mention "v0.80" in some places~~ ✅ **FIXED** - Sphinx config now shows 0.95a
- Recent additions (multilayer centrality, modularity algorithms) not fully documented in Sphinx docs
- Tutorial pages reference legacy API patterns
- GitHub README is more current than published docs

**Impact**:
- New users may learn outdated patterns
- Recent features (2025 multilayer centralities) only documented in GitHub markdown files
- API reference doesn't cover all modules

**Mitigation**:
- Prefer GitHub documentation over hosted Sphinx docs for recent features
- Check `docs/` directory in GitHub for markdown tutorials (e.g., `multilayer_centrality_tutorial.md`)
- Refer to `LLM.md` (this file) as the authoritative reference
- Look at example scripts in `examples/` directory for current usage patterns
- When in doubt, check the source code and inline docstrings

**Recommended documentation priority**:
1. `LLM.md` - Most comprehensive and current
2. `docs/` directory - Markdown tutorials and development guides (10min_tutorial.md, development.md)
3. `examples/` directory - Working code examples
4. GitHub `README.md` - Current quick start (minimalistic, points to other docs)
5. Sphinx documentation - API reference (may be incomplete)

### API Stability and Backward Compatibility

**Issue**: The library is in active development with evolving APIs:
- Version 0.95a (alpha) indicates pre-1.0 unstable status
- Recent additions like multilayer centrality are marked as new/experimental
- Some algorithm APIs may change as the library matures
- The modernization roadmap (Phases 1-4) involves ongoing refactoring

**Current status**:
- Core APIs (`multi_layer_network` class, basic visualization) are stable
- Recent additions (Phase 2 features) maintain backward compatibility
- No breaking changes are planned, but new features may refine APIs

**Mitigation**:
- Pin your py3plex version in requirements.txt for production use
- Test your code when upgrading py3plex versions
- Core functionality (network construction, basic algorithms) is reliable
- New features may see API refinements before 1.0 release
- Check release notes and commit messages when updating

### Community Testing and Issue Reporting

**Issue**: The issue tracker shows relatively few open issues despite known limitations:
- Low reported issue count may indicate:
  - Small active user community
  - Users working around issues without reporting
  - Issues not being tracked in GitHub
  - Limited CI/CD coverage for edge cases

**Mitigation**:
- Report issues you encounter to help improve the library
- Check closed issues for solutions to similar problems
- Use the examples directory as reference implementations
- Contribute fixes for issues you solve
- Engage with maintainers on GitHub for questions

### Summary Table of Limitations

| Limitation | Severity | Status | Notes |
|------------|----------|--------|-------|
| External binary dependencies | High | Known issue | Binaries in bin/, need unbundling |
| Mixed licensing (BSD/AGPL) | High | Known issue | Infomap code is AGPL, needs separation |
| Random seed reproducibility | Medium | ✅ Mostly resolved | Unified get_rng() helper, seeds in tests |
| Supra-adjacency memory use | High | ✅ Resolved | Sparse by default, warnings implemented |
| Visualization scalability | Medium | Needs improvement | No automatic size guards yet |
| PyPI version lag | Medium | Known issue | Install from GitHub recommended |
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

## Development Roadmap and Future Improvements

**Quick Reference Documents**:
- **Quick Status**: `docs/ROADMAP_STATUS_SUMMARY.md` - Section-by-section completion status and top priorities
- **Detailed Analysis**: `docs/OPEN_ISSUES_ANALYSIS_2025-10-14.md` - Comprehensive breakdown of all remaining issues
- **This Document**: Full roadmap with implementation details and examples

This section outlines planned and in-progress improvements to py3plex, addressing known limitations and enhancing the library's usability, scalability, and maintainability.

### 1. External Dependencies & Licensing Improvements

**Status**: ~~Planned~~ **Mostly Complete** | **Priority**: High | **Effort**: Large

**Goals**:
- Replace external Infomap binary with a pip-installable optional dependency (`infomap` package)
- Detect Infomap presence at runtime and raise clear, actionable `ImportError` with installation hints
- Split AGPL-encumbered integrations (Infomap, external binaries) into an optional plugin (`py3plex-infomap`) so the core package stays BSD-only
- Add a license compatibility matrix in README documenting which features require which licenses
- ~~Unbundle large/opaque binaries (e.g., `bin/node2vec`, `bin/Infomap`) from the repository~~ ✅ **COMPLETED**
- Prefer Python-native implementations (`node2vec`, `stellargraph`) or provide lazy download with checksums behind a `--with-extras` flag

**Impact**:
- Reduces repository size and installation complexity (~5MB reduction)
- Clarifies licensing for commercial/proprietary use
- Improves cross-platform portability (no binary compilation needed)
- Makes dependencies explicit and manageable via pip

**Current State** (Updated 2025-10-12):
- ✅ Infomap and node2vec binaries removed from `bin/` directory
- ✅ Runtime checks for binary availability with helpful error messages
- ✅ `bin/README.md` provides installation instructions and alternatives
- ✅ Examples updated to handle missing binaries gracefully with try/except
- ✅ `.gitignore` updated to prevent re-bundling binaries
- ⚠️ `py3plex/algorithms/community_detection/infomap/` still contains AGPLv3-licensed code (separate cleanup needed)
- ⚠️ Default binary paths now assume binaries in PATH or current directory

**Implementation Notes**:
```python
# ✅ IMPLEMENTED - Runtime checks with helpful errors
def infomap_communities(graph, binary="./infomap", **kwargs):
    if not os.path.exists(binary):
        raise FileNotFoundError(
            f"Infomap binary not found at '{binary}'. "
            "Please provide a valid path to the Infomap binary using the 'binary' parameter, "
            "or install Infomap from https://www.mapequation.org/infomap/. "
            "Alternatively, use Louvain community detection: "
            "partition = louvain_communities(network)"
        )
    # Implementation...
```

**Remaining Work**:
- Move AGPLv3-licensed Infomap code to separate optional package
- Add license compatibility matrix to README
- Create optional dependency groups in pyproject.toml

### 2. Reproducibility & Random Seed Management

**Status**: ~~Partially Complete~~ ~~Mostly Complete~~ **Complete** | **Priority**: High | **Effort**: Medium

**Goals**:
- ~~Introduce a unified random state helper function (`get_rng(seed)`) and use it across generators, embeddings, and layouts~~ ✅ **COMPLETED**
- ~~Ensure layout algorithms (force-directed, ForceAtlas2) accept and respect seed parameters~~ ✅ **COMPLETED**
- ~~Document seeding best practices with concrete examples in documentation~~ ✅ **COMPLETED** (in algorithm guide)
- ~~Make all community detection wrappers seedable (plumb `seed` argument through to Infomap, label propagation, and any RNGs)~~ ✅ **COMPLETED**
- Default to deterministic runs in all tests (ongoing improvement)

**Current State** (Updated 2025-10-12):
- ✅ `multilayer_modularity.louvain_multilayer()` accepts `random_state` parameter
- ✅ Unified `get_rng()` helper implemented in `py3plex.utils` module
- ✅ Layout algorithms expose seed parameters (`compute_force_directed_layout`, `compute_random_layout`)
- ✅ Documentation includes seeding best practices in algorithm selection guide
- ✅ `community_wrapper.infomap_communities()` now accepts `seed` parameter
- ✅ `run_infomap()` passes seed to Infomap binary with `--seed` flag
- ✅ Examples updated to demonstrate seed usage for reproducibility
- ⚠️ Tests don't all set seeds by default (gradual improvement)
- ℹ️ Infomap C++ binary seed support requires version 1.0+ with `--seed` flag

**Implementation Notes**:
```python
# ✅ IMPLEMENTED - Unified random state helper in py3plex/utils.py
from py3plex.utils import get_rng

rng = get_rng(seed=42)  # Returns np.random.Generator
random_values = rng.random(10)  # Use for reproducible randomness

# ✅ IMPLEMENTED - Seed support in community detection
partition = infomap_communities(network, seed=42)  # Reproducible communities

# ✅ IMPLEMENTED - Seed support in layouts
def compute_random_layout(g: nx.Graph, seed: Optional[int] = None):
    rng = get_rng(seed)
    pos = {n: rng.random(2) for n in g.nodes()}
    return pos
```

**Remaining Work**:
- Add seed parameters to remaining algorithms that use randomness
- Systematically update tests to use seeds for determinism

### 3. Scalability & Sparse Matrix Support

**Status**: ~~Planned~~ **Complete** | **Priority**: High | **Effort**: ~~Large~~ Complete

**Goals**:
- ~~Switch supra-adjacency matrix construction to sparse by default (`scipy.sparse`)~~ ✅ **COMPLETED**
- ~~Add `as_dense=False` parameter to supra construction methods~~ ✅ **COMPLETED** (implemented as `mtype="sparse"`)
- ~~Document memory complexity and add checks that refuse dense builds above N×L thresholds unless `force=True`~~ ✅ **COMPLETED** (warnings for >1GB, >10GB)
- ~~Provide scalable supra builders~~ ✅ **COMPLETED** (sparse CSR format)
- Add comprehensive performance benchmarks using `asv` (Airspeed Velocity) or timed pytest
- Add benchmarks on synthetic multiplexes (vary N, L, interlayer density)
- Provide chunked Kronecker assembly for extremely large networks (optional optimization)

**Current State**:
- ✅ **Sparse matrices are the DEFAULT**: `get_supra_adjacency_matrix(mtype="sparse")` returns scipy.sparse.csr_matrix
- ✅ **Memory warnings implemented**: Automatic warnings for large dense matrices (>1GB, >10GB thresholds)
- ✅ **Size estimation**: Memory requirements calculated before construction
- ✅ **Clear error messages**: Warning messages direct users to sparse alternatives
- ✅ **Well-documented**: Memory complexity documented, examples demonstrate usage

**Remaining Work** (optional optimizations):
- [ ] Add formal performance benchmark suite (asv or timed pytest)
- [ ] Add scalability benchmarks with synthetic networks
- [ ] Provide chunked Kronecker assembly for extremely large networks (defer until needed)

**Example Usage**:
```python
# Recommended: Use sparse matrices (default)
from py3plex.core import multinet
network = multinet.multi_layer_network()
# ... add layers, nodes, edges ...

# Get sparse supra-adjacency matrix (default)
supra_sparse = network.get_supra_adjacency_matrix(mtype="sparse")
# Returns scipy.sparse.csr_matrix

# For small networks only: dense matrices
if len(network.get_nodes()) * len(network.get_layers()) < 1000:
    supra_dense = network.get_supra_adjacency_matrix(mtype="dense")
    # Returns numpy.ndarray
```

**Note**: This section was previously marked as "Planned" but the functionality is already implemented and has been for some time. The roadmap status has been corrected to reflect reality.

### 4. API Standardization & Type Safety

**Status**: In Progress | **Priority**: Medium | **Effort**: Large

**Goals**:
- Normalize algorithm outputs to a single schema (e.g., `pandas.DataFrame` with columns: `node`, `layer`, `score`, `algorithm`, `params_hash`)
- Ensure stable, typed return types across all public APIs
- Refactor multilayer centrality implementations to accept uniform argument sets: `graph_or_multinet`, `layers=None|list`, `normalize`, `weighted`, `directed`
- Document formulas and literature references for each centrality method
- Add type hints across the entire public API and enforce with mypy in CI
- Publish minimal docstrings with parameter/return types

**Current State**:
- Algorithm outputs vary: some return dicts, others lists, some return tuples
- Community detection returns `Dict[node, community_id]` or `Dict[node, List[community_ids]]`
- Centrality functions have inconsistent parameter names and defaults
- Limited type hints in public APIs
- mypy not running in CI

**Implementation Example**:
```python
from typing import Dict, List, Optional, Union
import pandas as pd

def compute_multilayer_centrality(
    network: 'multi_layer_network',
    method: str = 'pagerank',
    layers: Optional[List[str]] = None,
    normalize: bool = True,
    weighted: bool = False,
    directed: bool = False,
    **kwargs
) -> pd.DataFrame:
    """Compute centrality scores for multilayer network.
    
    Args:
        network: Multilayer network object
        method: Centrality measure ('pagerank', 'betweenness', 'closeness')
        layers: Layer subset (None = all layers)
        normalize: Normalize scores to [0, 1] range
        weighted: Use edge weights if available
        directed: Treat graph as directed
        **kwargs: Method-specific parameters
        
    Returns:
        DataFrame with columns: node, layer, score, method, timestamp
        
    References:
        - PageRank: Page et al. (1999) "The PageRank Citation Ranking"
        - Multilayer extension: De Domenico et al. (2015)
    """
    # Implementation...
    return pd.DataFrame({
        'node': nodes,
        'layer': layers,
        'score': scores,
        'method': method,
        'timestamp': pd.Timestamp.now()
    })
```

### 5. Documentation & Examples Overhaul

**Status**: ~~In Progress~~ **Mostly Complete** | **Priority**: High | **Effort**: Medium

**Goals**:
- ~~Document algorithmic complexity (time/space) for each major routine (aggregation, supra build, centralities, community detection)~~ ✅ **PARTIALLY COMPLETED**
- ~~Add a "Pick the right tool" decision guide with bullets for algorithm selection~~ ✅ **COMPLETED** (docs/algorithm_selection_guide.md)
- ~~Update ReadTheDocs to current API~~ ✅ **FIXED** - Sphinx config updated to 0.95a (ReadTheDocs will reflect on next build)
- Auto-build and publish docs from `main` branch via GitHub Actions
- Include gallery-style runnable examples (doctests) that execute in CI
- Provide reproducible notebooks in `examples/` that run without local datasets (auto-fetch small CC-licensed graphs)
- Replace `.mat` file dependencies with CSV/edge-lists
- Add `make examples-smoke` to quickly validate all examples
- Create troubleshooting documentation for common pitfalls (missing binaries, OOM errors, NetworkX version mismatches)

**Current State** (Updated 2025-10-12):
- ✅ Comprehensive examples in `examples/` directory (44 scripts, including tutorial)
- ✅ Documentation version updated to 0.95a in Sphinx config
- ✅ Algorithm selection guide created with complexity analysis
- ✅ Complexity documented in key algorithms (louvain_multilayer, layout functions)
- ✅ **10-minute tutorial created** (`docs/10min_tutorial.md`)
- ✅ **Tutorial CI validation workflow created** (`.github/workflows/tutorial-validation.yml`)
- ✅ **Executable tutorial example** (`examples/tutorial_10min.py`)
- ✅ **Automatic doc building from CI** (`.github/workflows/docs.yml` with GitHub Pages deployment)
- ❌ Not all algorithms have complexity documentation

**Documentation Priorities**:
1. ~~Update version in Sphinx config~~ ✅ **COMPLETED**
2. ~~Add complexity tables to algorithm docstrings~~ ✅ **IN PROGRESS** (louvain_multilayer done)
3. ~~Create algorithm selection guide~~ ✅ **COMPLETED**
4. ~~Create 10-minute tutorial~~ ✅ **COMPLETED** (2025-10-12)
5. ~~Add CI workflow for tutorial validation~~ ✅ **COMPLETED** (2025-10-12)
6. ~~Set up ReadTheDocs webhook or GitHub Actions build~~ ✅ **COMPLETED** (2025-10-13)
7. Convert remaining examples to use downloadable datasets

### 6. Deprecation Management & Migration Paths

**Status**: Not Started | **Priority**: Medium | **Effort**: Small

**Goals**:
- Introduce deprecation shims with warnings for legacy APIs (e.g., old community wrapper signatures)
- Maintain `CHANGELOG.md` with migration notes and code examples
- Publish clear migration path for users on PyPI (0.95) vs. GitHub master
- Cut a new tagged release (e.g., `1.0.0`) with release notes, wheels for Python 3.9-3.12, and slim sdist (exclude datasets/binaries)
- Document breaking changes with concrete before/after examples

**Current State**:
- No `CHANGELOG.md` file exists
- No deprecation warnings in code
- Last PyPI release may be out of sync with GitHub
- No formal versioning/release process documented

**CHANGELOG.md Template**:
```markdown
# Changelog

All notable changes to py3plex will be documented in this file.

## [Unreleased]

### Added
- Sparse supra-adjacency matrix support (default)
- Unified `random_state` parameter across all algorithms
- Type hints for public API

### Changed
- **BREAKING**: `get_supra_adjacency_matrix()` now returns sparse by default
  - **Migration**: Add `as_dense=True` to restore old behavior
- Infomap is now an optional dependency
  - **Migration**: `pip install py3plex[infomap]`

### Deprecated
- `community_wrapper.old_infomap()` (use `infomap_communities()` instead)

### Removed
- Bundled binaries from `bin/` directory
  - **Migration**: Install `pip install py3plex[binaries]` or use pure-Python alternatives

### Fixed
- Memory issues with large supra-adjacency matrices
- Non-deterministic test failures due to missing seeds

## [0.95a] - 2025-01-XX

...
```

### 7. Visualization Hardening for Scale

**Status**: Planned | **Priority**: Medium | **Effort**: Medium

**Goals**:
- Default to downsampling or layer-wise faceting for large networks
- Add `max_nodes`/`max_edges` guards with helpful error messages
- Expose `seed` parameter for all layout algorithms
- Enable headless mode (Matplotlib `Agg` backend) in examples and tests
- Replace `plt.show()` in examples/tests with file outputs under `/tmp` or `./artifacts`
- Assert generated images exist to keep CI headless-friendly

**Current State**:
- Visualization functions may hang or crash on large networks (>10k nodes)
- No automatic size warnings before expensive layouts
- Layout algorithms don't consistently expose seed parameters
- Examples use `plt.show()`, which fails in headless CI environments
- Tests don't verify that visualizations actually generate output

**Implementation Notes**:
```python
def draw_multilayer_default(
    network,
    max_nodes=5000,
    layout='spring',
    seed=None,
    output_file=None,
    show=True
):
    """Draw multilayer network with scale guards.
    
    Args:
        network: Multilayer network
        max_nodes: Maximum nodes before refusing to draw (default: 5000)
        layout: Layout algorithm ('spring', 'kamada_kawai', 'random')
        seed: Random seed for reproducible layouts
        output_file: Save to file instead of showing (None = show interactively)
        show: Whether to call plt.show() (False for headless CI)
    """
    n_nodes = len(network.get_nodes())
    
    if n_nodes > max_nodes:
        raise ValueError(
            f"Network too large for visualization: {n_nodes} nodes > {max_nodes}. "
            "Consider: (1) filtering layers, (2) sampling nodes, "
            "(3) using aggregate view, or (4) increasing max_nodes."
        )
    
    # Use seed for layout
    pos = nx.spring_layout(network.graph, seed=seed)
    
    # ... drawing code ...
    
    if output_file:
        plt.savefig(output_file, bbox_inches='tight', dpi=150)
    
    if show and output_file is None:
        plt.show()
```

### 8. Testing & CI Expansion

**Status**: ~~Partially Complete~~ **Mostly Complete** | **Priority**: High | **Effort**: Medium

**Goals**:
- Add algorithmic unit tests with fixed seeds and tiny golden graphs (Louvain, Infomap, label propagation, centralities)
- Assert both partition structure and metric values within tolerances
- Expand CI to full matrix: Ubuntu/macOS/Windows × Python 3.9-3.12
- Run mypy in CI and enforce type checking
- Publish coverage badge to README
- Fail CI on presence of unpinned optional binaries
- Add round-trip tests for all supported I/O formats (GML, GraphML, GEXF, CSV, edge-lists)
- ~~Create tutorial validation workflow~~ ✅ **COMPLETED** (2025-10-12)

**Current State**:
- ✅ CI runs on Ubuntu with Python 3.8-3.12
- ✅ ruff and black run in CI
- ✅ pytest with coverage runs in CI
- ✅ **Tutorial validation workflow** (tests tutorial code on Python 3.8, 3.10, 3.12)
- ✅ **Coverage badge** added to README (Codecov integration)
- ✅ **macOS and Windows testing** added to CI (Python 3.10, 3.11, 3.12)
- ⚠️ mypy in CI but not enforcing (runs with `|| true`)
- ⚠️ Some tests are non-deterministic due to missing seeds (ongoing improvement)

**Current CI Matrix**:
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]
    exclude:
      # Skip expensive combinations
      - os: macos-latest
        python-version: '3.9'
      - os: windows-latest
        python-version: '3.9'
```

### 9. I/O Validation & Robustness

**Status**: Planned | **Priority**: Medium | **Effort**: Small

**Goals**:
- Add robust I/O validators with schema checks for multilayer edge lists
- Expect columns: `src`, `dst`, `layer`, optional `weight`
- Provide clear error messages on missing columns or malformed data
- Add round-trip tests for all supported formats (load → save → load → compare)
- Support standard edge-list formats from common network repositories (KONECT, NetworkRepository)

**Current State**:
- Parsers exist but may silently fail on malformed input
- No explicit schema validation
- Limited error messages for common mistakes (wrong column names, missing data)

**Example Validator**:
```python
def validate_multilayer_edgelist(df: pd.DataFrame, require_weight=False):
    """Validate multilayer edge list schema.
    
    Args:
        df: DataFrame to validate
        require_weight: Whether 'weight' column is mandatory
        
    Raises:
        ValueError: If schema is invalid
    """
    required_cols = {'src', 'dst', 'layer'}
    if require_weight:
        required_cols.add('weight')
    
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}\n"
            f"Expected: {required_cols}\n"
            f"Got: {set(df.columns)}\n"
            "See: https://py3plex.readthedocs.io/en/latest/formats.html"
        )
    
    # Additional checks: no NaN in required columns, valid layer names, etc.
```

### 10. CLI & Batch Workflows

**Status**: Not Started | **Priority**: Low | **Effort**: Medium

**Goals**:
- Provide CLI entry points: `py3plex-community`, `py3plex-supra`, `py3plex-visualize`
- Mirror Python API functionality for batch workflows
- Include common flags: `--seed`, `--layers`, `--weighted`, `--output`
- Support reading from standard input or file
- Enable scriptable, reproducible analysis pipelines

**Proposed CLI**:
```bash
# Community detection
py3plex-community input.edgelist --method louvain --seed 42 --output communities.csv

# Supra-adjacency construction
py3plex-supra input.edgelist --layers L1,L2,L3 --sparse --output supra.npz

# Visualization
py3plex-visualize input.edgelist --layout spring --seed 42 --output network.png
```

### Implementation Phases

To manage the scope of improvements, we propose a phased rollout:

**Phase 1: Critical Fixes (Q1 2025)**
- Add seed parameters to all algorithms
- Switch to sparse supra-adjacency by default
- Remove bundled binaries, add pyproject.toml extras
- Create CHANGELOG.md

**Phase 2: API Stabilization (Q2 2025)**
- Normalize algorithm outputs
- Add type hints and run mypy in CI
- Expand test coverage
- Update documentation to current version

**Phase 3: Scalability & Performance (Q3 2025)**
- Implement scalable supra builders
- Add performance benchmarks
- Harden visualizations for large networks
- Expand CI to macOS/Windows

**Phase 4: Polish & Release (Q4 2025)**
- Cut 1.0.0 release with wheels
- Publish coverage badge
- Complete documentation overhaul
- Add CLI entry points

### Progress Tracking

Track roadmap progress in GitHub Issues:
- Tag issues with `roadmap`, `priority:high`, `priority:medium`, `priority:low`
- Link PRs to roadmap items
- Update this section quarterly with completed items

**Completed Roadmap Items** (Updated 2025-10-14):
- ✅ Modern build system with pyproject.toml
- ✅ Makefile-based development workflow
- ✅ CI with code quality checks (ruff, black, isort)
- ✅ Multi-Python version testing (3.8-3.12)
- ✅ Multi-platform testing (Ubuntu, macOS, Windows)
- ✅ NetworkX 3.x compatibility
- ✅ Seed support across major algorithms (multilayer_modularity, layouts, infomap)
- ✅ CHANGELOG.md creation
- ✅ Python 3.12 in CI test matrix
- ✅ Optional dependency groups ([infomap], [algos], [viz])
- ✅ Sphinx documentation version updated to 0.95a
- ✅ Unified random seeding helper (`get_rng()` in py3plex.utils)
- ✅ Seed parameters added to layout algorithms (force_directed, random)
- ✅ Algorithm selection guide created (docs/algorithm_selection_guide.md)
- ✅ Complexity documentation added to key algorithms (louvain_multilayer)
- ✅ Bundled binaries removed from bin/ directory (~5MB reduction)
- ✅ Seed parameter added to infomap_communities wrapper
- ✅ Reproducibility work complete (Section 2 of roadmap - 95%)
- ✅ Coverage badge added to README (Codecov integration)
- ✅ Automatic documentation building (GitHub Actions + Pages)
- ✅ Test determinism improvements (added seeds to non-deterministic tests)
- ✅ Mypy configuration fixed (python_version 3.9)
- ✅ **Mypy exclusions for generated code** (build/, infomap.py SWIG bindings)
- ✅ **Sparse supra-adjacency matrices** (default behavior, with memory warnings)
- ✅ **License compatibility matrix in README** (BSD vs AGPL documentation)
- ✅ 10-minute tutorial created (docs/10min_tutorial.md)
- ✅ Tutorial validation workflow
- ✅ Bare except clause cleanup (100% elimination, 50+ → 0)
- ✅ Print→logging conversion (major progress: 82 remaining in source, most legitimate)
- ✅ Type hints expansion (65.4% coverage, 70/107 modules)
- ✅ Modern I/O system (py3plex/io/ with schema validation)
- ✅ Pre-commit hooks configuration

**Next Priorities** (sorted by impact, updated 2025-10-14):
1. ~~Remove bundled binaries → reduce repo size, improve licensing clarity~~ ✅ **COMPLETED** (2025-10-12)
2. ~~Unified seeding → ensure reproducibility~~ ✅ **COMPLETED** (get_rng() helper added, all major algorithms support seeds)
3. ~~Documentation update → reflect current capabilities~~ ✅ **COMPLETED** (algorithm guide + auto-build CI)
4. ~~Coverage badge → visibility into test coverage~~ ✅ **COMPLETED** (2025-10-13)
5. ~~Multi-platform CI → test on macOS/Windows~~ ✅ **COMPLETED** (2025-10-13)
6. ~~Add license compatibility matrix to README~~ ✅ **COMPLETED** (2025-10-14, document BSD vs AGPL features)
7. ~~Remove debug print and build artifacts~~ ✅ **COMPLETED** (2025-10-14, cleaned wrappers/__init__.py and removed 21 tracked build files)
8. **Move AGPL Infomap code to separate package** → licensing clarity (HIGH PRIORITY)
9. **Enforce mypy in CI** → improve type safety (HIGH PRIORITY, ~40 errors remaining after 51% reduction)
10. ~~Print→logging conversion~~ ✅ **LARGELY COMPLETED** (82 remaining are mostly legitimate - error handling, verbose flags)
11. **Prepare 1.0.0 release** → tag, wheels, release notes, PyPI update
12. Type hints + mypy enforcement → improve developer experience (ongoing, 65% → 100%)
13. ~~CHANGELOG.md creation → track changes systematically~~ ✅ **COMPLETED**
13. ~~Sparse supra-adjacency matrices → improve scalability~~ ✅ **COMPLETED** (already implemented, was misclassified!)
14. API standardization → consistent return types (Section 4 of roadmap)
15. Visualization hardening → max_nodes guards, headless mode

---

## Repository State Assessment (2025)

**Status Update**: October 14, 2025  
**Quick Reference**: See `docs/ROADMAP_STATUS_SUMMARY.md` for a concise status overview  
**Detailed Analysis**: See `docs/OPEN_ISSUES_ANALYSIS_2025-10-14.md` for comprehensive issue breakdown

This section provides an up-to-date assessment of which roadmap items have been completed, which are in progress, and which remain planned.

### ✅ Completed Items

**Build System & Development Workflow**
- Modern `pyproject.toml` with PEP 517/518/621 compliance
- Comprehensive Makefile with colorized output and helpful commands
- Development extras defined (`dev` optional dependencies)
- Black, ruff, isort, mypy configurations in pyproject.toml
- Pre-commit hooks support

**CI/CD Infrastructure**
- GitHub Actions workflows for tests and code quality
- Multi-Python version testing (3.8, 3.9, 3.10, 3.11)
- Automated linting with ruff, black, isort in CI
- Test execution via pytest with coverage tracking
- Both full and minimal dependency test matrices

**Scalability Features**
- **Sparse supra-adjacency matrices**: Already implemented! `get_supra_adjacency_matrix(mtype="sparse")` is the default
- Memory usage warnings for large dense matrices (>1GB, >10GB thresholds)
- Automatic size estimation before dense matrix construction
- Clear warning messages directing users to sparse alternatives

**NetworkX Compatibility**
- NetworkX 3.x compatibility layer implemented (`nx_compat.py`)
- Tests for NetworkX compatibility exist
- Shim utilities for G.edges(data=...) semantics

**Code Quality & Standards**
- Consistent code formatting with Black
- Linting rules configured and enforced
- Some type hints present in core modules
- Docstrings with parameter descriptions

**Testing Infrastructure**
- Test suite with pytest framework
- Coverage reporting configured
- Integration tests for I/O operations
- Community detection algorithm tests
- Multilayer centrality tests
- Multilayer modularity tests with benchmarks

### 🟡 Partially Completed Items

**Random Seed Support**
- ✅ `multilayer_modularity.louvain_multilayer()` accepts `random_state` parameter
- ✅ Tests use fixed seeds in many places
- ✅ Unified `get_rng()` helper function implemented in `py3plex.utils`
- ✅ Layout algorithms expose seed parameter (`compute_force_directed_layout`, `compute_random_layout`)
- ✅ `infomap_communities()` now accepts seed parameter (2025-10-12)
- ✅ `run_infomap()` passes seed to Infomap binary with `--seed` flag
- ✅ Examples demonstrate seed usage for reproducibility
- ⚠️ Not all algorithms use the unified helper yet (ongoing improvement)

**Documentation**
- ✅ Comprehensive `LLM.md` with development context
- ✅ 43 working examples in `examples/` directory
- ✅ Docstrings present in major functions
- ✅ Sphinx config updated to version 0.95a
- ✅ Algorithm selection guide created (`docs/algorithm_selection_guide.md`)
- ✅ Complexity documented in key algorithms (e.g., `louvain_multilayer`)
- ✅ **Automatic doc building from CI** (`.github/workflows/docs.yml`)
- ❌ Algorithmic complexity not systematically documented across all functions

**Type Hints**
- ✅ Some type hints in new code (e.g., `community_wrapper.py`)
- ✅ Mypy configured in pyproject.toml (fixed to use Python 3.9)
- ✅ Type hints added to additional modules (`utils.py`, layout algorithms, node2vec wrapper improvements)
- ⚠️ Mypy running in CI but not enforcing (uses `|| true`)
- ❌ Type hints not comprehensive across public API
- ❌ Return types not fully annotated

**External Binary Handling**
- ✅ Good error messages when binaries not found
- ✅ Path validation and permission checks
- ✅ Suggestions for alternatives in error messages
- ✅ Binaries removed from `bin/` directory (2025-10-12, ~5MB reduction)
- ✅ `bin/README.md` with installation instructions and alternatives
- ✅ Examples updated to handle missing binaries gracefully
- ✅ `.gitignore` prevents re-bundling binaries
- ✅ **Optional dependency groups** added to pyproject.toml ([infomap], [algos], [viz])
- ⚠️ AGPL-licensed Infomap code still bundled in source tree (needs separate cleanup)

### ❌ Not Started Items

**Licensing & Dependencies**
- ⚠️ License compatibility matrix in README (high priority)
- ⚠️ Separate `py3plex-infomap` plugin package (high priority)
- ✅ ~~`pyproject.toml` extras for `[infomap]`, `[algos]`, `[visual]`~~ **COMPLETED** (extras exist)
- ❌ AGPL code separation from BSD code (high priority)

**API Standardization**
- ❌ Standardized output schema (DataFrame with node/layer/score/algorithm)
- ❌ Algorithm outputs still vary (dicts, lists, tuples)
- ❌ Centrality functions have inconsistent signatures
- ❌ No formulas or references in algorithm docstrings (partially done)

**Release Management**
- ✅ `CHANGELOG.md` file exists
- ❌ No deprecation warnings or shims
- ❌ No clear migration path documented (needs migration guide)
- ❌ No 1.0.0 release plan
- ⚠️ PyPI package outdated (last release June 2023)

**Visualization Hardening**
- ❌ No automatic downsampling for large networks
- ❌ No `max_nodes`/`max_edges` guards (only memory warnings for matrices exist)
- ✅ Layout algorithms expose seed parameter (force_directed, random)
- ❌ Examples still use `plt.show()` instead of saving to files
- ❌ No headless mode enforcement in tests

**Performance & Benchmarking**
- ❌ No formal performance benchmark suite (asv or similar)
- ❌ No scalability benchmarks with synthetic networks
- ❌ No chunked Kronecker or memory-mapped supra builders (optional optimization)

**I/O Validation**
- ⚠️ New I/O system (`py3plex/io/`) has schema validation, but legacy parsers don't
- ❌ No explicit column name checking in legacy parsers
- ❌ No round-trip tests for all formats in legacy system
- ❌ Error messages could be more helpful in legacy parsers

**CLI Tools**
- ❌ No command-line entry points
- ❌ No batch workflow scripts
- ❌ No `py3plex-community`, `py3plex-supra`, etc. commands

**Testing Completeness**
- ✅ Multi-platform CI (macOS, Windows, Ubuntu)
- ✅ Multi-Python version (3.8-3.12)
- ✅ Coverage badge published
- ❌ Tests may not fail on unpinned binaries (can improve)
- ⚠️ Round-trip tests for all I/O formats (partially done in new system)

### Summary Statistics

**Updated**: October 14, 2025

- **Total Roadmap Items**: 50 identified across 10 major categories
- **Completed**: 20 items (40%)
- **In Progress**: 10 items (20%)
- **Not Started**: 20 items (40%)

**Roadmap Section Completion**:
- Section 1 (External Dependencies): 70% complete (binaries removed, AGPL code needs separation)
- Section 2 (Reproducibility): 95% complete (unified seeding mostly done, minor cleanup remaining)
- Section 3 (Scalability): 90% complete (sparse matrices already implemented and default!)
- Section 4 (API Standardization): 50% complete (type hints 65%, schema standardization needed)
- Section 5 (Documentation): 80% complete (auto-build CI done, complexity docs needed)
- Section 6 (Deprecation Management): 10% complete (CHANGELOG exists, deprecation warnings needed)
- Section 7 (Visualization Hardening): 30% complete (seed support done, size guards needed)
- Section 8 (Testing & CI): 90% complete (multi-platform CI done, mypy errors reduced 51%, near enforcement)
- Section 9 (I/O Validation): 40% complete (new I/O system exists, legacy parsers need validation)
- Section 10 (CLI Tools): 0% complete (not started)

**Detailed Analysis**: See `docs/OPEN_ISSUES_ANALYSIS_2025-10-14.md` for comprehensive breakdown of remaining work, priority matrix, and actionable recommendations.

### Priority Recommendations

**Updated**: October 14, 2025

Based on impact and current state, the recommended priority order is:

1. **High Priority, Quick Wins** (1-2 days each):
   - ~~Add CHANGELOG.md~~ ✅ **COMPLETED**
   - ~~Update Sphinx version to 0.95a~~ ✅ **COMPLETED**
   - ~~Add pyproject.toml extras ([infomap], [algos], [viz])~~ ✅ **COMPLETED**
   - ~~Add Python 3.12 to test matrix~~ ✅ **COMPLETED**
   - ~~Add license compatibility matrix to README~~ ✅ **COMPLETED** (document BSD vs AGPL features)
   - **Enforce mypy in CI** - **IN PROGRESS** ⚠️ (82 → 40 errors fixed, 51% reduction! Remaining 40 errors need attention before full enforcement)

2. **High Priority, Medium Effort** (3-7 days each):
   - ~~Unified random state helper and consistent seeding~~ ✅ **COMPLETED** (get_rng() helper added)
   - ~~Unbundle binaries from repository~~ ✅ **COMPLETED** (binaries removed from bin/)
   - **Move AGPL Infomap code to separate optional package** (licensing clarity)
   - ~~Complete print→logging conversion~~ ✅ **LARGELY COMPLETED** (82 remaining are mostly legitimate - error handling, verbose flags, examples)
   - **Add deprecation warnings for legacy APIs** (prepare for 1.0.0)
   - **Prepare 1.0.0 release** (tag, wheels, release notes, PyPI update)

3. **Medium Priority, High Impact** (1-2 weeks each):
   - **Standardize algorithm output schema** (DataFrame-based, consistent return types)
   - **Expand type hints to 100% of public API** (currently 65.4%)
   - ~~Create "Pick the right tool" guide~~ ✅ **COMPLETED** (algorithm_selection_guide.md)
   - **Create comprehensive algorithmic complexity documentation** (systematic across all algorithms)
   - **Visualization hardening** (max_nodes guards, headless mode, file outputs instead of plt.show())

4. **Lower Priority** (can defer):
   - CLI entry points (nice-to-have, 1 week)
   - Performance benchmark suite with asv (can defer, 2 weeks)
   - ~~macOS/Windows CI~~ ✅ **COMPLETED** (multi-platform testing active)
   - Advanced supra builders (chunked Kronecker, memory-mapped - defer until needed, 2 weeks)
   - I/O format round-trip tests (can defer, 3-5 days)

### Recent Improvements (Post-LLM.md Creation)

The repository has seen significant improvements since the original limitations were documented:

- Sparse matrix support is now the default and well-implemented
- Memory warnings protect users from OOM errors
- CI infrastructure is robust with multi-version testing (3.8-3.12)
- Modern Python tooling (black, ruff, pytest) is fully integrated
- NetworkX 3.x compatibility issues have been resolved
- Code quality has improved with consistent formatting
- **NEW (2025-10-12)**: CHANGELOG.md added for systematic change tracking
- **NEW (2025-10-12)**: Python 3.12 added to CI test matrix
- **NEW (2025-10-12)**: Optional dependency groups added ([infomap], [algos], [viz])
- **NEW (2025-10-12)**: Sphinx documentation version updated to 0.95a
- **NEW (2025-10-12)**: README.md updated with optional dependency installation instructions
- **NEW (2025-10-13)**: Coverage badge and Codecov integration added
- **NEW (2025-10-13)**: Multi-platform CI testing (Ubuntu, macOS, Windows)
- **NEW (2025-10-13)**: Automatic documentation building via GitHub Actions
- **NEW (2025-10-14)**: Comprehensive open issues analysis created (`docs/OPEN_ISSUES_ANALYSIS_2025-10-14.md`)
- **NEW (2025-10-14)**: Roadmap statistics corrected (40% complete, not 30%)
- **NEW (2025-10-14)**: Section 3 (Scalability) status corrected to "Complete" (sparse matrices already implemented)
- **NEW (2025-10-14)**: **License compatibility matrix added to README** (BSD vs AGPL feature documentation)
- **NEW (2025-10-14)**: **Mypy configuration improved** (exclude build/ and SWIG-generated files, 209→82 errors)
- **NEW (2025-10-14)**: **Major mypy error reduction** - Fixed 42 type errors (82→40 errors, 51% reduction). Resolved missing imports, type annotations, broken references, and type incompatibilities across 16 files. Remaining 40 errors are mostly complex type issues detailed below.
- **NEW (2025-10-14)**: **Build artifact cleanup** - Removed 21 build artifact files that were incorrectly tracked in git (`py3plex/algorithms/build/`, `py3plex/algorithms/community_detection/build/`). .gitignore already has proper `build/` exclusion patterns.
- **NEW (2025-10-14)**: **Debug print statement removed** - Removed debug print("wrappers imported") from `py3plex/wrappers/__init__.py` that was causing noise on every import.

**Remaining Mypy Errors** (40 errors in 18 files):
- **Error types**: no-any-return (9), assignment (9), index (4), attr-defined (4), var-annotated (4), return-value (2), list-item (2), call-arg (2), others (4)
- **Files affected**: Core modules (multinet.py, converters.py, nx_compat.py), I/O system (io/converters.py, io/api.py), community detection algorithms (5 files), statistics (4 files), wrappers (2 files), visualization (2 files)
- **Next steps**: Fix no-any-return errors with explicit casts, resolve assignment incompatibilities, correct index types, add missing type annotations, then remove `|| true` from Makefile to enable full CI enforcement
- **Estimated effort**: 1-2 days to complete all fixes and enable enforcement

**Print Statement Status** (as of 2025-10-14):
- **Total remaining**: 82 print statements in source code (excluding tests and examples)
- **Primary sources**: `powerlaw.py` (25 statements - legitimate for statistics library), Infomap examples (26 statements - legitimate), error handling and verbose output (31 statements - mostly legitimate)
- **Status**: Most remaining print statements are legitimate (error messages, verbose output with flags, or in example code). Only 2-3 debug prints identified for cleanup in future work.

The main remaining gaps are in **licensing clarity** (AGPL code separation), **API standardization** (consistent return types), **type safety** (100% coverage + mypy enforcement), and **release management** (1.0.0 preparation). The technical foundation is strong, and most improvements are now about polish, user experience, and maintainability rather than fundamental architectural changes.

---

## Performance Optimization Initiative (2025-10-14)

### ✅ Completed Specifications

#### 🧩 **Spec A — Vectorized Multiplex Aggregation** ✅ **COMPLETE**

**Status**: Implemented and tested  
**Module**: `py3plex/multinet/aggregation.py`  
**Tests**: `tests/test_aggregation.py`  
**Benchmarks**: `benchmarks/bench_aggregation.py`

**Implementation**:
- ✅ Created `aggregate_layers(edges, weight_col="w", reducer="sum", to_sparse=True)` function
- ✅ Accepts DataFrame or ndarray with `(layer, src, dst, weight)` columns
- ✅ Replaced Python loops with vectorized NumPy/SciPy sparse operations
- ✅ Supports reducers: `sum`, `mean`, `max`
- ✅ Returns sparse CSR by default, dense ndarray optional
- ✅ Added comprehensive test suite (24 tests covering correctness, validation, performance, edge cases)
- ✅ Added benchmark harness with pytest-benchmark integration

**Performance Results**:
- ✅ **8.04× speedup** on 1M edges, 4 layers (target: ≥3×) ✅
- ✅ 7.65× speedup on 100K edges
- ✅ 7.35× speedup on 10K edges
- ✅ Vectorized implementation: ~0.20s for 1M edges (vs ~1.6s legacy extrapolated)
- ✅ Outputs identical to reference implementation (float tolerance 1e-6)
- ✅ Linear scaling with edge count verified
- ✅ Minimal degradation with increasing layer count

**Key Features**:
- Memory-efficient sparse matrix output by default
- Handles large node ID spaces efficiently
- Supports self-loops, directed edges, negative weights
- Deterministic output for reproducibility
- Comprehensive logging with `logger.debug` (no prints)
- Full docstrings with complexity analysis: O(E) time, O(E) memory for sparse
- Type annotations throughout

**Acceptance Criteria Met**:
- ✅ ≥3× faster for 1M edges (achieved 8.04×)
- ✅ Outputs identical to reference within 1e-6 tolerance
- ✅ Sparse output uses <20% memory vs dense for sparse graphs
- ✅ All 24 tests pass
- ✅ Backward compatible (new module, doesn't break existing code)

---

### 📋 Remaining Specifications

#### 🧱 **Spec B — Streaming Supra-Adjacency**
**Status**: Not started  
**Target**: ≥2× faster supra build for L=8, N=25k, ≥50% less memory

**Planned Tasks**:
- [ ] Create `py3plex/multinet/supra.py` module
- [ ] Implement `build_supra(blocks, dense=False, block_iter=False)`
- [ ] Add streaming mode → generator of `(i, j, csr_block)`
- [ ] Introduce lightweight `SupraView` class
- [ ] Replace dense default with `dense=False`
- [ ] Add tests and benchmarks

#### 🔁 **Spec C — Backend Registry & Adapters**
**Status**: Not started (requires optional dependencies)  
**Target**: 1.5–3× speedup via igraph/cugraph

**Planned Tasks**:
- [ ] Create `py3plex/backends/` directory
- [ ] Add capability map: `_CAPS = {"pagerank": ["cugraph", "igraph", "nx"]}`
- [ ] Implement `pick_backend(op, backend="auto")`
- [ ] Define routing for `pagerank()` and `community_leiden()`
- [ ] Add igraph and cugraph implementations with availability checks
- [ ] Add tests ensuring parity across backends (±1e-6)

#### ⚡ **Spec D — ForceAtlas2 Layout Modernization**
**Status**: Not started (requires C extension work)  
**Target**: ≥1.5× faster layout on N=50k nodes

**Planned Tasks**:
- [ ] Provide prebuilt FA2 C-extension wheels via CI
- [ ] Add `forceatlas2_layout(G, iterations=300, return_numpy=True, **kw)`
- [ ] Return contiguous NumPy array if `return_numpy=True`
- [ ] Maintain deterministic results when seeded
- [ ] Build wheels for Linux/macOS/Win, Python 3.9–3.12

#### 🧪 **Spec E — Benchmark Harness & CI Integration**
**Status**: Partially complete (aggregation benchmarks done)  
**Target**: Full benchmark suite with CI integration

**Completed**:
- ✅ pytest-benchmark suite for aggregation
- ✅ Benchmarks demonstrate speedup targets

**Remaining Tasks**:
- [ ] Add benchmarks for supra adjacency
- [ ] Add benchmarks for centrality (if backends implemented)
- [ ] Add benchmarks for ForceAtlas2 (if modernized)
- [ ] Implement `scripts/run_bench.sh` → CSV + Markdown summary
- [ ] Integrate into CI (compare vs baseline tag v0.95a)
- [ ] Add README badge for performance regression status

---

### 🎯 Next Steps

**Priority 1 (High Impact)**:
1. ~~**Spec A**: Vectorized Aggregation~~ ✅ **COMPLETE**
2. **Spec E**: Complete benchmark harness (CSV/MD export, CI integration)
3. **Spec B**: Streaming Supra-Adjacency (2× speedup target)

**Priority 2 (Optional Enhancements)**:
4. **Spec C**: Backend registry (requires igraph/cugraph as optional deps)
5. **Spec D**: FA2 modernization (requires C extension build infrastructure)

**Documentation Updates**:
- ✅ Added `py3plex/multinet/` module with comprehensive docstrings
- ✅ Added test coverage for new functionality
- ✅ Added benchmarks demonstrating performance improvements
- [ ] Update main README with performance optimization highlights
- [ ] Add migration guide for users wanting to use new optimized functions

**Backward Compatibility**:
- ✅ New module doesn't affect existing APIs
- ✅ Existing `multi_layer_network.aggregate_edges()` unchanged
- ✅ Users can opt-in to new optimized functions
- [ ] Future: Consider deprecating old methods in favor of new optimized ones (post-1.0.0)
