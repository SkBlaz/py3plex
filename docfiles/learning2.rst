Label Propagation
==================

Semi-supervised learning on networks using label propagation.

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.network_classification import validate_label_propagation
    
    network = multinet.multi_layer_network().load_network(
        "../datasets/cora.mat", directed=False, input_type="sparse")
    
    # Run label propagation with different normalization schemes
    results = validate_label_propagation(
        network.core_network,
        network.labels,
        dataset_name="cora",
        repetitions=5,
        normalization_scheme="freq")

Examples
--------

See: ``example_label_propagation.py``

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
