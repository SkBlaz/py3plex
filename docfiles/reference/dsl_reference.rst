DSL Reference
=============

Complete reference for the py3plex DSL (Domain-Specific Language) for querying multilayer networks.

.. note::
   For task-oriented usage, see :doc:`../how-to/query_with_dsl`.
   This page is a complete reference with all syntax and operators.

Overview
--------

The py3plex DSL provides two interfaces:

1. **String syntax:** SQL-like queries for quick exploration
2. **Builder API:** Type-safe Python interface for production code (autocomputes referenced metrics)

String Syntax Reference
-----------------------

Basic Structure
~~~~~~~~~~~~~~~

.. code-block:: text

    SELECT <target> [FROM <layers>] [WHERE <conditions>] [COMPUTE <metrics>] [ORDER BY <field>] [LIMIT <n>]
    [AT <timestamp> | DURING <start> TO <end>]

Use ``AT`` for a single time point and ``DURING`` for closed intervals (ISO 8601 strings).

Targets
~~~~~~~

* ``nodes`` — Select nodes
* ``edges`` — Select edges (experimental; limited coverage support)

Layer Selection
~~~~~~~~~~~~~~~

.. code-block:: text

    FROM layer="layer_name"
    FROM layers IN ("layer1", "layer2")

If ``FROM`` is omitted, all layers are considered.

Conditions
~~~~~~~~~~

**Operators:**

* ``=`` — Equal
* ``>`` — Greater than
* ``<`` — Less than
* ``>=`` — Greater than or equal
* ``<=`` — Less than or equal
* ``!=`` — Not equal

**Logical operators:**

* ``AND`` — Both conditions must be true
* ``OR`` — Either condition must be true
* ``NOT`` — Negate a condition

**Examples:**

.. code-block:: text

    WHERE degree > 5
    WHERE layer="friends" AND degree > 3
    WHERE degree > 5 OR betweenness_centrality > 0.1
    WHERE NOT layer="spam"

String values must be wrapped in double quotes.

Compute Clause
~~~~~~~~~~~~~~

Calculate metrics for selected nodes:

.. code-block:: text

    COMPUTE degree
    COMPUTE degree betweenness_centrality
    COMPUTE clustering pagerank

**Available metrics:**

* ``degree`` — Node degree
* ``betweenness_centrality`` — Betweenness centrality
* ``closeness_centrality`` — Closeness centrality
* ``clustering`` — Clustering coefficient
* ``pagerank`` — PageRank score
* ``layer_count`` — Number of layers node appears in

Metrics are computed after filtering and layer selection. See :doc:`algorithm_reference` for the complete metric list.

Order By
~~~~~~~~

.. code-block:: text

    ORDER BY degree
    ORDER BY -degree  # Descending (prefix with -)
    ORDER BY betweenness_centrality

You can specify multiple keys in sequence; each key may be prefixed with ``-`` for descending order.

Limit
~~~~~

.. code-block:: text

    LIMIT 10
    LIMIT 100

Complete Examples
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.dsl import execute_query
    
    # Get high-degree nodes
    result = execute_query(
        network,
        'SELECT nodes WHERE degree > 5'
    )
    
    # Get nodes from specific layer
    result = execute_query(
        network,
        'SELECT nodes FROM layer="friends" '
        'WHERE degree > 3 '
        'COMPUTE betweenness_centrality '
        'ORDER BY -betweenness_centrality '
        'LIMIT 10'
    )

Builder API Reference
---------------------

Import
~~~~~~

.. code-block:: python

    from py3plex.dsl import Q, L

Query Construction
~~~~~~~~~~~~~~~~~~

**Start a query:**

.. code-block:: python

    Q.nodes()     # Select nodes
    Q.edges()     # Select edges (experimental)

Layer Selection
~~~~~~~~~~~~~~~

**Single layer:**

.. code-block:: python

    Q.nodes().from_layers(L["friends"])

**Multiple layers (union):**

.. code-block:: python

    Q.nodes().from_layers(L["friends"] + L["work"])
    
    # Or use the new LayerSet algebra:
    Q.nodes().from_layers(L["friends | work"])

**Layer intersection:**

.. code-block:: python

    Q.nodes().from_layers(L["friends"] & L["work"])

**Advanced Layer Set Algebra:**

.. code-block:: python

    # All layers except coupling
    Q.nodes().from_layers(L["* - coupling"])
    
    # Complex expressions with set operations
    Q.nodes().from_layers(L["(social | work) & ~bots"])
    
    # Named groups for reuse
    from py3plex.dsl import LayerSet
    LayerSet.define_group("bio", LayerSet("ppi") | LayerSet("gene"))
    Q.nodes().from_layers(LayerSet("bio"))

.. seealso::
   
   For complete documentation on layer set algebra including all operators, 
   string parsing, named groups, and real-world examples, see:
   :doc:`layer_set_algebra`

Filtering
~~~~~~~~~

**Comparison operators:**

.. code-block:: python

    Q.nodes().where(degree__gt=5)       # Greater than
    Q.nodes().where(degree__gte=5)      # Greater than or equal
    Q.nodes().where(degree__lt=5)       # Less than
    Q.nodes().where(degree__lte=5)      # Less than or equal
    Q.nodes().where(degree__eq=5)       # Equal
    Q.nodes().where(degree__ne=5)       # Not equal

**Multiple conditions:**

.. code-block:: python

    Q.nodes().where(
        degree__gt=5,
        layer_count__gte=2
    )

Computing Metrics
~~~~~~~~~~~~~~~~~

.. code-block:: python

    Q.nodes().compute("degree")
    Q.nodes().compute("degree", "betweenness_centrality")

Row-wise Transformations (Mutate)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create new columns or transform existing ones with row-by-row operations:

.. code-block:: python

    # Simple transformation
    Q.nodes().compute("degree").mutate(
        doubled=lambda row: row.get("degree", 0) * 2
    )
    
    # Multiple transformations
    Q.nodes().compute("degree", "clustering").mutate(
        hub_score=lambda row: row.get("degree", 0) * row.get("clustering", 0),
        is_hub=lambda row: row.get("degree", 0) > 2
    )
    
    # Conditional transformation
    Q.nodes().compute("degree").mutate(
        category=lambda row: "hub" if row.get("degree", 0) > 3 else "peripheral"
    )

The lambda function receives a dictionary with all computed attributes and network properties
for each node/edge. Use ``row.get(attr_name, default)`` to safely access attributes.

.. note::
   Use ``mutate()`` for row-by-row transformations. For group-level aggregations,
   use ``summarize()`` or ``aggregate()`` instead.

Sorting
~~~~~~~

.. code-block:: python

    Q.nodes().order_by("degree")           # Ascending
    Q.nodes().order_by("-degree")          # Descending

Limiting
~~~~~~~~

.. code-block:: python

    Q.nodes().limit(10)

Execution
~~~~~~~~~

.. code-block:: python

    result = Q.nodes().execute(network)

Chaining
~~~~~~~~

All methods can be chained:

.. code-block:: python

    result = (
        Q.nodes()
         .from_layers(L["friends"])
         .where(degree__gt=5)
         .compute("betweenness_centrality", "degree")
         .mutate(
             influence=lambda row: row.get("degree", 0) * row.get("betweenness_centrality", 0)
         )
         .order_by("-influence")
         .limit(10)
         .execute(network)
    )

Temporal Queries
----------------

Filter by Time Point
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # String syntax
    result = execute_query(
        network,
        'SELECT nodes AT "2024-01-15T10:00:00"'
    )
    
    # Builder API
    result = (
        Q.nodes()
         .at("2024-01-15T10:00:00")
         .execute(network)
    )

Filter by Time Range
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # String syntax
    result = execute_query(
        network,
        'SELECT nodes DURING "2024-01-01" TO "2024-01-31"'
    )
    
    # Builder API
    result = (
        Q.nodes()
         .during("2024-01-01", "2024-01-31")
         .execute(network)
    )

Temporal Edge Attributes
~~~~~~~~~~~~~~~~~~~~~~~~~

Edges can have temporal attributes:

* ``t`` — Point in time (ISO 8601 timestamp)
* ``t_start`` and ``t_end`` — Time range

See :doc:`../user_guide/networks` for creating temporal networks.

Grouping and Coverage Queries
------------------------------

Per-Layer Grouping
~~~~~~~~~~~~~~~~~~

Group results by layer and apply per-group operations:

.. code-block:: python

    # Group by layer
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree")
         .per_layer()              # Sugar for .group_by("layer")
            .top_k(5, "degree")    # Top 5 per layer
         .end_grouping()
         .execute(network)
    )

Top-K Per Group
~~~~~~~~~~~~~~~

Select top-k items per group (requires prior grouping):

.. code-block:: python

    # Top 10 highest-degree nodes per layer
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree", "betweenness_centrality")
         .per_layer()
            .top_k(10, "degree")
         .end_grouping()
         .execute(network)
    )

Coverage Filtering
~~~~~~~~~~~~~~~~~~

Filter based on presence across groups:

**Mode: "all"** — Keep items appearing in ALL groups (intersection)

.. code-block:: python

    # Nodes that are top-5 hubs in ALL layers
    multi_hubs = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("betweenness_centrality")
         .per_layer()
            .top_k(5, "betweenness_centrality")
         .end_grouping()
         .coverage(mode="all")
         .execute(network)
    )

**Mode: "any"** — Keep items appearing in AT LEAST ONE group (union)

.. code-block:: python

    # Nodes that are top-5 in any layer
    any_hubs = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree")
         .per_layer()
            .top_k(5, "degree")
         .end_grouping()
         .coverage(mode="any")
         .execute(network)
    )

**Mode: "at_least"** — Keep items appearing in at least K groups

.. code-block:: python

    # Nodes in top-10 of at least 2 layers
    two_layer_hubs = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree")
         .per_layer()
            .top_k(10, "degree")
         .end_grouping()
         .coverage(mode="at_least", k=2)
         .execute(network)
    )

**Mode: "exact"** — Keep items appearing in exactly K groups

.. code-block:: python

    # Layer specialists: top-5 in exactly 1 layer
    specialists = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("betweenness_centrality")
         .per_layer()
            .top_k(5, "betweenness_centrality")
         .end_grouping()
         .coverage(mode="exact", k=1)
         .execute(network)
    )

Wildcard Layer Selection
~~~~~~~~~~~~~~~~~~~~~~~~

Use ``L["*"]`` to select all layers:

.. code-block:: python

    # All layers
    Q.nodes().from_layers(L["*"])
    
    # All layers except "bots"
    Q.nodes().from_layers(L["*"] - L["bots"])
    
    # Layer algebra still works
    Q.nodes().from_layers((L["*"] - L["spam"]) & L["verified"])

General Grouping
~~~~~~~~~~~~~~~~

Group by arbitrary attributes (not just layer):

.. code-block:: python

    # Group by multiple attributes
    result = (
        Q.nodes()
         .compute("degree", "community")
         .group_by("layer", "community")
            .top_k(3, "degree")
         .end_grouping()
         .execute(network)
    )

Limitations
~~~~~~~~~~~

* Coverage filtering is currently supported only for **node queries**
* Edge queries with coverage will raise a clear ``DslExecutionError``
* Grouping requires computed attributes or inherent node properties (like layer)

Explaining Results
------------------

The ``.explain()`` method adds interpretable explanations to query results or displays execution plans.

Execution Plan Mode
~~~~~~~~~~~~~~~~~~~

Call ``.explain()`` with no arguments to get the query execution plan:

.. code-block:: python

    plan = Q.nodes().compute("degree").where(degree__gt=5).explain()
    print(plan)  # Shows query stages and optimization

This mode does NOT execute the query or attach explanations.

Explanations Mode
~~~~~~~~~~~~~~~~~

Call ``.explain()`` with arguments to attach explanations to each result row:

.. code-block:: python

    result = (
        Q.nodes()
         .compute("pagerank")
         .explain(
             include=["community", "top_neighbors", "attribution"],
             attribution={"metric": "pagerank", "seed": 42}
         )
         .execute(network)
    )
    
    # Access explanations
    df = result.to_pandas(expand_explanations=True)
    # df now has explanation columns with JSON-serialized dicts

Available Explanation Blocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``"community"`` — Community membership and size
* ``"top_neighbors"`` — Top neighbors by weight/degree  
* ``"layer_footprint"`` — Layers where node/edge appears
* ``"attribution"`` — Shapley-based attribution explanations (see below)

Default blocks: ``["community", "top_neighbors", "layer_footprint"]``

Attribution Block
~~~~~~~~~~~~~~~~~

The ``"attribution"`` block provides Shapley value-based explanations for why nodes/edges have high metric values or rankings.

**Purpose**: Decompose metric contributions across layers and/or edges using game-theoretic attribution.

**Basic Example**:

.. code-block:: python

    result = (
        Q.nodes()
         .compute("pagerank")
         .explain(
             include=["attribution"],
             attribution={
                 "metric": "pagerank",
                 "levels": ["layer"],
                 "method": "shapley_mc",
                 "seed": 42
             }
         )
         .execute(network)
    )

**Configuration Parameters**:

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Parameter
     - Type
     - Default
     - Description
   * - ``metric``
     - str | None
     - Auto-infer
     - Which computed metric to explain (required if multiple metrics)
   * - ``objective``
     - str
     - "value"
     - ``"value"`` explains metric score, ``"rank"`` explains ranking position
   * - ``levels``
     - List[str]
     - ["layer"]
     - Attribution levels: ``["layer"]``, ``["edge"]``, or both
   * - ``method``
     - str
     - "shapley_mc"
     - ``"shapley"`` (exact), ``"shapley_mc"`` (Monte Carlo), ``"influence"`` (approx)
   * - ``feature_space``
     - str
     - "layers"
     - ``"layers"``, ``"layer_pairs"``, or ``"coupling_types"``
   * - ``n_permutations``
     - int
     - 128
     - Monte Carlo sample count (≥16)
   * - ``max_exact_features``
     - int
     - 8
     - Switch from exact to MC Shapley at this threshold
   * - ``seed``
     - int | None
     - None
     - Random seed for determinism (strongly recommended)
   * - ``edge_scope``
     - str
     - "incident"
     - ``"incident"``, ``"ego_k_hop"``, ``"shortest_path_sample"``, ``"global_top_m"``
   * - ``k_hop``
     - int
     - 2
     - Ego network radius (for ``edge_scope="ego_k_hop"``)
   * - ``max_edges``
     - int
     - 40
     - Maximum candidate edges to consider
   * - ``top_k_layers``
     - int
     - 10
     - Number of top layer contributions to return
   * - ``top_k_edges``
     - int
     - 20
     - Number of top edge contributions to return
   * - ``include_negative``
     - bool
     - True
     - Include negative contributions
   * - ``cache``
     - bool
     - True
     - Cache subset computations for performance
   * - ``uq``
     - str
     - "off"
     - ``"off"``, ``"propagate"`` (compute per UQ replicate), ``"summarize_only"``
   * - ``ci_level``
     - float
     - 0.95
     - Confidence interval level for UQ propagation

**Output Structure**:

.. code-block:: python

    {
        "metric": "pagerank",
        "objective": "value",
        "utility_def": None,  # or "margin_to_cutoff(k=10)" for rank
        "levels": ["layer"],
        "method": "shapley_mc",
        "seed": 42,
        "n_permutations": 128,
        "feature_space": "layers",
        "full_value": 0.1186,
        "baseline_value": 0.0500,
        "delta": 0.0686,
        "residual": 1e-12,  # sum(phi) ≈ delta
        "layer_contrib": [
            {"layer": "social", "phi": 0.0401},
            {"layer": "work", "phi": 0.0285}
        ],
        "edge_contrib": [],  # populated if levels includes "edge"
        "warnings": [],
        "cache_hit_rate": 0.73
    }

**Advanced Examples**:

.. code-block:: python

    # Edge attribution for betweenness
    result = (
        Q.nodes()
         .compute("betweenness_centrality")
         .order_by("-betweenness_centrality")
         .limit(10)
         .explain(
             include=["attribution"],
             attribution={
                 "objective": "rank",  # Explain ranking position
                 "levels": ["layer", "edge"],
                 "edge_scope": "ego_k_hop",
                 "k_hop": 2,
                 "max_edges": 40,
                 "n_permutations": 128,
                 "seed": 42
             }
         )
         .execute(network)
    )
    
    # With UQ propagation
    result = (
        Q.nodes()
         .uq(method="perturbation", n_samples=30, seed=42)
         .compute("pagerank")
         .explain(
             include=["attribution"],
             attribution={
                 "metric": "pagerank",
                 "uq": "propagate",  # Compute attribution per UQ replicate
                 "levels": ["layer"],
                 "seed": 42
             }
         )
         .execute(network)
    )

**Determinism**:

- Setting ``seed`` ensures reproducible Shapley values across runs
- Same seed produces identical attributions regardless of parallel execution settings
- Different seeds produce statistically different but valid attributions

**Performance Notes**:

- **Exact Shapley**: Only feasible for ≤ ``max_exact_features`` layers (default 8)
- **Monte Carlo Shapley**: Scales to larger feature sets via sampling
- **Edge Attribution**: More expensive than layer attribution; bounded by ``max_edges``
- **Caching**: Enabled by default to reuse subset metric computations

**UQ Integration**:

- ``uq="off"``: No UQ (default), deterministic scalar Shapley values
- ``uq="propagate"``: Compute attribution per UQ replicate, aggregate mean/std/CI
- ``uq="summarize_only"``: Compute once on base network, wrap in UQ-like structure

**Export**:

Attribution data serializes to JSON strings when using ``expand_explanations=True``:

.. code-block:: python

    df = result.to_pandas(expand_explanations=True)
    # df["attribution"] contains JSON-serialized attribution dicts

Working with Results
--------------------

Result Object
~~~~~~~~~~~~~

``execute`` returns a ``QueryResult`` with items, computed attributes, and metadata:

.. code-block:: python

    result = Q.nodes().compute("degree").execute(network)
    
    # Counts and identifiers
    print(result.count)    # -> number of nodes/edges
    print(result.nodes[:3])  # first few nodes (use .edges for edge queries)
    
    # Attributes are aligned lists keyed by metric name
    degrees = result.attributes["degree"]
    for node, deg in zip(result.nodes, degrees):
        print(node, deg)
    
    # Execution metadata (e.g., grouping, ordering)
    print(result.meta)

Convert to Pandas
~~~~~~~~~~~~~~~~~

.. code-block:: python

    df = result.to_pandas(multiindex=True, include_grouping=True)
    print(df.head())

Set ``expand_uncertainty=True`` to unpack UQ-aware metrics into multiple columns.

Extensibility
-------------

Custom Operators
~~~~~~~~~~~~~~~~

Register custom DSL operators:

.. code-block:: python

    from py3plex.dsl import register_operator
    
    @register_operator('my_metric')
    def my_custom_metric(context, node):
        """Compute custom metric for a node."""
        # Your implementation
        return value

See :doc:`../dev/code_architecture` for plugin development.

Performance Considerations
--------------------------

1. **Compute metrics once:** Don't recompute in multiple queries
2. **Filter early:** Use WHERE before COMPUTE
3. **Limit results:** Use LIMIT for large networks
4. **Layer-specific:** Query single layers when possible

Next Steps
----------

* **Learn by doing:** :doc:`../how-to/query_with_dsl`
* **See examples:** :doc:`../examples/index`
* **Understand implementation:** :doc:`../dev/code_architecture`
