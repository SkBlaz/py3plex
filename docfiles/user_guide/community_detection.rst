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
* **Leiden** — **Improved modularity optimization** with better guarantees
* **Infomap** — **Flow-based** community detection (requires external binary)
* **Label Propagation** — **Semi-supervised** approach with known seed communities
* **Multilayer Modularity** — **True multilayer** community detection (Mucha et al. 2010)
* **SBM (Stochastic Block Model)** — **Model-based** approach with automatic model selection
* **DC-SBM (Degree-Corrected SBM)** — **Default SBM variant** that accounts for degree heterogeneity

Model-Based vs. Objective-Based Algorithms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Objective-based algorithms** (Louvain, Leiden, Infomap) optimize a quality function like modularity or code length:

* **Pros**: Fast, scalable, work well on most networks
* **Cons**: Number of communities not specified a priori, can be sensitive to resolution

**Model-based algorithms** (SBM, DC-SBM) fit a generative model to the network:

* **Pros**: Principled model selection (automatic K), uncertainty quantification, handles degree heterogeneity (DC-SBM)
* **Cons**: Computationally more expensive, requires careful parameter tuning
* **When to use**: When you need to select the number of communities automatically, when degree distributions vary widely, or when you need rigorous statistical inference

**Rule of thumb**: Use **Louvain/Leiden** for exploratory analysis and large networks. Use **DC-SBM** when you need automatic model selection or degree-corrected communities.

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


Stochastic Block Model (SBM)
-----------------------------

Model-Based Community Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Stochastic Block Model (SBM)** is a **generative model** for community structure. Unlike objective-based algorithms (Louvain, Leiden), SBM explicitly models the probability of edges based on community memberships.

**Standard SBM:**

.. math::

   P(A_{ij}=1 \mid z_i, z_j) = \theta_{z_i z_j}

**Degree-Corrected SBM (DC-SBM)** — **Recommended default:**

.. math::

   P(A_{ij}=1 \mid z_i, z_j) = \theta_i \theta_j \omega_{z_i z_j}

DC-SBM accounts for **degree heterogeneity** (nodes with widely varying degrees), making it more realistic for many real-world networks.

Why Use SBM?
~~~~~~~~~~~~

**Use SBM when you need:**

1. **Automatic model selection** — Selects number of communities (K) via MDL/BIC
2. **Degree-corrected communities** — Handles hubs and low-degree nodes appropriately
3. **Statistical inference** — Principled likelihood-based approach
4. **Uncertainty quantification** — Natural support for bootstrap and perturbation UQ

**Don't use SBM when:**

- Network is very large (>10K nodes) — Use Louvain/Leiden instead
- You already know the number of communities
- Speed is critical — SBM is slower than modularity-based methods

Basic Usage (with AutoCommunity)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Recommended**: Use via AutoCommunity runner for automatic budget management:

.. code-block:: python

    from py3plex.algorithms.community_detection import AutoCommunity
    from py3plex.algorithms.community_detection.budget import BudgetSpec
    from py3plex.algorithms.community_detection.runner import run_community_algorithm
    from py3plex.core import multinet
    
    # Load network
    net = multinet.multi_layer_network(directed=False)
    net.load_network("network.csv", input_type="edgelist")
    
    # Run DC-SBM with AutoCommunity
    result = (
        AutoCommunity()
          .candidates("louvain", "dc_sbm")
          .metrics("modularity", "sbm_log_likelihood")
          .seed(42)
          .execute(net)
    )
    
    print(f"Selected: {result.selected}")
    print(f"Communities: {result.community_stats.n_communities}")

Direct Usage
~~~~~~~~~~~~

**For advanced users**: Call runner directly with explicit budget:

.. code-block:: python

    from py3plex.algorithms.community_detection.runner import run_community_algorithm
    from py3plex.algorithms.community_detection.budget import BudgetSpec
    
    # Define budget
    budget = BudgetSpec(
        max_iter=100,      # EM iterations
        n_restarts=5,      # Random initializations
        uq_samples=None    # No UQ (single run)
    )
    
    # Run DC-SBM
    result = run_community_algorithm(
        algorithm_id="dc_sbm",
        network=net,
        budget=budget,
        seed=42,
        K_range=[2, 3, 4, 5, 6, 7, 8]  # Model selection range
    )
    
    # Access results
    partition = result.partition
    K_selected = result.meta["K_selected"]
    log_likelihood = result.meta["log_likelihood"]
    mdl = result.meta["mdl"]  # Lower is better
    
    print(f"Selected K={K_selected} with MDL={mdl:.2f}")

Model Selection
~~~~~~~~~~~~~~~

SBM automatically selects the number of communities (K) using **Minimum Description Length (MDL)**:

.. code-block:: python

    # Specify K range for model selection
    result = run_community_algorithm(
        algorithm_id="dc_sbm",
        network=net,
        budget=BudgetSpec(max_iter=100, n_restarts=3),
        seed=42,
        K_range=[2, 3, 4, 5, 6, 7, 8]  # Try these K values
    )
    
    # Best K is selected automatically
    print(f"Selected K: {result.meta['K_selected']}")
    print(f"MDL score: {result.meta['mdl']:.2f}")  # Lower = better

**Model selection criteria:**

- **ELBO** (Evidence Lower Bound) — Maximize (higher is better)
- **MDL/BIC** (Minimum Description Length) — Minimize (lower is better)
- **ICL** (Integrated Classification Likelihood) — Minimize, penalizes fuzzy assignments

Uncertainty Quantification
~~~~~~~~~~~~~~~~~~~~~~~~~~

Enable UQ via ``uq_samples`` in budget:

.. code-block:: python

    # Run with uncertainty quantification
    budget_uq = BudgetSpec(
        max_iter=50,
        n_restarts=2,
        uq_samples=20  # 20 bootstrap samples
    )
    
    result = run_community_algorithm(
        algorithm_id="dc_sbm",
        network=net,
        budget=budget_uq,
        seed=42,
        K_range=[2, 3, 4, 5]
    )
    
    # Access uncertainty metrics
    ll_mean = result.meta["log_likelihood"]
    ll_std = result.meta["log_likelihood_std"]
    
    print(f"Log-likelihood: {ll_mean:.2f} ± {ll_std:.2f}")

Multilayer Networks
~~~~~~~~~~~~~~~~~~~

DC-SBM supports **shared-membership multilayer networks** where nodes have one community assignment across all layers:

.. code-block:: python

    # Create multilayer network
    net = multinet.multi_layer_network(directed=False)
    
    # Add edges in multiple layers
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'A', 'target': 'C', 'source_type': 'work', 'target_type': 'work'},
    ])
    
    # Run DC-SBM (automatically handles multilayer)
    result = run_community_algorithm(
        algorithm_id="dc_sbm",
        network=net,
        budget=BudgetSpec(max_iter=100, n_restarts=3),
        seed=42,
        K_range=[2, 3, 4]
    )
    
    # Partition is across all layers
    print(result.partition)

**Note**: All layers must be **node-aligned** (same set of nodes across layers).

Successive Halving with SBM
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SBM works with **Successive Halving** for efficient model selection:

.. code-block:: python

    result = (
        AutoCommunity()
          .candidates("louvain", "leiden", "dc_sbm")
          .metrics("modularity", "sbm_log_likelihood")
          .strategy(
              "successive_halving",
              eta=3,
              budget0={"max_iter": 10, "n_restarts": 1},
              utility_method="mean_minus_std"
          )
          .seed(42)
          .execute(net)
    )

**Budget scaling** for SBM across Successive Halving rounds:

- **Round 0**: ``max_iter=10, n_restarts=1, K_range=[2,3,4]``
- **Round 1**: ``max_iter=30, n_restarts=3, K_range=[2,3,4,5,6]``
- **Round 2**: ``max_iter=90, n_restarts=9, K_range=[2,3,4,5,6,7,8]``

Advantages
~~~~~~~~~~

* **Automatic K selection** via MDL
* **Degree-corrected** (handles heterogeneous degrees)
* **Principled statistical model**
* **Uncertainty quantification**
* **Multilayer support**
* **Deterministic** (given seed)

Disadvantages
~~~~~~~~~~~~~

* **Slower** than modularity-based methods
* **Requires node-aligned multilayer networks**
* **More parameters** to tune (max_iter, n_restarts)
* **Not suitable for very large networks** (>10K nodes)

Performance Recommendations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

For **small networks** (<100 nodes):

.. code-block:: python

    BudgetSpec(max_iter=200, n_restarts=10)

For **medium networks** (100-1000 nodes):

.. code-block:: python

    BudgetSpec(max_iter=100, n_restarts=5)

For **large networks** (1000-10000 nodes):

.. code-block:: python

    BudgetSpec(max_iter=50, n_restarts=2)

For **very large networks** (>10000 nodes):

Use Louvain/Leiden instead, or use SBM with small K_range and conservative budgets.

SBM Metrics
~~~~~~~~~~~

SBM provides specialized metrics for AutoCommunity:

* ``sbm_log_likelihood`` — Higher is better (maximize)
* ``sbm_mdl`` — Lower is better (minimize), MDL/BIC criterion
* ``sbm_n_blocks`` — Number of blocks selected

Use these in AutoCommunity for model comparison:

.. code-block:: python

    result = (
        AutoCommunity()
          .candidates("dc_sbm", "louvain")
          .metrics("modularity", "sbm_log_likelihood", "sbm_mdl")
          .seed(42)
          .execute(net)
    )

**Note**: SBM metrics only apply to SBM/DC-SBM algorithms. Other algorithms will have ``None`` values for these metrics.


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

----

Distributional Community Detection (New in v1.1)
-------------------------------------------------

**Uncertainty-aware community detection** via distributional partitions.

Traditional community detection returns a single partition. But what if the structure is uncertain? **Distributional community detection** runs the algorithm multiple times (with different seeds or on perturbed networks) to produce a **distribution over partitions**.

This enables:

- **Co-association matrices**: P(node_i and node_j in same community)
- **Consensus partitions**: Representative partition (medoid)
- **Node confidence scores**: Per-node stability measures
- **Boundary node identification**: Nodes with uncertain assignments

Basic Usage
~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection import multilayer_louvain_distribution
    
    # Load network
    net = multinet.multi_layer_network(directed=False)
    net.load_network("data.edgelist", directed=False, input_type="edgelist_hash")
    
    # Run distributional community detection
    dist = multilayer_louvain_distribution(
        net,
        n_runs=100,
        resampling='perturbation',
        perturbation_params={'edge_drop_p': 0.05},
        seed=42,
        n_jobs=4
    )
    
    # Get consensus partition
    consensus = dist.consensus_partition()
    
    # Get per-node confidence scores
    confidence = dist.node_confidence()
    
    # Identify stable vs boundary nodes
    stable_mask = confidence >= 0.8
    stable_nodes = [dist.nodes[i] for i in range(dist.n_nodes) if stable_mask[i]]
    
    print(f"Communities: {len(set(consensus))}")
    print(f"Stable core: {len(stable_nodes)}/{dist.n_nodes} nodes")

Resampling Strategies
~~~~~~~~~~~~~~~~~~~~~

**Seed-only** (``resampling='seed'``):
  Run algorithm multiple times with different random seeds. **Fastest**, captures algorithm stochasticity.

**Perturbation** (``resampling='perturbation'``):
  Randomly drop edges before each run (e.g., ``edge_drop_p=0.05``). **Assesses structural uncertainty**.

**Bootstrap** (``resampling='bootstrap'``):
  Resample edges with replacement. **Statistical bootstrap** for formal inference.

Best Practices
~~~~~~~~~~~~~~

1. Use ``coassoc_mode='auto'`` for large networks (sparse for n_nodes > 2000)
2. Always set seed for reproducibility
3. Use ``resampling='seed'`` as default (fastest)
4. Use ``weight_by='modularity'`` to weight better partitions more heavily

See ``examples/communities/example_distributional_community_detection.py`` for complete example.

----

Successive Halving for Algorithm Selection
-------------------------------------------

When you don't know which algorithm will work best, **Successive Halving** efficiently races multiple algorithms with increasing computational budgets, eliminating poor performers early.

Overview
~~~~~~~~

Successive Halving is a **racing strategy** that:

1. Starts with all candidate algorithms
2. Evaluates on small budget (e.g., max_iter=5, uq_samples=10)
3. Eliminates worst performers (keeps top 1/η)
4. Increases budget and repeats with survivors
5. Returns winner when one algorithm remains

**Key benefits:**
- **Efficient:** Quickly eliminates poor algorithms
- **UQ-aware:** Uses distribution-based utilities
- **Deterministic:** Fully reproducible with seed
- **Provenance-rich:** Complete racing history

Basic Usage
~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.community_detection import AutoCommunity
    from py3plex.core import multinet
    
    # Load network
    network = multinet.multi_layer_network(directed=False)
    network.load_network("network.csv", input_type="edgelist")
    
    # Run Successive Halving
    result = (
        AutoCommunity()
          .candidates("louvain", "leiden", "label_propagation")
          .metrics("modularity", "coverage")
          .strategy("successive_halving", eta=3, rounds=2)
          .seed(42)
          .execute(network)
    )
    
    # Winner
    print(f"Winner: {result.selected}")
    print(f"Communities: {result.community_stats.n_communities}")

Configuration
~~~~~~~~~~~~~

.. code-block:: python

    # Custom budget and utility function
    result = (
        AutoCommunity()
          .candidates("louvain", "leiden")
          .metrics("modularity", "coverage")
          .strategy(
              "successive_halving",
              eta=3,                     # Keep top 1/3 each round
              rounds=3,                  # Number of rounds
              budget0={                  # Initial budget
                  "max_iter": 10,
                  "n_restarts": 1,
                  "uq_samples": 15,
              },
              budget_growth=3.0,         # Budget scales 3x per round
              utility_method="mean_minus_std",  # Utility function
              metric_weights={           # Custom weights
                  "modularity": 0.6,
                  "coverage": 0.4,
              },
          )
          .seed(42)
          .execute(network)
    )

Racing History
~~~~~~~~~~~~~~

Access complete provenance:

.. code-block:: python

    # Racing summary
    history = result.provenance["racing_history"]
    print(f"Rounds: {len(history['rounds'])}")
    print(f"Winner: {history['winner_algo_id']}")
    print(f"Runtime: {history['total_runtime_ms']:.2f} ms")
    
    # Per-round details
    for i, round_rec in enumerate(history["rounds"]):
        print(f"Round {i}:")
        print(f"  Algorithms: {len(round_rec['algorithms'])}")
        print(f"  Survivors: {round_rec['survivors']}")
        print(f"  Eliminated: {round_rec['eliminated']}")
        
        # Show utilities
        utilities = round_rec["utilities"]
        for algo, utility in utilities.items():
            print(f"    {algo}: {utility:.4f}")

Utility Methods
~~~~~~~~~~~~~~~

**mean_minus_std** (default):
  U = mean(score) - λ * std(score)
  
  Balances expected performance with risk. Higher λ = more conservative.

**expected_regret**:
  U = -E[max(scores) - score]
  
  Minimizes expected loss relative to best.

**prob_near_best**:
  U = P(score ≥ max - ε)
  
  Probability of being near-optimal.

.. code-block:: python

    # Use expected regret utility
    result = (
        AutoCommunity()
          .candidates("louvain", "leiden")
          .metrics("modularity")
          .strategy("successive_halving", utility_method="expected_regret")
          .seed(42)
          .execute(network)
    )

With Uncertainty Quantification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Enable UQ for stability-aware selection:

.. code-block:: python

    result = (
        AutoCommunity()
          .candidates("louvain", "leiden")
          .metrics("modularity", "coverage", "stability")
          .uq(method="seed", n_samples=20)  # Enable UQ
          .strategy("successive_halving", eta=3)
          .seed(42)
          .execute(network)
    )
    
    # Check stability
    stats = result.community_stats
    print(f"Stability: {stats.stability_score:.3f}")

When to Use
~~~~~~~~~~~

**Use Successive Halving when:**

- Testing many algorithms (>5 candidates)
- Computational budget is limited
- Want efficient early elimination
- Clear metric preferences (weighted)

**Use default Pareto strategy when:**

- Few candidates (<5)
- Multi-objective without clear weights
- Want consensus from non-dominated set
- Null model calibration is critical

Best Practices
~~~~~~~~~~~~~~

1. **Start small:** budget0 with max_iter=5, uq_samples=10
2. **Elimination:** eta=3 for aggressive, eta=2 for conservative
3. **UQ:** Enable with uq_samples in budget for stability
4. **Seed:** Always set for reproducibility
5. **Weights:** Encode domain knowledge via metric_weights
6. **History:** Inspect racing_history to understand selection

Complete Example
~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.community_detection import AutoCommunity
    from py3plex.core import multinet
    import json
    
    # 1. Load network
    net = multinet.multi_layer_network(directed=False)
    net.load_network("network.csv", input_type="edgelist")
    
    # 2. Run Successive Halving with UQ
    result = (
        AutoCommunity()
          .candidates("louvain", "leiden", "label_propagation")
          .metrics("modularity", "coverage", "stability")
          .uq(method="seed", n_samples=20)
          .strategy(
              "successive_halving",
              eta=3,
              rounds=2,
              budget0={"max_iter": 10, "uq_samples": 15},
              utility_method="mean_minus_std",
              metric_weights={"modularity": 0.5, "coverage": 0.3, "stability": 0.2},
          )
          .seed(42)
          .execute(net)
    )
    
    # 3. Results
    print(f"Winner: {result.selected}")
    print(f"Communities: {result.community_stats.n_communities}")
    print(f"Coverage: {result.community_stats.coverage:.3f}")
    
    # 4. Export
    df = result.to_pandas()
    df.to_csv("communities.csv", index=False)
    
    # 5. Save provenance
    with open("provenance.json", "w") as f:
        json.dump(result.provenance, f, indent=2)
