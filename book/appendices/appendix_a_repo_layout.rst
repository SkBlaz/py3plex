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

Mapping Book Chapters to Examples
----------------------------------

:ref:`installation-chapter` (Installation and Getting Started)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``examples/getting_started/quickstart.py``
* ``examples/getting_started/first_network.py``

:ref:`data-loading-chapter` (Data Loading)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``examples/io_and_data/load_edgelist.py``
* ``examples/io_and_data/arrow_parquet_io.py``
* ``examples/io_and_data/csv_loading.py``

:ref:`visualization-chapter` (Visualization)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``examples/visualization/basic_plot.py``
* ``examples/visualization/hairball_plot.py``
* ``examples/visualization/matrix_visualization.py``

:ref:`algorithms-chapter` (Core Algorithms)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``examples/network_analysis/example_community_detection.py``
* ``examples/network_analysis/example_centrality.py``
* ``examples/network_analysis/example_explainable_centrality.py``
* ``examples/dynamics/sir_epidemic.py``

:ref:`dsl-chapter` and :ref:`advanced-dsl-chapter` (DSL)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``examples/network_analysis/example_dsl_builder_api.py`` — **Primary reference**
* ``examples/network_analysis/example_dsl_queries.py``
* ``examples/network_analysis/example_dsl_advanced.py``
* ``examples/network_analysis/example_dsl_community_detection.py``

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
