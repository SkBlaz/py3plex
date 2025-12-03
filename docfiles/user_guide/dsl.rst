SQL-like DSL for Multilayer Networks
=====================================

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

Py3plex provides a Domain-Specific Language (DSL) for querying and analyzing multilayer networks using SQL-like syntax. This intuitive interface allows users to filter nodes and edges, compute network measures, and perform complex analyses with simple, readable queries.

The DSL enables you to express complex network queries in a natural, SQL-like language without writing verbose code. For example, instead of manually iterating through nodes and checking conditions, you can write::

    execute_query(network, 'SELECT nodes WHERE layer="social" AND degree > 5')

The DSL is particularly useful for:

- **Interactive network exploration**: Quickly test hypotheses and explore network structure
- **Rapid prototyping**: Build analysis workflows without extensive coding
- **Educational purposes**: Learn network concepts with intuitive queries
- **Production pipelines**: Create maintainable, self-documenting analysis code

.. note::

   **Flagship Example Available!**
   
   For a comprehensive demonstration of DSL capabilities including centrality analysis,
   statistics, and community detection, see the flagship example::
   
       python examples/network_analysis/example_dsl_flagship.py
   
   This example showcases the full power of the DSL in a complete analysis workflow.

Basic Syntax
------------

The DSL follows a SQL-inspired syntax::

    SELECT target WHERE conditions COMPUTE measures

Where:

- **target**: Either ``nodes`` or ``edges``
- **conditions**: Filtering criteria (optional)
- **measures**: Network measures to compute (optional)

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
    SELECT edges     # Select edges (edge queries in development)

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

The DSL raises specific exceptions for different error types::

    from py3plex.dsl import execute_query, DSLSyntaxError, DSLExecutionError
    
    try:
        result = execute_query(network, 'SELECT nodes WHERE invalid_condition')
    except DSLSyntaxError as e:
        print(f"Syntax error: {e}")
    except DSLExecutionError as e:
        print(f"Execution error: {e}")

Common syntax errors:

- Missing SELECT keyword
- Invalid target (not 'nodes' or 'edges')
- Malformed conditions
- Unknown operators
- Invalid measure names

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

Complete examples are available in the repository:

- ``examples/network_analysis/example_dsl_flagship.py`` - **Flagship example**: Complete DSL-powered workflow with centralities, statistics, and community detection
- ``examples/network_analysis/example_dsl_queries.py`` - Basic DSL usage with detailed output
- ``examples/network_analysis/example_dsl_advanced.py`` - Advanced queries and transportation network analysis

Run these examples::

    cd examples/network_analysis
    python example_dsl_flagship.py   # Comprehensive flagship example
    python example_dsl_queries.py
    python example_dsl_advanced.py

The flagship example (``example_dsl_flagship.py``) demonstrates:

- DSL query syntax with all operators
- Centrality analysis (betweenness, closeness, degree)
- Cross-layer centrality comparison
- Multilayer centrality with versatility scores
- Statistical report generation
- Community detection with Louvain algorithm
- Convenience functions for common operations
- First-class method usage on network objects

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

1. **Start simple**: Begin with basic queries and add complexity incrementally
2. **Validate data**: Ensure network is properly constructed before querying
3. **Check results**: Inspect result counts and samples before processing
4. **Use convenience functions**: For common operations, use provided shortcuts
5. **Handle errors**: Wrap queries in try-except for robust code
6. **Performance**: For large networks, filter by layer first to reduce computation

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

- :doc:`../basic_usage` - Network construction basics
- :doc:`../multilayer_concepts` - Understanding multilayer networks
- :doc:`../algorithm_guide` - Network analysis algorithms
- :doc:`recipes_and_workflows` - Common analysis patterns

See Also
--------

- NetworkX documentation for centrality measures
- Examples directory for complete use cases
- API documentation for detailed function signatures
