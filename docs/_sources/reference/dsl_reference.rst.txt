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
2. **Builder API:** Type-safe Python interface for production code

String Syntax Reference
-----------------------

Basic Structure
~~~~~~~~~~~~~~~

.. code-block:: text

    SELECT <target> [FROM <layers>] [WHERE <conditions>] [COMPUTE <metrics>] [ORDER BY <field>] [LIMIT <n>]

Targets
~~~~~~~

* ``nodes`` — Select nodes
* ``edges`` — Select edges (experimental)

Layer Selection
~~~~~~~~~~~~~~~

.. code-block:: text

    FROM layer="layer_name"
    FROM layers IN ("layer1", "layer2")

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

**Examples:**

.. code-block:: text

    WHERE degree > 5
    WHERE layer="friends" AND degree > 3
    WHERE degree > 5 OR betweenness_centrality > 0.1

Compute Clause
~~~~~~~~~~~~~~

Calculate metrics for selected nodes:

.. code-block:: text

    COMPUTE degree
    COMPUTE degree COMPUTE betweenness_centrality
    COMPUTE clustering

**Available metrics:**

* ``degree`` — Node degree
* ``betweenness_centrality`` — Betweenness centrality
* ``closeness_centrality`` — Closeness centrality
* ``clustering`` — Clustering coefficient
* ``pagerank`` — PageRank score
* ``layer_count`` — Number of layers node appears in

See :doc:`algorithm_reference` for complete metric list.

Order By
~~~~~~~~

.. code-block:: text

    ORDER BY degree
    ORDER BY -degree  # Descending (prefix with -)
    ORDER BY betweenness_centrality

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

**Layer intersection:**

.. code-block:: python

    Q.nodes().from_layers(L["friends"] & L["work"])

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
         .compute("betweenness_centrality")
         .order_by("-betweenness_centrality")
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

Working with Results
--------------------

Result Object
~~~~~~~~~~~~~

Query results are dictionaries mapping nodes to their computed attributes:

.. code-block:: python

    result = Q.nodes().compute("degree").execute(network)
    
    # Access individual node
    node = ('Alice', 'friends')
    degree = result[node]['degree']
    
    # Iterate
    for node, data in result.items():
        print(f"{node}: {data}")

Convert to Pandas
~~~~~~~~~~~~~~~~~

.. code-block:: python

    df = result.to_pandas()
    print(df.head())

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
