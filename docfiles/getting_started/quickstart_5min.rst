5-Minute Quickstart
===================

Create a multilayer network, compute statistics, and visualize—all in 5 minutes.

**You will learn:**

* Create a multilayer network with ``add_edges()``
* Display network statistics with ``basic_stats()``
* Compute layer-specific metrics
* Visualize your network
* Query with the SQL-like DSL

Installation
------------

.. code-block:: bash

    pip install py3plex

For Docker setup, see :doc:`installation`.

Create Your First Network
-------------------------

.. code-block:: python

    from py3plex.core import multinet

    network = multinet.multi_layer_network()

    # Format: [source_node, source_layer, target_node, target_layer, weight]
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Bob', 'friends', 'Carol', 'friends', 1],
        ['Alice', 'colleagues', 'Bob', 'colleagues', 1],
        ['Bob', 'colleagues', 'Dave', 'colleagues', 1]
    ], input_type="list")

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

**Key concept:** The network has 6 node-layer pairs but only 4 unique people. Alice appears in both layers as ``('Alice', 'friends')`` and ``('Alice', 'colleagues')``.

Visualize
---------

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default
    
    draw_multilayer_default([network], display=True)

Nodes are colored by layer. Edges connect nodes within and across layers.

Basic Analysis
--------------

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    # Layer density: how connected is each layer?
    print(f"Friends density: {mls.layer_density(network, 'friends'):.3f}")
    print(f"Colleagues density: {mls.layer_density(network, 'colleagues'):.3f}")
    
    # Node activity: what fraction of layers does Bob appear in?
    print(f"Bob's activity: {mls.node_activity(network, 'Bob'):.3f}")

**Output:**

.. code-block:: text

    Friends density: 0.667
    Colleagues density: 0.667
    Bob's activity: 1.000

* **Density 0.667** — 2 of 3 possible edges exist
* **Activity 1.0** — Bob appears in 100% of layers (both)

Query with DSL
--------------

Use SQL-like queries for network exploration:

.. code-block:: python

    from py3plex.dsl import execute_query
    
    # Find high-degree nodes
    result = execute_query(network, 'SELECT nodes WHERE degree > 1')
    print(f"Found {result['count']} high-degree nodes")
    
    # Get nodes in a specific layer
    result = execute_query(network, 'SELECT nodes WHERE layer="friends"')

See :doc:`../user_guide/dsl` for complete DSL documentation.

Key Concepts
------------

1. **Node-layer pairs:** Nodes are ``(node_id, layer_id)`` tuples. Alice in friends is different from Alice in colleagues.

2. **Layers preserve context:** Each layer represents a different relationship type. Statistics and algorithms respect layer boundaries.

3. **NetworkX compatible:** py3plex uses NetworkX internally. All NetworkX algorithms work.

4. **Multilayer statistics:** Metrics like node activity and edge overlap reveal cross-layer patterns invisible to single-layer tools.

Next Steps
----------

* :doc:`tutorial_10min` — Complete workflow with community detection and embeddings
* :doc:`installation` — Optional dependencies and setup options
* :doc:`common_issues` — Solutions to common problems
* ``examples/`` directory — 50+ working examples
