Performance and Scalability
============================

This guide provides **best practices** for optimizing py3plex performance and scaling to **large networks**.

Memory Management
-----------------

Sparse vs Dense Matrices
~~~~~~~~~~~~~~~~~~~~~~~~~

**Always use sparse matrices for large networks:**

.. code-block:: python

    # Good: Sparse representation (default)
    supra_adj = network.get_supra_adjacency_matrix(sparse=True)
    
    # Bad: Dense representation for large networks
    # supra_adj = network.get_supra_adjacency_matrix(sparse=False)

**Memory requirements:**

* **Sparse:** :math:`O(m)` where :math:`m` is **number of edges**
* **Dense:** :math:`O(n^2)` where :math:`n` is **total nodes across layers**

**Rule of thumb:** Use **sparse** for networks with >1,000 nodes or density <10%

Matrix Construction Optimization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Avoid unnecessary matrix constructions:

.. code-block:: python

    # Bad: Repeated construction
    for iteration in range(100):
        adj = network.get_supra_adjacency_matrix()
        # ... use adj ...
    
    # Good: Construct once
    adj = network.get_supra_adjacency_matrix()
    for iteration in range(100):
        # ... use adj ...

Efficient Network Construction
-------------------------------

Batch Operations
~~~~~~~~~~~~~~~~

Add nodes and edges in **batches** rather than one at a time:

.. code-block:: python

    # Bad: Individual additions
    for edge in edge_list:
        network.add_edges([[edge[0], edge[1], edge[2], edge[3], edge[4]]], input_type='list')
    
    # Good: Batch addition
    network.add_edges(edge_list, input_type='list')

Pre-allocate Data Structures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When possible, provide all data at construction time:

.. code-block:: python

    # Efficient: Provide all edges at once
    network = multinet.multi_layer_network()
    network.add_edges(all_edges, input_type='list')
    
    # Less efficient: Incremental addition
    network = multinet.multi_layer_network()
    for edge_batch in batches:
        network.add_edges(edge_batch, input_type='list')

Algorithm Selection
-------------------

Time Complexity Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~~

Choose algorithms based on **network size**:

.. list-table::
   :header-rows: 1
   :widths: 30 20 25 25

   * - Network Size
     - Community Detection
     - Centrality
     - Embeddings
   * - Small (<1K nodes)
     - Any
     - Any (including betweenness)
     - Node2Vec (full)
   * - Medium (1K-10K)
     - Louvain
     - Degree, PageRank
     - Node2Vec (reduced walks)
   * - Large (10K-100K)
     - Louvain, Label Prop
     - Degree only
     - DeepWalk (sampling)
   * - Very Large (>100K)
     - Label Prop
     - Degree
     - Skip or sample

Avoid Expensive Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~

**O(n²) or worse complexity:**

* **Full betweenness centrality**
* **All-pairs shortest paths**
* **Closeness centrality** on large networks
* **Dense matrix operations**

**Alternative approaches:**

.. code-block:: python

    # Instead of betweenness on full network
    # betweenness = calc.multilayer_betweenness_centrality()  # O(nm)
    
    # Use degree as proxy or sample
    degree = calc.overlapping_degree_centrality()  # O(n+m)
    
    # Or sample nodes
    import random
    sample_nodes = random.sample(list(network.get_nodes()), k=100)
    # Compute betweenness on induced subgraph

Parallel Processing
-------------------

Using Joblib for Parallelization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

py3plex operations can often be parallelized:

.. code-block:: python

    from joblib import Parallel, delayed
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    # Parallel layer statistics
    layers = network.get_layers()
    densities = Parallel(n_jobs=-1)(
        delayed(mls.layer_density)(network, layer) 
        for layer in layers
    )

NumPy Vectorization
~~~~~~~~~~~~~~~~~~~

Use **vectorized operations** instead of loops:

.. code-block:: python

    import numpy as np
    
    # Bad: Python loop
    degrees = {}
    for node in nodes:
        degrees[node] = sum(1 for neighbor in G.neighbors(node))
    
    # Good: Vectorized
    degrees = dict(G.degree())  # NetworkX optimized
    
    # Even better for matrices
    adj_matrix = network.get_adjacency_matrix(layer='layer1')
    degrees = np.asarray(adj_matrix.sum(axis=1)).flatten()

Visualization Optimization
--------------------------

Layout Computation
~~~~~~~~~~~~~~~~~~

Layout algorithms have **varying complexity**:

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Layout
     - Complexity
     - Best For
   * - Random
     - O(n)
     - Testing, very large networks
   * - Circular
     - O(n)
     - Small networks with clear order
   * - Spring/Force
     - O(n² × iterations)
     - <1,000 nodes
   * - ForceAtlas2
     - O(n log n × iterations)
     - 1,000-10,000 nodes

**Optimization strategies:**

.. code-block:: python

    # 1. Reduce iterations for approximate layout
    pos = dm.compute_layout(G, algorithm='force', iterations=50)  # Default is often 500
    
    # 2. Precompute and save layouts
    import pickle
    pos = dm.compute_layout(G, algorithm='force')
    with open('layout.pkl', 'wb') as f:
        pickle.dump(pos, f)
    
    # Load saved layout
    with open('layout.pkl', 'rb') as f:
        pos = pickle.load(f)

Reduce Visual Elements
~~~~~~~~~~~~~~~~~~~~~~

For large networks, reduce the number of rendered elements:

.. code-block:: python

    # 1. Sample edges
    import random
    all_edges = list(network.get_edges())
    sampled_edges = random.sample(all_edges, k=min(1000, len(all_edges)))
    
    # 2. Hide labels
    draw_network(network, show_labels=False)
    
    # 3. Use smaller node/edge sizes
    draw_network(network, node_size=1, edge_width=0.1)

Use Appropriate Visualization Type
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Match visualization to network size:

.. code-block:: python

    num_nodes = len(network.get_nodes())
    
    if num_nodes < 100:
        # Full network with labels
        draw_multilayer_default([network], display=True, show_labels=True)
    
    elif num_nodes < 1000:
        # Network without labels, force layout
        hairball_plot(network.core_network, layout_algorithm='force')
    
    elif num_nodes < 10000:
        # Diagonal projection
        draw_multilayer_default([network], layout_style='diagonal')
    
    else:
        # Matrix visualization
        adj = network.get_supra_adjacency_matrix(sparse=True)
        plt.spy(adj, markersize=0.1)
        plt.show()

I/O Optimization
----------------

Efficient File Formats
~~~~~~~~~~~~~~~~~~~~~~

Choose appropriate file formats:

.. list-table::
   :header-rows: 1
   :widths: 20 20 30 30

   * - Format
     - Load Speed
     - File Size
     - Best For
   * - gpickle
     - Fast
     - Small
     - Temporary storage, Python only
   * - GraphML
     - Medium
     - Large (XML)
     - Interchange, attributes
   * - Edge list
     - Fast
     - Small
     - Simple networks, no attributes
   * - GML
     - Slow
     - Medium
     - Legacy compatibility

**Recommendation:**

.. code-block:: python

    # For temporary storage (fastest)
    network.save_network("cache.gpickle", output_type="gpickle")
    network = multinet.multi_layer_network().load_network("cache.gpickle", input_type="gpickle")
    
    # For interchange (portable)
    network.save_network("data.graphml", output_type="graphml")

Streaming Large Files
~~~~~~~~~~~~~~~~~~~~~

For very large networks, process incrementally:

.. code-block:: python

    # Read edge list in chunks
    network = multinet.multi_layer_network()
    
    chunk_size = 10000
    with open('large_edgelist.txt', 'r') as f:
        chunk = []
        for line in f:
            chunk.append(line.strip().split())
            if len(chunk) >= chunk_size:
                network.add_edges(chunk, input_type='list')
                chunk = []
        
        # Add remaining edges
        if chunk:
            network.add_edges(chunk, input_type='list')

Benchmarking and Profiling
---------------------------

Time Your Code
~~~~~~~~~~~~~~

Use timing utilities to identify bottlenecks:

.. code-block:: python

    import time
    
    start = time.time()
    communities = community_louvain.best_partition(network.core_network)
    elapsed = time.time() - start
    print(f"Community detection took {elapsed:.2f} seconds")

Memory Profiling
~~~~~~~~~~~~~~~~

Monitor memory usage:

.. code-block:: python

    import tracemalloc
    
    tracemalloc.start()
    
    # Your code here
    adj = network.get_supra_adjacency_matrix(sparse=True)
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory: {current / 1024**2:.2f} MB")
    print(f"Peak memory: {peak / 1024**2:.2f} MB")
    tracemalloc.stop()

Line Profiling
~~~~~~~~~~~~~~

For detailed profiling:

.. code-block:: bash

    pip install line_profiler
    
    # Add @profile decorator to functions
    # Run with:
    kernprof -l -v script.py

Caching Strategies
------------------

Function-Level Caching
~~~~~~~~~~~~~~~~~~~~~~

Cache expensive computations:

.. code-block:: python

    from functools import lru_cache
    
    @lru_cache(maxsize=128)
    def expensive_centrality(network_hash, layer):
        """Cached centrality computation."""
        # Compute centrality
        return centrality_values

Network-Level Caching
~~~~~~~~~~~~~~~~~~~~~

Save intermediate results:

.. code-block:: python

    import os
    import pickle
    
    cache_file = 'communities_cache.pkl'
    
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            communities = pickle.load(f)
    else:
        communities = community_louvain.best_partition(network.core_network)
        with open(cache_file, 'wb') as f:
            pickle.dump(communities, f)

Best Practices Summary
----------------------

Network Size Guidelines
~~~~~~~~~~~~~~~~~~~~~~~

**< 1,000 nodes:**

* Any algorithm works
* Full visualization with labels
* Path-based centrality is fine
* Dense matrices acceptable

**1,000 - 10,000 nodes:**

* Use Louvain for communities
* Degree/PageRank for centrality
* Sparse matrices essential
* Diagonal projection visualization
* No labels in visualization

**10,000 - 100,000 nodes:**

* Label propagation for communities
* Degree centrality only
* Batch operations critical
* Matrix visualization
* Sample for exploration

**> 100,000 nodes:**

* Degree-based measures only
* Label propagation
* Incremental processing
* Sampling required
* Consider distributed tools for some tasks

Memory Checklist
~~~~~~~~~~~~~~~~

✅ Use sparse matrices (``sparse=True``)

✅ Batch add edges (not one at a time)

✅ Avoid repeated matrix construction

✅ Use generators instead of lists where possible

✅ Clear unused variables (``del variable``)

✅ Monitor memory with ``tracemalloc``

Speed Checklist
~~~~~~~~~~~~~~~

✅ Choose appropriate algorithms for network size

✅ Avoid O(n²) operations on large networks

✅ Use NumPy vectorization

✅ Cache expensive computations

✅ Precompute layouts

✅ Sample for exploration

✅ Profile to find bottlenecks

Benchmarking Examples
---------------------

Run the built-in benchmarks:

.. code-block:: bash

    cd benchmarks
    python config_benchmark.py

Create your own benchmarks:

.. code-block:: python

    from py3plex.core import multinet
    import time
    
    # Create networks of different sizes
    sizes = [100, 500, 1000, 5000]
    times = []
    
    for size in sizes:
        network = multinet.multi_layer_network()
        
        # Generate random edges
        import random
        edges = []
        for i in range(size * 5):  # ~5 edges per node
            edges.append([
                f'n{random.randint(0, size)}', 'L1',
                f'n{random.randint(0, size)}', 'L1', 1
            ])
        
        start = time.time()
        network.add_edges(edges, input_type='list')
        elapsed = time.time() - start
        
        times.append((size, elapsed))
        print(f"Size {size}: {elapsed:.3f}s")

Next Steps
----------

* :doc:`algorithm_guide` - Algorithm selection guide
* :doc:`basic_usage` - Usage examples
* :doc:`tutorials/multilayer_centrality` - Centrality tutorial
* Benchmark scripts in ``benchmarks/`` directory

Getting Help
------------

For performance issues:

1. Check this guide first
2. Run built-in benchmarks
3. Profile your code
4. Open an issue with profiling results
