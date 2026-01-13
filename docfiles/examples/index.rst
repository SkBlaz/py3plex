Examples & Recipes
==================

Browse **170+ comprehensive examples** grouped by topic and learning progression. Every entry below corresponds to a file in the ``examples/`` directory (`GitHub listing <https://github.com/SkBlaz/py3plex/tree/master/examples>`_). Examples range from quick introductions to advanced techniques.

**What's here:**

* **Runnable Examples** — 170+ scripts covering all py3plex features
* **Analysis Recipes** — Reusable patterns (:doc:`../user_guide/recipes_and_workflows`)
* **Case Studies** — Real-world applications from biology, social networks, and more

**Learning Path:**

1. **Start here:** ``getting_started/`` - Basics and 10-minute tutorial
2. **Load data:** ``io_and_data/`` - I/O and data handling
3. **Analyze:** ``network_analysis/`` - Statistics and metrics
4. **Query:** ``dsl_query_zoo/`` - DSL examples collection
5. **Advanced:** ``advanced/``, ``communities/``, ``dynamics/``, ``temporal/``, etc.

To run any example:

.. code-block:: bash

    python examples/<folder>/<filename>.py

Example Structure
-----------------

The examples are organized into comprehensive topic-based folders:

.. code-block:: text

    examples/
    ├── getting_started/        (7 files) - Basics and 10-min tutorial
    ├── io_and_data/           (10 files) - I/O and data handling
    ├── network_analysis/      (16 files) - Statistics and metrics
    ├── communities/           (14 files) - Community detection
    ├── visualization/         (17 files) - Network visualizations
    ├── advanced/              (29 files) - Advanced techniques
    ├── dynamics/              (3 files) - Dynamical processes
    ├── temporal/              (7 files) - Temporal networks
    ├── uncertainty/           (6 files) - Uncertainty quantification
    ├── dsl_query_zoo/         - DSL query examples collection
    ├── workflows/             (2 files) - Config-driven workflows
    ├── pipelines/             (7 files) - Analysis pipelines
    ├── case_studies/          (4 files) - Real-world applications
    ├── cli/                   (3 files) - CLI examples
    └── README.md              - Navigation guide

getting_started/
----------------

**Goal:** Get started with py3plex quickly.

* ``tutorial_10min.py`` - 10-minute comprehensive tutorial
* ``example_datasets.py`` - Load built-in datasets
* ``example_multilayer_functionality.py`` - Core multilayer features
* ``example_random_generator.py`` - Generate random networks
* And more...

**Run the tutorial:**

.. code-block:: bash

    python examples/getting_started/tutorial_10min.py

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

communities/
------------

**Goal:** Comprehensive community detection methods.

* ``example_community_detection.py`` - Basic community detection
* ``example_leiden_multilayer.py`` - Leiden algorithm for multilayer networks
* ``example_auto_select_basic.py`` - AutoCommunity meta-algorithm
* ``example_label_propagation.py`` - Label propagation
* And more advanced examples...

See the ``communities/`` directory for all 14 community detection examples.

dynamics/
---------

**Goal:** Simulate dynamical processes on networks.

* ``sir_epidemic.py`` - SIR epidemic model
* ``sis_dynamics.py`` - SIS epidemic model
* ``random_walk.py`` - Random walks

See also the ``advanced/`` directory for more dynamics examples.

uncertainty/
------------

**Goal:** Uncertainty quantification in network analysis.

* Bootstrap and perturbation methods
* Null model comparisons
* Confidence intervals for centrality measures

See the ``uncertainty/`` directory for all 6 UQ examples.

Running Examples
----------------

Examples are designed for various use cases from quick learning to production workflows.

.. code-block:: bash

    # Quick start - run the tutorial
    python examples/getting_started/tutorial_10min.py
    
    # Load and analyze a dataset
    python examples/getting_started/example_datasets.py
    
    # Community detection
    python examples/communities/example_community_detection.py
    
    # Run all fast examples (CI validation)
    python .github/scripts/run_examples.py --fast-only --timeout 30

Performance
-----------

Examples range from quick demonstrations to comprehensive analyses:

* **Fast examples:** Marked with ``Runtime: FAST`` - run in < 5 seconds
* **CI-tested:** Fast examples run in CI for validation
* **Slow examples:** Marked with ``SKIP_CI: slow`` - comprehensive analyses
* **Interactive:** Marked with ``SKIP_CI: interactive`` - require display/interaction
* **External deps:** Marked with ``SKIP_CI: external_deps`` - need external datasets

Example Guidelines
------------------

When creating new examples:

.. code-block:: python

    """
    Example title: Describe what this example demonstrates.
    
    Runtime: FAST (< 5 seconds) or SKIP_CI: slow/interactive/external_deps
    
    Demonstrates:
    - Primary feature or technique
    - Key API patterns
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

* **Descriptive:** Clear docstring explaining what is demonstrated
* **Runtime markers:** Add ``Runtime: FAST`` or appropriate ``SKIP_CI`` marker
* **Comments:** Use section comments for clarity
* **Self-contained:** Include all necessary imports and setup

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
