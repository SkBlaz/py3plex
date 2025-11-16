Network Analysis
################

Core Operations
***************

The ``multi_layer_network`` object provides methods for network analysis and manipulation.

Basic Iteration
===============

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
===========

.. code-block:: python

    # Extract by layer
    layer_subnet = network.subnetwork(['1'], subset_by="layers")
    
    # Extract by node names
    node_subnet = network.subnetwork(['1'], subset_by="node_names")
    
    # Extract by node-layer pairs
    specific_subnet = network.subnetwork(
        [('1','1'), ('2','1')], subset_by="node_layer_names")

NetworkX Integration
====================

py3plex networks are compatible with NetworkX:

.. code-block:: python

    # Use any NetworkX function
    centralities = network.monoplex_nx_wrapper("degree_centrality")
    print(centralities)

**Expected Output** (node centrality values):

.. code-block:: text

    {'A_layer1': 0.5, 'B_layer1': 1.0, 'C_layer1': 0.5, ...}

Network Fingerprinting
======================

Generate a comprehensive statistical characterization of your multilayer network:

.. code-block:: python

    # Get comprehensive network statistics as a DataFrame
    fingerprint = network.get_fingerprint()
    print(fingerprint)
    
    # For large networks, disable detailed layer statistics for speed
    fingerprint = network.get_fingerprint(include_layer_stats=False)
    
    # Export fingerprint to CSV
    fingerprint.to_csv('network_fingerprint.csv', index=False)

**Expected Output** (example fingerprint):

.. code-block:: text

                      statistic     value                          description
       total_node_layer_pairs         6       Total unique (node, layer) tuples
                 unique_nodes         3       Unique node IDs across all layers
                  total_edges         8              Total edges in the network
                   num_layers         2                        Number of layers
                  is_directed     False         Whether the network is directed
              overall_density  0.533333  Network density (edges/possible_edges)
            intra_layer_edges         5                     Edges within layers
            inter_layer_edges         3                    Edges between layers
      entropy_of_multiplexity  0.970951   Diversity of node layer participation
                   avg_degree  2.666667                     Average node degree
    ...

The fingerprint includes:

- **Basic metrics**: nodes, edges, layers, density, directedness
- **Layer statistics**: per-layer density, node counts, edge counts
- **Inter-layer metrics**: coupling strength, edge overlap
- **Network properties**: entropy, clustering, connectivity, activity
- **Centrality measures**: degree, betweenness (via sampling)

Use cases:

- **Network comparison**: Compare networks using their fingerprints
- **Feature extraction**: Use as input features for machine learning
- **Quick diagnostics**: Get a rapid overview of network structure
- **Documentation**: Generate comprehensive network reports
- **Classification**: Identify network types based on statistical patterns

For More Examples
*****************

See detailed examples:

- ``example_multilayer_functionality.py`` - Core operations
- ``example_networkx_wrapper.py`` - NetworkX integration
- ``example_spreading.py`` - Network traversal
- ``example_manipulation.py`` - Network manipulation

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
