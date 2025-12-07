GUI: Web Interface for Network Exploration
===========================================

.. warning::

   **Development Mode Only:** The GUI is intended for local development and exploration. Do not expose it to the public internet without proper authentication and security hardening. See :doc:`gui_deployment` for production configuration.

The py3plex GUI provides a web-based interface for interactive multilayer network exploration.

**Features:**

* Load networks from various file formats without code
* Interactive, zoomable visualizations
* Compute statistics via point-and-click menus
* Detect communities and visualize them
* Export results for further analysis

**This section covers:**

* :doc:`gui_user_guide` — Loading data, exploring networks, running analyses
* :doc:`gui_deployment` — Running locally, Docker, production setup
* :doc:`gui_api_reference` — Backend API documentation
* :doc:`gui_architecture` — How the GUI is built
* :doc:`gui_testing` — Testing infrastructure

Running the GUI Locally
------------------------

**Quick start (Docker - Recommended):**

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex/gui
    
    # Copy environment configuration
    cp .env.example .env
    
    # Start all services
    make up
    
    # Open browser to http://localhost:8080

**Alternative: Install from source:**

.. code-block:: bash

    # Install with GUI extras
    pip install py3plex[gui]
    
    # Or install from source
    git clone https://github.com/SkBlaz/py3plex.git
    cd py3plex
    pip install -e ".[gui]"
    
    # Navigate to GUI directory and start services
    cd gui
    make up

The GUI will be available at ``http://localhost:8080``. See :doc:`gui_deployment` for detailed setup instructions and troubleshooting.

GUI Actions vs py3plex APIs
----------------------------

The GUI provides a point-and-click interface for common py3plex operations. Here's how GUI actions map to Python API calls:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - GUI Action
     - Equivalent Python API
   * - **Load Network** (upload file)
     - ``network = multinet.multi_layer_network().load_network(file_path, input_type="...")``
   * - **Compute Statistics** → Basic Stats
     - ``network.basic_stats()``
   * - **Compute Statistics** → Layer Density
     - ``from py3plex.algorithms.statistics import multilayer_statistics as mls`` |br|
       ``mls.layer_density(network, layer_name)``
   * - **Detect Communities** → Louvain
     - ``from py3plex.algorithms.community_detection import community_louvain`` |br|
       ``partition = community_louvain.best_partition(network.get_layers()[layer])``
   * - **Compute Centrality** → Degree
     - ``from py3plex.algorithms.multilayer_algorithms.centrality import MultilayerCentrality`` |br|
       ``calc = MultilayerCentrality(network)`` |br|
       ``degree = calc.overlapping_degree_centrality()``
   * - **Visualize Network**
     - ``from py3plex.visualization.multilayer import draw_multilayer_default`` |br|
       ``draw_multilayer_default([network], display=True)``
   * - **Export** → JSON
     - ``network.save_network("output.json", output_type="json")``

.. |br| raw:: html

   <br />

This mapping helps you transition from GUI exploration to programmatic analysis.

When to Use the GUI
-------------------

**Use GUI for:**

* Domain experts who prefer not to write Python
* Quick exploratory analysis of new datasets
* Demonstrations and teaching
* Collaborative work with mixed technical backgrounds

**Use Python library for:**

* Production pipelines and automation
* Reproducible analysis workflows
* Advanced customization
* Large-scale processing

Start with :doc:`gui_deployment` to run the GUI, then :doc:`gui_user_guide` for usage.
