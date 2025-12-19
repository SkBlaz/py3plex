Algorithm Selection Guide
=========================

This guide helps you choose the right algorithms for your multilayer network analysis tasks.

Notation and assumptions
------------------------

Unless noted otherwise:

* :math:`n` = number of physical nodes; :math:`m` = edges on the graph being analyzed (aggregated by default, supra-graph when explicitly stated)
* :math:`n_L` = number of state nodes (node-layer pairs), :math:`L` = number of layers; supra-graph algorithms use :math:`n_L` and the corresponding intra- + inter-layer edge count
* For embeddings and other core-network operations, :math:`n` and :math:`m` refer to the aggregated physical-node graph; supra-adjacency algorithms use :math:`n_L` instead
* Complexities assume sparse graphs and hide constant factors from iterative solvers
* Supra-adjacency constructions are assumed sparse; dense forms are only for toy examples
* Shortest-path-based metrics assume non-negative edge weights; negative weights are unsupported

Community Detection
-------------------

Choose based on your network characteristics and requirements:

Louvain Algorithm
~~~~~~~~~~~~~~~~~

Best for:

* Large networks (10,000+ nodes)
* Fast approximate results
* Non-overlapping communities
* Modularity optimization

**Complexity:** :math:`O(m \log n)` in typical sparse settings (implementation-dependent)

**Usage:**

.. code-block:: python

    from py3plex.algorithms.community_detection import community_louvain
    communities = community_louvain.best_partition(network.core_network)

**Pros:**

* Very fast on large networks
* Well-established and widely used
* BSD license (commercial-friendly)

**Cons:**

* Non-deterministic (random initialization)
* Cannot find overlapping communities
* Resolution limit issues

Infomap Algorithm
~~~~~~~~~~~~~~~~~

Best for:

* Flow-based community structure
* Hierarchical community detection
* Information-theoretic optimization
* Optional overlapping output (link communities mode)

**Complexity:** :math:`O(m \log n)` where :math:`m` is edges, :math:`n` is nodes (average-case)

**Usage:**

.. code-block:: python

    from py3plex.algorithms.community_detection import community_wrapper
    communities = community_wrapper.infomap_communities(
        network.core_network,
        binary_path="/path/to/infomap"
    )

**Pros:**

* Can output overlapping communities when configured
* Flow-based approach (natural for many applications)
* Hierarchical structure

**Cons:**

* Requires external binary or AGPLv3 code
* Slower than Louvain
* AGPLv3 license (viral copyleft)

Label Propagation
~~~~~~~~~~~~~~~~~

Best for:

* Label-seeded (semi-supervised) community detection
* Known seed communities
* Very large sparse networks
* Linear-time approximate results

**Complexity:** :math:`O(m)` linear in number of edges

**Usage:**

.. code-block:: python

    from py3plex.algorithms.community_detection import label_propagation
    communities = label_propagation.propagate(
        network.core_network,
        seed_labels={'node1': 0, 'node2': 1}
    )

**Pros:**

* Very fast (linear time)
* Can incorporate prior knowledge
* MIT license

**Cons:**

* Non-deterministic
* Sensitive to initialization
* May not converge

Multilayer Modularity
~~~~~~~~~~~~~~~~~~~~~

Best for:

* True multilayer community detection
* Cross-layer community structure
* Layer coupling analysis
* Research applications

**Complexity:** :math:`O(n_L^2)` to build a dense supra-adjacency (sparse: :math:`O(m)`) plus the downstream Louvain optimization (:math:`O(m \log n_L)` in practice on the sparse supra-graph). Prefer sparse supra-adjacency for anything beyond small toy graphs.

**Usage:**

.. code-block:: python

    from py3plex.algorithms.community_detection import multilayer_modularity as mlm
    supra_adj = network.get_supra_adjacency_matrix()
    communities = mlm.multilayer_louvain(supra_adj)

**Pros:**

* Accounts for multilayer structure
* Implements Mucha et al. (2010) algorithm
* Configurable inter-layer coupling

**Cons:**

* More computationally expensive
* Requires careful parameter tuning
* May not scale to very large networks

Centrality Measures
-------------------

Complexities below use :math:`n_L` state nodes and :math:`m` total edges unless noted.

Degree Centrality
~~~~~~~~~~~~~~~~~

Best for:

* Quick importance ranking
* Local connectivity measure
* Well-connected node identification

**Complexity:** :math:`O(n + m)`

**Variants:**

* Layer-specific degree
* Supra-adjacency degree
* Overlapping degree (sum across layers for each physical node)

**Usage:**

.. code-block:: python

    from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality
    calc = MultilayerCentrality(network)
    degrees = calc.overlapping_degree_centrality()

Betweenness Centrality
~~~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Bridge node identification
* Information flow bottlenecks
* Critical path analysis

**Complexity:** :math:`O(n_L m)` for unweighted, :math:`O(n_L m + n_L^2 \log n_L)` for weighted (Brandes with Dijkstra on the supra-graph)

**Usage:**

.. code-block:: python

    calc = MultilayerCentrality(network)
    betweenness = calc.multilayer_betweenness_centrality()

**Warning:** Computationally expensive beyond a few thousand state nodes; use sampling or approximations when possible

**Note:** Runs on the supra-graph; weighted variants rely on Dijkstra and add the :math:`n_L^2 \log n_L` term. Disconnected components yield zero betweenness for unreachable pairs.

Closeness Centrality
~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Broadcasting efficiency
* Average distance to other nodes
* Central position in network

**Complexity:** :math:`O(n_L m)`

**Usage:**

.. code-block:: python

    closeness = calc.multilayer_closeness_centrality()

**Note:** Distance is computed on the supra-graph; unreachable node-layers typically produce zero closeness.

Eigenvector Centrality
~~~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Influence measure (connections to important nodes)
* Recursive importance
* Prestige ranking

**Complexity:** :math:`O(m)` per iteration, usually converges quickly

**Usage:**

.. code-block:: python

    eigenvector = calc.multiplex_eigenvector_centrality()

**Note:** Convergence assumes a dominant eigenvalue; disconnected graphs are handled per connected component.

PageRank
~~~~~~~~

**Best for:**

* Directed networks
* Web-like structures
* Random walk centrality

**Complexity:** :math:`O(m)` per iteration

**Usage:**

.. code-block:: python

    pagerank = calc.pagerank_centrality(alpha=0.85)

**Note:** Damping factor :math:`\alpha` controls teleportation; set higher values (0.85–0.95) for web-like graphs to avoid sink traps.

Versatility Centrality
~~~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Multilayer-specific importance
* Cross-layer influence
* Multi-context analysis

**Complexity:** :math:`O(m L)` where :math:`L` is number of layers (dominated by the chosen per-layer centrality)

**Usage:**

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls
    versatility = mls.versatility_centrality(network, centrality_type='degree')

New Multiplex Network Metrics
------------------------------

The following metrics extend standard network analysis to multiplex networks, accounting for inter-layer couplings and layer-specific structures. Unless noted, :math:`n_L` is the number of node-layer pairs and :math:`m` counts both intra- and inter-layer edges; all path-based quantities use the supra-graph.

Multiplex Betweenness Centrality
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Identifying bridge nodes across layers
* Finding bottlenecks in multiplex information flow
* Analyzing paths that traverse inter-layer couplings

**Complexity:** :math:`O(n_L m)` for unweighted supra-graphs

**Usage:**

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls
    betweenness = mls.multiplex_betweenness_centrality(network, normalized=True)
    top_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]

**Definition:** Uses shortest paths on the supra-graph; set inter-layer edge weights to reflect coupling strength and ensure weights are non-negative.

**Reference:** De Domenico et al. (2015), "Structural reducibility of multilayer networks"

Multiplex Closeness Centrality
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Finding nodes that can quickly reach all other node-layers
* Broadcasting efficiency across layers
* Central position analysis in multiplex networks

**Complexity:** :math:`O(n_L m)`

**Usage:**

.. code-block:: python

    closeness = mls.multiplex_closeness_centrality(network, normalized=True)
    central_nodes = {k: v for k, v in closeness.items() if v > 0.5}

**Note:** Distances are computed on the supra-graph; nodes in disconnected components yield zero closeness.

**Reference:** De Domenico et al. (2015), "Structural reducibility of multilayer networks"

Community Participation Metrics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Measuring node diversity across communities
* Identifying nodes that bridge different communities
* Analyzing cross-community connections

**Complexity:** :math:`O(k)` per node (overall :math:`O(m)`) where :math:`k` is node degree across all layers

**Usage:**

.. code-block:: python

    # Participation coefficient: P_i = 1 - sum_s (k_is / k_i)**2
    pc = mls.community_participation_coefficient(network, communities, 'Alice')
    
    # Participation entropy: H_i = -sum_s (k_is / k_i) * log(k_is / k_i)
    entropy = mls.community_participation_entropy(network, communities, 'Alice')

**Definitions:** :math:`k_{is}` is the number of links from node :math:`i` to community :math:`s` (summing over layers), and :math:`k_i = \sum_s k_{is}`. If :math:`k_i = 0`, both metrics return 0 to avoid undefined values.

**Reference:** Guimera & Amaral (2005), "Functional cartography of complex metabolic networks"

Layer Redundancy Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Measuring edge overlap between layers
* Identifying redundant vs. unique connections
* Understanding layer complementarity

**Complexity:** :math:`O(m)` where :math:`m` is edges

**Usage:**

.. code-block:: python

    # Redundancy coefficient: R_{alpha,beta} = |E_alpha cap E_beta| / |E_alpha|
    redundancy = mls.layer_redundancy_coefficient(network, 'social', 'work')
    
    # Count unique and redundant edges
    unique, redundant = mls.unique_redundant_edges(network, 'social', 'work')

**Definition:** :math:`E_\alpha` denotes edges in layer :math:`\alpha` (treated as unordered pairs unless your data are directed); :math:`R_{\alpha,\beta}` is asymmetric because it normalizes by :math:`|E_\alpha|`.

**Reference:** Nicosia & Latora (2015), "Measuring and modeling correlations in multiplex networks"

Multiplex Rich-Club Coefficient
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Analyzing whether high-degree nodes connect preferentially
* Network core structure identification
* Hierarchy analysis in multiplex networks

**Complexity:** :math:`O(m)` where :math:`m` is edges

**Usage:**

.. code-block:: python

    rich_club = mls.multiplex_rich_club_coefficient(network, k=10, normalized=True)

**Note:** ``normalized=True`` uses the function's internal null-model rescaling; set it to ``False`` for the raw coefficient.

**Reference:** Extended from Alstott et al. (2014) to multiplex networks

Robustness and Percolation Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Network resilience assessment
* Critical layer identification
* Cascade failure analysis

**Complexity:** :math:`O(t (n_L + m))` where :math:`t` is number of trials

**Usage:**

.. code-block:: python

    # Estimate percolation threshold
    threshold = mls.percolation_threshold(
        network, 
        removal_strategy='degree',  # or 'random', 'betweenness'
        trials=20
    )
    
    # Simulate layer removal
    resilience = mls.targeted_layer_removal(
        network, 
        'social', 
        return_resilience=True
    )

**Reference:** Buldyrev et al. (2010), "Catastrophic cascade of failures in interdependent networks"

Direct Modularity Computation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Evaluating community partition quality
* Comparing different community structures
* Direct modularity calculation without detection

**Complexity:** :math:`O(m)` where :math:`m` is edges

**Usage:**

.. code-block:: python

    # Compute multislice modularity score
    Q = mls.compute_modularity_score(
        network, 
        communities, 
        gamma=1.0,  # resolution parameter
        omega=1.0   # inter-layer coupling
    )

**Reference:** Mucha et al. (2010), Science 328, 876-878

Complete Example
~~~~~~~~~~~~~~~~

See ``examples/network_analysis/example_new_multiplex_metrics.py`` for a comprehensive demonstration of all new metrics.

Network Statistics
------------------

Use these quick calculations to profile the network before running heavier algorithms.

Basic Statistics
~~~~~~~~~~~~~~~~

**Fast operations** (suitable for large networks):

* Node count: :math:`O(n)`
* Edge count: :math:`O(m)`
* Degree distribution: :math:`O(n + m)`
* Density: :math:`O(1)` if counts are known

.. code-block:: python

    network.basic_stats()
    layers = network.get_layers()
    num_nodes = network.node_count

Multilayer Statistics
~~~~~~~~~~~~~~~~~~~~~

**Layer density** - :math:`O(m_\alpha)` per layer: density of edges within layer :math:`\alpha`

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls
    density = mls.layer_density(network, 'layer1')

**Inter-layer correlation** - :math:`O(n)`: correlation of node degrees across layers (uses only nodes present in both layers)

.. code-block:: python

    correlation = mls.inter_layer_degree_correlation(network, 'layer1', 'layer2')

**Edge overlap** - :math:`O(m)`: shared edges across two layers

.. code-block:: python

    overlap = mls.edge_overlap(network, 'layer1', 'layer2')

**Versatility centrality** - :math:`O(m L)`: multilayer importance that mixes centrality across layers

.. code-block:: python

    versatility = mls.versatility_centrality(network, centrality_type='betweenness')

Path-based Measures
~~~~~~~~~~~~~~~~~~~

**Warning:** These are computationally expensive for large networks

* **Diameter** - :math:`O(n_L m)` or :math:`O(n_L^2 \log n_L)`
* **Average shortest path** - :math:`O(n_L m)` or :math:`O(n_L^2 \log n_L)`
* **Betweenness centrality** - :math:`O(n_L m)` or :math:`O(n_L m + n_L^2 \log n_L)`

**Recommendation:** For interactive analysis, keep to a few thousand state nodes or use sampling/approximations

**Note:** Distances are computed on the supra-graph; disconnected components yield infinite paths and zero scores for unreachable pairs.

Node Embeddings
---------------

Embeddings typically operate on the aggregated graph of physical nodes (``network.core_network``) rather than the full supra-adjacency.

Node2Vec
~~~~~~~~

**Best for:**

* Feature learning for downstream tasks
* Link prediction
* Node classification
* Similarity computation

**Complexity:** :math:`O(r \times l \times n)` where :math:`r` is walks per node, :math:`l` is walk length on the aggregated graph

**Parameters:**

* ``dimensions``: Embedding dimensions (default: 128)
* ``walk_length``: Length of random walks (default: 80)
* ``num_walks``: Number of walks per node (default: 10)
* ``p``: Return parameter (default: 1.0)
* ``q``: In-out parameter (default: 1.0)

**Usage:**

.. code-block:: python

    from py3plex.wrappers import node2vec_embedding
    embeddings = node2vec_embedding.generate_embeddings(
        network.core_network,
        dimensions=128,
        walk_length=80,
        num_walks=10,
        p=1.0,
        q=1.0
    )

**Parameter tuning:**

* Low ``p`` (<1): Encourages backtracking (local exploration)
* High ``p`` (>1): Discourages backtracking
* Low ``q`` (<1): Encourages outward exploration (BFS-like)
* High ``q`` (>1): Encourages staying local (DFS-like)

DeepWalk
~~~~~~~~

**Best for:**

* Same as Node2Vec but simpler (uniform random walks)
* Faster than Node2Vec

**Complexity:** :math:`O(r \times l \times n)` on the aggregated graph

**Usage:**

.. code-block:: python

    # DeepWalk is Node2Vec with p=1, q=1
    embeddings = node2vec_embedding.generate_embeddings(
        network.core_network,
        p=1.0,
        q=1.0
    )

Visualization
-------------

Choose layouts based on graph size and desired interpretation; the scalability notes below are practical heuristics rather than hard limits.

Diagonal Projection Plot
~~~~~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Large multilayer networks (>1000 nodes)
* Clear layer separation
* Publication-ready figures

**Scalability:** Practical for tens of thousands of nodes in sparse graphs

**Usage:**

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default
    draw_multilayer_default([network], display=True, layout_style='diagonal')

Force-Directed Layout
~~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Small to medium networks (<1000 nodes)
* Interactive exploration
* Natural-looking layouts

**Scalability:** Practical up to a few thousand nodes

**Usage:**

.. code-block:: python

    from py3plex.visualization.multilayer import hairball_plot
    hairball_plot(network.core_network, layout_algorithm='force')

Matrix Visualization
~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Pattern recognition
* Very large networks
* Quantitative analysis

**Scalability:** Memory-bound; scales to very large sparse networks when plotted as matrices

**Usage:**

.. code-block:: python

    import matplotlib.pyplot as plt
    adj = network.get_supra_adjacency_matrix()
    plt.imshow(adj.toarray() if hasattr(adj, 'toarray') else adj, cmap='viridis')
    plt.colorbar()
    plt.show()

Performance Guidelines
----------------------

Network Size Categories
~~~~~~~~~~~~~~~~~~~~~~~

Heuristics below refer to physical node counts; for dense supra-adjacency graphs, treat the effective size as :math:`n_L`.

**Small** (< 1,000 nodes):
  * All algorithms are fast
  * Can use expensive path-based measures
  * Interactive visualization works well

**Medium** (1,000 - 10,000 nodes):
  * Use Louvain over Infomap
  * Avoid full betweenness centrality
  * Use diagonal projection for visualization

**Large** (10,000 - 100,000 nodes):
  * Use degree-based measures
  * Louvain or label propagation only
  * Matrix visualizations or sampling

**Very Large** (> 100,000 nodes):
  * Degree, PageRank only
  * Label propagation for communities
  * Sparse matrix operations essential

Memory Considerations
~~~~~~~~~~~~~~~~~~~~~

**Supra-adjacency matrix:**

* Sparse representation: :math:`O(m)` memory
* Dense representation: :math:`O(n_L^2)` memory (avoid for large networks)

**Always use sparse matrices for networks with >1,000 state nodes**

.. code-block:: python

    # Ensure sparse representation
    supra_adj = network.get_supra_adjacency_matrix(sparse=True)

Algorithm Comparison Table
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 20 30

   * - Algorithm
     - Complexity
     - Scalability
     - License
     - Best Use Case
   * - Louvain
     - O(m log n)
     - Large
     - BSD
     - Fast community detection
   * - Infomap
     - O(m log n)
     - Medium
     - AGPLv3
     - Flow-based communities
   * - Label Prop
     - O(m)
     - Very Large
     - MIT
     - Semi-supervised, very fast
   * - Degree Centrality
     - O(n + m)
     - Very Large
     - MIT
     - Quick importance
   * - Betweenness
     - O(n_L m)
     - Small
     - MIT
     - Critical paths
   * - PageRank
     - O(m) per iter
     - Large
     - MIT
     - Directed networks
   * - Node2Vec
     - O(r * l * n)
     - Medium
     - MIT
     - Feature learning

Citation Guidelines
-------------------

When using specific algorithms in publications, cite the original papers:

**Louvain:**
  Blondel, V. D., et al. (2008). Fast unfolding of communities in large networks. *Journal of Statistical Mechanics*.

**Infomap:**
  Rosvall, M., & Bergstrom, C. T. (2008). Maps of random walks on complex networks reveal community structure. *PNAS*, 105(4), 1118-1123.

**Node2Vec:**
  Grover, A., & Leskovec, J. (2016). node2vec: Scalable feature learning for networks. *KDD*, 855-864.

**Multilayer Modularity:**
  Mucha, P. J., et al. (2010). Community structure in time-dependent, multiscale, and multiplex networks. *Science*, 328(5980), 876-878.

For complete references with DOIs, please refer to the algorithm citations provided in the individual algorithm documentation or the published paper.

Next Steps
----------

* :doc:`tutorials/community_detection` - Community detection tutorial
* :doc:`tutorials/multilayer_centrality` - Centrality measures tutorial
* :doc:`deployment/performance_scalability` - Performance optimization guide
