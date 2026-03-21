.. _algorithms-chapter:

Core Algorithms: Communities, Centrality, Dynamics
=============================================================

This chapter covers py3plex's three major algorithm families for multilayer network analysis: community detection, centrality measures, and dynamics/spreading processes. It also states assumptions and caveats so results are interpreted within method limits.

.. admonition:: DSL Tip: Streamline Algorithm Workflows
   :class: dsl-info

   The DSL simplifies many algorithmic workflows:

   .. code-block:: python

       from py3plex.dsl import Q, L

       # Quick centrality analysis
       top_central = (
           Q.nodes()
            .from_layers(L["social"])
            .compute("betweenness_centrality", "pagerank", "degree")
            .order_by("-betweenness_centrality")
            .limit(20)
            .execute(network)
       )

       # Multilayer comparison
       for layer in ["social", "work"]:
           result = (
               Q.nodes()
                .from_layers(L[layer])
                .compute("betweenness_centrality")
                .execute(network)
           )
           print(f"{layer}: avg BC = {sum(result.measures['betweenness_centrality'].values()) / result.count:.4f}")

   See :ref:`dsl-chapter` for comprehensive DSL coverage!

Overview
--------

py3plex provides three major algorithm families for analyzing multilayer networks:

1. **Community Detection** — Find groups of nodes that are densely connected within and across layers. Algorithms include Louvain, Infomap, Label Propagation, and multilayer modularity optimization.

2. **Centrality Measures** — Identify important nodes using degree, betweenness, closeness, PageRank, eigenvector centrality, and 30+ other measures adapted for multilayer structure.

3. **Dynamics and Processes** — Simulate epidemic spread (SIR, SIS), random walks, and diffusion processes that leverage multilayer connectivity patterns.

These algorithms can account for both intra-layer (within-layer) and inter-layer (cross-layer) connections, but this depends on the selected method and representation.

Assumptions and Caveats
-----------------------

Before applying any algorithm in this chapter, check the following:

1. **Graph representation:** some workflows operate on a supra-graph approximation rather than a solver with explicit multilayer coupling terms.
2. **Metric cost:** global path-based metrics (especially betweenness) can become impractical on large graphs.
3. **Model fit:** epidemic and diffusion models are stylized abstractions; parameter sensitivity should be explored, not assumed away.
4. **Result transferability:** conclusions from one layer configuration or one seed do not automatically generalize.

Community Detection
-------------------

Community detection identifies groups of nodes that are more densely connected to each other than to the rest of the network. In multilayer networks, communities can span multiple layers, accounting for both intra-layer and inter-layer structure.

Multilayer Modularity
~~~~~~~~~~~~~~~~~~~~~

The multilayer modularity quality function extends Newman-Girvan modularity to account for both intra-layer and inter-layer edges:

.. math::

   Q = \frac{1}{2\mu} \sum_{ijrs} \left[ A_{ijr} - \gamma_r \frac{k_{ir} k_{jr}}{2m_r} \right] \delta(g_i, g_j) \delta_{rs} 
       + \frac{1}{2\mu} \sum_{ijrs} C_{ijrs} \delta(g_i, g_j)

Where:

- :math:`A_{ijr}` is the adjacency matrix in layer *r*
- :math:`k_{ir}` is the degree of node *i* in layer *r*
- :math:`\gamma_r` is the resolution parameter for layer *r*
- :math:`C_{ijrs}` represents inter-layer coupling
- :math:`\delta(g_i, g_j)` is 1 if nodes *i* and *j* are in the same community

**Implementation:**

.. code-block:: python

    from py3plex.algorithms.community_detection import community_louvain
    
    # Detect communities using Louvain on the supra-graph representation
    # Note: This applies standard Louvain to the flattened multilayer structure
    communities = community_louvain.best_partition(network.core_network)
    
    # Print community assignments
    for node, comm_id in communities.items():
        print(f"Node {node} -> Community {comm_id}")

.. admonition:: Implementation Note
   :class: note

   The implementation shown applies standard Louvain modularity optimization to the **supra-graph representation** of the multilayer network (``network.core_network``), where all layers are combined into a single NetworkX MultiGraph. This is a practical approximation that works well for many use cases.
   
   **True multilayer modularity optimization** (Mucha et al. 2010) with explicit inter-layer coupling terms requires specialized solvers. For such optimization, consider using external tools like GenLouvain (MATLAB) or multilayer-specific implementations, then importing results back into py3plex.

Algorithms Available
~~~~~~~~~~~~~~~~~~~~

py3plex supports several community detection algorithms. See ``examples/network_analysis/`` for complete examples:

**Example 1: Single-Layer Louvain**

See ``examples/network_analysis/example_community_detection.py``:

.. code-block:: bash

    # Using uv
    uv run examples/network_analysis/example_community_detection.py
    
    # Or using python
    python examples/network_analysis/example_community_detection.py

**Example 2: Multilayer Detection**

See ``examples/network_analysis/example_multiplex_community_detection.py``:

.. code-block:: bash

    # Using uv
    uv run examples/network_analysis/example_multiplex_community_detection.py
    
    # Or using python
    python examples/network_analysis/example_multiplex_community_detection.py

**Example 3: AutoCommunity Detection**

See ``examples/network_analysis/example_auto_select_basic.py``:

.. code-block:: bash

    # Using uv
    uv run examples/network_analysis/example_auto_select_basic.py
    
    # Or using python
    python examples/network_analysis/example_auto_select_basic.py

**Available algorithms:**

- **Louvain** — Fast modularity optimization, O(n log n). Best for most use cases (100-100K nodes).
- **Infomap** — Flow-based detection using random walk dynamics. Optional dependency (see below).
- **Label Propagation** — Semi-supervised approach with known seed communities. Linear time O(m + n).

Infomap Integration
~~~~~~~~~~~~~~~~~~~

Infomap is an optional community detection algorithm based on information-theoretic compression of random walks. It is not included in the default py3plex installation due to licensing (AGPL).

**Installation:**

.. code-block:: bash

    pip install py3plex[infomap]

**Usage:**

.. code-block:: python

    from py3plex.algorithms.community_detection import infomap_communities
    
    # Run Infomap on network
    communities = infomap_communities(network.core_network)
    
    # communities is a dict: {node: community_id}

**Important notes:**

* Infomap is licensed under AGPLv3 (copyleft license) - see :ref:`installation-chapter` for license implications
* If you don't need Infomap specifically, use Louvain or Label Propagation instead
* Infomap tends to find smaller, more fine-grained communities than Louvain

**Time Complexity Summary:**

- Louvain: O(n log n) typical, O(n²) worst case
- Label Propagation: O(m + n) per iteration
- Infomap: O(m log n) typical

Choosing a Community Detection Method
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Selection guidelines:**

- **Network size < 10,000 nodes:** Use Louvain (fast and accurate)
- **Network size > 100,000 nodes:** Use Label Propagation (linear time) or streaming Louvain
- **Strong inter-layer coupling:** Use multilayer modularity for true cross-layer communities
- **Known seed communities:** Use Label Propagation with seeds
- **Flow-based interpretation needed:** Use Infomap (installation required)

**Interpretability considerations:**

- Louvain and multilayer modularity produce hierarchical community structure
- Infomap optimizes for information compression, emphasizing flow patterns
- Label Propagation is less deterministic but handles semi-supervised scenarios

Centrality Measures
-------------------

Centrality measures identify important nodes in the network. py3plex provides direct DSL access to core centrality measures (degree, betweenness, closeness, eigenvector, PageRank, clustering) and seamless integration with NetworkX's 30+ additional centrality algorithms.

**DSL-integrated measures (available via ``Q.nodes().compute()``)**:

* ``degree`` — Node degree (number of edges)
* ``degree_centrality`` — Normalized degree centrality
* ``betweenness_centrality`` — Betweenness centrality (Brandes algorithm)
* ``closeness_centrality`` — Closeness centrality
* ``eigenvector_centrality`` — Eigenvector centrality
* ``pagerank`` — PageRank centrality
* ``clustering`` — Local clustering coefficient
* ``communities`` — Community detection (Louvain)

**Additional measures via NetworkX** (use ``network.core_network`` with any ``nx.*_centrality`` function):

* **Katz centrality** — Weighted count of walks (influence via connections)
* **Load centrality** — Traffic load through each node
* **Harmonic centrality** — Average inverse distance to all nodes
* **Current flow betweenness** — Betweenness based on electrical current flow
* **Percolation centrality** — Importance during network cascades
* **Subgraph centrality** — Based on counting closed walks
* And 24+ more available in NetworkX

See NetworkX documentation at https://networkx.org/documentation/stable/reference/algorithms/centrality.html and :ref:`appendix-e` for complete API reference.

Multilayer PageRank
~~~~~~~~~~~~~~~~~~~

PageRank extends to multilayer networks by defining random walks that can jump between layers:

.. math::

   \pi_i^r = (1-d) \frac{1}{N \cdot L} + d \sum_{j,s} \frac{A_{ji}^{rs}}{k_j^s} \pi_j^s

Where :math:`\pi_i^r` is the PageRank of node *i* in layer *r*, *d* is the damping factor (typically 0.85), and :math:`A_{ji}^{rs}` accounts for both intra-layer and inter-layer edges.

**Usage:**

.. code-block:: python

    from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality
    
    calc = MultilayerCentrality(network)
    pagerank_scores = calc.compute_pagerank(alpha=0.85)

Degree Centrality
~~~~~~~~~~~~~~~~~

In multilayer networks, degree centrality distinguishes between:

- **Intra-layer degree:** Number of connections within a single layer
- **Inter-layer degree:** Number of connections to other layers
- **Supra-degree:** Total degree across all layers
- **Overlapping degree:** Node-level aggregation ignoring layer distinctions

The **participation coefficient** measures how evenly a node's connections are distributed across layers:

.. math::

   P_i = \frac{L}{L-1} \left(1 - \sum_{r=1}^L \left(\frac{k_i^r}{k_i}\right)^2\right)

Where :math:`k_i^r` is degree in layer *r* and :math:`k_i` is total degree. Values near 1 indicate even distribution (hub-like behavior), values near 0 indicate concentration in one layer.

Betweenness Centrality
~~~~~~~~~~~~~~~~~~~~~~~

Multilayer betweenness counts shortest paths through the supra-adjacency graph:

.. math::

   BC(i,r) = \sum_{s \neq i,r \neq t,l} \frac{\sigma_{(s,k),(t,l)}(i,r)}{\sigma_{(s,k),(t,l)}}

Where :math:`\sigma_{(s,k),(t,l)}` is the number of shortest paths from node-layer *(s,k)* to *(t,l)*, and :math:`\sigma_{(s,k),(t,l)}(i,r)` counts paths passing through *(i,r)*.

**Time complexity:** O(n³) for dense networks, O(nm) for sparse networks using Brandes' algorithm.

Explainable Centrality
~~~~~~~~~~~~~~~~~~~~~~

Explainable centrality decomposes a node's centrality score by layer contribution, revealing which layers drive importance:

.. code-block:: python

    from py3plex.algorithms.centrality.explain import explain_node_centrality
    
    # Get layer-wise breakdown of degree centrality
    explanation = explain_node_centrality(network, 'Alice', measure='degree')
    
    # Output:
    # Layer 'social': degree = 12 (60%)
    # Layer 'work':   degree = 8  (40%)
    # Total degree:   20

This helps answer: "Is Alice influential because of social connections, work connections, or both?"

Dynamics and Processes
-----------------------

py3plex provides comprehensive support for simulating dynamical processes on multilayer networks, including epidemic models and random walks.

**For complete documentation**, see the user guide section on multilayer dynamics and the SIR epidemic simulator documentation.

Random Walks
~~~~~~~~~~~~

Random walks simulate exploration and diffusion on networks:

.. code-block:: python

    from py3plex.dynamics import RandomWalkDynamics
    
    # Create random walk
    walk = RandomWalkDynamics(network, start_node=0, lazy_probability=0.1)
    walk.set_seed(42)
    results = walk.run(steps=1000)
    
    # Analyze trajectory
    trajectory = results.get_measure("trajectory")

Random walks are fundamental to PageRank, community detection, and network embeddings (Node2Vec, DeepWalk).

Epidemic Models
~~~~~~~~~~~~~~~

Simulate disease spread and information diffusion with SIR and SIS models:

.. code-block:: python

    from py3plex.dynamics import SIRDynamics, SISDynamics
    
    # SIR: Susceptible-Infected-Recovered (with immunity)
    sir = SIRDynamics(network, beta=0.3, gamma=0.1, initial_infected=0.1)
    sir.set_seed(42)
    results = sir.run(steps=100)
    
    # Extract measures
    prevalence = results.get_measure("prevalence")
    state_counts = results.get_measure("state_counts")
    
    print(f"Peak prevalence: {prevalence.max():.2%}")
    print(f"Final recovered: {state_counts['R'][-1]}")

**Key parameters:**

- :math:`\beta \in (0, 1)`: Transmission probability per contact (infection probability per contact)
- :math:`\gamma \in (0, 1)`: Recovery probability per time step
- :math:`R_0 = \frac{\beta}{\gamma} \langle k \rangle`: Basic reproduction number for homogeneous networks, with epidemic threshold at :math:`R_0 = 1`

**Models:**

- **SIR** — Epidemic with immunity (measles, chickenpox). Always dies out eventually.
- **SIS** — Endemic disease without immunity (common cold, malware). Reaches stable equilibrium.

Multilayer Dynamics
~~~~~~~~~~~~~~~~~~~

Infection spreads through multiple interaction channels:

.. code-block:: python

    # Two-layer network: physical + digital contacts
    network = multinet.multi_layer_network(directed=False)
    
    # Add physical layer (local connections)
    # Add digital layer (global connections)
    
    # Run dynamics
    sir = SIRDynamics(network, beta=0.3, gamma=0.1)
    results = sir.run(steps=100)

The multilayer structure allows simultaneous spread through different contexts, often leading to faster and more extensive diffusion than single-layer networks.

Algorithm Complexity and Scaling
---------------------------------

**Performance characteristics:**

.. list-table:: Algorithm Complexity Summary
   :header-rows: 1
   :widths: 30 20 20 30

   * - Algorithm
     - Time Complexity
     - Memory
     - Scales to
   * - Louvain
     - O(n log n)
     - O(n + m)
     - 100K nodes
   * - Label Propagation
     - O(m + n)
     - O(n)
     - 1M+ nodes
   * - Degree Centrality
     - O(n + m)
     - O(n)
     - 10M+ nodes
   * - Betweenness Centrality
     - O(nm)
     - O(n²)
     - 10K nodes
   * - PageRank
     - O(m) per iteration
     - O(n)
     - 1M+ nodes
   * - SIR Dynamics
     - O(t·m)
     - O(n)
     - 100K nodes

**When to use each family:**

- **Community detection:** When you need to understand group structure and identify functional modules. Use early in exploratory analysis.

- **Centrality measures:** When identifying key nodes for targeting, removal, or intervention strategies. Fast for large networks if using degree-based measures.

- **Dynamics:** When modeling spreading processes, cascades, or temporal evolution. Essential for epidemiology, information diffusion, and failure analysis.

**Memory considerations:**

- Betweenness centrality requires O(n²) memory for path counting; use sampling for networks > 10K nodes
- PageRank and degree-based measures scale well with sparse matrices
- Dynamics simulations require O(n) memory per time step if storing full state history

Summary
-------

This chapter introduced three core algorithm families for multilayer network analysis:

1. **Community detection** reveals group structure using modularity optimization (Louvain), flow-based methods (Infomap), or label propagation. Choose based on network size and interpretability needs.

2. **Centrality measures** identify important nodes using degree, paths, random walks, or eigenvector-based approaches. Multilayer variants account for cross-layer influence.

3. **Dynamics and processes** simulate epidemic spread, diffusion, and random walks on multilayer networks, capturing how layer structure affects spreading patterns.

All algorithms integrate with the py3plex DSL for concise, expressive workflows. The next chapter introduces the DSL and shows how to chain queries for complex analyses.

Uncertainty Quantification
--------------------------

Py3plex provides tools for quantifying uncertainty in network analysis through bootstrap sampling and null model comparisons. See ``examples/network_analysis/`` for complete examples.

**Example 1: UQ-Enabled Centrality**

See ``examples/network_analysis/example_dsl_uq_ergonomics.py``:

.. code-block:: bash

    # Using uv
    uv run examples/network_analysis/example_dsl_uq_ergonomics.py
    
    # Or using python
    python examples/network_analysis/example_dsl_uq_ergonomics.py

**Example 2: Bootstrap Sampling**

See ``examples/network_analysis/example_dsl_uncertainty_bootstrap_nullmodel.py``:

.. code-block:: bash

    # Using uv
    uv run examples/network_analysis/example_dsl_uncertainty_bootstrap_nullmodel.py
    
    # Or using python
    python examples/network_analysis/example_dsl_uncertainty_bootstrap_nullmodel.py

**Example 3: UQ vs Deterministic Comparison**

See ``examples/network_analysis/example_selection_uq_topk.py``:

.. code-block:: bash

    # Using uv
    uv run examples/network_analysis/example_selection_uq_topk.py
    
    # Or using python
    python examples/network_analysis/example_selection_uq_topk.py

These tools help assess sensitivity and uncertainty in observed network metrics; they do not by themselves establish causal claims.

.. seealso::

   **Further Reading:**
   
   - Community detection details: ``docfiles/user_guide/community_detection.rst``
   - Centrality implementations: ``docfiles/tutorials/multilayer_centrality.rst``
   - Dynamics API: ``docfiles/sir_epidemic_simulator.rst``
   - Algorithm reference: ``docfiles/algorithm_guide.rst``
