Examples & Recipes
==================

Browse **26 minimal, focused examples** grouped by learning progression. Every entry below corresponds to a file in the ``examples/`` directory (`GitHub listing <https://github.com/SkBlaz/py3plex/tree/master/examples>`_). Each example demonstrates exactly one concept in 20-40 lines of code and runs in under 2 seconds.

**Philosophy:** *Examples are onboarding instruments, not encyclopedias.*

**What's here:**

* **Runnable Examples** — 26 atomic scripts teaching core concepts
* **Analysis Recipes** — Reusable patterns (:doc:`../user_guide/recipes_and_workflows`)
* **Case Studies** — Extended tutorials in the book (PDF)

**Learning Path (30 minutes total):**

1. **Start here:** ``00_quickstart/`` (5 minutes)
2. **Build networks:** ``01_network_construction/`` (3 examples)
3. **Query data:** ``02_basic_queries/`` + ``03_dsl_v2/`` (8 examples)
4. **Analyze:** ``04_graph_ops/`` through ``07_uncertainty/`` (12 examples)

To run any example:

.. code-block:: bash

    python examples/<folder>/<filename>.py

Example Structure
-----------------

The examples are organized into 8 progressive folders:

.. code-block:: text

    examples/
    ├── 00_quickstart/          (3 files) - First 5 minutes
    ├── 01_network_construction/ (3 files) - How to build networks
    ├── 02_basic_queries/       (4 files) - Basic querying
    ├── 03_dsl_v2/             (4 files) - Modern DSL (recommended)
    ├── 04_graph_ops/          (3 files) - dplyr-style operations
    ├── 05_communities/        (3 files) - Community detection
    ├── 06_dynamics/           (3 files) - Dynamical processes
    ├── 07_uncertainty/        (3 files) - Uncertainty quantification
    └── README.md              - Navigation guide

00_quickstart/
--------------

**Goal:** Get started with py3plex in 5 minutes.

* ``01_load_and_query.py`` - Load a dataset and run a simple query
* ``02_create_and_visualize.py`` - Create a network from scratch
* ``03_communities.py`` - Detect communities

**Run all three:**

.. code-block:: bash

    python examples/00_quickstart/01_load_and_query.py
    python examples/00_quickstart/02_create_and_visualize.py
    python examples/00_quickstart/03_communities.py

01_network_construction/
------------------------

**Goal:** Learn how to build multilayer networks.

* ``01_from_edges.py`` - Build from edge list
* ``02_fluent_building.py`` - Method chaining
* ``03_from_networkx.py`` - Convert from NetworkX

**No analytics. No DSL.** Just network construction patterns.

02_basic_queries/
-----------------

**Goal:** Understand the mental model of querying.

* ``01_legacy_string_dsl.py`` - Legacy string DSL (backward compatibility only)
* ``02_select_by_layer.py`` - Layer filtering
* ``03_filter_by_degree.py`` - Degree filtering
* ``04_compute_centrality.py`` - Single metric computation

**Note:** Use DSL v2 (next section) for new code.

03_dsl_v2/
----------

**Goal:** Master the modern Python DSL (recommended).

* ``01_builder_basic.py`` - Q.nodes() builder pattern
* ``02_layer_algebra.py`` - Layer unions/intersections
* ``03_grouping_aggregation.py`` - Per-layer grouping
* ``04_explain.py`` - Query explanation

.. admonition:: Featured: DSL v2 Builder API
   :class: dsl-example

   The DSL provides a SQL-like query language with Python builder syntax:

   .. code-block:: python

       from py3plex.dsl import Q, L

       # From 01_builder_basic.py
       result = (
           Q.nodes()
            .where(degree__gte=5)
            .compute("degree_centrality")
            .sort(by="degree_centrality", descending=True)
            .limit(15)
            .execute(network)
       )

   **Key features:**

   * SQL-like syntax for network queries
   * Python builder API with type hints
   * Layer algebra: ``L["layer1", "layer2"]`` for union
   * Django-style WHERE: ``degree__gt=5``, ``layer__ne="coupling"``
   * COMPUTE measures with automatic calculation
   * Sort, limit, explain, export to pandas/NetworkX/Arrow

   See :doc:`../user_guide/dsl` for full documentation.

04_graph_ops/
-------------

**Goal:** Use dplyr-style operations on network data.

* ``01_filter_mutate.py`` - Filter + add columns
* ``02_group_summarise.py`` - Group by + aggregation
* ``03_subgraph.py`` - Subgraph extraction

**No DSL here.** Pure dplyr-inspired data manipulation.

05_communities/
---------------

**Goal:** Community detection, nothing else.

* ``01_louvain_single.py`` - Single-layer Louvain
* ``02_multilayer_detection.py`` - Multilayer communities
* ``03_auto_community.py`` - AutoCommunity (flagship feature)

**No visualization. No benchmarking.** Just community detection algorithms.

06_dynamics/
------------

**Goal:** Simulate dynamical processes on networks.

* ``01_sis_epidemic.py`` - SIS epidemic model
* ``02_multilayer_epidemic.py`` - Multilayer spreading
* ``03_custom_model.py`` - Custom dynamics

**No queries. No DSL.** Focus on dynamics concepts.

07_uncertainty/
---------------

**Goal:** Uncertainty quantification as a first-class feature.

* ``01_uq_centrality.py`` - UQ-enabled centrality
* ``02_bootstrap.py`` - Bootstrap/perturbation
* ``03_comparison.py`` - UQ vs deterministic

Running Examples
----------------

All examples run with base dependencies only (no optional packages required except ``05_communities/03_auto_community.py``).

.. code-block:: bash

    # Quick validation - run all quickstart examples
    python examples/00_quickstart/01_load_and_query.py
    python examples/00_quickstart/02_create_and_visualize.py
    python examples/00_quickstart/03_communities.py
    
    # Recommended DSL v2 starting point
    python examples/03_dsl_v2/01_builder_basic.py
    
    # Community detection
    python examples/05_communities/01_louvain_single.py

Performance
-----------

All examples are designed for CI and development:

* **Fast execution:** Each example runs in ~2 seconds
* **No SKIP_CI markers:** All examples tested in CI
* **Small datasets:** Use ``load_aarhus_cs()`` or tiny synthetic networks
* **Minimal code:** 20-40 lines per example
* **One concept:** Each example teaches exactly one thing

Example Template
----------------

When creating new examples, follow this pattern:

.. code-block:: python

    """
    Example title: One concept per example.
    
    Demonstrates:
    - Primary concept
    - Optional secondary concept
    """
    
    from py3plex.datasets import load_aarhus_cs
    from py3plex.dsl import Q
    
    # 1. Load network
    network = load_aarhus_cs()
    
    # 2. Run operation
    result = Q.nodes().compute("degree_centrality").execute(network)
    
    # 3. Inspect result
    print(result.to_pandas().head())

Guidelines:

* **Atomic:** One concept maximum (two if unavoidable)
* **Minimal:** 20-40 lines total
* **Fast:** Runs in < 2 seconds
* **Clear:** Section comments (# 1. Load network)
* **Numbered:** Use ``01_``, ``02_`` prefixes

See ``examples/README.md`` for complete guidelines.

Related Documentation
---------------------

* :doc:`../getting_started/quickstart` - Quick start guide
* :doc:`../user_guide/networks` - Working with networks
* :doc:`../user_guide/dsl` - DSL reference
* :doc:`../user_guide/visualization` - Visualization guide
* :doc:`../user_guide/recipes_and_workflows` - Analysis recipes

**Advanced topics** (see book PDF):

* Case studies with domain interpretation
* Research pipelines
* Performance benchmarks
* Custom plugin development

**Repository:**

* Examples directory: https://github.com/SkBlaz/py3plex/tree/master/examples
* Examples README: https://github.com/SkBlaz/py3plex/tree/master/examples/README.md
* Submit examples: https://github.com/SkBlaz/py3plex/pulls
