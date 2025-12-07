How to Export and Serialize Networks
=====================================

**Goal:** Save multilayer networks to files and load them back.

**Prerequisites:** A network to export (see :doc:`load_and_build_networks`).

Quick Save and Load
-------------------

Using Pickle (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    import pickle
    
    # Create or load network
    network = multinet.multi_layer_network()
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1.0],
        ['Bob', 'work', 'Carol', 'work', 1.0],
    ], input_type="list")
    
    # Save to file
    with open('network.pkl', 'wb') as f:
        pickle.dump(network, f)
    
    # Load from file
    with open('network.pkl', 'rb') as f:
        loaded_network = pickle.load(f)
    
    loaded_network.basic_stats()

Export as Edge List
-------------------

Simple Text Format
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Export edges to text file
    with open('edges.txt', 'w') as f:
        for edge in network.get_edges():
            source, target = edge
            source_node, source_layer = source
            target_node, target_layer = target
            
            # Get edge attributes
            attrs = network.get_edge_data(source, target)
            weight = attrs.get('weight', 1.0)
            
            f.write(f"{source_node} {source_layer} {target_node} {target_layer} {weight}\n")

CSV Format
~~~~~~~~~~

.. code-block:: python

    import pandas as pd
    
    # Convert to DataFrame
    edges_data = []
    for edge in network.get_edges():
        source, target = edge
        source_node, source_layer = source
        target_node, target_layer = target
        
        attrs = network.get_edge_data(source, target)
        
        edges_data.append({
            'source': source_node,
            'source_layer': source_layer,
            'target': target_node,
            'target_layer': target_layer,
            'weight': attrs.get('weight', 1.0)
        })
    
    df = pd.DataFrame(edges_data)
    df.to_csv('network_edges.csv', index=False)

Export as JSON
--------------

Full Network Structure
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import json
    
    # Build JSON structure
    network_data = {
        'nodes': [],
        'edges': [],
        'layers': list(network.get_layers())
    }
    
    # Add nodes
    for node, layer in network.get_nodes():
        node_attrs = network.get_node_attributes(node, layer)
        network_data['nodes'].append({
            'id': node,
            'layer': layer,
            'attributes': node_attrs
        })
    
    # Add edges
    for edge in network.get_edges():
        source, target = edge
        source_node, source_layer = source
        target_node, target_layer = target
        
        attrs = network.get_edge_data(source, target)
        
        network_data['edges'].append({
            'source': source_node,
            'source_layer': source_layer,
            'target': target_node,
            'target_layer': target_layer,
            'attributes': attrs
        })
    
    # Save
    with open('network.json', 'w') as f:
        json.dump(network_data, f, indent=2)

Load from JSON
~~~~~~~~~~~~~~

.. code-block:: python

    import json
    from py3plex.core import multinet
    
    # Load JSON
    with open('network.json', 'r') as f:
        data = json.load(f)
    
    # Reconstruct network
    network = multinet.multi_layer_network()
    
    # Add edges (nodes created automatically)
    for edge in data['edges']:
        network.add_edge(
            edge['source'], edge['source_layer'],
            edge['target'], edge['target_layer'],
            **edge['attributes']
        )

Export to NetworkX
------------------

Convert to Single-Layer NetworkX Graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    
    # Flatten to single layer
    G = nx.Graph()
    
    for edge in network.get_edges():
        source, target = edge
        source_node, source_layer = source
        target_node, target_layer = target
        
        # Add nodes with layer info
        G.add_node(source_node, layer=source_layer)
        G.add_node(target_node, layer=target_layer)
        
        # Add edge
        attrs = network.get_edge_data(source, target)
        G.add_edge(source_node, target_node, **attrs)
    
    # Save as GraphML
    nx.write_graphml(G, 'network.graphml')

Export Specific Layer
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Extract single layer
    layer = 'friends'
    subgraph = Q.edges().from_layers(L[layer]).execute(network)
    
    # Convert to NetworkX
    G = nx.Graph()
    for edge in subgraph.get_edges():
        source, target = edge
        G.add_edge(source[0], target[0])  # Just node IDs
    
    # Save
    nx.write_edgelist(G, f'layer_{layer}.edgelist')

High-Performance: Apache Arrow/Parquet
---------------------------------------

For Large Networks
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import pyarrow as pa
    import pyarrow.parquet as pq
    
    # Convert edges to table
    edges_data = {
        'source': [],
        'source_layer': [],
        'target': [],
        'target_layer': [],
        'weight': []
    }
    
    for edge in network.get_edges():
        source, target = edge
        source_node, source_layer = source
        target_node, target_layer = target
        
        attrs = network.get_edge_data(source, target)
        
        edges_data['source'].append(source_node)
        edges_data['source_layer'].append(source_layer)
        edges_data['target'].append(target_node)
        edges_data['target_layer'].append(target_layer)
        edges_data['weight'].append(attrs.get('weight', 1.0))
    
    # Create Arrow table
    table = pa.table(edges_data)
    
    # Save as Parquet
    pq.write_table(table, 'network.parquet')

Load from Parquet
~~~~~~~~~~~~~~~~~

.. code-block:: python

    import pyarrow.parquet as pq
    from py3plex.core import multinet
    
    # Load table
    table = pq.read_table('network.parquet')
    df = table.to_pandas()
    
    # Reconstruct network
    network = multinet.multi_layer_network()
    
    for _, row in df.iterrows():
        network.add_edge(
            row['source'], row['source_layer'],
            row['target'], row['target_layer'],
            weight=row['weight']
        )

Export Statistics and Results
------------------------------

Save Analysis Results
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.dsl import Q
    
    # Compute statistics
    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )
    
    # Save to CSV
    df = result.to_pandas()
    df.to_csv('node_statistics.csv', index=False)

Save Communities
~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.community_detection import louvain_communities
    import pandas as pd
    
    # Detect communities
    communities = louvain_communities(network)
    
    # Convert to DataFrame
    data = []
    for (node, layer), comm_id in communities.items():
        data.append({
            'node': node,
            'layer': layer,
            'community': comm_id
        })
    
    df = pd.DataFrame(data)
    df.to_csv('communities.csv', index=False)

Batch Export
------------

Export Multiple Formats
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import os
    
    # Create output directory
    os.makedirs('export', exist_ok=True)
    
    # Export in multiple formats
    formats = {
        'pickle': lambda: pickle.dump(network, open('export/network.pkl', 'wb')),
        'json': lambda: json.dump(network_data, open('export/network.json', 'w')),
        'csv': lambda: df.to_csv('export/edges.csv', index=False)
    }
    
    for fmt, export_func in formats.items():
        try:
            export_func()
            print(f"Exported to {fmt}")
        except Exception as e:
            print(f"Failed to export {fmt}: {e}")

Next Steps
----------

* **Load data:** :doc:`load_and_build_networks`
* **Visualize networks:** :doc:`visualize_networks`
* **API reference:** :doc:`../reference/api_index`
