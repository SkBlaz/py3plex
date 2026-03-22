.. _advanced-dsl-chapter:

Advanced Workflows: Compositional Queries Under Uncertainty
===========================================================

Advanced DSL usage is not about longer chains. It is about controlling semantic scope, computational cost, and uncertainty propagation.

Workflow Pattern 1: Grouped Selection with Coverage
----------------------------------------------------

.. code-block:: python

    from py3plex.dsl import Q, L

    result = (
        Q.nodes()
         .from_layers(L['*'])
         .compute('degree')
         .per_layer()
           .top_k(10, 'degree')
         .end_grouping()
         .coverage(mode='at_least', k=2)
         .execute(network)
    )

Judgment point: coverage threshold controls strictness. ``all`` can be too restrictive in heterogeneous systems.

Workflow Pattern 2: UQ-Aware Ranking
------------------------------------

.. code-block:: python

    result = (
        Q.nodes()
         .compute('pagerank')
         .uq(method='bootstrap', n_samples=100, seed=42)
         .order_by('-pagerank')
         .limit(20)
         .execute(network)
    )

Interpretive warning: confidence intervals quantify algorithm/data perturbation under a model; they do not validate domain truth.

Workflow Pattern 3: Temporal Slicing
------------------------------------

.. code-block:: python

    temporal = (
        Q.edges()
         .during(100.0, 150.0)
         .from_layers(L['transport'])
         .execute(temporal_network)
    )

Judgment point: time-window boundaries can dominate observed effects. Report window design choices explicitly.

Composability vs Readability
----------------------------

As pipelines grow, readability declines. Recommended practices:

* split complex pipelines into named stages,
* log final query strings or AST hashes,
* avoid mixing exploratory and production logic in one chain.

Performance and Approximation
-----------------------------

For larger networks:

* use selective layer scopes before expensive measures,
* use approximations when ranking is sufficient,
* record approximation parameters in outputs.

Never present approximate outputs as exact without explicit disclosure.

Advanced Checklist
------------------

Before finalizing an advanced query workflow:

1. verify semantic scope (global vs per-layer),
2. verify uncertainty configuration,
3. verify seeds and provenance capture,
4. verify that outputs answer the intended question.
