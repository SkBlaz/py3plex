.. _gui-chapter:

The Py3plex GUI (Overview)
=======================================

The py3plex GUI is a web-based interface for interactive multilayer network exploration. It provides point-and-click access to py3plex features without requiring programming. **For detailed deployment configurations and production setup, see Appendix B.**

.. admonition:: Status: Experimental
   :class: warning

   The py3plex GUI is **experimental** and designed for **local use only**.
   It is not hardened for public internet deployment. Use for exploration and
   learning, not production analysis.

What is the Py3plex GUI?
-------------------------

The GUI is a FastAPI + SvelteKit web application that provides:

* **Network upload** — Load networks from files (edgelist, GraphML, JSON)
* **Interactive visualization** — D3.js-powered network rendering
* **Query interface** — Execute DSL queries via web forms
* **Analysis workflows** — Common operations (centrality, communities) without coding
* **Export results** — Download analysis outputs as CSV/JSON

**Target users:** Researchers learning py3plex, educators demonstrating concepts, non-programmers exploring networks.

Architecture
------------

Technology Stack
~~~~~~~~~~~~~~~~

* **Backend:** FastAPI (Python) — Fast, async HTTP server
* **Frontend:** SvelteKit (JavaScript) — Reactive UI framework
* **Visualization:** D3.js (static), Plotly (interactive)
* **API:** RESTful HTTP endpoints for network operations
* **Storage:** Local filesystem for uploads (no database)

**Component structure:**

.. code-block:: text

    gui/
    ├── api/              # FastAPI backend
    │   ├── app.py        # Main server
    │   ├── routes/       # API endpoints
    │   └── models/       # Data models
    ├── frontend/         # SvelteKit app
    │   ├── src/
    │   │   ├── routes/   # Pages
    │   │   └── lib/      # Components
    │   └── static/       # Assets
    └── uploads/          # Temporary file storage

**For detailed architecture documentation, see:** ``docfiles/gui/gui_architecture.rst``

Running Locally
---------------

Installation
~~~~~~~~~~~~

Install py3plex with GUI dependencies:

.. code-block:: bash

    # Install with GUI extras
    pip install 'py3plex[gui]'
    
    # Or from source
    cd py3plex
    pip install -e '.[gui]'

Quickstart with Docker Compose
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The recommended way to run the GUI locally is using Docker Compose:

.. code-block:: bash

    # Navigate to GUI directory
    cd gui
    
    # Start all services (API, frontend, Redis, worker)
    docker-compose up -d
    
    # Access the GUI at http://localhost:8080
    # API available at http://localhost:8000
    # Flower (task monitor) at http://localhost:5555

**Services started:**

* **API:** FastAPI backend on port 8000 (uvicorn server) - internal
* **Frontend:** SvelteKit dev server on port 5173 - internal
* **Nginx:** Reverse proxy on port 8080 - **access GUI here**
* **Redis:** Task queue backend on port 6379 - internal
* **Worker:** Celery worker for background tasks - internal

**Access the GUI at http://localhost:8080** - Nginx routes requests to the appropriate backend services.

Manual Development Setup
~~~~~~~~~~~~~~~~~~~~~~~~~

For development without Docker:

.. code-block:: bash

    # Terminal 1: Start backend
    cd gui/api
    pip install -r requirements.txt
    uvicorn app.main:app --reload --port 8000
    
    # Terminal 2: Start frontend
    cd gui/frontend
    npm install
    npm run dev
    
    # Open browser to http://localhost:5173

**Note:** Manual setup requires Redis running separately for background tasks.

Configuration
~~~~~~~~~~~~~

Basic configuration in ``gui/api/config.py``:

.. code-block:: python

    # Development settings
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 8000
    
    # File handling
    UPLOAD_FOLDER = './uploads'
    MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100 MB
    
    # Analysis limits
    MAX_NODES = 10000  # Prevent performance issues

Key Workflows
-------------

Upload and Explore
~~~~~~~~~~~~~~~~~~

**Basic workflow:**

1. **Upload network** — Click "Upload Network", select file (edgelist, GraphML, etc.)
2. **View statistics** — See node count, edge count, layer info
3. **Visualize** — Interactive network rendering with zoom/pan
4. **Layer selection** — Toggle layers on/off for focused viewing
5. **Export** — Download visualization as PNG or SVG

Query Interface
~~~~~~~~~~~~~~~

Execute DSL queries without writing code:

1. Navigate to "Query" tab
2. Build query using form:
   
   * Select target: nodes or edges
   * Choose layers
   * Add filters (degree, centrality, etc.)
   * Select measures to compute
   * Set ordering and limits

3. Click "Execute"
4. View results in table
5. Export as CSV or JSON

**Example:** "Find top 20 nodes by betweenness centrality in the social layer"

Analysis Pipelines
~~~~~~~~~~~~~~~~~~

Pre-built workflows for common analyses:

* **Community Detection** — Run Louvain or Infomap, visualize communities
* **Centrality Analysis** — Compute degree, betweenness, PageRank
* **Layer Comparison** — Compare statistics across layers
* **Ego Networks** — Extract neighborhoods around selected nodes

Each pipeline provides a guided interface with sensible defaults.

Limitations and Safety
----------------------

Security Considerations
~~~~~~~~~~~~~~~~~~~~~~~

**⚠ WARNING:** The GUI is **NOT secure for public deployment**.

* **No authentication** — Anyone with URL access can use it
* **No rate limiting** — Vulnerable to resource exhaustion
* **No input sanitization** — File uploads not sandboxed
* **No HTTPS** — Data transmitted in plaintext

**Safe use cases:**

* Local machine only (``localhost``)
* Trusted network (lab/office LAN)
* Single-user exploration

**Unsafe use cases:**

* Public internet exposure
* Multi-tenant environments
* Sensitive data processing

**For production deployment:** See Appendix B for authentication, reverse proxy, and security hardening.

Scalability Limits
~~~~~~~~~~~~~~~~~~

Performance degrades with network size:

* **<1,000 nodes** — Full interactivity, all features work well
* **1,000-5,000 nodes** — Some slowness, simplify visualizations
* **5,000-10,000 nodes** — Limited features, use minimal layouts
* **>10,000 nodes** — **Use CLI/library instead**, GUI becomes unusable

**Tips for large networks:**

* Use layer filtering to reduce size
* Disable interactive visualization
* Export to CSV and analyze programmatically

When to Use the GUI vs CLI
---------------------------

**Use GUI for:**

* **Exploratory analysis** — Quick network inspection and hypothesis testing
* **Learning** — Understanding py3plex features interactively
* **Demonstration** — Presenting to non-programmers or stakeholders
* **Rapid prototyping** — Testing analysis ideas before writing code

**Use CLI/library for:**

* **Large networks** — >5,000 nodes
* **Production workflows** — Automated, reproducible pipelines
* **Complex analyses** — Chaining multiple operations
* **Performance-critical tasks** — Maximum speed and control
* **Reproducibility** — Version-controlled scripts

Summary
-------

The py3plex GUI provides:

* **Interactive exploration** without requiring programming skills
* **Visual network rendering** with D3.js and Plotly
* **Query interface** for executing DSL queries via forms
* **Pre-built workflows** for common analyses
* **Local deployment** for individual researchers and small teams

**Key limitations:**

* **Experimental status** — Not production-ready
* **Security** — Local use only, no public deployment
* **Performance** — Limited to small/medium networks (<5,000 nodes)
* **Features** — Advanced capabilities require CLI/library

**For deployment details and security hardening, see Appendix B.**
**For GUI API reference, see:** ``docfiles/gui/gui_api_reference.rst``
