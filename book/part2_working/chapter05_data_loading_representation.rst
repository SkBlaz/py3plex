Data Loading and Representation
==========================================

This chapter covers how to load multilayer networks from various data sources, choose appropriate formats, and represent complex network structures correctly.

.. admonition:: DSL Tip: Validate Data After Loading
   :class: dsl-info

   Use DSL to quickly validate loaded data:

   .. code-block:: python

       from py3plex.dsl import Q, L

       # Check layer sizes
       for layer in network.get_layers():
           count = Q.nodes().from_layers(L[layer]).execute(network).count
           print(f"{layer}: {count} nodes")

       # Find potential data issues
       isolated = Q.nodes().where(degree=0).execute(network)
       if isolated.count > 0:
           print(f"Warning: {isolated.count} isolated nodes")

       # Verify high-degree nodes make sense
       hubs = (
           Q.nodes()
            .where(degree__gt=20)
            .compute("degree")
            .execute(network)
       )
       print(f"Hubs (degree > 20): {hubs.count}")

   Quick validation catches data issues early!

Data Loading Basics
-------------------

Multiple Input Methods
~~~~~~~~~~~~~~~~~~~~~~

Py3plex supports several ways to create multilayer networks:

**1. Direct edge addition** (for programmatic construction):

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network()
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Bob', 'friends', 'Carol', 'friends', 1],
    ], input_type="list")

**2. File loading** (for external data):

.. code-block:: python

    # Load from file
    network = multinet.multi_layer_network()
    network.load_network("data.edgelist", input_type="edgelist")

**3. From NetworkX** (for integration):

.. code-block:: python

    import networkx as nx
    
    G = nx.karate_club_graph()
    network = multinet.multi_layer_network()
    network.load_network_from_networkx(G, layer_name='social')

Edgelist Format
---------------

The **edgelist** format is the simplest and most common:

.. code-block:: text

    # File: network.edgelist
    Alice friends Bob friends 1.0
    Bob friends Carol friends 1.0
    Alice colleagues Bob colleagues 0.8

**Format:** ``source source_layer target target_layer weight``

**Loading:**

.. code-block:: python

    network = multinet.multi_layer_network()
    network.load_network("network.edgelist", input_type="edgelist")

**Best practices:**

* Use consistent node identifiers across layers
* Separate fields with spaces or tabs
* Include weights (default to 1.0 if omitted)
* Comment lines start with ``#``

Dictionary Format
-----------------

For programmatic construction, the dictionary format is most explicit:

.. code-block:: python

    network.add_edges([
        {
            'source': 'Alice',
            'source_type': 'friends',
            'target': 'Bob',
            'target_type': 'friends',
            'weight': 1.0,
            'timestamp': '2023-01-15'  # Optional attributes
        },
        {
            'source': 'Bob',
            'source_type': 'colleagues',
            'target': 'Carol',
            'target_type': 'colleagues',
            'weight': 0.8
        }
    ])

**Advantages:**

* Self-documenting (field names explicit)
* Supports arbitrary edge attributes
* Type-safe (Python dicts)
* Pythonic and readable

Modern I/O System
-----------------

Py3plex provides a modern I/O system (``py3plex.io``) for high-performance serialization:

Supported Formats
~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 15 20 20 45

   * - Format
     - Extension
     - Best For
     - Trade-offs
   * - JSON
     - ``.json``
     - Human-readable, small networks
     - Slower, larger files
   * - JSONL
     - ``.jsonl``
     - Streaming, large networks
     - Not human-friendly
   * - CSV
     - ``.csv``
     - Spreadsheet tools, manual editing
     - Limited attributes
   * - Arrow
     - ``.arrow``
     - High performance, large networks
     - Requires pyarrow
   * - Parquet
     - ``.parquet``
     - Storage, compression, archiving
     - Requires pyarrow

Reading and Writing
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.io import read, write, MultiLayerGraph
    
    # Write (auto-detects format from extension)
    write(network, 'network.json')
    write(network, 'network.arrow')
    write(network, 'network.parquet')
    
    # Read (auto-detects format)
    graph = read('network.json')
    graph = read('network.arrow')
    
    # Specify format explicitly
    write(network, 'myfile.dat', format='json')
    graph = read('myfile.dat', format='parquet')

Apache Arrow Format (Recommended for Large Networks)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Arrow provides 2-3x faster I/O and better compression:

.. code-block:: bash

    # Install Arrow support
    pip install 'py3plex[arrow]'

.. code-block:: python

    from py3plex.io import read, write
    
    # Feather format (fast, uncompressed)
    write(graph, 'network.arrow')
    graph = read('network.arrow')
    
    # Parquet format (compressed, archival)
    write(graph, 'network.parquet')
    graph = read('network.parquet')

**Performance comparison** (1000 nodes, 5000 edges):

=========  ===========  ==========  ===========
Format     Write Time   Read Time   File Size
=========  ===========  ==========  ===========
Arrow      0.016s       0.008s      0.46 MB
Parquet    0.020s       0.010s      0.35 MB
JSON       0.046s       0.030s      1.09 MB
=========  ===========  ==========  ===========

**When to use Arrow:**

* Large networks (>10k nodes)
* Performance-critical pipelines
* Interoperability with pandas, Spark, DuckDB
* Production data workflows

**When to use JSON:**

* Small networks (<1k nodes)
* Human readability required
* Debugging and manual editing
* Maximum compatibility

CSV with Sidecars
~~~~~~~~~~~~~~~~~

CSV format supports optional sidecar files for attributes:

.. code-block:: python

    # Write with sidecars
    write(graph, 'edges.csv', write_sidecars=True)
    # Creates: edges.csv, nodes.csv, layers.csv
    
    # Read with sidecars
    graph = read('edges.csv',
                 nodes_file='nodes.csv',
                 layers_file='layers.csv')

Data Validation and Best Practices
-----------------------------------

Always Verify After Loading
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After loading external data, always verify structure:

.. code-block:: python

    network.load_network("data.edgelist", input_type="edgelist")
    
    # Verify structure
    print(f"Layers: {network.get_layers()}")
    print(f"Nodes per layer: {network.get_number_of_nodes_per_layer()}")
    
    # Check for unexpected layers
    expected_layers = {'friends', 'colleagues'}
    actual_layers = set(network.get_layers())
    if actual_layers != expected_layers:
        print(f"Warning: unexpected layers {actual_layers - expected_layers}")
    
    # Basic statistics
    network.basic_stats()

Consistent Node Identifiers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule:** The same entity must have the same ID across all layers.

**Good:**

.. code-block:: python

    # Alice has the same ID in both layers
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Alice', 'colleagues', 'Carol', 'colleagues', 1],
    ], input_type="list")

**Bad:**

.. code-block:: python

    # Alice's ID differs across layers—breaks multiplex structure
    network.add_edges([
        ['alice_social', 'friends', 'Bob', 'friends', 1],
        ['Alice_Work', 'colleagues', 'Carol', 'colleagues', 1],
    ], input_type="list")

Naming Conventions
~~~~~~~~~~~~~~~~~~

**Layer names:**

* Use descriptive names: ``'coauthor'``, ``'twitter'``, not ``'layer1'``, ``'l2'``
* Lowercase with underscores: ``'social_media'``, not ``'SocialMedia'``
* Avoid special characters

**Node IDs:**

* Use stable, meaningful identifiers (user IDs, DOIs, names)
* Avoid auto-generated IDs that change across runs
* Preserve external IDs when loading from databases

Metadata and Attributes
~~~~~~~~~~~~~~~~~~~~~~~~

Store metadata as node/edge attributes:

.. code-block:: python

    # Add node attributes
    network.core_network.nodes[('Alice', 'friends')]['age'] = 30
    network.core_network.nodes[('Alice', 'friends')]['country'] = 'USA'
    
    # Add edge attributes
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1, {'type': 'close', 'since': 2018}]
    ], input_type="list")

**Recommended practices:**

* Use consistent attribute names across layers
* Store timestamps as ISO format strings: ``'2023-01-15T10:30:00Z'``
* Use numeric types for attributes that will be analyzed
* Document attribute semantics in code comments

Representing Different Network Types
-------------------------------------

Multiplex Networks (Same Nodes Across Layers)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For networks where the same entities appear in all layers:

.. code-block:: python

    network = multinet.multi_layer_network(network_type='multiplex')
    
    # Load data
    network.load_network('social.edges', input_type='multiplex_edges')
    
    # Coupling edges are automatically created
    # (Alice, friends) <-> (Alice, colleagues)
    
    # Get explicit edges only (exclude coupling)
    explicit_edges = list(network.get_edges(multiplex_edges=False))

**When to use:**

* Same people across multiple social platforms
* Same cities in transportation modes (air, rail, road)
* Same proteins in different tissue types

Heterogeneous Networks (Different Node Types)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For networks with different entity types per layer:

.. code-block:: python

    network = multinet.multi_layer_network(network_type='multilayer')
    
    # Different node types
    network.add_edges([
        ['Alice', 'authors', 'Paper1', 'papers', 1],
        ['Bob', 'authors', 'Paper1', 'papers', 1],
        ['Paper1', 'papers', 'ICML', 'venues', 1],
    ], input_type="list")

**When to use:**

* Academic networks (authors, papers, venues)
* E-commerce (users, products, sellers)
* Biomedical (drugs, diseases, targets)

Temporal Networks (Time-Sliced Layers)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For networks that evolve over time:

.. code-block:: python

    network = multinet.multi_layer_network()
    
    # Time windows as layers
    network.add_edges([
        ['Alice', '2020', 'Bob', '2020', 1],
        ['Alice', '2021', 'Bob', '2021', 1],
        ['Bob', '2021', 'Carol', '2021', 1],
    ], input_type="list")

**Best practices:**

* Use consistent time granularity (years, months, days)
* Layer names should be sortable: ``'2020-01'``, ``'2020-02'``, ...
* Add temporal edges connecting adjacent time slices if modeling evolution

Converting Between Formats
---------------------------

NetworkX to Py3plex
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    from py3plex.core import multinet
    
    # Create NetworkX graph
    G = nx.karate_club_graph()
    
    # Convert to py3plex
    network = multinet.multi_layer_network()
    network.load_network_from_networkx(G, layer_name='social')

Py3plex to NetworkX
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Extract single layer as NetworkX graph
    friends_layer = network.get_layer_subgraph('friends')
    
    # Or access the full graph directly
    full_graph = network.core_network  # MultiGraph or MultiDiGraph

Pandas DataFrame to Py3plex
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import pandas as pd
    
    # Load edges from DataFrame
    df = pd.read_csv('edges.csv')
    # Columns: source, source_layer, target, target_layer, weight
    
    # Convert to list of lists
    edges = df[['source', 'source_layer', 'target', 'target_layer', 'weight']].values.tolist()
    
    network = multinet.multi_layer_network()
    network.add_edges(edges, input_type="list")

Common Data Loading Patterns
-----------------------------

Pattern 1: Load from Multiple Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    network = multinet.multi_layer_network()
    
    # Load different layers from different files
    for layer_name, filename in [('friends', 'friends.txt'),
                                   ('colleagues', 'colleagues.txt')]:
        with open(filename) as f:
            for line in f:
                source, target, weight = line.strip().split()
                network.add_edges([
                    [source, layer_name, target, layer_name, float(weight)]
                ], input_type="list")

Pattern 2: Load from Database
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import sqlite3
    
    conn = sqlite3.connect('network.db')
    cursor = conn.execute(
        "SELECT source, source_layer, target, target_layer, weight FROM edges"
    )
    
    network = multinet.multi_layer_network()
    edges = [[row[0], row[1], row[2], row[3], row[4]] for row in cursor]
    network.add_edges(edges, input_type="list")

Pattern 3: Incremental Loading (Large Networks)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    network = multinet.multi_layer_network()
    
    # Load in batches to manage memory
    BATCH_SIZE = 10000
    
    with open('large_network.edgelist') as f:
        batch = []
        for line in f:
            parts = line.strip().split()
            batch.append(parts)
            
            if len(batch) >= BATCH_SIZE:
                network.add_edges(batch, input_type="list")
                batch = []
        
        # Add remaining edges
        if batch:
            network.add_edges(batch, input_type="list")

Troubleshooting
---------------

Issue: Duplicate Edges
~~~~~~~~~~~~~~~~~~~~~~

**Symptom:** More edges than expected after loading.

**Solution:** Check for duplicate entries in source data:

.. code-block:: python

    # Count edge multiplicity
    edge_counts = {}
    for edge in network.get_edges():
        edge_counts[edge] = edge_counts.get(edge, 0) + 1
    
    duplicates = {e: c for e, c in edge_counts.items() if c > 1}
    if duplicates:
        print(f"Found {len(duplicates)} duplicate edges")

Issue: Unexpected Layers
~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptom:** Layers you didn't expect appear in the network.

**Solution:** Verify layer names in source data:

.. code-block:: python

    expected = {'friends', 'colleagues'}
    actual = set(network.get_layers())
    
    if actual != expected:
        print(f"Unexpected layers: {actual - expected}")
        print(f"Missing layers: {expected - actual}")

Issue: Node ID Mismatches
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Symptom:** Same entity appears as different nodes across layers.

**Solution:** Normalize node IDs before loading:

.. code-block:: python

    def normalize_id(node_id):
        """Normalize node identifiers."""
        return str(node_id).strip().lower()
    
    # Apply during loading
    edges = [[normalize_id(s), sl, normalize_id(t), tl, w]
             for s, sl, t, tl, w in raw_edges]
    network.add_edges(edges, input_type="list")

Summary
-------

This chapter covered:

1. **Loading methods** — Direct addition, files, NetworkX import
2. **Data formats** — Edgelist, dictionary, JSON, CSV, Arrow/Parquet
3. **Best practices** — Consistent IDs, validation, metadata storage
4. **Network types** — Multiplex, heterogeneous, temporal
5. **Common patterns** — Multi-file loading, databases, incremental loading

**Key recommendations:**

* Use **Arrow/Parquet** for large networks (>10k nodes)
* Use **JSON** for small networks and debugging
* **Always verify** structure after loading
* Use **consistent node IDs** across layers
* Store **metadata as attributes** for richer analysis

The next chapter covers visualization techniques for exploring multilayer network structure.

Further Reading
---------------

* Arrow format specification: https://arrow.apache.org/docs/
* NetworkX I/O reference: https://networkx.org/documentation/stable/reference/readwrite/
* Chapter 7 (Core Algorithms) for analysis after loading
