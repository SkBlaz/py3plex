**********************************
Py3plex Documentation
**********************************

.. image:: https://github.com/SkBlaz/py3plex/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/SkBlaz/py3plex/actions/workflows/tests.yml
   :alt: Tests

.. image:: https://github.com/SkBlaz/py3plex/actions/workflows/code-quality.yml/badge.svg
   :target: https://github.com/SkBlaz/py3plex/actions/workflows/code-quality.yml
   :alt: Code Quality

**py3plex** enables scalable analysis and visualization of **multilayer** and **multiplex** networks in Python, supporting complex network modeling across diverse scientific and applied domains.

Overview
========

py3plex is a **lightweight Python library** designed specifically for analyzing and visualizing **heterogeneous** and **multilayer networks**. Unlike traditional network analysis tools that focus on homogeneous networks (single node and edge type), py3plex provides specialized capabilities for networks with:

* Multiple node types
* Multiple edge types  
* Multiple layers of interaction
* Temporal dynamics
* Heterogeneous attributes

**Target Users:** Researchers in network science, computational biology, complex systems, social network analysis, and applied network modeling.

**Key Features:**

* **Native support** for multiplex and multilayer network structures
* **Diagonal projection visualization** for large multilayer networks
* **Comprehensive multilayer centrality measures**
* **Community detection** across network layers
* **Network decomposition** and feature extraction
* **Semantic enrichment** with external knowledge bases
* **Integration** with NetworkX, igraph, and other graph libraries

Installation
============

Install from GitHub
-------------------

.. code-block:: bash

    pip install git+https://github.com/SkBlaz/py3plex.git

Docker Installation (Alternative)
----------------------------------

Py3plex is also available as a Docker container with all dependencies pre-installed:

.. code-block:: bash

    # Clone and build
    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    docker build -t py3plex:latest .

    # Run commands
    docker run --rm py3plex:latest --version
    docker run --rm py3plex:latest selftest

See :doc:`tutorials/docker_usage` for complete Docker documentation.

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

**vs. NetworkX:**
NetworkX excels at **single-layer homogeneous networks** but lacks native multilayer support. py3plex builds on NetworkX while adding:

* **Native multilayer data structures**
* **Layer-aware algorithms**
* **Specialized multilayer visualizations**
* **Heterogeneous network decomposition**

**vs. Other Multilayer Tools:**
py3plex provides:

* **Lightweight** and easy to integrate
* **Comprehensive statistical measures** (17+ multilayer metrics)
* **Publication-ready visualizations**
* **Active development** and research backing

Use Cases
=========

py3plex is particularly well-suited for:

* **Biological networks:** Protein-protein interactions with multiple evidence types, gene regulatory networks
* **Social networks:** Multi-platform analysis (Twitter + Facebook), relationship type analysis
* **Citation networks:** Author-paper-venue multilayer structures, knowledge graphs
* **Transportation:** Multi-modal networks (bus, train, air), urban mobility
* **Temporal networks:** Evolving social networks, dynamic community evolution

Documentation Contents
======================

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart
   10min_tutorial
   core_idea

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   basic_usage
   basic_usage_analysis
   basic_usage_analysis_multiplex
   multilayer_concepts
   recipes
   visualization
   visualization_guide
   dependencies_guide
   networkx_interop
   algorithm_guide
   performance
   performance_guide

.. toctree::
   :maxdepth: 2
   :caption: Tutorials

   tutorials/cli_usage
   tutorials/docker_usage
   tutorials/csv_loading
   tutorials/multilayer_centrality
   tutorials/multilayer_modularity
   tutorials/community_detection
   tutorials/network_decomposition
   tutorials/incidence_gadget_encoding
   multilayer_centrality_matrix_functions
   random_walks
   supra

.. toctree::
   :maxdepth: 2
   :caption: Advanced Topics

   learning
   learning2
   learning3

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   apidocs
   core
   community_detection

.. toctree::
   :maxdepth: 2
   :caption: Contributing

   contributing
   development
   architecture
   citation

.. toctree::
   :maxdepth: 1
   :caption: Additional Resources

   acknowledgements

Examples
========

**The best way to learn py3plex is through examples!**

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
