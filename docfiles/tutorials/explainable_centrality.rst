Explainable Centrality in Multilayer Networks
==============================================

This tutorial demonstrates how to use **explainable centrality** to get **human-readable explanations** for why certain nodes have high or low centrality scores in multilayer networks.

Overview
--------

The ``py3plex.algorithms.centrality.explain`` module provides tools to **decompose centrality scores** into interpretable components:

* **Per-layer contributions**: How much each layer contributes to a node's centrality
* **Inter-layer connectivity**: Number of edges crossing between layers
* **Neighborhood structure**: Local motifs like triangles
* **Ranking information**: Rank and percentile among all nodes

This is particularly useful for:

* Understanding **bridge nodes** that connect different layers
* Identifying **layer-specific influences** on centrality
* Explaining centrality to non-technical stakeholders
* Debugging and validating centrality computations

Quickstart
-----------

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.centrality.explain import (
        explain_node_centrality,
        explain_top_k_central_nodes,
    )
    from py3plex.algorithms.centrality_toolkit import multiplex_degree_centrality

    # Create a multilayer network
    net = multinet.multi_layer_network(directed=False)
    net.add_edges([
        ['A', 'social', 'B', 'social', 1],
        ['B', 'social', 'C', 'social', 1],
        ['B', 'collab', 'D', 'collab', 1],
    ], input_type='list')

    # Compute centrality
    centrality = multiplex_degree_centrality(net)

    # Explain a single node
    explanation = explain_node_centrality(net, ('B', 'social'), centrality)
    print(f"Score: {explanation['score']}")
    print(f"Per-layer degree: {explanation['degree_per_layer']}")
    print(f"Inter-layer edges: {explanation['num_interlayer_edges']}")

Explanation Components
----------------------

Each explanation is a dictionary with the following fields:

``score``
~~~~~~~~~
The node's centrality score from the input centrality_scores dict.

``layer_breakdown``
~~~~~~~~~~~~~~~~~~~
Estimated contribution of each layer to the node's centrality.

* For **degree centrality**: exact per-layer degree counts
* For **betweenness**: approximate proportional to degree in each layer  
* For **eigenvector/PageRank**: approximate based on neighbor centralities

``degree_per_layer``
~~~~~~~~~~~~~~~~~~~~
The node's degree (number of connections) in each layer it appears in.

``num_interlayer_edges``
~~~~~~~~~~~~~~~~~~~~~~~~~
Count of edges connecting the node to other layers (identifies bridge nodes).

``local_motifs``
~~~~~~~~~~~~~~~~
Dictionary of local network motifs:

* ``triangles``: Number of triangles the node participates in

``rank``
~~~~~~~~
The node's rank when sorted by centrality (1 = highest).

``percentile``
~~~~~~~~~~~~~~
Percentile rank from 0-100 (higher is more central).

Supported Centrality Methods
-----------------------------

The ``method`` parameter controls how layer contributions are approximated:

``degree``
~~~~~~~~~~
* Layer breakdown = exact degree in each layer
* Most accurate explanation

``betweenness``
~~~~~~~~~~~~~~~
* Layer breakdown ≈ proportional to degree in each layer
* Heuristic approximation

``eigenvector`` / ``pagerank``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Layer breakdown ≈ sum of neighbor centralities per layer
* Heuristic approximation

Explaining Top-K Nodes
----------------------

To explain multiple high-centrality nodes at once:

.. code-block:: python

    # Get explanations for top 5 nodes
    top_explanations = explain_top_k_central_nodes(
        net, 
        centrality,
        method='degree',
        k=5
    )

    for node, explanation in top_explanations.items():
        print(f"Node {node}: score={explanation['score']}, "
              f"rank={explanation['rank']}")

Use Cases
---------

Identifying Bridge Nodes
~~~~~~~~~~~~~~~~~~~~~~~~

Bridge nodes connect different layers and often have high centrality:

.. code-block:: python

    explanation = explain_node_centrality(net, node, centrality)
    
    if explanation['num_interlayer_edges'] > 0:
        print(f"Node {node} is a bridge node connecting:")
        for layer, degree in explanation['degree_per_layer'].items():
            print(f"  - {layer}: {degree} connections")

Comparing Layer Influences
~~~~~~~~~~~~~~~~~~~~~~~~~~

See which layers contribute most to a node's centrality:

.. code-block:: python

    explanation = explain_node_centrality(net, node, centrality)
    
    # Sort layers by contribution
    layers = sorted(
        explanation['layer_breakdown'].items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    print(f"Layer contributions for {node}:")
    for layer, contrib in layers:
        print(f"  {layer}: {contrib:.3f}")

Understanding Ranking
~~~~~~~~~~~~~~~~~~~~~

Contextualize a node's centrality score:

.. code-block:: python

    explanation = explain_node_centrality(net, node, centrality)
    
    print(f"Node {node}:")
    print(f"  - Rank: {explanation['rank']} of {len(centrality)}")
    print(f"  - Percentile: {explanation['percentile']:.1f}%")
    print(f"  - Score: {explanation['score']:.3f}")

Example: Social-Collaboration Network
--------------------------------------

Complete example analyzing a network with bridge nodes:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.centrality.explain import explain_top_k_central_nodes
    from py3plex.algorithms.centrality_toolkit import multiplex_degree_centrality

    # Create network
    net = multinet.multi_layer_network(directed=False)
    
    # Social layer: A-B-C chain
    net.add_edges([
        ['A', 'social', 'B', 'social', 1],
        ['B', 'social', 'C', 'social', 1],
    ], input_type='list')
    
    # Collaboration layer: B-D-E chain (B is bridge)
    net.add_edges([
        ['B', 'collab', 'D', 'collab', 1],
        ['D', 'collab', 'E', 'collab', 1],
    ], input_type='list')
    
    # Compute and explain
    centrality = multiplex_degree_centrality(net, normalized=False)
    explanations = explain_top_k_central_nodes(net, centrality, k=3)
    
    # Display results
    for node, exp in explanations.items():
        print(f"\nNode {node}:")
        print(f"  Score: {exp['score']}")
        print(f"  Layers: {list(exp['degree_per_layer'].keys())}")
        
        if len(exp['degree_per_layer']) > 1:
            print("  ** Bridge node **")

API Reference
-------------

``explain_node_centrality(graph, node, centrality_scores, method='degree')``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generate detailed explanation for a single node's centrality.

**Parameters:**

* ``graph``: py3plex multi_layer_network object
* ``node``: Node identifier (string or (node_id, layer) tuple)
* ``centrality_scores``: Dictionary mapping nodes to centrality scores
* ``method``: Centrality method ('degree', 'betweenness', 'eigenvector', 'pagerank')

**Returns:** Dictionary with explanation fields

``explain_top_k_central_nodes(graph, centrality_scores, method='degree', k=5)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generate explanations for the top-k most central nodes.

**Parameters:**

* ``graph``: py3plex multi_layer_network object
* ``centrality_scores``: Dictionary mapping nodes to centrality scores
* ``method``: Centrality method ('degree', 'betweenness', 'eigenvector', 'pagerank')
* ``k``: Number of top nodes to explain (default: 5)

**Returns:** Dictionary mapping node -> explanation_dict

Notes and Limitations
---------------------

Heuristic Nature
~~~~~~~~~~~~~~~~

The layer breakdown for **betweenness** and **eigenvector/PageRank** centralities are **heuristic approximations**, not exact decompositions. They provide interpretable insights but should not be treated as mathematically rigorous attributions.

For fully rigorous explanations, consider using **Shapley values** or other game-theoretic attribution methods (not currently implemented).

Performance
~~~~~~~~~~~

Explanation is **fast** and scales linearly with the number of nodes explained. It does **not** require recomputing centrality.

Node Format
~~~~~~~~~~~

The module supports both:

* **Flat node IDs**: ``'A'``, ``'B'``, etc. (for single-layer or aggregated views)
* **Tuple node IDs**: ``('A', 'layer1')``, ``('B', 'layer2')``, etc. (for multilayer views)

The function automatically adapts to the node format in ``centrality_scores``.

See Also
--------

* :doc:`multilayer_centrality` - Computing centrality measures
* :doc:`../algorithm_guide` - Overview of all algorithms
* ``examples/network_analysis/example_explainable_centrality.py`` - Complete working example

References
----------

* Battiston, F., et al. (2014). "Structural measures for multiplex networks." Physical Review E, 89(3), 032804.
* De Domenico, M., et al. (2015). "Ranking in interconnected multilayer networks reveals versatile nodes." Nature Communications, 6, 6868.
