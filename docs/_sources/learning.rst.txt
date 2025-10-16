Random Network Generation
=========================

Generate synthetic multilayer networks for testing and benchmarking.

.. code-block:: python

    from py3plex.core import random_generators
    
    # Generate Erdős-Rényi multilayer network
    network = random_generators.random_multilayer_ER(
        num_nodes=200, 
        num_layers=6, 
        probability=0.09, 
        directed=True)
    
    network.visualize_network(show=True, no_labels=True)

Examples
--------

See: ``example_random_generator.py``

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
