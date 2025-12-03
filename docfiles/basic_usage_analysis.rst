Network Analysis
================

This guide covers core network analysis operations in py3plex, including iteration, subnetwork extraction, and integration with NetworkX for standard graph algorithms.

Understanding the Data Model
----------------------------

Before diving into analysis, it's important to understand how py3plex represents multilayer networks:

**Node-Layer Pairs:** In a multilayer network, nodes are represented as tuples ``(node_id, layer_id)``. This means the same entity (e.g., "Alice") can appear multiple times—once in each layer she participates in. The tuple ``('Alice', 'friends')`` and ``('Alice', 'colleagues')`` are different nodes in the network, even though they represent the same person.

**Why This Matters:** This representation allows each node to have different properties and connections in different layers. Alice might be a hub in her friend network but peripheral in her colleague network.

Core Operations
---------------

The ``multi_layer_network`` object provides methods for iterating over and extracting information from your network.

Basic Iteration
~~~~~~~~~~~~~~~

Iterating over nodes and edges is the foundation of most network analysis tasks:

.. code-block:: python

    from py3plex.core import multinet
    
    # Load a multilayer network
    network = multinet.multi_layer_network().load_network(
        "../datasets/multiedgelist.txt", input_type="multiedgelist", directed=False)
    
    # Iterate over all edges
    # Each edge is a tuple: (source_node, target_node, attributes_dict)
    for edge in network.get_edges(data=True):
        source, target, attrs = edge
        print(f"Edge: {source} -> {target}, Weight: {attrs.get('weight', 1.0)}")
    
    # Iterate over all nodes
    # Each node is a tuple: (node_id, attributes_dict)
    for node in network.get_nodes(data=True):
        node_id, attrs = node
        print(f"Node: {node_id}, Layer: {attrs.get('type', 'unknown')}")

**Expected Output** (example edges and nodes):

.. code-block:: text

    Edge: ('1', '1') -> ('2', '1'), Weight: 1.0
    Edge: ('1', '1') -> ('3', '1'), Weight: 1.0
    Edge: ('2', '1') -> ('6', '2'), Weight: 1.0
    ...
    Node: ('1', '1'), Layer: 1
    Node: ('2', '1'), Layer: 1
    Node: ('6', '2'), Layer: 2
    ...

**Interpreting Node Tuples:**

- ``('1', '1')`` means "node 1 in layer 1"
- ``('6', '2')`` means "node 6 in layer 2"
- The ``type`` attribute stores the layer ID for each node

Extracting Subnetworks
~~~~~~~~~~~~~~~~~~~~~~

Subnetwork extraction allows you to focus on specific parts of your multilayer network for targeted analysis:

.. code-block:: python

    # Extract by layer: Get all nodes and edges within specific layers
    # Useful for comparing structure across layers
    layer_subnet = network.subnetwork(['1'], subset_by="layers")
    
    # Extract by node names: Get specific entities across all their layers
    # Useful for tracking individuals across contexts
    node_subnet = network.subnetwork(['1'], subset_by="node_names")
    
    # Extract by node-layer pairs: Get exactly specified nodes
    # Useful for precise control over analysis scope
    specific_subnet = network.subnetwork(
        [('1','1'), ('2','1')], subset_by="node_layer_names")

**When to Use Each Method:**

- **subset_by="layers"**: Analyze one layer independently, compare layer properties
- **subset_by="node_names"**: Track specific entities across all layers they appear in
- **subset_by="node_layer_names"**: Precise extraction of specific node-layer pairs

NetworkX Integration
~~~~~~~~~~~~~~~~~~~~

Py3plex networks are built on NetworkX, allowing you to use any NetworkX algorithm:

.. code-block:: python

    # Apply any NetworkX function through the wrapper
    # Returns results as a dictionary mapping nodes to values
    centralities = network.monoplex_nx_wrapper("degree_centrality")
    print("Top 5 nodes by degree centrality:")
    for node, score in sorted(centralities.items(), key=lambda x: -x[1])[:5]:
        print(f"  {node}: {score:.4f}")

**Expected Output** (node centrality values):

.. code-block:: text

    Top 5 nodes by degree centrality:
      ('1', '1'): 0.5000
      ('2', '1'): 0.3333
      ('3', '1'): 0.2500
      ('6', '2'): 0.2500
      ('5', '2'): 0.1667

**Available NetworkX Functions:**

The wrapper supports any NetworkX function that takes a graph as input:

- ``"degree_centrality"`` - Fraction of nodes each node is connected to
- ``"betweenness_centrality"`` - How often a node lies on shortest paths
- ``"closeness_centrality"`` - How close a node is to all others
- ``"pagerank"`` - Importance based on link structure
- ``"clustering"`` - Local clustering coefficient
- ``"connected_components"`` - Find connected subgraphs

Direct NetworkX Access
~~~~~~~~~~~~~~~~~~~~~~

For more control, access the underlying NetworkX graph directly:

.. code-block:: python

    import networkx as nx
    
    # Get the underlying NetworkX graph
    G = network.core_network
    
    # Use any NetworkX function directly
    components = list(nx.connected_components(G))
    print(f"Number of connected components: {len(components)}")
    
    # Compute clustering coefficient
    clustering = nx.average_clustering(G)
    print(f"Average clustering: {clustering:.4f}")
    
    # Find shortest path between nodes
    if nx.has_path(G, ('1', '1'), ('6', '2')):
        path = nx.shortest_path(G, ('1', '1'), ('6', '2'))
        print(f"Shortest path: {' -> '.join(str(n) for n in path)}")

Practical Analysis Workflow
---------------------------

Here's a complete workflow for analyzing a multilayer network:

.. code-block:: python

    from py3plex.core import multinet
    import networkx as nx
    
    # 1. Load and inspect
    network = multinet.multi_layer_network().load_network(
        "../datasets/multiedgelist.txt", input_type="multiedgelist", directed=False)
    network.basic_stats()
    
    # 2. Extract and compare layers
    layers = network.get_layers()
    for layer_id, layer_graph in layers.items():
        density = nx.density(layer_graph)
        clustering = nx.average_clustering(layer_graph)
        print(f"Layer {layer_id}: density={density:.4f}, clustering={clustering:.4f}")
    
    # 3. Find important nodes across the whole network
    centrality = network.monoplex_nx_wrapper("pagerank")
    top_nodes = sorted(centrality.items(), key=lambda x: -x[1])[:10]
    print("\nTop 10 nodes by PageRank:")
    for node, score in top_nodes:
        print(f"  {node}: {score:.4f}")

For More Examples
-----------------

See detailed examples covering various analysis scenarios:

- ``example_multilayer_functionality.py`` - Comprehensive core operations tour
- ``example_networkx_wrapper.py`` - NetworkX integration patterns
- ``example_spreading.py`` - Network traversal and diffusion
- ``example_manipulation.py`` - Adding, removing, and modifying network elements
- ``example_subnetworks.py`` - Advanced subnetwork extraction
- ``example_comparison.py`` - Comparing network properties

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
