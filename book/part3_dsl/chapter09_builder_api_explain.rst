The Builder API and Explain Plans
============================================

The DSL Builder API provides a Pythonic, type-safe way to construct network queries using method chaining. This chapter covers the builder pattern, query execution plans, and advanced features like parameterization and query reuse.

Builder Pattern and Fluent API
-------------------------------

The builder API uses method chaining to construct queries incrementally. Each method returns the query object, allowing you to chain operations naturally.

See ``examples/network_analysis/example_dsl_builder_api.py`` for a complete example:

.. code-block:: python

    from py3plex.dsl import Q, L
    from py3plex.core import multinet
    
    # Create network
    net = multinet.multi_layer_network()
    # ... add nodes and edges ...
    
    # Build query with method chaining
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .where(degree__gt=3)
         .compute("betweenness_centrality")
         .order_by("-betweenness_centrality")
         .limit(10)
         .execute(net)
    )

**Run this example:**

.. code-block:: bash

    # Basic builder API examples
    python examples/network_analysis/example_dsl_builder_api.py
    
    # Advanced DSL features
    python examples/network_analysis/example_dsl_advanced.py

**Advantages over string DSL:**

* **Type safety:** IDE autocomplete and type checking
* **Composability:** Build queries programmatically
* **Readability:** Self-documenting code
* **Error detection:** Catch mistakes before execution

Method Chaining
~~~~~~~~~~~~~~~

Build queries step-by-step:

.. code-block:: python

    # Start with a base query
    q = Q.nodes()
    
    # Add filters
    q = q.where(layer="social")
    q = q.where(degree__gt=3)
    
    # Add computation
    q = q.compute("degree", "clustering")
    
    # Sort and limit
    q = q.order_by("-degree")
    q = q.limit(20)
    
    # Execute
    result = q.execute(network)

**Builder operators:**

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Operator
     - DSL Equivalent
   * - ``where(degree__gt=5)``
     - ``WHERE degree > 5``
   * - ``where(degree__gte=5)``
     - ``WHERE degree >= 5``
   * - ``where(degree__lt=5)``
     - ``WHERE degree < 5``
   * - ``where(degree__lte=5)``
     - ``WHERE degree <= 5``
   * - ``where(layer="social")``
     - ``WHERE layer = "social"``
   * - ``where(layer__in=["a", "b"])``
     - ``WHERE layer IN ("a", "b")``

Type Hints and IDE Support
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The builder API is fully type-hinted for modern IDEs:

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # IDE shows available methods and parameters
    result = (
        Q.nodes()           # Autocomplete suggests: where, from_layers, compute, ...
         .where(            # Autocomplete shows: degree__gt, degree__lt, layer, ...
             degree__gt=5   # Type hints ensure correct parameter types
         )
         .compute(          # Autocomplete lists available measures
             "degree",      # String literals with validation
             "betweenness_centrality"
         )
         .execute(network)  # Type checker ensures network is correct type
    )

**Benefits:**

* Catch typos before runtime
* Discover available methods and measures
* Understand query structure through types
* Safer refactoring with IDE support

EXPLAIN Mode
------------

Query Execution Plans
~~~~~~~~~~~~~~~~~~~~~

Get a query execution plan without actually running the query:

.. code-block:: python

    from py3plex.dsl import Q
    
    # Build a complex query
    q = (
        Q.nodes()
         .from_layers(L["social"])
         .where(degree__gt=5)
         .compute("betweenness_centrality", "pagerank")
         .order_by("-betweenness_centrality")
         .limit(10)
    )
    
    # Get execution plan
    plan = q.explain().execute(network)
    
    # Inspect the plan
    print(f"Query: {plan.query}")
    print(f"Estimated nodes: {plan.estimated_node_count}")
    
    for step in plan.steps:
        print(f"  {step.description}")
        print(f"    Complexity: {step.estimated_complexity}")
        print(f"    Estimated time: {step.estimated_time_ms}ms")
    
    # Check for warnings
    for warning in plan.warnings:
        print(f"  ⚠ {warning}")

**Example output:**

.. code-block:: text

    Query: SELECT nodes FROM layers social WHERE degree > 5 
           COMPUTE betweenness_centrality pagerank 
           ORDER BY -betweenness_centrality LIMIT 10
    
    Estimated nodes: ~150
    
      1. Filter by layer
        Complexity: O(n)
        Estimated time: 2ms
      
      2. Filter by degree
        Complexity: O(n)
        Estimated time: 1ms
      
      3. Compute betweenness_centrality
        Complexity: O(n³)
        Estimated time: 850ms
        ⚠ Betweenness centrality is expensive for large graphs
      
      4. Compute pagerank
        Complexity: O(n²)
        Estimated time: 45ms
      
      5. Sort results
        Complexity: O(n log n)
        Estimated time: 3ms
      
      6. Limit results
        Complexity: O(1)
        Estimated time: <1ms

Complexity Estimates
~~~~~~~~~~~~~~~~~~~~

EXPLAIN mode provides complexity estimates for each operation:

* **O(1)** — Constant time (e.g., limit, basic metadata)
* **O(n)** — Linear in number of nodes (e.g., filtering by attribute)
* **O(m)** — Linear in number of edges (e.g., edge filtering)
* **O(n log n)** — Log-linear (e.g., sorting)
* **O(n²)** — Quadratic (e.g., PageRank, all-pairs measures)
* **O(n³)** — Cubic (e.g., betweenness centrality on large graphs)

Use EXPLAIN to:

1. **Identify bottlenecks** before executing expensive queries
2. **Compare alternative formulations** of the same query
3. **Estimate runtime** for large networks
4. **Optimize query order** (apply cheap filters first)

Optimization Tips
~~~~~~~~~~~~~~~~~

**1. Apply filters before computing measures**

.. code-block:: python

    # ❌ Slow: Compute for all, then filter
    Q.nodes().compute("betweenness_centrality").where(degree__gt=5)
    
    # ✅ Fast: Filter first, then compute
    Q.nodes().where(degree__gt=5).compute("betweenness_centrality")

**2. Use layer filtering early**

.. code-block:: python

    # ❌ Slow: Compute for all layers
    Q.nodes().compute("degree").where(layer="social")
    
    # ✅ Fast: Filter to layer first
    Q.nodes().from_layers(L["social"]).compute("degree")

**3. Limit results when possible**

.. code-block:: python

    # Top 10 is much faster than computing for all nodes
    Q.nodes().compute("degree").order_by("-degree").limit(10)

**4. Choose efficient measures**

* **Cheap:** degree, clustering coefficient (local measures)
* **Moderate:** PageRank, eigenvector centrality (iterative)
* **Expensive:** betweenness centrality, closeness centrality (all-pairs)

Advanced Builder Features
-------------------------

Parameterized Queries
~~~~~~~~~~~~~~~~~~~~~

Use ``Param`` to create reusable query templates:

.. code-block:: python

    from py3plex.dsl import Q, Param
    
    # Create a parameterized query template
    influencer_query = (
        Q.nodes()
         .from_layers(L[Param.str("target_layer")])
         .where(degree__gt=Param.int("min_degree"))
         .compute("betweenness_centrality")
         .order_by("-betweenness_centrality")
         .limit(Param.int("top_n"))
    )
    
    # Execute with different parameters
    social_influencers = influencer_query.execute(
        network,
        target_layer="social",
        min_degree=10,
        top_n=20
    )
    
    work_influencers = influencer_query.execute(
        network,
        target_layer="professional",
        min_degree=5,
        top_n=50
    )

**Parameter types:**

* ``Param.int("name")`` — Integer parameter
* ``Param.float("name")`` — Float parameter
* ``Param.str("name")`` — String parameter
* ``Param.ref("name")`` — Untyped reference

**Benefits:**

* **Safety:** Type-checked at execution time
* **Reusability:** One query definition, many executions
* **Maintainability:** Parameters are self-documenting
* **Performance:** Query is parsed once, executed multiple times

Query Reuse
~~~~~~~~~~~

Build queries once and execute them multiple times:

.. code-block:: python

    # Define a query once
    high_degree_analysis = (
        Q.nodes()
         .where(degree__gt=10)
         .compute("betweenness_centrality", "clustering")
    )
    
    # Execute on different networks
    result1 = high_degree_analysis.execute(network1)
    result2 = high_degree_analysis.execute(network2)
    result3 = high_degree_analysis.execute(network3)
    
    # Or execute with different parameters over time
    for threshold in [5, 10, 15, 20]:
        q = Q.nodes().where(degree__gt=threshold).compute("degree")
        result = q.execute(network)
        print(f"Threshold {threshold}: {result.count} nodes")

Converting to DSL String
~~~~~~~~~~~~~~~~~~~~~~~~

Convert a builder query back to string format:

.. code-block:: python

    q = (
        Q.nodes()
         .from_layers(L["social"])
         .where(degree__gt=5)
         .compute("degree")
         .limit(10)
    )
    
    # Get DSL string representation
    dsl_string = q.to_dsl()
    print(dsl_string)
    # Output: SELECT nodes FROM layers social WHERE degree > 5 
    #         COMPUTE degree LIMIT 10

**Use cases:**

* **Logging:** Record queries in application logs
* **Debugging:** Inspect query structure
* **Serialization:** Save queries to files or databases
* **Auditing:** Track what analyses were run

Error Handling with Suggestions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The DSL provides helpful error messages with suggestions:

.. code-block:: python

    from py3plex.dsl import Q, UnknownMeasureError
    
    try:
        # Typo in measure name
        result = Q.nodes().compute("betweenes").execute(network)
    except UnknownMeasureError as e:
        print(e)
        # Output: Unknown measure 'betweenes'. Did you mean 'betweenness_centrality'?
        #         Known measures: betweenness_centrality, closeness_centrality, ...

Summary
-------

The DSL Builder API provides:

* **Pythonic interface:** Natural method chaining
* **Type safety:** IDE support and autocomplete
* **Query plans:** EXPLAIN mode for optimization
* **Parameterization:** Reusable query templates
* **Error handling:** Helpful "did you mean?" messages

**Best practices:**

1. Use builder API for programmatic queries
2. Run EXPLAIN before executing expensive queries
3. Filter early, compute late
4. Parameterize queries that you'll reuse
5. Use type hints and IDE support to catch errors

**Next chapter:** Advanced query patterns and workflow integration
