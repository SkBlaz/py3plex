.. _installation-chapter:

Installation and Getting Started
===========================================

This chapter covers installing py3plex and running your first multilayer network analysis. We provide a minimal quickstart example followed by installation details for different use cases.

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

Quick Install
-------------

For most users, installation is straightforward:

.. code-block:: bash

    pip install py3plex

This installs py3plex with core dependencies (NetworkX, NumPy, SciPy, pandas, matplotlib).

**Using uv (recommended for development):**

`uv <https://github.com/astral-sh/uv>`_ is a fast Python package installer and resolver. To use uv:

.. code-block:: bash

    # Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Install py3plex with uv
    uv pip install py3plex

**Verify installation:**

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

Create and analyze a multilayer network in 30 seconds. See the complete example in ``examples/00_quickstart/02_create_and_visualize.py``:

.. literalinclude:: ../../examples/00_quickstart/02_create_and_visualize.py
   :language: python
   :lines: 1-25

**Run this example:**

.. code-block:: bash

    # Using uv
    uv run examples/00_quickstart/02_create_and_visualize.py
    
    # Or using python
    python examples/00_quickstart/02_create_and_visualize.py

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

Use SQL-like queries to explore the network. See the complete example in ``examples/00_quickstart/01_load_and_query.py``:

.. literalinclude:: ../../examples/00_quickstart/01_load_and_query.py
   :language: python
   :lines: 1-27

**Run this example:**

.. code-block:: bash

    # Using uv
    uv run examples/00_quickstart/01_load_and_query.py
    
    # Or using python
    python examples/00_quickstart/01_load_and_query.py

The DSL (covered in Part III) provides a powerful way to filter, compute, and analyze multilayer networks without writing explicit loops.

Installation Options
--------------------

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

Virtual Environments
~~~~~~~~~~~~~~~~~~~~

We strongly recommend using virtual environments:

**Using venv:**

.. code-block:: bash

    python3 -m venv py3plex-env
    source py3plex-env/bin/activate  # Linux/macOS
    # py3plex-env\Scripts\activate   # Windows
    pip install py3plex

**Using conda:**

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

Browse the ``examples/`` directory in the repository for working examples covering various use cases:

* ``examples/00_quickstart/`` — Getting started (3 examples)
* ``examples/01_network_construction/`` — Building networks (3 examples)
* ``examples/02_basic_queries/`` — Basic DSL queries (4 examples)
* ``examples/03_dsl_v2/`` — Advanced DSL (4 examples)
* ``examples/04_graph_ops/`` — Data manipulation (3 examples)
* ``examples/05_communities/`` — Community detection (3 examples)
* ``examples/06_dynamics/`` — Network dynamics (3 examples)
* ``examples/07_uncertainty/`` — Uncertainty quantification (3 examples)

**Run any example:**

.. code-block:: bash

    # Using uv (recommended)
    uv run examples/00_quickstart/01_load_and_query.py
    
    # Or using python
    python examples/00_quickstart/01_load_and_query.py

Summary
-------

This chapter covered:

1. **Quick install** — ``pip install py3plex``
2. **Hello World** — Create a multilayer network in 30 seconds
3. **Basic analysis** — Statistics, visualization, and DSL queries
4. **Installation options** — Development, Docker, optional dependencies
5. **Key concepts** — Node-layer pairs, NetworkX compatibility, input formats

With py3plex installed, you're ready to analyze multilayer networks. The next chapter covers loading real data and representing complex multilayer structures.
