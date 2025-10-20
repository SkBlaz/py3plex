Command-Line Interface (CLI) Tutorial
======================================

Py3plex includes a comprehensive command-line interface that provides access to all main algorithms and functionality directly from the terminal. This is useful for quick analysis, scripting, and automation workflows.

Installation
------------

The CLI tool is automatically available after installing py3plex:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git

After installation, verify the CLI is available:

.. code-block:: bash

    py3plex --help

Getting Help
------------

The CLI includes built-in documentation for all commands:

.. code-block:: bash

    # Main help with all commands
    py3plex --help
    
    # Help for specific command
    py3plex create --help
    py3plex community --help
    py3plex centrality --help

Available Commands
------------------

The py3plex CLI provides 8 main commands:

* ``create`` - Create new multilayer networks
* ``load`` - Load and inspect networks
* ``community`` - Detect communities
* ``centrality`` - Compute centrality measures
* ``stats`` - Compute multilayer network statistics
* ``visualize`` - Create network visualizations
* ``aggregate`` - Aggregate multilayer networks into single layer
* ``convert`` - Convert between network formats

Creating Networks
-----------------

Create Random Networks
~~~~~~~~~~~~~~~~~~~~~~

Create a simple multilayer network with random edges:

.. code-block:: bash

    py3plex create --nodes 100 --layers 3 --output network.graphml --seed 42

This creates a network with 100 nodes per layer and 3 layers, saving it to ``network.graphml``.

Network Generation Models
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Erdős-Rényi Random Graphs:**

.. code-block:: bash

    py3plex create --nodes 50 --layers 2 --type er --probability 0.15 \
        --output er_network.graphml --seed 42

**Barabási-Albert Preferential Attachment:**

.. code-block:: bash

    py3plex create --nodes 100 --layers 3 --type ba --probability 0.05 \
        --output ba_network.graphml --seed 42

**Watts-Strogatz Small-World:**

.. code-block:: bash

    py3plex create --nodes 50 --layers 2 --type ws --probability 0.2 \
        --output ws_network.graphml --seed 42

Output Formats
~~~~~~~~~~~~~~

The CLI supports multiple output formats (automatically detected from file extension):

* ``.graphml`` - GraphML format (XML-based, recommended)
* ``.gexf`` - GEXF format (XML-based, for Gephi)
* ``.gpickle`` - Python pickle format (binary, fastest)

Loading and Inspecting Networks
--------------------------------

Basic Network Information
~~~~~~~~~~~~~~~~~~~~~~~~~

Display basic network statistics:

.. code-block:: bash

    py3plex load network.graphml --info

**Output:**

.. code-block:: text

    Network Information:
      Nodes: 300
      Edges: 450
      Layers: 3 (layer1, layer2, layer3)
      Directed: False

Detailed Statistics
~~~~~~~~~~~~~~~~~~~

Get comprehensive statistics including layer densities and clustering:

.. code-block:: bash

    py3plex load network.graphml --stats

**Output:**

.. code-block:: text

    Network Information:
      Nodes: 300
      Edges: 450
      Layers: 3 (layer1, layer2, layer3)
      Directed: False

    Basic Statistics:
      Layer Densities:
        layer1: 0.0303
        layer2: 0.0298
        layer3: 0.0305
      Avg Clustering: 0.0421
      Avg Degree: 3.00
      Max Degree: 12

Save to JSON
~~~~~~~~~~~~

Export network information to JSON for further processing:

.. code-block:: bash

    py3plex load network.graphml --info --output network_info.json

Community Detection
-------------------

Louvain Algorithm
~~~~~~~~~~~~~~~~~

Detect communities using the Louvain modularity optimization algorithm:

.. code-block:: bash

    py3plex community network.graphml --algorithm louvain --output communities.json

**Output:**

.. code-block:: text

    Loading network from network.graphml...
    Detecting communities using louvain...
    Found 8 communities
    Community sizes: min=15, max=52, avg=37.5
    Communities saved to communities.json

With Custom Resolution
~~~~~~~~~~~~~~~~~~~~~~

Adjust the resolution parameter to find more or fewer communities:

.. code-block:: bash

    # Higher resolution = more communities
    py3plex community network.graphml --algorithm louvain --resolution 1.5

    # Lower resolution = fewer communities
    py3plex community network.graphml --algorithm louvain --resolution 0.5

Label Propagation
~~~~~~~~~~~~~~~~~

Use label propagation for fast community detection:

.. code-block:: bash

    py3plex community network.graphml --algorithm label_prop --output communities.json

Infomap (Optional)
~~~~~~~~~~~~~~~~~~

If Infomap is installed, use it for overlapping community detection:

.. code-block:: bash

    py3plex community network.graphml --algorithm infomap --output communities.json

Centrality Measures
-------------------

Degree Centrality
~~~~~~~~~~~~~~~~~

Compute degree centrality and show top nodes:

.. code-block:: bash

    py3plex centrality network.graphml --measure degree --top 10

**Output:**

.. code-block:: text

    Loading network from network.graphml...
    Computing degree centrality...

    Top 10 nodes by degree centrality:
      node42---layer1: 12.000000
      node18---layer2: 11.000000
      node77---layer1: 10.000000
      ...

Save Results
~~~~~~~~~~~~

Export centrality scores to JSON:

.. code-block:: bash

    py3plex centrality network.graphml --measure degree --output centrality.json

All Centrality Measures
~~~~~~~~~~~~~~~~~~~~~~~~

**Betweenness Centrality:**

.. code-block:: bash

    py3plex centrality network.graphml --measure betweenness --top 10

**Closeness Centrality:**

.. code-block:: bash

    py3plex centrality network.graphml --measure closeness --top 10

**Eigenvector Centrality:**

.. code-block:: bash

    py3plex centrality network.graphml --measure eigenvector --top 10

**PageRank:**

.. code-block:: bash

    py3plex centrality network.graphml --measure pagerank --top 10

Multilayer Network Statistics
------------------------------

Comprehensive Statistics
~~~~~~~~~~~~~~~~~~~~~~~~

Compute all available multilayer statistics:

.. code-block:: bash

    py3plex stats network.graphml --measure all --output stats.json

**Output includes:**

* Layer densities for each layer
* Clustering coefficient
* Node activity samples
* Versatility centrality (top nodes)
* Edge overlap between layers

Specific Statistics
~~~~~~~~~~~~~~~~~~~

**Layer Density:**

.. code-block:: bash

    py3plex stats network.graphml --measure layer_density

**Clustering Coefficient:**

.. code-block:: bash

    py3plex stats network.graphml --measure clustering

**Node Activity:**

.. code-block:: bash

    py3plex stats network.graphml --measure node_activity

**Versatility Centrality:**

.. code-block:: bash

    py3plex stats network.graphml --measure versatility

**Edge Overlap:**

.. code-block:: bash

    py3plex stats network.graphml --measure edge_overlap

Network Visualization
---------------------

Multilayer Layout
~~~~~~~~~~~~~~~~~

Create a visualization using the specialized multilayer layout:

.. code-block:: bash

    py3plex visualize network.graphml --layout multilayer --output network.png

Standard Layouts
~~~~~~~~~~~~~~~~

Use NetworkX layouts for different visual styles:

**Spring Layout (Force-Directed):**

.. code-block:: bash

    py3plex visualize network.graphml --layout spring --output network_spring.png

**Circular Layout:**

.. code-block:: bash

    py3plex visualize network.graphml --layout circular --output network_circular.png

**Kamada-Kawai Layout:**

.. code-block:: bash

    py3plex visualize network.graphml --layout kamada_kawai --output network_kk.png

Custom Figure Size
~~~~~~~~~~~~~~~~~~

Adjust the output image dimensions:

.. code-block:: bash

    py3plex visualize network.graphml --layout spring --width 15 --height 10 \
        --output large_viz.png

Network Aggregation
-------------------

Aggregate multiple layers into a single layer using different methods:

Sum Aggregation
~~~~~~~~~~~~~~~

Sum edge weights across layers:

.. code-block:: bash

    py3plex aggregate network.graphml --method sum --output aggregated.graphml

Mean Aggregation
~~~~~~~~~~~~~~~~

Average edge weights across layers:

.. code-block:: bash

    py3plex aggregate network.graphml --method mean --output aggregated_mean.graphml

Other Aggregation Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``max`` - Take maximum edge weight across layers
* ``min`` - Take minimum edge weight across layers

Format Conversion
-----------------

Convert Between Formats
~~~~~~~~~~~~~~~~~~~~~~~~

Convert networks between different file formats:

**To GEXF (for Gephi):**

.. code-block:: bash

    py3plex convert network.graphml --output network.gexf

**To JSON:**

.. code-block:: bash

    py3plex convert network.graphml --output network.json

**To gpickle (Python binary):**

.. code-block:: bash

    py3plex convert network.graphml --output network.gpickle

Complete Workflow Examples
---------------------------

Example 1: Create, Analyze, and Visualize
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Step 1: Create a Barabási-Albert network
    py3plex create --nodes 100 --layers 3 --type ba --probability 0.05 \
        --output ba_network.graphml --seed 42
    
    # Step 2: Detect communities
    py3plex community ba_network.graphml --algorithm louvain \
        --output communities.json
    
    # Step 3: Compute centrality
    py3plex centrality ba_network.graphml --measure pagerank --top 20 \
        --output central_nodes.json
    
    # Step 4: Visualize
    py3plex visualize ba_network.graphml --layout spring --width 15 --height 10 \
        --output ba_visualization.png

Example 2: Load, Analyze Statistics, and Export
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Step 1: Load and inspect
    py3plex load existing_network.graphml --stats
    
    # Step 2: Compute comprehensive statistics
    py3plex stats existing_network.graphml --measure all --output stats.json
    
    # Step 3: Convert to GEXF for Gephi
    py3plex convert existing_network.graphml --output for_gephi.gexf

Example 3: Multiple Analysis Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Create network
    py3plex create --nodes 50 --layers 2 --type er --probability 0.15 \
        --output network.graphml --seed 42
    
    # Run all centrality measures
    py3plex centrality network.graphml --measure degree --output degree.json
    py3plex centrality network.graphml --measure betweenness --output betweenness.json
    py3plex centrality network.graphml --measure pagerank --output pagerank.json
    
    # Detect communities with different algorithms
    py3plex community network.graphml --algorithm louvain --output louvain.json
    py3plex community network.graphml --algorithm label_prop --output label_prop.json
    
    # Create multiple visualizations
    py3plex visualize network.graphml --layout multilayer --output viz_ml.png
    py3plex visualize network.graphml --layout spring --output viz_spring.png
    py3plex visualize network.graphml --layout circular --output viz_circular.png

Tips and Best Practices
------------------------

1. **Use Seeds for Reproducibility**: Always use ``--seed`` when creating networks for reproducible results.

2. **JSON Output for Scripting**: Use ``--output`` to save results as JSON for post-processing with other tools.

3. **Check Help for Each Command**: Each command has detailed help with examples:

   .. code-block:: bash

       py3plex <command> --help

4. **Format Auto-Detection**: The CLI automatically detects file formats from extensions, so use appropriate extensions (.graphml, .gexf, .json, .gpickle).

5. **Large Networks**: For large networks (>1000 nodes), prefer:
   
   * ``spring`` or ``circular`` layouts for visualization
   * ``louvain`` for community detection (faster than infomap)
   * ``degree`` centrality for quick analysis

6. **Batch Processing**: Combine CLI commands with shell scripts for batch processing multiple networks.

Common Issues and Solutions
----------------------------

**Issue: "Infomap not available"**

Solution: Infomap requires separate installation. Use ``louvain`` or ``label_prop`` instead.

**Issue: "Eigenvector centrality failed"**

Solution: Some networks don't converge for eigenvector centrality. The CLI automatically falls back to degree centrality.

**Issue: Visualization too slow**

Solution: Use simpler layouts (``circular``) or reduce figure size (``--width 8 --height 6``).

**Issue: Memory errors with large networks**

Solution: Use aggregation to reduce network size before visualization, or compute statistics without visualization.

See Also
--------

* :doc:`../quickstart` - Python API quickstart
* :doc:`../10min_tutorial` - 10-minute Python tutorial
* :doc:`community_detection` - Community detection algorithms in detail
* :doc:`multilayer_centrality` - Centrality measures for multilayer networks
* :doc:`../index` - Main documentation index
