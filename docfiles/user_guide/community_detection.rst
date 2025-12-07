Community Detection
===================

*Finding groups that span multiple layers of interaction.*

.. admonition:: DSL Tip: Filter by Communities
   :class: dsl-info

   After detecting communities, use DSL to analyze them:

   .. code-block:: python

       from py3plex.core import multinet
       from py3plex.dsl import Q, L
       from py3plex.algorithms.community_detection import community_louvain

       # Step 1: Detect communities
       communities = community_louvain.best_partition(network.core_network)
       
       # Step 2: Store community IDs as node attributes
       for node, comm_id in communities.items():
           network.core_network.nodes[node]['community'] = comm_id
       
       # Step 3: Find high-degree nodes in specific community
       result = (
           Q.nodes()
            .where(community=0)  # Filter by community ID
            .compute("degree", "betweenness_centrality")
            .order_by("-degree")
            .limit(10)
            .execute(network)
       )
       
       # Step 4: Export for further analysis
       df = result.to_pandas()
       df.to_csv("community_hubs.csv", index=False)
       
       # Example output:
       #                  id  degree  betweenness_centrality
       #     (Alice, social)       3                   0.667
       #       (Bob, social)       2                   0.000
       #   (Charlie, social)       2                   0.000

   Combine traditional algorithms with DSL queries for powerful workflows!

----

Networks are rarely homogeneous. People cluster into social groups. Proteins form functional modules. Cities organize into regional hubs. **Community detection** finds these natural groupings—but in multilayer networks, the question is more subtle: *do communities exist within layers, across layers, or both?*

This chapter shows you how to detect communities in multilayer networks, how to tune algorithm parameters for your specific domain, and how to interpret results that may differ from single-layer community detection.

Overview
--------

Community detection identifies **groups of nodes** that are more **densely connected** to each other than to the rest of the network. For **multilayer networks**, communities can **span multiple layers**, accounting for both **intra-layer** and **inter-layer** structure.

**Key insight:** A person who is moderately connected across multiple social platforms (layers) may be more central to a cross-platform community than someone who is highly connected on just one platform. Multilayer community detection captures this.

Supported Algorithms
--------------------

py3plex provides **several community detection algorithms**:

* **Louvain** — **Fast modularity optimization** (recommended for most use cases)
* **Infomap** — **Flow-based** community detection (requires external binary)
* **Label Propagation** — **Semi-supervised** approach with known seed communities
* **Multilayer Modularity** — **True multilayer** community detection (Mucha et al. 2010)

----

Louvain Algorithm
-----------------

Basic Usage
~~~~~~~~~~~

**Fastest algorithm** for large networks:

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

* ``resolution=1.0`` - **Standard modularity**
* ``resolution>1.0`` - **More, smaller communities**
* ``resolution<1.0`` - **Fewer, larger communities**

Advantages
~~~~~~~~~~

* **Very fast**: :math:`O(n \log n)`
* **Scales to millions** of nodes
* **BSD license** (commercial-friendly)
* **Well-established** and widely used

Disadvantages
~~~~~~~~~~~~~

* **Non-deterministic** (random initialization)
* **Cannot find overlapping** communities
* **Resolution limit** issues

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

    Q^{ML} = \frac{1}{2\mu} \sum_{ij\alpha\beta} \left[ (A_{ij}^{[\alpha]} - \gamma_{\alpha} P_{ij}^{[\alpha]})\delta_{\alpha\beta} + \omega_{\alpha\beta}\delta_{ij} \right] \delta(g_{i}^{[\alpha]}, g_{j}^{[\beta]})

Where:

* :math:`A_{ij}^{[\alpha]}` is the adjacency matrix of layer :math:`\alpha`
* :math:`P_{ij}^{[\alpha]}` is the null model (e.g., configuration model)
* :math:`\gamma_{\alpha}` is the resolution parameter for layer :math:`\alpha`
* :math:`\omega_{\alpha\beta}` is the coupling strength between layers
* :math:`\delta(g_{i}^{[\alpha]}, g_{j}^{[\beta]})` is 1 if nodes are in the same community, 0 otherwise

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

Understanding Single-Layer vs. Multilayer Community Detection
--------------------------------------------------------------

Before diving into algorithm specifics, it's important to understand the conceptual differences between approaches.

Single-Layer Community Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Traditional community detection finds groups in a single graph. Applied to a multilayer network, you have two options:

1. **Flatten and detect:** Aggregate all layers into one graph, then find communities. This loses layer information.

2. **Detect per layer:** Find communities independently in each layer. This ignores cross-layer structure.

Neither captures the full multilayer picture.

Multilayer Community Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Multilayer algorithms find communities that are consistent across layers while respecting layer-specific structure. They ask: "Which nodes cluster together across multiple contexts?"

**Key insight:** A node that is moderately connected in many layers may be more "community-central" than a node highly connected in just one layer.

Overlapping vs. Non-Overlapping Communities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Non-overlapping:** Each node belongs to exactly one community. Algorithms like Louvain and Leiden produce non-overlapping partitions.

**Overlapping:** Nodes can belong to multiple communities. Algorithms like NoRC and clique percolation find overlapping structure.

*When to use overlapping:* When nodes naturally belong to multiple groups (e.g., a person in both a work community and a hobby community).

Flow-Based vs. Modularity-Based Views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Modularity-based (Louvain, Leiden):** Optimize a quality function that compares edge density within communities to expected density. Fast, widely used, but has resolution limit issues.

**Flow-based (Infomap):** Model random walks on the network and find community structure that minimizes description length of those walks. Theoretically grounded, finds hierarchical structure, but slower.

*When to use which:*

* Use **modularity-based** for speed and when you don't need hierarchical structure
* Use **flow-based** when you care about information flow or want to find nested communities

Parameter Tuning Cookbook
--------------------------

Tuning Resolution (Gamma)
~~~~~~~~~~~~~~~~~~~~~~~~~~

The resolution parameter γ controls community size:

.. code-block:: python

    from py3plex.algorithms.community_detection.multilayer_modularity import (
        louvain_multilayer
    )
    
    # Experiment with different resolution values
    for gamma in [0.5, 1.0, 1.5, 2.0]:
        partition = louvain_multilayer(network, gamma=gamma, omega=1.0, random_state=42)
        num_comms = len(set(partition.values()))
        print(f"gamma={gamma}: {num_comms} communities")

**Interpretation guide:**

* **Very few communities (2-5) when you expect more:** γ is too low → increase γ
* **Many singleton communities:** γ is too high → decrease γ  
* **One giant community + many tiny ones:** Resolution limit problem → try γ > 1 or use Leiden

**Recommended starting procedure:**

1. Start with γ=1.0 (standard modularity)
2. Look at community size distribution
3. If too coarse, try γ=1.5, 2.0
4. If too fine, try γ=0.5, 0.25

Tuning Inter-Layer Coupling (Omega)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The coupling parameter ω controls how much layers influence each other:

.. code-block:: python

    # Experiment with different coupling values
    for omega in [0.1, 0.5, 1.0, 2.0, 5.0]:
        partition = louvain_multilayer(network, gamma=1.0, omega=omega, random_state=42)
        num_comms = len(set(partition.values()))
        
        # Check cross-layer consistency
        # (how often does the same node get same community across layers?)
        # ... (compute consistency metric)
        print(f"omega={omega}: {num_comms} communities")

**Interpretation guide:**

* **ω = 0:** Layers are independent (equivalent to detecting per-layer, then combining)
* **ω = 1:** Balanced coupling (default, usually good)
* **ω > 1:** Strong coupling (forces cross-layer consistency)
* **ω → ∞:** All layers must have identical community structure

**Domain-specific guidance:**

* **Multiplex social networks:** Start with ω=1.0 (people are the same across platforms)
* **Temporal networks:** ω=0.5 to 1.0 (communities can evolve but not too fast)
* **Heterogeneous networks:** ω=0.1 to 0.5 (different node types may have different community structure)

Diagnosing Bad Partitions
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem: All nodes in one community**

.. code-block:: python

    if len(set(partition.values())) == 1:
        print("All nodes in single community - try increasing gamma")

*Causes:* Network is too dense, γ too low, or network genuinely has no community structure.

**Problem: Each node is its own community**

.. code-block:: python

    if len(set(partition.values())) == len(partition):
        print("All singletons - try decreasing gamma or increasing omega")

*Causes:* Network is too sparse, γ too high, ω too low.

**Problem: Communities don't match domain expectations**

*Actions:*

1. Visualize communities and examine specific nodes
2. Check if high-degree nodes are correctly assigned
3. Verify that known groups (e.g., departments) are recovered
4. Consider using ground-truth labels for NMI comparison

Mini Case Studies
-----------------

Case Study 1: Biological Network Communities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Scenario:** A protein-protein interaction network with 3 layers representing different experimental evidence types (yeast two-hybrid, co-immunoprecipitation, affinity purification).

**Goal:** Find functional modules (groups of proteins with shared biological function).

**Approach:**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.multilayer_modularity import (
        louvain_multilayer
    )
    
    # Load network
    network = multinet.multi_layer_network().load_network(
        "ppi_multilayer.txt", input_type="multiedgelist", directed=False
    )
    
    # Use moderate coupling - different evidence types should 
    # contribute to same modules, but we don't require perfect consistency
    partition = louvain_multilayer(
        network, 
        gamma=1.0,     # Standard resolution
        omega=0.5,     # Moderate coupling
        random_state=42
    )
    
    # Validate: Do communities correspond to GO biological process terms?
    # Compare community assignments to known functional annotations

**Expected outcome:** Communities should correspond to functional modules like "cell cycle," "DNA repair," "metabolic pathways." Proteins appearing in multiple layers with high connectivity should be community hubs.

Case Study 2: Transportation Network Communities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Scenario:** A multi-modal transportation network with layers for metro, bus, and bike-share in a city.

**Goal:** Find "travel basins"—regions where people travel together within a mode and switch between modes at hubs.

**Approach:**

.. code-block:: python

    # Load network
    network = multinet.multi_layer_network().load_network(
        "transport_network.txt", input_type="multiedgelist", directed=False
    )
    
    # Higher coupling - the same station serves multiple modes
    partition = louvain_multilayer(
        network,
        gamma=1.2,     # Slightly higher to find smaller regions
        omega=1.5,     # Strong coupling at multimodal hubs
        random_state=42
    )
    
    # Validate: Do communities correspond to geographic regions?
    # Are major transfer stations correctly identified as community boundaries?

**Expected outcome:** Communities should correspond to neighborhoods or districts. Multimodal hubs (stations serving metro + bus + bike) should appear at community boundaries or as bridges between communities.

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

1. **Visual inspection** — Plot and examine communities
2. **Modularity** — Check modularity score (>0.3 is good)
3. **Size distribution** — Check for giant communities or singletons
4. **Domain knowledge** — Do communities make sense for your application?
5. **Ground truth comparison** — If you have labels, compute NMI or Adjusted Rand Index

Common Failure Modes
~~~~~~~~~~~~~~~~~~~~~

* **Trivial partitions:** All-in-one or all-singletons → tune γ and ω
* **Unstable results:** Different runs give very different partitions → use ``random_state`` and run multiple times
* **Over-fragmentation:** Too many small communities → decrease γ or try Leiden
* **Resolution limit:** Can't find small communities in large networks → increase γ or use hierarchical methods

What You Learned
----------------

This chapter covered community detection in multilayer networks:

**Algorithms:**

- **Louvain** — Fast, O(n log n), BSD license, good for most use cases
- **Infomap** — Flow-based, finds hierarchical structure, AGPLv3 license
- **Label Propagation** — Very fast, linear in edges, supports semi-supervised detection
- **Multilayer Modularity** — True multilayer detection with inter-layer coupling

**Parameter tuning:**

- **Resolution γ** — Higher = more, smaller communities; lower = fewer, larger
- **Coupling ω** — Higher = cross-layer consistency; lower = layer-specific structure
- Start with γ=1.0, ω=1.0 and adjust based on results

**Interpretation:**

- Trivial partitions (all-in-one or all-singletons) indicate parameter tuning needed
- High modularity (>0.3) suggests good community structure
- Validate with visualization, domain knowledge, and ground truth if available

**Conceptual differences:**

- Single-layer detection treats node-layer pairs independently
- Multilayer detection finds communities consistent across layers
- Overlapping vs. non-overlapping communities serve different use cases

References
----------

**Louvain:**

Blondel, V. D., et al. (2008). Fast unfolding of communities in large networks. *Journal of Statistical Mechanics*.

**Infomap:**

Rosvall, M., & Bergstrom, C. T. (2008). Maps of random walks on complex networks reveal community structure. *PNAS*, 105(4), 1118-1123.

**Multilayer Modularity:**

Mucha, P. J., et al. (2010). Community structure in time-dependent, multiscale, and multiplex networks. *Science*, 328(5980), 876-878.

See :doc:`../reference/citation_and_acknowledgements` for complete citations with DOIs.

What's Next?
------------

* :doc:`random_walks_embeddings` — Generate embeddings for ML tasks
* :doc:`visualization` — Visualize communities with color-coding
* :doc:`../concepts/algorithm_landscape` — Overview of all algorithms

**Related Examples:**

* ``examples/communities/example_community_detection.py`` — Complete workflow
* ``examples/communities/example_multilayer_louvain.py`` — Parameter tuning
