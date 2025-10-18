.. _multilayer_centrality_matrix_functions:

Supra Matrix Function Centralities
===================================

These centrality measures operate directly on the supra-adjacency matrix of a multilayer network using matrix functions. They provide global measures of node-layer pair importance based on walks, paths, and communication patterns across the entire network structure.

Overview
--------

Matrix function centralities extend classical centrality concepts to multilayer networks by:

* Operating on the full supra-adjacency matrix that captures both intra-layer and inter-layer connections
* Using matrix functions (exponential, matrix inversion) to account for all paths simultaneously
* Providing normalized scores that can be compared across different network structures
* Supporting both sparse and dense computation for efficiency

These measures are particularly useful for:

* Identifying influential node-layer pairs in multiplex networks
* Analyzing information flow across network layers
* Comparing node importance across different network structures
* Understanding long-range dependencies in multilayer systems

Available Methods
-----------------

Communicability Centrality
~~~~~~~~~~~~~~~~~~~~~~~~~~

Communicability centrality measures the weighted sum of all walks between nodes, with exponentially decaying weights for longer walks. It is based on the matrix exponential of the supra-adjacency matrix.

**Mathematical Definition:**

.. math::

    c_i = \sum_j (e^{A_{\text{supra}}})_{ij}

where :math:`A_{\text{supra}}` is the supra-adjacency matrix.

**Best for:**

* Measuring node importance based on all possible paths
* Accounting for redundancy in communication channels
* Networks where multiple paths contribute to influence
* Global network analysis

**Complexity:** :math:`O(n^2)` for sparse matrices using Krylov subspace methods, where :math:`n` is the total number of node-layer pairs

**Reference:** Estrada, E., & Hatano, N. (2008). Communicability in complex networks. Physical Review E, 77(3), 036111.

.. autofunction:: py3plex.algorithms.multilayer_algorithms.supra_matrix_function_centrality.communicability_centrality

Katz Centrality
~~~~~~~~~~~~~~~

Katz centrality measures node influence by accounting for all paths with exponentially decaying weights, controlled by an attenuation parameter :math:`\alpha`. It includes an exogenous influence term to ensure all nodes have non-zero centrality.

**Mathematical Definition:**

.. math::

    x = (I - \alpha A_{\text{supra}})^{-1} \mathbf{1}

where :math:`\alpha < 1/\lambda_{\max}(A_{\text{supra}})` is the attenuation parameter and :math:`\mathbf{1}` is a vector of ones.

**Best for:**

* Controlling the influence of distant connections via :math:`\alpha`
* Networks with clear source-sink patterns
* Comparing with PageRank and eigenvector centrality
* Tunable sensitivity to network topology

**Complexity:** :math:`O(n^2)` for sparse linear system solving, where :math:`n` is the total number of node-layer pairs

**Reference:** Katz, L. (1953). A new status index derived from sociometric analysis. Psychometrika, 18(1), 39-43.

.. autofunction:: py3plex.algorithms.multilayer_algorithms.supra_matrix_function_centrality.katz_centrality

Usage Examples
--------------

Basic Usage
~~~~~~~~~~~

Compute both centrality measures on a multiplex network:

.. code-block:: python

    from py3plex.core import random_generators
    from py3plex.algorithms.multilayer_algorithms.supra_matrix_function_centrality import (
        communicability_centrality,
        katz_centrality,
    )

    # Create a random multiplex network
    net = random_generators.random_multiplex_ER(50, 3, 0.1)
    
    # Get the supra-adjacency matrix
    A = net.get_supra_adjacency_matrix()
    
    # Compute communicability centrality
    comm_scores = communicability_centrality(A, normalize=True)
    print(f"Communicability centrality computed for {len(comm_scores)} node-layer pairs")
    print(f"Top 5 node-layer pairs: {sorted(enumerate(comm_scores), key=lambda x: x[1], reverse=True)[:5]}")
    
    # Compute Katz centrality with automatic alpha
    katz_scores = katz_centrality(A, alpha=None)
    print(f"Katz centrality computed for {len(katz_scores)} node-layer pairs")
    print(f"Normalization check: sum = {katz_scores.sum():.6f}")

Advanced Usage
~~~~~~~~~~~~~~

Control computation parameters and compare results:

.. code-block:: python

    from py3plex.core import random_generators
    from py3plex.algorithms.multilayer_algorithms.supra_matrix_function_centrality import (
        communicability_centrality,
        katz_centrality,
    )
    import numpy as np

    # Create a network
    net = random_generators.random_multiplex_ER(100, 4, 0.08)
    A = net.get_supra_adjacency_matrix()
    
    # Communicability with sparse computation
    comm_sparse = communicability_centrality(
        A,
        normalize=True,
        use_sparse=True,  # Force sparse computation
        max_iter=100,
        tol=1e-6
    )
    
    # Katz with custom alpha and beta
    katz_custom = katz_centrality(
        A,
        alpha=0.05,      # Small attenuation for long-range effects
        beta=1.0,        # Uniform exogenous influence
        tol=1e-6
    )
    
    # Compare correlation between methods
    correlation = np.corrcoef(comm_sparse, katz_custom)[0, 1]
    print(f"Correlation between communicability and Katz: {correlation:.3f}")
    
    # Find nodes with high communicability but low Katz
    diff = comm_sparse - katz_custom
    divergent_nodes = np.argsort(np.abs(diff))[-10:]
    print(f"Node-layer pairs with largest differences: {divergent_nodes}")

Loading from Network Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apply to real network data:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.multilayer_algorithms.supra_matrix_function_centrality import (
        communicability_centrality,
        katz_centrality,
    )

    # Load a multiplex network from edge list
    net = multinet.multi_layer_network().load_network(
        "data/example_multiplex.edgelist",
        input_type="multiplex_edges"
    )
    
    # Get supra-adjacency matrix
    A = net.get_supra_adjacency_matrix()
    
    # Compute centralities
    comm_scores = communicability_centrality(A, normalize=True)
    katz_scores = katz_centrality(A, alpha=None)
    
    # Get node-layer mapping to interpret results
    node_layer_pairs = list(net.get_nodes())
    top_k = 10
    
    print(f"Top {top_k} nodes by communicability centrality:")
    for idx in np.argsort(comm_scores)[-top_k:][::-1]:
        node, layer = node_layer_pairs[idx]
        print(f"  Node {node} in layer {layer}: {comm_scores[idx]:.6f}")

Performance Considerations
--------------------------

Matrix Size and Sparsity
~~~~~~~~~~~~~~~~~~~~~~~~~

* **Small networks (< 100 node-layer pairs):** Dense computation is faster
* **Medium networks (100-1000 pairs):** Sparse computation recommended
* **Large networks (> 1000 pairs):** Only sparse computation is feasible

The implementation automatically chooses the appropriate method based on matrix size when ``use_sparse=True`` is set for communicability centrality.

Memory Usage
~~~~~~~~~~~~

* **Communicability:** Requires :math:`O(n)` memory for Krylov subspace methods (sparse) or :math:`O(n^2)` for dense matrices
* **Katz:** Requires :math:`O(n^2)` memory for sparse linear system factorization

Computation Time
~~~~~~~~~~~~~~~~

Typical computation times on a standard workstation:

* **50 node-layer pairs:** < 0.1 seconds
* **150 node-layer pairs (50 nodes × 3 layers):** 0.5-1 second
* **500 node-layer pairs:** 5-10 seconds
* **1500 node-layer pairs (500 nodes × 3 layers):** 30-60 seconds

For very large networks, consider:

* Using higher tolerance values (e.g., ``tol=1e-4``)
* Focusing on specific layers rather than the full supra-matrix
* Using other centrality measures like degree or PageRank

Parameter Guidelines
--------------------

Communicability Centrality
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``normalize=True``: Always recommended for comparing across networks
* ``use_sparse=True``: Recommended for networks > 100 node-layer pairs
* ``max_iter=100``: Default is sufficient for most networks
* ``tol=1e-6``: Default provides good accuracy; increase for speed

Katz Centrality
~~~~~~~~~~~~~~~

* ``alpha=None``: Auto-compute as 0.85/λ_max (recommended)
* ``alpha=0.01-0.1``: Manual values for custom attenuation
* ``beta=1.0``: Default uniform exogenous influence (rarely needs changing)
* ``tol=1e-6``: Eigenvalue computation tolerance

Common Issues and Solutions
---------------------------

Matrix Not Square
~~~~~~~~~~~~~~~~~

**Error:** ``Py3plexMatrixError: Matrix must be square``

**Solution:** Ensure you're passing the supra-adjacency matrix from ``get_supra_adjacency_matrix()``, not an edge list or other format.

Alpha Too Large
~~~~~~~~~~~~~~~

**Error:** ``Py3plexMatrixError: Alpha must be less than 1/lambda_max``

**Solution:** Use ``alpha=None`` for automatic computation, or manually compute lambda_max and choose a smaller alpha.

Memory Error
~~~~~~~~~~~~

**Error:** ``MemoryError`` during computation

**Solution:** 

* Use ``use_sparse=True`` for communicability centrality
* Ensure your network is not too dense
* Consider analyzing individual layers separately
* Increase available system memory

See Also
--------

* :ref:`Multilayer Centrality Measures <centrality>` - Overview of all centrality measures
* :ref:`Algorithm Selection Guide <algorithm_guide>` - Choosing the right algorithm
* :ref:`Multiplex Network Concepts <multilayer_concepts>` - Understanding multilayer networks

References
----------

* Estrada, E., & Hatano, N. (2008). Communicability in complex networks. Physical Review E, 77(3), 036111.
* Katz, L. (1953). A new status index derived from sociometric analysis. Psychometrika, 18(1), 39-43.
* De Domenico, M., Solé-Ribalta, A., Cozzo, E., Kivelä, M., Moreno, Y., Porter, M. A., ... & Arenas, A. (2013). Mathematical formulation of multilayer networks. Physical Review X, 3(4), 041022.
