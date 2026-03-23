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

Raw Python vs DSL (When to Use Each)
------------------------------------

Use raw Python when the task is truly simple or highly custom (for example, quick one-off filtering in a notebook). Use the DSL when you need an auditable chain with explicit scope, ordering, and reproducibility hooks. A practical split: prototype in Python if needed, then promote claim-bearing analysis to DSL.

Theory vs Implementation vs Workflow
------------------------------------

* **Theory:** filtering by degree defines a set under a degree function.
* **Implementation:** py3plex resolves fields, may autocompute metrics, and executes against internal graph structures.
* **Workflow:** your chosen thresholds and ordering reflect domain judgment.

In the query above, ``where(degree__gt=3)`` is not just syntax: it operationalizes an inclusion threshold that can change the inferred "important actors" set.
Keep these separate in analysis reports.

Layer Algebra and Scope Control
-------------------------------

Layer selection should reflect hypothesis scope, not convenience:

.. code-block:: python

    from py3plex.dsl import L

    social_or_work = L['social'] + L['work']
    social_not_work = L['social'] - L['work']

A common error is using all layers by default and inferring layer-specific conclusions.

Autocompute and Hidden Assumptions
----------------------------------

Autocompute can be useful, but it can also hide expensive or semantically consequential metric resolution. If a field is resolved implicitly, reviewers may miss that a methodological choice was made. Prefer explicit ``.compute(...)`` calls in claim-bearing workflows.

What New Users Usually Misunderstand
------------------------------------

1. Query fluency does not remove semantic ambiguity (replicas vs physical nodes).
2. A short query can still encode strong assumptions.
3. Ranking stability requires separate checks (UQ, sensitivity, or perturbation).

For example, ``Q.nodes().from_layers(L['social']).order_by('-degree').limit(10)`` looks compact but encodes a strong methodological choice: social-layer degree is being treated as the primary definition of importance.

Next Step
---------

Chapter 10 covers builder internals and explain plans. Chapter 11 covers advanced workflows where query complexity can hide methodological risk.
