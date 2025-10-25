Algorithm Selection Guide
=========================

This guide helps you choose the right algorithms for your multilayer network analysis tasks.

Community Detection
-------------------

Choose based on your network characteristics and requirements:

Louvain Algorithm
~~~~~~~~~~~~~~~~~

**Best for:**

* Large networks (10,000+ nodes)
* Fast approximate results
* Non-overlapping communities
* Modularity optimization

**Complexity:** :math:`O(n \log n)` where :math:`n` is the number of nodes

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

**Best for:**

* Flow-based community structure
* Overlapping communities
* Hierarchical community detection
* Information-theoretic optimization

**Complexity:** :math:`O(m \log n)` where :math:`m` is edges, :math:`n` is nodes

**Usage:**

.. code-block:: python

    from py3plex.algorithms.community_detection import community_wrapper
    communities = community_wrapper.infomap_communities(
        network.core_network,
        binary_path="/path/to/infomap"
    )

**Pros:**

* Can detect overlapping communities
* Flow-based approach (natural for many applications)
* Hierarchical structure

**Cons:**

* Requires external binary or AGPLv3 code
* Slower than Louvain
* AGPLv3 license (viral copyleft)

Label Propagation
~~~~~~~~~~~~~~~~~

**Best for:**

* Semi-supervised community detection
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

**Best for:**

* True multilayer community detection
* Cross-layer community structure
* Layer coupling analysis
* Research applications

**Complexity:** :math:`O(n^2)` for supra-adjacency construction + Louvain complexity

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

Degree Centrality
~~~~~~~~~~~~~~~~~

**Best for:**

* Quick importance ranking
* Local connectivity measure
* Well-connected node identification

**Complexity:** :math:`O(n + m)`

**Variants:**

* Layer-specific degree
* Supra-adjacency degree
* Overlapping degree (sum across layers)

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

**Complexity:** :math:`O(nm)` for unweighted, :math:`O(nm + n^2 \log n)` for weighted

**Usage:**

.. code-block:: python

    calc = MultilayerCentrality(network)
    betweenness = calc.multilayer_betweenness_centrality()

**Warning:** Computationally expensive for large networks (>1000 nodes)

Closeness Centrality
~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Broadcasting efficiency
* Average distance to other nodes
* Central position in network

**Complexity:** :math:`O(nm)` 

**Usage:**

.. code-block:: python

    closeness = calc.multilayer_closeness_centrality()

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

Versatility Centrality
~~~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Multilayer-specific importance
* Cross-layer influence
* Multi-context analysis

**Complexity:** :math:`O(m \times L)` where :math:`L` is number of layers

**Usage:**

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls
    versatility = mls.versatility_centrality(network, centrality_type='degree')

Network Statistics
------------------

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
    num_nodes = len(network.get_nodes())

Multilayer Statistics
~~~~~~~~~~~~~~~~~~~~~

**Layer density** - :math:`O(m_\alpha)` per layer:

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls
    density = mls.layer_density(network, 'layer1')

**Inter-layer correlation** - :math:`O(n)`:

.. code-block:: python

    correlation = mls.inter_layer_degree_correlation(network, 'layer1', 'layer2')

**Edge overlap** - :math:`O(m)`:

.. code-block:: python

    overlap = mls.edge_overlap(network, 'layer1', 'layer2')

**Versatility centrality** - :math:`O(m \times L)`:

.. code-block:: python

    versatility = mls.versatility_centrality(network, centrality_type='betweenness')

Path-based Measures
~~~~~~~~~~~~~~~~~~~

**Warning:** These are computationally expensive for large networks

* **Diameter** - :math:`O(nm)` or :math:`O(n^2 \log n)`
* **Average shortest path** - :math:`O(nm)` or :math:`O(n^2 \log n)`
* **Betweenness centrality** - :math:`O(nm)` or :math:`O(nm + n^2 \log n)`

**Recommendation:** Limit to networks with <5,000 nodes for interactive analysis

Node Embeddings
---------------

Node2Vec
~~~~~~~~

**Best for:**

* Feature learning for downstream tasks
* Link prediction
* Node classification
* Similarity computation

**Complexity:** :math:`O(r \times l \times |V|)` where :math:`r` is walks per node, :math:`l` is walk length

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

**Complexity:** :math:`O(r \times l \times |V|)`

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

Diagonal Projection Plot
~~~~~~~~~~~~~~~~~~~~~~~~

**Best for:**

* Large multilayer networks (>1000 nodes)
* Clear layer separation
* Publication-ready figures

**Scalability:** Handles 10,000+ nodes

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

**Scalability:** Practical up to ~5,000 nodes

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

**Scalability:** Handles 100,000+ nodes (limited by memory)

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
* Dense representation: :math:`O(n^2)` memory (avoid for large networks)

**Always use sparse matrices for networks with >1,000 nodes**

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
     - O(n log n)
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
     - O(n+m)
     - Very Large
     - MIT
     - Quick importance
   * - Betweenness
     - O(nm)
     - Small
     - MIT
     - Critical paths
   * - PageRank
     - O(m) per iter
     - Large
     - MIT
     - Directed networks
   * - Node2Vec
     - O(r×l×n)
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

For complete references with DOIs, see the `ALGORITHM_CITATIONS.md <https://github.com/SkBlaz/py3plex/blob/master/docs/ALGORITHM_CITATIONS.md>`_ file in the repository.

Next Steps
----------

* :doc:`tutorials/community_detection` - Community detection tutorial
* :doc:`tutorials/multilayer_centrality` - Centrality measures tutorial
* :doc:`performance` - Performance optimization guide
* See `ALGORITHM_CITATIONS.md <https://github.com/SkBlaz/py3plex/blob/master/docs/ALGORITHM_CITATIONS.md>`_ for full citation list
