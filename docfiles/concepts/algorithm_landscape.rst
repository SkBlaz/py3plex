Algorithm Landscape
===================

This guide provides a narrative overview of the algorithm families available in py3plex, highlighting when to use each type of algorithm for multilayer network analysis. It complements the API reference with plain-language guidance, trade-offs, and cues for multilayer specifics.

Overview
--------

py3plex provides algorithms in seven main categories that work on multilayer graphs encoded as ``(node_id, layer_id)`` pairs:

1. **Community Detection** - Finding groups of densely connected nodes
2. **Centrality & Importance** - Measuring node and edge importance
3. **Network Statistics** - Computing network-level and layer-specific metrics
4. **Random Walks & Embeddings** - Node representations and sampling
5. **Node Ranking & Classification** - Ordering and classifying nodes
6. **Visualization & Layout** - Rendering and spatial arrangement
7. **Benchmarking & Generation** - Testing and synthetic network creation

For detailed parameter lists and API reference, see :doc:`../reference/algorithm_reference`. Use this page to choose a method family, then dive into the reference for parameters.

Community Detection
-------------------

**Goal:** Identify groups of nodes that are more densely connected to each other than to the rest of the network (within or across layers). In multilayer settings, decide whether communities should stay layer-specific or span layers via coupling (``omega`` controls inter-layer links; ``omega = 0`` means layers do not interact).

When to Use
~~~~~~~~~~~

Use community detection when you want to:

* Discover functional modules in biological networks
* Find social groups in multilayer social networks
* Identify topical clusters in citation networks
* Understand organizational structure
* Detect anomalies (nodes that don't fit any community)

Algorithm Families
~~~~~~~~~~~~~~~~~~

**Modularity-Based Methods**

*Best for:* Fast community detection on large networks

*Examples:*

* **Louvain** - Fast, greedy modularity optimization
* **Leiden** - Improved version of Louvain with better stability
* **Multilayer Louvain** - Extends Louvain to multiple layers with inter-layer coupling (set ``omega > 0`` when layers should interact; ``gamma`` tunes community resolution)

*Trade-offs:*

*  Fast (scales to millions of nodes)
*  Easy to use (minimal parameters)
*  Resolution limit (may miss small communities)
*  Stochastic (different runs give different results)

.. code-block:: python

    from py3plex.algorithms.community_detection import community_louvain
    
    # Single-layer Louvain
    partition = community_louvain.best_partition(network.core_network)
    
    # Multilayer Louvain (gamma: resolution, omega: inter-layer coupling)
    from py3plex.algorithms.community_detection.multilayer_modularity import (
        louvain_multilayer
    )
    partition = louvain_multilayer(network, gamma=1.0, omega=1.0)

**Flow-Based Methods**

*Best for:* Finding communities based on information flow

*Examples:*

* **Infomap** - Minimizes description length of random walks (treat multilayer by adding explicit inter-layer edges or by aggregating first)
* **Walktrap** - Based on random walk distances (single-layer)

*Trade-offs:*

*  Theoretically grounded (information theory)
*  Finds hierarchical structure
*  Slower than modularity methods
*  May require external binaries
*  Sensitive to how inter-layer edges are weighted (add or scale them explicitly before running on multilayer data)

.. code-block:: python

    from py3plex.algorithms.community_detection import community_wrapper
    
    # Infomap (requires binary)
    partition = community_wrapper.infomap_communities(
        network.core_network,
        binary_path="/path/to/infomap"
    )

**Overlapping Community Detection**

*Best for:* Networks where nodes belong to multiple communities

*Examples:*

* **NoRC** - Network of Ranked Communities (overlapping membership)
* **Clique Percolation** - Based on overlapping cliques

*Trade-offs:*

*  More realistic for many real networks
*  Captures multi-role nodes
*  More complex to interpret
*  Computationally expensive

.. code-block:: python

    from py3plex.algorithms.community_detection import community_wrapper
    
    # NoRC overlapping communities
    partition = community_wrapper.NoRC_communities(network, alpha=0.5)

Choosing a Community Detection Method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use this decision tree (follow the first condition that applies):

.. code-block:: text

    Do you need overlapping communities?
    ├─ Yes → NoRC or Clique Percolation (expect overlapping memberships)
    └─ No
       └─ Is your network multilayer?
          ├─ Yes → Multilayer Louvain or Leiden
          └─ No
             └─ What's most important?
                ├─ Speed → Louvain
                ├─ Stability → Leiden
                └─ Theory / flow objective → Infomap

Centrality & Importance
-----------------------

**Goal:** Quantify the importance of nodes or edges in the network, per layer or aggregated. Decide whether to keep ``(node, layer)`` pairs separate (preserves context) or to aggregate scores per entity after aligning identifiers.

When to Use
~~~~~~~~~~~

Use centrality measures when you want to:

* Identify influential nodes (e.g., key proteins, opinion leaders)
* Find bottlenecks in flow networks
* Prioritize nodes for intervention or study
* Understand network vulnerability
* Analyze node roles across layers

Algorithm Families
~~~~~~~~~~~~~~~~~~

**Degree-Based Centrality**

*Measures:* Local connectivity

*Examples:*

* **Degree Centrality** - Number of connections
* **Multilayer Degree** - Degree summed across layers
* **Versatility** - Participation across layers (counts how many layers a node engages with; higher means broader presence)

*When to use:*

* Quick assessment of connectivity
* Identifying hubs
* Local importance measures; supply ``weight`` if edge weights matter

.. code-block:: python

    import networkx as nx
    
    # Single-layer degree centrality
    degree_cent = nx.degree_centrality(network.core_network)
    
    # Multilayer versatility
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    versatility = mls.versatility_centrality(network, centrality_type='degree')

**Distance-Based Centrality**

*Measures:* Global position in network

*Examples:*

* **Closeness Centrality** - Average distance to all other nodes (computed within connected components)
* **Betweenness Centrality** - Fraction of shortest paths through node
* **Harmonic Centrality** - Harmonic mean of distances (stable on disconnected graphs)

*When to use:*

* Identifying central nodes
* Finding information brokers
* Understanding information flow (run per connected component if closeness is used, or switch to harmonic variants)

.. code-block:: python

    # Betweenness centrality
    betweenness = nx.betweenness_centrality(network.core_network)
    
    # Closeness centrality
    closeness = nx.closeness_centrality(network.core_network)

**Eigenvector-Based Centrality**

*Measures:* Importance based on connections to important nodes

*Examples:*

* **Eigenvector Centrality** - First eigenvector of adjacency matrix (requires connectivity within each component; compute per component)
* **PageRank** - Google's ranking algorithm (damping factor controls teleportation)
* **HITS** - Hubs and authorities (use on directed graphs)

*When to use:*

* Ranking web pages or citations
* Finding influential nodes in social networks
* Authority/hub analysis

.. code-block:: python

    # PageRank
    pagerank = nx.pagerank(network.core_network)
    
    # Eigenvector centrality
    eigenvector = nx.eigenvector_centrality(network.core_network)

Choosing a Centrality Measure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Consider these questions:

1. **Local vs. Global?**
   - Local → Degree centrality
   - Global → Closeness or betweenness

2. **Direct connections or influence?**
   - Direct → Degree
   - Influence → PageRank or eigenvector

3. **Network type?**
   - Directed → PageRank or HITS
   - Undirected → Any method
   - Weighted → Use weight-aware versions (pass ``weight`` to the function)

4. **Computational cost?**
   - Large network → Degree or PageRank (fast)
   - Small network → Betweenness (expensive but informative)
5. **Layer handling?**
   - Keep per-layer scores when layer context matters
   - Aggregate across layers only after aligning node identifiers

Node Ranking & Classification
-----------------------------

**Goal:** Order nodes by importance or predict node labels using network-derived features. In multilayer settings, decide whether to rank per layer or on an aggregated view, and whether to treat layers as features.

When to Use
~~~~~~~~~~~

Use ranking or classification when you want to:

* Prioritize entities (recommendations, audits, interventions)
* Score candidates for follow-up analysis
* Train classifiers from structural features (centrality, embeddings)
* Combine multilayer evidence into a single ordering

Approaches
~~~~~~~~~~

* **Rank with centrality:** Use degree/PageRank/eigenvector (per layer or aggregated); normalize if layers differ in size.
* **Rank with random walks:** Use multilayer random-walk methods (e.g., MultiXRank) to blend within-layer and cross-layer signals; tune restart probability to control locality.
* **Classify with embeddings:** Generate node embeddings (Node2Vec/DeepWalk/LINE) then train a downstream classifier (e.g., scikit-learn). Include layer ID as a feature if labels depend on layer context.
* **Hybrid scores:** Combine statistical features (degree, clustering, participation coefficient) with embeddings for models that need both local and global cues.

Network Statistics
------------------

**Goal:** Characterize network structure at the global, layer, or node level without committing to a specific downstream task. These checks help validate data quality before heavier modeling.

When to Use
~~~~~~~~~~~

Use network statistics when you want to:

* Compare networks quantitatively
* Understand structural properties
* Validate network models
* Monitor network evolution
* Detect anomalies

Statistic Families
~~~~~~~~~~~~~~~~~~

**Global Statistics**

*Examples:*

* Number of nodes, edges, layers
* Density, clustering coefficient
* Average path length (per connected component unless you use harmonic variants)
* Degree distribution

*When to use:* Basic network characterization or sanity checks before heavier analysis

.. code-block:: python

    # Basic stats
    network.basic_stats()
    
    # Clustering
    import networkx as nx
    clustering = nx.average_clustering(network.core_network)
    
    # Density
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    density = mls.layer_density(network, 'layer1')

**Layer-Specific Statistics**

*Examples:*

* Layer density
* Layer similarity (Jaccard, correlation)
* Edge overlap between layers
* Inter-layer degree correlation

*When to use:* Comparing layers, understanding layer relationships

Layer similarity and overlap assume node identifiers are consistent across layers; if they differ, map or relabel before comparing.

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    # Layer density
    density_l1 = mls.layer_density(network, 'layer1')
    
    # Layer similarity
    similarity = mls.layer_similarity(network, 'layer1', 'layer2', method='jaccard')
    
    # Edge overlap
    overlap = mls.edge_overlap(network, 'layer1', 'layer2')

**Node-Level Statistics**

*Examples:*

* Node activity (presence across layers)
* Participation coefficient
* Cross-layer degree correlation

*When to use:* Characterizing node behavior across layers

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    # Node activity
    activity = mls.node_activity(network, 'Alice')
    
    # Participation coefficient
    participation = mls.community_participation_coefficient(network, partition)

Random Walks & Embeddings
--------------------------

**Goal:** Generate node representations or sample the network through traversal (often as input to downstream ML). Walks operate on the encoded ``(node, layer)`` graph, so inter-layer edges and their weights directly influence the sampled context.

When to Use
~~~~~~~~~~~

Use random walks and embeddings when you want to:

* Create low-dimensional node representations for ML
* Sample large networks efficiently
* Measure node similarity
* Generate features for classification/clustering
* Understand structural equivalence

Algorithm Families
~~~~~~~~~~~~~~~~~~

**Random Walk Algorithms**

*Examples:*

* **Basic Random Walk** - Uniform random traversal
* **Node2Vec** - Biased walks (BFS/DFS-like); works on multilayer graphs if inter-layer edges are present
* **DeepWalk** - Uniform random walks for embeddings

*Parameters:*

* ``walk_length`` - Steps per walk
* ``num_walks`` - Walks per node
* ``p`` (Node2Vec) - Return parameter
* ``q`` (Node2Vec) - In-out parameter
* ``random_seed`` - Set for reproducible walks

.. code-block:: python

    from py3plex.algorithms.general.walkers import generate_walks, node2vec_walk
    
    # Basic walks
    walks = generate_walks(
        network.core_network,
        num_walks=10,
        walk_length=80
    )
    
    # Node2Vec walks (BFS-like: stay local)
    walks_bfs = generate_walks(
        network.core_network,
        num_walks=10,
        walk_length=80,
        p=1.0, q=2.0  # BFS-like
    )
    
    # Node2Vec walks (DFS-like: explore)
    walks_dfs = generate_walks(
        network.core_network,
        num_walks=10,
        walk_length=80,
        p=1.0, q=0.5  # DFS-like
    )

Pass ``random_seed`` to ``generate_walks`` for reproducible samples.

**Embedding Methods**

*Examples:*

* **Node2Vec** - Skip-gram on random walks
* **DeepWalk** - Word2Vec on uniform walks
* **LINE** - First/second-order proximity preservation

*When to use:*

* Node classification
* Link prediction
* Visualization in 2D/3D
* Clustering
* Similarity computation

.. code-block:: python

    from py3plex.wrappers import node2vec_embedding
    
    # Generate embeddings
    embeddings = node2vec_embedding.generate_embeddings(
        network.core_network,
        dimensions=128,
        walk_length=80,
        num_walks=10,
        p=1.0,
        q=1.0
    )
    
    # Use embeddings for ML
    # embeddings is a numpy array: (num_nodes, dimensions)

Choosing Walk Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~

**walk_length:**

* Short (10-20): Fast, local neighborhood
* Medium (40-80): Balanced, standard choice
* Long (100+): Global structure, slower

**p (return parameter):**

* p < 1: More likely to return to previous node (stay local)
* p = 1: Balanced
* p > 1: Less likely to return (keep exploring)

**q (in-out parameter):**

* q < 1: DFS-like (explore distant nodes)
* q = 1: Balanced
* q > 1: BFS-like (stay in local neighborhood)

Visualization & Layout
----------------------

**Goal:** Create visual representations of multilayer networks for exploration or presentation.

When to Use
~~~~~~~~~~~

Use visualization when you want to:

* Explore network structure
* Present findings
* Communicate patterns
* Identify visual anomalies
* Create publication-ready figures

Layout Families
~~~~~~~~~~~~~~~

**Force-Directed Layouts**

*Examples:*

* Spring layout
* Fruchterman-Reingold
* Force Atlas

*Best for:* General-purpose visualization, showing community structure

.. code-block:: python

    from py3plex.visualization.multilayer import hairball_plot
    
    hairball_plot(
        network.core_network,
        layout_algorithm="force",
        layout_parameters={"iterations": 50}
    )

**Specialized Multilayer Layouts**

*Examples:*

* Diagonal projection
* Layered stacking
* Circular layer arrangement

*Best for:* Emphasizing multilayer structure

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default
    
    # Diagonal layout for multilayer networks
    draw_multilayer_default(
        [network],
        display=True,
        layout_style='diagonal'
    )

**Hierarchical Layouts**

*Examples:*

* Reingold-Tilford tree
* Radial tree
* Sugiyama layered

*Best for:* Trees and DAGs

For complete visualization documentation, see :doc:`../user_guide/visualization`.

Benchmarking & Generation
--------------------------

**Goal:** Create synthetic networks for testing and validation without risking production data.

When to Use
~~~~~~~~~~~

Use synthetic network generation when you want to:

* Test algorithm performance
* Validate implementations
* Create controlled experiments
* Generate training data
* Benchmark scalability
* Produce reproducible baselines (fix ``random_state`` when available)

Generator Families
~~~~~~~~~~~~~~~~~~

**Random Network Models**

*Examples:*

* **Erdős-Rényi** - Random edges with fixed probability
* **Barabási-Albert** - Preferential attachment (scale-free)
* **Watts-Strogatz** - Small-world networks

Use ER for null models, BA for heavy-tailed degree distributions, and WS when you need clustering with short paths.

.. code-block:: python

    from py3plex.core import random_generators
    
    # Random multilayer ER network
    network = random_generators.random_multilayer_ER(
        num_nodes=100,
        num_layers=3,
        probability=0.05,
        directed=False
    )

**Benchmark Networks**

*Examples:*

* LFR benchmark (with ground-truth communities)
* Configuration model (preserving degree distribution)
* Block model (with planted partition)

Pick LFR when you need ground truth for community detection, configuration for degree-preserving nulls, and block models for controllable meso-scale structure.

Algorithm Combinations
----------------------

Common Workflows
~~~~~~~~~~~~~~~~

Use these as starting patterns; swap in alternative algorithms from the sections above as needed.

**Community Detection + Visualization:**

.. code-block:: python

    # Detect communities
    partition = louvain_multilayer(network)
    
    # Visualize with community colors
    from py3plex.visualization.multilayer import hairball_plot
    from py3plex.visualization.colors import colors_default
    from collections import Counter
    
    top_communities = [c for c, _ in Counter(partition.values()).most_common(5)]
    color_map = dict(zip(top_communities, colors_default[:5]))
    node_colors = [color_map.get(partition.get(node), 'gray') 
                   for node in network.get_nodes()]
    
    hairball_plot(network.core_network, node_colors, layout_algorithm="force")

**Centrality + Ranking:**

.. code-block:: python

    # Compute centrality
    centrality = nx.betweenness_centrality(network.core_network)
    
    # Rank nodes
    ranked = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
    
    # Top 10
    print("Top 10 nodes:", ranked[:10])

**Embeddings + Classification:**

.. code-block:: python

    # Generate embeddings
    embeddings = node2vec_embedding.generate_embeddings(network.core_network)
    
    # Use for classification (with sklearn)
    from sklearn.ensemble import RandomForestClassifier
    clf = RandomForestClassifier()
    # clf.fit(embeddings, labels)
    # predictions = clf.predict(embeddings_test)

Performance Considerations
--------------------------

Algorithm Complexity
~~~~~~~~~~~~~~~~~~~~

Complexity notation: n = number of nodes, m = number of edges, k = walks per node, l = walk length. Complexities are approximate and assume sparse graphs unless stated otherwise.

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Algorithm Family
     - Typical Complexity
     - Notes
   * - Degree Centrality
     - O(m)
     - Fast, scales well
   * - Betweenness
     - O(nm) or O(nm + n²log n)
     - Expensive for large networks
   * - Louvain
     - ~O(m)
     - Near-linear in practice on sparse graphs
   * - Node2Vec
     - O(m) to precompute + O(k·l·n) for walk generation
     - Training adds extra cost proportional to walk tokens; tune k and l to control runtime
   * - Force Layout
     - O(n²)
     - Slow for >1000 nodes

When working with large networks:

* Use approximate algorithms (e.g., sampling for betweenness)
* Consider layer-by-layer analysis
* Use sparse representations
* See :doc:`../deployment/performance_scalability`

Next Steps
----------

* :doc:`../user_guide/community_detection` - Detailed community detection guide
* :doc:`../user_guide/statistics` - Complete statistics reference
* :doc:`../user_guide/random_walks_embeddings` - Embeddings and walks
* :doc:`../user_guide/visualization` - Visualization techniques
* :doc:`../reference/algorithm_reference` - Detailed algorithm parameters and API

**Academic References:**

* Fortunato & Hric (2016). "Community detection in networks: A user guide." *Physics Reports* 659: 1-44.
* Grover & Leskovec (2016). "node2vec: Scalable feature learning for networks." *KDD*.
* Newman (2018). "Networks" (2nd ed.). Oxford University Press.
