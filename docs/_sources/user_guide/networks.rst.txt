Working with Networks
=====================

This guide covers everything you need to know about creating, loading, and manipulating multilayer networks in py3plex.

Creating Networks from Scratch
-------------------------------

Method 1: Add Edges Directly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest way to create a network is to add edges directly. Nodes are created automatically.

.. code-block:: python

    from py3plex.core import multinet
    
    # Create empty network
    network = multinet.multi_layer_network()
    
    # Add edges in list format
    # Format: [source_node, source_layer, target_node, target_layer, weight]
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1.0],
        ['Bob', 'friends', 'Carol', 'friends', 1.0],
        ['Alice', 'colleagues', 'Bob', 'colleagues', 1.0],
        ['Bob', 'colleagues', 'Dave', 'colleagues', 1.0]
    ], input_type="list")
    
    # Verify
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

Method 2: Add Nodes and Edges Separately
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For more control, add nodes explicitly before adding edges:

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network()
    
    # Add nodes explicitly (as node-layer tuples)
    network.add_nodes([
        ('Alice', 'friends'),
        ('Bob', 'friends'),
        ('Carol', 'friends'),
        ('Alice', 'colleagues'),
        ('Bob', 'colleagues'),
        ('Dave', 'colleagues')
    ])
    
    # Add edges between existing nodes
    network.add_edges([
        [('Alice', 'friends'), ('Bob', 'friends'), 1.0],
        [('Bob', 'friends'), ('Carol', 'friends'), 1.0],
        [('Alice', 'colleagues'), ('Bob', 'colleagues'), 1.0],
        [('Bob', 'colleagues'), ('Dave', 'colleagues'), 1.0]
    ])
    
    network.basic_stats()

Method 3: Define Layers First
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can define layers explicitly before adding content:

.. code-block:: python

    network = multinet.multi_layer_network()
    
    # Define layers
    network.add_layer('friends')
    network.add_layer('colleagues')
    network.add_layer('family')
    
    # Check layers
    print("Layers:", network.get_layers())
    
    # Add edges (nodes created automatically)
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1.0],
        ['Alice', 'family', 'Carol', 'family', 1.0]
    ], input_type="list")

**Output:**

.. code-block:: text

    Layers: ['friends', 'colleagues', 'family']

Method 4: Build from NetworkX Graphs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start with existing NetworkX graphs for each layer:

.. code-block:: python

    import networkx as nx
    from py3plex.core import multinet
    
    # Create layer graphs
    friends = nx.Graph()
    friends.add_edges_from([('Alice', 'Bob'), ('Bob', 'Carol')])
    
    colleagues = nx.Graph()
    colleagues.add_edges_from([('Alice', 'Bob'), ('Bob', 'Dave')])
    
    # Combine into multilayer network
    network = multinet.multi_layer_network()
    
    # Add edges from each graph with layer label
    for u, v in friends.edges():
        network.add_edges([[u, 'friends', v, 'friends', 1.0]], input_type="list")
    
    for u, v in colleagues.edges():
        network.add_edges([[u, 'colleagues', v, 'colleagues', 1.0]], input_type="list")

Loading Networks from Files
----------------------------

py3plex supports multiple file formats for loading networks. See :doc:`io_and_formats` for complete I/O documentation.

From Simple Edge Lists
~~~~~~~~~~~~~~~~~~~~~~~

**Format:** Simple ``source target`` pairs (one per line)

**File example (data.edgelist):**

.. code-block:: text

    Alice Bob
    Bob Carol
    Carol Dave

**Code:**

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network().load_network(
        "data.edgelist",
        input_type="edgelist",
        directed=False
    )
    
    network.basic_stats()

**Output:**

.. code-block:: text

    Number of nodes: 4
    Number of edges: 3
    Number of unique nodes (as node-layer tuples): 4
    Number of unique node IDs (across all layers): 4
    Nodes per layer:
      Layer 'null': 4 nodes

**Note:** Simple edge lists create a single layer named ``'null'`` by default.

From Multilayer Edge Lists
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Format:** ``source target layer`` (space or tab-separated)

**File example (data.multiedgelist):**

.. code-block:: text

    Alice Bob friends
    Bob Carol friends
    Alice Bob colleagues
    Bob Dave colleagues

**Code:**

.. code-block:: python

    network = multinet.multi_layer_network().load_network(
        "data.multiedgelist",
        input_type="multiedgelist",
        directed=False
    )
    
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

From GraphML
~~~~~~~~~~~~

GraphML is an XML-based format that preserves node and edge attributes:

.. code-block:: python

    network = multinet.multi_layer_network().load_network(
        "data.graphml",
        input_type="graphml"
    )

From GML
~~~~~~~~

Graph Modeling Language is another standard format:

.. code-block:: python

    network = multinet.multi_layer_network().load_network(
        "data.gml",
        input_type="gml"
    )

From NetworkX Pickle
~~~~~~~~~~~~~~~~~~~~

NetworkX's native pickle format:

.. code-block:: python

    network = multinet.multi_layer_network().load_network(
        "data.gpickle",
        input_type="gpickle"
    )

From NetworkX Graphs
~~~~~~~~~~~~~~~~~~~~

Load directly from a NetworkX graph object:

.. code-block:: python

    import networkx as nx
    from py3plex.core import multinet
    
    # Create or load a NetworkX graph
    G = nx.karate_club_graph()
    
    # Convert to py3plex
    network = multinet.multi_layer_network()
    network.load_network_from_networkx(G)
    
    # Result is a single-layer network
    network.basic_stats()

Modern I/O with Arrow/Parquet
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For high-performance I/O, use the modern schema-based API. See :doc:`io_and_formats` for details.

.. code-block:: python

    from py3plex.io import read, write
    
    # Read (auto-detects format from extension)
    network = read('network.arrow')  # or .parquet, .json
    
    # Write
    write(network, 'output.arrow')

Network Operations
------------------

Querying Network Elements
~~~~~~~~~~~~~~~~~~~~~~~~~

**Get all nodes:**

.. code-block:: python

    # Without attributes
    nodes = network.get_nodes(data=False)
    print("Nodes:", list(nodes)[:5])
    
    # With attributes
    nodes_with_data = network.get_nodes(data=True)
    for node, attrs in list(nodes_with_data)[:3]:
        print(f"Node: {node}, Attributes: {attrs}")

**Get nodes in a specific layer:**

.. code-block:: python

    # Filter by layer
    friends_nodes = network.get_nodes(layer='friends')
    print("Friends layer nodes:", list(friends_nodes))

**Get all edges:**

.. code-block:: python

    # Without attributes
    edges = network.get_edges(data=False)
    print("Edges:", list(edges)[:5])
    
    # With attributes
    edges_with_data = network.get_edges(data=True)
    for u, v, attrs in list(edges_with_data)[:3]:
        print(f"Edge: {u} -> {v}, Attributes: {attrs}")

**Get neighbors:**

.. code-block:: python

    # Get neighbors of a node in a specific layer
    neighbors = list(network.get_neighbors('Alice', layer_id='friends'))
    print(f"Alice's friends: {neighbors}")

**Get layers:**

.. code-block:: python

    layers = network.get_layers()
    print(f"Layers: {layers}")
    print(f"Number of layers: {len(layers)}")

Extracting Subnetworks
~~~~~~~~~~~~~~~~~~~~~~~

**Extract a single layer:**

.. code-block:: python

    # Get all nodes and edges in one layer
    friends_subnet = network.subnetwork(['friends'], subset_by="layers")
    friends_subnet.basic_stats()

**Extract multiple layers:**

.. code-block:: python

    # Combine multiple layers
    social_subnet = network.subnetwork(['friends', 'family'], subset_by="layers")

**Extract specific nodes (all layers):**

.. code-block:: python

    # Get all appearances of specific nodes
    alice_bob_subnet = network.subnetwork(['Alice', 'Bob'], subset_by="node_names")
    alice_bob_subnet.basic_stats()

**Extract specific node-layer pairs:**

.. code-block:: python

    # Get specific node-layer combinations
    specific_subnet = network.subnetwork(
        [('Alice', 'friends'), ('Bob', 'friends')],
        subset_by="node_layer_names"
    )
    specific_subnet.basic_stats()

Iterating Over Network Elements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Iterate over nodes:**

.. code-block:: python

    # Simple iteration
    for node in network.get_nodes():
        print(node)  # Prints (node_id, layer_id) tuples
    
    # With attributes
    for node, attrs in network.get_nodes(data=True):
        print(f"{node}: {attrs}")

**Iterate over edges:**

.. code-block:: python

    # Simple iteration
    for u, v in network.get_edges():
        print(f"{u} -> {v}")
    
    # With attributes
    for u, v, attrs in network.get_edges(data=True):
        print(f"{u} -> {v}: weight={attrs.get('weight', 1.0)}")

**Iterate over layers:**

.. code-block:: python

    for layer_name in network.get_layers():
        layer_subnet = network.subnetwork([layer_name], subset_by="layers")
        num_nodes = len(list(layer_subnet.get_nodes()))
        num_edges = len(list(layer_subnet.get_edges()))
        print(f"Layer {layer_name}: {num_nodes} nodes, {num_edges} edges")

Modifying Networks
------------------

Adding Elements
~~~~~~~~~~~~~~~

**Add new nodes:**

.. code-block:: python

    # Add single node
    network.add_nodes([('Eve', 'friends')])
    
    # Add multiple nodes
    network.add_nodes([
        ('Eve', 'colleagues'),
        ('Frank', 'colleagues')
    ])

**Add new edges:**

.. code-block:: python

    # Add single edge
    network.add_edges([
        ['Alice', 'friends', 'Eve', 'friends', 1.0]
    ], input_type="list")
    
    # Add multiple edges
    network.add_edges([
        ['Eve', 'colleagues', 'Frank', 'colleagues', 1.0],
        ['Bob', 'colleagues', 'Frank', 'colleagues', 1.0]
    ], input_type="list")

**Add new layer:**

.. code-block:: python

    network.add_layer('family')

Removing Elements
~~~~~~~~~~~~~~~~~

To remove nodes or edges, work with the underlying NetworkX graph:

.. code-block:: python

    # Access NetworkX graph
    G = network.core_network
    
    # Remove node (removes all edges)
    G.remove_node(('Alice', 'friends'))
    
    # Remove edge
    G.remove_edge(('Bob', 'friends'), ('Carol', 'friends'))
    
    # Remove multiple nodes
    G.remove_nodes_from([('Alice', 'colleagues'), ('Bob', 'colleagues')])

Modifying Attributes
~~~~~~~~~~~~~~~~~~~~

**Node attributes:**

.. code-block:: python

    # Access NetworkX graph
    G = network.core_network
    
    # Set node attribute
    G.nodes[('Alice', 'friends')]['age'] = 30
    G.nodes[('Alice', 'friends')]['role'] = 'admin'
    
    # Get node attribute
    age = G.nodes[('Alice', 'friends')].get('age')
    print(f"Alice's age: {age}")

**Edge attributes:**

.. code-block:: python

    # Set edge attribute
    G[('Alice', 'friends')][('Bob', 'friends')]['weight'] = 0.8
    G[('Alice', 'friends')][('Bob', 'friends')]['type'] = 'close'
    
    # Get edge attribute
    weight = G[('Alice', 'friends')][('Bob', 'friends')].get('weight')
    print(f"Edge weight: {weight}")

Network Properties
------------------

Basic Statistics
~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get comprehensive stats
    network.basic_stats()
    
    # Output shows:
    # - Total nodes
    # - Total edges
    # - Unique node-layer pairs
    # - Unique node IDs
    # - Nodes per layer

**Manual counting:**

.. code-block:: python

    # Count elements manually
    num_nodes = len(list(network.get_nodes()))
    num_edges = len(list(network.get_edges()))
    num_layers = len(network.get_layers())
    
    print(f"Nodes: {num_nodes}, Edges: {num_edges}, Layers: {num_layers}")

Network Type
~~~~~~~~~~~~

.. code-block:: python

    # Check if directed
    G = network.core_network
    is_directed = G.is_directed()
    print(f"Directed: {is_directed}")
    
    # Check if multigraph
    is_multi = G.is_multigraph()
    print(f"Multigraph: {is_multi}")

Connectivity
~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    
    G = network.core_network
    
    # For undirected networks
    if not G.is_directed():
        is_connected = nx.is_connected(G)
        num_components = nx.number_connected_components(G)
        print(f"Connected: {is_connected}")
        print(f"Number of components: {num_components}")
    
    # For directed networks
    else:
        is_weakly_connected = nx.is_weakly_connected(G)
        is_strongly_connected = nx.is_strongly_connected(G)
        print(f"Weakly connected: {is_weakly_connected}")
        print(f"Strongly connected: {is_strongly_connected}")

Matrix Representations
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get supra-adjacency matrix
    supra_adj = network.get_supra_adjacency_matrix(sparse=True)
    print(f"Supra-adjacency shape: {supra_adj.shape}")
    
    # For small networks, get dense version
    if num_nodes < 1000:
        supra_adj_dense = network.get_supra_adjacency_matrix(sparse=False)

See :doc:`../concepts/py3plex_core_model` for details on supra-adjacency matrices.

NetworkX Integration
--------------------

Direct Access
~~~~~~~~~~~~~

The ``core_network`` attribute gives you direct access to the NetworkX graph:

.. code-block:: python

    import networkx as nx
    
    # Get NetworkX graph
    G = network.core_network
    
    # Use any NetworkX function
    degree = dict(G.degree())
    betweenness = nx.betweenness_centrality(G)
    clustering = nx.clustering(G)
    
    print(f"Average clustering: {nx.average_clustering(G):.3f}")

NetworkX Wrappers
~~~~~~~~~~~~~~~~~

py3plex provides convenience wrappers for common NetworkX functions:

.. code-block:: python

    # Extract a layer first
    friends_layer = network.subnetwork(['friends'], subset_by="layers")
    
    # Apply NetworkX algorithms via wrapper
    degree_centrality = friends_layer.monoplex_nx_wrapper("degree_centrality")
    betweenness = friends_layer.monoplex_nx_wrapper("betweenness_centrality")
    pagerank = friends_layer.monoplex_nx_wrapper("pagerank")
    
    # Results are dictionaries
    top_degree = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:5]
    print("Top 5 by degree:", top_degree)

Converting to NetworkX
~~~~~~~~~~~~~~~~~~~~~~~

Since py3plex networks ARE NetworkX graphs, conversion is trivial:

.. code-block:: python

    # Export to standard NetworkX formats
    import networkx as nx
    
    G = network.core_network
    
    # Save as GraphML
    nx.write_graphml(G, "output.graphml")
    
    # Save as GML
    nx.write_gml(G, "output.gml")
    
    # Save as pickle
    nx.write_gpickle(G, "output.gpickle")

See :doc:`io_and_formats` for more export options.

Best Practices
--------------

File Organization
~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Use absolute paths or path relative to script
    import os
    
    # Get directory of current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    network_path = os.path.join(data_dir, "network.edgelist")
    
    # Load
    network = multinet.multi_layer_network().load_network(
        network_path,
        input_type="edgelist"
    )

Always Verify After Loading
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Load network
    network = multinet.multi_layer_network().load_network(...)
    
    # ALWAYS check stats
    network.basic_stats()
    
    # Verify it matches expectations
    assert len(network.get_layers()) == 3, "Expected 3 layers"
    assert len(list(network.get_nodes())) > 0, "Network is empty!"

Use Appropriate Data Structures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # For large networks, use sparse matrices
    supra_adj = network.get_supra_adjacency_matrix(sparse=True)  # Good
    
    # Avoid dense matrices for large networks
    # supra_adj = network.get_supra_adjacency_matrix(sparse=False)  # Bad for n > 1000

Common Patterns
---------------

Pattern 1: Load, Analyze, Visualize
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.visualization.multilayer import draw_multilayer_default
    
    # Load
    network = multinet.multi_layer_network().load_network(
        "data.multiedgelist", input_type="multiedgelist"
    )
    
    # Analyze
    network.basic_stats()
    
    # Visualize
    draw_multilayer_default([network], display=True)

Pattern 2: Create from Multiple Sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Combine data from multiple files
    network = multinet.multi_layer_network()
    
    # Load friends from file
    import pandas as pd
    friends_df = pd.read_csv("friends.csv")
    for _, row in friends_df.iterrows():
        network.add_edges([[row['source'], 'friends', row['target'], 'friends', 1]], 
                         input_type="list")
    
    # Load colleagues from database (pseudocode)
    # colleagues = query_database("SELECT * FROM colleagues")
    # for source, target in colleagues:
    #     network.add_edges([[source, 'colleagues', target, 'colleagues', 1]], 
    #                      input_type="list")

Pattern 3: Layer-by-Layer Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Analyze each layer separately
    for layer_name in network.get_layers():
        print(f"\n=== Layer: {layer_name} ===")
        
        # Extract layer
        layer_subnet = network.subnetwork([layer_name], subset_by="layers")
        
        # Compute metrics
        layer_subnet.basic_stats()
        
        # Optional: visualize
        # draw_multilayer_default([layer_subnet], display=True)

Next Steps
----------

* :doc:`statistics` - Computing network metrics
* :doc:`community_detection` - Finding communities
* :doc:`io_and_formats` - Complete I/O documentation
* :doc:`visualization` - Visualization techniques
* :doc:`../concepts/py3plex_core_model` - Understanding the internal representation

**Related Examples:**

* ``example_multilayer_functionality.py`` - Core operations
* ``example_IO.py`` - Loading and saving
* ``example_manipulation.py`` - Network manipulation
* ``example_networkx_wrapper.py`` - NetworkX integration

Repository: https://github.com/SkBlaz/py3plex/tree/master/examples
