Examples & Recipes
==================

The runnable examples live in the `repository examples directory
<https://github.com/SkBlaz/py3plex/tree/master/examples>`_. Clone the repository
before running these scripts; installing the Python package does not install
this source directory.

Start Here
----------

From the repository root, with py3plex installed:

.. code-block:: bash

    python examples/getting_started/01_basic_query.py
    python examples/getting_started/dsl_patterns_quick_reference.py
    python examples/getting_started/tutorial_10min.py

The first script creates a small network and queries node degrees. The second
covers common builder patterns. The tutorial adds loading, communities, and
visualization; it takes longer and writes plots to ``example_images/``.

For a notebook environment, use the linked notebooks in
:doc:`../how-to/query_with_dsl` and :doc:`../how-to/run_community_detection`.

Browse by Task
--------------

* ``getting_started/`` — Basic construction, datasets, queries, and tutorials.
* ``io_and_data/`` — File loading, conversion, and exports.
* ``network_analysis/`` — Statistics, community detection, and DSL workflows.
* ``dsl_zoo/`` — Composable DSL query examples and helper datasets.
* ``visualization/`` — Layouts, layer plots, and interactive figures.
* ``advanced/`` — Temporal networks, uncertainty, dynamics, and specialized methods.
* ``pipelines/`` — Reusable analysis pipelines.
* ``out_of_core/`` — Streaming and out-of-core workflows.

Individual examples may require optional extras or additional datasets. Read the
script's prerequisites before running it. For feature installation commands,
see :doc:`../getting_started/installation`.

Continue Learning
-----------------

* :doc:`../getting_started/tutorial_10min` — First network and analysis.
* :doc:`../user_guide/dsl` — Query language and builder API.
* :doc:`../user_guide/recipes_and_workflows` — Reusable recipes.
* :doc:`../user_guide/visualization` — Visualization concepts and examples.
