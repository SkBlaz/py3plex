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
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.core.parsers
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.core.converters
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.core.random_generators
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.core.supporting
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.core.nx_compat
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

HINMINE Network Decomposition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Modules for heterogeneous information network (HINMINE) decomposition, including I/O helpers.

.. automodule:: py3plex.core.HINMINE.decomposition
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.core.HINMINE.IO
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Configuration and Utilities
----------------------------

Global configuration objects, shared utilities, and base exceptions.

.. automodule:: py3plex.config
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.utils
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.exceptions
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Domain-Specific Language (DSL)
-------------------------------

SQL-like query language for selecting and computing properties on multilayer networks.

.. automodule:: py3plex.dsl
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Uncertainty Quantification
---------------------------

Uncertainty estimation tools and supporting types for ranking and inference tasks.

.. automodule:: py3plex.uncertainty
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.uncertainty.types
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.uncertainty.context
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.uncertainty.estimation
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Algorithms
----------

Algorithm implementations grouped by task.

Community Detection
~~~~~~~~~~~~~~~~~~~

.. automodule:: py3plex.algorithms.community_detection.community_wrapper
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.community_detection.multilayer_modularity
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.community_detection.community_louvain
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.community_detection.community_measures
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.community_detection.multilayer_benchmark
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Statistics
~~~~~~~~~~

Network statistics, enrichment tests, and topology utilities.

.. automodule:: py3plex.algorithms.statistics.statistics
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.statistics.multilayer_statistics
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.statistics.topology
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.statistics.enrichment
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.statistics.correlation_networks
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.statistics.basic_statistics
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Multilayer Algorithms
~~~~~~~~~~~~~~~~~~~~~

Algorithms designed for multilayer graphs, including centrality and entanglement measures.

.. automodule:: py3plex.algorithms.multilayer_algorithms.centrality
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.centrality_toolkit
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.multilayer_algorithms.multixrank
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.multilayer_algorithms.entanglement
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.multilayer_algorithms.supra_matrix_function_centrality
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.multicentrality
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

General Algorithms
~~~~~~~~~~~~~~~~~~

General-purpose algorithms such as random walkers and benchmarking helpers.

.. automodule:: py3plex.algorithms.general.walkers
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.general.benchmark_classification
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Node Ranking
~~~~~~~~~~~~

Node ranking routines for multilayer and single-layer graphs.

.. automodule:: py3plex.algorithms.node_ranking.node_ranking
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Network Classification
~~~~~~~~~~~~~~~~~~~~~~

.. Note: :noindex: prevents duplicate object descriptions in the documentation index
   since this module is also documented elsewhere.

Label propagation and related network classification helpers.

.. automodule:: py3plex.algorithms.network_classification.label_propagation
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Visualization
-------------

Plotting utilities for multilayer networks and layouts.

.. automodule:: py3plex.visualization.multilayer
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.visualization.drawing_machinery
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.visualization.colors
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.visualization.layout_algorithms
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.visualization.bezier
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.visualization.benchmark_visualizations
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Wrappers
--------

Convenience wrappers for embedding and benchmarking workflows.

.. automodule:: py3plex.wrappers.node2vec_embedding
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.wrappers.benchmark_nodes
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

I/O Operations
--------------

File readers, writers, and related helpers.

.. automodule:: py3plex.io.input_output
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Aggregation and Network Operations
----------------------------------

Layer aggregation and network-level transformations.

.. automodule:: py3plex.multinet.aggregation
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Profiling Utilities
-------------------

Timing and profiling utilities for performance analysis.

.. automodule:: py3plex.profiling
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Logging Configuration
---------------------

Default logging setup for py3plex.

.. automodule:: py3plex.logging_config
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

I/O Schema and Validation
-------------------------

.. Note: :noindex: prevents duplicate object descriptions in the documentation index
   since this module is documented in multiple locations.

Schema definitions and validation helpers for I/O routines.

.. automodule:: py3plex.io.schema
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

.. automodule:: py3plex.io.api
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Hedwig Rule Learning
--------------------

Hedwig inductive logic programming components and helpers.

.. automodule:: py3plex.algorithms.hedwig
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.core.example
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.core.predicate
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.core.rule
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Force Atlas 2 Visualization
---------------------------

ForceAtlas2 layout implementation and utilities.

.. automodule:: py3plex.visualization.fa2.forceatlas2
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.visualization.fa2.fa2util
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Embedding Visualization
-----------------------

Helpers for visualizing graph embeddings.

.. automodule:: py3plex.visualization.embedding_visualization.embedding_visualization
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Network Generation and Benchmarking
-----------------------------------

Synthetic network generation and benchmarking utilities.

.. automodule:: py3plex.algorithms.general.network_generation
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Additional Statistics and Analysis
----------------------------------

Supplementary statistical tests and information-theoretic utilities.

.. automodule:: py3plex.algorithms.statistics.bayesiantests
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.statistics.information_theory
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.statistics.distribution
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Community Detection Advanced
----------------------------

Additional community detection and ranking algorithms.

.. automodule:: py3plex.algorithms.community_detection.NoRC
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.community_detection.community_ranking
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.community_detection.label_propagation_multilayer
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Node Ranking and Classification
-------------------------------

Combined node ranking and classification utilities.

.. automodule:: py3plex.algorithms.node_ranking
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.network_classification
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Embeddings and Wrappers
-----------------------

Embedding primitives and wrapper scripts for training node representations.

Core Embedding APIs
~~~~~~~~~~~~~~~~~~~

.. automodule:: py3plex.ml.embedding.base
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.trainer
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.node2vec
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.deepwalk
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.netmf
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.line
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.metapath2vec
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.multiplex
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.evaluation
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.ml.embedding.similarity
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Wrapper Entry Points
~~~~~~~~~~~~~~~~~~~~

.. automodule:: py3plex.wrappers.train_node2vec_embedding
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.wrappers.train_word2vec_embedding
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Network Motifs and Patterns
---------------------------

Motif detection and pattern discovery tools.

.. automodule:: py3plex.algorithms.network_patterns.motif_detection
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

HINMINE Data Structures
-----------------------

Typed data structures used by HINMINE components.

.. automodule:: py3plex.core.HINMINE.dataStructures
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Command-Line Interface
----------------------

CLI entry points and argument parsing.

.. automodule:: py3plex.cli
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Validation Utilities
--------------------

Validation helpers for input data and configuration.

.. automodule:: py3plex.validation
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Network Comparison and Testing
------------------------------

Network distance measures, slicing, and comparison helpers.

.. automodule:: py3plex.algorithms.general.network_comparison
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.general.distances
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.general.network_slicer
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Hedwig Learning Algorithms
--------------------------

Learning strategies within the Hedwig framework.

.. automodule:: py3plex.algorithms.hedwig.learners.learner
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.learners.bottomup
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.learners.optimal
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Hedwig Statistics and Scoring
-----------------------------

Scoring functions and validation routines for Hedwig learners.

.. automodule:: py3plex.algorithms.hedwig.stats.scorefunctions
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.stats.validate
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Hedwig Core Components
----------------------

Core converters, knowledge base structures, and settings used by Hedwig.

.. automodule:: py3plex.algorithms.hedwig.core.converters
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.core.kb
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.algorithms.hedwig.core.settings
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Time Series and Temporal Analysis
---------------------------------

Temporal analysis utilities.

.. automodule:: py3plex.algorithms.temporal.time_series_analysis
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Advanced Visualization
----------------------

Specialized visualizations such as hairball and Sankey diagrams.

.. automodule:: py3plex.visualization.hairballs
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

.. automodule:: py3plex.visualization.sankey
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:

Link Prediction
---------------

Link prediction algorithms.

.. automodule:: py3plex.algorithms.link_prediction.link_prediction
   :no-index:
   :members:
   :undoc-members:
   :show-inheritance:
