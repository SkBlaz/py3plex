I/O and Serialization
=====================

py3plex provides a comprehensive I/O system for reading and writing multilayer graphs in various formats. The system is designed to be extensible, efficient, and easy to use.

Supported Formats
-----------------

Pick the format that best fits your graph size, performance needs, and toolchain. Arrow and Parquet require the optional ``pyarrow`` dependency.

* **JSON** — Human-readable, widely compatible, good for small to medium networks
* **JSONL** — Streaming JSON format, efficient for large networks
* **CSV** — Spreadsheet-compatible, easy to edit manually
* **Arrow/Feather** — High-performance columnar format (fast, uncompressed)
* **Parquet** — Compressed columnar format, best for storage

Basic Usage
-----------

The I/O system provides two main functions: ``read()`` and ``write()``. Both return or accept a ``MultiLayerGraph`` object that keeps nodes, layers, and edges consistent.
Use the same functions for all supported formats so your code stays uniform even when the on-disk format changes.

Reading Graphs
~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.io import read
    
    # Auto-detect format from extension
    graph = read('network.json')
    graph = read('network.csv')
    graph = read('network.arrow')
    
    # Or specify format explicitly
    graph = read('myfile.dat', format='json')

``read`` returns a validated ``MultiLayerGraph`` instance regardless of input format.

Writing Graphs
~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.io import write
    
    # Auto-detect format from extension
    write(graph, 'network.json')
    write(graph, 'network.arrow')
    write(graph, 'network.parquet')
    
    # Or specify format explicitly
    write(graph, 'myfile.dat', format='json')

Format detection uses the file extension; pass ``format=`` when writing to streams or unconventional filenames to avoid ambiguity.

Creating Graphs with the Schema API
------------------------------------

The modern I/O system uses a schema-based API for creating graphs. Nodes, layers, and edges are explicit objects, which keeps attributes and layer membership clear and consistent across formats:

.. code-block:: python

    from py3plex.io import MultiLayerGraph, Node, Layer, Edge
    
    # Create graph
    graph = MultiLayerGraph(
        directed=True,
        attributes={'name': 'Social Network'}
    )
    
    # Add layers
    graph.add_layer(Layer(id='facebook', attributes={'type': 'social'}))
    graph.add_layer(Layer(id='twitter', attributes={'type': 'social'}))
    
    # Add nodes
    graph.add_node(Node(id='alice', attributes={'age': 30}))
    graph.add_node(Node(id='bob', attributes={'age': 25}))
    
    # Add edges
    graph.add_edge(Edge(
        src='alice',
        dst='bob',
        src_layer='facebook',
        dst_layer='facebook',
        attributes={'weight': 0.8}
    ))

Apache Arrow Format
-------------------

Apache Arrow is a high-performance columnar format designed for efficient data interchange. py3plex supports Arrow through two sub-formats:

* **Feather** — Fast, uncompressed format ideal for temporary storage and intermediate pipeline steps
* **Parquet** — Compressed format ideal for long-term storage and interchange

Files ending in ``.arrow`` use Feather by default; specify ``format='parquet'`` for compressed Arrow output.

Installing Arrow Support
~~~~~~~~~~~~~~~~~~~~~~~~~

Arrow support requires the pyarrow package:

.. code-block:: bash

    pip install 'py3plex[arrow]'
    # or directly
    pip install pyarrow

Using Arrow Format
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.io import read, write
    
    # Feather format (fast, uncompressed)
    write(graph, 'network.arrow')
    graph = read('network.arrow')
    
    # Parquet format (compressed)
    write(graph, 'network.parquet', format='parquet')
    graph = read('network.parquet', format='parquet')

Benefits of Arrow Format
~~~~~~~~~~~~~~~~~~~~~~~~

1. **Performance**: Columnar storage enables fast read/write operations.
2. **Compression**: Parquet format provides excellent compression ratios.
3. **Interoperability**: Arrow is an industry-standard format supported by:
   
   - pandas, polars (Python data analysis)
   - Apache Spark (big data processing)
   - R, Julia (statistical computing)
   - DuckDB (analytical database)

4. **Type Safety**: Schema preservation with strong typing.
5. **Zero-Copy**: Efficient in-memory representation for fast hand-offs between tools.

Performance Comparison
~~~~~~~~~~~~~~~~~~~~~~

Illustrative timings on a small multilayer network with ~1000 nodes and ~5000 edges (single local run):

+---------+------------+-----------+-------------+
| Format  | Write Time | Read Time | File Size   |
+=========+============+===========+=============+
| Arrow   | 0.016s     | 0.008s    | 0.46 MB     |
+---------+------------+-----------+-------------+
| Parquet | 0.020s     | 0.010s    | 0.35 MB     |
+---------+------------+-----------+-------------+
| JSON    | 0.046s     | 0.030s    | 1.09 MB     |
+---------+------------+-----------+-------------+

Arrow formats are typically faster to write and smaller on disk than JSON for multilayer graphs.
Exact results depend on hardware, compression settings, and graph structure, so treat the table above as a rough guide rather than a benchmark.

When to Use Each Format
~~~~~~~~~~~~~~~~~~~~~~~

**Use Arrow/Feather when:**

- You need maximum read/write performance
- Working with large networks (>10k nodes)
- Interoperating with data science tools (pandas, polars)
- Building data pipelines

**Use Parquet when:**

- Long-term storage is important
- Minimizing storage costs
- Sharing data across platforms
- Archiving networks with schema intact

**Use JSON when:**

- Human readability is important
- Working with small networks
- Debugging or manual editing
- Maximum compatibility needed

**Use CSV when:**

- Working with spreadsheet tools (Excel)
- Simple edge lists
- Manual data entry/editing
- You want sidecar files for node and layer attributes

CSV Format with Sidecars
-------------------------

CSV format supports optional sidecar files for node and layer attributes to keep edge lists clean and avoid repeating metadata in the edge list:

.. code-block:: python

    from py3plex.io import read, write
    
    # Write with sidecars
    write(graph, 'edges.csv', format='csv', write_sidecars=True)
    # Creates: edges.csv, nodes.csv, layers.csv

    # Read with sidecars
    graph = read('edges.csv', format='csv',
                 nodes_file='nodes.csv',
                 layers_file='layers.csv')
    
Use sidecars when you want to keep the primary edge list minimal while still preserving node and layer metadata.

Integration with NetworkX
--------------------------

Convert between py3plex I/O format and NetworkX. Use ``mode='union'`` for single-layer algorithms and ``mode='multiplex'`` when you need to preserve layer identity:

.. code-block:: python

    from py3plex.io import read, to_networkx, from_networkx
    
    # Load graph
    graph = read('network.json')
    
    # Convert to NetworkX
    G = to_networkx(graph, mode='union')       # Merge all layers into one graph
    G = to_networkx(graph, mode='multiplex')   # Preserve layers by using (node, layer) tuples
    
    # Convert back from NetworkX
    graph = from_networkx(G, mode='multiplex')

Example: Complete Workflow
---------------------------

Here's a complete example demonstrating the I/O system:

.. code-block:: python

    from py3plex.io import (
        MultiLayerGraph, Node, Layer, Edge,
        read, write, to_networkx
    )
    
    # Create a multilayer network
    graph = MultiLayerGraph(directed=True)
    
    # Add layers
    for layer_id in ['social', 'work', 'family']:
        graph.add_layer(Layer(id=layer_id))
    
    # Add nodes
    for name in ['alice', 'bob', 'charlie']:
        graph.add_node(Node(id=name))
    
    # Add edges
    edges = [
        ('alice', 'bob', 'social', 'social', 0.8),
        ('bob', 'charlie', 'work', 'work', 0.6),
        ('alice', 'charlie', 'family', 'family', 0.9),
    ]
    
    for src, dst, src_layer, dst_layer, weight in edges:
        graph.add_edge(Edge(
            src=src, dst=dst,
            src_layer=src_layer, dst_layer=dst_layer,
            attributes={'weight': weight}
        ))
    
    # Save in multiple formats
    write(graph, 'network.json')
    write(graph, 'network.arrow')
    write(graph, 'network.parquet')
    
    # Load back
    loaded = read('network.arrow')
    
    # Convert to NetworkX for analysis
    G = to_networkx(loaded, mode='union')
    
    # Use NetworkX algorithms
    import networkx as nx
    centrality = nx.degree_centrality(G)
    print(f"Most central node: {max(centrality, key=centrality.get)}")

Checking Supported Formats
---------------------------

You can query which formats are available at runtime:

.. code-block:: python

    from py3plex.io import supported_formats
    
    formats = supported_formats()
    print(f"Read formats: {formats['read']}")
    print(f"Write formats: {formats['write']}")

This is useful for checking if optional dependencies (like pyarrow) are installed.
Only formats with all required dependencies will appear in the supported lists.

Schema Validation
-----------------

The I/O system includes automatic validation:

.. code-block:: python

    from py3plex.io import (
        MultiLayerGraph, Node, Edge,
        ReferentialIntegrityError
    )
    
    graph = MultiLayerGraph()
    graph.add_node(Node(id='alice'))
    
    try:
        # This will fail - bob doesn't exist
        graph.add_edge(Edge(
            src='alice', dst='bob',
            src_layer='l1', dst_layer='l1'
        ))
    except ReferentialIntegrityError as e:
        print(f"Validation error: {e}")

Validation ensures:

1. All edge endpoints reference existing nodes
2. All edge layers reference existing layers
3. All attributes are JSON-serializable
4. No duplicate edges (by src, dst, src_layer, dst_layer, key)

Advanced: Custom Formats
-------------------------

The I/O system is extensible. You can register custom format readers/writers:

.. code-block:: python

    from py3plex.io import (
        register_reader, register_writer, MultiLayerGraph
    )
    
    def my_reader(filepath, **kwargs):
        # Custom reading logic
        graph = MultiLayerGraph()
        # ... populate graph ...
        return graph
    
    def my_writer(graph, filepath, **kwargs):
        # Custom writing logic
        with open(filepath, 'w') as f:
            # ... write graph ...
            pass
    
    # Register with py3plex so read/write can find them
    register_reader('myformat', my_reader)
    register_writer('myformat', my_writer)
    # Pick a unique format name so you do not shadow built-in formats.
    
    # Now you can use it
    write(graph, 'network.myformat')
    graph = read('network.myformat')

Examples
--------

Complete examples are available in ``examples/io_and_data/``:

* ``example_new_io.py`` - Comprehensive I/O demonstration
* ``example_save_to_arrow.py`` - Apache Arrow format usage
* ``example_save_to_gpickle.py`` - NetworkX pickle format
* ``example_save_to_edgelist.py`` - Edge list format
* ``example_schema_validation.py`` - Schema validation examples

See Also
--------

* :doc:`getting_started/tutorial_10min` - Getting started tutorial
* :doc:`networkx_interop` - NetworkX integration details
* :doc:`deployment/performance_scalability` - Performance optimization tips
