SQL-like DSL for Multilayer Networks
=====================================

.. contents:: Table of Contents
   :local:
   :depth: 2

.. note::

   **For AI Agents and Advanced Users**: See ``AGENTS.md`` in the repository root for:
   
   - Formal DSL v2 specification with RFC 2119 keywords
   - Complete decision guide (when to use DSL vs graph_ops vs pipeline API)
   - Multilayer semantics guide (node replicas, degree ambiguity, coverage modes)
   - Comprehensive testing strategy and correctness guarantees
   - 30+ advanced topics (UQ, dynamics, temporal, semiring algebra, etc.)
   
   This RST guide covers basic usage and quick start. AGENTS.md provides the complete reference.

.. important::

   **Current DSL Version: 2.1**
   
   This documentation covers **DSL v2 (Builder API)** as the recommended approach. The legacy string-based DSL remains available for backward compatibility but is not recommended for new code.

Overview
--------

Py3plex provides a Domain-Specific Language (DSL) for querying and analyzing multilayer networks using SQL-like syntax. This intuitive interface allows users to filter nodes and edges, compute network measures, and perform complex analyses with simple, readable queries.

**DSL v2 (Current)** introduces several major improvements:

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

**Recommended: Using Builder API (DSL v2)**

Here's a complete working example using the modern Builder API::

    from py3plex.core import multinet
    from py3plex.dsl import Q, L
    
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
    result = Q.nodes().from_layers(L["social"]).execute(network)
    print(f"Found {result.count} nodes in social layer")
    print(result.items[:5])  # Show first 5
    
    # Query 2: Find high-degree nodes
    result = Q.nodes().where(degree__gt=1).execute(network)
    print(f"Found {result.count} high-degree nodes")
    
    # Query 3: Compute centrality for filtered nodes
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .compute("betweenness_centrality")
         .execute(network)
    )
    # Export to pandas for analysis
    df = result.to_pandas()
    print(df[['node', 'betweenness_centrality']].head())

**Expected Output:**

.. code-block:: text

    Found 3 nodes in social layer
    [('Alice', 'social'), ('Bob', 'social'), ('Charlie', 'social')]
    
    Found 1 high-degree nodes
    
           node  betweenness_centrality
    0  (Alice, social)              0.0000
    1    (Bob, social)              1.0000
    2 (Charlie, social)             0.0000

.. note::

   **Legacy String DSL**: The original string-based DSL using ``execute_query()`` and ``format_result()`` is still available for backward compatibility but is **not recommended for new code**. See the "String DSL (Legacy)" section below for details.

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

Approximate Centrality (Fast Path)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For large networks, centrality computation can be slow. Py3plex provides **fast approximate algorithms** as first-class citizens in both DSL syntaxes.

**String DSL with APPROXIMATE keyword:**

.. code-block:: python

    # Use default approximation method
    execute_query(net, 'SELECT nodes COMPUTE betweenness_centrality APPROXIMATE')
    
    # Specify method and parameters
    execute_query(net, 
        'SELECT nodes COMPUTE betweenness_centrality APPROXIMATE(method="sampling", n_samples=512, seed=42)'
    )

**Builder API with approx parameters:**

.. code-block:: python

    from py3plex.dsl import Q
    
    # Approximate betweenness (sampling-based)
    result = Q.nodes().compute(
        "betweenness_centrality",
        approx=True,
        n_samples=512,
        seed=42
    ).execute(net)
    
    # Approximate closeness (landmark-based)
    result = Q.nodes().compute(
        "closeness_centrality",
        approx=True,
        n_landmarks=64,
        seed=42
    ).execute(net)
    
    # Approximate PageRank (power iteration)
    result = Q.nodes().compute(
        "pagerank",
        approx=True,
        tol=1e-6,
        max_iter=100
    ).execute(net)

**Supported approximation methods:**

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Measure
     - Default Method
     - Parameters
   * - ``betweenness_centrality``
     - ``sampling``
     - ``n_samples`` (int), ``seed`` (int)
   * - ``closeness_centrality``
     - ``landmarks``
     - ``n_landmarks`` (int), ``seed`` (int)
   * - ``pagerank``
     - ``power_iteration``
     - ``tol`` (float), ``max_iter`` (int)

**Approximation guarantees:**

- **Determinism**: Same ``seed`` produces identical results
- **Accuracy**: Approximate values are close to exact on small graphs
- **Provenance**: Approximation parameters recorded in ``result.meta["approximation"]``
- **Fast path**: ``fast_path=True`` set in provenance when approximation is used

**When to use approximation:**

- Networks with >1000 nodes where exact computation is slow
- Exploratory analysis where approximate values are sufficient
- Production pipelines requiring predictable execution time
- Sensitivity analysis with multiple runs (use different seeds)

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
     .mutate(**transformations)  # Transform/create columns (optional)
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

MUTATE - Row-wise Transformations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``mutate()`` method creates new columns or transforms existing ones using 
row-by-row operations (similar to dplyr::mutate in R). This is different from 
``summarize()`` or ``aggregate()`` which operate on groups of rows.

**Basic transformation with lambda functions**::

    # Create a new column based on existing attributes
    result = Q.nodes().compute("degree").mutate(
        doubled_degree=lambda row: row.get("degree", 0) * 2
    ).execute(network)

**Multiple transformations**::

    # Create several derived columns at once
    result = Q.nodes().compute("degree", "clustering").mutate(
        hub_score=lambda row: row.get("degree", 0) * row.get("clustering", 0),
        is_hub=lambda row: row.get("degree", 0) > 2,
        normalized_degree=lambda row: row.get("degree", 0) / 10.0
    ).execute(network)

**Conditional transformations**::

    # Use conditional logic in transformations
    result = Q.nodes().compute("degree").mutate(
        category=lambda row: "hub" if row.get("degree", 0) > 3 else "peripheral"
    ).execute(network)

**Chaining with other operations**::

    # Combine mutate with filtering and ordering
    result = (
        Q.nodes()
         .where(layer="social")
         .compute("degree", "betweenness_centrality")
         .mutate(
             influence=lambda row: (
                 row.get("degree", 0) * 0.4 + 
                 row.get("betweenness_centrality", 0) * 0.6
             )
         )
         .order_by("-influence")
         .limit(10)
         .execute(network)
    )

The lambda function receives a dictionary with all available attributes for each node/edge,
including computed metrics and network properties.

.. seealso::
   
   For complete examples of mutate operations, see:
   ``examples/network_analysis/example_dsl_mutate.py``

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

String DSL (Legacy)
-------------------

.. warning::

   **Legacy API**: The string-based DSL using ``execute_query()`` is maintained for **backward compatibility only**. New code should use the **Builder API (DSL v2)** shown in the examples above. The string DSL has the following limitations:
   
   - No type hints or IDE autocompletion
   - Limited error messages
   - No layer algebra operations
   - No EXPLAIN mode
   - Dictionary-based results (less ergonomic than Builder API's QueryResult objects)

If you're maintaining legacy code or need SQL-like syntax for teaching, the string DSL is still available:

Example Queries
~~~~~~~~~~~~~~~

Basic Queries
^^^^^^^^^^^^^

Select all nodes in a layer::

    result = execute_query(network, 'SELECT nodes WHERE layer="social"')

Select high-degree nodes::

    result = execute_query(network, 'SELECT nodes WHERE degree > 5')

Select all nodes (no filter)::

    result = execute_query(network, 'SELECT nodes')

Complex Queries
^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^

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

Working with Legacy Results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^

Use ``format_result`` for human-readable output::

    from py3plex.dsl import format_result
    
    result = execute_query(network, 'SELECT nodes WHERE degree > 3')
    print(format_result(result, limit=10))

Legacy Convenience Functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

.. note::

   **End of Legacy DSL Section**: The sections above document the legacy string-based DSL for backward compatibility. For new code, use the Builder API (DSL v2) shown in the examples below.

Use Cases with Builder API
---------------------------

Hub Identification
~~~~~~~~~~~~~~~~~~

Find important nodes in each layer::

    from py3plex.dsl import Q, L
    
    for layer_name in ['social', 'work', 'transport']:
        result = (
            Q.nodes()
             .from_layers(L[layer_name])
             .where(degree__gt=5)
             .execute(network)
        )
        print(f"Hubs in {layer_name}: {result.count}")

Layer Comparison
~~~~~~~~~~~~~~~~

Compare network properties across layers::

    from py3plex.dsl import Q, L
    import pandas as pd
    
    layers = ['social', 'work', 'transport']
    stats = []
    
    for layer_name in layers:
        result = (
            Q.nodes()
             .from_layers(L[layer_name])
             .compute("degree")
             .execute(network)
        )
        df = result.to_pandas()
        avg_degree = df['degree'].mean()
        stats.append({'layer': layer_name, 'avg_degree': avg_degree})
    
    stats_df = pd.DataFrame(stats)
    print(stats_df)

Node Importance Ranking
~~~~~~~~~~~~~~~~~~~~~~~

Rank nodes by multiple measures::

    from py3plex.dsl import Q, L
    
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .compute("betweenness_centrality", "degree_centrality")
         .execute(network)
    )
    
    # Convert to pandas for easy analysis
    df = result.to_pandas()
    df['combined_score'] = df['betweenness_centrality'] + df['degree_centrality']
    df = df.sort_values('combined_score', ascending=False)
    
    # Show top nodes
    print(df[['node', 'combined_score']].head())

Network Filtering
~~~~~~~~~~~~~~~~~

Create subnetworks based on queries::

    from py3plex.dsl import Q
    
    # Get high-degree nodes
    result = Q.nodes().where(degree__gt=5).execute(network)
    high_degree_nodes = result.items
    
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

For detailed documentation and formalism, see `advanced queries documentation <../how-to/query_zoo.html>`_.

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

- `advanced queries documentation <../how-to/query_zoo.html>`_ - Complete dynamics DSL guide with formalism
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

Replayable Provenance and Query Replay
---------------------------------------

**New in v1.1:** py3plex provides replayable provenance that captures sufficient information to deterministically reproduce query results. This enables reproducible research, debugging, and result verification.

Basic Usage
~~~~~~~~~~~

Execute queries with replayable provenance using the ``.provenance()`` method:

.. code-block:: python

    from py3plex.dsl import Q
    
    # Execute with replayable provenance
    result = (
        Q.nodes()
         .provenance(mode="replayable", capture="auto", seed=42)
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )
    
    # Check if replayable
    print(result.is_replayable)  # True
    
    # Replay to reproduce results
    result2 = result.replay(strict=False)
    assert result.count == result2.count

Provenance Modes
~~~~~~~~~~~~~~~~

- **log** (default): Lightweight metadata tracking for development
- **replayable**: Full provenance with network snapshot and AST serialization

Capture Methods
~~~~~~~~~~~~~~~

- **auto**: Automatically decide based on network size (recommended)
- **fingerprint**: Only capture metadata (for very large networks)
- **snapshot**: Always capture full network state
- **delta**: Capture changes from base (future feature)

.. code-block:: python

    # Auto-capture (recommended)
    result = Q.nodes().provenance(mode="replayable", capture="auto", seed=42).execute(network)
    
    # Force snapshot for complete replay
    result = Q.nodes().provenance(mode="replayable", capture="snapshot").execute(network)
    
    # Fingerprint only (lightweight)
    result = Q.nodes().provenance(mode="log", capture="fingerprint").execute(network)

Convenience Method: reproducible()
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For simpler syntax, use the ``.reproducible()`` method:

.. code-block:: python

    # Equivalent to .provenance(mode="replayable", capture="auto", seed=42)
    result = (
        Q.nodes()
         .reproducible(True, seed=42)
         .compute("degree")
         .execute(network)
    )
    
    # Disable reproducibility
    result = Q.nodes().reproducible(False).compute("degree").execute(network)

Bundle Export and Import
~~~~~~~~~~~~~~~~~~~~~~~~~

Export results with provenance as portable bundles:

.. code-block:: python

    from py3plex.provenance import replay_from_bundle
    
    # Export bundle (compressed JSON)
    result.export_bundle("result.json.gz", compress=True)
    
    # Load and replay from bundle
    result2 = replay_from_bundle("result.json.gz", strict=False)
    
    # Or load without replaying
    from py3plex.provenance import load_bundle
    bundle = load_bundle("result.json.gz")
    prov = bundle["provenance"]

Deterministic Replay with Uncertainty
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Replayable provenance works seamlessly with uncertainty quantification:

.. code-block:: python

    # Original query
    result1 = (
        Q.nodes()
         .reproducible(True, seed=42)
         .uq(method="bootstrap", n_samples=100)
         .compute("betweenness_centrality")
         .execute(network)
    )
    
    # Replay produces identical confidence intervals
    result2 = result1.replay()
    
    # Verify deterministic reproduction
    for node in result1.items:
        stats1 = result1.attributes['betweenness_centrality'][node]
        stats2 = result2.attributes['betweenness_centrality'][node]
        assert stats1['mean'] == stats2['mean']

Accessing Provenance
~~~~~~~~~~~~~~~~~~~~~

Query results include structured provenance metadata:

.. code-block:: python

    # Access provenance
    prov = result.provenance
    
    # Schema information
    print(prov['schema_version'])  # "1.0"
    print(prov['mode'])  # "replayable"
    
    # Query information
    print(prov['query']['engine'])  # "dsl_v2_executor"
    print(prov['query']['ast_summary'])  # Human-readable summary
    
    # Network snapshot
    nc = prov['network_capture']
    print(nc['node_count'], nc['edge_count'])
    print(nc['capture_method'])  # "snapshot_graph"
    
    # Randomness configuration
    if prov['randomness']['used']:
        print(prov['randomness']['base_seed'])
    
    # Performance timing
    for stage, time_ms in prov['performance'].items():
        print(f"{stage}: {time_ms:.2f}ms")

Size Guardrails
~~~~~~~~~~~~~~~

Provenance respects size limits to avoid memory issues:

- Networks ≤10,000 nodes and ≤50,000 edges: inline snapshot
- Larger networks: fingerprint only (unless explicitly set to snapshot)
- Configurable via ``max_bytes`` parameter

.. code-block:: python

    # Custom size limits
    result = (
        Q.nodes()
         .provenance(
             mode="replayable",
             capture="auto",
             max_bytes=20*1024*1024  # 20MB limit
         )
         .execute(network)
    )

Backward Compatibility
~~~~~~~~~~~~~~~~~~~~~~

Queries without provenance configuration use log mode by default:

.. code-block:: python

    # Legacy behavior (still works)
    result = Q.nodes().compute("degree").execute(network)
    
    # Has provenance but not replayable
    assert result.provenance is not None
    assert not result.is_replayable  # False (log mode)

Best Practices
~~~~~~~~~~~~~~

**When to use replayable provenance:**

- Publishing research results (papers, reports)
- Debugging complex queries
- Archiving analysis results
- Collaborative workflows requiring verification

**When log mode is sufficient:**

- Exploratory analysis
- Development and testing
- Interactive sessions
- Performance-critical applications

.. code-block:: python

    # Research/production: enable reproducibility
    result = Q.nodes().reproducible(True, seed=42).compute("degree").execute(network)
    result.export_bundle("paper_results/network_analysis.json.gz")
    
    # Development: use default log mode
    result = Q.nodes().compute("degree").execute(network)

Limitations
~~~~~~~~~~~

- **Large Networks:** Auto-capture uses fingerprint for >10k nodes
- **Version Compatibility:** ``strict=True`` enforces exact version match
- **Non-Deterministic Operations:** Some hash-based operations may differ across Python versions

Example: Complete Reproducible Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.dsl import Q
    from py3plex.provenance import replay_from_bundle
    
    # Step 1: Execute analysis with reproducibility
    result = (
        Q.nodes()
         .reproducible(True, seed=42)
         .from_layers(L["social"])
         .where(degree__gt=3)
         .uq(method="bootstrap", n_samples=100)
         .compute("betweenness_centrality", "clustering")
         .order_by("-betweenness_centrality")
         .limit(20)
         .execute(network)
    )
    
    # Step 2: Export bundle for archival
    result.export_bundle("top_nodes_analysis.json.gz")
    
    # Step 3: Later, replay from bundle
    result2 = replay_from_bundle("top_nodes_analysis.json.gz")
    
    # Step 4: Verify deterministic reproduction
    assert result.count == result2.count
    assert result.items == result2.items

Further Reading
---------------

- :doc:`../getting_started/tutorial_10min` - Network construction basics
- :doc:`../concepts/multilayer_networks_101` - Understanding multilayer networks
- :doc:`../reference/algorithm_reference` - Network analysis algorithms
- :doc:`recipes_and_workflows` - Common analysis patterns

See Also
--------

- :doc:`graph_ops` - Dplyr-style chainable graph operations (alternative API for complex transformations)
- NetworkX documentation for centrality measures
- Examples directory for complete use cases
- API documentation for detailed function signatures

Counterexample Generation
--------------------------

Py3plex's DSL v2 includes a **counterexample generation engine** that finds violations of network invariants and provides minimal witness subgraphs.

Use Cases
~~~~~~~~~

- **Hypothesis Testing**: Verify or refute claims about network properties
- **Algorithm Debugging**: Find edge cases that violate assumptions
- **Network Understanding**: Discover counterintuitive patterns

Basic Usage
~~~~~~~~~~~

Use ``Q.counterexample()`` to find violations:

.. code-block:: python

    from py3plex.dsl import Q
    from py3plex.core import multinet
    
    # Build network
    net = multinet.multi_layer_network(directed=False)
    # ... add nodes and edges ...
    
    # Find counterexample
    cex = (Q.counterexample()
             .claim("degree__ge(k) -> pagerank__rank_le(r)")
             .params(k=10, r=50)
             .seed(42)
             .execute(net))
    
    if cex:
        print(cex.explain())
        witness = cex.subgraph

Claim Syntax
~~~~~~~~~~~~

Claims are implications in the format: ``antecedent -> consequent``

**Supported comparators**: ``gt``, ``ge``, ``gte``, ``lt``, ``le``, ``lte``, ``eq``, ``ne``

**Examples**:

.. code-block:: python

    # Value-based predicates
    "degree__ge(k) -> pagerank__gt(x)"
    "betweenness_centrality__ge(x) -> degree__ge(k)"
    
    # Rank-based predicates  
    "degree__ge(k) -> pagerank__rank_le(r)"
    "betweenness_centrality__gt(x) -> pagerank__rank_gt(r)"

Configuration Options
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    cex = (Q.counterexample()
             .claim("degree__ge(k) -> pagerank__rank_le(r)")
             .params(k=10, r=50)
             .seed(42)                          # Determinism
             .find_minimal(True)                # Minimize witness
             .budget(max_tests=200,             # Minimization budget
                    max_witness_size=500)      # Max witness nodes
             .initial_radius(2)                 # Ego subgraph radius
             .layers(L["social"] + L["work"])  # Layer selection
             .execute(net))

For more details, see the **AGENTS.md** file.

Query Algebra
-------------

**Query Algebra** enables compositional reasoning over queries and their results at the DSL level. Queries become first-class mathematical objects that can be combined using set-theoretic operators before or after execution.

.. admonition:: Why Query Algebra?
   :class: note

   Traditional network analysis requires manual post-processing to combine results from different queries. Query Algebra provides:
   
   - **Compositionality**: Build complex queries from simpler ones
   - **Multilayer semantics**: Preserve layer information during operations
   - **Uncertainty propagation**: Correctly handle UQ through algebraic operations
   - **Scientific rigor**: Explicit semantics prevent silent errors

Design Principle
~~~~~~~~~~~~~~~~

**Users should reason about network analyses algebraically, not procedurally.**

Query algebra operates at two distinct levels:

1. **Pre-compute algebra**: Logical composition of filters and scopes (queries not yet executed)
2. **Post-compute algebra**: Combining annotated results (executed queries with attributes)

Algebraic Operators
~~~~~~~~~~~~~~~~~~~

Four operators are supported for compatible queries:

.. list-table::
   :header-rows: 1
   :widths: 15 30 55

   * - Operator
     - Symbol
     - Semantics
   * - Union
     - ``q1 | q2``
     - Items in either query (set union)
   * - Intersection
     - ``q1 & q2``
     - Items in both queries (set intersection)
   * - Difference
     - ``q1 - q2``
     - Items in first query but not second (set difference)
   * - Symmetric Diff
     - ``q1 ^ q2``
     - Items in exactly one query (exclusive or)

**Compatibility Rule**: Only queries with the same target can be combined (nodes with nodes, edges with edges, etc.). Incompatible combinations raise ``IncompatibleQueryError``.

Pre-compute Algebra: Logical Composition
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pre-compute algebra combines queries **before execution**, creating a logical composition of filters and scopes.

**Example 1: Union of Layer-Filtered Queries**

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Define queries for different layers
    social_hubs = Q.nodes().from_layers(L["social"]).where(degree__gt=5)
    work_hubs = Q.nodes().from_layers(L["work"]).where(degree__gt=5)
    
    # Union: nodes that are hubs in either layer
    all_hubs = social_hubs | work_hubs
    
    # Execute the composed query
    result = all_hubs.execute(network)

**Example 2: Intersection for Multi-Criteria Filtering**

.. code-block:: python

    # Define criteria independently
    high_degree = Q.nodes().where(degree__gt=5)
    high_betweenness = Q.nodes().where(betweenness_centrality__gt=0.1)
    
    # Intersection: nodes meeting both criteria
    important_hubs = high_degree & high_betweenness
    
    result = important_hubs.execute(network)

**Example 3: Difference for Exclusion**

.. code-block:: python

    # All nodes vs. outliers
    all_nodes = Q.nodes()
    outliers = Q.nodes().where(degree__gt=10)
    
    # Normal nodes (not outliers)
    normal = all_nodes - outliers
    
    result = normal.execute(network)

Post-compute Algebra: Combining Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Post-compute algebra operates on **executed results** with computed attributes, merging both items and their associated data.

**Example 4: Union with Attribute Preservation**

.. code-block:: python

    # Execute queries independently
    social_result = Q.nodes().from_layers(L["social"]).compute("degree").execute(network)
    work_result = Q.nodes().from_layers(L["work"]).compute("degree").execute(network)
    
    # Union: combine results with attributes
    combined = social_result | work_result
    
    # Convert to DataFrame
    df = combined.to_pandas()

**Example 5: Intersection with Attribute Merging**

.. code-block:: python

    # Query with different metrics
    result1 = Q.nodes().compute("degree").execute(network)
    result2 = Q.nodes().compute("pagerank").execute(network)
    
    # Intersection merges both attributes
    merged = result1 & result2
    
    # Now each node has both degree and pagerank
    df = merged.to_pandas()
    print(df[["node", "layer", "degree", "pagerank"]])

Identity Semantics: by_id vs by_replica
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Critical**: Multilayer networks require explicit identity strategies when comparing nodes.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Strategy
     - Semantics
   * - ``by_replica``
     - Compare nodes by (node_id, layer) tuple. Default. Treats replicas as distinct.
   * - ``by_id``
     - Compare nodes by node_id only, ignoring layer. Treats replicas as same entity.

**When is identity ambiguous?**

Ambiguity exists when:

- Both results have multilayer data (multiple layers represented)
- No explicit identity strategy is specified

**Resolution**: Use ``.resolve(identity="...")`` to specify strategy explicitly.

**Example 6: Identity Strategies**

.. code-block:: python

    # Get nodes from two layers
    social = Q.nodes().from_layers(L["social"]).execute(network)
    work = Q.nodes().from_layers(L["work"]).execute(network)
    
    # BY_REPLICA: treats (Alice, social) and (Alice, work) as different
    # This will raise AmbiguousIdentityError if not specified
    try:
        union_replica = social | work
    except AmbiguousIdentityError:
        # Specify explicitly
        pass
    
    # Option 1: Treat replicas as distinct (default when unambiguous)
    from py3plex.dsl.algebra import IdentityStrategy
    social.meta['identity_strategy'] = IdentityStrategy.BY_REPLICA
    work.meta['identity_strategy'] = IdentityStrategy.BY_REPLICA
    union_replica = social | work
    # Result includes both (Alice, social) and (Alice, work)
    
    # Option 2: Treat node IDs as identical across layers
    social.meta['identity_strategy'] = IdentityStrategy.BY_ID
    work.meta['identity_strategy'] = IdentityStrategy.BY_ID
    union_id = social | work
    # Result includes Alice once (merged across layers)

**Best Practice**: Always specify identity strategy for multilayer algebra to avoid ambiguity errors.

Attribute Conflict Resolution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When combining results with computed attributes, conflicts may arise when the same item has different attribute values in each operand.

**Conflict Resolution Strategies**:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Strategy
     - Behavior
   * - ``error`` (default)
     - Raise ``AttributeConflictError`` on any conflict
   * - ``prefer_left``
     - Keep value from left operand
   * - ``prefer_right``
     - Keep value from right operand
   * - ``mean``
     - Average numeric values (works with UQ)
   * - ``max``
     - Take maximum numeric value
   * - ``min``
     - Take minimum numeric value
   * - ``keep_both``
     - Store both values with namespaced keys

**Example 7: Conflict Resolution**

.. code-block:: python

    # Two queries compute the same metric differently
    result1 = Q.nodes().compute("degree").execute(network)
    result2 = Q.nodes().compute("degree").execute(network)  # Might differ with UQ
    
    # Default: raise error on conflicts
    try:
        merged = result1 & result2
    except AttributeConflictError as e:
        print(e)
    
    # Specify resolution strategy
    result1.meta['conflict_resolution'] = ConflictResolution.MEAN
    result2.meta['conflict_resolution'] = ConflictResolution.MEAN
    merged = result1 & result2  # Averages conflicting values

Alternatively, use the ``.resolve()`` method on queries:

.. code-block:: python

    q1 = Q.nodes().compute("degree")
    q2 = Q.nodes().compute("pagerank")
    
    # Set resolution strategies before execution
    combined_query = (q1 & q2).resolve(identity="by_id", conflicts="mean")
    result = combined_query.execute(network)

Uncertainty-Aware Algebra
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Critical**: Query algebra correctly propagates uncertainty when combining results with UQ.

**UQ Propagation Rules**:

1. **Union/Intersection**: Uncertainty information from both operands is merged
2. **Methods tracked**: Records which UQ methods were used
3. **Sample sizes preserved**: Maintains n_samples metadata
4. **Seeds tracked**: If both operands used same seed, it's preserved

**Example 8: Algebra with Uncertainty**

.. code-block:: python

    # Queries with UQ
    result1 = (
        Q.nodes()
         .compute("degree")
         .uq(method="bootstrap", n_samples=100, seed=42)
         .execute(network)
    )
    
    result2 = (
        Q.nodes()
         .compute("betweenness_centrality")
         .uq(method="bootstrap", n_samples=100, seed=42)
         .execute(network)
    )
    
    # Union with UQ propagation
    combined = result1 | result2
    
    # UQ metadata is preserved
    print(combined.meta['uncertainty'])
    # {'combined': True, 'methods': ['bootstrap'], 'n_samples': [100, 100], 'seed': 42}
    
    # Export with confidence intervals
    df = combined.to_pandas(expand_uncertainty=True)
    print(df[["node", "degree_mean", "degree_ci95_low", "degree_ci95_high"]])

**Algebraic Laws Under UQ**:

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Law
     - Guaranteed
     - Notes
   * - Idempotence
     - ✓ Yes
     - ``q | q = q`` (with same seed)
   * - Commutativity
     - ✓ Yes
     - ``q1 | q2 = q2 | q1``
   * - Associativity
     - ✓ Yes
     - ``(q1 | q2) | q3 = q1 | (q2 | q3)``
   * - Distributivity
     - ✗ No
     - ``q1 & (q2 | q3) ≠ (q1 & q2) | (q1 & q3)`` when UQ differs

**Why Distributivity Fails**: UQ introduces probabilistic variation. Filtering before union vs. union before filtering can yield different confidence intervals.

Named Subqueries & Provenance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assign names to queries for better provenance tracking and debugging.

**Example 9: Named Queries**

.. code-block:: python

    # Name subqueries
    hubs = Q.nodes().where(degree__gt=5).name("hubs")
    stable = Q.nodes().uq(method="bootstrap", n_samples=100).name("stable_nodes")
    
    # Compose named queries
    robust_hubs = hubs & stable
    robust_hubs = robust_hubs.name("robust_hubs")
    
    # Execute
    result = robust_hubs.execute(network)
    
    # Names appear in provenance
    print(result.meta.get('algebra_op'))
    # {'operation': 'intersection', 'left': 'hubs', 'right': 'stable_nodes'}

Names propagate through:

- Provenance metadata (``result.meta``)
- Debug output (``result.debug()``)
- Explanations (``result.explain()``)

Verification & Assertions
~~~~~~~~~~~~~~~~~~~~~~~~~~

Query algebra enables **verification use cases** for scientific workflows.

**Assertion Methods**:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Method
     - Use Case
   * - ``Q.assert_subset(q1, q2)``
     - Verify q1 ⊆ q2 (monotonicity checks)
   * - ``Q.assert_nonempty(q)``
     - Ensure query returns results (validation)
   * - ``Q.assert_disjoint(q1, q2)``
     - Verify q1 ∩ q2 = ∅ (partitioning checks)

**Example 10: Regression Testing**

.. code-block:: python

    # Verify that filtering reduces results
    all_nodes = Q.nodes()
    filtered = Q.nodes().where(degree__gt=5)
    
    # Monotonicity assertion
    Q.assert_subset(filtered, all_nodes, network)
    # Raises AssertionError if violated

**Example 11: Intersection Validation**

.. code-block:: python

    # Ensure intersection is meaningful
    social = Q.nodes().from_layers(L["social"])
    high_degree = Q.nodes().where(degree__gt=5)
    
    intersection = social & high_degree
    
    # Verify intersection is non-empty
    Q.assert_nonempty(intersection, network, 
                      message="No high-degree nodes in social layer")

**Example 12: Partitioning Validation**

.. code-block:: python

    # Verify layer filters are exclusive
    social = Q.nodes().from_layers(L["social"])
    work = Q.nodes().from_layers(L["work"])
    
    # By replica, these should be disjoint
    Q.assert_disjoint(social, work, network, identity="by_replica")

Use Cases
~~~~~~~~~

**Scientific Claims Validation**:

.. code-block:: python

    # Claim: "High-degree nodes are always high-betweenness"
    high_degree = Q.nodes().where(degree__gt=10)
    high_betweenness = Q.nodes().where(betweenness_centrality__gt=0.2)
    
    # Test subset relationship
    try:
        Q.assert_subset(high_degree, high_betweenness, network)
        print("Claim holds")
    except AssertionError:
        print("Counterexample found")

**Monotonicity Testing**:

.. code-block:: python

    # More restrictive filter should yield subset
    filter1 = Q.nodes().where(degree__gt=5)
    filter2 = Q.nodes().where(degree__gt=10)
    
    # filter2 should be subset of filter1
    Q.assert_subset(filter2, filter1, network)

**Coverage Analysis**:

.. code-block:: python

    # Check how much overlap exists between layers
    social = Q.nodes().from_layers(L["social"]).execute(network)
    work = Q.nodes().from_layers(L["work"]).execute(network)
    
    # By ID: how many physical nodes appear in both?
    from py3plex.dsl.algebra import IdentityStrategy
    social.meta['identity_strategy'] = IdentityStrategy.BY_ID
    work.meta['identity_strategy'] = IdentityStrategy.BY_ID
    
    overlap = social & work
    print(f"Overlap: {len(overlap.items)} / {len(social.items)}")

Failure Cases & Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Query algebra fails explicitly and informatively when operations are invalid.

**Error 1: Incompatible Targets**

.. code-block:: python

    nodes_query = Q.nodes()
    edges_query = Q.edges()
    
    try:
        combined = nodes_query | edges_query
    except IncompatibleQueryError as e:
        print(e)
        # "Cannot combine queries with different targets: nodes vs edges"

**Error 2: Ambiguous Identity**

.. code-block:: python

    social = Q.nodes().from_layers(L["social"]).execute(network)
    work = Q.nodes().from_layers(L["work"]).execute(network)
    
    try:
        union = social | work
    except AmbiguousIdentityError as e:
        print(e)
        # "Identity strategy is ambiguous for multilayer results. 
        #  Specify explicitly: result.resolve(identity='by_id') or ..."

**Error 3: Attribute Conflicts**

.. code-block:: python

    result1 = Q.nodes().compute("custom_metric").execute(network)
    result2 = Q.nodes().compute("custom_metric").execute(network)
    
    try:
        merged = result1 & result2
    except AttributeConflictError as e:
        print(e)
        # "Attribute conflict for 'custom_metric': 5.2 vs 4.8. 
        #  Use .resolve(conflicts=...) to specify resolution strategy."

**Best Practices**:

1. **Always specify identity strategy** for multilayer algebra
2. **Use named queries** for complex compositions
3. **Set conflict resolution** when merging computed attributes
4. **Leverage assertions** for validation in scientific workflows
5. **Check provenance** to understand how results were combined

Algebraic Laws & Guarantees
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Guaranteed Laws** (always hold):

- **Idempotence**: ``q | q = q``, ``q & q = q``
- **Commutativity**: ``q1 | q2 = q2 | q1``, ``q1 & q2 = q2 & q1``
- **Associativity**: ``(q1 | q2) | q3 = q1 | (q2 | q3)``
- **Identity**: ``q | ∅ = q``, ``q & U = q`` (where U is universal set)
- **Annihilation**: ``q & ∅ = ∅``

**Conditional Laws** (hold under specific conditions):

- **Distributivity**: ``q1 & (q2 | q3) = (q1 & q2) | (q1 & q3)`` 
  
  - ✓ Holds for deterministic queries
  - ✗ May not hold with UQ due to probabilistic variation

**Explicitly Unsupported**:

- **Complement**: ``~q`` is not supported (requires universe definition)
- **De Morgan's Laws**: Cannot be verified without complement
- **Absorption**: ``q1 | (q1 & q2) = q1`` not guaranteed with different provenance

Summary
~~~~~~~

Query Algebra provides:

- **Compositionality**: Build complex queries from simple building blocks
- **Type safety**: Only compatible queries can combine
- **Explicit semantics**: No silent ambiguity resolution
- **Multilayer native**: Proper handling of node replicas and layers
- **Uncertainty aware**: Correct UQ propagation through operations
- **Verification support**: Assertions for scientific validation

For more examples, see:

- ``examples/dsl_query_zoo/query_algebra_basic.py``
- ``examples/dsl_query_zoo/query_algebra_uncertainty.py``
- ``examples/dsl_query_zoo/query_algebra_verification.py``

Semiring Algebra (S builder)
-----------------------------

**Definition (Semiring).**
A semiring is a tuple (K, ⊕, ⊗, 0, 1) where K is a set and ⊕, ⊗ are binary operations on K such that:

1) (K, ⊕, 0) is a commutative monoid: ⊕ is associative and commutative, and 0 is the identity (a ⊕ 0 = a).
2) (K, ⊗, 1) is a monoid: ⊗ is associative and 1 is the identity (a ⊗ 1 = 1 ⊗ a = a).
3) ⊗ distributes over ⊕: a ⊗ (b ⊕ c) = (a ⊗ b) ⊕ (a ⊗ c), and (b ⊕ c) ⊗ a = (b ⊗ a) ⊕ (c ⊗ a).
4) 0 is absorbing for ⊗: 0 ⊗ a = a ⊗ 0 = 0.

**Note**: Some useful semirings relax commutativity of ⊕; therefore this library supports both "strict semiring" and "relaxed semiring" modes via flags.

**Definition (Lift).**
Given an edge e, lift : Edge → K maps edge attributes (weight, layer, time, etc.) into semiring space.

**Definition (Path algebra).**
For a walk w = (e1, e2, ..., ek), its semiring weight is:
W(w) = lift(e1) ⊗ lift(e2) ⊗ ... ⊗ lift(ek).
For two alternative walks w and w', the combined value is W(w) ⊕ W(w').

**Definition (Closure).**
Given semiring adjacency A (where A[u,v] aggregates all edges u→v via ⊕), the closure is:
A* = I ⊕ A ⊕ A^2 ⊕ A^3 ⊕ ...
where I has I[u,u]=1 and I[u,v]=0 for u≠v, and multiplication/addition are semiring matrix ops.

Overview
~~~~~~~~

The **S builder** provides semiring-based path and closure computations for multilayer networks. Semirings generalize shortest paths, reachability, reliability, and multiobjective optimization into a unified algebraic framework.

Built-in Semirings
~~~~~~~~~~~~~~~~~~

- **min_plus**: Shortest paths (tropical semiring)
- **boolean**: Reachability
- **max_times**: Most reliable paths (probability products)
- **tropical_lex**: Lexicographic optimization (cost, then layer switches)

Example 1: Min-Plus Shortest Paths
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compute shortest paths using the min-plus (tropical) semiring:

.. code-block:: python

    from py3plex.dsl import S, L
    from py3plex.core import multinet
    
    # Create network
    net = multinet.multi_layer_network(directed=False)
    net.add_nodes([
        {'source': 'A', 'type': 'transport'},
        {'source': 'B', 'type': 'transport'},
        {'source': 'C', 'type': 'transport'},
    ])
    net.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'transport', 
         'target_type': 'transport', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'transport', 
         'target_type': 'transport', 'weight': 2.0},
    ])
    
    # Compute shortest paths from A
    result = (
        S.paths()
         .from_node('A')
         .semiring('min_plus')
         .lift(attr='weight', default=1.0)
         .from_layers(L['transport'])
         .witness(True)  # Request path witnesses
         .execute(net)
    )
    
    # Access results
    for item in result.items:
        print(f"{item['node']}: distance={item['value']}, path={item['path']}")

Example 2: Boolean Reachability
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check which nodes are reachable from a source:

.. code-block:: python

    from py3plex.dsl import S, L
    
    # Compute reachability from A using boolean semiring
    result = (
        S.paths()
         .from_node('A')
         .semiring('boolean')
         .lift(attr=None, default=True)  # All edges contribute True
         .from_layers(L['social'])
         .execute(net)
    )
    
    # Check reachability
    for item in result.items:
        node = item['node']
        reachable = item['value']
        print(f"{node}: {'reachable' if reachable else 'unreachable'}")

Example 3: Tropical Lexicographic (Layer-Switch Counting)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Optimize for both path cost and number of layer switches:

.. code-block:: python

    from py3plex.dsl import S
    
    # Use tropical_lex for multiobjective optimization
    # Minimizes (cost, layer_switches) lexicographically
    result = (
        S.paths()
         .from_node('A')
         .to_node('C')
         .semiring('tropical_lex')
         .lift(attr='weight', default=1.0)
         .crossing_layers(mode='penalize')  # Count layer switches
         .execute(net)
    )
    
    # Result: (cost, switches) tuple
    for item in result.items:
        cost, switches = item['value']
        print(f"{item['node']}: cost={cost}, switches={switches}")

S Builder API Reference
~~~~~~~~~~~~~~~~~~~~~~~

**Path queries**:

.. code-block:: python

    S.paths()
      .from_node(source)           # Required: source node
      .to_node(target)              # Optional: target node (all if omitted)
      .semiring(name)               # Semiring name or spec
      .lift(attr="weight", default=1.0)  # Edge attribute extraction
      .from_layers(L[...])          # Layer filter
      .max_hops(n)                  # Maximum path length
      .witness(True)                # Request path witnesses
      .algorithm("auto"|"dijkstra"|"bellman_ford")
      .execute(network)

**Closure queries**:

.. code-block:: python

    S.closure()
      .semiring(name)
      .lift(attr="weight", default=1.0)
      .from_layers(L[...])
      .max_hops(n)
      .execute(network)

Custom Semirings
~~~~~~~~~~~~~~~~

Define custom semirings using ``SemiringSpec``:

.. code-block:: python

    from py3plex.semiring import SemiringSpec, register_semiring
    import math
    
    # Define custom semiring
    custom = SemiringSpec(
        name="my_semiring",
        zero=math.inf,
        one=0.0,
        plus=lambda a, b: min(a, b),
        times=lambda a, b: a + b,
        strict=True,
        is_idempotent_plus=True,
        examples=(0.0, 1.0, 2.0, math.inf),
    )
    
    # Register for use
    register_semiring(custom, overwrite=True)
    
    # Use in queries
    result = S.paths().from_node('A').semiring('my_semiring').execute(net)

Provenance and Metadata
~~~~~~~~~~~~~~~~~~~~~~~~

Semiring queries include detailed provenance:

.. code-block:: python

    result = S.paths().from_node('A').semiring('min_plus').execute(net)
    
    # Access provenance
    prov = result.meta['provenance']
    print(f"Semiring: {prov['algebra']['semiring']['name']}")
    print(f"Algorithm: {prov['algorithm']}")
    print(f"Iterations: {prov['relaxations']}")
    print(f"Time: {prov['performance']['total_ms']}ms")

Algorithm Selection
~~~~~~~~~~~~~~~~~~~

The ``algorithm`` parameter controls path-finding strategy:

- **"auto"** (default): Automatically selects based on semiring properties
  
  - Uses Dijkstra for min_plus or idempotent semirings with ordering
  - Falls back to Bellman-Ford otherwise

- **"dijkstra"**: Efficient for monotone, ordered semirings (e.g., min_plus, max_times)

- **"bellman_ford"**: General-purpose relaxation, works for all semirings

max_hops Parameter
~~~~~~~~~~~~~~~~~~

**Important**: Non-idempotent semirings without ordering **require** explicit ``max_hops``:

.. code-block:: python

    # Non-idempotent semiring without leq ordering
    result = (
        S.paths()
         .from_node('A')
         .semiring('my_custom_semiring')
         .max_hops(10)  # REQUIRED for termination guarantee
         .execute(net)
    )

If ``max_hops`` is omitted for such semirings, a warning is issued and a safe default is used.

See also:

- ``examples/network_analysis/semiring_paths.py`` - Min-plus shortest paths
- ``examples/network_analysis/semiring_boolean.py`` - Boolean reachability
- ``examples/network_analysis/semiring_tropical_lex.py`` - Multiobjective optimization
- ``examples/network_analysis/semiring_pareto.py`` - Pareto frontier example

Cross-Network Meta-Analysis
============================

Overview
--------

The **M (Meta-analysis)** builder enables statistical pooling of network statistics across multiple networks using fixed-effect and random-effects models. This is useful for:

- **Comparing networks across conditions**: Pool effects from control vs treatment networks
- **Multi-study synthesis**: Combine results from multiple network studies
- **Robustness analysis**: Test if findings generalize across different network samples
- **Node-level pooling**: Meta-analyze node-level statistics (e.g., PageRank across shared genes)

Meta-analysis is not visualization sugar—it's statistical infrastructure with full provenance tracking and determinism guarantees.

Basic Usage
-----------

**Network-Level Meta-Analysis:**

.. code-block:: python

    from py3plex.dsl import Q, M
    
    # Compute average degree across three networks
    meta = (
        M.meta("avg_degree_meta")
         .on_networks({"net1": net1, "net2": net2, "net3": net3})
         .run(
             Q.nodes().compute("degree").summarize(avg_degree="mean(degree)"),
             effect="avg_degree",
         )
         .model("random")  # Default is random-effects
         .execute()
    )
    
    # Access results
    df = meta.to_pandas()
    print(f"Pooled effect: {df['pooled_effect'].iloc[0]:.3f}")
    print(f"I² heterogeneity: {df['I2'].iloc[0]:.1f}%")

Statistical Models
------------------

**Fixed-Effect Model** (Inverse Variance Weighting):

Uses inverse variance weighting where studies with lower standard errors receive more weight:

.. math::

    w_i = \frac{1}{se_i^2}
    
    \text{pooled\_effect} = \frac{\sum(w_i \cdot y_i)}{\sum(w_i)}
    
    \text{pooled\_se} = \sqrt{\frac{1}{\sum(w_i)}}

**Random-Effects Model** (DerSimonian-Laird):

Accounts for between-study heterogeneity by estimating τ² (tau-squared):

.. math::

    Q = \sum w_i (y_i - \mu_{\text{fixed}})^2
    
    \tau^2 = \max\left(0, \frac{Q - df}{C}\right)
    
    w_i^* = \frac{1}{se_i^2 + \tau^2}

Where C = Σ(w_i) - Σ(w_i²) / Σ(w_i).

**Heterogeneity Metrics**:

- **Q**: Cochran's Q statistic (tests for heterogeneity)
- **τ²**: Between-study variance
- **I²**: Percentage of variation due to heterogeneity (0-100%)
- **H**: Ratio of observed to expected variation

Node-Level Pooling
-------------------

Pool node-level statistics across networks with shared node IDs:

.. code-block:: python

    from py3plex.dsl import Q, M, UQ
    
    # Pool PageRank for genes across treatment conditions
    meta = (
        M.meta("pagerank_gene_meta")
         .on_networks({"ctrl": netA, "trt1": netB, "trt2": netC})
         .run(
             Q.nodes()
              .node_type("gene")
              .uq(UQ.standard(seed=42))  # UQ provides SE
              .compute("pagerank")
              .select("node", "pagerank", "pagerank_std"),
             effect="pagerank",
             se="pagerank_std",
             group_by=["node"],  # Pool per gene
         )
         .model("fixed")
         .execute()
    )
    
    # Results: one pooled effect per gene

Effect and SE Resolution
-------------------------

**Effect Extraction Rules**:

1. If query returns >1 row and ``group_by`` not provided → ERROR
2. If ``group_by`` provided: pooling is independent per group
3. If query returns exactly 1 row: ``group_by`` is ignored

**SE Resolution Priority** (STRICT ORDER):

1. Explicit ``se="column_name"`` if column exists
2. Expression ``se="se(effect_col)"`` if variance available
3. Auto-infer from ``.uq()`` if UQ was used (uses ``effect_std``)
4. ERROR unless ``.allow_unweighted(True)`` is set

**Unweighted Pooling** (explicit opt-in only):

.. code-block:: python

    meta = (
        M.meta()
         .on_networks(networks)
         .run(query, effect="metric")
         .allow_unweighted(True)  # Enables sample mean + SD
         .execute()
    )
    
    # Uses: pooled_mean = arithmetic mean, SE = sample SD / sqrt(k)

Subgroup Meta-Analysis
-----------------------

Partition networks by metadata and pool per subgroup:

.. code-block:: python

    meta = (
        M.meta()
         .on_networks({"a": net1, "b": net2, "c": net3})
         .with_network_meta({
             "a": {"condition": "ctrl"},
             "b": {"condition": "trt"},
             "c": {"condition": "trt"},
         })
         .run(
             Q.nodes().compute("degree").summarize(avg_degree="mean(degree)"),
             effect="avg_degree",
         )
         .subgroup(by="condition")  # Partition by condition
         .model("random")
         .execute()
    )
    
    # Results include both per-subgroup and overall pooled effects

Meta-Regression
---------------

**Constrained v1 Scope**: Network-level effects only, numeric covariates only.

.. code-block:: python

    # Regress network-level effects on network characteristics
    meta = (
        M.meta()
         .on_networks(nets)
         .with_network_meta({
             "net1": {"node_count": 100, "edge_count": 450},
             "net2": {"node_count": 150, "edge_count": 680},
             # ...
         })
         .run(
             Q.nodes().compute("degree").summarize(avg_degree="mean(degree)"),
             effect="avg_degree",
         )
         .meta_regress(formula="avg_degree ~ node_count + edge_count")
         .model("random")
         .execute()
    )
    
    # Coefficients in meta.meta_provenance["meta_regression"]["coefficients"]

**Limitations**:

- Network-level effects only (no ``group_by``)
- Numeric covariates only
- No interactions (raise ``NotImplementedError``)
- Categorical variables must be pre-encoded

Provenance and Determinism
---------------------------

**Provenance Aggregation**:

Meta-analysis aggregates provenance from all networks:

.. code-block:: python

    result = meta.execute()
    prov = result.meta_provenance
    
    # Contains:
    # - Per-network provenance (query AST hash, randomness, performance)
    # - Meta-model type and parameters
    # - Network fingerprints (node/edge/layer counts)
    # - Warnings and diagnostics

**Determinism Guarantees**:

- Same networks + same query + same seeds → identical results
- Network order is stable (sorted by key unless ``.preserve_order(True)``)
- Explicit query seeds are always honored
- Meta-level ``.seed()`` fills missing seeds only

**Example**:

.. code-block:: python

    # Deterministic meta-analysis
    meta1 = (
        M.meta()
         .on_networks(nets)
         .run(Q.nodes().uq(seed=42).compute("pagerank"), effect="pagerank", se="pagerank_std")
         .seed(42)  # Fills missing seeds only
         .execute()
    )
    
    meta2 = (/* same config */).execute()
    
    # meta1 and meta2 produce identical results

Error Handling
--------------

All meta-analysis errors use ``MetaAnalysisError`` with actionable hints:

.. code-block:: python

    from py3plex.exceptions import MetaAnalysisError
    
    try:
        meta = M.meta().on_networks(nets).run(query, effect="missing_col").execute()
    except MetaAnalysisError as e:
        print(e)  # "Effect column 'missing_col' not found in query results"
        print(e.hint)  # "Available columns: node, degree, betweenness"

**Common Errors**:

- Missing effect column
- Missing SE without ``.allow_unweighted(True)``
- ``group_by`` mismatch across networks
- Missing network metadata for subgroup/regression

Edge Cases
----------

**k=1 (Single Network)**:

.. code-block:: python

    # Single network: no pooling needed
    meta = M.meta().on_networks({"net1": net1}).run(query, effect="metric").execute()
    
    # Results: pooled_effect = y₁, pooled_se = se₁, τ² = NaN, Q = NaN, I² = NaN

**All Effects Equal** (No Heterogeneity):

.. code-block:: python

    # If all y_i are identical:
    # τ² = 0, I² = 0, pooled_effect = y_i (exact)

**Numerical Stability**:

- C ≤ 0 in DL estimation → τ² = 0 with provenance warning
- Q ≤ df → I² = 0 (no heterogeneity)
- All divisions are guarded against overflow/underflow

See Also
--------

- AGENTS.md section 3.11 for complete M builder specification
- ``tests/test_meta_analysis.py`` for comprehensive test examples
- ``py3plex/meta/`` module for implementation details


Query Canonicalization and Equivalence
=======================================

py3plex DSL v2 includes a built-in **query equivalence engine** that lets you test whether
two queries are semantically equivalent, normalize queries to a canonical form, and obtain
a stable hash for equivalent queries.

These features are implemented directly on the ``QueryBuilder`` object returned by
``Q.nodes()``, ``Q.edges()``, etc.

Scopes
------

Two scopes control what counts as equivalent:

- **``"relational"``** (default): Standard relational-algebra equivalence.
  ``order_by`` is considered **semantic** in py3plex (it affects result ordering),
  so two queries that differ only in ordering direction are **not** equivalent under
  this scope either.  Use ``"relational"`` for most comparisons.
- **``"strict"``**: Same as relational, but additionally deduplicates repeated
  ``order_by`` items (R8).  Two queries that merely have a duplicate sort key are
  considered equivalent in strict scope.

``Query.canonical(scope="relational")``
----------------------------------------

Returns a new ``QueryBuilder`` whose internal AST is in canonical normal form.
Canonicalization is **deterministic** and **idempotent**::

    q = Q.nodes().where(layer="social", degree__gt=5)
    c1 = q.canonical()
    c2 = c1.canonical()
    assert c1.canonical_ast_hash == c2.canonical_ast_hash   # idempotent

Canonical form rules applied:

- **R1/R2** — consecutive/duplicate ``where`` predicates are merged into a single
  AND-condition.
- **R3** — AND/OR predicate trees are flattened and sorted by a deterministic key.
- **R5** — consecutive ``from_layers`` calls are intersected into a single filter.
- **R8** (strict scope only) — duplicate ``order_by`` items are removed.
- **R9** — stacked ``limit`` calls are reduced to ``min(n, m)``.

``Query.equivalent_to(other, scope="relational", explain=False)``
-----------------------------------------------------------------

Returns ``True`` if two queries are semantically equivalent under the given scope::

    q1 = Q.nodes().where(degree__gt=5).where(layer="social")
    q2 = Q.nodes().where(layer="social", degree__gt=5)
    assert q1.equivalent_to(q2)   # True — merged AND with sorted terms

Pass ``explain=True`` to receive a ``(bool, proof)`` tuple, where ``proof`` is a
dictionary with keys ``"self_proof"``, ``"other_proof"`` (lists of rule names
applied during canonicalization), and ``"diff"`` (first differing path, if any)::

    eq, proof = q1.equivalent_to(q2, explain=True)
    # proof["self_proof"]  → ["R2:where_idempotence", "R3:predicate_normalization"]
    # proof["other_proof"] → ["R3:predicate_normalization"]
    # Rule name prefix reference: see AGENTS.md § "Query Algebra, Canonicalization, Equivalence".

``Query.canonical_ast_hash``
-----------------------------

A stable, run-independent hexadecimal SHA-256 hash of the canonical AST.
Equivalent queries always share the same hash; non-equivalent queries produce
different hashes::

    q1 = Q.nodes().where(degree__gt=5, layer="social")
    q2 = Q.nodes().where(layer="social").where(degree__gt=5)
    assert q1.canonical_ast_hash == q2.canonical_ast_hash

    q3 = Q.nodes().where(degree__gt=10)   # different threshold
    assert q1.canonical_ast_hash != q3.canonical_ast_hash

The hash is computed from ``Query.canonical(scope="relational")`` and is **not**
the same as the existing ``Query.ast_hash`` (which operates on the raw, un-normalised
AST).

Algebraic Optimization (internal)
----------------------------------

The equivalence engine is built on top of the existing ``canonicalize_ast``
machinery in ``py3plex/dsl/ast.py``.  The new scope-aware entry point
``canonicalize_ast_scoped(query_ast, scope)`` extends that function and returns
a ``(canonical_query_ast, proof_list)`` pair.  Application developers who need
to extend the rule set should add new rules inside
``_canonicalize_select_stmt_scoped`` in ``ast.py``.

See Also
--------

- ``tests/test_query_equivalence.py`` — full test suite covering all rules and scopes.
- AGENTS.md §"Query Algebra, Canonicalization, Equivalence" for the formal specification.
