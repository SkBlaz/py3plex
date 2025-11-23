Dependency Management and Troubleshooting
==========================================

This guide covers dependency installation, optional features, and common troubleshooting scenarios.

.. contents:: Table of Contents
   :local:
   :depth: 2

Core Dependencies
-----------------

Automatic Installation
~~~~~~~~~~~~~~~~~~~~~~

Core dependencies are **automatically installed** when you install Py3plex:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git

**Core dependencies include:**

* ``networkx >= 2.5`` - Graph data structures and algorithms
* ``numpy >= 1.19.0`` - Numerical computing
* ``scipy >= 1.5.0`` - Scientific computing and sparse matrices
* ``matplotlib >= 3.3.0`` - Static visualization
* ``pandas`` - Data manipulation
* ``scikit-learn >= 0.24.0`` - Machine learning utilities
* ``tqdm >= 4.40.0`` - Progress bars
* ``rdflib >= 6.0.0`` - Semantic web support
* ``bitarray >= 2.0.0`` - Efficient boolean arrays
* ``seaborn >= 0.11.0`` - Statistical visualization
* ``gensim >= 4.0.0`` - Topic modeling and embeddings
* ``cython >= 0.29.0`` - C extensions for performance

Verifying Installation
~~~~~~~~~~~~~~~~~~~~~~

Check that Py3plex and dependencies are installed:

.. code-block:: python

    import py3plex
    print(f"Py3plex version: {py3plex.__version__}")
    
    # Check key dependencies
    import networkx as nx
    import numpy as np
    import scipy
    import matplotlib
    
    print(f"NetworkX: {nx.__version__}")
    print(f"NumPy: {np.__version__}")
    print(f"SciPy: {scipy.__version__}")
    print(f"Matplotlib: {matplotlib.__version__}")
    
    print("\n[OK] All core dependencies available")

Optional Dependencies
---------------------

Py3plex offers several optional feature sets. Install only what you need.

Advanced Visualization (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install Plotly and igraph for interactive and advanced visualizations:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz]

**Provides:**

* ``plotly >= 5.0.0`` - Interactive network plots
* ``python-igraph >= 0.10.0`` - Fast C-based graph algorithms

**Use cases:**

* Interactive exploration in Jupyter notebooks
* Web-based visualizations
* Fast layout computation
* Large network rendering

**Example:**

.. code-block:: python

    # Check if available
    try:
        import plotly
        import igraph
        print("[OK] Advanced visualization available")
    except ImportError:
        print("[X] Install with: pip install py3plex[viz]")

Additional Algorithms
~~~~~~~~~~~~~~~~~~~~~

Install extra community detection and clustering algorithms:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[algos]

**Provides:**

* ``python-louvain >= 0.16`` - Louvain modularity optimization
* ``cdlib >= 0.3.0`` - Community discovery library (many algorithms)

**Use cases:**

* Advanced community detection
* Algorithm comparison studies
* Overlapping community detection
* Hierarchical clustering

**Example:**

.. code-block:: python

    # Using Louvain algorithm
    from py3plex.algorithms.community_detection import community_louvain
    
    communities = community_louvain.best_partition(network.core_network)
    print(f"Detected {len(set(communities.values()))} communities")

Infomap Community Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install Infomap for information-theoretic community detection:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[infomap]

**Provides:**

* ``infomap >= 2.0.0`` - Information flow-based community detection

**WARNING️ Important licensing note:**

Infomap is licensed under **AGPLv3** (viral copyleft license). If you use Infomap functions
in your project, your project may also need to be AGPLv3 licensed.

**For commercial/proprietary projects:** Use alternative algorithms:

* Louvain (BSD-3-Clause)
* Label propagation (MIT)
* Built-in NetworkX algorithms (BSD)

**Example:**

.. code-block:: python

    # Check if available
    try:
        import infomap
        print("[OK] Infomap available")
    except ImportError:
        print("[X] Install with: pip install py3plex[infomap]")
        print("  OR use Louvain algorithm instead")

Installing All Optional Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install everything at once:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz,algos,infomap]

Development Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

For contributors and developers:

.. code-block:: bash

    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    pip install -e ".[dev]"

**Provides:**

* ``pytest`` - Testing framework
* ``pytest-cov`` - Coverage reporting
* ``pytest-benchmark`` - Performance testing
* ``black`` - Code formatting
* ``ruff`` - Linting
* ``mypy`` - Type checking
* ``sphinx`` - Documentation building
* ``crosshair-tool`` - Formal verification
* ``hypothesis`` - Property-based testing

Dependency Troubleshooting
---------------------------

Common Installation Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~

Issue: "Could not find a version that satisfies the requirement"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause:** Python version too old or package unavailable

**Solution 1:** Upgrade Python to 3.8 or higher

.. code-block:: bash

    python --version  # Check current version
    # If < 3.8, install Python 3.10 or 3.11

**Solution 2:** Update pip

.. code-block:: bash

    pip install --upgrade pip setuptools wheel

**Solution 3:** Check PyPI availability

.. code-block:: bash

    pip search networkx  # Check if package exists

Issue: "No matching distribution found"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause:** Network issues or package not available for your platform

**Solution 1:** Check internet connection

.. code-block:: bash

    ping pypi.org

**Solution 2:** Use alternative index

.. code-block:: bash

    pip install --index-url https://pypi.org/simple/ \
        git+https://github.com/SkBlaz/py3plex.git

**Solution 3:** Check platform compatibility

Some packages may not be available for all platforms (e.g., Windows ARM, older macOS).

Issue: "Failed building wheel"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause:** Missing C compiler or development headers

**Solution (Ubuntu/Debian):**

.. code-block:: bash

    sudo apt-get update
    sudo apt-get install python3-dev build-essential

**Solution (macOS):**

.. code-block:: bash

    xcode-select --install

**Solution (Windows):**

1. Download Visual C++ Build Tools
2. Install "Desktop development with C++"
3. Restart and try again

Issue: "Permission denied"
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause:** Trying to install in system Python without sudo

**Solution 1:** Use virtual environment (recommended)

.. code-block:: bash

    python3 -m venv py3plex-env
    source py3plex-env/bin/activate  # Linux/macOS
    # OR: py3plex-env\Scripts\activate  # Windows
    
    pip install git+https://github.com/SkBlaz/py3plex.git

**Solution 2:** User installation

.. code-block:: bash

    pip install --user git+https://github.com/SkBlaz/py3plex.git

Runtime Dependency Issues
~~~~~~~~~~~~~~~~~~~~~~~~~

Issue: "No module named 'plotly'"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause:** Optional visualization dependency not installed

**Solution:**

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz]
    
    # OR install just what you need
    pip install plotly

**Workaround:** Use matplotlib for visualization (included by default)

Issue: "ImportError: cannot import name 'infomap'"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause:** Optional Infomap package not installed

**Solution:**

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[infomap]

**Alternative:** Use Louvain algorithm instead:

.. code-block:: python

    from py3plex.algorithms.community_detection import community_louvain
    communities = community_louvain.best_partition(network.core_network)

Issue: "Qt platform plugin could not be initialized"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause:** Matplotlib backend issue (usually on headless servers)

**Solution:** Use non-interactive backend

.. code-block:: python

    import matplotlib
    matplotlib.use('Agg')  # Must be before importing pyplot
    import matplotlib.pyplot as plt

Issue: "MemoryError" with large networks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause:** Insufficient RAM for dense operations

**Solution 1:** Use sparse matrices (automatic for most operations)

**Solution 2:** Sample network

.. code-block:: python

    import random
    
    # Sample 10% of nodes
    all_nodes = list(network.get_nodes())
    sample_size = len(all_nodes) // 10
    sample_nodes = random.sample(all_nodes, sample_size)
    
    subnetwork = network.get_subnetwork(sample_nodes)

**Solution 3:** Increase swap space or use machine with more RAM

Version Conflicts
~~~~~~~~~~~~~~~~~

Issue: "Incompatible versions of numpy and scipy"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause:** Version mismatch between numerical packages

**Solution:** Reinstall in correct order

.. code-block:: bash

    pip uninstall numpy scipy
    pip install numpy scipy
    pip install git+https://github.com/SkBlaz/py3plex.git

Issue: "AttributeError: module 'networkx' has no attribute 'X'"
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Cause:** NetworkX version too old

**Solution:** Upgrade NetworkX

.. code-block:: bash

    pip install --upgrade networkx
    
    # Verify version
    python -c "import networkx; print(networkx.__version__)"
    # Should be >= 2.5

LLM-Friendly Dependency Guidance
---------------------------------

For AI Assistants Helping Users
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a user encounters a missing dependency error:

**Step 1:** Identify the missing package from the error message

.. code-block:: python

    # Example error:
    # ModuleNotFoundError: No module named 'plotly'

**Step 2:** Suggest appropriate installation command

.. code-block:: bash

    # For plotly (visualization):
    pip install plotly
    
    # OR install full viz bundle:
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz]

**Step 3:** Provide alternative solutions

If installation fails, suggest:

1. Using built-in alternatives (matplotlib instead of plotly)
2. Checking Python version compatibility
3. Using virtual environment
4. Checking firewall/proxy settings

Quick Dependency Checker Script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provide users with this diagnostic script:

.. code-block:: python

    """Check Py3plex dependencies."""
    
    def check_dependencies():
        """Check which dependencies are available."""
        
        required = {
            'networkx': 'Core',
            'numpy': 'Core',
            'scipy': 'Core',
            'matplotlib': 'Core',
            'pandas': 'Core',
        }
        
        optional = {
            'plotly': 'Visualization',
            'igraph': 'Visualization',
            'infomap': 'Community detection',
            'python-louvain': 'Community detection',
        }
        
        print("=== Py3plex Dependency Check ===\n")
        
        print("Required packages:")
        for package, category in required.items():
            try:
                __import__(package.replace('-', '_'))
                print(f"  [OK] {package:20s} ({category})")
            except ImportError:
                print(f"  [X] {package:20s} ({category}) - MISSING!")
        
        print("\nOptional packages:")
        for package, category in optional.items():
            try:
                __import__(package.replace('-', '_'))
                print(f"  [OK] {package:20s} ({category})")
            except ImportError:
                print(f"  [X] {package:20s} ({category}) - Not installed")
        
        print("\nInstallation commands:")
        print("  Core: pip install git+https://github.com/SkBlaz/py3plex.git")
        print("  Viz:  pip install py3plex[viz]")
        print("  All:  pip install py3plex[viz,algos]")
    
    if __name__ == '__main__':
        check_dependencies()

Save as ``check_deps.py`` and run:

.. code-block:: bash

    python check_deps.py

Best Practices
--------------

Recommendations for Different Use Cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**For research (exploratory):**

.. code-block:: bash

    # Core only
    pip install git+https://github.com/SkBlaz/py3plex.git

**For visualization-heavy work:**

.. code-block:: bash

    # Core + visualization
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz]

**For comprehensive analysis:**

.. code-block:: bash

    # Everything except Infomap (avoid AGPLv3 license)
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz,algos]

**For commercial projects:**

.. code-block:: bash

    # Core + algos (all permissive licenses)
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz,algos]
    # Avoid: infomap (AGPLv3)

Virtual Environment Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Create project directory
    mkdir my_network_project
    cd my_network_project
    
    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate  # Linux/macOS
    
    # Install Py3plex
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz,algos]
    
    # Save dependencies
    pip freeze > requirements.txt
    
    # Later, recreate environment
    pip install -r requirements.txt

Keeping Dependencies Updated
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Update Py3plex
    pip install --upgrade git+https://github.com/SkBlaz/py3plex.git
    
    # Update all dependencies
    pip install --upgrade numpy scipy networkx matplotlib
    
    # Check for outdated packages
    pip list --outdated

Next Steps
----------

- :doc:`installation` - Full installation guide
- :doc:`getting_started/quickstart_5min` - Get started with Py3plex
- :doc:`tutorials/csv_loading` - Load your data
- :doc:`visualization_guide` - Create visualizations

For installation help, open an issue on `GitHub Issues <https://github.com/SkBlaz/py3plex/issues>`_.
