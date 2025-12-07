How to Query Multilayer Graphs with the SQL-like DSL
====================================================

**Goal:** Use the SQL-inspired DSL to query and analyze multilayer networks.

**Prerequisites:** A loaded network (see :doc:`load_and_build_networks`). For complete reference, see :doc:`../reference/dsl_reference`.

String Syntax (Quick and Readable)
-----------------------------------

Basic SELECT
~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.dsl import execute_query
    
    network = multinet.multi_layer_network()
    network.load_network("data.multiedgelist", input_type="multiedgelist")
    
    # Get all nodes
    result = execute_query(network, 'SELECT nodes')
    print(f"Found {len(result)} nodes")

Filter by Layer
~~~~~~~~~~~~~~~

.. code-block:: python

    # Get nodes in specific layer
    result = execute_query(
        network,
        'SELECT nodes WHERE layer="friends"'
    )

Filter by Property
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get high-degree nodes
    result = execute_query(
        network,
        'SELECT nodes WHERE degree > 5'
    )
    
    # Multiple conditions
    result = execute_query(
        network,
        'SELECT nodes WHERE layer="work" AND degree > 3'
    )

Compute Statistics
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Compute metrics
    result = execute_query(
        network,
        'SELECT nodes WHERE layer="social" '
        'COMPUTE degree COMPUTE betweenness_centrality'
    )
    
    # Convert to DataFrame
    df = result.to_pandas()
    print(df.head())

Builder API (Type-Safe)
-----------------------

Recommended for production code—provides IDE autocompletion and type checking.

Basic Queries
~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.dsl import Q, L
    
    # Get all nodes
    result = Q.nodes().execute(network)
    
    # Get nodes from specific layer
    result = (
        Q.nodes()
         .from_layers(L["friends"])
         .execute(network)
    )

Filtering
~~~~~~~~~

.. code-block:: python

    # Filter by property
    result = (
        Q.nodes()
         .where(degree__gt=5)
         .execute(network)
    )
    
    # Multiple conditions
    result = (
        Q.nodes()
         .from_layers(L["work"])
         .where(degree__gt=3, layer_count__gte=2)
         .execute(network)
    )

Supported operators:

* ``__gt``: greater than
* ``__gte``: greater than or equal
* ``__lt``: less than
* ``__lte``: less than or equal
* ``__eq``: equal
* ``__ne``: not equal

Computing Metrics
~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Compute multiple metrics
    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality", "clustering")
         .execute(network)
    )

Sorting and Limiting
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get top 10 by degree
    result = (
        Q.nodes()
         .compute("degree")
         .order_by("-degree")  # - for descending
         .limit(10)
         .execute(network)
    )

Working with Results
--------------------

Access as Dictionary
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    result = Q.nodes().compute("degree").execute(network)
    
    # Iterate
    for node, data in result.items():
        print(f"{node}: degree={data['degree']}")

Convert to Pandas
~~~~~~~~~~~~~~~~~

.. code-block:: python

    df = result.to_pandas()
    print(df.describe())

Filter Results
~~~~~~~~~~~~~~

.. code-block:: python

    # Get only nodes with degree > 5
    high_degree = {
        node: data
        for node, data in result.items()
        if data['degree'] > 5
    }

Advanced Queries
----------------

Multiple Layer Selection
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Combine layers
    result = (
        Q.nodes()
         .from_layers(L["friends"] + L["work"])
         .execute(network)
    )

Layer Intersection
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Nodes present in BOTH layers
    result = (
        Q.nodes()
         .from_layers(L["friends"] & L["work"])
         .execute(network)
    )

Query Edges
~~~~~~~~~~~

.. code-block:: python

    # Select edges
    edges = (
        Q.edges()
         .from_layers(L["social"])
         .where(weight__gt=0.5)
         .execute(network)
    )

Temporal Queries
----------------

Filter by Time
~~~~~~~~~~~~~~

.. code-block:: python

    # Nodes active at specific time
    result = (
        Q.nodes()
         .at("2024-01-15T10:00:00")
         .execute(network)
    )

Time Range
~~~~~~~~~~

.. code-block:: python

    # Nodes active during period
    result = (
        Q.nodes()
         .during("2024-01-01", "2024-01-31")
         .execute(network)
    )

See :doc:`../reference/dsl_reference` for complete temporal query syntax.

Common Patterns
---------------

Pattern: Find Influential Nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # High degree + high betweenness
    result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .where(degree__gt=10)
         .order_by("-betweenness_centrality")
         .limit(20)
         .execute(network)
    )

Pattern: Compare Layer Activity
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    layers = network.get_layers()
    
    for layer in layers:
        result = (
            Q.nodes()
             .from_layers(L[layer])
             .compute("degree")
             .execute(network)
        )
        df = result.to_pandas()
        print(f"{layer}: {len(df)} nodes, avg degree={df['degree'].mean():.2f}")

Pattern: Export Subnetwork
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Extract high-activity nodes
    active_nodes = (
        Q.nodes()
         .where(layer_count__gt=2)
         .execute(network)
    )
    
    # Create subnetwork
    subnetwork = network.subgraph(active_nodes.keys())

Next Steps
----------

* **Complete DSL reference:** :doc:`../reference/dsl_reference`
* **Build analysis pipelines:** :doc:`build_pipelines`
* **See examples:** :doc:`../examples/index`
