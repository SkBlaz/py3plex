Community Detection Tutorial
=============================

This tutorial demonstrates community detection algorithms for multilayer networks using py3plex.

Overview
--------

Community detection identifies groups of nodes that are more densely connected to each other than to the rest of the network. For multilayer networks, communities can span multiple layers, accounting for both intra-layer and inter-layer structure.

Supported Algorithms
--------------------

py3plex provides several community detection algorithms:

* **Louvain** - Fast modularity optimization (recommended for most use cases)
* **Infomap** - Flow-based community detection (requires external binary)
* **Label Propagation** - Semi-supervised approach with known seed communities
* **Multilayer Modularity** - True multilayer community detection (Mucha et al. 2010)

Louvain Algorithm
-----------------

Basic Usage
~~~~~~~~~~~

Fastest algorithm for large networks:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection import community_louvain
    
    # Create or load network
    network = multinet.multi_layer_network()
    network.load_network("data.graphml", input_type="graphml")
    
    # Detect communities using Louvain
    communities = community_louvain.best_partition(network.core_network)
    
    # Print results
    for node, community_id in communities.items():
        print(f"Node {node} -> Community {community_id}")

Parameters
~~~~~~~~~~

.. code-block:: python

    # With custom resolution parameter
    communities = community_louvain.best_partition(
        network.core_network,
        resolution=1.0  # Higher = more communities, Lower = fewer communities
    )

**Resolution parameter:**

* ``resolution=1.0`` - Standard modularity
* ``resolution>1.0`` - More, smaller communities
* ``resolution<1.0`` - Fewer, larger communities

Advantages
~~~~~~~~~~

* Very fast: :math:`O(n \\log n)`
* Scales to millions of nodes
* BSD license (commercial-friendly)
* Well-established and widely used

Disadvantages
~~~~~~~~~~~~~

* Non-deterministic (random initialization)
* Cannot find overlapping communities
* Resolution limit issues

Infomap Algorithm
-----------------

Basic Usage
~~~~~~~~~~~

Flow-based approach for detecting communities:

.. code-block:: python

    from py3plex.algorithms.community_detection import community_wrapper
    
    # Detect communities using Infomap
    communities = community_wrapper.infomap_communities(
        network.core_network,
        binary_path="/path/to/infomap"  # Path to Infomap binary
    )

With Hierarchical Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get hierarchical community structure
    hierarchical_communities = community_wrapper.infomap_communities(
        network.core_network,
        binary_path="/path/to/infomap",
        hierarchical=True
    )

Advantages
~~~~~~~~~~

* Can detect overlapping communities
* Flow-based (natural for many applications)
* Hierarchical structure
* Information-theoretic foundation

Disadvantages
~~~~~~~~~~~~~

* Requires external binary
* AGPLv3 license (viral copyleft - problematic for commercial use)
* Slower than Louvain

Label Propagation
-----------------

Semi-Supervised Detection
~~~~~~~~~~~~~~~~~~~~~~~~~

Use when you have some known community memberships:

.. code-block:: python

    from py3plex.algorithms.community_detection import label_propagation
    
    # Provide seed labels for some nodes
    seed_labels = {
        'node1': 0,
        'node2': 0,
        'node3': 1,
        'node4': 1
    }
    
    # Propagate labels to unlabeled nodes
    communities = label_propagation.propagate(
        network.core_network,
        seed_labels=seed_labels,
        max_iter=100
    )

Fully Unsupervised
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Without seed labels (random initialization)
    communities = label_propagation.propagate(
        network.core_network,
        max_iter=100
    )

Advantages
~~~~~~~~~~

* Very fast: :math:`O(m)` linear in edges
* Can incorporate prior knowledge
* MIT license
* Simple and interpretable

Disadvantages
~~~~~~~~~~~~~

* Non-deterministic
* Sensitive to initialization
* May not converge
* Lower quality than Louvain/Infomap

Multilayer Modularity
---------------------

True Multilayer Detection
~~~~~~~~~~~~~~~~~~~~~~~~~

Accounts for multilayer structure following Mucha et al. (2010):

.. code-block:: python

    from py3plex.algorithms.community_detection import multilayer_modularity as mlm
    
    # Get supra-adjacency matrix
    supra_adj = network.get_supra_adjacency_matrix(sparse=True)
    
    # Detect communities with multilayer modularity
    communities = mlm.multilayer_louvain(
        supra_adj,
        gamma=1.0,      # Resolution parameter
        omega=1.0       # Inter-layer coupling strength
    )

Parameter Tuning
~~~~~~~~~~~~~~~~

.. code-block:: python

    # Emphasize layer-specific structure
    communities = mlm.multilayer_louvain(
        supra_adj,
        gamma=1.0,
        omega=0.1  # Low coupling = layer-specific communities
    )
    
    # Emphasize cross-layer structure
    communities = mlm.multilayer_louvain(
        supra_adj,
        gamma=1.0,
        omega=10.0  # High coupling = cross-layer communities
    )

Mathematical Formulation
~~~~~~~~~~~~~~~~~~~~~~~~

Multilayer modularity is defined as:

.. math::

    Q^{ML} = \\frac{1}{2\\mu} \\sum_{ij\\alpha\\beta} \\left[ (A_{ij}^{[\\alpha]} - \\gamma_{\\alpha} P_{ij}^{[\\alpha]})\\delta_{\\alpha\\beta} + \\omega_{\\alpha\\beta}\\delta_{ij} \\right] \\delta(g_{i}^{[\\alpha]}, g_{j}^{[\\beta]})

Where:

* :math:`A_{ij}^{[\\alpha]}` is the adjacency matrix of layer :math:`\\alpha`
* :math:`P_{ij}^{[\\alpha]}` is the null model (e.g., configuration model)
* :math:`\\gamma_{\\alpha}` is the resolution parameter for layer :math:`\\alpha`
* :math:`\\omega_{\\alpha\\beta}` is the coupling strength between layers
* :math:`\\delta(g_{i}^{[\\alpha]}, g_{j}^{[\\beta]})` is 1 if nodes are in the same community, 0 otherwise

Advantages
~~~~~~~~~~

* Accounts for multilayer structure
* Implements state-of-the-art algorithm
* Configurable inter-layer coupling
* Published in Science (Mucha et al. 2010)

Disadvantages
~~~~~~~~~~~~~

* More computationally expensive
* Requires parameter tuning
* May not scale to very large networks (>100k nodes)

Evaluating Community Quality
-----------------------------

Modularity Score
~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    
    # Compute modularity
    modularity = nx.community.modularity(network.core_network, communities)
    print(f"Modularity: {modularity:.3f}")

**Interpretation:**

* :math:`Q > 0.3`: Good community structure
* :math:`Q > 0.5`: Strong community structure
* :math:`Q < 0.3`: Weak or no community structure

Coverage and Performance
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Coverage: fraction of edges within communities
    coverage = nx.community.coverage(network.core_network, communities)
    
    # Performance: fraction of correctly classified node pairs
    performance = nx.community.performance(network.core_network, communities)
    
    print(f"Coverage: {coverage:.3f}")
    print(f"Performance: {performance:.3f}")

Visualizing Communities
-----------------------

Color by Community
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization.multilayer import hairball_plot
    import matplotlib.pyplot as plt
    
    # Map communities to colors
    node_colors = [communities.get(node, 0) for node in network.core_network.nodes()]
    
    # Visualize with community colors
    hairball_plot(
        network.core_network,
        node_color=node_colors,
        layout_algorithm='force',
        cmap='tab10'
    )
    plt.show()

Community Size Distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from collections import Counter
    import matplotlib.pyplot as plt
    
    # Count community sizes
    community_sizes = Counter(communities.values())
    sizes = list(community_sizes.values())
    
    # Plot distribution
    plt.hist(sizes, bins=20)
    plt.xlabel('Community Size')
    plt.ylabel('Frequency')
    plt.title('Community Size Distribution')
    plt.show()

Comparing Algorithms
--------------------

Run Multiple Algorithms
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Run different algorithms
    louvain_comms = community_louvain.best_partition(network.core_network)
    label_prop_comms = label_propagation.propagate(network.core_network)
    
    # Compare number of communities
    print(f"Louvain: {len(set(louvain_comms.values()))} communities")
    print(f"Label Prop: {len(set(label_prop_comms.values()))} communities")
    
    # Compare modularity
    louvain_mod = nx.community.modularity(network.core_network, 
                                          [set(n for n, c in louvain_comms.items() if c == i) 
                                           for i in set(louvain_comms.values())])
    label_mod = nx.community.modularity(network.core_network,
                                        [set(n for n, c in label_prop_comms.items() if c == i)
                                         for i in set(label_prop_comms.values())])
    
    print(f"Louvain modularity: {louvain_mod:.3f}")
    print(f"Label Prop modularity: {label_mod:.3f}")

Normalized Mutual Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compare similarity between community structures:

.. code-block:: python

    from sklearn.metrics import normalized_mutual_info_score
    
    # Convert to lists
    louvain_list = [louvain_comms[node] for node in network.core_network.nodes()]
    label_list = [label_prop_comms[node] for node in network.core_network.nodes()]
    
    # Compute NMI
    nmi = normalized_mutual_info_score(louvain_list, label_list)
    print(f"NMI between Louvain and Label Prop: {nmi:.3f}")

**Interpretation:**

* NMI = 1.0: Identical community structures
* NMI = 0.0: Completely different structures
* NMI > 0.5: Similar structures

Best Practices
--------------

Algorithm Selection
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 20 30 30

   * - Network Size
     - Speed Priority
     - Quality Priority
     - Recommendation
   * - Small (<1K)
     - Any
     - Any
     - Try all algorithms
   * - Medium (1K-10K)
     - Louvain
     - Louvain/Infomap
     - Louvain (good balance)
   * - Large (10K-100K)
     - Louvain/Label Prop
     - Louvain
     - Louvain
   * - Very Large (>100K)
     - Label Prop
     - Louvain
     - Label Prop or sample

Parameter Guidelines
~~~~~~~~~~~~~~~~~~~~

**Louvain resolution:**

* Start with ``resolution=1.0``
* Increase if communities are too large
* Decrease if communities are too fragmented

**Multilayer coupling (omega):**

* ``omega=1.0`` - Default, balanced
* ``omega<1.0`` - Emphasize layer-specific structure
* ``omega>1.0`` - Emphasize cross-layer structure

Validation
~~~~~~~~~~

Always validate community detection results:

1. **Visual inspection** - Plot and examine communities
2. **Modularity** - Check modularity score (>0.3 is good)
3. **Size distribution** - Check for giant communities or singletons
4. **Domain knowledge** - Do communities make sense for your application?

References
----------

**Louvain:**

Blondel, V. D., et al. (2008). Fast unfolding of communities in large networks. *Journal of Statistical Mechanics*.

**Infomap:**

Rosvall, M., & Bergstrom, C. T. (2008). Maps of random walks on complex networks reveal community structure. *PNAS*, 105(4), 1118-1123.

**Multilayer Modularity:**

Mucha, P. J., et al. (2010). Community structure in time-dependent, multiscale, and multiplex networks. *Science*, 328(5980), 876-878.

See :doc:`../citation` for complete citations with DOIs.

Next Steps
----------

* :doc:`multilayer_centrality` - Centrality measures tutorial
* :doc:`multilayer_modularity` - Multilayer modularity details
* :doc:`../algorithm_guide` - Algorithm selection guide
* Examples in ``examples/example_community_detection.py``
