Py3plex: Multilayer Network Analysis
*************************************

.. image:: ../example_images/py3plex_showcase.png
   :alt: Py3plex Visualization Showcase
   :align: center

.. image:: https://github.com/SkBlaz/py3plex/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/SkBlaz/py3plex/actions/workflows/tests.yml
   :alt: Tests

.. image:: https://github.com/SkBlaz/py3plex/actions/workflows/code-quality.yml/badge.svg
   :target: https://github.com/SkBlaz/py3plex/actions/workflows/code-quality.yml
   :alt: Code Quality

----

.. admonition:: Documentation Versions
   :class: note

   **You are viewing the documentation for py3plex 1.x** (current stable version). These docs are actively maintained and updated.

   **Legacy documentation for py3plex 0.8x** is still available at https://py3plex.readthedocs.io but is no longer updated. Most users should use the 1.x docs you're reading now.

   **Which version should you use?** See :ref:`which-docs-to-use` below for guidance.

----

py3plex provides scalable analysis and visualization of multilayer and multiplex networks in Python.

**Key Features:**

* Multiplex and multilayer network structures
* **SQL-like DSL for network queries** — first-class feature
* 17+ multilayer statistics and centrality measures
* Community detection (Louvain, Infomap, multilayer modularity)
* Random walk algorithms (Node2Vec, DeepWalk) for embeddings
* Publication-ready visualizations
* High-performance I/O with Arrow/Parquet support
* Full NetworkX compatibility

.. admonition:: DSL: Query Networks Like SQL
   :class: dsl-example

   The py3plex DSL lets you query networks using intuitive SQL-like syntax or a type-safe Python builder API:

   .. code-block:: python

       from py3plex.dsl import execute_query, Q, L

       # String DSL: Simple and readable
       result = execute_query(network, 
           'SELECT nodes WHERE layer="social" AND degree > 5 '
           'COMPUTE betweenness_centrality'
       )

       # Builder API: Type-safe with autocompletion
       result = (
           Q.nodes()
            .from_layers(L["social"])
            .where(degree__gt=5)
            .compute("betweenness_centrality")
            .order_by("-betweenness_centrality")
            .limit(10)
            .execute(network)
       )

   The DSL is **perfect for**:
   
   * Interactive network exploration
   * Rapid prototyping
   * Educational purposes
   * Production pipelines

   See the complete :doc:`user_guide/dsl` guide for all features!

Quickstart
==========

Install:

.. code-block:: bash

    pip install py3plex

Create a multilayer network:

.. code-block:: python

    from py3plex.core import multinet

    network = multinet.multi_layer_network()
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Bob', 'friends', 'Carol', 'friends', 1],
        ['Alice', 'colleagues', 'Bob', 'colleagues', 1],
    ], input_type="list")

    network.basic_stats()
    network.visualize_network(show=True)

**Expected output:**

.. code-block:: text

    Number of nodes: 6
    Number of edges: 3

Start Here
==========

**New to py3plex?** → Begin with the :doc:`getting_started/tutorial_10min` to go from basics to advanced analysis in 10 minutes.

**Already familiar with multilayer networks?** → Jump to :doc:`how-to/run_community_detection` or explore the :doc:`how-to/part_intro`.

**Just need the API?** → Go straight to :doc:`reference/api_index` or :doc:`reference/dsl_reference`.

**Want to understand the concepts?** → Read :doc:`concepts/multilayer_networks_101` for the theory behind multilayer networks.

Documentation Structure
=======================

This documentation follows the `Diátaxis <https://diataxis.fr/>`_ framework with 7 top-level sections:

Part I: Overview
----------------

High-level introduction to py3plex and multilayer networks.

.. toctree::
   :maxdepth: 2
   :caption: Overview

   overview/part_intro
   overview/what_is_py3plex
   overview/key_use_cases
   overview/multilayer_in_2min

----

Part II: Getting Started (Tutorials)
-------------------------------------

Step-by-step tutorials for beginners. Start here if you're new to py3plex.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting_started/part_intro
   getting_started/installation
   getting_started/tutorial_10min
   getting_started/common_issues

----

Part III: How-to Guides
------------------------

Task-oriented guides answering "How do I...?" questions.

.. toctree::
   :maxdepth: 2
   :caption: How-to Guides

   how-to/part_intro
   how-to/load_and_build_networks
   how-to/query_zoo
   how-to/compute_statistics
   how-to/run_community_detection
   how-to/simulate_dynamics
   how-to/run_random_walks
   how-to/export_serialize
   how-to/visualize_networks
   how-to/query_with_dsl
   how-to/query_with_patterns
   how-to/build_pipelines
   how-to/reproduce_workflows

----

Part IV: Concepts & Explanations
---------------------------------

Theoretical background and architectural explanations.

.. toctree::
   :maxdepth: 2
   :caption: Concepts & Explanations

   concepts/part_intro
   concepts/multilayer_networks_101
   concepts/py3plex_core_model
   concepts/design_principles
   concepts/algorithm_landscape

----

Part V: API & DSL Reference
----------------------------

Complete reference documentation for APIs and DSL syntax.

.. toctree::
   :maxdepth: 2
   :caption: API & DSL Reference

   reference/part_intro
   reference/algorithm_reference
   reference/dsl_reference
   reference/layer_set_algebra
   reference/uncertainty_first_statistics
   reference/api_index
   reference/configuration

----

Part VI: Examples & Recipes
----------------------------

Complete working examples and analysis recipes.

.. toctree::
   :maxdepth: 2
   :caption: Examples & Recipes

   examples/index
   user_guide/recipes_and_workflows
   user_guide/case_studies

----

Part VII: Project Info
-----------------------

Project information, contributing guidelines, and citations.

.. toctree::
   :maxdepth: 2
   :caption: Project Info

   project/part_intro
   project/changelog
   project/roadmap
   project/contributing
   project/benchmarking
   project/citing

----

Additional Sections
-------------------

.. toctree::
   :maxdepth: 1
   :caption: Deployment & GUI

   deployment/part_intro
   deployment/cli_and_docker
   deployment/performance_scalability
   gui/part_intro
   gui/gui_user_guide

.. toctree::
   :maxdepth: 1
   :caption: Developer Docs

   dev/part_intro
   dev/development_guide
   dev/code_architecture

Citation
========

If you use py3plex in your research, please cite:

.. code-block:: bibtex

    @Article{Skrlj2019,
      author={Skrlj, Blaz and Kralj, Jan and Lavrac, Nada},
      title={Py3plex toolkit for visualization and analysis of multilayer networks},
      journal={Applied Network Science},
      year={2019},
      volume={4},
      number={1},
      pages={94},
      doi={10.1007/s41109-019-0203-7}
    }

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
