How to Load and Build Networks
===============================

**Goal:** Create multilayer networks from scratch or load them from files.

**Prerequisites:** Basic Python knowledge. For conceptual background, see :doc:`../concepts/py3plex_core_model`.

Creating Networks from Scratch
-------------------------------

Method 1: Add Edges Directly (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest approach—nodes are created automatically when you add edges.

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
    stats = network.basic_stats()

**Expected output:**

.. code-block:: text

    Number of nodes: 6
    Number of edges: 4
    Number of unique node IDs (across all layers): 4
    Nodes per layer:
      Layer 'friends': 3 nodes
      Layer 'colleagues': 3 nodes

Method 2: Add Nodes First
~~~~~~~~~~~~~~~~~~~~~~~~~~

For more control over node attributes:

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
        [('Bob', 'friends'), ('Carol', 'friends'), 1.0]
    ])

Method 3: Use Dictionary Format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For networks with edge attributes:

.. code-block:: python

    network = multinet.multi_layer_network()
    
    # Add edges with custom attributes
    network.add_edges([
        {
            'source': 'Alice',
            'source_type': 'friends',
            'target': 'Bob',
            'target_type': 'friends',
            'weight': 1.0,
            'timestamp': '2024-01-15',
            'interaction_type': 'message'
        },
        {
            'source': 'Bob',
            'source_type': 'friends',
            'target': 'Carol',
            'target_type': 'friends',
            'weight': 2.5,
            'timestamp': '2024-01-16'
        }
    ], input_type="dict")

Loading Networks from Files
----------------------------

Load Edge Lists
~~~~~~~~~~~~~~~

Most common format: one edge per line.

**File format (example.txt):**

.. code-block:: text

    Alice friends Bob friends 1.0
    Bob friends Carol friends 1.0
    Alice colleagues Bob colleagues 1.0

**Load it:**

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network()
    network.load_network(
        "example.txt",
        input_type="multiedgelist"
    )
    
    network.basic_stats()

Load from Pandas DataFrame
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Convert tabular data to networks:

.. code-block:: python

    import pandas as pd
    from py3plex.core import multinet
    
    # Your data
    df = pd.DataFrame({
        'source': ['Alice', 'Bob', 'Alice'],
        'layer': ['friends', 'friends', 'work'],
        'target': ['Bob', 'Carol', 'Carol'],
        'weight': [1.0, 1.0, 2.0]
    })
    
    # Convert to network
    network = multinet.multi_layer_network()
    
    for _, row in df.iterrows():
        network.add_edge(
            row['source'], row['layer'],
            row['target'], row['layer'],
            weight=row['weight']
        )

Load from JSON
~~~~~~~~~~~~~~

For complex networks with metadata:

.. code-block:: python

    import json
    from py3plex.core import multinet
    
    # Load JSON
    with open('network.json', 'r') as f:
        data = json.load(f)
    
    network = multinet.multi_layer_network()
    
    # Assuming JSON structure: {"edges": [...], "nodes": [...]}
    for edge in data['edges']:
        network.add_edge(
            edge['source'], edge['source_layer'],
            edge['target'], edge['target_layer'],
            **edge.get('attributes', {})
        )

Load from NetworkX
~~~~~~~~~~~~~~~~~~

Convert existing single-layer networks:

.. code-block:: python

    import networkx as nx
    from py3plex.core import multinet
    
    # Existing NetworkX graph
    G = nx.karate_club_graph()
    
    # Convert to multilayer (single layer)
    network = multinet.multi_layer_network()
    
    for u, v in G.edges():
        network.add_edge(u, 'layer1', v, 'layer1')

Loading with Inter-layer Edges
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To represent the same entity across layers:

.. code-block:: python

    network = multinet.multi_layer_network()
    
    # Intra-layer edges
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1.0],
        ['Alice', 'work', 'Carol', 'work', 1.0],
    ], input_type="list")
    
    # Inter-layer edges (same person across layers)
    network.add_edge('Alice', 'friends', 'Alice', 'work', type='interlayer')
    network.add_edge('Bob', 'friends', 'Bob', 'work', type='interlayer')

Common Patterns
---------------

Pattern 1: Social Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Multiple relationship types between same people:

.. code-block:: python

    network = multinet.multi_layer_network()
    network.add_edges([
        ['Alice', 'twitter', 'Bob', 'twitter', 1],
        ['Alice', 'linkedin', 'Bob', 'linkedin', 1],
        ['Bob', 'twitter', 'Carol', 'twitter', 1],
    ], input_type="list")

Pattern 2: Heterogeneous Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Different entity types:

.. code-block:: python

    # Author-Paper bipartite network
    network = multinet.multi_layer_network()
    network.add_edges([
        ['Alice', 'authors', 'Paper1', 'papers', 1],
        ['Bob', 'authors', 'Paper1', 'papers', 1],
        ['Alice', 'authors', 'Paper2', 'papers', 1],
    ], input_type="list")

Pattern 3: Temporal Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Time-stamped edges:

.. code-block:: python

    network = multinet.multi_layer_network()
    network.add_edges([
        {
            'source': 'Alice',
            'source_type': 'social',
            'target': 'Bob',
            'target_type': 'social',
            't': '2024-01-15T10:00:00'  # Point in time
        },
        {
            'source': 'Bob',
            'source_type': 'social',
            'target': 'Carol',
            'target_type': 'social',
            't_start': '2024-01-15',     # Time range
            't_end': '2024-01-20'
        }
    ], input_type="dict")

See :doc:`../reference/api_index` for temporal network details.

Verifying Your Network
-----------------------

After loading, verify the structure:

.. code-block:: python

    # Basic stats
    network.basic_stats()
    
    # Get specific information
    layers = network.get_layers()
    print(f"Layers: {layers}")
    
    num_nodes = len(list(network.get_nodes()))
    print(f"Total nodes: {num_nodes}")
    
    # Check a specific layer
    from py3plex.dsl import Q, L
    layer_nodes = Q.nodes().from_layers(L["friends"]).execute(network)
    print(f"Friends layer: {len(layer_nodes)} nodes")

**Expected output:**

.. code-block:: text

    Layers: ['friends', 'colleagues']
    Total nodes: 6
    Friends layer: 3 nodes

Next Steps
----------

* **Compute statistics:** :doc:`compute_statistics`
* **Visualize your network:** :doc:`visualize_networks`
* **Query the network:** :doc:`query_with_dsl`
* **Understand the data model:** :doc:`../concepts/py3plex_core_model`
* **API reference:** :doc:`../reference/api_index`
