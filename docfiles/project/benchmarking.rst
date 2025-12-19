Benchmarking & Performance
==========================

Performance characteristics, runtime expectations, and practical optimization strategies for py3plex.

Network Scale Guidelines
------------------------

py3plex targets research-scale multilayer networks. Use the ranges below as directional guidance rather than hard limits; structure (density, layer coupling) has a bigger impact than raw node counts.

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
     - Sampling required

Performance Tips
----------------

Use Sparse Matrices
~~~~~~~~~~~~~~~~~~~

For large networks, use sparse matrix representations:

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network(sparse=True)

This typically reduces memory usage by 10-100x for moderately sparse graphs.

Batch Operations
~~~~~~~~~~~~~~~~

Process multiple operations together instead of issuing separate passes:

.. code-block:: python

    from py3plex.dsl import Q
    
    # Compute multiple metrics at once
    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality", "clustering")
         .execute(network)
    )

Avoid repeated single-metric computations when they can be combined.

Use Arrow/Parquet for I/O
~~~~~~~~~~~~~~~~~~~~~~~~~~

For large datasets, prefer columnar formats over CSV:

.. code-block:: python

    import pyarrow.parquet as pq
    
    # Save
    table = pq.write_table(edges_table, 'network.parquet')
    
    # Load (much faster than CSV)
    table = pq.read_table('network.parquet')

Parallel Processing
~~~~~~~~~~~~~~~~~~~

For Node2Vec and other CPU-intensive algorithms:

.. code-block:: python

    from py3plex.wrappers import train_node2vec
    
    embeddings = train_node2vec(
        network,
        workers=8  # Use multiple CPU cores
    )

Benchmark Results
-----------------

Performance benchmarks for common operations on synthetic multilayer networks. Use these results for rough planning, not as guarantees.

**Test Environment**

* CPU: Intel Core i7-9700K @ 3.6GHz (8 cores)
* RAM: 32 GB DDR4
* Python: 3.10
* py3plex: v1.0.0

**Methodology & Caveats**

* Synthetic multilayer graphs with comparable density across sizes
* Single-run wall-clock timings on the hardware above
* Runtimes vary materially with density, weight usage, and layer count; rerun locally for precise estimates

Algorithm Runtimes vs. Network Size
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Community Detection (Louvain)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table:: Louvain Algorithm Runtime
   :header-rows: 1
   :widths: 25 25 25 25

   * - Nodes
     - Edges
     - Layers
     - Runtime
   * - 100
     - 500
     - 3
     - 0.05s
   * - 1,000
     - 5,000
     - 3
     - 0.3s
   * - 10,000
     - 50,000
     - 3
     - 4.2s
   * - 100,000
     - 500,000
     - 3
     - 58s

Centrality Computation (Betweenness)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table:: Betweenness Centrality Runtime
   :header-rows: 1
   :widths: 25 25 25 25

   * - Nodes
     - Edges
     - Layers
     - Runtime
   * - 100
     - 500
     - 3
     - 0.12s
   * - 1,000
     - 5,000
     - 3
     - 8.5s
   * - 10,000
     - 50,000
     - 3
     - 1,240s (21 min)
   * - 100,000
     - 500,000
     - 3
     - N/A (too slow)

*Note: Betweenness is O(n³); use approximation methods for large networks.*

Node2Vec Embeddings
^^^^^^^^^^^^^^^^^^^

.. list-table:: Node2Vec Runtime (128-dim, 10 walks/node)
   :header-rows: 1
   :widths: 25 25 25 25

   * - Nodes
     - Edges
     - Layers
     - Runtime
   * - 100
     - 500
     - 3
     - 2.3s
   * - 1,000
     - 5,000
     - 3
     - 18s
   * - 10,000
     - 50,000
     - 3
     - 245s (4 min)
   * - 100,000
     - 500,000
     - 3
     - 3,200s (53 min)

Dynamics Simulation (SIR)
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table:: SIR Simulation Runtime (100 steps)
   :header-rows: 1
   :widths: 25 25 25 25

   * - Nodes
     - Edges
     - Layers
     - Runtime
   * - 100
     - 500
     - 3
     - 0.8s
   * - 1,000
     - 5,000
     - 3
     - 4.5s
   * - 10,000
     - 50,000
     - 3
     - 52s
   * - 100,000
     - 500,000
     - 3
     - 680s (11 min)

Memory Usage Profiles
~~~~~~~~~~~~~~~~~~~~~

.. list-table:: Peak Memory Usage
   :header-rows: 1
   :widths: 25 25 25 25

   * - Nodes
     - Edges
     - Dense Storage
     - Sparse Storage
   * - 100
     - 500
     - 2 MB
     - 0.5 MB
   * - 1,000
     - 5,000
     - 24 MB
     - 2 MB
   * - 10,000
     - 50,000
     - 2.4 GB
     - 18 MB
   * - 100,000
     - 500,000
     - 240 GB
     - 180 MB

**Key Insight:** Sparse storage reduces memory by 10-1000x for typical moderately sparse networks (adjacency-like storage, unweighted).

Comparison with Other Tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Community Detection: py3plex vs. NetworkX
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table:: Louvain Performance Comparison (1k nodes, 5k edges, single layer)
   :header-rows: 1
   :widths: 33 33 34

   * - Tool
     - Runtime
     - Notes
   * - py3plex
     - 0.3s
     - Multilayer-aware
   * - NetworkX + python-louvain
     - 0.2s
     - Single-layer only
   * - graph-tool
     - 0.08s
     - C++ backend, faster

**Verdict:** py3plex is competitive on single-layer inputs while adding multilayer capability others lack.

Node Embeddings: py3plex vs. node2vec
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. list-table:: Node2Vec Performance (1k nodes, 128-dim, 10 walks)
   :header-rows: 1
   :widths: 33 33 34

   * - Tool
     - Runtime
     - Notes
   * - py3plex
     - 18s
     - Python wrapper
   * - node2vec (original)
     - 15s
     - C++ implementation
   * - Gensim
     - 12s
     - Optimized Word2Vec

**Verdict:** py3plex wraps established libraries (e.g., gensim); performance is comparable, with minor Python overhead expected.

**Benchmarking Notes**

* Results vary with network structure (density, clustering, layer coupling).
* Algorithmic scaling differs (linear vs. quadratic vs. cubic) and dominates at large sizes.
* Treat these tables as directional; rerun locally for reliable planning.
* For the most accurate estimates, run the bundled scripts on your hardware and data.

Running Benchmarks
------------------

Reproduce or extend the tables above with the bundled scripts:

.. code-block:: bash

    cd benchmarks
    python run_benchmarks.py

Profiling Your Code
-------------------

Use Python profiling tools:

.. code-block:: python

    import cProfile
    import pstats
    
    # Profile your analysis
    cProfile.run('your_analysis_function(network)', 'profile_stats')
    
    # View results
    stats = pstats.Stats('profile_stats')
    stats.sort_stats('cumulative')
    stats.print_stats(20)

Memory Profiling
~~~~~~~~~~~~~~~~

.. code-block:: bash

    pip install memory_profiler
    python -m memory_profiler your_script.py

Optimization Strategies
-----------------------

For Large Networks
~~~~~~~~~~~~~~~~~~

1. **Sample the network** for exploratory analysis
2. **Use layer-specific analysis** instead of full multilayer
3. **Compute metrics incrementally** rather than all at once
4. **Cache intermediate results**

For Repeated Analysis
~~~~~~~~~~~~~~~~~~~~~

1. **Precompute and save** expensive metrics
2. **Use config-driven workflows** for reproducibility
3. **Batch process** multiple networks

For Production
~~~~~~~~~~~~~~

1. **Use Docker containers** for consistent environments
2. **Implement monitoring** for long-running jobs
3. **Add checkpointing** for crash recovery

See :doc:`../deployment/cli_and_docker` for deployment best practices.

Hardware Recommendations
------------------------

**Minimum:**

* 4 GB RAM
* 2 CPU cores
* Small networks (<1k nodes)

**Recommended:**

* 16 GB RAM
* 8 CPU cores
* Networks up to 10k nodes

**High-Performance:**

* 64+ GB RAM
* 16+ CPU cores
* Large networks (>10k nodes)

Next Steps
----------

* **Optimize I/O:** :doc:`../how-to/export_serialize`
* **Deploy to production:** :doc:`../deployment/cli_and_docker`
* **See deployment guide:** :doc:`../deployment/performance_scalability` (original full guide)
