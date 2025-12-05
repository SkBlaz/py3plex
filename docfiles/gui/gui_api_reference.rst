GUI API Reference
==================

This reference documents the REST API endpoints provided by the py3plex web interface.

Overview
--------

The py3plex GUI provides a REST API for:

* Uploading network data
* Running analyses
* Generating visualizations
* Exporting results

**Base URL:** ``http://localhost:5000/api`` (development)

**Authentication:** Currently no authentication (add in production)

**Response Format:** JSON

General Endpoints
-----------------

Health Check
~~~~~~~~~~~~

Check if the server is running.

**Endpoint:** ``GET /health``

**Response:**

.. code-block:: json

    {
      "status": "healthy",
      "version": "0.95",
      "timestamp": "2025-01-23T12:00:00Z"
    }

**Status Codes:**

* 200 - Server is healthy
* 503 - Server is unhealthy

Server Info
~~~~~~~~~~~

Get server information.

**Endpoint:** ``GET /api/info``

**Response:**

.. code-block:: json

    {
      "py3plex_version": "0.95",
      "python_version": "3.10.0",
      "available_algorithms": ["louvain", "infomap", "node2vec"],
      "max_upload_size": 104857600
    }

Network Management
------------------

Upload Network
~~~~~~~~~~~~~~

Upload a network file for analysis.

**Endpoint:** ``POST /api/upload``

**Parameters:**

* ``file`` (form-data, required) - Network file
* ``input_type`` (form-data, required) - File format (edgelist, multiedgelist, graphml, etc.)
* ``directed`` (form-data, optional) - Boolean, default false

**Request Example:**

.. code-block:: bash

    curl -X POST http://localhost:5000/api/upload \
      -F "file=@network.edgelist" \
      -F "input_type=edgelist" \
      -F "directed=false"

**Response:**

.. code-block:: json

    {
      "success": true,
      "network_id": "abc123",
      "num_nodes": 100,
      "num_edges": 450,
      "num_layers": 3,
      "message": "Network uploaded successfully"
    }

**Status Codes:**

* 200 - Success
* 400 - Invalid file or parameters
* 413 - File too large
* 500 - Server error

List Networks
~~~~~~~~~~~~~

List all uploaded networks.

**Endpoint:** ``GET /api/networks``

**Response:**

.. code-block:: json

    {
      "networks": [
        {
          "id": "abc123",
          "filename": "network.edgelist",
          "uploaded_at": "2025-01-23T12:00:00Z",
          "num_nodes": 100,
          "num_edges": 450
        }
      ]
    }

Get Network Info
~~~~~~~~~~~~~~~~

Get detailed information about a specific network.

**Endpoint:** ``GET /api/networks/<network_id>``

**Response:**

.. code-block:: json

    {
      "id": "abc123",
      "filename": "network.edgelist",
      "num_nodes": 100,
      "num_edges": 450,
      "num_layers": 3,
      "layers": ["layer1", "layer2", "layer3"],
      "statistics": {
        "density": 0.045,
        "clustering": 0.32
      }
    }

Delete Network
~~~~~~~~~~~~~~

Delete an uploaded network.

**Endpoint:** ``DELETE /api/networks/<network_id>``

**Response:**

.. code-block:: json

    {
      "success": true,
      "message": "Network deleted successfully"
    }

Analysis Endpoints
------------------

Run Community Detection
~~~~~~~~~~~~~~~~~~~~~~~

Detect communities in a network.

**Endpoint:** ``POST /api/analysis/communities``

**Parameters:**

* ``network_id`` (required) - Network ID
* ``algorithm`` (required) - Algorithm name (louvain, leiden, infomap)
* ``gamma`` (optional) - Resolution parameter (default: 1.0)
* ``omega`` (optional) - Inter-layer coupling (default: 1.0)

**Request:**

.. code-block:: json

    {
      "network_id": "abc123",
      "algorithm": "louvain",
      "gamma": 1.0,
      "omega": 1.0
    }

**Response:**

.. code-block:: json

    {
      "success": true,
      "num_communities": 5,
      "modularity": 0.42,
      "partition": {
        "node1": 0,
        "node2": 0,
        "node3": 1
      }
    }

Compute Statistics
~~~~~~~~~~~~~~~~~~

Compute network statistics.

**Endpoint:** ``POST /api/analysis/statistics``

**Parameters:**

* ``network_id`` (required) - Network ID
* ``metrics`` (required) - List of metrics to compute

**Request:**

.. code-block:: json

    {
      "network_id": "abc123",
      "metrics": ["density", "clustering", "degree_distribution"]
    }

**Response:**

.. code-block:: json

    {
      "success": true,
      "statistics": {
        "density": 0.045,
        "clustering": 0.32,
        "degree_distribution": {
          "1": 10,
          "2": 25,
          "3": 30
        }
      }
    }

Compute Centrality
~~~~~~~~~~~~~~~~~~

Compute node centrality measures.

**Endpoint:** ``POST /api/analysis/centrality``

**Parameters:**

* ``network_id`` (required) - Network ID
* ``measure`` (required) - Centrality measure (degree, betweenness, pagerank, eigenvector)
* ``layer`` (optional) - Specific layer to analyze

**Request:**

.. code-block:: json

    {
      "network_id": "abc123",
      "measure": "betweenness",
      "layer": "layer1"
    }

**Response:**

.. code-block:: json

    {
      "success": true,
      "centrality": {
        "node1": 0.42,
        "node2": 0.35,
        "node3": 0.15
      }
    }

Generate Embeddings
~~~~~~~~~~~~~~~~~~~

Generate node embeddings.

**Endpoint:** ``POST /api/analysis/embeddings``

**Parameters:**

* ``network_id`` (required) - Network ID
* ``method`` (required) - Embedding method (node2vec, deepwalk)
* ``dimensions`` (optional) - Embedding dimensions (default: 128)
* ``walk_length`` (optional) - Walk length (default: 80)
* ``num_walks`` (optional) - Walks per node (default: 10)
* ``p`` (optional) - Return parameter (default: 1.0)
* ``q`` (optional) - In-out parameter (default: 1.0)

**Request:**

.. code-block:: json

    {
      "network_id": "abc123",
      "method": "node2vec",
      "dimensions": 128,
      "walk_length": 80,
      "num_walks": 10,
      "p": 1.0,
      "q": 1.0
    }

**Response:**

.. code-block:: json

    {
      "success": true,
      "embedding_id": "emb456",
      "dimensions": 128,
      "num_nodes": 100
    }

Visualization Endpoints
-----------------------

Generate Layout
~~~~~~~~~~~~~~~

Compute network layout.

**Endpoint:** ``POST /api/visualization/layout``

**Parameters:**

* ``network_id`` (required) - Network ID
* ``algorithm`` (required) - Layout algorithm (force, spring, circular, diagonal)
* ``iterations`` (optional) - Number of iterations (default: 50)

**Request:**

.. code-block:: json

    {
      "network_id": "abc123",
      "algorithm": "force",
      "iterations": 100
    }

**Response:**

.. code-block:: json

    {
      "success": true,
      "layout_id": "layout789",
      "positions": {
        "node1": [0.5, 0.3],
        "node2": [0.6, 0.8]
      }
    }

Render Visualization
~~~~~~~~~~~~~~~~~~~~

Generate network visualization image.

**Endpoint:** ``POST /api/visualization/render``

**Parameters:**

* ``network_id`` (required) - Network ID
* ``layout_id`` (optional) - Pre-computed layout ID
* ``width`` (optional) - Image width (default: 800)
* ``height`` (optional) - Image height (default: 600)
* ``format`` (optional) - Output format (png, svg, pdf, default: png)

**Request:**

.. code-block:: json

    {
      "network_id": "abc123",
      "layout_id": "layout789",
      "width": 1200,
      "height": 900,
      "format": "png"
    }

**Response:**

Returns image file with appropriate Content-Type header.

**Status Codes:**

* 200 - Success (returns image)
* 400 - Invalid parameters
* 404 - Network or layout not found

Export Endpoints
----------------

Export Network
~~~~~~~~~~~~~~

Export network in different formats.

**Endpoint:** ``GET /api/export/network/<network_id>``

**Query Parameters:**

* ``format`` (required) - Export format (graphml, gml, edgelist, json, arrow)

**Example:**

.. code-block:: bash

    curl http://localhost:5000/api/export/network/abc123?format=graphml \
      -o output.graphml

**Response:**

Returns file in requested format.

Export Analysis Results
~~~~~~~~~~~~~~~~~~~~~~~

Export analysis results as JSON or CSV.

**Endpoint:** ``GET /api/export/analysis/<analysis_id>``

**Query Parameters:**

* ``format`` (optional) - Export format (json, csv, default: json)

**Example:**

.. code-block:: bash

    curl http://localhost:5000/api/export/analysis/analysis123?format=csv \
      -o results.csv

**Response:**

Returns file in requested format.

Error Handling
--------------

Error Response Format
~~~~~~~~~~~~~~~~~~~~~

All errors return a consistent JSON format:

.. code-block:: json

    {
      "success": false,
      "error": "Error message description",
      "error_code": "ERROR_CODE",
      "details": {
        "field": "Additional error details"
      }
    }

Common Error Codes
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - HTTP Status
     - Error Code
     - Description
   * - 400
     - INVALID_INPUT
     - Invalid request parameters
   * - 400
     - INVALID_FILE
     - Invalid or corrupted file
   * - 401
     - UNAUTHORIZED
     - Authentication required
   * - 404
     - NOT_FOUND
     - Resource not found
   * - 413
     - FILE_TOO_LARGE
     - Upload exceeds size limit
   * - 500
     - INTERNAL_ERROR
     - Server error
   * - 503
     - SERVICE_UNAVAILABLE
     - Service temporarily unavailable

Rate Limits
-----------

Default rate limits (configurable):

* 200 requests per day per IP
* 50 requests per hour per IP
* 10 uploads per hour per IP

Rate limit headers in responses:

.. code-block:: text

    X-RateLimit-Limit: 50
    X-RateLimit-Remaining: 45
    X-RateLimit-Reset: 1674480000

Usage Examples
--------------

Python Client
~~~~~~~~~~~~~

.. code-block:: python

    import requests
    
    BASE_URL = "http://localhost:5000/api"
    
    # Upload network
    with open("network.edgelist", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/upload",
            files={"file": f},
            data={"input_type": "edgelist", "directed": "false"}
        )
    
    network_id = response.json()["network_id"]
    print(f"Uploaded network: {network_id}")
    
    # Run community detection
    response = requests.post(
        f"{BASE_URL}/analysis/communities",
        json={
            "network_id": network_id,
            "algorithm": "louvain"
        }
    )
    
    communities = response.json()
    print(f"Found {communities['num_communities']} communities")

cURL Examples
~~~~~~~~~~~~~

.. code-block:: bash

    # Upload network
    curl -X POST http://localhost:5000/api/upload \
      -F "file=@network.edgelist" \
      -F "input_type=edgelist" \
      -F "directed=false"
    
    # Get network info
    curl http://localhost:5000/api/networks/abc123
    
    # Run analysis
    curl -X POST http://localhost:5000/api/analysis/communities \
      -H "Content-Type: application/json" \
      -d '{"network_id":"abc123","algorithm":"louvain"}'
    
    # Export network
    curl http://localhost:5000/api/export/network/abc123?format=graphml \
      -o output.graphml

JavaScript/Fetch Example
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: javascript

    const BASE_URL = 'http://localhost:5000/api';
    
    // Upload network
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('input_type', 'edgelist');
    formData.append('directed', 'false');
    
    const response = await fetch(`${BASE_URL}/upload`, {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    console.log(`Uploaded network: ${data.network_id}`);
    
    // Run analysis
    const analysisResponse = await fetch(`${BASE_URL}/analysis/communities`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        network_id: data.network_id,
        algorithm: 'louvain'
      })
    });
    
    const communities = await analysisResponse.json();
    console.log(`Found ${communities.num_communities} communities`);

Related Documentation
---------------------

* :doc:`gui_user_guide` - Using the web interface
* :doc:`gui_deployment` - Deploying in production
* :doc:`gui_architecture` - Technical architecture
* :doc:`gui_testing` - Testing the API

**External Resources:**

* REST API Best Practices: https://restfulapi.net/
* Flask-RESTful Documentation: https://flask-restful.readthedocs.io/
