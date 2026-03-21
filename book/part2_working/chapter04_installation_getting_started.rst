.. _installation-chapter:

Installation and Getting Started
===========================================

This chapter covers installing py3plex and running your first multilayer network analysis. It presents one recommended path first, then lists alternatives for contributors and containerized workflows.

.. admonition:: DSL Quick Start
   :class: dsl-example

   After installation, try the DSL for instant network exploration:

   .. code-block:: python

       from py3plex.core import multinet
       from py3plex.dsl import Q, L

       # Create a simple network
       network = multinet.multi_layer_network()
       network.add_edges([
           ['Alice', 'friends', 'Bob', 'friends', 1],
           ['Bob', 'friends', 'Carol', 'friends', 1],
       ], input_type="list")

       # Query it with DSL
       result = (
           Q.nodes()
            .compute("degree")
            .order_by("-degree")
            .execute(network)
       )
       print(result.to_pandas())

   DSL makes network analysis intuitive from day one!

Recommended Installation Path
-----------------------------

For most users, installation is straightforward:

.. code-block:: bash

    pip install py3plex

This installs py3plex with core dependencies (NetworkX, NumPy, SciPy, pandas, matplotlib).

**Environment recommendation:** create a fresh virtual environment before installing.

.. code-block:: bash

    python3 -m venv py3plex-env
    source py3plex-env/bin/activate  # Linux/macOS
    # py3plex-env\Scripts\activate   # Windows

**Using uv (optional):**

`uv <https://github.com/astral-sh/uv>`_ is a fast Python package installer and resolver. To use uv:

.. code-block:: bash

    # Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Install py3plex with uv
    uv pip install py3plex

Verification Command
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import py3plex
    print(py3plex.__version__)  # Should print 1.x

System Requirements
-------------------

**Python:** 3.8 or higher (tested on 3.8, 3.9, 3.10, 3.11, 3.12)

**Platforms:** Linux, macOS, Windows

**Core dependencies** (installed automatically):

* NetworkX (≥2.8) — Graph data structures and algorithms
* NumPy (≥1.22) — Numerical computing and array operations
* SciPy (≥1.8) — Sparse matrices and scientific computing
* pandas (≥1.4) — Data manipulation and analysis
* matplotlib (≥3.5) — Visualization and plotting
* scikit-learn (≥1.0) — Machine learning utilities

Hello Multilayer Network
-------------------------

Create and analyze a multilayer network in 30 seconds:

.. code-block:: python

    from py3plex.core import multinet
    
    # Create a multilayer network
    net = multinet.multi_layer_network()
    
    # Add nodes and edges
    net.add_nodes([
        {'source': 'Alice', 'type': 'friends'},
        {'source': 'Bob', 'type': 'friends'},
        {'source': 'Alice', 'type': 'work'},
    ])
    
    net.add_edges([
        {'source': 'Alice', 'target': 'Bob', 
         'source_type': 'friends', 'target_type': 'friends'},
        {'source': 'Alice', 'target': 'Charlie', 
         'source_type': 'work', 'target_type': 'work'},
    ])
    
    # Display statistics
    net.basic_stats()

**See also:** ``examples/getting_started/tutorial_10min.py`` for a complete tutorial.

**Output:**

.. code-block:: text

    Number of nodes: 6
    Number of edges: 4
    Number of unique nodes (as node-layer tuples): 6
    Number of unique node IDs (across all layers): 4
    Nodes per layer:
      Layer 'friends': 3 nodes
      Layer 'colleagues': 3 nodes

**Key insight:** The network has 6 node-layer pairs (Alice-friends, Alice-colleagues, Bob-friends, Bob-colleagues, Carol-friends, Dave-colleagues) but only 4 unique people.

Visualize the Network
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.visualization.multilayer import draw_multilayer_default
    
    # Simple visualization
    draw_multilayer_default(network.get_layers(), display=True)

This creates a force-directed layout with nodes colored by layer.

Basic Analysis
~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    # Layer density (how connected is each layer?)
    print(f"Friends density: {mls.layer_density(network, 'friends'):.3f}")
    # Output: Friends density: 0.667 (2 of 3 possible edges exist)
    
    # Node activity (fraction of layers a node appears in)
    print(f"Bob's activity: {mls.node_activity(network, 'Bob'):.3f}")
    # Output: Bob's activity: 1.000 (appears in both layers)

Query with DSL
~~~~~~~~~~~~~~

Use SQL-like queries to explore the network:

.. code-block:: python

    from py3plex.dsl import Q, L
    from py3plex.core import multinet
    
    # Create a network
    net = multinet.multi_layer_network()
    # ... add nodes and edges ...
    
    # Query: Find nodes with degree > 3 in the social layer
    result = (
        Q.nodes()
         .from_layers(L["social"])
         .compute("degree")
         .where(degree__gt=3)
         .execute(net)
    )
    
    # Convert to pandas DataFrame
    df = result.to_pandas()
    print(df)

**See also:** ``examples/network_analysis/example_dsl_builder_api.py`` for complete DSL examples.

The DSL (covered in Part III) provides a concise way to filter, compute, and analyze multilayer networks without writing explicit loops.

Alternative Installation Paths (Use Only If Needed)
---------------------------------------------------

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

For contributors or to access the latest features:

.. code-block:: bash

    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    pip install -e .

The ``-e`` flag installs in editable mode—changes to source code are immediately available.

**For development with testing/linting tools:**

.. code-block:: bash

    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    make setup        # Create virtual environment
    make dev-install  # Install with dev dependencies

This installs pytest, black, ruff, mypy, and sphinx for development workflows.

Docker Installation
~~~~~~~~~~~~~~~~~~~

For a containerized environment with all dependencies:

.. code-block:: bash

    # Clone repository
    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    
    # Build image
    docker build -t py3plex:latest .
    
    # Run commands
    docker run --rm py3plex:latest --version

**Benefits:**

* No Python setup required
* Consistent environment across systems
* Isolated from system Python

Optional Dependencies
~~~~~~~~~~~~~~~~~~~~~

Py3plex supports optional feature sets:

.. code-block:: bash

    # Advanced community detection (Infomap)
    pip install py3plex[infomap]
    
    # Extra algorithms (Louvain, cdlib)
    pip install py3plex[algos]
    
    # Advanced visualization (Plotly, igraph)
    pip install py3plex[viz]
    
    # High-performance I/O (Arrow/Parquet)
    pip install py3plex[arrow]
    
    # Install multiple extras
    pip install py3plex[infomap,viz,algos,arrow]

**Conda alternative:**

.. code-block:: bash

    conda create -n py3plex python=3.10
    conda activate py3plex
    pip install py3plex

Key Concepts
------------

Before proceeding, understand these fundamental concepts:

Node-Layer Pairs
~~~~~~~~~~~~~~~~

In py3plex, a node is always associated with a layer. The tuple ``(node_id, layer_id)`` is the fundamental unit.

* ``('Alice', 'friends')`` is different from ``('Alice', 'colleagues')``
* This allows the same logical entity to have different properties and connections in different contexts

Example:

.. code-block:: python

    # Access nodes as (node_id, layer_id) tuples
    for node in network.get_nodes():
        print(node)  # ('Alice', 'friends'), ('Bob', 'friends'), ...

NetworkX Compatibility
~~~~~~~~~~~~~~~~~~~~~~

Py3plex uses NetworkX as its underlying graph representation:

.. code-block:: python

    import networkx as nx
    
    # Direct access to the NetworkX graph
    G = network.core_network
    
    # Use any NetworkX algorithm
    betweenness = nx.betweenness_centrality(G)
    
    # Modify directly
    G.nodes[('Alice', 'friends')]['age'] = 30

This means:

* Any NetworkX algorithm works on py3plex networks
* You can mix py3plex and NetworkX functions freely
* Learning curve is minimal if you already know NetworkX

Input Formats
~~~~~~~~~~~~~

Py3plex supports multiple edge input formats:

**List format** (used in examples above):

.. code-block:: python

    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
    ], input_type="list")

**Dictionary format** (explicit, Pythonic):

.. code-block:: python

    network.add_edges([{
        'source': 'Alice',
        'source_type': 'friends',
        'target': 'Bob',
        'target_type': 'friends',
        'weight': 1
    }])

**File loading** (for larger networks):

.. code-block:: python

    # Edgelist format
    network.load_network("data.edgelist", input_type="edgelist")
    
    # GraphML, JSON, Arrow, etc.
    # See :ref:`data-loading-chapter` for details

Common Issues
-------------

Issue: "No module named 'py3plex'"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution:** Ensure py3plex is installed in the active Python environment:

.. code-block:: bash

    pip install py3plex

Verify which Python interpreter you're using:

.. code-block:: bash

    which python  # Linux/macOS
    where python  # Windows

Issue: Import errors for optional dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution:** Install the relevant extra:

.. code-block:: bash

    pip install py3plex[infomap]  # For Infomap
    pip install py3plex[viz]      # For Plotly

Issue: Permission denied on Linux/macOS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution:** Use a virtual environment (recommended) or install with ``--user``:

.. code-block:: bash

    pip install --user py3plex

License Considerations
----------------------

Py3plex core is released under the **MIT License**, which allows commercial and non-commercial use without restrictions.

Optional AGPL Components
~~~~~~~~~~~~~~~~~~~~~~~~

**Important:** Some optional features include code licensed under **AGPLv3** (a copyleft license):

* **Infomap community detection** (``py3plex[infomap]``)

If you install and use these features, your application may be subject to AGPLv3 requirements:

* You must make your application's source code available if you distribute it
* Modified versions must also be released under AGPLv3

**How to avoid AGPLv3:**

1. Don't install extras with AGPL components (don't use ``pip install py3plex[infomap]``)
2. Use alternative algorithms (Louvain, Label Propagation) instead of Infomap
3. Check the license of any extra before installing

**Default installation** (``pip install py3plex``) includes only MIT-licensed code.

Verifying Installation
----------------------

Run a self-test to confirm everything works:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    
    # Create test network
    network = multinet.multi_layer_network()
    network.add_edges([
        ['A', 'L1', 'B', 'L1', 1],
        ['B', 'L1', 'C', 'L1', 1],
    ], input_type="list")
    
    # Test basic operations
    assert network.get_number_of_nodes() == 3
    assert mls.layer_density(network, 'L1') > 0
    
    print("✓ py3plex is working correctly")

Next Steps
----------

Now that you have py3plex installed and understand the basics:

* :ref:`data-loading-chapter` — Learn about data loading, supported formats, and best practices for representing multilayer networks
* :ref:`visualization-chapter` — Explore visualization techniques for multilayer networks
* :ref:`algorithms-chapter` — Apply core algorithms: community detection, centrality measures, and dynamics

**For immediate exploration:**

Browse the ``examples/`` directory in the repository for current workflows:

* ``examples/getting_started/`` — first-run examples
* ``examples/network_analysis/`` — DSL, algorithms, and analysis patterns
* ``examples/dsl_zoo/`` — focused DSL query patterns
* ``examples/io_and_data/`` — loading and conversion workflows
* ``examples/visualization/`` — plotting and rendering examples

**Run any example:**

.. code-block:: bash

    # Using uv (recommended)
    uv run examples/getting_started/01_basic_query.py
    
    # Or using python
    python examples/getting_started/01_basic_query.py

Closing Note
------------

If the recommended path worked, continue directly to :ref:`data-loading-chapter`. Return to alternative paths only when you need editable installs, optional extras, or containerized execution.
