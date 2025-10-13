Community Detection
===================

py3plex provides wrappers for community detection algorithms optimized for multilayer networks.

Supported Algorithms
--------------------

- **Infomap** - Information-theoretic, supports overlapping communities
- **Louvain** - Modularity optimization
- **Label Propagation** - Semi-supervised learning

Basic Usage
-----------

**Louvain**:

.. code-block:: python

    from py3plex.algorithms.community_detection import community_wrapper as cw
    from py3plex.core import multinet
    
    network = multinet.multi_layer_network().load_network(
        "../datasets/cora.mat", directed=False, input_type="sparse")
    
    partition = cw.louvain_communities(network)

**Infomap** (multiplex):

.. code-block:: python

    network = multinet.multi_layer_network(network_type="multiplex").load_network(
        "../datasets/simple_multiplex.edgelist", 
        directed=False, 
        input_type="multiplex_edges")
    
    partition = cw.infomap_communities(
        network, binary="../bin/Infomap", multiplex=True, verbose=True)

Examples
--------

See detailed examples:

- ``example_community_detection.py`` - Basic community detection
- ``example_community_multiplex.py`` - Multiplex community detection
- ``example_community_visualization.py`` - Visualizing communities

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
