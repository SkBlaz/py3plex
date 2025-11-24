Design Principles
=================

py3plex is built on a foundation of key design principles that guide its development and usage. Understanding these principles helps you use the library effectively and extend it for your needs.

Core Philosophy
---------------

Simple, Off-the-Shelf Functionality
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Principle:** Provide ready-to-use tools that work out of the box with minimal configuration.

**In practice:**

.. code-block:: python

    from py3plex.core import multinet
    
    # Simple, intuitive API
    network = multinet.multi_layer_network()
    network.add_edges([['A', 'L1', 'B', 'L1', 1]], input_type="list")
    network.basic_stats()  # Works immediately

**Rationale:** Researchers and practitioners need tools that are easy to adopt without extensive setup or configuration. py3plex aims to minimize the barrier to entry for multilayer network analysis.

NetworkX Compatibility
~~~~~~~~~~~~~~~~~~~~~~

**Principle:** Build on NetworkX rather than reinventing the wheel.

**In practice:**

.. code-block:: python

    import networkx as nx
    
    # Direct access to NetworkX graph
    G = network.core_network
    
    # Use any NetworkX function
    betweenness = nx.betweenness_centrality(G)
    communities = nx.community.louvain_communities(G)

**Rationale:** NetworkX is the de facto standard for network analysis in Python. By building on it, py3plex:

* Leverages a mature, well-tested codebase
* Provides access to hundreds of NetworkX algorithms
* Ensures interoperability with the broader Python ecosystem
* Reduces learning curve for users familiar with NetworkX

Modular Architecture
~~~~~~~~~~~~~~~~~~~~

**Principle:** Separate concerns into independent, composable modules.

**Structure:**

.. code-block:: text

    py3plex/
    ├── core/                   # Data structures
    ├── algorithms/             # Analysis methods
    │   ├── community_detection/
    │   ├── statistics/
    │   └── multilayer_algorithms/
    ├── visualization/          # Plotting
    └── wrappers/               # High-level interfaces

**In practice:**

.. code-block:: python

    # Import only what you need
    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    from py3plex.visualization.multilayer import hairball_plot

**Rationale:** Modular design allows users to:

* Import only the functionality they need
* Understand and maintain code more easily
* Extend the library with custom modules
* Mix and match components flexibly

Implementation Principles
-------------------------

Flexibility
~~~~~~~~~~~

**Principle:** Support multiple ways to accomplish tasks, accommodating different workflows.

**Examples:**

.. code-block:: python

    # Multiple ways to create networks
    
    # Method 1: Direct edge addition
    network.add_edges([['A', 'L1', 'B', 'L1', 1]], input_type="list")
    
    # Method 2: Load from file
    network.load_network("data.edgelist", input_type="edgelist")
    
    # Method 3: From NetworkX
    network.load_network_from_networkx(nx_graph)
    
    # Multiple ways to access nodes
    nodes1 = network.get_nodes()
    nodes2 = list(network.core_network.nodes())
    nodes3 = network.get_nodes(layer='L1')

**Rationale:** Different users have different preferences and workflows. Flexibility ensures py3plex adapts to the user's needs, not vice versa.

Lazy Evaluation
~~~~~~~~~~~~~~~

**Principle:** Compute expensive operations only when needed.

**In practice:**

.. code-block:: python

    # Supra-adjacency matrix is not computed on network creation
    network = multinet.multi_layer_network()
    network.add_edges([...])  # Fast
    
    # Matrix is computed only when requested
    supra_adj = network.get_supra_adjacency_matrix()  # Computed here
    
    # Subsequent calls may use cached result (where appropriate)

**Rationale:** Many multilayer operations (e.g., matrix construction) are computationally expensive. Lazy evaluation:

* Improves performance for common operations
* Reduces memory usage
* Allows working with large networks when full matrices aren't needed

Graceful Degradation
~~~~~~~~~~~~~~~~~~~~

**Principle:** Optional features should fail gracefully, not crash the entire application.

**In practice:**

.. code-block:: python

    # If Infomap is not installed
    try:
        communities = infomap_communities(network)
    except ImportError as e:
        print("Infomap not available. Using Louvain instead.")
        communities = louvain_partition(network)

**Rationale:** Not all users need all features. By degrading gracefully, py3plex:

* Allows users to install only what they need
* Reduces dependency bloat
* Provides helpful error messages
* Suggests alternatives when dependencies are missing

Explicit Over Implicit
~~~~~~~~~~~~~~~~~~~~~~~

**Principle:** Make behavior explicit and predictable, avoiding surprising defaults.

**Good examples:**

.. code-block:: python

    # Explicit parameter names
    network.load_network(
        "data.txt",
        input_type="edgelist",     # Explicit format
        directed=False             # Explicit directionality
    )
    
    # Explicit layer specification
    neighbors = network.get_neighbors('Alice', layer_id='friends')

**Rationale:** Explicit code is:

* Easier to understand and debug
* Less prone to errors
* Self-documenting
* More maintainable

Performance Considerations
--------------------------

Sparse Representations
~~~~~~~~~~~~~~~~~~~~~~

**Principle:** Use sparse data structures for large networks.

**In practice:**

.. code-block:: python

    # Sparse matrix by default (efficient for large networks)
    supra_adj = network.get_supra_adjacency_matrix(sparse=True)
    
    # Dense only for small networks or specific algorithms
    supra_adj_dense = network.get_supra_adjacency_matrix(sparse=False)

**Rationale:** Real-world networks are typically sparse (few edges relative to potential edges). Sparse representations:

* Reduce memory usage by orders of magnitude
* Enable analysis of networks with millions of nodes
* Maintain computational efficiency

Efficient Data Structures
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Principle:** Choose appropriate data structures for common operations.

**Examples:**

* NetworkX graphs for topology (edge lookups, traversals)
* Dictionaries for layer mappings (O(1) lookups)
* Sparse matrices for linear algebra
* Sets for membership testing

**Rationale:** The right data structure makes operations fast and memory-efficient.

Algorithmic Defaults
~~~~~~~~~~~~~~~~~~~~

**Principle:** Provide sensible default parameters based on empirical research.

**In practice:**

.. code-block:: python

    # Default parameters work well for most cases
    partition = louvain_multilayer(
        network,
        gamma=1.0,     # Standard resolution
        omega=1.0,     # Balanced inter-layer coupling
        random_state=42  # Reproducibility
    )

**Rationale:** Good defaults:

* Make the library easy to use for beginners
* Reduce parameter tuning overhead
* Are based on published research and empirical validation

Extensibility
-------------

Plugin-Friendly Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Principle:** Make it easy to add custom functionality.

**In practice:**

.. code-block:: python

    # Easy to add custom algorithms
    def my_centrality(ml_network):
        """Custom centrality measure."""
        G = ml_network.core_network
        # Implement your algorithm
        return centrality_scores
    
    # Easy to add custom visualizations
    def my_plot(ml_network, **kwargs):
        """Custom visualization."""
        # Use py3plex drawing machinery
        from py3plex.visualization import drawing_machinery as dm
        # Implement your plot
        pass

**Rationale:** Research needs evolve. Extensibility ensures py3plex can grow with new methods without requiring core library changes.

Clear Interfaces
~~~~~~~~~~~~~~~~

**Principle:** Define clear, stable APIs for modules.

**In practice:**

.. code-block:: python

    # All statistics follow same interface
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    density = mls.layer_density(network, layer)
    activity = mls.node_activity(network, node)
    overlap = mls.edge_overlap(network, layer1, layer2)
    
    # Consistent parameter names and return types

**Rationale:** Clear interfaces make py3plex:

* Easier to learn (patterns repeat)
* More predictable
* More maintainable
* Easier to extend

Documentation and Testing
-------------------------

Comprehensive Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Principle:** Every feature should be documented with examples.

**In practice:**

* Detailed docstrings for all public functions
* Code examples in documentation
* Real-world use cases
* API reference with parameter descriptions

**Rationale:** Good documentation:

* Reduces barrier to entry
* Serves as a reference for experienced users
* Helps maintainers understand code
* Acts as specification

Extensive Testing
~~~~~~~~~~~~~~~~~

**Principle:** Test all core functionality and edge cases.

**In practice:**

.. code-block:: bash

    # Comprehensive test suite
    make test          # Unit tests
    make benchmark     # Performance tests
    make fuzz-property # Property-based tests

**Rationale:** Tests ensure:

* Code works as intended
* Changes don't break existing functionality
* Edge cases are handled correctly
* Performance regressions are caught

Interoperability
----------------

Standard Formats
~~~~~~~~~~~~~~~~

**Principle:** Support widely-used data formats.

**Formats supported:**

* EdgeList (simple, human-readable)
* GraphML (XML-based, preserves attributes)
* GML (Graph Modeling Language)
* Pickle (NetworkX native)
* JSON/Arrow/Parquet (modern, efficient)

**Rationale:** Standard formats enable:

* Data sharing between tools
* Integration with other software
* Long-term data preservation

Cross-Platform Compatibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Principle:** Work consistently across operating systems.

**Tested on:**

* Linux (Ubuntu 20.04, 22.04)
* macOS (11, 12, 13)
* Windows (Server 2019, 2022)

**Rationale:** Users work on different platforms. Cross-platform support ensures py3plex works everywhere.

Research-Oriented Design
------------------------

Citation and Attribution
~~~~~~~~~~~~~~~~~~~~~~~~

**Principle:** Make it easy to cite algorithms and give proper attribution.

**In practice:**

.. code-block:: python

    # Algorithms include citations in docstrings
    help(louvain_multilayer)
    # Docstring includes:
    # References:
    #   Mucha et al. (2010). "Community structure in time-dependent..."

**See:** :doc:`../reference/citation_and_acknowledgements`

**Rationale:** Proper attribution:

* Gives credit to algorithm developers
* Helps users find original papers
* Supports reproducibility

Reproducibility
~~~~~~~~~~~~~~~

**Principle:** Support reproducible research.

**In practice:**

.. code-block:: python

    # Random seed parameters for reproducibility
    partition = louvain_multilayer(
        network,
        random_state=42  # Reproducible results
    )
    
    walks = generate_walks(
        network,
        seed=42  # Reproducible walks
    )

**Rationale:** Reproducibility is fundamental to science. Seed parameters ensure:

* Results can be verified
* Comparisons are fair
* Bugs can be diagnosed

Validation and Benchmarking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Principle:** Validate algorithms against published results.

**In practice:**

* Benchmark suite comparing to reference implementations
* Validation against known network properties
* Performance metrics for large networks

**Rationale:** Validation ensures:

* Implementations are correct
* Performance is acceptable
* Results match published literature

Practical Implications
----------------------

For Users
~~~~~~~~~

These design principles mean you can:

1. **Start quickly** with minimal setup
2. **Use NetworkX knowledge** and tools directly
3. **Choose your workflow** with multiple approaches
4. **Work efficiently** with large networks
5. **Extend easily** with custom algorithms
6. **Trust results** through validation and testing

For Contributors
~~~~~~~~~~~~~~~~

When contributing to py3plex, follow these principles:

1. **Maintain NetworkX compatibility** in new features
2. **Document thoroughly** with examples
3. **Test extensively** including edge cases
4. **Provide sensible defaults** based on research
5. **Fail gracefully** with helpful error messages
6. **Follow existing patterns** for consistency

See :doc:`../dev/contributing` for detailed guidelines.

Comparison with Other Libraries
--------------------------------

py3plex vs. Pure NetworkX
~~~~~~~~~~~~~~~~~~~~~~~~~

**NetworkX:**

* Excellent for single-layer networks
* Lacks native multilayer support
* General-purpose graph library

**py3plex:**

* Native multilayer data structures
* Layer-aware algorithms
* Specialized multilayer visualizations
* Built on NetworkX (inherits all features)

py3plex vs. Other Multilayer Tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Other tools (e.g., muxViz, pymnet):**

* Often specialized or platform-specific
* May have steep learning curves
* Limited algorithm libraries

**py3plex:**

* Pure Python (easy installation)
* Comprehensive algorithm library
* NetworkX integration
* Active development
* Research-backed

Related Documentation
---------------------

* :doc:`multilayer_networks_101` - Conceptual introduction to multilayer networks
* :doc:`py3plex_core_model` - Internal representation details
* :doc:`algorithm_landscape` - Overview of available algorithms
* :doc:`../dev/development_guide` - Contributing to py3plex
* :doc:`../dev/code_architecture` - Internal architecture details

**Academic References:**

* Škrlj et al. (2019). "Py3plex toolkit for visualization and analysis of multilayer networks." *Applied Network Science* 4(1): 94.
