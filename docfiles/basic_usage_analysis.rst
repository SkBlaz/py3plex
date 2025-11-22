Network Analysis
================

Core Operations
---------------

The ``multi_layer_network`` object provides methods for network analysis and manipulation.

Basic Iteration
~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network().load_network(
        "../datasets/multiedgelist.txt", input_type="multiedgelist", directed=False)
    
    # Iterate edges
    for edge in network.get_edges(data=True):
        print(edge)
    
    # Iterate nodes
    for node in network.get_nodes(data=True):
        print(node)

**Expected Output** (example edges and nodes):

.. code-block:: text

    ('A_layer1', 'B_layer1', {'weight': 1.0, 'source': 'A', 'target': 'B', 'layer': 'layer1'})
    ('B_layer1', 'C_layer1', {'weight': 1.0, 'source': 'B', 'target': 'C', 'layer': 'layer1'})
    ...
    ('A_layer1', {'type': 'layer1', 'name': 'A'})
    ('B_layer1', {'type': 'layer1', 'name': 'B'})
    ...

Subnetworks
~~~~~~~~~~~

.. code-block:: python

    # Extract by layer
    layer_subnet = network.subnetwork(['1'], subset_by="layers")
    
    # Extract by node names
    node_subnet = network.subnetwork(['1'], subset_by="node_names")
    
    # Extract by node-layer pairs
    specific_subnet = network.subnetwork(
        [('1','1'), ('2','1')], subset_by="node_layer_names")

NetworkX Integration
~~~~~~~~~~~~~~~~~~~~

py3plex networks are compatible with NetworkX:

.. code-block:: python

    # Use any NetworkX function
    centralities = network.monoplex_nx_wrapper("degree_centrality")
    print(centralities)

**Expected Output** (node centrality values):

.. code-block:: text

    {'A_layer1': 0.5, 'B_layer1': 1.0, 'C_layer1': 0.5, ...}

For More Examples
-----------------

See detailed examples:

- ``example_multilayer_functionality.py`` - Core operations
- ``example_networkx_wrapper.py`` - NetworkX integration
- ``example_spreading.py`` - Network traversal
- ``example_manipulation.py`` - Network manipulation

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
