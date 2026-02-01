Dplyr-style Chainable Graph Operations
=======================================

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

Py3plex provides a dplyr-style, fluent method-chaining interface for working with nodes
and edges in multilayer networks. This API is inspired by R's dplyr package and provides
verbs like ``filter``, ``select``, ``mutate``, ``arrange``, ``group_by``, and ``summarise``.

The API enables you to express complex data manipulations as readable chains of operations::

    from py3plex.graph_ops import nodes, edges
    import numpy as np

    df = (
        nodes(multinet, layers=["ppi"])
        .filter(lambda n: n["degree"] > 10)
        .mutate(k=lambda n: n["degree"] / (n["weight"] + 1))
        .group_by("layer")
        .summarise(avg_degree=("degree", np.mean))
        .to_pandas()
    )

The graph_ops module is particularly useful for:

- **Fluent data manipulation**: Chain operations naturally without intermediate variables
- **Aggregation and summarization**: Group data and compute statistics
- **Integration with pandas**: Export results directly to DataFrames
- **Filtering and transformation**: Apply complex logic to nodes and edges

Key Concepts
------------

NodeFrame and EdgeFrame
~~~~~~~~~~~~~~~~~~~~~~~

The two main "frame" types wrap collections of nodes or edges:

- **NodeFrame**: A chainable view over a collection of nodes
- **EdgeFrame**: A chainable view over a collection of edges

Both wrap:

- A reference to the underlying py3plex graph object (multinet)
- A current selection of nodes or edges (as a list of dicts)

All verbs return a new NodeFrame/EdgeFrame, enabling method chaining.

Top-level Helpers
~~~~~~~~~~~~~~~~~

Use the ``nodes()`` and ``edges()`` functions to create frames::

    from py3plex.graph_ops import nodes, edges
    
    # Get all nodes from the network
    node_frame = nodes(multinet)
    
    # Get nodes from specific layers
    node_frame = nodes(multinet, layers=["layer1", "layer2"])
    
    # Get all edges
    edge_frame = edges(multinet)
    
    # Get edges from specific layers
    edge_frame = edges(multinet, layers=["ppi"])

Quick Start Example
-------------------

Here's a complete working example::

    from py3plex.core import multinet
    from py3plex.graph_ops import nodes, edges
    import numpy as np
    
    # Create a multilayer network
    network = multinet.multi_layer_network(directed=False)
    
    # Add nodes
    network.add_nodes([
        {'source': 'A', 'type': 'layer1'},
        {'source': 'B', 'type': 'layer1'},
        {'source': 'C', 'type': 'layer1'},
        {'source': 'D', 'type': 'layer1'},
        {'source': 'A', 'type': 'layer2'},
        {'source': 'B', 'type': 'layer2'},
    ])
    
    # Add edges
    network.add_edges([
        {'source': 'A', 'target': 'B', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 1.0},
        {'source': 'B', 'target': 'C', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 2.0},
        {'source': 'C', 'target': 'D', 'source_type': 'layer1', 'target_type': 'layer1', 'weight': 3.0},
        {'source': 'A', 'target': 'B', 'source_type': 'layer2', 'target_type': 'layer2', 'weight': 0.5},
    ])
    
    # Example 1: Filter + mutate + to_pandas
    df = (
        nodes(network, layers=["layer1"])
        .filter(lambda n: n["degree"] > 1)
        .mutate(k=lambda n: n["degree"] / (n.get("weight", 1) + 1))
        .to_pandas()
    )
    print(df)
    
    # Example 2: Grouping and summarising
    df_summary = (
        nodes(network)
        .group_by("layer")
        .summarise(
            avg_degree=("degree", np.mean),
            n=("id", len),
        )
        .arrange("avg_degree", reverse=True)
        .to_pandas()
    )
    print(df_summary)
    
    # Example 3: Edges
    df_edges = (
        edges(network, layers=["layer1"])
        .filter(lambda e: e.get("weight", 0) > 1.5)
        .head(10)
        .to_pandas()
    )
    print(df_edges)

Verb Reference
--------------

Filter
~~~~~~

Filter nodes/edges using a predicate function::

    # Using a lambda predicate
    result = nodes(network).filter(lambda n: n["degree"] > 5)
    
    # Filter edges by weight
    result = edges(network).filter(lambda e: e.get("weight", 0) > 0.8)

Or use expression strings for simple conditions::

    result = nodes(network).filter_expr("degree > 10 and layer == 'ppi'")

**Signature:**

.. code-block:: python

    def filter(self, predicate: Callable[[dict], bool]) -> "NodeFrame": ...
    def filter_expr(self, expr: str) -> "NodeFrame": ...

Select
~~~~~~

Keep only the specified attributes::

    result = nodes(network).select("id", "layer", "degree")

**Signature:**

.. code-block:: python

    def select(self, *fields: str) -> "NodeFrame": ...

If no fields are passed, behaves as a no-op.

Mutate
~~~~~~

Compute new attributes from existing values::

    import math
    
    result = nodes(network).mutate(
        k=lambda n: n["degree"] / (n.get("weight", 1) + 1),
        log_degree=lambda n: math.log1p(n["degree"]),
    )

**Signature:**

.. code-block:: python

    def mutate(self, **new_fields: Callable[[dict], Any]) -> "NodeFrame": ...

Arrange (Sort)
~~~~~~~~~~~~~~

Sort nodes/edges by an attribute or custom key::

    # Sort by attribute name
    result = nodes(network).arrange("degree", reverse=True)
    
    # Sort using a custom key function
    result = nodes(network).arrange(lambda n: -n["degree"])

**Signature:**

.. code-block:: python

    def arrange(self, key: Union[str, Callable[[dict], Any]], reverse: bool = False) -> "NodeFrame": ...

Head (Take)
~~~~~~~~~~~

Keep only the first n rows::

    result = nodes(network).head(10)  # First 10 nodes

**Signature:**

.. code-block:: python

    def head(self, n: int = 5) -> "NodeFrame": ...

Group By + Summarise
~~~~~~~~~~~~~~~~~~~~

Group data and compute aggregations::

    import numpy as np
    
    result = (
        nodes(network)
        .group_by("layer")
        .summarise(
            avg_degree=("degree", np.mean),
            n=("id", len),
        )
    )

**Signatures:**

.. code-block:: python

    def group_by(self, *fields: str) -> "GroupedNodeFrame": ...
    
    def summarise(self, **aggregations: tuple[str, Callable[[list[Any]], Any]]) -> "NodeFrame": ...

The aggregations are tuples of ``(field_name, aggregation_function)``.

Export Methods
--------------

to_pandas
~~~~~~~~~

Convert the current selection to a pandas DataFrame::

    df = nodes(network).to_pandas()
    
    # Chain with other operations
    df = (
        nodes(network)
        .filter(lambda n: n["degree"] > 5)
        .select("id", "layer", "degree")
        .to_pandas()
    )

**Signature:**

.. code-block:: python

    def to_pandas(self) -> pandas.DataFrame: ...

to_subgraph
~~~~~~~~~~~

Build a py3plex subgraph containing only the selected nodes::

    subgraph = (
        nodes(network)
        .filter(lambda n: n["layer"] == "ppi")
        .to_subgraph()
    )

**Signature:**

.. code-block:: python

    def to_subgraph(self) -> Any: ...

Mapping to dplyr Concepts
-------------------------

The following table shows the correspondence between dplyr verbs and graph_ops methods:

+-------------------+------------------------------------------+
| dplyr Verb        | graph_ops Method                         |
+===================+==========================================+
| ``dplyr::filter`` | ``NodeFrame.filter / EdgeFrame.filter``  |
+-------------------+------------------------------------------+
| ``dplyr::select`` | ``NodeFrame.select / EdgeFrame.select``  |
+-------------------+------------------------------------------+
| ``dplyr::mutate`` | ``NodeFrame.mutate / EdgeFrame.mutate``  |
+-------------------+------------------------------------------+
| ``dplyr::arrange``| ``NodeFrame.arrange / EdgeFrame.arrange``|
+-------------------+------------------------------------------+
| ``dplyr::head``   | ``NodeFrame.head / EdgeFrame.head``      |
+-------------------+------------------------------------------+
| ``dplyr::group_by``| ``NodeFrame.group_by``                  |
+-------------------+------------------------------------------+
| ``dplyr::summarise``| ``GroupedNodeFrame.summarise``         |
+-------------------+------------------------------------------+

.. note::

    There is no direct equivalent of joins or relational joins yet. The design
    is open for future extensions like joining on node ID, layer, etc.

Complete Examples
-----------------

Example 1: Hub Identification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Find and analyze hub nodes across layers::

    from py3plex.core import multinet
    from py3plex.graph_ops import nodes
    import numpy as np
    
    network = multinet.multi_layer_network(directed=False)
    # ... add nodes and edges ...
    
    # Find high-degree nodes (hubs) in each layer
    hub_summary = (
        nodes(network)
        .filter(lambda n: n["degree"] >= 5)  # Only high-degree nodes
        .group_by("layer")
        .summarise(
            hub_count=("id", len),
            avg_hub_degree=("degree", np.mean),
            max_degree=("degree", max),
        )
        .arrange("hub_count", reverse=True)
        .to_pandas()
    )
    print(hub_summary)

Example 2: Layer Comparison
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compare network properties across different layers::

    from py3plex.graph_ops import nodes
    import numpy as np
    
    # Get per-layer statistics
    layer_stats = (
        nodes(network)
        .group_by("layer")
        .summarise(
            node_count=("id", len),
            avg_degree=("degree", np.mean),
            total_degree=("degree", sum),
        )
        .to_pandas()
    )
    print(layer_stats)

Example 3: Edge Filtering and Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Filter edges and compute statistics::

    from py3plex.graph_ops import edges
    
    # Find high-weight edges
    high_weight_edges = (
        edges(network, layers=["ppi", "coexpr"])
        .filter(lambda e: e.get("weight", 0) > 0.8)
        .mutate(
            is_intra_layer=lambda e: e["source_layer"] == e["target_layer"],
            weight_class=lambda e: "high" if e.get("weight", 0) > 0.9 else "medium",
        )
        .arrange("weight", reverse=True)
        .head(100)
        .to_pandas()
    )
    print(high_weight_edges)

Example 4: Subgraph Extraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a subgraph from filtered nodes::

    from py3plex.graph_ops import nodes
    
    # Extract a subgraph of high-degree nodes in layer1
    subgraph = (
        nodes(network)
        .filter(lambda n: n["layer"] == "layer1")
        .filter(lambda n: n["degree"] >= 3)
        .to_subgraph()
    )
    
    # Analyze the subgraph
    print(f"Subgraph has {len(list(subgraph.get_nodes()))} nodes")

API Reference
-------------

nodes()
~~~~~~~

.. code-block:: python

    def nodes(multinet: Any, layers: Optional[List[str]] = None) -> NodeFrame:
        """Create a NodeFrame from a py3plex multi_layer_network.
        
        Args:
            multinet: py3plex multi_layer_network object
            layers: Optional list of layers to restrict to
            
        Returns:
            A NodeFrame wrapping the network's nodes
        """

edges()
~~~~~~~

.. code-block:: python

    def edges(multinet: Any, layers: Optional[List[str]] = None) -> EdgeFrame:
        """Create an EdgeFrame from a py3plex multi_layer_network.
        
        Args:
            multinet: py3plex multi_layer_network object
            layers: Optional list of layers to restrict to
            
        Returns:
            An EdgeFrame wrapping the network's edges
        """

NodeFrame
~~~~~~~~~

.. code-block:: python

    @dataclass
    class NodeFrame:
        """A chainable view over a collection of nodes.
        
        Attributes:
            multinet: Reference to the underlying py3plex multi_layer_network
            data: Current selection of nodes as a list of dicts
        """
        
        def filter(self, predicate: Callable[[dict], bool]) -> "NodeFrame": ...
        def filter_expr(self, expr: str) -> "NodeFrame": ...
        def select(self, *fields: str) -> "NodeFrame": ...
        def mutate(self, **new_fields: Callable[[dict], Any]) -> "NodeFrame": ...
        def arrange(self, key: Union[str, Callable], reverse: bool = False) -> "NodeFrame": ...
        def head(self, n: int = 5) -> "NodeFrame": ...
        def group_by(self, *fields: str) -> "GroupedNodeFrame": ...
        def to_pandas(self) -> pandas.DataFrame: ...
        def to_subgraph(self) -> Any: ...

EdgeFrame
~~~~~~~~~

.. code-block:: python

    @dataclass
    class EdgeFrame:
        """A chainable view over a collection of edges.
        
        Attributes:
            multinet: Reference to the underlying py3plex multi_layer_network
            data: Current selection of edges as a list of dicts
        """
        
        def filter(self, predicate: Callable[[dict], bool]) -> "EdgeFrame": ...
        def filter_expr(self, expr: str) -> "EdgeFrame": ...
        def select(self, *fields: str) -> "EdgeFrame": ...
        def mutate(self, **new_fields: Callable[[dict], Any]) -> "EdgeFrame": ...
        def arrange(self, key: Union[str, Callable], reverse: bool = False) -> "EdgeFrame": ...
        def head(self, n: int = 5) -> "EdgeFrame": ...
        def group_by(self, *fields: str) -> "GroupedEdgeFrame": ...
        def to_pandas(self) -> pandas.DataFrame: ...

GroupedNodeFrame
~~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class GroupedNodeFrame:
        """A grouped view of nodes for aggregation operations.
        
        Attributes:
            parent: The parent NodeFrame from which this was created
            group_fields: Tuple of field names to group by
        """
        
        def summarise(self, **aggregations: tuple) -> "NodeFrame": ...
        def summarize(self, **aggregations: tuple) -> "NodeFrame": ...  # Alias

Best Practices
--------------

1. **Start simple**: Begin with basic filters and add complexity incrementally
2. **Use method chaining**: Chain operations for readable, fluent code
3. **Handle missing values**: Use ``.get()`` for optional attributes::

       frame.mutate(x=lambda n: n.get("weight", 1) * 2)

4. **Export early for debugging**: Use ``.to_pandas()`` to inspect intermediate results
5. **Filter before grouping**: Reduce data volume before aggregation for better performance
6. **Name aggregations clearly**: Use descriptive names in ``summarise()``

Comparison with DSL
-------------------

The graph_ops module complements the existing SQL-like DSL:

.. list-table:: DSL vs graph_ops Comparison
   :header-rows: 1
   :widths: 20 40 40

   * - Feature
     - DSL (Builder API / String)
     - graph_ops
   * - **Syntax**
     - SQL-like strings or Builder API (Q, L)
     - Python method chaining
   * - **Filtering**
     - WHERE clauses / ``.where()`` method
     - ``.filter()`` with lambdas
   * - **Aggregation**
     - COMPUTE measures / ``.compute()``
     - ``.group_by().summarise()``
   * - **Custom logic**
     - Limited to predefined measures
     - Full Python expressiveness
   * - **Type safety**
     - Builder API: Full type hints; String DSL: None
     - Full with type hints
   * - **Best for**
     - Network-specific queries, multilayer operations
     - Complex transformations, data pipelines

When to Use Which
~~~~~~~~~~~~~~~~~

**Use DSL (Builder API) when:**

- You need network-specific queries (layer algebra, centrality, etc.)
- You want type-safe, IDE-friendly code (use ``Q.nodes()``, ``L[]``)
- You're doing filtering and centrality computation with multilayer semantics
- You want autocompletion and inline documentation
- You need to quickly prototype network analysis

**Use String DSL when:**

- You need quick, exploratory queries in notebooks or REPL
- You prefer SQL-like syntax for familiar, readable one-liners
- You're migrating legacy code (maintained for backward compatibility)

**Use graph_ops when:**

- You need complex data transformations with custom logic
- You want full type hints and IDE autocompletion
- You're building reusable analysis pipelines
- You need grouping and aggregation operations
- You're integrating with pandas workflows

See Also
--------

- :doc:`dsl` - SQL-like DSL for network queries (Builder API recommended, string DSL available for backward compatibility)
- :doc:`networks` - Working with multilayer networks
- :doc:`statistics` - Network statistics and measures
