Benchmarking & Performance
==========================

Performance characteristics and optimization strategies for py3plex.

Network Scale Guidelines
-------------------------

py3plex is optimized for research-scale networks:

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

This reduces memory usage by 10-100x for typical networks.

Batch Operations
~~~~~~~~~~~~~~~~

Process multiple operations together:

.. code-block:: python

    from py3plex.dsl import Q
    
    # Compute multiple metrics at once
    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality", "clustering")
         .execute(network)
    )

Avoid repeated single-metric computations.

Use Arrow/Parquet for I/O
~~~~~~~~~~~~~~~~~~~~~~~~~~

For large datasets:

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

**TODO:** Add benchmark results from benchmarks/ directory

* Algorithm runtimes vs. network size
* Memory usage profiles
* Comparison with other tools

Running Benchmarks
------------------

Run benchmarks yourself:

.. code-block:: bash

    cd benchmarks
    python run_benchmarks.py

See the `benchmarks/` directory in the repository for benchmark scripts.

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
