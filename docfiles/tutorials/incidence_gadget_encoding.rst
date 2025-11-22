Incidence Gadget Encoding Tutorial
===================================

This tutorial demonstrates how to transform multiplex networks into homogeneous hypergraphs using incidence gadget encoding with prime-based layer signatures in py3plex.

Overview
--------

Incidence gadget encoding provides a lossless transformation of multiplex networks into standard graph representations. This is useful for:

* Converting multiplex networks to formats compatible with classical graph algorithms
* Graph isomorphism testing with layer-aware structure preservation
* Network compression and serialization
* Cross-tool interoperability (exporting to tools without native multiplex support)

The encoding uses **prime numbers** to uniquely identify layers through cycle structures attached to edge-nodes.

What is Incidence Gadget Encoding?
-----------------------------------

Multiplex Networks
~~~~~~~~~~~~~~~~~~

A **multiplex network** contains nodes that appear in multiple layers with different types of connections.

Example - Social Network:

* **Layers:** friendship, colleague, family
* **Nodes:** People appearing in multiple layers
* **Edges:** Different relationships between same people in different layers

Incidence Gadget Transformation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The transformation creates:

* **Vertex-nodes** (v_*): One for each unique node in the multiplex
* **Edge-nodes** (e_*): One for each edge, connected to its endpoint vertex-nodes
* **Signature cycles** (C_p): Prime-length cycles attached to edge-nodes to encode layers

Layer Encoding with Primes
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each layer is assigned a unique prime number:

* Layer 1 → prime 2 → cycle of length 2
* Layer 2 → prime 3 → cycle of length 3
* Layer 3 → prime 5 → cycle of length 5
* Layer 4 → prime 7 → cycle of length 7
* ...

The prime cycle length uniquely identifies which layer each edge belongs to.

Basic Usage
-----------

Encoding a Multiplex Network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    
    # Create a multiplex network
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes to different layers
    network.add_nodes([
        {'source': 'Alice', 'type': 'friendship'},
        {'source': 'Bob', 'type': 'friendship'},
        {'source': 'Alice', 'type': 'colleague'},
        {'source': 'Bob', 'type': 'colleague'}
    ], input_type='dict')
    
    # Add edges in each layer
    network.add_edges([
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'friendship', 'target_type': 'friendship'},
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'colleague', 'target_type': 'colleague'}
    ], input_type='dict')
    
    # Encode to homogeneous hypergraph
    H, node_mapping, edge_info = network.to_homogeneous_hypergraph()
    
    print(f"Encoded graph has {len(H.nodes())} nodes and {len(H.edges())} edges")
    print(f"Node mapping: {node_mapping}")
    print(f"Edge information: {edge_info}")

Decoding Back to Multiplex
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Decode the homogeneous hypergraph back to multiplex structure
    recovered = network.from_homogeneous_hypergraph(H)
    
    # recovered is a dict: {layer_name: [(u, v), ...]}
    for layer, edges in recovered.items():
        print(f"Layer {layer}: {edges}")

Understanding the Output
------------------------

Node Mapping
~~~~~~~~~~~~

The ``node_mapping`` dictionary maps original node IDs to vertex-nodes in H:

.. code-block:: python

    node_mapping = {
        'Alice': 'v_Alice',
        'Bob': 'v_Bob',
        'Charlie': 'v_Charlie'
    }

Edge Information
~~~~~~~~~~~~~~~~

The ``edge_info`` dictionary maps edge-nodes to their layer and endpoints:

.. code-block:: python

    edge_info = {
        'e_0': ('friendship', ('Alice', 'Bob')),
        'e_1': ('colleague', ('Alice', 'Bob')),
        'e_2': ('family', ('Alice', 'Charlie'))
    }

Homogeneous Graph Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The encoded graph H contains three types of nodes:

* **Vertex-nodes** (v_*): Original nodes from the multiplex
* **Edge-nodes** (e_*): Represent edges in the multiplex
* **Signature nodes** (*_s*): Form prime-length cycles for layer encoding

Complete Example
----------------

Social Network Encoding
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    import networkx as nx
    
    # Create a multiplex social network
    network = multinet.multi_layer_network(directed=False)
    
    # Define people and relationships
    people = ['Alice', 'Bob', 'Charlie', 'Diana']
    
    # Friendship layer
    network.add_nodes([
        {'source': p, 'type': 'friendship'} for p in people
    ], input_type='dict')
    network.add_edges([
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'friendship', 'target_type': 'friendship'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'friendship', 'target_type': 'friendship'}
    ], input_type='dict')
    
    # Colleague layer
    network.add_nodes([
        {'source': p, 'type': 'colleague'} for p in ['Alice', 'Bob', 'Diana']
    ], input_type='dict')
    network.add_edges([
        {'source': 'Alice', 'target': 'Diana', 'source_type': 'colleague', 'target_type': 'colleague'}
    ], input_type='dict')
    
    # Encode to homogeneous hypergraph
    H, node_mapping, edge_info = network.to_homogeneous_hypergraph()
    
    # Analyze the encoded graph
    print(f"Original multiplex: {len(list(network.get_nodes()))} nodes, {len(list(network.get_edges()))} edges")
    print(f"Encoded graph H: {len(H.nodes())} nodes, {len(H.edges())} edges")
    print(f"Connected components: {nx.number_connected_components(H)}")
    
    # Decode back
    recovered = network.from_homogeneous_hypergraph(H)
    print(f"\nRecovered {len(recovered)} layers")
    for layer, edges in recovered.items():
        print(f"  {layer}: {len(edges)} edges")

Analyzing Cycle Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from sympy import primerange
    
    # The first few primes used for encoding
    primes = list(primerange(2, 20))
    print(f"Layer encoding primes: {primes[:5]}")
    # Output: [2, 3, 5, 7, 11]
    
    # Find cycles in the encoded graph
    all_cycles = nx.cycle_basis(H)
    print(f"Number of cycles: {len(all_cycles)}")
    print(f"Cycle lengths: {sorted([len(c) for c in all_cycles])}")
    
    # Each edge-node has a cycle through it of prime length
    for edge_node, (layer, endpoints) in edge_info.items():
        cycles_with_edge = [c for c in all_cycles if edge_node in c]
        if cycles_with_edge:
            cycle_len = len(cycles_with_edge[0])
            print(f"{edge_node} (layer {layer}): cycle length = {cycle_len}")

Advanced Usage
--------------

Working with Large Networks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For networks with many layers and edges:

.. code-block:: python

    # Create a larger multiplex network
    network = multinet.multi_layer_network(directed=False)
    
    # Multiple layers
    for layer in ['Layer1', 'Layer2', 'Layer3']:
        # Add nodes
        network.add_nodes([
            {'source': str(i), 'type': layer} for i in range(10)
        ], input_type='dict')
        
        # Create ring topology
        for i in range(10):
            network.add_edges([
                {'source': str(i), 'target': str((i+1) % 10), 
                 'source_type': layer, 'target_type': layer}
            ], input_type='dict')
    
    # Encode
    H, node_mapping, edge_info = network.to_homogeneous_hypergraph()
    
    # Analyze node types in encoded graph
    vertex_nodes = [n for n in H.nodes() if str(n).startswith('v_')]
    edge_nodes = [n for n in H.nodes() if str(n).startswith('e_')]
    signature_nodes = [n for n in H.nodes() 
                      if not str(n).startswith('v_') and not str(n).startswith('e_')]
    
    print(f"Vertex-nodes: {len(vertex_nodes)}")
    print(f"Edge-nodes: {len(edge_nodes)}")
    print(f"Signature-nodes: {len(signature_nodes)}")

Exporting Encoded Graphs
~~~~~~~~~~~~~~~~~~~~~~~~~

The encoded graph H is a standard NetworkX Graph and can be exported:

.. code-block:: python

    import networkx as nx
    
    # Export to various formats
    nx.write_graphml(H, "encoded_network.graphml")
    nx.write_gexf(H, "encoded_network.gexf")
    nx.write_edgelist(H, "encoded_network.edgelist")
    
    # Save node mapping and edge info separately
    import json
    
    with open("node_mapping.json", "w") as f:
        json.dump(node_mapping, f)
    
    with open("edge_info.json", "w") as f:
        # Convert tuples to lists for JSON serialization
        edge_info_serializable = {
            k: [v[0], list(v[1])] for k, v in edge_info.items()
        }
        json.dump(edge_info_serializable, f)

Technical Details
-----------------

Complexity
~~~~~~~~~~

* **Encoding time**: O(E × p_max) where E is number of edges, p_max is largest prime
* **Decoding time**: O(V + E + C) where V is nodes, E is edges, C is cycle detection cost
* **Space**: O(E × p_max) due to signature cycles

Limitations
~~~~~~~~~~~

* Maximum 305 layers (number of primes less than 2000)
* Cycle detection cost increases with number of layers
* Output graph size grows linearly with edge count and layer diversity
* Edge attributes are not preserved (only topological structure)

Mathematical Foundation
~~~~~~~~~~~~~~~~~~~~~~~

The encoding is based on:

* **Incidence representation**: Edges become nodes (edge-nodes)
* **Prime signatures**: Unique prime p for each layer α
* **Cycle gadgets**: Cycle C_p of length p attached to each edge in layer α
* **Isomorphism preservation**: Graph structure uniquely identifies layer membership

References
~~~~~~~~~~

* Based on incidence gadget constructions from graph theory
* Prime-based encoding ensures unique layer identification through cycle length
* Related to graph product operations and hypergraph representations

See Also
--------

* :doc:`./network_decomposition` - Alternative network transformation techniques
* :doc:`./multilayer_centrality` - Centrality measures for multiplex networks
* :doc:`./community_detection` - Community detection in multilayer networks

Example Scripts
---------------

See ``examples/advanced/example_incidence_gadget_encoding.py`` for complete demonstrations:

* Basic encoding and decoding workflow
* Social network multiplex example  
* Cycle structure analysis
* Network properties comparison

All examples are runnable and include detailed output explanations.
