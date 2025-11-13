Quick Start Guide
=================

Installation
------------

Install py3plex:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git

Basic Usage
-----------

Import the library:

.. code-block:: python

    from py3plex.core import multinet

Loading Networks
----------------

From edge lists:

.. code-block:: python

    network = multinet.multi_layer_network().load_network(
        "./datasets/test.edgelist", directed=False, input_type="edgelist")

From multilayer edge lists (format: node1 layer1 node2 layer2 weight):

.. code-block:: python

    network = multinet.multi_layer_network().load_network(
        "./datasets/multiedgelist.txt", directed=False, input_type="multiedgelist")

Multiplex networks (same nodes, different layers):

.. code-block:: python

    network = multinet.multi_layer_network(network_type="multiplex").load_network(
        "./datasets/simple_multiplex.edgelist", directed=False, input_type="multiplex_edges")

Network Operations
------------------

Basic operations:

.. code-block:: python

    # Get network statistics
    network.basic_stats()
    
    # Visualize
    network.visualize_network()

For More Examples
-----------------

See the ``examples/`` directory for detailed usage patterns:

- ``example_multilayer_visualization.py`` - Visualization techniques
- ``example_IO.py`` - Loading and saving networks
- ``example_manipulation.py`` - Network manipulation
- ``example_multilayer_functionality.py`` - Core functionality

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
