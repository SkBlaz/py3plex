Py3plex: A Practical Guide to Multilayer Network Analysis
***********************************************************

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

*A practical, hands-on guide to analyzing and visualizing multilayer networks in Python.*

----

Welcome to py3plex. This documentation is organized as a progressive learning journey—from your first five-minute example through conceptual foundations to advanced production workflows. Whether you're a researcher exploring social network dynamics, a bioinformatician analyzing protein interactions across multiple evidence types, or a data scientist building features for machine learning, this guide will show you how to work effectively with multilayer network structures.

py3plex enables scalable analysis and visualization of multilayer and multiplex networks in Python, supporting complex network modeling across diverse scientific and applied domains.

Getting Started

**Key Features:**

* Native support for multiplex and multilayer network structures
* SQL-like DSL for intuitive network queries
* 17+ multilayer-specific statistics and centrality measures
* Community detection across network layers (Louvain, Infomap, multilayer modularity)
* Random walk algorithms (Node2Vec, DeepWalk) for graph embeddings
* Publication-ready visualizations with diagonal projection layouts
* High-performance I/O with Arrow/Parquet support
* Full NetworkX compatibility

Quick Paths
===========

.. tip::

   * **"I have a multilayer edge list and want communities"** → :doc:`getting_started/quickstart_5min` → :doc:`user_guide/community_detection`
   * **"I want embeddings for ML"** → :doc:`getting_started/quickstart_5min` → :doc:`user_guide/random_walks_embeddings`
   * **"I want to contribute a new algorithm"** → :doc:`dev/development_guide` → :doc:`dev/code_architecture`

Quick Start
===========

Install py3plex:

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git

Create your first multilayer network:

.. code-block:: python

    from py3plex.core import multinet

    # Create a multilayer network
    network = multinet.multi_layer_network()

    # Add edges (nodes are created automatically)
    network.add_edges([
        ['Alice', 'friends', 'Bob', 'friends', 1],
        ['Bob', 'friends', 'Carol', 'friends', 1],
        ['Alice', 'colleagues', 'Bob', 'colleagues', 1],
    ], input_type="list")

    # Display statistics and visualize
    network.basic_stats()
    network.visualize_network(show=True)

For a complete introduction, see :doc:`getting_started/quickstart_5min` (5 minutes) or :doc:`getting_started/tutorial_10min` (10 minutes).

Documentation Contents
======================

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

   examples/part_intro
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
