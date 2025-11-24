5-Minute Quickstart
===================

Get started with py3plex in just 5 minutes with this minimal example.

Installation
------------

Install py3plex from GitHub:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git

If you prefer Docker, see :doc:`installation` for container-based setup.

Hello World: Your First Multilayer Network
-------------------------------------------

Create a simple multilayer network with just a few lines of code:

.. code-block:: python

    from py3plex.core import multinet

    # Create a new multilayer network
    network = multinet.multi_layer_network()

    # Add edges (nodes are created automatically)
    # Format: [source_node, source_layer, target_node, target_layer, weight]
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Bob', 'friends', 'Carol', 'friends', 1],
        ['Alice', 'colleagues', 'Bob', 'colleagues', 1],
        ['Bob', 'colleagues', 'Dave', 'colleagues', 1]
    ], input_type="list")

    # Display basic statistics
    network.basic_stats()

**Output:**

.. code-block:: text

    Number of nodes: 6
    Number of edges: 4
    Number of unique nodes (as node-layer tuples): 6
    Number of unique node IDs (across all layers): 4
    Nodes per layer:
      Layer 'friends': 3 nodes
      Layer 'colleagues': 3 nodes

Visualize Your Network
----------------------

Create a simple visualization:

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default
    
    # Simple visualization
    draw_multilayer_default([network], display=True)

This creates a visual plot showing your multilayer network with nodes colored by layer.

Basic Analysis
--------------

Compute some basic network statistics:

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    # How dense is each layer?
    friends_density = mls.layer_density(network, 'friends')
    colleagues_density = mls.layer_density(network, 'colleagues')
    
    print(f"Friends layer density: {friends_density:.3f}")
    print(f"Colleagues layer density: {colleagues_density:.3f}")
    
    # How active is Bob across layers?
    bob_activity = mls.node_activity(network, 'Bob')
    print(f"Bob's activity: {bob_activity:.3f}")

**Output:**

.. code-block:: text

    Friends layer density: 0.667
    Colleagues layer density: 0.667
    Bob's activity: 1.000

Bob appears in both layers (100% activity) and both layers are well-connected.

What's Next?
------------

Congratulations! You've created your first multilayer network. To dive deeper:

* :doc:`tutorial_10min` - Comprehensive 10-minute tutorial with more features
* :doc:`installation` - Complete installation guide with optional dependencies
* :doc:`common_issues` - Troubleshooting common problems
* :doc:`../user_guide/networks` - Learn more about creating and loading networks
* :doc:`../user_guide/visualization` - Advanced visualization techniques

Need Help?
----------

* **Documentation:** https://skblaz.github.io/py3plex/
* **GitHub Issues:** https://github.com/SkBlaz/py3plex/issues
* **Examples:** `examples/ directory <https://github.com/SkBlaz/py3plex/tree/master/examples>`_
