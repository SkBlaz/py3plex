GUI API Reference
==================

This reference documents the REST API endpoints provided by the py3plex GUI backend. All endpoints live under ``/api`` in development unless otherwise noted.

Overview
--------

The py3plex GUI exposes a REST API for:

* Uploading network data
* Running analyses
* Generating visualizations
* Exporting results

Conventions
-----------

* **Base URL (development):** ``http://localhost:8000/api``
* **Authentication:** None (add in production)
* **Content types:** JSON for most endpoints; ``multipart/form-data`` for uploads
* **IDs:** ``graph_id`` is returned by upload; asynchronous jobs return ``job_id``
* **Async workflow:** Layout, centrality, and community detection run as Celery jobs. Each request returns a ``job_id``; poll ``GET /api/jobs/{job_id}`` for progress/results.
* **Errors:** FastAPI returns JSON payloads with ``detail``; job failures appear in the job status payload.
* **Docs:** Interactive docs live at ``/api/docs`` (Swagger UI) and ``/api/redoc``.

Health
------

Health Check
~~~~~~~~~~~~

Verify the API is reachable.

**Endpoint:** ``GET /api/health``

**Response:**

.. code-block:: json

    {
      "status": "ok",
      "version": "0.1.0"
    }

Uploads
-------

Upload Network
~~~~~~~~~~~~~~

Upload a network file and register it in the in-memory registry. The server detects the format and parses to NetworkX; a ``graph_id`` is returned for subsequent calls.

**Endpoint:** ``POST /api/upload``

**Parameters:**

* ``file`` (form-data, required) - Network file (edgelist, multilayer edgelist, gml, gpickle, txt)

**Response:**

.. code-block:: json

    {
      "graph_id": "b3e5cfd5-7f6b-4b30-8c3e-220f9a9c0de2",
      "filename": "network.edgelist",
      "message": "File uploaded and parsed successfully"
    }

Graph Queries
-------------

Get Graph Summary
~~~~~~~~~~~~~~~~~

Return node/edge counts, detected layers, and node attribute names.

**Endpoint:** ``GET /api/graphs/{graph_id}/summary``

**Response:**

.. code-block:: json

    {
      "graph_id": "b3e5cfd5-7f6b-4b30-8c3e-220f9a9c0de2",
      "nodes": 120,
      "edges": 340,
      "layers": ["default"],
      "attributes": ["layer", "weight"]
    }

Sample Graph
~~~~~~~~~~~~

Return a downsampled subgraph for preview (defaults to 500 nodes max). Small graphs return untouched; larger graphs include ``sampled: true`` and report totals.

**Endpoint:** ``GET /api/graphs/{graph_id}/sample``

**Query Parameters:**

* ``max_nodes`` (optional, default: 500)

**Response (full graph small enough):**

.. code-block:: json

    {
      "graph_id": "b3e5cfd5-7f6b-4b30-8c3e-220f9a9c0de2",
      "nodes": 120,
      "edges": 340,
      "layers": ["default"],
      "attributes": ["layer", "weight"]
    }

**Response (sampled):**

.. code-block:: json

    {
      "graph_id": "b3e5cfd5-7f6b-4b30-8c3e-220f9a9c0de2",
      "sampled": true,
      "nodes": 500,
      "edges": 910,
      "total_nodes": 1200,
      "total_edges": 2400
    }

Get Node Positions
~~~~~~~~~~~~~~~~~~

Retrieve node coordinates for rendering. If positions are missing, a layout is generated on the fly for smaller graphs; very large graphs may skip automatic layout.

**Endpoint:** ``GET /api/graphs/{graph_id}/positions``

**Response:**

.. code-block:: json

    {
      "graph_id": "b3e5cfd5-7f6b-4b30-8c3e-220f9a9c0de2",
      "positions": [
        {"node_id": "n1", "x": 0.12, "y": -0.33, "layer": "default"},
        {"node_id": "n2", "x": -0.48, "y": 0.05, "layer": "default"}
      ]
    }

Filter Graph
~~~~~~~~~~~~

Create a filtered subgraph and receive its new ``graph_id``. Filters combine with logical AND.

**Endpoint:** ``POST /api/graphs/{graph_id}/filter``

**Body (any combination is optional):**

* ``attribute`` - Node attribute to filter on (not applied by default)
* ``min_degree`` / ``max_degree`` - Degree bounds
* ``layers`` - Keep only edges in these layers
* ``communities`` - Keep nodes in the provided communities

**Response:**

.. code-block:: json

    {
      "subgraph_id": "4e468de5-3a87-4ac8-814d-4f27b9b9af69",
      "original_graph_id": "b3e5cfd5-7f6b-4b30-8c3e-220f9a9c0de2",
      "nodes": 80,
      "edges": 210
    }

Analysis Jobs (Async)
---------------------

The endpoints below enqueue Celery jobs and return a ``job_id`` immediately. Poll ``GET /api/jobs/{job_id}`` for progress, results, and artifact locations.

Layout
~~~~~~

Queue a layout computation.

**Endpoint:** ``POST /api/graphs/{graph_id}/layout``

**Body:**

* ``algorithm`` (optional) - ``spring`` | ``force_atlas`` | ``kamada_kawai`` | ``circular`` | ``random`` (default: ``spring``)
* ``seed`` (optional) - Integer seed (default: 42)
* ``dimensions`` (optional) - ``2`` or ``3`` (default: 2)
* ``iterations`` (optional) - Iteration budget (default: 50)

**Response:**

.. code-block:: json

    {
      "job_id": "2c1b6f35-2b4a-4ce2-9be9-3c77f2a5c4c0",
      "status": "queued"
    }

Centrality
~~~~~~~~~~

Queue centrality computation for one or more metrics.

**Endpoint:** ``POST /api/graphs/{graph_id}/analysis/centrality``

**Body:**

* ``metrics`` (required) - List of ``degree``, ``betweenness``, ``closeness``, ``eigenvector``, ``pagerank``
* ``layers`` (optional) - Restrict to these layers

**Response:**

.. code-block:: json

    {
      "job_id": "7e5a3b9d-6c3c-4c39-8f71-1b7f76dbd1c9",
      "status": "queued"
    }

Community Detection
~~~~~~~~~~~~~~~~~~~

Queue community detection.

**Endpoint:** ``POST /api/graphs/{graph_id}/analysis/community``

**Body:**

* ``algorithm`` (optional) - ``louvain`` | ``label_propagation`` | ``greedy_modularity`` (default: ``louvain``)
* ``resolution`` (optional) - Resolution parameter (default: ``1.0``)
* ``seed`` (optional) - Integer seed (default: 42)

**Response:**

.. code-block:: json

    {
      "job_id": "8f3a4b42-35ec-4f65-91da-2de5c0b01407",
      "status": "queued"
    }

Jobs
----

Get Job Status
~~~~~~~~~~~~~~

Poll for Celery job progress and results. Progress runs from 0 to 100; completed jobs may include artifacts. Failed jobs include an ``error`` string.

**Endpoint:** ``GET /api/jobs/{job_id}``

**Responses:**

Queued/pending:

.. code-block:: json

    {
      "job_id": "2c1b6f35-2b4a-4ce2-9be9-3c77f2a5c4c0",
      "status": "queued",
      "progress": 0
    }

Running with progress metadata:

.. code-block:: json

    {
      "job_id": "2c1b6f35-2b4a-4ce2-9be9-3c77f2a5c4c0",
      "status": "running",
      "progress": 45,
      "phase": "computing layout"
    }

Completed:

.. code-block:: json

    {
      "job_id": "2c1b6f35-2b4a-4ce2-9be9-3c77f2a5c4c0",
      "status": "completed",
      "progress": 100,
      "result": {
        "graph_id": "b3e5cfd5-7f6b-4b30-8c3e-220f9a9c0de2",
        "algorithm": "spring",
        "num_nodes": 120,
        "artifacts": ["/workspace/data/artifacts/<graph_id>/<job_id>/layout.json"]
      },
      "artifacts": ["/workspace/data/artifacts/<graph_id>/<job_id>/layout.json"]
    }

Failed:

.. code-block:: json

    {
      "job_id": "2c1b6f35-2b4a-4ce2-9be9-3c77f2a5c4c0",
      "status": "failed",
      "error": "Graph not found"
    }

Cancel Job
~~~~~~~~~~

Best-effort cancellation for a running job. The task may still complete if already executing.

**Endpoint:** ``DELETE /api/jobs/{job_id}``

**Response:**

.. code-block:: json

    {
      "message": "Job cancellation requested",
      "job_id": "2c1b6f35-2b4a-4ce2-9be9-3c77f2a5c4c0"
    }

Workspace Bundles
-----------------

Save Workspace
~~~~~~~~~~~~~~

Persist the current graph and optional frontend state into a bundle.

**Endpoint:** ``POST /api/workspaces/save``

**Body:**

* ``name`` (required) - Workspace label
* ``graph_id`` (required) - Graph to bundle
* ``view_state`` (optional) - UI state snapshot

**Response:**

.. code-block:: json

    {
      "workspace_id": "d6d5f6c0-4f3f-4b3d-8d22-6c0cba9b7a77",
      "filename": "workspace_d6d5f6c0.zip",
      "message": "Workspace saved"
    }

Load Workspace
~~~~~~~~~~~~~~

Load a workspace by ID and return the graph/view state. ``workspace_id`` is passed as a query parameter.

**Endpoint:** ``POST /api/workspaces/load?workspace_id={workspace_id}``

**Response:**

.. code-block:: json

    {
      "graph_id": "b3e5cfd5-7f6b-4b30-8c3e-220f9a9c0de2",
      "view_state": {},
      "message": "Workspace loaded"
    }

Cache Management
----------------

Cache Stats
~~~~~~~~~~~

Inspect the in-memory caches.

**Endpoint:** ``GET /api/cache/stats``

**Response:**

.. code-block:: json

    {
      "status": "ok",
      "stats": {
        "summary_cache_size": 2,
        "position_cache_size": 1,
        "graph_registry_size": 3
      }
    }

Clear All Cache
~~~~~~~~~~~~~~~

Purge summary/position caches and the registry. Clearing the registry invalidates all existing ``graph_id`` values.

**Endpoint:** ``DELETE /api/cache``

**Response:**

.. code-block:: json

    {
      "status": "ok",
      "message": "All caches cleared"
    }

Clear Graph Cache
~~~~~~~~~~~~~~~~~

Purge cached data for a specific graph.

**Endpoint:** ``DELETE /api/cache/{graph_id}``

**Response:**

.. code-block:: json

    {
      "status": "ok",
      "message": "Cache cleared for graph b3e5cfd5-7f6b-4b30-8c3e-220f9a9c0de2"
    }

Error Handling
--------------

Error Response Format
~~~~~~~~~~~~~~~~~~~~~

FastAPI returns standard error payloads. Typical shapes:

Validation error:

.. code-block:: json

    {
      "detail": [
        {
          "loc": ["body", "metrics", 0],
          "msg": "value is not a valid enumeration member; permitted: 'degree', 'betweenness', 'closeness', 'eigenvector', 'pagerank'",
          "type": "type_error.enum"
        }
      ]
    }

Not found:

.. code-block:: json

    {
      "detail": "Graph not found"
    }

Job failures surface in the job status payload as ``status: "failed"`` and an ``error`` string.

Usage Examples
--------------

Python Client
~~~~~~~~~~~~~

.. code-block:: python

    import requests
    
    BASE_URL = "http://localhost:8000/api"
    
    # Upload a graph
    with open("network.edgelist", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/upload",
            files={"file": f}
        )
    
    graph_id = response.json()["graph_id"]
    print(f"Uploaded graph: {graph_id}")
    
    # Queue community detection
    response = requests.post(
        f"{BASE_URL}/graphs/{graph_id}/analysis/community",
        json={
            "algorithm": "louvain",
            "resolution": 1.0
        }
    )
    
    job_id = response.json()["job_id"]
    print(f"Community job queued: {job_id}")
    
    # Poll job until completion
    status = requests.get(f"{BASE_URL}/jobs/{job_id}").json()
    print(status)

cURL Examples
~~~~~~~~~~~~~

.. code-block:: bash

    # Upload graph
    curl -X POST http://localhost:8000/api/upload \
      -F "file=@network.edgelist"
    
    # Get summary
    curl http://localhost:8000/api/graphs/<graph_id>/summary
    
    # Queue centrality
    curl -X POST http://localhost:8000/api/graphs/<graph_id>/analysis/centrality \
      -H "Content-Type: application/json" \
      -d '{"metrics":["betweenness","pagerank"]}'
    
    # Poll job
    curl http://localhost:8000/api/jobs/<job_id>

JavaScript/Fetch Example
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: javascript

    const BASE_URL = 'http://localhost:8000/api';
    
    // Upload graph
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    const response = await fetch(`${BASE_URL}/upload`, {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    console.log(`Uploaded graph: ${data.graph_id}`);
    
    // Queue community detection
    const analysisResponse = await fetch(`${BASE_URL}/graphs/${data.graph_id}/analysis/community`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        algorithm: 'louvain'
      })
    });
    
    const communities = await analysisResponse.json();
    console.log(`Job queued: ${communities.job_id}`);

Related Documentation
---------------------

* :doc:`gui_user_guide` - Using the web interface
* :doc:`gui_deployment` - Deploying in production
* :doc:`gui_architecture` - Technical architecture
* :doc:`gui_testing` - Testing the API

**External Resources:**

* REST API Best Practices: https://restfulapi.net/
* FastAPI Documentation: https://fastapi.tiangolo.com/
