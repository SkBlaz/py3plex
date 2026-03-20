.. _limitations-stability-chapter:

Limitations and Stability Guarantees
================================================

*This chapter scopes feature status to the workflows documented in this book.*

DSL Feature Status
------------------

Stable APIs
~~~~~~~~~~~

Features with strong backward-compatibility guarantees:

* **Node queries** — ``Q.nodes()`` with filtering and measures
* **Edge queries** — ``Q.edges()`` with substantial coverage of node-query workflows, including
  ``per_layer_pair()``, ``aggregate()``, ``where()``, and all export formats
* **Layer algebra** — Union, difference, intersection operations
* **Core measures** — degree, betweenness, closeness, pagerank
* **Result export** — pandas, JSON, CSV formats
* **Aggregations** — ``per_layer()`` / ``per_layer_pair()`` with ``aggregate()``
  supporting ``mean``, ``sum``, ``min``, ``max``, ``std``, ``var``, ``median``,
  ``quantile``, and ``count``
* **Temporal queries** — ``Q.edges().at(t)``, ``.during(t0, t1)``,
  ``.before(t)``, ``.after(t)``, ``.window(size, step)``
* **Join operations** — ``.join(right, on=..., how=...)`` with documented join types
* **Graph pattern matching** — ``Q.pattern()`` for motif-style matching

**Scope statement:** These APIs are intended to remain stable for the workflows described here; verify behavior against your pinned version when reproducing prior analyses.

Interface Selection Guide (Core vs Alternatives)
-------------------------------------------------

Use this chapter-level guide to choose the right interface once you already understand core DSL syntax.

.. list-table:: Interface Decision Matrix
   :header-rows: 1
   :widths: 20 25 25 30

   * - **Interface**
     - **Best For**
     - **Use When**
     - **Avoid When**
   * - **DSL v2 (Q, L, UQ)**
     - Multilayer querying and reproducible analysis scripts
     - Layer algebra, grouped summaries, provenance, UQ
     - You only need simple single-layer NetworkX operations
   * - **graph_ops**
     - Data-frame style exploration
     - You want quick filter/mutate/export cycles
     - You need multilayer-specific query semantics
   * - **Pipeline API**
     - Repeatable multi-step workflows
     - You need fit/transform-style orchestration
     - You are doing one-off exploratory queries
   * - **CLI**
     - Scripted batch tasks and quick checks
     - You need shell-based automation
     - You need complex custom branching logic

Experimental Features
~~~~~~~~~~~~~~~~~~~~~

Functional but may change in future versions:

* **Nested subqueries** — Complex query composition via ``join()`` and
  ``QueryResult`` chaining; the exact semantics may be refined

**Note:** Experimental features are marked in documentation. Use with awareness that API may evolve.

Planned Features
~~~~~~~~~~~~~~~~

Roadmap items (briefly mentioned, not detailed):

* **Streaming export** — Incremental result materialisation for very large networks
* **Custom semiring registration** — User-defined algebraic structures at runtime

Current Limitations
-------------------

Query Capabilities
~~~~~~~~~~~~~~~~~~

What the DSL **can** do:

* Node and edge filtering by degree, layer, and computed measures
* Compute centrality measures
* Layer algebra operations
* Export results in multiple formats
* Aggregate results per layer or per layer-pair (``mean``, ``sum``, ``min``,
  ``max``, ``std``, ``var``, ``median``, ``quantile``, ``count``)
* Query temporal networks with time-window and snapshot filters
* Match graph motifs and patterns via ``Q.pattern()``
* Join query results across layers with relational join semantics

What the DSL **cannot** (yet) do:

* Nested subqueries — queries whose ``where()`` clause references the result of
  another live query (not yet supported as a first-class construct)

Performance Boundaries
~~~~~~~~~~~~~~~~~~~~~~

* **Small networks** (<10k nodes) — No issues
* **Medium networks** (10k-100k nodes) — Most queries fast
* **Large networks** (>100k nodes) — Some queries may be slow; use filtering early

Scale and Performance
---------------------

Query Complexity
~~~~~~~~~~~~~~~~

DSL query operations have different time complexities:

.. list-table:: Query Operation Complexity
   :header-rows: 1
   :widths: 40 30 30

   * - Operation
     - Time Complexity
     - Notes
   * - ``Q.nodes()`` (no filter)
     - O(n)
     - Linear scan of nodes
   * - ``.where(degree__gt=k)``
     - O(n + m)
     - Degree computation
   * - ``.compute("degree")``
     - O(n + m)
     - Linear in edges
   * - ``.compute("betweenness")``
     - O(nm)
     - Expensive for large networks
   * - ``.compute("pagerank")``
     - O(k·m)
     - k iterations, m edges
   * - ``.order_by()``
     - O(n log n)
     - Sorting results
   * - ``.limit(k)``
     - O(k)
     - Constant after ordering
   * - ``.to_pandas()``
     - O(n)
     - Result materialization

**Query optimization tips:**

- Apply ``where()`` filters early to reduce working set size
- Use ``limit()`` when you only need top-k results
- Avoid betweenness centrality on networks > 10K nodes (use sampling or degree-based measures)
- Cache results with ``.to_pandas()`` if reusing the same query output

Memory Requirements
~~~~~~~~~~~~~~~~~~~

**Memory usage guidelines:**

- **Small networks** (<10K nodes): Negligible overhead, all queries run in-memory
- **Medium networks** (10K-100K nodes): 
  
  - Node queries: ~1-10 MB per query result
  - Betweenness centrality: O(n²) memory, problematic > 20K nodes
  - PageRank: O(n) memory, scales well
  
- **Large networks** (>100K nodes):
  
  - Use streaming or chunked queries where possible
  - Disable ``autocompute`` if metrics are pre-computed: ``Q.nodes().compute(..., autocompute=False)``
  - Export results incrementally with ``.to_json(stream=True)`` if available
  - Consider using external graph databases (Neo4j) for very large networks

**Best practices for large networks:**

1. Filter aggressively with ``where()`` before computing expensive measures
2. Use degree-based centrality instead of betweenness when possible
3. Sample nodes if exact answers aren't required
4. Leverage layer algebra to query subsets: ``Q.nodes().from_layers(L["layer1"])``

When Not to Use the DSL
~~~~~~~~~~~~~~~~~~~~~~~~

Use direct NetworkX/NumPy for:

* Single-layer graphs (DSL overhead not needed)
* Custom algorithms requiring fine-grained control
* Performance-critical inner loops

API Versioning Policy
---------------------

Semantic Versioning
~~~~~~~~~~~~~~~~~~~

py3plex follows semantic versioning (MAJOR.MINOR.PATCH):

* **MAJOR** (1.x → 2.x) — Breaking changes possible
* **MINOR** (1.1 → 1.2) — New features; existing documented APIs are intended to remain compatible
* **PATCH** (1.1.1 → 1.1.2) — Bug fixes only

Deprecation Policy
~~~~~~~~~~~~~~~~~~

Deprecated features are:

1. Marked in documentation and code (warnings)
2. Maintained for at least one minor version
3. Removed in next major version

Migration Guides
~~~~~~~~~~~~~~~~

When breaking changes occur in major versions, py3plex provides:

- **Migration guide documentation** in the CHANGELOG
- **Deprecation warnings** for at least one minor version before removal
- **Code examples** showing old vs. new API usage
- **Automated migration scripts** where feasible (e.g., for simple renames)

Migration guides are published in the ``docs/migration/`` directory and linked from the main documentation.

Summary
-------

**Intended stable workflows in this book:**

* Node and edge queries with filtering and broad feature coverage
* Core centrality measures
* Layer algebra
* Aggregations (mean, sum, min, max, std, var, median, quantile, count)
* Temporal queries (snapshots, windows, before/after)
* Graph pattern matching via ``Q.pattern()``
* Join operations (inner, left, right, outer, semi, anti)
* Result export

**Use with awareness:**

* Experimental features (nested subqueries) may change
* Large network performance depends on query structure

The DSL prioritizes transparent status reporting. Use stable workflows with version pinning, and treat experimental features as opt-in.

.. seealso::

   - **Full DSL reference:** ``docfiles/user_guide/dsl.rst``
   - **Algorithm roadmap:** ``docfiles/algorithm_roadmap.rst``
   - **Performance benchmarks:** ``benchmarks/`` directory
