CSV Data Loading Examples
==========================

This guide provides practical examples for loading multilayer network data from CSV files, 
which is one of the most common formats for network data.

.. contents:: Table of Contents
   :local:
   :depth: 2

Standard CSV Schema
-------------------

Multilayer Edge List Format
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The most common format for multilayer networks is a CSV with these columns:

**Required columns:** ``source``, ``target``, ``layer``  
**Optional columns:** ``weight`` (defaults to 1.0)

**Example CSV file** (save as ``network.csv``):

.. code-block:: text

    source,target,layer,weight
    A,B,collaboration,1.0
    A,C,dependency,0.8
    B,C,collaboration,1.0
    A,B,dependency,0.5
    C,D,collaboration,0.9

Loading Multilayer CSV
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    
    # Create network object
    network = multinet.multi_layer_network()
    
    # Load from CSV
    network.load_network(
        "network.csv",
        input_type="multiedgelist",
        directed=False
    )
    
    # Display basic statistics
    network.basic_stats()

**Expected Output:**

.. code-block:: text

    Number of nodes: 4
    Number of edges: 5
    Number of unique nodes (as node-layer tuples): 7
    Number of unique node IDs (across all layers): 4
    Nodes per layer:
      Layer 'collaboration': 4 nodes
      Layer 'dependency': 3 nodes

Simple Edge List Format
~~~~~~~~~~~~~~~~~~~~~~~~

For single-layer networks, use a simpler format:

**Required columns:** ``source``, ``target``  
**Optional columns:** ``weight`` (defaults to 1.0)

**Example CSV file** (save as ``simple_network.csv``):

.. code-block:: text

    source,target,weight
    A,B,1.0
    B,C,0.8
    C,D,1.5
    D,A,0.9

Loading Simple CSV
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    
    network = multinet.multi_layer_network()
    
    # Load simple edge list
    network.load_network(
        "simple_network.csv",
        input_type="edgelist",
        directed=False
    )
    
    network.basic_stats()

Creating CSV from Pandas DataFrame
-----------------------------------

Building Network from Existing Data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have data in a Pandas DataFrame, convert it to CSV format:

.. code-block:: python

    import pandas as pd
    from py3plex.core import multinet
    
    # Create sample data
    data = {
        'source': ['Alice', 'Alice', 'Bob', 'Bob', 'Charlie'],
        'target': ['Bob', 'Charlie', 'Charlie', 'David', 'David'],
        'layer': ['friendship', 'work', 'friendship', 'work', 'friendship'],
        'weight': [1.0, 0.8, 1.0, 0.6, 0.9]
    }
    df = pd.DataFrame(data)
    
    # Save to CSV
    df.to_csv('social_network.csv', index=False)
    
    # Load into py3plex
    network = multinet.multi_layer_network()
    network.load_network('social_network.csv', input_type="multiedgelist")
    
    print(f"Loaded {network.core_network.number_of_nodes()} nodes")
    print(f"Loaded {network.core_network.number_of_edges()} edges")

Alternative Formats
-------------------

Space-Delimited Multiedgelist
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Py3plex also supports space-delimited files (no header):

**Format:** ``source layer1 target layer2 [weight]``

**Example file** (save as ``network.txt``):

.. code-block:: text

    A layer1 B layer1 1.0
    B layer1 C layer1 1.0
    A layer2 B layer2 0.8
    B layer2 D layer2 0.6

.. code-block:: python

    # Load space-delimited format
    network = multinet.multi_layer_network()
    network.load_network(
        "network.txt",
        input_type="multiedgelist",
        directed=False
    )

Common Issues and Solutions
----------------------------

Issue: "Layer name missing" error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** CSV is missing the 'layer' column

**Solution 1:** Add layer column to CSV

.. code-block:: python

    import pandas as pd
    
    # Read CSV without layer
    df = pd.read_csv('network.csv')
    
    # Add default layer
    df['layer'] = 'layer1'
    
    # Save updated CSV
    df.to_csv('network_with_layer.csv', index=False)

**Solution 2:** Use 'edgelist' format for single-layer networks

.. code-block:: python

    # If your data has only source/target columns
    network.load_network(
        "network.csv",
        input_type="edgelist",  # Use edgelist instead of multiedgelist
        directed=False
    )

Issue: "Could not load network" error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** CSV format doesn't match expected schema

**Solution:** Verify CSV structure

.. code-block:: python

    import pandas as pd
    
    # Check CSV columns
    df = pd.read_csv('network.csv')
    print("Columns:", df.columns.tolist())
    print("\nFirst few rows:")
    print(df.head())
    
    # Verify required columns exist
    required = ['source', 'target', 'layer']
    missing = [col for col in required if col not in df.columns]
    
    if missing:
        print(f"\nMissing columns: {missing}")
    else:
        print("\n✓ All required columns present")

Issue: Encoding errors with special characters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:** CSV contains non-ASCII characters (é, ñ, 中文, etc.)

**Solution:** Specify encoding when creating CSV

.. code-block:: python

    import pandas as pd
    
    # Save with UTF-8 encoding
    df.to_csv('network.csv', index=False, encoding='utf-8')
    
    # If loading fails, try reading with explicit encoding
    df = pd.read_csv('network.csv', encoding='utf-8')

Complete Example Workflow
--------------------------

End-to-End Pipeline: CSV → Analysis → Visualization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import pandas as pd
    from py3plex.core import multinet
    from py3plex.visualization.multilayer import draw_multilayer_default
    from py3plex.algorithms.community_detection import community_louvain
    import matplotlib.pyplot as plt
    
    # Step 1: Create sample CSV data
    data = {
        'source': ['A', 'A', 'B', 'B', 'C', 'C', 'D'],
        'target': ['B', 'C', 'C', 'D', 'D', 'E', 'E'],
        'layer': ['social', 'work', 'social', 'work', 'social', 'work', 'social'],
        'weight': [1.0, 0.8, 1.0, 0.7, 0.9, 0.6, 0.8]
    }
    df = pd.DataFrame(data)
    df.to_csv('example_network.csv', index=False)
    
    # Step 2: Load network
    network = multinet.multi_layer_network()
    network.load_network('example_network.csv', input_type="multiedgelist")
    
    # Step 3: Basic analysis
    print("=== Network Statistics ===")
    network.basic_stats()
    
    # Step 4: Community detection
    communities = community_louvain.best_partition(network.core_network)
    print(f"\nDetected {len(set(communities.values()))} communities")
    
    # Step 5: Centrality analysis
    from py3plex.algorithms.statistics import basic_statistics
    hubs = basic_statistics.identify_n_hubs(network.core_network, top_n=3)
    print("\nTop 3 hub nodes:")
    for node, degree in hubs.items():
        print(f"  {node}: degree {degree}")
    
    # Step 6: Visualization
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    draw_multilayer_default(
        network.get_layers(),
        display=False,
        axis=ax,
        labels=True,
        background_shape="circle"
    )
    plt.title("Multilayer Network from CSV")
    plt.savefig('network_visualization.png', dpi=300, bbox_inches='tight')
    print("\n✓ Visualization saved to network_visualization.png")
    
    # Step 7: Export to NetworkX for further analysis
    nx_graph = network.to_nx_network()
    print(f"\n✓ Exported to NetworkX: {nx_graph.number_of_nodes()} nodes, "
          f"{nx_graph.number_of_edges()} edges")

**Expected Output:**

.. code-block:: text

    === Network Statistics ===
    Number of nodes: 5
    Number of edges: 7
    Number of unique nodes (as node-layer tuples): 9
    Number of unique node IDs (across all layers): 5
    Nodes per layer:
      Layer 'social': 5 nodes
      Layer 'work': 5 nodes
    
    Detected 2 communities
    
    Top 3 hub nodes:
      ('C', 'social'): degree 3
      ('D', 'social'): degree 3
      ('B', 'social'): degree 2
    
    ✓ Visualization saved to network_visualization.png
    ✓ Exported to NetworkX: 9 nodes, 7 edges

Validation Before Loading
--------------------------

Pre-validate CSV Format
~~~~~~~~~~~~~~~~~~~~~~~

Use the validation module to check CSV format before loading:

.. code-block:: python

    from py3plex.validation import validate_network_data, ParsingError
    
    try:
        # Validate before loading
        validate_network_data('network.csv', 'multiedgelist')
        print("✓ Validation passed")
        
        # Safe to load
        network = multinet.multi_layer_network()
        network.load_network('network.csv', input_type='multiedgelist')
        
    except ParsingError as e:
        print(f"✗ Validation failed:\n{e}")
        # Fix CSV and try again

This performs checks for:

- File exists and is readable
- Required columns are present
- CSV format is valid
- Data types are appropriate

Tips and Best Practices
------------------------

1. **Always use column names** in CSV (first row should be header)
2. **Use UTF-8 encoding** for files with special characters
3. **Validate data** before loading large networks
4. **Use meaningful layer names** (e.g., 'friendship', 'work' instead of 'layer1', 'layer2')
5. **Normalize weights** if needed (e.g., scale to [0, 1] range)
6. **Handle missing values** appropriately:

.. code-block:: python

    import pandas as pd
    
    # Load CSV and handle missing values
    df = pd.read_csv('network.csv')
    
    # Fill missing weights with default
    df['weight'] = df['weight'].fillna(1.0)
    
    # Remove rows with missing source/target
    df = df.dropna(subset=['source', 'target', 'layer'])
    
    # Save cleaned data
    df.to_csv('network_cleaned.csv', index=False)

Next Steps
----------

After loading CSV data:

* :doc:`../quickstart` - Learn basic operations
* :doc:`../basic_usage_analysis` - Perform network analysis
* :doc:`../visualization_guide` - Create publication-quality visualizations
* :doc:`./community_detection` - Detect communities and clusters

For more examples, see the `examples/ directory <https://github.com/SkBlaz/py3plex/tree/main/examples>`_ 
in the GitHub repository.
