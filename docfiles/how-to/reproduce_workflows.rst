How to Reproduce Common Analysis Workflows
===========================================

**Goal:** Use ready-made recipes for common multilayer network analysis tasks.

**Prerequisites:** Basic understanding of py3plex (see :doc:`../getting_started/tutorial_10min`).

Complete Workflows
------------------

This guide links to detailed recipes and case studies. For step-by-step implementations, see:

* **Recipes:** :doc:`../user_guide/recipes_and_workflows` — Focused solutions for specific tasks
* **Case Studies:** :doc:`../user_guide/case_studies` — Complete end-to-end analyses
* **Examples:** :doc:`../examples/index` — Runnable code examples

Quick Recipe Index
------------------

Network Construction
~~~~~~~~~~~~~~~~~~~~

* **Building from edge lists** → :doc:`load_and_build_networks`
* **Converting from NetworkX** → :doc:`../user_guide/recipes_and_workflows` (Recipe 1)
* **Loading temporal networks** → :doc:`../reference/api_index` (Temporal section)

Statistical Analysis
~~~~~~~~~~~~~~~~~~~~

* **Computing multilayer statistics** → :doc:`compute_statistics`
* **Comparing layers** → :doc:`../user_guide/recipes_and_workflows` (Recipe 3)
* **Node versatility analysis** → :doc:`../user_guide/recipes_and_workflows` (Recipe 4)

Community Detection
~~~~~~~~~~~~~~~~~~~

* **Multilayer Louvain** → :doc:`run_community_detection`
* **Cross-layer community comparison** → :doc:`../user_guide/recipes_and_workflows` (Recipe 5)
* **Community stability analysis** → :doc:`../user_guide/case_studies` (Case Study 2)

Network Embeddings
~~~~~~~~~~~~~~~~~~

* **Node2Vec for link prediction** → :doc:`run_random_walks`
* **Embedding-based clustering** → :doc:`../user_guide/recipes_and_workflows` (Recipe 7)
* **Layer-specific embeddings** → :doc:`run_random_walks`

Visualization
~~~~~~~~~~~~~

* **Publication-ready plots** → :doc:`visualize_networks`
* **Interactive visualizations** → :doc:`visualize_networks`
* **Layer comparison plots** → :doc:`../user_guide/recipes_and_workflows` (Recipe 9)

Domain-Specific Workflows
--------------------------

Social Networks
~~~~~~~~~~~~~~~

**Multi-platform social analysis:**

.. code-block:: python

    # See: user_guide/case_studies.rst - Social Network Case Study
    # 1. Load data from multiple platforms
    # 2. Detect cross-platform communities
    # 3. Identify influential users
    # 4. Analyze information diffusion

See :doc:`../user_guide/case_studies` for complete implementation.

Biological Networks
~~~~~~~~~~~~~~~~~~~

**Multi-omics integration:**

.. code-block:: python

    # See: user_guide/case_studies.rst - Biological Network Case Study
    # 1. Integrate protein-protein + gene regulation + metabolic pathways
    # 2. Find key regulators using multilayer centrality
    # 3. Detect functional modules
    # 4. Prioritize disease genes

See :doc:`../user_guide/case_studies` for complete implementation.

Transportation Networks
~~~~~~~~~~~~~~~~~~~~~~~

**Multimodal route analysis:**

.. code-block:: python

    # See: examples/index.rst - Transportation Example
    # 1. Model different transportation modes as layers
    # 2. Add transfer connections between layers
    # 3. Compute optimal multimodal routes
    # 4. Identify critical transfer points

See :doc:`../examples/index` for runnable code.

Config-Driven Workflows
-----------------------

Use configuration files for reproducibility:

.. code-block:: yaml

    # workflow_config.yaml
    network:
      input_file: "data.multiedgelist"
      input_type: "multiedgelist"
    
    analysis:
      - name: "statistics"
        metrics: ["degree", "betweenness_centrality"]
      
      - name: "community_detection"
        algorithm: "louvain"
        params:
          resolution: 1.0
      
      - name: "visualization"
        output: "network.png"
        layout: "force_directed"

Execute workflow:

.. code-block:: python

    from py3plex.workflows import execute_workflow
    
    results = execute_workflow("workflow_config.yaml")

See :doc:`../user_guide/recipes_and_workflows` for complete config-driven workflow examples.

Batch Processing
----------------

Process multiple networks:

.. code-block:: python

    import glob
    from py3plex.core import multinet
    
    results = []
    
    for filename in glob.glob("data/*.multiedgelist"):
        # Load network
        network = multinet.multi_layer_network()
        network.load_network(filename, input_type="multiedgelist")
        
        # Apply analysis pipeline
        stats = analyze_network(network)  # Your custom function
        
        results.append({
            'filename': filename,
            'stats': stats
        })
    
    # Aggregate results
    summary = aggregate_results(results)

Complete Example Templates
---------------------------

The following locations contain complete, runnable examples:

1. **User Guide Recipes** (:doc:`../user_guide/recipes_and_workflows`)
   
   * Recipe-style solutions with code + explanation
   * Focused on single tasks

2. **Case Studies** (:doc:`../user_guide/case_studies`)
   
   * End-to-end analyses
   * Real-world datasets
   * Publication-ready results

3. **Examples Gallery** (:doc:`../examples/index`)
   
   * Standalone Python scripts
   * Minimal, focused examples
   * Easy to adapt

Next Steps
----------

* **Learn fundamentals:** :doc:`../getting_started/tutorial_10min`
* **Detailed recipes:** :doc:`../user_guide/recipes_and_workflows`
* **Complete case studies:** :doc:`../user_guide/case_studies`
* **Browse examples:** :doc:`../examples/index`
