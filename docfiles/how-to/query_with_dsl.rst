How to Query Multilayer Graphs with the SQL-like DSL
====================================================

**Goal:** Use py3plex's SQL-inspired Domain-Specific Language (DSL) to query, filter, and analyze multilayer networks. The DSL is a **first-class query language** specifically designed for multilayer graph structures, providing both string syntax for interactive exploration and a type-safe builder API for production code.

**What Makes This DSL Special:**

* **Graph-aware**: Unlike generic query languages, the DSL understands multilayer structures—layers, layer intersections, intralayer vs. interlayer edges, and (node, layer) tuple semantics.
* **Dual interfaces**: String syntax for rapid prototyping in notebooks; builder API (``Q``, ``L``) for IDE autocompletion and type checking.
* **Integrated computation**: Compute centrality, clustering, and other network metrics directly in queries, with results returned as pandas DataFrames or NetworkX graphs.
* **Temporal support**: Query network snapshots and time ranges when your network includes temporal information.

**Prerequisites:** 

* A loaded ``multi_layer_network`` object (see :doc:`load_and_build_networks`)
* Basic familiarity with multilayer network concepts (nodes, layers, intralayer/interlayer edges)
* For complete DSL grammar and operator reference, see :doc:`../reference/dsl_reference`

Conceptual Overview
-------------------

The DSL has **two complementary interfaces** that compile to the same internal representation:

1. **String Syntax** (``execute_query(network, "SELECT nodes WHERE ...")``)
   
   * SQL-like, human-readable
   * Ideal for interactive exploration in Jupyter notebooks or the REPL
   * Quick one-liners for common queries

2. **Builder API** (``Q.nodes().where(...).compute(...).execute(network)``)
   
   * Pythonic, chainable methods
   * Type-safe with IDE autocompletion
   * Recommended for production code and complex workflows

**Mental Model:**

A typical DSL query follows this pipeline:

.. code-block:: text

    SELECT nodes/edges 
    → FROM LAYERS (restrict to specific layers)
    → WHERE (filter by attributes or special predicates)
    → COMPUTE (calculate metrics like degree, centrality)
    → ORDER BY (sort results)
    → LIMIT (cap number of results)
    → EXPORT (materialize as DataFrame, NetworkX graph, etc.)

**Key Concepts:**

* **Nodes as (node, layer) tuples**: In multilayer networks, a node may appear in multiple layers. The DSL represents these as ``(node_id, layer_name)`` pairs.
* **Layer algebra**: Combine layers with ``+`` (union), ``&`` (intersection), or ``-`` (difference).
* **Special predicates**: ``intralayer=True`` selects edges within a layer; ``interlayer=("layer1", "layer2")`` selects edges crossing specific layers.
* **Lazy execution**: Queries are built incrementally and executed only when ``.execute(network)`` is called.

**Comparison to SQL:**

Think of the DSL as SQL for graphs:

* ``SELECT nodes WHERE degree > 5`` ≈ SQL's ``SELECT * FROM nodes WHERE degree > 5``
* But instead of tables, you're querying **nodes and edges** with **multilayer and temporal attributes**
* Layer filters and graph-specific predicates (``intralayer``, ``interlayer``) have no SQL equivalent

String Syntax (Quick and Readable)
-----------------------------------

The string syntax provides a concise, SQL-like way to express queries. Best for exploratory analysis and quick investigations.

Basic SELECT
~~~~~~~~~~~~

Select all nodes and inspect the result:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dsl import execute_query
    
    network = multinet.multi_layer_network()
    network.load_network("data.multiedgelist", input_type="multiedgelist")
    
    # Get all nodes
    result = execute_query(network, 'SELECT nodes')
    
    print(f"Found {len(result)} nodes")
    # Inspect a few items
    for i, (node, data) in enumerate(result.items()):
        print(f"  {node}: {data}")
        if i >= 4:
            break

**Expected output:**

.. code-block:: text

    Found 100 nodes
      ('alice', 'social'): {'degree': 7, 'layer': 'social', 'layer_count': 2}
      ('bob', 'social'): {'degree': 5, 'layer': 'social', 'layer_count': 1}
      ('charlie', 'work'): {'degree': 3, 'layer': 'work', 'layer_count': 2}
      ('diana', 'social'): {'degree': 9, 'layer': 'social', 'layer_count': 3}
      ('eve', 'work'): {'degree': 4, 'layer': 'work', 'layer_count': 1}

**Note:** Keys are ``(node, layer)`` tuples representing node-layer pairs. The ``layer_count`` attribute indicates how many layers the node appears in across the entire network.

Filter by Layer
~~~~~~~~~~~~~~~

Restrict queries to nodes in a specific layer:

.. code-block:: python

    # Get nodes in the 'friends' layer only
    result = execute_query(
        network,
        'SELECT nodes WHERE layer="friends"'
    )
    
    print(f"Nodes in 'friends' layer: {len(result)}")

**Understanding Layer Filters:**

* ``layer="friends"`` selects only the node-layer pairs where ``layer == "friends"``
* This does **not** select all occurrences of nodes across layers—only their representation in the specified layer
* Use ``layer_count >= 2`` to find nodes appearing in multiple layers

**Example with statistics:**

.. code-block:: python

    result = execute_query(
        network,
        'SELECT nodes WHERE layer="friends" COMPUTE degree'
    )
    df = result.to_pandas()
    print(f"Nodes in 'friends': {len(df)}")
    print(f"Average degree in 'friends': {df['degree'].mean():.2f}")
    print(f"Max degree in 'friends': {df['degree'].max()}")

**Expected output:**

.. code-block:: text

    Nodes in 'friends': 42
    Average degree in 'friends': 5.23
    Max degree in 'friends': 15

Filter by Property
~~~~~~~~~~~~~~~~~~

Use comparisons to filter nodes by computed or intrinsic attributes:

.. code-block:: python

    # High-degree nodes
    result = execute_query(
        network,
        'SELECT nodes WHERE degree > 5'
    )
    print(f"High-degree nodes: {len(result)}")
    
    # Multilayer nodes with high degree
    result = execute_query(
        network,
        'SELECT nodes WHERE degree > 5 AND layer_count >= 2'
    )
    print(f"High-degree multilayer nodes: {len(result)}")

**Supported operators:** ``>``, ``>=``, ``<``, ``<=``, ``=``, ``!=``

**Multiple conditions** are combined with ``AND``. For more complex logic, use the builder API (see below).

**Expected output:**

.. code-block:: text

    High-degree nodes: 34
    High-degree multilayer nodes: 18

Compute Statistics
~~~~~~~~~~~~~~~~~~

The ``COMPUTE`` clause calculates network metrics and attaches them to result rows. This is where the DSL becomes powerful for analysis:

.. code-block:: python

    # Compute degree and betweenness centrality for nodes in 'social' layer
    result = execute_query(
        network,
        'SELECT nodes WHERE layer="social" '
        'COMPUTE degree COMPUTE betweenness_centrality'
    )
    
    # Convert to pandas for analysis
    df = result.to_pandas()
    
    print("Top nodes by betweenness centrality:")
    print(df[['id', 'degree', 'betweenness_centrality']].head())
    
    print("\nSummary statistics:")
    print(df[['degree', 'betweenness_centrality']].describe())

**Expected output:**

.. code-block:: text

    Top nodes by betweenness centrality:
                     id  degree  betweenness_centrality
    0  (alice, social)      12                 0.245
    1    (bob, social)       8                 0.189
    2    (eve, social)      15                 0.301
    3  (frank, social)       7                 0.134
    4  (grace, social)      11                 0.221

    Summary statistics:
                 degree  betweenness_centrality
    count     65.000000               65.000000
    mean       6.846154                0.112308
    std        3.241057                0.089542
    min        1.000000                0.000000
    25%        4.000000                0.045000
    50%        7.000000                0.089000
    75%       10.000000                0.167000
    max       15.000000                0.301000

**Available measures** include: ``degree``, ``betweenness_centrality``, ``closeness_centrality``, ``eigenvector_centrality``, ``pagerank``, ``clustering``, ``communities``. See :doc:`../reference/dsl_reference` for the complete list.

**Use case:** This pattern is ideal for generating summary statistics for papers, reports, or further statistical analysis.

Builder API (Type-Safe)
-----------------------

The **builder API is the recommended approach for production code**. It provides:

* IDE autocompletion and inline documentation
* Type checking with tools like mypy
* Clearer error messages
* Easier refactoring and composition of queries

All builder queries compile to the same AST as string queries, ensuring consistent semantics.

Basic Queries
~~~~~~~~~~~~~

Create and execute queries using the ``Q`` and ``L`` imports:

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Get all nodes
    result = Q.nodes().execute(network)
    print(f"Total nodes: {len(result)}")
    
    # Get nodes from a specific layer
    result = (
        Q.nodes()
         .from_layers(L["friends"])
         .execute(network)
    )
    print(f"Nodes in 'friends' layer: {len(result)}")

**Query reusability:** You can define a query once and execute it with different networks:

.. code-block:: python

    high_degree_query = Q.nodes().where(degree__gt=10).compute("betweenness_centrality")
    
    # Execute on multiple networks
    result_network1 = high_degree_query.execute(network1)
    result_network2 = high_degree_query.execute(network2)

Filtering
~~~~~~~~~

Use ``where()`` to add filter conditions. The builder API uses Django-style ``__`` suffixes for comparisons:

.. code-block:: python

    # Filter by property
    result = (
        Q.nodes()
         .where(degree__gt=5)
         .execute(network)
    )
    print(f"Nodes with degree > 5: {len(result)}")
    
    # Multiple conditions (combined with AND)
    result = (
        Q.nodes()
         .from_layers(L["work"])
         .where(degree__gt=3, layer_count__gte=2)
         .execute(network)
    )
    print(f"Multilayer high-degree nodes in 'work': {len(result)}")

**Supported comparison suffixes:**

* ``__gt``: greater than (``>``)
* ``__gte`` or ``__ge``: greater than or equal (``>=``)
* ``__lt``: less than (``<``)
* ``__lte`` or ``__le``: less than or equal (``<=``)
* ``__eq``: equal (``=``)
* ``__ne`` or ``__neq``: not equal (``!=``)

**Understanding** ``layer_count``:

In multilayer networks, a node may appear in multiple layers. The ``layer_count`` attribute indicates how many layers the node participates in:

* ``layer_count__gte=2``: nodes appearing in at least 2 layers
* ``layer_count__eq=1``: nodes appearing in exactly 1 layer (layer-specific nodes)

This is useful for identifying "connector" nodes that bridge multiple contexts.

Computing Metrics
~~~~~~~~~~~~~~~~~

Use ``compute()`` to calculate network metrics. Metrics are computed efficiently and attached to result rows:

.. code-block:: python

    # Compute multiple metrics
    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality", "clustering")
         .execute(network)
    )
    
    # Convert to DataFrame and analyze
    df = result.to_pandas()
    print(df.head(10))
    
    # Get top nodes by a metric
    top_by_betweenness = df.nlargest(10, 'betweenness_centrality')
    print("\nTop 10 nodes by betweenness centrality:")
    print(top_by_betweenness[['id', 'betweenness_centrality', 'degree']])

**Order of operations:**

* ``compute()`` can be called at any point in the chain
* Filters (``where()``) can reference computed metrics only if the metric is computed **before** the filter
* For best performance, filter first, then compute:

.. code-block:: python

    # Good: Filter first, then compute
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .where(degree__gt=5)
         .compute("betweenness_centrality")
         .execute(network)
    )

**Expected output:**

.. code-block:: text

                      id  degree  betweenness_centrality  clustering
    0   (alice, social)      12                 0.245000    0.545455
    1     (bob, social)       8                 0.189000    0.642857
    2     (eve, social)      15                 0.301000    0.428571
    3   (frank, social)       7                 0.134000    0.666667
    4   (grace, social)      11                 0.221000    0.509091
    ...

    Top 10 nodes by betweenness centrality:
                      id  betweenness_centrality  degree
    2     (eve, social)                 0.301000      15
    0   (alice, social)                 0.245000      12
    4   (grace, social)                 0.221000      11
    1     (bob, social)                 0.189000       8
    ...

Sorting and Limiting
~~~~~~~~~~~~~~~~~~~~

Use ``order_by()`` and ``limit()`` to control result ordering and size:

.. code-block:: python

    # Get top 10 nodes by degree
    result = (
        Q.nodes()
         .compute("degree")
         .order_by("-degree")  # "-" prefix for descending
         .limit(10)
         .execute(network)
    )
    
    print("Top 10 highest-degree nodes:")
    for node, data in result.items():
        print(f"  {node}: degree={data['degree']}")

**Sorting conventions:**

* ``order_by("degree")``: ascending (low to high)
* ``order_by("-degree")``: descending (high to low)
* Multiple keys: ``order_by("-degree", "layer_count")``: sort by degree descending, then layer_count ascending

**Expected output:**

.. code-block:: text

    Top 10 highest-degree nodes:
      ('eve', 'social'): degree=15
      ('alice', 'social'): degree=12
      ('grace', 'social'): degree=11
      ('charlie', 'work'): degree=10
      ('henry', 'friends'): degree=9
      ('diana', 'social'): degree=9
      ('bob', 'social'): degree=8
      ('frank', 'social'): degree=7
      ('iris', 'work'): degree=7
      ('jake', 'friends'): degree=6

Working with Results
--------------------

DSL queries return a ``QueryResult`` object that provides multiple ways to access and export data. Understanding how to work with results is crucial for integrating DSL queries into analysis pipelines.

Access as Dictionary
~~~~~~~~~~~~~~~~~~~~

``QueryResult`` provides dictionary-like access via ``.items()``:

.. code-block:: python

    result = Q.nodes().compute("degree").execute(network)
    
    # Iterate over all items
    for node, data in result.items():
        print(f"{node}: degree={data['degree']}")
    
    # Inspect one sample entry
    sample_key, sample_value = next(iter(result.items()))
    print(f"Sample key type: {type(sample_key)}")
    print(f"Sample key: {sample_key}")
    print(f"Sample value: {sample_value}")

**Result structure for nodes:**

* **Keys**: ``(node_id, layer)`` tuples (for multilayer queries) or ``node_id`` (for single-layer queries)
* **Values**: Dictionaries with computed attributes (``{"degree": 5, "betweenness_centrality": 0.23, ...}``)

**Result structure for edges:**

* **Keys**: ``((source, source_layer), (target, target_layer), {edge_data})`` tuples
* **Values**: Dictionaries with edge attributes and computed metrics

**Expected output:**

.. code-block:: text

    Sample key type: <class 'tuple'>
    Sample key: ('alice', 'social')
    Sample value: {'degree': 12, 'layer': 'social', 'layer_count': 2}

Convert to Pandas
~~~~~~~~~~~~~~~~~

**This is the recommended way to integrate DSL queries with statistical analysis and plotting libraries.**

.. code-block:: python

    result = (
        Q.nodes()
         .from_layers(L["social"])
         .compute("degree", "betweenness_centrality", "clustering")
         .execute(network)
    )
    
    # Convert to DataFrame
    df = result.to_pandas()
    
    # Inspect structure
    print(df.head())
    print("\nColumn names:", df.columns.tolist())
    print("\nSummary statistics:")
    print(df[['degree', 'betweenness_centrality', 'clustering']].describe())
    
    # Use pandas for further analysis
    high_influence = df[
        (df['degree'] > 10) & 
        (df['betweenness_centrality'] > 0.2)
    ]
    print(f"\nHigh-influence nodes: {len(high_influence)}")

**DataFrame structure:**

* **For node queries**: Columns include ``id`` (the node-layer tuple or node ID), plus all computed attributes
* **For edge queries**: Columns include ``source``, ``target``, ``source_layer``, ``target_layer``, ``weight``, plus computed attributes

**Expected output:**

.. code-block:: text

                      id  degree  betweenness_centrality  clustering
    0   (alice, social)      12                 0.245000    0.545455
    1     (bob, social)       8                 0.189000    0.642857
    2     (eve, social)      15                 0.301000    0.428571
    3   (frank, social)       7                 0.134000    0.666667
    4   (grace, social)      11                 0.221000    0.509091

    Column names: ['id', 'degree', 'betweenness_centrality', 'clustering']

    Summary statistics:
                 degree  betweenness_centrality  clustering
    count     65.000000               65.000000   65.000000
    mean       6.846154                0.112308    0.587692
    std        3.241057                0.089542    0.145231
    ...

    High-influence nodes: 8

**Multi-index option:**

For more complex analyses, you can reshape the ``id`` tuple into a multi-index:

.. code-block:: python

    df = result.to_pandas()
    # Split 'id' tuple into separate columns
    df[['node', 'layer']] = pd.DataFrame(df['id'].tolist(), index=df.index)
    df = df.drop('id', axis=1)
    df = df.set_index(['node', 'layer'])
    print(df.head())

Filter Results
~~~~~~~~~~~~~~

You can filter results in two ways: **using the DSL's** ``where()`` **clause** (recommended) or **post-processing** with Python/pandas.

**Option 1: Filter in the query (recommended for large networks):**

.. code-block:: python

    # Filter before computation for efficiency
    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .where(degree__gt=5)
         .execute(network)
    )

**Option 2: Filter the result dictionary (for small networks or ad-hoc filtering):**

.. code-block:: python

    result = Q.nodes().compute("degree").execute(network)
    
    # Pure Python filtering
    high_degree = {
        node: data
        for node, data in result.items()
        if data['degree'] > 5
    }
    print(f"High-degree nodes: {len(high_degree)}")

**Option 3: Filter the DataFrame (most flexible for complex conditions):**

.. code-block:: python

    df = result.to_pandas()
    
    # Use pandas boolean indexing
    filtered = df[df['degree'] > 5]
    
    # Complex conditions
    interesting_nodes = df[
        (df['degree'] > 5) & 
        (df['betweenness_centrality'] > df['betweenness_centrality'].mean())
    ]

**Performance note:** For very large networks (millions of nodes), filtering in the DSL query (Option 1) is most efficient because it avoids materializing unnecessary results. For smaller networks, pandas filtering (Option 3) is often more convenient.

Advanced Queries
----------------

This section showcases the DSL's power for sophisticated multilayer network analysis. These patterns are common in research and can be adapted to your specific needs.

Multiple Layer Selection
~~~~~~~~~~~~~~~~~~~~~~~~~

Use **layer algebra** to combine layers. The ``L`` object supports set operations:

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Union: nodes/edges from EITHER layer
    result = (
        Q.nodes()
         .from_layers(L["friends"] + L["work"])
         .compute("degree")
         .execute(network)
    )
    
    df = result.to_pandas()
    print(f"Combined nodes from 'friends' and 'work': {len(df)}")
    print(f"Average degree across both layers: {df['degree'].mean():.2f}")

**Set semantics:**

* ``L["friends"] + L["work"]``: **Union** of nodes/edges from both layers (nodes appearing in either layer)
* ``L["friends"] & L["work"]``: **Intersection** (see next section)
* ``L["friends"] - L["work"]``: **Difference** (nodes in friends but not work)

**Use case:** Compare activity across related contexts. For example, analyze user behavior across social and professional networks together.

**Expected output:**

.. code-block:: text

    Combined nodes from 'friends' and 'work': 87
    Average degree across both layers: 6.12

Layer Intersection
~~~~~~~~~~~~~~~~~~

Find nodes that appear in **multiple specific layers**:

.. code-block:: python

    # Nodes present in BOTH 'friends' AND 'work' layers
    result = (
        Q.nodes()
         .from_layers(L["friends"] & L["work"])
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )
    
    df = result.to_pandas()
    print(f"Nodes in both 'friends' and 'work': {len(df)}")
    print("\nThese are 'connector' nodes bridging social and professional contexts")
    print(df.head(10))

**Semantics:**

* ``L["friends"] & L["work"]`` selects nodes that have representations in **both** layers
* This is different from ``layer_count >= 2``, which selects nodes in **any** two layers
* Use intersection to find nodes bridging specific contexts

**Alternative approach using** ``layer_count``:

.. code-block:: python

    # More general: nodes in at least 2 layers (any layers)
    result = (
        Q.nodes()
         .where(layer_count__gte=2)
         .compute("degree")
         .execute(network)
    )
    print(f"Multilayer nodes (any 2+ layers): {len(result)}")

**Expected output:**

.. code-block:: text

    Nodes in both 'friends' and 'work': 23
    
    These are 'connector' nodes bridging social and professional contexts
                       id  degree  betweenness_centrality
    0    (alice, friends)      12                 0.245000
    1      (alice, work)       8                 0.189000
    2  (charlie, friends)      10                 0.201000
    3    (charlie, work)       7                 0.145000
    ...

Query Edges
~~~~~~~~~~~

The DSL supports edge queries with the same flexibility as node queries:

.. code-block:: python

    # Select edges from a layer with weight filter
    edges = (
        Q.edges()
         .from_layers(L["social"])
         .where(weight__gt=0.5)
         .compute("edge_betweenness")
         .execute(network)
    )
    
    df = edges.to_pandas()
    print(f"High-weight edges in 'social' layer: {len(df)}")
    print("\nSample edges:")
    print(df.head())
    
    # Analyze edge distribution
    print(f"\nMean edge weight: {df['weight'].mean():.3f}")
    print(f"Mean edge betweenness: {df['edge_betweenness'].mean():.3f}")

**Edge result structure:**

For edge queries, the DataFrame includes:

* ``source``, ``target``: node identifiers
* ``source_layer``, ``target_layer``: layer names (same for intralayer edges)
* ``weight``: edge weight (default 1.0 if not specified)
* Computed attributes: ``edge_betweenness``, etc.

**Filter by edge type:**

.. code-block:: python

    # Only intralayer edges (within a layer)
    intralayer_edges = (
        Q.edges()
         .where(intralayer=True)
         .execute(network)
    )
    print(f"Intralayer edges: {len(intralayer_edges)}")
    
    # Only interlayer edges between specific layers
    interlayer_edges = (
        Q.edges()
         .where(interlayer=("social", "work"))
         .execute(network)
    )
    print(f"Edges between 'social' and 'work': {len(interlayer_edges)}")

**Expected output:**

.. code-block:: text

    High-weight edges in 'social' layer: 156
    
    Sample edges:
        source  target source_layer target_layer  weight  edge_betweenness
    0    alice     bob       social       social    0.75          0.023400
    1      bob   charlie     social       social    0.80          0.034500
    2    alice   diana       social       social    0.92          0.019800
    3    diana     eve       social       social    0.65          0.028900
    4      eve   frank       social       social    0.88          0.041200
    
    Mean edge weight: 0.723
    Mean edge betweenness: 0.028

Smart Defaults and Error Messages
----------------------------------

The DSL includes **smart defaults** that automatically compute commonly used centrality metrics when referenced but not explicitly computed. This feature makes queries more ergonomic while maintaining predictable behavior.

Auto-Computing Centrality Metrics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you reference a centrality metric in operations like ``top_k()``, ``order_by()``, or other ranking operations, the DSL will automatically compute it if not already present:

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # The DSL auto-computes betweenness_centrality when needed
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .per_layer()
            .top_k(5, "betweenness_centrality")  # Auto-computed here
         .end_grouping()
         .execute(network)
    )
    
    df = result.to_pandas()
    # betweenness_centrality column is available even though
    # we didn't explicitly call .compute("betweenness_centrality")

**Supported centrality aliases:**

* ``degree``, ``degree_centrality``
* ``betweenness``, ``betweenness_centrality``
* ``closeness``, ``closeness_centrality``
* ``eigenvector``, ``eigenvector_centrality``
* ``pagerank``

**When auto-compute happens:**

* When the attribute is referenced in ``top_k()``
* When the attribute is used in ``order_by()``
* For both per-group (with grouping) and global operations

**Example with multiple auto-computed metrics:**

.. code-block:: python

    # Auto-compute degree for filtering and betweenness for ranking
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .where(degree__gt=2)  # degree auto-computed here
         .order_by("betweenness_centrality", desc=True)  # betweenness auto-computed here
         .limit(10)
         .execute(network)
    )

**Expected output:**

.. code-block:: text

        node layer  degree  betweenness_centrality
    0  alice social      8                0.143000
    1    bob social      7                0.098000
    2  carol social      6                0.067000
    ...

Controlling Autocompute Behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can explicitly control whether metrics are automatically computed using the ``autocompute`` parameter:

.. code-block:: python

    # Disable autocompute - require explicit .compute() calls
    result = (
        Q.nodes(autocompute=False)  # Autocompute disabled
         .from_layers(L["social"])
         .compute("degree")  # Must explicitly compute
         .where(degree__gt=5)
         .execute(network)
    )
    
    # This would raise DslMissingMetricError because betweenness is not computed:
    # Q.nodes(autocompute=False).order_by("betweenness_centrality").execute(net)

**When to disable autocompute:**

* **Performance-critical code**: Avoid unexpected expensive computations
* **Explicit control**: Make all metric computations visible in code
* **Debugging**: Understand exactly which metrics are computed and when

**Tracking computed metrics:**

Query results include a ``computed_metrics`` attribute that tracks which metrics were computed during execution:

.. code-block:: python

    result = (
        Q.nodes()
         .from_layers(L["social"])
         .compute("degree")
         .order_by("betweenness_centrality")  # Auto-computed
         .execute(network)
    )
    
    # Check which metrics were computed
    print(f"Computed metrics: {result.computed_metrics}")
    # Output: Computed metrics: {'degree', 'betweenness_centrality'}

**Use cases for computed_metrics:**

* Performance profiling: identify expensive operations
* Query optimization: avoid redundant computations
* Debugging: verify expected metrics were computed

Helpful Error Messages with Suggestions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you reference an unknown attribute, the DSL provides **did you mean?** suggestions using fuzzy string matching:

.. code-block:: python

    # Typo in attribute name
    try:
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .per_layer()
                .top_k(5, "betweness_centrality")  # Typo: "betweness" instead of "betweenness"
             .end_grouping()
             .execute(network)
        )
    except UnknownAttributeError as e:
        print(e)

**Output:**

.. code-block:: text

    Unknown attribute 'betweness_centrality'. Did you mean 'betweenness_centrality'?
    Known attributes: betweenness, betweenness_centrality, closeness, closeness_centrality, 
                      degree, degree_centrality, eigenvector, eigenvector_centrality, pagerank

**The error includes:**

* The incorrect attribute name
* A suggestion for the most similar correct name (using Levenshtein distance)
* A list of all available attributes

Grouping Requirements and Clear Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some operations require **active grouping** (via ``per_layer()`` or ``group_by()``). The DSL raises ``GroupingError`` with clear guidance when these operations are used incorrectly:

.. code-block:: python

    from py3plex.dsl.errors import GroupingError
    
    # This will raise GroupingError
    try:
        result = (
            Q.nodes()
             .from_layers(L["*"])
             .coverage(mode="all")  # Error: no grouping active
             .execute(network)
        )
    except GroupingError as e:
        print(e)

**Output:**

.. code-block:: text

    coverage() requires an active grouping (e.g. per_layer(), group_by('layer')). 
    No grouping is currently active.
    Example:
        Q.nodes().from_layers(L["*"])
            .per_layer().top_k(5, "degree").end_grouping()
            .coverage(mode="all")

**Correct usage:**

.. code-block:: python

    # With proper grouping
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .per_layer()  # Add grouping here
            .top_k(5, "degree")
         .end_grouping()
         .coverage(mode="all")  # Now works correctly
         .execute(network)
    )

When Smart Defaults DON'T Apply
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Smart defaults are **predictable and conservative**. They only apply in specific scenarios:

1. **Only for centrality metrics**: Smart defaults work for recognized centrality metrics (degree, betweenness, etc.), not arbitrary attributes.

2. **Explicit compute takes precedence**: If you explicitly compute a metric, the DSL uses your computation and doesn't auto-compute:

   .. code-block:: python
   
       # Explicit compute - no auto-compute happens
       result = (
           Q.nodes()
            .from_layers(L["*"])
            .compute("betweenness_centrality")  # Explicit
            .per_layer()
               .top_k(5, "betweenness_centrality")  # Uses explicit computation
            .end_grouping()
            .execute(network)
       )

3. **Edge attributes are not auto-computed**: For edge queries, attributes like ``weight`` are read from edge data, not auto-computed:

   .. code-block:: python
   
       # Edge weight is read from edge data, not computed
       result = (
           Q.edges()
            .from_layers(L["*"])
            .per_layer()
               .top_k(5, "weight")  # Uses edge data['weight']
            .end_grouping()
            .execute(network)
       )

Benefits of Smart Defaults
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Ergonomics**: Write less boilerplate for common patterns:

.. code-block:: python

    # Before smart defaults (verbose)
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree", "betweenness_centrality", "closeness_centrality")
         .per_layer()
            .top_k(5, "betweenness_centrality")
         .end_grouping()
         .execute(network)
    )
    
    # With smart defaults (concise)
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .per_layer()
            .top_k(5, "betweenness_centrality")  # Auto-computes what's needed
         .end_grouping()
         .execute(network)
    )

**Teaching errors**: When something goes wrong, you get actionable guidance instead of cryptic messages.

**Predictability**: Smart defaults only activate for well-known patterns. Your explicit operations always take precedence.

Temporal Queries
----------------

The DSL supports temporal filtering for networks with time-stamped edges or nodes. Four convenience methods provide intuitive temporal filtering: ``.at(t)``, ``.during(t0, t1)``, ``.before(t)``, and ``.after(t)``.

**Prerequisites for temporal queries:**

* Edges or nodes must have temporal attributes:
  
  * **Point-in-time**: ``t`` attribute (e.g., ``{"t": 150.0}``)
  * **Intervals**: ``t_start`` and ``t_end`` attributes (e.g., ``{"t_start": 100.0, "t_end": 200.0}``)

* Time values are typically numeric (timestamps) or ISO date strings

Temporal Semantics Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following table summarizes temporal query semantics:

.. list-table:: Temporal Query Operations
   :header-rows: 1
   :widths: 15 25 35 25

   * - Method
     - Description
     - Interval Semantics
     - Inclusivity
   * - ``.at(t)``
     - Snapshot at time t
     - Entities active at exactly t
     - Point (closed)
   * - ``.during(t0, t1)``
     - Range from t0 to t1
     - Entities active during [t0, t1]
     - [t0, t1] (closed interval)
   * - ``.before(t)``
     - Before time t
     - Equivalent to ``.during(None, t)``
     - (-∞, t] (closed at t)
   * - ``.after(t)``
     - After time t
     - Equivalent to ``.during(t, None)``
     - [t, +∞) (closed at t)

**Detailed semantics:**

* ``at(t)``: Selects entities active at a specific moment
  
  * For point-in-time edges: includes edges where ``t_edge == t``
  * For interval edges: includes edges where ``t`` is in ``[t_start, t_end]``

* ``during(t0, t1)``: Selects entities active during a time window
  
  * For point-in-time edges: includes edges where ``t`` is in ``[t0, t1]`` (closed interval)
  * For interval edges: includes edges where the interval **overlaps** ``[t0, t1]``
  * ``None`` values: Use ``t0=None`` for open lower bound, ``t1=None`` for open upper bound

* ``before(t)``: Selects entities active before (and at) time t
  
  * Convenience method equivalent to ``.during(None, t)``
  * Inclusive of the boundary: includes entities at exactly time t

* ``after(t)``: Selects entities active after (and at) time t
  
  * Convenience method equivalent to ``.during(t, None)``
  * Inclusive of the boundary: includes entities at exactly time t

Filter by Time (Snapshot)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Query the network state at a specific point in time:

.. code-block:: python

    # Nodes active at t=150.0
    result = (
        Q.nodes()
         .at(150.0)
         .compute("degree")
         .execute(network)
    )
    
    df = result.to_pandas()
    print(f"Nodes active at t=150: {len(df)}")
    print(f"Average degree at t=150: {df['degree'].mean():.2f}")
    print("\nTop nodes by degree at this snapshot:")
    print(df.nlargest(5, 'degree')[['id', 'degree']])

**Use case:** Analyze network structure at specific moments (e.g., before and after an event, at regular intervals for time series).

**Expected output:**

.. code-block:: text

    Nodes active at t=150: 78
    Average degree at t=150: 5.12
    
    Top nodes by degree at this snapshot:
                       id  degree
    12    (eve, social)      14
    5   (alice, social)      11
    23  (grace, social)      10
    8     (bob, social)       9
    31  (henry, work)        9

Time Range
~~~~~~~~~~

Query entities active during a time window:

.. code-block:: python

    # Nodes active during January 2024 (assuming numeric timestamps)
    # For ISO dates, use strings: .during("2024-01-01", "2024-01-31")
    result = (
        Q.nodes()
         .during(100.0, 200.0)
         .compute("degree")
         .execute(network)
    )
    
    df = result.to_pandas()
    print(f"Nodes active during [100, 200]: {len(df)}")
    
    # Compare to snapshot
    snapshot_result = Q.nodes().at(150.0).execute(network)
    print(f"Nodes at t=150 (snapshot): {len(snapshot_result)}")
    print(f"Nodes during [100, 200] (range): {len(df)}")
    print(f"Ratio: {len(df) / len(snapshot_result):.2f}x more nodes in range")

**Open-ended ranges:**

.. code-block:: python

    # From t=100 onwards (no upper limit)
    result_after = Q.edges().during(100.0, None).execute(network)
    
    # Up to t=200 (no lower limit)
    result_before = Q.edges().during(None, 200.0).execute(network)

**Use case:** Study network evolution, identify persistent vs. transient connections, analyze activity bursts.

**Expected output:**

.. code-block:: text

    Nodes active during [100, 200]: 142
    Nodes at t=150 (snapshot): 78
    Ratio: 1.82x more nodes in range

Before and After (Convenience Methods)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``.before()`` and ``.after()`` methods provide intuitive alternatives for open-ended temporal queries:

.. code-block:: python

    # Get all edges before time 100 (inclusive)
    early_edges = Q.edges().before(100.0).execute(network)
    
    # Get all edges after time 200 (inclusive)
    late_edges = Q.edges().after(200.0).execute(network)
    
    # Common pattern: compare network before and after an event
    event_time = 150.0
    
    before_event = (
        Q.nodes()
         .before(event_time)
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )
    
    after_event = (
        Q.nodes()
         .after(event_time)
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )
    
    # Compare metrics
    df_before = before_event.to_pandas()
    df_after = after_event.to_pandas()
    
    print(f"Average degree before event: {df_before['degree'].mean():.2f}")
    print(f"Average degree after event: {df_after['degree'].mean():.2f}")
    print(f"Network became {'denser' if df_after['degree'].mean() > df_before['degree'].mean() else 'sparser'}")

**Expected output:**

.. code-block:: text

    Average degree before event: 4.35
    Average degree after event: 5.87
    Network became denser

**Temporal edges example:**

.. code-block:: python

    # Edges active during a period
    edges = (
        Q.edges()
         .during(100.0, 200.0)
         .compute("edge_betweenness")
         .execute(network)
    )
    
    df = edges.to_pandas()
    print(f"Active edges during [100, 200]: {len(df)}")
    print(f"Mean edge betweenness: {df['edge_betweenness'].mean():.4f}")

**Note on implementation status:**

Temporal queries are **fully implemented** for edge-level temporal data. Node-level temporal filtering depends on your network's representation:

* If nodes have explicit ``t`` attributes, ``.at()``, ``.during()``, ``.before()``, and ``.after()`` work directly
* If only edges are timestamped, node activity is inferred from edge presence
* For most use cases, temporal edge queries are sufficient

See :doc:`../reference/dsl_reference` for complete temporal query syntax and examples with ISO date strings.

Common Patterns
---------------

This section presents **end-to-end recipes** for common multilayer network analysis tasks. These patterns are production-ready and can be adapted to your research questions.

Pattern: Find Influential Nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Identify nodes that are both well-connected (high degree) and structurally important (high betweenness centrality):

.. code-block:: python

    # High-degree nodes ranked by betweenness centrality
    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality", "layer_count")
         .where(degree__gt=10)
         .order_by("-betweenness_centrality")
         .limit(20)
         .execute(network)
    )
    
    df = result.to_pandas()
    print(f"Top 20 influential nodes (degree > 10):")
    print(df[['id', 'degree', 'betweenness_centrality', 'layer_count']])
    
    # Export for further analysis or publication
    df.to_csv("influential_nodes.csv", index=False)
    
    # Visualize
    import matplotlib.pyplot as plt
    plt.figure(figsize=(10, 6))
    plt.scatter(df['degree'], df['betweenness_centrality'], 
                s=df['layer_count']*50, alpha=0.6)
    plt.xlabel("Degree")
    plt.ylabel("Betweenness Centrality")
    plt.title("Influential Nodes (size = layer_count)")
    plt.tight_layout()
    plt.savefig("influential_nodes.png", dpi=300)

**Why this pattern works:**

* **Degree** measures local connectivity (how many neighbors)
* **Betweenness centrality** measures global importance (how often the node appears on shortest paths)
* Nodes high in both metrics are **influential bridges** in the network

**Expected output:**

.. code-block:: text

    Top 20 influential nodes (degree > 10):
                       id  degree  betweenness_centrality  layer_count
    0     (eve, social)      15                 0.301000            3
    1   (alice, social)      12                 0.245000            2
    2   (grace, social)      11                 0.221000            2
    3     (bob, social)      12                 0.198000            1
    4   (diana, work)        14                 0.187000            3
    ...

Pattern: Compare Layer Activity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compute summary statistics for each layer to understand layer-specific dynamics:

.. code-block:: python

    layers = network.get_layers()
    
    layer_stats = []
    for layer in layers:
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree", "clustering")
             .execute(network)
        )
        df = result.to_pandas()
        
        layer_stats.append({
            'layer': layer,
            'num_nodes': len(df),
            'mean_degree': df['degree'].mean(),
            'max_degree': df['degree'].max(),
            'mean_clustering': df['clustering'].mean(),
        })
        
        print(f"{layer}: {len(df)} nodes, "
              f"avg degree={df['degree'].mean():.2f}, "
              f"avg clustering={df['clustering'].mean():.3f}")
    
    # Create comparison DataFrame
    import pandas as pd
    comparison = pd.DataFrame(layer_stats)
    print("\nLayer comparison:")
    print(comparison)
    
    # Visualize
    comparison.plot(x='layer', y=['mean_degree', 'mean_clustering'], 
                    kind='bar', figsize=(10, 5))
    plt.ylabel("Value")
    plt.title("Layer Activity Comparison")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("layer_comparison.png", dpi=300)

**Use case:** Understand how network structure varies across different contexts (e.g., online vs. offline interactions, different communication channels).

**Expected output:**

.. code-block:: text

    friends: 50 nodes, avg degree=4.20, avg clustering=0.623
    work: 72 nodes, avg degree=3.15, avg clustering=0.512
    social: 65 nodes, avg degree=5.01, avg clustering=0.587
    family: 38 nodes, avg degree=6.84, avg clustering=0.701
    
    Layer comparison:
          layer  num_nodes  mean_degree  max_degree  mean_clustering
    0   friends         50         4.20          15            0.623
    1      work         72         3.15          12            0.512
    2    social         65         5.01          18            0.587
    3    family         38         6.84          21            0.701

Pattern: Export Subnetwork
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Extract a subnetwork based on query criteria for focused analysis or visualization:

.. code-block:: python

    # Extract high-activity multilayer nodes
    active_nodes = (
        Q.nodes()
         .where(layer_count__gt=2)
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )
    
    print(f"Selected {len(active_nodes)} multilayer nodes")
    
    # Create subnetwork containing only these nodes
    subnetwork = network.subgraph(active_nodes.keys())
    
    print(f"Subnetwork: {subnetwork.number_of_nodes()} nodes, "
          f"{subnetwork.number_of_edges()} edges")
    
    # Analyze subnetwork
    df = active_nodes.to_pandas()
    print(f"\nSubnetwork mean degree: {df['degree'].mean():.2f}")
    print(f"Subnetwork mean betweenness: {df['betweenness_centrality'].mean():.4f}")
    
    # Export for visualization or further analysis
    from py3plex.visualization import draw_multilayer_default
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(12, 10))
    draw_multilayer_default(subnetwork, ax=ax, display=False)
    plt.savefig("subnetwork_viz.png", dpi=300)
    plt.close()
    
    # Or export in various formats
    subnetwork.save_network("subnetwork.edgelist", output_type="edgelist")

**What** ``layer_count__gt=2`` **means:**

* Selects nodes appearing in **more than 2 layers**
* These are "connector" nodes that participate in multiple contexts
* Useful criterion for studying nodes that bridge different social spheres

**Alternative criteria:**

.. code-block:: python

    # High betweenness nodes
    influential = Q.nodes().compute("betweenness_centrality").where(
        betweenness_centrality__gt=0.1
    ).execute(network)
    
    # Nodes in specific community
    community_nodes = Q.nodes().compute("communities").where(
        communities__eq=3
    ).execute(network)

**Expected output:**

.. code-block:: text

    Selected 34 multilayer nodes
    Subnetwork: 34 nodes, 127 edges
    
    Subnetwork mean degree: 7.47
    Subnetwork mean betweenness: 0.0892

**Workflow integration:**

This pattern is often combined with community detection, dynamics simulation, or centrality analysis:

.. code-block:: python

    # 1. Select subnetwork
    core_nodes = Q.nodes().where(layer_count__gte=2, degree__gt=5).execute(network)
    subnetwork = network.subgraph(core_nodes.keys())
    
    # 2. Run community detection on subnetwork
    from py3plex.algorithms.community_detection.community_wrapper import louvain_communities
    communities = louvain_communities(subnetwork)
    
    # 3. Analyze communities
    print(f"Found {len(set(communities.values()))} communities")
    
    # 4. Visualize or export
    from py3plex.visualization import draw_multilayer_default
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(12, 10))
    # Note: communities dict can be used for node coloring if the visualization function supports it
    draw_multilayer_default(subnetwork, ax=ax, display=False)
    plt.savefig("core_network_communities.png", dpi=300)
    plt.close()

Pattern: Per-Layer Top-K with Coverage (Multi-Layer Hub Detection)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Find nodes that are top-k hubs (by any centrality metric) **across all layers**. This pattern is essential for identifying nodes that maintain high influence in the entire multilayer structure, not just in isolated layers.

**The Problem:**

Traditional approaches require manual loops over layers:

.. code-block:: python

    # Old approach: manual iteration
    layer_top = {}
    for layer in network.layers:
        res = (
            Q.nodes()
             .from_layers(L[str(layer)])
             .where(degree__gt=1)
             .compute("betweenness_centrality")
             .order_by("-betweenness_centrality")
             .limit(5)
             .execute(network)
        )
        layer_top[layer] = set(res.to_pandas()["id"])
    
    # Find intersection
    multi_hubs = set.intersection(*layer_top.values())

**The Solution: Grouping and Coverage API**

The new DSL supports per-layer operations in a single query:

.. code-block:: python

    from py3plex.core import random_generators
    from py3plex.dsl import Q, L
    
    # Generate example network
    net = random_generators.random_multilayer_ER(n=200, l=3, p=0.05, directed=False)
    
    # Find nodes that are top-5 betweenness hubs in ALL layers (single query!)
    multi_hubs = (
        Q.nodes()
         .from_layers(L["*"])                   # wildcard: all layers
         .where(degree__gt=1)
         .compute("degree", "betweenness_centrality")
         .per_layer()                           # group by layer
            .top_k(5, "betweenness_centrality") # top 5 per layer
         .end_grouping()
         .coverage(mode="all")                  # nodes in top-5 in ALL layers
         .execute(net)
    )
    
    df = multi_hubs.to_pandas()
    print(f"Multi-layer hubs (in top-5 of ALL layers): {set(df['id'])}")
    print(f"Count: {len(df['id'].unique())}")
    print(f"\nDetailed results:")
    print(df[['id', 'layer', 'degree', 'betweenness_centrality']].to_string())

**Expected output:**

.. code-block:: text

    Multi-layer hubs (in top-5 of ALL layers): {23, 45, 67}
    Count: 3
    
    Detailed results:
        id  layer  degree  betweenness_centrality
    0   23      0      12                  0.2456
    1   23      1      14                  0.2891
    2   23      2      11                  0.2234
    3   45      0      13                  0.2567
    4   45      1      11                  0.2123
    5   45      2      15                  0.3012
    6   67      0      10                  0.2001
    7   67      1      12                  0.2345
    8   67      2      13                  0.2678

**Coverage Modes:**

The ``coverage()`` method supports multiple modes for cross-layer analysis:

.. code-block:: python

    # Mode 1: "all" - intersection (nodes in top-k of ALL layers)
    all_layers_hubs = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree")
         .per_layer()
            .top_k(10, "degree")
         .end_grouping()
         .coverage(mode="all")
         .execute(net)
    )
    
    # Mode 2: "any" - union (nodes in top-k of AT LEAST ONE layer)
    any_layer_hubs = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree")
         .per_layer()
            .top_k(10, "degree")
         .end_grouping()
         .coverage(mode="any")
         .execute(net)
    )
    
    # Mode 3: "at_least" - nodes in top-k of at least K layers
    two_layer_hubs = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("betweenness_centrality")
         .per_layer()
            .top_k(5, "betweenness_centrality")
         .end_grouping()
         .coverage(mode="at_least", k=2)  # In at least 2 layers
         .execute(net)
    )
    
    # Mode 4: "exact" - nodes in top-k of exactly K layers (layer-specific hubs)
    single_layer_specialists = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree")
         .per_layer()
            .top_k(10, "degree")
         .end_grouping()
         .coverage(mode="exact", k=1)  # Exactly 1 layer
         .execute(net)
    )
    
    print(f"Hubs in ALL layers: {len(all_layers_hubs.to_pandas()['id'].unique())}")
    print(f"Hubs in ANY layer: {len(any_layer_hubs.to_pandas()['id'].unique())}")
    print(f"Hubs in ≥2 layers: {len(two_layer_hubs.to_pandas()['id'].unique())}")
    print(f"Layer specialists (exactly 1): {len(single_layer_specialists.to_pandas()['id'].unique())}")

**Expected output:**

.. code-block:: text

    Hubs in ALL layers: 3
    Hubs in ANY layer: 27
    Hubs in ≥2 layers: 12
    Layer specialists (exactly 1): 15

**Wildcard Layer Selection:**

The ``L["*"]`` wildcard automatically expands to all layers in the network:

.. code-block:: python

    # All layers
    Q.nodes().from_layers(L["*"])
    
    # All layers except one
    Q.nodes().from_layers(L["*"] - L["bots"])
    
    # All layers intersected with a specific one (same as selecting that layer)
    Q.nodes().from_layers(L["*"] & L["social"])

**Use Cases:**

1. **Identify persistent influencers**: Nodes that maintain high centrality across all contexts (layers)
2. **Find layer specialists**: Nodes that are important in only one layer (``mode="exact", k=1``)
3. **Detect multi-context bridges**: Nodes in top-k in at least 2 layers connect different contexts
4. **Community structure analysis**: Compare ``mode="all"`` vs ``mode="any"`` to understand layer cohesion

**Why This Pattern Matters:**

In real-world multilayer networks (social media, collaboration networks, biological systems), understanding **cross-layer** vs. **layer-specific** importance is crucial:

* **Email + Phone + Chat network**: Who are the omnipresent communicators vs. email-only specialists?
* **Author collaboration network**: Who publishes top papers in multiple fields vs. specialists in one domain?
* **Transportation network**: Which locations are hubs in all modes (bus, train, bike) vs. single-mode hubs?

**Performance Note:**

The per-layer computation is optimized: measures are computed on the selected nodes after layer filtering, and grouping operations leverage efficient dictionaries. For large networks (>100K nodes), consider filtering with ``where()`` before computing expensive metrics like betweenness centrality.

DSL Result Interoperability
----------------------------

DSL query results seamlessly integrate with py3plex's dplyr-style pipeline API (``nodes()``, ``edges()``, ``mutate()``, ``filter()``, ``arrange()``). This interoperability allows you to:

1. Start with a DSL query to filter and compute metrics
2. Continue with pipeline verbs for additional transformations
3. Combine the declarative power of DSL with the procedural flexibility of pipelines

QueryResult as Pipeline Input
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``QueryResult`` object returned by ``.execute()`` provides the same interface as pipeline frames (``NodeFrame``, ``EdgeFrame``), enabling seamless chaining:

.. code-block:: python

    from py3plex.dsl import Q, L
    from py3plex.core import multinet
    
    # Load network
    network = multinet.multi_layer_network()
    network.load_network("data.multiedgelist", input_type="multiedgelist")
    
    # Start with DSL query, continue with pipeline operations
    result = (
        Q.nodes()
         .from_layers(L["*"])
         .compute("degree", "betweenness_centrality")
         .execute(network)
         .filter(lambda row: row["degree"] > 5)  # Pipeline filter
         .mutate(
             # Add computed columns
             influence_score=lambda row: row["degree"] * row["betweenness_centrality"],
             is_hub=lambda row: row["degree"] > 10
         )
         .arrange("influence_score", reverse=True)  # Pipeline arrange (sort)
         .to_pandas()  # Export to DataFrame
    )
    
    print(result.head(10))

**What happens here:**

1. **DSL phase**: ``Q.nodes()...execute()`` filters nodes, computes centrality metrics
2. **Pipeline phase**: ``.filter()``, ``.mutate()``, ``.arrange()`` transform the result
3. **Export**: ``.to_pandas()`` materializes as a DataFrame

**Supported pipeline verbs on QueryResult:**

* ``.filter(predicate)``: Keep rows matching predicate
* ``.mutate(**kwargs)``: Add or transform columns
* ``.arrange(*cols, reverse=False)``: Sort by columns
* ``.select(*cols)``: Keep only specified columns
* ``.group_by(*cols)``: Group rows (enables ``.summarize()``)
* ``.summarize(**aggs)``: Aggregate grouped data
* ``.to_pandas()``: Convert to pandas DataFrame

Verb Mapping Table
~~~~~~~~~~~~~~~~~~

The following table shows how concepts map across the three interfaces (String DSL, Builder API, Pipeline):

.. list-table:: DSL and Pipeline Verb Mapping
   :header-rows: 1
   :widths: 20 25 25 30

   * - Concept
     - String DSL
     - Builder DSL
     - Pipeline/dplyr
   * - Filter rows
     - ``WHERE degree > 5``
     - ``.where(degree__gt=5)``
     - ``.filter(lambda r: r["degree"] > 5)``
   * - Select columns
     - ``SELECT id, degree``
     - ``.select("id", "degree")``
     - ``.select("id", "degree")``
   * - Sort/Order
     - ``ORDER BY degree DESC``
     - ``.order_by("degree", desc=True)``
     - ``.arrange("degree", reverse=True)``
   * - Group by field
     - ``GROUP BY layer``
     - ``.group_by("layer")``
     - ``.group_by("layer")``
   * - Add column
     - (not available)
     - ``.mutate(score=...)``
     - ``.mutate(score=lambda r: ...)``
   * - Aggregate
     - (not available)
     - ``.summarize(...)``
     - ``.summarize(mean_degree="mean(degree)")``
   * - Limit results
     - ``LIMIT 10``
     - ``.limit(10)``
     - ``.head(10)``

**Design rationale:**

* **DSL**: Declarative, optimized for graph queries (layer algebra, centrality, grouping)
* **Pipelines**: Procedural, flexible for data transformations (arbitrary computations, reshaping)
* **Interoperability**: Use DSL for graph-specific operations, pipelines for data munging

Example: Combined Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A realistic workflow combining both DSL and pipeline operations:

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Scenario: Find influential nodes in social network, normalize scores, 
    #           rank within communities, export for visualization
    
    result = (
        # DSL: Query and compute graph metrics
        Q.nodes()
         .from_layers(L["social"])
         .where(degree__gt=3)
         .compute("degree", "betweenness_centrality", "clustering")
         .execute(network)
         
         # Pipeline: Transform and enhance data
         .mutate(
             # Normalize centrality to [0, 1]
             norm_betweenness=lambda r: (
                 r["betweenness_centrality"] / max_betweenness
                 if max_betweenness > 0 else 0
             ),
             # Composite influence score
             influence=lambda r: (
                 0.5 * r["degree"] + 
                 0.3 * r["norm_betweenness"] + 
                 0.2 * (1 - r["clustering"])
             )
         )
         .group_by("community")  # Assume community attribute exists
         .summarize(
             count="count()",
             mean_influence="mean(influence)",
             top_influencer="max(influence)"
         )
         .arrange("mean_influence", reverse=True)
         .to_pandas()
    )
    
    # Now result is a pandas DataFrame ready for plotting
    print(result)

**Expected output:**

.. code-block:: text

    community  count  mean_influence  top_influencer
    0       5     23            0.72            0.89
    1       2     31            0.68            0.85
    2       8     19            0.61            0.79
    3       1     28            0.58            0.74
    ...

**Why this matters:**

1. **Single pipeline**: No need to export intermediate results to disk or juggle multiple DataFrames
2. **Type safety**: Builder API + pipeline verbs catch errors at query construction time
3. **Performance**: DSL computes centrality on the multilayer graph once, pipelines transform in-memory
4. **Expressiveness**: Each interface does what it's best at (DSL for graph queries, pipelines for data transformations)

**When to use each:**

* **DSL alone**: Simple queries, need graph-specific operations (centrality, grouping, coverage)
* **Pipelines alone**: Non-graph data, pure data transformations
* **Combined (DSL → Pipeline)**: Complex analytical workflows, need both graph metrics and custom computations

See :doc:`build_pipelines` for full pipeline API documentation and additional examples.

Next Steps
----------

Now that you understand the DSL, explore these related resources:

* **DSL Reference** (:doc:`../reference/dsl_reference`): Complete grammar, all operators, full list of built-in measures, and advanced features (EXPLAIN queries, parameter binding, custom operators)

* **Dplyr-Style Pipelines** (:doc:`build_pipelines`): Combine DSL queries with pipeline operations for more complex data transformation workflows. The pipeline API (``nodes()``, ``mutate()``, ``arrange()``) complements the DSL for when you need procedural transformations.

* **Community Detection** (:doc:`run_community_detection`): Use DSL queries to select nodes, then apply community detection algorithms. Pattern: query → detect communities → analyze community structure.

* **Network Dynamics** (:doc:`simulate_dynamics`): Run dynamics simulations on DSL-selected subnetworks. Pattern: query → extract subnetwork → simulate → analyze outcomes.

* **Linting and Validation** (:doc:`../reference/dsl_reference`): The DSL includes a linting subsystem (``py3plex dsl-lint``) that checks queries for errors, performance issues, and suggests optimizations. Use it to validate complex queries.

* **Examples Repository** (:doc:`../examples/index`): Full scripts showing DSL in context, including data loading, query composition, analysis, and visualization.

**Key Takeaways:**

1. **Use the builder API** (``Q``, ``L``) for production code—it's type-safe, refactorable, and IDE-friendly.
2. **Filter early**: Add ``where()`` clauses before ``compute()`` for better performance on large networks.
3. **Embrace pandas**: Use ``.to_pandas()`` for result analysis—it integrates seamlessly with the scientific Python stack.
4. **Layer algebra is powerful**: ``L["a"] + L["b"]`` (union), ``L["a"] & L["b"]`` (intersection) enable sophisticated multilayer queries.
5. **Temporal queries** require timestamped edges/nodes but unlock time-series network analysis.

**Community and Support:**

* Report issues or request features: https://github.com/SkBlaz/py3plex/issues
* Example notebooks: https://github.com/SkBlaz/py3plex/tree/main/examples
* py3plex documentation: https://skblaz.github.io/py3plex/
