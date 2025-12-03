Random Network Generation
=========================

Synthetic multilayer networks are essential for testing algorithms, benchmarking performance, and validating theoretical models before applying them to real-world data. Py3plex provides a comprehensive set of random graph generators specifically designed for multilayer network structures.

Why Use Random Networks?
------------------------

Random network generation serves several important purposes in multilayer network analysis:

**Algorithm Development and Testing:** When developing new algorithms or analysis methods, synthetic networks with known properties allow you to validate that your implementation produces expected results. For example, you can verify that a centrality measure correctly identifies hub nodes in a network where you control the degree distribution.

**Benchmarking and Performance Analysis:** Synthetic networks can be generated at various scales (from tens to millions of nodes) to benchmark algorithm performance and memory usage. This helps identify computational bottlenecks before processing large real-world datasets.

**Null Model Comparison:** Comparing real-world network metrics against random baseline models reveals statistically significant structural patterns. If your social network has significantly higher clustering than a random network with the same degree distribution, that clustering is meaningful rather than an artifact of network size.

**Teaching and Demonstration:** Simple random networks are excellent for teaching multilayer network concepts without the complexity of real data preprocessing.

Basic Usage: Erdős-Rényi Multilayer Networks
---------------------------------------------

The Erdős-Rényi (ER) model is the simplest random graph model. Each possible edge exists independently with a fixed probability. Py3plex extends this classic model to multilayer networks, where you can specify the number of layers and the edge probability within and between layers.

.. code-block:: python

    from py3plex.core import random_generators
    
    # Generate Erdős-Rényi multilayer network
    # - num_nodes: Number of unique entities in the network
    # - num_layers: Number of distinct layers
    # - probability: Edge existence probability (0.0 to 1.0)
    # - directed: Whether edges have direction
    network = random_generators.random_multilayer_ER(
        num_nodes=200, 
        num_layers=6, 
        probability=0.09, 
        directed=True)
    
    # Visualize the generated network
    network.visualize_network(show=True, no_labels=True)

**Understanding the Parameters:**

- ``num_nodes=200``: Creates 200 unique nodes. With 6 layers, this results in up to 1,200 node-layer pairs.
- ``num_layers=6``: Creates 6 distinct layers, representing different relationship types or contexts.
- ``probability=0.09``: Each possible edge has a 9% chance of existing. Higher values create denser networks.
- ``directed=True``: Edges have direction (A→B is different from B→A). Set to ``False`` for undirected networks.

**Expected Behavior:**

With these parameters, you'll get a moderately sparse multilayer network. The expected number of edges per layer is approximately ``n(n-1) × p / 2 ≈ 200 × 199 × 0.09 / 2 ≈ 1,791`` edges for undirected networks (double for directed). The actual number varies due to random sampling.

Interpreting Generated Networks
-------------------------------

After generating a random network, always verify its properties before use:

.. code-block:: python

    # Check basic statistics
    network.basic_stats()
    
    # Expected output (varies by random seed):
    # Number of nodes: ~1200 (200 × 6 layers)
    # Number of edges: ~10,000+ (varies with probability)

If the network is too dense or sparse for your needs, adjust the ``probability`` parameter. A rule of thumb: for sparse networks typical of social or biological systems, use probability values between 0.01 and 0.1.

Examples and Further Reading
----------------------------

For complete examples of random network generation, including other models like scale-free and small-world networks, see:

- ``example_random_generator.py`` - Basic random network generation
- ``example_random_networks.py`` - Comparing different random models
- ``example_benchmark_random.py`` - Performance benchmarking with random networks

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
