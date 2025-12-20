Installation and Setup
======================

This guide covers all aspects of installing py3plex and setting up your environment.

.. _which-docs-to-use:

Which Docs Should I Use?
-------------------------

**Most users should use these docs (py3plex 1.x)**, which you're reading now at https://skblaz.github.io/py3plex/. They cover:

* The current stable version with modern features (DSL v2, pipelines, workflows)
* All new APIs, including the SQL-like query DSL and dplyr-style operations
* Actively maintained and updated with examples

**Use the legacy docs (py3plex 0.8x) only if:**

* You're maintaining old code that depends on py3plex 0.8x specifically
* You need features that were removed in the 1.x rewrite (very rare)

The legacy docs are available at https://py3plex.readthedocs.io but are **no longer maintained or updated** and may have broken examples. We strongly recommend upgrading to 1.x for new projects.

Installation Modes
------------------

Choose the installation method based on your needs. In all cases, prefer a virtual environment to keep dependencies isolated from system Python:

.. list-table::
   :header-rows: 1
   :widths: 20 35 45

   * - Mode
     - Command
     - When to Use
   * - **User Install**
     - ``python -m pip install py3plex``
     - Standard usage: running analyses, using the library
   * - **Developer Install**
     - Clone repo + ``make setup`` + ``make dev-install``
     - Contributing code, running tests, building docs

Basic Installation
------------------

Install from PyPI (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The latest stable release is available on PyPI:

.. code-block:: bash

    python -m pip install --upgrade pip
    python -m pip install py3plex

This installs the core py3plex library with all required dependencies.

Install from Source
~~~~~~~~~~~~~~~~~~~

For development or to access the latest features:

.. code-block:: bash

    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    python -m pip install --upgrade pip
    python -m pip install -e .

The ``-e`` flag installs in editable mode, so changes to the source code are immediately available.

Docker Installation (Alternative)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For a containerized environment with all dependencies pre-installed, use Docker:

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    
    # Build the Docker image
    docker build -t py3plex:latest .
    
    # Run py3plex commands (mount local data if needed)
    docker run --rm -v ${PWD}:/data py3plex:latest --version
    docker run --rm -v ${PWD}:/data py3plex:latest selftest

**Benefits of Docker installation:**

* No Python environment setup required
* All dependencies pre-installed and tested
* Consistent environment across different systems
* Isolated from system Python installation

See :doc:`../deployment/cli_and_docker` for complete Docker documentation including:

* Building and running the container
* Working with data files via volume mounts
* Docker Compose usage
* Helper scripts (``py3plex-docker.sh``)
* Batch processing and CI/CD integration

Optional Dependencies
---------------------

py3plex offers several optional feature sets that can be installed separately. Quote extras (``"py3plex[extra]"``) to avoid shell globbing on some terminals.

Advanced Community Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install Infomap for advanced overlapping community detection:

.. code-block:: bash

    python -m pip install "py3plex[infomap]"

Additional Algorithms
~~~~~~~~~~~~~~~~~~~~~

Install extra community detection algorithms (Louvain, cdlib):

.. code-block:: bash

    python -m pip install "py3plex[algos]"

Advanced Visualization
~~~~~~~~~~~~~~~~~~~~~~

Install Plotly and igraph for interactive and advanced visualizations:

.. code-block:: bash

    python -m pip install "py3plex[viz]"

Apache Arrow Support
~~~~~~~~~~~~~~~~~~~~

Install pyarrow for high-performance I/O with Arrow/Parquet formats:

.. code-block:: bash

    python -m pip install "py3plex[arrow]"

Arrow format typically provides faster read/write operations and better compression than JSON/CSV for large graphs.
See :doc:`../user_guide/io_and_formats` for details on using Arrow format.

Multiple Extras
~~~~~~~~~~~~~~~

Install multiple feature sets at once:

.. code-block:: bash

    python -m pip install "py3plex[infomap,viz,algos,arrow]"

Workflow Configuration Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install YAML support for config-driven workflows:

.. code-block:: bash

    python -m pip install "py3plex[workflows]"

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

For contributors, install with development tools (testing, linting):

**Recommended (Makefile-based):**

.. code-block:: bash

    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    make setup        # Create virtual environment
    make dev-install  # Install with dev dependencies

**Alternative (manual):**

.. code-block:: bash

    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    python -m pip install --upgrade pip
    python -m pip install -e ".[dev]"

Both methods install:

* pytest and coverage tools
* black, ruff, isort for code formatting
* mypy for type checking
* sphinx for documentation building

System Requirements
-------------------

Python Version
~~~~~~~~~~~~~~

py3plex requires Python 3.8 or higher. We test on:

* Python 3.8
* Python 3.9
* Python 3.10
* Python 3.11
* Python 3.12

Platform Support
~~~~~~~~~~~~~~~~

py3plex is cross-platform and tested on:

* **Linux** (Ubuntu 20.04, 22.04)
* **macOS** (macOS 11, 12, 13)
* **Windows** (Windows Server 2019, 2022)

Core Dependencies
~~~~~~~~~~~~~~~~~

These are automatically installed with py3plex:

* ``networkx>=2.5`` - Graph data structures and algorithms
* ``numpy>=1.19.0`` - Numerical computing
* ``scipy>=1.5.0`` - Scientific computing and sparse matrices
* ``pandas`` - Data manipulation
* ``matplotlib>=3.3.0`` - Static visualization
* ``scikit-learn>=0.24.0`` - Machine learning utilities
* ``tqdm>=4.40.0`` - Progress bars
* ``rdflib>=6.0.0`` - Semantic web support
* ``bitarray>=2.0.0`` - Efficient boolean arrays
* ``gensim>=4.0.0`` - Topic modeling utilities
* ``seaborn>=0.11.0`` - Statistical plotting
* ``cython>=0.29.0`` - Extension compilation support

External Binaries (Optional)
-----------------------------

py3plex no longer bundles external binaries; install them separately when needed to keep the base package lightweight and licensing clear.

Infomap Community Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For advanced community detection using Infomap:

**Option 1:** Use the bundled Python implementation (recommended):

.. code-block:: bash

    python -m pip install "py3plex[infomap]"

**Option 2:** Download the C++ binary from the official source:

* Website: https://www.mapequation.org/infomap/
* Follow platform-specific installation instructions

**Alternative:** Use the built-in Louvain algorithm (no binary needed):

.. code-block:: python

    from py3plex.algorithms.community_detection import community_louvain
    communities = community_louvain.best_partition(network.core_network)

Node2Vec Embeddings
~~~~~~~~~~~~~~~~~~~

For Node2Vec node embeddings, use pure Python alternatives:

**Option 1:** Use pecanpy (fast parallel implementation):

.. code-block:: bash

    python -m pip install pecanpy

**Option 2:** Use node2vec package:

.. code-block:: bash

    python -m pip install node2vec

**Option 3:** Use py3plex's built-in random walk implementation:

.. code-block:: python

    from py3plex.algorithms.general.walkers import node2vec_walk, generate_walks
    walks = generate_walks(network.core_network, num_walks=10, walk_length=80)


Virtual Environment Setup
--------------------------

We strongly recommend using a virtual environment to prevent dependency conflicts:

Using venv
~~~~~~~~~~

.. code-block:: bash

    # Create virtual environment
    python3 -m venv py3plex-env
    
    # Activate (Linux/macOS)
    source py3plex-env/bin/activate
    
    # Activate (Windows)
    py3plex-env\Scripts\activate
    
    # Install py3plex inside the environment
    python -m pip install --upgrade pip
    python -m pip install py3plex

Using conda
~~~~~~~~~~~

.. code-block:: bash

    # Create conda environment
    conda create -n py3plex python=3.10
    
    # Activate
    conda activate py3plex
    
    # Install py3plex
    python -m pip install py3plex

Common Installation Issues
--------------------------

Issue: "No module named 'numpy'"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution:** Install numpy first (preferably in a virtual environment):

.. code-block:: bash

    python -m pip install numpy
    python -m pip install py3plex

Issue: Compilation errors on Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution:** Install Visual C++ Build Tools:

1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "Desktop development with C++"
3. Restart your shell, then retry installation

Issue: "Permission denied" on Linux/macOS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution 1:** Use a virtual environment:

.. code-block:: bash

    python3 -m venv py3plex-env
    source py3plex-env/bin/activate  # On Windows: py3plex-env\Scripts\activate
    python -m pip install --upgrade pip
    python -m pip install py3plex

**Solution 2:** Use the ``--user`` flag if you cannot use venv:

.. code-block:: bash

    python -m pip install --user py3plex

Issue: Old version installed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution:** Check the installed version and upgrade if needed:

.. code-block:: bash

    python -m pip show py3plex
    python -m pip install --upgrade py3plex

Verifying Installation
----------------------

Test that py3plex is correctly installed:

.. code-block:: python

    import py3plex
    print(py3plex.__version__)
    
    from py3plex.core import multinet
    network = multinet.multi_layer_network()
    print("py3plex installed successfully!")

Run the test suite:

.. code-block:: bash

    # Clone repository (if not already)
    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    
    # Run tests
    python run_tests.py

License Considerations
----------------------

Main Library License
~~~~~~~~~~~~~~~~~~~~

py3plex core is distributed under the MIT License (permissive, commercial-friendly).

Bundled Code Licenses
~~~~~~~~~~~~~~~~~~~~~~

**Important:** The repository contains AGPLv3-licensed code in ``py3plex/algorithms/community_detection/infomap/``. 

If you use Infomap-based community detection functions, your application may be subject to AGPLv3 requirements (copyleft).

License Matrix
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 15 15 40

   * - Feature Category
     - License
     - Commercial Use
     - Notes
   * - Core multilayer functionality
     - MIT
     - [OK] Yes
     - Safe for proprietary use
   * - Network visualization
     - MIT
     - [OK] Yes
     - Safe for proprietary use
   * - I/O operations
     - MIT
     - [OK] Yes
     - Safe for proprietary use
   * - Louvain community detection
     - BSD-3-Clause
     - [OK] Yes
     - Safe for proprietary use
   * - Label propagation
     - MIT
     - [OK] Yes
     - Safe for proprietary use
   * - **Infomap community detection**
     - **AGPLv3**
     - WARNING Restricted
     - Viral license - requires open-sourcing derived works

Recommendations
~~~~~~~~~~~~~~~

* For commercial/proprietary projects: Avoid Infomap functions or use the pure Python ``infomap`` package separately
* For open-source projects: All features are safe to use
* When in doubt: Use alternative algorithms (Louvain, label propagation) which are BSD/MIT licensed

Next Steps
----------

After installation, proceed to:

* :doc:`tutorial_10min` - 10-minute comprehensive tutorial
* :doc:`../user_guide/networks` - Detailed usage guide

Getting Help
------------

If you encounter installation issues:

1. Check `GitHub Issues <https://github.com/SkBlaz/py3plex/issues>`_
2. Search for similar problems
3. Open a new issue with:

   * Your operating system and version
   * Python version (``python --version``)
   * Error message and full traceback
   * Installation command used

For any errors, please open an issue at https://github.com/SkBlaz/py3plex/issues
