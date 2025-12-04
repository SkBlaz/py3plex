Meta Flow Report - Comprehensive Network Analysis
==================================================

The **Meta Flow Report** provides a unified interface for conducting multiple multilayer network analyses at once. Instead of running centrality measures, community detection, and statistics separately, you can now perform comprehensive analysis with a single function call.

Overview
--------

The meta flow report enables you to:

* Compute **multiple centrality measures** simultaneously (degree, eigenvector, betweenness, etc.)
* Run **multiple community detection algorithms** at once (Louvain, Leiden)
* Calculate **various network statistics** together (density, clustering, etc.)
* Generate **human-readable reports** summarizing all results
* **Export results** for further analysis

This is particularly useful for:

* **Exploratory analysis**: Get a comprehensive view of your network quickly
* **Comparative studies**: Analyze multiple networks with consistent metrics
* **Reporting**: Generate summaries for papers, presentations, or documentation
* **Teaching**: Demonstrate multiple network analysis concepts at once

Quick Start
-----------

Basic Usage
~~~~~~~~~~~

The simplest way to use the meta flow report is with the ``run_meta_analysis()`` convenience function:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.meta_flow_report import run_meta_analysis
    
    # Create or load your network
    network = multinet.multi_layer_network(directed=False)
    network.add_edges([
        ['Alice', 'facebook', 'Bob', 'facebook', 1],
        ['Bob', 'facebook', 'Carol', 'facebook', 1],
        ['Alice', 'twitter', 'Carol', 'twitter', 1],
        ['Alice', 'facebook', 'Alice', 'twitter', 1],
        ['Bob', 'facebook', 'Bob', 'twitter', 1],
        ['Carol', 'facebook', 'Carol', 'twitter', 1],
    ], input_type='list')
    
    # Run comprehensive analysis with automatic summary
    results = run_meta_analysis(network)

**Output:**

.. code-block:: text

    Computing centrality measures...
    Running community detection...
    Computing network statistics...
    
    ================================================================================
    META FLOW REPORT - Multilayer Network Analysis Summary
    ================================================================================
    
    ================================================================================
    CENTRALITY MEASURES
    ================================================================================
    
    Overlapping Degree:
      Alice                          2.000000
      Bob                            2.000000
      Carol                          2.000000
    
    [... more centrality measures ...]
    
    ================================================================================
    COMMUNITY DETECTION
    ================================================================================
    
    Louvain Communities:
      Number of communities: 2
      Community sizes: {0: 4, 1: 2}
    
    [... more results ...]

Selective Analysis
~~~~~~~~~~~~~~~~~~

You can choose which analyses to run:

.. code-block:: python

    from py3plex.algorithms.meta_flow_report import run_meta_analysis
    
    # Run only centralities and statistics (skip communities)
    results = run_meta_analysis(
        network,
        include_centralities=True,
        include_communities=False,
        include_statistics=True,
        print_summary=True
    )

Fine-Grained Control
~~~~~~~~~~~~~~~~~~~~

For more control, use the ``MetaFlowReport`` class directly:

.. code-block:: python

    from py3plex.algorithms.meta_flow_report import MetaFlowReport
    
    # Create report generator
    report = MetaFlowReport(network)
    
    # Run analyses separately
    centralities = report.compute_centralities(
        include_path_based=False,
        include_advanced=False
    )
    
    communities = report.detect_communities(
        methods=['louvain'],
        gamma=1.0,
        omega=1.0
    )
    
    statistics = report.compute_statistics(
        include_advanced=False
    )
    
    # Or run all at once with custom options
    results = report.run_all_analyses(
        include_centralities=True,
        include_communities=True,
        include_statistics=True,
        include_path_based=False,
        include_advanced=False
    )
    
    # Print summary
    report.print_summary(results, top_n=10)

Analysis Components
-------------------

Centrality Measures
~~~~~~~~~~~~~~~~~~~

The report computes the following centrality measures:

**Degree-based:**

* Layer-specific degree/strength
* Supra degree/strength
* Overlapping degree/strength
* Participation coefficient

**Eigenvector-based:**

* Multiplex eigenvector centrality
* Eigenvector versatility
* Katz-Bonacich centrality
* PageRank centrality

**Path-based** (optional, computationally expensive):

* Multilayer closeness centrality
* Multilayer betweenness centrality

**Advanced** (optional, computationally expensive):

* HITS centrality
* Current-flow closeness/betweenness
* Subgraph centrality
* Total communicability
* Multiplex k-core

.. code-block:: python

    # Include only basic measures (fast)
    results = report.compute_centralities(
        include_path_based=False,
        include_advanced=False
    )
    
    # Include all measures (slow for large networks)
    results = report.compute_centralities(
        include_path_based=True,
        include_advanced=True
    )

Community Detection
~~~~~~~~~~~~~~~~~~~

The report supports multiple community detection algorithms:

* **Louvain**: Fast modularity optimization
* **Leiden**: Improved Louvain algorithm

.. code-block:: python

    # Run specific methods
    communities = report.detect_communities(
        methods=['louvain', 'leiden'],
        gamma=1.0,   # Resolution parameter
        omega=1.0    # Inter-layer coupling
    )
    
    # Results include community assignments and modularity scores
    print(communities['louvain'])
    # {('Alice', 'facebook'): 0, ('Bob', 'facebook'): 0, ...}
    
    print(communities['leiden']['modularity'])
    # 0.523

Network Statistics
~~~~~~~~~~~~~~~~~~

The report computes various network statistics:

**Basic statistics:**

* Layer densities
* Node activities
* Inter-layer coupling strength
* Edge overlap between layers

**Advanced statistics** (optional):

* Versatility centrality
* Multilayer clustering coefficient

.. code-block:: python

    stats = report.compute_statistics(
        include_advanced=False
    )
    
    # Access individual statistics
    print(stats['layer_densities'])
    # {'facebook': 0.667, 'twitter': 0.333}
    
    print(stats['node_activities'])
    # {'Alice': 1.0, 'Bob': 0.5, ...}

Working with Results
--------------------

Extracting Top Nodes
~~~~~~~~~~~~~~~~~~~~~

Get the most important nodes by any measure:

.. code-block:: python

    # Run analysis first
    report.run_all_analyses()
    
    # Get top nodes by specific measures
    top_by_degree = report.get_top_nodes(
        measure='overlapping_degree',
        n=5,
        category='centralities'
    )
    
    print(top_by_degree)
    # [('Alice', 4.0), ('Bob', 3.5), ...]
    
    top_by_eigenvector = report.get_top_nodes(
        measure='multiplex_eigenvector',
        n=5,
        category='centralities'
    )

Exporting Results
~~~~~~~~~~~~~~~~~

Export all results as a dictionary for further processing:

.. code-block:: python

    # Run analysis
    report.run_all_analyses()
    
    # Export results
    results_dict = report.export_to_dict()
    
    # Access specific results
    centralities = results_dict['centralities']
    communities = results_dict['communities']
    statistics = results_dict['statistics']
    
    # Save to file (example)
    import json
    with open('network_analysis.json', 'w') as f:
        json.dump(results_dict, f, indent=2, default=str)

Custom Summaries
~~~~~~~~~~~~~~~~

Print custom summaries with different options:

.. code-block:: python

    # Show top 10 nodes instead of default 5
    report.print_summary(results, top_n=10)
    
    # Or create your own summary
    if 'centralities' in results:
        overlapping = results['centralities']['overlapping_degree']
        top_nodes = sorted(overlapping.items(), key=lambda x: x[1], reverse=True)[:3]
        
        print("Most Central Nodes:")
        for node, centrality in top_nodes:
            print(f"  {node}: {centrality:.4f}")

Performance Considerations
--------------------------

The meta flow report is designed to be efficient, but some measures are computationally expensive:

**Fast** (suitable for large networks):

* Degree-based centralities
* Eigenvector-based centralities
* Basic statistics

**Slow** (expensive for large networks):

* Path-based centralities (closeness, betweenness)
* Advanced centralities (current-flow, communicability)
* Advanced statistics

**Recommendations:**

.. code-block:: python

    # For large networks (>10,000 nodes): use basic measures only
    results = run_meta_analysis(
        network,
        include_path_based=False,
        include_advanced=False
    )
    
    # For medium networks (1,000-10,000 nodes): include path-based
    results = run_meta_analysis(
        network,
        include_path_based=True,
        include_advanced=False
    )
    
    # For small networks (<1,000 nodes): include all measures
    results = run_meta_analysis(
        network,
        include_path_based=True,
        include_advanced=True
    )

Complete Example
----------------

Here's a complete example analyzing a social network:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.algorithms.meta_flow_report import MetaFlowReport
    
    # Create a 3-layer social network
    network = multinet.multi_layer_network(directed=False)
    
    # Add connections in different platforms
    network.add_edges([
        # Facebook layer
        ['Alice', 'facebook', 'Bob', 'facebook', 1],
        ['Bob', 'facebook', 'Carol', 'facebook', 1],
        ['Carol', 'facebook', 'David', 'facebook', 1],
        
        # Twitter layer
        ['Alice', 'twitter', 'Carol', 'twitter', 1],
        ['Bob', 'twitter', 'David', 'twitter', 1],
        
        # LinkedIn layer
        ['Alice', 'linkedin', 'Bob', 'linkedin', 1],
        ['Carol', 'linkedin', 'David', 'linkedin', 1],
        
        # Inter-layer connections
        ['Alice', 'facebook', 'Alice', 'twitter', 1],
        ['Alice', 'twitter', 'Alice', 'linkedin', 1],
        ['Bob', 'facebook', 'Bob', 'twitter', 1],
        ['Bob', 'twitter', 'Bob', 'linkedin', 1],
        ['Carol', 'facebook', 'Carol', 'twitter', 1],
        ['Carol', 'twitter', 'Carol', 'linkedin', 1],
        ['David', 'facebook', 'David', 'twitter', 1],
        ['David', 'twitter', 'David', 'linkedin', 1],
    ], input_type='list')
    
    # Run comprehensive analysis
    report = MetaFlowReport(network)
    results = report.run_all_analyses(
        include_centralities=True,
        include_communities=True,
        include_statistics=True,
        include_path_based=False,
        include_advanced=False,
        gamma=1.0,
        omega=1.0
    )
    
    # Print summary
    print("\n" + "="*80)
    print("NETWORK ANALYSIS SUMMARY")
    print("="*80)
    report.print_summary(results, top_n=3)
    
    # Extract key insights
    print("\n" + "="*80)
    print("KEY INSIGHTS")
    print("="*80)
    
    # Most influential users
    top_users = report.get_top_nodes('overlapping_degree', n=3, category='centralities')
    print("\nMost Active Users:")
    for user, degree in top_users:
        print(f"  {user}: {degree} connections")
    
    # Community structure
    if 'communities' in results and 'louvain' in results['communities']:
        comms = results['communities']['louvain']
        num_communities = len(set(comms.values()))
        print(f"\nCommunity Structure:")
        print(f"  {num_communities} communities detected")
    
    # Layer densities
    if 'statistics' in results and 'layer_densities' in results['statistics']:
        densities = results['statistics']['layer_densities']
        print(f"\nLayer Activity:")
        for layer, density in sorted(densities.items(), key=lambda x: x[1], reverse=True):
            print(f"  {layer}: {density:.2%} of possible connections")

API Reference
-------------

``run_meta_analysis(network, ...)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Convenience function for quick comprehensive analysis.

**Parameters:**

* ``network``: py3plex multi_layer_network object
* ``include_centralities`` (bool): Compute centrality measures (default: True)
* ``include_communities`` (bool): Run community detection (default: True)
* ``include_statistics`` (bool): Compute statistics (default: True)
* ``include_path_based`` (bool): Include expensive path-based measures (default: False)
* ``include_advanced`` (bool): Include expensive advanced measures (default: False)
* ``print_summary`` (bool): Print summary of results (default: True)

**Returns:** Dictionary with analysis results

``MetaFlowReport`` Class
~~~~~~~~~~~~~~~~~~~~~~~~

Main class for comprehensive network analysis.

**Methods:**

* ``compute_centralities(include_path_based, include_advanced)``
* ``detect_communities(methods, gamma, omega)``
* ``compute_statistics(include_advanced)``
* ``run_all_analyses(...)``
* ``print_summary(results, top_n)``
* ``export_to_dict()``
* ``get_top_nodes(measure, n, category)``

See Also
--------

* :doc:`multilayer_centrality` - Detailed centrality measures documentation
* :doc:`../user_guide/community_detection` - Community detection algorithms
* ``examples/network_analysis/example_meta_flow_report.py`` - Complete example

References
----------

This module integrates multiple analysis approaches from:

* Kivelä, M., et al. (2014). "Multilayer networks". Journal of complex networks, 2(3), 203-271.
* Mucha, P. J., et al. (2010). "Community structure in time-dependent, multiscale, and multiplex networks". Science, 328(5980), 876-878.
* De Domenico, M., et al. (2013). "Mathematical formulation of multilayer networks". Physical Review X, 3(4), 041022.
