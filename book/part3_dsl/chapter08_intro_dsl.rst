.. _dsl-chapter:

DSL Fundamentals: A Query Mental Model
======================================

The DSL is useful when you need clear, replayable analytical pipelines over multilayer data. This chapter teaches the mental model first and syntax second.

Why a DSL Here?
---------------

A query pipeline makes assumptions explicit:

* selection scope (which layers, which entities),
* computed measures,
* ordering and filtering logic,
* reproducibility settings.

This helps analysts review and reproduce analytical intent.

Core Workflow Pattern
---------------------

.. code-block:: python

    from py3plex.dsl import Q, L

    result = (
        Q.nodes()
         .from_layers(L['social'])
         .where(degree__gt=3)
         .compute('betweenness_centrality')
         .order_by('-betweenness_centrality')
         .limit(10)
         .execute(network)
    )

Interpretation boundary: this is a reproducible computational selection, not automatically a defensible scientific claim.

Theory vs Implementation vs Workflow
------------------------------------

* **Theory:** filtering by degree defines a set under a degree function.
* **Implementation:** py3plex resolves fields, may autocompute metrics, and executes against internal graph structures.
* **Workflow:** your chosen thresholds and ordering reflect domain judgment.

Keep these separate in analysis reports.

Layer Algebra and Scope Control
-------------------------------

Layer selection should reflect hypothesis scope, not convenience:

.. code-block:: python

    from py3plex.dsl import L

    social_or_work = L['social'] + L['work']
    social_not_work = L['social'] - L['work']

A common error is using all layers by default and inferring layer-specific conclusions.

What New Users Usually Misunderstand
------------------------------------

1. Query fluency does not remove semantic ambiguity (replicas vs physical nodes).
2. A short query can still encode strong assumptions.
3. Ranking stability requires separate checks (UQ, sensitivity, or perturbation).

Next Step
---------

Chapter 9 covers builder internals and explain plans. Chapter 10 covers advanced workflows where query complexity can hide methodological risk.
