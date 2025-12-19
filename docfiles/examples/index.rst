Examples & Recipes
==================

Browse runnable scripts grouped by topic. Every entry below corresponds to a file in the ``examples/`` directory (`GitHub listing <https://github.com/SkBlaz/py3plex/tree/master/examples>`_), so you can copy, run, and adapt it directly. Run commands from the repository root with your virtual environment activated, and treat all paths as relative to ``examples/``.

**What's here:**

* **Runnable Examples** — Copy-paste code for common tasks
* **Analysis Recipes** — Reusable patterns (:doc:`../user_guide/recipes_and_workflows`)
* **Case Studies** — In-depth applications (:doc:`../user_guide/case_studies`)

**Quick start picks (paths relative to ``examples/``):**

* **DSL examples:** ``network_analysis/example_dsl_builder_api.py`` — Best starting point
* **Visualization:** ``visualization/example_multilayer_visualization.py``
* **Community detection:** ``communities/example_community_detection.py``
* **10-minute tutorial:** ``getting_started/tutorial_10min.py``

To run any example:

.. code-block:: bash

    python examples/<category>/<filename>.py

.. admonition:: Featured: DSL Examples
   :class: dsl-example

   The DSL examples showcase py3plex's SQL-like query language:

   .. code-block:: python

       from py3plex.dsl import Q, L

       # From example_dsl_builder_api.py - Comprehensive DSL v2
       result = (
           Q.nodes()
            .from_layers(L["social"] + L["work"])
            .where(degree__gt=5)
            .compute("betweenness_centrality", "pagerank")
            .order_by("-betweenness_centrality")
            .limit(20)
            .export_csv("top_influencers.csv")
            .execute(network)
       )

   **Recommended starting points:**

   * ``example_dsl_builder_api.py`` — Complete DSL v2 tutorial
   * ``example_dsl_queries.py`` — String DSL syntax
   * ``example_dsl_advanced.py`` — Advanced patterns

   See :doc:`../user_guide/dsl` for full DSL documentation!

Getting Started Examples
------------------------

Create small networks, load existing ones, and get oriented with the library.

**Basic Network Creation**

* ``example_load_network.py`` - Loading networks from files
* ``example_create_network.py`` - Creating networks from scratch
* ``example_basic_stats.py`` - Computing basic statistics

**Quick Tutorials**

* ``tutorial_10min.py`` - Executable version of the 10-minute tutorial
* ``example_quick_start.py`` - Quick start examples

Visualization Examples
----------------------

Plot multilayer networks, from simple layouts to interactive views.

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

Detect communities in single-layer and multilayer settings.

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

Use the DSL for expressive queries via strings or the builder API.

**DSL v2 (recommended)**

* ``example_dsl_builder_api.py`` - Comprehensive Python builder API examples (Q, L, Param)
* ``example_dsl_queries.py`` - String DSL syntax examples
* ``example_dsl_advanced.py`` - Advanced queries and transportation network analysis
* ``example_dsl_community_detection.py`` - Community detection with DSL

**Highlights:**
- SQL-like syntax for network queries
- Python builder API with type hints (``Q.nodes()``, ``L["layer"]``, ``Param``)
- Layer algebra (union, difference, intersection)
- Django-style WHERE conditions (``degree__gt=5``)
- COMPUTE measures with aliases
- ORDER BY, LIMIT, EXPLAIN mode
- Export to pandas, NetworkX, Arrow

Network Statistics Examples
----------------------------

Compute and compare network-level and node-level statistics.

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

Load, validate, and convert networks across common formats.

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

Generate walks and derive embeddings for downstream tasks.

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

Extract features and tensors from multilayer networks.

* ``example_network_decomposition.py`` - Meta-path feature extraction
* ``example_feature_extraction.py`` - Network feature engineering
* ``example_tensor_decomposition.py`` - Tensor decomposition methods

Network Manipulation
--------------------

Modify, subset, and aggregate networks.

* ``example_manipulation.py`` - Network operations (add, remove, filter)
* ``example_subnetworks.py`` - Extracting subnetworks
* ``example_layer_operations.py`` - Layer-specific operations
* ``example_aggregation.py`` - Aggregating layers

Algorithms and Analysis
-----------------------

Explore dynamics, motifs, and ML pipelines on networks.

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

Bridge py3plex and NetworkX for interoperability.

* ``example_networkx_wrapper.py`` - Using NetworkX functions
* ``example_networkx_interop.py`` - NetworkX interoperability
* ``example_convert_networkx.py`` - Converting to/from NetworkX

Benchmarking
------------

Measure performance and resource usage on representative workloads.

* ``example_benchmarking.py`` - Performance benchmarking
* ``example_scalability.py`` - Scalability testing
* ``example_memory_profiling.py`` - Memory usage analysis

GUI and API
-----------

Drive py3plex via the REST API, GUI, or batch commands.

* ``example_api_usage.py`` - Using the REST API
* ``example_gui_integration.py`` - GUI integration examples
* ``example_batch_processing.py`` - Batch processing with CLI

Case Studies: End-to-End Workflows
-----------------------------------

Complete domain-specific analysis pipelines with interpretation. Each case study follows a standard workflow: Data Import → Stats → Analysis → Visualization → Interpretation.

All case studies are in the ``examples/case_studies/`` directory. See the `Case Studies README <https://github.com/SkBlaz/py3plex/tree/master/examples/case_studies/README.md>`_ for complete documentation.

**Biological Networks** — Intermediate

* ``biological_networks.py`` - Protein-gene-disease multilayer network

  * Explores how protein interactions, gene regulation, and diseases interconnect
  * Shows how to surface hub proteins (e.g., TP53) as potential drug targets
  * Demonstrates detecting functional biological modules through community detection
  * **Layers:** protein (PPI), gene (regulation), disease (associations)
  * **Key techniques:** Multilayer centrality, cross-layer communities

**Social Networks** — Beginner

* ``social_networks.py`` - Multi-platform social media analysis

  * Shows how to identify cross-platform influencers
  * Compares behavior across Facebook, Twitter, LinkedIn
  * Demonstrates detecting social communities spanning multiple platforms
  * **Layers:** facebook (friends), twitter (followers), linkedin (professional)
  * **Key techniques:** Influence metrics, platform comparison

**Transportation Networks** — Intermediate

* ``transportation_networks.py`` - Multi-modal urban transport

  * Highlights critical transfer hubs
  * Computes accessibility metrics for urban planning
  * Highlights service zones and coverage gaps
  * **Layers:** bus (coverage), metro (backbone), bike (short trips)
  * **Key techniques:** Accessibility analysis, hub identification

**Using Case Studies:**

Each case study is:

* **Self-contained** — Generates synthetic data, no external files needed
* **Structured** — Follows 4-step pipeline (Import → Stats → Pipeline → Viz)
* **Interpretable** — Extensive domain-specific commentary on results
* **Adaptable** — Designed as templates for your own data

Run a case study:

.. code-block:: bash

    python examples/case_studies/biological_networks.py
    python examples/case_studies/social_networks.py
    python examples/case_studies/transportation_networks.py

See also:

* **Book chapters 12-14 (where available)** — Extended case studies with theoretical background
* **Notebooks** — Interactive versions (coming soon)

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

All examples can be run directly with Python from the repository root (paths below are relative to that root and assume an active virtual environment):

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

1. Create a well-documented script in the appropriate ``examples/<category>/`` directory.
2. Use the template above with docstring + ``main()`` + ``if __name__ == "__main__":``.
3. Follow the naming convention: ``example_<feature>.py``.
4. Test that it runs without errors from the repository root.
5. Add it to this index with a brief description under the correct topic.
6. Submit a pull request.

See :doc:`../dev/contributing` for detailed guidelines.

Related Documentation
---------------------

* :doc:`../getting_started/tutorial_10min` - 10-minute tutorial
* :doc:`../user_guide/networks` - Working with networks
* :doc:`../user_guide/visualization` - Visualization guide

**Repository:**

* Examples directory: https://github.com/SkBlaz/py3plex/tree/master/examples
* Submit examples: https://github.com/SkBlaz/py3plex/pulls
