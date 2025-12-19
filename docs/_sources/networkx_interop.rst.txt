NetworkX Interoperability Guide
================================

This guide covers converting between Py3plex and NetworkX formats, preserving
attributes, and integrating with external tools without losing layer context.

.. contents:: Table of Contents
   :local:
   :depth: 2

Why NetworkX Interoperability?
-------------------------------

Py3plex uses NetworkX as its underlying graph backend, which provides:

* **Compatibility** with hundreds of NetworkX algorithms
* **Easy export** to other tools (Gephi, Cytoscape, graph-tool)
* **Integration** with scientific Python ecosystem (NumPy, SciPy, pandas)
* **Standard formats** (GraphML, GEXF, GML, etc.)

Throughout this guide, nodes are addressed by their canonical Py3plex form
``(node_id, layer_name)``. When serialized to text formats, this tuple is
stringified using the configured label delimiter (default ``---``); adjust the
delimiter if you need file-level compatibility with other tools.

Export to NetworkX
-------------------

Basic Export
~~~~~~~~~~~~

Convert a Py3plex multilayer network to a NetworkX graph. The returned object is
the same ``MultiGraph`` or ``MultiDiGraph`` held inside Py3plex, so edits made
via NetworkX are reflected in Py3plex and vice versa. Use ``network.core_network.copy()``
if you want an isolated copy:

.. code-block:: python

    from py3plex.core import multinet
    
    # Load multilayer network
    network = multinet.multi_layer_network()
    network.load_network("data.csv", input_type="multiedgelist")

    # Export to NetworkX MultiGraph
    nx_graph = network.core_network  # Direct access to underlying MultiGraph/MultiDiGraph
    
    # OR use conversion method (returns the same object)
    nx_graph = network.to_nx_network()
    
    print(f"NetworkX graph: {nx_graph.number_of_nodes()} nodes, "
          f"{nx_graph.number_of_edges()} edges")

What Gets Exported
~~~~~~~~~~~~~~~~~~

When exporting to NetworkX, **all attributes are preserved**, and the graph type
is retained (undirected → ``MultiGraph``, directed → ``MultiDiGraph``). Layer
membership is always explicit on tuple nodes, so you do not need to parse
stringified labels to recover it:

**Node attributes (examples):**

* ``type`` - Layer name (identical to ``node[1]`` for tuple nodes)
* Custom attributes added via ``add_nodes()``

**Edge attributes (examples):**

* ``weight`` - Edge weight (default 1.0)
* ``type`` - Edge type (for multiplex coupling edges this is set to ``'coupling'``)
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

Layer information is encoded in node tuples, making layer access explicit without
parsing strings:

.. code-block:: python

    # Py3plex stores nodes as tuples: (node_id, layer_name)
    #
    # Example node: ('A', 'layer1')
    # - node_id: 'A'
    # - layer_name: 'layer1'
    
    # Iterate over nodes and extract layer info
    nx_graph = network.core_network
    
    for node in nx_graph.nodes():
        node_id, layer = node  # Unpack tuple directly
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

Most NetworkX algorithms that support ``MultiGraph``/``MultiDiGraph`` operate
directly on Py3plex networks. Algorithms that expect simple graphs should be
applied on a collapsed view, for example ``nx.Graph(network.core_network)`` to
drop parallel edges:

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
    
    # Betweenness centrality (use weight='weight' for weighted paths)
    between_cent = nx.betweenness_centrality(network.core_network, weight='weight')
    
    # Closeness centrality
    close_cent = nx.closeness_centrality(network.core_network, distance='weight')
    
    # PageRank (edge weights respected by default)
    pagerank = nx.pagerank(network.core_network, weight='weight')

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
    
    # Collapse to a simple, undirected view for connectivity checks
    G_simple = nx.Graph(network.core_network)
    
    if nx.is_connected(G_simple):
        print("Network is connected")
    else:
        print("Network has multiple components")
        
        # Find connected components
        components = list(nx.connected_components(G_simple))
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
    # Tuple nodes are stringified (e.g., ('A', 'layer1') -> 'A---layer1') in the output file
    nx.write_gexf(nx_graph, "network_for_gephi.gexf")
    
    print("[OK] Exported to network_for_gephi.gexf")
    print("  Open in Gephi: File → Open → network_for_gephi.gexf")

Export to Cytoscape
~~~~~~~~~~~~~~~~~~~

Cytoscape is a bioinformatics network analysis tool. Export to GraphML:

.. code-block:: python

    import networkx as nx
    
    # Export to GraphML (Cytoscape format)
    nx_graph = network.core_network
    # Node identifiers are stringified when written to GraphML
    nx.write_graphml(nx_graph, "network_for_cytoscape.graphml")
    
    print("[OK] Exported to network_for_cytoscape.graphml")
    print("  Open in Cytoscape: File → Import → Network from File")

Convert to igraph
~~~~~~~~~~~~~~~~~

igraph is a fast C-based network analysis library. When converting from a
``MultiGraph``/``MultiDiGraph``, parallel edges are collapsed in the simple
``Graph`` created below; attach weights if you need to preserve multiplicity:

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
    
    print(f"[OK] Converted to igraph: {ig_graph.vcount()} vertices, {ig_graph.ecount()} edges")
    
    # Use igraph algorithms
    communities = ig_graph.community_multilevel()
    print(f"  Detected {len(communities)} communities")

Py3plex → NetworkX → TensorLy
------------------------------

Complete Workflow
~~~~~~~~~~~~~~~~~

Convert a multilayer network to a dense tensor representation suitable for tensor
decomposition workflows. Axes are ordered as ``(source_node_id, layer, target_node_id)``,
so node identifiers are shared across layers and the layer axis carries context:

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
    
    # Fill tensor with intra-layer edges only; inter-layer edges are skipped here
    for (u_id, u_layer), (v_id, v_layer), data in nx_graph.edges(data=True):
        if u_layer == v_layer:  # Intra-layer edge
            i = node_to_idx[u_id]
            j = node_to_idx[v_id]
            k = layer_to_idx[u_layer]
            weight = data.get('weight', 1.0)
            
            # Accumulate in case multiple edges exist between the same pair
            tensor[i, k, j] += weight
            if not nx_graph.is_directed():
                tensor[j, k, i] += weight  # Mirror for undirected graphs
    
    print(f"Tensor shape: {tensor.shape}")
    print(f"Non-zero entries: {np.count_nonzero(tensor)}")
    
    # Step 5: Use TensorLy for decomposition
    try:
        import tensorly as tl
        from tensorly.decomposition import tucker, parafac
        
        # Tucker decomposition
        core, factors = tucker(tl.tensor(tensor), rank=[5, 2, 5])
        print(f"\n[OK] Tucker decomposition complete")
        print(f"  Core tensor shape: {core.shape}")
        print(f"  Factor matrices: {[f.shape for f in factors]}")
        
        # PARAFAC/CP decomposition
        factors_cp = parafac(tl.tensor(tensor), rank=5)
        print(f"\n[OK] PARAFAC decomposition complete")
        print(f"  Rank: 5")
        
    except ImportError:
        print("\n[X] TensorLy not installed")
        print("  Install: pip install tensorly")

Supra-Adjacency Matrix
~~~~~~~~~~~~~~~~~~~~~~~

Convert to supra-adjacency matrix for tensor analysis. The row/column ordering
matches ``network.get_nodes()``, so indices are aligned with tuple-based nodes:

.. code-block:: python

    import numpy as np
    from scipy.sparse import lil_matrix
    
    # Get supra-adjacency matrix (number of rows = node-layer pairs)
    supra_adj = network.get_supra_adjacency_matrix(sparse=True)
    
    print(f"Supra-adjacency matrix: {supra_adj.shape}")
    print(f"Sparsity: {1 - supra_adj.nnz / (supra_adj.shape[0]**2):.2%}")
    
    # Convert to dense (if small enough)
    if supra_adj.shape[0] < 1000:
        dense_supra = supra_adj.toarray()
        
        # Use for analysis
        eigenvalues = np.linalg.eigvals(dense_supra)
        print(f"Largest eigenvalue: {max(eigenvalues):.3f}")
    else:
        print("Matrix too large for safe dense conversion; keep sparse.")

Import from NetworkX
---------------------

Create Py3plex Network from NetworkX
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can initialize a Py3plex network from an existing NetworkX graph. Nodes
should already carry layer information (either as tuple ``(node, layer)`` or
stringified with the configured delimiter), and any existing edge attributes are
kept:

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
    
    print(f"[OK] Imported {network.core_network.number_of_nodes()} nodes")

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
    
    # Collapse multiedges if your metrics assume a simple graph
    G_simple = nx.Graph(G)
    
    # Compute various statistics
    print("=== Network Statistics ===")
    print(f"Nodes: {G_simple.number_of_nodes()}")
    print(f"Edges: {G_simple.number_of_edges()}")
    print(f"Density: {nx.density(G_simple):.4f}")
    
    # Degree statistics
    degrees = dict(G_simple.degree())
    print(f"Average degree: {sum(degrees.values()) / len(degrees):.2f}")
    print(f"Max degree: {max(degrees.values())}")
    
    # Clustering
    clustering = nx.clustering(G_simple)
    print(f"Average clustering: {sum(clustering.values()) / len(clustering):.4f}")
    
    # Connected components
    if not nx.is_directed(G_simple):
        components = list(nx.connected_components(G_simple))
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
    
    print("[OK] Exported to GEXF with community information")
    print("  Open in Gephi and color by 'community' attribute")

Next Steps
----------

- :doc:`basic_usage_analysis` - Network analysis methods
- :doc:`user_guide/community_detection` - Community detection algorithms
- :doc:`visualization_guide` - Visualization options
- :doc:`tutorials/csv_loading` - Load data from CSV

For more examples, see the `examples/ directory <https://github.com/SkBlaz/py3plex/tree/main/examples>`_ 
in the GitHub repository.
