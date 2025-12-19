Algorithm Roadmap
=================

This page provides a **comprehensive overview** of all algorithms implemented in py3plex, organized by category and showing relationships between different methods.

**Purpose:** Help you quickly find the right algorithm for your multilayer network analysis task.

Notation and assumptions
------------------------

Unless otherwise specified:

* :math:`n` = number of physical nodes; :math:`m` = edges on the graph being analyzed (aggregated by default, supra-graph when explicitly stated)
* :math:`n_L` = number of state nodes (node-layer pairs), :math:`L` = number of layers; supra-graph algorithms use :math:`n_L` and the corresponding intra- + inter-layer edge count
* When both :math:`n` and :math:`n_L` appear, :math:`n`/:math:`m` refer to the aggregated physical-node graph; :math:`n_L` and its edge count refer to the supra-adjacency
* Complexities assume sparse graphs and hide iteration-dependent constants from solvers
* Supra-adjacency matrices are sparse unless noted; dense forms are only for toy examples
* Shortest-path-based metrics assume non-negative edge weights; negative weights are unsupported

Algorithm Categories
--------------------

The algorithms in py3plex are organized into these main categories:

1. :ref:`community-detection-algorithms` - Finding community structure
2. :ref:`centrality-measures-algorithms` - Computing node importance
3. :ref:`network-statistics-algorithms` - Network-level metrics
4. :ref:`node-ranking-classification` - Ranking and classification methods
5. :ref:`random-walks-embeddings` - Random walk-based methods
6. :ref:`visualization-algorithms` - Layout and rendering
7. :ref:`benchmark-utilities` - Testing and evaluation

.. _community-detection-algorithms:

Community Detection Algorithms
-------------------------------

**Module:** ``py3plex.algorithms.community_detection``

These algorithms identify groups of densely connected nodes (communities) in multilayer networks.

.. _louvain-algorithm:

Louvain Algorithm
~~~~~~~~~~~~~~~~~

**Path:** ``community_detection.community_louvain``

**Functions:**

* ``best_partition(graph, partition, weight, resolution, randomize, random_state)`` - Main entry point
* ``generate_dendrogram(graph, partition, weight, resolution, randomize, random_state)`` - Hierarchical communities
* ``modularity(partition, graph, weight)`` - Calculate modularity score
* ``partition_at_level(dendrogram, level)`` - Extract partition at specific level
* ``induced_graph(partition, graph, weight)`` - Create quotient graph

**Best for:** Fast community detection on large single-layer networks

**Complexity:** O(m log n) in typical sparse settings

**Related algorithms:** 
  - :ref:`multilayer-louvain` (multilayer extension)
  - :ref:`leiden-algorithm` (improved Louvain)

Infomap Algorithm
~~~~~~~~~~~~~~~~~

**Path:** ``community_detection.community_wrapper``

**Functions:**

* ``infomap_communities(network_input, binary_path, arguments)`` - Main entry point
* ``run_infomap(network, binary_path, arguments)`` - Execute Infomap binary
* ``parse_infomap(outfile)`` - Parse Infomap output

**Best for:** Flow-based community detection, hierarchical structure, optional overlapping output

**Complexity:** O(m log n) where m is edges, n is nodes (average-case)

**Related algorithms:**
  - :ref:`louvain-algorithm` (faster alternative)

.. _multilayer-louvain:

Multilayer Louvain
~~~~~~~~~~~~~~~~~~

**Path:** ``community_detection.multilayer_modularity``

**Functions:**

* ``louvain_multilayer(supra_adj, omega, resolution, seed)`` - Multilayer Louvain
* ``multilayer_modularity(supra_adj, partition, omega)`` - Calculate multilayer modularity
* ``build_supra_modularity_matrix(network, omega)`` - Build modularity matrix

**Best for:** Community detection across multiple layers with inter-layer coupling

**Complexity:** O(n_L^2) to build a dense supra-adjacency (sparse construction: O(m)) plus Louvain-style optimization (about O(m log n_L) on the sparse supra-graph); prefer sparse supra-adjacency for anything beyond small toy graphs

**Algorithm details:** Implements Mucha et al. (2010) multilayer modularity optimization

**Related algorithms:**
  - :ref:`louvain-algorithm` (single-layer version)
  - :ref:`leiden-multilayer` (alternative optimizer)

.. _leiden-algorithm:
.. _leiden-multilayer:

Leiden Algorithm
~~~~~~~~~~~~~~~~

**Path:** ``community_detection.leiden_multilayer``

**Functions:**

* ``leiden_multilayer(supra_adj, omega, resolution, n_iterations, seed)`` - Main entry point

**Data structures:**

* ``LeidenResult`` - Holds partition results with modularity score

**Best for:** More stable community detection than Louvain

**Complexity:** About O(m) per iteration on the supplied graph (m counts intra + inter-layer edges when using a supra-adjacency), with faster convergence than Louvain

**Related algorithms:**
  - :ref:`louvain-algorithm` (predecessor)
  - :ref:`multilayer-louvain` (multilayer extension)

NoRC Algorithm
~~~~~~~~~~~~~~

**Path:** ``community_detection.NoRC`` and ``community_detection.community_wrapper``

**Functions:**

* ``NoRC_communities(network, alpha)`` - Wrapper function
* ``NoRC_communities_main(matrix, alpha)`` - Core implementation
* ``page_rank_kernel(index_row)`` - PageRank computation
* ``create_tree(centers)`` - Build community hierarchy

**Best for:** Networks with overlapping communities

**Complexity:** Dominated by PageRank-style iterations on the core graph; scales roughly with O(m * i) where i is iterations

**Related algorithms:**
  - :ref:`community-ranking` (related approach)

Community Measures
~~~~~~~~~~~~~~~~~~

**Path:** ``community_detection.community_measures``

**Functions:**

* ``modularity(network, partition, weight)`` - Calculate modularity
* ``size_distribution(network_partition)`` - Community size distribution
* ``number_of_communities(network_partition)`` - Count communities

**Purpose:** Evaluate quality of community partitions

**Related algorithms:** All community detection algorithms above

.. _community-ranking:

Community Ranking
~~~~~~~~~~~~~~~~~

**Path:** ``community_detection.community_ranking``

**Functions:**

* ``page_rank_kernel(index_row)`` - PageRank-based ranking
* ``create_tree(centers)`` - Build ranking tree
* ``return_infomap_communities(network)`` - Get Infomap communities

**Best for:** Ranking nodes within detected communities

**Related algorithms:**
  - :ref:`node-ranking-algorithms` (general ranking)

Multilayer Benchmarks
~~~~~~~~~~~~~~~~~~~~~

**Path:** ``community_detection.multilayer_benchmark``

**Functions:**

* ``generate_multilayer_lfr(n_nodes, n_layers, avg_degree, ...)`` - LFR benchmark
* ``generate_coupled_er_multilayer(n_nodes, n_layers, p_intra, p_inter)`` - ER benchmark
* ``generate_sbm_multilayer(sizes, p_matrix, n_layers, ...)`` - SBM benchmark

**Purpose:** Generate synthetic multilayer networks with known community structure for testing

**Related algorithms:** All community detection algorithms

.. _centrality-measures-algorithms:

Centrality Measures
-------------------

**Module:** ``py3plex.algorithms.multilayer_algorithms.centrality``

These algorithms measure the importance or influence of nodes in multilayer networks.

MultilayerCentrality Class
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Path:** ``multilayer_algorithms.centrality.MultilayerCentrality``

**Main class for computing various centrality measures on the supra-adjacency of state nodes (:math:`n_L`).**

Basic Centrality Measures
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Methods:**

* ``overlapping_degree_centrality()`` - Sum of degrees across all layers
* ``layer_specific_degree_centrality(layer)`` - Degree within specific layer
* ``multilayer_degree_centrality()`` - Supra-adjacency degree
* ``average_degree_centrality()`` - Average degree across layers

**Best for:** Quick importance ranking, well-connected node identification

**Complexity:** O(n_L + m) where n_L is state nodes, m is edges (intra + inter-layer)

**Related measures:** 
  - :ref:`versatility-centrality` (cross-layer activity)

Eigenvector-Based Measures
^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Methods:**

* ``multiplex_eigenvector_centrality(max_iter, tol)`` - Eigenvector centrality
* ``pagerank_centrality(alpha, max_iter, tol)`` - PageRank
* ``katz_centrality(alpha, beta, max_iter, tol)`` - Katz centrality
* ``communicability_centrality(beta)`` - Communicability centrality

**Best for:** Influence measure, recursive importance, prestige ranking

**Complexity:** O(m) per iteration on sparse supra-adjacency; typically converges in few iterations

**Related measures:**
  - :ref:`hubs-authorities` (directed networks)

Path-Based Measures
^^^^^^^^^^^^^^^^^^^

**Methods:**

* ``multilayer_betweenness_centrality()`` - Betweenness across layers
* ``multilayer_closeness_centrality()`` - Closeness across layers

**Best for:** Bridge identification, broadcasting efficiency

**Complexity:** O(n_L m) for unweighted, O(n_L m + n_L^2 log n_L) for weighted (Brandes with Dijkstra on the supra-graph)

**Warning:** Expensive beyond a few thousand state nodes; use sampling or approximations when possible. Distances are computed on the supra-graph; unreachable pairs yield zero scores.

**Note:** Weighted variants rely on non-negative edge weights for Dijkstra-based shortest paths.

**Related measures:**
  - :ref:`centrality-all` (batch computation)

.. _hubs-authorities:

Hubs and Authorities (HITS)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Path:** ``node_ranking.node_ranking.hubs_and_authorities``

**Best for:** Ranking nodes in directed networks (authority = important destination, hub = important source)

**Related measures:**
  - PageRank in :ref:`centrality-measures-algorithms`

.. _centrality-all:

Utility Functions
^^^^^^^^^^^^^^^^^

**Functions:**

* ``compute_all_centralities(network, include_path_based, include_advanced)`` - Compute multiple measures

**Purpose:** Batch computation of multiple centrality measures

.. _versatility-centrality:

Versatility Centrality
~~~~~~~~~~~~~~~~~~~~~~

**Path:** ``algorithms.statistics.multilayer_statistics.versatility_centrality``

**Function:**

* ``versatility_centrality(network, centrality_type)`` - Cross-layer versatility measure

**Best for:** Measuring how uniformly a node's importance is distributed across layers

**Complexity:** O(m L) where L is number of layers (dominated by the chosen per-layer centrality)

**Related measures:**
  - All centrality measures in :ref:`centrality-measures-algorithms`

Supra Matrix Function Centralities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Path:** ``multilayer_algorithms.supra_matrix_function_centrality``

**Functions:**

* ``communicability_centrality(supra_matrix, beta)`` - Matrix exponential based
* ``katz_centrality(supra_matrix, alpha, beta, max_iter, tol)`` - Resolvent based

**Best for:** Advanced centrality using matrix functions on supra-adjacency

**Complexity:** Dense matrix functions scale as O(n_L^2) to O(n_L^3); prefer sparse-aware solvers for larger supra-graphs

**Related measures:**
  - :ref:`centrality-measures-algorithms` (standard measures)

MultiXRank
~~~~~~~~~~

**Path:** ``multilayer_algorithms.multixrank``

**Functions:**

* ``multixrank_from_py3plex_networks(networks, config)`` - MultiXRank algorithm

**Best for:** Ranking in multiplex heterogeneous networks with bipartite layers

**Algorithm details:** Extends PageRank to multiplex/heterogeneous networks

**Related algorithms:**
  - PageRank in :ref:`centrality-measures-algorithms`

.. _network-statistics-algorithms:

Network Statistics
------------------

**Module:** ``py3plex.algorithms.statistics``

These algorithms compute various statistical properties of multilayer networks.

Multilayer Statistics
~~~~~~~~~~~~~~~~~~~~~

**Path:** ``statistics.multilayer_statistics``

**Layer-level measures:**

* ``layer_density(network, layer)`` - Density of specific layer
* ``edge_overlap(network, layer_i, layer_j)`` - Edge overlap between layers
* ``inter_layer_coupling_strength(network, layer_i, layer_j)`` - Coupling strength
* ``inter_layer_degree_correlation(network, layer_i, layer_j)`` - Degree correlation
* ``inter_layer_assortativity(network, layer_i, layer_j)`` - Assortativity between layers
* ``layer_similarity(network, layer_i, layer_j, method)`` - Layer similarity

**Node-level measures:**

* ``node_activity(network, node)`` - Activity across layers
* ``degree_vector(network, node, weighted)`` - Degree vector across layers
* ``multilayer_clustering_coefficient(network, node)`` - Multilayer clustering

**Network-level measures:**

* ``interdependence(network, sample_size)`` - Network interdependence
* ``supra_laplacian_spectrum(network, k)`` - Spectral properties
* ``algebraic_connectivity(network)`` - Second smallest Laplacian eigenvalue

**Best for:** Understanding multilayer network structure and properties

**Complexity:** Varies by measure; most layer/node summaries are O(n_L + m) on the relevant graph, while spectral routines operate on the supra-graph and can reach O(n_L^2) on dense inputs

**Related algorithms:**
  - :ref:`basic-statistics` (simpler measures)
  - :ref:`topology-measures` (topological properties)

.. _basic-statistics:
.. _multilayer-statistics:

Multilayer Statistics (Detailed)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See the full section above for complete details on multilayer statistics functions.

Basic Statistics
~~~~~~~~~~~~~~~~

**Path:** ``statistics.basic_statistics``

**Functions:**

* ``identify_n_hubs(network, n, metric)`` - Find top-n hub nodes
* ``core_network_statistics(network)`` - Comprehensive network statistics

**Best for:** Quick network overview, hub identification

**Complexity:** O(n + m) on the aggregated core graph for most measures

**Related algorithms:**
  - :ref:`multilayer-statistics` (advanced measures)

.. _topology-measures:

Topology Analysis
~~~~~~~~~~~~~~~~~

**Path:** ``statistics.topology``

Functions for analyzing topological properties of networks.

**Purpose:** Study structural properties like degree distributions, connected components, etc., on the aggregated core graph or per-layer projections.

**Related algorithms:**
  - :ref:`basic-statistics`

Correlation Networks
~~~~~~~~~~~~~~~~~~~~

**Path:** ``statistics.correlation_networks``

**Functions:**

* ``default_correlation_to_network(correlation_matrix, threshold)`` - Convert correlation matrix to network
* ``pick_threshold(matrix)`` - Automatically select threshold

**Best for:** Creating networks from correlation/similarity matrices

**Related algorithms:**
  - :ref:`network-statistics-algorithms` (analysis after construction)

Enrichment Analysis
~~~~~~~~~~~~~~~~~~~

**Path:** ``statistics.enrichment_modules``

**Functions:**

* ``compute_enrichment(term_dataset, annotation_database, ...)`` - General enrichment
* ``fet_enrichment_generic(...)`` - Fisher's exact test enrichment
* ``fet_enrichment_terms(...)`` - Term enrichment
* ``fet_enrichment_uniprot(...)`` - UniProt annotation enrichment
* ``calculate_pval(term, alternative)`` - p-value calculation
* ``multiple_test_correction(input_dataset)`` - FDR correction

**Best for:** Finding over-represented terms/annotations in network communities

**Related algorithms:**
  - :ref:`community-detection-algorithms` (provides communities for enrichment)

Statistical Comparison
~~~~~~~~~~~~~~~~~~~~~~

**Path:** ``statistics.stats_comparison``

**Functions:** Various statistical tests for comparing networks or algorithms

**Related modules:**
  - ``statistics.bayesiantests`` - Bayesian statistical tests
  - ``statistics.bayesian_distances`` - Bayesian distance measures
  - ``statistics.critical_distances`` - Critical difference diagrams

**Best for:** Comparing performance of different algorithms or network properties

Power Law Analysis
~~~~~~~~~~~~~~~~~~

**Path:** ``statistics.powerlaw``

Functions for testing and fitting power law distributions in networks.

**Best for:** Analyzing degree distributions, checking for scale-free properties

**Related algorithms:**
  - :ref:`basic-statistics` (degree distributions)

.. _node-ranking-classification:

Node Ranking & Classification
------------------------------

**Module:** ``py3plex.algorithms.node_ranking`` and ``py3plex.algorithms.network_classification``

These methods operate on the aggregated (often directed) core graph; :math:`n` and :math:`m` below refer to physical nodes and edges.

.. _node-ranking-algorithms:

Node Ranking
~~~~~~~~~~~~

**Path:** ``node_ranking.node_ranking``

**Functions:**

* ``sparse_page_rank(graph, alpha, personalization, max_iter, tol)`` - Sparse PageRank
* ``hubs_and_authorities(graph)`` - HITS algorithm
* ``hub_matrix(graph)`` - Hub matrix computation
* ``authority_matrix(graph)`` - Authority matrix computation
* ``stochastic_normalization(matrix)`` - Normalize for random walks
* ``stochastic_normalization_hin(matrix)`` - Normalize for heterogeneous networks

**Best for:** Ranking nodes by importance in directed networks

**Complexity:** O(m) per iteration for PageRank; HITS uses similar power iterations with the same per-iteration cost

**Related algorithms:**
  - PageRank in :ref:`centrality-measures-algorithms`
  - :ref:`label-propagation` (classification)

.. _label-propagation:

Label Propagation
~~~~~~~~~~~~~~~~~

**Path:** ``network_classification.label_propagation``

**Functions:**

* ``label_propagation(adjacency, labels, alpha, max_iter, tol, normalization)`` - Main algorithm
* ``validate_label_propagation(...)`` - Validation function
* ``label_propagation_normalization(matrix)`` - Normalization
* ``normalize_initial_matrix_freq(mat)`` - Frequency normalization
* ``normalize_amplify_freq(mat)`` - Amplified normalization
* ``normalize_exp(mat)`` - Exponential normalization

**Best for:** Semi-supervised node classification

**Complexity:** O(m * i) where m is edges and i is number of iterations

**Related algorithms:**
  - :ref:`ppr-algorithm` (personalized version)
  - Label propagation in :ref:`community-detection-algorithms`

.. _ppr-algorithm:

Personalized PageRank (PPR)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Path:** ``network_classification.PPR``

**Functions:**

* ``construct_PPR_matrix(graph_matrix, parallel)`` - Build PPR matrix
* ``construct_PPR_matrix_targets(graph_matrix, targets, parallel)`` - PPR for specific targets
* ``validate_ppr(...)`` - Validation function

**Best for:** Local network exploration, personalized node ranking

**Complexity:** O(n^2) for dense computation; sparse power iterations are about O(m * i) where i is iterations

**Related algorithms:**
  - :ref:`label-propagation` (similar propagation mechanism)
  - PageRank in :ref:`node-ranking-algorithms`

.. _random-walks-embeddings:

Random Walks & Embeddings
--------------------------

**Module:** ``py3plex.algorithms.general`` and ``py3plex.wrappers``

.. _random-walk-primitives:

Random Walk Primitives
~~~~~~~~~~~~~~~~~~~~~~

**Path:** ``general.walkers``

**Functions:**

* ``basic_random_walk(graph, start_node, walk_length)`` - Simple random walk
* ``node2vec_walk(graph, start_node, walk_length, p, q)`` - Biased random walk
* ``generate_walks(graph, num_walks, walk_length, strategy, ...)`` - Generate multiple walks
* ``general_random_walk(G, start_node, iterations, teleportation_prob)`` - Random walk with restart
* ``layer_specific_random_walk(network, start_node, start_layer, walk_length, ...)`` - Multilayer walk

**Best for:** Foundation for embedding algorithms, network exploration

**Complexity:** O(ell) per walk where ell is the walk length

**Related algorithms:**
  - :ref:`node2vec-embedding` (uses these walks)
  - :ref:`deepwalk-embedding` (uses these walks)

.. _node2vec-embedding:

Node2Vec Embedding
~~~~~~~~~~~~~~~~~~

**Path:** ``wrappers.node2vec_embedding``

**Functions:**

* ``generate_embeddings(graph, dimensions, walk_length, num_walks, p, q, ...)`` - Generate embeddings
* ``train_node2vec(graph, ...)`` - Training wrapper

**Best for:** Feature learning, link prediction, node classification

**Complexity:** O(r * l * n) where r is walks per node, l is walk length, n is nodes on the (aggregated) walk graph

**Parameters:**

* ``p``: Return parameter (controls backtracking)
* ``q``: In-out parameter (controls exploration vs exploitation)

**Related algorithms:**
  - :ref:`deepwalk-embedding` (special case with p=1, q=1)
  - :ref:`random-walk-primitives` (underlying walks)

.. _deepwalk-embedding:

DeepWalk Embedding
~~~~~~~~~~~~~~~~~~

**Implementation:** Node2Vec with p=1, q=1

**Best for:** Simpler alternative to Node2Vec with uniform random walks

**Related algorithms:**
  - :ref:`node2vec-embedding` (generalization)

Entanglement Analysis
~~~~~~~~~~~~~~~~~~~~~

**Path:** ``multilayer_algorithms.entanglement``

**Functions:**

* ``compute_entanglement_analysis(network)`` - Full entanglement analysis
* ``build_occurrence_matrix(network)`` - Build node-layer occurrence matrix
* ``compute_blocks(c_matrix)`` - Compute block structure
* ``compute_entanglement(block_matrix)`` - Calculate entanglement metrics

**Best for:** Analyzing node-layer participation patterns

**Purpose:** Measure how nodes are entangled across layers

**Related algorithms:**
  - :ref:`versatility-centrality` (similar cross-layer analysis)

.. _visualization-algorithms:

Visualization Algorithms
------------------------

**Module:** ``py3plex.visualization``

.. _layout-algorithms:

Layout Algorithms
~~~~~~~~~~~~~~~~~

**Path:** ``visualization.layout_algorithms``

**Available layouts:**

* Force-directed layouts (Spring, Fruchterman-Reingold)
* Circular layout
* Spectral layout
* Hierarchical layout
* Diagonal projection (multilayer-specific)

**Best for:** Positioning nodes for visualization

**Related algorithms:**
  - :ref:`multilayer-visualization` (uses these layouts)

.. _multilayer-visualization:

Multilayer Visualization
~~~~~~~~~~~~~~~~~~~~~~~~

**Path:** ``visualization.multilayer``

**Main functions:**

* ``draw_multilayer_default(networks, ...)`` - Default multilayer drawing
* ``hairball_plot(network, layout_algorithm)`` - Single-layer projection
* Diagonal projection plotting
* Layer-separated visualization

**Best for:** Visualizing multilayer network structure

**Scalability:** 
  - Diagonal projection: practical for tens of thousands of nodes in sparse graphs
  - Force-directed: best for a few thousand nodes
  - Matrix view: memory-bound; works for small/medium graphs or very sparse matrices—otherwise sample or project first

**Related algorithms:**
  - :ref:`layout-algorithms` (positioning)

Drawing Machinery
~~~~~~~~~~~~~~~~~

**Path:** ``visualization.drawing_machinery``

Low-level drawing functions and utilities.

**Purpose:** Support functions for rendering networks

Color Schemes
~~~~~~~~~~~~~

**Path:** ``visualization.colors``

Functions for generating color schemes for communities, layers, node types.

**Related algorithms:**
  - :ref:`community-detection-algorithms` (uses colors)
  - :ref:`multilayer-visualization` (uses colors)

Embedding Visualization
~~~~~~~~~~~~~~~~~~~~~~~

**Path:** ``visualization.embedding_visualization``

Functions for visualizing node embeddings in 2D/3D space.

**Best for:** Visualizing results of embedding algorithms

**Related algorithms:**
  - :ref:`node2vec-embedding`
  - :ref:`deepwalk-embedding`

.. _benchmark-utilities:

Benchmark & Utilities
---------------------

Network Classification Benchmark
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Path:** ``general.benchmark_classification``

**Functions:**

* ``evaluate_oracle_F1(probs, Y_real)`` - Evaluate classification performance

**Best for:** Evaluating node classification algorithms

**Related algorithms:**
  - :ref:`label-propagation`
  - :ref:`node2vec-embedding`

Benchmark Visualizations
~~~~~~~~~~~~~~~~~~~~~~~~

**Path:** ``visualization.benchmark_visualizations``

Functions for visualizing algorithm comparison results.

**Related algorithms:**
  - All algorithms (for benchmarking)

Algorithm Selection Guide
-------------------------

This section helps you choose the right algorithm category based on your task.

By Task Type
~~~~~~~~~~~~

**Community Detection:**
  → See :ref:`community-detection-algorithms`
  
**Node Importance:**
  → See :ref:`centrality-measures-algorithms`
  
**Node Classification:**
  → See :ref:`label-propagation` or :ref:`node2vec-embedding`
  
**Network Comparison:**
  → See :ref:`network-statistics-algorithms`
  
**Feature Learning:**
  → See :ref:`node2vec-embedding`
  
**Visualization:**
  → See :ref:`visualization-algorithms`

By Network Size
~~~~~~~~~~~~~~~

Counts below refer to physical nodes; for dense multilayer graphs treat the effective size as :math:`n_L`.

**Small (<1,000 nodes):**
  * All algorithms work well
  * Can use expensive path-based measures
  * All visualization methods

**Medium (1,000-10,000 nodes):**
  * Prefer Louvain/Leiden over Infomap for speed
  * Avoid full betweenness centrality
  * Use diagonal projection for visualization

**Large (10,000-100,000 nodes):**
  * Degree/PageRank; avoid all-pairs paths
  * Louvain or label propagation
  * Use sampling or projections instead of matrix visualizations

**Very Large (>100,000 nodes):**
  * Degree, PageRank only
  * Label propagation for communities
  * Sparse matrix operations essential

By Network Type
~~~~~~~~~~~~~~~

**Single-layer networks:**
  * Standard algorithms: Louvain, PageRank, betweenness
  * See :ref:`community-detection-algorithms` and :ref:`centrality-measures-algorithms`

**Multiplex/multilayer networks:**
  * Multilayer-specific: :ref:`multilayer-louvain`, :ref:`versatility-centrality`
  * Layer statistics: :ref:`multilayer-statistics`
  * Cross-layer measures

**Directed networks:**
  * PageRank, HITS algorithm
  * See :ref:`node-ranking-algorithms`

**Weighted networks:**
  * Most algorithms support weights
  * Specify a ``weight`` field/parameter where available

**Temporal networks:**
  * Layer-based representation
  * Time-respecting random walks: :ref:`random-walk-primitives` (ensure edges respect ordering)

Algorithm Dependencies
----------------------

This diagram shows how algorithms depend on each other:

.. code-block:: text

    Basic Network Operations
            |
            ├── Random Walks ──────────────┬─→ Node2Vec/DeepWalk
            |                              |
            ├── Centrality Measures ───────┼─→ Versatility
            |                              |
            ├── Community Detection ───────┼─→ Community Measures
            |   |                          |
            |   ├─→ Modularity             └─→ Enrichment Analysis
            |   └─→ Community Ranking
            |
            ├── Statistics ────────────────┬─→ Benchmarks
            |                              └─→ Comparisons
            |
            └── Embeddings ────────────────┬─→ Visualization
                                           └─→ Classification

Common Algorithm Workflows
--------------------------

Community Detection Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # 1. Detect communities
    from py3plex.algorithms.community_detection import louvain_multilayer
    communities = louvain_multilayer(network.get_supra_adjacency_matrix())
    
    # 2. Evaluate quality
    from py3plex.algorithms.community_detection import multilayer_modularity
    quality = multilayer_modularity(network.get_supra_adjacency_matrix(), communities)
    
    # 3. Analyze communities
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    from py3plex.algorithms.statistics.enrichment_modules import compute_enrichment
    
    # 4. Visualize
    from py3plex.visualization.multilayer import draw_multilayer_default
    draw_multilayer_default([network], communities=communities)

Centrality Analysis Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # 1. Compute centralities
    from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality
    calc = MultilayerCentrality(network)
    
    # 2. Multiple measures
    degree = calc.overlapping_degree_centrality()
    pagerank = calc.pagerank_centrality()
    betweenness = calc.multilayer_betweenness_centrality()
    
    # 3. Cross-layer analysis
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    versatility = mls.versatility_centrality(network, centrality_type='degree')
    
    # 4. Identify hubs
    from py3plex.algorithms.statistics.basic_statistics import identify_n_hubs
    hubs = identify_n_hubs(network, n=10, metric='degree')

Embedding Workflow
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # 1. Generate walks
    from py3plex.algorithms.general.walkers import generate_walks
    walks = generate_walks(network.core_network, num_walks=10, 
                          walk_length=80, strategy='node2vec')
    
    # 2. Learn embeddings
    from py3plex.wrappers.node2vec_embedding import generate_embeddings
    embeddings = generate_embeddings(network.core_network, 
                                     dimensions=128, p=1.0, q=1.0)
    
    # 3. Use for classification
    from py3plex.algorithms.network_classification.label_propagation import label_propagation
    # Or use embeddings directly with sklearn

Statistical Analysis Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # 1. Layer-level statistics
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    density = mls.layer_density(network, 'layer1')
    overlap = mls.edge_overlap(network, 'layer1', 'layer2')
    correlation = mls.inter_layer_degree_correlation(network, 'layer1', 'layer2')
    
    # 2. Node-level statistics
    for node in important_nodes:
        activity = mls.node_activity(network, node)
        degree_vec = mls.degree_vector(network, node)
    
    # 3. Network-level statistics
    interdep = mls.interdependence(network)
    connectivity = mls.algebraic_connectivity(network)

Further Reading
---------------

For detailed usage examples and parameter descriptions:

* :doc:`algorithm_guide` - Algorithm selection guide with complexity analysis
* :doc:`tutorials/community_detection` - Community detection examples
* :doc:`tutorials/multilayer_centrality` - Centrality computation examples
* :doc:`deployment/performance_scalability` - Performance optimization tips
* :doc:`apidocs` - Complete API reference

Citation Information
--------------------

When using specific algorithm families, please cite the original papers:

**Louvain & Multilayer Modularity:**
  Blondel et al. (2008), Mucha et al. (2010)

**Node2Vec:**
  Grover & Leskovec (2016)

**Infomap:**
  Rosvall & Bergstrom (2008)

See :doc:`citation` for complete citation information and BibTeX entries.
