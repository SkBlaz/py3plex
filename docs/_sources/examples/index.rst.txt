Examples
========

This page provides a curated list of example scripts demonstrating py3plex features. All examples are available in the `examples/ directory <https://github.com/SkBlaz/py3plex/tree/master/examples>`_ of the repository.

Getting Started Examples
------------------------

**Basic Network Creation**

* ``example_load_network.py`` - Loading networks from files
* ``example_create_network.py`` - Creating networks from scratch
* ``example_basic_stats.py`` - Computing basic statistics

**Quick Tutorials**

* ``tutorial_10min.py`` - Executable version of the 10-minute tutorial
* ``example_quick_start.py`` - Quick start examples

Visualization Examples
----------------------

**Basic Visualization**

* ``example_multilayer_visualization.py`` - Basic multilayer plots
* ``example_simple_viz.py`` - Simple visualization examples
* ``example_hairball.py`` - Hairball plots

**Advanced Visualization**

* ``example_custom_layouts.py`` - Custom layout algorithms
* ``example_diagonal_plot.py`` - Diagonal projection for multilayer networks
* ``example_interactive_plots.py`` - Interactive visualizations with Plotly
* ``example_layer_visualization.py`` - Layer-by-layer visualization

**Community Visualization**

* ``example_community_viz.py`` - Visualizing detected communities
* ``example_colored_networks.py`` - Custom node/edge coloring

Community Detection Examples
-----------------------------

**Single-Layer Community Detection**

* ``example_community_detection.py`` - Louvain and Infomap
* ``example_louvain.py`` - Louvain algorithm examples
* ``example_label_propagation.py`` - Semi-supervised community detection

**Multilayer Community Detection**

* ``example_multilayer_communities.py`` - Multilayer Louvain
* ``example_modularity.py`` - Modularity optimization
* ``example_overlapping_communities.py`` - Overlapping community detection

DSL and Query Examples
----------------------

**DSL v2 (Recommended)**

* ``example_dsl_builder_api.py`` - Comprehensive Python builder API examples (Q, L, Param)
* ``example_dsl_queries.py`` - String DSL syntax examples  
* ``example_dsl_advanced.py`` - Advanced queries and transportation network analysis
* ``example_dsl_community_detection.py`` - Community detection with DSL

**Features**:
- SQL-like syntax for network queries
- Python builder API with type hints (``Q.nodes()``, ``L["layer"]``, ``Param``)
- Layer algebra (union, difference, intersection)
- Django-style WHERE conditions (``degree__gt=5``)
- COMPUTE measures with aliases
- ORDER BY, LIMIT, EXPLAIN mode
- Export to pandas, NetworkX, Arrow

Network Statistics Examples
----------------------------

**Basic Statistics**

* ``example_multilayer_statistics.py`` - Multilayer-specific statistics
* ``example_layer_comparison.py`` - Comparing layers
* ``example_node_metrics.py`` - Node-level metrics

**Centrality Measures**

* ``example_centrality.py`` - Degree, betweenness, PageRank
* ``example_multilayer_centrality.py`` - Multilayer centrality measures
* ``example_versatility.py`` - Versatility centrality

**Network Comparison**

* ``example_network_comparison.py`` - Comparing multiple networks
* ``example_statistical_tests.py`` - Statistical comparison

I/O and Data Format Examples
-----------------------------

**Loading Networks**

* ``example_IO.py`` - Various input formats
* ``example_edgelist_loading.py`` - Edge list formats
* ``example_graphml.py`` - GraphML format
* ``example_csv_loading.py`` - CSV with sidecars

**Modern I/O (Arrow/Parquet)**

* ``example_arrow_io.py`` - Apache Arrow format
* ``example_parquet.py`` - Parquet format
* ``example_schema_graph.py`` - Schema-based I/O

**Format Conversion**

* ``example_format_conversion.py`` - Converting between formats
* ``example_export.py`` - Exporting networks

Random Walks and Embeddings
----------------------------

**Random Walks**

* ``example_random_walks.py`` - Basic and Node2Vec walks
* ``example_walkers.py`` - Different walk strategies
* ``example_metapath_walks.py`` - Meta-path based walks

**Node Embeddings**

* ``example_n2v_embedding.py`` - Node2Vec embeddings
* ``example_deepwalk.py`` - DeepWalk embeddings
* ``example_embeddings.py`` - Various embedding methods

**Embedding Applications**

* ``example_link_prediction.py`` - Link prediction with embeddings
* ``example_node_classification.py`` - Node classification
* ``example_clustering_embeddings.py`` - Clustering with embeddings

Network Decomposition
----------------------

* ``example_network_decomposition.py`` - Meta-path feature extraction
* ``example_feature_extraction.py`` - Network feature engineering
* ``example_tensor_decomposition.py`` - Tensor decomposition methods

Network Manipulation
--------------------

* ``example_manipulation.py`` - Network operations (add, remove, filter)
* ``example_subnetworks.py`` - Extracting subnetworks
* ``example_layer_operations.py`` - Layer-specific operations
* ``example_aggregation.py`` - Aggregating layers

Algorithms and Analysis
-----------------------

**Network Dynamics**

* ``example_spreading.py`` - Network traversal and spreading processes
* ``example_sir_epidemic.py`` - SIR epidemic simulation
* ``example_diffusion.py`` - Diffusion processes

**Specialized Algorithms**

* ``example_ricci_curvature.py`` - Ricci curvature computation
* ``example_motifs.py`` - Network motif discovery
* ``example_path_analysis.py`` - Path-based analysis

**Machine Learning**

* ``example_ml_features.py`` - Feature extraction for ML
* ``example_graph_kernels.py`` - Graph kernel methods
* ``example_supervised_learning.py`` - Supervised learning on networks

NetworkX Integration
--------------------

* ``example_networkx_wrapper.py`` - Using NetworkX functions
* ``example_networkx_interop.py`` - NetworkX interoperability
* ``example_convert_networkx.py`` - Converting to/from NetworkX

Benchmarking
------------

* ``example_benchmarking.py`` - Performance benchmarking
* ``example_scalability.py`` - Scalability testing
* ``example_memory_profiling.py`` - Memory usage analysis

GUI and API
-----------

* ``example_api_usage.py`` - Using the REST API
* ``example_gui_integration.py`` - GUI integration examples
* ``example_batch_processing.py`` - Batch processing with CLI

Real-World Datasets
-------------------

**Biological Networks**

* ``example_protein_interaction.py`` - Protein-protein interaction networks
* ``example_gene_regulation.py`` - Gene regulatory networks
* ``example_metabolic_networks.py`` - Metabolic pathways

**Social Networks**

* ``example_social_multiplex.py`` - Multiplex social networks
* ``example_citation_network.py`` - Citation networks
* ``example_collaboration.py`` - Collaboration networks

**Transportation**

* ``example_multimodal_transport.py`` - Multi-modal transportation
* ``example_flight_network.py`` - Airline networks

Running Examples
----------------

All examples can be run directly with Python from the repository root:

.. code-block:: bash

    # Run DSL builder API examples (recommended starting point)
    python examples/network_analysis/example_dsl_builder_api.py
    
    # Run string DSL examples
    python examples/network_analysis/example_dsl_queries.py
    
    # Run advanced DSL examples
    python examples/network_analysis/example_dsl_advanced.py
    
    # Run a visualization example
    python examples/visualization/example_multilayer_visualization.py
    
    # Run a community detection example
    python examples/communities/example_community_detection.py
    
    # Run a getting started example
    python examples/getting_started/tutorial_10min.py

Many examples accept command-line arguments:

.. code-block:: bash

    python examples/communities/example_community_detection.py --algorithm louvain

Example Template
----------------

Use this template when creating new example scripts. The pattern includes
a docstring, a ``main()`` function, and an ``if __name__ == "__main__":`` guard:

.. code-block:: python

    """
    Example: Your Feature
    =====================
    
    Description of what this example demonstrates.
    
    Usage:
        python examples/<category>/example_your_feature.py
    """
    
    from py3plex.core import multinet
    from py3plex.visualization.multilayer import draw_multilayer_default
    
    def main():
        # Load or create network
        network = multinet.multi_layer_network()
        network.add_edges([
            ['A', 'layer1', 'B', 'layer1', 1]
        ], input_type="list")
        
        # Your analysis
        network.basic_stats()
        
        # Visualization
        draw_multilayer_default([network], display=True)
    
    if __name__ == "__main__":
        main()

Contributing Examples
---------------------

To contribute an example:

1. Create a well-documented script in the appropriate ``examples/<category>/`` directory
2. Use the template above with docstring + ``main()`` + ``if __name__ == "__main__":``
3. Follow the naming convention: ``example_<feature>.py``
4. Test that it runs without errors
5. Add it to this index with a brief description
6. Submit a pull request

See :doc:`../dev/contributing` for detailed guidelines.

Related Documentation
---------------------

* :doc:`../getting_started/quickstart_5min` - Quick start guide
* :doc:`../getting_started/tutorial_10min` - 10-minute tutorial
* :doc:`../user_guide/networks` - Working with networks
* :doc:`../user_guide/visualization` - Visualization guide

**Repository:**

* Examples directory: https://github.com/SkBlaz/py3plex/tree/master/examples
* Submit examples: https://github.com/SkBlaz/py3plex/pulls
