What is py3plex?
================

py3plex is a Python library for scalable analysis and visualization of multilayer and multiplex networks.

Key Features
------------

Use py3plex when you need to keep relationship types distinct while still running end-to-end analysis and visualization.

Multilayer Network Structures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

py3plex provides native support for:

* **Multiplex networks** — Same nodes across multiple layers (e.g., social networks with friendship, collaboration, and family ties).
* **Heterogeneous networks** — Different node types across layers (e.g., author-paper-venue networks).
* **Temporal networks** — Networks that evolve over time; edges and nodes can carry timestamps or time windows.

All network types are first-class citizens with consistent APIs.

SQL-like DSL for Network Queries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Query networks using SQL-inspired syntax that stays close to plain language:

.. code-block:: python

    from py3plex.dsl import execute_query

    # String DSL: readable and concise
    result = execute_query(network, 
        'SELECT nodes WHERE layer="social" AND degree > 5 '
        'COMPUTE betweenness_centrality'
    )

Or use the type-safe builder API for IDE autocompletion and refactoring support:

.. code-block:: python

    from py3plex.dsl import Q, L

    # Builder API: with IDE autocompletion
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .where(degree__gt=5)
         .compute("betweenness_centrality")
         .execute(network)
    )

The DSL makes complex network analyses readable and maintainable.

Comprehensive Algorithm Suite
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

py3plex includes multilayer-specific algorithms such as:

* **Community detection:** Louvain, Infomap, multilayer modularity.
* **Centrality measures:** Multilayer PageRank, betweenness, versatility.
* **Random walks:** Node2Vec, DeepWalk for network embeddings.
* **Dynamics:** SIR/SIS epidemic models, diffusion processes.

All algorithms handle multilayer structure natively without flattening.

Publication-Ready Visualizations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create professional network diagrams with:

* Automatic multilayer layouts that preserve layer separation.
* Customizable styling and colors.
* Support for large networks (1000+ nodes).
* Export to multiple formats (PNG, PDF, SVG).

High-Performance I/O
~~~~~~~~~~~~~~~~~~~~

* Apache Arrow/Parquet support for large datasets.
* NetworkX compatibility for easy integration.
* Multiple input formats (edge lists, adjacency matrices, JSON) without forcing layer flattening.

What Makes py3plex Unique?
---------------------------

**Native Multilayer Representation**

Unlike tools that flatten multilayer networks into single-layer graphs, py3plex preserves the multilayer structure throughout the analysis pipeline. This leads to more accurate results for multilayer-specific properties.

**Node-Layer Pair Abstraction**

py3plex represents multilayer networks using node-layer pairs: a node in layer A is distinct from the same node in layer B. This clean abstraction enables:

* Layer-specific queries.
* Inter-layer and intra-layer edge differentiation.
* Efficient supra-adjacency matrix operations.

**Production-Ready Design**

py3plex is designed for both research and production:

* Sklearn-style pipelines for reproducible workflows.
* Comprehensive type hints and documentation.
* Broad test coverage across core functionality.
* CLI and Docker deployment options.

When to Use py3plex?
--------------------

py3plex is ideal when you have:

* **Multiple relationship types** between entities (e.g., email + phone + in-person contacts)
* **Heterogeneous networks** with different node types (e.g., users, posts, hashtags)
* **Temporal networks** where relationships change over time
* **Need for layer-specific analysis** (e.g., comparing community structure across layers)

If you only need single-layer network analysis, NetworkX or igraph might be simpler choices.

Related Projects
----------------

* **NetworkX:** py3plex builds on NetworkX for single-layer operations
* **igraph:** Faster for single-layer networks, but limited multilayer support
* **pymnet:** Pure Python multilayer library, different API design
* **graph-tool:** High performance, but steeper learning curve

py3plex balances ease of use with multilayer-specific functionality.

Next Steps
----------

* **Get started:** :doc:`../getting_started/tutorial_10min`
* **See use cases:** :doc:`key_use_cases`
* **Understand multilayer networks:** :doc:`multilayer_in_2min`
* **Deep dive:** :doc:`../concepts/py3plex_core_model`
