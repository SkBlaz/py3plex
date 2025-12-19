Network Construction
====================

The ``multi_layer_network`` class is the **core data structure** in py3plex. It keeps layer metadata explicit so you can build, load, and analyze multilayer or multiplex graphs without losing context.

Basic Usage
-----------

Start by creating a network, loading data, and inspecting quick stats. The network is undirected by default; set ``directed=True`` when needed.

.. code-block:: python

   from py3plex.core import multinet
   
   # Initialize an empty network (undirected by default)
   network = multinet.multi_layer_network()
   
   # Load a graph from disk; set input_type to match your file format
   network.load_network("data.gml", directed=False, input_type="gml")
   
   # Inspect basic statistics (node, edge, and layer counts)
   network.basic_stats()

Supported Input Formats
-----------------------

py3plex supports **all NetworkX formats** plus **multilayer-specific formats**. Pick the ``input_type`` that matches your file structure:

- **edgelist** - Simple edge lists (one layer or already aggregated).
- **multiedgelist** - Multilayer edge lists (``node1 layer1 node2 layer2 weight``).
- **multiplex_edges** - Multiplex format (``layer node1 node2 weight``).
- **gml** - GML format.
- **gpickle** - Compressed NetworkX pickle format.
- **graphml** - GraphML format.
- **nx** - Direct NetworkX object (skip disk I/O).

Multilayer Conventions
-----------------------

- Nodes and edges carry a ``type`` flag to mark layer membership; keep this consistent across files.
- Edges can include a ``weight`` attribute; omit it for unweighted graphs.
- Node labels can encode multiple classes with a delimiter (e.g., ``class1---class2``).
- When loading, set the delimiter explicitly: ``load_network(..., label_delimiter="---")``.

Examples
--------

For detailed walkthroughs, see:

- ``example_IO.py`` - Loading and saving networks.
- ``example_manipulation.py`` - Network construction.
- ``example_multilayer_functionality.py`` - Core operations.

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
