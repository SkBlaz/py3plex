10-Minute Tutorial
==================

**New to py3plex? Start with this comprehensive 10-minute introduction!**

The tutorial covers:

- Creating multilayer networks
- Loading networks from files
- Exploring network structure
- Computing network metrics
- Community detection
- Basic visualization

**View the full tutorial**: `10min_tutorial.md <https://github.com/SkBlaz/py3plex/blob/master/docs/10min_tutorial.md>`_

**Run the executable version**:

.. code-block:: bash

    cd examples
    python tutorial_10min.py

Quick Example
-------------

.. code-block:: python

    from py3plex.core import multinet

    # Create a multilayer network
    network = multinet.multi_layer_network()

    # Add nodes and edges
    network.add_nodes([[1, 2], [2, 3], [3, 4]], layer_name="layer1")
    network.add_edges([[1, 2], [2, 3]], layer_name="layer1")
    
    # Visualize
    network.visualize_network()

Next Steps
----------

After completing the tutorial:

- Explore more examples in the ``examples/`` directory
- Read the development guide: :doc:`development`
- Check out specialized tutorials:
  
  - `Multilayer Modularity <https://github.com/SkBlaz/py3plex/blob/master/docs/multilayer_modularity_tutorial.md>`_
  - `Multilayer Centrality <https://github.com/SkBlaz/py3plex/blob/master/docs/multilayer_centrality_tutorial.md>`_
  - `Algorithm Selection Guide <https://github.com/SkBlaz/py3plex/blob/master/docs/algorithm_selection_guide.md>`_

