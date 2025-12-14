Appendix E: Extended API and DSL Reference
==========================================

This appendix provides a quick reference for the py3plex API and DSL syntax.

Core API Reference
------------------

Creating Networks
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    
    # Create empty network
    network = multinet.multi_layer_network(
        directed=False,           # True for directed networks
        network_type='multilayer' # or 'multiplex'
    )

Adding Nodes and Edges
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Add edges (nodes created implicitly)
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1.0],
        ['Bob', 'friends', 'Carol', 'friends', 1.0],
    ], input_type="list")
    
    # Add edges with attributes
    network.add_edges([{
        'source': 'Alice',
        'source_type': 'friends',
        'target': 'Bob',
        'target_type': 'friends',
        'weight': 0.8,
        'timestamp': '2023-01-15'
    }])

Loading Networks
~~~~~~~~~~~~~~~~

.. code-block:: python

    # From file
    network.load_network("data.edgelist", input_type="edgelist")
    
    # From NetworkX
    import networkx as nx
    G = nx.karate_club_graph()
    network.load_network_from_networkx(G, layer_name='social')

Basic Operations
~~~~~~~~~~~~~~~~

.. code-block:: python

    # Get network information
    layers = network.get_layers()
    nodes = list(network.get_nodes())
    edges = list(network.get_edges())
    
    # Statistics
    network.basic_stats()
    num_nodes = network.get_number_of_nodes()
    num_edges = network.get_number_of_edges()
    
    # Layer-specific
    nodes_per_layer = network.get_number_of_nodes_per_layer()
    layer_subgraph = network.get_layer_subgraph('friends')

Algorithms API
--------------

Statistics
~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    # Layer density
    density = mls.layer_density(network, 'friends')
    
    # Node activity (fraction of layers a node appears in)
    activity = mls.node_activity(network, 'Alice')
    
    # Layer overlap
    overlap = mls.layer_overlap(network, 'friends', 'colleagues')

Community Detection
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.community_detection import multilayer_louvain
    
    # Detect communities
    communities = multilayer_louvain.best_partition(network.core_network)
    
    # communities = {('Alice', 'friends'): 0, ('Bob', 'friends'): 0, ...}

Centrality
~~~~~~~~~~

.. code-block:: python

    import networkx as nx
    
    # Standard centralities (use NetworkX)
    G = network.core_network
    degree_cent = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G)
    closeness = nx.closeness_centrality(G)
    
    # Explainable centrality (py3plex-specific)
    from py3plex.algorithms.centrality.explain import explain_node_centrality
    
    explanation = explain_node_centrality(
        network,
        node='Alice',
        measure='degree'
    )
    # Returns: {'score': 4, 'layer_breakdown': {...}, ...}

Dynamics
~~~~~~~~

.. code-block:: python

    from py3plex.dynamics.models import SIRDynamics, SISDynamics
    
    # Configure SIR model
    sir = SIRDynamics(
        network,
        beta=0.3,      # Infection rate
        gamma=0.1,     # Recovery rate
        initial_infected={'Alice': 0}  # Initial conditions
    )
    
    # Set seed for reproducibility
    sir.set_seed(42)
    
    # Run simulation
    results = sir.run(steps=100)
    
    # Extract measures
    prevalence = results.get_measure('prevalence')
    recovered = results.get_measure('state_counts')[2]  # State 2 = recovered

DSL Quick Reference
-------------------

Builder API (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.dsl import Q, L, Param
    
    # Basic query
    result = Q.nodes().execute(network)
    
    # Filter by layer
    result = Q.nodes().from_layers(L["social"]).execute(network)
    
    # Filter by condition
    result = Q.nodes().where(degree__gt=5).execute(network)
    
    # Multiple conditions
    result = Q.nodes().where(layer="social", degree__gt=3).execute(network)
    
    # Layer algebra
    result = Q.nodes().from_layers(L["social"] + L["work"]).execute(network)      # Union
    result = Q.nodes().from_layers(L["social"] - L["bots"]).execute(network)     # Difference
    result = Q.nodes().from_layers(L["social"] & L["work"]).execute(network)     # Intersection
    
    # Compute measures
    result = Q.nodes().compute("degree", "betweenness_centrality").execute(network)
    
    # Order and limit
    result = (
        Q.nodes()
         .compute("degree")
         .order_by("-degree")
         .limit(10)
         .execute(network)
    )
    
    # Export results
    (
        Q.nodes()
         .compute("degree")
         .export_csv("output.csv")
         .execute(network)
    )
    
    # Parameterized queries
    result = (
        Q.nodes()
         .where(degree__gt=Param('min_degree'))
         .execute(network, params={'min_degree': 5})
    )

String DSL Syntax
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.dsl import execute_query
    
    # Basic syntax: SELECT target WHERE conditions COMPUTE measures
    
    # Select all nodes
    execute_query(network, 'SELECT nodes')
    
    # Filter by layer
    execute_query(network, 'SELECT nodes WHERE layer="social"')
    
    # Filter by degree
    execute_query(network, 'SELECT nodes WHERE degree > 5')
    
    # Multiple conditions
    execute_query(network, 'SELECT nodes WHERE layer="social" AND degree > 3')
    
    # Compute measures
    execute_query(network, 'SELECT nodes COMPUTE betweenness_centrality')
    
    # Combined
    execute_query(network,
        'SELECT nodes WHERE layer="social" AND degree > 3 '
        'COMPUTE degree betweenness_centrality'
    )

DSL Operators
~~~~~~~~~~~~~

**Comparison operators:**

* ``=`` — Equal to
* ``!=`` — Not equal to
* ``>`` — Greater than
* ``<`` — Less than
* ``>=`` — Greater than or equal
* ``<=`` — Less than or equal

**Logical operators:**

* ``AND`` — Logical AND
* ``OR`` — Logical OR
* ``NOT`` — Logical NOT

**Filter modifiers (Builder API):**

* ``field=value`` — Equal
* ``field__ne=value`` — Not equal
* ``field__gt=value`` — Greater than
* ``field__gte=value`` — Greater or equal
* ``field__lt=value`` — Less than
* ``field__lte=value`` — Less or equal

Available Measures
~~~~~~~~~~~~~~~~~~

* ``degree`` — Node degree
* ``degree_centrality`` — Normalized degree
* ``betweenness_centrality`` — Betweenness
* ``closeness_centrality`` — Closeness
* ``eigenvector_centrality`` — Eigenvector
* ``pagerank`` — PageRank
* ``clustering`` — Clustering coefficient

Working with Results
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    result = Q.nodes().compute("degree").execute(network)
    
    # Iteration
    for node in result:
        print(node)
    
    # Count
    print(f"Found {result.count} nodes")
    
    # Measures
    degrees = result.measures['degree']
    for node, degree in degrees.items():
        print(f"{node}: {degree}")
    
    # To pandas
    df = result.to_pandas()

I/O API
-------

Modern I/O System
~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.io import read, write, MultiLayerGraph
    
    # Read (auto-detects format from extension)
    graph = read('network.json')
    graph = read('network.arrow')
    graph = read('network.parquet')
    
    # Write
    write(network, 'output.json')
    write(network, 'output.arrow')
    write(network, 'output.parquet')
    
    # Specify format explicitly
    graph = read('file.dat', format='json')
    write(network, 'file.dat', format='arrow')

Supported Formats
~~~~~~~~~~~~~~~~~

* **JSON** — ``.json`` — Human-readable
* **JSONL** — ``.jsonl`` — Streaming
* **CSV** — ``.csv`` — Spreadsheet-compatible
* **Arrow** — ``.arrow`` — High-performance
* **Parquet** — ``.parquet`` — Compressed

Visualization API
-----------------

Basic Visualization
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default
    
    # Simple visualization
    draw_multilayer_default(network.get_layers(), display=True)
    
    # With layout options
    draw_multilayer_default(
        network.get_layers(),
        display=True,
        layout='force_directed',
        node_size=300,
        edge_width=2
    )

Matrix Visualization
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Visualize supra-adjacency matrix
    network.visualize_matrix({"display": True})

Command-Line Interface
----------------------

Basic Usage
~~~~~~~~~~~

.. code-block:: bash

    # Show version
    python -m py3plex --version
    
    # Run self-test
    python -m py3plex selftest
    
    # Analyze network
    python -m py3plex analyze network.edgelist
    
    # Community detection
    python -m py3plex communities network.edgelist --algorithm louvain

Summary
-------

This appendix provided quick references for:

* Core API (creating networks, adding nodes/edges)
* Algorithms API (statistics, communities, centrality, dynamics)
* DSL syntax (both Builder API and string syntax)
* I/O API (reading/writing various formats)
* Visualization API
* Command-line interface

**For detailed documentation:**

* Main text chapters for concepts and examples
* Appendix A for repository layout
* Appendix D for error handling
* Online API docs: https://skblaz.github.io/py3plex/

