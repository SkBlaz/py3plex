Py3plex Documentation
**********************************

.. image:: ../example_images/py3plex_showcase.png
   :alt: Py3plex Visualization Showcase
   :align: center

.. image:: https://github.com/SkBlaz/py3plex/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/SkBlaz/py3plex/actions/workflows/tests.yml
   :alt: Tests

.. image:: https://github.com/SkBlaz/py3plex/actions/workflows/code-quality.yml/badge.svg
   :target: https://github.com/SkBlaz/py3plex/actions/workflows/code-quality.yml
   :alt: Code Quality

py3plex enables scalable analysis and visualization of multilayer and multiplex networks in Python, supporting complex network modeling across diverse scientific and applied domains.

Overview
========

py3plex is a lightweight Python library designed specifically for analyzing and visualizing heterogeneous and multilayer networks. Unlike traditional network analysis tools that focus on homogeneous networks (single node and edge type), py3plex provides specialized capabilities for networks with:

* Multiple node types
* Multiple edge types
* Multiple layers of interaction
* Temporal dynamics
* Heterogeneous attributes

**Target Users:** Researchers in network science, computational biology, complex systems, social network analysis, and applied network modeling.

**Key Features:**

* Native support for multiplex and multilayer network structures
* Diagonal projection visualization for large multilayer networks
* Comprehensive multilayer centrality measures
* Community detection across network layers
* Network decomposition and feature extraction
* Semantic enrichment with external knowledge bases
* Integration with NetworkX, igraph, and other graph libraries

Installation
============

Install from GitHub
-------------------

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git

Docker Installation (Alternative)
----------------------------------

py3plex is also available as a Docker container with all dependencies pre-installed:

.. code-block:: bash

    # Clone and build
    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    docker build -t py3plex:latest .

    # Run commands
    docker run --rm py3plex:latest --version
    docker run --rm py3plex:latest selftest

See :doc:`deployment/cli_and_docker` for complete Docker documentation.

Install from source for development
------------------------------------

.. code-block:: bash

    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    pip install -e .

Optional Dependencies
---------------------

.. code-block:: bash

    # Advanced community detection with Infomap
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[infomap]

    # Additional algorithms (Louvain, cdlib)
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[algos]

    # Advanced visualization (plotly, igraph)
    pip install git+https://github.com/SkBlaz/py3plex.git#egg=py3plex[viz]

    # For development (includes testing and linting tools)
    pip install -e ".[dev]"

Requirements
------------

* Python 3.8 or higher
* NetworkX, NumPy, SciPy (automatically installed)
* Optional: Matplotlib, Plotly for visualization

Quick Start
===========

Create a simple multilayer network:

.. code-block:: python

    from py3plex.core import multinet

    # Create a new multilayer network
    network = multinet.multi_layer_network()

    # Add edges within layers
    network.add_edges([
        ['A', 'layer1', 'B', 'layer1', 1],
        ['B', 'layer1', 'C', 'layer1', 1],
        ['A', 'layer2', 'B', 'layer2', 1],
    ], input_type="list")

    # Display basic statistics
    network.basic_stats()

    # Visualize
    from py3plex.visualization.multilayer import draw_multilayer_default
    draw_multilayer_default([network], display=True)

Load from file and analyze:

.. code-block:: python

    # Load from edge list
    network = multinet.multi_layer_network().load_network(
        "data.edgelist", input_type="edgelist", directed=False)

    # Compute multilayer statistics
    from py3plex.algorithms.statistics import multilayer_statistics as mls
    density = mls.layer_density(network, 'layer1')
    versatility = mls.versatility_centrality(network, centrality_type='degree')

    # Community detection
    from py3plex.algorithms.community_detection import community_wrapper
    communities = community_wrapper.best_partition(network.core_network)

Why py3plex?
============

vs. NetworkX
------------

NetworkX excels at single-layer homogeneous networks but lacks native multilayer support. py3plex builds on NetworkX while adding:

* Native multilayer data structures
* Layer-aware algorithms
* Specialized multilayer visualizations
* Heterogeneous network decomposition

vs. Other Multilayer Tools
---------------------------

py3plex provides:

* Lightweight and easy to integrate
* Comprehensive statistical measures (17+ multilayer metrics)
* Publication-ready visualizations
* Active development and research backing

Use Cases
=========

py3plex is particularly well-suited for:

* **Biological networks:** Protein-protein interactions with multiple evidence types, gene regulatory networks
* **Social networks:** Multi-platform analysis (Twitter + Facebook), relationship type analysis
* **Citation networks:** Author-paper-venue multilayer structures, knowledge graphs
* **Transportation:** Multi-modal networks (bus, train, air), urban mobility
* **Temporal networks:** Evolving social networks, dynamic community evolution

What's in this Documentation?
==============================

This documentation is organized to help different types of users find what they need quickly:

**New to py3plex?** Start with :doc:`getting_started/quickstart_5min` for a 5-minute introduction, then explore :doc:`getting_started/tutorial_10min` for a comprehensive walkthrough.

**Power users?** Jump to the :doc:`user_guide/networks` and other user guide sections for detailed how-tos, or browse the :doc:`examples/index` for working code.

**Want to understand the concepts?** Check out :doc:`concepts/multilayer_networks_101` and :doc:`concepts/py3plex_core_model` for deep conceptual explanations.

**Deploying in production?** See the :doc:`deployment/cli_and_docker` and :doc:`deployment/performance_scalability` guides.

**Contributing?** Read the :doc:`dev/development_guide` and :doc:`dev/contributing` pages.

Documentation Contents
======================

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting_started/quickstart_5min
   getting_started/tutorial_10min
   getting_started/installation
   getting_started/common_issues

.. toctree::
   :maxdepth: 2
   :caption: Concepts & Architecture

   concepts/multilayer_networks_101
   concepts/py3plex_core_model
   concepts/design_principles
   concepts/algorithm_landscape

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   user_guide/networks
   user_guide/statistics
   user_guide/community_detection
   user_guide/random_walks_embeddings
   user_guide/io_and_formats
   user_guide/visualization
   dsl_guide
   user_guide/recipes_and_workflows

.. toctree::
   :maxdepth: 2
   :caption: Environments & Deployment

   deployment/cli_and_docker
   deployment/performance_scalability

.. toctree::
   :maxdepth: 2
   :caption: Py3plex GUI

   gui/gui_user_guide
   gui/gui_deployment
   gui/gui_api_reference
   gui/gui_architecture
   gui/gui_testing

.. toctree::
   :maxdepth: 2
   :caption: Developer & Contributor Docs

   dev/development_guide
   dev/code_architecture
   dev/repo_layout
   dev/contributing

.. toctree::
   :maxdepth: 1
   :caption: Examples

   examples/index

.. toctree::
   :maxdepth: 2
   :caption: Reference & Citation

   reference/algorithm_reference
   reference/api_index
   reference/citation_and_acknowledgements

Examples
========

The best way to learn py3plex is through examples.

All examples are available in the `examples/ directory <https://github.com/SkBlaz/Py3Plex/tree/master/examples>`_.

Key examples:

* ``tutorial_10min.py`` - Executable version of the 10-minute tutorial
* ``example_random_walks.py`` - Random walk primitives (Node2Vec, DeepWalk)
* ``example_multilayer_visualization.py`` - Network visualization
* ``example_community_detection.py`` - Community detection with Louvain and Infomap
* ``example_network_decomposition.py`` - Meta-path feature extraction
* ``example_multilayer_statistics.py`` - Computing multilayer metrics
* ``example_n2v_embedding.py`` - Node2Vec embeddings
* ``example_label_propagation.py`` - Semi-supervised learning

Citation
========

If you use py3plex in your research, please cite:

.. code-block:: bibtex

    @Article{Skrlj2019,
      author={Škrlj, Blaž and Kralj, Jan and Lavrač, Nada},
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
