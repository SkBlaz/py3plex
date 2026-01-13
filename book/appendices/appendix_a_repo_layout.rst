Appendix A: Repository Layout and Scripts
==========================================

This appendix provides a reference for the py3plex repository structure and maps book examples to actual scripts.

Repository Structure
--------------------

Top-Level Organization
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    py3plex/
    ├── py3plex/              # Main package
    ├── tests/                # Test suite
    ├── examples/             # 50+ example scripts
    ├── docfiles/             # Documentation source (Sphinx)
    ├── book/                 # This book's source files
    ├── gui/                  # Web GUI application
    ├── benchmarks/           # Performance benchmarks
    ├── datasets/             # Sample datasets
    ├── pyproject.toml        # Package configuration
    ├── Makefile              # Development automation
    └── README.md             # Project overview

Main Package Structure
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    py3plex/
    ├── __init__.py
    ├── core/                 # Data structures
    │   ├── multinet.py       # multi_layer_network class
    │   └── random_generators.py
    ├── algorithms/           # Analysis algorithms
    │   ├── statistics/
    │   ├── centrality/
    │   ├── community_detection/
    │   └── paths/
    ├── dynamics/             # Dynamical processes
    │   ├── models.py         # SIS, SIR, SEIR
    │   ├── core.py
    │   └── compartmental.py
    ├── dsl/                  # Query language
    │   ├── __init__.py
    │   ├── builder.py        # Builder API
    │   ├── executor.py
    │   └── export.py
    ├── visualization/        # Plotting
    ├── io/                   # I/O handlers
    │   ├── readers.py
    │   └── writers.py
    ├── cli.py                # Command-line interface
    ├── graph_ops.py          # Dplyr-style API
    ├── pipeline.py           # sklearn-style pipelines
    └── workflows.py          # Config-driven workflows

Examples Directory
------------------

The ``examples/`` directory contains 50+ working scripts organized by topic:

.. code-block:: text

    examples/
    ├── getting_started/      # Introductory examples
    ├── network_analysis/     # Core analysis examples
    │   ├── example_dsl_builder_api.py       # DSL chapters
    │   ├── example_dsl_queries.py
    │   ├── example_community_detection.py   # Algorithms chapter
    │   └── example_centrality.py
    ├── dynamics/             # Epidemic and process models
    ├── visualization/        # Plotting examples
    ├── communities/          # Community detection
    ├── io_and_data/          # Data loading
    ├── cli/                  # Command-line usage
    ├── workflows/            # Complete workflows
    └── advanced/             # Advanced topics

Examples Directory Structure
-----------------------------

The ``examples/`` directory contains 26 focused examples across 8 categories:

.. code-block:: text

    examples/
    ├── 00_quickstart/              # First 5 minutes (3 files)
    ├── 01_network_construction/    # Building networks (3 files)
    ├── 02_basic_queries/           # Basic DSL (4 files)
    ├── 03_dsl_v2/                  # Advanced DSL (4 files)
    ├── 04_graph_ops/               # Data manipulation (3 files)
    ├── 05_communities/             # Community detection (3 files)
    ├── 06_dynamics/                # Network dynamics (3 files)
    └── 07_uncertainty/             # UQ analysis (3 files)

Each example is standalone, minimal (25-40 lines), and demonstrates exactly 1-2 concepts. See ``examples/README.md`` for details.

Mapping Book Chapters to Examples
----------------------------------

:ref:`installation-chapter` (Installation and Getting Started)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``examples/00_quickstart/01_load_and_query.py`` — Load dataset and run DSL query
* ``examples/00_quickstart/02_create_and_visualize.py`` — Create network from scratch
* ``examples/00_quickstart/03_communities.py`` — Simple community detection

:ref:`data-loading-chapter` (Data Loading)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``examples/01_network_construction/01_from_edges.py`` — Build from edge list
* ``examples/01_network_construction/02_fluent_building.py`` — Method chaining
* ``examples/01_network_construction/03_from_networkx.py`` — Convert from NetworkX

:ref:`algorithms-chapter` (Core Algorithms)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``examples/05_communities/01_louvain_single.py`` — Single-layer Louvain
* ``examples/05_communities/02_multilayer_detection.py`` — Multilayer communities
* ``examples/05_communities/03_auto_community.py`` — AutoCommunity detection
* ``examples/06_dynamics/01_sis_epidemic.py`` — SIS epidemic model
* ``examples/06_dynamics/02_multilayer_epidemic.py`` — Multilayer spreading
* ``examples/06_dynamics/03_custom_model.py`` — Custom dynamics
* ``examples/07_uncertainty/01_uq_centrality.py`` — UQ-enabled centrality
* ``examples/07_uncertainty/02_bootstrap.py`` — Bootstrap sampling
* ``examples/07_uncertainty/03_comparison.py`` — UQ vs deterministic

:ref:`dsl-chapter` and :ref:`advanced-dsl-chapter` (DSL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``examples/02_basic_queries/01_legacy_string_dsl.py`` — Legacy string syntax
* ``examples/02_basic_queries/02_select_by_layer.py`` — Layer filtering
* ``examples/02_basic_queries/03_filter_by_degree.py`` — Degree filtering
* ``examples/02_basic_queries/04_compute_centrality.py`` — Single metric computation
* ``examples/03_dsl_v2/01_builder_basic.py`` — Q.nodes() builder pattern (Primary)
* ``examples/03_dsl_v2/02_layer_algebra.py`` — Layer unions/intersections
* ``examples/03_dsl_v2/03_grouping_aggregation.py`` — Per-layer grouping
* ``examples/03_dsl_v2/04_explain.py`` — Query explanation
* ``examples/04_graph_ops/01_filter_mutate.py`` — Filter + add columns (dplyr-style)
* ``examples/04_graph_ops/02_group_summarise.py`` — Group by + aggregation
* ``examples/04_graph_ops/03_subgraph.py`` — Subgraph extraction

:ref:`gui-chapter` (GUI)
~~~~~~~~~~~~~~~~~~~~~~~~

* ``gui/app.py`` — Main application
* ``gui/README.md`` — Setup instructions

Key Scripts Reference
---------------------

Makefile Targets
~~~~~~~~~~~~~~~~

The ``Makefile`` provides common development tasks:

.. code-block:: bash

    make setup           # Create virtual environment
    make dev-install     # Install with dev dependencies
    make test            # Run test suite
    make test-coverage   # Generate coverage report
    make lint            # Run code quality checks
    make format          # Format code with black
    make docs            # Build documentation
    make clean           # Clean build artifacts

Development Scripts
~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    scripts/
    ├── run_tests.py              # Test runner
    ├── generate_docs.py          # Documentation generator
    └── benchmark.py              # Performance benchmarking

Configuration Files
-------------------

Package Configuration
~~~~~~~~~~~~~~~~~~~~~

**pyproject.toml** — Modern Python package configuration (PEP 518):

* Package metadata (name, version, authors)
* Dependencies and extras (``[infomap]``, ``[viz]``, etc.)
* Build system configuration
* Tool configurations (black, ruff, mypy)

Testing Configuration
~~~~~~~~~~~~~~~~~~~~~

**pytest.ini** — Test framework configuration:

* Test discovery patterns
* Coverage settings
* Markers for test categories

Documentation Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**docfiles/conf.py** — Sphinx documentation configuration:

* Extensions (autodoc, napoleon, mathjax)
* Theme settings (sphinx_rtd_theme)
* Build options

Docker Configuration
~~~~~~~~~~~~~~~~~~~~

**Dockerfile** — Container image definition
**docker-compose.yml** — Multi-service orchestration

[Detailed Docker configs in Appendix B]

Data Files
----------

Sample Datasets
~~~~~~~~~~~~~~~

.. code-block:: text

    datasets/
    ├── karate_multiplex.edgelist
    ├── example_biological.graphml
    └── README.md

External Datasets
~~~~~~~~~~~~~~~~~

The ``multilayer_datasets/`` directory contains links and scripts for downloading larger datasets used in case studies.

Summary
-------

**Key directories:**

* ``py3plex/`` — Main package code
* ``tests/`` — Test suite
* ``examples/`` — 50+ working examples mapped to book chapters
* ``docfiles/`` — Documentation source
* ``gui/`` — Web interface

**Development workflow:**

1. Clone repository
2. ``make setup`` to create environment
3. ``make dev-install`` to install dependencies
4. Modify code, run ``make test``
5. Use ``examples/`` as reference

**Finding code:**

* Algorithms → ``py3plex/algorithms/``
* DSL → ``py3plex/dsl/``
* Examples → ``examples/`` (organized by topic)
