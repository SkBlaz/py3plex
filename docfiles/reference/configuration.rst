Configuration & Environment
===========================

This page documents configuration options, environment variables, and file formats for py3plex.

Configuration Files
-------------------

py3plex supports configuration files for reproducible workflows. Configuration can be provided in YAML or JSON format.

**Network Configuration (YAML):**

.. code-block:: yaml

    # network_config.yaml
    network:
      input_file: "data/multilayer.edges"
      input_type: "multiedgelist"
      directed: false
      weighted: true
    
    # Load with:
    # network.load_network(**config['network'])

**Algorithm Parameters:**

.. code-block:: yaml

    # algorithm_config.yaml
    community_detection:
      algorithm: "louvain_multilayer"
      params:
        gamma: 1.0
        omega: 0.5
        random_state: 42
    
    node2vec:
      dimensions: 128
      walk_length: 80
      num_walks: 10
      p: 1.0
      q: 1.0
    
    dynamics:
      model: "SIR"
      beta: 0.3
      gamma: 0.1
      initial_infected: 0.05
      steps: 100

**Visualization Settings:**

.. code-block:: yaml

    # viz_config.yaml
    visualization:
      layout: "force_directed"
      node_size: 50
      edge_width: 2
      dpi: 300
      output_format: "png"
      color_by_layer: true

**Loading configuration:**

.. code-block:: python

    import yaml
    from py3plex.core import multinet
    
    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Use config
    network = multinet.multi_layer_network(
        directed=config['network']['directed']
    )
    network.load_network(
        config['network']['input_file'],
        input_type=config['network']['input_type']
    )

Environment Variables
---------------------

py3plex respects the following environment variables for customization:

**Data Directories:**

* ``PY3PLEX_DATA_DIR`` — Override default data directory location
  
  * Default: ``~/.py3plex/data``
  * Used for: Cached datasets, downloaded networks
  
* ``PY3PLEX_CACHE_DIR`` — Cache directory for computed results
  
  * Default: ``~/.py3plex/cache``
  * Used for: Embedding caches, computation results

**Performance Tuning:**

* ``PY3PLEX_NUM_WORKERS`` — Number of parallel workers for algorithms
  
  * Default: ``os.cpu_count()``
  * Used by: Node2Vec, community detection, some centrality computations

* ``PY3PLEX_MEMORY_LIMIT`` — Memory limit for large-scale operations (in GB)
  
  * Default: System memory / 2
  * Used by: Tensor operations, large network processing

**Setting environment variables:**

.. code-block:: bash

    # Linux/macOS
    export PY3PLEX_DATA_DIR="/path/to/data"
    export PY3PLEX_NUM_WORKERS=8
    
    # Or in Python
    import os
    os.environ['PY3PLEX_DATA_DIR'] = '/path/to/data'

**Debugging and Development:**

* ``PY3PLEX_DEBUG`` — Enable debug mode (verbose output)
  
  * Values: ``0`` (off), ``1`` (on)
  * Default: ``0``

* ``PY3PLEX_PROFILE`` — Enable profiling for performance analysis
  
  * Values: ``0`` (off), ``1`` (on)
  * Default: ``0``

Input Formats
-------------

Supported file formats:

* ``multiedgelist`` — Multilayer edge list format
* ``edgelist`` — Standard edge list
* ``json`` — JSON network format
* ``graphml`` — GraphML format
* ``parquet`` — Apache Parquet (high performance)

See :doc:`../how-to/load_and_build_networks` for format details.

Output Formats
--------------

Networks can be exported to:

* Pickle (Python serialization)
* JSON
* CSV/TSV
* GraphML
* Parquet

See :doc:`../how-to/export_serialize` for export details.

Algorithm Configuration
-----------------------

Many algorithms accept configuration parameters:

Community Detection
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.algorithms.community_detection import multilayer_louvain
    
    communities = multilayer_louvain(
        network,
        resolution=1.0,  # Resolution parameter
        omega=0.5        # Inter-layer coupling
    )

Node2Vec
~~~~~~~~

.. code-block:: python

    from py3plex.wrappers import train_node2vec
    
    embeddings = train_node2vec(
        network,
        dimensions=128,      # Embedding size
        walk_length=80,      # Walk length
        num_walks=10,        # Walks per node
        p=1.0,              # Return parameter
        q=1.0,              # In-out parameter
        workers=4           # Parallel workers
    )

Dynamics
~~~~~~~~

.. code-block:: python

    from py3plex.dynamics import SIRDynamics
    
    sir = SIRDynamics(
        network,
        beta=0.3,           # Infection rate
        gamma=0.1,          # Recovery rate
        initial_infected=5  # Initial infected count
    )

See :doc:`algorithm_reference` for complete parameter documentation.

Visualization Configuration
---------------------------

Customize visualization:

.. code-block:: python

    network.visualize_network(
        output_file='network.png',
        layout_algorithm='force_directed',
        node_size=50,
        edge_width=2,
        dpi=300,
        show=False
    )

See :doc:`../how-to/visualize_networks` for visualization options.

Logging Configuration
---------------------

py3plex uses Python's standard ``logging`` module. Configure logging for debugging and monitoring:

**Basic Logging Setup:**

.. code-block:: python

    import logging
    
    # Set log level
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Now py3plex operations will log to console
    from py3plex.core import multinet
    network = multinet.multi_layer_network()
    # ... logs will appear

**Log Levels:**

* ``DEBUG`` — Detailed information, typically of interest only when diagnosing problems
* ``INFO`` — Confirmation that things are working as expected (default)
* ``WARNING`` — An indication that something unexpected happened
* ``ERROR`` — A more serious problem, the software has not been able to perform some function
* ``CRITICAL`` — A serious error, the program may be unable to continue running

**Log to File:**

.. code-block:: python

    import logging
    
    # Configure file handler
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('py3plex.log'),
            logging.StreamHandler()  # Also log to console
        ]
    )

**Log File Location:**

By default, logs are written to:

* Console (stdout) when using ``StreamHandler``
* Custom file when using ``FileHandler``
* Environment variable ``PY3PLEX_LOG_FILE`` can override default location

**Component-Specific Logging:**

.. code-block:: python

    import logging
    
    # Enable debug logging only for specific components
    logging.getLogger('py3plex.algorithms').setLevel(logging.DEBUG)
    logging.getLogger('py3plex.dsl').setLevel(logging.INFO)
    logging.getLogger('py3plex.dynamics').setLevel(logging.WARNING)

**Custom Logging Handlers:**

For advanced use cases (e.g., sending logs to external systems):

.. code-block:: python

    import logging
    from logging.handlers import RotatingFileHandler
    
    # Rotating file handler (10MB max, keep 5 backups)
    handler = RotatingFileHandler(
        'py3plex.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # Add to py3plex logger
    logger = logging.getLogger('py3plex')
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

Performance Tuning
------------------

See :doc:`../project/benchmarking` for performance optimization strategies.

Next Steps
----------

* **Load networks:** :doc:`../how-to/load_and_build_networks`
* **Export networks:** :doc:`../how-to/export_serialize`
* **Algorithm reference:** :doc:`algorithm_reference`
