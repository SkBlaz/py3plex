Label Propagation
==================

Label propagation is a semi-supervised learning technique that leverages network structure to infer labels for unlabeled nodes based on the labels of their neighbors. This approach is particularly powerful in multilayer networks, where relationships across different contexts can provide complementary information for classification.

Understanding Semi-Supervised Learning on Networks
----------------------------------------------------

In many real-world scenarios, you have a network where only some nodes are labeled. For example:

- **Social networks:** You know the interests of some users and want to predict interests for others
- **Citation networks:** Some papers are classified by topic; you want to classify the rest
- **Biological networks:** Some proteins have known functions; you want to predict functions for others

Label propagation works by iteratively spreading label information from labeled nodes to their neighbors. Nodes connected to labeled neighbors "receive" label influence proportional to edge weights. After several iterations, the algorithm converges and assigns labels to previously unlabeled nodes.

**Key Insight:** The algorithm assumes *network homophily*—connected nodes tend to share properties. This assumption holds in many real-world networks (friends share interests, co-cited papers address similar topics) but should be validated for your specific domain.

Basic Usage
-----------

The following example demonstrates label propagation on the Cora citation network, a standard benchmark dataset in graph learning:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.network_classification import validate_label_propagation
    
    # Load the Cora network (citation network with labeled paper categories)
    network = multinet.multi_layer_network().load_network(
        "../datasets/cora.mat", directed=False, input_type="sparse")
    
    # Run label propagation with different normalization schemes
    # - network.core_network: The underlying graph structure
    # - network.labels: Ground truth labels for validation
    # - dataset_name: Name for logging and output files
    # - repetitions: Number of runs for statistical robustness
    # - normalization_scheme: How to normalize transition probabilities
    results = validate_label_propagation(
        network.core_network,
        network.labels,
        dataset_name="cora",
        repetitions=5,
        normalization_scheme="freq")

**Understanding the Parameters:**

- ``network.core_network``: The underlying NetworkX graph representing connections between papers.
- ``network.labels``: A dictionary mapping node IDs to category labels. During validation, some labels are hidden and predicted.
- ``repetitions=5``: The experiment runs 5 times with different train/test splits to ensure robust results.
- ``normalization_scheme="freq"``: Normalizes label influence by frequency. Alternatives include:
  
  - ``"binary"``: Treats all edges equally regardless of weight
  - ``"degree"``: Normalizes by node degree to prevent high-degree nodes from dominating
  - ``"symmetric"``: Symmetric normalization for balanced influence

Interpreting Results
--------------------

The ``validate_label_propagation`` function returns accuracy metrics comparing predicted labels against held-out ground truth. Typical results for the Cora dataset:

- **Accuracy:** 70-80% depending on normalization scheme and train/test ratio
- **F1-Score:** Macro and micro F1 scores across categories

If accuracy is lower than expected, consider:

1. **Network structure:** Weak community structure reduces label propagation effectiveness
2. **Homophily assumption:** If connected nodes don't share properties, consider alternative methods
3. **Normalization scheme:** Different schemes work better for different network types

Advanced: Multilayer Label Propagation
--------------------------------------

In multilayer networks, label propagation can leverage information from multiple layers simultaneously. A node's label is influenced by its neighbors across all layers, potentially improving accuracy when layers provide complementary information:

.. code-block:: python

    # Multilayer networks provide richer context for classification
    # The algorithm considers neighbors across ALL layers
    multilayer_results = validate_label_propagation(
        multilayer_network.core_network,
        multilayer_network.labels,
        dataset_name="multilayer_example",
        repetitions=10,
        normalization_scheme="degree")

Examples and Further Reading
----------------------------

For complete examples of label propagation and other semi-supervised methods, see:

- ``example_label_propagation.py`` - Basic label propagation tutorial
- ``example_node_classification.py`` - Comparison of classification methods
- ``example_semi_supervised.py`` - Semi-supervised learning workflows

**Academic Reference:**

Label propagation algorithms are based on: Zhu, X., & Ghahramani, Z. (2002). "Learning from labeled and unlabeled data with label propagation."

Repository: https://github.com/SkBlaz/Py3Plex/tree/master/examples
