Common Issues and Troubleshooting
==================================

Quick fixes for frequent issues when getting started with py3plex. Work through the sections in order (installation → data loading → visualization → performance → algorithms). Apply one fix at a time, then rerun your script before trying the next so you know which change helped.

Installation Issues
-------------------

"No module named 'numpy'"
~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Import error when trying to use py3plex (``ModuleNotFoundError``).

**Solution:** Install numpy first (preferably in a virtual environment to avoid system-wide changes). Upgrading pip often avoids build warnings:

.. code-block:: bash

    python -m pip install --upgrade pip
    python -m pip install numpy
    python -m pip install py3plex

Compilation Errors on Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** C++ compilation errors during installation on Windows.

**Solution:** Install Visual C++ Build Tools, then reinstall:

1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "Desktop development with C++"
3. Restart your shell, then retry installation

.. code-block:: bash

    python -m pip install py3plex

"Permission denied" on Linux/macOS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Permission errors during pip install (for example, ``[Errno 13] Permission denied`` or ``EACCES``).

**Solution 1:** Use a virtual environment (recommended; keeps dependencies isolated):

.. code-block:: bash

    python3 -m venv py3plex-env
    source py3plex-env/bin/activate  # On Windows: py3plex-env\Scripts\activate
    python -m pip install --upgrade pip
    python -m pip install py3plex

**Solution 2:** Use pip install with --user flag (if you cannot use venv):

.. code-block:: bash

    python -m pip install --user py3plex

Old Version Installed
~~~~~~~~~~~~~~~~~~~~~

**Problem:** Changes not reflecting or documentation mentions newer features.

**Solution:** Verify the installed version, then upgrade to the latest release:

.. code-block:: bash

    python -m pip show py3plex
    python -m pip install --upgrade py3plex
    python -m pip show py3plex  # Confirm the version changed

Data Loading Issues
-------------------

File Not Found Errors
~~~~~~~~~~~~~~~~~~~~~

**Problem:** ``FileNotFoundError`` when loading networks.

**Solution 1:** Confirm the file exists and your working directory is correct (``os.getcwd()`` often differs from the script directory):

.. code-block:: python

    import os

    print("Current directory:", os.getcwd())
    print("File exists:", os.path.exists("data.edgelist"))

**Solution 2:** Use an absolute path to avoid ambiguity:

.. code-block:: python

    network_path = "/absolute/path/to/data.edgelist"
    network = multinet.multi_layer_network().load_network(
        network_path, input_type="edgelist", directed=False
    )

**Solution 3:** Build a path relative to the script location (avoids brittle working-directory assumptions):

.. code-block:: python

    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "data", "network.edgelist")
    network = multinet.multi_layer_network().load_network(
        data_path, input_type="edgelist", directed=False
    )

Empty or Malformed Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Network loads but has no nodes or edges (zero counts).

**Solution:** Confirm the file contents and chosen ``input_type`` match. Pick the loader that matches your columns and delimiter:

.. code-block:: python

    # For simple edge lists (source target)
    network.load_network("data.txt", input_type="edgelist")
    
    # For multilayer edge lists (source target layer)
    network.load_network("data.txt", input_type="multiedgelist")
    
    # Always verify after loading
    network.basic_stats()

If counts are still zero:

* Inspect the first few lines for the expected number of columns and delimiters.
* Ensure header rows are skipped or removed before loading.
* Check that the file is not empty (``os.path.getsize``).

Visualization Issues
--------------------

Visualization Not Showing
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** No window appears when calling visualization functions (plots silently finish).

**Solution 1:** For Jupyter notebooks, enable inline plots:

.. code-block:: python

    %matplotlib inline

**Solution 2:** For scripts, explicitly show the plot or set ``display=True``:

.. code-block:: python

    import matplotlib.pyplot as plt
    
    # Your visualization code
    draw_multilayer_default([network], display=False)
    
    # Explicitly show
    plt.show()

**Solution 3:** Save to file instead of displaying:

.. code-block:: python

    from py3plex.visualization.multilayer import hairball_plot
    import matplotlib.pyplot as plt
    
    plt.figure(figsize=(10, 10))
    hairball_plot(network.core_network, layout_algorithm="force")
    plt.savefig("network.png", dpi=150, bbox_inches='tight')
    plt.close()

"No Display Found" Error
~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Error on headless servers or SSH sessions without X11.

**Solution:** Use Agg backend for matplotlib so plots are rendered to files:

.. code-block:: python

    import matplotlib
    matplotlib.use('Agg')  # Must be before importing pyplot
    import matplotlib.pyplot as plt
    
    # Now visualization will save to file instead of displaying
    from py3plex.visualization.multilayer import draw_multilayer_default
    draw_multilayer_default([network], display=False)
    plt.savefig("output.png")

Blurry or Low-Quality Plots
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Plots look pixelated or blurry.

**Solution:** Increase DPI and tighten bounding boxes when saving:

.. code-block:: python

    plt.savefig("network.png", dpi=300, bbox_inches="tight")

Missing Dependencies
--------------------

**Tip:** Feature-specific extras are optional; install only what you need.

"No module named 'plotly'"
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Interactive visualization features not working.

**Solution:** Install visualization extras (plotly and related dependencies):

.. code-block:: bash

    python -m pip install "py3plex[viz]"  # Quotes required on some shells

"No module named 'infomap'"
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Infomap community detection not working.

**Solution:** Install Infomap support:

.. code-block:: bash

    python -m pip install "py3plex[infomap]"  # Quotes required on some shells

Or use alternative community detection methods if you cannot install the extra:

.. code-block:: python

    from py3plex.algorithms.community_detection import community_louvain
    communities = community_louvain.best_partition(network.core_network)

Performance Issues
------------------

Very Slow Loading
~~~~~~~~~~~~~~~~~

**Problem:** Loading large networks takes too long.

**Solution 1:** Prefer Arrow/Parquet for large networks to speed up I/O:

.. code-block:: bash

    # Install Arrow support
    python -m pip install "py3plex[arrow]"  # Quotes required on some shells

.. code-block:: python

    from py3plex.io import read, write
    
    # Save in efficient format
    write(network, "network.arrow")
    
    # Load faster from Arrow
    network = read("network.arrow")

**Solution 2:** Process in chunks or use subnetworks for testing:

.. code-block:: python

    # Extract a single layer for testing
    layer_1 = network.subnetwork(['layer1'], subset_by="layers")
    
    # Work with the smaller network
    layer_1.basic_stats()

Out of Memory Errors
~~~~~~~~~~~~~~~~~~~~

**Problem:** Python crashes or raises MemoryError with large networks.

**Solution:** See :doc:`../deployment/performance_scalability` for:

* Memory-efficient loading strategies
* Batch processing techniques
* Sparse matrix representations
* Subnetwork extraction

Algorithm Issues
----------------

Community Detection Returns Trivial Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Each node in its own community or all nodes in one community (degenerate partition).

**Solution:** Adjust algorithm parameters and randomness, then compare partitions:

.. code-block:: python

    from py3plex.algorithms.community_detection.multilayer_modularity import (
        louvain_multilayer
    )
    
    # Try different resolution parameters
    partition = louvain_multilayer(
        network,
        gamma=0.5,    # Lower = fewer, larger communities
        omega=1.5,    # Higher = more layer consistency
        random_state=42
    )

Random Walk or Embedding Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Random walk or Node2Vec functions fail.

**Solution:** Ensure the graph is connected before running walks:

.. code-block:: python

    import networkx as nx
    
    # Check connectivity
    if not nx.is_connected(network.core_network.to_undirected()):
        print("Warning: Network is not connected")
        
        # Get largest component
        largest = max(nx.connected_components(
            network.core_network.to_undirected()
        ), key=len)
        
        # Create subgraph
        subgraph = network.core_network.subgraph(largest)

Use the subgraph for embedding or random walk routines if the full network is disconnected. Re-attach results to the full graph only after inspecting coverage.

Docker Issues
-------------

Docker Build Fails
~~~~~~~~~~~~~~~~~~

**Problem:** Docker build fails or takes very long.

**Solution:** Clear Docker cache (removes all unused images and build layers) and rebuild:

.. code-block:: bash

    docker system prune -a
    docker build --no-cache -t py3plex:latest .

Cannot Access Files in Docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Docker container can't see your data files.

**Solution:** Mount volumes correctly so container paths resolve:

.. code-block:: bash

    # Mount current directory
    docker run -v $(pwd):/data py3plex:latest /data/network.edgelist
    
    # On Windows (PowerShell)
    docker run -v ${PWD}:/data py3plex:latest /data/network.edgelist

Adjust the command after the image name to match your workflow (for example, ``py3plex load /data/network.edgelist --info``).

See :doc:`../deployment/cli_and_docker` for complete Docker documentation.

Getting Help
------------

If you encounter an issue not covered here:

1. **Search GitHub Issues:** https://github.com/SkBlaz/py3plex/issues
2. **Check Documentation:** https://skblaz.github.io/py3plex/
3. **Browse Examples:** https://github.com/SkBlaz/py3plex/tree/master/examples

When reporting issues, include:
* Python version (``python --version``)
* py3plex version (``python -m pip show py3plex``)
* Operating system
* Full error traceback
* Minimal code to reproduce the problem (or a link to the example you ran)

Related Pages
-------------

* :doc:`installation` - Complete installation guide
* :doc:`tutorial_10min` - Comprehensive tutorial from basics to advanced topics
* :doc:`../deployment/performance_scalability` - Performance optimization
