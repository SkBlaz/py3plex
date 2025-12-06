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

.. admonition:: 🔍 DSL: Query Networks Like SQL
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

   📖 See the complete :doc:`user_guide/dsl` guide for all features!

Quick Start
===========

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

See :doc:`getting_started/quickstart_5min` (5 min) or :doc:`getting_started/tutorial_10min` (10 min) for complete introductions.

Documentation Contents
======================

Part I: Getting Started
-----------------------

Installation, quick start guides, and tutorials to get you up and running with py3plex.

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting_started/part_intro
   getting_started/installation
   getting_started/quickstart_5min
   getting_started/tutorial_10min
   getting_started/common_issues

----

Part II: Concepts & Architecture
--------------------------------

Understand multilayer network theory and py3plex's design philosophy.

.. toctree::
   :maxdepth: 2
   :caption: Concepts & Architecture

   concepts/part_intro
   concepts/multilayer_networks_101
   concepts/py3plex_core_model
   concepts/design_principles
   concepts/algorithm_landscape

----

Part III: User Guide
--------------------

Comprehensive how-to guides for every major feature.

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/part_intro
   user_guide/networks
   user_guide/statistics
   user_guide/community_detection
   user_guide/multilayer_dynamics
   user_guide/random_walks_embeddings
   user_guide/io_and_formats
   user_guide/visualization
   user_guide/dsl
   user_guide/graph_ops
   user_guide/recipes_and_workflows
   user_guide/case_studies

----

Part IV: Environments & Deployment
----------------------------------

CLI, Docker, and performance optimization for production use.

.. toctree::
   :maxdepth: 2
   :caption: Environments & Deployment

   deployment/part_intro
   deployment/cli_and_docker
   deployment/performance_scalability

----

Part V: Py3plex GUI
-------------------

Web-based graphical interface for interactive network exploration.

.. toctree::
   :maxdepth: 2
   :caption: Py3plex GUI

   gui/part_intro
   gui/gui_user_guide
   gui/gui_deployment
   gui/gui_api_reference
   gui/gui_architecture
   gui/gui_testing

----

Part VI: Developer & Contributor Docs
-------------------------------------

Development setup, architecture, and contribution guidelines.

.. toctree::
   :maxdepth: 2
   :caption: Developer & Contributor Docs

   dev/part_intro
   dev/development_guide
   dev/code_architecture
   dev/repo_layout
   dev/contributing

----

Part VII: Examples
------------------

Working code examples for various use cases.

.. toctree::
   :maxdepth: 1
   :caption: Examples

   examples/index

----

Part VIII: Reference & Citation
-------------------------------

API documentation and citation information.

.. toctree::
   :maxdepth: 2
   :caption: Reference & Citation

   reference/part_intro
   reference/algorithm_reference
   reference/api_index
   reference/citation_and_acknowledgements

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
