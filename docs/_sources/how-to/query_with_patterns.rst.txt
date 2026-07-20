How to Find Graph Patterns and Motifs with the Pattern Matching API
====================================================================

**Goal:** Use py3plex's Pattern Matching Builder API to find graph motifs, paths, triangles, and complex subgraph patterns in multilayer networks.

.. admonition::  What You'll Learn
   :class: tip

   * How to express graph patterns using the ``Q.pattern()`` builder API
   * How to match edges, paths, triangles, and custom motifs
   * How to apply multilayer-aware constraints (within/between layers)
   * How to filter patterns using node and edge predicates
   * How to extract and analyze pattern match results

.. admonition::  Complete Example
   :class: note

   See the full executable example: :download:`example_pattern_matching.py <../../examples/network_analysis/example_pattern_matching.py>`

**Prerequisites:**

* A loaded ``multi_layer_network`` object (see :doc:`load_and_build_networks`)
* Basic familiarity with the DSL (see :doc:`query_with_dsl`)
* Understanding of graph motifs (edges, paths, triangles, subgraphs)

Why Pattern Matching?
---------------------

Pattern matching allows you to find **specific subgraph structures** in your network. Unlike node/edge queries that return individual elements, pattern matching returns **complete matches** where multiple nodes and edges satisfy structural constraints.

**Common Use Cases:**

* **Motif Detection:** Find triangles, cliques, or other structural patterns
* **Path Analysis:** Discover multi-hop connections between nodes
* **Multilayer Patterns:** Identify cross-layer relationships
* **Complex Queries:** Express "find nodes A, B, C where A connects to B with weight > 0.5, B connects to C, and all are in the social layer"

**Comparison to Basic Queries:**

+-------------------------------------+-------------------------------------------+
| Basic DSL Query                     | Pattern Matching Query                    |
+=====================================+===========================================+
| ``Q.nodes().where(degree__gt=3)``   | ``Q.pattern().node("a").where(...)``      |
| Returns individual nodes            | Returns complete pattern matches          |
+-------------------------------------+-------------------------------------------+
| ``Q.edges().where(weight__gt=0.5)`` | ``Q.pattern().edge("a", "b").where(...)`` |
| Returns individual edges            | Returns node pairs with context           |
+-------------------------------------+-------------------------------------------+

Quick Start: Your First Pattern
-------------------------------

Let's start with a simple example: finding all edges in a network.

**Mental model:** ``Q.pattern()`` binds **variables** (``"a"``, ``"b"``, etc.) to actual node-layer tuples, then checks that every required edge or path between those variables exists. Each match is a complete mapping of variables → node-layer tuples rather than a single node or edge.

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dsl import Q
    
    # Create a simple network
    network = multinet.multi_layer_network(directed=False)
    network.add_nodes([
        {'source': 'Alice', 'type': 'social'},
        {'source': 'Bob', 'type': 'social'},
        {'source': 'Charlie', 'type': 'social'},
    ])
    network.add_edges([
        {'source': 'Alice', 'target': 'Bob', 
         'source_type': 'social', 'target_type': 'social', 'weight': 1.0},
        {'source': 'Bob', 'target': 'Charlie', 
         'source_type': 'social', 'target_type': 'social', 'weight': 2.0},
    ])
    
    # Find all edges (simple pattern)
    pattern = (
        Q.pattern()
         .node("a")              # Define node variable "a"
         .node("b")              # Define node variable "b"
         .edge("a", "b")         # Require edge between a and b
    )
    
    result = pattern.execute(network)
    print(f"Found {result.count} matches")
    print(result.to_pandas())

**Output:**

.. code-block:: text

    Found 4 matches
                     a                  b
    0  (Alice, social)      (Bob, social)
    1    (Bob, social)    (Alice, social)
    2    (Bob, social)  (Charlie, social)
    3  (Charlie, social)    (Bob, social)

Notice that undirected edges produce matches in both directions.

Pattern Components
------------------

Nodes
~~~~~

Define node variables that will be bound to actual nodes during matching:

.. code-block:: python

    # Simple node
    Q.pattern().node("a")
    
    # Node with semantic labels (metadata only)
    Q.pattern().node("a", labels="person")
    
    # Node with predicates
    Q.pattern().node("a").where(degree__gt=3)
    
    # Node with layer constraint
    Q.pattern().node("a").where(layer="social")

**Node Predicates:**

All standard DSL predicates work with pattern nodes:

* ``degree__gt=5`` — degree greater than 5
* ``degree__lt=2`` — degree less than 2
* ``layer="social"`` — node must be in social layer
* Any node attribute: ``age__gt=30``, ``type="user"``, etc.

Edges
~~~~~

Define edges between node variables:

.. code-block:: python

    # Undirected edge
    Q.pattern().edge("a", "b", directed=False)
    
    # Directed edge
    Q.pattern().edge("a", "b", directed=True)
    
    # Edge with predicates
    Q.pattern().edge("a", "b").where(weight__gt=0.5)
    
    # Edge with optional type
    Q.pattern().edge("a", "b", etype="friendship")

**Edge Predicates:**

Filter edges by attributes:

* ``weight__gt=0.5`` — edge weight greater than 0.5
* ``weight__lt=1.0`` — edge weight less than 1.0
* Any edge attribute: ``timestamp__gt=100``, ``color="red"``, etc.

Paths
~~~~~

Sugar method for defining sequential connections:

.. code-block:: python

    # 2-hop path: a → b → c
    Q.pattern().path(["a", "b", "c"])
    
    # Equivalent to:
    Q.pattern().edge("a", "b").edge("b", "c")
    
    # Directed path
    Q.pattern().path(["a", "b", "c"], directed=True)

Paths enforce adjacency in the order you list the variables; with ``directed=True`` the edges must follow that direction.

Triangles
~~~~~~~~~

Sugar method for triangle motifs:

.. code-block:: python

    # Triangle: a-b, b-c, c-a
    Q.pattern().triangle("a", "b", "c")
    
    # Equivalent to:
    Q.pattern().edge("a", "b").edge("b", "c").edge("c", "a")

Multilayer-Aware Patterns
-------------------------

One of the most powerful features is specifying layer constraints on edges.

Within Layer
~~~~~~~~~~~~

Find edges that exist within a single layer:

.. code-block:: python

    # Edges within the social layer
    pattern = (
        Q.pattern()
         .node("a").where(layer="social")
         .node("b").where(layer="social")
         .edge("a", "b")
    )

Between Layers
~~~~~~~~~~~~~~

Find edges that cross between specific layers:

.. code-block:: python

    # Edges between social and work layers
    pattern = (
        Q.pattern()
         .node("a").where(layer="social")
         .node("b").where(layer="work")
         .edge("a", "b").between_layers("social", "work")
    )

Any Layer
~~~~~~~~~

Allow edges in any layer (default behavior; call it explicitly if you want the query to read clearly):

.. code-block:: python

    pattern = Q.pattern().edge("a", "b").any_layer()

Practical Examples
------------------

Example 1: Find Triangles with Weight Constraints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Find triangles where all edges have weight > 1.0.

.. code-block:: python

    pattern = (
        Q.pattern()
         .edge("a", "b").where(weight__gt=1.0)
         .edge("b", "c").where(weight__gt=1.0)
         .edge("c", "a").where(weight__gt=1.0)
         .limit(10)
    )
    
    result = pattern.execute(network)
    triangles = result.to_pandas()
    print(f"Found {len(triangles)} triangles")

If you prefer the ``triangle()`` sugar, expand it as above to attach edge predicates, or apply the weight filter after executing the simpler triangle pattern.

Example 2: Find 2-Hop Paths in Specific Layer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Find all 2-hop paths within the social layer.

.. code-block:: python

    pattern = (
        Q.pattern()
         .node("a").where(layer="social")
         .node("b").where(layer="social")
         .node("c").where(layer="social")
         .path(["a", "b", "c"])
         .returning("a", "b", "c")
         .limit(5)
    )
    
    result = pattern.execute(network)
    df = result.to_pandas()
    
    print(f"Found {result.count} paths")
    print(df)

**Output:**

.. code-block:: text

    Found 5 paths
                       a                b                  c
    0      (Bob, social)  (Alice, social)      (Bob, social)
    1      (Bob, social)  (Alice, social)  (Charlie, social)
    2  (Charlie, social)    (Bob, social)    (Alice, social)
    ...

Example 3: Find High-Degree Nodes with Specific Connections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Find pairs of high-degree nodes (degree > 2) connected by strong edges (weight > 1.5).

.. code-block:: python

    pattern = (
        Q.pattern()
         .node("a").where(layer="social", degree__gt=2)
         .node("b").where(layer="social", degree__gt=2)
         .edge("a", "b").where(weight__gt=1.5)
         .constraint("a != b")  # Ensure different nodes
         .returning("a", "b")
    )
    
    result = pattern.execute(network)
    print(f"Found {result.count} high-degree pairs")
    
    # Get unique nodes involved
    nodes = result.to_nodes(unique=True)
    print(f"Unique nodes: {len(nodes)}")

Example 4: Cross-Layer Hub Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Find nodes that appear in multiple layers and have high degree in each.

.. code-block:: python

    # This requires multiple pattern queries
    # Find nodes in social layer
    social_hubs = (
        Q.pattern()
         .node("a").where(layer="social", degree__gt=3)
         .returning("a")
         .execute(network)
    )
    
    # Find nodes in work layer
    work_hubs = (
        Q.pattern()
         .node("a").where(layer="work", degree__gt=3)
         .returning("a")
         .execute(network)
    )
    
    # Find intersection (nodes in both)
    social_nodes = {n[0] for n in social_hubs.to_nodes(unique=True)}
    work_nodes = {n[0] for n in work_hubs.to_nodes(unique=True)}
    cross_layer_hubs = social_nodes & work_nodes
    
    print(f"Cross-layer hubs: {cross_layer_hubs}")

Working with Results
--------------------

The ``PatternQueryResult`` object provides multiple ways to access matches. Use raw ``rows`` for programmatic iteration, ``to_pandas`` for tabular analysis, and ``to_nodes`` / ``to_edges`` when you want to pass results back into graph algorithms.

Accessing Rows
~~~~~~~~~~~~~~

.. code-block:: python

    result = pattern.execute(network)
    
    # Get all matches as list of dictionaries
    for match in result.rows:
        print(f"Match: {match}")
        # e.g., {'a': ('Alice', 'social'), 'b': ('Bob', 'social')}

``result.count`` is the number of rows returned, equivalent to ``len(result.rows)``.
Each row maps your variable names to concrete ``(node, layer)`` tuples.

Converting to Pandas
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    df = result.to_pandas()
    
    # Now use pandas operations
    print(df.head())
    print(df.describe())
    
    # Export to CSV
    df.to_csv("pattern_matches.csv", index=False)

Column order follows the variables you specified with ``.returning(...)``; if you did not set it, all variables are returned in declaration order.

Extracting Nodes
~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get all matched nodes (as tuples)
    all_nodes = result.to_nodes()
    
    # Get unique nodes only
    unique_nodes = result.to_nodes(unique=True)
    
    # Get nodes for specific variables
    a_nodes = result.to_nodes(vars=["a"], unique=True)

Extracting Edges
~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get all matched edges as tuples
    edges = result.to_edges()
    
    # Each edge is a (source_tuple, target_tuple) pair
    for src, dst in edges:
        print(f"Edge: {src} -> {dst}")

Creating Subgraphs
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Create induced subgraph of matched nodes
    subgraph = result.to_subgraph(network)
    
    # Now use NetworkX operations
    print(f"Subgraph has {subgraph.number_of_nodes()} nodes")
    print(f"Subgraph has {subgraph.number_of_edges()} edges")
    
    # Create one subgraph per match
    subgraphs = result.to_subgraph(network, per_match=True)
    print(f"Created {len(subgraphs)} subgraphs")

Filtering Results
~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Filter matches using a predicate
    filtered = result.filter(lambda match: match["a"][0].startswith("A"))
    
    # Limit number of results
    limited = result.limit(10)

``filter`` and ``limit`` return new ``PatternQueryResult`` objects; they do not modify the original result.

Query Execution Planning
------------------------

Use ``.explain()`` to see how the pattern will be executed:

.. code-block:: python

    pattern = (
        Q.pattern()
         .node("a").where(degree__gt=3)
         .node("b")
         .edge("a", "b")
    )
    
    plan = pattern.explain()
    print(f"Root variable: {plan['root_var']}")
    print(f"Join order: {[step['var'] for step in plan['join_order']]}")
    print(f"Estimated complexity: {plan['estimated_complexity']}")

**Example Output:**

.. code-block:: text

    Root variable: a
    Join order: ['a', 'b']
    Estimated complexity: 1000

The planner chooses ``a`` as the root because it has the most restrictive predicates (``degree__gt=3``), which will generate fewer candidates.
The ``estimated_complexity`` field is a relative heuristic, useful for comparing different patterns rather than predicting exact runtime.

Performance Tips
----------------

1. **Add Predicates Early:** The more selective predicates you add to the root variable, the faster the query.

   .. code-block:: python
   
       # Good: Restrictive predicate on first node
       Q.pattern().node("a").where(degree__gt=10).node("b").edge("a", "b")
       
       # Less efficient: No predicates
       Q.pattern().node("a").node("b").edge("a", "b")

2. **Use Layer Constraints:** Layer filters significantly reduce the search space.

   .. code-block:: python
   
       # Good: Restrict to one layer
       Q.pattern().node("a").where(layer="social")
       
       # Less efficient: Search all layers
       Q.pattern().node("a")

3. **Set Limits:** For large networks, use ``.limit()`` to cap results.

   .. code-block:: python
   
       pattern.limit(100).execute(network)

4. **Use Constraints:** Add ``a != b`` constraints to avoid self-loops if not needed.

   .. code-block:: python
   
       Q.pattern().node("a").node("b").edge("a", "b").constraint("a != b")

5. **Return only needed variables:** Reducing the result width lowers serialization overhead.

   .. code-block:: python
   
       Q.pattern().path(["a", "b", "c"]).returning("a", "c")

Advanced Features
-----------------

Constraints
~~~~~~~~~~~

Global constraints that apply across variables:

.. code-block:: python

    # All-different constraint
    pattern = (
        Q.pattern()
         .node("a")
         .node("b")
         .node("c")
         .edge("a", "b")
         .edge("b", "c")
         .constraint("a != b")
         .constraint("b != c")
         .constraint("a != c")
    )

Returning Specific Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, all variables are returned. You can select specific ones:

.. code-block:: python

    pattern = (
        Q.pattern()
         .node("a")
         .node("b")
         .node("c")
         .path(["a", "b", "c"])
         .returning("a", "c")  # Only return endpoints
    )
    
    result = pattern.execute(network)
    # Result only contains 'a' and 'c' columns

Execution Options
~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Set maximum matches
    result = pattern.execute(network, max_matches=100)
    
    # Set timeout (in seconds)
    result = pattern.execute(network, timeout=10.0)

Comparison with Other Approaches
--------------------------------

Pattern Matching vs. NetworkX
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+----------------------------------------+--------------------------------------+
| NetworkX Approach                      | Pattern Matching Approach            |
+========================================+======================================+
| ``nx.triangles(G)``                    | ``Q.pattern().triangle("a","b","c")``|
| Returns triangle count per node        | Returns actual triangle matches      |
+----------------------------------------+--------------------------------------+
| ``nx.all_simple_paths(G, source, tgt)``| ``Q.pattern().path(["a", "b", "c"])``|
| Enumerates all paths                   | Finds paths with constraints         |
+----------------------------------------+--------------------------------------+
| Manual loops and filtering             | Declarative pattern specification    |
+----------------------------------------+--------------------------------------+

**Advantages of Pattern Matching:**

* Declarative and composable
* Built-in support for multilayer constraints
* Integrated with DSL ecosystem
* Returns results in consistent format (DataFrame, nodes, edges, subgraph)

Pattern Matching vs. DSL Node/Edge Queries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+----------------------------------------+----------------------------------------+
| DSL Node/Edge Query                    | Pattern Matching                       |
+========================================+========================================+
| Returns individual elements            | Returns complete structural matches    |
+----------------------------------------+----------------------------------------+
| ``Q.nodes().where(degree__gt=3)``     | ``Q.pattern().node("a", degree__gt=3)`` |
| Single-element selection               | Part of larger pattern                 |
+----------------------------------------+----------------------------------------+
| No structural relationships            | Explicit edge relationships            |
+----------------------------------------+----------------------------------------+

Use node/edge queries when you need individual elements. Use pattern matching when you need to find subgraph structures.

Limitations and Future Work
---------------------------

Current Limitations (v1)
~~~~~~~~~~~~~~~~~~~~~~~~

* **Fixed-length paths only:** Variable-length paths like ``(a)-[*1..3]-(b)`` not yet supported
* **No optional matching:** All pattern elements must match
* **No UNION patterns:** Cannot express "match pattern A OR pattern B"
* **Limited aggregation:** Aggregation over matches not yet implemented

These features are planned for future versions while maintaining the current clean API.

Best Practices
~~~~~~~~~~~~~~

1. **Start simple:** Begin with small patterns and add complexity incrementally
2. **Test on small data:** Validate pattern logic on toy networks before scaling up
3. **Use explain():** Check execution plans for complex queries
4. **Combine with DSL:** Use pattern matching for structure, DSL for attributes
5. **Document patterns:** Add comments explaining complex pattern logic

Troubleshooting
---------------

Pattern Returns No Matches
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** Your pattern should match but returns 0 results.

**Solutions:**

1. Check layer constraints — are nodes actually in the layers you specified?
2. Verify predicates — are the thresholds too restrictive?
3. Use ``.explain()`` to see the execution plan
4. Test with simpler patterns first
5. Check if your network has the expected structure

.. code-block:: python

    # Debug: Check basic statistics first
    result = Q.nodes().where(layer="social").execute(network)
    print(f"Social layer has {result.count} nodes")
    
    result = Q.edges().where(intralayer=True).execute(network)
    print(f"Network has {result.count} intralayer edges")

Too Many Matches
~~~~~~~~~~~~~~~~

**Problem:** Pattern returns too many results.

**Solutions:**

1. Add more predicates to narrow the search
2. Use ``.limit()`` to cap results
3. Add layer constraints to restrict search space
4. Use ``.constraint("a != b")`` to avoid duplicates

.. code-block:: python

    # Limit results
    pattern.limit(100).execute(network)

Slow Performance
~~~~~~~~~~~~~~~~

**Problem:** Pattern matching takes too long.

**Solutions:**

1. Add selective predicates to the root variable
2. Use layer constraints to reduce search space
3. Consider breaking pattern into smaller sub-patterns
4. Use ``.explain()`` to check estimated complexity
5. Set timeout to avoid runaway queries

.. code-block:: python

    # Set timeout
    result = pattern.execute(network, timeout=30.0)

Related Documentation
---------------------

* :doc:`query_with_dsl` — Basic DSL queries for nodes and edges
* :doc:`query_zoo` — Gallery of DSL query examples
* :doc:`load_and_build_networks` — Creating multilayer networks
* :doc:`compute_statistics` — Computing network metrics

Next Steps
----------

* Explore the :doc:`query_zoo` for more complex examples
* Try combining pattern matching with DSL queries
* Experiment with different motifs (triangles, cliques, paths)
* Build your own domain-specific pattern library

.. tip::
   **Pro Tip:** Pattern matching is most powerful when combined with the rest of the DSL. 
   Use patterns to find structures, then use regular DSL queries to compute metrics on the matches!
