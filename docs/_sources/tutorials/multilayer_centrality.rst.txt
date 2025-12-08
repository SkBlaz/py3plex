Multilayer Network Centrality Measures
======================================


This tutorial demonstrates how to compute **various centrality measures** for **multilayer** and **multiplex** networks using py3plex.

Overview
--------


The `py3plex.algorithms.multilayer_algorithms.centrality` module provides **comprehensive implementations** of centrality measures specifically designed for **multilayer networks**. These measures follow **standard definitions** from multilayer network analysis literature.

Supported Centrality Measures
-----------------------------


1. Degree/Strength-based Measures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


* **Layer-specific degree/strength**: Centrality computed **within individual layers**
* **Supra degree/strength**: Centrality on the **full supra-adjacency matrix**
* **Overlapping degree/strength**: **Node-level aggregation** across all layers
* **Participation coefficient**: Measures how **evenly** a node's connections are distributed across layers

2. Eigenvector-type Measures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


* **Multiplex eigenvector centrality**: **Principal eigenvector** of the supra-adjacency matrix
* **Eigenvector versatility**: **Node-level aggregation** of eigenvector centrality
* **Katz-Bonacich centrality**: **Weighted sum of walks** on the supra-graph
* **PageRank centrality**: **Random walk** centrality on the supra-graph

3. Path-based Measures
~~~~~~~~~~~~~~~~~~~~~~


* **Multilayer closeness centrality**: Based on **shortest paths** in the supra-graph
* **Multilayer betweenness centrality**: Fraction of **shortest paths** passing through each node-layer

4. Advanced Measures
~~~~~~~~~~~~~~~~~~~~


* **HITS centrality**: **Hubs and authorities** (equals eigenvector for undirected networks)
* **Current-flow closeness/betweenness**: Based on **electrical current flow** through the network
* **Subgraph centrality**: Counts **closed walks** via matrix exponential
* **Total communicability**: Sum of **matrix exponential** entries
* **Multiplex k-core**: **Core decomposition** of the multilayer network

5. Extended Measures
~~~~~~~~~~~~~~~~~~~~


* **Information centrality**: **Stephenson-Zelen style** using modified Laplacian inverse
* **Communicability betweenness**: **Estrada-style** measure using matrix exponential
* **Accessibility centrality**: **Entropy-based** measure of h-step reach diversity
* **Percolation centrality**: **Bond percolation** Monte Carlo simulation
* **Spreading (Epidemic) centrality**: **SIR/IC model** based outbreak size
* **Collective influence**: **CI_ℓ** identifying influential spreaders at distance ℓ
* **Load centrality**: **Shortest-path load** through nodes
* **Flow betweenness**: **Maximum flow** based measure
* **Harmonic closeness**: **Handles disconnections** better than standard closeness
* **Edge betweenness**: **Edge-level** shortest path measure
* **Bridging centrality**: **Combines betweenness** with bridging coefficient
* **Local efficiency**: **Neighbor subgraph** efficiency measure
* **Lp-aggregated centrality**: **Framework** for combining per-layer measures

6. Co-Ranking Algorithms
~~~~~~~~~~~~~~~~~~~~~~~~


* **MultiRank**: **Co-ranking** of nodes and layers through iterative updates
* **Multiplex PageRank variants** (Halu et al. 2013):
  
  * **Neutral**: Baseline with no cross-layer influence
  * **Additive**: Cross-layer influence via sum
  * **Multiplicative**: Cross-layer influence via product
  * **Combined**: Both additive and multiplicative coupling

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

**Example Output:**

.. code-block:: python

    print("Layer degrees:", layer_degrees)
    # Layer degrees: {'L1': {'A': 1, 'B': 2, 'C': 1}, 'L2': {'A': 1, 'C': 1}}
    
    print("Overlapping degrees:", overlapping_degrees)
    # Overlapping degrees: {'A': 2, 'B': 2, 'C': 2}
    
    print("Participation coefficient:", participation)
    # Participation coefficient: {'A': 1.0, 'B': 0.0, 'C': 1.0}
    # (Node B only appears in one layer, so participation is 0)


Computing All Centralities
--------------------------


For convenience, you can compute **all available centrality measures** at once:

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


The module provides **several methods** to aggregate node-layer centralities to node-level centralities:

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


* **Path-based measures** (closeness, betweenness) are **computationally expensive** as they require shortest path computations on the entire supra-graph
* **Advanced measures** (current-flow, communicability, k-core) involve **matrix operations** that can be costly for large networks
* **Matrix exponential** computations (subgraph centrality, communicability) are **particularly expensive**
* For **large networks**, consider using only degree-based and eigenvector-based measures
* Use `include_path_based=False` and `include_advanced=False` (defaults) in `compute_all_centralities()` for **better performance**

MultiRank and Multiplex PageRank Variants
-----------------------------------------


The `py3plex.algorithms.multilayer_algorithms.multirank` module provides **co-ranking algorithms** that simultaneously rank nodes and layers.

MultiRank Usage
~~~~~~~~~~~~~~~


MultiRank iteratively updates **node scores** and **layer scores** based on their mutual influence:

.. code-block:: python

    from py3plex.algorithms.multilayer_algorithms.multirank import multirank
    import numpy as np
    
    # Create layer adjacency matrices
    L1 = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)
    L2 = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)
    
    # Compute co-rankings
    node_scores, layer_scores = multirank([L1, L2], alpha=0.85)
    
    print("Node scores:", node_scores)
    # Node scores: [0.33, 0.34, 0.33] (normalized)
    
    print("Layer scores:", layer_scores)
    # Layer scores: [0.6, 0.4] (L1 has more edges, higher score)

**Key Parameters:**

* `alpha`: Damping parameter (typically 0.85), controls random walk probability
* `tol`: Convergence tolerance (default 1e-6)
* `max_iter`: Maximum iterations (default 1000)
* `interlayer_coupling`: Optional L×L coupling matrix (default: identity)

Multiplex PageRank Variants Usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The Halu et al. (2013) framework provides **four variants** of cross-layer influence:

.. code-block:: python

    from py3plex.algorithms.multilayer_algorithms.multirank import multiplex_pagerank
    import numpy as np
    
    # Create layer adjacency matrices
    L1 = np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]], dtype=float)
    L2 = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]], dtype=float)
    
    # Neutral variant (baseline, no cross-layer influence)
    result_neutral = multiplex_pagerank([L1, L2], variant='neutral')
    
    # Additive variant (cross-layer sum)
    result_additive = multiplex_pagerank([L1, L2], variant='additive', c=0.5)
    
    # Multiplicative variant (cross-layer product)
    result_multiplicative = multiplex_pagerank([L1, L2], 
                                               variant='multiplicative', 
                                               c=0.5)
    
    # Combined variant (additive + multiplicative)
    result_combined = multiplex_pagerank([L1, L2], 
                                        variant='combined', 
                                        c1=0.5, 
                                        c2=0.3)
    
    # Access results
    node_scores = result_additive['node_scores']       # Aggregated node scores
    replica_scores = result_additive['replica_scores'] # Per-layer scores (N x L)

**Coupling Functions:**

* **Neutral**: :math:`F^\ell_i = 1` (no coupling)
* **Additive**: :math:`F^\ell_i = 1 + c \sum_{\ell' \neq \ell} r^{\ell'}_i`
* **Multiplicative**: :math:`F^\ell_i = \prod_{\ell' \neq \ell} (r^{\ell'}_i + \epsilon)^c`
* **Combined**: :math:`F^\ell_i = (1 + c_1 \sum_{\ell' \neq \ell} r^{\ell'}_i) \times \prod_{\ell' \neq \ell} (r^{\ell'}_i + \epsilon)^{c_2}`

**Key Parameters:**

* `variant`: One of 'neutral', 'additive', 'multiplicative', 'combined'
* `c`: Coupling strength for additive/multiplicative (default 1.0)
* `c1`, `c2`: Coupling strengths for combined variant
* `epsilon`: Numerical stability constant (default 1e-12)
* `alpha`: Damping parameter (default 0.85)

Extended Centrality Measures
-----------------------------


The extended centrality measures provide specialized metrics for different network analysis scenarios:

.. code-block:: python

    # Information centrality (Stephenson-Zelen style)
    info_cent = calc.information_centrality()
    
    # Communicability betweenness (considers all walks)
    comm_between = calc.communicability_betweenness_centrality()
    
    # Accessibility (entropy-based h-step reach)
    accessibility = calc.accessibility_centrality(h=2)
    
    # Harmonic closeness (better for disconnected graphs)
    harmonic = calc.harmonic_closeness_centrality()
    
    # Local efficiency (fault tolerance)
    local_eff = calc.local_efficiency_centrality()
    
    # Bridging centrality (identifies bridges)
    bridging = calc.bridging_centrality()

**Monte Carlo Simulations:**

.. code-block:: python

    # Percolation centrality (bond percolation)
    percolation = calc.percolation_centrality(
        edge_activation_prob=0.5,
        trials=100
    )
    
    # Spreading/epidemic centrality (SIR model)
    spreading = calc.spreading_centrality(
        beta=0.2,  # Infection rate
        mu=0.1,    # Recovery rate
        trials=50,
        steps=100
    )
    
    # Flow betweenness (max-flow based)
    flow_between = calc.flow_betweenness_centrality(samples=100)

**Influence and Load Measures:**

.. code-block:: python

    # Collective influence (for influential spreaders)
    collective = calc.collective_influence(radius=2)
    
    # Load centrality (shortest-path load)
    load = calc.load_centrality()
    
    # Edge betweenness (edge-level measure)
    edge_between = calc.edge_betweenness_centrality()

**Aggregation Framework:**

.. code-block:: python

    # Lp-aggregated centrality (combine per-layer measures)
    # First get per-layer centralities
    layer_degrees = calc.layer_degree_centrality(weighted=False)
    
    # L2 norm aggregation
    l2_agg = calc.lp_aggregated_centrality(layer_degrees, p=2)
    
    # L-infinity norm (maximum)
    linf_agg = calc.lp_aggregated_centrality(
        layer_degrees,
        p=float('inf')
    )
    
    # Weighted aggregation
    weights = {'L1': 0.6, 'L2': 0.4}
    weighted_agg = calc.lp_aggregated_centrality(
        layer_degrees,
        p=2,
        weights=weights
    )

**Computing All Extended Measures:**

.. code-block:: python

    # Compute all centrality measures including extended ones
    results = compute_all_centralities(
        network,
        include_extended=True
    )
    
    # Access specific measures
    info_centrality = results['information']
    spreading_cent = results['spreading']
    harmonic_close = results['harmonic_closeness']

Example Applications
--------------------


1. **Social network analysis**: Identify **influential users** across different communication platforms
2. **Transportation networks**: Find **critical stations/stops** across different transport modes
3. **Biological networks**: Analyze **protein interactions** across different cellular conditions
4. **Infrastructure networks**: Study **robustness** of multilayer utility networks
5. **Co-ranking applications**: Simultaneously rank **nodes and layers** for importance (MultiRank)
6. **Cross-platform influence**: Model **influence propagation** across interconnected platforms (Multiplex PageRank)
7. **Epidemic modeling**: Use **spreading centrality** to identify superspreaders in contact networks
8. **Network resilience**: Apply **percolation centrality** to assess infrastructure robustness
9. **Information flow**: Use **accessibility** and **local efficiency** to analyze communication networks

Uncertainty Quantification for Centrality Measures
---------------------------------------------------

**New in version 1.0:** py3plex now supports **first-class uncertainty quantification** for centrality measures. All statistics return typed containers (``StatSeries``) that can carry uncertainty information.

Overview
~~~~~~~~

Centrality measures can be uncertain due to:

* **Algorithm stochasticity**: Random initial conditions or tie-breaking
* **Network noise**: Measurement errors, missing edges, temporal variations  
* **Sampling effects**: Incomplete network observations

The uncertainty module provides tools to **quantify and visualize** this uncertainty through resampling strategies.

Basic Usage: Uncertainty Parameter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add uncertainty estimation to any supported centrality function using the ``uncertainty`` parameter:

.. code-block:: python

    from py3plex.algorithms.centrality_toolkit import multilayer_pagerank
    from py3plex.uncertainty import ResamplingStrategy
    
    # Deterministic computation (default)
    result = multilayer_pagerank(network, uncertainty=False)
    print(result.mean)  # Point estimates
    print(result.is_deterministic)  # True
    
    # With uncertainty estimation
    result_uncertain = multilayer_pagerank(
        network,
        uncertainty=True,
        n_runs=50,
        resampling=ResamplingStrategy.PERTURBATION,
        random_seed=42
    )
    
    # Access uncertainty information
    print(result_uncertain.mean)  # Mean across runs
    print(result_uncertain.std)   # Standard deviations
    print(result_uncertain.quantiles[0.025])  # Lower 95% CI
    print(result_uncertain.quantiles[0.975])  # Upper 95% CI

**Resampling Strategies:**

* ``SEED``: Multiple random seeds (for stochastic algorithms)
* ``PERTURBATION``: Random edge/node drops (network structure uncertainty)
* ``BOOTSTRAP``: Bootstrap resampling (future)
* ``JACKKNIFE``: Leave-one-out (future)

Global Context Manager
~~~~~~~~~~~~~~~~~~~~~~~

For pipelines with multiple centrality computations, use the ``uncertainty_enabled`` context:

.. code-block:: python

    from py3plex.uncertainty import uncertainty_enabled
    from py3plex.algorithms.centrality_toolkit import multilayer_pagerank
    
    # Enable uncertainty for entire pipeline
    with uncertainty_enabled(n_runs=100):
        pagerank_scores = multilayer_pagerank(network)
        # Automatically has uncertainty quantified
        
        betweenness_scores = multilayer_betweenness_centrality(network)
        # Also has uncertainty quantified

**Benefits:**

* No need to pass ``uncertainty=True`` to every function
* Consistent uncertainty settings across workflow
* Clean, readable code

StatSeries Type
~~~~~~~~~~~~~~~

All centrality functions return ``StatSeries`` objects, whether deterministic or uncertain:

.. code-block:: python

    from py3plex.algorithms.centrality_toolkit import multilayer_pagerank
    import numpy as np
    
    result = multilayer_pagerank(network, uncertainty=True, n_runs=50)
    
    # StatSeries properties
    print(result.index)        # Node IDs
    print(result.mean)         # Mean centrality values (np.ndarray)
    print(result.std)          # Standard deviations (np.ndarray or None)
    print(result.quantiles)    # Dict with quantiles: {0.025: [...], 0.975: [...]}
    print(result.meta)         # Algorithm metadata
    
    # Backward compatibility
    arr = np.array(result)     # Extracts mean (for plotting, etc.)
    score = result[node]       # Dict-like access: {'mean': ..., 'std': ...}
    dict_result = result.to_dict()  # Full conversion to dict

**Checking uncertainty:**

.. code-block:: python

    if not result.is_deterministic:
        print(f"Certainty: {result.certainty}")  # 0.0 for uncertain
        print(f"Has std: {result.std is not None}")
        print(f"Has quantiles: {result.quantiles is not None}")

Visualization with Uncertainty
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Plot centrality with confidence bands:

.. code-block:: python

    import matplotlib.pyplot as plt
    import numpy as np
    from py3plex.algorithms.centrality_toolkit import multilayer_pagerank
    
    result = multilayer_pagerank(network, uncertainty=True, n_runs=50)
    
    # Sort by mean centrality
    indices = np.argsort(result.mean)[::-1]
    
    # Plot with error bars
    plt.figure(figsize=(10, 6))
    plt.errorbar(
        range(len(result)),
        result.mean[indices],
        yerr=result.std[indices] if result.std is not None else None,
        fmt='o',
        capsize=5,
        label='PageRank ± std'
    )
    
    # Or plot with confidence bands
    plt.fill_between(
        range(len(result)),
        result.quantiles[0.025][indices],
        result.quantiles[0.975][indices],
        alpha=0.3,
        label='95% CI'
    )
    
    plt.xlabel('Node rank')
    plt.ylabel('PageRank centrality')
    plt.legend()
    plt.title('PageRank with Uncertainty')
    plt.show()

Perturbation Parameters
~~~~~~~~~~~~~~~~~~~~~~~

Customize network perturbations for robustness analysis:

.. code-block:: python

    from py3plex.uncertainty import estimate_uncertainty, ResamplingStrategy
    from py3plex.algorithms.centrality_toolkit import multilayer_pagerank
    
    def my_pagerank(net):
        # Custom centrality function
        return {node: 1.0 for node in net.get_nodes()}
    
    # Custom perturbation: drop 10% edges, 5% nodes
    result = estimate_uncertainty(
        network,
        my_pagerank,
        n_runs=100,
        resampling=ResamplingStrategy.PERTURBATION,
        perturbation_params={
            "edge_drop_p": 0.10,  # Drop 10% of edges
            "node_drop_p": 0.05   # Drop 5% of nodes
        },
        random_seed=42
    )

**Use cases:**

* **Robustness analysis**: How stable is centrality under edge failures?
* **Network noise**: What if some edges are incorrectly measured?
* **Sampling effects**: How reliable is centrality from partial observations?

Supported Algorithms
~~~~~~~~~~~~~~~~~~~~

**Currently supported with uncertainty:**

* ``multilayer_pagerank()`` ✓

**Coming soon:**

* ``multilayer_betweenness_centrality()``
* ``multilayer_eigenvector_centrality()``
* ``multiplex_degree_centrality()``

To add uncertainty support to custom centrality functions, see the :doc:`../reference/api_index` documentation for ``py3plex.uncertainty.estimate_uncertainty``.

References
----------


The implementations follow **standard definitions** from multilayer network analysis literature, particularly:

* Kivelä, M., Arenas, A., Barthelemy, M., Gleeson, J. P., Moreno, Y., & Porter, M. A. (2014). **Multilayer networks**. Journal of complex networks, 2(3), 203-271.
* Boccaletti, S., Bianconi, G., Criado, R., Del Genio, C. I., Gómez-Gardenes, J., Romance, M., ... & Zanin, M. (2014). **The structure and dynamics of multilayer networks**. Physics Reports, 544(1), 1-122.
* Halu, A., Mondragon, R. J., Panzarasa, P., & Bianconi, G. (2013). **Multiplex PageRank**. PloS one, 8(10), e78293.
* De Domenico, M., Solé-Ribalta, A., Cozzo, E., Kivelä, M., Moreno, Y., Porter, M. A., ... & Arenas, A. (2013). **Mathematical formulation of multilayer networks**. Physical Review X, 3(4), 041022.
* Stephenson, K., & Zelen, M. (1989). **Rethinking centrality: Methods and examples**. Social networks, 11(1), 1-37.
* Estrada, E., & Hatano, N. (2008). **Communicability in complex networks**. Physical Review E, 77(3), 036111.
* Estrada, E., Higham, D. J., & Hatano, N. (2009). **Communicability betweenness in complex networks**. Physica A, 388(5), 764-774.
* Morone, F., & Makse, H. A. (2015). **Influence maximization in complex networks through optimal percolation**. Nature, 524(7563), 65-68.
* Latora, V., & Marchiori, M. (2001). **Efficient behavior of small-world networks**. Physical review letters, 87(19), 198701.