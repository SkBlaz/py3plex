SQL-like DSL for Multilayer Networks
=====================================

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

Py3plex provides a Domain-Specific Language (DSL) for querying and analyzing multilayer networks using SQL-like syntax. This intuitive interface allows users to filter nodes and edges, compute network measures, and perform complex analyses with simple, readable queries.

**DSL v2** introduces several major improvements:

- **Python Builder API**: Chainable, type-hinted query construction
- **Layer Algebra**: Union, difference, and intersection operations on layers
- **Rich Results**: Export to pandas, NetworkX, or Arrow formats
- **EXPLAIN Mode**: Query execution plans with complexity estimates
- **Parameterized Queries**: Safe parameter binding for dynamic queries
- **Better Errors**: "Did you mean?" suggestions for typos

.. admonition:: Quick Start with Builder API
   :class: tip

   For the fastest start, see the comprehensive builder API example:
   
   .. code-block:: bash
   
       python examples/network_analysis/example_dsl_builder_api.py
   
   This example demonstrates all DSL v2 features with working code and explanations.

The DSL enables you to express complex network queries in a natural, SQL-like language without writing verbose code. For example, instead of manually iterating through nodes and checking conditions, you can write:

**String DSL syntax:**

.. code-block:: python

    execute_query(network, 'SELECT nodes WHERE layer="social" AND degree > 5')

**Or using the new Builder API (recommended):**

.. code-block:: python

    from py3plex.dsl import Q, L
    
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .where(degree__gt=5)
         .execute(network)
    )

The DSL is particularly useful for:

- **Interactive network exploration**: Quickly test hypotheses and explore network structure
- **Rapid prototyping**: Build analysis workflows without extensive coding
- **Educational purposes**: Learn network concepts with intuitive queries
- **Production pipelines**: Create maintainable, self-documenting analysis code

Basic Syntax
------------

The DSL follows a SQL-inspired syntax::

    SELECT target WHERE conditions COMPUTE measures

Where:

- **target**: Either ``nodes`` or ``edges``
- **conditions**: Filtering criteria (optional)
- **measures**: Network measures to compute (optional)

DSL Cheat Sheet
---------------

**Quick Syntax Reference:**

.. code-block:: text

    SELECT target WHERE conditions COMPUTE measures ORDER BY field LIMIT n

**Common Query Patterns:**

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Task
     - DSL Query
   * - Select all nodes in a layer
     - ``SELECT nodes WHERE layer="social"``
   * - Find high-degree nodes
     - ``SELECT nodes WHERE degree > 5``
   * - Filter by degree range
     - ``SELECT nodes WHERE degree >= 2 AND degree <= 10``
   * - Compute centrality
     - ``SELECT nodes COMPUTE betweenness_centrality``
   * - Filter + compute
     - ``SELECT nodes WHERE layer="social" COMPUTE degree_centrality``

**DSL String vs Python Builder API:**

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - DSL String
     - Python Builder API
   * - ``'SELECT nodes WHERE layer="social"'``
     - ``Q.nodes().where(layer="social")``
   * - ``'SELECT nodes WHERE degree > 5'``
     - ``Q.nodes().where(degree__gt=5)``
   * - ``'SELECT nodes WHERE layer="social" AND degree > 3'``
     - ``Q.nodes().where(layer="social", degree__gt=3)``
   * - Layer union (social OR work)
     - ``Q.nodes().from_layers(L["social"] + L["work"])``
   * - Layer difference (social NOT bots)
     - ``Q.nodes().from_layers(L["social"] - L["bots"])``
   * - Order and limit
     - ``Q.nodes().compute("degree").order_by("-degree").limit(10)``
   * - Export to CSV
     - ``Q.nodes().compute("degree").export_csv("output.csv")``
   * - Export to JSON
     - ``Q.nodes().compute("degree").export_json("output.json")``

Quick Start Example
-------------------

Here's a complete working example to get you started::

    from py3plex.core import multinet
    from py3plex.dsl import execute_query, format_result
    
    # Create a multilayer network
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes to different layers
    network.add_nodes([
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
        {'source': 'Alice', 'type': 'work'},
        {'source': 'Bob', 'type': 'work'},
    ])
    
    # Add edges
    network.add_edges([
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
    ])
    
    # Query 1: Select all nodes in the social layer
    result = execute_query(network, 'SELECT nodes WHERE layer="social"')
    print(f"Found {result['count']} nodes in social layer")
    print(result['nodes'])
    
    # Query 2: Find high-degree nodes
    result = execute_query(network, 'SELECT nodes WHERE degree > 1')
    print(format_result(result))
    
    # Query 3: Compute centrality for filtered nodes
    result = execute_query(
        network,
        'SELECT nodes WHERE layer="social" COMPUTE betweenness_centrality'
    )
    for node, centrality in result['computed']['betweenness_centrality'].items():
        print(f"{node}: {centrality:.4f}")

**Expected Output:**

.. code-block:: text

    Found 3 nodes in social layer
    [('Alice', 'social'), ('Bob', 'social'), ('Charlie', 'social')]
    
    Query: SELECT nodes WHERE degree > 1
    Target: nodes
    Count: 2
    
    Nodes (showing 2 of 2):
      ('Alice', 'social')
      ('Bob', 'social')
    
    ('Alice', 'social'): 0.0000
    ('Bob', 'social'): 1.0000
    ('Charlie', 'social'): 0.0000

Query Components
----------------

SELECT Clause
~~~~~~~~~~~~~

Specifies what to select from the network::

    SELECT nodes     # Select nodes

.. warning::

   **Edge Queries (Experimental)**: Edge queries (``SELECT edges``) are currently in development and not fully supported. The DSL primarily focuses on node queries at this time. Use node-based queries for production work.

**Note**: Current version primarily supports node queries.

WHERE Clause
~~~~~~~~~~~~

Filters results based on conditions. Supports:

**Layer filtering**::

    WHERE layer="transport"
    WHERE layer="social"

**Degree filtering**::

    WHERE degree > 5
    WHERE degree >= 3
    WHERE degree <= 10

**Logical operators**::

    WHERE layer="social" AND degree > 3
    WHERE layer="work" OR layer="social"
    WHERE NOT layer="transport"

**Comparison operators**:

- ``=`` : Equal to
- ``!=`` : Not equal to
- ``>`` : Greater than
- ``<`` : Less than
- ``>=`` : Greater than or equal
- ``<=`` : Less than or equal

COMPUTE Clause
~~~~~~~~~~~~~~

Calculates network measures for filtered nodes::

    COMPUTE degree
    COMPUTE betweenness_centrality
    COMPUTE closeness_centrality
    COMPUTE eigenvector_centrality

**Supported measures**:

- ``degree`` - Node degree
- ``degree_centrality`` - Normalized degree centrality
- ``betweenness_centrality`` - Betweenness centrality
- ``closeness_centrality`` - Closeness centrality
- ``eigenvector_centrality`` - Eigenvector centrality
- ``pagerank`` - PageRank score
- ``clustering`` - Clustering coefficient

**Multiple measures**::

    COMPUTE degree betweenness_centrality closeness_centrality

DSL Syntax Comparison: String vs Builder API
---------------------------------------------

Py3plex provides two complementary ways to query networks: the **SQL-like string DSL** and the **Python builder API (DSL v2)**. Both execute the same underlying query engine, but offer different developer experiences.

When to Use Each
~~~~~~~~~~~~~~~~

**Use String DSL when:**

* Writing quick, exploratory queries in notebooks
* Teaching network concepts with familiar SQL syntax
* Scripting simple one-off analyses
* Maximum readability for domain experts

**Use Builder API when:**

* Building production pipelines
* Needing IDE autocompletion and type checking
* Constructing complex, dynamic queries programmatically
* Exporting results to multiple formats
* Requiring advanced features (layer algebra, EXPLAIN mode)

Side-by-Side Examples
~~~~~~~~~~~~~~~~~~~~~

Here's the same query implemented both ways:

**Example 1: Basic node filtering**

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dsl import execute_query, Q, L

    # Create a small network
    network = multinet.multi_layer_network(directed=False)
    network.add_nodes([
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Carol', 'type': 'social'},
    ])
    network.add_edges([
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Carol', 'source_type': 'social', 'target_type': 'social'},
    ])

    # STRING DSL: SQL-like syntax
    result_string = execute_query(
        network,
        'SELECT nodes WHERE layer="social" AND degree > 1'
    )
    print(f"String DSL found: {result_string['count']} nodes")

    # BUILDER API: Pythonic chainable calls
    result_builder = (
        Q.nodes()
         .from_layers(L["social"])
         .where(degree__gt=1)
         .execute(network)
    )
    print(f"Builder API found: {result_builder.count} nodes")

**Expected output:**

.. code-block:: text

    String DSL found: 1 nodes
    Builder API found: 1 nodes

**Example 2: Computing centrality with ordering**

.. code-block:: python

    # STRING DSL: Compute and return all results
    result_string = execute_query(
        network,
        'SELECT nodes WHERE layer="social" '
        'COMPUTE betweenness_centrality'
    )
    # Manual sorting needed
    centralities = result_string['computed']['betweenness_centrality']
    sorted_nodes = sorted(centralities.items(), key=lambda x: -x[1])
    top_3 = sorted_nodes[:3]

    # BUILDER API: Ordering and limiting built-in
    result_builder = (
        Q.nodes()
         .from_layers(L["social"])
         .compute("betweenness_centrality")
         .order_by("-betweenness_centrality")
         .limit(3)
         .execute(network)
    )
    # Results already ordered and limited
    top_3 = list(result_builder)

**Example 3: Layer algebra**

.. code-block:: python

    # BUILDER API: Advanced layer operations
    # Union: nodes in social OR work layer
    result = (
        Q.nodes()
         .from_layers(L["social"] + L["work"])
         .execute(network)
    )

    # Difference: nodes in social BUT NOT bots
    result = (
        Q.nodes()
         .from_layers(L["social"] - L["bots"])
         .execute(network)
    )

    # Intersection: nodes in BOTH social AND work
    result = (
        Q.nodes()
         .from_layers(L["social"] & L["work"])
         .execute(network)
    )

.. note::

   Layer algebra operations (union, difference, intersection) are **only available in the Builder API**. The string DSL uses OR/AND operators but these work differently (node-level boolean logic, not layer sets).

**Recommendation:** Start with the string DSL for learning and exploration. Migrate to the builder API when building production workflows or needing advanced features.

Python Builder API (DSL v2)
---------------------------

DSL v2 introduces a Pythonic builder API that provides type hints, autocompletion, 
and a chainable interface for constructing queries. The builder API maps directly 
to the DSL syntax but with Python-native ergonomics.

Basic Usage
~~~~~~~~~~~

Import the builder components::

    from py3plex.dsl import Q, L, Param

Create and execute a simple query::

    # Select nodes in the social layer
    result = Q.nodes().where(layer="social").execute(network)
    
    # Get the count
    print(f"Found {result.count} nodes")
    
    # Iterate over results
    for node in result:
        print(node)

Query Builder Methods
~~~~~~~~~~~~~~~~~~~~~

The ``Q`` class provides factory methods to start building queries:

- ``Q.nodes()`` - Start a query for nodes
- ``Q.edges()`` - Start a query for edges

The ``QueryBuilder`` returned supports these chainable methods:

.. code-block:: python

    Q.nodes()
     .from_layers(layer_expr)    # Filter by layers (optional)
     .where(**conditions)        # Filter by conditions (optional)
     .compute(*measures)         # Compute measures (optional)
     .order_by(*keys)            # Order results (optional)
     .limit(n)                   # Limit results (optional)
     .execute(network, **params) # Execute the query

WHERE Conditions
~~~~~~~~~~~~~~~~

The ``where()`` method supports Django-style field lookups:

**Equality**::

    .where(layer="social")

**Comparisons** (using double-underscore suffixes)::

    .where(degree__gt=5)      # degree > 5
    .where(degree__gte=5)     # degree >= 5
    .where(degree__lt=10)     # degree < 10
    .where(degree__lte=10)    # degree <= 10
    .where(layer__ne="bots")  # layer != "bots"

**Multiple conditions** (combined with AND)::

    .where(layer="social", degree__gt=5)

**Special predicates**::

    .where(intralayer=True)                    # Edges within same layer
    .where(interlayer=("social", "work"))     # Edges between specific layers

COMPUTE with Aliases
~~~~~~~~~~~~~~~~~~~~

Compute network measures with optional aliases::

    # Single measure
    result = Q.nodes().compute("betweenness_centrality").execute(network)
    
    # Single measure with alias
    result = Q.nodes().compute("betweenness_centrality", alias="bc").execute(network)
    
    # Multiple measures
    result = Q.nodes().compute("degree", "clustering").execute(network)
    
    # Multiple measures with aliases
    result = Q.nodes().compute(aliases={
        "betweenness_centrality": "bc",
        "closeness_centrality": "cc"
    }).execute(network)

ORDER BY and LIMIT
~~~~~~~~~~~~~~~~~~

Sort and limit results::

    # Order by degree (ascending)
    result = Q.nodes().compute("degree").order_by("degree").execute(network)
    
    # Order descending with - prefix
    result = Q.nodes().compute("degree").order_by("-degree").execute(network)
    
    # Order by multiple keys
    result = Q.nodes().compute("degree", "clustering").order_by("-degree", "clustering").execute(network)
    
    # Limit results
    result = Q.nodes().compute("degree").order_by("-degree").limit(10).execute(network)

Layer Algebra
~~~~~~~~~~~~~

DSL v2 introduces layer algebra for combining multiple layers. Use the ``L`` proxy 
to reference layers and combine them with operators:

**Union** (+): Nodes from either layer::

    layers = L["social"] + L["work"]
    result = Q.nodes().from_layers(layers).execute(network)

**Difference** (-): Nodes from one layer but not another::

    layers = L["social"] - L["bots"]
    result = Q.nodes().from_layers(layers).execute(network)

**Intersection** (&): Nodes in both layers::

    layers = L["social"] & L["work"]
    result = Q.nodes().from_layers(layers).execute(network)

**Complex expressions**::

    # (social OR work) - bots
    layers = L["social"] + L["work"] - L["bots"]
    result = Q.nodes().from_layers(layers).execute(network)

Complete Builder Example
~~~~~~~~~~~~~~~~~~~~~~~~

Here's a comprehensive example using the builder API::

    from py3plex.core import multinet
    from py3plex.dsl import Q, L
    
    # Create network
    network = multinet.multi_layer_network(directed=False)
    network.add_nodes([
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
        {'source': 'Dave', 'type': 'work'},
        {'source': 'Eve', 'type': 'work'},
    ])
    network.add_edges([
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Dave', 'target': 'Eve', 'source_type': 'work', 'target_type': 'work'},
    ])
    
    # Query using builder API
    result = (
        Q.nodes()
         .from_layers(L["social"] + L["work"])
         .where(degree__gt=0)
         .compute("betweenness_centrality", alias="bc")
         .order_by("-bc")
         .limit(3)
         .execute(network)
    )
    
    # Access results
    print(f"Top {result.count} nodes by betweenness centrality:")
    df = result.to_pandas()
    print(df)

QueryResult Object
~~~~~~~~~~~~~~~~~~

The builder API returns a ``QueryResult`` object with rich export capabilities:

**Properties**::

    result.target    # 'nodes' or 'edges'
    result.items     # List of node/edge tuples
    result.count     # Number of items
    result.nodes     # Alias for items (when target='nodes')
    result.edges     # Alias for items (when target='edges')
    result.attributes  # Computed measure values

**Export methods**::

    # Export to pandas DataFrame
    df = result.to_pandas()
    
    # Export to NetworkX subgraph
    G = result.to_networkx(network)
    
    # Export to Apache Arrow table
    table = result.to_arrow()
    
    # Export to dictionary
    d = result.to_dict()

**Iteration**::

    for node in result:
        print(node)
    
    # Length
    print(len(result))

Declarative File Exports
~~~~~~~~~~~~~~~~~~~~~~~~~

DSL v2 supports declarative file exports, allowing you to export query results 
to files as part of the query pipeline itself. The export is a side-effect - 
the query still returns a ``QueryResult`` object to Python.

**Basic CSV Export**::

    from py3plex.dsl import Q, L
    
    # Export to CSV file
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .compute("degree")
         .export_csv("results/social_degree.csv")
         .execute(network)
    )
    
    # Result is still available in Python
    print(f"Exported {result.count} nodes")

**JSON Export with Options**::

    # Export to JSON with custom format
    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .order_by("degree", desc=True)
         .limit(10)
         .export_json(
             "results/top_nodes.json",
             columns=["id", "degree", "betweenness_centrality"],
             orient="records"
         )
         .execute(network)
    )

**Generic Export Method**::

    # Export with explicit format specification
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .compute("degree")
         .export(
             path="results/output.csv",
             fmt="csv",
             columns=["id", "degree"],
             delimiter=";"
         )
         .execute(network)
    )

**Supported Export Formats:**

- ``csv`` - Comma-separated values (default)
- ``json`` - JSON format with various orientations
- ``tsv`` - Tab-separated values

**Export Options:**

*CSV/TSV Options:*

- ``delimiter`` - Field delimiter (default: ``,`` for CSV, ``\t`` for TSV)
- ``columns`` - List of columns to include/order

*JSON Options:*

- ``orient`` - JSON orientation (``records``, ``columns``, ``split``, ``index``, ``values``)
- ``indent`` - Indentation level (default: 2)
- ``columns`` - List of columns to include/order

**Column Selection**::

    # Export only specific columns in specific order
    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality", "clustering")
         .export_csv(
             "results/selected.csv",
             columns=["id", "degree"]  # Only export ID and degree
         )
         .execute(network)
    )

**Complete Export Example**::

    from py3plex.core import multinet
    from py3plex.dsl import Q, L
    
    # Create network
    network = multinet.multi_layer_network(directed=False)
    # ... add nodes and edges ...
    
    # Export social layer analysis to CSV
    (
        Q.nodes()
         .from_layers(L["social"])
         .compute("degree", "betweenness_centrality")
         .order_by("degree", desc=True)
         .export_csv("results/social_analysis.csv")
         .execute(network)
    )
    
    # Export work layer analysis to JSON
    (
        Q.nodes()
         .from_layers(L["work"])
         .compute("degree")
         .export_json("results/work_analysis.json", orient="records")
         .execute(network)
    )
    
    # Export combined analysis with custom delimiter
    (
        Q.nodes()
         .compute("degree")
         .export_csv("results/all_nodes.tsv", delimiter="\t")
         .execute(network)
    )

The export functionality automatically creates parent directories if needed and 
provides clear error messages for unsupported formats or file I/O issues.

.. seealso::

   For a comprehensive example with 7 different usage patterns, see:
   ``examples/network_analysis/example_dsl_export.py``

EXPLAIN Mode
~~~~~~~~~~~~

Get a query execution plan without actually running the query::

    from py3plex.dsl import Q
    
    # Build a query
    q = Q.nodes().where(layer="social").compute("betweenness_centrality")
    
    # Get execution plan
    plan = q.explain().execute(network)
    
    # Inspect the plan
    for step in plan.steps:
        print(f"{step.description} ({step.estimated_complexity})")
    
    # Check for warnings
    for warning in plan.warnings:
        print(f"Warning: {warning}")

The execution plan includes:

- Step-by-step breakdown of query execution
- Estimated time complexity for each step
- Warnings for expensive operations (e.g., betweenness centrality on large graphs)

Parameterized Queries
~~~~~~~~~~~~~~~~~~~~~

Use ``Param`` to create queries with placeholders that are bound at execution time::

    from py3plex.dsl import Q, Param
    
    # Create a reusable query template
    q = Q.nodes().where(layer="social", degree__gt=Param.int("min_degree"))
    
    # Execute with different parameters
    result1 = q.execute(network, min_degree=5)
    result2 = q.execute(network, min_degree=10)

Parameter types:

- ``Param.int("name")`` - Integer parameter
- ``Param.float("name")`` - Float parameter
- ``Param.str("name")`` - String parameter
- ``Param.ref("name")`` - Untyped parameter

Convert Builder to DSL String
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Convert a builder query back to DSL string format::

    q = Q.nodes().where(layer="social", degree__gt=5).compute("degree").limit(10)
    
    # Get DSL string
    dsl_string = q.to_dsl()
    print(dsl_string)
    # Output: SELECT nodes WHERE layer = "social" AND degree > 5 COMPUTE degree LIMIT 10

This is useful for:

- Debugging queries
- Logging and auditing
- Serializing queries for later use

Error Handling with Suggestions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

DSL v2 provides helpful error messages with "Did you mean?" suggestions::

    from py3plex.dsl import Q, UnknownMeasureError
    
    try:
        # Typo in measure name
        result = Q.nodes().compute("betweenes").execute(network)
    except UnknownMeasureError as e:
        print(e)
        # Output: Unknown measure 'betweenes'. Did you mean 'betweenness'?
        #         Known measures: betweenness_centrality, closeness_centrality, ...

Measure Registry
~~~~~~~~~~~~~~~~

DSL v2 includes a centralized registry for network measures. View available measures::

    from py3plex.dsl import measure_registry
    
    # List all measures
    print(measure_registry.list_measures())
    
    # Check if a measure exists
    if measure_registry.has("degree"):
        print("degree is available")
    
    # Get measure description
    desc = measure_registry.get_description("betweenness_centrality")
    print(desc)

Example Queries
---------------

Basic Queries
~~~~~~~~~~~~~

Select all nodes in a layer::

    result = execute_query(network, 'SELECT nodes WHERE layer="social"')

Select high-degree nodes::

    result = execute_query(network, 'SELECT nodes WHERE degree > 5')

Select all nodes (no filter)::

    result = execute_query(network, 'SELECT nodes')

Complex Queries
~~~~~~~~~~~~~~~

Combine multiple conditions::

    # Nodes in transport layer with high degree
    result = execute_query(
        network,
        'SELECT nodes WHERE layer="transport" AND degree > 5'
    )

Use OR operator::

    # Nodes in either social or work layer
    result = execute_query(
        network,
        'SELECT nodes WHERE layer="social" OR layer="work"'
    )

Degree range filtering::

    # Nodes with moderate degree
    result = execute_query(
        network,
        'SELECT nodes WHERE degree >= 2 AND degree <= 5'
    )

Analytical Queries
~~~~~~~~~~~~~~~~~~

Compute centrality for a layer::

    result = execute_query(
        network,
        'SELECT nodes WHERE layer="transport" COMPUTE betweenness_centrality'
    )
    
    # Access computed values
    for node, centrality in result['computed']['betweenness_centrality'].items():
        print(f"{node}: {centrality}")

Multiple measures for filtered nodes::

    result = execute_query(
        network,
        'SELECT nodes WHERE degree > 3 COMPUTE degree_centrality closeness_centrality'
    )

Working with Results
--------------------

The ``execute_query`` function returns a dictionary containing:

- ``query``: Original query string
- ``target``: Query target (nodes or edges)
- ``nodes`` or ``edges``: List of selected items
- ``count``: Number of items returned
- ``computed``: Dictionary of computed measures (if COMPUTE used)

Example::

    result = execute_query(network, 'SELECT nodes WHERE layer="social"')
    
    # Access results
    print(f"Found {result['count']} nodes")
    for node in result['nodes']:
        print(node)
    
    # If COMPUTE was used
    if 'computed' in result:
        for measure, values in result['computed'].items():
            print(f"{measure}:")
            for node, value in values.items():
                print(f"  {node}: {value}")

**Example Output:**

.. code-block:: text

    Found 3 nodes
    ('Alice', 'social')
    ('Bob', 'social')
    ('Charlie', 'social')

Formatting Results
~~~~~~~~~~~~~~~~~~

Use ``format_result`` for human-readable output::

    from py3plex.dsl import format_result
    
    result = execute_query(network, 'SELECT nodes WHERE degree > 3')
    print(format_result(result, limit=10))

Convenience Functions
---------------------

The DSL module provides convenience functions for common operations:

Select nodes by layer::

    from py3plex.dsl import select_nodes_by_layer
    
    nodes = select_nodes_by_layer(network, 'transport')

Select high-degree nodes::

    from py3plex.dsl import select_high_degree_nodes
    
    # All high-degree nodes
    nodes = select_high_degree_nodes(network, min_degree=5)
    
    # High-degree nodes in specific layer
    nodes = select_high_degree_nodes(network, min_degree=5, layer='social')

Compute centrality for a layer::

    from py3plex.dsl import compute_centrality_for_layer
    
    centrality = compute_centrality_for_layer(
        network, 
        layer='transport',
        centrality='betweenness_centrality'
    )

Use Cases
---------

Hub Identification
~~~~~~~~~~~~~~~~~~

Find important nodes in each layer::

    for layer in ['social', 'work', 'transport']:
        result = execute_query(
            network,
            f'SELECT nodes WHERE layer="{layer}" AND degree > 5'
        )
        print(f"Hubs in {layer}: {result['count']}")

Layer Comparison
~~~~~~~~~~~~~~~~

Compare network properties across layers::

    layers = ['social', 'work', 'transport']
    
    for layer in layers:
        result = execute_query(
            network,
            f'SELECT nodes WHERE layer="{layer}" COMPUTE degree'
        )
        degrees = result['computed']['degree']
        avg_degree = sum(degrees.values()) / len(degrees)
        print(f"{layer} average degree: {avg_degree:.2f}")

Node Importance Ranking
~~~~~~~~~~~~~~~~~~~~~~~

Rank nodes by multiple measures::

    result = execute_query(
        network,
        'SELECT nodes WHERE layer="social" COMPUTE betweenness_centrality degree_centrality'
    )
    
    # Combine measures for ranking
    scores = {}
    for node in result['nodes']:
        betweenness = result['computed']['betweenness_centrality'].get(node, 0)
        degree_cent = result['computed']['degree_centrality'].get(node, 0)
        scores[node] = betweenness + degree_cent
    
    # Show top nodes
    for node, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"{node}: {score:.4f}")

Network Filtering
~~~~~~~~~~~~~~~~~

Create subnetworks based on queries::

    # Get high-degree nodes
    result = execute_query(network, 'SELECT nodes WHERE degree > 5')
    high_degree_nodes = result['nodes']
    
    # Create subnetwork with these nodes
    subnetwork = network.subnetwork(
        [node for node in high_degree_nodes],
        subset_by='node_layer_names'
    )

Error Handling
--------------

The DSL raises specific exceptions for different error types.

Legacy Error Types
~~~~~~~~~~~~~~~~~~

For string DSL queries::

    from py3plex.dsl import execute_query, DSLSyntaxError, DSLExecutionError
    
    try:
        result = execute_query(network, 'SELECT nodes WHERE invalid_condition')
    except DSLSyntaxError as e:
        print(f"Syntax error: {e}")
    except DSLExecutionError as e:
        print(f"Execution error: {e}")

DSL v2 Error Types
~~~~~~~~~~~~~~~~~~

For builder API queries, more specific error types are available::

    from py3plex.dsl import (
        Q,
        DslError,              # Base error class
        DslSyntaxError,        # Syntax errors
        DslExecutionError,     # Execution errors
        UnknownAttributeError, # Unknown attribute name
        UnknownMeasureError,   # Unknown measure name
        UnknownLayerError,     # Unknown layer name
        ParameterMissingError, # Missing parameter
        TypeMismatchError,     # Type mismatch
    )
    
    try:
        result = Q.nodes().compute("unknwon_measure").execute(network)
    except UnknownMeasureError as e:
        print(e)  # Includes "Did you mean?" suggestion
    except DslError as e:
        print(f"DSL error: {e}")

All DSL v2 errors include:

- Original query context (when available)
- Line and column information for syntax errors
- "Did you mean?" suggestions using Levenshtein distance

Common syntax errors:

- Missing SELECT keyword
- Invalid target (not 'nodes' or 'edges')
- Malformed conditions
- Unknown operators
- Invalid measure names

Common DSL Errors
~~~~~~~~~~~~~~~~~

Here's an example of a common error and how to fix it:

**Malformed Query (missing quotes around layer name):**

.. code-block:: python

    # Wrong - missing quotes around layer name
    result = execute_query(network, 'SELECT nodes WHERE layer=social')

**Error:**

.. code-block:: text

    DslSyntaxError: Invalid condition at position 27: expected quoted string for layer value.
    Hint: Use layer="social" instead of layer=social

**Fix:**

.. code-block:: python

    # Correct - layer name is quoted
    result = execute_query(network, 'SELECT nodes WHERE layer="social"')

**Unknown measure name:**

.. code-block:: python

    result = Q.nodes().compute("betweenes").execute(network)
    # UnknownMeasureError: Unknown measure 'betweenes'. Did you mean 'betweenness_centrality'?

See the :doc:`../reference/api_index` for complete details on DSL exceptions and error types.

Complete Working Examples
-------------------------

This section provides complete, runnable examples demonstrating various DSL features with expected outputs.

Example 1: Basic Network Querying
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a simple social network and query it::

    from py3plex.core import multinet
    from py3plex.dsl import execute_query, format_result
    
    # Create network
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes in social layer
    network.add_nodes([
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
        {'source': 'David', 'type': 'social'},
    ])
    
    # Add edges
    network.add_edges([
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Charlie', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
    ])
    
    # Query all nodes
    result = execute_query(network, 'SELECT nodes WHERE layer="social"')
    print(format_result(result))
    
    # Find high-degree nodes
    result = execute_query(network, 'SELECT nodes WHERE degree > 1')
    print(f"High-degree nodes: {result['count']}")

**Expected Output:**

.. code-block:: text

    Query: SELECT nodes WHERE layer="social"
    Target: nodes
    Count: 4
    
    Nodes (showing 4 of 4):
      ('Alice', 'social')
      ('Bob', 'social')
      ('Charlie', 'social')
      ('David', 'social')
    
    High-degree nodes: 3

Example 2: Multilayer Network Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Analyze a network with multiple layers::

    from py3plex.core import multinet
    from py3plex.dsl import execute_query
    
    # Create multilayer network
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes to multiple layers
    nodes = []
    for person in ['Alice', 'Bob', 'Charlie']:
        for layer in ['social', 'work', 'family']:
            nodes.append({'source': person, 'type': layer})
    network.add_nodes(nodes)
    
    # Add edges in different layers
    edges = [
        # Social connections
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        # Work connections
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work'},
        # Family connections
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'family', 'target_type': 'family'},
    ]
    network.add_edges(edges)
    
    # Compare layers
    for layer in ['social', 'work', 'family']:
        result = execute_query(network, f'SELECT nodes WHERE layer="{layer}"')
        print(f"{layer} layer: {result['count']} nodes")
        
        # Compute degree for this layer
        result = execute_query(network, f'SELECT nodes WHERE layer="{layer}" COMPUTE degree')
        degrees = result['computed']['degree']
        avg_degree = sum(degrees.values()) / len(degrees) if degrees else 0
        print(f"  Average degree: {avg_degree:.2f}")

**Expected Output:**

.. code-block:: text

    social layer: 3 nodes
      Average degree: 1.33
    work layer: 3 nodes
      Average degree: 0.67
    family layer: 3 nodes
      Average degree: 0.67

Example 3: Hub Identification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Find and rank important nodes using multiple centrality measures::

    from py3plex.core import multinet
    from py3plex.dsl import execute_query
    
    # Create network
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    network.add_nodes([
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
        {'source': 'David', 'type': 'social'},
        {'source': 'Eve', 'type': 'social'},
    ])
    
    # Add edges creating a star network centered on Bob
    network.add_edges([
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Eve', 'source_type': 'social', 'target_type': 'social'},
    ])
    
    # Find high-degree nodes in social layer
    result = execute_query(
        network,
        'SELECT nodes WHERE layer="social" AND degree >= 2'
    )
    print(f"Found {result['count']} hub nodes")
    
    # Compute multiple centrality measures for hubs
    result = execute_query(
        network,
        'SELECT nodes WHERE layer="social" AND degree >= 2 '
        'COMPUTE betweenness_centrality closeness_centrality degree_centrality'
    )
    
    # Rank nodes by betweenness centrality
    if 'computed' in result and 'betweenness_centrality' in result['computed']:
        centralities = result['computed']['betweenness_centrality']
        sorted_nodes = sorted(centralities.items(), key=lambda x: x[1], reverse=True)
        
        print("\nTop nodes by betweenness centrality:")
        for node, centrality in sorted_nodes[:5]:
            print(f"  {node}: {centrality:.4f}")

**Expected Output:**

.. code-block:: text

    Found 1 hub nodes
    
    Top nodes by betweenness centrality:
      ('Bob', 'social'): 1.0000

Example 4: Layer Comparison Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compare network structure across different layers::

    from py3plex.core import multinet
    from py3plex.dsl import execute_query
    
    # Create multilayer network
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes to multiple layers
    people = ['Alice', 'Bob', 'Charlie', 'David']
    nodes = []
    for person in people:
        for layer in ['social', 'work', 'transport']:
            nodes.append({'source': person, 'type': layer})
    network.add_nodes(nodes)
    
    # Add edges in different layers
    network.add_edges([
        # Social (well connected)
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Charlie', 'target': 'David', 'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Charlie', 'source_type': 'social', 'target_type': 'social'},
        # Work (moderately connected)
        {'source': 'Alice', 'target': 'Bob', 'source_type': 'work', 'target_type': 'work'},
        {'source': 'Bob', 'target': 'Charlie', 'source_type': 'work', 'target_type': 'work'},
        # Transport (sparsely connected)
        {'source': 'Alice', 'target': 'David', 'source_type': 'transport', 'target_type': 'transport'},
    ])
    
    layers = ['social', 'work', 'transport']
    layer_stats = {}
    
    for layer in layers:
        # Get nodes in this layer
        result = execute_query(network, f'SELECT nodes WHERE layer="{layer}"')
        node_count = result['count']
        
        # Compute centrality measures
        result = execute_query(
            network,
            f'SELECT nodes WHERE layer="{layer}" COMPUTE betweenness_centrality'
        )
        
        if 'computed' in result and 'betweenness_centrality' in result['computed']:
            centralities = result['computed']['betweenness_centrality']
            avg_centrality = sum(centralities.values()) / len(centralities) if centralities else 0
            max_centrality = max(centralities.values()) if centralities else 0
            
            layer_stats[layer] = {
                'nodes': node_count,
                'avg_centrality': avg_centrality,
                'max_centrality': max_centrality
            }
    
    # Print comparison
    print("\nLayer Comparison:")
    print(f"{'Layer':<12} {'Nodes':<8} {'Avg Centrality':<16} {'Max Centrality':<16}")
    print("-" * 55)
    for layer, stats in layer_stats.items():
        print(f"{layer:<12} {stats['nodes']:<8} {stats['avg_centrality']:<16.4f} {stats['max_centrality']:<16.4f}")

**Expected Output:**

.. code-block:: text

    Layer Comparison:
    Layer        Nodes    Avg Centrality   Max Centrality
    -------------------------------------------------------
    social       4        0.1667           0.5000
    work         4        0.0833           0.3333
    transport    4        0.0000           0.0000

Example Files
~~~~~~~~~~~~~

Additional complete examples are available in the repository:

- ``examples/network_analysis/example_dsl_builder_api.py`` - **Comprehensive builder API examples** (recommended starting point for DSL v2)
- ``examples/network_analysis/example_dsl_queries.py`` - Basic DSL usage with string syntax
- ``examples/network_analysis/example_dsl_advanced.py`` - Advanced queries and transportation network analysis
- ``examples/network_analysis/example_dsl_community_detection.py`` - Community detection with DSL
- ``examples/cli/example_3_dsl_queries.sh`` - CLI usage examples for both string and builder syntax

Run these examples::

    # Recommended: Comprehensive builder API examples
    python examples/network_analysis/example_dsl_builder_api.py
    
    # String DSL examples
    python examples/network_analysis/example_dsl_queries.py
    
    # Advanced queries
    python examples/network_analysis/example_dsl_advanced.py

API Reference
-------------

Main Functions
~~~~~~~~~~~~~~

.. code-block:: python

    def execute_query(network: Any, query: str) -> Dict[str, Any]:
        """Execute a DSL query on a multilayer network.
        
        Args:
            network: Multilayer network object
            query: DSL query string
            
        Returns:
            Dictionary with 'nodes'/'edges', 'count', and optionally 'computed'
        """

    def format_result(result: Dict[str, Any], limit: int = 10) -> str:
        """Format query result as human-readable string.
        
        Args:
            result: Result from execute_query
            limit: Maximum items to display
            
        Returns:
            Formatted string
        """

Convenience Functions
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def select_nodes_by_layer(network: Any, layer: str) -> List[Any]:
        """Select all nodes in a specific layer."""
    
    def select_high_degree_nodes(network: Any, min_degree: int, 
                                 layer: Optional[str] = None) -> List[Any]:
        """Select nodes with degree above threshold."""
    
    def compute_centrality_for_layer(network: Any, layer: str, 
                                     centrality: str = 'betweenness_centrality') -> Dict[Any, float]:
        """Compute centrality for all nodes in a layer."""

DSL v2 Builder API
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class Q:
        """Query factory for creating QueryBuilder instances."""
        
        @staticmethod
        def nodes() -> QueryBuilder:
            """Create a query builder for nodes."""
        
        @staticmethod
        def edges() -> QueryBuilder:
            """Create a query builder for edges."""
    
    class QueryBuilder:
        """Chainable query builder."""
        
        def from_layers(self, layer_expr: LayerExprBuilder) -> QueryBuilder:
            """Filter by layers using layer algebra."""
        
        def where(self, **kwargs) -> QueryBuilder:
            """Add WHERE conditions."""
        
        def compute(self, *measures: str, alias: str = None) -> QueryBuilder:
            """Add measures to compute."""
        
        def order_by(self, *keys: str, desc: bool = False) -> QueryBuilder:
            """Add ORDER BY clause."""
        
        def limit(self, n: int) -> QueryBuilder:
            """Limit number of results."""
        
        def explain(self) -> ExplainQuery:
            """Create EXPLAIN query for execution plan."""
        
        def execute(self, network: Any, **params) -> QueryResult:
            """Execute the query."""
        
        def to_ast(self) -> Query:
            """Export as AST Query object."""
        
        def to_dsl(self) -> str:
            """Export as DSL string."""
    
    class QueryResult:
        """Rich result object from query execution."""
        
        target: str       # 'nodes' or 'edges'
        items: List[Any]  # List of node/edge tuples
        count: int        # Number of items
        attributes: Dict  # Computed measure values
        
        def to_pandas(self):
            """Export to pandas DataFrame."""
        
        def to_networkx(self, network=None):
            """Export to NetworkX subgraph."""
        
        def to_arrow(self):
            """Export to Apache Arrow table."""
        
        def to_dict(self) -> Dict[str, Any]:
            """Export as dictionary."""
    
    class L:
        """Layer proxy for layer algebra."""
        
        def __getitem__(self, name: str) -> LayerExprBuilder:
            """Create layer expression: L['social']"""
    
    class Param:
        """Factory for parameter references."""
        
        @staticmethod
        def int(name: str) -> ParamRef:
            """Create integer parameter."""
        
        @staticmethod
        def float(name: str) -> ParamRef:
            """Create float parameter."""
        
        @staticmethod
        def str(name: str) -> ParamRef:
            """Create string parameter."""

DSL-Based Dynamics Simulation
------------------------------

The py3plex DSL extends beyond network queries to support declarative dynamics
simulation on multilayer networks. This section demonstrates how to use the
dynamics DSL for epidemic modeling and other dynamical processes.

For detailed documentation and formalism, see :doc:`../../../book/part3_dsl/chapter10_advanced_queries_workflows`.

Quickstart
~~~~~~~~~~~

The dynamics DSL uses a builder API similar to the query DSL:

.. code-block:: python

    from py3plex.dynamics import D, SIS
    from py3plex.core import multinet

    # Create network
    network = multinet.multi_layer_network()
    # ... add nodes and edges ...

    # Define SIS simulation
    sim = (
        D.process(SIS(beta=0.3, mu=0.1))  # Transmission and recovery rates
         .initial(infected=0.05)           # 5% initially infected
         .steps(100)                       # Run for 100 time steps
         .measure("prevalence", "incidence")  # Track measures
         .replicates(10)                   # Run 10 independent simulations
         .seed(42)                         # For reproducibility
    )

    # Execute simulation
    result = sim.run(network)

    # Access results
    print(f"Mean final prevalence: {result.data['prevalence'][:, -1].mean():.3f}")

    # Convert to pandas for analysis
    df_dict = result.to_pandas()
    prevalence_df = df_dict['prevalence']

Available Processes
~~~~~~~~~~~~~~~~~~~

The dynamics module supports several built-in processes:

- **SIS** - Susceptible-Infected-Susceptible (endemic diseases)
- **SIR** - Susceptible-Infected-Recovered (epidemic diseases with immunity)
- **RandomWalk** - Random walk dynamics on networks

Each process has configurable parameters:

.. code-block:: python

    from py3plex.dynamics import SIS, SIR, RandomWalk

    # SIS with transmission rate β=0.3, recovery rate μ=0.1
    SIS(beta=0.3, mu=0.1)

    # SIR with transmission rate β=0.4, recovery rate γ=0.15
    SIR(beta=0.4, gamma=0.15)

    # Random walk with teleportation probability
    RandomWalk(teleport=0.05)

Multilayer Dynamics
~~~~~~~~~~~~~~~~~~~

The dynamics DSL seamlessly integrates with layer selection:

.. code-block:: python

    from py3plex.dsl import L

    # Simulate on specific layers
    sim = (
        D.process(SIS(beta=0.25, mu=0.08))
         .on_layers(L["offline"] + L["online"])  # Select layers using layer algebra
         .coupling(node_replicas="strong")       # Nodes share states across layers
         .initial(infected=0.1)
         .steps(120)
         .measure("prevalence", "prevalence_by_layer")
         .replicates(15)
    )

    result = sim.run(multilayer_network)

Integration with Query DSL
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use query DSL to specify targeted initial conditions:

.. code-block:: python

    from py3plex.dsl import Q

    # Start infection at high-degree nodes (hubs)
    sim = (
        D.process(SIS(beta=0.35, mu=0.12))
         .initial(
             infected=Q.nodes().where(degree__gte=5)  # Query selects hubs
         )
         .steps(100)
         .measure("prevalence")
         .replicates(10)
    )

    result = sim.run(network)

This powerful combination allows precise control over initial conditions based
on network structure, centrality, or any other computable property.

Result Analysis
~~~~~~~~~~~~~~~

The ``SimulationResult`` object provides rich analysis capabilities:

.. code-block:: python

    # Get summary statistics
    summary = result.summary()
    print(summary)

    # Plot time series with confidence intervals
    import matplotlib.pyplot as plt
    result.plot("prevalence")
    plt.show()

    # Export to pandas for custom analysis
    df_dict = result.to_pandas()
    prevalence_df = df_dict['prevalence']

    # Compute mean trajectory across replicates
    mean_trajectory = (
        prevalence_df
        .groupby('t')['value']
        .agg(['mean', 'std'])
    )

Complete Example
~~~~~~~~~~~~~~~~

See ``examples/network_analysis/example_dsl_dynamics.py`` for a comprehensive
example demonstrating:

- SIS and SIR epidemic simulations
- Multilayer dynamics with coupling
- Random walk dynamics
- Query DSL integration for initial conditions
- Parameter comparison across simulations

Run the example::

    python examples/network_analysis/example_dsl_dynamics.py

Further Reading
^^^^^^^^^^^^^^^

For mathematical formalism and detailed documentation:

- :doc:`../../../book/part3_dsl/chapter10_advanced_queries_workflows` - Complete dynamics DSL guide with formalism
- ``examples/network_analysis/example_dsl_dynamics.py`` - Comprehensive dynamics examples
- ``examples/advanced/example_dynamics_core.py`` - Core dynamics classes (OOP-style)
- :doc:`../sir_epidemic_simulator` - SIR multiplex simulator documentation

Limitations and Future Work
----------------------------

Current limitations:

- Edge queries are not yet fully supported
- Complex nested conditions require multiple queries
- Limited to NetworkX-based measures
- No aggregation functions (SUM, AVG, etc.)

Planned enhancements:

- Full edge query support
- Nested subqueries
- Aggregation operators
- Custom measure registration
- Query optimization
- Save/load query results

Best Practices
--------------

**1. Choose the Right API**

- **Builder API (Q.nodes())**: Recommended for production code, complex queries, and when type hints are important
- **String DSL**: Good for simple queries, interactive exploration, and when learning the syntax

**2. Start simple, build incrementally**

Begin with basic queries and add complexity step by step:

.. code-block:: python

    # Start simple
    result = Q.nodes().execute(network)
    
    # Add filtering
    result = Q.nodes().where(layer="social").execute(network)
    
    # Add computation
    result = Q.nodes().where(layer="social").compute("degree").execute(network)
    
    # Add ordering and limiting
    result = (
        Q.nodes()
        .where(layer="social")
        .compute("degree")
        .order_by("-degree")
        .limit(10)
        .execute(network)
    )

**3. Use parameterized queries for reusability**

Create reusable query templates with Param:

.. code-block:: python

    # Define once
    top_nodes_query = (
        Q.nodes()
        .where(layer=Param.str("layer_name"), degree__gt=Param.int("threshold"))
        .compute("betweenness_centrality")
        .order_by("-betweenness_centrality")
        .limit(Param.int("top_n"))
    )
    
    # Execute many times with different parameters
    social_hubs = top_nodes_query.execute(network, layer_name="social", threshold=5, top_n=10)
    work_hubs = top_nodes_query.execute(network, layer_name="work", threshold=3, top_n=20)

**4. Use EXPLAIN for expensive queries**

Before running expensive queries on large networks, check the execution plan:

.. code-block:: python

    q = Q.nodes().compute("betweenness_centrality")
    plan = q.explain().execute(network)
    
    for step in plan.steps:
        print(f"{step.description} - {step.estimated_complexity}")
    
    if plan.warnings:
        print("Warnings:", plan.warnings)

**5. Validate data and check results**

Always inspect result counts and samples before processing large result sets:

.. code-block:: python

    result = Q.nodes().where(degree__gt=5).execute(network)
    
    print(f"Found {result.count} nodes")
    if result.count > 0:
        print(f"Sample: {result.items[:3]}")
        # Process results...

**6. Choose appropriate export format**

- **to_pandas()**: Best for data analysis, statistical operations, and visualization
- **to_networkx()**: Best for further NetworkX operations or subgraph analysis
- **to_arrow()**: Best for large datasets, columnar operations, or data interchange
- **to_dict()**: Best for serialization, API responses, or custom processing

**7. Handle errors gracefully**

Use try-except blocks and leverage error messages:

.. code-block:: python

    from py3plex.dsl import Q, UnknownMeasureError
    
    try:
        result = Q.nodes().compute("my_measure").execute(network)
    except UnknownMeasureError as e:
        print(f"Measure not found: {e}")
        # Fallback logic or use suggested measure

**8. Performance optimization**

For large networks, follow these guidelines:

- Filter by layer first to reduce search space
- Use ``limit()`` to restrict result size when you don't need all results
- Cache computed measures if reusing them multiple times
- Consider using ``degree`` instead of more expensive centrality measures for initial filtering

.. code-block:: python

    # Less efficient - computes centrality for all nodes
    result = Q.nodes().compute("betweenness_centrality").order_by("-betweenness_centrality").limit(10).execute(network)
    
    # More efficient - filter by degree first
    result = Q.nodes().where(degree__gt=5).compute("betweenness_centrality").order_by("-betweenness_centrality").limit(10).execute(network)

Performance Considerations
--------------------------

- Computing centrality measures can be expensive on large networks
- Filter by layer first to reduce search space
- Cache computed measures if reusing them
- Consider using convenience functions for better performance
- Pre-compute measures and store in node attributes for repeated use

Example performance optimization::

    # Less efficient - computes centrality multiple times
    for threshold in [3, 5, 7]:
        result = execute_query(
            network,
            f'SELECT nodes WHERE degree > {threshold} COMPUTE betweenness_centrality'
        )
    
    # More efficient - compute once, filter in post-processing
    result = execute_query(
        network,
        'SELECT nodes COMPUTE betweenness_centrality'
    )
    centralities = result['computed']['betweenness_centrality']
    
    for threshold in [3, 5, 7]:
        high_degree = [n for n in result['nodes'] 
                      if network.core_network.degree(n) > threshold]

Further Reading
---------------

- :doc:`../getting_started/quickstart_5min` - Network construction basics
- :doc:`../concepts/multilayer_networks_101` - Understanding multilayer networks
- :doc:`../reference/algorithm_reference` - Network analysis algorithms
- :doc:`recipes_and_workflows` - Common analysis patterns

See Also
--------

- :doc:`graph_ops` - Dplyr-style chainable graph operations (alternative API for complex transformations)
- NetworkX documentation for centrality measures
- Examples directory for complete use cases
- API documentation for detailed function signatures
