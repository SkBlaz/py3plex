The Py3plex GUI (Overview)
=======================================

*TODO: High-level GUI overview—detailed deployment in Appendix B*

What is the Py3plex GUI?
-------------------------

[Web-based interface for interactive network exploration]

Key Features
~~~~~~~~~~~~

* **Network upload** — Load from files
* **Interactive visualization** — Explore structure visually
* **Query interface** — DSL queries via web UI
* **Analysis workflows** — Common operations without coding

Architecture
------------

Technology Stack
~~~~~~~~~~~~~~~~

* **Backend:** FastAPI (Python)
* **Frontend:** SvelteKit (JavaScript)
* **Visualization:** D3.js, Plotly
* **API:** RESTful HTTP endpoints

[For detailed architecture → See Appendix or docfiles/gui/gui_architecture.rst]

Running Locally
---------------

Quick Start
~~~~~~~~~~~

.. code-block:: bash

    # Install with GUI dependencies
    pip install 'py3plex[gui]'
    
    # Start development server
    cd gui
    python app.py

The GUI will be available at ``http://localhost:5000``.

Configuration
~~~~~~~~~~~~~

.. code-block:: python

    # gui/config.py
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    UPLOAD_FOLDER = './uploads'

Key Workflows
-------------

Upload and Explore
~~~~~~~~~~~~~~~~~~

1. Upload network file (edgelist, GraphML, JSON)
2. View statistics and layer information
3. Interactive visualization
4. Export results

Query Interface
~~~~~~~~~~~~~~~

[Execute DSL queries via web form]

Analysis Pipelines
~~~~~~~~~~~~~~~~~~

[Pre-built workflows: community detection, centrality, etc.]

Limitations and Safety
----------------------

Security Considerations
~~~~~~~~~~~~~~~~~~~~~~~

**WARNING:** The GUI is designed for **local use only**, not for public internet exposure.

* No authentication by default
* No rate limiting
* No input sanitization for public use
* File uploads are not sandboxed

**For production:** See Appendix B for:

* Nginx reverse proxy configuration
* Authentication setup
* Security hardening checklist

Scalability Limits
~~~~~~~~~~~~~~~~~~

* **Small networks** (<1k nodes) — Full interactivity
* **Medium networks** (1k-10k nodes) — Some features slow
* **Large networks** (>10k nodes) — Use CLI instead of GUI

When to Use the GUI vs CLI
---------------------------

**Use GUI for:**

* Exploratory analysis
* Learning py3plex features
* Presenting to non-programmers
* Quick prototyping

**Use CLI/library for:**

* Large networks
* Production workflows
* Reproducible analyses
* Performance-critical tasks

Summary
-------

The py3plex GUI provides:

* **Interactive exploration** without coding
* **Visualization** for understanding structure
* **Query interface** for the DSL
* **Local deployment** for individual researchers

**Key limitations:**

* Not hardened for public deployment
* Performance limited for large networks
* Advanced features require CLI/library

[For deployment details → Appendix B]
[For API reference → docfiles/gui/gui_api_reference.rst]

*Source files:*
- docfiles/gui/ (all files)
- gui/ (application code)
- Deployment details → Appendix B
