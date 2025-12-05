Backends
========

py3plex supports multiple backends for multilayer network representation.
This allows you to choose the underlying library that best fits your use case.

Available Backends
------------------

NetworkX Backend (default)
^^^^^^^^^^^^^^^^^^^^^^^^^^

The default backend uses NetworkX's ``MultiGraph`` and ``MultiDiGraph`` classes
to represent multilayer networks. This is the most compatible option and works
out of the box with all py3plex features.

**Advantages:**

- Always available (NetworkX is a required dependency)
- Full compatibility with NetworkX ecosystem
- Well-tested and stable
- Good for general-purpose network analysis

**When to use:**

- Default choice for most use cases
- When you need to use other NetworkX-based libraries
- When working with existing NetworkX code

Pymnet Backend (optional)
^^^^^^^^^^^^^^^^^^^^^^^^^

The optional pymnet backend uses the `pymnet library <https://github.com/mnets/pymnet>`_
for native multilayer network representation.

**Installation:**

.. code-block:: bash

    pip install pymnet
    # or with py3plex
    pip install py3plex[pymnet]

**Advantages:**

- Native multilayer network data structures
- Specialized multilayer analysis functions
- Built-in visualization capabilities
- Memory-efficient for certain network types

**When to use:**

- When working with complex multiplex networks
- When you need pymnet's specialized analysis functions
- For research involving formal multilayer network theory

Using Backends
--------------

Checking Available Backends
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import py3plex as p3

    # List all available backends
    print(p3.list_backends())
    # Output: ['networkx'] or ['networkx', 'pymnet'] if pymnet is installed

    # Check if a specific backend is available
    print(p3.is_backend_available('networkx'))  # True
    print(p3.is_backend_available('pymnet'))    # True if installed

Getting a Backend Instance
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import py3plex as p3

    # Get the default backend
    backend = p3.get_backend()
    print(backend.name)  # 'networkx'

    # Get a specific backend
    nx_backend = p3.get_backend('networkx')
    
    # If pymnet is installed
    # pymnet_backend = p3.get_backend('pymnet')

Setting the Default Backend
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import py3plex as p3

    # Change the default backend (only if pymnet is installed)
    if p3.is_backend_available('pymnet'):
        p3.set_default_backend('pymnet')
        
        # Now get_backend() returns the pymnet backend
        backend = p3.get_backend()
        print(backend.name)  # 'pymnet'

Backend API
-----------

All backends implement a common interface defined by the ``BaseBackend`` class.
This ensures consistent behavior regardless of which backend you use.

Core Operations
^^^^^^^^^^^^^^^

.. code-block:: python

    from py3plex.backends import get_backend

    backend = get_backend()

    # Create a graph
    g = backend.create_graph(directed=False)

    # Add nodes (as node-layer tuples)
    backend.add_node(g, ('Alice', 'friends'), weight=1.0)
    backend.add_node(g, ('Bob', 'friends'), weight=2.0)

    # Add edges
    backend.add_edge(g, ('Alice', 'friends'), ('Bob', 'friends'), weight=0.5)

    # Check existence
    print(backend.has_node(g, ('Alice', 'friends')))  # True
    print(backend.has_edge(g, ('Alice', 'friends'), ('Bob', 'friends')))  # True

    # Iterate
    for node in backend.nodes(g):
        print(node)
    
    for source, target, data in backend.edges(g, data=True):
        print(f"{source} -> {target}: {data}")

    # Graph properties
    print(backend.number_of_nodes(g))  # 2
    print(backend.number_of_edges(g))  # 1
    print(backend.get_layers(g))       # ['friends']

Subgraph Extraction
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from py3plex.backends import get_backend

    backend = get_backend()
    g = backend.create_graph(directed=False)
    
    # Build a multilayer network
    backend.add_edge(g, ('A', 'layer1'), ('B', 'layer1'))
    backend.add_edge(g, ('A', 'layer2'), ('B', 'layer2'))
    backend.add_edge(g, ('B', 'layer1'), ('C', 'layer1'))

    # Extract by nodes
    subg = backend.subgraph(g, nodes=[('A', 'layer1'), ('B', 'layer1')])
    print(backend.number_of_nodes(subg))  # 2

    # Extract by layers
    subg = backend.subgraph(g, layers=['layer1'])
    print(backend.get_layers(subg))  # ['layer1']

Interoperability
^^^^^^^^^^^^^^^^

All backends can convert to and from NetworkX graphs:

.. code-block:: python

    import networkx as nx
    from py3plex.backends import get_backend

    backend = get_backend()

    # Create a graph in the backend
    g = backend.create_graph(directed=False)
    backend.add_edge(g, ('A', 'layer1'), ('B', 'layer1'))

    # Convert to NetworkX
    nx_graph = backend.to_networkx(g)
    print(type(nx_graph))  # <class 'networkx.classes.multigraph.MultiGraph'>

    # Create from NetworkX
    nx_graph = nx.Graph()
    nx_graph.add_edge(('X', 'test'), ('Y', 'test'))
    g2 = backend.from_networkx(nx_graph)

Creating Custom Backends
------------------------

You can create custom backends by subclassing ``BaseBackend``:

.. code-block:: python

    from py3plex.backends.base import BaseBackend, BackendRegistry

    class MyCustomBackend(BaseBackend):
        @property
        def name(self):
            return "my_backend"
        
        @property
        def version(self):
            return "1.0.0"
        
        def create_graph(self, directed=True):
            # Your implementation
            pass
        
        # Implement all other abstract methods...

    # Register the backend
    from py3plex.backends import _registry
    _registry.register("my_backend", MyCustomBackend)

See the source code of ``NetworkXBackend`` for a complete implementation example.

Configuration
-------------

Backend settings can be configured in ``py3plex.config``:

.. code-block:: python

    from py3plex import config

    # View current default
    print(config.DEFAULT_BACKEND)  # 'networkx'

    # Set a new default (must be a valid backend name)
    config.DEFAULT_BACKEND = 'pymnet'  # Only if pymnet is installed
