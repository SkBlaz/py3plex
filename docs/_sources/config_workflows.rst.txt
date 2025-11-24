Config-Driven Workflows
========================

.. contents:: Table of Contents
   :depth: 2
   :local:

Overview
--------

Config-driven workflows in py3plex allow you to define and execute complex network analysis pipelines using YAML or JSON configuration files. This approach is ideal for:

* **Reproducible research** - Share exact experiment configurations
* **Pipeline automation** - Integrate with CI/CD systems
* **Batch processing** - Run multiple experiments with different parameters
* **Version control** - Track experimental setups alongside code

Configuration Format
--------------------

A workflow configuration file consists of three main sections:

1. **Metadata**: Workflow name and description
2. **Datasets**: Networks to load or generate
3. **Operations**: Analysis steps to perform
4. **Output**: Where to save results

YAML Example
^^^^^^^^^^^^

.. code-block:: yaml

   name: "Basic Network Analysis"
   description: "Analyze a multilayer network"

   datasets:
     - name: "my_network"
       type: "generate"
       generator: "random"
       parameters:
         nodes: 100
         layers: 3
         probability: 0.1
         seed: 42

   operations:
     - type: "stats"
       dataset: "my_network"
       parameters: {}

     - type: "community"
       dataset: "my_network"
       parameters:
         algorithm: "louvain"

     - type: "visualize"
       dataset: "my_network"
       parameters:
         output: "network.png"
         layout: "spring"

   output:
     directory: "results"
     summary: "summary.json"

JSON Example
^^^^^^^^^^^^

.. code-block:: json

   {
     "name": "Network Comparison",
     "description": "Compare two networks",
     "datasets": [
       {
         "name": "network1",
         "type": "file",
         "path": "network1.graphml"
       },
       {
         "name": "network2",
         "type": "file",
         "path": "network2.graphml"
       }
     ],
     "operations": [
       {
         "type": "stats",
         "dataset": "network1",
         "parameters": {}
       },
       {
         "type": "stats",
         "dataset": "network2",
         "parameters": {}
       }
     ],
     "output": {
       "directory": "comparison",
       "summary": "results.json"
     }
   }

Dataset Specification
---------------------

Loading from File
^^^^^^^^^^^^^^^^^

Load existing network files:

.. code-block:: yaml

   datasets:
     - name: "my_network"
       type: "file"
       path: "path/to/network.graphml"

Supported file formats:

* GraphML (``.graphml``)
* GPickle (``.gpickle``)
* Multiedgelist (``.edgelist``, ``.txt``)

Generating Networks
^^^^^^^^^^^^^^^^^^^

Generate synthetic networks:

.. code-block:: yaml

   datasets:
     - name: "random_network"
       type: "generate"
       generator: "random"
       parameters:
         nodes: 50        # Number of nodes
         layers: 2        # Number of layers
         probability: 0.15 # Edge probability
         seed: 42         # Random seed (optional)

Available Operations
--------------------

Statistics
^^^^^^^^^^

Compute network statistics:

.. code-block:: yaml

   - type: "stats"
     dataset: "my_network"
     parameters: {}

Computes:

* Node and edge counts
* Layer densities
* Clustering coefficients

Community Detection
^^^^^^^^^^^^^^^^^^^

Detect communities:

.. code-block:: yaml

   - type: "community"
     dataset: "my_network"
     parameters:
       algorithm: "louvain"  # Community detection algorithm

Supported algorithms:

* ``louvain`` - Louvain method

Centrality
^^^^^^^^^^

Compute node centrality:

.. code-block:: yaml

   - type: "centrality"
     dataset: "my_network"
     parameters:
       measure: "degree"  # Centrality measure

Supported measures:

* ``degree`` - Degree centrality
* ``betweenness`` - Betweenness centrality
* ``closeness`` - Closeness centrality

Visualization
^^^^^^^^^^^^^

Visualize networks:

.. code-block:: yaml

   - type: "visualize"
     dataset: "my_network"
     parameters:
       output: "network.png"  # Output file
       layout: "spring"       # Layout algorithm

Supported layouts:

* ``spring`` - Force-directed spring layout
* ``circular`` - Circular layout

Aggregation
^^^^^^^^^^^

Aggregate multilayer networks:

.. code-block:: yaml

   - type: "aggregate"
     dataset: "my_network"
     parameters:
       method: "sum"  # Aggregation method

Supported methods:

* ``sum`` - Sum edge weights
* ``mean`` - Average edge weights
* ``max`` - Maximum edge weight
* ``min`` - Minimum edge weight

Conversion
^^^^^^^^^^

Convert network formats:

.. code-block:: yaml

   - type: "convert"
     dataset: "my_network"
     parameters:
       output: "network.json"  # Output file

Running Workflows
-----------------

Command Line
^^^^^^^^^^^^

Run a workflow from the command line:

.. code-block:: bash

   # Run workflow
   py3plex run-config my_workflow.yaml

   # Validate configuration without running
   py3plex run-config my_workflow.yaml --validate-only

Python API
^^^^^^^^^^

Run workflows programmatically:

.. code-block:: python

   from py3plex.workflows import run_workflow

   # Run workflow from config file
   run_workflow("my_workflow.yaml")

   # Or use the full API
   from py3plex.workflows import WorkflowConfig, WorkflowRunner

   config = WorkflowConfig.from_file("my_workflow.yaml")
   
   # Validate
   errors = config.validate()
   if errors:
       print("Validation errors:", errors)
   else:
       # Execute
       runner = WorkflowRunner(config)
       runner.run()

Examples
--------

See the ``examples/config_driven/`` directory for complete examples:

* ``example_config.yaml`` - Basic workflow with generated network
* ``comparison_config.json`` - Multi-dataset comparison
* ``example_config_workflow.py`` - Python example script

To run the examples:

.. code-block:: bash

   cd examples/config_driven
   python example_config_workflow.py

   # Or using CLI
   py3plex run-config example_config.yaml
   py3plex run-config comparison_config.json

Best Practices
--------------

Version Control
^^^^^^^^^^^^^^^

* Store config files in version control alongside your code
* Use descriptive names for workflows
* Document parameters in comments

Reproducibility
^^^^^^^^^^^^^^^

* Always set random seeds for generated networks
* Document dataset sources and versions
* Include workflow descriptions

Organization
^^^^^^^^^^^^

* Use separate configs for different experiments
* Group related operations together
* Create reusable config templates

Troubleshooting
---------------

YAML Not Available
^^^^^^^^^^^^^^^^^^

If you get an error about YAML support:

.. code-block:: bash

   pip install pyyaml

Then use YAML config files. JSON is always supported without extra dependencies.

Validation Errors
^^^^^^^^^^^^^^^^^

Use ``--validate-only`` to check configuration:

.. code-block:: bash

   py3plex run-config my_workflow.yaml --validate-only

Common issues:

* Missing required fields (``name``, ``type``, etc.)
* Invalid operation types
* Referenced datasets that don't exist
* Invalid file paths

Further Reading
---------------

* :doc:`CLI Guide <getting_started/quickstart_5min>` - Command-line interface
* :doc:`API Documentation <apidocs>` - Python API reference
* :doc:`Examples <example>` - More examples
