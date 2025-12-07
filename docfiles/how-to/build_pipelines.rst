How to Build Analysis Pipelines with Dplyr-style Operations
============================================================

**Goal:** Chain operations to build reproducible analysis workflows.

**Prerequisites:** A loaded network (see :doc:`load_and_build_networks`).

Basic Pipeline
--------------

Node Operations
~~~~~~~~~~~~~~~

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.graph_ops import nodes
    
    network = multinet.multi_layer_network()
    network.load_network("data.multiedgelist", input_type="multiedgelist")
    
    # Build pipeline
    result = (
        nodes(network)
        .filter(lambda n: n["degree"] > 2)
        .mutate(score=lambda n: n["degree"] * 2)
        .arrange("degree", reverse=True)
        .to_pandas()
    )
    
    print(result.head())

Available Operations
--------------------

filter()
~~~~~~~~

Select nodes based on condition:

.. code-block:: python

    result = (
        nodes(network)
        .filter(lambda n: n["layer"] == "friends")
        .filter(lambda n: n["degree"] > 5)
        .to_pandas()
    )

mutate()
~~~~~~~~

Add or modify columns:

.. code-block:: python

    result = (
        nodes(network)
        .mutate(
            degree_squared=lambda n: n["degree"] ** 2,
            is_hub=lambda n: n["degree"] > 10
        )
        .to_pandas()
    )

select()
~~~~~~~~

Choose specific columns:

.. code-block:: python

    result = (
        nodes(network)
        .select("node", "layer", "degree")
        .to_pandas()
    )

arrange()
~~~~~~~~~

Sort results:

.. code-block:: python

    result = (
        nodes(network)
        .arrange("degree", reverse=True)  # Descending
        .to_pandas()
    )

group_by() and summarize()
~~~~~~~~~~~~~~~~~~~~~~~~~~

Aggregate data:

.. code-block:: python

    result = (
        nodes(network)
        .group_by("layer")
        .summarize(
            avg_degree=lambda g: g["degree"].mean(),
            max_degree=lambda g: g["degree"].max(),
            count=lambda g: len(g)
        )
        .to_pandas()
    )

**Expected output:**

.. code-block:: text

          layer  avg_degree  max_degree  count
    0   friends        3.45          12     46
    1      work        2.87          08     46
    2    family        4.12          15     42

Complex Pipelines
-----------------

Multi-Step Analysis
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    result = (
        nodes(network)
        # Step 1: Filter active nodes
        .filter(lambda n: n["layer_count"] > 1)
        # Step 2: Add computed score
        .mutate(
            activity_score=lambda n: n["degree"] * n["layer_count"]
        )
        # Step 3: Filter by score
        .filter(lambda n: n["activity_score"] > 20)
        # Step 4: Sort by score
        .arrange("activity_score", reverse=True)
        # Step 5: Get top 20
        .head(20)
        # Convert to pandas
        .to_pandas()
    )

Combining with DSL
------------------

Mix dplyr-style and DSL:

.. code-block:: python

    from py3plex.dsl import Q
    from py3plex.graph_ops import nodes
    
    # Use DSL to compute metrics
    dsl_result = (
        Q.nodes()
         .compute("degree", "betweenness_centrality")
         .execute(network)
    )
    
    # Use dplyr-style to filter and transform
    final_result = (
        nodes(dsl_result)
        .filter(lambda n: n["degree"] > 5)
        .mutate(
            centrality_rank=lambda n: n["betweenness_centrality"] * 100
        )
        .arrange("centrality_rank", reverse=True)
        .to_pandas()
    )

Sklearn-Style Pipelines
------------------------

For machine learning workflows:

.. code-block:: python

    from py3plex.pipeline import NetworkPipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    
    # Define pipeline
    pipeline = NetworkPipeline([
        ('features', 'compute_features'),  # Extract features
        ('scaler', StandardScaler()),       # Normalize
        ('cluster', KMeans(n_clusters=5))   # Cluster
    ])
    
    # Fit and predict
    labels = pipeline.fit_predict(network)
    
    print(f"Assigned {len(set(labels))} clusters")

Exporting Pipelines
-------------------

Save Pipeline Definition
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    import json
    
    pipeline_config = {
        'steps': [
            {'operation': 'filter', 'condition': 'degree > 2'},
            {'operation': 'mutate', 'column': 'score', 'expr': 'degree * 2'},
            {'operation': 'arrange', 'by': 'score', 'reverse': True}
        ]
    }
    
    with open('pipeline.json', 'w') as f:
        json.dump(pipeline_config, f, indent=2)

Load and Execute
~~~~~~~~~~~~~~~~

.. code-block:: python

    with open('pipeline.json', 'r') as f:
        config = json.load(f)
    
    # Execute pipeline from config
    result = execute_pipeline(network, config)

Reusable Pipelines
------------------

Create Pipeline Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def identify_hubs(network, threshold=10):
        """Reusable pipeline to identify hub nodes."""
        return (
            nodes(network)
            .filter(lambda n: n["degree"] > threshold)
            .mutate(hub_score=lambda n: n["degree"] * n["layer_count"])
            .arrange("hub_score", reverse=True)
            .to_pandas()
        )
    
    # Use
    hubs = identify_hubs(network, threshold=5)
    print(hubs)

Next Steps
----------

* **Query with DSL:** :doc:`query_with_dsl`
* **Complete workflows:** :doc:`reproduce_workflows`
* **API reference:** :doc:`../reference/api_index`
