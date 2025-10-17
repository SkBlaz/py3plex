Multilayer Modularity and Community Detection
=============================================


This tutorial demonstrates how to use py3plex's multilayer modularity maximization and community detection capabilities based on Mucha et al. (2010).

Overview
--------


Multilayer modularity extends Newman's modularity to networks with multiple layers (e.g., temporal or multiplex networks). The key idea is that each node-layer pair can be assigned to a community, allowing the same physical node to belong to different communities in different layers.

Mathematical Background
-----------------------


Multilayer Modularity Quality Function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The multilayer modularity :math:`Q` is defined as:

$:math:`Q_{\text{multilayer}} = \frac{1}{2\mu} \sum_{i,j}\sum_{\alpha,\beta} \Big[ \big(A^{[\alpha]}_{ij} - \gamma^{[\alpha]}P^{[\alpha]}_{ij}\big)\,\delta_{\alpha\beta} + \delta_{ij}\,\omega_{\alpha\beta}\Big]\,\delta\big(g_{i,\alpha},\,g_{j,\beta}\big)`$

where:
* :math:`A^{[\alpha]}_{ij}` is the adjacency matrix of layer :math:`\alpha`
* :math:`P^{[\alpha]}_{ij}` is the expected weight under a null model (e.g., :math:`k_i^\alpha k_j^\alpha / 2m_\alpha`)
* :math:`\gamma^{[\alpha]}` is the resolution parameter for layer :math:`\alpha`
* :math:`\omega_{\alpha\beta}` is the inter-layer coupling strength
* :math:`\delta(g_{i,\alpha}, g_{j,\beta}) = 1` if node :math:`i` in layer :math:`\alpha` and node :math:`j` in layer :math:`\beta` are in the same community

Supra-Adjacency Matrix Representation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


A multilayer network can be represented as a supra-adjacency matrix of size :math:`NL \times NL` (for :math:`N` nodes and :math:`L` layers), where:
* Diagonal blocks contain the intra-layer adjacency matrices :math:`A^{[\alpha]}`
* Off-diagonal blocks encode inter-layer connections (e.g., :math:`\omega I` for identity coupling)

Basic Usage
-----------


Calculating Multilayer Modularity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.community_detection.multilayer_modularity import multilayer_modularity
    
    # Create a multilayer network
    network = multinet.multi_layer_network(directed=False)
    network.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1],
        ['C', 'L1', 'A', 'L1', 1],
        ['A', 'L2', 'B', 'L2', 1],
        ['B', 'L2', 'C', 'L2', 1]
    ], input_type='list')
    
    # Assign communities (node-layer pairs to community IDs)
    communities = {
        ('A', 'L1'): 0, ('B', 'L1'): 0, ('C', 'L1'): 1,
        ('A', 'L2'): 0, ('B', 'L2'): 0, ('C', 'L2'): 1
    }
    
    # Calculate modularity with uniform parameters
    Q = multilayer_modularity(network, communities, gamma=1.0, omega=1.0)
    print(f"Modularity: {Q:.3f}")


Layer-Specific Resolution Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


You can specify different resolution parameters for each layer:

.. code-block:: python

    # Different resolution per layer
    gamma_dict = {
        'L1': 0.5,  # Lower resolution (larger communities)
        'L2': 2.0   # Higher resolution (smaller communities)
    }
    
    Q = multilayer_modularity(network, communities, gamma=gamma_dict, omega=1.0)
    print(f"Modularity with layer-specific gamma: {Q:.3f}")


Custom Inter-Layer Coupling
~~~~~~~~~~~~~~~~~~~~~~~~~~~


You can specify layer-pair specific coupling strengths:

.. code-block:: python

    import numpy as np
    
    # Custom coupling matrix (3x3 for 3 layers)
    omega_matrix = np.array([
        [0.0, 1.0, 0.5],  # Layer 0 couplings
        [1.0, 0.0, 1.0],  # Layer 1 couplings
        [0.5, 1.0, 0.0]   # Layer 2 couplings
    ])
    
    Q = multilayer_modularity(network, communities, gamma=1.0, omega=omega_matrix)


Community Detection
-------------------


Generalized Louvain Algorithm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


The generalized Louvain algorithm greedily maximizes multilayer modularity:

.. code-block:: python

    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer
    
    # Detect communities using Louvain
    communities = louvain_multilayer(
        network,
        gamma=1.0,
        omega=1.0,
        max_iter=100,
        random_state=42
    )
    
    # Print results
    for (node, layer), community_id in sorted(communities.items()):
        print(f"Node {node} in layer {layer}: Community {community_id}")
    
    # Calculate resulting modularity
    Q = multilayer_modularity(network, communities, gamma=1.0, omega=1.0)
    print(f"Final modularity: {Q:.3f}")


Effect of Coupling Strength
~~~~~~~~~~~~~~~~~~~~~~~~~~~


The coupling parameter :math:`\omega` controls how much communities align across layers:

.. code-block:: python

    # Weak coupling (independent layers)
    communities_weak = louvain_multilayer(network, gamma=1.0, omega=0.1)
    
    # Strong coupling (same communities across layers)
    communities_strong = louvain_multilayer(network, gamma=1.0, omega=10.0)
    
    # Compare results
    print("Weak coupling communities:", communities_weak)
    print("Strong coupling communities:", communities_strong)


Supra-Modularity Matrix
-----------------------


For spectral methods, you can build the supra-modularity matrix:

.. code-block:: python

    from py3plex.algorithms.community_detection.multilayer_modularity import build_supra_modularity_matrix
    
    # Build modularity matrix
    B, node_layer_list = build_supra_modularity_matrix(
        network, 
        gamma=1.0, 
        omega=1.0
    )
    
    print(f"Supra-modularity matrix shape: {B.shape}")
    print(f"Node-layer pairs: {node_layer_list}")
    
    # Use for spectral analysis
    import numpy as np
    eigenvalues, eigenvectors = np.linalg.eigh(B)
    print(f"Leading eigenvalues: {eigenvalues[-5:]}")


Synthetic Benchmark Networks
----------------------------


Multilayer LFR Benchmark
~~~~~~~~~~~~~~~~~~~~~~~~


Generate multilayer networks with ground-truth communities:

.. code-block:: python

    from py3plex.algorithms.community_detection.multilayer_benchmark import generate_multilayer_lfr
    
    # Generate with identical communities across layers
    network, ground_truth = generate_multilayer_lfr(
        n=100,
        layers=['L1', 'L2', 'L3'],
        tau1=2.0,           # Degree distribution exponent
        tau2=1.5,           # Community size distribution exponent
        mu=0.1,             # Mixing parameter (10% external edges)
        avg_degree=10,
        min_community=20,
        community_persistence=1.0,  # Same communities in all layers
        seed=42
    )
    
    # Check ground truth
    print(f"Generated {len(set(ground_truth.values()))} communities")
    
    # Detect communities
    detected = louvain_multilayer(network, gamma=1.0, omega=1.0)
    
    # Compare with ground truth
    # (would need to implement community comparison metrics)


Evolving Communities
~~~~~~~~~~~~~~~~~~~~


Generate networks where communities evolve across layers:

.. code-block:: python

    # Generate with evolving communities
    network, ground_truth = generate_multilayer_lfr(
        n=100,
        layers=['T0', 'T1', 'T2', 'T3'],  # Temporal layers
        mu=0.1,
        avg_degree=10,
        community_persistence=0.7,  # 70% nodes keep community
        seed=42
    )
    
    # Analyze community persistence
    for layer in ['T0', 'T1', 'T2', 'T3']:
        layer_nodes = [(n, l) for (n, l) in ground_truth.keys() if l == layer]
        print(f"{layer}: {len(layer_nodes)} nodes")


Overlapping Communities
~~~~~~~~~~~~~~~~~~~~~~~


Generate networks with nodes belonging to multiple communities:

.. code-block:: python

    # Generate with overlapping communities
    network, ground_truth = generate_multilayer_lfr(
        n=100,
        layers=['L1', 'L2'],
        mu=0.1,
        overlapping_nodes=20,        # 20 nodes overlap
        overlapping_membership=2,    # Each belongs to 2 communities
        seed=42
    )
    
    # Check overlapping nodes
    overlapping_count = sum(1 for coms in ground_truth.values() if len(coms) > 1)
    print(f"Nodes with multiple communities: {overlapping_count}")


Partial Node Overlap
~~~~~~~~~~~~~~~~~~~~


Generate networks where not all nodes appear in all layers:

.. code-block:: python

    # Generate with partial node presence
    network, ground_truth = generate_multilayer_lfr(
        n=100,
        layers=['Social', 'Work', 'Family'],
        mu=0.1,
        node_overlap=0.7,  # 70% nodes in all layers
        seed=42
    )
    
    # Check node presence per layer
    for layer in ['Social', 'Work', 'Family']:
        layer_nodes = set(n for (n, l) in ground_truth.keys() if l == layer)
        print(f"{layer}: {len(layer_nodes)} nodes")


Coupled Erdős-Rényi Models
--------------------------


Generate random multilayer networks with controllable coupling:

.. code-block:: python

    from py3plex.algorithms.community_detection.multilayer_benchmark import generate_coupled_er_multilayer
    
    # Full multiplex (all nodes coupled)
    network = generate_coupled_er_multilayer(
        n=100,
        layers=['L1', 'L2', 'L3'],
        p=0.1,              # Edge probability per layer
        omega=1.0,          # Coupling strength
        coupling_probability=1.0,  # All nodes coupled
        seed=42
    )
    
    # Interdependent networks (partial coupling)
    network = generate_coupled_er_multilayer(
        n=100,
        layers=['L1', 'L2'],
        p=0.1,
        omega=0.5,
        coupling_probability=0.5,  # Only 50% nodes coupled
        seed=42
    )


Layer-Specific Edge Probabilities
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. code-block:: python

    # Different density per layer
    network = generate_coupled_er_multilayer(
        n=100,
        layers=['Sparse', 'Dense'],
        p=[0.05, 0.3],  # Different probabilities
        omega=1.0,
        seed=42
    )


Stochastic Block Model
----------------------


Generate multilayer networks with explicit block structure:

.. code-block:: python

    from py3plex.algorithms.community_detection.multilayer_benchmark import generate_sbm_multilayer
    
    # Define communities
    communities = [
        {0, 1, 2, 3, 4},      # Community 0
        {5, 6, 7, 8, 9},      # Community 1
        {10, 11, 12, 13, 14}  # Community 2
    ]
    
    # Generate with high intra-community, low inter-community edges
    network, ground_truth = generate_sbm_multilayer(
        n=15,
        layers=['L1', 'L2'],
        communities=communities,
        p_in=0.7,   # 70% intra-community edges
        p_out=0.05, # 5% inter-community edges
        community_persistence=0.8,
        seed=42
    )
    
    # Verify structure
    print(f"Ground truth communities: {set(ground_truth.values())}")


Advanced Examples
-----------------


Parameter Tuning
~~~~~~~~~~~~~~~~


Finding optimal resolution and coupling parameters:

.. code-block:: python

    import numpy as np
    
    # Test range of parameters
    gammas = [0.5, 1.0, 1.5, 2.0]
    omegas = [0.1, 0.5, 1.0, 2.0, 5.0]
    
    results = []
    for gamma in gammas:
        for omega in omegas:
            communities = louvain_multilayer(network, gamma=gamma, omega=omega)
            Q = multilayer_modularity(network, communities, gamma=gamma, omega=omega)
            n_communities = len(set(communities.values()))
            results.append((gamma, omega, Q, n_communities))
            print(f"γ={gamma}, ω={omega}: Q={Q:.3f}, n_com={n_communities}")
    
    # Find best parameters
    best = max(results, key=lambda x: x[2])
    print(f"\nBest: γ={best[0]}, ω={best[1]}, Q={best[2]:.3f}")


Temporal Community Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Analyzing community evolution over time:

.. code-block:: python

    # Generate temporal network
    network, ground_truth = generate_multilayer_lfr(
        n=50,
        layers=[f'T{i}' for i in range(10)],  # 10 time steps
        mu=0.1,
        community_persistence=0.9,  # Slowly evolving
        seed=42
    )
    
    # Detect communities
    communities = louvain_multilayer(network, gamma=1.0, omega=1.0)
    
    # Track community evolution
    node = 0  # Track first node
    timeline = []
    for t in range(10):
        com = communities.get((node, f'T{t}'), -1)
        timeline.append(com)
    
    print(f"Node {node} community timeline: {timeline}")


Comparing Detection Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. code-block:: python

    # Compare different coupling strengths
    weak_coupling = louvain_multilayer(network, gamma=1.0, omega=0.1)
    strong_coupling = louvain_multilayer(network, gamma=1.0, omega=10.0)
    
    Q_weak = multilayer_modularity(network, weak_coupling, gamma=1.0, omega=0.1)
    Q_strong = multilayer_modularity(network, strong_coupling, gamma=1.0, omega=10.0)
    
    print(f"Weak coupling: Q={Q_weak:.3f}, n_com={len(set(weak_coupling.values()))}")
    print(f"Strong coupling: Q={Q_strong:.3f}, n_com={len(set(strong_coupling.values()))}")


Performance Considerations
--------------------------


Large Networks
~~~~~~~~~~~~~~


For large networks, the Louvain algorithm can be slow. Consider:

.. code-block:: python

    # Limit iterations
    communities = louvain_multilayer(
        network, 
        gamma=1.0, 
        omega=1.0,
        max_iter=50  # Reduce from default 100
    )
    
    # Use lower coupling for faster convergence
    communities = louvain_multilayer(
        network,
        gamma=1.0,
        omega=0.5,  # Lower coupling = faster
        max_iter=100
    )


Memory Usage
~~~~~~~~~~~~


The supra-adjacency matrix can be large. Use sparse representations when possible:

.. code-block:: python

    # The network internally uses sparse matrices
    supra_matrix = network.get_supra_adjacency_matrix()
    print(f"Supra-matrix is sparse: {type(supra_matrix)}")


References
----------


1. **Mucha et al., "Community Structure in Time-Dependent, Multiscale, and Multiplex Networks"**, Science 328:876-878 (2010)
   * Original multilayer modularity formulation

2. **Kivelä et al., "Multilayer networks"**, J. Complex Netw. 2:203 (2014)
   * Comprehensive review of multilayer network analysis

3. **De Domenico et al., "Mathematical Formulation of Multilayer Networks"**, Phys. Rev. X 3, 041022 (2013)
   * Mathematical foundations and tensor representation

4. **Granell et al., "Benchmark model to assess community structure in evolving networks"**, Phys. Rev. E 92, 012805 (2015)
   * Temporal network benchmarks

5. **Pamfil et al., "Relating modularity maximization and stochastic block models"**, SIAM J. Data Science 1(4):667 (2019)
   * Theoretical grounding for parameter selection

See Also
--------


* `Multilayer Centrality Tutorial <multilayer_centrality_tutorial.md>`_
* `Supra-Adjacency Matrices <../docfiles/supra.rst>`_
* Community Detection in py3plex
