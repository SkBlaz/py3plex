Performance and Scalability Best Practices
============================================

This guide provides recommendations for optimizing Py3plex performance and handling large multilayer networks.

.. contents:: Table of Contents
   :local:
   :depth: 2

Network Scale Guidelines
------------------------

Py3plex is optimized for research-scale networks. This table shows expected performance characteristics:

.. list-table:: Network Scale Performance
   :header-rows: 1
   :widths: 20 20 20 40

   * - Network Size
     - Performance
     - Visualization
     - Recommendations
   * - Small (<100 nodes)
     - Excellent
     - Fast, detailed
     - Use dense visualization mode
   * - Medium (100-1k nodes)
     - Good
     - Fast, balanced
     - Default settings work well
   * - Large (1k-10k nodes)
     - Good
     - Slower, minimal
     - Use sparse matrices, sampling
   * - Very Large (>10k nodes)
     - Variable
     - Very slow
     - Sampling required, use NetworkX/igraph

Sparse Matrix Backend
---------------------

Why Sparse Matrices?
~~~~~~~~~~~~~~~~~~~~

Most real-world networks are **sparse** (few edges compared to possible edges). Sparse matrices:

* **Reduce memory usage** by 10-100x for typical networks
* **Speed up** matrix operations (multiplication, inversion)
* **Enable** analysis of larger networks

**Example:**

.. code-block:: python

    import numpy as np
    from scipy.sparse import csr_matrix
    
    # Dense representation (10k × 10k network)
    # Memory: 10,000^2 × 8 bytes = 800 MB
    
    # Sparse representation (with 1% density)
    # Memory: ~8 MB (100x reduction!)

Automatic Sparse Matrix Usage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Py3plex **automatically uses sparse matrices** for:

* Supra-adjacency matrix operations
* Large network storage (>1000 nodes)
* Matrix-based algorithms (PageRank, spectral methods)

**Verify sparse usage:**

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network()
    network.load_network("large_network.csv", input_type="multiedgelist")
    
    # Get sparse adjacency matrix
    adj_sparse = network.get_sparse_adjacency_matrix()
    
    print(f"Matrix size: {adj_sparse.shape}")
    print(f"Non-zero entries: {adj_sparse.nnz}")
    print(f"Sparsity: {1 - adj_sparse.nnz / (adj_sparse.shape[0]**2):.2%}")

Force Sparse Operations
~~~~~~~~~~~~~~~~~~~~~~~~

For custom algorithms, explicitly use sparse operations:

.. code-block:: python

    from scipy.sparse import csr_matrix, lil_matrix
    import numpy as np
    
    # Create sparse adjacency matrix
    adj = lil_matrix((n_nodes, n_nodes))
    
    for u, v in network.core_network.edges():
        i, j = node_to_idx[u], node_to_idx[v]
        adj[i, j] = 1
        adj[j, i] = 1  # Undirected
    
    # Convert to efficient format for operations
    adj_csr = adj.tocsr()
    
    # Sparse matrix operations are MUCH faster
    result = adj_csr @ adj_csr  # Matrix multiplication
    eigvals = scipy.sparse.linalg.eigs(adj_csr, k=10)  # Top eigenvalues

Network Sampling
----------------

When to Sample
~~~~~~~~~~~~~~

Sampling is necessary when:

* Network is too large to visualize (>5k nodes)
* Algorithms take too long (>10 minutes)
* Memory usage is excessive (>8GB RAM)
* You need quick exploratory analysis

Random Node Sampling
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import random
    from py3plex.core import multinet
    
    # Load full network
    network = multinet.multi_layer_network()
    network.load_network("large_network.csv", input_type="multiedgelist")
    
    # Sample 1000 random nodes
    all_nodes = list(network.get_nodes())
    sample_nodes = random.sample(all_nodes, min(1000, len(all_nodes)))
    
    # Create subnetwork
    subnetwork = network.get_subnetwork(sample_nodes)
    
    print(f"Original: {len(all_nodes)} nodes")
    print(f"Sample: {len(sample_nodes)} nodes")
    print(f"Sampling ratio: {len(sample_nodes)/len(all_nodes):.1%}")

Stratified Sampling (Preserve Layer Distribution)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Sample proportionally from each layer
    layers = network.get_layer_names()
    sample_nodes_per_layer = {}
    
    for layer in layers:
        layer_nodes = [n for n in network.get_nodes() if n[1] == layer]
        sample_size = len(layer_nodes) // 10  # 10% sample
        sample_nodes_per_layer[layer] = random.sample(layer_nodes, sample_size)
    
    # Combine samples
    all_samples = [node for nodes in sample_nodes_per_layer.values() for node in nodes]
    subnetwork = network.get_subnetwork(all_samples)

Hub-Based Sampling (Keep Important Nodes)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    
    # Sample high-degree nodes (hubs)
    degrees = dict(network.core_network.degree())
    
    # Sort by degree and take top 1000
    sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
    hub_nodes = [node for node, deg in sorted_nodes[:1000]]
    
    subnetwork = network.get_subnetwork(hub_nodes)
    print(f"Sampled top 1000 hubs")

Algorithm Optimization
----------------------

Choose Efficient Algorithms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some algorithms scale better than others:

.. list-table:: Algorithm Complexity
   :header-rows: 1
   :widths: 30 20 50

   * - Algorithm
     - Complexity
     - Recommendations
   * - Degree centrality
     - O(n + m)
     - Fast, use freely
   * - Betweenness centrality
     - O(nm)
     - Slow for large networks, sample first
   * - PageRank
     - O(iterations × m)
     - Fast if sparse, limit iterations
   * - Community detection (Louvain)
     - O(m log n)
     - Fast, recommended
   * - Shortest paths (all pairs)
     - O(n²m)
     - Very slow, use sampling or approximate
   * - Force-directed layout
     - O(n²)
     - Slow for >5k nodes, use alternatives

**Example - Fast centrality:**

.. code-block:: python

    import networkx as nx
    
    G = network.core_network
    
    # FAST: Degree centrality
    degree_cent = nx.degree_centrality(G)  # O(n+m) - instant
    
    # SLOW: Betweenness centrality
    # For large networks, sample first or use approximate algorithm
    if G.number_of_nodes() < 1000:
        between_cent = nx.betweenness_centrality(G)
    else:
        # Use approximate algorithm
        between_cent = nx.betweenness_centrality(G, k=100)  # Sample 100 nodes

Limit Algorithm Iterations
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    
    # PageRank with iteration limit
    pagerank = nx.pagerank(
        network.core_network,
        max_iter=50,        # Limit iterations
        tol=1e-4            # Tolerance for convergence
    )
    
    # Community detection with resolution limit
    from py3plex.algorithms.community_detection import community_louvain
    communities = community_louvain.best_partition(
        network.core_network,
        resolution=1.0      # Adjust resolution parameter
    )

Parallel Processing
-------------------

Multi-Core Processing
~~~~~~~~~~~~~~~~~~~~~

Use joblib for parallel node/edge operations:

.. code-block:: python

    from joblib import Parallel, delayed
    import networkx as nx
    
    def compute_node_centrality(node, graph):
        """Compute centrality for a single node."""
        # Custom centrality computation
        neighbors = list(graph.neighbors(node))
        return node, len(neighbors)
    
    # Parallel processing
    nodes = list(network.core_network.nodes())
    results = Parallel(n_jobs=-1)(  # Use all cores
        delayed(compute_node_centrality)(node, network.core_network)
        for node in nodes
    )
    
    centralities = dict(results)

GPU Acceleration (Advanced)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For very large networks, use GPU acceleration:

.. code-block:: bash

    # Install CuPy for GPU NumPy operations
    pip install cupy-cuda11x  # Replace 11x with CUDA version

.. code-block:: python

    # Requires NVIDIA GPU with CUDA
    try:
        import cupy as cp
        
        # Convert to GPU array
        adj_matrix = network.get_sparse_adjacency_matrix().toarray()
        gpu_adj = cp.array(adj_matrix)
        
        # GPU-accelerated matrix operations
        gpu_result = cp.dot(gpu_adj, gpu_adj)
        
        # Transfer back to CPU
        result = cp.asnumpy(gpu_result)
        
    except ImportError:
        print("CuPy not available, using CPU")

Visualization Optimization
---------------------------

Reduce Visual Complexity
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default
    
    # For large networks (>1000 nodes)
    draw_multilayer_default(
        network.get_layers(),
        node_size=3,              # Tiny nodes
        labels=False,             # No labels
        edge_size=0.3,            # Thin edges
        alphalevel=0.2,           # Very transparent
        remove_isolated_nodes=True  # Remove disconnected
    )

Save to File Instead of Display
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import matplotlib.pyplot as plt
    
    # Don't show interactively (faster)
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    draw_multilayer_default(
        network.get_layers(),
        display=False,  # Don't show
        axis=ax
    )
    
    # Save directly to file
    plt.savefig('network.png', dpi=150, bbox_inches='tight')
    plt.close()  # Free memory

Use Lower Resolution
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # For quick exploration, use low DPI
    plt.figure(figsize=(8, 6), dpi=72)  # Low resolution
    
    # For publications, use high DPI
    plt.figure(figsize=(10, 8), dpi=300)  # High resolution

Memory Management
-----------------

Monitor Memory Usage
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import psutil
    import os
    
    def get_memory_usage():
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    
    print(f"Memory before loading: {get_memory_usage():.1f} MB")
    
    network = multinet.multi_layer_network()
    network.load_network("large_network.csv", input_type="multiedgelist")
    
    print(f"Memory after loading: {get_memory_usage():.1f} MB")

Free Memory When Done
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Delete network when no longer needed
    del network
    
    # Force garbage collection
    import gc
    gc.collect()

Use Generators Instead of Lists
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # BAD: Loads all nodes into memory
    all_nodes = list(network.get_nodes())
    for node in all_nodes:
        process(node)
    
    # GOOD: Processes nodes one at a time
    for node in network.get_nodes():
        process(node)

Batch Processing
----------------

Process Networks in Batches
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For multiple networks:

.. code-block:: python

    import os
    import gc
    
    network_files = ["net1.csv", "net2.csv", "net3.csv", ...]
    
    results = []
    for i, file in enumerate(network_files):
        print(f"Processing {i+1}/{len(network_files)}: {file}")
        
        # Load network
        network = multinet.multi_layer_network()
        network.load_network(file, input_type="multiedgelist")
        
        # Compute statistics
        result = analyze_network(network)
        results.append(result)
        
        # Free memory
        del network
        gc.collect()
        
        # Save intermediate results every 10 networks
        if (i + 1) % 10 == 0:
            save_results(results, f"results_batch_{i+1}.json")

Benchmark Results
-----------------

Performance Benchmarks (2025)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tested on: Intel i7-10700K, 32GB RAM, Python 3.10

.. list-table:: Operation Performance
   :header-rows: 1
   :widths: 40 15 15 15 15

   * - Operation
     - 100 nodes
     - 1k nodes
     - 10k nodes
     - 100k nodes
   * - Load from CSV
     - <1s
     - <1s
     - 2s
     - 20s
   * - Basic statistics
     - <1s
     - <1s
     - <1s
     - 3s
   * - Degree centrality
     - <1s
     - <1s
     - 1s
     - 10s
   * - PageRank
     - <1s
     - <1s
     - 2s
     - 25s
   * - Louvain communities
     - <1s
     - 1s
     - 5s
     - 60s
   * - Visualization (sparse)
     - <1s
     - 2s
     - 15s
     - N/A*

\* Visualization not recommended for >10k nodes without sampling

Scaling Recommendations
~~~~~~~~~~~~~~~~~~~~~~~

Based on network size:

**<1k nodes:**
  * Use any algorithms
  * Full visualization
  * No sampling needed

**1k-10k nodes:**
  * Use sparse matrices
  * Minimal visualization
  * Sample for some algorithms

**10k-100k nodes:**
  * Sparse matrices required
  * Sample for visualization
  * Use approximate algorithms
  * Consider igraph for speed

**>100k nodes:**
  * Use specialized tools (igraph, graph-tool, NetworKit)
  * Sample heavily for Py3plex operations
  * Focus on specific analyses

Alternative Tools for Scale
----------------------------

When Py3plex Isn't Enough
~~~~~~~~~~~~~~~~~~~~~~~~~~

For networks >100k nodes, consider:

**igraph** (C-based, very fast):

.. code-block:: python

    import igraph as ig
    
    # 10-100x faster for large networks
    g = ig.Graph.Read_GraphML("large_network.graphml")
    communities = g.community_multilevel()
    
    # Export back to Py3plex if needed
    # (via GraphML or edge list)

**graph-tool** (C++, fastest):

.. code-block:: python

    import graph_tool.all as gt
    
    # Fastest for >1M edges
    g = gt.load_graph("large_network.graphml")
    communities = gt.community_structure.minimize_blockmodel_dl(g)

**NetworKit** (C++, parallel):

.. code-block:: python

    import networkit as nk
    
    # Excellent for parallel algorithms
    G = nk.readGraph("large_network.edgelist", nk.Format.EdgeList)
    communities = nk.community.detectCommunities(G)

Quick Performance Checklist
----------------------------

Before Running on Large Network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    ☐ Enable sparse matrices (automatic for most ops)
    ☐ Sample network if >10k nodes
    ☐ Choose efficient algorithms (degree > betweenness)
    ☐ Limit visualization detail
    ☐ Monitor memory usage
    ☐ Use batch processing for multiple networks
    ☐ Consider alternative tools if >100k nodes

Optimization Order
~~~~~~~~~~~~~~~~~~

1. **Use sparse matrices** (biggest impact, usually automatic)
2. **Sample network** (if >10k nodes)
3. **Choose efficient algorithms** (avoid O(n³) operations)
4. **Parallelize** (if multi-core available)
5. **GPU acceleration** (only if CUDA GPU available)

Next Steps
----------

- :doc:`dependencies_guide` - Install optional performance packages
- :doc:`visualization_guide` - Optimize visualizations
- :doc:`networkx_interop` - Use NetworkX algorithms
- :doc:`/tutorials/csv_loading` - Efficient data loading

For performance issues, open an issue on `GitHub Issues <https://github.com/SkBlaz/py3plex/issues>`_.
