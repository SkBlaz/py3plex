Chapter 10: Advanced Queries and Workflows
==========================================

This chapter explores advanced DSL patterns for complex multilayer network analyses.

.. admonition:: 🔍 Advanced DSL Patterns
   :class: dsl-example

   The DSL supports sophisticated analysis workflows:

   .. code-block:: python

       from py3plex.dsl import Q, L, Param

       # 1. Parameterized queries for systematic analysis
       query = (
           Q.nodes()
            .from_layers(L[Param.str("layer")])
            .where(degree__gt=Param.int("threshold"))
            .compute("betweenness_centrality")
            .limit(Param.int("top_n"))
       )

       # Execute with different parameters
       for layer in ["social", "work", "family"]:
           result = query.execute(network, layer=layer, threshold=5, top_n=20)
           result.to_pandas().to_csv(f"{layer}_hubs.csv")

       # 2. Multi-layer comparative analysis
       comparison = []
       for layer in network.get_layers():
           stats = (
               Q.nodes()
                .from_layers(L[layer])
                .compute("degree", "betweenness_centrality", "clustering")
                .execute(network)
           )
           df = stats.to_pandas()
           comparison.append({
               'layer': layer,
               'nodes': stats.count,
               'avg_degree': df['degree'].mean(),
               'max_bc': df['betweenness_centrality'].max(),
           })

       # 3. EXPLAIN mode for optimization
       expensive_query = Q.nodes().compute("betweenness_centrality")
       plan = expensive_query.explain().execute(network)
       for step in plan.steps:
           print(f"{step.description}: {step.estimated_complexity}")

   Advanced patterns enable complex research workflows!

*TODO: Expand from advanced DSL examples and patterns*

Complex Query Patterns
-----------------------

Multilayer Motifs
~~~~~~~~~~~~~~~~~

[Pattern detection across layers]

Multilayer Paths
~~~~~~~~~~~~~~~~

[Path queries respecting layer structure]

Aggregations and Grouping
~~~~~~~~~~~~~~~~~~~~~~~~~~

[Aggregate measures by layer]

Result Conversion
-----------------

To Pandas DataFrames
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    df = result.to_pandas()

To NetworkX
~~~~~~~~~~~

[Export query results as NetworkX graphs]

To Arrow/Parquet
~~~~~~~~~~~~~~~~

[High-performance export]

Workflow Integration
--------------------

Pipeline Composition
~~~~~~~~~~~~~~~~~~~~

[Chain multiple queries]

Combining with sklearn
~~~~~~~~~~~~~~~~~~~~~~

[Integration with machine learning pipelines]

Custom Measures
~~~~~~~~~~~~~~~

[Extending the DSL with custom functions]

Performance Tips
----------------

Query Optimization
~~~~~~~~~~~~~~~~~~

[Best practices for large networks]

Memory Management
~~~~~~~~~~~~~~~~~

[Streaming results for large queries]

Summary
-------

[Advanced DSL capabilities]

*Source files:*
- examples/network_analysis/example_dsl_advanced.py
- docfiles/user_guide/dsl.rst (advanced sections)
