Network Construction
====================

The ``multi_layer_network`` class is the **core data structure** in py3plex.

Basic Usage
-----------

.. code-block:: python

   from py3plex.core import multinet
   
   # Initialize network
   network = multinet.multi_layer_network()
   
   # Load network
   network.load_network("data.gml", directed=False, input_type="gml")
   
   # Basic statistics
   network.basic_stats()

Supported Input Formats
-----------------------

py3plex supports **all NetworkX formats** plus **multilayer-specific formats**:

- **edgelist** - Simple edge lists
- **multiedgelist** - Multilayer edge lists (**node1 layer1 node2 layer2 weight**)
- **multiplex_edges** - Multiplex format (**layer node1 node2 weight**)
- **gml** - **GML format**
- **gpickle** - **Compressed NetworkX format**
- **graphml** - **GraphML format**
- **nx** - **Direct NetworkX object**

Multilayer Conventions
-----------------------

- Nodes and edges can have a **type** flag
- Edges can have **weights**
- Node labels use **delimiter-separated** classes (e.g., ``class1---class2``)
- Specify delimiter with: ``load_network(..., label_delimiter="---")``

Examples
--------

For **detailed examples**, see:

- ``example_IO.py`` - **Loading and saving networks**
- ``example_manipulation.py`` - **Network construction**
- ``example_multilayer_functionality.py`` - **Core operations**

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
