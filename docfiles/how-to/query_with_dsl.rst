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
        'COMPUTE degree, betweenness_centrality'
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

Temporal Queries
----------------

The DSL supports temporal filtering for networks with time-stamped edges or nodes. Use ``.at(t)`` for point-in-time snapshots and ``.during(t0, t1)`` for time ranges.

**Prerequisites for temporal queries:**

* Edges or nodes must have temporal attributes:
  
  * **Point-in-time**: ``t`` attribute (e.g., ``{"t": 150.0}``)
  * **Intervals**: ``t_start`` and ``t_end`` attributes (e.g., ``{"t_start": 100.0, "t_end": 200.0}``)

* Time values are typically numeric (timestamps) or ISO date strings

**Temporal semantics:**

* ``at(t)``: Selects entities active at a specific moment
  
  * For point-in-time edges: includes edges where ``t_edge == t``
  * For interval edges: includes edges where ``t`` is in ``[t_start, t_end]``

* ``during(t0, t1)``: Selects entities active during a time window
  
  * For point-in-time edges: includes edges where ``t`` is in ``[t0, t1]``
  * For interval edges: includes edges where the interval **overlaps** ``[t0, t1]``

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

* If nodes have explicit ``t`` attributes, ``.at()`` and ``.during()`` work directly
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
    from py3plex.visualization import multilayer_visualize
    multilayer_visualize(subnetwork, output_file="subnetwork_viz.png")
    
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
    from py3plex.algorithms.community_detection import louvain_communities
    communities = louvain_communities(subnetwork)
    
    # 3. Analyze communities
    print(f"Found {len(set(communities.values()))} communities")
    
    # 4. Visualize or export
    multilayer_visualize(subnetwork, communities=communities, 
                        output_file="core_network_communities.png")

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
