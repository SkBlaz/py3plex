Limitations and Stability Guarantees
================================================

*This chapter explicitly marks feature status for user confidence*

DSL Feature Status
------------------

Stable APIs
~~~~~~~~~~~

Features with strong backward-compatibility guarantees:

* **Node queries** — ``Q.nodes()`` with filtering and measures
* **Layer algebra** — Union, difference, intersection operations
* **Core measures** — degree, betweenness, closeness, pagerank
* **Result export** — pandas, JSON, CSV formats

**Guarantee:** Stable APIs will not break in minor version updates (1.x → 1.y).

Experimental Features
~~~~~~~~~~~~~~~~~~~~~

Functional but may change in future versions:

* **Edge queries** — ``Q.edges()`` (limited implementation)
* **Advanced aggregations** — ``GROUP BY`` equivalents
* **Nested subqueries** — Complex query composition

**Note:** Experimental features are marked in documentation. Use with awareness that API may evolve.

Planned Features
~~~~~~~~~~~~~~~~

Roadmap items (briefly mentioned, not detailed):

* **Full edge query support** — Complete parity with node queries
* **Graph pattern matching** — Motif detection DSL
* **Temporal queries** — Time-aware filtering

Current Limitations
-------------------

Query Capabilities
~~~~~~~~~~~~~~~~~~

What the DSL **can** do:

* Node filtering by degree, layer, and computed measures
* Compute centrality measures
* Layer algebra operations
* Export results in multiple formats

What the DSL **cannot** (yet) do:

* Complex edge queries (partial support only)
* Nested subqueries
* Aggregate functions (SUM, AVG, etc.)
* Join operations across layers

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
* **MINOR** (1.1 → 1.2) — New features, stable API unchanged
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

**Stable and production-ready:**

* Node queries with filtering
* Core centrality measures
* Layer algebra
* Result export

**Use with awareness:**

* Experimental features may change
* Large network performance depends on query structure
* Some features are planned but not yet implemented

The DSL prioritizes transparency about feature status and limitations. Users should feel confident relying on stable APIs while being aware of experimental features and performance boundaries.

.. seealso::

   - **Full DSL reference:** ``docfiles/user_guide/dsl.rst``
   - **Algorithm roadmap:** ``docfiles/algorithm_roadmap.rst``
   - **Performance benchmarks:** ``benchmarks/`` directory
