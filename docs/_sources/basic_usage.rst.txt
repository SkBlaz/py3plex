Quick Start Guide
=================

This guide provides a rapid introduction to py3plex, covering installation, basic operations, and your first network analysis. After completing this guide, you'll be able to load networks, perform basic analysis, and create visualizations.

Installation
------------

Py3plex is installed directly from GitHub to ensure you have the latest version with all features and bug fixes:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git

**Optional Dependencies:**

For advanced features, install additional packages:

.. code-block:: bash

    # Advanced visualization (interactive plots with Plotly)
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz]
    
    # Advanced algorithms (Louvain, cdlib community detection)
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[algos]
    
    # High-performance I/O (Apache Arrow, Parquet)
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[arrow]
    
    # All optional dependencies
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[all]

Basic Usage
-----------

Import the library to start working with multilayer networks:

.. code-block:: python

    from py3plex.core import multinet

The ``multinet`` module provides the core ``multi_layer_network`` class, which is the central data structure for all multilayer network operations.

Loading Networks
----------------

Py3plex supports multiple input formats for loading network data. Choose the format that matches your data.

**From Edge Lists (Simple Format):**

Edge lists are the simplest format: each line contains a source-target pair representing an edge.

.. code-block:: python

    # Simple edge list: one edge per line (source target)
    network = multinet.multi_layer_network().load_network(
        "./datasets/test.edgelist", directed=False, input_type="edgelist")

**From Multilayer Edge Lists (With Layer Information):**

Multilayer edge lists include layer information: ``node1 layer1 node2 layer2 weight``

.. code-block:: python

    # Format: source_node source_layer target_node target_layer weight
    network = multinet.multi_layer_network().load_network(
        "./datasets/multiedgelist.txt", directed=False, input_type="multiedgelist")

This format is ideal when you have multiple types of relationships between entities. For example, a social network might have "friends", "colleagues", and "family" layers.

**Multiplex Networks (Same Nodes, Different Layers):**

Multiplex networks are a special case where the same set of nodes appears in all layers:

.. code-block:: python

    # Multiplex: same nodes appear across all layers
    network = multinet.multi_layer_network(network_type="multiplex").load_network(
        "./datasets/simple_multiplex.edgelist", directed=False, input_type="multiplex_edges")

**Understanding Directed vs. Undirected:**

- ``directed=False``: Edges are bidirectional (A→B implies B→A). Use for mutual relationships like friendships.
- ``directed=True``: Edges have direction (A→B does not imply B→A). Use for relationships like citations, followers, or flows.

Network Operations
------------------

Once loaded, you can inspect and manipulate your network using several built-in methods.

**Basic Statistics:**

Always run ``basic_stats()`` first to verify your network loaded correctly:

.. code-block:: python

    # Display comprehensive network statistics
    network.basic_stats()

Expected output:

.. code-block:: text

    Number of nodes: 150
    Number of edges: 432
    Number of unique nodes (as node-layer tuples): 150
    Number of unique node IDs (across all layers): 50
    Nodes per layer:
      Layer 'layer1': 50 nodes
      Layer 'layer2': 50 nodes
      Layer 'layer3': 50 nodes

**Visualization:**

Create a quick visualization to inspect the network structure:

.. code-block:: python

    # Visualize with default settings
    network.visualize_network()

This creates a hairball-style plot showing nodes colored by layer. For large networks (>500 nodes), consider adding parameters to reduce visual clutter:

.. code-block:: python

    # For larger networks, simplify the visualization
    network.visualize_network(
        node_size=5,           # Smaller nodes
        labels=False,          # Hide labels
        alphalevel=0.1         # More transparent edges
    )

For More Examples
-----------------

The examples directory contains comprehensive tutorials organized by topic:

**Visualization:**

- ``example_multilayer_visualization.py`` - Core visualization techniques
- ``example_interactive_hairball.py`` - Interactive plots with Plotly
- ``example_community_visualization.py`` - Visualizing communities

**I/O and Data Loading:**

- ``example_IO.py`` - Loading and saving networks in various formats
- ``example_arrow_io.py`` - High-performance Arrow/Parquet I/O
- ``example_csv_loading.py`` - CSV format with sidecars

**Network Manipulation:**

- ``example_manipulation.py`` - Adding, removing, filtering nodes and edges
- ``example_subnetworks.py`` - Extracting subnetworks by layer or nodes
- ``example_aggregation.py`` - Aggregating layers

**Core Analysis:**

- ``example_multilayer_functionality.py`` - Comprehensive feature tour
- ``example_basic_stats.py`` - Computing network statistics
- ``example_centrality.py`` - Node centrality measures

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples

Next Steps
----------

After mastering the basics, explore these advanced topics:

- :doc:`getting_started/tutorial_10min` - Comprehensive 10-minute tutorial
- :doc:`user_guide/networks` - Advanced network creation and manipulation
- :doc:`user_guide/statistics` - Multilayer network statistics
- :doc:`user_guide/community_detection` - Detecting communities across layers
- :doc:`user_guide/visualization` - Publication-quality visualizations
