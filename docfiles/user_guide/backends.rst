Backends (Experimental)
=======================

.. warning::
    The backend system is experimental and provides **limited feature parity**
    with the standard ``multi_layer_network`` class. It is primarily designed
    for **interoperability** with other multilayer network libraries, not as
    a replacement for py3plex's core functionality.

py3plex provides experimental utilities for converting between py3plex and
other multilayer network libraries like pymnet. This enables you to:

1. Use pymnet's specialized analysis functions on py3plex networks
2. Import pymnet networks into py3plex for visualization
3. Work with low-level graph structures when needed

For standard multilayer network analysis, continue using ``multi_layer_network`` directly.

Converting Between py3plex and pymnet
-------------------------------------

The primary use case for the backend system is converting networks between
py3plex and pymnet formats.

**Export to pymnet:**

.. code-block:: python

    from py3plex import multi_layer_network
    from py3plex.backends import to_pymnet

    # Create a py3plex network
    net = multi_layer_network()
    net.add_edges([
        {'source': 'A', 'target': 'B',
         'source_type': 'layer1', 'target_type': 'layer1'},
        {'source': 'B', 'target': 'C',
         'source_type': 'layer1', 'target_type': 'layer1'},
    ])

    # Convert to pymnet for specialized analysis
    if is_backend_available('pymnet'):
        pymnet_net = to_pymnet(net)
        # Now use pymnet functions on pymnet_net

**Import from pymnet:**

.. code-block:: python

    from py3plex.backends import from_pymnet, is_backend_available
    import pymnet  # requires: pip install pymnet

    # Create a pymnet network
    pn = pymnet.MultiplexNetwork(couplings='none')
    pn['Alice', 'Bob', 'friends'] = 1
    pn['Bob', 'Carol', 'friends'] = 1

    # Convert to py3plex for visualization
    net = from_pymnet(pn)
    net.visualize_network(style='diagonal')

Installation
------------

To use pymnet conversion features:

.. code-block:: bash

    pip install pymnet
    # or
    pip install py3plex[pymnet]

Checking Availability
---------------------

.. code-block:: python

    from py3plex.backends import list_backends, is_backend_available

    # List available backends
    print(list_backends())  # ['networkx'] or ['networkx', 'pymnet']

    # Check specific backend
    if is_backend_available('pymnet'):
        print("pymnet is available for conversion")

Low-Level Backend API
---------------------

For advanced users who need direct access to graph operations, backends
provide a consistent interface for basic graph manipulation.

.. note::
    The low-level API does NOT replace ``multi_layer_network``. It provides
    basic graph operations only. Use ``multi_layer_network`` for full
    py3plex functionality including visualization, community detection,
    random walks, and I/O operations.

.. code-block:: python

    from py3plex.backends import get_backend

    backend = get_backend()

    # Create a graph
    g = backend.create_graph(directed=False)

    # Add nodes (as node-layer tuples)
    backend.add_node(g, ('Alice', 'friends'))
    backend.add_node(g, ('Bob', 'friends'))

    # Add edges
    backend.add_edge(g, ('Alice', 'friends'), ('Bob', 'friends'), weight=1.0)

    # Basic operations
    print(backend.number_of_nodes(g))  # 2
    print(backend.number_of_edges(g))  # 1
    print(backend.get_layers(g))       # ['friends']

Available Backends
------------------

NetworkX Backend (default)
^^^^^^^^^^^^^^^^^^^^^^^^^^

Always available. Provides a thin wrapper around NetworkX MultiGraph/MultiDiGraph.

Pymnet Backend (optional)
^^^^^^^^^^^^^^^^^^^^^^^^^

Available when pymnet is installed. Provides conversion to/from pymnet's
native MultiplexNetwork format.

**Pymnet advantages:**

- Native multilayer network data structures
- Specialized multilayer analysis functions (clustering, centrality)
- Built-in visualization
- Memory-efficient for certain network structures

For more information about pymnet, see the
`pymnet documentation <https://mnets.github.io/pymnet/>`_.
