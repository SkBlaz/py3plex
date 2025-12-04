I/O and Serialization
======================

py3plex provides a comprehensive I/O system for reading and writing multilayer graphs in various formats. The system is designed to be extensible, efficient, and easy to use.

Supported Formats
-----------------

The I/O system supports multiple file formats, each with different trade-offs:

* **JSON** - Human-readable, widely compatible, good for small to medium networks
* **JSONL** - Streaming JSON format, efficient for large networks
* **CSV** - Spreadsheet-compatible, easy to edit manually
* **Arrow/Feather** - High-performance columnar format (requires pyarrow)
* **Parquet** - Compressed columnar format, best for storage (requires pyarrow)

Basic Usage
-----------

The I/O system provides two main functions: ``read()`` and ``write()``.

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

Creating Graphs with the Schema API
------------------------------------

The modern I/O system uses a schema-based API for creating graphs:

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

* **Feather** - Fast, uncompressed format ideal for temporary storage
* **Parquet** - Compressed format ideal for long-term storage

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

1. **Performance**: Columnar storage enables fast read/write operations
2. **Compression**: Parquet format provides excellent compression ratios
3. **Interoperability**: Arrow is an industry-standard format supported by:
   
   - pandas, polars (Python data analysis)
   - Apache Spark (big data processing)
   - R, Julia (statistical computing)
   - DuckDB (analytical database)

4. **Type Safety**: Schema preservation with strong typing
5. **Zero-Copy**: Efficient in-memory representation

Performance Comparison
~~~~~~~~~~~~~~~~~~~~~~

For a typical multilayer network with 1000 nodes and ~5000 edges:

+---------+------------+-----------+-------------+
| Format  | Write Time | Read Time | File Size   |
+=========+============+===========+=============+
| Arrow   | 0.016s     | 0.008s    | 0.46 MB     |
+---------+------------+-----------+-------------+
| Parquet | 0.020s     | 0.010s    | 0.35 MB     |
+---------+------------+-----------+-------------+
| JSON    | 0.046s     | 0.030s    | 1.09 MB     |
+---------+------------+-----------+-------------+

Arrow format is **2-3x faster** for writes and provides **2-3x better compression** compared to JSON.

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
- Archiving networks

**Use JSON when:**

- Human readability is important
- Working with small networks
- Debugging or manual editing
- Maximum compatibility needed

**Use CSV when:**

- Working with spreadsheet tools (Excel)
- Simple edge lists
- Manual data entry/editing

CSV Format with Sidecars
-------------------------

CSV format supports optional sidecar files for node and layer attributes:

.. code-block:: python

    from py3plex.io import read, write
    
    # Write with sidecars
    write(graph, 'edges.csv', format='csv', write_sidecars=True)
    # Creates: edges.csv, nodes.csv, layers.csv
    
    # Read with sidecars
    graph = read('edges.csv', format='csv',
                 nodes_file='nodes.csv',
                 layers_file='layers.csv')

Integration with NetworkX
--------------------------

Convert between py3plex I/O format and NetworkX:

.. code-block:: python

    from py3plex.io import read, to_networkx, from_networkx
    
    # Load graph
    graph = read('network.json')
    
    # Convert to NetworkX
    G = to_networkx(graph, mode='union')  # Merge all layers
    # or
    G = to_networkx(graph, mode='multiplex')  # Preserve layers as (node, layer)
    
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

    from py3plex.io import register_reader, register_writer
    
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
    
    # Register
    register_reader('myformat', my_reader)
    register_writer('myformat', my_writer)
    
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

* :doc:`getting_started/quickstart_5min` - Getting started guide
* :doc:`getting_started/tutorial_10min` - Complete tutorial
* :doc:`networkx_interop` - NetworkX integration details
* :doc:`deployment/performance_scalability` - Performance optimization tips
