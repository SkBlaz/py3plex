Graph Programs: First-Class Compositional Objects
=================================================

**Goal:** Use Graph Programs to build typed, optimizable, reproducible query pipelines that can be inspected, composed, and cached before execution.

.. admonition:: 🎯 Key Concept
   :class: tip

   Graph Programs turn DSL v2 queries into **first-class objects** with:
   
   * Canonical AST representation
   * Stable hash for reproducibility
   * Type signatures for validation
   * Cost model metadata
   * Rewrite-based optimization
   * Provenance tracking

Prerequisites
-------------

* Understanding of DSL v2 (see :doc:`query_with_dsl`)
* A loaded ``multi_layer_network`` object
* Python 3.8+

Core Concepts
-------------

What is a GraphProgram?
^^^^^^^^^^^^^^^^^^^^^^^

A ``GraphProgram`` is an **immutable, typed representation** of a DSL query pipeline that can be:

* **Composed**: Chain multiple programs together
* **Optimized**: Apply rewrite rules to reduce cost
* **Explained**: Inspect pipeline steps and costs
* **Diffed**: Compare two programs
* **Cached**: Store results with reproducibility guarantees
* **Executed**: Run against a network

Creating a GraphProgram
^^^^^^^^^^^^^^^^^^^^^^^

Use the ``.to_program()`` method on any DSL query:

.. code-block:: python

    from py3plex.dsl import Q, L
    from py3plex.dsl.program import GraphProgram

    # Build a program without executing
    program = (Q.nodes()
        .from_layers(L["social"])
        .compute("degree", "betweenness_centrality")
        .top_k(10, "degree")
        .to_program())

    # Inspect the program
    print(f"Program hash: {program.hash()}")
    print(f"Type signature: {program.type_signature}")

Type System
-----------

Every GraphProgram has a type signature inferred from its operations. The type system includes:

* ``GraphType``: The full multilayer network
* ``NodeSetType``: Set of nodes (possibly filtered by layer)
* ``EdgeSetType``: Set of edges
* ``PartitionType``: Community partition
* ``TableType``: Tabular results (like pandas DataFrame)
* ``DistributionType[T]``: Uncertainty-quantified values
* ``ScalarType``: Single numeric/string value
* ``TimeSeriesType``: Temporal sequence

Type checking happens automatically:

.. code-block:: python

    from py3plex.dsl.program import type_check, infer_type

    # Check if program is well-typed
    is_valid = type_check(program.canonical_ast)
    
    # Infer the output type
    output_type = infer_type(program.canonical_ast)
    print(f"Output type: {output_type}")

Optimization with Rewrite Rules
--------------------------------

GraphPrograms can be optimized using **correctness-preserving rewrite rules**:

Optimization Levels
^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    # Basic optimization (safe rewrites only)
    optimized = program.optimize(level=1)
    
    # Aggressive optimization
    optimized = program.optimize(level=2, objective="min_time")
    
    # Budget-constrained optimization
    optimized = program.optimize(budget="10s", objective="min_time")

Available Rewrite Rules
^^^^^^^^^^^^^^^^^^^^^^^

**Pushdown/Fusion Rules:**

1. Push ``WHERE`` before ``COMPUTE`` (avoids computing filtered nodes)
2. Fuse multiple ``COMPUTE`` into one pass
3. Fuse multiple ``WHERE`` clauses
4. Push ``LIMIT`` early
5. Eliminate unused metrics

**Layer Distributivity Rules:**

6. Move ``per_layer()`` early for parallelization
7. Fuse nested ``per_layer()``
8. Convert ``group_by(layer)`` to canonical form

**UQ-Aware Rules:**

9. Move deterministic operations inside UQ to reduce sampling cost
10. Hoist reporting operations outside UQ
11. Cache identical subprograms in UQ samples

**Community-Specific Rules:**

12. Fuse community detection + annotation
13. Optimize community filtering to partition slicing
14. Batch multiple community metrics

**Common Subexpression Elimination:**

15. Detect and cache common subexpressions
16. Mark expensive metrics for caching

Cost Model
----------

Every operator has cost estimates for time and memory:

.. code-block:: python

    from py3plex.dsl.program import CostModel, GraphStats
    
    # Create cost model
    cost_model = CostModel()
    
    # Estimate program cost
    stats = GraphStats(num_nodes=1000, num_edges=5000, num_layers=2)
    cost = cost_model.estimate_program_cost(program, stats)
    
    print(f"Estimated time: {cost.time_estimate_seconds:.2f}s")
    print(f"Time complexity: {cost.time_complexity}")
    print(f"Parallelizable: {cost.parallelizable}")

Budget Enforcement
^^^^^^^^^^^^^^^^^^

Programs can enforce time budgets:

.. code-block:: python

    from py3plex.dsl.program import ExecutionContext, execute_program
    
    # Create execution context with budget
    context = ExecutionContext(
        time_budget=30.0,  # 30 seconds
        seed=42,
        n_jobs=4
    )
    
    try:
        result = execute_program(program, network, context)
    except BudgetExceededError as e:
        print(f"Budget exceeded: {e}")
        print(f"Suggestions: {e.suggestions}")

Explaining Programs
-------------------

Generate human-readable explanations:

.. code-block:: python

    # Basic explanation
    explanation = program.explain()
    print(explanation)
    
    # Detailed explanation with costs
    from py3plex.dsl.program import explain_program
    
    detailed = explain_program(
        program,
        include_cost=True,
        include_types=True,
        include_optimizations=True
    )
    
    print(detailed.to_text())

Output::

    ============================================================
    Graph Program Explanation
    ============================================================
    
    Pipeline Steps:
      1. SELECT nodes
         Type: NodeSet
         Cost: O(V)
    
      2. FROM layers: social
         Type: NodeSet (filtered)
         Cost: O(1) filter
    
      3. COMPUTE degree
         Type: Table
         Cost: O(E)
    
      4. COMPUTE betweenness_centrality
         Type: Table
         Cost: O(VE)
    
      5. ORDER BY degree DESC
         Type: Table
         Cost: O(N log N) sort
    
      6. LIMIT 10
         Type: Table
         Cost: O(1) slice
    
    Total Estimated Cost: 2.340s (est.)
    
    ============================================================

Comparing Programs
------------------

Diff two programs to see structural and semantic differences:

.. code-block:: python

    from py3plex.dsl.program import diff_programs
    
    # Create two programs
    program1 = Q.nodes().compute("degree").to_program()
    program2 = Q.nodes().compute("degree", "betweenness").to_program()
    
    # Compare them
    diff = diff_programs(program1, program2)
    
    print(diff.summary())
    print(f"Hash changed: {diff.hash_changed}")
    print(f"Type changed: {diff.type_changed}")
    
    if diff.cost_impact:
        print(f"Cost impact: {diff.cost_impact:.2f}x")

Output::

    Found 1 difference(s):
      - AST structure differs (3 line changes) (impact: high)
    
    Program hash changed - cache invalidated

Composing Programs
------------------

Combine multiple programs into pipelines:

.. code-block:: python

    from py3plex.dsl.program import compose
    
    # Define reusable components
    select_nodes = Q.nodes().from_layers(L["social"]).to_program()
    compute_centrality = Q.nodes().compute("degree", "betweenness").to_program()
    
    # Compose them
    pipeline = compose(select_nodes, compute_centrality)
    
    # Execute composed program
    result = pipeline.execute(network)

Reproducibility & Caching
--------------------------

Programs support deterministic caching for reproducibility:

Graph Fingerprints
^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from py3plex.dsl.program import graph_fingerprint
    
    # Generate stable network fingerprint
    fingerprint = graph_fingerprint(network)
    print(f"Network fingerprint: {fingerprint}")

Cache Keys
^^^^^^^^^^

Cache keys combine graph, program, and execution context:

.. code-block:: python

    from py3plex.dsl.program import (
        CacheKey,
        graph_fingerprint,
        execution_fingerprint,
        environment_signature
    )
    
    # Create cache key
    key = CacheKey(
        graph_fingerprint=graph_fingerprint(network),
        program_hash=program.hash(),
        execution_context=execution_fingerprint(seed=42, n_jobs=1),
        environment_signature=environment_signature()
    )

Using the Cache
^^^^^^^^^^^^^^^

.. code-block:: python

    from py3plex.dsl.program import get_global_cache, clear_global_cache
    
    # Execute with caching
    result1 = program.execute(network, seed=42)
    
    # Second execution uses cache
    result2 = program.execute(network, seed=42)
    
    # Check cache statistics
    cache = get_global_cache()
    stats = cache.statistics()
    print(f"Cache hits: {stats['hits']}")
    print(f"Cache misses: {stats['misses']}")
    print(f"Hit rate: {stats['hit_rate']:.1%}")
    
    # Clear cache
    clear_global_cache()

UQ Semantics
------------

Programs support uncertainty quantification with Distribution types:

.. code-block:: python

    from py3plex.dsl.program import Distribution, UQMode, UQMetadata
    
    # Create distribution from samples
    samples = [0.45, 0.48, 0.52, 0.50, 0.49]
    
    metadata = UQMetadata(
        mode=UQMode.BOOTSTRAP,
        n_samples=100,
        seed=42,
        ci_level=0.95
    )
    
    dist = Distribution.from_samples(samples, metadata=metadata)
    
    # Get confidence intervals
    ci_low, ci_high = dist.ci(0.95)
    print(f"95% CI: [{ci_low:.3f}, {ci_high:.3f}]")
    print(f"Mean: {dist.mean:.3f} ± {dist.std:.3f}")

Distribution Propagation
^^^^^^^^^^^^^^^^^^^^^^^^

Distributions propagate through aggregations:

.. code-block:: python

    from py3plex.dsl.program import propagate_distribution
    
    # Propagate through mean operation
    values = [dist1, dist2, 0.5]  # Mix of Distributions and floats
    result = propagate_distribution(values, operation="mean")
    
    # Result is a Distribution if any input is a Distribution
    print(type(result))  # Distribution

Complete Example
----------------

Here's a complete workflow using Graph Programs:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dsl import Q, L
    from py3plex.dsl.program import (
        GraphProgram,
        explain_program,
        diff_programs,
        get_global_cache,
    )
    
    # Load network
    net = multinet.multi_layer_network(directed=False)
    net.load_network("network.csv", input_type="edgelist")
    
    # Build program
    program = (Q.nodes()
        .from_layers(L["*"])
        .compute("degree", "betweenness_centrality", "clustering")
        .where(degree__gt=5)
        .per_layer()
        .top_k(10, "betweenness_centrality")
        .to_program())
    
    # Inspect before execution
    print("=== Program Info ===")
    print(f"Hash: {program.hash()}")
    print(f"Type: {program.type_signature}")
    
    # Explain
    print("\n=== Explanation ===")
    explanation = explain_program(program, include_cost=True)
    print(explanation.to_text())
    
    # Optimize
    print("\n=== Optimization ===")
    optimized = program.optimize(budget="30s", objective="min_time")
    print(f"Rewrites applied: {len(optimized.metadata.provenance_chain)}")
    
    # Compare
    print("\n=== Diff ===")
    diff = diff_programs(program, optimized)
    print(diff.summary())
    
    # Execute with caching
    print("\n=== Execution ===")
    result = optimized.execute(net, seed=42)
    
    # Cache stats
    cache_stats = get_global_cache().statistics()
    print(f"Cache hit rate: {cache_stats['hit_rate']:.1%}")
    
    # Export results
    df = result.to_pandas()
    df.to_csv("top_nodes.csv", index=False)
    print(f"Results exported: {len(df)} rows")

See Also
--------

* :doc:`query_with_dsl` - DSL v2 query fundamentals
* :doc:`uncertainty_analysis` - Uncertainty quantification
* :doc:`build_pipelines` - Pipeline composition
* :doc:`reproduce_workflows` - Reproducibility best practices
