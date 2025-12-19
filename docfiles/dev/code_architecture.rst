Architecture and Design
=======================

This document describes the **system architecture**, **design patterns**, and **extension points** of py3plex. It explains how the layers fit together, what each layer owns, and where to plug in new capabilities without leaking responsibilities across layers.

System Overview
---------------

py3plex uses a **modular, layered architecture** with explicit boundaries. Higher layers depend on lower ones, never the reverse; data flows downward for computation and back upward for presentation:

.. code-block:: text

    ┌─────────────────────────────────────────────────────┐
    │          High-Level Interfaces (Wrappers)           │
    │  node2vec_embedding, benchmark_nodes                │
    └─────────────────────────────────────────────────────┘
                            ↓
    ┌─────────────────────────────────────────────────────┐
    │              Algorithms Layer                        │
    │  ┌──────────────┬───────────────┬─────────────────┐ │
    │  │  Community   │  Statistics   │  Multilayer     │ │
    │  │  Detection   │               │  Algorithms     │ │
    │  └──────────────┴───────────────┴─────────────────┘ │
    └─────────────────────────────────────────────────────┘
                            ↓
    ┌─────────────────────────────────────────────────────┐
    │            Visualization Layer                       │
    │  ┌──────────────┬───────────────┬─────────────────┐ │
    │  │  Multilayer  │  Drawing      │  Layout         │ │
    │  │  Plots       │  Machinery    │  Algorithms     │ │
    │  └──────────────┴───────────────┴─────────────────┘ │
    └─────────────────────────────────────────────────────┘
                            ↓
    ┌─────────────────────────────────────────────────────┐
    │                Core Layer                            │
    │  ┌──────────────┬───────────────┬─────────────────┐ │
    │  │  multinet    │  Parsers      │  Converters     │ │
    │  │  (MultiLayer │               │                 │ │
    │  │   Network)   │               │                 │ │
    │  └──────────────┴───────────────┴─────────────────┘ │
    └─────────────────────────────────────────────────────┘
                            ↓
    ┌─────────────────────────────────────────────────────┐
    │           NetworkX Foundation                        │
    │  MultiDiGraph, MultiGraph, Algorithms                │
    └─────────────────────────────────────────────────────┘

**Reading the diagram:** NetworkX primitives sit at the base. The core layer wraps them in a multilayer-aware data model. Algorithms, visualization, and wrappers build on that model and never mutate it implicitly; wrappers orchestrate complete tasks while delegating computation to the lower layers.

Architectural Layers
--------------------

Each layer has a narrow contract: the core encodes data, algorithms consume that encoding, visualization renders results, and wrappers orchestrate complete tasks. When extending py3plex, start from the lowest layer you need and only depend upward.

Core Layer
~~~~~~~~~~

**Purpose:** Fundamental data structures and I/O operations. Everything else depends on this layer, so invariants and encoding live here.

**Key Components:**

* ``multinet.py`` - The ``multi_layer_network`` class (core facade)
* ``parsers.py`` - Input/output for various formats
* ``converters.py`` - Format conversion utilities
* ``random_generators.py`` - Random network generators
* ``HINMINE/`` - Heterogeneous network decomposition helpers

**Responsibilities:**

* Network construction and mutation through a single API
* File I/O (GraphML, GML, GEXF, edge lists, etc.)
* Layer management (string ↔ integer IDs, delimiter handling)
* Matrix representations (adjacency, supra-adjacency)
* NetworkX integration and type selection (directed vs. undirected)
* Cache ownership (e.g., supra adjacency, embeddings) and invalidation hooks triggered by mutations

**Design Pattern:** **Facade Pattern** — ``multi_layer_network`` exposes one consistent interface while hiding NetworkX wiring and encoding details

Algorithms Layer
~~~~~~~~~~~~~~~~

**Purpose:** Network analysis algorithms optimized for multilayer networks. Algorithms assume core-layer encoding and never adjust it themselves.

**Key Components:**

* ``community_detection/`` - Community detection algorithms
* ``statistics/`` - Network statistics and metrics
* ``multilayer_algorithms/`` - Multilayer-specific methods
* ``node_ranking/`` - Centrality and ranking measures
* ``general/`` - General-purpose algorithms (random walks, etc.)

**Responsibilities:**

* Community detection (Louvain, Infomap, Label Propagation)
* Statistical analysis (multilayer density, inter-layer correlation, etc.)
* Centrality computation (degree, betweenness, PageRank, and variants)
* Random walks and embeddings
* Network decomposition primitives
* Result caching where appropriate (never mutating the underlying graph)

**Design Pattern:** **Strategy Pattern** — interchangeable algorithms share a common interface

Visualization Layer
~~~~~~~~~~~~~~~~~~~

**Purpose:** Network plotting and rendering for multilayer structures. Visualization consumes algorithm outputs but does not compute new graph state.

**Key Components:**

* ``multilayer.py`` - High-level multilayer plotting
* ``drawing_machinery.py`` - Core drawing primitives
* ``layout_algorithms.py`` - Layout computation
* ``colors.py`` - Color scheme generators
* ``fa2/`` - ForceAtlas2 layout

**Responsibilities:**

* Diagonal projection plots and multilayer-specific layouts
* Force-directed and ForceAtlas2 layouts
* Matrix visualizations
* Color mapping and legend helpers
* Interactive plots (via Plotly)

**Design Pattern:** **Template Method Pattern** — layout algorithms follow a shared skeleton with overridable steps

Wrappers Layer
~~~~~~~~~~~~~~

**Purpose:** High-level interfaces for common workflows so users can run end-to-end tasks without touching internals. Wrappers compose algorithms and visualization, but defer state changes to the core.

**Key Components:**

* ``node2vec_embedding.py`` - Node2Vec embedding generation
* ``benchmark_nodes.py`` - Node classification benchmarking

**Responsibilities:**

* Simplified interfaces for multi-step workflows
* Integration with external tools
* Benchmarking and evaluation shortcuts

**Design Pattern:** **Facade Pattern** — hides orchestration and sensible defaults behind a small API

Core Data Structure
-------------------

The multi_layer_network Class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Central to py3plex, this class wraps the underlying NetworkX graph and enforces multilayer encoding invariants:

.. code-block:: python

    class multi_layer_network:
        def __init__(self, directed=True, label_delimiter="---", coupling_weight=1.0):
            self.core_network = nx.MultiDiGraph() if directed else nx.MultiGraph()
            self.layer_name_map = {}  # Bidirectional mapping
            self.label_delimiter = label_delimiter
            self.coupling_weight = coupling_weight
            self.embedding = None
            self.labels = None

**Key Attributes:**

* ``core_network`` - Underlying NetworkX graph
* ``layer_name_map`` - Maps layer names to integer IDs
* ``label_delimiter`` - Separator for node-layer encoding (default: ``"---"``)
* ``coupling_weight`` - Default weight for inter-layer edges
* ``embedding`` - Cached node embedding matrix
* ``labels`` - Node classification labels

**Encoding Scheme and Invariants:**

* Nodes are represented as ``(node_id, layer)`` tuples in Python.
* When serialized to flat text (files, labels), tuples are joined with the delimiter: ``"{node_id}{delimiter}{layer}"``. Avoid using the delimiter inside raw IDs.
* Layer names are mapped to integers in ``layer_name_map`` for stable ordering.
* ``core_network`` stays a NetworkX ``MultiGraph``/``MultiDiGraph``; avoid injecting derived attributes that are not part of the graph definition.
* Inter-layer edges use ``coupling_weight`` unless explicitly weighted; modifying coupling should clear related caches.
* Any mutation (adding/removing nodes, relabeling layers) should invalidate cached matrices or embeddings.

Design Patterns
---------------

Facade Pattern
~~~~~~~~~~~~~~

**Used in:** ``multi_layer_network``, wrappers

**Purpose:** Provide a simplified interface to complex subsystems and enforce a single entry point for mutations.

.. code-block:: python

    # Complex underlying operations hidden behind simple interface
    network = multinet.multi_layer_network()
    network.add_edges(edges, input_type='list')  # Handles parsing, encoding, validation
    stats = network.basic_stats()  # Aggregates multiple NetworkX calls behind one call

Strategy Pattern
~~~~~~~~~~~~~~~~

**Used in:** Algorithms, layout computation

**Purpose:** Interchangeable algorithms following a common interface; callers pick by name without changing call sites.

.. code-block:: python

    # Different community detection strategies
    def detect_communities(network, method='louvain'):
        strategies = {
            'louvain': community_louvain.best_partition,
            'infomap': community_wrapper.infomap_communities,
            'label_prop': label_propagation.propagate
        }
        return strategies[method](network.core_network)  # Adding a new strategy means adding one entry to the map

Template Method Pattern
~~~~~~~~~~~~~~~~~~~~~~~

**Used in:** Visualization, layout algorithms

**Purpose:** Define algorithm skeleton, allow customization in subclasses; shared steps live in the base class.

.. code-block:: python

    class LayoutAlgorithm:
        def compute(self, graph):
            self.initialize(graph)
            self.iterate()
            return self.finalize()
        
        def initialize(self, graph):
            raise NotImplementedError
        
        def iterate(self):
            raise NotImplementedError
        
        def finalize(self):
            raise NotImplementedError

Dependency Injection
~~~~~~~~~~~~~~~~~~~~

**Used in:** Configuration, algorithm parameters

**Purpose:** Inject dependencies rather than hard-coding so testing and theming stay configurable.

.. code-block:: python

    # Configuration injected rather than hard-coded
    from py3plex.config import DEFAULT_COLORS, LAYOUT_PARAMS
    
    def draw_network(network, colors=None, layout_params=None):
        colors = colors or DEFAULT_COLORS
        layout_params = layout_params or LAYOUT_PARAMS
        # Use injected configuration without touching global state

Data Flow
---------

Typical Workflow
~~~~~~~~~~~~~~~~

py3plex workflows follow a predictable sequence: load → compute → analyze → visualize → export. Each step uses the layer beneath it and should avoid mutating lower layers unless explicitly intended.

1. **Input:** Load or create network, keeping encoding consistent

   .. code-block:: python

       network = multinet.multi_layer_network()
       network.load_network("data.graphml", input_type="graphml")

2. **Processing:** Apply algorithms against the core graph without re-encoding

   .. code-block:: python

       communities = community_louvain.best_partition(network.core_network)
       centrality = calc.multilayer_degree_centrality(network)

3. **Analysis:** Compute statistics on the derived results

   .. code-block:: python

       density = mls.layer_density(network, 'layer1')
       correlation = mls.inter_layer_degree_correlation(network, 'layer1', 'layer2')

4. **Visualization:** Render results; visualization functions expect immutable inputs

   .. code-block:: python

       draw_multilayer_default([network], display=True)

5. **Output:** Export results using the same delimiter and layer naming

   .. code-block:: python

       network.save_network("output.graphml", output_type="graphml")

State Management
~~~~~~~~~~~~~~~~

**Immutable Operations:** Most algorithms don't modify the network or its caches

.. code-block:: python

    # These don't modify the network
    centrality = calc.multilayer_degree_centrality(network)
    communities = community_louvain.best_partition(network.core_network)

**Mutable Operations:** Some operations modify network state (nodes, edges, layer mappings, caches)

.. code-block:: python

    # These modify the network
    network.add_edges(new_edges, input_type='list')
    network.aggregate_layers(['L1', 'L2'], 'combined')

After running mutable operations, clear or recompute cached matrices/embeddings before downstream analysis. If you need isolation, copy the network or work on a subgraph before running destructive operations.

Extension Points
----------------

Custom Algorithms
~~~~~~~~~~~~~~~~~

Add new algorithms by following existing patterns (pure functions returning dictionaries or NetworkX objects). Keep inputs typed as ``multi_layer_network`` to reuse encoding and caching, and avoid mutating the passed network unless the function is explicitly transformative. Document input assumptions (directed vs. undirected, weighted vs. unweighted) and expose new callables in the relevant package ``__init__`` when you want them importable by name.

.. code-block:: python

    # py3plex/algorithms/my_module/my_algorithm.py
    from py3plex.core.multinet import multi_layer_network
    
    def my_centrality(network: multi_layer_network) -> dict:
        """
        Custom centrality measure.
        
        Parameters
        ----------
        network : multi_layer_network
            Input network
        
        Returns
        -------
        dict
            Node centrality scores
        """
        G = network.core_network
        centrality = {}
        
        for node in G.nodes():
            # Implement custom logic
            centrality[node] = compute_score(node, G)
        
        return centrality

Custom Visualizations
~~~~~~~~~~~~~~~~~~~~~

Create custom plots using drawing machinery. Treat the network as read-only and reuse shared layout helpers to keep visuals consistent with built-in plots:

.. code-block:: python

    from py3plex.visualization import drawing_machinery as dm
    import matplotlib.pyplot as plt
    
    def my_custom_plot(network):
        """Custom visualization."""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Compute layout
        pos = dm.compute_layout(network.core_network, 'force')
        
        # Draw elements
        dm.draw_nodes(ax, network.core_network, pos, node_size=50)
        dm.draw_edges(ax, network.core_network, pos, edge_width=1)
        dm.draw_labels(ax, pos, labels=network.get_node_labels())
        
        plt.show()

Custom Parsers
~~~~~~~~~~~~~~

Add support for new file formats. Normalize layer names, respect ``label_delimiter``, and raise the appropriate domain exceptions so callers can distinguish parsing failures from missing data:

.. code-block:: python

    # py3plex/core/parsers.py
    def parse_my_format(input_file, **kwargs):
        """
        Parse custom file format.
        
        Parameters
        ----------
        input_file : str
            Path to input file
        
        Returns
        -------
        multi_layer_network
            Parsed network
        """
        network = multi_layer_network()
        
        with open(input_file, 'r') as f:
            for line in f:
                # Parse line and add to network
                pass
        
        return network

Configuration System
--------------------

Centralized Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

``py3plex/config.py`` provides centralized configuration:

.. code-block:: python

    # Default color palettes (8 options including colorblind-safe)
    DEFAULT_COLORS = 'Set1'
    COLORBLIND_SAFE = 'colorblind'
    
    # Visualization defaults
    DEFAULT_NODE_SIZE = 20
    DEFAULT_EDGE_WIDTH = 1.0
    DEFAULT_ALPHA = 0.7
    
    # Layout parameters
    LAYOUT_PARAMS = {
        'force': {'iterations': 500, 'optimal_distance': 1.0},
        'fa2': {'iterations': 1000, 'gravity': 1.0}
    }
    
    # Performance settings
    SPARSE_THRESHOLD = 1000  # Use sparse matrices above this node count
    MEMORY_WARNING_THRESHOLD = 10000  # Warn for large dense matrices

Usage:

.. code-block:: python

    from py3plex.config import DEFAULT_COLORS, LAYOUT_PARAMS
    
    colors = DEFAULT_COLORS
    iterations = LAYOUT_PARAMS['force']['iterations']

Prefer importing needed values rather than mutating module globals. For per-run overrides, pass parameters explicitly into drawing or layout helpers.

Testing Architecture
--------------------

Test Organization
~~~~~~~~~~~~~~~~~

Tests mirror the architecture: core primitives first, then algorithms and workflows.

.. code-block:: text

    tests/
    ├── test_core_functionality.py      # Core data structure tests
    ├── test_multilayer_*.py            # Multilayer algorithm tests
    ├── test_random_walks.py            # Random walk tests
    ├── test_io_*.py                    # I/O and parsing tests
    ├── test_config_api.py              # Configuration tests
    └── test_utils.py                   # Utility function tests

Test Patterns
~~~~~~~~~~~~~

**Unit Tests:** Test individual functions in isolation

.. code-block:: python

    def test_layer_density():
        network = create_test_network()
        density = mls.layer_density(network, 'layer1')
        assert 0 <= density <= 1

**Integration Tests:** Test workflows across modules

.. code-block:: python

    def test_community_detection_workflow():
        network = load_network("test_data.graphml")
        communities = community_louvain.best_partition(network.core_network)
        assert len(communities) > 0

**Property-Based Tests:** Test invariants

.. code-block:: python

    def test_centrality_normalization():
        network = create_random_network()
        centrality = calc.multilayer_degree_centrality(network)
        # Centrality values should not be negative; normalized variants stay within [0, 1]
        assert all(v >= 0 for v in centrality.values())

Performance Considerations
--------------------------

Lazy Evaluation
~~~~~~~~~~~~~~~

Expensive operations are computed on-demand and cached on the instance:

.. code-block:: python

    class multi_layer_network:
        @property
        def supra_adjacency(self):
            if self._supra_adj_cache is None:
                self._supra_adj_cache = self._compute_supra_adjacency()
            return self._supra_adj_cache

Sparse Matrices
~~~~~~~~~~~~~~~

Use sparse representations for large networks; the threshold is configurable in ``config.py``:

.. code-block:: python

    def get_supra_adjacency_matrix(self, sparse=True):
        if sparse or len(self.get_nodes()) > SPARSE_THRESHOLD:
            return scipy.sparse.csr_matrix(adj)
        return np.array(adj)

Keep the chosen representation consistent downstream to avoid repeated dense↔sparse conversions.

Vectorization
~~~~~~~~~~~~~

Prefer NumPy vectorized operations to avoid Python loops:

.. code-block:: python

    # Bad: Python loop
    degrees = [sum(1 for _ in G.neighbors(node)) for node in nodes]
    
    # Good: Vectorized
    degrees = np.array(list(dict(G.degree()).values()))

Logging Infrastructure
----------------------

Centralized Logging
~~~~~~~~~~~~~~~~~~~

``py3plex/logging_config.py`` provides structured logging:

.. code-block:: python

    import logging
    from py3plex.logging_config import get_logger
    
    logger = get_logger(__name__)
    
    logger.info("Processing network with %d nodes", num_nodes)
    logger.warning("Large network detected, using sparse matrices")
    logger.error("Invalid layer: %s", layer_name)
    
Call ``get_logger`` once per module; configure logging once in the application entrypoint to avoid duplicate handlers.

Log Levels
~~~~~~~~~~

* **DEBUG:** Detailed diagnostic information
* **INFO:** General informational messages
* **WARNING:** Warning messages (e.g., performance concerns)
* **ERROR:** Error messages
* **CRITICAL:** Critical errors

Error Handling
--------------

Custom Exceptions
~~~~~~~~~~~~~~~~~

``py3plex/exceptions.py`` defines domain-specific exceptions:

.. code-block:: python

    class NetworkError(Exception):
        """Base exception for network errors."""
        pass
    
    class LayerNotFoundError(NetworkError):
        """Raised when layer doesn't exist."""
        pass
    
    class InvalidFormatError(NetworkError):
        """Raised when file format is invalid."""
        pass

Usage:

.. code-block:: python

    from py3plex.exceptions import LayerNotFoundError
    
    def get_layer(self, layer_name):
        if layer_name not in self.layer_name_map:
            raise LayerNotFoundError(f"Layer '{layer_name}' not found")
        return self.layer_name_map[layer_name]

Prefer raising domain-specific exceptions for recoverable errors so callers can distinguish parsing failures, missing layers, or invalid formats.

Future Architecture
-------------------

Planned Improvements
~~~~~~~~~~~~~~~~~~~~

1. **Backend Registry:** Support for igraph, cugraph backends
2. **Streaming API:** Process networks larger than memory
3. **Distributed Computing:** Dask/Ray integration for large-scale analysis
4. **Plugin System:** Easy addition of third-party algorithms
5. **Type System:** Full type hints coverage (currently 65%)

These roadmap items are exploratory; expect details and APIs to evolve.

See Also
--------

* :doc:`contributing` - Contributing guidelines
* :doc:`development` - Development workflow
* :doc:`core` - Core API documentation
