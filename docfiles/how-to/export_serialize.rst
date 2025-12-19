How to Export and Serialize Networks
=====================================

**Goal:** Save multilayer networks to files and load them back—quick persistence,
interoperable edge lists, and analysis-ready formats.

**Prerequisites:** A network to export (see :doc:`load_and_build_networks`). All
examples assume an in-memory ``network`` instance.

Quick Save and Load
-------------------

Using Pickle (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pickle is the quickest way to persist a network within Python environments when
you do not need cross-language compatibility.

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

.. note::
   Only unpickle files from trusted sources, and prefer the same Python + py3plex
   versions for best compatibility. Use a text format (CSV/JSON) if you need
   portability.

Export as Edge List
-------------------

Use plain text or CSV when you want human-readable exports or interoperability
with tools outside Python.

Simple Text Format
~~~~~~~~~~~~~~~~~~

Write a plain text edge list with node IDs, layers, and weights. ``get_edges``
returns edges as ``((node, layer), (node, layer))`` tuples. Each line below
follows ``source source_layer target target_layer weight``.

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

Create a CSV edge list with explicit columns for nodes, layers, and weights.
CSV is easier to load in spreadsheets and dataframes than the plain text format.

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

Capture nodes, layers, edge endpoints, and their attributes in a single JSON
document for easy round-tripping. JSON keeps attribute dictionaries intact and
readable.

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

Recreate a multilayer network from the exported JSON representation.

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
    
    network.basic_stats()

Export to NetworkX
------------------

Convert to Single-Layer NetworkX Graph
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Flatten multilayer data into a single NetworkX graph, keeping the layer as a
node attribute. This drops parallel edges between layers and merges nodes with
the same ID across layers.

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

Persist just one layer to a simpler graph file.

.. code-block:: python

    import networkx as nx
    from py3plex.dsl import Q, L
    
    # Extract single layer
    layer = 'friends'
    subgraph = Q.edges().from_layers(L[layer]).execute(network)
    
    # Convert to NetworkX
    G = nx.Graph()
    for edge in subgraph.get_edges():
        source, target = edge
        G.add_edge(source[0], target[0])  # Just node IDs; include weights if needed
    
    # Save
    nx.write_edgelist(G, f'layer_{layer}.edgelist')

High-Performance: Apache Arrow/Parquet
---------------------------------------

For Large Networks
~~~~~~~~~~~~~~~~~~

Use columnar storage (Arrow/Parquet) to handle large edge lists efficiently.
These formats preserve data types, compress well, and load quickly for analytics
workloads.

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

Rebuild a network from a Parquet edge list. Ensure ``pyarrow`` is installed.

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
    
    network.basic_stats()

Export Statistics and Results
------------------------------

Save Analysis Results
~~~~~~~~~~~~~~~~~~~~~

Persist computed metrics (via DSL) for later inspection or sharing with
colleagues.

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

Store detected communities alongside node and layer IDs for downstream
visualization or comparison.

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

Create a small export bundle so you can hand off the same network in different
formats.

.. code-block:: python

    import json
    import os
    import pickle
    import pandas as pd
    
    # Prepare reusable structures
    def edges_to_df(network):
        records = []
        for edge in network.get_edges():
            (src, src_layer), (dst, dst_layer) = edge
            attrs = network.get_edge_data(edge[0], edge[1])
            records.append({
                "source": src,
                "source_layer": src_layer,
                "target": dst,
                "target_layer": dst_layer,
                "weight": attrs.get("weight", 1.0),
            })
        return pd.DataFrame(records)
    
    edges_df = edges_to_df(network)
    
    network_json = {
        "nodes": [{"id": n, "layer": l} for (n, l) in network.get_nodes()],
        "edges": edges_df.to_dict(orient="records"),
        "layers": list(network.get_layers()),
    }
    
    # Create output directory
    os.makedirs('export', exist_ok=True)
    
    # Export in multiple formats
    formats = {
        'pickle': lambda: pickle.dump(network, open('export/network.pkl', 'wb')),
        'json': lambda: json.dump(network_json, open('export/network.json', 'w')),
        'csv': lambda: edges_df.to_csv('export/edges.csv', index=False)
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
