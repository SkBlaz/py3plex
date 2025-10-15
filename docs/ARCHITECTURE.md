# Py3plex Architecture

This document provides an architectural overview of py3plex to help contributors understand the system structure and relationships between components.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Code                                │
│                  (Scripts, Notebooks, Applications)              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Py3plex Public API                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Exceptions │  │    Config    │  │   Logging    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│     Core     │    │  Algorithms  │    │Visualization │
│              │◄───┤              │◄───┤              │
│  Data Model  │    │  Analysis    │    │  Rendering   │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                    │
       ▼                   ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   I/O Layer  │    │   Wrappers   │    │   Utils      │
│              │    │              │    │              │
│File Parsers  │    │ External Libs│    │   Helpers    │
└──────────────┘    └──────────────┘    └──────────────┘
```

## Component Layers

### Layer 1: User Interface
- **Purpose**: Entry point for all user interactions
- **Components**: Python scripts, Jupyter notebooks, command-line tools
- **Dependencies**: Imports py3plex modules

### Layer 2: Public API
- **Purpose**: Stable interface with versioning and error handling
- **Components**:
  - `__init__.py`: Package exports and version info
  - `exceptions.py`: Domain-specific exception hierarchy
  - `config.py`: Centralized configuration
  - `logging_config.py`: Logging infrastructure
- **Guarantees**: Backward compatibility within major versions

### Layer 3: Core Modules

#### Core (`py3plex/core/`)
- **Purpose**: Fundamental data structures for multilayer networks
- **Key Files**:
  - `multinet.py`: `multi_layer_network` class (primary data structure)
  - `parsers.py`: Input/output parsers (GML, GraphML, GEXF, CSV, JSON)
  - `converters.py`: Format converters
  - `nx_compat.py`: NetworkX compatibility layer
  - `random_generators.py`: Synthetic network generators
- **Dependencies**: NetworkX, NumPy
- **Exports**: Network objects, loading/saving functions

#### Algorithms (`py3plex/algorithms/`)
- **Purpose**: Analytical methods for network analysis
- **Submodules**:
  - `community_detection/`: Louvain, Infomap, multilayer modularity
  - `statistics/`: Network metrics, power-law fitting, enrichment
  - `multilayer_algorithms/`: Multilayer-specific algorithms
  - `node_ranking/`: Centrality measures, PageRank
  - `network_classification/`: Graph classification
  - `hedwig/`: Subgroup discovery
  - `temporal_multiplex/`: Temporal analysis
- **Dependencies**: Core, SciPy, scikit-learn (optional)
- **Exports**: Functions that take networks and return analytical results

#### Visualization (`py3plex/visualization/`)
- **Purpose**: Rendering multilayer networks
- **Key Files**:
  - `multilayer.py`: Main visualization functions
  - `drawing_machinery.py`: Low-level drawing primitives
  - `layout_algorithms.py`: Layout computation (force-directed, random)
  - `colors.py`: Color scheme generation
  - `bezier.py`: Curve drawing utilities
  - `fa2/`: ForceAtlas2 layout implementation
- **Dependencies**: Core, Matplotlib, Plotly (optional)
- **Exports**: Visualization functions returning figures

### Layer 4: Supporting Components

#### I/O Layer (`py3plex/io/`)
- **Purpose**: File format handling
- **Key Files**:
  - `api.py`: High-level I/O interface
  - `converters.py`: Format converters
  - `schema.py`: Data validation schemas
  - `formats/`: Format-specific handlers
- **Dependencies**: Core
- **Exports**: Load/save functions for various formats

#### Wrappers (`py3plex/wrappers/`)
- **Purpose**: Interfaces to external tools
- **Key Files**:
  - `node2vec_embedding.py`: Node2Vec wrapper
  - `benchmark_nodes.py`: Benchmark utilities
- **Dependencies**: Core, external binaries
- **Exports**: High-level functions wrapping external tools

#### Utils (`py3plex/utils.py`)
- **Purpose**: Shared utilities
- **Functions**:
  - `get_rng()`: Random state management
  - `deprecated()`: Deprecation decorator
  - `warn_if_deprecated()`: Deprecation warnings
  - `validate_multilayer_input()`: Input validation
- **Dependencies**: NumPy
- **Exports**: Utility functions used across modules

## Data Flow

### Loading a Network
```
File (GML/CSV/etc)
    │
    ▼
parsers.py (parse file)
    │
    ▼
multi_layer_network (core object)
    │
    ├──► algorithms (analyze)
    │
    └──► visualization (render)
```

### Community Detection Pipeline
```
User Code
    │
    ▼
community_wrapper.py (high-level API)
    │
    ├──► community_louvain.py (Louvain)
    │
    ├──► multilayer_modularity.py (Multilayer)
    │
    └──► infomap/ (external binary)
    │
    ▼
Community Assignment (dict/DataFrame)
```

### Visualization Pipeline
```
multi_layer_network object
    │
    ▼
layout_algorithms.py (compute positions)
    │
    ▼
multilayer.py (coordinate mapping)
    │
    ▼
drawing_machinery.py (render nodes/edges)
    │
    ├──► Matplotlib (static plots)
    │
    └──► Plotly (interactive plots)
    │
    ▼
Figure/HTML output
```

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────┐
│                     External Dependencies                    │
│  NetworkX   NumPy   SciPy   Matplotlib   scikit-learn       │
│  Plotly(opt) Gensim(opt) Infomap(opt) Louvain(opt)         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │         py3plex.core               │
        │    (fundamental data structures)   │
        └────────────┬───────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌──────────────┐          ┌──────────────┐
│ algorithms   │          │visualization │
└──────────────┘          └──────────────┘
        │                         │
        └────────────┬────────────┘
                     │
                     ▼
            ┌────────────────┐
            │   wrappers     │
            └────────────────┘
```

## Key Design Patterns

### 1. Centralized Data Model
- All components operate on the `multi_layer_network` class
- Ensures consistency and interoperability
- Single source of truth for network state

### 2. Layered Architecture
- Clear separation between data model, algorithms, and presentation
- Dependencies flow downward (visualization → algorithms → core)
- Prevents circular dependencies

### 3. NetworkX Compatibility
- NetworkX used as underlying graph representation
- Extends NetworkX with multilayer capabilities
- Easy integration with existing NetworkX workflows

### 4. Configuration Over Code
- Centralized config module for defaults
- Users can override settings programmatically
- Consistent behavior across modules

### 5. Error Handling
- Domain-specific exception hierarchy
- Exceptions propagate with context
- Clear error messages for users

### 6. Logging
- Structured logging at module level
- Configurable verbosity
- Aids debugging and monitoring

## Extension Points

To extend py3plex, contributors can:

1. **Add new algorithms**: Implement in appropriate `algorithms/` subdirectory
2. **Add new formats**: Create parser in `io/formats/`
3. **Add new layouts**: Implement in `visualization/layout_algorithms.py`
4. **Add new visualizations**: Extend `visualization/multilayer.py`
5. **Add new metrics**: Implement in `algorithms/statistics/`

Each extension should:
- Follow existing code patterns
- Include docstrings with citations (if applicable)
- Add unit tests
- Update relevant documentation
- Respect the layered architecture

## Testing Strategy

```
Unit Tests
    ├── Core functionality (network construction, manipulation)
    ├── Algorithm correctness (known outputs for inputs)
    ├── I/O operations (format conversion)
    └── Utilities (helpers, logging, config)

Integration Tests
    ├── Algorithm + Visualization pipelines
    ├── Multi-format I/O workflows
    └── External tool wrappers (when available)

CI/CD
    ├── Linting (ruff, black, isort)
    ├── Type checking (mypy)
    ├── Multi-Python version tests (3.8-3.12)
    └── Multi-platform tests (Linux, macOS, Windows)
```

## Performance Considerations

- **Sparse matrices**: Used for large networks (>1000 nodes)
- **Vectorization**: NumPy operations preferred over loops
- **Caching**: Layout computation results cached
- **Batch operations**: Visualization renders in batches
- **Optional dependencies**: Heavy dependencies are optional

## Future Architecture Directions

Potential improvements being considered:

1. **Abstract backend interface**: Pluggable rendering backends (Matplotlib/Plotly/PyVis)
2. **Parallel algorithms**: Multi-core support for community detection
3. **GPU acceleration**: CUDA support for large-scale embeddings
4. **Streaming support**: Handle networks too large for memory
5. **Web API**: REST API for py3plex as a service

## Contributing to Architecture

When proposing architectural changes:

1. Open a discussion issue first
2. Explain the problem being solved
3. Propose the change with diagrams
4. Discuss impact on existing code
5. Get maintainer approval before implementing

For questions, see `CONTRIBUTING.md` or open an issue.
