How to Build Analysis Pipelines with Dplyr-style Operations
============================================================

**Goal:** Chain operations to build reproducible analysis workflows on node or edge tables.

**Prerequisites:** Load a network first (see :doc:`load_and_build_networks`). ``nodes(...)`` returns a chainable ``NodeFrame`` (view over ``id``, ``layer``, ``degree``, etc.); ``edges(...)`` returns an ``EdgeFrame``. Examples below use ``NodeFrame`` and end with ``.to_pandas()`` to materialize results.

Quickstart
----------

Filter → add a column → sort → convert to pandas:

.. code-block:: python

    from py3plex.core import multinet
    from py3plex.graph_ops import nodes
    
    network = multinet.multi_layer_network()
    network.load_network("data.multiedgelist", input_type="multiedgelist")
    
    # Build pipeline: filter → add a column → sort → convert to pandas
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

Common verbs you can chain on ``nodes(...)`` or ``edges(...)``:

- ``filter``: keep rows that satisfy a predicate
- ``mutate``: add or modify columns
- ``select``: choose columns (and optionally reorder)
- ``arrange``: sort by a column or key function
- ``group_by`` + ``summarise``: aggregate per group
- ``head``: keep the first *n* rows (useful for previews)

filter()
~~~~~~~~

Select rows based on conditions. Chain multiple filters for readability:

.. code-block:: python

    result = (
        nodes(network)
        .filter(lambda n: n["layer"] == "friends")
        .filter(lambda n: n["degree"] > 5)
        .to_pandas()
    )

mutate()
~~~~~~~~

Add or modify columns using callables that receive each row (a dict-like object):

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

Choose specific columns (and optionally reorder them):

.. code-block:: python

    result = (
        nodes(network)
        .select("id", "layer", "degree")
        .to_pandas()
    )

arrange()
~~~~~~~~~

Sort results (ascending by default, or descending with ``reverse=True``):

.. code-block:: python

    result = (
        nodes(network)
        .arrange("degree", reverse=True)  # Descending
        .to_pandas()
    )

group_by() and summarise()
~~~~~~~~~~~~~~~~~~~~~~~~~~

Aggregate by one or more columns. ``summarise`` expects functions that return scalars (e.g., ``mean``, ``max``, ``len``):

.. code-block:: python

    result = (
        nodes(network)
        .group_by("layer")
        .summarise(
            avg_degree=lambda g: g["degree"].mean(),
            max_degree=lambda g: g["degree"].max(),
            count=lambda g: len(g)
        )
        .to_pandas()
    )

**Illustrative output (values depend on your data):**

.. code-block:: text

          layer  avg_degree  max_degree  count
    0   friends        3.45          12     46
    1      work        2.87           8     46
    2    family        4.12          15     42

Complex Pipelines
-----------------

Multi-Step Analysis
~~~~~~~~~~~~~~~~~~~

Combine several verbs to narrow down to the most active nodes. This example assumes ``layer_count`` and ``degree`` columns already exist (e.g., after computing node statistics):

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

Mix dplyr-style operations with DSL queries to narrow down candidates, then enrich them:

.. code-block:: python

    from py3plex.dsl import Q
    from py3plex.graph_ops import nodes
    
    # Use the same network as above
    # Use DSL (Builder API) to select nodes and compute measures once
    dsl_result = (
        Q.nodes()
         .where(degree__gt=5)
         .compute("betweenness_centrality")
         .execute(network)
    )
    
    # Extract nodes and betweenness values
    selected = set(dsl_result.items)
    df_dsl = dsl_result.to_pandas()
    
    # Use dplyr-style to filter and transform the same nodes
    final_result = (
        nodes(network)
        .filter(lambda n: (n["id"], n["layer"]) in selected)
        .mutate(
            betweenness=lambda n: betweenness.get((n["id"], n["layer"]), 0.0),
            centrality_rank=lambda n: betweenness.get((n["id"], n["layer"]), 0.0) * 100
        )
        .arrange("centrality_rank", reverse=True)
        .to_pandas()
    )

Scikit-learn-style Pipelines
----------------------------

Use the built-in ``Pipeline`` to chain reusable steps (each step implements ``transform`` and receives the previous output). The first step should handle ``None`` input (``LoadStep`` does). Replace or extend steps with your own ``PipelineStep`` subclasses when needed.

.. code-block:: python

    from py3plex.pipeline import Pipeline, LoadStep, FilterNodes, ComputeStats
    
    pipe = Pipeline([
        ("load", LoadStep(path="data.multiedgelist", input_type="multiedgelist")),
        ("filter", FilterNodes(min_degree=2)),
        ("stats", ComputeStats(include_layer_stats=True)),
    ])
    
    stats = pipe.run()
    print(stats)
    
Custom steps can wrap scikit-learn components if they implement ``transform`` (and optionally ``fit``) to accept the previous step's output and return the next input.

Exporting Pipelines
-------------------

Persist Step Settings
~~~~~~~~~~~~~~~~~~~~~

Store the parameters you passed to each step so you can recreate the pipeline later:

.. code-block:: python

    import json
    
    config = {
        "steps": [
            {"name": "load", "params": {"path": "data.multiedgelist", "input_type": "multiedgelist"}},
            {"name": "filter", "params": {"min_degree": 2}},
            {"name": "stats", "params": {"include_layer_stats": True}},
        ]
    }
    
    with open("pipeline.json", "w") as f:
        json.dump(config, f, indent=2)

Reload and Rebuild
~~~~~~~~~~~~~~~~~~

Recreate the pipeline by instantiating the same steps with saved parameters:

.. code-block:: python

    import json
    from py3plex.pipeline import Pipeline, LoadStep, FilterNodes, ComputeStats
    
    with open("pipeline.json", "r") as f:
        config = json.load(f)
    
    step_params = {step["name"]: step["params"] for step in config["steps"]}
    
    pipe = Pipeline([
        ("load", LoadStep(**step_params["load"])),
        ("filter", FilterNodes(**step_params["filter"])),
        ("stats", ComputeStats(**step_params["stats"])),
    ])
    
    stats = pipe.run()

Reusable Pipelines
------------------

Create Pipeline Functions
~~~~~~~~~~~~~~~~~~~~~~~~~

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
