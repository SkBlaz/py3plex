Quick Start Tutorial
====================

Get started with py3plex in just a few minutes. This tutorial shows you the essential concepts through three focused examples.

.. admonition:: 📓 Executable Examples
   :class: tip

   All examples are in the ``examples/00_quickstart/`` directory and can be run directly:
   
   .. code-block:: bash

       python examples/00_quickstart/01_load_and_query.py
       python examples/00_quickstart/02_create_and_visualize.py
       python examples/00_quickstart/03_communities.py

**You will learn:**

* Load and query multilayer networks
* Create networks from scratch
* Detect communities across layers

Installation
------------

.. code-block:: bash

    python -m pip install py3plex

For Docker setup or optional dependencies, see :doc:`installation`.
Run inside a virtual environment to keep dependencies isolated.

----

Example 1: Load and Query (1 min)
----------------------------------

Load a built-in dataset and run a simple query:

.. code-block:: python

    from py3plex.datasets import load_aarhus_cs
    from py3plex.dsl import Q

    # 1. Load network
    network = load_aarhus_cs()

    # 2. Run query - find nodes with degree > 5
    result = (
        Q.nodes()
        .where(degree__gt=5)
        .compute("degree_centrality")
        .execute(network)
    )

    # 3. Inspect result
    print(f"Found {len(result.nodes)} high-degree nodes")
    df = result.to_pandas()
    print(df.head())

**What this does:**

* Loads the Aarhus CS multilayer social network (61 nodes, 5 layers)
* Filters nodes with more than 5 connections
* Computes degree centrality
* Displays results as a pandas DataFrame

**Next:** See ``examples/03_dsl_v2/`` for advanced DSL queries.

----

Example 2: Create Network (2 min)
----------------------------------

Create a simple multilayer network from scratch:

.. code-block:: python

    from py3plex.core.multinet import multi_layer_network

    # 1. Create network
    network = multi_layer_network(directed=False)

    # 2. Add edges (nodes created automatically)
    network.add_edges([
        {'source': 'Alice', 'target': 'Bob', 
         'source_type': 'social', 'target_type': 'social'},
        {'source': 'Bob', 'target': 'Charlie', 
         'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Charlie', 
         'source_type': 'social', 'target_type': 'social'},
        {'source': 'Alice', 'target': 'Bob', 
         'source_type': 'work', 'target_type': 'work'},
        {'source': 'Bob', 'target': 'David', 
         'source_type': 'work', 'target_type': 'work'},
    ])

    # 3. Print statistics
    print(f"Nodes: {len(list(network.get_nodes()))}")
    print(f"Edges: {len(list(network.get_edges()))}")
    print(f"Layers: {len(network.layers)}")

**What this does:**

* Creates an undirected multilayer network
* Adds edges in two layers: 'social' and 'work'
* Nodes are created automatically from edge definitions
* Displays basic network statistics

**Next:** See ``examples/01_network_construction/`` for more construction patterns.

----

Example 3: Detect Communities (2 min)
--------------------------------------

Detect communities in a multilayer network:

.. code-block:: python

    from py3plex.datasets import load_aarhus_cs
    from py3plex.algorithms.community_detection.multilayer_modularity import louvain_multilayer

    # 1. Load network
    network = load_aarhus_cs()

    # 2. Detect communities
    partition, modularity = louvain_multilayer(network, random_state=42)

    # 3. Inspect result
    print(f"Found {len(set(partition.values()))} communities")
    print(f"Modularity: {modularity:.3f}")
    print(f"Sample partition: {dict(list(partition.items())[:5])}")

**What this does:**

* Loads the Aarhus CS network
* Runs multilayer Louvain community detection
* Returns partition (node → community mapping) and modularity score
* Displays summary statistics

**Next:** See ``examples/05_communities/`` for more community detection algorithms.

----

Next Steps
----------

**Continue learning:**

1. **More Examples:** Explore ``examples/`` directory (26 focused examples)
2. **DSL Guide:** :doc:`../user_guide/dsl` - SQL-like queries
3. **Visualization:** :doc:`../user_guide/visualization` - Create plots
4. **Advanced Topics:** See the book (PDF) for case studies

**Example categories:**

* ``00_quickstart/`` - Start here (3 examples)
* ``01_network_construction/`` - Build networks (3 examples)
* ``02_basic_queries/`` - Basic queries (4 examples)
* ``03_dsl_v2/`` - Modern DSL (4 examples, **recommended**)
* ``04_graph_ops/`` - dplyr-style ops (3 examples)
* ``05_communities/`` - Community detection (3 examples)
* ``06_dynamics/`` - Network dynamics (3 examples)
* ``07_uncertainty/`` - Uncertainty quantification (3 examples)

See :doc:`../examples/index` for the complete examples catalog.

**Getting help:**

* :doc:`common_issues` - Troubleshooting guide
* `GitHub Issues <https://github.com/SkBlaz/py3plex/issues>`_ - Report bugs
* `GitHub Discussions <https://github.com/SkBlaz/py3plex/discussions>`_ - Ask questions

----

Related Documentation
---------------------

* :doc:`installation` - Setup guide
* :doc:`../examples/index` - All examples
* :doc:`../user_guide/networks` - Network concepts
* :doc:`../user_guide/dsl` - Query language reference
