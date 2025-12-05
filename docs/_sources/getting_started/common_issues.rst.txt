Common Issues and Troubleshooting
==================================

This guide helps you troubleshoot common problems when getting started with py3plex.

Installation Issues
-------------------

"No module named 'numpy'"
~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Import error when trying to use py3plex.

**Solution:** Install numpy first:

.. code-block:: bash

    pip install numpy
    pip install py3plex

Compilation Errors on Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** C++ compilation errors during installation on Windows.

**Solution:** Install Visual C++ Build Tools:

1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "Desktop development with C++"
3. Retry installation

.. code-block:: bash

    pip install py3plex

"Permission denied" on Linux/macOS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Permission errors during pip install.

**Solution 1:** Use pip install with --user flag:

.. code-block:: bash

    pip install --user py3plex

**Solution 2:** Use a virtual environment (recommended):

.. code-block:: bash

    python3 -m venv py3plex-env
    source py3plex-env/bin/activate  # On Windows: py3plex-env\Scripts\activate
    pip install py3plex

Old Version Installed
~~~~~~~~~~~~~~~~~~~~~

**Problem:** Changes not reflecting or documentation mentions newer features.

**Solution:** Upgrade to the latest version:

.. code-block:: bash

    pip install --upgrade py3plex

Data Loading Issues
-------------------

File Not Found Errors
~~~~~~~~~~~~~~~~~~~~~

**Problem:** ``FileNotFoundError`` when loading networks.

**Solution 1:** Use absolute paths:

.. code-block:: python

    import os
    
    network_path = "/absolute/path/to/data.edgelist"
    network = multinet.multi_layer_network().load_network(
        network_path, input_type="edgelist", directed=False
    )

**Solution 2:** Ensure you're running from the correct directory:

.. code-block:: python

    import os
    
    # Check current directory
    print("Current directory:", os.getcwd())
    
    # List files
    print("Files:", os.listdir('.'))

**Solution 3:** Use paths relative to script location:

.. code-block:: python

    import os
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(script_dir, "data", "network.edgelist")

Empty or Malformed Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Network loads but has no nodes or edges.

**Solution:** Check file format matches input_type:

.. code-block:: python

    # For simple edge lists (source target)
    network.load_network("data.txt", input_type="edgelist")
    
    # For multilayer edge lists (source target layer)
    network.load_network("data.txt", input_type="multiedgelist")
    
    # Always verify after loading
    network.basic_stats()

Visualization Issues
--------------------

Visualization Not Showing
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** No window appears when calling visualization functions.

**Solution 1:** For Jupyter notebooks, add at the top:

.. code-block:: python

    %matplotlib inline

**Solution 2:** For scripts, explicitly show the plot:

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

**Solution:** Use Agg backend for matplotlib:

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

**Solution:** Increase DPI when saving:

.. code-block:: python

    plt.savefig("network.png", dpi=300, bbox_inches='tight')

Missing Dependencies
--------------------

"No module named 'plotly'"
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Interactive visualization features not working.

**Solution:** Install visualization extras:

.. code-block:: bash

    pip install py3plex[viz]

"No module named 'infomap'"
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Infomap community detection not working.

**Solution:** Install Infomap support:

.. code-block:: bash

    pip install py3plex[infomap]

Or use alternative community detection methods:

.. code-block:: python

    from py3plex.algorithms.community_detection import community_louvain
    communities = community_louvain.best_partition(network.core_network)

Performance Issues
------------------

Very Slow Loading
~~~~~~~~~~~~~~~~~

**Problem:** Loading large networks takes too long.

**Solution 1:** Use Arrow/Parquet format for large networks:

.. code-block:: bash

    # Install Arrow support
    pip install py3plex[arrow]

.. code-block:: python

    from py3plex.io import read, write
    
    # Save in efficient format
    write(network, "network.arrow")
    
    # Load much faster
    network = read("network.arrow")

**Solution 2:** Process in chunks or use subnetworks:

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

**Problem:** Each node in its own community or all nodes in one community.

**Solution:** Adjust algorithm parameters:

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

**Solution:** Ensure network is connected:

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

Docker Issues
-------------

Docker Build Fails
~~~~~~~~~~~~~~~~~~

**Problem:** Docker build fails or takes very long.

**Solution:** Clear Docker cache and rebuild:

.. code-block:: bash

    docker system prune -a
    docker build --no-cache -t py3plex:latest .

Cannot Access Files in Docker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Docker container can't see your data files.

**Solution:** Mount volumes correctly:

.. code-block:: bash

    # Mount current directory
    docker run -v $(pwd):/data py3plex:latest /data/network.edgelist
    
    # On Windows (PowerShell)
    docker run -v ${PWD}:/data py3plex:latest /data/network.edgelist

See :doc:`../deployment/cli_and_docker` for complete Docker documentation.

Getting Help
------------

If you encounter an issue not covered here:

1. **Search GitHub Issues:** https://github.com/SkBlaz/py3plex/issues
2. **Check Documentation:** https://skblaz.github.io/py3plex/
3. **Browse Examples:** https://github.com/SkBlaz/py3plex/tree/master/examples

When reporting issues, include:
* Python version (``python --version``)
* py3plex version (``pip show py3plex``)
* Operating system
* Full error traceback
* Minimal code to reproduce the problem

Related Pages
-------------

* :doc:`installation` - Complete installation guide
* :doc:`quickstart_5min` - Quick introduction
* :doc:`tutorial_10min` - Comprehensive tutorial
* :doc:`../deployment/performance_scalability` - Performance optimization
