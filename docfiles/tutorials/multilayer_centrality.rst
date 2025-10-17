Multilayer Network Centrality Measures
======================================


This tutorial demonstrates how to compute various centrality measures for multilayer and multiplex networks using py3plex.

Overview
--------


The `py3plex.algorithms.multilayer_algorithms.centrality` module provides comprehensive implementations of centrality measures specifically designed for multilayer networks. These measures follow standard definitions from multilayer network analysis literature.

Supported Centrality Measures
-----------------------------


1. Degree/Strength-based Measures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


* **Layer-specific degree/strength**: Centrality computed within individual layers
* **Supra degree/strength**: Centrality on the full supra-adjacency matrix
* **Overlapping degree/strength**: Node-level aggregation across all layers
* **Participation coefficient**: Measures how evenly a node's connections are distributed across layers

2. Eigenvector-type Measures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


* **Multiplex eigenvector centrality**: Principal eigenvector of the supra-adjacency matrix
* **Eigenvector versatility**: Node-level aggregation of eigenvector centrality
* **Katz-Bonacich centrality**: Weighted sum of walks on the supra-graph
* **PageRank centrality**: Random walk centrality on the supra-graph

3. Path-based Measures
~~~~~~~~~~~~~~~~~~~~~~


* **Multilayer closeness centrality**: Based on shortest paths in the supra-graph
* **Multilayer betweenness centrality**: Fraction of shortest paths passing through each node-layer

4. Advanced Measures
~~~~~~~~~~~~~~~~~~~~


* **HITS centrality**: Hubs and authorities (equals eigenvector for undirected networks)
* **Current-flow closeness/betweenness**: Based on electrical current flow through the network
* **Subgraph centrality**: Counts closed walks via matrix exponential
* **Total communicability**: Sum of matrix exponential entries
* **Multiplex k-core**: Core decomposition of the multilayer network

Basic Usage
-----------


.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality
    
    # Create a multilayer network
    network = multinet.multi_layer_network(directed=False)
    network.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1],
        ['A', 'L2', 'C', 'L2', 1]
    ], input_type='list')
    
    # Initialize centrality calculator
    calc = MultilayerCentrality(network)
    
    # Compute various centrality measures
    layer_degrees = calc.layer_degree_centrality(weighted=False)
    overlapping_degrees = calc.overlapping_degree_centrality(weighted=False)
    participation = calc.participation_coefficient(weighted=False)
    eigenvector = calc.multiplex_eigenvector_centrality()
    pagerank = calc.pagerank_centrality()
    hits = calc.hits_centrality()
    subgraph = calc.subgraph_centrality()
    k_core = calc.multiplex_k_core()


Computing All Centralities
--------------------------


For convenience, you can compute all available centrality measures at once:

.. code-block:: python

    from py3plex.algorithms.multilayer_algorithms.centrality import compute_all_centralities
    
    # Compute basic centralities
    basic_centralities = compute_all_centralities(network)
    
    # Include path-based measures (computationally expensive)
    with_paths = compute_all_centralities(network, include_path_based=True)
    
    # Include all advanced measures (most comprehensive but computationally intensive)
    all_centralities = compute_all_centralities(network, 
                                              include_path_based=True, 
                                              include_advanced=True)


Aggregation Methods
-------------------


The module provides several methods to aggregate node-layer centralities to node-level centralities:

.. code-block:: python

    # Sum aggregation (default)
    node_centralities = calc.aggregate_to_node_level(layer_centralities, method='sum')
    
    # Mean aggregation
    node_centralities = calc.aggregate_to_node_level(layer_centralities, method='mean')
    
    # Maximum aggregation
    node_centralities = calc.aggregate_to_node_level(layer_centralities, method='max')
    
    # Weighted sum with custom layer weights
    layer_weights = {'L1': 2.0, 'L2': 1.0}
    node_centralities = calc.aggregate_to_node_level(layer_centralities, 
                                                    method='weighted_sum', 
                                                    weights=layer_weights)


Mathematical Definitions
------------------------


Degree-based Measures
~~~~~~~~~~~~~~~~~~~~~


**Layer-specific degree (unweighted)**
* Undirected: :math:`k^{[\alpha]}_i = \sum_j \mathbf{1}(A^{[\alpha]}_{ij} > 0)`
* Directed: :math:`k^{[\alpha],\text{out}}_i = \sum_j \mathbf{1}(A^{[\alpha]}_{ij} > 0)`, :math:`k^{[\alpha],\text{in}}_i = \sum_j \mathbf{1}(A^{[\alpha]}_{ji} > 0)`

**Layer-specific strength (weighted)**
* :math:`s^{[\alpha]}_i = \sum_j A^{[\alpha]}_{ij}` (out-strength)
* :math:`s^{[\alpha],\text{in}}_i = \sum_j A^{[\alpha]}_{ji}` (in-strength)

**Supra degree/strength**
* :math:`k_{i\alpha} = \sum_{j,\beta} \mathbf{1}(M_{(i,\alpha),(j,\beta)} > 0)`
* :math:`s_{i\alpha} = \sum_{j,\beta} M_{(i,\alpha),(j,\beta)}`

**Overlapping degree/strength**
* :math:`k_i^{\text{over}} = \sum_\alpha k^{[\alpha]}_i`
* :math:`s_i^{\text{over}} = \sum_\alpha s^{[\alpha]}_i`

**Participation coefficient**
* :math:`P_i = 1 - \sum_{\alpha=1}^m \left(\frac{k^{[\alpha]}_i}{k_i^{\text{over}}}\right)^2`

Eigenvector-type Measures
~~~~~~~~~~~~~~~~~~~~~~~~~


**Multiplex eigenvector centrality**
* :math:`x = \frac{1}{\lambda_{\max}} Mx` where :math:`x_{i\alpha}` is the centrality of node :math:`i` in layer :math:`\alpha`

**Katz-Bonacich centrality**
* :math:`z = \sum_{t=0}^\infty \alpha^t M^t b = (I - \alpha M)^{-1} b`

**PageRank centrality**
* Standard PageRank algorithm applied to the supra-adjacency matrix

Advanced Measures
~~~~~~~~~~~~~~~~~


**HITS centrality**
* For undirected networks: equivalent to eigenvector centrality
* For directed networks: separate hub and authority scores

**Subgraph centrality**
* :math:`SC_i = (e^A)_{ii}` where :math:`A` is the adjacency matrix

**Total communicability**
* :math:`TC_i = \sum_j (e^A)_{ij}` (row sum of matrix exponential)

**Multiplex k-core**
* Core number: maximum :math:`k` such that node has at least :math:`k` neighbors in the multilayer network

Performance Considerations
--------------------------


* **Path-based measures** (closeness, betweenness) are computationally expensive as they require shortest path computations on the entire supra-graph
* **Advanced measures** (current-flow, communicability, k-core) involve matrix operations that can be costly for large networks
* **Matrix exponential** computations (subgraph centrality, communicability) are particularly expensive
* For large networks, consider using only degree-based and eigenvector-based measures
* Use `include_path_based=False` and `include_advanced=False` (defaults) in `compute_all_centralities()` for better performance

Example Applications
--------------------


1. **Social network analysis**: Identify influential users across different communication platforms
2. **Transportation networks**: Find critical stations/stops across different transport modes
3. **Biological networks**: Analyze protein interactions across different cellular conditions
4. **Infrastructure networks**: Study robustness of multilayer utility networks

References
----------


The implementations follow standard definitions from multilayer network analysis literature, particularly:

* Kivelä, M., Arenas, A., Barthelemy, M., Gleeson, J. P., Moreno, Y., & Porter, M. A. (2014). Multilayer networks. Journal of complex networks, 2(3), 203-271.
* Boccaletti, S., Bianconi, G., Criado, R., Del Genio, C. I., Gómez-Gardenes, J., Romance, M., ... & Zanin, M. (2014). The structure and dynamics of multilayer networks. Physics Reports, 544(1), 1-122.