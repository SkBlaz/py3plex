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

Execution Model
---------------

Workflows follow a fixed lifecycle:

* Validate the configuration structure (required fields, supported types)
* Load or generate all datasets
* Execute operations in the order listed (each references a dataset by name)
* Collect results in memory; optionally write them under ``output.directory``

Results in memory are keyed as ``<dataset>_<operation>_<index>`` to avoid collisions across repeated operations.

Configuration Format
--------------------

A workflow file always follows the same shape (YAML or JSON):

* ``name`` (required): Workflow identifier. Used in logs and output filenames.
* ``description`` (optional): Free-text summary of the workflow intent.
* ``datasets`` (required): List of inputs to load or generate. Each entry must have a unique ``name`` so operations can reference it.
* ``operations`` (required): Ordered list of steps. Each step has a ``type``, a ``dataset`` to operate on, and optional ``parameters``.
* ``output`` (optional): Where to store results. If omitted, results stay in memory only.

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

Each dataset entry requires a ``name`` and a ``type``. Supported ``type`` values:

* ``file`` — load an existing network file (``path`` is required)
* ``generate`` — create a synthetic network (``generator`` is required)

Names must be unique because operations reference datasets by ``dataset``. Paths are resolved relative to the current working directory when you run the workflow, not the config file location.

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

The loader preserves the directed/undirected flag stored in the file when available. Multiedgelist input is treated as undirected by default.

Generating Networks
^^^^^^^^^^^^^^^^^^^

Generate synthetic networks with the built-in ``random`` generator:

.. code-block:: yaml

   datasets:
     - name: "random_network"
       type: "generate"
       generator: "random"   # Currently supported generator
       parameters:
         nodes: 50         # Number of nodes (default: 10)
         layers: 2         # Number of layers (default: 2)
         probability: 0.15 # Edge probability (default: 0.1)
         seed: 42          # Random seed (optional; keeps runs reproducible)

Nodes are named ``node0`` ... ``nodeN`` per layer; layers are named ``layer1``, ``layer2``, etc.

Available Operations
--------------------

All operations share the same basic shape and are validated against the allowed ``type`` values:

.. code-block:: yaml

   - type: "<operation_name>"
     dataset: "<dataset_name>"
     parameters: { ... }

Statistics
^^^^^^^^^^

Compute network statistics:

.. code-block:: yaml

     - type: "stats"
       dataset: "my_network"
       parameters: {}

Computes:

* Node and edge counts
* Layer densities (one density per layer if layers can be inferred from node tuples)

Result keys: ``nodes``, ``edges``, and optional ``layer_densities`` (one entry per detected layer).

Community Detection
^^^^^^^^^^^^^^^^^^^

Detect communities (Louvain):

.. code-block:: yaml

   - type: "community"
     dataset: "my_network"
     parameters:
       algorithm: "louvain"  # Community detection algorithm

Supported algorithms:

* ``louvain`` - Louvain method for community detection

Directed graphs are converted to undirected for community detection to match the algorithm's assumptions. Results include ``algorithm``, ``num_communities``, and a ``communities`` mapping from stringified node IDs to integer community labels.

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

Directed graphs are converted to undirected before computing measures. Results include ``measure`` and a ``centrality`` dictionary keyed by node (as strings).

Visualization
^^^^^^^^^^^^^

Visualize networks and save a static image:

.. code-block:: yaml

   - type: "visualize"
     dataset: "my_network"
     parameters:
       output: "network.png"  # Output file (default: network.png)
       layout: "spring"       # Layout algorithm (default: spring)

Supported layouts:

* ``spring`` - Force-directed spring layout
* ``circular`` - Circular layout

Visualization always writes an image file (default ``network.png``) and returns the output path; node labels are omitted for readability on large graphs.

Aggregation
^^^^^^^^^^^

Aggregate multilayer networks:

.. code-block:: yaml

   - type: "aggregate"
     dataset: "my_network"
     parameters:
       method: "sum"  # Aggregation method (default: sum)

Supported methods:

* ``sum`` - Sum edge weights
* ``mean`` - Average edge weights
* ``max`` - Maximum edge weight
* ``min`` - Minimum edge weight

Aggregation returns an in-memory aggregated network object in the workflow results. To persist it, follow with a ``convert`` step.

Conversion
^^^^^^^^^^

Convert network formats:

.. code-block:: yaml

   - type: "convert"
     dataset: "my_network"
     parameters:
       output: "network.json"  # Output file

Supported outputs:

* ``.graphml`` - Full graph structure (preferred)
* ``.json`` - Node/edge lists without extra attributes

Unsupported extensions raise an error. GraphML preserves attributes and edge multiplicity; the JSON output is a minimal node/edge list.

Output Section
--------------

The ``output`` block controls where results are written:

.. code-block:: yaml

   output:
     directory: "results"    # Created if missing (default: ".")
     summary: "summary.json" # File containing all operation results (default: summary.json)

If the ``output`` block is omitted, results remain in memory only. The summary file mirrors the in-memory results dictionary.

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

The runner validates required fields before execution and stops if validation fails. Validation checks dataset names/types, required parameters for each type, and whether operations reference known datasets.

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

Results are kept in memory during the run and optionally written to disk based on the ``output`` section. If ``output`` is omitted, no files are written. The Python API raises ``ValueError`` on validation failure.

Examples
--------

See the ``examples/workflows/`` directory for complete examples:

* ``example_config.yaml`` - Basic workflow with generated network
* ``comparison_config.json`` - Multi-dataset comparison
* ``example_config_workflow.py`` - Python example script

To run the examples:

.. code-block:: bash

   cd examples/workflows
   python example_config_workflow.py

   # Or using CLI
   py3plex run-config example_config.yaml
   py3plex run-config comparison_config.json

Best Practices
--------------

Version Control
^^^^^^^^^^^^^^^

* Store config files in version control alongside your code.
* Use descriptive names for workflows and datasets to make logs readable.
* Document non-obvious parameters in comments next to the field.

Reproducibility
^^^^^^^^^^^^^^^

* Set ``seed`` when generating networks to reproduce results.
* Document dataset sources and versions in ``description`` or comments.
* Keep configs and the exact py3plex version together in your repo or summary output.

Organization
^^^^^^^^^^^^

* Use separate configs for distinct experiments rather than overloading a single file.
* Group related operations together so results are easy to trace.
* Start from a template (YAML/JSON) and adjust parameters instead of editing from scratch.

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

* :doc:`CLI Guide <getting_started/tutorial_10min>` - Command-line interface
* :doc:`API Documentation <apidocs>` - Python API reference
* :doc:`Examples <examples_reference>` - More examples
