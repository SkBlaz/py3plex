Chapter 11: Limitations and Stability Guarantees
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

[Keep this section SHORT—no long speculative lists]

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

[Table showing O(n), O(n log n), O(n²) operations]

Memory Requirements
~~~~~~~~~~~~~~~~~~~

[Guidelines for large networks]

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
* **PATCH** (1.1.0 → 1.1.1) — Bug fixes only

Deprecation Policy
~~~~~~~~~~~~~~~~~~

Deprecated features are:

1. Marked in documentation and code (warnings)
2. Maintained for at least one minor version
3. Removed in next major version

Migration Guides
~~~~~~~~~~~~~~~~

[Commit to providing migration guides for breaking changes]

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

[Focus on transparency and user confidence]

*Source files:*
- docfiles/user_guide/dsl.rst (limitations sections)
- docfiles/algorithm_roadmap.rst (for planned features—keep brief)
