Example Network Analysis
========================

This page demonstrates common network analysis workflows using py3plex.

.. contents:: Table of Contents
   :local:
   :depth: 2

Creating Networks from Scratch
-------------------------------

Simple Multilayer Network
~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a basic multilayer network by adding edges:

.. code-block:: python

    from py3plex.core import multinet
    
    # Initialize network
    network = multinet.multi_layer_network()
    
    # Add edges between nodes in different layers
    network.add_edges([
        ['Alice', 'social', 'Bob', 'social', 1.0],
        ['Bob', 'social', 'Charlie', 'social', 1.0],
        ['Alice', 'work', 'Charlie', 'work', 1.0],
        ['Alice', 'social', 'Alice', 'work', 0.5],  # Inter-layer connection
    ], input_type="list")
    
    # Display basic information
    network.basic_stats()

Random Network Generation
~~~~~~~~~~~~~~~~~~~~~~~~~~

Generate random multilayer networks for testing:

.. code-block:: python

    from py3plex.core import random_generators
    
    # Generate Erdős–Rényi multilayer network
    # 100 nodes, 3 layers, 5% connection probability
    network = random_generators.random_multilayer_ER(
        num_nodes=100,
        num_layers=3,
        probability=0.05,
        directed=False
    )
    
    print(f"Generated network with {len(network.get_nodes())} nodes")

Loading Real Networks
---------------------

From Edge List Files
~~~~~~~~~~~~~~~~~~~~

Load networks from various file formats:

.. code-block:: python

    from py3plex.core import multinet
    
    # Simple edge list (node1 node2)
    network = multinet.multi_layer_network().load_network(
        "network.edgelist",
        input_type="edgelist",
        directed=False
    )
    
    # Multilayer edge list (node1 layer1 node2 layer2 weight)
    network = multinet.multi_layer_network().load_network(
        "multilayer.txt",
        input_type="multiedgelist",
        directed=False
    )

From NetworkX Graphs
~~~~~~~~~~~~~~~~~~~~~

Import existing NetworkX graphs:

.. code-block:: python

    import networkx as nx
    from py3plex.core import multinet
    
    # Create NetworkX graph
    G = nx.karate_club_graph()
    
    # Import to py3plex
    network = multinet.multi_layer_network()
    network.load_network(G, input_type="nx")

Analyzing Networks
------------------

Computing Statistics
~~~~~~~~~~~~~~~~~~~~

Calculate basic and advanced network statistics:

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    # Basic statistics
    network.basic_stats()
    
    # Layer-specific density
    density = mls.layer_density(network, 'layer1')
    print(f"Layer density: {density:.3f}")
    
    # Node activity (fraction of layers where node appears)
    activity = mls.node_activity(network, 'Alice')
    print(f"Node activity: {activity:.3f}")
    
    # Versatility centrality
    versatility = mls.versatility_centrality(network, centrality_type='degree')
    top_nodes = sorted(versatility.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"Top 5 versatile nodes: {top_nodes}")

Community Detection
~~~~~~~~~~~~~~~~~~~

Detect communities in multilayer networks:

.. code-block:: python

    from py3plex.algorithms.community_detection import community_louvain
    
    # Detect communities using Louvain algorithm
    communities = community_louvain.best_partition(network.core_network)
    
    # Count communities
    num_communities = len(set(communities.values()))
    print(f"Detected {num_communities} communities")
    
    # Print community assignments
    for node, comm_id in sorted(communities.items())[:10]:
        print(f"  Node {node} → Community {comm_id}")

Visualizing Networks
--------------------

Basic Visualization
~~~~~~~~~~~~~~~~~~~

Create quick visualizations:

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default
    
    # Basic visualization
    draw_multilayer_default(
        network.get_layers(),
        display=True,
        labels=True,
        node_size=10
    )

Customized Visualization
~~~~~~~~~~~~~~~~~~~~~~~~

Create publication-quality figures:

.. code-block:: python

    import matplotlib.pyplot as plt
    from py3plex.visualization.multilayer import draw_multilayer_default
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Draw with custom settings
    draw_multilayer_default(
        network.get_layers(),
        display=False,
        axis=ax,
        node_size=15,
        edge_size=1.5,
        labels=True,
        background_shape="circle"
    )
    
    # Add title and save
    plt.title("Multilayer Network Structure", fontsize=14)
    plt.savefig("network.png", dpi=300, bbox_inches='tight')
    print("Saved to network.png")

Complete Workflow Example
--------------------------

Putting It All Together
~~~~~~~~~~~~~~~~~~~~~~~

A complete analysis pipeline:

.. code-block:: python

    from py3plex.core import multinet, random_generators
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    from py3plex.algorithms.community_detection import community_louvain
    from py3plex.visualization.multilayer import draw_multilayer_default
    import matplotlib.pyplot as plt
    
    # Step 1: Generate or load network
    network = random_generators.random_multilayer_ER(
        num_nodes=50,
        num_layers=3,
        probability=0.1,
        directed=False
    )
    
    # Step 2: Analyze structure
    print("=== Network Statistics ===")
    network.basic_stats()
    
    # Compute versatility
    versatility = mls.versatility_centrality(network, centrality_type='degree')
    print(f"\nTop 3 versatile nodes:")
    for node, score in sorted(versatility.items(), key=lambda x: x[1], reverse=True)[:3]:
        print(f"  {node}: {score:.3f}")
    
    # Step 3: Detect communities
    communities = community_louvain.best_partition(network.core_network)
    num_communities = len(set(communities.values()))
    print(f"\nDetected {num_communities} communities")
    
    # Step 4: Visualize
    draw_multilayer_default(
        network.get_layers(),
        display=True,
        labels=True,
        node_size=10
    )

Next Steps
----------

- :doc:`basic_usage` - Detailed usage guide
- :doc:`tutorials/community_detection` - Community detection tutorial
- :doc:`visualization_guide` - Comprehensive visualization guide
- See the `examples/ directory <https://github.com/SkBlaz/py3plex/tree/master/examples>`_ for more examples
