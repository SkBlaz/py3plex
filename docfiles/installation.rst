Installation and Setup
======================

This guide covers all aspects of installing py3plex and setting up your environment.

Basic Installation
------------------

Install from GitHub (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The latest version is always available on GitHub:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git

This installs the core py3plex library with all required dependencies.

Install from Source
~~~~~~~~~~~~~~~~~~~

For development or to access the latest features:

.. code-block:: bash

    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    pip install -e .

The ``-e`` flag installs in "editable" mode, so changes to the source code are immediately available.

Optional Dependencies
---------------------

py3plex offers several optional feature sets that can be installed separately:

Advanced Community Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install Infomap for advanced overlapping community detection:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[infomap]

Additional Algorithms
~~~~~~~~~~~~~~~~~~~~~

Install extra community detection algorithms (Louvain, cdlib):

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[algos]

Advanced Visualization
~~~~~~~~~~~~~~~~~~~~~~

Install Plotly and igraph for interactive and advanced visualizations:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz]

Multiple Extras
~~~~~~~~~~~~~~~

Install multiple feature sets at once:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[infomap,viz,algos]

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

For contributors, install with development tools (testing, linting):

.. code-block:: bash

    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    pip install -e ".[dev]"

This installs:

* pytest and coverage tools
* black, ruff, isort for code formatting
* mypy for type checking
* sphinx for documentation building

System Requirements
-------------------

Python Version
~~~~~~~~~~~~~~

py3plex requires **Python 3.8 or higher**. We test on:

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
* ``numpy>=0.8`` - Numerical computing
* ``scipy>=1.1.0`` - Scientific computing and sparse matrices
* ``pandas`` - Data manipulation
* ``matplotlib`` - Static visualization
* ``scikit-learn`` - Machine learning utilities
* ``tqdm`` - Progress bars
* ``rdflib>=0.1`` - Semantic web support
* ``bitarray>=2.0.0`` - Efficient boolean arrays

External Binaries (Optional)
-----------------------------

**Note:** As of October 2025, py3plex no longer bundles external binaries to reduce repository size and improve licensing clarity.

Infomap Community Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For advanced community detection using Infomap:

**Option 1:** Use the bundled Python implementation (recommended):

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[infomap]

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

    pip install pecanpy

**Option 2:** Use node2vec package:

.. code-block:: bash

    pip install node2vec

**Option 3:** Use py3plex's built-in random walk implementation:

.. code-block:: python

    from py3plex.algorithms.general.walkers import node2vec_walk, generate_walks
    walks = generate_walks(network.core_network, num_walks=10, walk_length=80)

See ``bin/README.md`` for detailed installation instructions and alternatives.

Virtual Environment Setup
--------------------------

We strongly recommend using a virtual environment:

Using venv
~~~~~~~~~~

.. code-block:: bash

    # Create virtual environment
    python3 -m venv py3plex-env
    
    # Activate (Linux/macOS)
    source py3plex-env/bin/activate
    
    # Activate (Windows)
    py3plex-env\Scripts\activate
    
    # Install py3plex
    pip install git+https://github.com/SkBlaz/py3plex.git

Using conda
~~~~~~~~~~~

.. code-block:: bash

    # Create conda environment
    conda create -n py3plex python=3.10
    
    # Activate
    conda activate py3plex
    
    # Install py3plex
    pip install git+https://github.com/SkBlaz/py3plex.git

Common Installation Issues
--------------------------

Issue: "No module named 'numpy'"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution:** Install numpy first:

.. code-block:: bash

    pip install numpy
    pip install git+https://github.com/SkBlaz/py3plex.git

Issue: Compilation errors on Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution:** Install Visual C++ Build Tools:

1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "Desktop development with C++"
3. Retry installation

Issue: "Permission denied" on Linux/macOS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution:** Use pip install with --user flag:

.. code-block:: bash

    pip install --user git+https://github.com/SkBlaz/py3plex.git

Or use a virtual environment (recommended).

Issue: Old version installed
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution:** Upgrade to latest version:

.. code-block:: bash

    pip install --upgrade git+https://github.com/SkBlaz/py3plex.git

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

py3plex core is distributed under the **MIT License** (permissive, commercial-friendly).

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
     - ✅ Yes
     - Safe for proprietary use
   * - Network visualization
     - MIT
     - ✅ Yes
     - Safe for proprietary use
   * - I/O operations
     - MIT
     - ✅ Yes
     - Safe for proprietary use
   * - Louvain community detection
     - BSD-3-Clause
     - ✅ Yes
     - Safe for proprietary use
   * - Label propagation
     - MIT
     - ✅ Yes
     - Safe for proprietary use
   * - **Infomap community detection**
     - **AGPLv3**
     - ⚠️ Restricted
     - Viral license - requires open-sourcing derived works

Recommendations
~~~~~~~~~~~~~~~

* **For commercial/proprietary projects:** Avoid Infomap functions or use the pure Python ``infomap`` package separately
* **For open-source projects:** All features are safe to use
* **When in doubt:** Use alternative algorithms (Louvain, label propagation) which are BSD/MIT licensed

Next Steps
----------

After installation, proceed to:

* :doc:`quickstart` - Quick introduction to basic features
* :doc:`10min_tutorial` - Comprehensive 10-minute tutorial
* :doc:`basic_usage` - Detailed usage guide

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
