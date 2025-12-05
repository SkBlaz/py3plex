Command-Line Interface (CLI) Tutorial
======================================

Py3plex includes a comprehensive command-line interface that provides access to all main algorithms and functionality directly from the terminal. This is useful for quick analysis, scripting, and automation workflows.

Installation
------------

The CLI tool is automatically available after installing py3plex:

.. code-block:: bash

    pip install py3plex

After installation, verify the CLI is available:

.. code-block:: bash

    py3plex --help

**Alternative: Using Docker**

If you prefer Docker, the CLI is also available via the Docker container:

.. code-block:: bash

    # Build the Docker image
    docker build -t py3plex:latest .
    
    # Run CLI commands
    docker run --rm py3plex:latest --help
    docker run --rm -v $(pwd)/data:/data py3plex:latest create --nodes 100 --output /data/network.edgelist

See :doc:`cli_and_docker` for complete Docker documentation.

Quick Start
-----------

**New to py3plex?** Start with these essential commands:

.. code-block:: bash

    # Run an interactive demo with example graph
    py3plex quickstart

    # Verify installation
    py3plex selftest

    # Check version
    py3plex --version

    # Get help
    py3plex --help

The ``quickstart`` command creates a small demo multilayer network, computes statistics, generates a visualization, and shows you next steps. It's the fastest way to see py3plex in action!

Getting Help
------------

The CLI includes built-in documentation for all commands:

.. code-block:: bash

    # Main help with all commands
    py3plex --help
    
    # Help for specific command
    py3plex create --help
    py3plex community --help
    py3plex centrality --help

Available Commands
------------------

The py3plex CLI provides these main commands:

* ``quickstart`` - Interactive demo with example graph (recommended for new users)
* ``selftest`` - Verify installation and core functionality
* ``check`` - Lint and validate graph data files
* ``create`` - Create new multilayer networks
* ``load`` - Load and inspect networks
* ``community`` - Detect communities
* ``centrality`` - Compute centrality measures
* ``stats`` - Compute multilayer network statistics
* ``visualize`` - Create network visualizations
* ``aggregate`` - Aggregate multilayer networks into single layer
* ``convert`` - Convert between network formats
* ``help`` - Show detailed help information

Quick Reference
~~~~~~~~~~~~~~~

**Essential flags:**

* ``--version`` - Display py3plex version
* ``--help`` - Display help for any command

**Common workflows:**

.. code-block:: bash

    # Quick demo
    py3plex quickstart

    # Validate → Load → Analyze
    py3plex check data.csv
    py3plex load data.csv --stats
    
    # Create → Analyze → Visualize
    py3plex create --nodes 50 --layers 2 --output net.graphml
    py3plex load net.graphml --stats
    py3plex visualize net.graphml --output viz.png

    # Community detection workflow
    py3plex community net.graphml --algorithm louvain --output communities.json

Unix Piping and Stdin Support
-----------------------------

Py3plex CLI supports Unix-style piping workflows, allowing you to chain commands together and integrate with other Unix tools. This is especially powerful for automation and scripting.

Stdin Input with ``-``
~~~~~~~~~~~~~~~~~~~~~~

Use ``-`` as the input file argument to read network data from stdin:

.. code-block:: bash

    # Pipe network data to load command
    cat network.edgelist | py3plex load - --info

    # Pipe to query command
    cat network.edgelist | py3plex query - "SELECT nodes COMPUTE degree"

Piping Between Commands
~~~~~~~~~~~~~~~~~~~~~~~

Chain py3plex commands together without intermediate files:

.. code-block:: bash

    # Create a network and immediately query it
    py3plex create --nodes 50 --layers 3 -o /dev/stdout 2>/dev/null | \
        py3plex query - "SELECT nodes COMPUTE degree" --format table

    # Create and compute statistics in one pipeline
    py3plex create --nodes 100 --layers 2 --seed 42 -o /dev/stdout 2>/dev/null | \
        py3plex load - --info

The Query Command
~~~~~~~~~~~~~~~~~

The ``query`` command executes DSL queries on networks and outputs results in multiple formats. This is particularly useful for piping workflows.

**String DSL Syntax:**

.. code-block:: bash

    # Get all nodes
    py3plex query network.edgelist "SELECT nodes"

    # Filter by layer
    py3plex query network.edgelist "SELECT nodes WHERE layer='social'"

    # Compute metrics
    py3plex query network.edgelist "SELECT nodes COMPUTE degree"

    # Multiple computations
    py3plex query network.edgelist "SELECT nodes COMPUTE degree, betweenness_centrality"

**Python DSL Builder Syntax (use ``--dsl`` flag):**

.. code-block:: bash

    # Basic query with DSL builder
    py3plex query network.edgelist 'Q.nodes().compute("degree")' --dsl

    # With filtering, ordering, and limiting
    py3plex query network.edgelist \
        'Q.nodes().where(layer="social").compute("degree").order_by("-degree").limit(10)' --dsl

    # Layer algebra (union of layers)
    py3plex query network.edgelist \
        'Q.nodes().from_layers(L["social"] + L["work"]).compute("degree")' --dsl

Output Formats
~~~~~~~~~~~~~~

Control the output format for different use cases:

.. code-block:: bash

    # JSON output (default) - good for further processing
    py3plex query network.edgelist "SELECT nodes COMPUTE degree" --format json

    # CSV output - good for spreadsheets and data analysis
    py3plex query network.edgelist "SELECT nodes COMPUTE degree" --format csv > results.csv

    # Table output - good for human reading in terminal
    py3plex query network.edgelist "SELECT nodes COMPUTE degree" --format table

Combining with Unix Tools
~~~~~~~~~~~~~~~~~~~~~~~~~

Combine py3plex output with standard Unix tools for powerful data processing:

**With jq (JSON processing):**

.. code-block:: bash

    # Get top 5 nodes by degree
    py3plex query network.edgelist "SELECT nodes COMPUTE degree" 2>/dev/null | \
        jq '.nodes[:5]'

    # Extract just the computed values
    py3plex query network.edgelist "SELECT nodes COMPUTE degree" 2>/dev/null | \
        jq '.computed.degree'

    # Count nodes
    py3plex query network.edgelist "SELECT nodes" 2>/dev/null | \
        jq '.count'

**With grep and other tools:**

.. code-block:: bash

    # Filter JSON output
    py3plex query network.edgelist "SELECT nodes COMPUTE degree" --format json 2>/dev/null | \
        grep -o '"count": [0-9]*'

    # Count rows in CSV output
    py3plex query network.edgelist "SELECT nodes COMPUTE degree" --format csv 2>/dev/null | \
        wc -l

Complete Piping Workflow Examples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Example 1: End-to-end analysis pipeline**

.. code-block:: bash

    #!/bin/bash
    # Generate network, analyze, and save results

    # Create network
    py3plex create --nodes 100 --layers 3 --probability 0.1 -o network.edgelist --seed 42

    # Compute centrality and save top nodes using DSL
    py3plex query network.edgelist \
        'Q.nodes().compute("degree", "betweenness_centrality").order_by("-degree").limit(20)' \
        --dsl -o top_nodes.json

    # Detect communities
    py3plex community network.edgelist --algorithm louvain -o communities.json

**Example 2: Batch processing multiple files**

.. code-block:: bash

    #!/bin/bash
    # Process multiple network files

    for file in networks/*.edgelist; do
        echo "Processing $file..."
        py3plex query "$file" "SELECT nodes COMPUTE degree" \
            --format csv > "${file%.edgelist}_degrees.csv"
    done

**Example 3: Create and analyze without intermediate files**

.. code-block:: bash

    # Create and immediately analyze - no file needed
    py3plex create --nodes 50 --layers 2 -o /dev/stdout 2>/dev/null | \
        py3plex query - 'Q.nodes().compute("degree").order_by("-degree").limit(5)' --dsl

Tips for Piping Workflows
~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Suppress logging**: Redirect stderr with ``2>/dev/null`` when piping to avoid log messages in output
2. **Use appropriate formats**: Use ``--format json`` for programmatic processing, ``--format csv`` for large datasets
3. **Reproducibility**: Always use ``--seed`` when creating random networks
4. **Debugging**: Use ``--format table`` for quick visual inspection during development

Validating Data Files
---------------------

Before loading network data, you can validate file format and data integrity using the ``check`` command. This helps catch common issues early and provides actionable suggestions for fixing problems.

Basic Validation
~~~~~~~~~~~~~~~~

Validate a graph data file (auto-detects format):

.. code-block:: bash

    py3plex check network.csv

**Output for valid file:**

.. code-block:: text

    Checking file: network.csv
    ✓ No issues found!

**Output for file with issues:**

.. code-block:: text

    Checking file: network.csv
    
    Found 5 issue(s):
    
    [INFO] No layer columns found - this appears to be a single-layer network
    [ERROR] Line 3: Empty destination node
      → Suggestion: Provide a valid destination node ID
    [WARNING] Line 4: Negative weight: -1.5
      → Suggestion: Negative weights may not be supported by all algorithms
    [WARNING] Line 5: Self-loop detected: Dave -> Dave
      → Suggestion: Self-loops may not be supported by all algorithms
    [WARNING] Line 6: Duplicate edge: Alice -> Bob
      → Suggestion: Remove duplicate edges or consolidate with edge weights
    
    Linting results:
      Errors: 1
      Warnings: 3
      Info: 1
    
    ✗ Validation failed with errors

Supported File Formats
~~~~~~~~~~~~~~~~~~~~~~

The ``check`` command automatically detects and validates these formats:

* **CSV** - Comma-separated values with headers (e.g., ``network.csv``)
* **Edgelist** - Space-separated node pairs (e.g., ``network.edgelist``)
* **Multiedgelist** - Space-separated with layer information (e.g., ``network.txt``)

Strict Mode
~~~~~~~~~~~

Use ``--strict`` to treat warnings as errors (useful for CI/CD pipelines):

.. code-block:: bash

    py3plex check network.csv --strict

With strict mode enabled, the command exits with error code 1 if any warnings are found, making it suitable for automated validation in scripts.

Validation Checks
~~~~~~~~~~~~~~~~~

The linter performs these checks:

**Errors (cause validation failure):**

* Missing or empty node IDs
* Invalid weight values (non-numeric)
* Missing required columns (for CSV files)
* Malformed file structure

**Warnings (reported but don't fail validation):**

* Negative weights
* Self-loops
* Duplicate edges

**Info (informational messages):**

* Single-layer network detected (when no layer columns found)
* Format detection results

Example Workflows
~~~~~~~~~~~~~~~~~

**Validate before loading:**

.. code-block:: bash

    # Step 1: Validate the file
    py3plex check my_network.csv
    
    # Step 2: If valid, load and analyze
    py3plex load my_network.csv --stats

**CI/CD integration:**

.. code-block:: bash

    # In your CI script - fail if any issues found
    py3plex check network.csv --strict || exit 1
    
    # Proceed with analysis if validation passed
    py3plex load network.csv --stats

**Batch validation:**

.. code-block:: bash

    # Validate multiple files
    for file in data/*.csv; do
        echo "Checking $file..."
        py3plex check "$file"
    done

Creating Networks
-----------------

Create Random Networks
~~~~~~~~~~~~~~~~~~~~~~

Create a simple multilayer network with random edges:

.. code-block:: bash

    py3plex create --nodes 100 --layers 3 --output network.graphml --seed 42

This creates a network with 100 nodes per layer and 3 layers, saving it to ``network.graphml``.

Network Generation Models
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Erdős-Rényi Random Graphs:**

.. code-block:: bash

    py3plex create --nodes 50 --layers 2 --type er --probability 0.15 \
        --output er_network.graphml --seed 42

**Barabási-Albert Preferential Attachment:**

.. code-block:: bash

    py3plex create --nodes 100 --layers 3 --type ba --probability 0.05 \
        --output ba_network.graphml --seed 42

**Watts-Strogatz Small-World:**

.. code-block:: bash

    py3plex create --nodes 50 --layers 2 --type ws --probability 0.2 \
        --output ws_network.graphml --seed 42

Output Formats
~~~~~~~~~~~~~~

The CLI supports multiple output formats (automatically detected from file extension):

* ``.graphml`` - GraphML format (XML-based, recommended)
* ``.gexf`` - GEXF format (XML-based, for Gephi)
* ``.gpickle`` - Python pickle format (binary, fastest)

Loading and Inspecting Networks
--------------------------------

Basic Network Information
~~~~~~~~~~~~~~~~~~~~~~~~~

Display basic network statistics:

.. code-block:: bash

    py3plex load network.graphml --info

**Output:**

.. code-block:: text

    Network Information:
      Nodes: 300
      Edges: 450
      Layers: 3 (layer1, layer2, layer3)
      Directed: False

Detailed Statistics
~~~~~~~~~~~~~~~~~~~

Get comprehensive statistics including layer densities and clustering:

.. code-block:: bash

    py3plex load network.graphml --stats

**Output:**

.. code-block:: text

    Network Information:
      Nodes: 300
      Edges: 450
      Layers: 3 (layer1, layer2, layer3)
      Directed: False

    Basic Statistics:
      Layer Densities:
        layer1: 0.0303
        layer2: 0.0298
        layer3: 0.0305
      Avg Clustering: 0.0421
      Avg Degree: 3.00
      Max Degree: 12

Save to JSON
~~~~~~~~~~~~

Export network information to JSON for further processing:

.. code-block:: bash

    py3plex load network.graphml --info --output network_info.json

Community Detection
-------------------

Louvain Algorithm
~~~~~~~~~~~~~~~~~

Detect communities using the Louvain modularity optimization algorithm:

.. code-block:: bash

    py3plex community network.graphml --algorithm louvain --output communities.json

**Output:**

.. code-block:: text

    Loading network from network.graphml...
    Detecting communities using louvain...
    Found 8 communities
    Community sizes: min=15, max=52, avg=37.5
    Communities saved to communities.json

With Custom Resolution
~~~~~~~~~~~~~~~~~~~~~~

Adjust the resolution parameter to find more or fewer communities:

.. code-block:: bash

    # Higher resolution = more communities
    py3plex community network.graphml --algorithm louvain --resolution 1.5

    # Lower resolution = fewer communities
    py3plex community network.graphml --algorithm louvain --resolution 0.5

Label Propagation
~~~~~~~~~~~~~~~~~

Use label propagation for fast community detection:

.. code-block:: bash

    py3plex community network.graphml --algorithm label_prop --output communities.json

Infomap (Optional)
~~~~~~~~~~~~~~~~~~

If Infomap is installed, use it for overlapping community detection:

.. code-block:: bash

    py3plex community network.graphml --algorithm infomap --output communities.json

Centrality Measures
-------------------

Degree Centrality
~~~~~~~~~~~~~~~~~

Compute degree centrality and show top nodes:

.. code-block:: bash

    py3plex centrality network.graphml --measure degree --top 10

**Output:**

.. code-block:: text

    Loading network from network.graphml...
    Computing degree centrality...

    Top 10 nodes by degree centrality:
      node42---layer1: 12.000000
      node18---layer2: 11.000000
      node77---layer1: 10.000000
      ...

Save Results
~~~~~~~~~~~~

Export centrality scores to JSON:

.. code-block:: bash

    py3plex centrality network.graphml --measure degree --output centrality.json

All Centrality Measures
~~~~~~~~~~~~~~~~~~~~~~~~

**Betweenness Centrality:**

.. code-block:: bash

    py3plex centrality network.graphml --measure betweenness --top 10

**Closeness Centrality:**

.. code-block:: bash

    py3plex centrality network.graphml --measure closeness --top 10

**Eigenvector Centrality:**

.. code-block:: bash

    py3plex centrality network.graphml --measure eigenvector --top 10

**PageRank:**

.. code-block:: bash

    py3plex centrality network.graphml --measure pagerank --top 10

Multilayer Network Statistics
------------------------------

Comprehensive Statistics
~~~~~~~~~~~~~~~~~~~~~~~~

Compute all available multilayer statistics:

.. code-block:: bash

    py3plex stats network.graphml --measure all --output stats.json

**Output includes:**

* Layer densities for each layer
* Clustering coefficient
* Node activity samples
* Versatility centrality (top nodes)
* Edge overlap between layers

Specific Statistics
~~~~~~~~~~~~~~~~~~~

**Layer Density:**

.. code-block:: bash

    py3plex stats network.graphml --measure layer_density

**Clustering Coefficient:**

.. code-block:: bash

    py3plex stats network.graphml --measure clustering

**Node Activity:**

.. code-block:: bash

    py3plex stats network.graphml --measure node_activity

**Versatility Centrality:**

.. code-block:: bash

    py3plex stats network.graphml --measure versatility

**Edge Overlap:**

.. code-block:: bash

    py3plex stats network.graphml --measure edge_overlap

Network Visualization
---------------------

Multilayer Layout
~~~~~~~~~~~~~~~~~

Create a visualization using the specialized multilayer layout:

.. code-block:: bash

    py3plex visualize network.graphml --layout multilayer --output network.png

Standard Layouts
~~~~~~~~~~~~~~~~

Use NetworkX layouts for different visual styles:

**Spring Layout (Force-Directed):**

.. code-block:: bash

    py3plex visualize network.graphml --layout spring --output network_spring.png

**Circular Layout:**

.. code-block:: bash

    py3plex visualize network.graphml --layout circular --output network_circular.png

**Kamada-Kawai Layout:**

.. code-block:: bash

    py3plex visualize network.graphml --layout kamada_kawai --output network_kk.png

Custom Figure Size
~~~~~~~~~~~~~~~~~~

Adjust the output image dimensions:

.. code-block:: bash

    py3plex visualize network.graphml --layout spring --width 15 --height 10 \
        --output large_viz.png

Network Aggregation
-------------------

Aggregate multiple layers into a single layer using different methods:

Sum Aggregation
~~~~~~~~~~~~~~~

Sum edge weights across layers:

.. code-block:: bash

    py3plex aggregate network.graphml --method sum --output aggregated.graphml

Mean Aggregation
~~~~~~~~~~~~~~~~

Average edge weights across layers:

.. code-block:: bash

    py3plex aggregate network.graphml --method mean --output aggregated_mean.graphml

Other Aggregation Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``max`` - Take maximum edge weight across layers
* ``min`` - Take minimum edge weight across layers

Format Conversion
-----------------

Convert Between Formats
~~~~~~~~~~~~~~~~~~~~~~~~

Convert networks between different file formats:

**To GEXF (for Gephi):**

.. code-block:: bash

    py3plex convert network.graphml --output network.gexf

**To JSON:**

.. code-block:: bash

    py3plex convert network.graphml --output network.json

**To gpickle (Python binary):**

.. code-block:: bash

    py3plex convert network.graphml --output network.gpickle

Complete Workflow Examples
---------------------------

Example 1: Create, Analyze, and Visualize
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Step 1: Create a Barabási-Albert network
    py3plex create --nodes 100 --layers 3 --type ba --probability 0.05 \
        --output ba_network.graphml --seed 42
    
    # Step 2: Detect communities
    py3plex community ba_network.graphml --algorithm louvain \
        --output communities.json
    
    # Step 3: Compute centrality
    py3plex centrality ba_network.graphml --measure pagerank --top 20 \
        --output central_nodes.json
    
    # Step 4: Visualize
    py3plex visualize ba_network.graphml --layout spring --width 15 --height 10 \
        --output ba_visualization.png

Example 2: Load, Analyze Statistics, and Export
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Step 1: Load and inspect
    py3plex load existing_network.graphml --stats
    
    # Step 2: Compute comprehensive statistics
    py3plex stats existing_network.graphml --measure all --output stats.json
    
    # Step 3: Convert to GEXF for Gephi
    py3plex convert existing_network.graphml --output for_gephi.gexf

Example 3: Multiple Analysis Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Create network
    py3plex create --nodes 50 --layers 2 --type er --probability 0.15 \
        --output network.graphml --seed 42
    
    # Run all centrality measures
    py3plex centrality network.graphml --measure degree --output degree.json
    py3plex centrality network.graphml --measure betweenness --output betweenness.json
    py3plex centrality network.graphml --measure pagerank --output pagerank.json
    
    # Detect communities with different algorithms
    py3plex community network.graphml --algorithm louvain --output louvain.json
    py3plex community network.graphml --algorithm label_prop --output label_prop.json
    
    # Create multiple visualizations
    py3plex visualize network.graphml --layout multilayer --output viz_ml.png
    py3plex visualize network.graphml --layout spring --output viz_spring.png
    py3plex visualize network.graphml --layout circular --output viz_circular.png

Example 4: Validate External Data Before Analysis
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Step 1: Validate the data file
    py3plex check external_data.csv
    
    # Step 2: If validation passes, load the network
    py3plex load external_data.csv --info
    
    # Step 3: Run analysis
    py3plex stats external_data.csv --measure all --output stats.json
    
    # Step 4: Detect communities
    py3plex community external_data.csv --algorithm louvain --output communities.json
    
    # Step 5: Create visualization
    py3plex visualize external_data.csv --layout spring --output network_viz.png

Tips and Best Practices
------------------------

1. **Validate Data Files First**: Always run ``py3plex check`` on external data files before analysis to catch format issues early.

2. **Use Seeds for Reproducibility**: Always use ``--seed`` when creating networks for reproducible results.

3. **JSON Output for Scripting**: Use ``--output`` to save results as JSON for post-processing with other tools.

4. **Check Help for Each Command**: Each command has detailed help with examples:

   .. code-block:: bash

       py3plex <command> --help

4. **Format Auto-Detection**: The CLI automatically detects file formats from extensions, so use appropriate extensions (.graphml, .gexf, .json, .gpickle).

5. **Large Networks**: For large networks (>1000 nodes), prefer:
   
   * ``spring`` or ``circular`` layouts for visualization
   * ``louvain`` for community detection (faster than infomap)
   * ``degree`` centrality for quick analysis

6. **Batch Processing**: Combine CLI commands with shell scripts for batch processing multiple networks.

Common Issues and Solutions
----------------------------

**Issue: "Infomap not available"**

Solution: Infomap requires separate installation. Use ``louvain`` or ``label_prop`` instead.

**Issue: "Eigenvector centrality failed"**

Solution: Some networks don't converge for eigenvector centrality. The CLI automatically falls back to degree centrality.

**Issue: Visualization too slow**

Solution: Use simpler layouts (``circular``) or reduce figure size (``--width 8 --height 6``).

**Issue: Memory errors with large networks**

Solution: Use aggregation to reduce network size before visualization, or compute statistics without visualization.

See Also
--------

* :doc:`../getting_started/quickstart_5min` - Python API quickstart
* :doc:`../getting_started/tutorial_10min` - 10-minute Python tutorial
* :doc:`./community_detection` - Community detection algorithms in detail
* :doc:`./multilayer_centrality` - Centrality measures for multilayer networks
* :doc:`../index` - Main documentation index
