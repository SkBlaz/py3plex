NetworkX Interoperability and Migration Guide
=============================================

This guide covers converting between Py3plex and NetworkX formats, preserving attributes,
integrating with external tools, and **migrating from NetworkX to py3plex**.

.. contents:: Table of Contents
   :local:
   :depth: 2

Why Migrate from NetworkX?
---------------------------

**NetworkX** is excellent for single-layer networks but lacks native support for:

* Multiple layers with different relationship types
* Inter-layer edges (coupling between layers)
* Multilayer-specific algorithms and metrics

**Py3plex** extends network analysis to multilayer structures while maintaining a familiar API.

Quick Comparison
~~~~~~~~~~~~~~~~

**NetworkX Single-Layer Graph:**

.. code-block:: python

    import networkx as nx
    
    G = nx.Graph()
    G.add_nodes_from(['Alice', 'Bob', 'Carol'])
    G.add_edges_from([
        ('Alice', 'Bob'),
        ('Bob', 'Carol'),
    ])

**Py3plex Equivalent (Single Layer):**

.. code-block:: python

    from py3plex import multi_layer_network
    
    network = multi_layer_network()
    network.add_nodes_from([
        ('Alice', 'layer1'),
        ('Bob', 'layer1'),
        ('Carol', 'layer1'),
    ])
    network.add_edges_from([
        ('Alice', 'Bob', 'layer1'),
        ('Bob', 'Carol', 'layer1'),
    ])

**Key Difference:** Py3plex requires explicit layer specification.

API Mapping Table
~~~~~~~~~~~~~~~~~

+-----------------------------------+-------------------------------------------+------------------------+
| NetworkX                          | Py3plex                                   | Notes                  |
+===================================+===========================================+========================+
| ``G = nx.Graph()``                | ``net = multi_layer_network()``           | Both undirected        |
+-----------------------------------+-------------------------------------------+------------------------+
| ``G = nx.DiGraph()``              | ``net = multi_layer_network(directed=T)`` | Directed               |
+-----------------------------------+-------------------------------------------+------------------------+
| ``G.add_node('A')``               | ``net.add_node('A', 'layer1')``           | Layer required         |
+-----------------------------------+-------------------------------------------+------------------------+
| ``G.add_edge('A', 'B')``          | ``net.add_edge('A', 'B', 'layer1')``      | Layer required         |
+-----------------------------------+-------------------------------------------+------------------------+
| ``G.nodes()``                     | ``net.get_nodes()``                       | Returns generator      |
+-----------------------------------+-------------------------------------------+------------------------+
| ``G.edges()``                     | ``net.get_edges()``                       | Returns generator      |
+-----------------------------------+-------------------------------------------+------------------------+
| ``G.number_of_nodes()``           | ``net.number_of_nodes()``                 | ✓ Same                 |
+-----------------------------------+-------------------------------------------+------------------------+
| ``G.number_of_edges()``           | ``net.number_of_edges()``                 | ✓ Same                 |
+-----------------------------------+-------------------------------------------+------------------------+

Conversion Functions
~~~~~~~~~~~~~~~~~~~~

**From NetworkX to Py3plex:**

.. code-block:: python

    import networkx as nx
    from py3plex import multi_layer_network
    
    def networkx_to_py3plex(G, layer_name="default"):
        """Convert a NetworkX graph to py3plex (single layer)."""
        network = multi_layer_network()
        
        # Add all nodes to the specified layer
        for node in G.nodes():
            network.add_node(node, layer_name)
        
        # Add all edges
        for u, v in G.edges():
            network.add_edge(u, v, layer_name)
        
        return network
    
    # Usage
    G = nx.karate_club_graph()
    network = networkx_to_py3plex(G, "social")

**From Py3plex to NetworkX:**

.. code-block:: python

    import networkx as nx
    
    def py3plex_to_networkx(network, layer=None):
        """
        Convert py3plex network to NetworkX.
        If layer is specified, extract only that layer.
        If layer is None, create a merged NetworkX graph.
        """
        G = nx.Graph()
        
        if layer:
            # Extract single layer
            for node in network.get_nodes():
                if node[1] == layer:
                    G.add_node(node[0])
            
            for edge in network.get_edges():
                if len(edge) >= 3 and edge[2] == layer:
                    G.add_edge(edge[0], edge[1])
        else:
            # Merge all layers (loses layer information)
            nodes_seen = set()
            for node in network.get_nodes():
                if node[0] not in nodes_seen:
                    G.add_node(node[0])
                    nodes_seen.add(node[0])
            
            edges_seen = set()
            for edge in network.get_edges():
                edge_tuple = (edge[0], edge[1])
                if edge_tuple not in edges_seen:
                    G.add_edge(edge[0], edge[1])
                    edges_seen.add(edge_tuple)
        
        return G
    
    # Usage
    G = py3plex_to_networkx(network, layer="social")  # Single layer
    G_all = py3plex_to_networkx(network)  # Merged

Why NetworkX Interoperability?
-------------------------------

Py3plex uses NetworkX as its underlying graph backend, which provides:

* **Compatibility** with hundreds of NetworkX algorithms
* **Easy export** to other tools (Gephi, Cytoscape, graph-tool)
* **Integration** with scientific Python ecosystem (NumPy, SciPy, pandas)
* **Standard formats** (GraphML, GEXF, GML, etc.)

Export to NetworkX
-------------------

Basic Export
~~~~~~~~~~~~

Convert Py3plex multilayer network to NetworkX graph:

.. code-block:: python

    from py3plex.core import multinet
    
    # Load multilayer network
    network = multinet.multi_layer_network()
    network.load_network("data.csv", input_type="multiedgelist")
    
    # Export to NetworkX MultiGraph
    nx_graph = network.core_network  # Direct access
    
    # OR use conversion method (equivalent)
    nx_graph = network.to_nx_network()
    
    print(f"NetworkX graph: {nx_graph.number_of_nodes()} nodes, "
          f"{nx_graph.number_of_edges()} edges")

What Gets Exported
~~~~~~~~~~~~~~~~~~

When exporting to NetworkX, **all attributes are preserved**:

**Node attributes:**

* ``type`` - Layer name
* Custom attributes added via ``add_nodes()``

**Edge attributes:**

* ``weight`` - Edge weight (default 1.0)
* ``type`` - Edge type (e.g., 'coupling' for inter-layer edges)
* Custom attributes added via ``add_edges()``

**Example:**

.. code-block:: python

    # Access NetworkX graph
    nx_graph = network.core_network
    
    # Inspect node attributes
    for node, attrs in list(nx_graph.nodes(data=True))[:3]:
        print(f"Node: {node}")
        print(f"  Attributes: {attrs}")
        print()
    
    # Inspect edge attributes
    for u, v, attrs in list(nx_graph.edges(data=True))[:3]:
        print(f"Edge: {u} -> {v}")
        print(f"  Attributes: {attrs}")
        print()

Attribute Preservation
----------------------

Layer Information
~~~~~~~~~~~~~~~~~

Layer information is encoded in node tuples:

.. code-block:: python

    # Py3plex stores nodes as tuples: (node_id, layer_name)
    
    # Example node: ('A', 'layer1')
    # - node_id: 'A'
    # - layer_name: 'layer1'
    
    # Iterate over nodes and extract layer info
    nx_graph = network.core_network
    
    for node in nx_graph.nodes():
        node_id, layer = node  # Unpack tuple
        node_type = nx_graph.nodes[node]['type']  # Should equal layer
        
        print(f"Node {node_id} in layer {layer} (type={node_type})")

Weight Preservation
~~~~~~~~~~~~~~~~~~~

Edge weights are preserved as edge attributes:

.. code-block:: python

    nx_graph = network.core_network
    
    # Get edge weights
    for u, v, data in nx_graph.edges(data=True):
        weight = data.get('weight', 1.0)  # Default to 1.0
        print(f"{u} -> {v}: weight={weight}")

Custom Attributes
~~~~~~~~~~~~~~~~~

Any custom attributes you add are preserved:

.. code-block:: python

    from py3plex.core import multinet
    
    # Create network
    network = multinet.multi_layer_network()
    
    # Add edges with custom attributes
    network.add_edges([
        ['A', 'layer1', 'B', 'layer1', 1.0, {'color': 'red', 'importance': 0.8}],
        ['B', 'layer1', 'C', 'layer1', 1.0, {'color': 'blue', 'importance': 0.6}],
    ], input_type="list")
    
    # Export to NetworkX
    nx_graph = network.core_network
    
    # Custom attributes are preserved
    for u, v, data in nx_graph.edges(data=True):
        print(f"{u} -> {v}:")
        print(f"  color: {data.get('color')}")
        print(f"  importance: {data.get('importance')}")

Using NetworkX Algorithms
--------------------------

All NetworkX algorithms work directly on Py3plex networks:

Shortest Paths
~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    from py3plex.core import multinet
    
    # Load network
    network = multinet.multi_layer_network()
    network.load_network("network.csv", input_type="multiedgelist")
    
    # Use NetworkX shortest path algorithm
    nx_graph = network.core_network
    
    try:
        # Find shortest path between two node-layer tuples
        source = ('A', 'layer1')
        target = ('C', 'layer2')
        
        path = nx.shortest_path(nx_graph, source=source, target=target)
        print(f"Shortest path: {' -> '.join(str(n) for n in path)}")
        
        # Path length
        length = nx.shortest_path_length(nx_graph, source=source, target=target)
        print(f"Path length: {length}")
        
    except nx.NetworkXNoPath:
        print("No path exists between these nodes")

Centrality Measures
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    
    # Degree centrality
    degree_cent = nx.degree_centrality(network.core_network)
    top_nodes = sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:5]
    
    print("Top 5 nodes by degree centrality:")
    for node, centrality in top_nodes:
        print(f"  {node}: {centrality:.3f}")
    
    # Betweenness centrality
    between_cent = nx.betweenness_centrality(network.core_network)
    
    # Closeness centrality
    close_cent = nx.closeness_centrality(network.core_network)
    
    # PageRank
    pagerank = nx.pagerank(network.core_network)

Community Detection
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    from networkx.algorithms import community
    
    # Greedy modularity communities
    communities = community.greedy_modularity_communities(network.core_network)
    
    print(f"Detected {len(communities)} communities")
    for i, comm in enumerate(communities):
        print(f"Community {i}: {len(comm)} nodes")

Connectivity
~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    
    # Check if network is connected
    if nx.is_connected(network.core_network.to_undirected()):
        print("Network is connected")
    else:
        print("Network has multiple components")
        
        # Find connected components
        components = list(nx.connected_components(network.core_network.to_undirected()))
        print(f"Number of components: {len(components)}")
        for i, comp in enumerate(components):
            print(f"  Component {i}: {len(comp)} nodes")

Integration with External Tools
--------------------------------

Export to Gephi
~~~~~~~~~~~~~~~

Gephi is a popular network visualization tool. Export Py3plex networks to GEXF format:

.. code-block:: python

    import networkx as nx
    
    # Export to GEXF (Gephi format)
    nx_graph = network.core_network
    nx.write_gexf(nx_graph, "network_for_gephi.gexf")
    
    print("✓ Exported to network_for_gephi.gexf")
    print("  Open in Gephi: File → Open → network_for_gephi.gexf")

Export to Cytoscape
~~~~~~~~~~~~~~~~~~~

Cytoscape is a bioinformatics network analysis tool. Export to GraphML:

.. code-block:: python

    import networkx as nx
    
    # Export to GraphML (Cytoscape format)
    nx_graph = network.core_network
    nx.write_graphml(nx_graph, "network_for_cytoscape.graphml")
    
    print("✓ Exported to network_for_cytoscape.graphml")
    print("  Open in Cytoscape: File → Import → Network from File")

Convert to igraph
~~~~~~~~~~~~~~~~~

igraph is a fast C-based network analysis library:

.. code-block:: python

    # Requires: pip install python-igraph
    import igraph as ig
    import networkx as nx
    
    # Convert NetworkX to igraph
    nx_graph = network.core_network
    
    # Method 1: Via GraphML
    nx.write_graphml(nx_graph, "temp.graphml")
    ig_graph = ig.Graph.Read_GraphML("temp.graphml")
    
    # Method 2: Via edge list (faster)
    edges = list(nx_graph.edges())
    nodes = list(nx_graph.nodes())
    
    ig_graph = ig.Graph()
    ig_graph.add_vertices(len(nodes))
    ig_graph.vs["name"] = [str(n) for n in nodes]
    
    # Map node names to indices
    node_to_idx = {n: i for i, n in enumerate(nodes)}
    ig_edges = [(node_to_idx[u], node_to_idx[v]) for u, v in edges]
    ig_graph.add_edges(ig_edges)
    
    print(f"✓ Converted to igraph: {ig_graph.vcount()} vertices, {ig_graph.ecount()} edges")
    
    # Use igraph algorithms
    communities = ig_graph.community_multilevel()
    print(f"  Detected {len(communities)} communities")

Py3plex → NetworkX → TensorLy
------------------------------

Complete Workflow
~~~~~~~~~~~~~~~~~

Convert multilayer network to tensor representation for tensor decomposition:

.. code-block:: python

    import numpy as np
    import networkx as nx
    from py3plex.core import multinet
    
    # Step 1: Load multilayer network
    network = multinet.multi_layer_network()
    network.load_network("network.csv", input_type="multiedgelist")
    
    # Step 2: Get NetworkX graph
    nx_graph = network.core_network
    
    # Step 3: Extract layer information
    layers = sorted(set(node[1] for node in nx_graph.nodes()))
    nodes = sorted(set(node[0] for node in nx_graph.nodes()))
    
    n_nodes = len(nodes)
    n_layers = len(layers)
    
    print(f"Network: {n_nodes} nodes, {n_layers} layers")
    
    # Step 4: Create 3D adjacency tensor (nodes × layers × nodes)
    tensor = np.zeros((n_nodes, n_layers, n_nodes))
    
    # Create mappings
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    layer_to_idx = {layer: i for i, layer in enumerate(layers)}
    
    # Fill tensor
    for (u_id, u_layer), (v_id, v_layer), data in nx_graph.edges(data=True):
        if u_layer == v_layer:  # Intra-layer edge
            i = node_to_idx[u_id]
            j = node_to_idx[v_id]
            k = layer_to_idx[u_layer]
            weight = data.get('weight', 1.0)
            
            tensor[i, k, j] = weight
            tensor[j, k, i] = weight  # Undirected
    
    print(f"Tensor shape: {tensor.shape}")
    print(f"Non-zero entries: {np.count_nonzero(tensor)}")
    
    # Step 5: Use TensorLy for decomposition
    try:
        import tensorly as tl
        from tensorly.decomposition import tucker, parafac
        
        # Tucker decomposition
        core, factors = tucker(tl.tensor(tensor), rank=[5, 2, 5])
        print(f"\n✓ Tucker decomposition complete")
        print(f"  Core tensor shape: {core.shape}")
        print(f"  Factor matrices: {[f.shape for f in factors]}")
        
        # PARAFAC/CP decomposition
        factors_cp = parafac(tl.tensor(tensor), rank=5)
        print(f"\n✓ PARAFAC decomposition complete")
        print(f"  Rank: 5")
        
    except ImportError:
        print("\n✗ TensorLy not installed")
        print("  Install: pip install tensorly")

Supra-Adjacency Matrix
~~~~~~~~~~~~~~~~~~~~~~~

Convert to supra-adjacency matrix for tensor analysis:

.. code-block:: python

    import numpy as np
    from scipy.sparse import lil_matrix
    
    # Get supra-adjacency matrix
    supra_adj = network.get_supra_adjacency_matrix(sparse=True)
    
    print(f"Supra-adjacency matrix: {supra_adj.shape}")
    print(f"Sparsity: {1 - supra_adj.nnz / (supra_adj.shape[0]**2):.2%}")
    
    # Convert to dense (if small enough)
    if supra_adj.shape[0] < 1000:
        dense_supra = supra_adj.toarray()
        
        # Use for analysis
        eigenvalues = np.linalg.eigvals(dense_supra)
        print(f"Largest eigenvalue: {max(eigenvalues):.3f}")

Import from NetworkX
---------------------

Create Py3plex Network from NetworkX
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    from py3plex.core import multinet
    
    # Create NetworkX graph
    G = nx.Graph()
    G.add_edges_from([
        (('A', 'layer1'), ('B', 'layer1'), {'weight': 1.0}),
        (('B', 'layer1'), ('C', 'layer1'), {'weight': 0.8}),
        (('A', 'layer2'), ('C', 'layer2'), {'weight': 0.6}),
    ])
    
    # Import to Py3plex
    network = multinet.multi_layer_network()
    network.load_network(G, input_type="nx")
    
    print(f"✓ Imported {network.core_network.number_of_nodes()} nodes")

Practical Examples
------------------

Example 1: Network Statistics Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    from py3plex.core import multinet
    
    # Load network
    network = multinet.multi_layer_network()
    network.load_network("network.csv", input_type="multiedgelist")
    
    # Get NetworkX graph
    G = network.core_network
    
    # Compute various statistics
    print("=== Network Statistics ===")
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")
    print(f"Density: {nx.density(G):.4f}")
    
    # Degree statistics
    degrees = dict(G.degree())
    print(f"Average degree: {sum(degrees.values()) / len(degrees):.2f}")
    print(f"Max degree: {max(degrees.values())}")
    
    # Clustering
    clustering = nx.clustering(G.to_undirected())
    print(f"Average clustering: {sum(clustering.values()) / len(clustering):.4f}")
    
    # Connected components
    if not nx.is_directed(G):
        components = list(nx.connected_components(G))
        print(f"Connected components: {len(components)}")

Example 2: Multilayer PageRank
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    
    # Compute PageRank on multilayer network
    G = network.core_network
    pagerank = nx.pagerank(G, weight='weight')
    
    # Group by layer
    layers = {}
    for (node_id, layer), score in pagerank.items():
        if layer not in layers:
            layers[layer] = []
        layers[layer].append((node_id, score))
    
    # Print top nodes per layer
    for layer, nodes in layers.items():
        top_nodes = sorted(nodes, key=lambda x: x[1], reverse=True)[:5]
        print(f"\nTop 5 nodes in {layer}:")
        for node_id, score in top_nodes:
            print(f"  {node_id}: {score:.4f}")

Example 3: Export for Gephi Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    from py3plex.core import multinet
    
    # Load and process network
    network = multinet.multi_layer_network()
    network.load_network("network.csv", input_type="multiedgelist")
    
    # Add community detection results
    from py3plex.algorithms.community_detection import community_louvain
    communities = community_louvain.best_partition(network.core_network)
    
    # Add community as node attribute
    for node, comm_id in communities.items():
        network.core_network.nodes[node]['community'] = comm_id
    
    # Export to GEXF with communities
    nx.write_gexf(network.core_network, "network_with_communities.gexf")
    
    print("✓ Exported to GEXF with community information")
    print("  Open in Gephi and color by 'community' attribute")

Next Steps
----------

- :doc:`basic_usage_analysis` - Network analysis methods
- :doc:`community_detection` - Community detection algorithms
- :doc:`visualization_guide` - Visualization options
- :doc:`tutorials/csv_loading` - Load data from CSV

For more examples, see the `examples/ directory <https://github.com/SkBlaz/py3plex/tree/main/examples>`_ 
in the GitHub repository.
