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
