.. _dsl-chapter:

Introduction to the Py3plex DSL
==========================================

This chapter introduces the py3plex Domain-Specific Language (DSL), a SQL-like query language for expressing multilayer network analyses concisely. The DSL is a **major first-class feature** that sets py3plex apart from other network libraries.

.. admonition:: DSL at a Glance
   :class: dsl-example

   The DSL provides intuitive SQL-like syntax for network queries:

   .. code-block:: python

       from py3plex.dsl import Q, L

       # Simple: Find high-degree nodes
       result = Q.nodes().where(degree__gt=5).execute(network)

       # Powerful: Multilayer analysis with export
       result = (
           Q.nodes()
            .from_layers(L["social"] + L["work"])
            .where(degree__gt=3)
            .compute("betweenness_centrality", "pagerank")
            .order_by("-betweenness_centrality")
            .limit(20)
            .export_csv("top_influencers.csv")
            .execute(network)
       )

   Express complex analyses in a few readable lines!

Why a DSL for Networks?
-----------------------

Traditional network analysis requires writing explicit loops and conditionals:

.. code-block:: python

    # Traditional approach: verbose and error-prone
    high_degree_nodes = []
    for node in network.get_nodes():
        if node[1] == 'social':  # Check layer
            degree = network.core_network.degree(node)
            if degree > 5:
                high_degree_nodes.append(node)
    
    # Compute centrality for filtered nodes
    G = network.core_network  # NetworkX graph
    centralities = nx.betweenness_centrality(G)
    filtered_centralities = {node: centralities[node] for node in high_degree_nodes}

The DSL provides a declarative alternative:

.. code-block:: python

    # DSL approach: clear and concise
    from py3plex.dsl import execute_query
    
    result = execute_query(network,
        'SELECT nodes WHERE layer="social" AND degree > 5 '
        'COMPUTE betweenness_centrality'
    )

**Benefits:**

1. **Declarative** — State *what* you want, not *how* to get it
2. **Readable** — SQL-like syntax is familiar and self-documenting
3. **Composable** — Build complex queries from simple building blocks
4. **Maintainable** — Less code means fewer bugs

DSL Versions
------------

Py3plex provides two DSL interfaces:

**String DSL (v1)**
  SQL-like queries as strings. Good for simple queries and REPL exploration.

.. code-block:: python

    result = execute_query(network, 'SELECT nodes WHERE degree > 5')

**Builder API (v2, recommended)**
  Python-native chainable API with type hints and autocompletion.

.. code-block:: python

    from py3plex.dsl import Q, L
    
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .where(degree__gt=5)
         .execute(network)
    )

This chapter focuses on the **Builder API (v2)** as it provides a better development experience. The string DSL is covered briefly for reference.

Which Interface When? — The Decision Guide
-------------------------------------------

Py3plex provides **four primary interfaces** for network analysis. This opinionated guide helps you choose the right one for your task.

.. list-table:: Interface Decision Matrix
   :header-rows: 1
   :widths: 20 20 30 30

   * - **Interface**
     - **Best For**
     - **Use When...**
     - **Avoid When...**
   * - **DSL v2 (Q, L, UQ)**
     - Exploratory analysis, research notebooks, reproducible workflows
     - • Complex multilayer queries
       
       • Need uncertainty quantification
       
       • Want provenance tracking
       
       • Building reusable query pipelines
     - • Simple NetworkX operations suffice
       
       • Performance-critical loops
       
       • Non-multilayer graphs
   * - **graph_ops (dplyr)**
     - Data frame–style manipulation, interactive exploration
     - • Familiar with R's dplyr
       
       • Need data frame output
       
       • Iterative filtering/mutation
       
       • Working with node/edge attributes
     - • Need multilayer layer algebra
       
       • Want uncertainty analysis
       
       • Building production pipelines
   * - **Pipeline API**
     - Production workflows, benchmarking, ML integration
     - • Sklearn-style fit/transform needed
       
       • Batch processing networks
       
       • Comparing algorithms
       
       • Building reproducible experiments
     - • One-off analyses
       
       • Interactive exploration
       
       • Complex query logic
   * - **CLI Tool**
     - Quick analysis, scripting, CI/CD, non-Python users
     - • No Python coding needed
       
       • Shell script integration
       
       • Quick statistics/visualization
       
       • Testing network files
     - • Complex custom logic
       
       • Interactive workflows
       
       • Advanced UQ/provenance

**Typical User Personas:**

* **Research Scientist**: DSL v2 → reproducible queries with UQ and provenance
* **Data Analyst**: graph_ops → familiar dplyr-style data manipulation
* **ML Engineer**: Pipeline API → sklearn-compatible workflows
* **DevOps/Analyst**: CLI → quick stats and visualization in scripts

**Decision Heuristics:**

1. **Start with DSL v2 (Q)** if working with multilayer networks and need any of:
   
   - Layer filtering (``L["social"] + L["work"]``)
   - Uncertainty quantification (``uq()``)
   - Grouping (``per_layer()``, ``per_layer_pair()``)
   - Provenance tracking

2. **Use graph_ops** if:
   
   - Your workflow is "select → filter → mutate → export to CSV"
   - You're comfortable with dplyr and want similar ergonomics
   - You don't need multilayer-specific operations

3. **Use Pipeline API** if:
   
   - You're building sklearn-style workflows (``fit/transform``)
   - Benchmarking multiple algorithms systematically
   - Need reproducible experiment configs

4. **Use CLI** if:
   
   - You're not writing Python code
   - Scripting quick analyses in bash/shell
   - Need to process multiple network files

**Common Anti-Patterns:**

* ❌ Using string DSL (v1) for new code → **Use DSL v2 builder API instead**
* ❌ Using DSL for simple single-layer NetworkX operations → **Use NetworkX directly**
* ❌ Using graph_ops for multilayer grouping → **Use DSL v2's per_layer() instead**
* ❌ Building custom sklearn pipelines → **Use Pipeline API's built-in steps**

**Interface Interoperability:**

All interfaces work with the same ``multi_layer_network`` objects:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dsl import Q, L
    from py3plex.graph_ops import nodes
    
    net = multinet.multi_layer_network()
    # ... load data ...
    
    # DSL v2
    result = Q.nodes().from_layers(L["social"]).execute(net)
    
    # graph_ops (on same network)
    df = nodes(net, layers=["social"]).to_pandas()
    
    # Both work on the same network object

Basic Query Structure
---------------------

A typical DSL query has four parts:

1. **Target** — What to select (nodes or edges)
2. **Layer filtering** — Which layers to include (optional)
3. **Conditions** — Filter criteria (optional)
4. **Measures** — What to compute (optional)

Example:

.. code-block:: python

    from py3plex.dsl import Q, L
    
    result = (
        Q.nodes()                        # 1. Select nodes
         .from_layers(L["social"])       # 2. Filter to social layer
         .where(degree__gt=5)            # 3. Filter by degree > 5
         .compute("betweenness_centrality")  # 4. Compute centrality
         .execute(network)               # Execute query
    )

Your First Query
----------------

Let's build a simple query step-by-step. See the complete examples in ``examples/network_analysis/`` and ``examples/dsl_query_zoo/``.

**Example 1: Filter by layer**

.. code-block:: python

    from py3plex.dsl import Q, L
    from py3plex.core import multinet
    
    # Create a simple multilayer network
    net = multinet.multi_layer_network()
    net.add_nodes([
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'work'},
    ])
    net.add_edges([
        {'source': 'Alice', 'target': 'Bob', 
         'source_type': 'social', 'target_type': 'social'},
        {'source': 'Charlie', 'target': 'Alice', 
         'source_type': 'work', 'target_type': 'work'},
    ])
    
    # Select nodes from the social layer
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .execute(net)
    )
    
    print(result.to_pandas())

**Run complete DSL examples:**

.. code-block:: bash

    # Basic DSL builder API
    python examples/network_analysis/example_dsl_builder_api.py
    
    # Advanced DSL features
    python examples/network_analysis/example_dsl_advanced.py
    
    # Query Zoo examples
    python examples/dsl_query_zoo/run_all.py

**Example 2: Filter by degree**

.. code-block:: python

    # Find high-degree nodes
    result = (
        Q.nodes()
         .from_layers(L["*"])  # All layers
         .compute("degree")
         .where(degree__gt=3)
         .execute(net)
    )

**Example 3: Compute centrality**

See ``examples/02_basic_queries/04_compute_centrality.py``:

.. code-block:: bash

    # Using uv
    uv run examples/02_basic_queries/04_compute_centrality.py
    
    # Or using python
    python examples/02_basic_queries/04_compute_centrality.py

Layer Filtering
---------------

The DSL provides powerful layer algebra operations. See ``examples/03_dsl_v2/02_layer_algebra.py`` for complete examples.

.. admonition:: DSL Layer Algebra
   :class: dsl-info

   Layer algebra lets you combine layers with set operations:

   .. code-block:: python

       from py3plex.dsl import Q, L

       # Union: nodes in social OR work
       Q.nodes().from_layers(L["social"] + L["work"])

       # Difference: nodes in social but NOT bots
       Q.nodes().from_layers(L["social"] - L["bots"])

       # Intersection: nodes in both social AND work
       Q.nodes().from_layers(L["social"] & L["work"])

       # Complex: (social OR work) - bots
       Q.nodes().from_layers(L["social"] + L["work"] - L["bots"])

   This makes multilayer queries intuitive and expressive!

**Run layer algebra examples:**

.. code-block:: bash

    # Using uv
    uv run examples/03_dsl_v2/02_layer_algebra.py
    
    # Or using python
    python examples/03_dsl_v2/02_layer_algebra.py

Simple Layer Selection
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Single layer
    Q.nodes().from_layers(L["social"])
    
    # Multiple layers (union)
    Q.nodes().from_layers(L["social"] + L["work"])

Layer Algebra
~~~~~~~~~~~~~

**Union** (OR):

.. code-block:: python

    # Nodes in social OR work layers
    Q.nodes().from_layers(L["social"] + L["work"])

**Difference** (NOT):

.. code-block:: python

    # Nodes in social but NOT in bots layer
    Q.nodes().from_layers(L["social"] - L["bots"])

**Intersection** (AND):

.. code-block:: python

    # Nodes present in both social AND work
    Q.nodes().from_layers(L["social"] & L["work"])

**All layers:**

.. code-block:: python

    # Don't specify from_layers() to query all layers
    Q.nodes().where(degree__gt=5)

Filtering Conditions
--------------------

The ``where()`` method accepts filtering predicates.

Degree Filters
~~~~~~~~~~~~~~

.. code-block:: python

    # Greater than
    Q.nodes().where(degree__gt=5)
    
    # Greater than or equal
    Q.nodes().where(degree__gte=3)
    
    # Less than
    Q.nodes().where(degree__lt=10)
    
    # Less than or equal
    Q.nodes().where(degree__lte=5)
    
    # Equal
    Q.nodes().where(degree=2)

Layer Filters
~~~~~~~~~~~~~

.. code-block:: python

    # Specific layer
    Q.nodes().where(layer="social")
    
    # Exclude layer
    Q.nodes().where(layer__ne="bots")

Multiple Conditions (AND)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Combine conditions
    Q.nodes().where(layer="social", degree__gt=3)
    
    # Equivalent to: layer="social" AND degree > 3

Computing Measures
------------------

The ``compute()`` method calculates network measures.

Single Measure
~~~~~~~~~~~~~~

.. code-block:: python

    result = (
        Q.nodes()
         .compute("degree")
         .execute(network)
    )
    
    # Access results
    for node, degree in result.measures['degree'].items():
        print(f"{node}: {degree}")

Multiple Measures
~~~~~~~~~~~~~~~~~

.. code-block:: python

    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality", "closeness_centrality")
         .execute(network)
    )
    
    # Access each measure
    degrees = result.measures['degree']
    betweenness = result.measures['betweenness_centrality']
    closeness = result.measures['closeness_centrality']

Available Measures
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Measure
     - Description
   * - ``degree``
     - Node degree (number of neighbors)
   * - ``degree_centrality``
     - Normalized degree centrality
   * - ``betweenness_centrality``
     - Betweenness centrality (path-based importance)
   * - ``closeness_centrality``
     - Closeness centrality (average distance to others)
   * - ``eigenvector_centrality``
     - Eigenvector centrality (importance of neighbors)
   * - ``pagerank``
     - PageRank score
   * - ``clustering``
     - Clustering coefficient

Ordering and Limiting
---------------------

Order By
~~~~~~~~

.. code-block:: python

    # Order by degree (ascending)
    Q.nodes().compute("degree").order_by("degree")
    
    # Order by degree (descending)
    Q.nodes().compute("degree").order_by("-degree")
    
    # Order by multiple keys
    Q.nodes().compute("degree").order_by("-degree", "node_id")

Limit
~~~~~

.. code-block:: python

    # Get top 10 by degree
    result = (
        Q.nodes()
         .compute("degree")
         .order_by("-degree")
         .limit(10)
         .execute(network)
    )

Working with Results
--------------------

The ``QueryResult`` object provides multiple ways to access results.

Iteration
~~~~~~~~~

.. code-block:: python

    result = Q.nodes().execute(network)
    
    for node in result:
        print(node)  # ('Alice', 'friends'), ...

Count
~~~~~

.. code-block:: python

    result = Q.nodes().where(degree__gt=5).execute(network)
    print(f"Found {result.count} nodes")

Measures
~~~~~~~~

.. code-block:: python

    result = Q.nodes().compute("degree").execute(network)
    
    # Access as dict
    degrees = result.measures['degree']
    for node, degree in degrees.items():
        print(f"{node}: {degree}")

To Pandas
~~~~~~~~~

.. code-block:: python

    # Convert to DataFrame
    df = result.to_pandas()
    print(df.head())

String DSL Syntax (Reference)
------------------------------

For completeness, here's the string DSL syntax. See ``examples/02_basic_queries/01_legacy_string_dsl.py`` for a complete example.

**Basic queries:**

.. code-block:: python

    # Select nodes
    execute_query(network, 'SELECT nodes')
    
    # Filter by layer
    execute_query(network, 'SELECT nodes WHERE layer="social"')
    
    # Filter by degree
    execute_query(network, 'SELECT nodes WHERE degree > 5')
    
    # Multiple conditions
    execute_query(network, 'SELECT nodes WHERE layer="social" AND degree > 3')
    
    # Compute measures
    execute_query(network, 'SELECT nodes COMPUTE betweenness_centrality')

**Run legacy DSL examples:**

.. code-block:: bash

    # Using uv
    uv run examples/02_basic_queries/01_legacy_string_dsl.py
    
    # Or using python
    python examples/02_basic_queries/01_legacy_string_dsl.py

**Operators:**

* ``=`` — Equal
* ``!=`` — Not equal
* ``>`` — Greater than
* ``<`` — Less than
* ``>=`` — Greater or equal
* ``<=`` — Less or equal
* ``AND`` — Logical AND
* ``OR`` — Logical OR
* ``NOT`` — Logical NOT

Example: Complete Workflow
---------------------------

Here's a complete example demonstrating DSL capabilities:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dsl import Q, L
    
    # Create network
    network = multinet.multi_layer_network()
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Bob', 'friends', 'Carol', 'friends', 1],
        ['Carol', 'friends', 'Dave', 'friends', 1],
        ['Alice', 'colleagues', 'Bob', 'colleagues', 1],
        ['Bob', 'colleagues', 'Eve', 'colleagues', 1],
        ['Eve', 'colleagues', 'Frank', 'colleagues', 1],
    ], input_type="list")
    
    # Query 1: Find high-degree nodes across all layers
    result = (
        Q.nodes()
         .where(degree__gte=2)
         .compute("degree", "betweenness_centrality")
         .order_by("-betweenness_centrality")
         .execute(network)
    )
    
    print("High-degree nodes:")
    for node in result:
        degree = result.measures['degree'][node]
        bc = result.measures['betweenness_centrality'][node]
        print(f"  {node}: degree={degree}, BC={bc:.3f}")
    
    # Query 2: Compare layers
    for layer in ['friends', 'colleagues']:
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree")
             .execute(network)
        )
        avg_degree = sum(result.measures['degree'].values()) / result.count
        print(f"{layer} layer: {result.count} nodes, avg degree={avg_degree:.2f}")

Common Patterns
---------------

Pattern 1: Filter → Compute → Order → Limit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Find top 10 central nodes in a specific layer
    top_10 = (
        Q.nodes()
         .from_layers(L["social"])
         .compute("betweenness_centrality")
         .order_by("-betweenness_centrality")
         .limit(10)
         .execute(network)
    )

Pattern 2: Layer Comparison
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Compare degree distribution across layers
    for layer_name in network.get_layers():
        result = (
            Q.nodes()
             .from_layers(L[layer_name])
             .compute("degree")
             .execute(network)
        )
        degrees = list(result.measures['degree'].values())
        print(f"{layer_name}: mean degree = {sum(degrees)/len(degrees):.2f}")

Pattern 3: Conditional Export
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Export high-degree nodes to CSV
    (
        Q.nodes()
         .where(degree__gt=5)
         .compute("degree", "betweenness_centrality")
         .order_by("-degree")
         .export_csv("high_degree_nodes.csv")
         .execute(network)
    )

Summary
-------

This chapter introduced the py3plex DSL:

1. **Motivation** — Declarative queries replace explicit loops
2. **Builder API** — Python-native with type hints (recommended)
3. **Query structure** — Target, layers, conditions, measures
4. **Layer algebra** — Union, difference, intersection operations
5. **Results** — Iteration, measures, pandas export

**Key takeaways:**

* Use **Builder API** for type safety and autocompletion
* **Chain methods** to build complex queries incrementally
* **Layer algebra** enables powerful layer filtering
* **Compute measures** in a single call instead of manual loops

The next chapter covers the EXPLAIN mode for understanding query execution and performance.

Further Reading
---------------

* The Builder API and Explain Plans (Chapter 9)
* Advanced Queries and Workflows (Chapter 10)
* ``examples/02_basic_queries/`` — Basic query examples
* ``examples/03_dsl_v2/`` — Advanced DSL v2 examples
