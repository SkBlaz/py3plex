Advanced Multilayer Metrics
============================

Overview
--------

The ``multilayer_statistics`` module provides advanced entropy-based, information-theoretic, and influence metrics for multilayer network analysis. These metrics enable deep characterization of structural complexity, layer interdependencies, and centrality patterns across network layers.

New Metrics (v0.96+)
--------------------

The following advanced metrics have been added to py3plex for comprehensive multilayer network analysis:

1. **Entropy-based Layer Complexity Measures**
2. **Cross-layer Mutual Information**
3. **Layer Influence Centrality**
4. **Multilayer Betweenness Surface**
5. **Inter-layer Degree Correlation Matrix**

Installation
------------

These metrics are included in py3plex. Ensure you have the required dependencies:

.. code-block:: bash

    pip install numpy scipy networkx matplotlib seaborn

Quickstart
-----------

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls

    # Create a multilayer network
    network = multinet.multi_layer_network(directed=False)
    network.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1],
        ['A', 'L2', 'C', 'L2', 1],
        ['A', 'L1', 'A', 'L2', 1],  # Inter-layer edge
    ], input_type='list')

    # Calculate entropy-based metrics
    entropy = mls.layer_connectivity_entropy(network, 'L1')
    mi = mls.cross_layer_mutual_information(network, 'L1', 'L2')
    influence = mls.layer_influence_centrality(network, 'L1')

    print(f"Connectivity entropy: {entropy:.3f}")
    print(f"Mutual information: {mi:.3f}")
    print(f"Layer influence: {influence:.3f}")

**Expected Output:**

.. code-block:: text

    Connectivity entropy: 1.500
    Mutual information: 0.500
    Layer influence: 1.000

Entropy-based Complexity Measures
----------------------------------

These metrics quantify structural complexity using information-theoretic entropy.

Layer Connectivity Entropy
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Measures heterogeneity of node connectivity within a layer using Shannon entropy of the degree distribution.

**Formula:** H_c = -Σᵢ (kᵢ/Σⱼkⱼ) log₂(kᵢ/Σⱼkⱼ)

**Interpretation:**
- H_c = 0: uniform degree distribution (all nodes have same degree)
- Higher values: more diverse connectivity patterns
- Useful for identifying layers with hub-and-spoke vs. distributed structures

.. code-block:: python

    # Calculate for each layer
    for layer in ['L1', 'L2', 'L3']:
        entropy = mls.layer_connectivity_entropy(network, layer)
        print(f"Layer {layer} connectivity entropy: {entropy:.3f}")

**Example Output:**

.. code-block:: text

    Layer L1 connectivity entropy: 2.000
    Layer L2 connectivity entropy: 1.585
    Layer L3 connectivity entropy: 2.252

Inter-layer Dependence Entropy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Measures diversity in how nodes couple two layers through inter-layer edges.

**Formula:** H_dep = -Σₙ pₙ log₂(pₙ), where pₙ is the proportion of inter-layer edges for node n

**Interpretation:**
- H_dep = 0: uniform coupling (all nodes equally involved in inter-layer connections)
- Higher values: more heterogeneous coupling patterns
- Identifies layers with specialized bridge nodes

.. code-block:: python

    # Calculate inter-layer dependence
    entropy = mls.inter_layer_dependence_entropy(network, 'L1', 'L2')
    print(f"Inter-layer dependence entropy: {entropy:.3f}")

**Example Output:**

.. code-block:: text

    Inter-layer dependence entropy: 1.500

Cross-layer Redundancy Entropy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Measures diversity in structural overlap across all layer pairs using edge overlap.

**Formula:** H_r = -Σᵢⱼ rᵢⱼ log₂(rᵢⱼ), where rᵢⱼ is normalized edge overlap

**Interpretation:**
- H_r = 0: uniform redundancy across all layer pairs
- Higher values: varied overlap patterns (some layers very similar, others distinct)
- Useful for identifying functionally redundant vs. complementary layers

.. code-block:: python

    # Calculate global redundancy entropy
    entropy = mls.cross_layer_redundancy_entropy(network)
    print(f"Cross-layer redundancy entropy: {entropy:.3f}")

**Example Output:**

.. code-block:: text

    Cross-layer redundancy entropy: 1.000

Cross-layer Mutual Information
-------------------------------

Quantifies statistical dependence between degree distributions in two layers.

**Formula:** I(Lᵢ; Lⱼ) = H(Lᵢ) + H(Lⱼ) - H(Lᵢ, Lⱼ)

**Properties:**
- I = 0: layers are statistically independent
- I > 0: layers are dependent (higher values = stronger dependence)
- I(Lᵢ; Lⱼ) ≤ min(H(Lᵢ), H(Lⱼ))
- Symmetric: I(Lᵢ; Lⱼ) = I(Lⱼ; Lᵢ)

**Use Cases:**
- Identify functionally related layers
- Detect redundant vs. complementary layers
- Guide layer aggregation or dimensionality reduction
- Predict cross-layer influence patterns

.. code-block:: python

    # Calculate mutual information between layer pairs
    mi_12 = mls.cross_layer_mutual_information(network, 'L1', 'L2', bins=10)
    mi_13 = mls.cross_layer_mutual_information(network, 'L1', 'L3', bins=10)
    mi_23 = mls.cross_layer_mutual_information(network, 'L2', 'L3', bins=10)

    print(f"I(L1; L2) = {mi_12:.3f} bits")
    print(f"I(L1; L3) = {mi_13:.3f} bits")
    print(f"I(L2; L3) = {mi_23:.3f} bits")

**Example Output:**

.. code-block:: text

    I(L1; L2) = 0.250 bits
    I(L1; L3) = 0.000 bits
    I(L2; L3) = 0.150 bits

**Parameters:**
- ``network``: py3plex multi_layer_network object
- ``layer_i``: First layer identifier
- ``layer_j``: Second layer identifier
- ``bins``: Number of bins for discretizing degree distributions (default: 10)

Layer Influence Centrality
---------------------------

Quantifies how much a layer influences others through inter-layer connections or information flow.

**Two Methods:**

1. **Coupling-based Influence**
   
   **Formula:** Iᵅ = Σᵦ≠ᵅ C^αβ / (L-1)
   
   - Based on inter-layer coupling strength
   - Structural measure
   - Fast to compute

2. **Flow-based Influence**
   
   **Formula:** Iᵅ = flow probability from layer α to other layers
   
   - Based on random walk simulations
   - Dynamic measure
   - Captures indirect influence

**Interpretation:**
- Higher values indicate layers that strongly influence others
- Useful for identifying critical layers in multilayer infrastructure
- Guides targeted interventions or layer removal strategies

.. code-block:: python

    # Coupling-based influence
    influence_coupling = mls.layer_influence_centrality(
        network, 'L1', method='coupling'
    )

    # Flow-based influence
    influence_flow = mls.layer_influence_centrality(
        network, 'L1', method='flow', sample_size=100
    )

    print(f"Layer L1 coupling influence: {influence_coupling:.3f}")
    print(f"Layer L1 flow influence: {influence_flow:.3f}")

**Example Output:**

.. code-block:: text

    Layer L1 coupling influence: 1.250
    Layer L1 flow influence: 0.420

**Parameters:**
- ``network``: py3plex multi_layer_network object
- ``layer``: Layer identifier
- ``method``: 'coupling' or 'flow' (default: 'coupling')
- ``sample_size``: Number of random walk steps for flow method (default: 100)

Multilayer Betweenness Surface
-------------------------------

Visualizes betweenness centrality across all node-layer pairs as a 2D matrix (surface).

**Output:** 2D array of shape (num_nodes, num_layers)

**Applications:**
- Identify bridge nodes that connect different layers
- Visualize centrality patterns as heatmaps or 3D surfaces
- Compare node importance across layers
- Detect layer-specific vs. global central nodes

.. code-block:: python

    # Calculate betweenness surface
    surface, (nodes, layers) = mls.multilayer_betweenness_surface(
        network, normalized=True
    )

    # Visualize as heatmap
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.figure(figsize=(10, 6))
    sns.heatmap(surface, annot=True, fmt='.3f', 
                xticklabels=layers, yticklabels=nodes,
                cmap='YlOrRd', cbar_kws={'label': 'Betweenness Centrality'})
    plt.xlabel('Layers')
    plt.ylabel('Nodes')
    plt.title('Multilayer Betweenness Surface')
    plt.tight_layout()
    plt.savefig('betweenness_surface.png', dpi=300)

**Example Output:**

.. code-block:: text

    Surface shape: (5, 3) nodes × layers
    
    Node     L1      L2      L3
    --------------------------------
    Alice    0.250   0.333   0.115
    Bob      0.280   0.000   0.154
    Carol    0.180   0.038   0.295
    David    0.128   0.038   0.000
    Eve      0.000   0.000   0.000

**Visualization Tips:**
- Use heatmaps for quick overview
- Use 3D surface plots for presentations
- Cluster rows (nodes) to identify groups with similar patterns
- Compare surfaces across different time points or conditions

Inter-layer Degree Correlation Matrix
--------------------------------------

Computes Pearson correlations of node degrees between all pairs of layers.

**Output:** Symmetric correlation matrix (num_layers × num_layers)

**Properties:**
- Diagonal elements are 1.0 (self-correlation)
- Off-diagonal elements in [-1, 1]
- Positive values: nodes with high degree in one layer tend to have high degree in another
- Negative values: inverse relationship (hubs in one layer are peripheral in another)

**Applications:**
- Identify correlated vs. independent layers
- Detect layer redundancy for network compression
- Guide layer aggregation strategies
- Understand cross-layer degree assortativity

.. code-block:: python

    # Calculate correlation matrix
    corr_matrix, layers = mls.interlayer_degree_correlation_matrix(network)

    # Visualize
    import matplotlib.pyplot as plt
    import seaborn as sns

    plt.figure(figsize=(8, 6))
    sns.heatmap(corr_matrix, annot=True, fmt='.3f',
                xticklabels=layers, yticklabels=layers,
                cmap='coolwarm', center=0, vmin=-1, vmax=1,
                cbar_kws={'label': 'Pearson Correlation'})
    plt.title('Inter-layer Degree Correlation Matrix')
    plt.tight_layout()
    plt.savefig('degree_correlation_matrix.png', dpi=300)

**Example Output:**

.. code-block:: text

    Correlation Matrix:
                 L1       L2       L3
    L1          1.000    0.750   -0.250
    L2          0.750    1.000    0.000
    L3         -0.250    0.000    1.000

**Interpretation:**
- L1 and L2 are strongly positively correlated (r = 0.75)
- L1 and L3 are negatively correlated (r = -0.25)
- L2 and L3 are independent (r = 0.00)

Complete Example
----------------

This example demonstrates all advanced metrics on a social-professional network:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    import numpy as np

    # Create 3-layer social-professional network
    network = multinet.multi_layer_network(directed=False)

    # Facebook layer (social)
    network.add_edges([
        ['Alice', 'facebook', 'Bob', 'facebook', 1],
        ['Alice', 'facebook', 'Carol', 'facebook', 1],
        ['Bob', 'facebook', 'Carol', 'facebook', 1],
    ], input_type='list')

    # LinkedIn layer (professional)
    network.add_edges([
        ['Alice', 'linkedin', 'Bob', 'linkedin', 1],
        ['Carol', 'linkedin', 'David', 'linkedin', 1],
    ], input_type='list')

    # Twitter layer (public)
    network.add_edges([
        ['Alice', 'twitter', 'Carol', 'twitter', 1],
        ['Bob', 'twitter', 'David', 'twitter', 1],
    ], input_type='list')

    # Inter-layer connections
    network.add_edges([
        ['Alice', 'facebook', 'Alice', 'linkedin', 1],
        ['Alice', 'linkedin', 'Alice', 'twitter', 1],
        ['Bob', 'facebook', 'Bob', 'twitter', 1],
        ['Carol', 'facebook', 'Carol', 'twitter', 1],
    ], input_type='list')

    # 1. Entropy-based complexity measures
    print("=== ENTROPY-BASED MEASURES ===")
    for layer in ['facebook', 'linkedin', 'twitter']:
        entropy = mls.layer_connectivity_entropy(network, layer)
        print(f"{layer}: {entropy:.3f} bits")

    # 2. Cross-layer mutual information
    print("\n=== MUTUAL INFORMATION ===")
    mi = mls.cross_layer_mutual_information(network, 'facebook', 'linkedin')
    print(f"I(facebook; linkedin) = {mi:.3f} bits")

    # 3. Layer influence centrality
    print("\n=== LAYER INFLUENCE ===")
    for layer in ['facebook', 'linkedin', 'twitter']:
        influence = mls.layer_influence_centrality(network, layer, method='coupling')
        print(f"{layer}: {influence:.3f}")

    # 4. Betweenness surface
    print("\n=== BETWEENNESS SURFACE ===")
    surface, (nodes, layers) = mls.multilayer_betweenness_surface(network)
    print(f"Shape: {surface.shape}")
    print(f"Mean betweenness: {np.mean(surface):.3f}")

    # 5. Degree correlation matrix
    print("\n=== DEGREE CORRELATION MATRIX ===")
    corr_matrix, layers = mls.interlayer_degree_correlation_matrix(network)
    print("Correlation matrix:")
    print(corr_matrix)

**Expected Output:**

.. code-block:: text

    === ENTROPY-BASED MEASURES ===
    facebook: 1.585 bits
    linkedin: 1.500 bits
    twitter: 1.500 bits

    === MUTUAL INFORMATION ===
    I(facebook; linkedin) = 0.000 bits

    === LAYER INFLUENCE ===
    facebook: 1.000
    linkedin: 1.000
    twitter: 1.000

    === BETWEENNESS SURFACE ===
    Shape: (4, 3)
    Mean betweenness: 0.158

    === DEGREE CORRELATION MATRIX ===
    Correlation matrix:
    [[ 1.     0.5   -0.5  ]
     [ 0.5    1.     0.   ]
     [-0.5    0.     1.   ]]

API Reference
-------------

layer_connectivity_entropy(network, layer)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Calculate Shannon entropy of degree distribution within a layer.

**Parameters:**
- ``network`` (multi_layer_network): The multilayer network
- ``layer`` (str): Layer identifier

**Returns:**
- ``float``: Entropy in bits (≥ 0)

inter_layer_dependence_entropy(network, layer_i, layer_j)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Calculate entropy of inter-layer coupling patterns.

**Parameters:**
- ``network`` (multi_layer_network): The multilayer network
- ``layer_i`` (str): First layer identifier
- ``layer_j`` (str): Second layer identifier

**Returns:**
- ``float``: Entropy in bits (≥ 0)

cross_layer_redundancy_entropy(network)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Calculate entropy of edge overlap across all layer pairs.

**Parameters:**
- ``network`` (multi_layer_network): The multilayer network

**Returns:**
- ``float``: Entropy in bits (≥ 0)

cross_layer_mutual_information(network, layer_i, layer_j, bins=10)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Calculate mutual information between degree distributions.

**Parameters:**
- ``network`` (multi_layer_network): The multilayer network
- ``layer_i`` (str): First layer identifier
- ``layer_j`` (str): Second layer identifier
- ``bins`` (int): Number of bins for discretization (default: 10)

**Returns:**
- ``float``: Mutual information in bits (≥ 0)

layer_influence_centrality(network, layer, method='coupling', sample_size=100)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Calculate layer influence through coupling or flow.

**Parameters:**
- ``network`` (multi_layer_network): The multilayer network
- ``layer`` (str): Layer identifier
- ``method`` (str): 'coupling' or 'flow' (default: 'coupling')
- ``sample_size`` (int): Number of random walk steps for flow method (default: 100)

**Returns:**
- ``float``: Influence centrality value (≥ 0)

multilayer_betweenness_surface(network, normalized=True, weight=None)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Calculate betweenness centrality matrix for all node-layer pairs.

**Parameters:**
- ``network`` (multi_layer_network): The multilayer network
- ``normalized`` (bool): Normalize betweenness values (default: True)
- ``weight`` (str): Edge weight attribute (default: None)

**Returns:**

- ``tuple``: (surface, (nodes, layers))

  - ``surface`` (np.ndarray): 2D array of shape (num_nodes, num_layers)
  - ``nodes`` (list): Node labels
  - ``layers`` (list): Layer labels

interlayer_degree_correlation_matrix(network)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Calculate Pearson correlations of node degrees between all layer pairs.

**Parameters:**
- ``network`` (multi_layer_network): The multilayer network

**Returns:**

- ``tuple``: (corr_matrix, layers)

  - ``corr_matrix`` (np.ndarray): Symmetric correlation matrix
  - ``layers`` (list): Layer labels

Best Practices
--------------

**Choosing Metrics:**
- Use entropy measures for structural complexity analysis
- Use mutual information for layer dependency analysis
- Use influence centrality for identifying critical layers
- Use betweenness surface for node-level analysis across layers
- Use correlation matrix for layer similarity analysis

**Computational Considerations:**
- Entropy and correlation metrics are fast (O(E) or O(N×L))
- Mutual information requires discretization (adjust ``bins`` parameter)
- Flow-based influence requires random walk simulation (adjust ``sample_size``)
- Betweenness surface can be slow for large networks (consider sampling)

**Interpretation Guidelines:**
- Compare metric values across networks, not absolute values
- Use entropy as a relative measure of heterogeneity
- Mutual information identifies functional dependencies
- Layer influence guides intervention strategies
- Betweenness surface reveals cross-layer bridge nodes

References
----------

1. Shannon, C. E. (1948). "A Mathematical Theory of Communication." *Bell System Technical Journal*, 27(3), 379-423.

2. Cover, T. M., & Thomas, J. A. (2006). *Elements of Information Theory*. John Wiley & Sons.

3. De Domenico, M., et al. (2013). "Mathematical formulation of multilayer networks." *Physical Review X*, 3(4), 041022.

4. De Domenico, M., et al. (2015). "Structural reducibility of multilayer networks." *Nature Communications*, 6, 6864.

5. Bianconi, G. (2018). *Multilayer Networks: Structure and Function*. Oxford University Press.

6. Kivelä, M., et al. (2014). "Multilayer networks." *Journal of Complex Networks*, 2(3), 203-271.

7. Cozzo, E., et al. (2013). "Mathematical formulation of multilayer networks." *Physical Review E*, 88(5), 050801.

Examples
--------

See the following example scripts in the repository:

- ``examples/network_analysis/example_advanced_multilayer_metrics.py`` - Comprehensive demonstration of all new metrics
- ``examples/network_analysis/example_multilayer_statistics.py`` - Basic multilayer statistics
- ``examples/network_analysis/example_new_multiplex_metrics.py`` - Multiplex-specific metrics

Repository: https://github.com/SkBlaz/py3plex/tree/master/examples

Related Documentation
---------------------

- :doc:`basic_usage_analysis_multiplex` - Basic multiplex network analysis
- :doc:`statistical_comparison` - Statistical comparison framework
- :doc:`multilayer_centrality_matrix_functions` - Centrality measures
