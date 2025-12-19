API Documentation
=================

This section contains the complete API documentation for py3plex, automatically generated from docstrings. The modules listed below anchor high-traffic entry points; the full tree produced by ``sphinx-apidoc`` lives under ``AUTOGEN_results`` after a build. Keep the order stable so cross-references into the generated tree remain predictable.

How to regenerate
-----------------

Prerequisites: py3plex importable in the current environment and ``sphinx``/``sphinx-apidoc`` available on ``PATH``.

#. From the repository root, change into ``docfiles``::

       cd docfiles

#. Rebuild the API stubs (``-f`` overwrites existing files)::

       sphinx-apidoc -o AUTOGEN_results -f ../py3plex

#. Build the documentation with warnings treated as errors to catch missing imports or directives::

       sphinx-build -b html -n -W --keep-going docfiles _build/loop-docs

Use ``:noindex:`` on any ``automodule`` entries that appear elsewhere to avoid duplicate index warnings.

Core Modules
------------

Core multilayer network container, parsers, converters, generators, and compatibility helpers.

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

Legacy hierarchical decomposition utilities used by HINMINE components.

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

Configuration loader, convenience utilities, and shared exceptions.

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

Algorithms
----------

Algorithm modules are grouped by task; most depend on NetworkX and may require optional extras for specific methods.

Community Detection
~~~~~~~~~~~~~~~~~~~

Wrappers for modularity-based and benchmark community detection in multilayer graphs.

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

Descriptive statistics, topology summaries, enrichment tests, and correlation utilities.

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

Centrality and entanglement measures defined over supra-adjacency representations.

.. automodule:: py3plex.algorithms.multilayer_algorithms.centrality
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

Random-walk primitives and generic benchmarking helpers.

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

Single-layer node ranking utilities.

.. automodule:: py3plex.algorithms.node_ranking.node_ranking
   :members:
   :undoc-members:
   :show-inheritance:

Network Classification
~~~~~~~~~~~~~~~~~~~~~~

Label propagation and related network-level classifiers.

.. Note: :noindex: prevents duplicate object descriptions in the documentation index
   since this module is also documented elsewhere.

.. automodule:: py3plex.algorithms.network_classification.label_propagation
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Visualization
-------------

Rendering utilities for multilayer networks, layouts, and color helpers.

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

Command-line friendly wrappers for embeddings and benchmarking workflows.

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

Low-level file readers and writers.

.. automodule:: py3plex.io.input_output
   :members:
   :undoc-members:
   :show-inheritance:

Aggregation and Network Operations
----------------------------------

Graph aggregation helpers for multiplex/multilayer data.

.. automodule:: py3plex.multinet.aggregation
   :members:
   :undoc-members:
   :show-inheritance:

Profiling Utilities
-------------------

Timing and profiling helpers used across algorithms.

.. automodule:: py3plex.profiling
   :members:
   :undoc-members:
   :show-inheritance:

Logging Configuration
---------------------

Logger setup used by CLI and modules.

.. automodule:: py3plex.logging_config
   :members:
   :undoc-members:
   :show-inheritance:

I/O Schema and Validation
-------------------------

Schema helpers and validation API for structured inputs.

.. Note: :noindex: prevents duplicate object descriptions in the documentation index
   since this module is documented in multiple locations.

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

Hedwig rule-learning algorithms and supporting components.

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

Helpers for plotting learned embeddings.

.. automodule:: py3plex.visualization.embedding_visualization.embedding_visualization
   :members:
   :undoc-members:
   :show-inheritance:

Network Generation and Benchmarking
-----------------------------------

Synthetic graph generators and benchmark helpers.

.. automodule:: py3plex.algorithms.general.network_generation
   :members:
   :undoc-members:
   :show-inheritance:

Additional Statistics and Analysis
----------------------------------

Bayesian comparisons, information theory helpers, and distributions.

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

Advanced or experimental community detection routines.

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

Higher-level ranking and classification front-ends.

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

Training wrappers for node2vec/word2vec embeddings.

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

Motif detection and related pattern utilities.

.. automodule:: py3plex.algorithms.network_patterns.motif_detection
   :members:
   :undoc-members:
   :show-inheritance:

HINMINE Data Structures
-----------------------

Data structures used by the HINMINE components.

.. automodule:: py3plex.core.HINMINE.dataStructures
   :members:
   :undoc-members:
   :show-inheritance:

Command-Line Interface
----------------------

CLI entry points and option parsing.

.. automodule:: py3plex.cli
   :members:
   :undoc-members:
   :show-inheritance:

Validation Utilities
--------------------

Validators for graph inputs and model outputs.

.. automodule:: py3plex.validation
   :members:
   :undoc-members:
   :show-inheritance:

Network Comparison and Testing
------------------------------

Distances, comparisons, and slicing helpers.

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

Learners used by Hedwig for rule induction.

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

Scoring and validation routines for Hedwig rules.

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

Core conversions, knowledge bases, and settings for Hedwig.

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

Temporal analysis helpers for sequence-based data.

.. automodule:: py3plex.algorithms.temporal.time_series_analysis
   :members:
   :undoc-members:
   :show-inheritance:

Advanced Visualization
----------------------

Additional layouts and visual encodings for large or complex networks.

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

Baseline link-prediction routines.

.. automodule:: py3plex.algorithms.link_prediction.link_prediction
   :members:
   :undoc-members:
   :show-inheritance:
