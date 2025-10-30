Network Visualization
=====================

py3plex provides **specialized visualization** for multilayer networks.

Basic Visualization
-------------------

**Hairball plot** (standard network layout):

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network().load_network(
        "../datasets/goslim_mirna.gpickle", 
        directed=False, 
        input_type="gpickle_biomine")
    
    network.visualize_network(style="hairball")

**Diagonal multilayer layout** (py3plex **specialty**):

.. code-block:: python

    network.visualize_network(style="diagonal")

Examples
--------

For **detailed visualization examples**, see:

- ``example_multilayer_visualization.py`` - **Core visualization techniques**
- ``example_visualization.py`` - **Various plotting styles**
- ``example_community_visualization.py`` - **Community detection visualization**
- ``example_supra_adjacency.py`` - **Supra-adjacency matrices**

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
