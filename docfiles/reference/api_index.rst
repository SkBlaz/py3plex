API Documentation
=================

This page indexes the auto-generated API documentation for py3plex. Use it as a map to find module-level details after building the docs.

.. tip::
   
   **Looking for algorithm documentation?** Visit :doc:`algorithm_reference` for a conceptual overview of all algorithms organized by category with working examples. Then come back here for detailed API signatures.

How to (re)generate the API pages::

    cd docfiles
    sphinx-apidoc -o AUTOGEN_results -f ../py3plex
    make html

You will find the generated RST sources under ``docfiles/AUTOGEN_results`` and the rendered HTML under ``docfiles/_build``.

Core Modules
------------

Core data structures and helpers for loading, converting, and working with multilayer networks.

.. automodule:: py3plex.core.multinet
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.core.parsers
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.core.converters
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.core.random_generators
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.core.supporting
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.core.nx_compat
   :members:
   :undoc-members:
   :show-inheritance:

HINMINE Network Decomposition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Modules for heterogeneous information network (HINMINE) decomposition, including I/O helpers.

.. automodule:: py3plex.core.HINMINE.decomposition
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.core.HINMINE.IO
   :members:
   :undoc-members:
   :show-inheritance:

Configuration and Utilities
----------------------------

Global configuration objects, shared utilities, and base exceptions.

.. automodule:: py3plex.config
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.utils
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

Domain-Specific Language (DSL)
-------------------------------

SQL-like query language for selecting and computing properties on multilayer networks.

.. automodule:: py3plex.dsl
   :members:
   :undoc-members:
   :show-inheritance:

Uncertainty Quantification
---------------------------

Uncertainty estimation tools and supporting types for ranking and inference tasks.

.. automodule:: py3plex.uncertainty
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.uncertainty.types
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.uncertainty.context
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.uncertainty.estimation
   :members:
   :undoc-members:
   :show-inheritance:

Algorithms
----------

Algorithm implementations grouped by task.

Community Detection
~~~~~~~~~~~~~~~~~~~

.. automodule:: py3plex.algorithms.community_detection.community_wrapper
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.community_detection.multilayer_modularity
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.community_detection.community_louvain
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.community_detection.community_measures
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.community_detection.multilayer_benchmark
   :members:
   :undoc-members:
   :show-inheritance:

Statistics
~~~~~~~~~~

Network statistics, enrichment tests, and topology utilities.

.. automodule:: py3plex.algorithms.statistics.statistics
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.statistics.multilayer_statistics
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.statistics.topology
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.statistics.enrichment
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.statistics.correlation_networks
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.statistics.basic_statistics
   :members:
   :undoc-members:
   :show-inheritance:

Multilayer Algorithms
~~~~~~~~~~~~~~~~~~~~~

Algorithms designed for multilayer graphs, including centrality and entanglement measures.

.. automodule:: py3plex.algorithms.multilayer_algorithms.centrality
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.centrality_toolkit
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.multilayer_algorithms.multixrank
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.multilayer_algorithms.entanglement
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.multilayer_algorithms.supra_matrix_function_centrality
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.multicentrality
   :members:
   :undoc-members:
   :show-inheritance:

General Algorithms
~~~~~~~~~~~~~~~~~~

General-purpose algorithms such as random walkers and benchmarking helpers.

.. automodule:: py3plex.algorithms.general.walkers
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.general.benchmark_classification
   :members:
   :undoc-members:
   :show-inheritance:

Node Ranking
~~~~~~~~~~~~

Node ranking routines for multilayer and single-layer graphs.

.. automodule:: py3plex.algorithms.node_ranking.node_ranking
   :members:
   :undoc-members:
   :show-inheritance:

Network Classification
~~~~~~~~~~~~~~~~~~~~~~

.. Note: :noindex: prevents duplicate object descriptions in the documentation index
   since this module is also documented elsewhere.

Label propagation and related network classification helpers.

.. automodule:: py3plex.algorithms.network_classification.label_propagation
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Visualization
-------------

Plotting utilities for multilayer networks and layouts.

.. automodule:: py3plex.visualization.multilayer
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.visualization.drawing_machinery
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.visualization.colors
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.visualization.layout_algorithms
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.visualization.bezier
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.visualization.benchmark_visualizations
   :members:
   :undoc-members:
   :show-inheritance:

Wrappers
--------

Convenience wrappers for embedding and benchmarking workflows.

.. automodule:: py3plex.wrappers.node2vec_embedding
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.wrappers.benchmark_nodes
   :members:
   :undoc-members:
   :show-inheritance:

I/O Operations
--------------

File readers, writers, and related helpers.

.. automodule:: py3plex.io.input_output
   :members:
   :undoc-members:
   :show-inheritance:

Aggregation and Network Operations
----------------------------------

Layer aggregation and network-level transformations.

.. automodule:: py3plex.multinet.aggregation
   :members:
   :undoc-members:
   :show-inheritance:

Profiling Utilities
-------------------

Timing and profiling utilities for performance analysis.

.. automodule:: py3plex.profiling
   :members:
   :undoc-members:
   :show-inheritance:

Logging Configuration
---------------------

Default logging setup for py3plex.

.. automodule:: py3plex.logging_config
   :members:
   :undoc-members:
   :show-inheritance:

I/O Schema and Validation
-------------------------

.. Note: :noindex: prevents duplicate object descriptions in the documentation index
   since this module is documented in multiple locations.

Schema definitions and validation helpers for I/O routines.

.. automodule:: py3plex.io.schema
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

.. automodule:: py3plex.io.api
   :members:
   :undoc-members:
   :show-inheritance:

Hedwig Rule Learning
--------------------

Hedwig inductive logic programming components and helpers.

.. automodule:: py3plex.algorithms.hedwig
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.core.example
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.core.predicate
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.core.rule
   :members:
   :undoc-members:
   :show-inheritance:

Force Atlas 2 Visualization
---------------------------

ForceAtlas2 layout implementation and utilities.

.. automodule:: py3plex.visualization.fa2.forceatlas2
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.visualization.fa2.fa2util
   :members:
   :undoc-members:
   :show-inheritance:

Embedding Visualization
-----------------------

Helpers for visualizing graph embeddings.

.. automodule:: py3plex.visualization.embedding_visualization.embedding_visualization
   :members:
   :undoc-members:
   :show-inheritance:

Network Generation and Benchmarking
-----------------------------------

Synthetic network generation and benchmarking utilities.

.. automodule:: py3plex.algorithms.general.network_generation
   :members:
   :undoc-members:
   :show-inheritance:

Additional Statistics and Analysis
----------------------------------

Supplementary statistical tests and information-theoretic utilities.

.. automodule:: py3plex.algorithms.statistics.bayesiantests
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.statistics.information_theory
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.statistics.distribution
   :members:
   :undoc-members:
   :show-inheritance:

Community Detection Advanced
----------------------------

Additional community detection and ranking algorithms.

.. automodule:: py3plex.algorithms.community_detection.NoRC
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.community_detection.community_ranking
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.community_detection.label_propagation_multilayer
   :members:
   :undoc-members:
   :show-inheritance:

Node Ranking and Classification
-------------------------------

Combined node ranking and classification utilities.

.. automodule:: py3plex.algorithms.node_ranking
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.network_classification
   :members:
   :undoc-members:
   :show-inheritance:

Embeddings and Wrappers
-----------------------

Embedding primitives and wrapper scripts for training node representations.

Core Embedding APIs
~~~~~~~~~~~~~~~~~~~

.. automodule:: py3plex.ml.embedding.base
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.trainer
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.node2vec
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.deepwalk
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.netmf
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.line
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.metapath2vec
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.multiplex
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.evaluation
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.similarity
   :members:
   :undoc-members:
   :show-inheritance:

Wrapper Entry Points
~~~~~~~~~~~~~~~~~~~~

.. automodule:: py3plex.wrappers.train_node2vec_embedding
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.wrappers.train_word2vec_embedding
   :members:
   :undoc-members:
   :show-inheritance:

Network Motifs and Patterns
---------------------------

Motif detection and pattern discovery tools.

.. automodule:: py3plex.algorithms.network_patterns.motif_detection
   :members:
   :undoc-members:
   :show-inheritance:

HINMINE Data Structures
-----------------------

Typed data structures used by HINMINE components.

.. automodule:: py3plex.core.HINMINE.dataStructures
   :members:
   :undoc-members:
   :show-inheritance:

Command-Line Interface
----------------------

CLI entry points and argument parsing.

.. automodule:: py3plex.cli
   :members:
   :undoc-members:
   :show-inheritance:

Validation Utilities
--------------------

Validation helpers for input data and configuration.

.. automodule:: py3plex.validation
   :members:
   :undoc-members:
   :show-inheritance:

Network Comparison and Testing
------------------------------

Network distance measures, slicing, and comparison helpers.

.. automodule:: py3plex.algorithms.general.network_comparison
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.general.distances
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.general.network_slicer
   :members:
   :undoc-members:
   :show-inheritance:

Hedwig Learning Algorithms
--------------------------

Learning strategies within the Hedwig framework.

.. automodule:: py3plex.algorithms.hedwig.learners.learner
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.learners.bottomup
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.learners.optimal
   :members:
   :undoc-members:
   :show-inheritance:

Hedwig Statistics and Scoring
-----------------------------

Scoring functions and validation routines for Hedwig learners.

.. automodule:: py3plex.algorithms.hedwig.stats.scorefunctions
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.stats.validate
   :members:
   :undoc-members:
   :show-inheritance:

Hedwig Core Components
----------------------

Core converters, knowledge base structures, and settings used by Hedwig.

.. automodule:: py3plex.algorithms.hedwig.core.converters
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.core.kb
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.core.settings
   :members:
   :undoc-members:
   :show-inheritance:

Time Series and Temporal Analysis
---------------------------------

Temporal analysis utilities.

.. automodule:: py3plex.algorithms.temporal.time_series_analysis
   :members:
   :undoc-members:
   :show-inheritance:

Advanced Visualization
----------------------

Specialized visualizations such as hairball and Sankey diagrams.

.. automodule:: py3plex.visualization.hairballs
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.visualization.sankey
   :members:
   :undoc-members:
   :show-inheritance:

Link Prediction
---------------

Link prediction algorithms.

.. automodule:: py3plex.algorithms.link_prediction.link_prediction
   :members:
   :undoc-members:
   :show-inheritance:
