Repository Layout
=================

Use this guide to navigate the py3plex repository and understand what each directory contains.
Treat it as a map: start from the overview tree, then jump to the sections below to find what you need.

Overview
--------

.. code-block:: text

    py3plex/
    ├── py3plex/              # Main package source code
    ├── docs/                 # Built documentation (HTML)
    ├── docfiles/             # Documentation source (RST files)
    ├── examples/             # Example scripts
    ├── tests/                # Test suite
    ├── gui/                  # Web interface
    ├── datasets/             # Sample datasets
    ├── benchmarks/           # Performance benchmarks
    ├── fuzzing/              # Fuzz testing
    ├── .github/              # GitHub Actions CI/CD
    ├── pyproject.toml        # Package configuration
    ├── Makefile              # Development commands
    └── README.md             # Project README

Main Package (py3plex/)
-----------------------

Source code for the py3plex library:

.. code-block:: text

    py3plex/
    ├── __init__.py           # Package initialization
    ├── core/                 # Core data structures
    │   ├── multinet.py       # multi_layer_network class
    │   ├── parsers.py        # File I/O
    │   └── converters.py     # Format conversion
    ├── algorithms/           # Network algorithms
    │   ├── community_detection/
    │   ├── statistics/
    │   ├── multilayer_algorithms/
    │   └── general/
    ├── visualization/        # Plotting and rendering
    │   ├── multilayer.py
    │   ├── drawing_machinery.py
    │   └── layout_algorithms.py
    ├── wrappers/             # High-level interfaces
    └── io/                   # Modern I/O system

**Key modules:**

* ``core/multinet.py`` - Main ``multi_layer_network`` class
* ``algorithms/`` - All analysis algorithms
* ``visualization/`` - All visualization code
* ``io/`` - Modern schema-based I/O

Documentation (docfiles/)
--------------------------

Sphinx documentation source files:

.. code-block:: text

    docfiles/
    ├── index.rst             # Main documentation index
    ├── conf.py               # Sphinx configuration
    ├── Makefile              # Build commands
    ├── getting_started/      # Beginner guides
    ├── concepts/             # Conceptual explanations
    ├── user_guide/           # How-to guides
    ├── deployment/           # Deployment guides
    ├── gui/                  # GUI documentation
    ├── dev/                  # Developer docs
    ├── examples/             # Example index
    └── reference/            # API reference

**Building documentation (from repository root):**

.. code-block:: bash

    make docs            # Output in docfiles/_build/html/

If Sphinx is missing, (re)install the development extras in your active virtual environment and rerun the command.

**Manual build from docfiles/:**

.. code-block:: bash

    cd docfiles
    sphinx-build -b html . _build/html  # Output in _build/html/

Examples (examples/)
--------------------

Executable example scripts demonstrating various features:

.. code-block:: text

    examples/
    ├── basic/                    # Basic usage
    │   ├── example_load_network.py
    │   ├── example_basic_stats.py
    │   └── example_simple_viz.py
    ├── visualization/            # Visualization examples
    │   ├── example_multilayer_viz.py
    │   ├── example_custom_layouts.py
    │   └── example_interactive_plots.py
    ├── analysis/                 # Analysis examples
    │   ├── example_community_detection.py
    │   ├── example_centrality.py
    │   └── example_statistics.py
    ├── advanced/                 # Advanced topics
    │   ├── example_node2vec.py
    │   ├── example_random_walks.py
    │   └── example_embeddings.py
    └── io/                       # I/O examples
        ├── example_arrow_io.py
        └── example_format_conversion.py

**Running examples:**

.. code-block:: bash

    # From an activated virtual environment
    python examples/basic/example_load_network.py

Tests (tests/)
--------------

Test suite using pytest:

.. code-block:: text

    tests/
    ├── test_core.py              # Core functionality
    ├── test_algorithms.py        # Algorithm tests
    ├── test_visualization.py     # Visualization tests
    ├── test_io.py                # I/O tests
    ├── test_performance_core.py  # Performance benchmarks
    ├── test_fuzzing_properties.py# Property-based tests
    └── conftest.py               # Pytest configuration

**Running tests:**

.. code-block:: bash

    make test             # Run all tests (default environment)
    make test-fast        # Skip slow tests
    make coverage         # With coverage report
    python -m pytest tests/test_core.py -k "degree"  # Targeted run

GUI (gui/)
----------

Web interface for py3plex:

.. code-block:: text

    gui/
    ├── app.py                # Flask application
    ├── routes/               # API endpoints
    ├── templates/            # HTML templates
    ├── static/               # CSS, JS, images
    ├── config.py             # Configuration
    └── Dockerfile            # Docker container

**Running GUI:**

.. code-block:: bash

    python gui/app.py

Datasets (datasets/)
--------------------

Sample networks for testing and examples:

.. code-block:: text

    datasets/
    ├── test.edgelist         # Simple test network
    ├── multiedgelist.txt     # Multilayer test
    ├── karate_club/          # Karate club network
    └── bio_networks/         # Biological networks

Benchmarks (benchmarks/)
------------------------

Performance benchmarking suite:

.. code-block:: text

    benchmarks/
    ├── bench_core.py         # Core operations
    ├── bench_algorithms.py   # Algorithm performance
    ├── bench_io.py           # I/O performance
    └── bench_aggregation.py  # Aggregation benchmarks

**Running benchmarks:**

.. code-block:: bash

    make benchmark

CI/CD (.github/)
----------------

GitHub Actions workflows:

.. code-block:: text

    .github/
    ├── workflows/
    │   ├── tests.yml         # Test CI
    │   ├── code-quality.yml  # Linting/formatting
    │   ├── docs.yml          # Documentation build
    │   └── release.yml       # Release automation
    └── dependabot.yml        # Dependency updates

Configuration Files
-------------------

Root-level configuration:

* ``pyproject.toml`` - Package metadata, dependencies, build config
* ``Makefile`` - Development commands (make test, make docs, etc.)
* ``README.md`` - Project overview and quick start
* ``.gitignore`` - Git ignore rules
* ``LICENSE`` - MIT license
* ``CITATION.cff`` - Citation information
* ``MANIFEST.in`` - Package manifest for distribution

Working with the Repository
----------------------------

Initial Setup
~~~~~~~~~~~~~

**Recommended (Makefile-based):**

.. code-block:: bash

    # Clone repository
    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    
    # Create virtual environment and install dependencies
    make setup
    
    # Install package in editable mode with dev dependencies
    make dev-install

**Alternative (manual venv + pip):**

.. code-block:: bash

    # Clone repository
    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    
    # Install in development mode
    pip install -e ".[dev]"

Development Workflow
~~~~~~~~~~~~~~~~~~~~

1. Activate your virtual environment.
2. Make focused changes to code or docs.
3. Format: ``make format``.
4. Lint: ``make lint``.
5. Test: ``make test`` (or ``make test-fast`` for quicker feedback).
6. Build docs: ``make docs``.
7. Commit and push:

   .. code-block:: bash

        git add .
        git commit -m "Description"
        git push

Finding Things
--------------

"Where is...?"
~~~~~~~~~~~~~~

**Core network class?**
  ``py3plex/core/multinet.py`` → ``multi_layer_network`` class

**Community detection algorithms?**
  ``py3plex/algorithms/community_detection/``

**Visualization code?**
  ``py3plex/visualization/``

**I/O functions?**
  ``py3plex/io/`` (modern) or ``py3plex/core/parsers.py`` (legacy)

**Tests for feature X?**
  ``tests/test_*.py`` - grep for the feature name

**Example using feature X?**
  ``examples/`` - check the relevant subdirectory

**Documentation source?**
  ``docfiles/`` - RST files organized by topic

**Built documentation?**
  ``docs/`` - HTML files (generated from docfiles/)

File Naming Conventions
-----------------------

* **Source files:** ``snake_case.py``
* **Test files:** ``test_<module>.py``
* **Example files:** ``example_<feature>.py``
* **Documentation:** ``<topic>.rst``
* **Configuration:** Various (``pyproject.toml``, ``conf.py``, etc.)

Important Files
---------------

For Contributors
~~~~~~~~~~~~~~~~

* ``CONTRIBUTING.md`` - Contribution guidelines (if exists)
* ``docfiles/dev/contributing.rst`` - Contribution documentation
* ``Makefile`` - Available development commands
* ``pyproject.toml`` - Package dependencies

For Users
~~~~~~~~~

* ``README.md`` - Quick start guide
* ``docfiles/index.rst`` - Documentation entry point
* ``examples/`` - Working code examples
* ``LICENSE`` - MIT license

For CI/CD
~~~~~~~~~

* ``.github/workflows/*.yml`` - CI pipelines
* ``Makefile`` - Automated commands
* ``pyproject.toml`` - Build configuration

Directory Conventions
---------------------

**Source code directories:**

* No spaces in names
* Lowercase with underscores
* Descriptive names (``community_detection``, not ``cd``)

**Test directories:**

* Mirror source structure
* One test file per source file when possible

**Documentation directories:**

* Organize by user journey/topic
* Clear, descriptive names

Package Distribution
--------------------

When building packages, these files are included:

**Included:**

* All ``.py`` files in ``py3plex/``
* LICENSE
* README.md
* Required configuration files

**Excluded (via .gitignore):**

* ``__pycache__/``
* ``.pytest_cache/``
* ``*.pyc``
* ``build/``, ``dist/``, ``*.egg-info/``
* Virtual environments
* IDE-specific files

See ``MANIFEST.in`` for complete inclusion/exclusion rules.

Related Documentation
---------------------

* :doc:`development_guide` - Development setup and workflow
* :doc:`contributing` - How to contribute
* :doc:`code_architecture` - Internal architecture
* :doc:`../getting_started/installation` - Installation guide

**External Resources:**

* Repository: https://github.com/SkBlaz/py3plex
* Issues: https://github.com/SkBlaz/py3plex/issues
* Pull Requests: https://github.com/SkBlaz/py3plex/pulls
